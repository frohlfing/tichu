"""
Replay-Simulator für die Tichu-Datenbank
"""

__all__ =  "replay_simulator"

import os

from src import config
from src.lib.bsw.database import GameEntity
from src.lib.cards import Cards, CARD_MAH, sum_card_points, is_wish_in
from src.lib.combinations import Combination, CombinationType, get_trick_combination
from src.public_state import PublicState
from src.private_state import PrivateState
from typing import Tuple, Generator
import io


def replay_simulator(game: GameEntity) -> Generator[Tuple[PublicState, PrivateState, Tuple[Cards, Combination]]]:
    """
    Spielt eine auf der Brettspielwelt gespielte Partie nach und gibt jeden Entscheidungspunkt für das Ausspielen der Karten zurück.

    :param game: Die Rundendaten einer Partie
    :return: Ein Generator, der den öffentlichen Spielzustand, den privaten Spielzustand und die ausgeführte Aktion liefert.
    """

    # Spielzustand initialisieren
    pub = PublicState(table_name=f"BSW Replay {game.id}", player_names=[p.name for p in game.players], is_running=True)
    privs = [PrivateState(player_index=i) for i in range(4)]

    # Partie spielen
    for r in game.rounds:
        # Neue Runde...

        # Status für eine neue Runde zurücksetzen
        pub.reset_round()
        for priv in privs:
            priv.reset_round()

        # 8 Karten aufnehmen
        for player_index in range(4):
            pub.count_hand_cards[player_index] = 8
            privs[player_index].hand_cards = r.start_hands[player_index][:8]

        # Möchte der Spieler ein großes Tichu ansagen?
        for player_index in range(4):
            priv = privs[player_index]
            announcement = r.tichu_positions[player_index] == -2
            # todo Entscheidungspunkt für "announce_grand_tichu" ausliefern
            #  yield pub, priv, announcement
            #  Überlegung:
            #  In der Projektdoku steht: "Laut offiziellem Regelwerk kann ein einfaches Tichu schon vor und während des Schupfens angesagt werden.
            #  Fairerweise müssen dann aber alle Spieler die Möglichkeit haben, ihre Schupfkarten noch einmal zu wählen.
            #  Aber das ist offiziell nicht geregelt und auch lästig für alle. Daher die Regel: Einfaches Tichu erst nach dem Schupfen."
            #  Folge: Diese Fälle im Datensatz als neuen "Fehler ANNOUNCEMENT_PREMATURE" definieren und überspringen.
            #  Aber dieser Fall ist noch nicht definitiv entschieden.
            #  Neuer Gedanke: ANNOUNCEMENT_PREMATURE sollte auch zutreffen, wenn jemand Tichu ansagt und danach passt.
            #  Das bringt nichts, er hätte noch warten können! Oder bringt es doch was, was ich nicht sehe?
            if announcement:
                pub.announcements[player_index] = 2

        # Die restlichen Karten aufnehmen
        for player_index in range(4):
            pub.count_hand_cards[player_index] = 14
            privs[player_index].hand_cards = r.start_hands[player_index]

        # Falls noch nichts angesagt wurde, darf ein einfaches Tichu angesagt werden.
        for player_index in range(4):
            priv = privs[player_index]
            if not pub.announcements[player_index]:
                announcement = r.tichu_positions[player_index] == -1
                # todo Entscheidungspunkt für "announce_tichu" ausliefern
                #  yield pub, priv, announcement
                if announcement:
                    pub.announcements[player_index] = 1

        # Schupfen (Tauschkarten abgeben)
        for player_index in range(4):
            priv = privs[player_index]
            schupf_cards = r.schupf_hands[player_index]
            # todo Entscheidungspunkt für "schupf" ausliefern
            #  yield pub, priv, (schupf_cards[0], schupf_cards[1], schupf_cards[2])
            pub.count_hand_cards[player_index] = 11
            priv.given_schupf_cards = schupf_cards[0], schupf_cards[1], schupf_cards[2]
            priv.hand_cards = [card for card in priv.hand_cards if card not in priv.given_schupf_cards]
            assert len(priv.hand_cards) == 11

        # Tauscharten aufnehmen
        for player_index in range(4):
            pub.count_hand_cards[player_index] = 14
            priv = privs[player_index]
            priv.received_schupf_cards = (
                privs[(player_index + 1) % 4].given_schupf_cards[2],
                privs[(player_index + 2) % 4].given_schupf_cards[1],
                privs[(player_index + 3) % 4].given_schupf_cards[0],
            )
            priv.hand_cards += priv.received_schupf_cards
            assert len(priv.hand_cards) == 14

        # Startspieler bekannt geben
        pub.start_player_index = r.history[0][0]
        assert CARD_MAH in privs[pub.start_player_index].hand_cards

        # Los geht's - das eigentliche Spiel kann beginnen.
        pub.current_turn_index = pub.start_player_index

        for history_index, (current_player_index, cards, trick_collector_index) in enumerate(r.history):
            combination = get_trick_combination(cards, pub.trick_combination[2])
            priv = privs[pub.current_turn_index]

            # Tichu-Ansage abfragen (falls noch alle mitspielen, und falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde)
            for player_index in range(4):
                if pub.count_hand_cards[player_index] == 14 and not pub.announcements[player_index]:
                    priv = privs[player_index]
                    announcement = r.tichu_positions[player_index] == history_index
                    # todo Entscheidungspunkt für "announce_tichu" ausliefern
                    #  yield pub, priv, announcement
                    if announcement:
                        pub.announcements[player_index] = 1

            # Spielzug durchführen
            action = cards, combination

            # todo Für alle Spieler, die eine Bombe haben, Entscheidungspunkt "bomb" liefern
            #  yield pub, priv, action

            # Das Zugrecht kann durch eine Bombe erobert werden.
            if current_player_index != pub.current_turn_index:
                assert combination[0] == CombinationType.BOMB
                pub.current_turn_index = current_player_index
                priv = privs[pub.current_turn_index]
            else:
                assert current_player_index == pub.current_turn_index
                # Entscheidungspunkt "play" ausliefern
                yield pub, priv, action

            # todo tricks kann raus aus dem Spielstatus - der Status ist eine Momentaufnahme (inkl. aktuellen Stich, aber weiter zurück nicht)
            if pub.trick_owner_index == -1:  # neuer Stich?
                pub.tricks.append([(pub.current_turn_index, cards, combination)])
            else:
                pub.tricks[-1].append((pub.current_turn_index, cards, combination))

            if combination[0] != CombinationType.PASS:
                # Handkarten aktualisieren
                pub.count_hand_cards[pub.current_turn_index] -= combination[1]
                priv.hand_cards = [card for card in priv.hand_cards if card not in cards]

                # Stich aktualisieren
                pub.trick_owner_index = pub.current_turn_index
                pub.trick_cards = cards
                if combination == (CombinationType.SINGLE, 1, 16):
                    # Der Phönix ist eigentlich um 0.5 größer als der Stich, aber gleichsetzen geht auch (Anspiel == 1).
                    if pub.trick_combination[2] == 0:  # Anspiel oder Hund?
                        pub.trick_combination = (CombinationType.SINGLE, 1, 1)
                else:
                    pub.trick_combination = combination
                pub.trick_points += sum_card_points(cards)

                # Gespielte Karten merken
                pub.played_cards += cards

                # Ist der erste Spieler fertig?
                if pub.count_hand_cards[pub.current_turn_index] == 0:
                    n = pub.count_active_players
                    if n == 3:
                        pub.winner_index = pub.current_turn_index

                # Wunsch erfüllt?
                if pub.wish_value > 0 and is_wish_in(pub.wish_value, cards):
                    pub.wish_value = 0

                # Runde vorbei?
                if pub.count_hand_cards[pub.current_turn_index] == 0:
                    n = pub.count_active_players
                    if n == 3:
                        pub.winner_index = pub.current_turn_index
                    elif n == 2:
                        if (pub.current_turn_index + 2) % 4 == pub.winner_index:  # Doppelsieg?
                            pub.is_round_over = True
                            pub.is_double_victory = True
                    else:
                        pub.is_round_over = True
                        for player_index in range(4):
                            if pub.count_hand_cards[player_index] > 0:
                                pub.loser_index = player_index
                                break

                # Falls ein MahJong ausgespielt wurde, darf ein Wunsch geäußert werden.
                if not pub.is_round_over and CARD_MAH in cards:
                    # todo Entscheidungspunkt für "wish" ausliefern
                    pub.wish_value = r.wish_value

            if trick_collector_index != -1:
                # Stich kassieren
                if pub.trick_combination == (CombinationType.SINGLE, 1, 15) and not pub.is_double_victory:  # Drache kassiert? Muss verschenkt werden, wenn kein Doppelsieg!
                    # Stich verschenken
                    # todo Entscheidungspunkt für "give_dragon_away" ausliefern
                    #  yield pub, priv, trick_collector_index
                    pub.dragon_recipient = trick_collector_index
                # Punkte erhalten
                pub.points[trick_collector_index] += pub.trick_points
                # Stich zurücksetzen
                pub.trick_owner_index = -1
                pub.trick_cards = []
                pub.trick_combination = (CombinationType.PASS, 0, 0)
                pub.trick_points = 0
                pub.trick_counter += 1

            # Nächster Spieler ist an der Reihe
            if pub.trick_combination == (CombinationType.SINGLE, 1, 0) and pub.trick_owner_index == pub.current_turn_index:
                pub.current_turn_index = (pub.current_turn_index + 2) % 4
            else:
                pub.current_turn_index = (pub.current_turn_index + 1) % 4

            # Spieler ohne Handkarten überspringen
            while pub.count_hand_cards[pub.current_turn_index] == 0:
                pub.current_turn_index = (pub.current_turn_index + 1) % 4

        # Runde ist beendet
        assert pub.is_round_over

        # Endwertung der Runde
        if pub.is_double_victory:
            # Doppelsieg! Das Gewinnerteam kriegt 200 Punkte. Die Gegner nichts.
            pub.points = [0, 0, 0, 0]
            pub.points[pub.winner_index] = 200
        else:
            # a) Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
            assert 0 <= pub.loser_index <= 3
            leftover_points = 100 - sum_card_points(pub.played_cards)
            pub.points[(pub.loser_index + 1) % 4] += leftover_points
            # b) Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
            pub.points[pub.winner_index] += pub.points[pub.loser_index]
            pub.points[pub.loser_index] = 0

        # Bonus für Tichu-Ansage
        for player_index in range(4):
            if pub.announcements[player_index]:
                if player_index == pub.winner_index:
                    pub.points[player_index] += 100 * pub.announcements[player_index]
                else:
                    pub.points[player_index] -= 100 * pub.announcements[player_index]

        # Ergebnis der Runde in die Punktetabelle der Partie eintragen.
        score = pub.points[2] + pub.points[0], pub.points[3] + pub.points[1]
        pub.game_score[0].append(score[0])
        pub.game_score[1].append(score[1])

        # Runde validieren
        #pub.count_hand_cards[player_index]
        #pub.played_cards
        for player_index in range(4):
            pos = r.tichu_positions[player_index]
            if pub.announcements[player_index] != (2 if pos == -2 else 1 if pos >= -1 else 0):
                raise ValueError(f"Partie {r.game_id}, Runde {r.round_index}: Tichu-Ansage von Spieler {player_index} ist falsch: {pub.announcements[player_index]} != {2 if pos == -2 else 1 if pos >= -1 else 0}")

        assert pub.dragon_recipient == r.dragon_recipient

        if pub.is_double_victory != bool(r.is_double_victory):
            raise ValueError(f"Partie {r.game_id}, Runde {r.round_index}: Doppelsieg ist falsch: {pub.is_double_victory} != {r.is_double_victory}")

        assert score == r.score
        assert pub.winner_index == r.winner_index
        assert pub.loser_index == r.loser_index

    # Partie validieren
    total_score = pub.total_score
    assert total_score[0] >= 1000 or total_score[1] >= 1000
