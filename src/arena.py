import config
import numpy as np
from multiprocessing import Pool, Manager, cpu_count
from src.lib.cards import CARD_MAH
from src.lib.combinations import FIGURE_DOG, FIGURE_DRA, build_action_space, FIGURE_PASS
from src.players.agent import Agent
from src.players.client import Client
from src.private_state import PrivateState
from src.public_state import PublicState
from time import time
from typing import Optional


class Arena:
    # In der Arena können Agenten gegeneinander antreten.

    def __init__(self, agents: list[Agent], max_episodes: int, verbose=False,
                 validate=False, capture=False, early_stopping=False, win_rate: float=config.ARENA_WIN_RATE,
                 pubs: tuple[PublicState] = (),
                 privs: tuple[tuple[PrivateState, PrivateState, PrivateState, PrivateState]] = (),
                 worker: int = config.ARENA_WORKER,
                 seed=None):
        assert len(agents) == 4
        self._agents = agents  # Agent 0, Agent 1, Agent 2 und Agent 3
        self._max_episodes = max_episodes  # Maximale Anzahl zu spielende Partien
        self._verbose = verbose  # Spielverlauf ausführlich anzeigen
        self._validate = validate  # Aktionen überprüfen
        self._capture = capture  # Trainingsdaten aus dem Spiel generieren
        self._early_stopping = early_stopping  # Wettkampf abbrechen, wenn die Gewinnquote erreicht wurde oder nicht mehr erreicht werden kann
        self._win_rate = win_rate  # gewünschte Gewinnquote WIN / (WIN + LOST); nur relevant, wenn early_stopping gesetzt ist
        self._stop_event = Manager().Event()
        self._init_pubs = pubs  # wenn gesetzt, werden diese öffentlichen Spielzustände zum Start einer neuen Epoche genommen
        self._init_privs = privs  # wenn gesetzt, werden diese privaten Spielzustände zum Start einer neuen Epoche genommen
        self._worker = worker  # wenn größer 1, werden die Episode in entsprechend vielen Prozessen parallel ausgeführt
        #self._progbar = Progbar(max_episodes, stateful_metrics=["Wins", "Lost", "Draws"])
        self._time_start = None  # Zeitstempel zu Beginn der ersten Partie.
        self._seconds = 0  # Spieldauer insgesamt in Sekunden
        self._episodes = 0  # Anzahl Episoden
        self._rounds = 0  # Rundenzähler über alle Episoden
        self._tricks = 0  # Stichzähler über alle Episoden
        self._rating = [0, 0, 0]  # Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)
        self._history = []  # Spielverlauf = [ ([(state, probability, action)], reward) ]
        self._seed = seed  # Initialwert für Zufallsgenerator (Integer > 0 oder None)
        self._random = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig
        self._number_of_clients = sum([int(isinstance(agent, Client)) for agent in agents])

    def notify_clients(self, data) -> None:
        if not self._number_of_clients:
            return
        for player in self._agents:
            if isinstance(player, Client):
                pass

    def run(self) -> tuple:
        # Wettkampf durchführen

        self._time_start = time()

        #if not self._verbose:
        #    self._progbar.update(0, values=[("Wins", 0), ("Lost", 0), ("Draws", 0)])

        if self._worker < 2:
            for episode in range(self._max_episodes):
                self._update(self._play_episode(episode))
        else:
            pool = Pool(processes=self._worker)
            for episode in range(self._max_episodes):
                pool.apply_async(self._play_episode, args=(episode,), callback=self._update)
            # processes = [pool.apply_async(self._play_episode, args=(episode,)) for episode in range(max_episodes)]
            # for p in processes:
            #     self._update(p.get())
            pool.close()  # verhindert, dass weitere Aufgaben an den Pool gesendet werden
            pool.join()  # warten, bis die Worker-Prozesse beendet sind

        if self._verbose:
            print("\r ")
        #else:
        #    if sum(self._rating) < self._max_episodes:
        #        self._progbar.update(sum(self._rating), finalize=True)  # es wurde früher beendet

        return tuple(self._rating)

    # Diese Methode läuft parallel im eigenen Prozess (im Multiprocessing-Mode)!
    def _play_episode(self, episode: int) -> Optional[tuple]:
        if self._stop_event.is_set():
            return None

        # Agents zurücksetzen
        for agent in self._agents:
            agent.reset()

        # Episode spielen
        pub = self._init_pubs[episode] if self._init_pubs else PublicState()
        privs = self._init_privs[episode] if self._init_privs else (PrivateState(0), PrivateState(1), PrivateState(2), PrivateState(3))
        rounds = 0  # Rundenzähler
        tricks = 0  # Stichzähler
        while pub.score[0] < 1000 and pub.score[1] < 1000:
            # Neue Runde...
            pub.reset()
            pub.shuffle_cards()
            rounds += 1

            # Karten aufnehmen, erst 8 dann alle
            first = self._rand_int(0, 3)  # wählt zufällig eine Zahl zwischen 0 und 3 (inklusiv 3)
            for n in (8, 14):
                for player in range(0, 4):
                    cards = pub.deal_out(player, n)
                    privs[player].take_cards(cards)
                    pub.set_number_of_cards(player, n)
                self.notify_clients("")
                # Tichu ansagen?
                for i in range(0, 4):
                    player = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                    grand = n == 8  # großes Tichu?
                    if not pub.announcements[player] and self._agents[player].announce(pub, privs[player], grand):
                        pub.announce(player, grand)
                        self.notify_clients("")

            # Jetzt müssen die Spieler schupfen.
            schupfed = [None, None, None, None]
            for player in range(0, 4):
                schupfed[player] = privs[player].schupf(self._agents[player].schupf(pub, privs[player]))
                assert privs[player].number_of_cards == 11
                pub.set_number_of_cards(player, 11)
            self.notify_clients("")

            # Die abgegebenen Karten der Mitspieler aufnehmen.
            for player in range(0, 4):
                privs[player].take_schupfed_cards([schupfed[giver][player] for giver in range(0, 4)])
                assert privs[player].number_of_cards == 14
                pub.set_number_of_cards(player, 14)
                if privs[player].has_mahjong:
                    pub.set_start_player(player)  # Startspieler bekannt geben
            self.notify_clients("")

            # Los geht es. Das eigentliche Spiel kann beginnen...
            assert 0 <= pub.current_player <= 3
            while not pub.is_done:
                priv = privs[pub.current_player]
                agent = self._agents[pub.current_player]
                assert pub.number_of_cards[priv.player] == priv.number_of_cards
                assert 0 <= pub.number_of_cards[priv.player] <= 14
                self.notify_clients("")

                # Falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen.
                # Der Hund bleibt aber immer liegen.
                if pub.trick_player == priv.player and pub.trick_figure != FIGURE_DOG:
                    if not pub.double_win and pub.trick_figure == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                        opponent = agent.gift(pub, priv)
                        assert opponent in ((1, 3) if priv.player in (0, 2) else (0, 2))
                    else:
                        opponent = -1
                    pub.clear_trick(opponent)
                    self.notify_clients("")

                # Hat der Spieler noch Karten?
                if pub.number_of_cards[priv.player] > 0:
                    # Falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde, darf Tichu angesagt werden.
                    if pub.number_of_cards[priv.player] == 14 and not pub.announcements[priv.player]:
                        if agent.announce(pub, priv):
                            pub.announce(priv.player)
                            self.notify_clients("")

                    # Kombination auswählen
                    action_space = build_action_space(priv.combinations, pub.trick_figure, pub.wish)
                    combi = agent.combination(pub, priv, action_space)
                    assert pub.number_of_cards[priv.player] == priv.number_of_cards
                    assert combi[1][1] <= pub.number_of_cards[priv.player] <= 14

                    # Kombination ausspielen
                    priv.play(combi)
                    assert priv.number_of_cards == pub.number_of_cards[priv.player] - combi[1][1]
                    pub.play(combi)
                    assert pub.number_of_cards[priv.player] == priv.number_of_cards
                    self.notify_clients("")

                    if combi[1] != FIGURE_PASS:
                        # Spiel vorbei?
                        if pub.is_done:
                            # Spiel ist vorbei; letzten Stich abräumen und fertig!
                            assert pub.trick_player == priv.player
                            if not pub.double_win and pub.trick_figure == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                                opponent = agent.gift(pub, priv)
                                assert opponent in ((1, 3) if priv.player in (0, 2) else (0, 2))
                            else:
                                opponent = -1
                            pub.clear_trick(opponent)
                            self.notify_clients("")
                            break

                        # Falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden.
                        if CARD_MAH in combi[0]:
                            assert pub.wish == 0
                            wish = agent.wish(pub, priv)
                            assert 2 <= wish <= 14
                            pub.set_wish(wish)
                            self.notify_clients("")

                # Nächster Spieler ist an der Reihe
                pub.step()

            # Runde abgeschlossen
            tricks += pub.trick_counter

        # Episode abgeschlossen
        return episode, rounds, pub.score, pub.history, tricks

    # Diese Methode läuft wieder im Hauptprozess!
    def _update(self, result):
        if not result:
            return

        episode, rounds, score, history, tricks = result

        self._seconds = time() - self._time_start
        self._episodes += 1
        self._rounds += rounds
        self._tricks += tricks

        if score[0] > score[1]:
            self._rating[0] += 1
        elif score[0] < score[1]:
            self._rating[1] += 1
        else:
            self._rating[2] += 1

        if self._early_stopping:
            total = self._max_episodes - self._rating[2]  # Unentschieden fällt nicht in die Bewertung
            unplayed = self._max_episodes - sum(self._rating)
            if total > 0 and float(self._rating[0]) / total >= self._win_rate:
                self._stop_event.set()  # die gewünschte Gewinnquote ist sicher erreicht
            elif total > 0 and float(self._rating[0] + unplayed) / total < self._win_rate:
                self._stop_event.set()  # die gewünschte Gewinnquote kann nicht mehr erreicht werden

        if self._capture:
            self._history.append((history, self._rating))

        if self._verbose:
            if self._episodes == 1:
                print("\nEpisode | Runden |    Score    |    Rating   ")
            print(f"\r{(episode + 1):7d}"
                  f" | {rounds:6d}"
                  f" | {score[0]:>5d}/{score[1]:<5d}"
                  f" | {self._rating[0]:>5d}/{self._rating[1]:<5d}")
            seconds_per_episode = self._seconds / self._episodes
            print(f"Restzeit ca. {(self._max_episodes - self._episodes) * seconds_per_episode:6.3f} s", end="")
        #else:
        #    self._progbar.update(sum(self._rating), values=[("Wins", self._rating[0]), ("Lost", self._rating[1]), ("Draws", self._rating[2])])

    def _rand_int(self, low, high):
        # Gibt eine zufällige Ganzzahl zwischen low (inklusiv) und high (inklusiv) zurück
        if not self._random:
            self._random = np.random.RandomState(seed=self._seed)

        return self._random.randint(low, high + 1)

    @staticmethod
    def cpu_count() -> int:
        # Ermittelt die Anzahl verfügbarer CPU-Kerne
        return cpu_count()

    @property
    def seconds(self) -> int:
        """
        Spieldauer insgesamt in Sekunden
        """
        return self._seconds

    @property
    def episodes(self) -> int:
        """
        Anzahl Episoden
        """
        return self._episodes

    @property
    def rounds(self) -> int:
        """
        Anzahl Runden insgesamt über alle Episoden
        """
        return self._rounds

    @property
    def tricks(self) -> int:
        """
        Anzahl Stiche insgesamt über alle Episoden
        """
        return self._tricks

    @property
    def rating(self) -> list:
        # # Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)
        return self._rating

    @property
    def history(self) -> list:
        """
        # Spielverlauf = [ ([(state, probability, action)], reward) ]
        Reward bezieht sich auf Agent0
        Abfragebeispiel:
            for episode, (data, reward) in enumerate(arena.history):
                for state, prob, action in data:
                    print(episode, state, prob, action, reward)
        """
        return self._history
