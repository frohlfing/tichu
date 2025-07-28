# todo Baustelle

# Die Klasse wurde von Gemini generiert und von mir noch nicht überarbeitet.

class DecisionTransformerAgent(Agent):
    def __init__(self, model, ...):
        self.model = model
        self.bisherige_trajektorie = []  # Speichert die Historie der Runde

    def reset_round(self):
        # Wichtig: Die Historie für jede neue Runde zurücksetzen
        self.bisherige_trajektorie = []

    async def play(self, ...) -> Tuple[Cards, Combination]:
        # 1. Ziel-RTG festlegen
        ziel_rtg = self.determine_target_rtg(self.pub)  # z.B. basierend auf dem game_score

        # 2. Aktuellen RTG berechnen
        kassierte_punkte_bisher = self.calculate_current_score(self.pub)
        aktueller_rtg = ziel_rtg - kassierte_punkte_bisher

        # 3. Aktuellen Zustand in einen Vektor umwandeln
        zustand_t = create_feature_vector(self.pub, self.priv)

        # 4. Input-Sequenz für das Modell vorbereiten
        #    (DT-Modelle haben oft eine maximale Sequenzlänge, z.B. die letzten 20 Züge)
        input_sequenz = self.bisherige_trajektorie + [(aktueller_rtg, zustand_t)]

        # 5. Vorhersage erhalten
        #    (Die genaue Form des Inputs hängt von der Implementierung des Modells ab)
        aktions_wahrscheinlichkeiten = self.model.predict(input_sequenz)  # Gibt 57 Wahrscheinlichkeiten zurück

        # 6. Besten legalen Zug auswählen (identisch zum MLP-Agenten)
        action_space = build_action_space(...)
        bester_zug = self.select_best_move_from_probs(action_space, aktions_wahrscheinlichkeiten)

        # 7. Update der Trajektorie für den nächsten Zug
        #    Wir fügen die gerade getroffene Entscheidung zur Historie hinzu.
        #    Dafür brauchen wir den Label-Vektor der Aktion.
        aktions_vektor = create_action_vector({'type': 'play', 'cards': bester_zug[0]})
        self.bisherige_trajektorie.append((aktueller_rtg, zustand_t, aktions_vektor))

        return bester_zug

    def determine_target_rtg(self, pub: PublicState) -> int:
        # Hier kommt die "Persönlichkeit" der KI hin
        own_score, opp_score = pub.total_score
        if own_score > 900:
            return 50  # Spiel sicher nach Hause bringen
        if opp_score > 900 and own_score < 700:
            return 250  # Hohes Risiko gehen!
        return 100  # Standard-Ziel

    # ... weitere Hilfsfunktionen ...