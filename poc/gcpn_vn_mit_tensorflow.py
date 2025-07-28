"""
TensorFlow-Implementation von GCPN+VN.

Hier ist ein einfaches Musterbeispiel für die kombinierte GCPN+VN Architektur.
"""

import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Dropout, Concatenate
from tensorflow.keras.models import Model


def build_hybrid_model_tf():
    # --- Inputs ---
    state_input = Input(shape=(375,), name='state_input')
    rtg_input = Input(shape=(1,), name='rtg_input')

    # --- Shared Backbone ---
    shared = Dense(1024, activation='relu')(state_input)
    shared = Dropout(0.2)(shared)
    shared = Dense(1024, activation='relu')(shared)
    shared = Dropout(0.2)(shared)
    # `shared` ist jetzt unser "Gedanken-Vektor"

    # --- Value Head ---
    value_hidden = Dense(256, activation='relu')(shared)
    value_output = Dense(1, activation='linear', name='value_output')(value_hidden)

    # --- Policy Head ---
    # Konkateniere den Gedanken-Vektor mit dem RTG-Input
    policy_input = Concatenate()([shared, rtg_input])
    policy_hidden = Dense(512, activation='relu')(policy_input)
    policy_output = Dense(57, activation='sigmoid', name='policy_output')(policy_hidden)

    # --- Erstelle das finale Modell ---
    model = Model(
        inputs={'state_input': state_input, 'rtg_input': rtg_input},
        outputs={'policy_output': policy_output, 'value_output': value_output}
    )

    # --- Kompiliere das Modell mit zwei Verlustfunktionen ---
    model.compile(
        optimizer='adam',
        loss={
            'policy_output': 'binary_crossentropy',
            'value_output': 'mean_squared_error'
        },
        # Optional: Gewichtung der Verluste
        loss_weights={'policy_output': 1.0, 'value_output': 0.5}
    )

    return model


# Modell erstellen und anzeigen
hybrid_model = build_hybrid_model_tf()
hybrid_model.summary()