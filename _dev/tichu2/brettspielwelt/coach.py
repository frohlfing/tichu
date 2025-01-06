import math
import config
import numpy as np
from os import environ, path, mkdir, listdir
from datetime import datetime
from tichu.brettspielwelt.samples import load_samples
from tichu.nnet import load_or_create_model, clone_model, y_labels
from tichu.callbacks import CategoricalMetrics, LifePlotter, Logger
from time import time
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

# Tensorflow Log Level
# 0 = all messages are logged (default behavior)
# 1 = INFO messages are not printed
# 2 = INFO and WARNING messages are not printed
# 3 = INFO, WARNING, and ERROR messages are not printed
environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
# from tensorflow.python.ops.confusion_matrix import confusion_matrix


# Ein Model anhand von Brettspielwelt-Daten durch überwachtes Lernen (Supervised Learning) trainieren
class Coach:
    # version: Laufende Nummer
    def __init__(self, part: str, version=1):
        assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points')
        self._part = part
        folder = path.join(config.DATA_PATH, 'brettspielwelt/models')
        if not path.exists(folder):
            mkdir(folder)
        folder = path.join(folder, f'{part}_{version:02d}')
        if not path.exists(folder):
            mkdir(folder)
        self._hdf5 = path.join(folder, 'model.h5')
        self._plot = path.join(folder, 'plot.pkl')
        self._checkpoints = path.join(folder, 'checkpoints')  # ckpt
        if not path.exists(self._checkpoints):
            mkdir(self._checkpoints)
        self._model = None
        self._log_file = path.join(folder, 'log.txt')
        self._log_stream = None

    # Model trainieren und auswerten
    def train(self, num=1):
        self._start_log()

        if not self._model:
            self._model = load_or_create_model(self._hdf5, self._part)

        # Beispieldaten holen
        x_train, y_train = load_samples('train', self._part, num=num, n=1000000, verbose=True)
        x_val, y_val = load_samples('val', self._part, num=num, n=100000, verbose=True)

        # https://www.tensorflow.org/beta/guide/checkpoints
        callbacks = []

        # Metriken bereitstellen, die erst am Ende einer Epoche berechnet werden können
        compute_metrics = CategoricalMetrics(validation_data=(x_val, y_val))
        callbacks.append(compute_metrics)

        # Plotter
        if self._part in ('bonus', 'points'):
            metrics = 'loss', 'mae'
            plotter = LifePlotter(self._plot,
                                  width=12, height=6,
                                  nrows=1, ncols=2,
                                  metrics=metrics,
                                  colors=('orange', 'blue'))
        else:
            metrics = 'loss', 'cm', 'acc', 'recall', 'precision', 'f1'
            plotter = LifePlotter(self._plot,
                                  width=12, height=6,
                                  nrows=2, ncols=3,
                                  metrics=metrics,
                                  colors=('red', 'black', 'blue', 'orange', 'green', 'blue'),
                                  cm_labels=y_labels(self._part),
                                  cm_normalize=True)
        callbacks.append(plotter)
        
        # Logger
        logger = Logger(self._log_stream, metrics=metrics)
        callbacks.append(logger)
        
        # Model speichern, wenn sich Loss verbessert hat
        # https://www.tensorflow.org/beta/tutorials/keras/save_and_restore_models#save_checkpoints_during_training
        # file = 'ckpt-{epoch:03d}-{val_loss:.2f}.h5'
        callbacks.append(ModelCheckpoint(monitor='loss', filepath=path.join(self._checkpoints, 'weights-{epoch:04d}-{loss:.3f}-{val_loss:.3f}.h5'), save_best_only=False, save_weights_only=True))

        # Anzahl Epochen, in welche Loss kleiner werden muss. Ansonsten wird das Training abgebrochen.
        if 0 < config.PATIENCE_STOPPING < config.EPOCHS:
            callbacks.append(EarlyStopping(monitor='val_loss', patience=config.PATIENCE_STOPPING))

        # Anzahl Epochen, in welche Loss kleiner werden muss. Ansonsten wird die Lernrate mit 0.1 multipliziert.
        if (0 < config.PATIENCE_REDUCE < config.EPOCHS) and (0 < config.REDUCE_FACTOR < 1):
            callbacks.append(ReduceLROnPlateau(monitor='val_loss', patience=config.PATIENCE_REDUCE, factor=config.REDUCE_FACTOR))

        # Training fortsetzen?
        epoch_offset = plotter.epochs
        if epoch_offset > 0:
            print(f'Setze Training ab Epoche {epoch_offset + 1} fort')
            assert epoch_offset < config.EPOCHS

        # Trainieren
        time_start = time()
        history = self._model.fit(x_train, y_train,
                                  batch_size=config.BATCH_SIZE,
                                  epochs=config.EPOCHS,
                                  initial_epoch=epoch_offset,
                                  validation_data=(x_val, y_val),
                                  callbacks=callbacks,
                                  verbose=1)  # 0 = silent, 1 = progress bar, 2 = one line per epoch

        # Speichern
        self._model.save(self._hdf5)

        print(f'Time total: {(time() - time_start) / 60:5.1f} minutes')
        self._log(f'Time total: {(time() - time_start) / 60:5.1f} minutes')

        # noinspection PyUnboundLocalVariable
        return history

    def restore_from_checkpoint(self, best=False, save_model=False):
        files = sorted(listdir(self._checkpoints), reverse=True)
        if len(files) == 0:
            return

        file = files[0]
        if best:
            v_min = math.inf
            for f in files:
                epoch, loss, val_loss = f[8:-3].split('-')
                v = float(loss)
                if v_min > v:
                    v_min = v
                    file = f

        file = path.join(self._checkpoints, file)

        if not self._model:
            self._model = load_or_create_model(self._hdf5, self._part)

        print(f'Lade Gewichte {file}')
        self._model.load_weights(file)
        # print(self._model.get_layer('p1').get_weights()[:10])

        if save_model:
            print(f'Speicher Model {self._hdf5}')
            self._model.save(self._hdf5)

    def evaluate(self, untrained=False, check=False):
        """
        Model testen

        :param untrained: Die Messung wird an einem frischen Modell durchgeführt. Default: False
        :param check: Das Ergebnis wird mittels model.evaluate() überprüft. Default: False
        """
        if not self._model:
            self._model = load_or_create_model(self._hdf5, self._part)
        model = clone_model(self._model, part=self._part, copy_weights=False) if untrained else self._model

        # Zielwerte holen
        # steps = config.TEST_STEPS
        # n = config.BATCH_SIZE * steps  # max. Stichprobengröße
        # gen = batch_generator('test', self._part, n=n, endless=False)
        # time_start = time()
        # x_test = y_test = np.array([])
        # try:
        #     _, x_test, y_test = next(gen)
        # except StopIteration:
        #     print('EOF')
        # seconds_gen = time() - time_start
        x_test, y_test = load_samples('test', self._part)
        n = len(y_test)  # Stichprobengröße

        # Vorhersage treffen
        time_start = time()
        y_pred = model.predict(x_test, verbose=0)
        seconds_nnet = time() - time_start

        print()
        print(f'Model: {model.name}' + (' (untrainiert)' if untrained else ''))
        print(f'Stichprobengröße: {n}')
        print(f'NNet-Zeit: {seconds_nnet:5.3f} Sekunden')

        # Metrics berechnen
        print()
        labels = y_labels(self._part)

        if self._part in ('bonus', 'points'):
            print('Mittlerer absoluter Fehler (MAE)')
            y_test_argmax = y_pred_argmax = None
            y_pred = y_pred.flatten()
            y_mae = np.mean(np.abs(y_test - y_pred))
            print(f'y_mae: {y_mae:.5f}')
        else:
            assert y_test.shape[1] == len(labels)
            print('Genauigkeit (ACC)')
            y_test_argmax = y_test.argmax(axis=1)
            y_pred_argmax = np.array(y_pred).argmax(axis=1)
            y_acc = np.mean(y_test_argmax == y_pred_argmax)
            print(f'y_acc: {y_acc:.5f}')

        if check:
            print('Überprüfe Ergebnis...')
            y_eval = model.evaluate(x=x_test, y=y_test, verbose=1)
            if self._part in ('bonus', 'points'):
                loss, y_mae = y_eval
                print(f'y_mae: {y_mae:.5f}')
            else:
                loss, y_acc = y_eval
                print(f'y_acc: {y_acc:.5f}')

        # # Distribution - Verteilung der Daten ermitteln und anzeigen
        # print()
        # print('Verteilung der Daten')
        # i, c = np.unique(y_test_argmax, return_counts=True)
        # d = dict(zip(i, c))  # pro Index die Anzahl im Dictionary ablegen
        # print('Idx | Label       |  Count')
        # for i, label in enumerate(labels):
        #     print(f'{i:3d} | {label:11s} | {d[i] if i in d else 0:6d}')

        # Confusion Matrix, Recall-, Precision- und F1-Score
        # Spalten == Vorhersage, Zeilen == reale Werte
        if self._part not in ('bonus', 'points'):
            print()
            print('Confusion Matrix')
            # cm = confusion_matrix(labels=y_test_argmax, predictions=y_pred_argmax, num_classes=len(labels)).numpy()
            # cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]  # normalisieren
            cm = confusion_matrix(y_true=y_test_argmax, y_pred=y_pred_argmax, normalize='true')
            for r, row in enumerate(cm):
                if r == 0:
                    print(''.ljust(10), end='')
                    ln = '|-'.rjust(10)
                    for c, v in enumerate(row):
                        print('Pred 0' if c == 0 else f'{c:6d}', end='')
                        ln += ''.ljust(6, '-')
                    print(f'\n{ln}')
                for c, v in enumerate(row):
                    if c == 0:
                        print('True  0 | ' if r == 0 else f'{r:7d} | ', end='')
                    print(f'  {v:.2f}', end='')
                print()

            y_recall = recall_score(y_test_argmax, y_pred_argmax, average='macro', zero_division=0)
            print(f'y_recall: {y_recall:.5f}')

            y_precision = precision_score(y_test_argmax, y_pred_argmax, average='macro', zero_division=0)
            print(f'y_precision: {y_precision:.5f}')

            y_f1 = f1_score(y_test_argmax, y_pred_argmax, average='macro', zero_division=0)
            print(f'y_f1: {y_f1:.5f}')

    def _start_log(self):
        if self._log_stream is None:
            self._log_stream = open(self._log_file, 'a')
            file_size = path.getsize(self._log_file)
            if file_size:
                self._log_stream.write('\n')
        now = datetime.now()
        self._log_stream.write('**** Starte Training *****\n')
        self._log_stream.write(now.strftime('%Y-%m-%d %H:%M:%S') + '\n')
        self._log_stream.write('\n')
        self._log_stream.write(f'EPOCHS={config.EPOCHS}\n')
        self._log_stream.write(f'BATCH_SIZE={config.BATCH_SIZE}\n')
        self._log_stream.write(f'TRAIN_STEPS={config.TRAIN_STEPS}\n')
        self._log_stream.write(f'VAL_STEPS={config.VAL_STEPS}\n')
        # self._log_stream.write(f'TEST_STEPS={config.TEST_STEPS}\n')
        self._log_stream.write(f'SQL_RATE={config.SQL_RATE}\n')
        self._log_stream.write(f'ACTIVATION={config.ACTIVATION}\n')
        self._log_stream.write(f'OPTIMIZER={config.OPTIMIZER}\n')
        self._log_stream.write(f'LR={config.LR}\n')
        self._log_stream.write(f'L2={config.L2}\n')
        self._log_stream.write(f'DROPOUT={config.DROPOUT}\n')
        # self._log_stream.write(f'LAYERS={config.LAYERS}\n')
        # self._log_stream.write(f'FILTERS={config.FILTERS}\n')
        # self._log_stream.write(f'KERNEL_SIZE={config.KERNEL_SIZE}\n')
        # self._log_stream.write(f'DENSE_UNITS={config.DENSE_UNITS}\n')
        self._log_stream.write(f'PATIENCE_STOPPING={config.PATIENCE_STOPPING}\n')
        self._log_stream.write(f'PATIENCE_REDUCE={config.PATIENCE_REDUCE}\n')
        self._log_stream.write(f'REDUCE_FACTOR={config.REDUCE_FACTOR}\n')
        self._log_stream.write('\n')
        self._log_stream.flush()
        
    def _log(self, s: str = ''):
        self._log_stream.write(s + '\n')
        self._log_stream.flush()
