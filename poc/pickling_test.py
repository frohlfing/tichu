# --- Am Ende von src/public_state2.py (oder in separater Datei) ---
from src.lib.combinations import CombinationType
from src.public_state2 import PublicState
import pickle

if __name__ == "__main__":

    print("Teste Pickling von PublicState...")

    # Erstelle eine Beispielinstanz mit einigen Daten
    test_state = PublicState(
        table_name="TestTisch",
        player_names=["Alice", "Bob", "Charlie", "David"],
        current_turn_index=1,
        total_scores=[150, 210],
        round_counter=3,
        last_played_cards_internal=[(14, 1), (14, 2)], # Beispiel: Paar Asse (intern)
        last_combination_details=(CombinationType.PAIR, 2, 14), # Beispiel
        last_player_index=0,
        num_cards_in_hand=[5, 6, 5, 6],
        current_phase="playing"
    )
    print(f"Original Objekt: {test_state}")

    try:
        # Versuche zu picklen (in Bytes zu serialisieren)
        pickled_state = pickle.dumps(test_state)
        print(f"Pickling erfolgreich! ({len(pickled_state)} Bytes)")

        # Versuche zu unpicklen (aus Bytes zu deserialisieren)
        unpickled_state = pickle.loads(pickled_state)
        print("Unpickling erfolgreich!")
        print(f"Neues Objekt:    {unpickled_state}")

        # Vergleiche (optional, __eq__ muss in PublicState implementiert sein,
        # was bei @dataclass standardmäßig der Fall ist)
        if test_state == unpickled_state:
            print("Vergleich: Objekte sind gleichwertig.")
        else:
            print("Vergleich: Objekte sind NICHT gleichwertig.")

    except Exception as e:
        print(f"\n!!! FEHLER BEIM PICKLING/UNPICKLING: {e}")
        import traceback
        traceback.print_exc()

    print("\nPickling-Test beendet.")