# tests/test_rand.py
"""
Tests für src.common.rand.

Zusammenfassung der Tests für Random:
- Initialisierung:
    Prüft, ob der Seed korrekt gespeichert und der interne Generator (_random) anfangs None ist.

- Lazy Initialization:
Stellt sicher, dass _random erst beim ersten Aufruf einer Methode initialisiert wird und dabei der korrekte Seed verwendet wird.

- Methoden-Tests (integer, boolean, choice, sample, shuffle):
    - Prüfen die Rückgabetypen.
    - Prüfen, ob die Werte im erwarteten Bereich liegen bzw. aus der Eingabesequenz stammen.
    - Testen Randfälle (z.B. integer mit nur einem möglichen Wert, sample mit k=Länge).
    - Testen grundlegend die Logik (z.B. Einzigartigkeit bei sample, Änderung bei shuffle, Gewichtung bei choice).

- Reproduzierbarkeit:
    Der wichtigste Test hier! Stellt sicher, dass zwei Instanzen mit demselben Seed exakt dieselbe Sequenz von
    Zufallsereignissen über verschiedene Methoden hinweg erzeugen.

- Unterschiedlichkeit:
    Stellt sicher, dass unterschiedliche Seeds (oder keine Seeds) zu unterschiedlichen Ergebnissen führen (mit hoher
    Wahrscheinlichkeit).
"""

import pytest
import random as std_random # Standard-Modul zum Vergleichen

# Zu testende Klasse
from src.common.rand import Random

# === Testfälle ===

def test_random_init_without_seed():
    """Testet die Initialisierung ohne festen Seed."""
    custom_rand = Random()
    assert custom_rand._seed is None
    assert custom_rand._random is None # Noch nicht initialisiert

def test_random_init_with_seed():
    """Testet die Initialisierung mit festem Seed."""
    seed = 12345
    custom_rand = Random(seed=seed)
    assert custom_rand._seed == seed
    assert custom_rand._random is None # Noch nicht initialisiert

def test_random_lazy_initialization():
    """Testet, ob der interne Generator erst bei Bedarf initialisiert wird."""
    seed = 99
    custom_rand = Random(seed=seed)
    assert custom_rand._random is None
    # Erster Aufruf einer Methode sollte initialisieren
    custom_rand.integer(0, 10)
    assert custom_rand._random is not None
    assert isinstance(custom_rand._random, std_random.Random)
    # Prüfen, ob der Seed verwendet wurde (indirekt durch Vergleich)
    expected_gen = std_random.Random(seed)
    assert custom_rand._random.getstate() == expected_gen.getstate()

def test_random_integer_range():
    """Testet, ob 'integer' Zahlen im korrekten Bereich [low, high-1] liefert."""
    custom_rand = Random(seed=1)
    low = 5
    high = 8 # Exklusiv, also erwartet: 5, 6, 7
    results = set()
    for _ in range(50): # Viele Versuche
        val = custom_rand.integer(low, high)
        assert isinstance(val, int)
        assert low <= val < high
        results.add(val)
    # Prüfen, ob alle erwarteten Werte vorkamen (nicht garantiert, aber wahrscheinlich)
    assert results.issuperset({5, 6, 7})

def test_random_integer_single_value():
    """Testet den Fall, wo low und high nur einen Wert erlauben."""
    custom_rand = Random(seed=2)
    assert custom_rand.integer(10, 11) == 10

def test_random_boolean():
    """Testet, ob 'boolean' nur True oder False liefert."""
    custom_rand = Random(seed=3)
    results = set()
    for _ in range(30):
        val = custom_rand.boolean()
        assert isinstance(val, bool)
        results.add(val)
    # Beide Werte sollten vorkommen (wahrscheinlich)
    assert results == {True, False}

def test_random_choice_no_weights():
    """Testet 'choice' ohne Gewichtung."""
    custom_rand = Random(seed=4)
    sequence = [10, 20, 30, 40]
    results = set()
    for _ in range(50):
        val = custom_rand.choice(sequence)
        assert val in sequence
        results.add(val)
    # Alle Elemente sollten vorkommen (wahrscheinlich)
    assert results == set(sequence)

def test_random_choice_with_weights():
    """Testet 'choice' mit Gewichtung."""
    custom_rand = Random(seed=5)
    sequence = ['a', 'b', 'c']
    weights = [10, 1, 1] # 'a' sollte viel häufiger gewählt werden
    counts = {'a': 0, 'b': 0, 'c': 0}
    num_runs = 1000
    for _ in range(num_runs):
        val = custom_rand.choice(sequence, weights=weights)
        assert val in sequence
        counts[val] += 1
    # Prüfe, ob 'a' signifikant häufiger gewählt wurde
    assert counts['a'] > counts['b'] * 5 # Erwarte Faktor ~10
    assert counts['a'] > counts['c'] * 5
    assert counts['a'] + counts['b'] + counts['c'] == num_runs

def test_random_sample():
    """Testet 'sample'."""
    custom_rand = Random(seed=6)
    sequence = list(range(10)) # [0, 1, ..., 9]
    k = 4
    for _ in range(20):
        result = custom_rand.sample(sequence, k)
        assert isinstance(result, list)
        assert len(result) == k
        # Alle Elemente im Sample müssen aus der Originalsequenz sein
        assert all(item in sequence for item in result)
        # Alle Elemente im Sample müssen einzigartig sein (ohne Zurücklegen)
        assert len(set(result)) == k

def test_random_sample_k_equals_len():
    """Testet 'sample', wenn k gleich der Länge der Sequenz ist (Permutation)."""
    custom_rand = Random(seed=7)
    sequence = ['x', 'y', 'z']
    k = 3
    result = custom_rand.sample(sequence, k)
    assert len(result) == k
    assert set(result) == set(sequence) # Muss alle Elemente enthalten

def test_random_shuffle():
    """Testet 'shuffle'."""
    custom_rand = Random(seed=8)
    # Wähle einen Seed, der bekanntlich die Reihenfolge ändert
    sequence = list(range(10))
    original_sequence = list(sequence) # Kopie

    custom_rand.shuffle(sequence) # Modifiziert in-place

    # Reihenfolge sollte anders sein (sehr wahrscheinlich mit diesem Seed/Sequenz)
    assert sequence != original_sequence
    # Alle Originalelemente müssen noch vorhanden sein
    assert set(sequence) == set(original_sequence)
    # Länge muss gleich sein
    assert len(sequence) == len(original_sequence)

def test_random_reproducibility_with_seed():
    """Testet, ob derselbe Seed dieselbe Sequenz von Zufallszahlen erzeugt."""
    seed = 101
    # Generator 1
    rand1 = Random(seed=seed)
    seq1 = [rand1.integer(0, 100) for _ in range(10)]
    choice1 = rand1.choice(['x', 'y'], weights=[1, 5])
    sample1 = rand1.sample(range(20), 5)
    bool1 = rand1.boolean()
    shuffled_list1 = list(range(5))
    rand1.shuffle(shuffled_list1)

    # Generator 2 (gleicher Seed)
    rand2 = Random(seed=seed)
    seq2 = [rand2.integer(0, 100) for _ in range(10)]
    choice2 = rand2.choice(['x', 'y'], weights=[1, 5])
    sample2 = rand2.sample(range(20), 5)
    bool2 = rand2.boolean()
    shuffled_list2 = list(range(5))
    rand2.shuffle(shuffled_list2)

    # Vergleiche die Ergebnisse
    assert seq1 == seq2
    assert choice1 == choice2
    assert sample1 == sample2
    assert bool1 == bool2
    assert shuffled_list1 == shuffled_list2

def test_random_difference_without_seed_or_different_seed():
    """Testet, ob unterschiedliche Seeds oder kein Seed unterschiedliche Sequenzen erzeugen."""
    # Generator 1 (kein Seed)
    rand1 = Random()
    seq1 = [rand1.integer(0, 1000) for _ in range(10)]

    # Generator 2 (anderer Seed)
    rand2 = Random(seed=9876)
    seq2 = [rand2.integer(0, 1000) for _ in range(10)]

    # Generator 3 (kein Seed, neue Instanz)
    rand3 = Random()
    seq3 = [rand3.integer(0, 1000) for _ in range(10)]


    # Die Sequenzen sollten (extrem wahrscheinlich) unterschiedlich sein
    assert seq1 != seq2
    assert seq1 != seq3
    assert seq2 != seq3