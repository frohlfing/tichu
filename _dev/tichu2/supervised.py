# Supervised Training - Überwachtes Lernen

# todo ein Model anhand von Brettspielwelt-Daten trainieren
# todo Daten mit gleicher Struktur aus Selbstspiel mit Heuristik-Agent generieren und ein weiteres Model trainieren

import config
import json
from math import ceil
import numpy as np
from os import path, mkdir
from tichu.nnet import load_or_create_model
from tichu.callbacks import LifePlotter
import sqlite3
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.core.framework.types_pb2 import DT_STRING, DT_INT16
from tensorflow.python.data.experimental import SqlDataset
from tichu.agents import HeuristicAgent
from tichu.arena import Arena
from time import time


ACTION_SIZE = 230  # todo
ROWS = 10
COLUMNS = 10


class ExamplesDB:
    def __init__(self, file: str):
        self._file = file
        db_exists = path.exists(self._file)
        self._db = sqlite3.connect(self._file)
        if not db_exists:
            self._create_db()

    def __del__(self):
        self._db.close()

    # Datenbank erstellen
    #
    # Serialize board:
    # json.dumps(state.board.tolist()) =
    #   [[0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 1, 0, 0], [0, 2, 1, 0, 2, 0, 0], [2, 1, 1, 1, 1, 0, 2], [2, 1, 2, 1, 1, 2, 2]]
    #
    # Serialize probability:
    # json.dumps(prob.tolist()) =
    #   [0.14285714285714285, 0.14285714285714285, 0.14285714285714285, 0.14285714285714285, 0.14285714285714285, 0.14285714285714285, 0.14285714285714285]
    def _create_db(self):
        self._db.execute('''
            CREATE TABLE examples (
                id INTEGER PRIMARY KEY,
                iteration INTEGER,    
                part VARCHAR(4), 
                board VARCHAR(138),
                prob VARCHAR(147),
                reward INTEGER 
            );
            ''')

        self._db.execute('''
            CREATE INDEX examples_iteration ON examples(iteration);
            ''')

        self._db.execute('''
            CREATE INDEX examples_part ON examples(part);
            ''')

        self._db.execute('''
            CREATE INDEX examples_board_prob_reward ON examples(board, prob, reward);
            ''')

        self._db.execute('''
            CREATE INDEX examples_reward ON examples(reward);
            ''')

        self._db.commit()

    # Datenbank Cursor
    # Anwendungsbeispiel:
    #   cur = db.cursor()
    #   cur.execute('SELECT * FROM examples LIMIT 100')
    #   for id_, iteration, part, board, prob, reward in cur:
    #       print(f'{id_}; {iteration}; {part}; {board}; {prob}; {reward}')
    def cursor(self) -> sqlite3.Cursor:
        return self._db.cursor()

    def insert(self, iteration, examples: list):
        # examples: Trainingsdaten = [ (board, probability, reward) ]
        cur = self._db.cursor()
        n = len(examples)
        for i, data in enumerate(examples):
            ratio = (i + 1) / n
            part = 'test' if ratio > 0.9 else 'val' if ratio > 0.8 else 'train'
            board, prob, reward = data
            board = json.dumps(board.tolist())
            prob = json.dumps(prob.tolist())
            cur.execute('SELECT id FROM examples WHERE board=? AND prob=? AND reward=?', (board, prob, reward))
            if cur.fetchone() is None:
                self._db.execute('''
                    INSERT INTO examples (iteration, part, board, prob, reward) 
                    VALUES (?, ?, ?, ?, ?)
                    ''', (iteration, part, board, prob, reward))
        self._db.commit()

        # Falls für mehrere Aktionen fälschlicherweise (was sich erst nach mehr als 3 Spielzügen zeigt) der maximale
        # Gewinn geschätzt wird, kann es für dieselbe Brettstellung unterschiedliche Spielausgänge geben. Da auch die
        # Länge des Spiels in diesen Fällen variieren kann, kann auch prob variieren!
        # Diese Fälle werden zu 'train'-Parts, um sicherzugehen, das ausschließlich unbekannte Stellungen validiert und
        # getestet werden.
        cur.execute('''
            UPDATE examples SET part = 'train' WHERE board IN (
                SELECT board
                FROM examples
                GROUP BY board
                HAVING COUNT(*) > 1
            )
            ''')
        self._db.commit()

    # def update(self, id_: int, board, prob, reward):
    #     cur = self._db.cursor()
    #     cur.execute('UPDATE examples SET board=?, prob=?, reward=? WHERE id=?', (board, prob, reward, id_))
    #     self._db.commit()

    # def delete(self, id_: int):
    #     cur = self._db.cursor()
    #     cur.execute('DELETE FROM examples WHERE id=?', (id_,))
    #     self._db.commit()

    def count(self, part='train') -> int:
        cur = self._db.cursor()
        cur.execute('SELECT COUNT(*) AS n FROM examples WHERE part=?', (part,))
        return int(cur.fetchone()[0])

    def last_iteration(self) -> int:
        cur = self._db.cursor()
        cur.execute('SELECT MAX(iteration) AS n FROM examples')
        n = cur.fetchone()[0]
        return int(n) if n else 0

    def get(self, part, limit: int):
        cur = self._db.cursor()
        cur.execute('SELECT board, prob, reward FROM examples WHERE part=? LIMIT ?', (part, limit))
        # return np.array(cur.fetchall())
        x = []
        p = []
        v = []
        for board, prob, reward in cur:
            x.append(np.array(json.loads(board)))
            p.append(np.array(json.loads(prob)))
            v.append(reward)
        return np.array(x), np.array(p), np.asarray(v)

    def generator(self, part='train'):
        # noinspection SqlInjection
        sql = f'SELECT board, prob, reward FROM examples WHERE part="{part}"'
        i = 0
        x = p = v = []
        while True:
            dataset = SqlDataset('sqlite', self._file, sql, (DT_STRING, DT_STRING, DT_INT16))
            for board, prob, reward in dataset:
                if i == 0:
                    x = np.zeros((config.BATCH_SIZE, ROWS, COLUMNS), dtype=int)
                    p = np.zeros((config.BATCH_SIZE, ACTION_SIZE), dtype=float)
                    v = np.zeros((config.BATCH_SIZE,), dtype=int)
                x[i] = np.array(json.loads(board.numpy().decode('utf-8')))
                p[i] = np.array(json.loads(prob.numpy().decode('utf-8')))
                v[i] = reward.numpy()
                i += 1
                if i == config.BATCH_SIZE:
                    yield x, (p, v)  # Batch zurückgeben
                    i = 0


class Coach:
    def __init__(self, folder: str):
        if not path.exists(path.join(config.DATA_PATH, folder)):
            mkdir(path.join(config.DATA_PATH, folder))
        self._db = ExamplesDB(path.join(config.DATA_PATH, folder, 'db.sqlite'))
        self._hdf5 = path.join(config.DATA_PATH, folder, 'model.h5')
        self._plot = path.join(config.DATA_PATH, folder, 'plot.pkl')
        self._model = None

    def self_play(self):
        j = self._db.last_iteration()
        if j >= config.ITERATIONS:
            return
        print('* Self Play *')
        heu = HeuristicAgent()
        for i in range(j, config.ITERATIONS):
            print(f'Iteration #{i + 1} / {config.ITERATIONS}')

            # Heuristik-Agent gegen sich selber spielen lassen
            arena = Arena([heu, heu, heu, heu], max_episodes=config.SELFPLAY, capture=True)
            arena.play()

            # Trainingsdaten aus dem Spielverlauf extrahieren
            # todo
            examples = []
            for episode, (data, reward) in enumerate(arena.history):
                for state, prob, action in data:
                    r = reward if state.player == 0 else -reward  # reward bezieht sich auf Spieler 0
                    state = state.canonical()  # falls Spieler 1 an der Reihe ist, Spielsteine tauschen
                    for b, p in state.symmetries(prob):  # auch gleichwertige Stellungen auflisten
                        examples.append((b, p, r))

            # Trainingsdaten speichern
            # self._db.insert(i + 1, arena.examples(with_symmetries=True))
            self._db.insert(i + 1, examples)

    # Model trainieren und auswerten
    def train(self):
        print('* Train *')
        if not self._model:
            self._model = load_or_create_model(self._hdf5)

        # https://www.tensorflow.org/beta/guide/checkpoints
        callbacks = []

        # Plotter
        plotter = LifePlotter(self._plot)
        callbacks.append(plotter)

        # Model speichern, wenn sich Loss verbessert hat
        # https://www.tensorflow.org/beta/tutorials/keras/save_and_restore_models#save_checkpoints_during_training
        # file = f 'chk{epoch:03d}-{val_loss:.2f}.h5'
        callbacks.append(ModelCheckpoint(monitor='val_loss', filepath=self._hdf5, save_best_only=True, save_weights_only=False))

        # Anzahl Epochen, in welche sich Loss kleiner werden muss. Ansonsten wird das Training abgebrochen
        if 0 < config.PATIENCE_STOPPING < config.EPOCHS:
            callbacks.append(EarlyStopping(monitor='val_loss', patience=config.PATIENCE_STOPPING))

        # Anzahl Epochen, in welche Loss kleiner werden muss. Ansonsten wird die Lernrate mit 0.1 multipliziert.
        if (0 < config.PATIENCE_REDUCE < config.EPOCHS) and (0 < config.REDUCE_FACTOR < 1):
            callbacks.append(ReduceLROnPlateau(monitor='val_loss', patience=config.PATIENCE_REDUCE, factor=config.REDUCE_FACTOR))

        # Model trainieren
        # Make sure that your dataset or generator can generate at least `steps_per_epoch * epochs` batches.
        time_start = time()
        steps_per_epoch = ceil(self._db.count('train') / config.BATCH_SIZE)
        validation_steps = ceil(self._db.count('val') / config.BATCH_SIZE)
        assert steps_per_epoch > 0
        assert validation_steps > 0
        history = self._model.fit(self._db.generator('train'),
                                  epochs=config.EPOCHS,
                                  steps_per_epoch=steps_per_epoch,
                                  validation_data=self._db.generator('val'),
                                  validation_steps=validation_steps,
                                  callbacks=callbacks,
                                  verbose=1)  # 0 = silent, 1 = progress bar, 2 = one line per epoch
        print(f'Time total: {(time() - time_start) / 60:5.1f} minutes')
        self._model = load_or_create_model(self._hdf5)  # beste Model zurückholen
        return history

    @staticmethod
    def untrained_performance():
        print('* Trefferquote beim Raten (berechnet) *')
        p_acc = 1 / ACTION_SIZE
        v_min = -1
        v_max = 1
        v_mae = (v_max - v_min) / 2
        print(f'p_acc: {p_acc:.5f}')
        print(f'v_mae: {v_mae:.5f}')

    def untrained_performance_empirical(self):
        print('* Trefferquote beim Raten (empirisch) *')
        # eine Stichprobe der Zielwerte holen
        _, p_test, v_test = self._db.get('test', 10000)
        n = len(p_test)  # Stichprobengröße
        # die Zieldaten mischen und als "Vorhersage" nehmen
        p_pred = p_test.copy()
        v_pred = v_test.copy()
        np.random.shuffle(p_pred)
        np.random.shuffle(v_pred)
        # Metrics berechnen
        p_acc = sum([np.argmax(p_test[i]) == np.argmax(p_pred[i]) for i in range(n)]) / n
        v_mae = np.mean(np.abs(v_test - v_pred))
        print(f'n: {n}')
        print(f'p_acc: {p_acc:.5f}')
        print(f'v_mae: {v_mae:.5f}')

    def performance(self):
        print('* Leistungstest *')
        if not self._model:
            self._model = load_or_create_model(self._hdf5)
        steps = ceil(self._db.count('test') / config.BATCH_SIZE)
        _, _, _, p_acc, v_mae = self._model.evaluate(self._db.generator('test'), steps=steps, verbose=1)
        print(f'n: {steps * config.BATCH_SIZE}')
        print(f'p_acc: {p_acc:.5f}')
        print(f'v_mae: {v_mae:.5f}')

    def performance_manually(self):
        print('* Leistungstest (manual per Stichprobe berechnet) *')
        # eine Stichprobe der Zielwerte holen
        _, p_test, v_test = self._db.get('test', 10000)
        n = len(p_test)  # Stichprobengröße

        # Vorhersage treffen
        if not self._model:
            self._model = load_or_create_model(self._hdf5)
        steps = ceil(n / config.BATCH_SIZE)
        p_pred, v_pred = self._model.predict(self._db.generator('test'), steps=steps, verbose=1)
        p_pred = p_pred[:n]
        v_pred = v_pred[:n].flatten()

        # Metrics berechnen
        p_acc = sum([np.argmax(p_test[i]) == np.argmax(p_pred[i]) for i in range(n)]) / n
        v_mae = np.mean(np.abs(v_test - v_pred))
        print(f'n: {n}')
        print(f'p_acc: {p_acc:.5f}')
        print(f'v_mae: {v_mae:.5f}')


if __name__ == '__main__':
    subfolder = 'supervised_v1'  # LAYERS x FILTERS _ DEPTH
    print(f'Coaching "{subfolder}"')
    coach = Coach(subfolder)
    coach.self_play()
    coach.train()
    coach.untrained_performance()  # Trefferquote beim Raten (berechnet)
    coach.untrained_performance_empirical()  # Trefferquote beim Raten (empirisch)
    coach.performance()  # Leistungstest
    coach.performance_manually()  # Leistungstest (manual per Stichprobe berechnet)
