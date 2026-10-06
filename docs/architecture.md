# Architecture

## Scope

Playlist Emotion Studio V1.6.1 intentionally preserves the existing application architecture. This release is a GitHub/portfolio cleanup, not a full refactor. The main application remains in `playlist_emotion_studio.py` so functional behavior is not destabilized by unnecessary module moves.

## Runtime Layout

- `playlist_emotion_studio.py` — application entry point, UI, persistence layer and service clients.
- `data/playlist.db` — sanitized SQLite baseline and local runtime persistence.
- `data/generos_curados_v130.csv` — curated genre mapping consumed by the migration/genre workflow.
- `data/genre_catalog_musicbrainz.txt` — local genre/style catalog used by searchable genre controls.
- `data/starmaker_seed_v141.json` — local StarMaker public-data seed used by the existing migration path when applicable.
- `INICIAR.bat` — Windows launcher using `py -3` when available and falling back to `python`.

## UI

The interface is implemented with Tkinter/ttk. `App` owns the application window, SQLite `Database` instance, sidebar navigation and lazy creation of the main views.

Main views currently include:

- Dashboard (`DashboardView`)
- Library (`LibraryView`)
- Positive / Neutral / Negative emotion views (`EmotionView`)
- Show/playlist planner (`SetlistView`)
- StarMaker workspace (`StarMakerView`)
- Platform metadata workspace (`PlatformsView`)
- Settings (`SettingsView`)

Reusable controls include the scroll surface, searchable comboboxes, styled buttons and modal dialogs for song editing, genre research, level transfer and YouTube candidate selection.

## Persistence

`Database` wraps a local SQLite connection with foreign keys enabled. The schema stores:

- songs and emotional metadata;
- setlists and setlist items;
- show-performance metadata;
- StarMaker matches, snapshots, scan state and logs;
- local settings and integration credentials/tokens after the user configures them.

The public V1.6.1 database is sanitized: operational tables are empty and credential fields are blank. Historical migration methods are retained because they are part of the established schema evolution path.

## Service Layer

External integrations are implemented as client classes inside the main module:

- `MusicBrainzGenreClient`
- `StarMakerDirectAPIClient`
- `StarMakerPublicClient`
- `StarMakerWebDiscoveryClient`
- `StarMakerNativeSearchClient`
- `StarMakerHeadlessBrowserClient`
- `YouTubeClient`
- `SpotifyClient`

The current StarMaker UI primarily calls `StarMakerDirectAPIClient`. Older public-web/headless components remain in the codebase as legacy/fallback infrastructure because references still exist and this cleanup deliberately avoids risky code removal.

## General Flow

1. `main()` initializes Windows DPI awareness and creates `App`.
2. `App` opens the SQLite database and applies idempotent historical schema migrations.
3. The dashboard is shown first; other views are created when selected.
4. User actions read/write SQLite synchronously or launch network work in background threads where implemented.
5. External platform metadata is normalized and persisted locally.
6. The application closes the database connection through `App.on_close()`.

## Future Modularization

A future release can safely split the current file into packages such as `ui`, `services`, `models` and `persistence`, but that should be performed with automated regression tests and is intentionally outside the scope of V1.6.1.
