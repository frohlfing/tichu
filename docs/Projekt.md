https://gitingest.com/frohlfing/tichu

# Directory structure

## Neu

Diese Struktur ist skalierbar, folgt etablierten Konventionen und trennt klar zwischen:

- Quellcode (tichu_engine/)
- Skripten zur Ausführung (scripts/)
- Generierten Daten & Artefakten (data/)
- Tests (tests/)
- Frontend (web/)

<pre>
└── frohlfing-tichu/
    ├── .gitignore              # Ignoriert .venv, __pycache__, data/, cov/ (außer .svg), etc.
    ├── data/                   # (Von Git ignoriert) Für alle generierten Daten.
    │   ├── db/                 # Datenbanken
    │   │   └── tichu.sqlite
    │   ├── logs/               # Logdateien
    │   │   ├── app.log
    │   │   └── bw_raw/         # Rohe Logdaten von Brettspielwelt
    │   ├── models/             # Trainierte Modelle, Caches, Tabellen
    │   │   └── prob_tables/
    │   └── reports/            # Generierte Analyse-Reports
    ├── docs/
    ├── poc/
    ├── scripts/                # Ausführbare Skripte
    │   ├── run_arena.py
    │   ├── run_server.py
    │   ├── download_bw_logs.py
    │   └── process_bw_logs.py
    ├── tichu_engine/           # Das installierbare Python-Paket (ehemals 'src')
    │   ├── __init__.py
    │   ├── arena.py
    │   ├── config.py
    │   ├── server.py
    │   ├── common/
    │   ├── lib/
    │   └── players/
    ├── tests/
    ├── web/
    ├── pyproject.toml          # Definiert das 'tichu_engine' Paket
    ├── README.md
    └── ...                     # Andere Root-Dateien
</pre>

## Bisher

<pre>
└── frohlfing-tichu/
    ├── .idea
    ├── .venv
    ├── README.md
    ├── config.py
    ├── cov.ps1
    ├── LICENSE
    ├── main.py
    ├── pytest.ini
    ├── requirements.txt
    ├── server.py
    ├── wsclient.py
    ├── .coveragerc
    ├── .env.example
    ├── bin/
    ├── bw/
    │   ├── tichulog
    │   │   ├── 2007.zip
    │   │   ├── 2008.zip
    │   │   ├── 2009.zip
    │   │   └── 2022.zip
    │   └── Logs_runterladen.ipynb
    ├── cov/
    │   ├── htmlcov
    │   │   └── index.html
    │   ├── .coverage
    │   ├── coverage.svg
    │   └── coverage.xml
    ├── data/
    │   └── lib
    │       └── prob
    │           └── bomb04_hi.pkl.gz
    │           └── single_hi.pkl.gz
    │           └── stair08_lo.pkl.gz
    │           └── triple_lo.pkl.gz
    ├── docs/
    │   ├── benchmark.txt
    │   ├── Technische_Dokumentation.md
    │   ├── Todos.md
    │   ├── Zustandsänderung bei Ereignis.xlsx
    │   ├── .gitkeep
    ├── poc/
    │   ├── benchmark.py
    │   ├── poc_interrupt.py
    │   ├── poc_pickling.py
    │   └── arena_sync/
    │       ├── agent.py
    │       ├── arena.py
    │       ├── engine.py
    │       ├── main.py
    │       └── state.py
    ├── src/
    │   ├── arena.py
    │   ├── game_engine.py
    │   ├── game_factory.py
    │   ├── private_state.py
    │   ├── public_state.py
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
    │   └── players/
    │       ├── agent.py
    │       ├── heuristic_agent.py
    │       ├── peer.py
    │       ├── player.py
    │       └── random_agent.py
    ├── tests/
    │   ├── conftest.py
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
    │   └── src/
    │       ├── test_arena.py
    │       ├── test_game_engine.py
    │       ├── test_private_state.py
    │       └── test_public_state.py
    └── web/
        ├── index.html
        ├── tests.html
        ├── css/
        │   ├── animation.css
        │   ├── common.css
        │   ├── loading-view.css
        │   ├── lobby-view.css
        │   ├── login-view.css
        │   ├── modal.css
        │   ├── table-view.css
        │   └── test.css
        ├── fonts/
        │   └── architect-s-daughter/
        │       ├── Architects Daughter SIL OFL Font License.txt
        │       ├── ArchitectsDaughter.ttf
        │       ├── ArchitectsDaughter.ttf.import
        │       └── ArchitectsDaughter32.tres
        ├── images/
        │   ├── background.png/
        │   ├── bomb-icon.png
        │   ├── grand-tichu-icon.png
        │   ├── icon.png
        │   ├── logo.png
        │   ├── spinner.png
        │   ├── table-texture.png
        │   ├── tichu-icon.png
        │   └── wish-icon.png
        ├── js/
        │   ├── animation.js
        │   ├── app-controller.js
        │   ├── bot.js
        │   ├── config.js
        │   ├── event-bus.js
        │   ├── lib.js
        │   ├── main.js
        │   ├── modal.js
        │   ├── network.js
        │   ├── random.js
        │   ├── sound.js
        │   ├── state.js
        │   ├── test-runner.js
        │   ├── tests.js
        │   ├── user.js
        │   ├── view-manager.js
        │   └── views/
        │       ├── loading-view.js
        │       ├── lobby-view.js
        │       ├── login-view.js
        │       └── table-view.js
        └── sounds/
            ├── announce.ogg
            ├── bomb.ogg
            ├── play0.ogg
            ├── play1.ogg
            ├── play2.ogg
            ├── play3.ogg
            ├── schupf.ogg
            ├── score.ogg
            ├── select.ogg
            ├── shuffle.ogg
            └── take.ogg
</pre>