from itertools import combinations

# noinspection PyProtectedMember
from src.lib.probabilities import union_sets


def union_sets_optimized(sets: list[dict], k: int) -> list[list[dict]]:
    result = [sets]  # Level 1: Ursprungsmengen

    # Level 2 bis k: Kombinationen der Teilmengen
    for c in range(2, k + 1):
        new_unions = set()  # Menge, um Duplikate zu vermeiden
        # Kombiniere nur Mengen aus der vorherigen Ebene
        for comb in combinations(result[c - 2], c):
            union = {}
            for s in comb:
                for key, value in s.items():
                    union[key] = max(union.get(key, 0), value)

            # Wenn gültig, füge zur neuen Ebene hinzu
            if sum(union.values()) <= k:
                # Verwende ein Tuple aus den Items der Vereinigung, um Duplikate zu vermeiden
                new_unions.add(tuple(union.items()))

        # Wenn es gültige Vereinigungen gibt, füge sie hinzu
        if new_unions:
            # Konvertiere die Tupel wieder in Dictionaries
            result.append([dict(union) for union in new_unions])
        else:
            break

    return result


# noinspection DuplicatedCode
if __name__ == "__main__":  # pragma: no cover
    sets = [
        {10: 1, 11: 1, 12: 1, 13: 1, 16: 1},
        {10: 1, 11: 1, 12: 1, 13: 1, 14: 1},
        {11: 1, 12: 1, 13: 1, 14: 1, 16: 1},
        {10: 1, 12: 1, 13: 1, 14: 1, 16: 1},
        {10: 1, 11: 1, 13: 1, 14: 1, 16: 1},
        {10: 1, 11: 1, 12: 1, 14: 1, 16: 1}
    ]

    k = 6

    print("Erwartet:")
    result = union_sets(sets, k) # funktioniert, ist aber viel zu langsam für k > 8 und muss daher optimiert werden
    for level, unions in enumerate(result, start=1):
        print(f"Level {level}: {unions}")

    print("\nAktuell:")
    result = union_sets_optimized(sets, k)  # optimierte Version, aber leider liefert sie ein falsches Ergebnis
    for level, unions in enumerate(result, start=1):
        print(f"Level {level}: {unions}")

