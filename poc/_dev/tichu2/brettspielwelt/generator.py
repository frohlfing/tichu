from collections import deque
from tqdm import tqdm
import config
import numpy as np
from os import environ
from tichu.cards import sum_card_points, cardlabels_index, deck, other_cards
from tichu.combinations import BOMB, STREET, STAIR
from tichu.nnet import num_input

__all__ = 'generator',  'print_stdev_trick_points',


# BrettspielWelt-Generator für das überwachte Training

# Der Generator liefert pro Aufruf ein Beispiel (in Canonical Form!).
# Kategorische Größen werden One-Hot-Kodiert.  todo: nur x; p sind Integer
# Um Dummy Variable Trap zu vermeiden, wird für x die Kategorie 0 entfernt (d.h., kein Index gesetzt == 0; Index 0 == Wert 1)
#
# section: Unterteilung der Datensätze ('train', 'val', 'test' oder 'all')
# part: 'prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points' oder 'all'
# endless: Wenn False, wird ein Exception "StopIteration" geworfen, wenn der letzte Datensatz bereits durchlaufen wurde.
# test_lap_id und test_player: Für Unit-Test kann eine bestimmte Runde und ein bestimmter Spieler ausgewählt werden.
# validate: Wenn True, wird die Historie überprüft, indem die Endpunktzahl mit dem Datenbankeintrag verglichen wird. Part muss hierfür 'all' sein.
#
# Rückgabe (je nach Part eine Teilmenge der nachfolgenden Variablen):
# Variable                 Anzahl    Wertebereich     Typ             Beschreibung
# x0     hand (norm. Kar.) 13*4       0, 1            binary          Normale Handkarten (als Conv2D: 13 Werte * 4 Farben)
#        hand (spez. Kart)    4       0, 1            binary          Sonderkarten auf der Hand (0 == Hund, 1 == MahJong, 2 == Drache, 3 == Phönix)
# x1     schupfed1           16       0, 1            categorical     Schupf-Kartenwert für rechten Gegner (None == Hund, Index 0 == MahJong bis 15 == Phönix)
#        schupfed2           16       0, 1            categorical     Schupf-Kartenwert für Partner
#        schupfed3           16       0, 1            categorical     Schupf-Kartenwert für linken Gegner
# x2     number_of_cards      4       0.0 bis 1.0     continuous      Anzahl Handkarten (meine, rechte Gegner, Partner, linker Gegner; normalisiert: 1 == 14)
# x3     played_cards      13*4       0, 1            binary          Ausgespielte normale Karten (Conv2D: 13 Werte * 4 Farben)
#        played_cards (spez)  4       0, 1            binary          Ausgespielte Sonderkarten (0 == Hund, 1 == MahJong, 2 == Drache, 3 == Phönix)
# x4     tichu0               2       0, 1            categorical     Meine Tichu-Ansage (None == keine Ansage, 0 == kleines, 1 == großes Tichu)
#        tichu1               2       0, 1            categorical     Tichu-Ansage des rechten Gegners
#        tichu2               2       0, 1            categorical     Tichu-Ansage des Partners
#        tichu3               2       0, 1            categorical     Tichu-Ansage des linken Gegners
# x5     wish                14       0, 1            categorical     Wunsch (None == noch kein Wunsch geäußert, 0 == Wunsch wurde erfüllt, 1 == Wert 2 bis 13 == Wert 14)
# x6     trick_player         4       0, 1            categorical     Besitzer des Stichs (None == keiner, 0 == ich, 1 == rechter, 2 == Partner, 3 == linker)
#        trick_type           7       0, 1            categorical     Typ der Kartenkombination (None == Anspiel, 0 == Single bis 6 == Bombe)
#        trick_length        14       0, 1            categorical     Länge der Kartenkombination (None == Keine Karten, 0 == 1 Karte bis 13 == 14 Karten)
#        trick_value         15       0, 1            categorical     Höchste Karte in der Kombination (None == Hund, 0 == MahJong bis 14 == Drache)
#        trick_points         1      -0.625 bis 3.125 continuous      Punkte im Stich (normalisiert: -0.625 == -25 Punkte bis 3.125 == 125 Punkte; 1 == 40 Punkte)
# x7     points               4      -0.25 bis 1.25   continuous      Bisherige Punkte (meine, rechter, Partner, linker Gegner; (normalisiert: -0.25 == -25 bis 1.25 == 125 Punkte; 1 == 100 Punkte)
# x8     winner               4       0, 1            categorical     Spieler zuerst fertig (None == keiner, 0 == ich, 1 == rechter, 2 == Partner, 3 == linker)
# p0     tichu                2       0, 1            categorical     Gewählte Aktion: Tichu-Ansage (Index 0 == nein, Index 1 == ja)
# p1     figure_type          7       0, 1            categorical     Gewählte Aktion: Typ der Kartenkombination im Anspiel (0 == Single bis 6 == Bombe)
#        figure_length       14       0, 1            categorical     Gewählte Aktion: Länge der Treppe, Straße oder Bombe im Anspiel (0 == 4 Karte bis 10 == 14 Karten)
#        figure_value        16       0, 1            categorical     Gewählte Aktion: Höchste Karte im Anspiel (0 == Hund bis 15 == Drache; Phönix == MahJong, aber in der Praxis spielt im Anspiel niemand den Phönix!)
#        figure_card         16       0, 1            categorical     Gewählte Aktion: Höchste Karte beim Bedienen (0 == Passen, 1 = Phönix bis 15 == Drache; Phönix, wenn 1 oder p1d == x6d)
#        figure_bomb          2       0, 1            categorical     Gewählte Aktion: Bomben beim Bedienen (0 == Nein, 1 == Ja)
# p2     wish                13       0, 1            categorical     Gewählte Aktion: Wunsch (Index 0 == Wert 2 bis Index 12 == Wert 14)
# p3     gift                 2       0, 1            categorical     Gewählte Aktion: Geschenk (Index 0 == rechter Gegner, Index 1 == linker)
# p4     schupfed1           17       0, 1            categorical     Gewählte Aktion: Schupf-Kartenwert für rechten Gegner (Index 0 == Hund bis Index 16 == Phönix)
#        schupfed2           17       0, 1            categorical     Gewählte Aktion: Schupf-Kartenwert für Partner
#        schupfed3           17       0, 1            categorical     Gewählte Aktion: Schupf-Kartenwert für linken Gegner
# v0     bonus                1      -1.0 bis 1.0     continuous      Bonus für Tichu-Ansage (normalisiert: -1 == -200 bis 1 == 200 Punkte)
# v1     reward               1      -2.0 bis 2.0     continuous      Punktedifferenz am Ende der Runde mit Bonus (normalisiert: -2 == -800 bis 2 == 800 Punkte; 1 == 400 Punkte)
# v2     position             1      -1.0 bis 1.0     continuous      Position am Ende der Runde (-1 == Loser, 0 == Zweiter oder Dritter, 1 == Winner)

def generator(section: str, part: str, endless=True, offset=0, test_lap_id=None, test_player=None, validate=False):
    assert section in ('train', 'val', 'test', 'all')
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points', 'all')

    # Tensorflow Log Level
    # 0 = all messages are logged (default behavior)
    # 1 = INFO messages are not printed
    # 2 = INFO and WARNING messages are not printed
    # 3 = INFO, WARNING, and ERROR messages are not printed
    environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

    # Tensorflow darf wegen Multiprocessing nicht im Hauptprozess importiert werden.
    # Ansonsten würde ein Fork z.B. den GPU-RAM teilen wollen, das kann aber nicht funktionieren.
    import tensorflow as tf

    if section == 'val':
        filter_ = 'id % 10 = 0'  # 10% (id = 10, 20, 30, ...)
    elif section == 'test':
        filter_ = 'id % 10 = 1'  # 10% (id = 1, 11, 21, 31, ...)
    elif section == 'train':
        filter_ = 'id % 10 > 1'  # 80% (id = 2-9, 12-19, 22-29, 32-39, ...)
    else:  # all
        filter_ = '1'

    if offset:
        filter_ += f' AND id > {offset}'

    if test_lap_id:
        filter_ += f' AND id = {test_lap_id}'

    num_x = num_input(part)

    while True:
        dataset = tf.data.experimental.SqlDataset(
            'sqlite',
            config.DATA_PATH + '/brettspielwelt/brettspielwelt.sqlite',
            'SELECT id, episode_id, lap, \
                hand0, hand1, hand2, hand3, \
                schupfed0, schupfed1, schupfed2, schupfed3, \
                tichu0, tichu1, tichu2, tichu3, \
                wish, \
                gift, \
                winner, \
                loser, \
                points0, points1, \
                history \
            FROM laps \
            WHERE ' + filter_ + ' \
            ',
            (tf.int32, tf.int32, tf.int16,                # id, episode_id, lap
             tf.string, tf.string, tf.string, tf.string,  # hand: 8 + 6 Handkarten (z.B. "SZ S9 RZ RK G8 BK B9 B3 SK R8 R7 Ma GB B5")
             tf.string, tf.string, tf.string, tf.string,  # schupfed: Schupf-Karte für rechten Gegner, eine für den Partner und eine für den linken Gegner
             tf.int16, tf.int16, tf.int16, tf.int16,      # tichu: Position in der Historie, an der ein Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor Schupfen)
             tf.int16,                                    # wish: Wunsch 2 bis 14; 0 == MahJong wurde nicht gespielt
             tf.int16,                                    # gift: Spieler, der den Drachen bekommen hat (-1 == Drache wurde bis zum Schluss nicht verschenkt)
             tf.int16,                                    # winner: Spieler, der zuerst fertig wurde
             tf.int16,                                    # loser: Spieler, der nicht fertig wurde (-1 == Doppelsieg)
             tf.int16, tf.int16,                          # points: Punkte dieser Runde pro Team
             tf.string))                                  # history: [player,cards,cards_type,cards_value,card_points;...|...] (| == Stich einkassiert; beim Passen ist nur der Spieler angeben)

        for id_, episode_id, lap, hand0, hand1, hand2, hand3, schupfed0, schupfed1, schupfed2, schupfed3, tichu0, tichu1, tichu2, tichu3, wish, gift, winner, loser, points0, points1, history in dataset:
            # print('id', int(id_))
            # noinspection PyUnusedLocal
            id_ = int(id_)
            # noinspection PyUnusedLocal
            episode_id = int(episode_id)
            # noinspection PyUnusedLocal
            lap = int(lap)
            hands = hand0.numpy().decode().split(' '), hand1.numpy().decode().split(' '), hand2.numpy().decode().split(' '), hand3.numpy().decode().split(' ')
            schupfed = schupfed0.numpy().decode().split(' '), schupfed1.numpy().decode().split(' '), schupfed2.numpy().decode().split(' '), schupfed3.numpy().decode().split(' ')
            tichus = tichu0, tichu1, tichu2, tichu3
            wish = int(wish)
            gift = int(gift)
            winner = int(winner)
            loser = int(loser)
            points0 = int(points0)
            points1 = int(points1)
            history = history.numpy().decode().split('|')
            rand_player = np.random.randint(0, 4) if test_player is None else test_player  # Zufällig ausgewählter Spieler, bei dem v1 erfasst wird
            for player in range(4):
                if test_player is not None and player != test_player:
                    continue
                if part == 'points' and player != rand_player:
                    continue

                # Treppen, Straßen und Bomben zählen
                # - Für part == figure_n muss eine Treppe, Straße oder Straßen-Bombe im Anspiel gespielt werden.
                # - Für part == bombs müssen Bomben auf der Hand sein. Ich geh davon aus, dass man nicht auf eine
                #   Bombe sitzen bleibt, sondern sie irgendwann schmeißt.
                stairs_or_streets = 0
                bombs = 0
                if part in ('figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'bomb', 'all'):
                    for tricks in history:  # tricks == '0,Ma,1,1,0;1,G5,1,5,5;2,RK,1,13,10;3;0;1,RA,1,14,0;2;3;0'
                        for i, trick in enumerate(tricks.split(';')):  # trick == '0,Ma,1,1,0' (oder beim passen: trick = '2')
                            if len(trick) == 1:  # es wurde gepasst
                                continue
                            trick = trick.split(',')  # trick == player, cards, type, value, points
                            assert len(trick) == 5
                            if int(trick[0]) == player:
                                if i == 0 and (int(trick[2]) in (STAIR, STREET) or (int(trick[2]) == BOMB and len(trick[1]) > 4)):  # Treppe, Straße oder Bombe im Anspiel?
                                    stairs_or_streets += 1
                                if int(trick[2]) == BOMB:
                                    bombs += 1
                    if part in ('figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb') and stairs_or_streets == 0:
                        continue
                    if part == 'bomb' and bombs == 0:
                        continue

                # Canonical State
                x0a = np.zeros(52, dtype=int)  # Normale Handkarten (13 Werte * 4 Farben)
                x0b = np.zeros(4, dtype=int)   # Sonderkarten auf der Hand (0 == Hund, 1 == MahJong, 2 == Drache, 3 == Phönix)
                x1a = np.zeros(16, dtype=int)  # Schupf-Kartenwert für rechten Gegner (None == Hund, Index 1 == MahJong bis 16 == Phönix)
                x1b = np.zeros(16, dtype=int)  # Schupf-Kartenwert für Partner
                x1c = np.zeros(16, dtype=int)  # Schupf-Kartenwert für linken Gegner
                x2 = np.zeros(4, dtype=int)    # Anzahl Handkarten aller Spieler (meine, rechte Gegner, Partner, linker Gegner; normalisiert: 1 == 14 Karten)
                x3a = np.zeros(52, dtype=int)  # Ausgespielte Karten (13 Werte * 4 Farben)
                x3b = np.zeros(4, dtype=int)   # Ausgespielte Sonderkarten (0 == Hund, 1 == MahJong, 2 == Drache, 3 == Phönix)
                x4a = np.zeros(2, dtype=int)   # Meine Tichu-Ansage (None == keine Ansage, 0 == kleines, 1 == großes Tichu)
                x4b = np.zeros(2, dtype=int)   # Tichu-Ansage des rechten Gegners
                x4c = np.zeros(2, dtype=int)   # Tichu-Ansagen des Partners
                x4d = np.zeros(2, dtype=int)   # Tichu-Ansagen des linken Gegners
                x5 = np.zeros(14, dtype=int)   # Wunsch (None == noch kein Wunsch geäußert, 0 == Wunsch wurde erfüllt, 1 == Wert 2 bis 13 == Wert 14)
                x6a = np.zeros(4, dtype=int)   # Besitzer des Stichs (None == keiner, 0 == ich, 1 == rechter, 2 == Partner, 3 == linker)
                x6b = np.zeros(7, dtype=int)   # Typ der Kartenkombination (None == Anspiel, 0 == Single bis 6 == Bombe)
                x6c = np.zeros(14, dtype=int)  # Länge der Kartenkombination (None == Keine Karten, 0 == Länge 1 bis 13 == Länge 14)
                x6d = np.zeros(15, dtype=int)  # Wert der Kartenkombination (None == Hund, 0 == MahJong bis 14 == Drache)
                x6e = np.zeros(1, dtype=int)   # Punkte im Stich (normalisiert: 1 == 40 Punkte)
                x7 = np.zeros(4, dtype=int)    # Bisherige Punkte (meine, rechter, Partner, linker Gegner; normalisiert: 1 == 100 Punkte)
                x8 = np.zeros(4, dtype=int)    # Spieler zuerst fertig (None == keiner, 0 == ich, 1 == rechter, 2 == Partner, 3 == linker)
                # Canonical Target (gewählte Aktion)
                p0 = np.zeros(2, dtype=int)    # Tichu-Ansage (Index 0 == nein, Index 1 == ja)
                p1a = np.zeros(7, dtype=int)   # Typ der Kartenkombination im Anspiel (0 == Single bis 6 == Bombe)
                p1b = np.zeros(14, dtype=int)  # Länge der Treppe, Straße oder Bombe im Anspiel (0 == 4 Karte bis 10 == 14 Karten)
                p1c = np.zeros(16, dtype=int)  # Höchste Karte der Kombination im Anspiel (0 == Hund bis 15 == Drache; Phönix = MahJong, aber in der Praxis spielt im Anspiel niemand den Phönix!)
                p1d = np.zeros(16, dtype=int)  # Höchste Karte beim Bedienen (0 == Passen, 1 = Phönix bis 15 == Drache; Phönix, wenn 1 oder p1d == x6d)
                p1e = np.zeros(2, dtype=int)   # Bomben beim Bedienen (0 == Nein, 1 == Ja)
                p2 = np.zeros(13, dtype=int)   # Wunsch (Index 0 == Wert 2 bis Index 12 == Wert 14)
                p3 = np.zeros(2, dtype=int)    # Geschenk (Index 0 == rechter Gegner, Index 1 == linker Gegner)
                p4a = np.zeros(17, dtype=int)  # Schupf-Kartenwert für rechten Gegner (Index 0 == Hund bis Index 16 == Phönix)
                p4b = np.zeros(17, dtype=int)  # Schupf-Kartenwert für Partner
                p4c = np.zeros(17, dtype=int)  # Schupf-Kartenwert für linken Gegner
                # Canonical Target (Bewertung der aktuellen Spielsituation)
                # v0 = 0                       # Bonus für Tichu-Ansage (normalisiert: 1 == 200 Punkte)
                # v1 = 0                       # Punktedifferenz am Ende der Runde mit Bonus (normalisiert:  1 == 400 Punkte)
                # v2 = 0                       # Position am Ende der Runde (-1 == Loser, 0 == Zweiter oder Dritter, 1 == Winner)

                tmp_x = deque()                # Speichert alle Spielsituationen der Runde, aus denen eine für v0, v1 und v2 zufällig ausgewählt wird.

                # ----------------------------------------------------------------
                # Auftakt: die ersten 8 Karten wurden verteilt

                # Status: Handkarten
                for card in hands[player][:8]:
                    j = cardlabels_index[card]
                    if 2 <= j <= 53:
                        x0a[j - 2] = 1
                    else:
                        x0b[j if j < 2 else j - 52] = 1

                # Status: Anzahl Handkarten
                for k in range(4):
                    x2[k] = 8

                # Status: große Tichu-Ansagen (wir nehmen an, das die anderen Spieler vor mir die Ansage machten)
                for k in range(1, 4):
                    if tichus[(player + k) % 4] == -2:  # großes Tichu?
                        if k == 1:
                            x4b[1] = 1
                        elif k == 2:
                            x4c[1] = 1
                        elif k == 3:
                            x4d[1] = 1

                # Target: Tichu-Ansage (0 == nein, 1 == ja)
                p0[1 if tichus[player] == -2 else 0] = 1  # -2 == großes Tichu

                # Status und erwartete Aktion zurückgeben
                if part in ('prelude_grand', 'prelude', 'all'):
                    assert p0.sum() == 1
                    if part in ('prelude_grand', 'prelude'):
                        x = (x0a.copy().reshape((13, 4)), x0b.copy(), x4b.copy(), x4c.copy(), x4d.copy())
                    else:  # part == 'all'
                        x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                             x1a.copy(), x1b.copy(), x1c.copy(),
                             x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                             x3a.copy().reshape((13, 4)), x3b.copy(),
                             x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                             x5.copy(),
                             x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,  # x6e normalisiert
                             x7.copy() / 100,  # normalisiert
                             x8.copy())
                    if part in ('prelude_grand', 'prelude'):
                        y = p0.copy()
                    else:  # part == 'all'
                        y = p0.copy(), p1a.copy(), p1b.copy(), p1c.copy(), p1d.copy(), p1e.copy(), p2.copy(), p3.copy(), p4a.copy(), p4b.copy(), p4c.copy()
                    assert len(x) == num_x
                    yield id_, x, y
                elif part in ('bonus', 'points'):
                    x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                         x1a.copy(), x1b.copy(), x1c.copy(),
                         x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                         x3a.copy().reshape((13, 4)), x3b.copy(),
                         x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                         x5.copy(),
                         x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,  # x6e normalisiert
                         x7.copy() / 100,  # normalisiert
                         x8.copy())
                    tmp_x.append(x)

                # Status für mein großes Tichu aktualisieren (sollte ja vorausgesagt werden, daher wird es jetzt erst gesetzt)
                if tichus[player] == -2:  # großes Tichu?
                    x4a[1] = 1

                # ----------------------------------------------------------------
                # Auftakt: die letzten 6 Karten wurden verteilt

                # Status: Handkarten
                for card in hands[player][8:]:
                    j = cardlabels_index[card]
                    if 2 <= j <= 53:
                        x0a[j - 2] = 1
                    else:
                        x0b[j if j < 2 else j - 52] = 1

                # Status: Anzahl Handkarten
                assert x0a.sum() + x0b.sum() == 14
                for k in range(4):
                    x2[k] = 14

                # Status: Tichu-Ansagen (wir nehmen an, das die anderen Spieler vor mir die Ansage machten)
                for k in range(1, 4):
                    if tichus[(player + k) % 4] == -1:  # Ansage vor Schupfen?
                        if k == 1:
                            x4b[0] = 1
                        elif k == 2:
                            x4c[0] = 1
                        elif k == 3:
                            x4d[0] = 1

                # Target: Tichu-Ansage (0 == nein, 1 == ja)
                p0[p0.argmax()] = 0
                if tichus[player] != -2:  # Spieler darf kein großes Tichu angesagt haben
                    p0[1 if tichus[player] == -1 else 0] = 1  # -1 == normales Tichu im  Auftakt

                # Target: Schupfen
                for k, card in enumerate(schupfed[player]):
                    value, color = deck[cardlabels_index[card]]
                    if k == 0:
                        p4a[value] = 1
                    elif k == 1:
                        p4b[value] = 1
                    elif k == 2:
                        p4c[value] = 1

                # Status und erwartete Aktion zurückgeben
                if (part in ('prelude_not_grand', 'prelude') and p0.sum() == 1) or \
                        (part == 'schupf1' and p4a.sum() == 1) or \
                        (part == 'schupf2' and p4b.sum() == 1) or \
                        (part == 'schupf3' and p4c.sum() == 1) or \
                        part == 'all':
                    if part in ('prelude_not_grand', 'prelude'):
                        x = (x0a.copy().reshape((13, 4)), x0b.copy(), x4b.copy(), x4c.copy(), x4d.copy())
                    elif part in ('schupf1', 'schupf2', 'schupf3'):
                        x = (x0a.copy().reshape((13, 4)), x0b.copy(), x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy())
                    else:  # part == 'all'
                        x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                             x1a.copy(), x1b.copy(), x1c.copy(),
                             x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                             x3a.copy().reshape((13, 4)), x3b.copy(),
                             x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                             x5.copy(),
                             x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,  # x6e normalisiert
                             x7.copy() / 100,  # normalisiert
                             x8.copy())
                    if part in ('prelude_not_grand', 'prelude'):
                        y = p0.copy()
                    elif part == 'schupf1':
                        y = p4a.copy()
                    elif part == 'schupf2':
                        y = p4b.copy()
                    elif part == 'schupf3':
                        y = p4c.copy()
                    else:  # part == 'all'
                        y = p0.copy(), p1a.copy(), p1b.copy(), p1c.copy(), p1d.copy(), p1e.copy(), p2.copy(), p3.copy(), p4a.copy(), p4b.copy(), p4c.copy()
                    assert len(x) == num_x
                    yield id_, x, y
                elif part in ('bonus', 'points'):
                    x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                         x1a.copy(), x1b.copy(), x1c.copy(),
                         x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                         x3a.copy().reshape((13, 4)), x3b.copy(),
                         x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                         x5.copy(),
                         x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,  # x6e normalisiert
                         x7.copy() / 100,  # normalisiert
                         x8.copy())
                    tmp_x.append(x)

                # Schupfen (Karten abgeben)
                for k, card in enumerate(schupfed[player]):
                    # Status: Handkarten
                    j = cardlabels_index[card]
                    if 2 <= j <= 53:
                        x0a[j - 2] = 0
                    else:
                        x0b[j if j < 2 else j - 52] = 0
                    # Status: Schupfen
                    value, color = deck[j]
                    if value > 0:
                        if k == 0:
                            x1a[value - 1] = 1
                        elif k == 1:
                            x1b[value - 1] = 1
                        elif k == 2:
                            x1c[value - 1] = 1
                assert x0a.sum() + x0b.sum() == 11

                # Schupfen (Karten aufnehmen)
                for k in range(3):
                    # Status: Handkarten
                    card = schupfed[(player + 1 + k) % 4][2 - k]
                    j = cardlabels_index[card]
                    if 2 <= j <= 53:
                        x0a[j - 2] = 1
                    else:
                        x0b[j if j < 2 else j - 52] = 1
                assert x0a.sum() + x0b.sum() == 14

                # Status für mein Tichu aktualisieren (sollte ja vorausgesagt werden, daher wird es jetzt erst gesetzt)
                if tichus[player] == -1:  # Ansage vor Schupfen?
                    x4a[0] = 1

                if part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'schupf1', 'schupf2', 'schupf3'):
                    continue

                # ----------------------------------------------------------------
                # Spiel anhand der History durchlaufen...

                # Target: Schupfen
                p4a[p4a.argmax()] = 0  # das Schupfen ist jetzt nicht mehr möglich
                p4b[p4b.argmax()] = 0
                p4c[p4c.argmax()] = 0

                c = 0
                err = False
                for tricks in history:  # tricks == '0,Ma,1,1,0;1,G5,1,5,5;2,RK,1,13,10;3;0;1,RA,1,14,0;2;3;0'
                    if err:
                        break
                    elif part == 'tichu' and (x2[0] < 14 or x4a.sum() == 1):  # Spieler muss noch alle Karten haben und darf noch kein Tichu gesagt haben
                        break
                    elif part in ('figure_t', 'figure_n', 'figure_v', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'card', 'bomb') and (x2[0] == 0):  # Spieler muss noch Karten haben
                        break
                    elif part in ('figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb') and stairs_or_streets == 0:  # der Spieler muss noch mindestens eine Treppe, Straße oder Straßen-Bombe besitzen
                        break
                    elif part == 'bomb' and bombs == 0:  # der Spieler muss noch mindestens eine Bombe besitzen
                        break
                    elif part == 'wish' and x0b[1] == 0:  # der MahJong muss noch auf der Hand sein
                        break
                    elif part == 'gift' and x0b[2] == 0:  # der Drache muss noch auf der Hand sein
                        break

                    # Anspiel, Stich zurücksetzen
                    x6a[x6a.argmax()] = 0  # Besitzer des Stichs == Niemand
                    x6b[x6b.argmax()] = 0  # Typ == Passen == Anspiel
                    x6c[x6c.argmax()] = 0  # Länge == 0
                    x6d[x6d.argmax()] = 0  # Wert == Hund
                    x6e[0] = 0  # Punkte im Stich
                    dragon_wins = False
                    # noinspection GrazieInspection
                    for trick in tricks.split(';'):  # trick == '0,Ma,1,1,0' (oder beim passen: trick = '2')
                        # Stich auslesen
                        if len(trick) == 1:  # es wird gepasst
                            curr_player = int(trick)
                            cards = ''
                            cards_type = 0
                            cards_len = 0
                            cards_value = 0
                            cards_points = 0
                        else:  # es werden Karten ausgelegt
                            curr_player, cards, cards_type, cards_value, cards_points = trick.split(',')
                            curr_player = int(curr_player)
                            cards = cards.split(' ')
                            cards_type = int(cards_type)
                            cards_len = len(cards)
                            cards_value = int(cards_value)
                            cards_points = float(cards_points)
                            if cards[0] == 'Dr' and gift >= 0:
                                dragon_wins = True

                        # Status: Tichu-Ansage  (wir nehmen an, das die anderen Spieler vor mir die Ansage machten)
                        for k in range(1, 4):
                            if tichus[(player + k) % 4] == c:
                                if x2[k] != 14:
                                    # print(f' lap-id {id_}: Spieler {(player + k) % 4} sagt Tichu, hat aber nur noch {x2[k]} Karten.')
                                    err = True
                                if k == 1:
                                    x4b[0] = 1
                                elif k == 2:
                                    x4c[0] = 1
                                elif k == 3:
                                    x4d[0] = 1

                        if curr_player == player and not err:
                            # Target: Normale Tichu-Ansage (0 == nein, 1 == ja)
                            p0[p0.argmax()] = 0
                            if x2[0] == 14 and x4a.sum() == 0:  # Spieler muss noch alle Karten haben und darf noch kein Tichu gesagt haben
                                p0[1 if tichus[player] == c else 0] = 1

                            # Target: Karten legen
                            p1a[p1a.argmax()] = 0
                            p1b[p1b.argmax()] = 0
                            p1c[p1c.argmax()] = 0
                            p1d[p1d.argmax()] = 0
                            p1e[p1e.argmax()] = 0
                            if x6b.sum() == 0:  # kein Stich == Anspiel
                                assert cards_type > 0 and cards_len > 0  # Passen im Anspiel nicht erlaubt
                                p1a[cards_type - 1] = 1  # Typ im Anspiel (0 == Single bis 6 == Bombe)
                                if (cards_type == STAIR and part in ('figure_n', 'figure_n_stair', 'all')) or \
                                        (cards_type == STREET and part in ('figure_n', 'figure_n_street', 'all')) or \
                                        (cards_type == BOMB and part in ('figure_n', 'figure_n_bomb', 'all')):
                                    p1b[cards_len - 4] = 1  # Länge im Anspiel (0 == 4 Karte bis 10 == 14 Karten)
                                p1c[cards_value] = 1  # Wert im Anspiel (0 == Hund bis 15 == Drache)
                            else:
                                p1d[cards_value] = 1  # Wert beim Bedienen (0 == Passen, 1 = Phönix bis 15 == Drache)
                                if bombs > 0:
                                    p1e[1 if cards_type == BOMB else 0] = 1  # Bombe beim Bedienen (0 == Nein, 1 == Ja)

                            # Target: Wunsch (0 == Wert 2 bis 12 == Wert 14)
                            p2[p2.argmax()] = 0
                            if 'Ma' in cards:
                                p2[wish - 2] = 1

                            # Target: Geschenk (0 == rechter Gegner, 1 == linker)
                            p3[p3.argmax()] = 0
                            if cards_len == 1 and cards[0] == 'Dr' and gift >= 0:
                                p3[0 if (player + 1) % 4 == gift else 1] = 1

                            # Status und Target (erwartete Aktion) zurückgeben
                            assert part not in ('prelude_grand', 'prelude_not_grand', 'prelude', 'schupf1', 'schupf2', 'schupf3')
                            if (part == 'tichu' and p0.sum() == 1) or \
                                    (part == 'figure_t' and p1a.sum() == 1) or \
                                    (part in ('figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb') and p1b.sum() == 1) or \
                                    (part == 'figure_v' and p1c.sum() == 1) or \
                                    (part == 'card' and p1d.sum() == 1) or \
                                    (part == 'bomb' and p1e.sum() == 1) or \
                                    (part == 'wish' and p2.sum() == 1) or \
                                    (part == 'gift' and p3.sum() == 1) or \
                                    part == 'all':
                                if part == 'tichu':  # ohne x4a
                                    x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                                         x1a.copy(), x1b.copy(), x1c.copy(),
                                         x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                                         x3a.copy().reshape((13, 4)), x3b.copy(),
                                         x4b.copy(), x4c.copy(), x4d.copy(),
                                         x5.copy(),
                                         x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,
                                         # x6e normalisiert
                                         x7.copy() / 100,  # normalisiert
                                         x8.copy())
                                elif part in ('figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v'):  # ohne x6
                                    x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                                         x1a.copy(), x1b.copy(), x1c.copy(),
                                         x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                                         x3a.copy().reshape((13, 4)), x3b.copy(),
                                         x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                                         x5.copy(),
                                         x7.copy() / 100,  # normalisiert
                                         x8.copy())
                                elif part == 'wish':  # ohne x5
                                    x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                                         x1a.copy(), x1b.copy(), x1c.copy(),
                                         x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                                         x3a.copy().reshape((13, 4)), x3b.copy(),
                                         x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                                         x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,
                                         # x6e normalisiert
                                         x7.copy() / 100,  # normalisiert
                                         x8.copy())
                                else:  # part in ('card', 'bomb', 'gift', 'all)
                                    x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                                         x1a.copy(), x1b.copy(), x1c.copy(),
                                         x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                                         x3a.copy().reshape((13, 4)), x3b.copy(),
                                         x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                                         x5.copy(),
                                         x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,  # x6e normalisiert
                                         x7.copy() / 100,  # normalisiert
                                         x8.copy())

                                if part == 'tichu':
                                    y = p0.copy()
                                elif part == 'figure_t':
                                    y = p1a.copy()
                                elif part == 'figure_n':
                                    y = p1b.copy()
                                elif part in 'figure_n_stair':
                                    #    Karten:      4       6       8      10      12       14
                                    y = np.array([p1b[0], p1b[2], p1b[4], p1b[6], p1b[8], p1b[10]])
                                elif part in ('figure_n_street', 'figure_n_bomb'):
                                    y = p1b[1:]  # ab 5 Karten
                                elif part == 'figure_v':
                                    y = p1c.copy()
                                elif part == 'card':
                                    y = p1d.copy()
                                elif part == 'bomb':
                                    y = p1e.copy()
                                elif part == 'wish':
                                    y = p2.copy()
                                elif part == 'gift':
                                    y = p3.copy()
                                else:  # part == 'all'
                                    y = p0.copy(), p1a.copy(), p1b.copy(), p1c.copy(), p1d.copy(), p1e.copy(), p2.copy(), p3.copy(), p4a.copy(), p4b.copy(), p4c.copy()
                                assert len(x) == num_x
                                yield id_, x, y
                            elif part in ('bonus', 'points'):
                                x = (x0a.copy().reshape((13, 4)), x0b.copy(),
                                     x1a.copy(), x1b.copy(), x1c.copy(),
                                     x2.copy() / 14,  # normalisiert: 1 == 14 Karten
                                     x3a.copy().reshape((13, 4)), x3b.copy(),
                                     x4a.copy(), x4b.copy(), x4c.copy(), x4d.copy(),
                                     x5.copy(),
                                     x6a.copy(), x6b.copy(), x6c.copy(), x6d.copy(), x6e.copy() / 40,  # x6e normalisiert
                                     x7.copy() / 100,  # normalisiert
                                     x8.copy())
                                tmp_x.append(x)

                        # Aktion durchführen (Status aktualisieren)...

                        # Status für mein Tichu aktualisieren (sollte ja vorausgesagt werden, daher wird es jetzt erst gesetzt)
                        if tichus[player] == c:
                            if x2[0] != 14:
                                # print(f' lap-id {id_}: Spieler {player} sagt Tichu, hat aber nur noch {x2[0]} Karten.')
                                err = True
                            x4a[0] = 1

                        # Falls Karten ausgespielt wurden, Handkarten, gespielte Karten und Stich aktualisieren
                        if cards_len > 0:
                            # Anzahl Handkarten
                            j = (curr_player + 4 - player) % 4  # canonical index
                            x2[j] -= cards_len
                            assert x2[j] >= 0
                            if x2[j] == 0 and x8.sum() == 0:  # Zuerst fertig?
                                x8[j] = 1
                                assert winner == (player + j) % 4

                            assert 1 <= \
                                   (1 if x2[0] > 0 else 0) + \
                                   (1 if x2[1] > 0 else 0) + \
                                   (1 if x2[2] > 0 else 0) + \
                                   (1 if x2[3] > 0 else 0) <= 4

                            for card in cards:
                                # Gespielte Karten und eigene Handkarten
                                j = cardlabels_index[card]
                                if 2 <= j <= 53:
                                    x3a[j - 2] = 1
                                    if curr_player == player:
                                        x0a[j - 2] = 0
                                else:
                                    x3b[j if j < 2 else j - 52] = 1
                                    if curr_player == player:
                                        x0b[j if j < 2 else j - 52] = 0

                                # Wunsch
                                if wish == 0:  # kommt leider vor, dass kein Wunsch geäußert wurde :-(
                                    if j == 1:  # MahJong
                                        # print(f' lap-id {id_}: Spieler {player} spielt den Mahjong, wünscht sich aber nichts!')
                                        err = True
                                        x5[0] = 1  # Wunsch wurde quasi erfüllt
                                else:
                                    assert 2 <= wish <= 14
                                    if j == 1:  # MahJong
                                        x5[wish - 1] = 1  # Index 1 == Wert 2 bis Index 13 == Wert 14
                                    elif x5[wish - 1] == 1 and deck[j][0] == wish:  # Wunsch erfüllt
                                        x5[wish - 1] = 0
                                        x5[0] = 1  # Index 0 == Wunsch wurde erfüllt

                            if curr_player == player:
                                assert x0a.sum() + x0b.sum() == x2[0]
                            assert 56 - x2.sum() == x3a.sum() + x3b.sum()

                            # Besitzer des Stichs
                            x6a[x6a.argmax()] = 0
                            x6a[(curr_player + 4 - player) % 4] = 1

                            # Typ der Kartenkombination
                            x6b[x6b.argmax()] = 0
                            assert cards_type > 0
                            x6b[cards_type - 1] = 1  # 0 == Single bis 7 == Bombe
                            if curr_player == player:
                                if (cards_type in (STAIR, STREET) or (cards_type == BOMB and cards_len > 4)) and x6c.sum() == 0 and part in ('figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'all'):  # x6c == Tick-Länge == 0 -> Anspiel
                                    assert stairs_or_streets > 0
                                    stairs_or_streets -= 1
                                if cards_type == BOMB and part in ('bomb', 'all'):
                                    assert bombs > 0
                                    bombs -= 1

                            # Länge der Kartenkombination
                            x6c[x6c.argmax()] = 0
                            x6c[cards_len - 1] = 1

                            # Wert der Kartenkombination
                            x6d[x6d.argmax()] = 0
                            if cards_value > 0:  # kein Hund?
                                x6d[cards_value - 1] = 1

                            # Punkte im Stich
                            x6e[0] += cards_points

                        c += 1  # nächster Zug

                    # Stich wird einkassiert
                    if dragon_wins:
                        x7[(gift + 4 - player) % 4] += x6e[0]
                    else:
                        assert x6a.sum() == 1
                        x7[x6a.argmax()] += x6e[0]

                    # Punkte bei Spiel-Ende überprüfen
                    if validate:
                        double_win = (x2 == 0).sum() == 2 and (x2[0] == x2[2] == 0 or x2[1] == x2[3] == 0)
                        finished = double_win or (x2 == 0).sum() == 3
                        if finished:
                            points = np.array([0, 0, 0, 0])
                            if double_win:
                                if x2[0] == 0:
                                    points[player] = 200
                                else:
                                    points[(player + 1) % 4] = 200
                                loser_ = -1
                            else:
                                for k in range(4):  # k = canonical index
                                    j = (player + k) % 4  # j = real index
                                    points[j] = x7[k]
                                # Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
                                loser_ = (player + x2.argmax()) % 4
                                spezial_card_index = ((0, 0), (1, 0), (15, 0), (16, 0))  # Hund, MahJong, Drache, Phönix
                                played_cards = [deck[i + 2] for i, v in enumerate(x3a) if v] + [spezial_card_index[i] for i, v in enumerate(x3b) if v]
                                loser_hand = other_cards(played_cards)  # die noch nicht gespielten Karten hat der Loser auf der Hand
                                loser_points = sum_card_points(loser_hand)
                                assert x7.sum() + loser_points == 100
                                points[(loser_ + 1) % 4] += loser_points
                                # Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
                                points[winner] += points[loser_]
                                points[loser_] = 0
                                assert points.sum() == 100, f'points: {points}, x7: {x7}, player: {player}, winner: {winner}, loser: {loser_}'
                            assert loser_ == loser
                            bonus = np.array([0, 0, 0, 0])
                            for k in range(4):  # k = canonical index
                                j = (player + k) % 4  # j = real index
                                if tichus[j] == -2:
                                    bonus[j] += 200 if winner == j else -200
                                if tichus[j] >= -1:
                                    bonus[j] += 100 if winner == j else -100
                            assert points[0] + points[2] + bonus[0] + bonus[2] == points0
                            assert points[1] + points[3] + bonus[1] + bonus[3] == points1

                # v0 und v1 werden nur einmal pro Runde zurückgegeben, da die Ausgabe sich nicht verändert und die
                # Eingabe voneinander abhängt.
                if part in ('bonus', 'points'):
                    # Ein Zustand zufällig auswählen
                    j = np.random.randint(0, len(tmp_x))
                    x = tmp_x[j]

                    # Target: Bonus für Tichu-Ansage
                    if tichus[player] == -2:
                        v0 = 200 if winner == player else -200
                    elif tichus[player] >= -1:
                        v0 = 100 if winner == player else -100
                    else:
                        v0 = 0

                    # Target: Punktedifferenz am Ende der Runde
                    v1 = points0 - points1 if player in (0, 2) else points1 - points0

                    # Target: Position am Ende der Runde (-1 == Loser, 0 == Zweiter oder Dritter, 1 == Winner)
                    # v2 = 1 if winner == player else -1 if loser == player else 0

                    if part == 'bonus':
                        y = v0 / 200  # normalisiert
                    else:  # part == 'points'
                        y = v1 / 400  # normalisiert

                    assert len(x) == num_x
                    yield id_, x, y

                # Runde nochmal durchlaufen aus Sicht des nächsten Spielers

            # nächster Datensatz

        # Alle Datensätze durchlaufen.
        if not endless:
            break  # Abbruch, da eine Wiederholung nicht gewünscht ist


# Wie viele max. Punkte im Stich sind "normal"?
# Ergebnis: 26.5 +- 15.5; Max. Punkte gesamt:  80; n= 100000
def print_stdev_trick_points(n=100000):
    points = deque()
    points_max = deque()
    last_id = 0
    gen = generator('train', 'all', endless=False)
    for _ in tqdm(range(n)):
        id_, (x0a_, x0b_, x1a_, x1b_, x1c_, x2_, x3a_, x3b_, x4a_, x4b_, x4c_, x4d_, x5_, x6a_, x6b_, x6c_, x6d_, x6e_, x7_, x8_), y_ = next(gen)
        if 0 < last_id < id_:
            points_max.append(np.max(points))
            points = deque()
        points.append(x6e_ * 40)
        last_id = id_
    mean_ = np.mean(points_max)
    std_ = np.std(points_max)
    max_ = np.max(points_max)
    print(f'\rMax. Punkte im Stich: {mean_:4.1f} +-{std_:4.1f}; Max.: {max_:3.0f}; n={n}')
