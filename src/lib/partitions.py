__all__ = "Partition", \
    "build_partitions", "remove_partitions", \
    "filter_playable_partitions", "filter_playable_combinations", \
    "stringify_partition", \
    "partition_quality",

from typing import List, Tuple

import config
import math

from src.lib.cards import Cards
from src.lib.combinations import stringify_figure, remove_combinations, Combination

# todo Dokumentieren (reStructuredText)

# -----------------------------------------------------------------------------
# Partitionen
# -----------------------------------------------------------------------------

Partition = List[Tuple[Cards, Combination]]  # todo überall konsequent verwenden

# Berechnet die Partitionen, die mit den verfügbaren Kombinationen gebildet werden können.
#
# Da die offensichtlich guten Kombis zuerst aufgelistet sind, werden auch die offensichtlich besseren Partitionen zuerst gebildet.
#
# partitions: Diese Liste wird während der Berechnung gefüllt.
# combis: Die möglichen Kombinationen der Handkarten
# counter: Anzahl Handkarten
# maxlen: Maximale Anzahl Partitionen, die berechnet werden.
# curr: Die aktuell noch unvollständige Partition, für die passende Kombinationen gesucht werden.
# deep: Suchtiefe
# Rückgabe: True, wenn alle möglichen Partitionen berechnet wurden. False, wenn es mehr als partitions_max_len Partitionen gibt.
def build_partitions(partitions: list[list[tuple]], combis: list[tuple], counter: int, maxlen=config.PARTITIONS_MAXLEN, curr: list = None, deep=0) -> bool:
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


# Entfernt Karten aus den Partitionen

# partitions: Partitionen
# cards: Karten, die entfernt werden sollen
# return: Neue Liste der Partitionen
def remove_partitions(partitions: List[Partition], cards: Cards) -> List[Partition]:
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
                skip = True  # die gesamte Partition wird verworfen, weil die Kombi auseinander gerissen ist
                break
        if not skip and new_partition and new_partition not in new_partitions:
            new_partitions.append(new_partition)
    return new_partitions


# Ermittelt Partitionen, die mindestens eine spielbare Kombination haben
def filter_playable_partitions(partitions: list[list[tuple]], action_space: list[tuple]) -> list[list[tuple]]:
    new_partitions = []
    for partition in partitions:
        for combi in partition:
            if combi in action_space:
                new_partitions.append(partition)
                break
    return new_partitions


# Ermittelt die spielbaren Kartenkombinationen
def filter_playable_combinations(partition: list[tuple], action_space: list[tuple]) -> list[tuple]:
    combis = []
    for combi in partition:
        if combi in action_space:
            combis.append(combi)
    return combis


# Wandelt die Partition in ein Label um
def stringify_partition(partition: list[tuple]) -> str:
    return " ".join([stringify_figure(combi[1]) for combi in partition])


# Schätzt die Güte der gegebener Partition
#
# Die Güte ist ein Maß für die Qualität der Partition. Je häufiger wir das Anspielrecht erhalten, desto größer ist
# der Wert. Je häufiger wir das Anspielrecht verlieren, desto kleiner ist der Wert. Kombinationen, mir der wir
# statistisch gesehen weder das Anspielrecht gewinnen noch verlieren, beeinflussen die Güte nicht.
# Ein Wert von -1 bedeutet, dass man immer verliert (der Letzte ist).
# Ein Wert von 1 würde heißen, dass man immer gewinnt (als erstes fertig wird).
# Der Wert 0 heißt, dass man im Durchschnitt genauso häufig verliert wie man gewinnt.
#
# partition: Partition
# action_space: spielbare Aktionen (leer, wenn die Partition jetzt nicht gespielt werden darf)
# statistic: Ergebnis von combinations.calc_statistic()
# return: Güte im Wertebereich [-1, 1]
def partition_quality(partition: list[tuple], action_space: list[tuple], statistic: dict) -> float:

    # !!!!!!!!!!!!!!!!!! Neue Beschreibung  !!!!!!!!!!!!!!!!!!!
    #
    # p_lo: Wahrscheinlichkeit, dass ein Mitspieler die Kombination (mit niederem Rang) anspielen kann (Bespielbarkeit)
    # p_hi: Wahrscheinlichkeit, dass ein Mitspieler die Kombination überstechen kann
    # p_pw = 1 - p_hi  # Wahrscheinlichkeit, mit der Kombination das Anspielrecht zu erhalten (Schlagkraft)
    # q_combi = p_lo * p_pw  # Güte der Kombinationen = Bespielbarkeit * Schlagkraft
    #
    # Für die Kombinationen, die jetzt ausgespielt werden kann und soll, ist p_lo = 1 (sie ist definitiv bespielbar).
    # q_first_combi = p_pw
    #
    # Für die letzte Kombination ist p_hi = 0 (kann nicht überstochen werden) und somit p_pw = 1
    # q_last_combi = p_lo
    #
    # Die Güte der Hand ist die Summe aller Kombinationen, wobei die erste und letzte Kombinationen so gewählt sind, dass der Wert maximiert wird.
    # q_hand = q_first_combi + sum(q_middle_combi) + q_last_combi

    assert partition
    total_lo = total_hi = 0.
    lo_playing_now = math.inf
    hi_last_combi = -math.inf
    n_lo = n_hi = len(partition)
    assert n_lo > 0
    for combi in partition:
        assert tuple(combi[0]) in statistic, ("Fehler in der Statistik", combi[0], statistic)
        lo_opp, lo_par, hi_opp, hi_par, eq_opp, eq_par = statistic[tuple(combi[0])]
        lo = lo_opp + lo_par
        hi = hi_opp + hi_par
        total_lo += lo
        total_hi += hi
        if lo_playing_now > lo and combi in action_space:
            lo_playing_now = lo
        #     if n_hi == 1:
        #         hi_last_combi = hi
        # elif hi_last_combi < hi:
        if hi_last_combi < hi:
            hi_last_combi = hi

    # Falls wir dran sind, kann der kleinste Lo-Wert wieder abgezogen werden, da wir mit dieser Kombi jetzt spielen.
    if lo_playing_now < math.inf:
        total_lo -= lo_playing_now
        n_lo -= 1

    # Bei der letzten Kombination, die wir ausspielen werden, ist es egal, ob die Kombination durch den Mitspieler
    # überstochen werden kann. Wir können also den höchsten Hi-Wert auf 0 setzen und somit ignorieren.
    assert hi_last_combi > -math.inf
    total_hi -= hi_last_combi
    n_hi -= 1

    # normalisieren
    # Randbedingungen:
    # - Falls n_lo gleich 0 ist, ist n_hi auch 0, denn wir sind wir dran und spielen die letzte Kombi. q ist in diesem Fall 1.
    # - Falls nur n_hi gleich 0 ist, haben wir nur noch ein Kombi, sind aber nicht dran. Dann ist nur der lo-Anteil relevant.
    q = ((total_lo / n_lo) if n_lo else 1) - ((total_hi / n_hi) if n_hi else 0)
    return q
