import config
from math import sqrt
import numpy as np
from os import path
import sqlite3
from tqdm import tqdm
from tichu.cards import cardlabels, parse_cards, sum_card_points, stringify_cards
from tichu.combinations import get_figure, BOMB

__all__ = 'Database',


# Von BrettspielWelt heruntergeladene Tichu-Logs in eine SQLite-Datenbank importieren.
#
# Mit dem Datenbestand bis 2022/04 liegen 2.352.727 Episoden mit insgesamt 22.042.274 Runden vor.
# Im Schnitt werden demnach 9,37 Runden pro Episode gespielt.
# Insgesamt wurden 9.765.376 Bomben geworfen, davon 1.417.016 Bomben (14,5 % von allen Bomben) außer der Reihe.
class Database:
    def __init__(self):
        dbname = config.DATA_PATH + '/brettspielwelt/brettspielwelt.sqlite'
        # os.remove(dbname)
        db_exists = path.exists(dbname)
        self._db = sqlite3.connect(dbname)
        if not db_exists:
            self._create_db()

    def __del__(self):
        self._db.close()

    # Datenbank erstellen
    def _create_db(self):
        # nickname: Name der Spieler
        # score: Endergebnis der Episode
        # dt: Zeitpunkt des Spiels (z.B. 2007-01-09 19:03 )
        self._db.execute("""
            CREATE TABLE episodes (
                id INTEGER PRIMARY KEY,
                nickname0 VARCHAR(255),
                nickname1 VARCHAR(255),
                nickname2 VARCHAR(255),
                nickname3 VARCHAR(255),
                score0 INTEGER,
                score1 INTEGER,
                dt DATETIME
            )
            """)

        # lap: Rundenzähler
        # hand: 8 + 6 Handkarten (z.B. "SZ S9 RZ RK G8 BK B9 B3 SK R8 R7 Ma GB B5")
        # schupfed: Schupf-Karte für rechten Gegner, eine für den Partner und eine für den linken Gegner
        # tichu: Position in der Historie, an der ein Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor Schupfen)
        # wish: Wunsch (2 bis 14; 0 == MahJong wurde nicht gespielt)
        # gift: Spieler, der den Drachen bekommen hat (-1 == Drache wurde bis zum Schluss nicht verschenkt)
        # winner: Spieler, der zuerst fertig wurde
        # loser: Spieler, der nicht fertig wurde  (-1 == Doppelsieg)
        # points: Punkte dieser Runde pro Team
        # history: [player,cards,cards_type,cards_value,card_points;...|...] (| == Stich einkassiert; beim Passen ist nur der Spieler angeben)
        self._db.execute("""
            CREATE TABLE laps (
                id INTEGER PRIMARY KEY,
                episode_id INTEGER,    
                lap INTEGER, 
                hand0 VARCHAR(41),
                hand1 VARCHAR(41),
                hand2 VARCHAR(41),
                hand3 VARCHAR(41),
                schupfed0 VARCHAR(8),
                schupfed1 VARCHAR(8),
                schupfed2 VARCHAR(8),
                schupfed3 VARCHAR(8),
                tichu0 INTEGER,
                tichu1 INTEGER,
                tichu2 INTEGER,
                tichu3 INTEGER,
                wish INTEGER,
                gift INTEGER,
                winner INTEGER,
                loser INTEGER,
                points0 INTEGER,
                points1 INTEGER,
                history TEXT
            )
            """)

        self._db.execute("""
            CREATE INDEX laps_episode_id ON laps(episode_id);
            """)

        self._db.commit()

    # Datenbank Cursor
    def cursor(self) -> sqlite3.Cursor:
        return self._db.cursor()

    # Logfiles in die Datenbank einlesen
    # y2, m2: Jahr und Monat des letzten Eintrags der heruntergeladenen Log-Files
    def import_logs(self, y2: int, m2: int):
        # letzte gespeicherte Episode ermitteln
        cur = self._db.cursor()
        cur.execute("SELECT id, dt FROM episodes ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            last_id, last_dt = row
        else:
            last_id, last_dt = 0, '2007-01-09 00:00'
        y1, m1 = last_dt[0:7].split('-')
        y1 = int(y1)
        m1 = int(m1)

        # Alle Monate durchlaufen...
        for y in range(y1, y2 + 1):
            a = m1 if y == y1 else 1
            b = m2 if y == y2 else 12
            for m in range(a, b + 1):
                # Index des Monats öffnen und alle Episoden durchlaufen...
                folder = config.DATA_PATH + '/brettspielwelt/tichulog/{0:04d}/{1:04d}{2:02d}'.format(y, y, m)
                file = folder + '/index.html'
                with open(file, 'r') as fp:
                    for line in fp:
                        line = line.strip()
                        if not line.startswith('<a href='):
                            continue
                        i = line.find('.tch')
                        j = line.find('</a>')
                        episode_id = int(line[10:i])
                        if episode_id <= last_id:
                            continue
                        print(f'\r{y:04d}-{m:02d} - Episode {episode_id} ', end='')
                        dt = line[i + 6:i + 22]
                        nicknames = line[i + 23:j].split(' ')
                        # Runden zur Episode speichern
                        score = self._save_laps(folder, episode_id)
                        if score == [0, 0]:
                            continue
                        # Spieler, Endergebnis und Datum der Episode speichern
                        self._db.execute('''
                            INSERT INTO episodes (id, nickname0, nickname1, nickname2, nickname3, score0, score1, dt) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (episode_id, nicknames[0], nicknames[1], nicknames[2], nicknames[3], score[0], score[1], dt))
                        # Hat alles geklappt, jetzt Datenbankänderungen permanent abschließen
                        self._db.commit()
        print(f'\nImport beendet')

    # Runden speichern und Endergebnis zurückgeben
    def _save_laps(self, folder, episode_id):
        score = [0, 0]
        # Log-Datei öffnen und alle Zeilen einlesen
        file = folder + '/{0}.tch'.format(episode_id)
        if not path.exists(file):
            print(f'{file[-24:]}: Log-Datei existiert nicht. Überspringe Episode.')
            return score
        with open(file) as fp:
            lines = fp.readlines()
        lines = [line.strip() for line in lines]
        # Alle Zeilen durchlaufen
        n = len(lines)
        i = 0
        lap = 1
        try:
            while i < n:
                # Runde parsen
                hands, schupfed, tichus, wish, gift, winner, loser, points, history, i = self._parse_lap(lines, i)
                if not history:
                    continue
                # Runde speichern
                self._db.execute('''
                    INSERT INTO laps (episode_id, lap, hand0, hand1, hand2, hand3, schupfed0, schupfed1, schupfed2, schupfed3,
                    tichu0, tichu1, tichu2, tichu3, wish, gift, winner, loser, points0, points1, history) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (episode_id, lap, hands[0], hands[1], hands[2], hands[3], schupfed[0], schupfed[1], schupfed[2], schupfed[3],
                          tichus[0], tichus[1], tichus[2], tichus[3], wish, gift, winner, loser, points[0] + points[2], points[1] + points[3],
                          history))
                # Endergebnis aktualisieren
                score[0] += points[0] + points[2]
                score[1] += points[1] + points[3]
                lap += 1
        except IndexError as E:
            # Runde nicht zu Ende gespielt?
            j = n - 1
            while j > 0 and lines[j] == '':
                j -= 1
            if lines[j].startswith('Ergebnis: '):
                # Runde wurde zu Ende gespielt, der Fehler liegt woanders
                print(f'{file[-24:]}: Fehler in Runde {lap} (ab Zeile {i + 1})')
                raise E
        except Exception as E:
            print(f'{file[-24:]}: Fehler in Runde {lap} (ab Zeile {i + 1})')
            raise E
        return score

    # Runde parsen
    @staticmethod
    def _parse_lap(lines, i):
        # sicherstellen, dass zu Ende gespielt wurde
        j = i + 1
        while not lines[j].startswith('Ergebnis: '):  # wirft IndexError, wenn kein Ergebnis vorliegt
            j += 1

        # Tichukarten (die ersten 8 Karten)
        assert lines[i] == '---------------Gr.Tichukarten------------------'
        i += 1
        hands8 = [[], [], [], []]
        for player in range(0, 4):
            line = lines[i]
            i += 1
            j = line.find(' ')
            assert j != -1
            tmp = line[j + 1:].replace('10', 'Z')
            hands8[player] = stringify_cards(sorted(parse_cards(tmp), reverse=True)).split(' ')  # Karten sortieren
            assert len(set(hands8[player])) == 8

        # die restlichen 6 Karten
        assert lines[i] == '---------------Startkarten------------------'
        i += 1
        hands6 = [[], [], [], []]
        hands = [[], [], [], []]  # Karten vor dem Schupfen
        for player in range(0, 4):
            line = lines[i]
            i += 1
            j = line.find(' ')
            assert j != -1
            tmp = line[j + 1:].replace('10', 'Z')  # das sind alle Handkarten
            tmp = ' '.join([card for card in tmp.split(' ') if card not in hands8[player]])  # die restlichen 6 Karten extrahiert
            hands6[player] = stringify_cards(sorted(parse_cards(tmp), reverse=True)).split(' ')  # Karten sortieren
            assert len(set(hands6[player])) == 6
            hands[player] = hands8[player] + hands6[player]

        # Alle 56 Karten verteilt?
        assert len(set(hands[0] + hands[1] + hands[2] + hands[3]).intersection(cardlabels)) == 56

        # großes Tichu
        tichus = [-3, -3, -3, -3]  # Position in der Historie, an der ein Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor Schupfen)
        while lines[i].startswith('Grosses Tichu:'):
            line = lines[i]
            i += 1
            player = int(line[16])
            assert 0 <= player <= 3
            tichus[player] = -2

        # kleines Tichu
        while lines[i].startswith('Tichu:'):
            line = lines[i]
            i += 1
            player = int(line[8])
            assert 0 <= player <= 3
            tichus[player] = -1

        # Schupfen
        assert lines[i] == 'Schupfen:'
        i += 1
        schupfed = [['', '', ''], ['', '', ''], ['', '', ''], ['', '', '']]
        for player in range(0, 4):
            line = lines[i]
            i += 1
            j = line.find(' gibt: ')
            assert j != -1
            tmp = line[j + 7:].rstrip(' -').split(' - ')
            j = len(tmp)
            assert j == 3
            for k in range(0, 3):
                nickname, card = tmp[k].split(': ')
                card = card.replace('10', 'Z')
                assert card in hands[player]
                schupfed[player][k] = card
            if len(set(schupfed[player])) != 3:
                print(f'Zeile {i}: Ein Spieler hat keine drei unterschiedliche Karten geschupft. Überspringe die Runde.')
                while not lines[i].startswith('Ergebnis: '):  # wirft IndexError, wenn kein Ergebnis vorliegt
                    i += 1
                i += 1
                n = len(lines)
                while i < n and lines[i] == '':  # Leerzeichen (am Dateiende) überspringen
                    i += 1
                return None, None, None, None, None, None, None, None, None, None, i
            assert len(set(schupfed[player])) == 3  # 3 unterschiedliche Karten?

        # geschupfte Karten der Mitspieler aufnehmen
        hands3 = [[], [], [], []]
        for player in range(0, 4):
            hands3[player] = [schupfed[(player + 1 + k) % 4][2 - k] for k in range(0, 3)]
            assert len(set(hands3[player])) == 3

        # Handkarten nach dem Schupfen
        rest = [[], [], [], []]
        for player in range(0, 4):
            rest[player] = [card for card in hands[player] if card not in schupfed[player]] + hands3[player]
            assert len(set(rest[player])) == 14

        # Wer eine Bombe hat, wird extra angezeigt. Können wir ignorieren.
        while lines[i].startswith('BOMBE:'):
            i += 1

        # Spielverlauf
        assert lines[i] == '---------------Rundenverlauf------------------'
        i += 1
        history = []
        current_player = -1
        trick = (0, 0, 0)
        trick_player = -1
        trick_points = 0
        points = [0, 0, 0, 0]
        wish = 0
        gift = -1
        number_of_players = 4
        winner = -1
        loser = -1
        is_done = False
        while True:
            line = lines[i]
            i += 1
            if line.startswith('Wunsch:'):
                wish = line[7:]
                if wish == 'B':
                    wish = 11
                elif wish == 'D':
                    wish = 12
                elif wish == 'K':
                    wish = 13
                elif wish == 'A':
                    wish = 14
                else:
                    wish = int(wish)
                    assert 2 <= wish <= 14
            elif line.startswith('Tichu: '):
                player = int(line[8])
                assert 0 <= player <= 3
                tichus[player] = len(history)
                if len(set(rest[player])) < 14:
                    assert tichus[player] > 0
                    tichus[player] -= 1
                    print(f'Zeile {i}: Tichu-Ansage korrigiert (Spieler hat erst Karten gelegt und dann Tichu gesagt)')
            elif line.startswith('Drache an: '):
                continue
            elif line.startswith('Ergebnis: '):
                # Runde ist vorbei!
                assert is_done
                assert winner >= 0
                result: list = line[10:].split(' - ')
                result[0] = int(result[0])
                result[1] = int(result[1])
                if number_of_players == 2:
                    # Doppelsieg
                    assert loser == -1
                    points = [0, 0, 0, 0]
                    points[winner] = 200
                else:
                    assert 0 <= loser <= 3
                    assert trick_points == 0  # es wurde schon abgeräumt
                    # Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
                    leftover_points = sum_card_points(parse_cards(' '.join(rest[loser])))
                    points[(loser + 1) % 4] += leftover_points
                    # Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
                    points[winner] += points[loser]
                    points[loser] = 0
                    assert sum(points) == 100
                # Bonus für Tichu-Ansage
                for player in range(0, 4):
                    if tichus[player] == -2:  # großes Tichu
                        points[player] += 200 if player == winner else -200
                    elif tichus[player] >= -1:  # normales Tichu
                        points[player] += 100 if player == winner else -100
                # Rechenfehler von Brettspielwelt korrigieren
                if result != [points[0] + points[2], points[1] + points[3]]:
                    # Kann das Ergebnis von Brettspielwelt stimmen?
                    # Bonus vom Brettspielwelt-Ergebnis abziehen.
                    tmp = result.copy()
                    for player in range(0, 4):
                        if tichus[player] == -2:  # großes Tichu
                            tmp[player % 2] += -200 if player == winner else +200
                        elif tichus[player] >= -1:  # normales Tichu
                            tmp[player % 2] += -100 if player == winner else +100
                    if not (sum(tmp) == 100 or ((tmp[0] == 200 and tmp[1] == 0) or (tmp[0] == 0 and tmp[1] == 200))):
                        # print(f'Zeile {i}: Endergebnis {result[0]}/{result[1]} - Brettspielwelt hat sich verrechnet. Korrigiere auf {points[0] + points[2]}/{points[1] + points[3]}.')
                        result = [points[0] + points[2], points[1] + points[3]]
                    # if result != [points[0] + points[2], points[1] + points[3]]:
                    #    print(f'Zeile {i}: Verrechnet! Brettspielwelt: {result} - Ich: {[points[0] + points[2], points[1] + points[3]]}, Tichus: {tichus}')
                    assert result == [points[0] + points[2], points[1] + points[3]]
                # Daten über die Runde zurückgeben
                n = len(lines)
                while i < n and lines[i] == '':  # Leerzeichen (am Dateiende) überspringen
                    i += 1
                for player in range(0, 4):
                    hands[player] = ' '.join(hands[player])
                    schupfed[player] = ' '.join(schupfed[player])
                history = ';'.join(history).rstrip('|').replace('|;', '|')
                return hands, schupfed, tichus, wish, gift, winner, loser, points, history, i
            else:  # normaler Spielzug
                player = int(line[1])
                assert 0 <= player <= 3
                assert len(rest[player]) > 0
                j = line.find(' ')
                assert j != -1
                if current_player == -1:
                    current_player = player
                take_trick = False
                if line[j + 1:] != 'passt.':
                    # es wurden Karten gelegt
                    if is_done:
                        print(f'Zeile {i}: Spieler legt Karten, aber das Spiel ist vorbei. Ignoriere diesen Zug.')
                        continue
                    cards = parse_cards(line[j + 1:].replace('10', 'Z'))
                    trick = get_figure(cards, trick[2], shift_phoenix=True)
                    trick_player = player
                    card_points = sum_card_points(cards)
                    trick_points += card_points
                    cards = stringify_cards(cards).split(' ')
                    assert len(set(cards).intersection(rest[player])) == len(cards)
                    rest[player] = [card for card in rest[player] if card not in cards]
                    if len(rest[player]) == 0:
                        number_of_players -= 1
                        assert 1 <= number_of_players <= 3
                        if number_of_players == 3:
                            winner = player
                        elif number_of_players == 2:
                            if player == (winner + 2) % 4:
                                is_done = True
                        elif number_of_players == 1:
                            for loser in range(0, 4):
                                if len(rest[loser]) > 0:
                                    break
                            is_done = True
                    if trick[0] == BOMB:
                        if current_player != player:
                            current_player = player
                    else:
                        assert player == current_player
                    tmp = ' '.join(cards)
                    history.append(f'{player},{tmp},{trick[0]},{trick[2]},{card_points}')
                else:
                    # es wurde gepasst
                    cards = []
                    assert player == current_player
                    if player == trick_player:  # der Spieler schaut auf seinen Stich
                        if trick != (1, 1, 0):  # kein Hund?
                            take_trick = True  # dann Stich kassieren
                    else:
                        assert not is_done  # 2022-05-12 nachträglich hinzugefügt - passiert, wenn der Drache als letzte Karte gelegt wird
                        history.append(f'{player}')

                # Falls der Spieler nicht nur die Karten aufgenommen hat, ist der nächste Spieler am Zug...
                if not take_trick:
                    if not is_done:
                        current_player = (player + (2 if len(cards) == 1 and cards[0] == 'Hu' else 1)) % 4
                    while True:
                        # Hat der Spieler noch Handkarten?
                        if len(rest[current_player]) > 0:
                            break
                        # Der Spieler hat keine Karten mehr. Räumt er noch den Stich ab?
                        if current_player == trick_player and (len(cards) != 1 or cards[0] != 'Hu'):
                            take_trick = True
                        current_player = (current_player + 1) % 4

                # Stich kassieren
                if take_trick:
                    assert 0 <= trick_player <= 3
                    if trick == (1, 1, 15) and not lines[i].startswith('Ergebnis: '):  # Drachen verschenken (und kein Ende wegen Doppelsieg)
                        assert gift == -1
                        if lines[i].startswith('Drache an: '):
                            line = lines[i]
                            i += 1
                            gift = int(line[12])
                        else:
                            # Manchmal wird der Drache etwas später verschenkt. Wir suchen also die Stelle.
                            j = i + 1
                            while not lines[j].startswith('Ergebnis: '):
                                if lines[j].startswith('Drache an: '):
                                    gift = int(lines[j][12])
                                    break
                                j += 1
                        assert 0 <= gift <= 3
                        points[gift] += trick_points
                    else:
                        points[trick_player] += trick_points
                    trick = (0, 0, 0)
                    trick_points = 0
                    trick_player = -1
                    history[-1] += '|'

    def episode_count(self) -> int:
        # Anzahl Episoden ermitteln
        cur = self.cursor()
        cur.execute('SELECT COUNT(*) AS n FROM episodes')
        return int(cur.fetchone()[0])

    def lap_count(self) -> int:
        # Anzahl Runden ermitteln
        cur = self.cursor()
        cur.execute('SELECT COUNT(*) AS n FROM laps')
        return int(cur.fetchone()[0])

    def first_dt(self) -> int:
        # Datum der letzten Episode
        cur = self.cursor()
        cur.execute('SELECT dt AS n FROM episodes ORDER BY id ASC LIMIT 1')
        return cur.fetchone()[0]

    def last_dt(self) -> int:
        # Datum der letzten Episode
        cur = self.cursor()
        cur.execute('SELECT dt AS n FROM episodes ORDER BY id DESC LIMIT 1')
        return cur.fetchone()[0]

    def stdev_points(self, n=1000000):
        # Mittelwert, Standardabweichung und Maximalwert für Punktedifferenz
        # n: Stichprobengröße

        # Ergebnisse
        # n=  100000: (158.7052, 109.77565983841775, 800)
        # n= 1000000: (159.45053, 110.29255089406129, 800)
        # n=10000000: (167.771586, 113.22187911814835, 800)
        # n=22042274: (179.05570223834437, 117.1560941892016, 800)

        cur = self.cursor()
        cur.execute('SELECT AVG(diff) AS diff_mean, '
                    'AVG(diff * diff) - AVG(diff) * AVG(diff) AS diff_variance,'
                    'MAX(diff) as diff_max '
                    f'FROM (SELECT ABS(points0 - points1) AS diff FROM laps LIMIT {n}) AS sub')
        mean_, variance_, max_ = cur.fetchone()
        return mean_, sqrt(variance_), max_

    def report(self):
        print(f'Zeitraum:         {self.first_dt()} bis {self.last_dt()}')
        print(f'Anzahl Episoden:  {self.episode_count()}')
        print(f'Anzahl Runden:    {self.lap_count()}')

        # Punktedifferenz
        mean_, std_, max_ = self.stdev_points()
        print(f'Punktedifferenz:  {mean_:4.1f} +-{std_:4.1f}; Max {max_:3d}')

        # Wie viele Kartenzüge gibt es pro Runde?
        cur = self.cursor()
        cur.execute('SELECT history FROM laps LIMIT 1000000')
        # cur.execute('SELECT history FROM laps')
        tricks = []
        moves = []
        for history, in tqdm(cur, total=1000000):  # history: [player,cards,cards_type,cards_value,card_points;...|...] (| == Tichu einkassiert)
            tricks.append(len(history.split('|')))
            moves.append(len(history.replace('|', ';').split(';')))
        tricks = np.array(tricks)
        moves = np.array(moves)
        moves_per_trick = moves / tricks
        print(f'Stiche/Runde:     {tricks.mean():4.1f} +-{tricks.std():4.1f}; Max {tricks.max(initial=0):3d}')
        print(f'Kartenzüge/Runde: {moves.mean():4.1f} +-{moves.std():4.1f}; Max {moves.max(initial=0):3d}')
        print(f'Züge/Stich:       {moves_per_trick.mean():4.1f} +-{moves_per_trick.std():4.1f}; Max {round(moves_per_trick.max(initial=0)):3d}')

    def print_distribution_points(self, n=10000):
        # Verteilung über Punktedifferenz
        # n: Stichprobengröße
        cur = self.cursor()
        # noinspection SqlInjection
        cur.execute('SELECT diff, count(*) AS m FROM ('
                    f'SELECT ABS(points0 - points1) AS diff FROM laps LIMIT {n}'
                    ') AS sub GROUP BY diff')
        print('Verteilung über Punktedifferenz')
        d = {}
        for diff, m in tqdm(cur):
            print(diff, m)
            d[diff] = m
        print(d)

    def print_distribution_bonus(self, n=10000):
        # Verteilung über Bonus
        # n: Stichprobengröße
        cur = self.cursor()
        cur.execute('SELECT bonus, count(*) AS m FROM ('
                    'SELECT CASE'
                    ' WHEN tichu0 = -3 THEN 0'
                    ' WHEN tichu0 = -2 THEN CASE WHEN winner = 0 THEN 200 ELSE -200 END'
                    ' WHEN tichu0 > -2 THEN CASE WHEN winner = 0 THEN 100 ELSE -100 END'
                    f' END AS bonus FROM laps LIMIT {n}'
                    ') AS sub GROUP BY bonus')
        print('Verteilung über Bonus')
        d = {}
        for bonus, m in tqdm(cur):
            print(bonus, m)
            d[bonus] = m
        print(d)
