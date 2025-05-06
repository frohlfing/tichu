import asyncio
import config
from multiprocessing import Pool, Manager, cpu_count
from src.common.logger import logger
from src.game_engine2 import GameEngine
from src.players.agent import Agent
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from time import time
from typing import Optional, List


# todo Datei und Klasse dokumentieren (reStructuredText)


async def _run_game(table_name: str, agents: list[Agent], seed: Optional[int], pub: Optional[PublicState], privs: Optional[List[PrivateState]]) -> Optional[PublicState]:
    """ Führt eine Partie asynchron aus. """
    try:
        # Erstelle Engine
        engine = GameEngine(table_name, default_agents=agents, seed=seed)

        # Starte das Spiel
        await engine.run_game_loop(pub=pub, privs=privs)

        # Warte auf das Ende des game_loop_tasks
        if engine.game_loop_task:
            await engine.game_loop_task
            # Nach Ende des Tasks ist der finale State in engine.public_state
            return engine.public_state
        else:
            logger.error(f"GameEngine {table_name} wurde nicht gestartet.")
            return None
    except Exception as e:
        logger.exception(f"Fehler in GameEngine {table_name}: {e}")
        return None


class Arena:
    # In der Arena können Agenten gegeneinander antreten.

    def __init__(self, agents: list[Agent], max_episodes: int, verbose: bool = False,
                 early_stopping: bool = False, win_rate: float = config.ARENA_WIN_RATE,
                 pubs: list[PublicState] = None, privs: list[list[PrivateState]] = None,
                 worker: int = config.ARENA_WORKER,
                 seed: int = None):
        assert len(agents) == 4
        self._agents = agents  # Agent 0, Agent 1, Agent 2 und Agent 3
        self._max_episodes = max_episodes  # Maximale Anzahl zu spielende Partien
        self._verbose = verbose  # Spielverlauf ausführlich anzeigen
        self._early_stopping = early_stopping  # Wettkampf abbrechen, wenn die Gewinnquote erreicht wurde oder nicht mehr erreicht werden kann
        self._win_rate = win_rate  # gewünschte Gewinnquote WIN / (WIN + LOST); nur relevant, wenn early_stopping gesetzt ist
        self._init_pubs = pubs  # wenn gesetzt, werden diese öffentlichen Spielzustände zum Start einer neuen Epoche genommen
        self._init_privs = privs  # wenn gesetzt, werden diese privaten Spielzustände zum Start einer neuen Epoche genommen
        self._worker = worker  # wenn größer 1, werden die Episode in entsprechend vielen Prozessen parallel ausgeführt
        self._seed = seed  # Seed für den Zufallsgenerator
        self._stop_event = Manager().Event() if worker > 1 else asyncio.Event()
        #self._progbar = Progbar(max_episodes, stateful_metrics=["Wins", "Lost", "Draws"])
        # Statistik
        self._time_start = None  # Zeitstempel zu Beginn der ersten Partie.
        self._seconds: int = 0  # Spieldauer insgesamt in Sekunden
        self._episodes: int = 0  # Anzahl Episoden
        self._rounds: int = 0  # Rundenzähler über alle Episoden
        self._tricks: int = 0  # Stichzähler über alle Episoden
        self._rating = [0, 0, 0]  # Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)
        logger.info("Arena initialisiert.")

    def run(self) -> tuple:
        """ Führt den Wettkampf durch. """

        self._time_start = time()

        logger.info(f"Starte Arena mit {self._worker} Worker(n)...")

        #if not self._verbose:
        #    self._progbar.update(0, values=[("Wins", 0), ("Lost", 0), ("Draws", 0)])

        if self._worker > 1:
            pool = Pool(processes=self._worker)
            for episode in range(self._max_episodes):
                pool.apply_async(self._play_game, args=(episode,), callback=self._update)
            # processes = [pool.apply_async(self._play_game, args=(episode,)) for episode in range(max_episodes)]
            # for p in processes:
            #     self._update(p.get())
            pool.close()  # verhindert, dass weitere Aufgaben an den Pool gesendet werden
            pool.join()  # warten, bis die Worker-Prozesse beendet sind

        else:  # worker == 1
            for episode in range(self._max_episodes):
                self._update(self._play_game(episode))

        self._seconds = time() - self._time_start
        logger.info(f"Arena beendet nach {self._seconds:.2f} Sekunden.")

        if self._verbose:
            print("\r ")
        #else:
        #    if sum(self._rating) < self._max_episodes:
        #        self._progbar.update(sum(self._rating), finalize=True)  # es wurde früher beendet

        return tuple(self._rating)

    # Diese Methode läuft parallel im eigenen Prozess (im Multiprocessing-Mode)!
    def _play_game(self, episode: int) -> Optional[tuple]:
        if self._stop_event.is_set():
            return None

        # Wichtig: Jeder Prozess braucht seine eigene Event-Loop.
        pub = asyncio.run(_run_game(
            table_name=f"Game_{episode}",
            agents=self._agents,
            seed=self._seed,
            pub = self._init_pubs[episode] if self._init_pubs else None,
            privs = self._init_privs[episode] if self._init_privs else None,
        ))

        return episode, pub

    # Diese Methode läuft wieder im Hauptprozess!
    def _update(self, result):
        if not result:
            return

        episode: int
        pub: PublicState
        episode, pub = result

        self._seconds = time() - self._time_start
        self._episodes += 1
        self._rounds += pub.round_counter

        if pub.total_scores[0] > pub.total_scores[1]:
            self._rating[0] += 1
        elif pub.total_scores[0] < pub.total_scores[1]:
            self._rating[1] += 1
        else:
            self._rating[2] += 1

        if self._early_stopping:
            total = self._max_episodes - self._rating[2]  # Unentschieden fällt nicht in die Bewertung
            unplayed = self._max_episodes - sum(self._rating)
            if total > 0 and float(self._rating[0]) / total >= self._win_rate:
                self._stop_event.set()  # die gewünschte Gewinnquote ist sicher erreicht
            elif total > 0 and float(self._rating[0] + unplayed) / total < self._win_rate:
                self._stop_event.set()  # die gewünschte Gewinnquote kann nicht mehr erreicht werden

        if self._verbose:
            if self._episodes == 1:
                print("\nEpisode | Runden |    Score    |    Rating   ")
            print(f"\r{(episode + 1):7d}"
                  f" | {pub.round_counter:6d}"
                  f" | {pub.total_scores[0]:>5d}/{pub.total_scores[1]:<5d}"
                  f" | {self._rating[0]:>5d}/{self._rating[1]:<5d}")
            seconds_per_episode = self._seconds / self._episodes
            print(f"Restzeit ca. {(self._max_episodes - self._episodes) * seconds_per_episode:6.3f} s", end="")
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
    def episodes(self) -> int:
        """
        Anzahl Episoden
        """
        return self._episodes

    @property
    def rounds(self) -> int:
        """
        Anzahl Runden insgesamt über alle Episoden
        """
        return self._rounds

    @property
    def tricks(self) -> int:
        """
        Anzahl Stiche insgesamt über alle Episoden
        """
        return self._tricks

    @property
    def rating(self) -> list:
        """
        Kumulative Bewertung des Teams 20 (Anzahl Partien gewonnenen, verloren, unentschieden)
        """
        return self._rating
