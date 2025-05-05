# -*- coding: utf-8 -*-
"""
Definiert die Datenstruktur für den privaten Spielzustand (Private State) eines Spielers.

Diese Klasse enthält alle Informationen über das Spiel, die nur für einen
spezifischen Spieler sichtbar sind (insbesondere dessen Handkarten).
Sie dient als reiner Datencontainer; die Logik zur Änderung des Zustands
befindet sich in der GameEngine oder ausgelagerten Regelfunktionen.
"""

from dataclasses import dataclass, field
from src.lib.cards import Card, stringify_cards
from typing import List, Dict, Any


@dataclass
class PrivateState:
    """
    Datencontainer für den privaten Zustand eines Tichu-Spielers.

    Diese Klasse sammelt die Datenpunkte, die nur dem jeweiligen Spieler bekannt sind.

    :ivar player_index: Der Index dieses Spielers am Tisch (0-3).
    :ivar hand_cards: Die aktuellen Handkarten des Spielers. Wird sortiert gehalten.
    :ivar received_schupf_cards: Die drei Karten, die der Spieler von anderen beim Schupfen erhalten hat.
    :ivar given_schupf_cards: Die drei Karten, die dieser Spieler zum Schupfen abgegeben hat.
    :ivar can_announce_tichu: Gibt an, ob der Spieler aktuell Tichu ansagen dürfte (z.B. vor dem ersten Zug).
    :ivar can_bomb: Gibt an, ob der Spieler aktuell eine Bombe werfen kann und darf.
    """
    # --- Spielerinformationen ---
    player_index: int = -1  # Index des Spielers (0-3).

    # --- Handkarten ---
    hand_cards: List[Card] = field(default_factory=list)  # Die Handkarten [(Wert, Farbe), ...], sortiert.

    # --- Schupfen ---
    received_schupf_cards: List[Card] = field(default_factory=list) # Die 3 Karten, die man beim Schupfen erhalten hat.
    given_schupf_cards: List[Card] = field(default_factory=list) # Die 3 Karten, die man beim Schupfen abgegeben hat.

    # --- Status-Flags ---
    can_announce_tichu: bool = False  # Darf der Spieler aktuell (kleines) Tichu ansagen?
    can_bomb: bool = True  # Kann und darf der Spieler aktuell eine Bombe werfen?


    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Zustand in ein Dictionary für JSON-Serialisierung.

        Verwendet eine übergebene Funktion zur Konvertierung interner Karten in ihre String-Label-Repräsentation.

        :return: Eine Dictionary-Repräsentation des Zustands mit Karten als Strings.
        """
        # Konvertiere interne Kartenlisten in String-Labels für die Ausgabe.
        hand_card_labels = stringify_cards(self.hand_cards)
        received_schupf_card_labels = stringify_cards(self.received_schupf_cards)
        given_schupf_card_labels = stringify_cards(self.given_schupf_cards)

        return {
            "playerIndex": self.player_index,
            "handCards": hand_card_labels,
            "receivedSchupfCards": received_schupf_card_labels,
            "givenSchupfCards": given_schupf_card_labels,
            "canAnnounceTichu": self.can_announce_tichu,
            "canBomb": self.can_bomb,
            # Weitere private Infos könnten hierhin, z.B. Infos über bekannte Karten anderer Spieler?
        }

# --- Nicht übernommene Felder/Konzepte aus altem PrivateState ---
# _schupfed (abgegebene Karten): Diese Information ist nach dem Abgeben für den Spieler selbst
#                                 nicht mehr direkt relevant (er hat sie ja nicht mehr).
#                                 Die Engine verwaltet den Schupf-Vorgang.
# _combination_cache: Berechnung von Kombinationen ist Aufgabe der Engine oder einer Hilfsfunktion,
#                     nicht Teil des reinen Zustands.
# _partition_cache: Siehe _combination_cache.
# _partitions_aborted: Zustand der Cache-Berechnung, gehört nicht zum reinen Spielerzustand.
# has_mahjong (Property): Kann leicht aus `hand_cards_internal` abgeleitet werden, wenn benötigt.