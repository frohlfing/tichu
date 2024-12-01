#import numpy as np

# def __init__(self, seed=None):
#     self._seed: Optional[int] = seed  # Initialwert für Zufallsgenerator (Integer > 0 oder None)
#     self._random: Optional[
#         np.random.Generator] = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig

# def _initialize_random(self):
#     if not self._random:
#         self._random = np.random.default_rng(self._seed)

# # Gibt eine zufällige Ganzzahl zwischen low (inklusiv) und high (exklusiv) zurück
# def _rand_int(self, low, high):
#     if not self._random:
#         self._random = np.random.default_rng(self._seed)
#     return self._random.integers(low, high)

# # Karten mischen
# def shuffle_cards(self):
#     if not self._random:
#         self._random = np.random.default_rng(self._seed)
#     self._random.shuffle(self._mixed_deck)

# BESSER!
# # Gibt eine zufällige Ganzzahl zwischen low (inklusiv) und high (exklusiv) zurück
# def _rand_int(self, low, high):
#     if not self._random:
#         self._random = np.random.RandomState(seed=self._seed)
#     return self._random.randint(low, high)