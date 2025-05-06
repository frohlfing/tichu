import config
from src.arena2 import Arena
from src.players.agent import Agent
from src.players.random_agent import RandomAgent


# -------------------------------------------------------------------
# Spiel eröffnen
# -------------------------------------------------------------------

def run_battle(agents: list[Agent], max_episodes=10, verbose=False):
    # Agenten gegeneinander antreten lassen.
    # max_episodes: Maximale Anzahl Episoden (Partien), die gespielt werden sollen.
    # verbose: Spielverlauf ausführlich anzeigen
    # Falls config.ARENA_WORKER > 1 ist, werden die Episode in entsprechend vielen Prozessen parallel ausgeführt.

    print(f"Team 20: {agents[2].name} + {agents[0].name}")
    print(f"Team 31: {agents[3].name} + {agents[1].name}")
    print(f"Verfügbare CPU-Kerne: {Arena.cpu_count()}")
    print(f"Eingesetzte Worker: {config.ARENA_WORKER}")
    print(f"Maximale Anzahl zu spielende Episoden: {max_episodes}")
    print("Los gehts...")
    #logger.debug('Los gehts')

    # Wettkampf durchführen
    arena = Arena(agents=agents, max_episodes=max_episodes, verbose=verbose)
    arena.run()

    # Ergebnis auswerten
    print(f"Anzahl Episoden: {arena.episodes}")
    print(f"Anzahl Runden: {arena.rounds}")
    print(f"Gesamtzeit: {arena.seconds:5.3f} s")
    print(f"Zeit/Episode: {arena.seconds / arena.episodes:5.3f} s")
    print(f"Zeit/Runde: {arena.seconds * 1000 / arena.rounds:5.3f} ms")
    print(f"Runden/Episode: {arena.rounds / arena.episodes:2.1f}")
    print(f"Stiche/Runde: {arena.tricks / arena.rounds:2.1f}")
    print("\nBewertung")
    wins, lost, draws = arena.rating
    print(f"Team 20 gewonnen: {wins:>5d} - {wins * 100 / arena.episodes:4.1f} %")
    print(f"Team 31 gewonnen: {lost:>5d} - {lost * 100 / arena.episodes:4.1f} %")
    print(f"Unentschieden:    {draws:>5d} - {draws * 100 / arena.episodes:4.1f} %")


if __name__ == "__main__":
    run_battle([
        RandomAgent(),
        RandomAgent(),
        RandomAgent(),
        RandomAgent(),
    ], 100, verbose=True)

# Interpreter-Options, um Asserts zu ignorieren:
# -O
