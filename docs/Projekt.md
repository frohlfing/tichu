# Verzeichnisstruktur

Diese Struktur trennt klar zwischen:

- Skripten zur Ausführung (bin/)
- Generierten Daten (data/)
- Dokumentation (docs/)
- Proof of Concept (poc/)
- Quellcode (src/)
- Tests (tests/)
- Frontend (web/)

<pre>
└── tichu/
    ├── .idea
    ├── .venv
    ├── bin/                    # ausführbare Skripte und Dateien
    │   ├── run_arena.py
    │   ├── run_server.py
    │   ├── download_bw_logs.py
    │   └── process_bw_logs.py
    ├── data/                   # alle generierten Daten (von Git ignoriert!)
    │   ├── bw/                 # Daten von Brettspielwelt
    │   │   ├── tichulog
    │   │   │   ├── 2007.zip
    │   │   │   └── 2022.zip
    │   │   └── Logs_runterladen.ipynb
    │   ├── cov/                # Coverage-Daten
    │   │   ├── .coverage
    │   │   ├── coverage.xml
    │   │   └── htmlcov/
    │   │       └── index.html
    │   ├── db/                 # Datenbanken
    │   │   └── tichu.sqlite
    │   ├── logs/               # Logdateien
    │   │   ├── app.log
    │   │   └── app.log.2025-07
    │   ├── models/             # Trainierte Modelle, Caches, Tabellen
    │   │   └── prob_tables/
    │   │   └── prob            # Hilfstabellen für das `src/lib/prob`-Pakage
    │   │       └── bomb04_hi.pkl.gz
    │   │       └── triple_lo.pkl.gz
    │   └── reports/
    ├── docs/
    │   ├── benchmark.txt
    │   ├── Technische_Dokumentation.md
    │   ├── Todos.md
    │   ├── Zustandsänderung bei Ereignis.xlsx
    │   ├── .gitkeep
    │   └── assets.py           # statische Assets (z.B. Bilder) für die Dokumentation
    │       └── coverage.svg
    ├── poc/                    # Proof of Concept
    │   ├── benchmark.py
    │   ├── poc_interrupt.py
    │   ├── poc_pickling.py
    │   └── arena_sync/
    │       └── main.py
    ├── src/                    # Top-Level Python-Package
    │   ├── common/
    │   │   ├── git_utils.py
    │   │   ├── logger.py
    │   │   └── rand.py
    │   ├── lib/
    │   │   ├── cards.py
    │   │   ├── combinations.py
    │   │   ├── errors.py
    │   │   ├── partitions.py
    │   │   └── prob/
    │   │       ├── prob_hi.py
    │   │       ├── prob_lo.py
    │   │       ├── statistic.py
    │   │       ├── tables_hi.py
    │   │       └── tables_lo.py
    │   ├── players/
    │   │   ├── agent.py
    │   │   ├── heuristic_agent.py
    │   │   ├── peer.py
    │   │   ├── player.py
    │   │   └── random_agent.py
    │   ├── __init__.py
    │   ├── arena.py
    │   ├── server.py
    │   ├── config.py
    │   ├── game_engine.py
    │   ├── game_factory.py
    │   ├── private_state.py
    │   └── public_state.py
    ├── tests/
    │   ├── common/
    │   │   ├── test_git_utils.py
    │   │   ├── test_logger.py
    │   │   └── test_rand.py
    │   ├── lib/
    │   │   ├── test_cards.py
    │   │   └── test_combinations.py
    │   ├── players/
    │   │   ├── test_agent.py
    │   │   ├── test_player.py
    │   │   └── test_random_agent.py
    │   ├── prob/
    │   │   ├── test_prob_hi.py
    │   │   └── test_prob_lo.py
    │   ├── src/
    │   │   ├── test_arena.py
    │   │   ├── test_game_engine.py
    │   │   ├── test_private_state.py
    │   │   └── test_public_state.py
    │   └── conftest.py
    ├── web/                    # Frontend
    │   ├── css/
    │   │   ├── animation.css
    │   │   ├── common.css
    │   │   ├── loading-view.css
    │   │   ├── lobby-view.css
    │   │   ├── login-view.css
    │   │   ├── modal.css
    │   │   ├── table-view.css
    │   │   └── test.css
    │   ├── fonts/
    │   │   └── architect-s-daughter/
    │   │       ├── Architects Daughter SIL OFL Font License.txt
    │   │       ├── ArchitectsDaughter.ttf
    │   │       ├── ArchitectsDaughter.ttf.import
    │   │       └── ArchitectsDaughter32.tres
    │   ├── images/
    │   │   ├── background.png/
    │   │   ├── bomb-icon.png
    │   │   ├── grand-tichu-icon.png
    │   │   ├── icon.png
    │   │   ├── logo.png
    │   │   ├── spinner.png
    │   │   ├── table-texture.png
    │   │   ├── tichu-icon.png
    │   │   └── wish-icon.png
    │   ├── js/
    │   │   └── views/
    │   │   │   ├── loading-view.js
    │   │   │   ├── lobby-view.js
    │   │   │   ├── login-view.js
    │   │   │   └── table-view.js
    │   │   ├── animation.js
    │   │   ├── app-controller.js
    │   │   ├── bot.js
    │   │   ├── config.js
    │   │   ├── event-bus.js
    │   │   ├── lib.js
    │   │   ├── main.js
    │   │   ├── modal.js
    │   │   ├── network.js
    │   │   ├── random.js
    │   │   ├── sound.js
    │   │   ├── state.js
    │   │   ├── test-runner.js
    │   │   ├── tests.js
    │   │   ├── user.js
    │   │   └── view-manager.js
    │   └── sounds/
    │   │   ├── announce.ogg
    │   │   ├── bomb.ogg
    │   │   ├── play0.ogg
    │   │   ├── play1.ogg
    │   │   ├── play2.ogg
    │   │   ├── play3.ogg
    │   │   ├── schupf.ogg
    │   │   ├── score.ogg
    │   │   ├── select.ogg
    │   │   ├── shuffle.ogg
    │   │   └── take.ogg
    │   ├── index.html
    │   └── tests.html
    ├── .env
    ├── .env.example
    ├── .gitignore               
    ├── cov.ps1
    ├── LICENSE
    ├── pyproject.toml          # Projekt-Setup
    ├── pytest.ini
    └── README.md
</pre>
