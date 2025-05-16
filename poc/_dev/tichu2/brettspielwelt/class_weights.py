import pickle
from collections import deque
from tqdm import tqdm
import config
import numpy as np
from os import path, mkdir
from tichu.brettspielwelt.generator import generator
from tichu.nnet import y_labels
from time import time


def create_class_weights(part: str, n=0):
    """
    Verteilung der Daten ermitteln

    :param part: 'prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2' oder 'schupf3'
    :param n: Anzahl Datensätze. Wenn 0 (default), wird nur das letzte Ergebnis ausgelesen.
    """
    # 'bonus' und 'points' sind stetige Größen und keine kategorische, daher für WCCE nicht geeignet.
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3')  # , 'bonus', 'points')

    folder = path.join(config.DATA_PATH, 'brettspielwelt/class_weights')
    if not path.exists(folder):
        mkdir(folder)
    file = path.join(folder, f'{part}.pkl')

    labels = y_labels(part)

    if n > 0:
        # Daten holen
        y = deque()
        gen = generator('train', part, endless=False)
        time_start = time()
        for _ in tqdm(range(n), desc='Lade Trainingsdaten'):
            _, _, y_ = next(gen)
            y.append(y_)
        seconds_gen = time() - time_start

        # Verteilung berechnen
        n = len(y)
        y_argmax = np.array(y).argmax(axis=1)
        i, c = np.unique(y_argmax, return_counts=True)
        d = dict(zip(i, c))  # pro Index die Anzahl im Dictionary ablegen
        counts = {label: d[i] if i in d else 0 for i, label in enumerate(labels)}

        # Optimale Gewichtung der Klassen für das Training berechnen
        mean = np.mean(list(d.values()))
        median = np.median(list(d.values()))
        weights_mean = [mean / d[i] if i in d else mean for i, label in enumerate(labels)]
        weights_median = [median / d[i] if i in d else median for i, label in enumerate(labels)]

        # Ergebnisse speichern
        with open(file, 'wb') as fp:
            pickle.dump((n, counts, mean, median, weights_mean, weights_median, seconds_gen), fp)

    # Ergebnisse laden
    with open(file, 'rb') as fp:
        # noinspection PickleLoad
        n, counts, mean, median, weights_mean, weights_median, seconds_gen = pickle.load(fp)

    # Ergebnis anzeigen
    print(f'Part: {part}')
    print(f'Generator-Zeit: {seconds_gen:5.3f} Sekunden')
    print(f'Stichprobengröße: {n}')
    print(f'Mittelwert: {mean:.6f}')  # ohne Nullen, aber das ist nicht so gravierend
    print(f'Median: {median}')  # ohne Nullen, aber das ist nicht so gravierend
    print()
    print(f'Verteilung - Part: {part}')
    print('Idx | Label       |    Count |   Weight Mean | Weight Median')
    for i, label in enumerate(labels):
        print(f'{i:3d} | {label:11s} | {counts[label]:8d} | {weights_mean[i]:13.6f} | {weights_median[i]:13.6f}')
