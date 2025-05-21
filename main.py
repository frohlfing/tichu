#!/usr/bin/env python

"""
Dieses Modul öffnet eine Arena und lässt Agenten gegeneinander spielen.

**Start des Wettkampfes**:
   ```
   python main.py
   ```
"""

import argparse
import config
config.LOG_LEVEL = "WARNING"

from src.common.git_utils import get_release
from src.arena import Arena
from src.players.heuristic_agent import HeuristicAgent
from src.players.random_agent import RandomAgent

# Verfügbare Agenten
agent_classes = {
    "HeuristicAgent": HeuristicAgent,
    "RandomAgent": RandomAgent,
}

def create_agent(class_name):
    """
    Erzeugt anhand der Klasse eine Agent-Instanz.

    :param class_name: Name der Klasse
    :return: Agent-Instanz
    """
    if class_name in agent_classes:
        cls = agent_classes[class_name]
    else:
        raise ValueError(f"'{class_name}' ist kein Agent.")
    return cls()


def main(args: argparse.Namespace):
    agents = [create_agent(class_name) for class_name in [args.agent1, args.agent2, args.agent3, args.agent4]]

    print(f"Team 20: {agents[2].name} + {agents[0].name}")
    print(f"Team 31: {agents[3].name} + {agents[1].name}")
    print(f"Verfügbare CPU-Kerne: {Arena.cpu_count()}")
    print(f"Eingesetzte Worker: {args.worker}")
    print(f"Maximale Anzahl zu spielende Partien: {args.max_games}")
    print("Los gehts...")
    #logger.debug('Los gehts')

    # Wettkampf durchführen
    arena = Arena(agents=agents, max_games=args.max_games, worker=args.worker, verbose=args.verbose)
    arena.run()

    # Ergebnis auswerten
    print(f"Anzahl Partien: {arena.games}")
    print(f"Anzahl Runden: {arena.rounds}")
    print(f"Gesamtzeit: {arena.seconds:5.3f} s")
    print(f"Zeit/Partie: {arena.seconds / arena.games:5.3f} s")
    print(f"Zeit/Runde: {arena.seconds * 1000 / arena.rounds:5.3f} ms")
    print(f"Runden/Partie: {arena.rounds / arena.games:2.1f}")
    print(f"Stiche/Runde: {arena.tricks / arena.rounds:2.1f}")
    print("\nBewertung")
    wins, lost, draws = arena.rating
    print(f"Team 20 gewonnen: {wins:>5d} - {wins * 100 / arena.games:4.1f} %")
    print(f"Team 31 gewonnen: {lost:>5d} - {lost * 100 / arena.games:4.1f} %")
    print(f"Unentschieden:    {draws:>5d} - {draws * 100 / arena.games:4.1f} %")


if __name__ == "__main__":
    print(f"Tichu Arena Version {get_release()}")

    # Argumente parsen (`nargs="?":` Dieses Argument für `add_argument` macht die Agenten-Argumente optional)
    parser = argparse.ArgumentParser(description=f"Lässt Agenten gegeneinander spielen. Verfügbare Agenten: {', '.join(agent_classes.keys())}.")
    parser.add_argument("agent1", nargs="?", default="RandomAgent", help="Agent 1 (Default: RandomAgent).")
    parser.add_argument("agent2", nargs="?", default="RandomAgent", help="Agent 2 (Default: RandomAgent).")
    parser.add_argument("agent3", nargs="?", default="RandomAgent", help="Agent 3 (Default: RandomAgent).")
    parser.add_argument("agent4", nargs="?", default="RandomAgent", help="Agent 4 (Default: RandomAgent).")
    parser.add_argument("-n", "--max-games", type=int, default=10, help=f"Maximale Anzahl der zu spielenden Partien (Default: {10}).")
    parser.add_argument("-w", "--worker", type=int, default=config.ARENA_WORKER, help=f"Wenn größer 1, werden die Partien in entsprechend vielen Prozessen parallel ausgeführt (Default: {config.ARENA_WORKER}).")
    parser.add_argument("-v", "--verbose", action="store_true", help=f"Spielverlauf ausführlich anzeigen.")

    # Main-Routine starten
    main(parser.parse_args())


# Interpreter-Options, um Asserts zu ignorieren:
# -O
