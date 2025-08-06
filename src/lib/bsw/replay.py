"""
Replay-Simulator für die Brettspielwelt-Datenbank
"""

__all__ =  "replay_play"

from src.lib.bsw.parse import BSWLogEntry
from src.lib.cards import Cards, CardSuit
from src.lib.combinations import Combination, CombinationType
from src.public_state import PublicState
from src.private_state import PrivateState
from typing import List, Tuple, Generator


def replay_play(all_round_data: List[BSWLogEntry]) -> Generator[Tuple[PublicState, List[PrivateState], Tuple[Cards, Combination]]]:
    """
    Spielt eine auf der Brettspielwelt gespielte Partie nach und gibt jeden Entscheidungspunkt für das Ausspielen der Karten zurück.

    :param all_round_data: Die geparsten Daten einer geloggten Partie.
    :return: Ein Generator, der den öffentlichen Spielzustand, die 4 privaten Spielzustände und die ausgeführte Aktion liefert.
    """
    if len(all_round_data) == 0:
        return None

    # aktueller Spielzustand
    pub = PublicState(
        table_name="BW Replay",
        player_names=["A", "B", "C", "D"],
    )
    privs = [PrivateState(player_index=i) for i in range(4)]
    action = [(1, CardSuit.SPECIAL)], (CombinationType.SINGLE, 1, 1)
    yield pub, privs, action
    return None
