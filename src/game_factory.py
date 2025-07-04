"""
Definiert die GameFactory-Klasse, die für die Verwaltung aller GameEngine-Instanzen zuständig ist.
"""

import asyncio
from src.common.logger import logger
from src.game_engine import GameEngine
from typing import Dict, Optional

class GameFactory:
    """
    Verwaltet die Erstellung, den Zugriff und die Bereinigung von GameEngine-Instanzen.
    """

    def __init__(self):
        """
        Initialisiert die GameFactory.
        """
        # Game-Engines
        self._engines: Dict[str, GameEngine] = {}

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser Instanz.

        Ruft die `cleanup`-Funktion aller GameEngine-Instanzen auf.
        """
        if self._engines:
            logger.info(f"[Factory] Bereinige {len(self._engines)} aktive Game-Engines...")
            # alle GameEngine-Instanzen bereinigen (parallel)
            await asyncio.gather(*[asyncio.create_task(e.cleanup()) for e in self._engines.values()], return_exceptions=True)
            self._engines.clear()
            logger.info(f"[Factory] Bereinigung der Game-Engines beendet.")

    def get_or_create_engine(self, table_name: str) -> GameEngine:
        """
        Gibt die GameEngine-Instanz für einen gegebenen Tischnamen zurück.

        Erstellt eine neue Engine, falls der Tisch noch nicht existiert.

        :param table_name: Der Name des Tisches.
        :return: Die GameEngine-Instanz für diesen Tisch.
        :raises ValueError: Wenn Parameter nicht ok sind.
        """
        if table_name not in self._engines:
            #logger.debug(f"[Factory] Erstelle Engine '{table_name}'")
            self._engines[table_name] = GameEngine(table_name)
        return self._engines[table_name]

    async def remove_engine(self, table_name: str):
        """
        Entfernt eine GameEngine-Instanz aus der Verwaltung.

        :param table_name: Der Name des zu entfernenden Tisches.
        """
        if table_name in self._engines:
            #logger.debug(f"[Factory] Entferne Engine '{table_name}'")
            game_engine = self._engines.pop(table_name)  # entfernt den Eintrag aus dem Dictionary
            try:
                await game_engine.cleanup()
            except Exception as e:
                logger.exception(f"[Factory] Unerwarteter Fehler. Tisch '{table_name}' konnte nicht aufgeräumt werden: {e}")
        else:
            logger.warning(f"[Factory] Tisch nicht gefunden. Tisch '{table_name}' konnte nicht entfernt werden.")

    def get_engine_by_session(self, session: str) -> Optional[GameEngine]:
        """
        Gibt die GameEngine-Instanz zurück, die den Spieler mit der gegebenen Session verwaltet.
        :param session: Die Session des Spielers.
        :return: Die GameEngine-Instanz, falls die Session existiert, sonst None.
        """
        for engine in self._engines.values():
            for p in engine.players:
                if p.session_id == session:
                    return engine
        return None
