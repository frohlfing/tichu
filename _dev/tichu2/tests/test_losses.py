import numpy as np
import tensorflow as tf
from tichu.losses import weighted_categorical_crossentropy
from unittest import TestCase


class TestWeightedCategoricalCrossentropy(TestCase):
    def setUp(self):
        pass

    def test_standalone(self):
        y_true = [[0, 1, 0],
                  [0, 0, 1]]

        y_pred = [[0.05, 0.95, 0.],
                  [0.1, 0.8, 0.1]]

        # Original Loss-Funktion
        # für jedes Beispiel wird der Verlust berechnet:
        # loss = -sum(y_true * log(y_pred))
        loss = tf.keras.losses.categorical_crossentropy(y_true, y_pred)  # [0.05129331 2.3025851]
        mean = np.mean(loss)  # 1.1769392490386963

        # Die Klasse spuckt nur den Mittelwert aus
        cce = tf.keras.losses.CategoricalCrossentropy()
        mean2 = cce(y_true, y_pred)
        self.assertAlmostEqual(float(mean), float(mean2), 6)

        # weighted_categorical_crossentropy() ohne Gewichtung
        wcce = weighted_categorical_crossentropy(class_weight=[1, 1, 1])
        loss2 = wcce(y_true, y_pred)
        self.assertEqual((2,), loss2.shape)
        self.assertAlmostEqual(float(loss[0]), float(loss2[0]), 6)
        self.assertAlmostEqual(float(loss[1]), float(loss2[1]), 6)

        # mit Gewichtung
        wcce = weighted_categorical_crossentropy(class_weight=[0.5, 2., 3.])
        loss2 = wcce(y_true, y_pred)
        self.assertEqual((2,), loss2.shape)
        self.assertAlmostEqual(float(loss[0] * 2), float(loss2[0]), 6)
        self.assertAlmostEqual(float(loss[1] * 3), float(loss2[1]), 6)

    def test_model(self):
        # Loss-Funktion am Modell testen

        # Beispieldaten generieren
        x = np.random.rand(100)
        y = np.random.rand(300).reshape(100, 3)

        # Modell anlegen
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(8, input_shape=(1,), activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(3),
            tf.keras.layers.Activation('linear', dtype='float32')
        ])
        wcce = weighted_categorical_crossentropy(class_weight=[0.5, 2., 3.])
        model.compile(optimizer='adam', loss=wcce)

        # Modell trainieren
        history = model.fit(x, y, epochs=2, verbose=0)


        # todo irgendwas berechne ich hire falsch!!
        loss = history.history['loss'][-1]
        y_pred = model.predict([x[-1]])
        loss2 = np.mean(wcce([y[-1]], y_pred))
        self.assertAlmostEqual(float(loss * 2), float(loss2), 6, f'{loss} == {loss2}')
