import json
from json import JSONDecodeError


class MeineKlasse:
    def __init__(self, name, alter):
        self.name = name
        self.alter = alter

    def to_dict(self):
        return {
            'name': self.name,
            'alter': self.alter
        }

    @classmethod
    def from_dict(cls, dict_obj):
        return cls(dict_obj['name'], dict_obj['alter'])


# Serialisieren (Objekt in JSON umwandeln)

my_obj = MeineKlasse('John', 30)

def json_serializer(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, 'to_list'):
        return obj.to_list()
    return obj

try:
    json_str = json.dumps(my_obj, default=json_serializer)
except TypeError as e:
    # Der übergebene Typ ist nicht serialisierbar.
    print(f"The object could not be serialized: {e}")
    exit(0)

print(json_str)  # Ausgabe: {"name": "John", "alter": 30}


# Deserialisieren (JSON-String zurück in ein Objekt umwandeln)

json_str = '{"name": "John", "alter": 30}'

def json_deserializer(dct):
    if 'name' in dct and 'alter' in dct:
        return MeineKlasse.from_dict(dct)
    return dct

try:
    my_obj = json.loads(json_str, object_hook=json_deserializer)
except JSONDecodeError as e:
    # Der JSON-String ist nicht korrekt formatiert.
    print(f"Error decoding JSON: {e}")
    exit(0)

print(my_obj.name, my_obj.alter)  # Ausgabe: John 30

