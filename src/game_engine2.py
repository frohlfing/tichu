"""
Definiert die Spiellogik.
"""

import asyncio
from src.lib.combinations import FIGURE_DRA, FIGURE_DOG, build_action_space, FIGURE_PASS, build_combinations, remove_combinations, CombinationType, FIGURE_PHO, FIGURE_MAH, SINGLE
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import deck, CARD_MAH, Card, is_wish_in, sum_card_points, CARD_DRA, other_cards
from src.lib.partitions import remove_partitions
from src.players.agent import Agent
from src.players.client import Client
from src.players.player import Player
from src.players.random_agent import RandomAgent
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import List, Optional

class GameEngine:
    """
    Steuert den Spielablauf eines Tisches.

    :ivar game_loop_task: Der asyncio Task, der die Hauptspielschleife ausführt.
    :ivar interrupt_event: globales Interrupt.
    """

    def __init__(self, table_name: str, default_agents: Optional[List[Agent]] = None, seed: Optional[int] = None):
        """
        Initialisiert eine neue GameEngine für einen gegebenen Tischnamen.

        :param table_name: Der Name des Spieltisches (eindeutiger Identifikator).
        :param default_agents: (Optional) Liste mit 4 Agenten als Standard/Fallback. Wenn None, werden RandomAgent-Instanzen verwendet.
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        :raises ValueError: Wenn Parameter nicht ok sind.
        """
        # Name dieses Spieltisches
        name_stripped = table_name.strip() if table_name else ""
        if not name_stripped:
            raise ValueError("Name des Spieltisches darf nicht leer sein.")
        self._table_name: str = name_stripped

        # Default-Agenten initialisieren
        if default_agents:
            if len(default_agents) != 4 or any(not isinstance(player, Agent) for player in default_agents):
                raise ValueError(f"`default_agents` muss genau 4 Agenten auflisten.")
            self._default_agents: List[Agent] = list(default_agents)  # Kopie erstellen (immutable machen)
        else:
            self._default_agents: List[Agent] = [RandomAgent(name=f"RandomAgent_{i + 1}") for i in range(4)]

        # Sitzplätze der Reihe nach vergeben (0 bis 3)
        for i, default_agent in enumerate(self._default_agents):
            default_agent.player_index = i

        agent_names = ", ".join(default_agent.name for default_agent in self._default_agents)
        logger.debug(f"[{self.table_name}] Agenten initialisiert: {agent_names}.")

        # aktuelle Spielerliste
        self._players: List[Player] = list(self._default_agents)

        # Referenz auf den Hintergrund-Task `_run_game_loop`
        self.game_loop_task: Optional[asyncio.Task] = None

        # Interrupt-Event
        self.interrupt_event: asyncio.Event = asyncio.Event()
        self._interrupt_player_index: Optional[int] = None
        self._interrupt_reason: Optional[str] = None

        # Zufallsgenerator, geeignet für Multiprocessing
        self._random = Random(seed)

        logger.info(f"GameEngine für Tisch '{table_name}' erstellt.")

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser Instanz.

        Bricht laufende Tasks ab und ruft dann die `cleanup`-Funktion aller Player-Instanzen auf.
        """
        logger.info(f"Bereinige Tisch '{self._table_name}'...")

        # breche den Haupt-Spiel-Loop Task ab, falls er läuft.
        if self.game_loop_task and not self.game_loop_task.done():
            logger.debug(f"Tisch '{self._table_name}': Breche Spiel-Loop Task ab.")
            self.game_loop_task.cancel()
            try:
                # Warte kurz darauf, dass der Task auf den Abbruch reagiert.
                await asyncio.wait_for(self.game_loop_task, timeout=1.0)
            except asyncio.CancelledError:
                logger.debug(f"Tisch '{self._table_name}': Spiel-Loop Task bestätigt abgebrochen.")
            except asyncio.TimeoutError:
                logger.warning(f"Tisch '{self._table_name}': Timeout beim Warten auf Abbruch des Spiel-Loop Tasks.")
            except Exception as e:
                 logger.error(f"Tisch '{self._table_name}': Fehler beim Warten auf abgebrochenen Spiel-Loop Task: {e}")
        self.game_loop_task = None # Referenz entfernen

        # alle Spieler-Instanzen bereinigen (parallel)
        await asyncio.gather(*[asyncio.create_task(p.cleanup()) for p in self._players], return_exceptions=True)

        logger.info(f"Bereinigung des Tisches '{self._table_name}' beendet.")

    # ------------------------------------------------------
    # Partie spielen
    # ------------------------------------------------------

    async def start_game(self):
        """
        Startet den Hintergrund-Task `_run_game_loop`
        """
        if self.game_loop_task and not self.game_loop_task.done():
            logger.warning(f"Tisch '{self.table_name}': Versuch, neue Partie zu starten, obwohl bereits eine läuft.")
            return

        logger.info(f"[{self.table_name}] Starte Hintergrund-Task für eine neue Partie.")
        self.game_loop_task = asyncio.create_task(self.run_game_loop(), name=f"Game Loop '{self.table_name}'")

    async def run_game_loop(self, pub: Optional[PublicState] = None, privs: Optional[List[PrivateState]] = None, _break_time = 5) -> PublicState|None:
        """
        Steuert den Spielablauf einer Partie.
        
        todo PlayerInterruptError muss hier im jedem Turn abgefangen werden.
         Nennen wir den Spieler, der den Interrupt anfordert, "Interrupter".  
         Wenn Interrupter seine beabsichtigte Aktion (Bombe werfen oder Tichu ansagen) nicht durchführen kann oder darf, kriegt er nur eine Fehlermeldung zurück.
         Ansonsten wird das Interrupt-Event gesetzt, so das der Spieler, der gerade am Zug ist, die Entscheidungsfindung abbricht.
         Der Interrupter wird aufgefordert, die Aktion durchzuführen. Danach wird die Runde wie gehabt fortgesetzt.

        :param pub: (Optional) Öffentlicher Spielzustand (sichtbar für alle Spieler am Tisch). Änderungen extern möglich, aber nicht vorgesehen.
        :param privs: (Optional) Private Spielzustände (für jeden Spieler einen). Änderungen extern möglich, aber nicht vorgesehen.
        :param _break_time: Pause in Sekunden zwischen den Runden.
        :return: Der öffentliche Spielzustand.
        :raises ValueError: Wenn Parameter nicht ok sind.
        """
        try:
            logger.info(f"[{self.table_name}] Starte neue Partie...")

            # öffentlicher Spielzustand initialisieren
            if pub:
                logger.debug(f"[{self.table_name}] Verwende übergebenen PublicState.")
            else:
                pub = PublicState()
            pub.table_name = self.table_name
            pub.player_names = [p.name for p in self._players]
            pub.current_phase = "playing"

            # privaten Spielzustände initialisieren
            if privs:
                if len(privs) != 4:
                    raise ValueError(f"Die Anzahl der Einträge in `privs` muss genau 4 sein.")
                logger.debug(f"[{self.table_name}] Verwende übergebene PrivateStates.")
            else:
                privs = [PrivateState() for _ in range(4)]
            for i, priv in enumerate(privs):
                priv.player_index = i

            # Kopie des sortiertem Standarddecks - wird jede Runde neu durchgemischt
            mixed_deck = list(deck)
            
            # aus Performance-Gründen für die Arena wollen wir so wenig wie möglich await aufrufen, daher ermitteln wir, ob überhautpt Clients im Spiel sind
            # todo testen, ob das wirklich relevant ist
            clients_joined = any(isinstance(p, Client) for p in self._players)
            
            # Partie spielen
            while sum(pub.game_score[0]) < 1000 and sum(pub.game_score[1]) < 1000:  # noch nicht game over?
                # Neue Runde...

                # öffentlichen Spielzustand zurücksetzen
                self.reset_public_state_for_round(pub)

                # privaten Spielzustand zurücksetzen
                for priv in privs:
                    self.reset_private_state_for_round(priv)

                # Agents zurücksetzen
                for agent in self._players:
                    agent.reset_round()

                # Karten mischen
                self.shuffle_cards(mixed_deck)

                # Karten aufnehmen, erst 8 dann alle
                first = self._random.integer(0, 4)  # wählt zufällig eine Zahl zwischen 0 und 3
                for n in (8, 14):
                    # Karten verteilen
                    for player in range(0, 4):
                        cards = self.deal_out(mixed_deck, player, n)
                        self.take_cards(privs[player], cards)
                        self.set_number_of_cards(pub, player, n)
                    if clients_joined: 
                        await self.broadcast("")

                    # Tichu ansagen?
                    for i in range(0, 4):
                        player = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                        grand = n == 8  # großes Tichu?
                        if not pub.announcements[player] and await self._players[player].announce(pub, privs[player], grand):
                            self.announce(pub, player, grand)
                            if clients_joined: 
                                await self.broadcast("")

                # jetzt müssen die Spieler schupfen
                schupfed = [None, None, None, None]
                for player in range(0, 4):
                    schupfed[player] = self.schupf(privs[player], await self._players[player].schupf(pub, privs[player]))
                    assert len(privs[player].hand_cards) == 11
                    self.set_number_of_cards(pub, player, 11)
                if clients_joined: 
                    await self.broadcast("")

                # die abgegebenen Karten der Mitspieler aufnehmen
                for player in range(0, 4):
                    self.take_schupfed_cards(privs[player], [schupfed[giver][player] for giver in range(0, 4)])
                    assert len(privs[player].hand_cards) == 14
                    self.set_number_of_cards(pub, player, 14)
                    if CARD_MAH in privs[player].hand_cards:
                        self.set_start_player(pub, player)  # Startspieler bekannt geben
                if clients_joined: 
                    await self.broadcast("")

                # los geht's - das eigentliche Spiel kann beginnen...
                assert 0 <= pub.current_turn_index <= 3
                while not pub.is_round_over:
                    priv = privs[pub.current_turn_index]
                    agent = self._players[pub.current_turn_index]
                    assert pub.num_hand_cards[priv.player_index] == len(priv.hand_cards)
                    assert 0 <= pub.num_hand_cards[priv.player_index] <= 14
                    if clients_joined: 
                        await self.broadcast("")

                    # falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen
                    if pub.trick_owner_index == priv.player_index and pub.trick_combination != FIGURE_DOG:  # der Hund bleibt aber immer liegen
                        if not pub.double_victory and pub.trick_combination == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                            opponent = await agent.gift(pub, priv)
                            assert opponent in ((1, 3) if priv.player_index in (0, 2) else (0, 2))
                        else:
                            opponent = -1
                        self.clear_trick(pub, opponent)
                        if clients_joined: 
                            await self.broadcast("")

                    # hat der Spieler noch Karten?
                    if pub.num_hand_cards[priv.player_index] > 0:
                        # falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde, darf Tichu angesagt werden
                        if pub.num_hand_cards[priv.player_index] == 14 and not pub.announcements[priv.player_index]:
                            if await agent.announce(pub, priv):
                                self.announce(pub, priv.player_index)
                                if clients_joined: 
                                    await self.broadcast("")

                        # Kombination auswählen
                        if not priv._combination_cache and priv.hand_cards:
                            priv._combination_cache = build_combinations(priv.hand_cards)
                        action_space = build_action_space(priv._combination_cache, pub.trick_combination, pub.wish_value)
                        combi = await agent.combination(pub, priv, action_space)
                        assert pub.num_hand_cards[priv.player_index] == len(priv.hand_cards)
                        assert combi[1][1] <= pub.num_hand_cards[priv.player_index] <= 14

                        # Kombination ausspielen
                        self.play_priv(priv, combi)
                        assert len(priv.hand_cards) == pub.num_hand_cards[priv.player_index] - combi[1][1]
                        self.play_pub(pub, combi)
                        assert pub.num_hand_cards[priv.player_index] == len(priv.hand_cards)
                        if clients_joined: 
                            await self.broadcast("")

                        if combi[1] != FIGURE_PASS:
                            # Spiel vorbei?
                            if pub.is_round_over:
                                # Spiel ist vorbei; letzten Stich abräumen und fertig!
                                assert pub.trick_owner_index == priv.player_index
                                if not pub.double_victory and pub.trick_combination == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                                    opponent = await agent.gift(pub, priv)
                                    assert opponent in ((1, 3) if priv.player_index in (0, 2) else (0, 2))
                                else:
                                    opponent = -1
                                self.clear_trick(pub, opponent)
                                if clients_joined: 
                                    await self.broadcast("")
                                break

                            # falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden
                            if CARD_MAH in combi[0]:
                                assert pub.wish_value == 0
                                wish = await agent.wish(pub, priv)
                                assert 2 <= wish <= 14
                                self.set_wish(pub, wish)
                                if clients_joined: 
                                    await self.broadcast("")

                    # nächster Spieler ist an der Reihe
                    self.turn(pub)

            logger.info(f"[{self.table_name}] Partie beendet. Endstand: Team 20: {sum(pub.game_score[0])}, Team 31: {sum(pub.game_score[1])}")
            if clients_joined:
                await self.broadcast_state(pub, privs)

            # Partie abgeschlossen
            return pub

        except asyncio.CancelledError:
            logger.info(f"[{self.table_name}] Spiel-Loop extern abgebrochen.")
            pub.current_phase = "aborted"
            # noinspection PyBroadException
            try:
                await self.broadcast_state(pub, privs)
            except Exception:
                pass
        except Exception as e:
            logger.exception(f"[{self.table_name}] Kritischer Fehler im Spiel-Loop: {e}")
            pub.current_phase = "error"
            # noinspection PyBroadException
            try:
                await self.broadcast_state(pub, privs)
            except Exception:
                pass
        finally:
            logger.info(f"[{self.table_name}] Spiel-Loop definitiv beendet.")
            self.game_loop_task = None  # Referenz aufheben

        return pub

    # ------------------------------------------------------
    # PublicState modifizieren
    # ------------------------------------------------------
    
    @staticmethod
    def reset_public_state_for_round(pub: PublicState):  # pragma: no cover
        """
        Spielzustand für eine neue Runde zurücksetzen
        :param pub: Öffentlicher Spielzustand
        """
        pub.current_turn_index = -1
        pub.start_player_index = -1
        pub.num_hand_cards = [0, 0, 0, 0]
        pub.played_cards = []
        pub.announcements = [0, 0, 0, 0]
        pub.wish_value = 0
        pub.dragon_recipient = -1
        pub.trick_owner_index = -1
        pub.trick_combination = (CombinationType.PASS, 0, 0)
        pub.trick_points = 0
        pub.round_history = []
        pub.points = [0, 0, 0, 0]
        pub.winner_index = -1
        pub.loser_index = -1
        pub.is_round_over = False
        pub.double_victory = False
    
    # @staticmethod
    # def number_of_players(pub: PublicState) -> int:
    #     """
    #     Anzahl Spieler, die noch im Rennen sind.
    #     :param pub: Öffentlicher Spielzustand
    #     """
    #     return sum(1 for n in pub.num_hand_cards if n > 0)

    def shuffle_cards(self, cards: List[Card]) -> None:
        """
        Karten mischen
        :param cards: Kartendeck
        """
        self._random.shuffle(cards)

    @staticmethod
    def deal_out(cards: List[Card], player_index: int, n: int) -> List[Card]:
        """
        Karten austeilen
        :param cards: Kartendeck
        :param player_index: Index des Spielers (0 bis 3)
        :param n: Anzahl Karten (8 oder 14)
        :return: Die ausgeteilten Karten, absteigend sortiert.
        """
        offset = player_index * 14
        return sorted(cards[offset:offset + n], reverse=True)

    @staticmethod
    def set_start_player(pub: PublicState, player_index: int):  # pragma: no cover
        """
        Startspieler bekannt geben
        :param pub: Öffentlicher Spielzustand
        :param player_index: Index des Spielers (0 bis 3)
        """
        assert not pub.is_round_over
        assert 0 <= player_index <= 3
        assert pub.start_player_index == -1
        pub.start_player_index = player_index
        assert pub.current_turn_index == -1
        pub.current_turn_index = player_index

    @staticmethod
    def set_number_of_cards(pub: PublicState, player_index: int, n: int):  # pragma: no cover
        """
        Anzahl der Handkarten angeben
        :param pub: Öffentlicher Spielzustand
        :param player_index: Der Index des Spielers. 
        :param n: Anzahl Handkarten des Spielers
        """
        assert not pub.is_round_over
        assert 0 <= player_index <= 3
        assert (pub.num_hand_cards[player_index] == 0 and n == 8) or \
               (pub.num_hand_cards[player_index] == 8 and n == 14) or \
               (pub.num_hand_cards[player_index] == 14 and n == 11) or \
               (pub.num_hand_cards[player_index] == 11 and n == 14)
        pub.num_hand_cards[player_index] = n

    @staticmethod
    def announce(pub: PublicState, player_index: int, grand: bool = False):  # pragma: no cover
        """
        Tichu ansagen
        :param pub: Öffentlicher Spielzustand
        :param player_index: Der Index des Spielers, der Tichu angesagt hat. 
        :param grand: True, wenn Grand Tichu angesagt wurde.
        """
        assert not pub.is_round_over
        assert 0 <= player_index <= 3
        assert pub.announcements[player_index] == 0
        assert (grand and pub.num_hand_cards[player_index] == 8 and pub.start_player_index == -1) or (not grand and pub.num_hand_cards[player_index] == 14)
        pub.announcements[player_index] = 2 if grand else 1

    @staticmethod
    def play_pub(pub: PublicState, combi: tuple):
        """
        Kombination spielen
        :param pub: Öffentlicher Spielzustand
        :param combi: Ausgewählte Kombination (Karten, (Typ, Länge, Wert)) 
        """
        assert not pub.is_round_over
        assert pub.current_turn_index != -1
        pub.round_history.append((pub.current_turn_index, combi))  # todo: in Stiche unterteilen
        if combi[1] == FIGURE_PASS:
            return

        # Gespielte Karten merken
        assert not set(combi[0]).intersection(pub.played_cards)  # darf keine Schnittmenge bilden
        pub.played_cards += combi[0]

        # Anzahl Handkarten aktualisieren
        assert combi[1][1] == len(combi[0])
        assert pub.num_hand_cards[pub.current_turn_index] >= combi[1][1]
        pub.num_hand_cards[pub.current_turn_index] -= combi[1][1]

        # Wunsch erfüllt?
        assert pub.wish_value == 0 or -2 >= pub.wish_value >= -14 or 2 <= pub.wish_value <= 14
        if pub.wish_value > 0 and is_wish_in(pub.wish_value, combi[0]):
            assert CARD_MAH in pub.played_cards
            pub.wish_value = -pub.wish_value

        # Stich aktualisieren
        pub.trick_owner_index = pub.current_turn_index
        if combi[1] == FIGURE_PHO:
            assert pub.trick_combination == (0, 0, 0) or pub.trick_combination[0] == SINGLE
            assert pub.trick_combination != FIGURE_DRA  # Phönix auf Drache geht nicht
            # Der Phönix ist eigentlich um 0.5 größer als der Stich, aber gleichsetzen geht auch (Anspiel == 1).
            if pub.trick_combination[2] == 0:  # Anspiel oder Hund?
                pub.trick_combination = FIGURE_MAH
        else:
            pub.trick_combination = combi[1]
        pub.trick_points += sum_card_points(combi[0])
        assert -25 <= pub.trick_points <= 125

        # Runde beendet?
        if pub.num_hand_cards[pub.current_turn_index] == 0:
            number_of_players = sum(1 for n in pub.num_hand_cards if n > 0)  # Anzahl Spieler, die noch im Rennen sind
            assert 1 <= number_of_players <= 3
            if number_of_players == 3:
                assert pub.winner_index == -1
                pub.winner_index = pub.current_turn_index
            elif number_of_players == 2:
                assert 0 <= pub.winner_index <= 3
                if (pub.current_turn_index + 2) % 4 == pub.winner_index:  # Doppelsieg?
                    pub.is_round_over = True
                    pub.double_victory = True
            elif number_of_players == 1:
                pub.is_round_over = True
                for player in range(0, 4):
                    if pub.num_hand_cards[player] > 0:
                        assert pub.loser_index == -1
                        pub.loser_index = player
                        break

    @staticmethod
    def set_wish(pub: PublicState, wish: int):  # pragma: no cover
        """
        Wunsch äußern
        :param pub: Öffentlicher Spielzustand
        :param wish: Der gewünschte Kartenwert. 
        """
        assert not pub.is_round_over
        assert 2 <= wish <= 14
        assert CARD_MAH in pub.played_cards
        assert pub.wish_value == 0
        pub.wish_value = wish

    @staticmethod
    def clear_trick(pub: PublicState, opponent: int = -1):
        """
        Stich abräumen
        :param pub: Öffentlicher Spielzustand
        :param opponent: opponent: Nummer des Gegners, falls der Stich verschenkt werden muss, ansonsten -1 
        """
        # Sicherstellen, dass die Funktion nicht zweimal aufgerufen wird, sondern nur, wenn ein Stich abgeräumt werden kann.
        assert pub.trick_owner_index != -1
        assert pub.trick_owner_index == pub.current_turn_index
        assert pub.trick_combination != (0, 0, 0)

        if pub.double_victory:
            # Doppelsieg! Die Karten müssen nicht gezählt werden.
            assert pub.is_round_over
            assert 0 <= pub.winner_index <= 3
            assert sum(1 for n in pub.num_hand_cards if n > 0) == 2
            pub.points = [0, 0, 0, 0]
            pub.points[pub.winner_index] = 200
        else:
            # Stich abräumen
            if opponent != -1:
                # Verschenken
                assert opponent in ((1, 3) if pub.trick_owner_index in (0, 2) else (0, 2))
                assert CARD_DRA in pub.played_cards
                assert pub.dragon_recipient == -1
                pub.dragon_recipient = opponent
                pub.points[opponent] += pub.trick_points
                assert -25 <= pub.points[opponent] <= 125
            else:
                # Selbst kassieren
                pub.points[pub.trick_owner_index] += pub.trick_points
                assert -25 <= pub.points[pub.trick_owner_index] <= 125

            # Runde vorbei?
            if pub.is_round_over:
                # Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
                assert 0 <= pub.loser_index <= 3
                leftover_points = 100 - sum_card_points(pub.played_cards)
                assert leftover_points == sum_card_points(other_cards(pub.played_cards))
                pub.points[(pub.loser_index + 1) % 4] += leftover_points
                # Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
                assert pub.winner_index >= 0
                pub.points[pub.winner_index] += pub.points[pub.loser_index]
                pub.points[pub.loser_index] = 0
                assert sum(pub.points) == 100
                assert -25 <= pub.points[0] <= 125
                assert -25 <= pub.points[1] <= 125
                assert -25 <= pub.points[2] <= 125
                assert -25 <= pub.points[3] <= 125

        pub.trick_owner_index = -1
        pub.trick_combination = (CombinationType.PASS, 0, 0)
        pub.trick_points = 0
        pub.trick_counter += 1

        # Runde vorbei? Dann Bonus-Punkte berechnen und Gesamt-Punktestand aktualisieren
        if pub.is_round_over:
            # Bonus für Tichu-Ansage
            for player in range(0, 4):
                if pub.announcements[player]:
                    if player == pub.winner_index:
                        pub.points[player] += 100 * pub.announcements[player]
                    else:
                        pub.points[player] -= 100 * pub.announcements[player]

            # Score (Gesamt-Punktestand der aktuellen Episode)
            pub.game_score[0] += pub.points[0] + pub.points[2]
            pub.game_score[1] += pub.points[1] + pub.points[3]
            pub.round_counter += 1

    @staticmethod
    def turn(pub: PublicState):
        """
        Nächsten Spieler auswählen        
        :param pub: Öffentlicher Spielzustand
        """
        assert not pub.is_round_over
        assert 0 <= pub.current_turn_index <= 3
        if pub.trick_combination == FIGURE_DOG and pub.trick_owner_index == pub.current_turn_index:
            pub.current_turn_index = (pub.current_turn_index + 2) % 4
        else:
            pub.current_turn_index = (pub.current_turn_index + 1) % 4

    # ------------------------------------------------------
    # PrivateState modifizieren
    # ------------------------------------------------------
    
    @staticmethod
    def reset_private_state_for_round(priv: PrivateState):  # pragma: no cover
        """
        Alles für eine neue Runde zurücksetzen.
        
        :param priv: Privater Spielzustand
        """
        priv.hand_cards = []
        priv.given_schupf_cards = []
        priv._combination_cache = []  # todo priv hat kein Cache
        priv._partition_cache = []  # todo priv hat kein Cache
        priv._partitions_aborted = True  # todo priv hat das Feld nicht

    @staticmethod
    def take_cards(priv: PrivateState, cards: List[Card]):
        """
        Handkarten für eine neue Runde aufnehmen
        
        :param priv: Privater Spielzustand
        :param cards: Karten, die aufgenommen werden sollen (8 oder 14 Karten).
        """
        n = len(cards)
        assert n == 8 or n == 14
        priv.hand_cards = cards
        priv.given_schupf_cards = []
        priv._combination_cache = []  # todo priv hat kein Cache
        priv._partition_cache = []  # todo priv hat kein Cache

    @staticmethod
    def schupf(priv: PrivateState, schupfed: list[tuple]) -> list[tuple]:
        """ 
        Tauschkarten an die Mitspieler abgeben
        
        :param priv: Privater Spielzustand
        :param schupfed: Tauschkarte für rechten Gegner, Karte für Partner, Karte für linken Gegner
        :return: Tauschkarten für Spieler 0 bis 3, kanonische Form (der eigene Spieler kriegt nichts, also None)
        """
        # Karten abgeben
        assert len(schupfed) == 3
        priv._schupfed = schupfed
        assert len(priv.hand_cards) == 14
        priv._hand = [card for card in priv.hand_cards if card not in priv.given_schupf_cards]
        priv._combination_cache = []  # todo priv hat kein Cache
        priv._partition_cache = []  # todo priv hat kein Cache
        assert len(priv.hand_cards) == 11
        cards = [None, None, None, None]
        for i in range(0, 3):
            cards[(priv.player_index + i + 1) % 4] = priv.given_schupf_cards[i]
        # todo: priv.received_schupf_cards aktualisieren
        return cards

    @staticmethod
    def take_schupfed_cards(priv: PrivateState, cards: list[tuple]):
        """
        Tauschkarten der Mitspieler aufnehmen
        
        :param priv: Privater Spielzustand
        :param cards: Tauschkarten der Spieler 0 bis 3 (None steht für keine Karte; eigener Spieler)
        """
        assert len(priv.hand_cards) == 11
        assert not set(cards).intersection(priv.hand_cards)  # darf keine Schnittmenge bilden
        priv.hand_cards += [card for card in cards if card is not None]
        priv.hand_cards.sort(reverse=True)
        priv._combination_cache = []  # todo priv hat kein Cache
        priv._partition_cache = []  # todo priv hat kein Cache
        assert len(priv.hand_cards) == 14

    @staticmethod
    def play_priv(priv: PrivateState, combi: tuple):
        """
        Kombination ausspielen (oder passen)
        
        :param priv: Privater Spielzustand
        :param combi: Ausgewählte Kombination (Karten, (Typ, Länge, Wert)) 
        """
        if combi[1] != FIGURE_PASS:
            # Handkarten aktualisieren
            priv.hand_cards = [card for card in priv.hand_cards if card not in combi[0]]
            if priv._combination_cache: # todo priv hat kein Cache
                # das Entfernen der Kombinationen ist im Schnitt ca. 1.25-mal schneller als neu zu berechnen
                priv._combination_cache = remove_combinations(priv._combination_cache, combi[0])  # todo priv hat kein Cache
            if priv._partition_cache: # todo priv hat kein Cache
                if priv._partitions_aborted: # todo priv hat kein Cache
                    # Die Berechnung aller Partitionen wurde abgebrochen, da es zu viele gibt. Daher kann die Liste
                    # nicht aktualisiert werden, sondern muss neu berechnet werden.
                    priv._partition_cache = []
                # das ist schneller, als alle Partitionen erneut zu berechnen
                priv._partition_cache = remove_partitions(priv.partitions, combi[0])  # todo priv hat kein Cache

    # ------------------------------------------------------
    # Client-spezifisches
    # ------------------------------------------------------

    async def join_client(self, client: Client) -> bool:
        """
        Lässt den Client mitspielen.
        :param client: Der Client, der mitspielen möchte.
        :return: True, wenn der Client einen Sitzplatz bekommen hat, ansonsten False.
        """
        # Sitzplatz suchen, der von der KI besetzt ist
        available_index = -1
        for i, p in enumerate(self._players):
            if not isinstance(p, Client):
                available_index = i
                break
        if available_index == -1:
            return False
        self._players[available_index] = client
        client.player_index = available_index
        return True

    async def leave_client(self, client: Client) -> None:
        """
        Lässt den Client gehen.
        :param client: Der Client, der gehen will.
        :raise ValueError: Wenn der Clients nicht gefunden werden kann.
        """
        index = client.player_index
        if index < 0 or index > 3:
            raise ValueError(f"Der Index des Spielers {client.name} ist nicht korrekt: {index}")
        if self._players[index].session != client.session:
            raise ValueError(f"Der Spielers {client.name} kann den Tisch {self._table_name} nicht verlassen, er sitz dort nicht.")
        self._players[index] = self._default_agents[index]
        client.player_index = -1

    async def broadcast(self, message_type: str, payload: Optional[dict] = None) -> None:
        """
        Sendet eine Nachricht an alle Clients.

        :param message_type: Der Typ der Nachricht.
        :param payload: (Optional) Die Nutzdaten der Nachricht.
        """
        if payload is None:
            payload = {}
        for player in self._players:
            if isinstance(player, Client):  
                await player.on_notify(message_type, payload)

    async def broadcast_state(self, pub: PublicState, privs: List[PrivateState]) -> None:
        """
        Sendet den aktuellen Spielzustand an alle Clients.

        :param pub: Öffentlicher Spielzustand
        :param privs: Private Spielzustände 
        """
        for player in self._players:
            if isinstance(player, Client):  
                await player.on_notify("state", {"pub": pub, "priv": privs[player.player_index]})

    async def on_interrupt(self, client: Client, reason: str):
        """
        Wird aufgerufen, wenn ein Client einen Interrupt anfordert (er meldet sich und sagt "Halt").

        :param client: Der anfragende Client.
        :param reason: Grund für den Interrupt ("bomb" oder "tichu").
        """
        logger.info(f"Tisch '{self.table_name}': Spieler {client.name} fordert Interrupt an: '{reason}'")

        # Prüfungen
        if self._interrupt_reason:
            logger.warning(f"Tisch '{self.table_name}': Interrupt von Spieler {client.name} ignoriert (anderer Interrupt läuft bereits).")
            await client.on_notify("error", {"message": "Ein anderer Interrupt wird gerade bearbeitet. Bitte warte."})
            return

        # todo darf der Spieler das jetzt tun?
        # if not ok:
        #   return

        # Sperre setzen
        self._interrupt_reason = True
        self._interrupt_player_index = client.player_index
        try:
            # Signalisiere den wartenden Tasks, dass Tichu angesagt wurde
            self.interrupt_event.set()
        except Exception as e:
            logger.exception(f"Tisch '{self.table_name}': Fehler bei Interrupt-Verarbeitung für Spieler {client.name}: {e}")
            await client.on_notify("error", {"message": "Interner Fehler bei Interrupt-Verarbeitung."})
        finally:
            # todo hier noch nicht die Sperre aufrufen. Das muss in run_game_loop passieren!
            # Sperre aufheben
            self._interrupt_reason = False
            self._interrupt_player_index = None
            logger.debug(f"Interrupt-Verarbeitung für Spieler {client.name} beendet.")

    # ------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------

    def get_player_by_session(self, session: str) -> Optional[Player]:
        """
        Gibt den Spieler anhand der Session zurück.

        :param session: Die Session des Spielers.
        :return: Die Player-Instanz falls die Session existiert, sonst None.
        """
        for p in self._players:
            if p.session == session:
                return p
        return None

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def table_name(self) -> str:
        """Der Name des Spieltisches (eindeutiger Identifikator)."""
        return self._table_name

    @property
    def players(self) -> List[Player]:
        return self._players # Rückgabe der Liste (Änderungen extern möglich, aber nicht vorgesehen)
    