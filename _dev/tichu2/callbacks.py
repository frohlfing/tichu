import _io
import itertools
import types
from time import time
import matplotlib.pyplot as plt
import numpy as np
from os import environ, path
import pickle
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

# Tensorflow Log Level
# 0 = all messages are logged (default behavior)
# 1 = INFO messages are not printed
# 2 = INFO and WARNING messages are not printed
# 3 = INFO, WARNING, and ERROR messages are not printed
environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
from keras.callbacks import Callback

__all__ = 'CategoricalMetrics', 'LifePlotter', 'Logger'


# Confusion Matrix (Wahrheitsmatrix) als Metrik für unausgeglichene Klassifikationsprobleme (unbalanced classes)
#
# Quellen
# https://www.saracus.com/blog/performance-metriken-klassifikation-2-2/
# https://neptune.ai/blog/implementing-the-macro-f1-score-in-keras
# https://stackoverflow.com/questions/49005892/keras-confusion-matrix-at-every-epoch
# https://medium.com/@thongonary/how-to-compute-f1-score-for-each-epoch-in-keras-a1acd17715a2
# https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html
#
# Die Verwendung einer Metrik-Funktion in Keras ist nicht der richtige Weg, um F1 oder ähnliches zu berechnen.
# Der Grund dafür ist, dass die Metrik bei jedem Batch-Schritt aufgerufen und daraus einen Durchschnittswert gebildet
# wird. Und das wäre nicht der richtige F1-Score! Der F1-Score kann erst am Ende einer Epoche berechnet werden.
# Aus diesem Grund wurde der F1-Score aus den metrischen Funktionen ab Keras 2.0 entfernt.
# Der richtige Weg, um den F1-Score zu berechnen, besteht darin, eine benutzerdefinierte Callback-Funktion zu verwenden.
#
# Confusion Matrix als Metrik für ein binäres Klassifikationsproblem:
#        | Pred. 0       1
#        |----------------
# True 0 |      TN      FP
#      1 |      FN      TP
#
# Für Multi-Class-Probleme berechnet man Precision, Recall und F1-Score für jede Klasse einzeln. Die Gesamtleistung ist
# der Durchschnitt der einzelnen Leistungen. Das Verfahren nennt sich Macro-Averaging.
# Bei Micro-Averaging bildet man dagegen eine neue Confusion Matrix: TP = SUM𝑖(TP𝑖); FP = SUM𝑖(FP𝑖); etc.
# Nachteil: Überrepräsentierte Klassen werden stärker gewichtet.
#
# Die Precision gibt den Anteil an richtig vorhergesagten positiven Ergebnissen (TP) bezogen auf die Gesamtheit aller
# als positiv vorhergesagten Ergebnisse (P*) an.
# Zum Beispiel sollte beim Spamfilter die Precision sehr hoch sein, da wichtige E-Mails besser nicht als Spam
# klassifiziert werden sollten.
#
# from keras import backend as K
# def precision(y_true, y_pred):
#     true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))  # TP
#     predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))      # P* = TP + FP
#     return true_positives / (predicted_positives + K.epsilon())
#
# Der Recall, auch Sensitivität genannt, ist eine Metrik, die uns sagt, wie gut das Modell in der Lage ist, positive
# Ergebnisse zu identifizieren.
# Zum Beispiel sollte bei einer Kindersicherung der Recall sehr hoch sein, damit jeder nicht-jugendfreie Film
# herausgefiltert wird.
#
# def recall(y_true, y_pred):  # TPR
#     true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))  # TP (Anteil der korrekt positiv klassifizierten Ergebnisse)
#     possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))       # P == TP + FN (Gesamtheit der tatsächlich positiven Ergebnisse)
#     return true_positives / (possible_positives + K.epsilon())
#
# Der F1-Score ist das harmonische Mittel aus Precision und Recall und wird häufig als zusammenfassende Metrik
# verwendet. Je größer der Wert, desto besser.
# f1 = 2 / (1/precision + 1/recall)
#    = 2 / (recall/(precision * recall) + precision/(precision * recall))
#    = 2 * (precision * recall) / (recall + precision)
#
# def f1_score(y_true, y_pred):
#     pre = precision(y_true, y_pred)
#     rec = recall(y_true, y_pred)
#     return 2 * ((pre * rec) / (pre + rec + K.epsilon()))

class CategoricalMetrics(Callback):
    def __init__(self,
                 validation_data=(),  # Validierungsdaten (x, y). y ist one-hot-kodiert.
                 metrics=('f1', 'recall', 'precision', 'cm')):
        super().__init__()
        self._data = validation_data
        self._is_generator = isinstance(validation_data, types.GeneratorType)
        self._metrics = metrics
        self._scores = {}

    def set_validation_data(self, validation_data):
        self._data = validation_data

    def on_train_begin(self, logs=None):
        for metric in self._metrics:
            self._scores[metric] = []

    def on_epoch_end(self, epoch, logs=None):
        # Vorhersage treffen
        if self._is_generator:
            x, y_true_argmax = next(self._data)
        else:
            x, y_true_argmax = self._data
        # y_true_argmax = np.argmax(y_true, axis=1)
        y_pred = self.model.predict(x, verbose=0)
        y_pred_argmax = np.argmax(y_pred, axis=1)

        # Metriken berechnen
        for metric in self._metrics:
            if metric == 'f1':
                score = f1_score(y_true_argmax, y_pred_argmax, average='macro', zero_division=0)
            elif metric == 'recall':
                score = recall_score(y_true_argmax, y_pred_argmax, average='macro', zero_division=0)
            elif metric == 'precision':
                score = precision_score(y_true_argmax, y_pred_argmax, average='macro', zero_division=0)
            elif metric == 'cm':  # Confusion Matrix
                score = confusion_matrix(y_true=y_true_argmax, y_pred=y_pred_argmax)
            else:
                raise Exception(f'Metric {metric} is not supported by the callback.')
            self._scores[metric].append(score)
            logs[f'val_{metric}'] = score  # für nachfolgenden Callbacks die Ergebnisse zum Log hinzufügen


class LifePlotter(Callback):
    def __init__(self, file: str,
                 width=9, height=6,  # Breite und Höhe der Chart in inches
                 nrows=3, ncols=3,   # Dimension der Chart
                 metrics=('loss', 'acc', 'mae', 'f1', 'recall', 'precision', 'cm'),
                 colors=('blue', 'orange', 'green', 'blue', 'orange', 'green', 'red', 'red', 'black'),
                 validation=True,    # Metrics auch für die Validierungsdaten anwenden
                 cm_labels=(),       # Klassenbezeichnungen für Confusion Matrix
                 cm_normalize=True):  # Werte für Confusion Matrix normalisieren
        super().__init__()
        self._file = file
        self._figsize = width, height
        self._dim = nrows, ncols
        self._png = path.splitext(file)[0] + '.png'
        self._metrics = metrics
        self._colors = colors
        self._val = validation
        self._x = []
        self._y_train = {}
        self._y_val = {}
        self._cm_labels = cm_labels
        self._cm_normalize = cm_normalize
        self.reset()
        if path.exists(self._file):
            self.load()
        # self.show()

    def reset(self):
        self._x = []
        self._y_train = {metric: [] for metric in self._metrics}
        self._y_val = {metric: [] for metric in self._metrics}

    def load(self):
        with open(self._file, 'rb') as fp:
            # noinspection PickleLoad
            self._x, self._y_train, self._y_val = pickle.load(fp)

    def save(self):
        with open(self._file, 'wb') as fp:
            pickle.dump((self._x, self._y_train, self._y_val), fp)
        plt.savefig(self._png)

    # noinspection PyUnusedLocal
    def on_train_begin(self, logs=None):
        plt.ion()  # enable interactive mode
        if not plt.get_fignums():
            self._render()
            plt.show()  # returned immediately in interactive mode
            plt.pause(0.001)

    # noinspection PyUnusedLocal
    def on_train_end(self, logs=None):
        plt.ioff()  # disable interactive mode
        # plt.close()

    # noinspection PyUnusedLocal
    def on_epoch_end(self, epoch, logs=None):
        epoch = len(self._x) + 1  # so muss in fit() nicht zwingend initial_epoch angegeben werden
        self._x.append(epoch)
        for i, metric in enumerate(self._metrics):
            if metric == 'cm':  # Confusion Matrix?
                self._y_val[metric] = logs.get(f'val_{metric}')
                self._plot_confusion_matrix(metric)
            else:
                self._y_train[metric].append(logs.get(metric))
                self._y_val[metric].append(logs.get(f'val_{metric}'))
                self._plot_metric(metric)
        self.save()

    def show(self, blocking=True):
        if plt.get_fignums():
            return  # wird bereits angezeigt
        if blocking:
            plt.ioff()  # disable interactive mode
        else:
            plt.ion()  # enable interactive mode
        self._render()
        plt.show()  # returned immediately in interactive mode
        plt.pause(0.001)

    @staticmethod
    def close():
        plt.close()

    def _render(self):
        plt.figure(figsize=self._figsize)  # Breite x Höhe
        for metric in self._metrics:
            if metric == 'cm':  # Confusion Matrix?
                self._plot_confusion_matrix(metric)
            else:
                self._plot_metric(metric)

    def _plot_metric(self, metric: str):
        assert metric != 'cm'
        index = self._metrics.index(metric)
        plt.subplot(self._dim[0], self._dim[1], index + 1)  # rows, cols, index
        lines = []
        if self._val:
            lines += plt.plot(self._x, self._y_train.setdefault(metric), color='black', linestyle=':', marker='', label='Training')
            lines += plt.plot(self._x, self._y_val.setdefault(metric), color=self._colors[index], linestyle='-', marker='', label='Validierung')
        else:
            lines += plt.plot(self._x, self._y_train.setdefault(metric), color=self._colors[index], linestyle='-', marker='', label='Training')
        plt.legend(handles=lines, loc='upper left')
        plt.xlabel('Epochen')
        plt.ylabel(metric)
        plt.grid(True)
        plt.draw()
        plt.pause(0.001)

    def _plot_confusion_matrix(self, metric: str):
        assert metric == 'cm'
        # Letzte Confusion Matrix holen
        cm = np.asarray(self._y_val.setdefault(metric, [[], []]))
        if cm.ndim != 2:
            cm = np.array([[], []])

        # Matrix normalisieren
        # todo: wirf manchmal das:  RuntimeWarning: invalid value encountered in true_divide
        if self._cm_normalize:
            cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        # Subplot auswählen
        index = self._metrics.index(metric)
        plt.subplot(self._dim[0], self._dim[1], index + 1)  # rows, cols, index

        # Confusion Matrix als Bild anzeigen
        # noinspection PyUnresolvedReferences
        color_map = plt.cm.Blues  # matplotlib colour map
        heatmap = plt.imshow(cm, interpolation='nearest', cmap=color_map)

        # Farbskala
        plt.colorbar(heatmap)

        # Werte in die Zellen setzen
        thresh = cm.max(initial=0) / 2.  # threshold
        for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
            v = f'{cm[i, j]:.2f}' if self._cm_normalize else cm[i, j]
            plt.text(j, i, v, horizontalalignment='center', color='white' if cm[i, j] > thresh else 'black')

        # Achsen
        plt.xlabel('val_pred')
        plt.ylabel('val_true')
        tick_marks = np.arange(len(self._cm_labels))
        plt.xticks(tick_marks, self._cm_labels, rotation=90)
        plt.yticks(tick_marks, self._cm_labels)

        # Anzeige neu aktualisieren
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)

    @property
    def epochs(self) -> int:  # pragma: no cover
        return len(self._x)


class Logger(Callback):
    def __init__(self,
                 file_or_stream=None,  # Dateiname oder Stream
                 metrics=('loss', 'acc', 'mae', 'f1', 'recall', 'precision', 'cm')):
        super().__init__()
        is_stream = type(file_or_stream) == _io.TextIOWrapper
        self._stream = file_or_stream if is_stream else open(self._log_file, 'a')
        self._metrics = metrics
        self._time_start = None

    def on_epoch_begin(self, epoch, logs=None):
        self._time_start = time()

    def on_epoch_end(self, epoch, logs=None):
        msg = f'Epoch {epoch + 1} - {time() - self._time_start:.3f} sec'
        for metric in self._metrics:
            t = logs.get(metric)
            v = logs.get(f'val_{metric}')
            if metric == 'cm':
                v = ' | '.join([' '.join([f'{e:.6f}' for e in row]) for row in v])
                msg += f' - val_cm: [{v}]'
            else:
                if t is not None:
                    msg += f' - {metric}: {t:.6f}'
                if v is not None:
                    msg += f' - val_{metric}: {v:.6f}'
        self._stream.write(msg + '\n')
        self._stream.flush()
