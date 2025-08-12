# todo Baustelle

# Die Klasse wurde von Gemini generiert und von mir noch nicht überarbeitet.

import numpy as np
from typing import Tuple

from src.players.agent import Agent
from src.lib.cards import Cards
from src.lib.combinations import Combination, CombinationType, build_action_space

# Annahme: Diese Funktionen existieren in einem data_processing Modul
from src.data_processing.vectorization import create_feature_vector


class NNetAgent(Agent):

    def __init__(self, model_path: str, name: Optional[str] = None, ...):
        super().__init__(name, ...)
        # Lade das trainierte Keras/TensorFlow-Modell
        # from tensorflow.keras.models import load_model
        # self.model = load_model(model_path)
        self.model = ...  # Platzhalter für das geladene Modell

    async def play(self, interruptable: bool = False) -> Tuple[Cards, Combination]:
        """
        Wählt einen Zug basierend auf der Vorhersage des Neuronalen Netzes.
        """
        # 1. Erstelle den Feature-Vektor aus dem aktuellen Spielzustand
        # -----------------------------------------------------------
        feature_vector = create_feature_vector(self.pub, self.priv)

        # Das Modell erwartet normalerweise einen "Batch" von Inputs, auch wenn es nur einer ist.
        # Daher formen wir den Vektor um von (375,) zu (1, 375).
        input_tensor = np.expand_dims(feature_vector, axis=0)

        # 2. Hole die Vorhersage (Wahrscheinlichkeiten) vom Neuronalen Netz
        # -----------------------------------------------------------------
        # `prediction` wird ein 2D-Array der Form [[p_card1, p_card2, ..., p_pass]] sein.
        prediction = self.model.predict(input_tensor)

        # Extrahiere den 1D-Vektor mit den 57 Wahrscheinlichkeiten
        probabilities = prediction[0]

        # 3. Bewerte alle legalen Züge aus dem `action_space`
        # ----------------------------------------------------

        # `build_action_space` wird von der GameEngine aufgerufen und das Ergebnis
        # wird hierher übergeben. Nehmen wir an, es ist in `self.pub.action_space`
        # oder wird direkt als Parameter übergeben.
        # Für das Beispiel nehmen wir an, der `action_space` verfügbar ist.
        action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)

        best_action = None
        highest_score = -1.0  # Initialisiere mit einem sehr niedrigen Wert

        for cards, combination in action_space:

            # Berechne einen "Score" für diese spezifische Aktion
            current_score = 0.0

            if combination[0] == CombinationType.PASS:
                # Der Score für "Passen" ist einfach die Wahrscheinlichkeit vom Passen-Neuron.
                # Das 57. Neuron hat den Index 56.
                current_score = probabilities[56]
            else:
                # Für einen Spielzug ist der Score die Summe der Wahrscheinlichkeiten der beteiligten Karten.
                # Dies ist eine einfache, aber effektive Heuristik.
                score = 0.0
                for card in cards:
                    card_index = deck.index(card)  # Finde den Index der Karte (0-55)
                    score += probabilities[card_index]

                # Man könnte den Score noch normalisieren (z.B. durch die Anzahl der Karten teilen),
                # um lange Kombinationen nicht übermäßig zu bevorzugen.
                # Alternative: Log-Wahrscheinlichkeiten summieren (oft numerisch stabiler).
                # Für den Anfang ist die einfache Summe gut.
                current_score = score

            # 4. Finde die Aktion mit dem höchsten Score
            # ---------------------------------------------
            if current_score > highest_score:
                highest_score = current_score
                best_action = (cards, combination)

        # 5. Gib den besten gefundenen legalen Zug zurück
        # ------------------------------------------------

        # Fallback, falls aus irgendeinem Grund kein Zug gefunden wurde (sollte nie passieren,
        # da "Passen" oder Anspiel immer eine Option ist, wenn man Karten hat).
        if best_action is None:
            logger.warning(f"[{self.name}] Konnte keinen besten Zug aus den NN-Vorhersagen ableiten. Wähle ersten Zug aus Action Space.")
            return action_space[0]

        logger.debug(f"[{self.name}] NN wählt Aktion: {stringify_cards(best_action[0]) if best_action[0] else 'Passen'} mit Score {highest_score:.4f}")
        return best_action

    # ... (Implementierungen für schupf, announce, wish etc. würden ähnlich funktionieren,
    #      wahrscheinlich mit separaten, kleineren Modellen)