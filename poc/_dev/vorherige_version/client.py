import asyncio
import json
from enum import Enum
from json import JSONDecodeError
from src.card_collection import CardCollection
from src.card_combination import CardCombination, CardCombinationType
from src.common.logger import logger
from src.globals import Action, Event
from src.player.player import Player
from typing import Optional
from websockets import WebSocketServerProtocol, ConnectionClosed


class ClientMessageType(Enum):
    # Nachrichten vom Client
    LEAVE = 0    # Spieler verlässt das Spiel
    ACTION = 1   # Spieler fordert Aktion an (verarbeitet die Game-Engine)
    # könnte erweiterte werden mit DEBUG, LOAD, SAVE... (verarbeitet z.B. die Game-Factory)


class ServerMessageType(Enum):
    # Nachrichten vom Server
    EVENT = 0    # Ereignis aufgetreten (wird von der Game-Engine ausgelöst werden)
    # könnte erweiterte werden mit DEBUG_MODE, CHECKPOINT_LOADED, CHECKPOINT_SAVED... (würde von der Game-Factory ausgelöst werden)


class Client(Player):
    # Bildet einen realen Spieler ab
    #
    # Client ist von Player abgeleitet. Das Objekt kommuniziert über die Websocket mit der Gegenstelle (peer).

    def __init__(self, nickname: str, canonical_chair: int, engine, websocket: WebSocketServerProtocol) -> None:
        super().__init__(nickname, canonical_chair, engine)
        self.websocket = websocket
        self.queue = asyncio.Queue()

    # Methoden

    async def message_loop(self) -> None:
        # Verarbeitet so lange Nachrichten von der Websocket, bis die Verbindung abbricht
        #
        # Die Nachrichtenschleife wird im Kontext des Websocket-Handlers aufgerufen. Wenn die Methode verlassen wird,
        # wird die Verbindung mit der Gegenstelle geschlossen, falls diese noch offen sein sollte.

        while True:
            try:
                # auf eine Nachricht warten
                message = await self.websocket.recv()
                try:
                    data = json.loads(message)
                except JSONDecodeError:
                    # der JSON-String ist nicht korrekt formatiert
                    logger.error(f"{self._engine.get_world_name()}, Player {self._nickname}: Invalid Json: {message}")
                    continue

                # Message-Type auslesen
                message_type_name = data.get("type")
                if not hasattr(ClientMessageType, message_type_name):
                    logger.error(f"{self._engine.get_world_name()}, Player {self._nickname}: Invalid message type: {message_type_name}")
                    continue
                message_type: ClientMessageType = getattr(ClientMessageType, message_type_name)

                # Spieler verlässt das Spiel
                if message_type == ClientMessageType.LEAVE:
                    break  # Nachrichtenschleife verlassen (dadurch wird die Verbindung mit der Gegenstelle geschlossen)

                # Spieler fordert Aktion an
                elif message_type == ClientMessageType.ACTION:
                    # Aktion auslesen
                    action_name = data.get("action")
                    if not hasattr(Action, action_name):
                        logger.error(f"{self._engine.get_world_name()}, Player {self._nickname}: Invalid action: {action_name}")
                        continue
                    action: Action = getattr(Action, action_name)

                    # Parameter deserialisieren
                    params = data.get("parameters", {})
                    assert isinstance(params, dict)
                    if "cards" in params:
                        params["cards"] = CardCollection.deserialize(params["cards"])
                    if "combination" in params:
                        params["combination"] = CardCombination.deserialize(params["combination"])

                    # Aktion zwischenspeichern
                    await self.queue.put((action, params))
                    if action in [Action.GRAND, Action.TICHU, Action.BOMB]:
                        # todo sicherstellen, dass der Spieler auch tatsächlich die Aktion durchführen darf
                        self._engine.interrupt(self.canonical_chair)

                # Message-Type übersehen?
                else:
                    assert False, f"message type {message_type} unprocessed"

            except ConnectionClosed:
                logger.debug(f"{self._engine.get_world_name()}, Player {self._nickname}: Connection closed.")
                break

    # noinspection PyMethodMayBeStatic
    def compute_grand(self) -> bool:
        # Trifft die Entscheidung für großes Tichu
        return False

    # noinspection PyMethodMayBeStatic
    def compute_tichu(self) -> bool:
        # Triff die Entscheidung für ein normales Tichu
        return False

    # noinspection PyMethodMayBeStatic
    def compute_schupf(self) -> CardCollection:
        # Wählt drei Tauschkarten
        # if cards.length() != 3:
        #     logger.error(f"{self._world_name}, Player {player.nickname}: 3 cards expected, {cards.length()} received.")
        #     return
        # if any(card not in player.hand for card in cards):
        #     logger.error(
        #         f"{self._world_name}, Player {player.nickname}: At least one card is not in the player's hand: {cards}. Hand: {player.hand}")
        #     return
        return CardCollection(self._hand.items[:3])

    # noinspection PyMethodMayBeStatic
    def compute_wish(self) -> int:
        # Wünscht sich ein Kartenwert (0 == wunschlos, ansonsten zwischen 2 und 14)
        # if wish != 0 and wish < 2 or wish > 14:
        #     logger.error(
        #         f"{self._world_name}, Player {player.nickname}: No wish expected or between 2 and 14, {wish} received.")
        #     return
        return 0

    # noinspection PyMethodMayBeStatic
    def compute_gift(self) -> int:
        # Trifft die Entscheidung, wer den Drachen bekommt (1 oder 3)
        # if recipient not in [1, 3]:
        #     logger.error(
        #         f"{self._world_name}, Player {player.nickname}: Recipient 1 or 3 expected, {recipient} received.")
        #     return
        return 1

    # noinspection PyMethodMayBeStatic
    def compute_play(self) -> Optional[CardCombination]:
        # Wählt eine Kartenkombination zum ausspielen
        # Die Methode kann durch ein Interrupt-Event abgebrochen werden. In dem Fall wird None zurückgegeben.
        # if combi.type == CardCombinationType.NONE:
        #     logger.error(f"{self._world_name}, Player {player.nickname}: It is not a combination: {combi.collection}")
        #     return
        # if any(card not in player.hand for card in combi):
        #     logger.error(
        #         f"{self._world_name}, Player {player.nickname}: At least one card is not in the player's hand: {combi.collection}. Hand: {player.hand}")
        #     return
        combinations = self._get_playable_combinations()
        assert combinations and combinations[0] != CardCombinationType.NONE
        return combinations[0]

    # noinspection PyMethodMayBeStatic
    def compute_pass(self) -> Optional[bool]:
        # Entscheidet, ob gepasst wird
        # Die Methode kann durch ein Interrupt-Event abgebrochen werden. In dem Fall wird None zurückgegeben.
        return False

    # noinspection PyMethodMayBeStatic
    def compute_bomb(self) -> bool:
        # Entscheidet, ob eine Bombe geworfen wird
        return False

    async def _compute_action_async(self) -> Optional[tuple[Action, dict]]:
        assert not self._engine.interrupt_event.is_set()
        done, _pending = await asyncio.wait([self.queue.get(), self._engine.interrupt_event.wait()],  return_when=asyncio.FIRST_COMPLETED)
        if self._engine.interrupt_event.is_set():
            self._engine.reset_interrupt()
            return None
        action, params = done.pop().result()
        return action, params

    def compute_action(self) -> Optional[tuple[Action, dict]]:
        loop = asyncio.get_event_loop()
        # if loop.is_running():
        #     return loop.run_until_complete(self._compute_action_async())
        # else:
        #     return asyncio.run(self._compute_action_async())
        assert loop.is_running(), "Event-Loop is not running"
        return loop.run_until_complete(self._compute_action_async())

    async def send_event(self, event: Event, params: dict=None) -> None:
        # Wird aufgerufen, wenn ein bestimmtes Spielereignis eingetreten ist

        if not self.websocket.open:
            return

        if params is None:
            params = {}

        # Params anreichern mit Werten des Beobachtungsraums, die sich geändert haben

        space = {}

        if event == Event.ERROR:
            # ups, ich hab einen Fehler gemacht
            assert "message" in params and isinstance(params["message"], str)
            space = self._get_observation_space()  # den kompletten Beobachtungsraum hinzufügen, um einen Abgleich vornehmen zu können

        elif event == Event.PLAYER_JOINED:
            # ein Spieler hat sich an den Tisch gesetzt
            assert "chair" in params and isinstance(params["chair"], int)
            chair = params["chair"]
            if chair == 0:  # bin ich es gewesen?
                space = self._get_observation_space()  # zum Abgleich den kompletten Beobachtungsraum mitgeben
            else:
                assert isinstance(chair, int)
                space["players"] = [{}, {}, {}, {}]
                space["players"][chair] = {"nickname": self.get_nickname(chair)}

        elif event == Event.GAME_STARTED:
            # die Partie wurde gestartet (ein Client hat auf Start geklickt)
            space["possible_actions"] = self._get_possible_actions()
            #space["is_running"] = self.is_running()
            space["score"] = self.get_score().serialize()
            #space["is_game_over"] = self.is_game_over()

        elif event == Event.CARDS_DEALT:
            # Karten wurden ausgeteilt
            space["possible_actions"] = self._get_possible_actions()
            space["hand"] = self._hand.serialize()
            space["players"] = [{}, {}, {}, {}]
            for chair in range(4):
                space["players"][chair] = {"number_of_cards": self.get_number_of_cards(chair)}

        elif event == Event.PLAYER_DECLARED:
            # ein Spieler hat ein großes Tichu angesagt bzw. abgelehnt oder ein normales Tichu angesagt
            assert "chair" in params and isinstance(params["chair"], int)
            chair = params["chair"]
            if chair == 0:  # bin ich es gewesen?
                space["possible_actions"] = self._get_possible_actions()
            space["players"] = [{}, {}, {}, {}]
            assert isinstance(chair, int)
            space["players"][chair] = {"declaration": self.get_declaration(chair)}

        elif event == Event.PLAYER_SCHUPFED:
            # ein Spieler hat Tauschkarten abgelegt
            assert "chair" in params and isinstance(params["chair"], int)
            chair = params["chair"]
            if chair == 0:  # bin ich es gewesen?
                space["possible_actions"] = self._get_possible_actions()
                space["hand"] = self._hand.serialize()
                space["outgoing_schupfed_cards"] = self._outgoing_schupfed_cards.serialize()
            space["players"] = [{}, {}, {}, {}]
            assert isinstance(chair, int)
            space["players"][chair] = {
                "number_of_cards": self.get_number_of_cards(chair),
                "has_schupfed": self.has_schupfed(chair)
            }

        elif event == Event.SCHUPF_DISTRIBUTED:
            # die Tauschkarten wurden verteilt
            space["possible_actions"] = self._get_possible_actions()
            space["hand"] = self._hand.serialize()
            space["incoming_schupfed_cards"] = self._incoming_schupfed_cards.serialize()
            space["players"] = [{}, {}, {}, {}]
            for chair in range(4):
                space["players"][chair] = {"number_of_cards": self.get_number_of_cards(chair)}
            space["start_chair"] = self.get_start_chair()

        elif event == Event.CARD_WISHED:
            # ein Kartenwert wurde sich gewünscht
            #assert "chair" in params and isinstance(params["chair"], int)
            space["possible_actions"] = self._get_possible_actions()
            space["wish"] = self.get_wish()

        elif event == Event.WISH_FULFILLED:
            # der Wunsch wurde erfüllt
            space["wish"] = self.get_wish()

        elif event == Event.DRAGON_GIVEN_AWAY:
            # der Drache wurde verschenkt
            #assert "chair" in params and isinstance(params["chair"], int)
            space["possible_actions"] = self._get_possible_actions()
            space["gift_recipient"] = self.get_gift_recipient()

        elif event == Event.PLAYER_PLAYED:
            # ein Spieler hat Karten ausgespielt
            assert "chair" in params and isinstance(params["chair"], int)
            chair = params["chair"]
            space["possible_actions"] = self._get_possible_actions()
            if chair == 0:  # bin ich es gewesen?
                space["hand"] = self._hand.serialize()
            space["players"] = [{}, {}, {}, {}]
            assert isinstance(chair, int)
            space["players"][chair] = {
                "number_of_cards": self.get_number_of_cards(chair),
            }
            space["current_chair"] = self.get_current_chair()
            space["wish"] = self.get_wish()
            space["trick"] = self.get_trick().serialize()
            space["winner"] = self.get_winner()
            space["hidden_cards"] = self.get_hidden_cards().serialize()

        elif event == Event.PLAYER_PASSED:
            # ein Spieler hat gepasst
            assert "chair" in params and isinstance(params["chair"], int)
            space["possible_actions"] = self._get_possible_actions()
            space["current_chair"] = self.get_current_chair()
            space["trick"] = self.get_trick().serialize()

        elif event == Event.BOMB_PENDING:
            # ausstehende Bombe
            space["possible_actions"] = self._get_possible_actions()
            space["current_chair"] = self.get_current_chair()

        elif event == Event.PLAYER_TOOK:
            # ein Spieler hat den Stich kassiert
            assert "chair" in params and isinstance(params["chair"], int)
            chair = params["chair"]
            space["possible_actions"] = self._get_possible_actions()
            space["players"] = [{}, {}, {}, {}]
            assert isinstance(chair, int)
            space["players"][chair]["points"] = self.get_points(chair)
            space["trick"] = self.get_trick().serialize()

        elif event == Event.ROUND_OVER:
            # die Runde ist beendet
            space = self._get_observation_space()  # den kompletten Beobachtungsraum hinzufügen, da sich bis auf Nickname alles geändert hat

        elif event == Event.GAME_OVER:
            # die Partie wurde beendet
            space["possible_actions"] = self._get_possible_actions()
            #space["is_running"] = self.is_running()
            #space["is_game_over"] = self.is_game_over()

        else:
            # Event übersehen?
            assert False, f"{event} unprocessed"

        if "possible_actions" in space:
            space["possible_actions"] = [action.name for action in space["possible_actions"]]

        params["space"] = space

        try:
            await self._send(json.dumps({"type": ServerMessageType.EVENT.name, "event": event.name, "parameters": params}))
        except TypeError as e:
            logger.error(f"{self._engine.get_world_name()}, Player {self._nickname}: The event could not be serialized: {e}")

    # Privates

    async def _send(self, message: str):
        # Sendet eine Nachricht über die Websocket an den Benutzer
        try:
            await self.websocket.send(message)
        except ConnectionClosed:
            logger.warning(f"{self._engine.get_world_name()}, Player {self._nickname}: Connection closed, message could not be sent: {message}")


    def _get_observation_space(self) -> dict:
        # Gibt den Beobachtungsraum als Dictionary zurück

        players = [{} for _ in range(4)]
        for relative_chair in range(4):
            players[relative_chair] = {
                "nickname": self.get_nickname(relative_chair),
                "declaration": self.get_declaration(relative_chair),
                "number_of_cards": self.get_number_of_cards(relative_chair),
                "has_schupfed": self.has_schupfed(relative_chair),
                "points": self.get_points(relative_chair),
            }

        return {
            # Identification
            "world_name": self.get_world_name(),
            "canonical_chair": self._canonical_chair,

            # Secret State Properties
            "possible_actions": self._get_possible_actions(),
            "hand": self._hand.serialize(),
            "outgoing_schupfed_cards": self._outgoing_schupfed_cards.serialize(),
            "incoming_schupfed_cards": self._incoming_schupfed_cards.serialize(),

            # Public State Properties
            "players": players,
            #"is_running": self.is_running(),  # Action.START not in possible_actions
            "start_chair": self.get_start_chair(),
            "current_chair": self.get_current_chair(),
            "wish": self.get_wish(),
            "gift_recipient": self.get_gift_recipient(),
            "trick": self.get_trick().serialize(),
            "hidden_cards": self.get_hidden_cards().serialize(),
            "winner": self.get_winner(),
            "loser": self.get_loser(),
            "score": self.get_score().serialize(),
            #"is_round_over": self.is_round_over(),  # loser >= 0
            #"is_game_over": self.is_game_over(),  # any(total >= 1000 for total in score.total())
        }

    def _get_possible_actions(self) -> list[Action]:
        # Ermittelt die möglichen Aktionen
        actions: list[Action] = []
        if not self._engine.is_running:  # Partie läuft noch nicht
            actions.append(Action.START)  # → Spieler darf neues Spiel starten
        else:  # Partie läuft (und noch kein Game Over)
            number_of_cards = self._hand.length()
            if self._outgoing_schupfed_cards.is_empty(): # Spieler hat noch nicht geschupft
                if number_of_cards == 8:  # es wurden die ersten 8 Karten verteilt
                    if self._declaration == -1:  # Spieler hat noch keine Entscheidung für ein großes Tichu getroffen
                        actions.append(Action.GRAND)  # → Spieler muss eine Entscheidung für großes Tichu treffen
                else:  # es wurden alle Karten verteilt
                    #assert number_of_cards == 14
                    actions.append(Action.SCHUPF)  # → Spieler muss Tauschkarten ablegen
                    if self._declaration == 0 and not self._engine.has_anyone_schupfed():  # Spieler hat noch kein Tichu gerufen und noch niemand hat geschupft
                        actions.append(Action.TICHU)  # → Spieler darf Tichu ansagen
            elif not self._incoming_schupfed_cards.is_empty():  # die Tauschkarten wurden verteilt
                trick = self._engine.trick
                history = self._engine.history
                if number_of_cards == 14 and self._declaration == 0:  # Spieler hat noch 14 Karten und kein Tichu gerufen
                    actions.append(Action.TICHU)  # → Spieler darf Tichu ansagen
                if self._engine.wish == -1 and trick.get_rank() > 0.0 and trick.get_last_combination().collection.has_mahjong():  # kein Wunsch geäußert und MahJong liegt im Stich
                    if self._canonical_chair == trick.get_owner():
                        actions.append(Action.WISH)  # → Spieler muss den Wunsch aussprechen
                elif self._engine.gift_recipient == -1 and not history.is_empty() and history[-1].get_last_combination().is_dragon():  # Stich durch den Drachen gewonnen
                    if self._canonical_chair == history[-1].get_owner():
                        actions.append(Action.GIFT)  # → Spieler muss den Drachen verschenken
                elif number_of_cards > 0:  # Spieler hat Handkarten
                    if self._engine.current_chair == self._canonical_chair:  # Spieler ist am Zug
                        if self._is_bombing or self._has_playable_combination():
                            actions.append(Action.PLAY)  # → Spieler kann Karten spielen (bzw. muss die angekündigte Bombe werfen)
                        if trick.get_rank() > 0.0 and not self._is_bombing and not self.can_fulfill_wish():  # kein Anspiel, muss keine Bombe werfen, kein Wunsch zu erfüllen
                            actions.append(Action.PASS)  # → Spieler darf passen
                    else:  # Spieler ist nicht am Zug
                        if trick.get_rank() > 0.0 and not self._is_bombing and self.can_bomb():  # kein Anspiel, muss keine Bombe werfen, hat aber eine spielbare Bombe
                            actions.append(Action.BOMB)  # → Spieler darf Zugrecht für eine Bombe anfordern
        return actions
