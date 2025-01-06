import gzip
import math
import pickle
from collections import deque
import config
import numpy as np
from os import path, mkdir, listdir
from tichu.brettspielwelt.generator import generator
from tichu.nnet import y_labels, num_input
from tqdm import tqdm

__all__ = 'create_samples', 'load_samples', 'cut_samples'


# def _create_tichu_samples(section: str, batch_size: int):
#     assert section in ('train', 'val', 'test')
#
#     folder = ['', '', '', '']
#     num_files = [1, 1, 1, 1]
#     num_x = [0, 0, 0, 0]
#     num_classes = 2
#     max_n = 1000000
#
#     for r, part in enumerate(('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu')):
#         folder[r] = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
#         if not path.exists(folder[r]):
#             mkdir(folder[r])
#         num_x[r] = num_input(part)
#
#     x = [[deque() for _ in range(num_x[r])] for r in range(4)]
#     y = [deque() for _ in range(4)]
#
#     # Prozess fortsetzen?
#     file = path.join(folder[3], f'id_{section}.pkl')
#     # with open(file, 'wb') as fp:
#     #     pickle.dump(2166961, fp)
#     if path.exists(file):
#         with open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             id_ = pickle.load(fp)
#         print(f'Letzte ID: {id_}')
#         # letzte Datei laden
#         for r in range(4):
#             files = [file for file in sorted(listdir(folder[r]), reverse=True) if file.startswith(section)]
#             file = path.join(folder[r], files[0])
#             print(f'Lade {file}... ', end='')
#             num_files[r] = int(file.split('-')[1].lstrip('0'))
#             with gzip.open(file, 'rb') as fp:
#                 # noinspection PickleLoad
#                 x_, y_ = pickle.load(fp)
#             n = len(y_)
#             for i in range(n):
#                 for j in range(num_x[r]):
#                     x[r][j].append(x_[j][i])
#                 y[r].append(y_[i])
#             print('ok')
#     else:
#         id_ = 0
#
#     gen = generator(section, 'tichu', endless=False, offset=id_)
#
#     eof = False
#     while not eof:
#         # ein Batch aus Datenbank lesen
#         tmp = [[deque() for _ in range(num_classes)] for _ in range(4)]  # pro Klasse eine Queue (nur für Train-Section, um die Datenverteilung auszugleichen)
#         try:
#             for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
#                 id_, x_, p0_ = next(gen)
#                 assert p0_.sum() == 1
#                 c = p0_.argmax()
#                 x0a_, x0b_, x1a_, x1b_, x1c_, x2_, x3a_, x3b_, x4b_, x4c_, x4d_, x5_, x6a_, x6b_, x6c_, x6d_, x6e_, x7_, x8_ = x_
#                 if x2_[0] == 1:  # 1 == 14 Karten (normalisiert!)
#                     if x1a_.sum() == 0 and x1b_.sum() == 0 and x1c_.sum() == 0:  # keine Karte geschupft
#                         r = 1  # normales Tichu im Auftakt
#                         x_ = [x0a_, x0b_, x4b_, x4c_, x4d_]
#                     else:
#                         r = 3  # Tichu im Hauptspiel
#                 else:
#                     r = 0  # großes Tichu
#                     x_ = [x0a_, x0b_, x4b_, x4c_, x4d_]
#                 if section == 'train':
#                     # noinspection PyTypeChecker
#                     tmp[r][c].append(x_)
#                 else:
#                     for j in range(num_x[r]):
#                         x[r][j].append(x_[j])
#                     y[r].append(c)
#                     if len(y[r]) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         num_files[r] += 1
#                         x[r] = [deque() for _ in range(num_x[r])]
#                         y[r] = deque()
#                         if r == 1:  # todo raus!!!!
#                             eof = True
#                     if r in (0, 1):
#                         r = 2  # Tichu im Auftakt
#                         for j in range(num_x[r]):
#                             x[r][j].append(x_[j])
#                         y[r].append(c)
#                         if len(y[r]) == max_n:
#                             # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                             with gzip.open(file, 'wb') as fp:
#                                 pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                             print(f'{file} gespeichert - letzte ID: {id_}')
#                             num_files[r] += 1
#                             x[r] = [deque() for _ in range(num_x[r])]
#                             y[r] = deque()
#         except StopIteration:
#             eof = True
#             print('EOF')
#
#         if section == 'train':
#             for r in (0, 1, 3):
#                 # Größe der kleinsten Klasse ermitteln
#                 n = batch_size
#                 for c in range(num_classes):
#                     # Verteilung
#                     # Idx | Label | prelude_grand | prelude_not_grand | prelude | tichu
#                     #   0 | Nein  |         95194 |             99881 |   97504 | 91592
#                     #   1 | Ja    |          4806 |               119 |    2496 |  8408
#                     m = len(tmp[r][c])
#                     if n > m:
#                         n = m
#                 # Klassenverteilung ausgleichen
#                 for c in range(num_classes):
#                     a = np.array(tmp[r][c], dtype=object)
#                     np.random.shuffle(a)  # mischen
#                     tmp[r][c] = a[:n]
#
#             # prelude_grand und prelude_not_grand zusammenlegen
#             for c in range(num_classes):
#                 a = deque(tmp[0][c])
#                 a.extend(tmp[1][c])
#                 a = np.array(a, dtype=object)
#                 np.random.shuffle(a)  # mischen
#                 # noinspection PyTypeChecker
#                 tmp[2][c] = a
#
#             for r in range(4):
#                 # Zur Gesamtmenge hinzufügen
#                 n = len(tmp[r][0])
#                 for i in range(n):
#                     for c in range(num_classes):
#                         for j in range(num_x[r]):
#                             x[r][j].append(tmp[r][c][i][j])
#                         y[r].append(c)
#                     if len(y[r]) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         num_files[r] += 1
#                         x[r] = [deque() for _ in range(num_x[r])]
#                         y[r] = deque()
#                         if r == 1:  # todo raus!!!!
#                             eof = True
#
#         # Speichern
#         for r in range(4):
#             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#             with gzip.open(file, 'wb') as fp:
#                 pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#             print(f'{file} gespeichert - letzte ID: {id_}')
#
#         # letzte ID speichern
#         file = path.join(folder[3], f'id_{section}.pkl')
#         with open(file, 'wb') as fp:
#             pickle.dump(id_, fp)
#
#
# def _create_figure_n_samples(section: str, batch_size: int):
#     assert section in ('train', 'val', 'test')
#
#     folder = ['', '', '', '']
#     num_files = [1, 1, 1, 1]
#     num_x = [0, 0, 0, 0]
#     num_classes = len(y_labels('figure_n'))
#     max_n = 1000000
#
#     for r, part in enumerate(('figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb')):
#         folder[r] = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
#         if not path.exists(folder[r]):
#             mkdir(folder[r])
#         num_x[r] = num_input(part)
#
#     x = [[deque() for _ in range(num_x[r])] for r in range(4)]
#     y = [deque() for _ in range(4)]
#
#     # Prozess fortsetzen?
#     file = path.join(folder[0], f'id_{section}.pkl')
#     if path.exists(file):
#         with open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             id_ = pickle.load(fp)
#         print(f'Letzte ID: {id_}')
#         # letzte Datei laden
#         for r in range(4):
#             files = [file for file in sorted(listdir(folder[r]), reverse=True) if file.startswith(section)]
#             file = path.join(folder[r], files[0])
#             print(f'Lade {file}... ', end='')
#             num_files[r] = int(file.split('-')[1].lstrip('0'))
#             with gzip.open(file, 'rb') as fp:
#                 # noinspection PickleLoad
#                 x_, y_ = pickle.load(fp)
#             n = len(y_)
#             for i in range(n):
#                 for j in range(num_x[r]):
#                     x[r][j].append(x_[j][i])
#                 y[r].append(y_[i])
#             print('ok')
#     else:
#         id_ = 0
#
#     gen = generator(section, 'figure_n', endless=False, offset=id_)
#
#     eof = [False, False, False, False]
#     while not eof[1]:  # or not eof[0] or not eof[2] or not eof[3]:
#         # ein Batch aus Datenbank lesen
#         tmp = [[deque() for _ in range(num_classes)] for _ in range(4)]  # pro Klasse eine Queue (nur für Train-Section, um die Datenverteilung auszugleichen)
#         try:
#             for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
#                 id_, x_, y_ = next(gen)
#                 # x0a_, x0b_, x1a_, x1b_, x1c_, x2_, x3a_, x3b_, x4a_, x4b_, x4c_, x4d_, x5_, x7_, x8_ = x_
#                 p1a_, p1b_ = y_
#                 assert p1a_.sum() == 1
#                 assert p1b_.sum() == 1
#                 t = p1a_.argmax() + 1  # 0 == Single, daher +1
#                 assert t in (STAIR, STREET, BOMB)
#                 if t == STAIR:
#                     r = 1
#                 elif t == STREET:
#                     r = 2
#                 else:
#                     r = 3
#                 c = p1b_.argmax()
#                 if section == 'train':
#                     # noinspection PyTypeChecker
#                     tmp[r][c].append(x_)
#                 else:
#                     for j in range(num_x[r]):
#                         x[r][j].append(x_[j])
#                     if r == 1:  # Treppe
#                         y[r].append(int(c / 2))
#                     elif r in (2, 3):  # Straße oder Bombe
#                         y[r].append(c - 1)
#                     if len(y[r]) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         num_files[r] += 1
#                         x[r] = [deque() for _ in range(num_x[r])]
#                         y[r] = deque()
#                         eof[r] = True
#
#                     r = 0
#                     for j in range(num_x[r]):
#                         x[r][j].append(x_[j])
#                     y[r].append(c)
#                     if len(y[r]) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         num_files[r] += 1
#                         x[r] = [deque() for _ in range(num_x[r])]
#                         y[r] = deque()
#                         eof[r] = True
#         except StopIteration:
#             eof[0] = True
#             eof[1] = True
#             eof[2] = True
#             eof[3] = True
#             print('EOF')
#
#         if section == 'train':
#             # Treppen, Straßen und Bomben zusammenlegen
#             for c in range(num_classes):
#                 a = deque(tmp[1][c])
#                 a.extend(tmp[2][c])
#                 a.extend(tmp[3][c])
#                 a = np.array(a, dtype=object)
#                 np.random.shuffle(a)  # mischen
#                 # noinspection PyTypeChecker
#                 tmp[0][c] = a
#
#             for r in range(4):
#                 # Größe der kleinsten Klasse ermitteln
#                 n = batch_size
#                 for c in range(num_classes):
#                     # Verteilung
#                     # Länge beim Anspiel
#                     # Idx | Label |  Alle | Treppe | Straße
#                     #   0 | 4     |   182 |   724  |     0
#                     #   1 | 5     |   249 |     0  |   326
#                     #   2 | 6     |   241 |   219  |   233
#                     #   3 | 7     |   124 |     0  |   171
#                     #   4 | 8     |    84 |    43  |   102
#                     #   5 | 9     |    41 |     0  |    66
#                     #   6 | 10    |    40 |    14  |    48
#                     #   7 | 11    |    28 |     0  |    37
#                     #   8 | 12    |     8 |     0  |    12
#                     #   9 | 13    |     3 |     0  |     5
#                     #  10 | 14    |     0 |     0  |     0
#                     if c >= 4:
#                         continue  # Länge ab 8 Karten bleiben unausgewogen
#                     m = len(tmp[r][c])
#                     if 0 < m < n:
#                         n = m
#                 # Klassenverteilung ausgleichen
#                 for c in range(num_classes):
#                     a = np.array(tmp[r][c], dtype=object)
#                     np.random.shuffle(a)  # mischen
#                     tmp[r][c] = a[:n]
#
#                 # Zur Gesamtmenge hinzufügen
#                 n = len(tmp[r][2])
#                 for i in range(n):
#                     for c in range(num_classes):
#                         if len(tmp[r][c]) <= i:
#                             continue
#                         for j in range(num_x[r]):
#                             x[r][j].append(tmp[r][c][i][j])
#                         if r == 1:  # Treppe
#                             y[r].append(int(c / 2))
#                         elif r in (2, 3):  # Straße oder Bombe
#                             y[r].append(c - 1)
#                         else:
#                             y[r].append(c)
#                         if len(y[r]) == max_n:
#                             # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                             with gzip.open(file, 'wb') as fp:
#                                 pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                             print(f'{file} gespeichert - letzte ID: {id_}')
#                             num_files[r] += 1
#                             x[r] = [deque() for _ in range(num_x[r])]
#                             y[r] = deque()
#                             eof[r] = True
#
#         # Speichern
#         for r in range(4):
#             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#             with gzip.open(file, 'wb') as fp:
#                 pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#             print(f'{file} gespeichert - letzte ID: {id_}')
#
#         # letzte ID speichern
#         file = path.join(folder[0], f'id_{section}.pkl')
#         with open(file, 'wb') as fp:
#             pickle.dump(id_, fp)
#
#
# def _create_figure_samples(section: str, batch_size: int):
#     assert section in ('train', 'val', 'test')
#
#     folder = ['', '', '', '']
#     num_files = [1, 1, 1, 1]
#     num_x = [0, 0, 0, 0]
#     num_classes = [0, 0, 0, 0]
#     max_n = 1000000
#
#     for r, part in enumerate(('figure_t', 'figure_v', 'card', 'bomb')):
#         folder[r] = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
#         if not path.exists(folder[r]):
#             mkdir(folder[r])
#         num_x[r] = num_input(part)
#         num_classes[r] = len(y_labels(part))
#
#     # noinspection PyUnusedLocal
#     x = [[deque() for _ in range(num_x[r])] for r in range(4)]
#     y = [deque() for _ in range(4)]
#
#     # Prozess fortsetzen?
#     file = path.join(folder[0], f'id_{section}.pkl')
#     if path.exists(file):
#         with open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             id_ = pickle.load(fp)
#         print(f'Letzte ID: {id_}')
#         # letzte Datei laden
#         for r in range(4):
#             files = [file for file in sorted(listdir(folder[r]), reverse=True) if file.startswith(section)]
#             file = path.join(folder[r], files[0])
#             print(f'Lade {file}... ', end='')
#             num_files[r] = int(file.split('-')[1].lstrip('0'))
#             with gzip.open(file, 'rb') as fp:
#                 # noinspection PickleLoad
#                 x_, y_ = pickle.load(fp)
#             n = len(y_)
#             for i in range(n):
#                 for j in range(num_x[r]):
#                     x[r][j].append(x_[j][i])
#                 y[r].append(y_[i])
#             print('ok')
#     else:
#         id_ = 0
#
#     gen = generator(section, 'card', endless=False, offset=id_)
#
#     eof = [False, False, False, False]
#     while not eof[0] or not eof[1] or not eof[2]:  # or not eof[3]:
#         # ein Batch aus Datenbank lesen
#         tmp = [[deque() for _ in range(num_classes[r])] for r in range(4)]  # pro Klasse eine Queue (nur für Train-Section, um die Datenverteilung auszugleichen)
#         try:
#             for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
#                 id_, x_, y_ = next(gen)
#                 x0a_, x0b_, x1a_, x1b_, x1c_, x2_, x3a_, x3b_, x4a_, x4b_, x4c_, x4d_, x5_, x6a_, x6b_, x6c_, x6d_, x6e_, x7_, x8_ = x_
#                 p1a_, p1c_, p1d_, p1e_ = y_
#                 if x6b_.sum() == 0:  # kein Stich ==> Anspiel
#                     assert p1a_.sum() == 1 and p1c_.sum() == 1 and p1d_.sum() == 0 and p1e_.sum() == 0
#                     x_ = [x0a_, x0b_, x1a_, x1b_, x1c_, x2_, x3a_, x3b_, x4a_, x4b_, x4c_, x4d_, x5_, x7_, x8_]  # ohne x6
#                     for r in (0, 1):
#                         if y_[r].sum() == 1:
#                             if section == 'train':
#                                 c = y_[r].argmax()
#                                 # noinspection PyTypeChecker
#                                 tmp[r][c].append(x_)
#                             else:  # section = val oder test
#                                 for j in range(num_x[r]):
#                                     x[r][j].append(x_[j])
#                                 y[r].append(y_[r].argmax())
#                                 if len(y[r]) == max_n:
#                                     # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                                     file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                                     with gzip.open(file, 'wb') as fp:
#                                         pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                                     print(f'{file} gespeichert - letzte ID: {id_}')
#                                     num_files[r] += 1
#                                     # noinspection PyUnusedLocal
#                                     x[r] = [deque() for _ in range(num_x[r])]
#                                     y[r] = deque()
#                                     eof[r] = True  # todo raus!!!!
#                 else:  # Bedienen
#                     assert p1a_.sum() == 0 and p1c_.sum() == 0 and p1d_.sum() == 1
#                     for r in (2, 3):
#                         if y_[r].sum() == 1:
#                             if section == 'train':
#                                 c = y_[r].argmax()
#                                 # noinspection PyTypeChecker
#                                 tmp[r][c].append(x_)
#                             else:  # section = val oder test
#                                 for j in range(num_x[r]):
#                                     x[r][j].append(x_[j])
#                                 y[r].append(y_[r].argmax())
#                                 if len(y[r]) == max_n:
#                                     # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                                     file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                                     with gzip.open(file, 'wb') as fp:
#                                         pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                                     print(f'{file} gespeichert - letzte ID: {id_}')
#                                     num_files[r] += 1
#                                     # noinspection PyUnusedLocal
#                                     x[r] = [deque() for _ in range(num_x[r])]
#                                     y[r] = deque()
#                                     eof[r] = True  # todo raus!!!!
#         except StopIteration:
#             eof[0] = True
#             eof[1] = True
#             eof[2] = True
#             eof[3] = True
#             print('EOF')
#
#         if section == 'train':
#             for r in range(4):
#                 # Größe der kleinsten Klasse ermitteln
#                 n = batch_size
#                 for c in range(num_classes[r]):
#                     # Typ beim Anspiel
#                     # Verteilung
#                     # Idx | Label     | Count
#                     #   0 | Einzel    | 54713
#                     #   1 | Paar      | 15339
#                     #   2 | Drilling  |  4394
#                     #   3 | Treppe    |  5859
#                     #   4 | FullHouse |  6586
#                     #   5 | Straße    | 12935
#                     #   6 | Bombe     |   174
#                     if r == 0 and c == 6:
#                         continue  # Bombe bleibt unausgewogen
#
#                     # Höchste Karte beim Anspiel (Phönix im Anspiel wäre wie MahJong, kommt in der Praxis aber nicht vor)
#                     # Verteilung
#                     # Idx | Label | Count
#                     #   0 | Hu    |  7288
#                     #   1 | Ma    |  8244
#                     #   2 | 2     | 11394
#                     #   3 | 3     |  8430
#                     #   4 | 4     |  6745
#                     #   5 | 5     |  6517
#                     #   6 | 6     |  6390
#                     #   7 | 7     |  5948
#                     #   8 | 8     |  5646
#                     #   9 | 9     |  5391
#                     #  10 | 10    |  5495
#                     #  11 | B     |  5279
#                     #  12 | D     |  5273
#                     #  13 | K     |  5536
#                     #  14 | A     |  5075
#                     #  15 | Dr    |  1349
#                     if r == 1 and c == 15:
#                         continue  # Drache bleibt unausgewogen
#
#                     # Höchste Karte beim Bedienen (Phönix, wenn p1d == x6d)
#                     # Idx | Label | Count
#                     #   0 | /     | 65735
#                     #   1 | Ph    |    14
#                     #   2 | 2     |   853
#                     #   3 | 3     |  1322
#                     #   4 | 4     |  1473
#                     #   5 | 5     |  1628
#                     #   6 | 6     |  1770
#                     #   7 | 7     |  1821
#                     #   8 | 8     |  1985
#                     #   9 | 9     |  2214
#                     #  10 | 10    |  2390
#                     #  11 | B     |  2928
#                     #  12 | D     |  3475
#                     #  13 | K     |  4070
#                     #  14 | A     |  6544
#                     #  15 | Dr    |  1778
#                     if r == 2 and c == 1:
#                         continue  # Phönix bleibt unausgewogen
#
#                     # Bomben
#                     # Idx | Label | Count
#                     #   0 | Nein  | 85797
#                     #   1 | Ja    | 14203
#
#                     m = len(tmp[r][c])
#                     if 0 < m < n:
#                         n = m
#
#                 # Klassenverteilung ausgleichen
#                 for c in range(num_classes[r]):
#                     a = np.array(tmp[r][c], dtype=object)
#                     np.random.shuffle(a)  # mischen
#                     tmp[r][c] = a[:n]
#
#             for r in range(4):
#                 # Zur Gesamtmenge hinzufügen
#                 n = len(tmp[r][0])
#                 for i in range(n):
#                     for c in range(num_classes[r]):
#                         if len(tmp[r][c]) > i:
#                             x_ = tmp[r][c][i]
#                             for j in range(num_x[r]):
#                                 x[r][j].append(x_[j])
#                             y[r].append(c)
#                             if len(y[r]) == max_n:
#                                 # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                                 file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                                 with gzip.open(file, 'wb') as fp:
#                                     pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#                                 print(f'{file} gespeichert - letzte ID: {id_}')
#                                 num_files[r] += 1
#                                 x[r] = [deque() for _ in range(num_x[r])]
#                                 y[r] = deque()
#                                 eof[r] = True  # todo raus!!!!
#
#         # Speichern
#         for r in range(4):
#             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#             with gzip.open(file, 'wb') as fp:
#                 pickle.dump(([np.array(x[r][j]) for j in range(num_x[r])], np.array(y[r])), fp)
#             print(f'{file} gespeichert - letzte ID: {id_}')
#
#         # letzte ID speichern
#         file = path.join(folder[0], f'id_{section}.pkl')
#         with open(file, 'wb') as fp:
#             pickle.dump(id_, fp)
#
#
# def _create_wish_samples(section: str, batch_size: int):
#     assert section in ('train', 'val', 'test')
#
#     num_files = 1
#     num_x = num_input('wish')
#     labels = y_labels('wish')
#     num_classes = len(labels)
#     max_n = 1000000
#     x = [deque() for _ in range(num_x)]
#     y = deque()
#
#     folder = path.join(config.DATA_PATH, f'brettspielwelt/samples/wish')
#     if not path.exists(folder):
#         mkdir(folder)
#
#     # Prozess fortsetzen?
#     file = path.join(folder, f'id_{section}.pkl')
#     if path.exists(file):
#         with open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             id_ = pickle.load(fp)
#         print(f'Letzte ID: {id_}')
#         # letzte Datei laden
#         files = [file for file in sorted(listdir(folder), reverse=True) if file.startswith(section)]
#         file = path.join(folder, files[0])
#         print(f'Lade {file}... ', end='')
#         num_files = int(file.split('-')[1].lstrip('0'))
#         with gzip.open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             x_, y_ = pickle.load(fp)
#         n = len(y_)
#         for i in range(n):
#             for j in range(num_x):
#                 x[j].append(x_[j][i])
#             y.append(y_[i])
#         print('ok')
#     else:
#         id_ = 0
#
#     gen = generator(section, 'wish', endless=False, offset=id_)
#
#     eof = False
#     while not eof:
#         # ein Batch aus Datenbank lesen
#         tmp = [deque() for _ in range(num_classes)]
#         try:
#             for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
#                 id_, x_, p2_ = next(gen)
#                 assert len(x_) == num_x
#                 assert p2_.sum() == 1
#                 if section == 'train':
#                     c = p2_.argmax()
#                     # noinspection PyTypeChecker
#                     tmp[c].append(x_)
#                 else:
#                     for j in range(num_x):
#                         x[j].append(x_[j])
#                     y.append(p2_.argmax())
#                     if len(y) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         num_files += 1
#                         x = [deque() for _ in range(num_x)]
#                         y = deque()
#                         eof = True  # todo raus!!!!
#         except StopIteration:
#             eof = True
#             print('EOF')
#
#         if section == 'train':
#             # Größe der kleinsten Klasse ermitteln
#             n = batch_size
#             for c in range(num_classes):
#                 # Verteilung der Daten
#                 #  Idx | Label | Count
#                 #    0 | 2     | 18057
#                 #    1 | 3     | 15646
#                 #    2 | 4     | 10642
#                 #    3 | 5     |  9946
#                 #    4 | 6     |  5473
#                 #    5 | 7     |  4020
#                 #    6 | 8     |  2308
#                 #    7 | 9     |  1780
#                 #    8 | 10    |  1679
#                 #    9 | B     |   771
#                 #   10 | D     |   690
#                 #   11 | K     | 21659
#                 #   12 | A     |  7329
#                 if 4 <= c <= 10:
#                     continue  # Kartenwerte zw. 6 und Dame werden nicht ausgewogen
#                 m = len(tmp[c])
#                 if 0 < m < n:
#                     n = m
#
#             # Klassenverteilung ausgleichen
#             for c in range(num_classes):
#                 a = np.array(tmp[c], dtype=object)
#                 np.random.shuffle(a)  # mischen
#                 tmp[c] = a[:n]
#
#             # Zur Gesamtmenge hinzufügen
#             n = len(tmp[0])
#             for i in range(n):
#                 for c in range(num_classes):
#                     if len(tmp[c]) > i:
#                         x_ = tmp[c][i]
#                         for j in range(num_x):
#                             x[j].append(x_[j])
#                         y.append(c)
#                         if len(y) == max_n:
#                             # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                             file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
#                             with gzip.open(file, 'wb') as fp:
#                                 pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
#                             print(f'{file} gespeichert - letzte ID: {id_}')
#                             num_files += 1
#                             x = [deque() for _ in range(num_x)]
#                             y = deque()
#                             eof = True  # todo raus!!!!
#
#         # Speichern
#         file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
#         with gzip.open(file, 'wb') as fp:
#             pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
#         print(f'{file} gespeichert - letzte ID: {id_}')
#
#         # letzte ID speichern
#         file = path.join(folder, f'id_{section}.pkl')
#         with open(file, 'wb') as fp:
#             pickle.dump(id_, fp)
#
#
# def _create_gift_samples(section: str, batch_size: int):
#     assert section in ('train', 'val', 'test')
#
#     num_files = 1
#     num_x = num_input('gift')
#     labels = y_labels('gift')
#     num_classes = len(labels)
#     max_n = 1000000
#     x = [deque() for _ in range(num_x)]
#     y = deque()
#
#     folder = path.join(config.DATA_PATH, f'brettspielwelt/samples/gift')
#     if not path.exists(folder):
#         mkdir(folder)
#
#     # Prozess fortsetzen?
#     file = path.join(folder, f'id_{section}.pkl')
#     if path.exists(file):
#         with open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             id_ = pickle.load(fp)
#         print(f'Letzte ID: {id_}')
#         # letzte Datei laden
#         files = [file for file in sorted(listdir(folder), reverse=True) if file.startswith(section)]
#         file = path.join(folder, files[0])
#         print(f'Lade {file}... ', end='')
#         num_files = int(file.split('-')[1].lstrip('0'))
#         with gzip.open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             x_, y_ = pickle.load(fp)
#         n = len(y_)
#         for i in range(n):
#             for j in range(num_x):
#                 x[j].append(x_[j][i])
#             y.append(y_[i])
#         print('ok')
#     else:
#         id_ = 0
#
#     gen = generator(section, 'gift', endless=False, offset=id_)
#
#     eof = False
#     while not eof:
#         # ein Batch aus Datenbank holen
#         tmp = [deque() for _ in range(num_classes)]  # pro Klasse eine Queue (nur für Train-Section, um die Datenverteilung auszugleichen)
#         try:
#             for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
#                 id_, x_, p3_ = next(gen)
#                 assert len(x_) == num_x
#                 assert p3_.sum() == 1
#                 c = p3_.argmax()
#                 if section == 'train':
#                     tmp[c].append(x_)
#                 else:
#                     for j in range(num_x):
#                         x[j].append(x_[j])
#                     y.append(c)
#                     if len(y) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         num_files += 1
#                         x = [deque() for _ in range(num_x)]
#                         y = deque()
#                         eof = True  # todo raus!!!!
#         except StopIteration:
#             eof = True
#             print('EOF')
#
#         # Under-Sampling der Trainingsdaten
#         if section == 'train':
#             # Größe der kleinsten Klasse ermitteln
#             n = batch_size
#             for c in range(num_classes):
#                 # Verteilung
#                 # Idx | Label | Count
#                 #   0 | R     | 37955
#                 #   1 | L     | 62045
#                 m = len(tmp[c])
#                 if n > m:
#                     n = m
#
#             # Klassenverteilung ausgleichen
#             for c in range(num_classes):
#                 a = np.array(tmp[c])
#                 np.random.shuffle(a)  # mischen
#                 tmp[c] = a[:n]
#
#             # Zur Gesamtmenge hinzufügen
#             for i in range(n):
#                 for c in range(num_classes):
#                     for j in range(num_x):
#                         x[j].append(tmp[c][i][j])
#                     y.append(c)
#                     if len(y) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         num_files += 1
#                         x = [deque() for _ in range(num_x)]
#                         y = deque()
#                         eof = True  # todo raus!!!!
#
#         # Speichern
#         file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
#         with gzip.open(file, 'wb') as fp:
#             pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
#         print(f'{file} gespeichert - letzte ID: {id_}')
#
#         # letzte ID speichern
#         file = path.join(folder, f'id_{section}.pkl')
#         with open(file, 'wb') as fp:
#             pickle.dump(id_, fp)
#
#
# def _create_schupf_samples(section: str, batch_size: int):
#     assert section in ('train', 'val', 'test')
#
#     folder = ['', '', '']
#     num_files = [1, 1, 1]
#     num_x = num_input('schupf1')
#     labels = y_labels('schupf1')
#     num_classes = len(labels)
#     max_n = 1000000
#
#     for r, part in enumerate(('schupf1', 'schupf2', 'schupf3')):
#         folder[r] = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
#         if not path.exists(folder[r]):
#             mkdir(folder[r])
#
#     # noinspection PyUnusedLocal
#     x = [[deque() for _ in range(num_x)] for r in range(3)]
#     y = [deque() for _ in range(3)]
#
#     # Prozess fortsetzen?
#     file = path.join(folder[0], f'id_{section}.pkl')
#     if path.exists(file):
#         with open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             id_ = pickle.load(fp)
#         print(f'Letzte ID: {id_}')
#         # letzte Datei laden
#         for r in range(3):
#             files = [file for file in sorted(listdir(folder[r]), reverse=True) if file.startswith(section)]
#             file = path.join(folder[r], files[0])
#             print(f'Lade {file}... ', end='')
#             num_files[r] = int(file.split('-')[1].lstrip('0'))
#             with gzip.open(file, 'rb') as fp:
#                 # noinspection PickleLoad
#                 x_, y_ = pickle.load(fp)
#             n = len(y_)
#             for i in range(n):
#                 for j in range(num_x):
#                     x[r][j].append(x_[j][i])
#                 y[r].append(y_[i])
#             print('ok')
#     else:
#         id_ = 0
#
#     gen = generator(section, 'schupf1', endless=False, offset=id_)
#
#     eof = [False, False, False]
#     while not eof[0] or not eof[1] or not eof[2]:
#         # ein Batch aus Datenbank lesen
#         tmp = [[deque() for _ in range(num_classes)] for _ in range(3)]  # pro Klasse eine Queue (nur für Train-Section, um die Datenverteilung auszugleichen)
#         try:
#             for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
#                 id_, x_, y_ = next(gen)
#                 assert len(x_) == num_x
#                 for r in range(3):
#                     assert y_[r].sum() == 1
#                 if section == 'train':
#                     for r in range(3):
#                         c = y_[r].argmax()
#                         # noinspection PyTypeChecker
#                         tmp[r][c].append(x_)
#                 else:
#                     for r in range(3):
#                         for j in range(num_x):
#                             x[r][j].append(x_[j])
#                         y[r].append(y_[r].argmax())
#                         if len(y[r]) == max_n:
#                             # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                             with gzip.open(file, 'wb') as fp:
#                                 pickle.dump(([np.array(x[r][j]) for j in range(num_x)], np.array(y[r])), fp)
#                             print(f'{file} gespeichert - letzte ID: {id_}')
#                             num_files[r] += 1
#                             # noinspection PyUnusedLocal
#                             x[r] = [deque() for _ in range(num_x)]
#                             y[r] = deque()
#                             eof[r] = True  # todo raus!!!!
#         except StopIteration:
#             eof[0] = True
#             eof[1] = True
#             eof[2] = True
#             print('EOF')
#
#         if section == 'train':
#             for r in range(3):
#                 # Größe der kleinsten Klasse ermitteln
#                 n = batch_size
#                 for c in range(num_classes):
#                     # Verteilung der Daten
#                     # Idx | Label | Schupf1  | Schupf2  | Schupf3
#                     #   0 | Hu    |   11040  |   13193  |   10064
#                     #   1 | Ma    |     993  |    5118  |     382
#                     #   2 | 2     |   49752  |     829  |   89964
#                     #   3 | 3     |   63959  |     915  |   43187
#                     #   4 | 4     |   34199  |    1752  |   44829
#                     #   5 | 5     |   39142  |    2566  |   25597
#                     #   6 | 6     |   25733  |    3368  |   28470
#                     #   7 | 7     |   27856  |    5121  |   18322
#                     #   8 | 8     |   18341  |    7519  |   18195
#                     #   9 | 9     |   17326  |   10315  |   11381
#                     #  10 | 10    |    7302  |   16878  |    6312
#                     #  11 | B     |    3234  |   26686  |    2485
#                     #  12 | D     |     991  |   37202  |     735
#                     #  13 | K     |     109  |   50970  |      63
#                     #  14 | A     |      20  |   69389  |       6
#                     #  15 | Dr    |       2  |   30943  |       4
#                     #  16 | Ph    |       1  |   17236  |       4
#                     if r in (0, 2) and (c == 1 or c >= 10):
#                         continue  # MahJong und Kartenwerte ab 10 für die Gegner bleiben unausgewogen
#                     if r == 1 and (2 <= c <= 6):
#                         continue  # Kartenwerte zw. 2 und 6 für den Partner bleiben unausgewogen
#                     m = len(tmp[r][c])
#                     if 0 < m < n:
#                         n = m
#                 # Klassenverteilung ausgleichen
#                 for c in range(num_classes):
#                     a = np.array(tmp[r][c], dtype=object)
#                     np.random.shuffle(a)  # mischen
#                     tmp[r][c] = a[:n]
#
#             for r in range(3):
#                 # Zur Gesamtmenge hinzufügen
#                 n = len(tmp[r][0])
#                 for i in range(n):
#                     for c in range(num_classes):
#                         if len(tmp[r][c]) > i:
#                             x_ = tmp[r][c][i]
#                             for j in range(num_x):
#                                 x[r][j].append(x_[j])
#                             y[r].append(c)
#                             if len(y[r]) == max_n:
#                                 # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                                 file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                                 with gzip.open(file, 'wb') as fp:
#                                     pickle.dump(([np.array(x[r][j]) for j in range(num_x)], np.array(y[r])), fp)
#                                 print(f'{file} gespeichert - letzte ID: {id_}')
#                                 num_files[r] += 1
#                                 x[r] = [deque() for _ in range(num_x)]
#                                 y[r] = deque()
#                                 eof[r] = True  # todo raus!!!!
#
#         # Speichern
#         for r in range(3):
#             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#             with gzip.open(file, 'wb') as fp:
#                 pickle.dump(([np.array(x[r][j]) for j in range(num_x)], np.array(y[r])), fp)
#             print(f'{file} gespeichert - letzte ID: {id_}')
#
#         # letzte ID speichern
#         file = path.join(folder[0], f'id_{section}.pkl')
#         with open(file, 'wb') as fp:
#             pickle.dump(id_, fp)
#
#
# def _create_point_samples(section: str, batch_size: int):
#     assert section in ('train', 'val', 'test')
#
#     folder = ['', '']
#     for r, part in enumerate(('bonus', 'points')):
#         folder[r] = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
#         if not path.exists(folder[r]):
#             mkdir(folder[r])
#
#     num_files = [1, 1]
#     num_x = 20
#     max_n = 1000000
#
#     # noinspection PyUnusedLocal
#     x = [[deque() for _ in range(num_x)] for r in range(2)]  # 20 Queue für 20 Eingänge
#     y = [deque(), deque()]  # je eine Queue für Bonus und für Points
#
#     # Prozess fortsetzen?
#     file = path.join(folder[1], f'id_{section}.pkl')
#     if path.exists(file):
#         with open(file, 'rb') as fp:
#             # noinspection PickleLoad
#             id_ = pickle.load(fp)
#         print(f'Letzte ID: {id_}')
#         # letzte Datei laden
#         for r in range(2):
#             files = [file for file in sorted(listdir(folder[r]), reverse=True) if file.startswith(section)]
#             file = path.join(folder[r], files[0])
#             print(f'Lade {file}... ', end='')
#             num_files[r] = int(file.split('-')[1].lstrip('0'))
#             with gzip.open(file, 'rb') as fp:
#                 # noinspection PickleLoad
#                 x_, y_ = pickle.load(fp)
#             n = len(y_)
#             for i in range(n):
#                 for j in range(num_x):
#                     x[r][j].append(x_[j][i])
#                 y[r].append(y_[i])
#             print('ok')
#     else:
#         id_ = 0
#
#     gen = generator(section, part='points', endless=False, offset=id_)
#
#     eof = False
#     while not eof:
#         # ein Batch aus Datenbank lesen
#         try:
#             for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
#                 id_, x_, y_ = next(gen)
#                 for r in range(2):
#                     for j in range(num_x):
#                         x[r][j].append(x_[j])
#                     y[r].append(y_[r])
#                     if len(y[r]) == max_n:
#                         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
#                         file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#                         with gzip.open(file, 'wb') as fp:
#                             pickle.dump(([np.array(x[r][j]) for j in range(num_x)], np.array(y[r])), fp)
#                         print(f'{file} gespeichert - letzte ID: {id_}')
#                         x[r] = [deque() for _ in range(num_x)]
#                         y[r] = deque()
#                         num_files[r] += 1
#                         eof = True  # todo raus!!!!
#
#         except StopIteration:
#             eof = True
#             print('EOF')
#
#         # Speichern
#         for r in range(2):
#             file = path.join(folder[r], f'{section}-{num_files[r]:02d}-{len(y[r]):07d}.pkl.gzip')
#             with gzip.open(file, 'wb') as fp:
#                 pickle.dump(([np.array(x[r][j]) for j in range(num_x)], np.array(y[r])), fp)
#                 print(f'{file} gespeichert - letzte ID: {id_}')
#
#         # letzte ID speichern
#         file = path.join(folder[1], f'id_{section}.pkl')
#         with open(file, 'wb') as fp:
#             pickle.dump(id_, fp)


def create_samples(section: str, part: str, batch_size=200000, max_files=math.inf):
    """
    Extrahiert Beispiele aus der Datenbank und speichert diese als Pickle-Datei.

    :param section: 'train', 'val' oder 'test'
    :param part: 'prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points'
    :param batch_size: Anzahl Datensätze pro Verarbeitungsschritt
    :param max_files: Anzahl Dateien: Default: INF (soviel wie möglich)
    """
    assert section in ('train', 'val', 'test')
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points')

    folder = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
    if not path.exists(folder):
        mkdir(folder)

    # Größe des Ausgabevektors
    # Ich kategorisiere die stetigen Variablen v0 und v1 in der temporären Liste, um auch diese gleichzuverteilen.
    if part == 'bonus':  # v0
        num_classes = 5  # -1, -0.5, 0, 0.5, 1
    elif part == 'points':  # v1
        num_classes = len(range(-800, 810, 10))  # 161; zw. -2 (=-800 Punkte) und 2 (=800 Punkte) mit Schrittweite 0.025 (10 Punkte)
    else:
        num_classes = len(y_labels(part))

    num_x = num_input(part)  # Anzahl der Eingabevariablen
    max_n = 1000000 if section == 'train' else 100000  # Anzahl Beispiele pro Datei
    x = [deque() for _ in range(num_x)]
    y = deque()

    # Prozess fortsetzen?
    file = path.join(folder, f'id_{section}.pkl')
    if path.exists(file):
        with open(file, 'rb') as fp:
            # noinspection PickleLoad
            id_ = pickle.load(fp)
        print(f'Letzte ID: {id_}')
        # letzte Datei laden
        files = [file for file in sorted(listdir(folder), reverse=True) if file.startswith(section)]
        file = path.join(folder, files[0])
        print(f'Lade {file}... ', end='')
        num_files = int(file.split('-')[1].lstrip('0'))  # Nummer der aktuellen Datei
        if num_files > max_files:
            print(f'Es wurden bereits {num_files - 1} Dateien mit {max_n} Beispielen generiert.')
            return
        with gzip.open(file, 'rb') as fp:
            # noinspection PickleLoad
            x_, y_ = pickle.load(fp)
        n = len(y_)
        for i in range(n):
            for j in range(num_x):
                x[j].append(x_[j][i])
            y.append(y_[i])
        print('ok')
    else:
        id_ = 0
        num_files = 1

    gen = generator(section, part, endless=False, offset=id_)
    eof = False
    while not eof and num_files <= max_files:
        # ein Batch aus Datenbank lesen
        tmp = [deque() for _ in range(num_classes)]
        try:
            for _ in tqdm(range(batch_size), desc=f'Lade Daten ab id {id_ + 1}'):
                id_, x_, y_ = next(gen)
                assert len(x_) == num_x
                if part not in ('bonus', 'points'):
                    assert y_.sum() == 1
                # if section == 'train':
                if part == 'bonus':  # todo testen
                    c = round(y_ * 2) + 2  # y_ == -1 (-200 Punkte) bis 1 (200 Punkte) => c == 0 bis 4
                elif part == 'points':  # todo testen
                    c = round(y_ * 40) + 80  # y_ == -2 (-800 Punkte) bis 2 (800 Punkte) => c == 0 bis 160
                else:
                    c = y_.argmax()
                # noinspection PyTypeChecker
                tmp[c].append(x_)
                # else:
                #     for j in range(num_x):
                #         x[j].append(x_[j])
                #     y.append(y_ if part in ('bonus', 'points') else y_.argmax())
                #     if len(y) == max_n:
                #         # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
                #         file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
                #         with gzip.open(file, 'wb') as fp:
                #             pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
                #         print(f'{file} gespeichert - letzte ID: {id_}')
                #         num_files += 1
                #         x = [deque() for _ in range(num_x)]
                #         y = deque()
        except StopIteration:
            eof = True
            print('EOF')

        # Verteilung der Klassen ausgleichen
        n = batch_size
        if section == 'train':
            # Größe der kleinsten Klasse ermitteln
            for c in range(num_classes):
                # Tichu
                # Idx | Label | prelude_grand | prelude_not_grand | prelude | tichu  (n = 100000)
                #   0 | Nein  |         95194 |             99881 |   97504 | 91592
                #   1 | Ja    |          4806 |               119 |    2496 |  8408

                # Typ beim Anspiel
                # Idx | Label     | Count  (n = 100000)
                #   0 | Einzel    | 54713
                #   1 | Paar      | 15339
                #   2 | Drilling  |  4394
                #   3 | Treppe    |  5859
                #   4 | FullHouse |  6586
                #   5 | Straße    | 12935
                #   6 | Bombe     |   174
                if part == 'figure_t' and c == 6:
                    continue  # Bombe bleibt unausgewogen

                # Länge beim Anspiel für Treppen, Straßen und Straßen-Bomben
                # Idx | Label | Count  (n = 100000)
                #   0 | 4     | 23773
                #   1 | 5     | 26053
                #   2 | 6     | 22740
                #   3 | 7     | 10339
                #   4 | 8     |  8092
                #   5 | 9     |  4221
                #   6 | 10    |  2677
                #   7 | 11    |  1310
                #   8 | 12    |   571
                #   9 | 13    |   188
                #  10 | 14    |    36
                if part == 'figure_n' and c >= 8:
                    continue  # Länge ab 12 Karten bleiben unausgewogen

                # Länge beim Anspiel (nur Treppen)
                # Idx | Label | Count
                #   0 | 4     |   724
                #   1 | 6     |   219
                #   2 | 8     |    43
                #   3 | 10    |    14
                #   4 | 12    |     0
                #   5 | 14    |     0
                if part == 'figure_n_stair' and c >= 4:
                    continue  # Länge ab 12 Karten bleiben unausgewogen

                # Länge beim Anspiel (nur Straßen)
                # Idx | Label | Count
                #   0 | 5     |   326
                #   1 | 6     |   233
                #   2 | 7     |   171
                #   3 | 8     |   102
                #   4 | 9     |    66
                #   5 | 10    |    48
                #   6 | 11    |    37
                #   7 | 12    |    12
                #   8 | 13    |     5
                #   9 | 14    |     0
                if part == 'figure_n_street' and c >= 7:
                    continue  # Länge ab 12 Karten bleiben unausgewogen

                # Länge beim Anspiel (nur Bomben)
                # so gut wie nie!
                # todo Verteilung ausgeben

                # Höchste Karte beim Anspiel (Phönix im Anspiel wäre wie MahJong, kommt in der Praxis aber nicht vor)
                # Verteilung
                # Idx | Label | Count  (n = 100000)
                #   0 | Hu    |  7288
                #   1 | Ma    |  8244
                #   2 | 2     | 11394
                #   3 | 3     |  8430
                #   4 | 4     |  6745
                #   5 | 5     |  6517
                #   6 | 6     |  6390
                #   7 | 7     |  5948
                #   8 | 8     |  5646
                #   9 | 9     |  5391
                #  10 | 10    |  5495
                #  11 | B     |  5279
                #  12 | D     |  5273
                #  13 | K     |  5536
                #  14 | A     |  5075
                #  15 | Dr    |  1349
                if part == 'figure_v' and c == 15:
                    continue  # Drache bleibt unausgewogen

                # Höchste Karte beim Bedienen (Phönix, wenn p1d == x6d)
                # Idx | Label | Count
                #   0 | /     | 65735
                #   1 | Ph    |    14
                #   2 | 2     |   853
                #   3 | 3     |  1322
                #   4 | 4     |  1473
                #   5 | 5     |  1628
                #   6 | 6     |  1770
                #   7 | 7     |  1821
                #   8 | 8     |  1985
                #   9 | 9     |  2214
                #  10 | 10    |  2390
                #  11 | B     |  2928
                #  12 | D     |  3475
                #  13 | K     |  4070
                #  14 | A     |  6544
                #  15 | Dr    |  1778
                if part == 'card' and c == 1:
                    continue  # Phönix bleibt unausgewogen

                # Bomben beim Bedienen
                # Idx | Label | Count
                #   0 | Nein  | 85797
                #   1 | Ja    | 14203

                # Wunsch
                #  Idx | Label | Count
                #    0 | 2     | 18057
                #    1 | 3     | 15646
                #    2 | 4     | 10642
                #    3 | 5     |  9946
                #    4 | 6     |  5473
                #    5 | 7     |  4020
                #    6 | 8     |  2308
                #    7 | 9     |  1780
                #    8 | 10    |  1679
                #    9 | B     |   771
                #   10 | D     |   690
                #   11 | K     | 21659
                #   12 | A     |  7329
                if part == 'wish' and (4 <= c <= 10):
                    continue  # Kartenwerte zw. 6 und Dame werden nicht ausgewogen

                # Geschenk
                # Idx | Label | Count
                #   0 | R     | 37955
                #   1 | L     | 62045

                # Schupfen
                # Idx | Label | Schupf1  | Schupf2  | Schupf3
                #   0 | Hu    |   11040  |   13193  |   10064
                #   1 | Ma    |     993  |    5118  |     382
                #   2 | 2     |   49752  |     829  |   89964
                #   3 | 3     |   63959  |     915  |   43187
                #   4 | 4     |   34199  |    1752  |   44829
                #   5 | 5     |   39142  |    2566  |   25597
                #   6 | 6     |   25733  |    3368  |   28470
                #   7 | 7     |   27856  |    5121  |   18322
                #   8 | 8     |   18341  |    7519  |   18195
                #   9 | 9     |   17326  |   10315  |   11381
                #  10 | 10    |    7302  |   16878  |    6312
                #  11 | B     |    3234  |   26686  |    2485
                #  12 | D     |     991  |   37202  |     735
                #  13 | K     |     109  |   50970  |      63
                #  14 | A     |      20  |   69389  |       6
                #  15 | Dr    |       2  |   30943  |       4
                #  16 | Ph    |       1  |   17236  |       4
                if part in ('schupf1', 'schupf3') and (c == 1 or c >= 10):
                    continue  # MahJong und Kartenwerte ab 10 für die Gegner bleiben unausgewogen
                if part == 'schupf2' and (2 <= c <= 6):
                    continue  # Kartenwerte zw. 2 und 6 für den Partner bleiben unausgewogen

                # Punktedifferenz
                # Idx | Label | Count
                #   0 |  -800 |     0  (== Anzahl bei 160 - Idx)
                # ...
                #  78 |   -20 |   372
                #  79 |   -10 |   327
                #  80 |     0 |   186
                #  81 |    10 |   327
                #  82 |    20 |   372
                #  83 |    30 |   362
                #  84 |    40 |   437
                #  85 |    50 |   377
                #  86 |    60 |   396
                #  87 |    70 |   351
                #  88 |    80 |   355
                #  89 |    90 |   352
                #  90 |   100 |   377
                #  91 |   110 |   234
                #  92 |   120 |   285
                #  93 |   130 |   262
                #  94 |   140 |   349
                #  95 |   150 |   303
                #  96 |   160 |   321
                #  97 |   170 |   242
                #  98 |   180 |   259
                #  99 |   190 |   212
                # 100 |   200 |   985
                # 101 |   210 |   123
                # 102 |   220 |   123
                # 103 |   230 |   126
                # 104 |   240 |   115
                # 105 |   250 |   110
                # 106 |   260 |   107
                # 107 |   270 |    69
                # 108 |   280 |    94
                # 109 |   290 |    54
                # 110 |   300 |  1194
                # 111 |   310 |    28
                # 112 |   320 |    17
                # 113 |   330 |    29
                # 114 |   340 |    11
                # 115 |   350 |    18
                # 116 |   360 |    10
                # 117 |   370 |     6
                # 118 |   380 |     6
                # 119 |   390 |    10
                # 120 |   400 |   308
                # 121 |   410 |     3
                # 122 |   420 |     9
                # 123 |   430 |     2
                # 124 |   440 |     5
                # 125 |   450 |     7
                # 126 |   460 |     7
                # 127 |   470 |     7
                # 128 |   480 |     6
                # 129 |   490 |     3
                # 130 |   500 |    20
                # 131 |   510 |     2
                # 132 |   520 |     0
                # 133 |   530 |     3
                # 134 |   540 |     1
                # 135 |   550 |     1
                # 136 |   560 |     0
                # 137 |   570 |     0
                # 138 |   580 |     0
                # 139 |   590 |     0
                # 140 |   600 |    22
                # ...
                # 160 |   800 |     0
                if part == 'points':
                    continue  # Punktedifferenz bleibt unausgewogen

                # Bonus
                # Idx | Label | Count
                #   0 |  -200 |   220
                #   1 |  -100 |   362
                #   2 |     0 |  7766
                #   3 |   100 |  1284
                #   4 |   200 |   368

                m = len(tmp[c])
                if 0 < m < n:
                    n = m

            # Alle Klassen auf gleiche Länge abschneiden
            for c in range(num_classes):
                a = np.array(tmp[c], dtype=object)
                np.random.shuffle(a)  # mischen
                tmp[c] = a[:n]

        # Zur Gesamtmenge hinzufügen
        for i in range(n):
            for c in range(num_classes):
                if len(tmp[c]) > i:
                    x_ = tmp[c][i]
                    for j in range(num_x):
                        x[j].append(x_[j])
                    if part == 'bonus':
                        y_ = (c - 2) / 2  # todo testen
                        y.append(y_)
                    elif part == 'points':
                        y_ = (c - 80) / 40  # todo testen
                        y.append(y_)
                    else:
                        y.append(c)
                    if len(y) == max_n:
                        # Maximale Anzahl Datensätze erreicht. Datei speichern und Queue zurücksetzen
                        file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
                        with gzip.open(file, 'wb') as fp:
                            pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
                        print(f'{file} gespeichert - letzte ID: {id_}')
                        num_files += 1
                        x = [deque() for _ in range(num_x)]
                        y = deque()

        # Speichern
        file = path.join(folder, f'{section}-{num_files:02d}-{len(y):07d}.pkl.gzip')
        with gzip.open(file, 'wb') as fp:
            pickle.dump(([np.array(x[j]) for j in range(num_x)], np.array(y)), fp)
        print(f'{file} gespeichert - letzte ID: {id_}')

        # letzte ID speichern
        file = path.join(folder, f'id_{section}.pkl')
        with open(file, 'wb') as fp:
            pickle.dump(id_, fp)


def load_samples(section: str, part: str, num=0, n=0, verbose=False):
    """
    Lade Beispiele.

    :param section: 'train', 'val' oder 'test'
    :param part: 'prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'wish', 'card', 'bomb', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points'
    :param num: Nummer der Datei
    :param n: Anzahl Datensätze. Setzt voraus, dass num angegeben ist.
    :param verbose: Mit Ausgabe, dass die Datei geladen wird.
    """
    assert section in ('train', 'val', 'test')
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points')
    folder = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
    if n > 0:
        assert num > 0
        starts = f'{section}-{num:02d}-{n:07d}'
    elif num > 0:
        starts = f'{section}-{num:02d}'
    else:
        starts = section
    files = [file for file in sorted(listdir(folder), reverse=True) if file.startswith(starts)]
    if not files:
        if verbose:
            print(f'Keine Datei in {folder} gefunden.')
        return np.array([]), np.array([])
    file = path.join(folder, files[0])
    if verbose:
        print(f'Lade {file}... ', end='')
    with gzip.open(file, 'rb') as fp:
        # noinspection PickleLoad
        samples = pickle.load(fp)
    if verbose:
        print('ok')
    return samples


def cut_samples(section: str, part: str, num, n, new_n, save=False, verbose=False):
    assert n != new_n

    # Laden
    x, y = load_samples(section, part, num, n, verbose)

    # Teilen
    m = len(x)
    for j in range(m):
        x[j] = x[j][:new_n]
    y = y[:new_n]

    # Speichern
    if save:
        folder = path.join(config.DATA_PATH, f'brettspielwelt/samples/{part}')
        file = path.join(folder, f'{section}-{num:02d}-{len(y):07d}.pkl.gzip')
        if verbose:
            print(f'Speicher {file}... ', end='')
        with gzip.open(file, 'wb') as fp:
            pickle.dump((x, y), fp)
        if verbose:
            print('ok')

    return x, y
