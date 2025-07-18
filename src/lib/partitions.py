"""
Dieses Modul definiert Funktionen zur Erstellung und Verwaltung einer Kartenpartition.
"""

__all__ = "Partition", \
    "build_partitions", "remove_partitions", \
    "filter_playable_partitions", "filter_playable_combinations", \
    "stringify_partition",

from src import config
from src.lib.cards import Cards
from src.lib.combinations import stringify_combination, remove_combinations, Combination
from typing import List, Tuple, Optional

# -----------------------------------------------------------------------------
# Partitionen
# -----------------------------------------------------------------------------

Partition = List[Tuple[Cards, Combination]]
"""
Type-Alias für eine Partition

Typ Partition ist technisch gleich Typ Combinations, aber in der Partition kommt keine Karte mehrfach vor.
"""

def build_partitions(partitions: List[Partition], combis: List[Tuple[Cards, Combination]], counter: int, maxlen=config.PARTITIONS_MAXLEN, curr: Optional[Partition] = None, deep=0) -> bool:
    """
    Berechnet die Partitionen, die mit den verfügbaren Kombinationen gebildet werden können.

    Da die offensichtlich guten Kombis zuerst aufgelistet sind, werden auch die offensichtlich besseren Partitionen zuerst gebildet.

    :param partitions: Diese Liste wird während der Berechnung gefüllt.
    :param combis: Die möglichen Kombinationen der Handkarten (sortiert, die besten zuerst!).
    :param counter: Anzahl Handkarten.
    :param maxlen: Die maximale Anzahl von Partitionen, die berechnet werden.
    :param curr: Die aktuell noch unvollständige Partition, für die passende Kombinationen gesucht werden.
    :param deep: Die Suchtiefe.
    :return: True, wenn alle möglichen Partitionen berechnet wurden. False, wenn es mehr als partitions_max_len Partitionen gibt.
    """
    if len(partitions) == maxlen:
        return False  # es gibt zu viele Möglichkeiten, wir brechen ab

    # Sobald alle Karten in der aktuellen Partition enthalten sind, können wir die Partition in unserer Liste
    # ablegen und wieder aus der rekursiven Suche eine Ebene zurückspringen.
    assert counter >= 0
    if counter == 0:
        assert curr
        partitions.append(curr)
        return True

    # Wir suchen rekursiv weiter...
    if curr is None:
        curr = []
    completed = True
    for combi in combis:
        cards, (t, n, v) = combi
        rest_combis = remove_combinations(combis[combis.index(combi) + 1:], cards)
        if not build_partitions(partitions, combis=rest_combis, maxlen=maxlen, counter=counter - n, curr=curr + [combi], deep=deep + 1):
            completed = False
    return completed


def remove_partitions(partitions: List[Partition], cards: Cards) -> List[Partition]:
    """
    Entfernt Karten aus den Partitionen.

    :param partitions: Die Partitionen.
    :param cards: Karten, die entfernt werden sollen.
    :return: Die neue Liste der Partitionen.
    """
    new_partitions = []
    for partition in partitions:
        new_partition = []
        skip = False
        for combi in partition:
            found = set(cards).intersection(combi[0])
            if not found:
                new_partition.append(combi)  # die Kombination ist nicht betroffen
            elif list(found) == combi[0]:
                pass  # die Kombination wird nicht übernommen, da alle Karten der Kombination betroffen sind
            else:
                skip = True  # die gesamte Partition wird verworfen, weil die Kombi auseinandergerissen ist
                break
        if not skip and new_partition and new_partition not in new_partitions:
            new_partitions.append(new_partition)
    return new_partitions


def filter_playable_partitions(partitions: List[Partition], action_space: List[Tuple[Cards, Combination]]) -> List[Partition]:
    """
    Ermittelt Partitionen, die mindestens eine spielbare Kombination haben.

    :param partitions: Die Partitionen.
    :param action_space: Die spielbaren Kombinationen.
    :return: Die Partitionen mit mindestens einer spielbaren Kombination.
    """
    new_partitions = []
    for partition in partitions:
        for combi in partition:
            if combi in action_space:
                new_partitions.append(partition)
                break
    return new_partitions


def filter_playable_combinations(partition: Partition, action_space: List[Tuple[Cards, Combination]]) -> List[Tuple[Cards, Combination]]:
    """
    Ermittelt die spielbaren Kartenkombinationen einer gegebenen Partition.

    :param partition: Die Partition.
    :param action_space: Alle spielbaren Kombinationen der Handkarten.
    :return: Die spielbaren Kombinationen der Partition.
    """
    combis = []
    for combi in partition:
        if combi in action_space:
            combis.append(combi)
    return combis


def stringify_partition(partition: Partition) -> str:
    """
    # Wandelt die Partition in ein Label um.

    :param partition: Die Partition.
    :return: Das Label der Partition.
    """
    return " ".join([stringify_combination(combi[1]) for combi in partition])
