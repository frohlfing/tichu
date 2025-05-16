import config
from tichu.losses import weighted_categorical_crossentropy
import pickle
from os import path, environ

__all__ = 'y_labels', 'num_input', 'load_or_create_model', 'load_model_without_gpu', 'clone_model', 'print_layers'


def y_labels(part: str):
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t',
                    'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb',
                    'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points')
    labels = []
    if part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'bomb'):
        labels = ['Nein', 'Ja']
    elif part == 'figure_t':  # Typ beim Anspiel
        labels = ['Einzel', 'Paar', 'Drilling', 'Treppe', 'FullHouse', 'Straße', 'Bombe']
    elif part == 'figure_n':  # Länge beim Anspiel
        labels = ['4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']
    elif part == 'figure_n_stair':  # Länge beim Anspiel
        labels = ['4', '6', '8', '10', '12', '14']
    elif part == 'figure_n_street':  # Länge beim Anspiel
        labels = ['5', '6', '7', '8', '9', '10', '11', '12', '13', '14']
    elif part == 'figure_n_bomb':  # Länge beim Anspiel
        labels = ['5', '6', '7', '8', '9', '10', '11', '12', '13']
    elif part == 'figure_v':  # Höchste Karte beim Anspiel
        labels = ['Hu', 'Ma', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A', 'Dr']
    elif part == 'card':  # Höchste Karte beim Bedienen
        labels = ['/', 'Ph', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A', 'Dr']  # '/' == Passen; Phönix, wenn 1 oder Wert == Stich
    elif part == 'wish':
        labels = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A']
    elif part == 'gift':
        labels = ['R', 'L']
    elif part in ('schupf1', 'schupf2', 'schupf3'):
        labels = ['Hu', 'Ma', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A', 'Dr', 'Ph']
    elif part == 'bonus':
        labels = ['Bonus']
    elif part == 'points':
        labels = ['Punkte']
    return labels


def num_input(part: str):
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points', 'all')
    if part in ('prelude_grand', 'prelude_not_grand', 'prelude'):
        j = 5  # nur x0a, x0b, x4b, x4c, x4d
    elif part in ('schupf1', 'schupf2', 'schupf3'):
        j = 6  # nur x0a, x0b, x4a, x4b, x4c, x4d
    elif part == 'tichu':
        j = 19  # ohne x4a
    elif part in ('figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v'):
        j = 15
    elif part == 'wish':
        j = 19  # ohne x5
    else:  # part in ('card', 'bomb', 'gift', 'bonus', 'points', 'all'):
        j = 20  # alle
    return j


# Verlustfunktion für unausgeglichene Klassenverteilung
# mit samples/*.pkl ist das nicht mehr erforderlich
def _get_wcce(part: str):
    # 'bonus' und 'points' sind stetige Größen und keine kategorische, daher für WCCE nicht geeignet.
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3')
    import tensorflow as tf
    file = path.join(config.DATA_PATH, f'brettspielwelt/class_weights/{part}.pkl')
    if path.isfile(file):
        with open(file, 'rb') as fp:
            # noinspection PickleLoad
            n, counts, mean, median, weights_mean, weights_median, seconds_gen = pickle.load(fp)
        wcce = weighted_categorical_crossentropy(class_weight=weights_median)
        print(f'Class Weights loaded from {file}')
    else:
        wcce = tf.keras.losses.categorical_crossentropy  # fallback
    return wcce


def load_or_create_model(file: str, part: str):
    """
    Lädt das Model. Falls es nicht existiert, wird ein neues angelegt und gespeichert.

    :param str file: Name der HDF5-Datei (z.B. model.h5)
    :param str part: 'prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus' oder 'points'
    :return: Model
    """
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points')
    
    # Tensorflow Log Level
    # 0 = all messages are logged (default behavior)
    # 1 = INFO messages are not printed
    # 2 = INFO and WARNING messages are not printed
    # 3 = INFO, WARNING, and ERROR messages are not printed
    environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

    # Tensorflow darf wegen Multiprocessing nicht im Hauptprozess importiert werden.
    # Ansonsten würde ein Fork z.B. den GPU-RAM teilen wollen, das kann aber nicht funktionieren.
    import tensorflow as tf

    # GPU gefunden?
    gpus = tf.config.experimental.list_physical_devices('GPU')
    # assert len(gpus) > 0

    # Speicherreservierung dynamisch
    # Ansonst bricht das Training mit folgenden Fehler ab:
    #    "UnknownError: Failed to get convolution algorithm. This is probably because cuDNN failed to initialize"
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

    if config.MIXED_PRECISION:
        # Mixed Precision
        # Für RTX-Karten sollte der Datentyp auf gemischter Genauigkeit festgelegt werden.
        # Dadurch kann die Leistung um mehr als das Dreifache verbessert werden.
        # (siehe https://www.tensorflow.org/guide/mixed_precision)
        policy = tf.keras.mixed_precision.Policy('mixed_float16')
        tf.keras.mixed_precision.set_global_policy(policy)
    else:
        policy = tf.keras.mixed_precision.global_policy()

    print(f'GPUs: {len(gpus)} - Compute dtype: {policy.compute_dtype} - Variable dtype: {policy.variable_dtype}')
    # print(f 'GPU Device Name: {tf.test.gpu_device_name()}')

    # Model laden, falls es existiert
    if path.isfile(file):
        # print(f'Load model "{path.basename(file)}"')
        from keras.models import load_model
        return load_model(file)
        # if part in ('bonus', 'points'):
        #     return load_model(file)
        # else:
        #     wcce = _get_wcce(part)
        #     return load_model(file, custom_objects={'wcce': wcce})

    # Model existiert nicht, also legen wir ein neues an und speichern es

    from keras import Input
    from keras.layers import Concatenate, Conv2D, Dropout, Dense, Flatten, MaxPooling2D, Reshape
    # from keras.layers import Activation, BatchNormalization, Reshape
    from keras.models import Model
    from keras.losses import mean_squared_error, sparse_categorical_crossentropy
    from keras.metrics import MeanAbsoluteError, SparseCategoricalAccuracy  # , CategoricalAccuracy
    from keras.optimizers import Adam, SGD, RMSprop
    from keras.regularizers import l2
    from keras.utils import plot_model

    act = config.ACTIVATION
    dropout = config.DROPOUT
    regu = l2(config.L2) if config.L2 else None
    
    # Input: Handkarten
    x0a = Input(shape=(13, 4), name="x0a")  # 52 normale Karten (13 Karten * 4 Farben)
    x0b = Input(shape=(4,), name="x0b")  # 4 Sonderkarten
    h0 = Reshape((13, 4, 1), name='x0a_reshape')(x0a)  # batch_size x high x width x 1
    h0 = Conv2D(filters=32, kernel_size=(3, 4), padding='same', activation=act, name='x0a_conv2d_1')(h0)
    h0 = MaxPooling2D(pool_size=(2, 2), name='x0a_pooling_1')(h0)
    h0 = Conv2D(filters=32, kernel_size=(3, 4), padding='same', activation=act, name='x0a_conv2d_2')(h0)
    h0 = MaxPooling2D(pool_size=(2, 2), name='x0a_pooling_2')(h0)
    h0 = Conv2D(filters=16, kernel_size=(3, 4), padding='same', activation=act, name='x0a_conv2d_3')(h0)
    h0 = Flatten(name='x0a_flatten')(h0)
    h0 = Concatenate(axis=1, name='x0_concatenate')([h0, x0b])
    h0 = Dense(units=32, activation=act, kernel_regularizer=regu, name='x0_dense')(h0)
    if dropout:
        h0 = Dropout(dropout, name='x0_dropout')(h0)

    # Input: Tichu-Ansagen
    x4b = Input(shape=(2,), name="x4b")  # rechter Gegner
    x4c = Input(shape=(2,), name="x4c")  # Partner
    x4d = Input(shape=(2,), name="x4d")  # linker Gegner
    if part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu'):
        x4a = None
        h4 = Concatenate(axis=1, name='x4_concatenate')([x4b, x4c, x4d])  # keine eigene Tichu-Ansage (soll ja vorausgesagt werden)
    else:
        x4a = Input(shape=(2,), name="x4a")  # meine
        h4 = Concatenate(axis=1, name='x4_concatenate')([x4a, x4b, x4c, x4d])
    h4 = Dense(units=8, activation=act, kernel_regularizer=regu, name='x4_dense_1')(h4)
    h4 = Dense(units=4, activation=act, kernel_regularizer=regu, name='x4_dense_2')(h4)
    if dropout:
        h4 = Dropout(dropout, name='x4_dropout')(h4)

    if part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'schupf1', 'schupf2', 'schupf3'):
        x1a = x1b = x1c = x2 = x3a = x3b = x5 = x6a = x6b = x6c = x6d = x6e = x7 = x8 = None  # damit die IDE nicht mehr meckert
        # für den Auftakt sind weitere Eingaben nicht erforderlich
        h = Concatenate(axis=1, name='x_concatenate')([h0, h4])
    else:
        # zusätzliche Eingaben für das Hauptspiel

        # Input: Schupf-Karten
        x1a = Input(shape=(16,), name="x1a")  # an den rechten Gegner
        x1b = Input(shape=(16,), name="x1b")  # an den Partner
        x1c = Input(shape=(16,), name="x1c")  # an den linken Gegner
        h1 = Concatenate(axis=1, name='x1_concatenate')([x1a, x1b, x1c])
        h1 = Dense(units=32, activation=act, kernel_regularizer=regu, name='x1_dense_1')(h1)
        h1 = Dense(units=16, activation=act, kernel_regularizer=regu, name='x1_dense_2')(h1)
        if dropout:
            h1 = Dropout(dropout, name='x1_dropout')(h1)

        # Input: Anzahl Handkarten aller Spieler
        x2 = Input(shape=(4,), name="x2")
        h2 = Dense(units=4, activation=act, kernel_regularizer=regu, name='x2_dense')(x2)
        if dropout:
            h2 = Dropout(dropout, name='x2_dropout')(h2)

        # Input: Ausgespielte Karten
        x3a = Input(shape=(13, 4), name="x3a")  # 52 normale Karten (13 Karten * 4 Farben)
        x3b = Input(shape=(4,), name="x3b")  # 4 Sonderkarten
        h3 = Reshape((13, 4, 1), name='x3a_reshape')(x3a)  # batch_size x high x width x 1
        h3 = Conv2D(filters=32, kernel_size=(3, 4), padding='same', activation=act, name='x3a_conv2d_1')(h3)
        h3 = MaxPooling2D(pool_size=(2, 2), name='x3a_pooling_1')(h3)
        h3 = Conv2D(filters=32, kernel_size=(3, 4), padding='same', activation=act, name='x3a_conv2d_2')(h3)
        h3 = MaxPooling2D(pool_size=(2, 2), name='x3a_pooling_2')(h3)
        h3 = Conv2D(filters=16, kernel_size=(3, 4), padding='same', activation=act, name='x3a_conv2d_3')(h3)
        h3 = Flatten(name='x3a_flatten')(h3)
        h3 = Concatenate(axis=1, name='x3_concatenate')([h3, x3b])
        h3 = Dense(units=32, activation=act, kernel_regularizer=regu, name='x3_dense')(h3)
        if dropout:
            h3 = Dropout(dropout, name='x3_dropout')(h3)

        # Input: Wunsch
        x5 = Input(shape=(14,), name="x5")
        h5 = Dense(units=8, activation=act, kernel_regularizer=regu, name='x5_dense_1')(x5)
        h5 = Dense(units=4, activation=act, kernel_regularizer=regu, name='x5_dense_2')(h5)
        if dropout:
            h5 = Dropout(dropout, name='x5_dropout')(h5)

        # Input: Stich
        x6a = Input(shape=(4,), name="x6a")  # player
        x6b = Input(shape=(7,), name="x6b")  # type
        x6c = Input(shape=(14,), name="x6c")  # length
        x6d = Input(shape=(15,), name="x6d")  # value
        x6e = Input(shape=(1,), name="x6e")  # points
        h6 = Concatenate(axis=1, name='x6_concatenate')([x6a, x6b, x6c, x6d, x6e])
        h6 = Dense(units=32, activation=act, kernel_regularizer=regu, name='x6_dense_1')(h6)
        h6 = Dense(units=16, activation=act, kernel_regularizer=regu, name='x6_dense_2')(h6)
        if dropout:
            h6 = Dropout(dropout, name='x6_dropout')(h6)

        # Input: Punkte
        x7 = Input(shape=(4,), name="x7")
        h7 = Dense(units=4, activation=act, kernel_regularizer=regu, name='x7_dense')(x7)
        if dropout:
            h7 = Dropout(dropout, name='x7_dropout')(h7)

        # Input: Zuerst fertig
        x8 = Input(shape=(4,), name="x8")
        h8 = Dense(units=4, activation=act, kernel_regularizer=regu, name='x8_dense')(x8)
        if dropout:
            h8 = Dropout(0.1, name='x8_dropout')(h8)

        # Inputs zusammenführen
        if part == 'wish':
            h = Concatenate(axis=1, name='x_concatenate')([h0, h1, h2, h3, h4, h6, h7, h8])  # ohne h5
        elif part in ('figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v'):
            h = Concatenate(axis=1, name='x_concatenate')([h0, h1, h2, h3, h4, h5, h7, h8])  # ohne h6
        else:
            h = Concatenate(axis=1, name='x_concatenate')([h0, h1, h2, h3, h4, h5, h6, h7, h8])

    h = Dense(units=128, activation=act, kernel_regularizer=regu, name='x_dense_1')(h)
    h = Dense(units=64, activation=act, kernel_regularizer=regu, name='x_dense_2')(h)
    h = Dense(units=32, activation=act, kernel_regularizer=regu, name='x_dense_3')(h)
    if dropout:
        h = Dropout(dropout, name='x_dropout')(h)

    # Targets
    y = Dense(units=16, activation=act, kernel_regularizer=regu, name='y_dense_1')(h)
    if part in ('figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v'):  # Kartenkombination im Anspiel (Typ, Länge, Wert)
        y = Dense(units=64, activation=act, kernel_regularizer=regu, name='y_dense_1')(h)
        y = Dense(units=128, activation=act, kernel_regularizer=regu, name='y_dense_2')(y)

    units = len(y_labels(part))
    y = Dense(units, activation='softmax', dtype='float32', name='y')(y)

    # Modell anlegen
    if part in ('prelude_grand', 'prelude_not_grand', 'prelude'):
        x = [x0a, x0b, x4b, x4c, x4d]
    elif part in ('schupf1', 'schupf2', 'schupf3'):
        x = [x0a, x0b, x4a, x4b, x4c, x4d]
    elif part == 'tichu':
        x = [x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4b, x4c, x4d, x5, x6a, x6b, x6c, x6d, x6e, x7, x8]  # ohne x4a
    elif part == 'wish':
        x = [x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4a, x4b, x4c, x4d, x6a, x6b, x6c, x6d, x6e, x7, x8]  # ohne x5
    elif part in ('figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v'):  # ohne x6
        x = [x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4a, x4b, x4c, x4d, x5, x7, x8]
    else:  # part in ('card', 'bomb', gift', 'bonus', 'points'):
        x = [x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4a, x4b, x4c, x4d, x5, x6a, x6b, x6c, x6d, x6e, x7, x8]
    assert len(x) == num_input(part)
    model = Model(inputs=x, outputs=y, name='model')

    # Model kompilieren
    if config.OPTIMIZER == 'adam':
        opti = Adam(learning_rate=config.LR)
    elif config.OPTIMIZER == 'sgd':
        opti = SGD(learning_rate=config.LR)
    elif config.OPTIMIZER == 'rmsprop':
        opti = RMSprop(learning_rate=config.LR)
    else:
        opti = config.OPTIMIZER

    if part in ('bonus', 'points'):
        model.compile(optimizer=opti, loss=[mean_squared_error], metrics=[MeanAbsoluteError(name='mae')])
    else:
        # wcce = _get_wcce(part)
        # model.compile(optimizer=opti, loss=[wcce], metrics=[CategoricalAccuracy(name='acc')])
        model.compile(optimizer=opti, loss=[sparse_categorical_crossentropy], metrics=[SparseCategoricalAccuracy(name='acc')])

    # Modell speichern
    print(f'Create model "{path.basename(file)}"')
    model.save(file)

    # Architektur dokumentieren
    plot_model(model, to_file=f'{file[:-3]}.png', show_shapes=True)
    with open(f'{file[:-3]}.txt', 'w') as f:
        model.summary(print_fn=lambda line: f.write(line + '\n'))

    return model


def load_model_without_gpu(file: str, part: str):
    """
    Lädt das Model ohne Nutzung der GPU.

    :param str file: Name der HDF5-Datei (z.B. model.h5)
    :param str part: 'prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus' oder 'points'
    :return: Modell
    """
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points')

    # GPU ausblenden
    environ['CUDA_VISIBLE_DEVICES'] = '-1'  # wirft Error: "failed call to cuInit: CUDA_ERROR_NO_DEVICE: no CUDA-capable device is detected"
    environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # daher erstmal ERROR-Meldungen abschalten - doof, aber keine ander Lösung gefunden :-(
    from keras.models import load_model  # Tensorflow darf wegen Multiprocessing nicht im Hauptprozess importiert werden.

    # Model laden
    model = load_model(file)
    # if part in ('bonus', 'points'):
    #     model = load_model(file)
    # else:
    #     wcce = _get_wcce(part)
    #     model = load_model(file, custom_objects={'wcce': wcce})

    # Tensorflow Log Level
    # 0 = all messages are logged (default behavior)
    # 1 = INFO messages are not printed
    # 2 = INFO and WARNING messages are not printed
    # 3 = INFO, WARNING, and ERROR messages are not printed
    environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

    # Anzahl GPUs sollte jetzt 0 sein
    import tensorflow as tf
    assert len(tf.config.experimental.list_physical_devices('GPU')) == 0

    return model


def clone_model(model, part: str, copy_weights: True):
    """
    Kopiert das Model ohne Gewichte.

    :param keras.models.Model model: Modell, das kopiert werden soll
    :param str part: 'prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus' oder 'points'
    :param bool copy_weights: Wenn True, werden auch die Gewichte übernommen. Ansonsten ist das neue Modell untrainiert. Default: True
    :return: Neues Modell
    """
    assert part in ('prelude_grand', 'prelude_not_grand', 'prelude', 'tichu', 'figure_t', 'figure_n', 'figure_n_stair', 'figure_n_street', 'figure_n_bomb', 'figure_v', 'card', 'bomb', 'wish', 'gift', 'schupf1', 'schupf2', 'schupf3', 'bonus', 'points')

    environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
    from keras.models import clone_model
    from keras.metrics import MeanAbsoluteError, SparseCategoricalAccuracy
    new_model = clone_model(model)

    # Das geklonte Modell ist noch nicht kompiliert. Holen wir jetzt nach.
    # Schade: metrics können nicht vom model übernommen werden!
    if model.optimizer:
        if part in ('bonus', 'points'):
            model.compile(optimizer=model.optimizer, loss=model.loss, metrics=[MeanAbsoluteError(name='mae')])
        else:
            model.compile(optimizer=model.optimizer, loss=model.loss, metrics=[SparseCategoricalAccuracy(name='acc')])

    # Gewichte übernehmen
    if copy_weights:
        new_model.set_weights(model.get_weights())

    return new_model


def print_layers(model):
    names = sorted([layer.name for layer in model.layers])
    for name in names:
        layer = model.get_layer(name)
        print(f'{name}:  Trainable={layer.trainable}')
    print(len(names))
