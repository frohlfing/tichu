# Customer Loss Functions - Benutzerdefinierte Verlustfunktionen für Keras

__all__ = 'weighted_categorical_crossentropy',


def weighted_categorical_crossentropy(class_weight):
    """
    Loss-Funktion categorical_crossentropy() um den Parameter class_weight erweitert.

    Auf diese Weise können unausgeglichenen Klassen (unbalanced classes) eine Gewichtung zugewiesen werden.

    Die fit-Methode unterstützt diese Gewichte auch, aber nur für Single Output Models: model.fit(class_weight=class_weight)

    Usage:
        wcce = weighted_categorical_crossentropy(class_weight=[0.5, 2., 3.])

        model.compile(loss=wcce, optimizer='adam')

    :param list class_weight: Gewichte für jede Klasse, z.B. [0.5, 2., 3.]
    :return: Loss-Funktion categorical_crossentropy
    """

    import tensorflow as tf

    class_weight = tf.convert_to_tensor(class_weight, dtype=tf.float32)

    def loss_fn(y_true, y_pred):
        # y_true ist one-hot-kodiert, z.B. [[0,1,0], [0,0,1]]
        # y_pred ist die Wahrscheinlichkeitsverteilung, z.B. [[0.05, 0.95, 0], [0.1, 0.8, 0.1]]

        # für jedes Beispiel wird der Verlust berechnet: loss = -sum(y_true * log(y_pred)), z.B. [0.05129331 2.3025851]
        loss = tf.keras.losses.categorical_crossentropy(y_true, y_pred)

        # class_weight sind die Gewichte für jede Klasse, z.B. [0.5, 2., 3.]
        # sample_weight sind die Gewichte für jedes Beispiel, z.B. max([[0,1,0], [0,0,1]] * [0.5, 2., 3.]) = max([[0. 2. 0.], [0. 0. 3.]]) = [2. 3.]
        sample_weight = tf.math.reduce_max(tf.math.multiply(y_true, class_weight), axis=1)

        # jedes Beispiel gewichten
        return tf.math.multiply(tf.cast(loss, tf.float32), sample_weight)

    loss_fn.__name__ = 'wcce'
    return loss_fn
