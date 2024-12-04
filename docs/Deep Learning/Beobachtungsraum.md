Beobachtungsraum  (Observation Space)
=====================================

## Identification
<pre>
world_name: str					                    # Betitelt die Welt
canonical_chair: int				                # Sitzplatznummer in der Normalform (zw. 0 und 3)
</pre>

## Private State
<pre>
possible_actions: list[Action] = []                 # Mögliche Aktionen
hand = CardCollection()  						    # Handkarten (Anzahl: zw. 0 und 14)
outgoing_schupfed_cards = CardCollection())  	    # Drei abgelegte Tauschkarten (für den rechten Gegner, für den Partner, für den linker Gegner)
incoming_schupfed_cards = CardCollection()  	    # Drei erhaltene Tauschkarten (vom rechter Gegner, vom Partner, vom linker Gegner)
</pre>

## Public State Properties
<pre>
for player in players:                              # Alle Spieler (ich, rechter Gegner, Partner, linker Gegner)
    nickname: str = nickname.strip()  	            # Name des Spielers
    declaration: int = -1 	                        # Tichu-Ansage des Spielers (-1 == noch keine Entscheidung für großes Tichu, 0 == keine Ansage, 1 == kleines Tichu, 2 == großes Tichu)
    number_of_cards: int = 0	                    # Anzahl der Handkarten des Spielers
    has_schupfed: bool = False		                # Spieler hat Tauschkarten abgegeben
    points: int = 0 		                        # Punkte, die der Spieler kassiert hat (zw. -25 und 125)
start_chair: int = -1 					            # Spieler, der den Mah Jong hat oder hatte (-1, falls das Schupfen noch nicht beendet ist, sonst zw. 0 und 3)
current_chair: int = -1  						    # Spieler der am Zug ist (-1 == niemand, ansonsten zw. 0 und 3)
wish: int = -1  								    # Unerfüllter Wunsch (-1 == kein Wunsch geäußert, 0 == wunschlos, -14 bis -2 bereits erfüllt, ansonsten ein Kartenwert zw. 2 und 14)
gift_recipient: int = -1 				            # Spieler, der den Drachen bekommen hat (-1 == niemand, ansonsten zw. 0 und 3)
for turns in trick:                                 # Offener Stich (alle Spielzüge des Stichs in Unterlisten gruppiert)
    for turn in turns:                              # Unterliste der Spielzüge (beinhaltet ein Karten-Zug und sofern vorhanden die darauf folgenden Pass-Züge) 
        self._chair: int = chair                    # Spieler, der am Zug war (zwischen 0 und 3)
        self._combination: CardCombination          # Abgelegte Kartenkombination (Anzahl zwischen 0 und 14 Karten) 
hidden_cards: CardCollection: 	                    # Noch nicht gespielte Karten ohne die eigenen Handkarten, also Handkarten der Mitspieler (Anzahl zw. 1 und 56)
winner: int 						                # Ermittelt den Spieler, der zuerst fertig wurde (-1 == alle Spieler sind noch dabei, ansonsten zw. 0 und 3)
loser: int 						                    # Ermittelt den Spieler, der als Letzter Handkarten hat (oder bei Doppelsieg das Team, das verloren hat) (-1 == Spiel läuft noch, 20 == Spieler 0 und 2 haben verloren, 31 == Spieler 1 und 3 haben verloren, ansonsten zw. 0 und 3)
score: list[tuple[int, int]] = []  					# Ergebnis (Team 20, Team 31) jeder Runde (pro Ergebnis pro Team: zw. -425 und 400, max. Differenz pro Runde: 800 (*)

(*)
Min: nur den Phönix kassiert (-25) + Ich großes Tichu verloren (-200) + Partner großes Tichu verloren (-200) 
Max: Doppelsieg gewonnen (200) + Ich oder Partner großes Tichu gewonnen (200)
Max. Differenz pro Runde: Doppelsieg gewonnen (200) + Ich oder Partner großes Tichu gewonnen (200) + Gegner zweimal großes Tichu verloren (200 x 2)
</pre>

Redundant, und wurde daher aus dem Beobachtungsraum entfernt:
is_running == Action.START not in possible_actions 	            # Partie läuft (wurde gestartet und noch kein Game Over)
is_round_over == loser >= 0 					                # Runde beendet
is_game_over == any(total >= 1000 for total in score.total())	# Partie beendet


Aktionsraum
===========
<pre>
NONE                                    # der Spieler darf nichts machen
START                         			# der Spieler möchte die Partie starten
GRAND(decision: bool)   			    # der Spieler möchte ein Großes Tichu ansagen bzw. ablehnen
TICHU   			                    # der Spieler möchte Tichu ansagen
SCHUPF(cards: CardCollection) 			# der Spieler möchte Tauschkarten ablegen
WISH(wish: int)               			# der Spieler möchte sich ein Kartenwert wünschen
GIFT(recipient: int)          			# der Spieler möchte den Drachen verschenken
PLAY(combination: CardCombination)  	# der Spieler möchte Karten spielen
PASS                          			# der Spieler möchte passen
BOMB                          			# der Spieler möchte eine Bombe werfen
</pre>


Spielereignisse (Events)
========================
<pre>
ERROR(message: String)        			# der Spieler hat ein Fehler gemacht (wird nur an dem betroffenen Spieler übermittelt)
PLAYER_JOINED(chair: int)     			# ein Client hat sich an den Tisch gesetzt (oder ein Agent hat den Platz eingenommen)
GAME_STARTED                  			# die Partie wurde gestartet (ein Spieler hat auf Start geklickt)
CARDS_DEALT                   			# Karten wurden ausgeteilt
PLAYER_DECLARED(chair: int)             # ein Spieler hat ein großes Tichu angesagt bzw. abgelehnt oder ein normales Tichu angesagt
PLAYER_SCHUPFED(chair: int)   			# ein Spieler hat Tauschkarten abgelegt
SCHUPF_DISTRIBUTED                      # die Tauschkarten wurden verteilt
CARD_WISHED                  			# ein Kartenwert wurde sich gewünscht
WISH_FULFILLED                			# der Wunsch wurde erfüllt
DRAGON_GIVEN_AWAY             			# der Drache wurde verschenkt
PLAYER_PLAYED(chair: int)     			# ein Spieler hat Karten ausgespielt
PLAYER_PASSED(chair: int)     			# ein Spieler hat gepasst
BOMB_PENDING                  			# ausstehende Bombe
PLAYER_TOOK(chair: int) 			    # ein Spieler hat den Stich kassiert
ROUND_OVER                    			# die Runde ist beendet
GAME_OVER                     			# die Partie wurde beendet
</pre>


