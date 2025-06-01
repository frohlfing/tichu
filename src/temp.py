# class GameEngine:
# ...

async def _resolve_interrupt_and_continue(self, interrupted_player_index: Optional[int] = None) -> bool:
    """
    Prüft alle Spieler auf gepufferte Interrupt-Aktionen (Tichu, Bombe),
    verarbeitet die erste valide, priorisierte Aktion und gibt True zurück,
    wenn eine Interrupt-Aktion verarbeitet wurde (was oft ein 'continue' in der Hauptschleife erfordert).
    Gibt False zurück, wenn kein Interrupt verarbeitet wurde.

    :param interrupted_player_index: Index des Spielers, dessen Aktion gerade unterbrochen wurde (optional).
    :return: True, wenn ein Interrupt verarbeitet wurde, sonst False.
    """
    logger.debug(f"[{self.table_name}] Auflösung von Interrupts gestartet.")
    action_taken = False

    # Priorisierung: Bomben vor Tichu-Ansagen (typische Tichu-Regel)

    # 1. Bomben prüfen (in zufälliger Reihenfolge für Fairness bei mehreren Bomben)
    shuffled_player_indices = list(range(4))
    self._random.shuffle(shuffled_player_indices)

    highest_bomb_played: Optional[Tuple[Player, Cards, Combination]] = None

    for p_idx in shuffled_player_indices:
        player = self._players[p_idx]
        # Agenten entscheiden direkt, Peers schauen in ihren Puffer
        bomb_action = await player.bomb()  # Diese Methode muss in Peer/Agent implementiert sein
        # Peer.bomb() prüft self._pending_bomb
        # Agent.bomb() entscheidet aktiv
        if bomb_action:
            bomb_cards, bomb_combination = bomb_action
            # FINALE Validierung durch die Engine (auch wenn Peer/Agent schon validiert haben)
            # Ist es eine valide Bombe? Sticht sie den aktuellen Stich (falls einer da ist)?
            # Ist sie höher als eine ggf. schon in diesem Zyklus gefundene Bombe?
            # (Diese Logik braucht Details zum aktuellen Stich etc.)

            # Beispielhafte Validierung (muss verfeinert werden):
            # Annahme: _validate_bomb(player, bomb_cards, bomb_combination) prüft alles
            # und berücksichtigt ggf. highest_bomb_played
            if self._is_bomb_playable_now(player, bomb_cards, bomb_combination, highest_bomb_played):
                if highest_bomb_played is None or bomb_combination[2] > highest_bomb_played[2][2]:  # Rank-Vergleich
                    highest_bomb_played = (player, bomb_cards, bomb_combination)
                    logger.info(f"[{self.table_name}] Spieler {player.name} hat eine potenziell spielbare Bombe: {bomb_cards}")

    if highest_bomb_played:
        interrupter, bomb_cards, bomb_combination = highest_bomb_played
        logger.info(f"[{self.table_name}] Verarbeite Bombe von Spieler {interrupter.name}: {bomb_cards}")

        # Bombe im PublicState spielen
        self._public_state.current_turn_index = interrupter.priv.player_index  # Interrupter ist dran
        # Alte Stichinfo clearen, da Bombe immer neuen Stich beginnt (oder alten beendet)
        self._public_state.trick_owner_index = -1
        self._public_state.trick_combination = (CombinationType.PASS, 0, 0)
        self._public_state.trick_points = 0

        # Logik aus self.play_pub (oder eine ähnliche Methode) hier anwenden:
        # pub.tricks.append(...)
        # pub.trick_owner_index = interrupter.priv.player_index
        # pub.trick_combination = bomb_combination
        # pub.trick_points += sum_card_points(bomb_cards)
        # pub.played_cards += bomb_cards
        # pub.count_hand_cards[interrupter.priv.player_index] -= len(bomb_cards)
        # privs[interrupter.priv.player_index].hand_cards = ...
        # (Diese Logik sollte in eine Hilfsmethode ausgelagert werden, die auch für normale Züge gilt)
        self._apply_played_combination(interrupter, bomb_cards, bomb_combination)

        await self._broadcast("bombed", {"player_index": interrupter.priv.player_index, "cards": stringify_cards(bomb_cards)})
        action_taken = True
        # Das interrupt_event wurde bereits vom _ask des unterbrochenen Spielers gecleart.
        # Hier muss es NICHT erneut gecleart werden.

    # 2. Wenn keine Bombe gespielt wurde, Tichu-Ansagen prüfen (falls relevant für die aktuelle Spielphase)
    if not action_taken and self._public_state.current_phase in ["schupfing", "playing_first_card_of_round"]:  # Nur in bestimmten Phasen
        # (Reihenfolge der Abfrage für Tichu ist weniger kritisch als bei Bomben,
        # aber zufällig ist auch hier fair, wenn mehrere gleichzeitig wollen)
        # self._random.shuffle(shuffled_player_indices) # Kann man machen
        for p_idx in shuffled_player_indices:
            player = self._players[p_idx]
            # Agenten entscheiden direkt, Peers schauen in ihren Puffer
            # player.announce_tichu() prüft _pending_announce oder Agent-Logik
            # Wichtig: Diese Methode sollte nur für "normales Tichu" sein, nicht Grand Tichu.
            # Grand Tichu hat seine eigene Phase.
            if self._can_player_announce_tichu_now(player):  # Zusätzliche Engine-Prüfung
                if await player.announce_tichu():  # Peer.announce_tichu() gibt gepufferten Wert zurück
                    self._public_state.announcements[player.priv.player_index] = 1
                    await self._broadcast("tichu_announced", {"player_index": player.priv.player_index})
                    action_taken = True
                    # Normalerweise kann nur ein Tichu pro Team, oder ein Spieler, der noch nicht dran war.
                    # Wenn ein Tichu angesagt wurde, könnten wir hier brechen, oder alle prüfen lassen,
                    # und die Logik _can_player_announce_tichu_now würde weitere verhindern.
                    break  # Nur eine Tichu-Ansage pro Interrupt-Auflösung

    if action_taken:
        logger.info(f"[{self.table_name}] Interrupt-Aktion verarbeitet.")
    else:
        logger.debug(f"[{self.table_name}] Keine Interrupt-Aktion in diesem Zyklus verarbeitet.")

    return action_taken


async def run_game_loop(self, break_time=5) -> Optional[PublicState]:
    # ... (Initialisierungen wie gehabt) ...
    try:
        while not pub.is_game_over:
            # ... (Runden-Setup, Karten austeilen, Grand Tichu) ...

            # --- Schupfen ---
            # a) Tauschkarten abgeben
            for i in range(0, 4):
                player_index_schupf = (first + i) % 4
                player_schupf = self._players[player_index_schupf]
                priv_schupf = privs[player_index_schupf]

                action_interrupted = False
                try:
                    # HIER: Interrupt-Fenster VOR dem Schupfen des Spielers öffnen
                    if await self._resolve_interrupt_and_continue():
                        # Ein Interrupt wurde verarbeitet (z.B. Tichu angesagt).
                        # Die Schupf-Phase muss möglicherweise neu bewertet werden oder
                        # der aktuelle Spieler ist jetzt ein anderer.
                        # Ein 'continue' zur äußeren while not pub.is_game_over Schleife
                        # ist hier wahrscheinlich zu grob. Wir müssen die Schupf-Logik
                        # für den *aktuellen* Spieler player_index_schupf erneut versuchen,
                        # oder die Schupf-Runde von vorne beginnen, wenn sich der Zustand stark geändert hat.
                        # Fürs Erste: Einfach die Aktion des Spielers erneut versuchen.
                        # Dies ist komplex, da der Interrupt den game state ändern kann.
                        # TODO: Raffinierteres Handling hier.
                        action_interrupted = True  # Markieren, dass wir die Aktion wiederholen müssen
                        # oder die Schupf-Schleife neu starten
                        # continue # Zurück zum Anfang der `for i in range(0,4)` Schleife für Schupfen?

                    if not action_interrupted:
                        priv_schupf.given_schupf_cards = await player_schupf.schupf()  # interruptable = True in Peer._ask

                except PlayerInterruptError:
                    logger.info(f"[{self.table_name}] Schupf-Aktion von Spieler {player_schupf.name} unterbrochen.")
                    action_interrupted = True  # Wichtig für die Logik unten

                if action_interrupted:
                    # Interrupt wurde gefangen und vom _ask des Spielers signalisiert.
                    # Jetzt die _resolve_interrupt_and_continue aufrufen, um die Ursache zu behandeln.
                    if await self._resolve_interrupt_and_continue(interrupted_player_index=player_index_schupf):
                        # Ein Interrupt wurde verarbeitet. Die Schupf-Logik muss ggf. von vorne für den
                        # unterbrochenen Spieler beginnen oder für alle.
                        # TODO: Hier genaue Logik, wie nach einem Interrupt im Schupfen fortgefahren wird.
                        # Fürs Erste: Wir könnten die aktuelle Iteration überspringen und hoffen,
                        # dass der nächste _resolve_interrupt_and_continue es fängt, oder die Schupf-Schleife neu starten.
                        # Am einfachsten ist oft, die aktuelle Aktion für den Spieler zu wiederholen,
                        # nachdem der Interrupt-Status (z.B. Tichu-Ansage) aktualisiert wurde.
                        # Wir müssen die for-Schleife hier evtl. mit einer while-Schleife umbauen,
                        # um den Index i nicht einfach weiterzuzählen.
                        # Für diesen Versuch: Wir wiederholen die Aktion für den Spieler
                        i -= 1  # Index dekrementieren, um den aktuellen Spieler nochmal zu fragen. VORSICHT: Unsauber.
                        continue  # Zurück zum Anfang der for-Schleife
                    else:
                        # Interrupt-Event wurde ausgelöst, aber kein Spieler hat eine Aktion angeboten.
                        # Das sollte selten sein. Aktion des Spielers trotzdem wiederholen.
                        i -= 1
                        continue

                # ... (Rest der Schupf-Logik: Karten annehmen, wenn alle Spieler geschupft haben) ...
                # Dieser Teil (asserts, count_hand_cards setzen) kommt erst, nachdem der Spieler erfolgreich geschupft hat.
                assert len(priv_schupf.given_schupf_cards) == 3
                # ... etc. ...

            # b) Tauschkarten aufnehmen (erst nachdem ALLE Spieler ihre Karten abgegeben haben)
            # ...

            # --- Hauptspiel-Loop ---
            while not pub.is_round_over:
                # ... (Spieler am Zug bestimmen, etc.) ...
                current_player_obj = self._players[pub.current_turn_index]
                current_priv_state = privs[pub.current_turn_index]

                # HIER: Interrupt-Fenster VOR dem Zug des Spielers öffnen
                if await self._resolve_interrupt_and_continue():
                    # Ein Interrupt (Bombe, Tichu) wurde verarbeitet.
                    # pub.current_turn_index könnte sich geändert haben.
                    # Die Schleife wird mit 'continue' neu gestartet, um den korrekten Spieler zu nehmen.
                    continue  # Zurück zum Anfang der `while not pub.is_round_over`-Schleife

                # ... (Logik für Stich abräumen, falls der Spieler dran ist und darf) ...

                if pub.count_hand_cards[pub.current_turn_index] > 0:
                    action_interrupted_play = False
                    try:
                        cards, combination = await current_player_obj.play()  # interruptable = True in Peer._ask
                    except PlayerInterruptError:
                        logger.info(f"[{self.table_name}] Play-Aktion von Spieler {current_player_obj.name} unterbrochen.")
                        action_interrupted_play = True

                    if action_interrupted_play:
                        # Interrupt wurde vom _ask des Spielers signalisiert.
                        # Jetzt die Ursache auflösen. _resolve_interrupt_and_continue wird am Anfang der
                        # nächsten while-Schleifeniteration aufgerufen.
                        continue  # Zurück zum Anfang der `while not pub.is_round_over`-Schleife

                    # ... (Logik zum Verarbeiten von cards, combination) ...

                # ... (Nächster Spieler, etc.) ...

    # ... (Rest der run_game_loop mit Exception Handling) ...