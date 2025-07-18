"""
Definiert die Arena, in der Agenten gegeneinander spielen können.
"""

import asyncio
from multiprocessing import Pool, Manager, cpu_count
from src import config
from src.common.logger import logger
from src.game_engine import GameEngine
from src.players.agent import Agent
from src.public_state import PublicState
from time import time
from typing import Optional

async def _create_engine_and_run(table_name: str, agents: list[Agent], seed: Optional[int]) -> Optional[PublicState]:
    """
    Erzeugt die Game-Engine und führt eine Partie asynchron aus.

    Diese Funktion ist eine Coroutine, muss also im Context von asyncio aufgerufen werden.

    :param table_name: Der Name des Tisches.
    :param agents: Die 4 Agenten.
    """
    try:
        engine = GameEngine(table_name, default_agents=agents, seed=seed)
        pub = await engine.run_game_loop()
        return pub
    except Exception as e:
        logger.exception(f"[Arena] Unerwarteter Fehler in der Game-Engine '{table_name}': {e}")
        return None


class Arena:
    """
    Repräsentiert die Arena, in der Agenten gegeneinander antreten können.
    """

    def __init__(self, agents: list[Agent], max_games: int, verbose: bool = False,
                 early_stopping: bool = False, win_rate: float = config.ARENA_WIN_RATE,
                 worker: int = config.ARENA_WORKER,
                 seed: int = None):
        """
            Initialisiert eine neue Instanz der Arena-Klasse.

            Dies stellt den Rahmen für einen Wettkampf zwischen vier Agenten dar, die in einer Reihe von Partien
            gegeneinander antreten.

            :param agents: Liste von vier Agenten (Agent 0 bis Agent 3), die gegeneinander antreten.
            :param max_games: Maximale Anzahl der zu spielenden Partien.
            :param verbose: Gibt an, ob der Spielverlauf detailliert angezeigt werden soll.
            :param early_stopping: Wenn True, wird der Wettkampf abgebrochen, sobald die gewünschte Gewinnquote erreicht oder nicht mehr erreicht werden kann.
            :param win_rate: Gewünschte Gewinnquote (WIN / (WIN + LOST)); wird nur verwendet, wenn early_stopping gesetzt ist.
            :param worker: Wenn größer 1, werden die Partien in entsprechend vielen Prozessen parallel ausgeführt.
            :param seed: Seed für den Zufallsgenerator.
            :raises AssertionError: Falls die Anzahl der Agenten nicht 4 beträgt.
            """
        assert len(agents) == 4
        self._agents = agents
        self._max_games = max_games
        self._verbose = verbose
        self._early_stopping = early_stopping
        self._win_rate = win_rate
        self._worker = worker
        self._seed = seed
        self._stop_event = Manager().Event() if worker > 1 else asyncio.Event()  # Event zum Unterbrechen der Partie
        #self._progbar = Progbar(max_games, stateful_metrics=["Wins", "Lost", "Draws"])
        # Statistik
        self._time_start = None  # Zeitstempel zu Beginn der ersten Partie.
        self._seconds: int = 0  # Spieldauer insgesamt in Sekunden
        self._games: int = 0  # Anzahl Partien
        self._rounds: int = 0  # Rundenzähler über alle Partien
        self._tricks: int = 0  # Stichzähler über alle Partien
        self._rating = [0, 0, 0]  # Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)

    def run(self):
        """
        Führt den Wettkampf durch.
        """

        self._time_start = time()

        #if not self._verbose:
        #    self._progbar.update(0, values=[("Wins", 0), ("Lost", 0), ("Draws", 0)])

        if self._worker > 1:
            pool = Pool(processes=self._worker)
            for game_index in range(self._max_games):
                pool.apply_async(self._play_game, args=(game_index,), callback=self._update)
            # processes = [pool.apply_async(self._play_game, args=(game_index,)) for game_index in range(max_games)]
            # for p in processes:
            #     self._update(p.get())
            pool.close()  # verhindert, dass weitere Aufgaben an den Pool gesendet werden
            pool.join()  # warten, bis die Worker-Prozesse beendet sind
        else:  # worker == 1
            for game_index in range(self._max_games):
                self._update(self._play_game(game_index))

        if self._verbose:  # pragma: no cover
            print("\r ")
        #else:
        #    if sum(self._rating) < self._max_games:
        #        self._progbar.update(sum(self._rating), finalize=True)  # es wurde früher beendet

    def _play_game(self, game_index: int) -> Optional[tuple]:
        """
        Führt eine einzelne Partie durch, sofern der Wettkampf nicht abgebrochen wurde.

        Diese Methode läuft im Multiprocessing-Mode parallel im eigenen Prozess!

        :param game_index: Der Index der Partie.
        :return: Index der Partie und der öffentliche Spielzustand (bzw. False, wenn der Wettkampf abgebrochen wurde).
        """
        # Partie nicht ausführen, falls der Wettkampf abgebrochen wurde.
        if self._stop_event.is_set():
            return None

        # Wichtig: Jeder Prozess braucht seine eigene Event-Loop.
        pub = asyncio.run(_create_engine_and_run(table_name=f"Game_{game_index}", agents=self._agents, seed=self._seed))

        return game_index, pub

    def _update(self, result):
        """
        Aktualisiert die Statistiken basierend auf dem Ergebnis einer einzelnen Partie.

        Diese Methode wird verwendet, um die kumulierten Daten des Wettkampfs nach einer gespielten Partie
        zu aktualisieren.

        Diese Methode läuft wieder im Hauptprozess!

        :param result: Das Ergebnis von `_play_game()`.
        """
        if not result:
            return  # der Wettkampf wurde abgebrochen

        game_index: int
        pub: PublicState
        game_index, pub = result

        self._seconds = time() - self._time_start
        self._games += 1
        self._tricks += pub.trick_counter
        self._rounds += pub.round_counter

        score = sum(pub.game_score[0]), sum(pub.game_score[1])
        if score[0] > score[1]:
            self._rating[0] += 1
        elif score[0] < score[1]:
            self._rating[1] += 1
        else:
            self._rating[2] += 1

        if self._early_stopping:
            total = self._max_games - self._rating[2]  # Unentschieden fällt nicht in die Bewertung
            unplayed = self._max_games - sum(self._rating)
            if total > 0 and float(self._rating[0]) / total >= self._win_rate:
                self._stop_event.set()  # die gewünschte Gewinnquote ist sicher erreicht
            elif total > 0 and float(self._rating[0] + unplayed) / total < self._win_rate:
                self._stop_event.set()  # die gewünschte Gewinnquote kann nicht mehr erreicht werden

        if self._verbose:  # pragma: no cover
            if self._games == 1:
                print("\nPartie | Runden |    Score    |    Rating   ")
            print(f"\r{(game_index + 1):7d}"
                  f" | {pub.round_counter:6d}"
                  f" | {score[0]:>5d}/{score[1]:<5d}"
                  f" | {self._rating[0]:>5d}/{self._rating[1]:<5d}")
            seconds_per_game = self._seconds / self._games
            print(f"Restzeit ca. {(self._max_games - self._games) * seconds_per_game:6.3f} s", end="")
        #else:
        #    self._progbar.update(sum(self._rating), values=[("Wins", self._rating[0]), ("Lost", self._rating[1]), ("Draws", self._rating[2])])

    @staticmethod
    def cpu_count() -> int:
        """
        Ermittelt die Anzahl verfügbarer CPU-Kerne
        """
        return cpu_count()

    @property
    def seconds(self) -> int:
        """
        Spieldauer insgesamt in Sekunden
        """
        return self._seconds

    @property
    def games(self) -> int:
        """
        Anzahl Partien
        """
        return self._games

    @property
    def rounds(self) -> int:
        """
        Anzahl Runden insgesamt über alle Partien
        """
        return self._rounds

    @property
    def tricks(self) -> int:
        """
        Anzahl Stiche insgesamt über alle Partien
        """
        return self._tricks

    @property
    def rating(self) -> list:
        """
        Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)
        """
        return self._rating
