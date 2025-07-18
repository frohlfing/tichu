![Coverage](docs/assets/coverage.svg)
![Version](https://img.shields.io/github/v/tag/frohlfing/tichu)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/github/license/frohlfing/tichu)
<!--
![Version](https://img.shields.io/badge/version-0.3.0-blue)
![Version](https://img.shields.io/github/v/release/frohlfing/tichu)
-->

# Tichu KI-Projekt

Willkommen zum Tichu KI-Projekt! Dies ist eine Python-Implementierung des Kartenspiels Tichu, die darauf ausgelegt ist, sowohl schnelle Simulationen zwischen KI-Agenten zu ermöglichen als auch eine Plattform für menschliche Spieler zu bieten, um online gegen KIs oder andere Menschen zu spielen.

## Über Tichu

Tichu ist ein Kartenspiel, das ursprünglich aus China stammt und Ähnlichkeiten mit Spielen wie Bridge, Poker und Big Two aufweist. Ziel ist es, als erster Spieler seine Karten loszuwerden und durch geschicktes Ausspielen von Kombinationen Punkte für das eigene Team zu sammeln. Besondere Karten wie Drache, Phönix, Hund und Mah Jong bringen zusätzliche strategische Tiefe ins Spiel.

[Detaillierte Regeln (Deutsch)](https://cardgames.wiki/de/blog/tichu-spielen-regeln-und-anleitung-einfach-erklaert)

## Projektziele

*   **KI-Arena:** Eine Umgebung, in der verschiedene KI-Agenten in hoher Geschwindigkeit gegeneinander antreten können, um Strategien zu testen, zu bewerten und Spieldaten für maschinelles Lernen zu generieren.
*   **Live-Betrieb (in Entwicklung):** Ein WebSocket-basierter Server, der es menschlichen Spielern ermöglicht, über einen Web-Client am Spiel teilzunehmen – entweder gegeneinander oder mit/gegen KI-Agenten.
*   **Entwicklung fortgeschrittener KI-Agenten:** Von einfachen regelbasierten Agenten bis hin zu komplexen, auf neuronalen Netzen basierenden Agenten (z.B. durch Behavior Cloning oder Reinforcement Learning).

## Aktueller Status

*   **Kern-Spiellogik:** Weitgehend implementiert und durch Unit-Tests abgedeckt.
*   **Arena-Modus:** Funktional und wird für die Entwicklung und das Testen von Agenten verwendet. Kann Spiele parallel ausführen.
*   **Agenten:**
    *   `RandomAgent`: Implementiert (spielt zufällige, gültige Züge).
    *   Weitere Agenten (heuristisch, neuronal) sind geplant.
*   **Server-Modus (Live-Spiel):** Weitgehend implementiert.
*   **Frontend:** Weitgehend implementiert.

## Systemanforderungen

*   **Entwicklung:** Getestet auf Windows 11.
*   **Zielplattform (Server):** Raspberry Pi 5 (Bookworm OS).

## Technische Dokumentation

Eine detailliertere technische Dokumentation zur Architektur, den Modulen und dem Spielablauf befindet sich in [Technische_Dokumentation.md](docs/Technische_Dokumentation.md).

## Quellen

- Regeln: https://abacusspiele.de/wp-content/uploads/2021/01/Tichu_Pocket_Regel.pdf

## Lizenz

Dieses Projekt steht unter der [GPL-3.0-Lizenz](LICENSE).

Die verwendeten Kartenmotive und das Spielprinzip von Tichu sind Eigentum von [Fata Morgana Spiele, Bern](https://www.fatamorgana.ch).
