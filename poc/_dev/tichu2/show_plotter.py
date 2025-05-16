import pickle
from os import path
import config
from tichu.combinations import figurelabels
from tichu.callbacks import LifePlotter
from tichu.nnet import y_labels


def labels(part: str):
    # Labels für p
    p_labels = []
    if part == 'tichu':
        p_labels = ['Nein', 'Ja']
    elif part == 'schupf':
        p_labels = ['Hu', 'Ma', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A', 'Dr', 'Ph']
    elif part == 'wish':
        p_labels = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A']
    elif part == 'gift':
        p_labels = ['R', 'L']
    elif part == 'figure':
        p_labels = figurelabels  # range(227)
    return p_labels


def cut_data(file_: str, n: int):
    with open(file_, 'rb') as fp:
        # noinspection PickleLoad
        x, y_train, y_val = pickle.load(fp)

    x = x[:100]
    for metric in y_train:
        y_train[metric] = y_train[metric][:100]
    for metric in y_val:
        y_val[metric] = y_val[metric][:100]

    with open(file_, 'wb') as fp:
        pickle.dump((x, y_train, y_val), fp)


if __name__ == '__main__':
    part = 'tichu'
    version = 3
    file = path.join(config.DATA_PATH, f'brettspielwelt/models/{part}_{version:02d}/plot.pkl')
    # cut_data(file, 100)

    metrics = 'loss', 'cm', 'acc', 'recall', 'precision', 'f1'
    plotter = LifePlotter(file,
                          width=12, height=6,
                          nrows=2, ncols=3,
                          metrics=metrics,
                          colors=('red', 'black', 'blue', 'orange', 'green', 'blue'),
                          cm_labels=y_labels(part),
                          cm_normalize=True)
    plotter.show()
    plotter.save()
