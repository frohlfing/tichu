from src import config
from multiprocessing import Pool, Manager, cpu_count
from poc.arena_sync.engine import GameEngine
from poc.arena_sync.agent import Agent
from poc.arena_sync.state import PublicState, PrivateState
from time import time
from typing import Optional


class Arena:
    # In der Arena können Agenten gegeneinander antreten.

    def __init__(self, agents: list[Agent], max_episodes: int, verbose: bool = False,
                 early_stopping: bool = False, win_rate: float = config.ARENA_WIN_RATE,
                 pubs: list[PublicState] = None, privs: list[list[PrivateState]] = None,
                 worker: int = config.ARENA_WORKER,
                 seed: int = None):
        assert len(agents) == 4
        self._agents = agents  # Agent 0, Agent 1, Agent 2 und Agent 3
        self._max_episodes = max_episodes  # Maximale Anzahl zu spielende Partien
        self._verbose = verbose  # Spielverlauf ausführlich anzeigen
        self._early_stopping = early_stopping  # Wettkampf abbrechen, wenn die Gewinnquote erreicht wurde oder nicht mehr erreicht werden kann
        self._win_rate = win_rate  # gewünschte Gewinnquote WIN / (WIN + LOST); nur relevant, wenn early_stopping gesetzt ist
        self._stop_event = Manager().Event()
        self._init_pubs = pubs  # wenn gesetzt, werden diese öffentlichen Spielzustände zum Start einer neuen Epoche genommen
        self._init_privs = privs  # wenn gesetzt, werden diese privaten Spielzustände zum Start einer neuen Epoche genommen
        self._worker = worker  # wenn größer 1, werden die Episode in entsprechend vielen Prozessen parallel ausgeführt
        #self._progbar = Progbar(max_episodes, stateful_metrics=["Wins", "Lost", "Draws"])
        self._time_start = None  # Zeitstempel zu Beginn der ersten Partie.
        self._seconds: int = 0  # Spieldauer insgesamt in Sekunden
        self._episodes: int = 0  # Anzahl Episoden
        self._rounds: int = 0  # Rundenzähler über alle Episoden
        self._tricks: int = 0  # Stichzähler über alle Episoden
        self._rating = [0, 0, 0]  # Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)
        self._number_of_clients = 0
        self._engine = GameEngine(self._agents, seed)

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

        pub = self._engine.play_episode(
            self._init_pubs[episode] if self._init_pubs else None,
            self._init_privs[episode] if self._init_privs else None,
        )

        return episode, pub

    # Diese Methode läuft wieder im Hauptprozess!
    def _update(self, result):
        if not result:
            return

        episode: int
        pub: PublicState
        episode, pub = result

        self._seconds = time() - self._time_start
        self._episodes += 1
        self._tricks += pub.trick_counter
        self._rounds += pub.round_counter

        if pub.score[0] > pub.score[1]:
            self._rating[0] += 1
        elif pub.score[0] < pub.score[1]:
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

        if self._verbose:
            if self._episodes == 1:
                print("\nEpisode | Runden |    Score    |    Rating   ")
            print(f"\r{(episode + 1):7d}"
                  f" | {pub.round_counter:6d}"
                  f" | {pub.score[0]:>5d}/{pub.score[1]:<5d}"
                  f" | {self._rating[0]:>5d}/{self._rating[1]:<5d}")
            seconds_per_episode = self._seconds / self._episodes
            print(f"Restzeit ca. {(self._max_episodes - self._episodes) * seconds_per_episode:6.3f} s", end="")
        #else:
        #    self._progbar.update(sum(self._rating), values=[("Wins", self._rating[0]), ("Lost", self._rating[1]), ("Draws", self._rating[2])])

    @staticmethod
    def cpu_count() -> int:
        """
        Ermittelt die Anzahl verfügbarer CPU-Kerne
        """
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
        """
        Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)
        """
        return self._rating
