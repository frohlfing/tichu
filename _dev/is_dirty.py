
class MyGameState:
    def __init__(self, score=0, level=1):
        self._data = {'score': score, 'level': level}
        self._dirty = set()

    def __getattr__(self, name):
        # Die Methode __getattr__(self, name) wird aufgerufen, wenn versucht wird, auf ein Attribut zuzugreifen, das nicht existiert.
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'GameState' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Die Methode __setattr__(self, name, value) wird aufgerufen, wenn ein Attribut gesetzt wird.
        if name in {'_data', '_original_data', '_dirty'}:
            super().__setattr__(name, value)
        elif name in self._data:
            if self._data[name] != value:
                self._dirty.add(name)
            self._data[name] = value
        else:
            raise AttributeError(f"'GameState' object has no attribute '{name}'")

    def is_dirty(self, name=None):
        # Überprüft, ob ein bestimmtes Attribut bzw. irgendein Attribut geändert wurde.
        if name:
            return name in self._dirty
        return bool(self._dirty)

    def get_dirty(self):
        # Gibt ein Dictionary der geänderten Attribute und deren neuen Werte zurück.
        return {key: self._data[key] for key in self._dirty}

    def mark_clean(self):
        # Setzt den Zustand der Klasse auf "sauber"
        self._dirty.clear()


# Beispielverwendung
state = MyGameState(score=0, level=1)
state.score = 10  # Ändert den Wert von 'score'
print(state.is_dirty('score'))  # True
print(state.get_dirty())  # {'score': 10}
state.mark_clean()
print(state.is_dirty())  # False

try:
    state.new_attribute = 5  # Wird einen Fehler auslösen
except AttributeError as e:
    print(e)  # Ausgabe: 'GameState' object has no attribute 'new_attribute'

