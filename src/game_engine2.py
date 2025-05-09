"""
Definiert die Spiellogik.
"""

import asyncio
from src.lib.combinations import FIGURE_DRA, FIGURE_DOG, build_action_space, FIGURE_PASS, build_combinations, remove_combinations
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import deck, CARD_MAH
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

        # Kopie des sortiertem Standarddecks - wird jede Runde neu durchgemischt
        self._mixed_deck = list(deck)

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

            # Partie spielen
            while sum(pub.game_score[0]) < 1000 and sum(pub.game_score[1]) < 1000:  # noch nicht game over?
                # Neue Runde...

                # öffentlichen Spielzustand zurücksetzen
                pub.reset_round()

                # privaten Spielzustand zurücksetzen
                for priv in privs:
                    priv._hand = []
                    priv._schupfed = []
                    priv._combination_cache = []
                    priv._partition_cache = []
                    priv._partitions_aborted = True

                # Agents zurücksetzen
                for agent in self._agents:
                    agent.reset_round()

                # Karten mischen
                pub.shuffle_cards()

                # Karten aufnehmen, erst 8 dann alle
                first = self._random.integer(0, 4)  # wählt zufällig eine Zahl zwischen 0 und 3
                for n in (8, 14):
                    # Karten verteilen
                    for player in range(0, 4):
                        cards = pub.deal_out(player, n)
                        priv = privs[player]
                        priv._hand = cards
                        priv._schupfed = []
                        priv._combination_cache = []
                        priv._partition_cache = []
                        pub.set_number_of_cards(player, n)
                    await self.broadcast("")

                    # Tichu ansagen?
                    for i in range(0, 4):
                        player = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                        grand = n == 8  # großes Tichu?
                        if not pub.announcements[player] and self._agents[player].announce(pub, privs[player], grand):
                            pub.announce(player, grand)
                            await self.broadcast("")

                # jetzt müssen die Spieler schupfen
                schupfed = [None, None, None, None]
                for player in range(0, 4):
                    schupfed[player] = privs[player].schupf(self._agents[player].schupf(pub, privs[player]))
                    assert privs[player].number_of_cards == 11
                    pub.set_number_of_cards(player, 11)
                await self.broadcast("")

                # die abgegebenen Karten der Mitspieler aufnehmen
                for player in range(0, 4):
                    privs[player].take_schupfed_cards([schupfed[giver][player] for giver in range(0, 4)])
                    assert privs[player].number_of_cards == 14
                    pub.set_number_of_cards(player, 14)
                    if privs[player].has_mahjong:
                        pub.set_start_player(player)  # Startspieler bekannt geben
                await self.broadcast("")

                # los geht's - das eigentliche Spiel kann beginnen...
                assert 0 <= pub.current_player_index <= 3
                while not pub.is_done:
                    priv = privs[pub.current_player_index]
                    agent = self._agents[pub.current_player_index]
                    assert pub.number_of_cards[priv.player_index] == len(priv._hand)
                    assert 0 <= pub.number_of_cards[priv.player_index] <= 14
                    await self.broadcast("")

                    # falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen
                    if pub.trick_player_index == priv.player_index and pub.trick_figure != FIGURE_DOG:  # der Hund bleibt aber immer liegen
                        if not pub.double_win and pub.trick_figure == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                            opponent = agent.gift(pub, priv)
                            assert opponent in ((1, 3) if priv.player_index in (0, 2) else (0, 2))
                        else:
                            opponent = -1
                        pub.clear_trick(opponent)
                        await self.broadcast("")

                    # hat der Spieler noch Karten?
                    if pub.number_of_cards[priv.player_index] > 0:
                        # falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde, darf Tichu angesagt werden
                        if pub.number_of_cards[priv.player_index] == 14 and not pub.announcements[priv.player_index]:
                            if agent.announce(pub, priv):
                                pub.announce(priv.player_index)
                                await self.broadcast("")

                        # Kombination auswählen
                        if not priv._combination_cache and priv._hand:
                            priv._combination_cache = build_combinations(priv._hand)
                        action_space = build_action_space(priv._combination_cache, pub.trick_figure, pub.wish)
                        combi = agent.combination(pub, priv, action_space)
                        assert pub.number_of_cards[priv.player_index] == len(priv._hand)
                        assert combi[1][1] <= pub.number_of_cards[priv.player_index] <= 14

                        # Kombination ausspielen -  play(combi)
                        if combi[1] != FIGURE_PASS:
                            # Handkarten aktualisieren
                            priv._hand = [card for card in priv._hand if card not in combi[0]]
                            if priv._combination_cache:
                                # das Entfernen der Kombinationen ist im Schnitt ca. 1.25-mal schneller als neu zu berechnen
                                priv._combination_cache = remove_combinations(priv._combination_cache, combi[0])
                            if priv._partition_cache:
                                if priv._partitions_aborted:
                                    # Die Berechnung aller Partitionen wurde abgebrochen, da es zu viele gibt. Daher kann die Liste
                                    # nicht aktualisiert werden, sondern muss neu berechnet werden.
                                    priv._partition_cache = []
                                # das ist schneller, als alle Partitionen erneut zu berechnen
                                priv._partition_cache = remove_partitions(priv.partitions, combi[0])

                        assert len(priv._hand) == pub.number_of_cards[priv.player_index] - combi[1][1]
                        pub.play(combi)
                        assert pub.number_of_cards[priv.player_index] == len(priv._hand)
                        await self.broadcast("")

                        if combi[1] != FIGURE_PASS:
                            # Spiel vorbei?
                            if pub.is_done:
                                # Spiel ist vorbei; letzten Stich abräumen und fertig!
                                assert pub.trick_player_index == priv.player_index
                                if not pub.double_win and pub.trick_figure == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                                    opponent = agent.gift(pub, priv)
                                    assert opponent in ((1, 3) if priv.player_index in (0, 2) else (0, 2))
                                else:
                                    opponent = -1
                                pub.clear_trick(opponent)
                                await self.broadcast("")
                                break

                            # falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden
                            if CARD_MAH in combi[0]:
                                assert pub.wish == 0
                                wish = agent.wish(pub, priv)
                                assert 2 <= wish <= 14
                                pub.set_wish(wish)
                                await self.broadcast("")

                    # nächster Spieler ist an der Reihe
                    pub.step()

            logger.info(f"[{self.table_name}] Partie beendet. Endstand: Team 20: {sum(pub.game_score[0])}, Team 31: {sum(pub.game_score[1])}")
            #await self.broadcast("public_state", pub)

            # Partie abgeschlossen
            return pub

        except asyncio.CancelledError:
            logger.info(f"[{self.table_name}] Spiel-Loop extern abgebrochen.")
            pub.current_phase = "aborted"
            # noinspection PyBroadException
            try:
                await self.broadcast("public_state", pub)
            except Exception:
                pass
        except Exception as e:
            logger.exception(f"[{self.table_name}] Kritischer Fehler im Spiel-Loop: {e}")
            pub.current_phase = "error"
            # noinspection PyBroadException
            try:
                await self.broadcast("public_state", pub)
            except Exception:
                pass
        finally:
            logger.info(f"[{self.table_name}] Spiel-Loop definitiv beendet.")
            self.game_loop_task = None  # Referenz aufheben

        return pub

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
        #f not self._num_clients:  # todo aus Performance-Gründen für die Arena wäre es hier besser, die Anzahl der Clients zu kennen!
        #    return
        if payload is None:
            payload = {}
        for player in self._players:
            if isinstance(player, Client):  
                await player.on_notify(message_type, payload)

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

    def _shuffle_deck(self):
        """
        Mischt das Kartendeck.
        """
        self._random.shuffle(self._mixed_deck)

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
    