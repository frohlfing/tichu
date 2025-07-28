# Entwicklung eines NNetAgents

**Inhaltsverzeichnis**

**ANHANG**

## 1. Ziel

Das Ziel ist es, Agenten für das Tichu-Spiel zu entwickeln, die neuronale Netze verwenden. 

Die Basisklasse hierfür ist `NNetAgent` (für "Neural Network Agent"). Folgende Entscheidungen muss der Agent treffen:

| Action                  | Beschreibung                                                             |
|-------------------------|--------------------------------------------------------------------------|
| "announce"              | Ein Tichu (großes oder einfaches) oder kein Tichu ansagen.               |
| "schupf"                | Für jeden der 3 Mitspieler je eine Karte (aus 56 möglichen) auszuwählen. |
| "play"                  | bis zu 14 Karten (aus 56 möglichen) ausspielen oder passen.              |
| "wish"                  | Einen Kartenwert zw. 2 und 14 wünschen.                                  |
| "give_dragon_away"      | Den Drachen an den rechten oder an den linken Gegner verschenken.        |

Wir konzentrieren uns zunächst auf "play".

## 2. Geplante Trainingsstufen, Netze und Agenten

Basisklasse: 

**`NetAgent`**: Überbegriff für Agenten, die neuronale Netze verwenden. Lernt die Spielstrategie durch Trainingsdaten.

### 2.1 Supervised Learning (SL) 

In der ersten Phase der Entwicklung werden wir einem neuronalen Netz mit Supervised Learning (SL) beibringen, menschliches Verhalten zu imitieren. 

Dazu nutzen wir einen riesigen Datensatz des Spiele-Portals "Brettspielwelt", um das Netz zu trainieren und zu validieren.

**Vorteil:**
*   Perfekter Einstieg. Es ist ein Standardproblem des überwachten Lernens.

**Nachteil:** 
*   Die KI kann nie fundamental besser als die Spieler in den Daten werden. Sie lernt nur, sie zu kopieren, inklusive ihrer Fehler.

#### 2.1.1 Policy Network (PN)

Wir beginnen mit einem einfachen Multi-Layer Perceptron (MLP).
Dieses Netz nennen wir im Python-Code `PolicyNet`, weil es eine Strategie lernt, die beste Aktion auszuwählen. 
Den Agenten nennen wir entsprechend `PolicyAgent`. 

Nach dem Training vergleichen wir die Leistung mit dem `RandomAgent` und dem `HeuristikAgent`.

So sammeln wir erste Erkenntnisse und Erfahrungen.

#### 2.1.2 Goal-Conditioned Policy Network (GCPN) und Value Network (VN)

Unser `PolicyNet` ist für dei Beantwortung dieser Frage trainiert:
"Welche Aktion wird ein Mensch wohl bei diesem Spielzustand wählen?"

Es würde enorm helfen, wenn das Netz wissen würde, wie viele Punkte noch zusätzlich bis zum Ende der Runde erzielt werden. 
Beispiel: "Es werden ab jetzt noch 80 Punkte dazuverdient, das kann ich nur erreichen, wenn ich ein Tichu ansage."

Dieser Wert nennt sich **Return-to-Go (RTG)**. Wir fügen ihn als weiteres Feature zum Input hinzu.  

Das MLP, welches RTG als Feature nutzt, kann eine zielorientierte Frage beantworten:
"Welche Aktion wird ein Mensch wohl bei diesem Spielzustand wählen, damit er am Ende der Runde mit X Punktedifferenz gewinnt?"
Dieses Netz nennen wir im Python-Code `GCPolicyNet`, weil es eine Strategie lernt, die das Ziel berücksichtigt.

Problem: Bei der Inferenz (eine Vorhersage im echten Spiel treffen) kennen wir das Endergebnis und somit den RTG noch nicht!
Lösung: Wir trainieren ein weiteres Netz, das das Endergebnis vorhersagt. Es beantwortet die Frage: 
"Wie gut ist dieser Spielzustand?" Dieses Netz nennen wir `ValueNet`. Es lernt, die "Güte" vorherzusagen. 
Die Güte ist die Punkte-Differenz der beiden Teams am Ende der Runde.

Der Agent, der `GCPolicyNet` (inkl. `ValueNet`) einsetzt, nennen wir `GCPolicyAgent`.

#### 2.1.3 Decision Transformer (DT)

Ein Transformer ist eine weiterentwickelte Version des GCPN, die nicht nur den aktuellen Zustand, sondern die gesamte 
bisherige Spielsequenz (Liste der Zustände) berücksichtigt.

Der Input für den DT wäre nicht ein einzelner Vektor, sondern eine Sequenz von Vektoren:

Input-Sequenz: [(RTG_0, Zustand_1, Aktion_1), (RTG_1, Zustand_2, Aktion_2), ..., (RTG_(T-1), Zustand_T, Aktion_T)]
   *   **Return-to-Go (RTG_(t-1):** Ein Skalar für jeden Zeitschritt, der angibt: "Wie viele Punkte wurden ab diesem Zug bis zum Ende der Runde noch erzielt?". RTG_t = Score_t + Score_{t+1} + ... + Score_{Ende}.
   *   **Zustand_t:** Dies wäre exakt der Feature-Vektor (375 Features), den wir gerade entworfen haben, für den Zeitpunkt t.
   *   **Aktion_t:** Dies wäre der Label-Vektor (57 Features), der beschreibt, welche Aktion zum Zeitpunkt t ausgeführt wurde.

Was ändert sich?
1.  **Datenaufbereitung:** Anstatt einzelne (Zustand, Aktion)-Paare zu speichern, müssten wir ganze **Runden-Trajektorien** speichern: eine Liste von (Zustand, Aktion, Return-to-Go)-Tupeln für jede Runde. Deine BWRoundData ist dafür perfekt. Wir müssten nur den replay_round-Simulator so anpassen, dass er diese Trajektorien erzeugt.
2.  **Modellarchitektur:** Wir würden den MLP durch eine Transformer-Architektur ersetzen.

Das Netz nennen wir im Python-Code `DTNet`, den Agenten `DTAgent`.

#### 2.1.4 Monte-Carlo Tree Search (MCTS) mit Upper Confidence Bound for Trees (UCB):

Hier führen wir eine tiefe Suche durch, bevor ein Zug gemacht wird.

Das beste Policy-Netz (`PolicyNet`, `GCPolicyNet` oder `DTNet`) leitet die Suche an ("welche Züge sehen vielversprechend aus?"), 
und das Value-Netz (`ValueNet`) bewertet die Endpunkte der simulierten Pfade ("wie gut ist diese Position?").

Den Agenten nennen wir `MCTSAgent`. 

BehaviorAgent

## 2.2 Reinforcement Learning (RL)

In der zweiten Phase lassen wir das beste im vorherigen Schritt trainierte Netz Millionen von Partien gegen sich selbst spielen. 
Das Netz lernt durch Versuch und Irrtum, welche Züge zu Siegen führen.

Theoretisch könnte man auch mit einem untrainierten Netz beginnen. Das würde aber eine enorme Menge an Rechenleistung und Zeit benötigen, um auf ein hohes Niveau zu kommen.

**Vorteil:** 
*   Kann Strategien entdecken, die Menschen nie in Betracht gezogen haben.
   
**Nachteile:** 
*   Die Implementierung ist ungleich schwieriger als bei SL. 
*   Sehr Rechenintensiv.
*   Der Trainingsprozess kann leicht in suboptimalen Strategien stecken bleiben.

Die durch RL trainieren Netze erhalten die Kennung `RL`, also `PolicyRLNet`, `GCPolicyRLNet`, `DTRLNet`.

Die Agenten nennen wir entsprechend `PolicyRLAgent`, `GCPolicyRLAgent`, `DTRLAgent`, `MCTSRLAgent`.

## 3. Feature Engineering 

Wie repräsentieren wir den Input (Zustand -> Feature-Vektor)?

### 3.1 Feature-Vektor für PolicyNet und ValueNet

Der von einem Spieler beobachtbare Spielzustand setzt sich aus dem öffentlichen Spielzustand (`PublicState`) und dem privaten Spielzustand (`PrivateState`) zusammen.

Daraus bilden wir den Feature-Vektor (Input für das NN).

| Variable                | Typ                                                    | Beschreibung                                                                                                                                     | Default-Wert      | Klasse         | Features (Input für das NN)                                                                                                                                                                          | Anmerkung zum Feature-Vektor                                                                                                                           |
|-------------------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `table_name`            | `str`                                                  | Der eindeutige Name des Tisches.                                                                                                                 | (Pflichtargument) | `PublicState`  | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `player_names`          | `[str, str, str, str]`                                 | Die Namen der 4 Spieler.                                                                                                                         | (Pflichtargument) | `PublicState`  | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `host_index`            | `int`                                                  | Index des Clients, der Host des Tisches ist (-1 == kein Client am Tisch).                                                                        | `-1`              | `PublicState`  | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `is_running`            | `bool`                                                 | Gibt an, ob eine Partie gerade läuft.                                                                                                            | `False`           | `PublicState`  | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `current_turn_index`    | `int`                                                  | Index des Spielers, der am Zug ist (-1 = Startspieler steht noch nicht fest).                                                                    | `-1`              | `PublicState`  | 5 Features: One-Hot-Vektor der Länge 5 (Labels: "steht noch nicht fest", ich", "rechter Gegner", "Partner", "linker Gegner") (relative Anordnung!)                                                   |                                                                                                                                                        |
| `start_player_index`    | `int`                                                  | Index des Spielers, der den Mahjong hat oder hatte (-1 == steht noch nicht fest; es wurde noch nicht geschupft).                                 | `-1`              | `PublicState`  | 5 Features: One-Hot-Vektor der Länge 5 (Labels: "steht noch nicht fest", "ich", "rechter Gegner", "Partner", "linker Gegner") (relative Anordnung!)                                                  |                                                                                                                                                        |
| `count_hand_cards`      | `[int, int, int, int]`                                 | Anzahl der Handkarten pro Spieler.                                                                                                               | `[0, 0, 0, 0]`    | `PublicState`  | 56 Features (4 * 14): Für sich selbst, rechten Gegner, Partner, linken Gegner jeweils ein "Thermometer"-kodierter Vektor der Länge 14.                                                               | Alternativ die eigene Kartenanzahl hinzufügen (14 Features). Steckt zwar implizit in `hand_cards`, könnte aber explizit nützlich sein.                 |
| `played_cards`          | `Cards` = `List[Card]`                                 | Bereits gespielte Karten in der aktuellen Runde.                                                                                                 | `[]`              | `PublicState`  | 56 Features: Multi-Hot-Vektor der Länge 56. 1 für jede bereits gespielte Karte, sonst 0.                                                                                                             | Gibt dem MLP ein rudimentäres Gedächtnis der Runde. Ist aber für RNN, LSTM, GRU und DT irrelevant, da redundant mit `tricks`.                          |
| `announcements`         | `[int, int, int, int]`                                 | Tichu-Ansagen pro Spieler (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).                                                          | `[0, 0, 0, 0]`    | `PublicState`  | 12 Features (4 * 3): Für sich selbst, rechten Gegner, Partner, linken Gegner (relative Anordnung!) jeweils ein One-Hot-Vektor der Länge 3 (Labels: "keine Ansage", "kleines Tichu", "großes Tichu"). |                                                                                                                                                        |
| `wish_value`            | `int`                                                  | Der gewünschte Kartenwert (2 bis 14, 0 == kein Wunsch geäußert, negativ == bereits erfüllt).                                                     | `0`               | `PublicState`  | 15 Features: One-Hot-Vektor der Länge 15 (Labels: "kein Wunsch geäußert", "Wunsch bereits erfüllt", "2", "3", ..., "14")                                                                             |                                                                                                                                                        |
| `dragon_recipient`      | `int`                                                  | Index des Spielers, der den Drachen bekommen hat (-1 == noch niemand).                                                                           | `-1`              | `PublicState`  | 5 Features: One-Hot-Vektor der Länge 5 (Labels: "noch niemand", "ich", "rechter Gegner", "Partner", "linker Gegner") (relative Anordnung!)                                                           |                                                                                                                                                        |
| `trick_owner_index`     | `int`                                                  | Index des Spielers, der die letzte Kombination gespielt hat, also Besitzer des Stichs ist (-1 == kein Stich).                                    | `-1`              | `PublicState`  | 5 Features: One-Hot-Vektor der Länge 5 (Labels: "kein Stich", "ich", "rechter Gegner", "Partner", "linker Gegner") (relative Anordnung!)                                                             |                                                                                                                                                        |
| `trick_cards`           | `Cards` = `List[Card]`                                 | Die obersten Karten im Stich.                                                                                                                    | `[]`              | `PublicState`  | Nicht relevant. Ist in `played_cards` enthalten. Spieltechnisch entscheidend ist `trick_combination`.                                                                                                |                                                                                                                                                        |
| `trick_combination`     | `Combination` = `Tuple[int, int, int]`                 | Typ, Länge und Rang des aktuellen Stichs ((0,0,0) == leerer Stich).                                                                              | `(PASS, 0, 0)`    | `PublicState`  | 46 Features: 31-dimensionaler One-Hot-Vektor für Typ und Länge (Labels: siehe `CombinationTypeAndLength`) + "Thermometer"-kodierter Vektor der Länge 15 für den Rang.                                | Bzgl. Rang: 0 = Pass/Hund, 1 = Mahjong, 2, 3, ..., 14, 15 = Drache. Phönix-Rang ist kontextabhängig und wird daher nicht kodiert.                      |
| `trick_points`          | `int`                                                  | Punkte im aktuellen Stich. Zwischen -25 (nur der Phönix) und 100 (z.B. drei 4er-Bomben aus Fünfen, Zehnen und Könige).                           | `0`               | `PublicState`  | 1 Feature: Ein Float, skaliert.                                                                                                                                                                      |                                                                                                                                                        |
| `tricks`                | `List[Trick]` = `List[Tuple[int, Cards, Combination]]` | Liste der Stiche der aktuellen Runde. Der letzte Eintrag ist u.U. noch offen (wenn der Stich noch nicht einkassiert wurde).                      | `[]`              | `PublicState`  | Nicht relevant.                                                                                                                                                                                      | Wird nur für RNN, LSTM, GRU oder DT indirekt benötigt, um die Sequenzen zu erzeugen.                                                                   |
| `points`                | `[int, int, int, int]`                                 | Bisher kassierte Punkte in der aktuellen Runde pro Spieler. Zwischen -25 (nur der Phönix) und 125 (alle Punkte außer Phönix).                    | `[0, 0, 0, 0]`    | `PublicState`  | 4 Features: Für sich selbst, rechten Gegner, Partner, linken Gegner (relative Anordnung!) jeweils ein Float, skaliert.                                                                               |                                                                                                                                                        |
| `winner_index`          | `int`                                                  | Index des Spielers, der zuerst in der aktuellen Runde fertig wurde (-1 == alle Spieler sind noch dabei).                                         | `-1`              | `PublicState`  | 5 Features: One-Hot-Vektor der Länge 5 (Labels: "noch niemand", "ich", "rechter Gegner", "Partner", "linker Gegner") (relative Anordnung!)                                                           | Wichtiges Etappen-Ziel. Man möchte gern den ersten Platz belegen und damit die Punkte des Verlierers bekommen.                                         |
| `loser_index`           | `int`                                                  | Index des Spielers, der in der aktuellen Runde als letztes übrig blieb (-1 == Runde läuft noch oder wurde mit Doppelsieg beendet).               | `-1`              | `PublicState`  | Nicht relevant (wird erst am Ende der Runde gesetzt, wenn keine Entscheidungen mehr getroffen werden).                                                                                               |                                                                                                                                                        |
| `is_round_over`         | `bool`                                                 | Gibt an, ob die aktuelle Runde beendet ist.                                                                                                      | `False`           | `PublicState`  | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `is_double_victory`     | `bool`                                                 | Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.                                                                                      | `False`           | `PublicState`  | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `game_score`            | `GameScore` = `Tuple[List[int], List[int]]`            | Punktetabelle der Partie (für Team 20 und Team 31 jeweils eine Liste der Rundenergebnisse). Max. mögliche Punktedifferenz: 800 Punkte (#1).      | `([], [])`        | `PublicState`  | 2 Features: Für eigenes Team und gegnerisches Team jeweils ein Float (für den letzte Eintrag aus der Liste), skaliert.                                                                               |                                                                                                                                                        |
| `trick_counter`         | `int`                                                  | Anzahl der abgeräumten Stiche insgesamt über alle Runden der Partie (nur für statistische Zwecke).                                               | `0`               | `PublicState`  | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `player_index`          | `int`                                                  | Der Index dieses Spielers am Tisch (zwischen 0 und 3).                                                                                           | (Pflichtargument) | `PrivateState` | Nicht relevant.                                                                                                                                                                                      |                                                                                                                                                        |
| `hand_cards`            | `Cards` = `List[Card]`                                 | Die aktuellen Handkarten des Spielers (absteigend sortiert).                                                                                     | `[]`              | `PrivateState` | 56 Features: Multi-Hot-Vektor der Länge 56. 1 für jede Karte auf der Hand, sonst 0.                                                                                                                  |                                                                                                                                                        |
| `given_schupf_cards`    | `Optional[Tuple[Card, Card, Card]]`                    | Die drei Karten, die der Spieler zum Schupfen an den rechten Gegner, Partner und linken Gegner abgegeben hat (None, falls noch nicht geschupft). | `None`            | `PrivateState` | 51 Features (3 * 17): Für rechten Gegner, Partner, linken Gegner (relative Anordnung!) jeweils ein One-Hot-Vektor der Länge 17 zur Kodierung des Kartenwerts (Labels: "0", "1", ..., "16")           | Um drei große dünn besetzte Vektoren zu vermeiden, die nur wenig bis gar keine relevanten Informationen mitführen, betrachten wir nur die Kartenwerte. |
| `received_schupf_cards` | `Optional[Tuple[Card, Card, Card]]`                    | Die drei Karten, die der Spieler beim Schupfen vom rechten Gegner, Partner und linken Gegner erhalten hat (None, falls noch nicht geschupft).    | `None`            | `PrivateState` | 51 Features (3 * 17): Für rechten Gegner, Partner, linken Gegner (relative Anordnung!) jeweils ein One-Hot-Vektor der Länge 17 zur Kodierung des Kartenwerts (Labels: "0", "1", ..., "16")           | Auch hier reicht es aus, nur die Kartenwerte zu betrachten.                                                                                            |

Anzahl Features gesamt: 5 + 5 + 56 + 56 +12 + 15 +5 + 5 + 46 + 1 + 4 + 5 + 2 + 56 + 51 + 51 = **375 Features**.

Fußnote: #1) Die Punkte am Ende einer Runde ohne Bonus liegen 
*  bei normalem Sieg: zw. -25 (nur Phönix kassiert) und 125 (alle Punkte außer Phönix kassiert).
*  bei Doppelsieg: zw. 0 (Doppelsieg verloren) + 200 (Doppelsieg gewonnen).
=> Die maximal mögliche Differenz: 200.

Der Bonus für Tichu liegt zw. -400 (2 x großes Tichu verloren) und 200 (großes Tichu gewonnen).
=> Die mögliche Differenz durch Bonus: 600.

### 3.2 Feature-Vektor für GCPolicyNet und DTNet

Das `GCPolicyNet` und das `DTNet`benötigen als zusätzliches Feature den RTG. 
Für diese beiden Netze sind es also **376 Features**.

#### 3.2.1 Berechnung von Return-to-Go (RTG)

Sei:
*   `FinalScore`: Der finale Punktestand, den das Team am Ende der Runde gutgeschrieben bekommt (inkl. Bonus für Tichu-Ansage). 
*   `KassiertePunkte_bis_t`: Die Summe der Punkte in allen Stichen, die das Team bis zum Zeitpunkt t (also vor der aktuellen Aktion) bereits kassiert hat.

Falls die Runde mit Doppelsieg endet: `RTG_t = FinalScoreEigen - FinalScoreGegner` (also konstant für alle t)
*   **Terminal Reward**: Ohne Zwischenbelohnung  
    *   Vorteil: Ist immer korrekt und spiegelt das wahre Ziel des Spiels wider.
    *   Nachteil: **Sparse Reward Problem**: Das Modell muss aus einer langen Kette von Aktionen lernen, welcher Zug am Anfang wirklich zum Sieg am Ende beigetragen hat. Das ist schwierig.
 
Falls die Runde ohne Doppelsieg endet: `RTG_t = (FinalScoreEigen - FinalScoreGegner) - (KassiertePunkteEigen_bis_t - KassiertePunkteGegner_bis_t)`
*   **Reward Shaping**: Eine "Zwischenbelohnung", die dem Modell hilft, die richtige Aktion zu wählen, den FinalScore zu erreichen.

Wir normalisieren RTG mit Faktor 1/100.

## 4. Label Engineering 

Wie repräsentieren wir den Output (Aktion -> Label-Vektor)?

### 4.1 Label-Vektor für PolicyNet, GCPolicyNet und DTNet

#### 4.1.1 Variante 1: Flache Repräsentation (einfach)

Der Output von unseren Policy-Netzen (`PolicyNet`, `GCPolicyNet` oder `DTNet`) hat 57 Labels (für jede der 56 Karten ein Label + Passen).

Für jede Karte wird die Wahrscheinlichkeit zw. 0 und 1 angegeben, dass die Karte eine gute Wahl ist, ausgespielt zu werden. 
Ebenso für das Passen.

**Aktivierungsfunktion:**
Es können mehrere Labels gleichzeitig klassifiziert werden, es ist eine **Multi-Label-Klassifikation**.
Daher muss `Sigmoid` als Aktivierungsfunktion  gewählt werden.

Diese Variante ist:
*   der Industriestandard für Multi-Label-Probleme.
*   einfach zu implementieren und zu trainieren.
*   erwiesenermaßen sehr leistungsfähig.

#### 4.1.2 Variante 2: Hierarchische Repräsentation (komplexer)

Das Model hat zwei Outputs:
*   Output mir 56 Label (für jede der 56 Karten ein Label) für Klasse "Karten ausspielen" (**Multi-Label-KlassifikationKomplexer**, `Sigmoid`-Aktivierung)
*   Output mit ein Label "ja" für Klasse "Passen" (**Binäre Klassifikation**, `Sigmoid`-Aktivierung)

Es kann nur ein Output gewählt werden. Dies ist eine **Multi-Klassen-Klassifikation**, d.h. es muss `Softmax` als Aktivierungsfunktion für die beiden Outputs gewählt werden.

Vorteil dieser Variante: 
*   Keine widersprüchlichen Outputs

#### 4.1.3 Interpretation

Dieser Aufbau ist der Standard für die Integration von neuronalen Netzen in regelbasierte Spiele wie Schach, Go und eben auch Tichu.

Der Agent berechnet für jeden möglichen Zug (aus action_space) einen "desirability score" (Attraktivitätsbewertung).
*  Für "Passen" ist der Score einfach der Output des 57. Neurons.
*  Für einen Kartenzug ist der Score die Summe der Wahrscheinlichkeiten aller Karten, die zu diesem Zug gehören. 

Der Agent wählt den Zug aus dem action_space, der den höchsten Score erzielt hat, und gibt ihn an die GameEngine zurück.

Man kann die Scoring-Heuristik verfeinern. Anstatt nur zu summieren, könnte man den Durchschnitt nehmen oder seltene Karten höher gewichten. Dies ermöglicht eine einfache Anpassung der Spielstärke, ohne das Netz neu trainieren zu müssen.

### 4.2 Label-Vektor für ValueNet

Der Output des Value-Netzes hat ein Label. Es ist die Punkte-Differenz der beiden Teams am Ende der Runde, 
also ein kontinuierlicher Zahlenwert (Float, Skalar).

Das Netz ordnet dem Input einen kontinuierlichen numerischen Wert zu. Dies ist eine **Regression**. 
Wir brauchen daher die `lineare` Aktivierungsfunktion.

#### 4.2.1 Interpretation

Der Output bei der Regression muss nicht interpretiert werden. Wir können ihn 1:1 als RGB übernehmen.

## 5. Modelldesign / Architektur

Welches Netz-Design verwenden wir, um vom Input zum Output zu gelangen?

Grundannahmen für alle Modelle:
*   Input-Dimension (Zustand): 375 Features
*   Input-Dimension (RTG): 1 Feature
*   Output-Dimension (Policy): 57 Features
*   Output-Dimension (Value): 1 Feature

### 5.1. Architektur für PolicyNet

Ein einfaches, aber tiefes MLP, das lernt, den Zustand auf Aktionen abzubilden.

**Visuelle Darstellung**
<pre>
   [375-dim Input: Zustand]
              |
+----------------------------+
| Dense Layer (512 Neuronen) |
| Activation: ReLU           |
| Dropout: 0.2               |
+----------------------------+
              |
+----------------------------+
| Dense Layer (512 Neuronen) |
| Activation: ReLU           |
| Dropout: 0.2               |
+----------------------------+
              |
+----------------------------+
| Dense Layer (256 Neuronen) |
| Activation: ReLU           |
+----------------------------+
              |
   [57-dim Output: P,P,...]
    (Activation: Sigmoid)
</pre>

Legende:
*   Dense Layer: Ein standardmäßiges, voll vernetztes Layer (in PyTorch: Linear).
*   ReLU: Die Standard-Aktivierungsfunktion für versteckte Schichten.
*   Dropout: Eine Regularisierungstechnik, die hilft, Overfitting zu verhindern, indem sie zufällig Neuronen während des Trainings "ausschaltet".

### 5.2. Architektur für GCPolicyNet + ValueNet

Dies ist eine Multi-Foot- und Multi-Head-Architektur mit geteiltem Körper.

**Visuelle Darstellung**
<pre>
[RTG-Input (1 dim)]   [375-dim Input: Zustand]
       |                    |
       |      +-----------------------------+
       |      |      SHARED BACKBONE        |
       |      | Dense Layer (1024 Neuronen) |
       |      | Activation: ReLU            |
       |      | Dropout: 0.2                |
       |      +-----------------------------+
       |                    |
       |      +-----------------------------+
       |      | Dense Layer (1024 Neuronen) |
       |      | Activation: ReLU            |
       |      | Dropout: 0.2                |
       |      +-----------------------------+
       |                    |
       |       [1024-dim "Gedanken-Vektor"]
       |                    |
       |        +-----------+-----------+
       |        |                       |
[Concat(RTG, Gedanke]                   |
+---------------------+       +---------------------+
|    POLICY HEAD      |       |     VALUE HEAD      |
| Dense Layer (512 N) |       | Dense Layer (256 N) |
| Activation: ReLU    |       | Activation: ReLU    |
+---------------------+       +---------------------+
           |                            |
[57-dim Output: P,P,...]        [1-dim Output: RTG]
 (Activation: Sigmoid)          (Activation: Linear)
</pre>

Legende:
*   Shared Backbone: Ein größerer gemeinsamer Körper lernt die allgemeine Repräsentation des Spiels.
*   Policy Head: Nimmt den "Gedanken-Vektor", konkateniert ihn mit dem RTG-Input und hat dann eine eigene Schicht, um die Aktion vorherzusagen.
*   Value Head: Nimmt denselben "Gedanken-Vektor" und sagt den Spielwert voraus.

### 5.3. Architektur für DLNet + ValueNet

Dies ist eine Multi-Head-Architektur mit geteiltem Körper.

**Visuelle Darstellung**
<pre>
   [ Sequenz von (RTG, Zustand, Aktion) Tokens ]
                         |
         +---------------------------------+
         | Embedding & Positional Encoding |  (Projiziert alles auf d_model=512)
         +---------------------------------+
                         |
         [ Sequenz von 512-dim Vektoren ]
                         |
          +-----------------------------+
          |    TRANSFORMER BACKBONE     |
          |   (z.B. 4x Transformer-    |
          |       Encoder-Layer)        |
          +-----------------------------+
                         |
    [ Output-Sequenz von 512-dim Vektoren ]
                         |
  (Nimm nur den Vektor des letzten Zustand-Tokens)
                         |
           +-------------+------------+
           |                          |
+---------------------+     +---------------------+
|    POLICY HEAD      |     |    VALUE HEAD       |
| Dense Layer (256 N) |     | Dense Layer (256 N) |
| Activation: ReLU    |     | Activation: ReLU    |
+---------------------+     +---------------------+
          |                           |
[57-dim Output: P,P,...]      [1-dim Output: RTG]
 (Activation: Sigmoid)        (Activation: Linear)
</pre>

Legende:
* Transformer Backbone: Der Hauptteil, der die Sequenz verarbeitet.
* Auswahl des letzten Tokens: Für die Vorhersage der nächsten Aktion und des aktuellen RTG verwenden wir 
  typischerweise nur den Output-Vektor des Transformers, der dem letzten Zustand in der Input-Sequenz entspricht.

## 6. Aufbereitung der Daten 
 
### 6.1 Datenbestand

Für das Training stehen 2.411.330 Logdateien (ca. 7 GB) vom Spiele-Portal "Brettspielwelt" zur Verfügung (Stand 26.07.2025 08:00, Letzter Eintrag: 2025/202507/2411377.tch).   
Jede Logdatei hat die Daten einer Partie. 

Mit dem Datenbestand bis 2022/04 lagen 2.352.727 Partien mit insgesamt 22.042.274 Runden vor.
Im Schnitt wurden demnach 9,37 Runden pro Partie gespielt.

Damit haben wir im aktuellen Datenbestand ca. 22.591.315 Runden. 

Da wir 4 Spieler haben, haben wir 4 verschiedene Perspektiven und somit die 4-fache Datenmenge: 90.365.260 "Perspektiv-Runden".

Im Spiel mit 4 HeuristicAgents fallen ca. 10.8 Stiche/Runde (so häufig wurden Karten kassiert). 

Ich schätze 6 Spielzüge (Kartenlegen oder Passen) pro Stich. Das ergibt 64.8 Spielzüge pro Runde.

Bezogen auf die Perspektiv-Runden haben wir ca. 975.944.808 Stiche bzw. 5.855.668.848 Spielzüge.

### 6.2 BWRoundData

Ein Parser überführt jede Logdatei in eine Liste von `BWRoundData`-Objekten. 

Der Datencontainer `BWRoundData` stellt alle aus der Logdatei verfügbaren Daten eine Runde bereit:
- `game_id: int` - Eindeutige ID der Partie.
- `round_index: int` - Index der Runde innerhalb der Partie.
- `player_names: List[str]` - Die Namen der 4 Spieler dieser Runde.
- `grand_tichu_hands: List[str]` - Die ersten 8 Handkarten der vier Spieler zu Beginn der Runde.
- `start_hands: List[str]` - Die 14 Handkarten der Spieler vor dem Schupfen.
- `tichu_positions: List[str]` - Position in der Historie, an der ein Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor Schupfen).
- `given_schupf_cards: List[str]` - Schupf-Karten (an rechten Gegner, Partner, linken Gegner).
- `bomb_owners: List[str]` - Gibt für jeden Spieler an, ob eine Bombe auf der Hand ist.
- `wish_value: int` - Wunsch (2 bis 14; 0 == kein Wunsch geäußert).
- `dragon_recipient: int` - Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde bis zum Schluss nicht verschenkt).
- `score_entry: Tuple[int, int]` - Punkte dieser Runde pro Team (Team20, Team31).
- `history: List[Union[Tuple[int, str], int]]` - Spielzüge. Jeder Spielzug ist ein Tuple aus Spieler-Index und Karten, oder beim Passen nur der Spieler-Index.
- `year: int` - Jahr der Logdatei.
- `month: int` - Monat der Logdatei.

### 6.3 Replay-Simulator

Der Replay-Simulator durchläuft alle Spielzüge einer Runde. 

Er benötigt für den gesamten Datenbestand TODO Minuten, durchschnittlich also TODO Sekunden pro Partie und TODO Sekunden pro Runde.

### 6.3 Daten analysieren

Um die Daten analysieren zu können, sammeln wir die relevanten Daten in einer DB. 

Dazu durchlaufen wir mit dem **Replay-Simulator** einmal den gesamten Datenbestand. Der Durchlauf hat TODO Minuten gedauert.

#### 6.3.1 Analyse-Fragen

Um die Trainingszeit und den Speicherbedarf abzuschätzen:
*   Anzahl Partien, Runden, Stiche und Spielzüge insgesamt.
        SELECT COUNT(*) FROM games; -> Anzahl Partien
        SELECT COUNT(*) FROM rounds; == SELECT SUM(num_rounds) FROM games; -> Anzahl Runden
        SELECT SUM(num_tricks) FROM rounds; -> Anzahl Stiche
        SELECT SUM(num_turns) FROM rounds; -> Anzahl Spielzüge

Um die Anzahl der Features zu bestimmen, die notwendig wären, würde man historische Daten hinzufügen:
*   Pro Partie die Anzahl Runden (min, max, mean, stddev).
        SELECT MIN(num_rounds), MAX(num_rounds), AVG(num_rounds), STDEV(num_rounds) FROM games;
        
*   Pro Runde die Anzahl Stiche und Spielzüge (min, max, mean, stddev).
        SELECT MIN(num_tricks), MAX(num_tricks), AVG(num_tricks), STDEV(num_tricks) FROM rounds;
    
*   Pro Runde die Anzahl Spielzüge (min, max, mean, stddev).
        SELECT MIN(num_turns), MAX(num_turns), AVG(num_turns), STDEV(num_turns) FROM rounds;

Zum Skalieren der kontinuierlichen Werte:
*   trick_point: Summe der Punkte im Stich

*   points: Bisher kassierte Punkte in der Runde pro Spieler
        SELECT MIN(min_points), MAX(max_points), SUM(avg_points * num_turns)/SUM(num_turns) AS avg_avg_points, STDEV(score_20) FROM rounds;
   
*   game_score: Einträge der Punktetabelle, d.h. Endergebnis jeder Runde 
        SELECT MIN(score_20), MAX(score_20), AVG(score_20), STDEV(score_20) FROM rounds;
        SELECT MIN(score_31), MAX(score_31), AVG(score_31), STDEV(score_31) FROM rounds;
        SELECT MIN(score_diff), MAX(score_diff), AVG(score_diff), STDEV(score_diff) FROM rounds;

Ausgewogenheit der Daten:
*   Runde mit Doppelsieg beendet
*   Großes Tichu angesagt
*   Großes Tichu angesagt und gewonnen 
*   Einfaches Tichu angesagt
*   Einfaches Tichu angesagt und gewonnen 
*   Wunsch-Wert
*   Empfänger des Drachens
*   Geschupfte Karte an den rechten Gegner
*   Geschupfte Karte an den Partner
*   Geschupfte Karte an den linken Gegner
*   Team20 schupft nach Regel "rechts gerade, links ungerade" bzw. "rechts ungerade, links gerade"
*   Team31 schupft nach Regel "rechts gerade, links ungerade" bzw. "rechts ungerade, links gerade"

Spieloptionen:
*   Wunsch wurde nicht geäußert, obwohl Mahjong gespielt wurde
*   Einfaches Tichu angesagt während des Schupfens
*   Zwei Tichu-Ansagen aus einem Team (großes + großes)
*   Zwei Tichu-Ansagen aus einem Team (großes + einfaches) 
*   Zwei Tichu-Ansagen aus einem Team (einfaches + einfaches)

Inhaltliche Fehler:
*   Regelbrüche (welcher Fehler hat der Replay-Simulator entdeckt?) 
 
Gute Spieler finden 
*   Finde die Spieler mit viel Spielerfahrung
*   Finde die Top 10% der Spieler basierend auf avg_score_diff.

#### 6.3.2 Analyse-Ergebnis

Die Analyse der Datenbank ist im Jupyter Notebook [Datenanalyse.ipynb](../jpynb/Datenanalyse.ipynb) dokumentiert.

Hier sind die Ergebnisse zusammengefasst:

TODO

### 6.4 Feature- und Label-Vektoren speichern

Auf Basis der Datenanalyse werden ausgewogene Datensätze mit den Feature- und Label-Vektoren im HDF5-Format gespeichert. 
Dabei werden die Ausreißer entsprechend behandelt und kontinuierliche Daten skaliert.   

Folgende Features sind kontinuierlich und werden skaliert:
*   `trick_points: int`
*   `points: [int, int, int, int]`
*   `game_score: Tuple[List[int], List[int]]`

### 6.5 Datensätze in Trainings-, Validierungs- und Testdaten aufteilen

## 7. Training

### 7.1 Geschätzter Rechenaufwand

Als Hardware steht eine RTX 2080 (8 GB VRAM) zur Verfügung.

`PolicyNet`, `GCPolicyNet` und `ValueNet`:

*   Modellgröße: Ein MLP mit 3-5 Schichten und ~512 Neuronen pro Schicht ist relativ klein. Die Anzahl der Parameter liegt im Bereich von wenigen Millionen.
*   GPU-Anforderung:
    *   Modell im VRAM: Das Modell selbst wird nur wenige Dutzend MB im VRAM belegen. Kein Problem.
    *   Daten-Batches im VRAM: Hier liegt der Engpass. Bei einer Batch-Größe von z.B. 1024 und einem Feature-Vektor von 376 (float32 = 4 Bytes) wäre ein Batch 1024 * 376 * 4 Bytes ≈ 1.5 MB groß. Das ist winzig.
    *   Zwischenberechnungen (Gradients): Das ist der Hauptverbraucher von VRAM. Für ein MLP dieser Größe wird der VRAM-Bedarf pro Batch im Bereich von einigen hundert MB liegen.
    *   => Die RTX 2080 (8 GB VRAM) ist absolut ausreichend. Große Batch-Größen (z.B. 4096, 8192 oder sogar mehr) sind problemlos zu verwenden.
*   Trainingszeit: Einige Stunden bis zu einem Tag.

`DLNet`:

*   Modellgröße: Transformer sind deutlich größer und komplexer als MLPs. Selbst ein "kleiner" DT hat oft mehr Parameter.
*   GPU-Anforderung:
    *   Sequenzlänge: Der VRAM-Bedarf eines Transformers skaliert quadratisch mit der Länge der Input-Sequenz (O(L²)). Eine Tichu-Runde kann 30-50 Züge haben. Wie wir besprochen haben, besteht jeder Zug aus 3 Tokens (Zustand, Aktion, RTG). Eine lange Runde könnte also eine Sequenzlänge von 50 * 3 = 150 haben. Das ist für einen Transformer schon recht lang.
    *   Batch-Größe: Wegen der langen Sequenzen musst du die Batch-Größe drastisch reduzieren. Anstatt Tausende von Beispielen auf einmal zu verarbeiten, kannst du vielleicht nur Batches von 16, 32 oder 64 Runden-Trajektorien in den 8 GB VRAM unterbringen.
    *   "Attention"-Mechanismus: Die Berechnungen im Transformer sind rechenintensiver als bei einem MLP.
    *   => Die RTX 2080 (8 GB VRAM): Es ist an der Grenze, aber machbar. Man müsste:
        * Sequenzlänge begrenzen (z.B. immer nur die letzten 20 Züge betrachten).
        * kleine Batch-Größe verwenden.
        * "Gradient Accumulation" verwenden, um größere effektive Batch-Größen zu simulieren.
        * eventuell Mixed-Precision-Training (float16) einsetzen, um VRAM zu sparen.
*   Trainingszeit: Mehrere Tage bis Wochen (durch die kleineren Batches und die komplexeren Berechnungen dauert es länger). 

Selfplay:

*   Aufgabe: Das System muss gleichzeitig Spiele simulieren (GameEngine auf der CPU) und das neuronale Netz für Vorhersagen nutzen (NNetAgent auf der GPU).
*   Rechenaufwand:
    *   Inferenz: MCTS ist extrem Inferenz-lastig. Für jeden einzelnen Zug im Self-Play werden Hunderte oder Tausende von Vorhersagen vom Policy- und Value-Netz benötigt. Deine GPU wird hier sehr stark ausgelastet sein, nur um die Spiele zu generieren.
    *   Training: Parallel dazu müssen die neu generierten Spieldaten verwendet werden, um das Netz regelmäßig neu zu trainieren.
    *   => Sehr, sehr anspruchsvoll. Professionelle Self-Play-Trainingsläufe für Spiele wie Schach oder Go nutzen oft ganze Cluster von GPUs und CPUs.
* Trainingszeit Wochen bis Monate (bis signifikante Verbesserungen zu sehen sind).

### 7.2. Verlustfunktion

*   Das Policy-Netz ist eine Multi-Label-Klassifikation, also nehmen wir **Binary Cross-Entropy (BCE)**.
*   Das Value-Netz ist eine Regression, also nehmen wir **Mean Squared Error (MSE)**.
 
### 7.3 Trainingsdurchlauf

Folgende Versuche mit folgenden Hyperparametern und Modifikationen an der Architektur haben wir durchgeführt:

TODO

### 7.4 Leistung des Modells bewerten

Hierzu werden die Validierungsdaten benötigt.

Vergleich zw. den Modellvarianten:

TODO

## 8. Finale Bewertung des Modells

Hierzu werden die Testdaten benötigt.

TODO

### 8.1 Treffergenauigkeit

# Anhang

## A1. Kartenkombinationen

<pre>
Rang der Karten
DOG MAH 2  3  4  5  6  7  8  9 10  J  Q  K  A DRA

SINGLE         # Einzelkarte
Anzahl=17      # DOG, MAH, 2 bis 14, DRA und PHO 

PAIR           # Paar
Anzahl=13      # Rang 2 bis 14

TRIPLE         # Drilling
Anzahl=13      # Rang 2 bis 14

STAIR          # Treppe
12             # 2er-Treppe: 2,3 bis K,A
11             # 3er-Treppe: 2,3,4 bis Q,K,A
10             # 4er-Treppe: 2,3,4,5 bis J,Q,K,A
 9             # 5er-Treppe: 2,3,4,5,6 bis 10,J,Q,K,A
 8             # 6er-Treppe: 2,3,4,5,6,7 bis 9,10,J,Q,K,A
 7             # 7er-Treppe: 2,3,4,5,6,7,8 bis 8,9,10,J,Q,K,A
--
Anzahl=57

FULLHOUSE      # Fullhouse
Anzahl=13      # Rang 2 bis 14

STREET         # Straße
10             #  5er-Straße: MAH,2,3,4,5 bis 10,J,Q,K,A
 9             #  6er-Straße: MAH,2,3,4,5,6 bis 9,10,J,Q,K,A
 8             #  7er-Straße: MAH,2,3,4,5,6,7 bis 8,9,10,J,Q,K,A 
 7             #  8er-Straße: MAH,2,3,4,5,6,7,8 bis 7,8,9,10,J,Q,K,A  
 6             #  9er-Straße: MAH,2,3,4,5,6,7,8,9 bis 6,7,8,9,10,J,Q,K,A   
 5             # 10er-Straße: MAH,2,3,4,5,6,7,8,9,10 bis 5,6,7,8,9,10,J,Q,K,A    
 4             # 11er-Straße: MAH,2,3,4,5,6,7,8,9,10,J bis 4,5,6,7,8,9,10,J,Q,K,A   
 3             # 12er-Straße: MAH,2,3,4,5,6,7,8,9,10,J,Q bis 3,4,5,6,7,8,9,10,J,Q,K,A   
 2             # 13er-Straße: MAH,2,3,4,5,6,7,8,9,10,J,Q,K bis 2,3,4,5,6,7,8,9,10,J,Q,K,A   
 1             # 14er-Straße: MAH,2,3,4,5,6,7,8,9,10,J,Q,K,A   
--
Anzahl=55

BOMB           # Bombe
13             #  4er-Bombe: 2 bis 14
 9             #  5er-Bombe: 2,3,4,5,6 bis 10,J,Q,K,A
 8             #  6er-Bombe: 2,3,4,5,6,7 bis 9,10,J,Q,K,A 
 7             #  7er-Bombe: 2,3,4,5,6,7,8 bis 8,9,10,J,Q,K,A  
 6             #  8er-Bombe: 2,3,4,5,6,7,8,9 bis 7,8,9,10,J,Q,K,A   
 5             #  9er-Bombe: 2,3,4,5,6,7,8,9,10 bis 6,7,8,9,10,J,Q,K,A    
 4             # 10er-Bombe: 2,3,4,5,6,7,8,9,10,11 bis 5,6,7,8,9,10,J,Q,K,A   
 3             # 11er-Bombe: 2,3,4,5,6,7,8,9,10,11,12 bis 4,5,6,7,8,9,10,J,Q,K,A   
 2             # 12er-Bombe: 2,3,4,5,6,7,8,9,10,11,12,13 bis 3,4,5,6,7,8,9,10,J,Q,K,A   
 1             # 13er-Bombe: 2,3,4,5,6,7,8,9,10,J,Q,K,A
--
Anzahl=58

===
Gesamtanzahl = 226 Kombinationsmöglichkeiten
</pre>

## A2. Kategoriale, diskrete und stetige Variablen

**Binäre Variable (Boolean):**
*   haben genau zwei Zustände
*   Beispiel: Ja/Nein, An/Aus, Gewonnen/Verloren

**Kategoriale Variable (One-Hot-Kodierung):**
*   umfassen eine endliche Anzahl von Kategorien oder eindeutigen Gruppen.
*   die Daten müssen nicht zwangsläufig eine logische Reihenfolge aufweisen.
*   Beispiel: Geschlecht, Materialtyp, Zahlungsmethode, Kartenkombination

**One-Hot-Kodierung:**
*   gehört zu den Standardpraktiken
*   Beispiel für die One-Hot-Kodierung für eine Ampelfarbe (3-dimensionaler One-Hot-Vektor, One-Hot-Vektor der Länge 3):
    - [1, 0, 0] = rot
    - [0, 1, 0] = gelb
    - [0, 0, 1] = grün
*  Es ist besser, "kein Wert" nicht mit "alles 0" zu kodieren, sondern den Vektor zu vergrößern:   
    - [1, 0, 0, 0] = Ampel kaputt
    - [0, 1, 0, 0] = rot
    - [0, 0, 1, 0] = gelb
    - [0, 0, 0, 1] = grün

**Stetige Variable (Float-Wert):**
*   sind numerische Variablen, die zwischen zwei beliebigen Werten eine unendliche Anzahl von Werten aufweisen.
*   die Daten weisen eine logische Reihenfolge auf (sind logisch sortierbar).
*   Beispiel: physikalische Messwerte, Zeitstempel 
*   eine Normalisierung des Wertes in den Bereich [0, 1] bzw. [-1, 1] gehört zu den Standardpraktiken

**Diskrete Variable (Int-Wert, "Thermometer"-Kodierung):**
*   zwischen zwei beliebigen Werten gibt es eine zählbare Anzahl von Werten.
*   ist immer numerisch.
*   kann nicht normalisiert werden
*   Beispiele: Anzahl von Kundenbeschwerden, Anzahl von Handkarten, Kartenwert, Wert und Länge einer Kombination

**"Thermometer"-kodierter Vektor**
*   ist für ein NN oft besser als nur eine einzelne Zahl.
*   gehört zu den Standardpraktiken
*   Beispiel für ein "Thermometer"-kodierter Vektor der Länge 14: 
    - [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0 ,0 ,0] = 5

### A2.1 Wann bevorzugt man "Thermometer" vs. normalisierter Float?

Beide kodieren ordinale (geordnete) Daten.

*	**Normalisierter Float (Skalar)**: value / max_value -> ergibt eine einzelne Zahl zwischen 0 und 1.
	*	**Wann verwenden?**
		*	Wenn die Variable **kontinuierlich** ist oder sehr viele diskrete Werte hat (z.B. Punktestand von 0 bis 1000). Ein Thermometer mit 1000 Stellen wäre unpraktikabel.
		*	Wenn die Beziehung zwischen den Werten **rein linear** ist. D.h., der Unterschied zwischen 10 und 20 Punkten ist strategisch genauso wichtig wie der zwischen 910 und 920.
	*	**Beispiele:** trick_points, game_score. Hier ist es perfekt.

*	**"Thermometer"-kodierter Vektor (fachlich: Cumulative Encoding oder Ordinal Encoding)**:
	*	**Wann verwenden?**
		*	Wenn die Variable **diskret** ist und eine **überschaubare Anzahl an Stufen** hat (z.B. Kartenanzahl 0-14, Rang 0-15).
		*	Wenn die Beziehung zwischen den Werten **nicht rein linear** ist. Ein Neuronales Netz kann durch die unterschiedliche Gewichtung der einzelnen "Stufen" im Thermometer lernen, dass bestimmte Schwellenwerte wichtiger sind. Z.B. ist der Unterschied zwischen 1 und 0 Handkarten (jemand wird fertig) strategisch viel wichtiger als der zwischen 13 und 12 Handkarten. Ein Thermometer gibt dem Netz mehr Flexibilität, solche nicht-linearen Beziehungen zu lernen.
	*	**Beispiele:** count_hand_cards, trick_combination_rank. Hier ist es die bessere Wahl.

**Faustregel:** Für "Zählungen" mit wenigen Stufen (wie Kartenanzahl) ist Thermometer oft überlegen. Für "Messwerte" mit vielen Stufen (wie Punkte) ist ein normalisierter Float besser.

### A2.2 Wann sollte man Redundanz in Kauf nehmen?

Zu count_hand_cards sagst du es könnte nützlich sein, eigene Kartenanzahl hinzufügen. [...] Wann sollte man trotzdem Redundanz in Kauf nehmen?

Das ist eine hohe Kunst im Feature Engineering. Redundanz ist nicht immer schlecht.

**Man nimmt Redundanz in Kauf, wenn:**

1.	ein Feature für das Netz schwer zu "lernen" ist: Die Anzahl der eigenen Handkarten ist zwar aus dem 56-dimensionalen hand_cards-Vektor exakt berechenbar (sum(hand_cards_vector)), aber das erfordert, dass das Netz lernt, über 56 Inputs zu summieren. Das ist eine zusätzliche Aufgabe. Wenn du ihm die Summe als separates Feature (z.B. als 14-dim Thermometer) gibst, **erleichterst du dem Netz die Arbeit**. Es muss diese grundlegende Information nicht mehr selbst ableiten.
2.	das Feature eine hohe strategische Bedeutung hat: Die eigene Kartenanzahl ist extrem wichtig (z.B. für Tichu-Ansagen). Indem man sie explizit macht, gibt man ihr mehr "Gewicht" und stellt sicher, dass das Netz sie nicht übersieht.
3.	**die Redundanz unterschiedliche Aspekte beleuchtet:** Der hand_cards-Vektor sagt: "**Welche** Karten habe ich?". Das redundante count_hand_cards_own-Thermometer sagt: "**Wie viele** Karten habe ich?". Das sind zwei unterschiedliche, wenn auch korrelierte, Informationen.

## A3. Nummerische kontinuierliche Features skalieren

Beispiel Score-Differenzen:
*   Theoretischer Bereich, aber extrem unwahrscheinlich: [-800, 800]
*   Datenmenge: ca 25 Mio. 

Vorgehen:
1. Visuelle Datenanalyse: Histogramm und Q-Q-Plot erstellen.
2. Numerische Datenanalyse: Statistische Kennwerte berechnen
3. Clipping: Ausreißer auf einen plausiblen Wert drücken.
4. Skalieren: Werte in den Bereich [0, 1] bzw. [-1, 1] überführen.

### A3.1 Visuelle Datenanalyse

#### A3.1.1 Histogramm

Ein Histogramm zeigt die Häufigkeit von Werten in einem Datensatz – also wie oft Werte in bestimmten Intervallen (Bins) vorkommen. 

```python
import numpy as np
import matplotlib.pyplot as plt

data = np.random.normal(0, 1, 1000)
plt.hist(data, bins=30, edgecolor='black')
plt.title("Histogramm")
plt.xlabel("Wert")
plt.ylabel("Häufigkeit")
plt.grid(True)
plt.show()
```

#### A3.1.2 Q-Q-Plot (Quantile-Quantile-Plot)

Ein **Q-Q-Plot (Quantile-Quantile-Plot)** vergleicht die Quantile deiner Daten mit denen einer theoretischen Verteilung (meist Normalverteilung).

```python
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

data = np.random.normal(0, 1, 100)
stats.probplot(data, dist="norm", plot=plt)
plt.title("Q-Q-Plot")
plt.grid(True)
plt.show()
```

Interpretation:
*   Punkte liegen nahe an der Diagonalen → Daten sind normalverteilt
*   Punkte weichen stark ab → Ausreißer oder nicht-normalverteilte Daten

### A3.2 Numerische Datenanalyse

Statistische Kennwerte berechnen

Lade alle Score-Differenzen aus den 25 Millionen Runden in ein NumPy-Array und berechne 
*   Minimal- und Maximal-Wert, 
*   Mittelwert und Standardabweichung
*   0.5-Perzentil (q=0.005) und 99.5-Perzentil (q=0.995).

Der Mittelwert ist der Durchschnitt aller Werte in einem Datensatz: `mean = sum(values) / len(values)`

Die Standardabweichung misst, wie stark die Werte um den Mittelwert streuen: `std_dev = math.sqrt(sum((value - mean) ** 2 for value in values) / (n - 1))`  (`** 2` = ^2)  

Die Perzentile sagen dir, unterhalb welches Wertes ein bestimmter Prozentsatz deiner Daten liegt.
*   Das 0.5-Perzentil: Der Wert, unter dem die niedrigsten 0.5% aller Scores liegen.
*   Das 99.5-Perzentil: Der Wert, unter dem 99.5% aller Scores liegen.

Die 25 Millionen Scores (25.000.000 * 4 Bytes/float ≈ 100 MB) sollten problemlos in den RAM der meisten modernen Computer passen.

Mit reinem Python ist die Berechnung dieser Daten nicht zu empfehlen (viel zu langsam für große Datenmengen). 
Besser und der Standard für numerische Daten ist NumPy:

```python
import numpy as np

scores_array = np.array(scores)

min_val = np.min(scores_array)
max_val = np.max(scores_array)
mean_val = np.mean(scores_array)
std_dev_val = np.std(scores_array, ddof=1)  # ddof=1 bedeutet, wir haben eine Stichprobe und teilen daher durch n-1 (statt durch n)

# Perzentile berechnen (q ist der Quantilwert von 0 bis 1)
p_0_5 = np.quantile(scores_array, 0.005)
p_99_5 = np.quantile(scores_array, 0.995)

print(f"Min: {min_val}, Max: {max_val}, Mean: {mean_val:.2f}, StdDev: {std_dev_val:.2f}")
print(f"0.5 Perzentil: {p_0_5}, 99.5 Perzentil: {p_99_5}")
```

#### A3.2.1 Shapiro-Wilk-Test

Der Shapiro-Wilk-Test prüft, ob ein Datensatz normalverteilt ist.

```python
import numpy as np
from scipy.stats import shapiro

data = np.random.normal(loc=0, scale=1, size=100)  # normalverteilte Daten
stat, p = shapiro(data)
print(f"Teststatistik: {stat:.3f}, p-Wert: {p:.3f}")

if p > 0.05:
    # Nullhypothese wird nicht verworfen → Daten sind normalverteilt
    print("✅ Daten sind normalverteilt")
else:
    print("❌ Daten sind nicht normalverteilt")
```

### A3.3. Clipping

Ausreißer auf einen plausiblen Wert drücken.

*    **Bei Normalisierung:** Clipping ist essenziell. Ein Fehler könnte zu einem absurden Wert von z.B. 9999 führen. 
     Ohne Clipping würde dieser eine Datenpunkt deine gesamte Statistik (min, max, mean, std_dev) zerstören und das Training ruinieren. 
*    **Bei Standardisierung:** Clipping ist sehr nützlich. Es verhindert, dass extreme Ausreißer den Mittelwert und 
     die Standardabweichung verzerren. Wenn der Mittelwert und die Standardabweichung stabiler sind, ist die resultierende 
     Skalierung für die Mehrheit der Daten aussagekräftiger. 

Die Werte des **0.5- und 99.5-Perzentils*** sind oft exzellente Kandidaten für deine Clipping-Grenzen.

Beispiel: Deine Analyse ergibt: `min = -800, max = 750, 0.5-Perzentil = -380, 99.5-Perzentil = +410`
Deine Clipping-Grenzen könnten sein: `min_grenze = -400, max_grenze = 400` (runde auf schöne Zahlen in der Nähe der Perzentile).

```python
import numpy as np
data = np.array([-550, -300, 120, 680])
clipped = np.clip(data, -400, 400)
print(clipped)  # Ergebnis: [-400, -300, 120, 400]
```

### A3.4 Skalieren

Warum ist Skalieren notwendig?

Neuronale Netze funktionieren am besten mit Zahlen, die in einem kleinen Bereich um 0 liegen (typischerweise 
zwischen -1 und 1 oder 0 und 1). Wenn deine Zielwerte aber z.B. im Bereich von -400 bis +400 liegen, sind die 
Fehler (`loss = (vorhersage - ziel)^2`) riesig (z.B. `(100 - (-200))^2 = 90000`). Diese riesigen Fehlerwerte 
führen zu extrem großen Gradienten (Anpassungssignalen) während des Backpropagation-Prozesses.

Die Folge (**Exploding Gradients**): Die Gewichte des Netzes werden bei jedem Schritt massiv geändert. Das 
Training wird instabil, die Gewichte können "explodieren" (ins Unendliche wachsen), und das Modell lernt gar nichts.

Wie skaliert man am besten? Es gibt zwei Hauptmethoden: Normalisierung und Standardisierung.

*   Normalisierung (Min-Max-Skalierung im Bereich [0, 1]):
    *   Formel: `skalierter_wert = (wert - min_wert) / (max_wert - min_wert)`
    *   Ergebnis: Alle Werte liegen exakt zwischen 0 und 1.

*   Normalisierung (Min-Max-Skalierung im Bereich [-1, 1]):
    *   Formel: `skalierter_wert = 2 * ((wert - min_wert) / (max_wert - min_wert)) - 1`
    *   Ergebnis: Alle Werte liegen exakt zwischen 1- und 1 (die Daten sind um den Nullpunkt zentriert)

*   Standardisierung (Z-Score-Normalisierung):
    *   Formel: `skalierter_wert = z_score = (wert - mittelwert) / standardabweichung`
    *   Ergebnis: Die skalierten Werte haben einen Mittelwert von 0 und eine Standardabweichung von 1. Die meisten Werte liegen typischerweise zwischen -3 und +3.

Wenn das Histogramm eine lineare oder gleichmäßige Verteilung zeigt, ist die Min-Max-Normalisierung sinnvoll ([0, 1] bei rein positiven Werten, sonst [-1, 1]).
 
Wenn das Histogramm eine Normalverteilung zeigt (Glockenkurve), ist die Z-Score-Standardisierung optimal.

## A4. Aufgabentypen

### A4.1 Klassifikation

**Binary Classification (Binäre Klassifikation):**

Es gibt nur zwei mögliche Klassen, und genau eine muss gewählt werden.
*   Beispiel: Ist diese E-Mail Spam oder kein Spam?
*   Output: 1 Neuron
*   Aktivierungsfunktion: `Sigmoid`. Quetscht den Wert in den Bereich zwischen 0 und 1.
*   Verlustfunktion: `Binary Cross-Entropy (BCE)`. Misst den Fehler (Abstand) des Outputs. Es bestraft das Modell stark, wenn es sich sehr sicher ist, aber falsch liegt (z.B. sagt 0.99 voraus, aber die Wahrheit war 0) und weniger stark, wenn es unsicher ist (sagt 0.6 voraus, Wahrheit war 0).

**Multi-Class Classification (Multi-Klassen-Klassifikation):**

Es gibt mehr als zwei mögliche Klassen, aber es kann immer nur genau eine die richtige sein.
*   Beispiel: Welches Tier ist auf diesem Bild: eine Katze, ein Hund oder ein Vogel?
*   Output: N Neuronen (eines pro Klasse)
*   Aktivierungsfunktion: `Softmax`. Wandelt die Werte in eine Wahrscheinlichkeitsverteilung um, bei der die Summe aller Werte exakt 1 ergibt.
*   Verlustfunktion: `Categorical Cross-Entropy`.

**Multi-Label Classification (Multi-Label-Klassifikation):**

Es gibt N mögliche Klassen (Labels), und ein Datenpunkt kann beliebig viele davon gleichzeitig haben (auch keine).
*   Beispiel: Welche Genres hat dieser Film: Komödie, Action, Romanze, Horror? (Ein Film kann Action UND Komödie sein).
*   Dein Tichu-Problem: Welche Karten gehören zu diesem Spielzug? (Ein Zug kann die Karte S8 UND B8 enthalten).
*   Output: N Neuronen (eines pro Label).
*   Aktivierungsfunktion: `Sigmoid`. Quetscht jeden Wert in den Bereich zwischen 0 und 1.
*   Verlustfunktion: `Binary Cross-Entropy (BCE)`. Misst den Fehler für jeden einzelnen Wert des Outputs und mittelt sie zu einem Gesamtfehler.

### A4.2 Regression

Dem Input wird ein kontinuierlicher numerischer Wert zugeordnet.
*   Beispiel: Preis eines Hauses, Temperatur von morgen, Punktestand in Tichu.
*   Output: Kontinuierlicher Zahlenwert (Float, Skalar).
*   Aktivierungsfunktion: `lineare`
*   Verlustfunktion (hier hat man zwei Optionen):
    * **Mean Squared Error (MSE):** (Standard) Misst den quadratischen Abstand zwischen Vorhersage und Ziel. Er bestraft große Fehler überproportional stark (weil der Fehler quadriert wird). 
    * **Mean Absolute Error (MAE).** Bestraft alle Fehler linear. Ist robuster gegenüber Ausreißern in den Daten.

## A5. Glossar für Deep Learning

*	**Neuronales Netz (NN):** Ein mathematisches Modell, inspiriert vom menschlichen Gehirn, das aus Schichten von "Neuronen" besteht und lernt, Muster in Daten zu erkennen.
*	**Tensor:** Ein mehrdimensionales Array (ein Vektor ist ein 1D-Tensor, eine Matrix ein 2D-Tensor). Der Grundbaustein für alle Daten in DL-Frameworks.
*	**Feature:** Eine einzelne, messbare Eigenschaft der Eingabedaten (z.B. "Anzahl der Karten des Partners").
*	**Training:** Der Prozess, bei dem das NN die Daten "sieht" und seine internen Parameter (Gewichte) anpasst, um bessere Vorhersagen zu machen.
*	**Inferenz:** Der Prozess, bei dem ein bereits trainiertes Modell verwendet wird, um eine Vorhersage für neue, ungesehene Daten zu machen (genau das tut unser NNetAgent.play()).
*   **MLP (Multi-Layer Perceptron):** Ein klassischer Typ von neuronalem Netz, das aus einer Eingabeschicht, einer oder mehreren "versteckten" Schichten (hidden layers) und einer Ausgabeschicht besteht. Die Informationen fließen nur in eine Richtung (von Input zu Output). Es ist ideal für Klassifikations- oder Regressionsprobleme mit tabellarischen oder Vektor-Daten, bei denen keine zeitliche Abhängigkeit besteht.
*   **RNN / LSTM / GRU (Recurrent Neural Network):** Spezialisierte neuronale Netze, die ein "Gedächtnis" besitzen, indem sie Informationen aus vorherigen Zeitschritten in ihre aktuelle Berechnung einbeziehen. Sie sind ideal für Sequenzdaten wie Text, Sprache oder eben die Historie von Spielzügen. LSTM (Long Short-Term Memory) und GRU (Gated Recurrent Unit) sind fortgeschrittene Varianten von RNNs, die besser mit langen Sequenzen umgehen können.
*   **Transformer / Decision Transformer (DT):** Eine modernere, oft leistungsfähigere Architektur für Sequenzdaten, die auf einem "Aufmerksamkeitsmechanismus" (Attention Mechanism) basiert. Sie kann Beziehungen zwischen beliebigen Teilen einer langen Sequenz lernen, nicht nur zwischen benachbarten. Der Decision Transformer ist eine spezielle Variante, die für Reinforcement Learning aus Offline-Daten entwickelt wurde, indem sie zielorientierte Aktionen lernt.
*   **One-Hot Encoding:** Eine Methode, um kategoriale Variablen (bei denen es keine Reihenfolge gibt, z.B. Kartentyp) in einen Vektor umzuwandeln. Für N mögliche Kategorien wird ein Vektor der Länge N erstellt, der nur Nullen enthält, außer an der Position, die die aktive Kategorie repräsentiert – dort steht eine Eins.
*   **Multi-Hot Encoding:** Ähnlich wie One-Hot, aber es können mehrere Einsen im Vektor sein. Wird verwendet, wenn mehrere Kategorien gleichzeitig aktiv sein können. Beispiel: Unser hand_cards-Vektor, bei dem mehrere Karten gleichzeitig vorhanden sein können.
*   **Multi-Hot Vektor:** Dies ist das Ergebnis des Multi-Hot Encodings. Es ist ein Vektor aus Nullen und Einsen, bei dem mehrere Positionen (>= 0) auf 1 gesetzt sein können. Beispiel: Unser hand_cards-Vektor ist ein Multi-Hot-Vektor, weil man mehrere Karten gleichzeitig haben kann. Unser Label-Vektor für einen Spielzug (z.B. eine Straße) ist ebenfalls ein Multi-Hot-Vektor.
*   **Thermometer Encoding (Cumulative Encoding):** Eine Methode, um ordinale Variablen (bei denen es eine klare Reihenfolge gibt, z.B. Kartenanzahl) zu kodieren. Für N mögliche Stufen wird ein Vektor der Länge N-1 erstellt. Für den Wert k werden die ersten k-1 Elemente auf 1 gesetzt, der Rest auf 0.
*   **Markov-Annahme:** Die Annahme, dass der zukünftige Zustand eines Systems nur vom aktuellen Zustand abhängt und nicht von der gesamten Historie, die zu diesem Zustand geführt hat. Unser MLP-Modell trifft diese Annahme, da es keine Historie als Input bekommt.
*   **Skalar (Scalar):** Ein einzelner Zahlenwert (im Gegensatz zu einem Vektor oder einer Matrix). Unser normalisierter trick_points-Wert ist ein Skalar-Feature.
*   **Episode:** In unserem Fall ist eine Episode eine Tichu-Runde. 
*   **Trajektorie (Trajectory):** In Reinforcement Learning und Sequenzmodellierung bezeichnet eine Trajektorie eine **vollständige Sequenz von Zuständen, Aktionen und Belohnungen** von Anfang bis Ende einer Episode. In unserem Fall ist eine Episode eine Tichu-Runde. Eine Trajektorie ist also die komplette, geordnete Aufzeichnung aller Züge und der daraus resultierenden Zustände einer Runde. Beispiel: [(Zustand_1, Aktion_1), (Zustand_2, Aktion_2), ...].
*   **Return-to-Go (RTG):** Bedeutet wörtlich "die Belohnung, die es von jetzt an noch zu holen gibt". Es ist ein abnehmender Wert innerhalb einer Sequenz (einer Runde). Eine Kennzahl, die an jedem Zeitschritt t einer Trajektorie berechnet wird. Sie repräsentiert die **Summe aller zukünftigen Belohnungen (Returns), die ab diesem Zeitpunkt bis zum Ende der Episode noch erzielt werden.** RTG_t = Belohnung_{t+1} + Belohnung_{t+2} + ... + Belohnung_{Ende}. In Tichu wäre die "Belohnung" die Punktzahl, die am Ende der Runde vergeben wird. Der RTG ist also die noch zu erwartende Punktzahl.
*   **Terminal Reward (End-Belohnung):** Ein Konzept im Reinforcement Learning, bei dem eine Belohnung (Reward) nur am Ende einer Episode (in Tichu: am Ende einer Runde) vergeben wird. Für alle Aktionen während der Episode ist die unmittelbare Belohnung null. Dieses Vorgehen ist typisch für Spiele mit klaren Sieg-/Verlustbedingungen (wie Schach, Go oder Tichu), bei denen das Ergebnis erst nach einer ganzen Sequenz von Zügen feststeht. Der Terminal Reward für eine Tichu-Runde ist der finale Punktestand, den ein Team erzielt hat, inklusive aller Boni (Tichu, Doppelsieg) und Mali.
*   **Sparse Reward Problem (Problem der spärlichen Belohnungen):** Eine fundamentale Herausforderung im Reinforcement Learning, die auftritt, wenn Belohnungen nur sehr selten vergeben werden (wie bei einem Terminal Reward). Die KI muss sehr viele Aktionen ausführen, bevor sie ein positives oder negatives Feedback erhält. Dadurch ist es für sie extrem schwierig zu lernen, welche der vielen Aktionen am Anfang der Runde tatsächlich für den Sieg am Ende verantwortlich war. Dies wird auch als "Credit Assignment Problem" (Problem der Verdienstzuweisung) bezeichnet.
*   **Reward Shaping (Belohnungsformung):** Eine fortgeschrittene Technik, um dem "Sparse Reward Problem" entgegenzuwirken. Dabei gibt man der KI zusätzliche, künstliche Zwischen-Belohnungen (Shaped Rewards), um ihr Verhalten in die richtige Richtung zu lenken. In Tichu könnte man der KI eine kleine positive Belohnung für das Gewinnen eines Stichs mit Punkten oder eine kleine negative Belohnung für das Aufbrechen einer Bombe geben. Vorsicht: Falsch implementiertes Reward Shaping kann zu unerwünschtem Verhalten führen, z.B. wenn die KI lernt, gierig Zwischen-Belohnungen zu sammeln, aber dadurch das eigentliche Ziel (die Runde zu gewinnen) aus den Augen verliert. Unser Ansatz, den Return-to-Go mit perfekter Zukunftsinformation aus den Offline-Logs zu berechnen, ist eine sehr elegante und effektive Form des Reward Shaping.
*   **Feature:** Eine einzelne, quantifizierbare Eigenschaft des Spielzustands, die dem neuronalen Netz als Input dient. Ein Feature ist eine "Zahl", die einen Aspekt des Spiels beschreibt. Beispiel: Die Anzahl der Handkarten des Partners (z.B. 10) oder ein Flag, ob der Wunsch aktiv ist (1).
*   **Feature-Vektor:** Ein geordnetes Array (oder Vektor) von Zahlen, das den gesamten Spielzustand zu einem bestimmten Zeitpunkt repräsentiert. Es ist die Sammlung aller Features, die das neuronale Netz "sieht", um eine Entscheidung zu treffen. Beispiel: Unser 360-dimensionaler Vektor, der alles von den Handkarten bis zum Punktestand kodiert.
*   **Label:** Die "richtige Antwort" oder das Ziel, das das neuronale Netz während des Trainings lernen soll. In unserem Fall ist das Label die Aktion, die ein menschlicher Spieler in einer bestimmten Situation ausgeführt hat. Beispiel: "Spiele das Paar Achten" oder "Passe".
*   **Label-Vektor:** Die numerische Repräsentation des Labels. Da ein neuronales Netz nur mit Zahlen arbeiten kann, wandeln wir die Aktion (das Label) in einen Vektor um, den das Netz vorhersagen kann. Beispiel: Unser 57-dimensionaler Vektor, bei dem zwei Positionen für die Achten auf 1 gesetzt sind.
*   **Empirie / empirisch**: Bezieht sich auf Erkenntnisse, die durch Beobachtung und Experimente gewonnen werden.
*   **Heuristik:** Bezeichnet eine erfahrungsbasierte Methode zur schnellen Lösungsfindung, die mit begrenztem Wissen arbeitet und nicht zwingend zur optimalen, aber oft zu einer praktikablen Lösung führt.
*   **Daten-Augmentierung (engl. Data Augmentation):** Ist eine Technik, bei der vorhandene Daten künstlich erweitert werden.
*   **Supervised Learning (überwachtes Lernen):** Ist ein Verfahren des maschinellen Lernens, bei dem ein Modell anhand von gelabelten Trainingsdaten lernt, also Daten, bei denen die korrekte Ausgabe bereits bekannt ist. Ziel ist es, eine Funktion zu entwickeln, die auch bei neuen, unbekannten Eingaben verlässliche Vorhersagen trifft. Typische Anwendungen sind Klassifikation (z.B. Spam-Erkennung) und Regression (z.B. Preisprognosen).
*   **Reinforcement Learning (verstärkendes Lernen):** Ist ein Lernansatz, bei dem ein Agent durch Interaktion mit einer Umgebung lernt, Handlungen zu optimieren, um eine möglichst hohe Belohnung zu erzielen. Statt gelabelter Daten erhält der Agent Feedback in Form von Belohnung oder Bestrafung und verbessert sein Verhalten durch Trial-and-Error. Typische Einsatzbereiche sind Robotik, Spielstrategien und autonome Systeme.
*   **Online-Lernen (Online Learning):** Beim Online-Lernen werden die Gewichte des neuronalen Netzes fortlaufend angepasst, während neue Daten eintreffen. Das Modell lernt inkrementell, also Schritt für Schritt – typischerweise nach jedem einzelnen Datenpunkt oder Mini-Batch.
*   **Offline-Lernen (Offline Learning):** Offline-Lernen bedeutet, dass das neuronale Netz auf einem festen, vollständigen Datensatz trainiert wird. Das Training erfolgt in mehreren Durchläufen (Epochen), wobei die Gewichte nicht während des Datenflusses, sondern nachträglich angepasst werden. 
*   **Policy Network:** (Policy - engl. Strategie) Ist ein neuronales Netz, das entscheidet, welche Aktion ein Agent in einem bestimmten Zustand ausführen sollte. 
*   **Value Network:** Ist ein neuronales Netz, das bewertet, wie gut ein Zustand ist – also den erwarteten zukünftigen Belohnungswert.
*   **Goal-conditioned Policy:** Eine Strategie, die das Ziel berücksichtigt.
