# BrettspielWelt-Daten aufbereiten und Model durch überwachtes Lernen (Supervised Learning) trainieren

from tichu.brettspielwelt.class_weights import create_class_weights
from tichu.brettspielwelt.database import Database
from tichu.brettspielwelt.coach import Coach
from tichu.brettspielwelt.generator import print_stdev_trick_points
from tichu.brettspielwelt.samples import create_samples, load_samples
from tichu.gpu import print_gpu_info


# Logdateien in die Datenbank einlesen
def import_logs():
    db = Database()
    db.import_logs(y2=2022, m2=4)
    print('fertig')


def sql_report():
    db = Database()

    # Zeitraum:         2007-01-09 19:03 bis 2022-04-30 23:32
    # Anzahl Episoden:   2.352.727
    # Anzahl Runden:    22.042.274
    # Punktedifferenz:  159.5 +-110.3; Max 800
    # Stiche/Runde:      11.0 +-  2.2; Max  29
    # Kartenzüge/Runde:  55.8 +- 10.1; Max 118
    # Züge/Stich:         5.2 +-  0.8; Max  12
    db.report()

    db.print_distribution_points()
    db.print_distribution_bonus()

    # Max. Punkte im Stich: 26.5 +-15.5; Max.: 80; n=100000
    print_stdev_trick_points()


def class_weights():
    n = 100000
    # create_class_weights('prelude_grand', n=n)
    # create_class_weights('prelude_not_grand', n=n)
    # create_class_weights('prelude', n=n)
    # create_class_weights('tichu', n=n)
    # create_class_weights('figure_t', n=n)
    # create_class_weights('figure_n', n=n)
    # create_class_weights('figure_n_stair', n=n)
    # create_class_weights('figure_n_street', n=n)
    # create_class_weights('figure_n_bomb', n=n)
    # create_class_weights('figure_v', n=n)
    # create_class_weights('card', n=n)
    # create_class_weights('bomb', n=n)
    # create_class_weights('wish', n=n)
    # create_class_weights('gift', n=n)
    create_class_weights('schupf1', n=n)
    create_class_weights('schupf2', n=n)
    create_class_weights('schupf3', n=n)


def samples():
    # cut_samples('val', 'tichu', num=1, n=200000, new_n=100000, save=True, verbose=True)
    # cut_samples('test', 'tichu', num=1, n=200000, new_n=100000, save=True, verbose=True)
    for section in ('val', 'test', 'train'):
        batch_size = 200000 if section == 'train' else 100000
        # create_samples(section, 'prelude_grand', batch_size=batch_size, max_files=1)
        # create_samples(section, 'prelude_not_grand', batch_size=batch_size, max_files=1)
        # create_samples(section, 'prelude', batch_size=batch_size, max_files=1)
        # create_samples(section, 'tichu', batch_size=batch_size, max_files=1)
        create_samples(section, 'figure_t', batch_size=batch_size, max_files=1)
        create_samples(section, 'figure_n', batch_size=batch_size, max_files=1)
        # create_samples(section, 'figure_n_stair', batch_size=batch_size, max_files=1)
        # create_samples(section, 'figure_n_street', batch_size=batch_size, max_files=1)
        # create_samples(section, 'figure_n_bomb', batch_size=batch_size, max_files=1)
        create_samples(section, 'figure_v', batch_size=batch_size, max_files=1)
        # create_samples(section, 'card', batch_size=batch_size, max_files=1)
        # create_samples(section, 'bomb', batch_size=batch_size, max_files=1)
        # create_samples(section, 'wish', batch_size=batch_size, max_files=1)
        # create_samples(section, 'gift', batch_size=batch_size, max_files=1)
        # create_samples(section, 'schupf1', batch_size=batch_size, max_files=1)
        # create_samples(section, 'schupf2', batch_size=batch_size, max_files=1)
        # create_samples(section, 'schupf3', batch_size=batch_size, max_files=1)


def sample_report():
    # todo Verteilung anzeigen
    data = load_samples('val', 'tichu')
    print(len(data))


def train():
    print_gpu_info()
    print()
    # part = 'tichu'
    # part = 'prelude_grand'
    # part = 'figure_t'
    part = 'figure_n'
    print(f'Part: {part}')
    coach = Coach(part=part, version=1)
    # coach.train()
    # coach.restore_from_checkpoint(save_model=True)


def evaluate_model():
    part = 'tichu'
    print(f'Part: {part}')
    coach = Coach(part=part, version=2)
    coach.evaluate(untrained=True, check=False)  # Trefferquote beim zufälligen Raten
    coach.evaluate()


if __name__ == '__main__':
    # import_logs()
    # sql_report()
    class_weights()
    # samples()
    # train()
    # evaluate_model()
