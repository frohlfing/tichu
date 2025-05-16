import config
from src.arena import Arena
from src.game_engine import GameEngine
from src.game_factory import GameFactory
from src.player.random_agent import RandomAgent


def play(engine: GameEngine, games=10, verbose=False):
    # Lässt Agenten gegeneinander spielen (im Synchronmodus; ohne Nachrichtenschleife)

    print('Los gehts...')
    # logger.debug('Los gehts')

    # Wettkampf durchführen
    arena = Arena(engine, games, verbose)
    arena.play()

    # Ergebnis auswerten
    wins, lost, draws = arena.rating
    print(f'Anzahl Episoden: {arena.episodes}')
    print(f'Anzahl Runden: {arena.rounds}')
    print(f'Ranking Team 20: {wins} - {wins * 100 / games:4.1f} %')
    print(f'Ranking Team 31: {lost} - {lost * 100 / games:4.1f} %')
    print(f'Unentschieden: {draws} - {draws * 100 / games:4.1f} %')
    print(f'Gesamtzeit: {arena.seconds:5.3f} s')
    print(f'Zeit/Episode: {arena.seconds / arena.episodes:5.3f} s')
    print(f'Zeit/Runde: {arena.seconds * 1000 / arena.rounds:5.3f} ms')
    print(f'Runden/Episode: {arena.rounds / arena.episodes:2.1f}')
    print(f'Runden/Episode: {arena.rounds / arena.episodes:2.1f}')
    print(f'Stiche/Runde: {arena.tricks / arena.rounds:2.1f}')


if __name__ == "__main__":
    factory = GameFactory()
    game_engine = factory.get_or_create_engine("Arena", [
        RandomAgent,
        RandomAgent,
        RandomAgent,
        RandomAgent
    ])
    play(game_engine, 10, verbose=True)

# Interpreter-Options, um Asserts zu ignorieren:
# -O
