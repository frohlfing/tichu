import numpy as np
from sklearn.metrics import f1_score
from tichu.callbacks import CategoricalMetrics
from unittest import TestCase


class TestComputeMetrics(TestCase):
    def setUp(self):
        pass

    def test_model(self):
        # Callback-Funktion am Modell testen

        # Beispieldaten generieren
        x = np.random.rand(100)
        p = np.random.rand(300).reshape(100, 3)
        v = np.random.rand(100)
        y = p, v

        # Modell anlegen
        from keras import Input
        from keras.layers import Dense
        from keras.models import Model
        x0 = Input(shape=(1,), name='x')
        h0 = Dense(units=16, activation='relu')(x0)
        p0 = Dense(units=3, activation='softmax', dtype='float32', name='p')(h0)
        v0 = Dense(units=1, activation='tanh', dtype='float32', name='v')(h0)
        model = Model(inputs=[x0], outputs=[p0, v0])
        model.compile(optimizer='adam', loss='categorical_crossentropy')

        # Modell trainieren
        compute_metrics = CategoricalMetrics(validation_data=(x, y))
        history = model.fit(x, y, epochs=2, validation_data=(x, y), callbacks=[compute_metrics])

        # history.history:
        #  {'loss': [4.029523849487305, ...],
        #  'val_loss': [4.029523849487305, ...],
        #  'val_f1': [0.13333333333333333, ...],
        #  'val_recall': [0.3333333333333333, ...],
        #  'val_precision': [0.08333333333333333, ...}
        self.assertEqual(['loss', 'val_loss', 'val_y_f1', 'val_y_recall', 'val_y_precision', 'val_y_cm'], list(history.history.keys()))
        self.assertEqual(2, len(history.history['val_p_f1']))  # Anzahl Epochen
        f1 = history.history['val_p_f1'][-1]
        p_true = np.argmax(p, axis=1)
        p_pred, v_pred = model.predict(x)
        p_pred = p_pred.argmax(axis=1)
        f1_pred = f1_score(p_true, p_pred, average='macro', zero_division=0)
        self.assertEqual(f1, f1_pred)
