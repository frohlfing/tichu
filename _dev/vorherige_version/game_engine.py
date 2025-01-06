import asyncio
import random
from typing import Optional

from src.card_collection import CardCollection
from src.card_combination import CardCombinationType
from src.common.logger import logger
from src.globals import Event
from src.history import History
from src.player.agent import Agent
from src.player.client import Client
from src.player.player import Player
from src.score import Score
from src.trick import Trick
from src.turn import Turn


class GameEngine:
    # Spiellogik (mutable)
    #
    # Die Sitzplatznummern sind in der kanonischen Form (Normalform) angegeben.

    def __init__(self, world_name: str, agent_factory: callable, seed: int = None) -> None:
        # Constructor

        # Name der Welt
        assert world_name.strip() != ""
        self._world_name = world_name

        # Zufallsgenerator
        self._seed: int = seed # Initialwert für Zufallsgenerator (Integer > 0 oder None)
        self._random: Optional[random.Random] = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig
        #self._random_np: Optional[np.random.RandomState] = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig

        # Public State Properties
        self._is_running = False  # Partie läuft (wurde gestartet und noch kein Game Over)
        self._current_chair: int = -1  # Spieler der am Zug ist (-1 == niemand, ansonsten zw. 0 und 3)
        self._wish: int = 0  # Unerfüllter Wunsch (-1 == kein Wunsch geäußert, 0 == wunschlos, -14 bis -2 bereits erfüllt, ansonsten ein Kartenwert zw. 2 und 14)
        self._gift_recipient: int = -1  # Spieler, der den Drachen bekommen hat (-1 == niemand, ansonsten zw. 0 und 3)
        self._trick = Trick()  # Offener Stich
        self._history = History()  # Alle abgeschlossenen Stiche
        self._score = Score()  # Ergebnisse jeder Runde (Team 20 gegen Team 31)

        # Kartendeck
        self._deck = CardCollection.create_deck()

        # Spieler
        self._clients: list[Client] = []
        self._agents: list[Agent] = agent_factory(self)
        self._players: list[Player] = self._agents.copy()

        # Interrupt-Event
        self.interrupt_event = asyncio.Event()

        logger.debug(f"{self._world_name}: Engine is created")

    def __del__(self):
        ## Destructor
        logger.debug(f"{self._world_name}: Engine is destroyed")

    def __str__(self) -> str:
        # Object representation as a String
        return self._world_name

    # Eigenschaften

    @property
    def world_name(self) -> str:
        # Betitelt die Welt
        return self._world_name

    @property
    def is_running(self) -> bool:
        # Partie läuft (wurde gestartet und noch kein Game Over)
        return self._is_running

    @property
    def current_chair(self) -> int:
        # Spieler der am Zug ist (-1 == niemand, ansonsten zw. 0 und 3)
        return self._current_chair

    @property
    def wish(self) -> int:
        # Unerfüllter Wunsch (-1 == kein Wunsch geäußert, 0 == wunschlos, -14 bis -2 bereits erfüllt, ansonsten ein Kartenwert zw. 2 und 14)
        return self._wish

    @property
    def gift_recipient(self) -> int:
        # Spieler, der den Drachen bekommen hat (-1 == niemand, ansonsten zw. 0 und 3)
        return self._gift_recipient

    @property
    def trick(self) -> Trick:
        # Kopie auf den offenen Stich (immutable)
        return self._trick.duplicate()

    @property
    def history(self) -> History:
        # Kopie auf alle abgeschlossenen Stiche (immutable)
        return self._history.duplicate()

    @property
    def score(self) -> Score:
        # Kopie auf die Ergebnisliste (immutable)
        return self._score.duplicate()

    # Methoden

    async def replace_player(self, player: Player) -> None:
        # Ersetzt den Spieler am gegebenen Sitzplatz

        assert player.get_world_name() == self._world_name
        chair = player.canonical_chair
        old_player = self._players[chair]
        self._players[chair] = player
        player.assign_secret_state(old_player)

        if isinstance(old_player, Agent):
            assert old_player in self._agents
            self._agents.remove(old_player)
        else:
            assert isinstance(old_player, Client) and old_player in self._clients
            self._clients.remove(old_player)

        if isinstance(player, Agent):
            assert player not in self._agents
            self._agents.append(player)
        else:
            assert isinstance(player, Client) and player not in self._clients
            self._clients.append(player)

        del old_player
        logger.info(f"{self._world_name}: Player {player.nickname} joined")

    def reset_game(self) -> None:
        # Startet eine neue Partie
        self._is_running = True
        self._score.clear()
        self.reset_round()
        #await self.notify_clients(Event.GAME_STARTED)

    def reset_round(self) -> None:
        # Setzt den State für eine neue Runde zurück (alle State Properties bis auf _is_running und _score)
        self._current_chair = -1
        self._wish = 0
        self._trick.clear()
        self._history.clear()
        for p in self._players:
            p.clear()

    def _initialize_random(self):
        if not self._random:
            self._random = random.Random(self._seed)

    def _rand_int(self, low, high) -> int:
        # Gibt eine zufällige Ganzzahl im Bereich von low (einschließlich) bis high (ausschließlich) zurück
        self._initialize_random()
        return self._random.randint(low, high)

    def play_round(self) -> None:
        # Spielt eine Runde

        # für eine neue Runde alles zurücksetzen
        self.reset_round()

        # Karten mischen
        self._deck.shuffle()

        # die ersten 8 Karten verteilen
        self._deal_cards(8)
        #await self.notify_clients(Event.CARDS_DEALT)

        # alle Spieler fragen, ob sie ein großes Tichu ansagen möchten
        first = self._rand_int(0, 3)  # wir fangen zufällig mit einem Spieler an
        for i in range(0, 4):
            chair = (first + i) % 4
            player = self._players[chair]
            decision = player.compute_grand()
            player.set_grand(decision)
            #await self.notify_clients(Event.PLAYER_DECLARED, {"chair": player.canonical_chair})

        # die restlichen Karten verteilen
        self._deal_cards(14)
        #await self.notify_clients(Event.CARDS_DEALT)

        # alle Spieler fragen, ob sie ein normales Tichu ansagen möchten
        for i in range(0, 4):
            chair = (first + i) % 4
            player = self._players[chair]
            decision = player.compute_tichu()
            if decision:
                player.set_tichu()
                #await self.notify_clients(Event.PLAYER_DECLARED, {"chair": player.canonical_chair})

        # jetzt müssen die Spieler schupfen
        for player in self._players:
            cards = player.compute_schupf()
            #assert cards.length() == 3
            player.set_outgoing_schupfed_cards(cards)
            #await self.notify_clients(Event.PLAYER_SCHUPFED, {"chair": player.canonical_chair})

        # wenn alle geschupft haben, Tauschkarten verteilen
        self._distribute_schupfed_card()
        #await self.notify_clients(Event.SCHUPF_DISTRIBUTED)

        # Startspieler steht nun fest
        for player in self._players:
            if player.hand.has_mahjong():
                self.set_current_chair(player.canonical_chair)

        # los geht's, die Spieler spielen ihre Karten aus...
        while True:
            player = self._players[self._current_chair]

            #if self.interrupt_event.is_set():  # todo wie viel Zeit nimmt das in Anspruch?
            #    self.reset_interrupt()

            if self._trick.get_rank() > 0.0 and not player.is_bombing and not player.can_fulfill_wish():
                # kein Anspiel, muss keine Bombe werfen, kann Wunsch nicht erfüllen (oder kein Wunsch offen) → darf passen
                passed = player.compute_pass()
                if passed is None:
                    continue  # es wurde ein Interrupt ausgelöst (jemand möchte eine Bombe werfen oder Tichu rufen)
            else:
                passed = False  # darf nicht passen

            if passed:
                # Spieler hat gepasst
                self._trick.append(Turn(player.canonical_chair))
                # nächsten Spieler ermitteln
                assert any(self.get_player(chair).is_playing() for chair in range(4))
                while True:
                    self._current_chair = (self.current_chair + 1) % 4
                    if self.trick.get_owner() == self.current_chair:
                        # Spieler schaut auf seinen letzten Zug
                        if self._gift_recipient == -1 and self._trick.get_last_combination().is_dragon():
                            # Stich durch den Drachen gewonnen → Stich verschenken
                            owner = self._players[self._trick.get_owner()]
                            recipient = owner.get_canonical_chair(owner.compute_gift())
                            self.set_gift_recipient(recipient)
                            # await self.notify_clients(Event.DRAGON_GIVEN_AWAY)
                        # Stich kassieren
                        self._history.append(self.trick)
                        self._trick.clear()
                        # await self.notify_clients(Event.PLAYER_TOOK)
                    if self.get_player(self.current_chair).is_playing():
                        break
                # await self.notify_clients(Event.PLAYER_PASSED, {"chair": player.canonical_chair})
            else:
                # Spieler hat nicht gepasst bzw. darf nicht passen, muss also eine Kombination ausspielen
                combi = player.compute_play()
                if combi is None:
                    continue  # es wurde ein Interrupt ausgelöst (jemand möchte eine Bombe werfen oder Tichu rufen)

                #  Ist die Kombination spielbar?
                if self._trick.get_rank() > 0.0:
                    # Stich ist offen und es ist kein Hund
                    trick_rank = self.trick.get_rank()
                    trick_type = self.get_trick_type()
                    if not ((combi.type == trick_type and combi.rank > trick_rank) or
                            (combi.type.value >= CardCombinationType.BOMB_04.value and combi.type.value > trick_type.value)):
                        logger.error(f"{self._world_name}, Player {player.nickname}: The combination is less than the trick: {combi}. Trick: {self.trick.get_last_combination().collection}")
                        continue  # die Kombination ist nicht spielbar

                # Karten auf den Stich legen
                self._trick.append(Turn(player.canonical_chair, combi))
                n = player.hand.length()
                player.play(combi)
                assert n == player.hand.length() + combi.collection.length()
                #await self.notify_clients(Event.PLAYER_PLAYED, {"chair": player.canonical_chair})

                # Runde vorbei?
                if self.is_round_over():
                    break

                if self._wish == -1 and combi.collection.has_mahjong():
                    # kein Wunsch geäußert und MahJong wurde ausgespielt → Wunsch äußern
                    wish = player.compute_wish()
                    self.set_wish(wish)
                    # await self.notify_clients(Event.CARD_WISHED)

                # nächsten Spieler ermitteln
                assert any(self.get_player(chair).is_playing() for chair in range(4))
                if combi.is_dog():
                    self._current_chair = (self.current_chair + 1) % 4
                while True:
                    self._current_chair = (self.current_chair + 1) % 4
                    if self.get_player(self.current_chair).is_playing():
                        break

            # if self._trick.get_rank() > 0.0 and not player.is_bombing and player.can_bomb():
            #     # kein Anspiel, muss keine Bombe werfen, hat aber eine spielbare Bombe
            #     if player.compute_bomb():
            #         # Zugrecht für eine Bombe anfordern
            #         self.set_current_chair(player.canonical_chair)
            #         #await self.notify_clients(Event.BOMB_PENDING)

        # Runde ist beendet → Punkte zählen
        loser = self.get_loser()
        winner = self.get_winner()
        if loser == 31:
            points = [100, 0, 100, 0]  # Doppelsieg für Team 20
        elif loser == 20:
            points = [0, 100, 0, 100]  # Doppelsieg für Team 31
        else:
            if self._gift_recipient == -1 and self._trick.get_last_combination().is_dragon():
                # letzten Stich durch den Drachen gewonnen → Stich verschenken
                owner = self._players[self._trick.get_owner()]
                recipient = owner.get_canonical_chair(owner.compute_gift())
                self.set_gift_recipient(recipient)
                # await self.notify_clients(Event.DRAGON_GIVEN_AWAY)
            assert self._gift_recipient != -1
            assert self._wish != -1 or self._trick.get_last_combination().collection.has_mahjong()
            # letzten Stich kassieren
            self._history.append(self.trick)
            self._trick.clear()
            # await self.notify_clients(Event.PLAYER_TOOK)
            # Stiche auswerten
            points = [self.get_points(chair) for chair in range(4)]
            points[winner] += points[loser]  # der Loser gibt seine Stiche an den Gewinner
            points[loser] = 0
            points[(loser + 1) % 4] += sum(card.points for card in self.get_player(loser).hand)  # der Loser gibt seine Handkarten an die Gegenpartei
            assert sum(points) == 100

        # Bonus für Tichu-Ansage auswerten
        # for chair in range(4):
        #     declaration = self._players[chair].declaration
        #     assert declaration != -1
        #     if winner == chair:
        #         points[winner] += 100 * declaration
        #     else:
        #         points[winner] -= 100 * declaration

        # Score aktualisieren
        self._score.append((points[2] + points[0], points[3] + points[1]))
        #print(self._score)
        # await self.notify_clients(Event.ROUND_OVER)

    def interrupt(self, chair: int):
        # Setze das Interrupt-Event, um den Denkprozess des Agenten zu unterbrechen
        assert 0 <= chair <= 3
        assert self.get_player(chair).is_playing()
        self._current_chair = chair
        self.interrupt_event.set()

    def reset_interrupt(self):
        # Setze das Interrupt-Event zurück
        self.interrupt_event.clear()

    def get_world_name(self) -> str:
        # Betitelt die Welt
        return self.world_name

    def get_nickname(self, chair: int) -> str:
        # Nennt den Namen des gegebenen Spielers
        assert 0 <= chair <= 3
        return self.get_player(chair).nickname

    def get_declaration(self, chair: int) -> int:
        # Gibt Auskunft über die Tichu-Ansage des gegebenen Spielers
        # (-1 == noch keine Entscheidung für großes Tichu, 0 == keine Ansage, 1 == kleines Tichu, 2 == großes Tichu)
        assert 0 <= chair <= 3
        return self.get_player(chair).declaration

    def is_playing(self, chair: int) -> bool:
        # Ermittelt, ob der gegebene Spieler noch spielt
        assert 0 <= chair <= 3
        return self.get_player(chair).is_playing()

    def get_number_of_cards(self, chair: int) -> int:
        # Ermittelt die Anzahl der Handkarten des gegebenen Spielers
        assert 0 <= chair <= 3
        return self.get_player(chair).get_number_of_cards()

    def has_schupfed(self, chair: int) -> bool:
        # Gibt an, ob der gegebene Spieler drei Karten zum Tauschen abgegeben hat
        assert 0 <= chair <= 3
        return self.get_player(chair).has_schupfed()

    def has_anyone_schupfed(self) -> bool:
        # Gibt an, ob irgendjemand schon Tauschkarten abgegeben hat
        return any(self.get_player(chair).has_schupfed() for chair in range(4))

    def schupf_distributed(self) -> bool:
        # Gibt an, ob die Tauschkarten verteilt wurden
        # es wird an alle Spieler gleichzeitig verteilt, daher reicht es, bei einem zu prüfen
        return self.get_player(0).schupf_distributed()

    def is_bombing(self, chair: int) -> bool:
        # Ermittelt, ob der Spieler das Zugrecht erhalten hat, um eine Bombe werfen zu können
        assert 0 <= chair <= 3
        return self.get_player(chair).is_bombing

    def get_start_chair(self) -> int:
        # Ermittelt den Spieler, der den Mah-Jong hat oder hatte
        # (-1, falls das Schupfen noch nicht beendet ist, sonst zw. 0 und 3)
        if not self.schupf_distributed():
            return -1
        chair = self._history.get_start_chair()  # wer hat den ersten Zug gemacht?
        if chair == -1:  # keiner?
            # den Mah-Jong in den Händen suchen
            for chair in range(4):
                if self.get_player(chair).hand.has_mahjong():
                    return chair
        return chair

    def get_trick_type(self) -> CardCombinationType:
        # Gibt den Typ des Stichs an
        return self._trick.get_type()

    def get_trick_rank(self) -> float:
        # Gibt den Rang des Stichs an
        return self._trick.get_rank()

    def get_played_cards(self) -> CardCollection:
        # Zeigt die bereits gespielten Karten (Anzahl zw. 0 und 55)
        cards = self._history.get_cards()
        cards.extend(self._trick.get_cards())
        return cards

    def get_unplayed_cards(self) -> CardCollection:
        # Zeigt die noch nicht gespielten Karten (Anzahl zw. 1 und 56; Summe aller Hände)
        cards = CardCollection()
        for chair in range(4):
            cards.extend(self.get_player(chair).hand)
        return cards

    def get_hidden_cards(self, chair: int) -> CardCollection:
        # Zeigt die noch nicht gespielten Karten ohne die eigenen Handkarten, also die Handkarten der Mitspieler (Anzahl zw. 1 und 56)
        assert 0 <= chair <= 3
        cards = CardCollection()
        for chair_ in range(4):
            if chair_ != chair:
                cards.extend(self.get_player(chair_).hand)
        return cards

    def get_points(self, chair: int) -> int:
        # Zählt die Punkte, die der gegebene Spieler kassiert hat (zw. -25 und 125)
        assert 0 <= chair <= 3
        return self._history.get_points(chair, self._gift_recipient)

    def get_winner(self) -> int:
        # Ermittelt den Spieler, der zuerst fertig wurde (-1 == alle Spieler sind noch dabei, ansonsten zw. 0 und 3)

        number_of_cards = [self.get_number_of_cards(chair) for chair in range(4)]
        zeros = number_of_cards.count(0)  # Anzahl der Spieler, die keine Karten mehr haben
        if zeros == 0:
            # noch niemand ist fertig
            return -1

        elif zeros == 1:
            # genau einer ist fertig
            return number_of_cards.index(0)

        # mehrere sind fertig
        for trick in reversed(self._history.items + [self._trick]):
            for index in range(trick.length() - 1, -1, -1):
                assert trick[index] and trick[index][0]
                turn = trick[index][0]
                number_of_cards[turn.chair] += turn.combination.collection.length()
                assert number_of_cards[turn.chair] <= 14  # sicherstellen, dass es nicht mehr als 14 Karten werden
                if number_of_cards.count(0) == 1:
                    return number_of_cards.index(0)
        return -1

    def get_loser(self) -> int:
        # Ermittelt den Spieler, der als letzter Handkarten hat (oder bei Doppelsieg das Team, das verloren hat)
        # (-1 == Spiel läuft noch, 20 == Spieler 0 und 2 haben verloren, 31 == Spieler 1 und 3 haben verloren, ansonsten zw. 0 und 3)
        chairs = [chair for chair in range(4) if self.get_player(chair).is_playing()]  # noch im Spiel
        n = len(chairs)
        if n == 1:
            return chairs[0]
        if n == 2:
            if chairs[0] == 0 and chairs[1] == 2:
                return 20  # Doppelsieg für Team 31
            elif chairs[0] == 1 and chairs[1] == 3:
                return 31  # Doppelsieg für Team 20
        return -1

    def get_total_score(self) -> tuple[int, int]:
        # Rechnet das Gesamtergebnis der Partie aus (Team 20 gegen Team 31)
        return self._score.total()

    def is_round_over(self) -> bool:
        # Ermittelt, ob die Runde beendet ist
        return self.get_loser() >= 0

    def is_game_over(self) -> bool:
        # Ermittelt, ob die Partie beendet ist
        #print(self._score.total())
        return any(total >= 1000 for total in self._score.total())

    # def duplicate(self) -> 'PublicState':
    #     # Kopiert den Status
    #     state = PublicState(self._engine)
    #     state._is_running = self._is_running
    #     state._current_chair = self._current_chair
    #     state._declarations = self._declarations.copy()
    #     state._wish = self._wish
    #     state._trick = self._trick.duplicate()
    #     state._history = self._history.duplicate()
    #     state._score = self._score.duplicate()
    #     return state

    # Setter

    def stop_game(self):
        # hält das Spiel an
        self._is_running = False

    # def set_current_chair(self, value: int) -> None:
    #     assert -1 <= value <= 3
    #     self._current_chair = value

    def set_wish(self, value: int) -> None:
        # (-1 == kein Wunsch geäußert, 0 == wunschlos, -14 bis -2 bereits erfüllt, ansonsten ein Kartenwert zw. 2 und 14)
        assert (value == 0) or (2 <= abs(value) <= 14)
        self._wish = value

    def set_wish_fulfilled(self) -> None:
        assert 2 <= abs(self._wish) <= 14
        self._wish *= -1

    def set_gift_recipient(self, recipient: int) -> None:
        self._gift_recipient = recipient

    def set_current_chair(self, chair: int) -> None:
        assert 0 <= chair <= 3
        assert self.get_player(chair).is_playing()
        self._current_chair = chair

    def get_player(self, chair: int) -> Player:
        # Gibt eine Referenz auf das Player-Objekt am gegebenen Sitzplatz zurück
        assert -1 <= chair <= 3
        return self._players[chair]

    # Privates

    def _deal_cards(self, number_of_cards: int) -> None:
        # Karten austeilen
        assert number_of_cards in [8, 14]
        for player in self._players:
            start_index = player.canonical_chair * 14
            player.set_hand(self._deck.slice(start_index, start_index + number_of_cards))

    def _distribute_schupfed_card(self) -> None:
        # Tauschkarten verteilen
        # 0: 01, 02, 03
        # 1: 12, 13, 10
        # 2: 23, 20, 21
        # 3: 30, 31, 32
        cards = [player.outgoing_schupfed_cards for player in self._players]
        self._players[0].set_incoming_schupfed_cards(CardCollection([cards[1][2], cards[2][1], cards[3][0]]))
        self._players[1].set_incoming_schupfed_cards(CardCollection([cards[2][2], cards[3][1], cards[0][0]]))
        self._players[2].set_incoming_schupfed_cards(CardCollection([cards[3][2], cards[0][1], cards[1][0]]))
        self._players[3].set_incoming_schupfed_cards(CardCollection([cards[0][2], cards[1][1], cards[2][0]]))

    async def notify_clients(self, event: Event, params: dict = None) -> None:
        # Benachrichtigt alle Clients über die Statusänderung
        for player in self._clients:
            await player.send_event(event, params)
