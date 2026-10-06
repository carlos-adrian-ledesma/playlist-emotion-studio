# Playlist Emotion Studio

Desktop music catalog, emotional metadata, show-planning and platform analytics application built with Python. It is designed to organize songs, classify emotional metadata, manage playlists/setlists, and enrich a local catalog with public metadata from external music platforms.

**Current release:** Playlist Emotion Studio V1.6.1 — GitHub & Portfolio Cleanup.

## Overview

Playlist Emotion Studio is a Windows-oriented desktop application with a Tkinter interface and SQLite persistence. The current codebase keeps the existing single-file application architecture to minimize regression risk; deeper modularization is reserved for a later release.

The public repository contains a sanitized baseline database. It does **not** include the author's operational song library, credentials, private tokens, backups, historical patch payloads, or development-only files.

## Features

- Music library management with create, edit, delete, filtering and CSV export workflows.
- Emotional classification using Positive, Neutral and Negative categories with Primary/Secondary levels.
- Dedicated emotion views and ordering tools.
- Playlist/show planner with timing, show metadata and CSV export.
- Intelligence dashboard for library, emotional mix, playlist and platform coverage summaries.
- StarMaker catalog lookup, matching, compatible-track aggregation, ranking/trend views and playlist analysis.
- YouTube Data API metadata lookup and refresh for identified videos.
- Spotify Web API metadata lookup using Authorization Code + PKCE.
- MusicBrainz genre research/catalog refresh.
- SQLite persistence and local backup/export tools.
- Multilingual interface support for Spanish, English, Japanese and Filipino.
- Offline startup when no external integration is being actively queried.

## Tech Stack

- Python 3.10+
- Tkinter / ttk
- SQLite
- Python standard-library HTTP clients (`urllib`)
- REST/JSON integrations
- OAuth 2.0 Authorization Code + PKCE for Spotify

No third-party Python package is required by the current application runtime.

## Integrations

### StarMaker

The primary current path uses StarMaker's public JSON search endpoint for song discovery and metadata aggregation. The codebase also retains older public-page/browser discovery components as compatibility/legacy fallback code; they were not removed in this cleanup because they still have internal references and removing them would be a functional refactor.

No StarMaker account credentials are required by the primary public-data flow.

### YouTube Data API

YouTube integration can identify a video for a song and store public metadata such as channel, views, likes, comments, publication date and duration. A user-supplied YouTube Data API key is required for API calls. No key is included in this repository.

### Spotify

Spotify integration stores a user-provided Client ID and uses Authorization Code + PKCE. No Client Secret is required by this implementation. Access/refresh tokens are stored only in the local SQLite database after authorization and are not included in the public baseline database.

See [`docs/integrations.md`](docs/integrations.md) for implementation details.

## Screenshots

Historical screenshots from older releases were intentionally excluded so they are not presented as V1.6.1. The repository is prepared for current captures under `docs/screenshots/`.

Suggested filenames for future V1.6.1 captures:

- `dashboard.png`
- `library.png`
- `scheduler.png`
- `starmaker.png`
- `platforms.png`
- `settings.png`

## Installation

### Windows

1. Install Python 3.10 or newer from python.org and enable **Add Python to PATH**.
2. Clone or download this repository.
3. Optional but recommended: create a virtual environment.

```powershell
python -m venv .venv
.venv\Scripts\activate
```

4. Install the runtime requirements file (currently no third-party packages):

```powershell
pip install -r requirements.txt
```

5. Start the application:

```powershell
python playlist_emotion_studio.py
```

You can also double-click `INICIAR.bat` on Windows.

## Configuration

Configuration is available from the application settings screen and is stored locally in `data/playlist.db`.

- **YouTube:** enter your own YouTube Data API key.
- **Spotify:** enter your Spotify Client ID and use the built-in PKCE authorization flow. Register `http://127.0.0.1/callback` as the redirect URI in your Spotify developer application.
- **StarMaker:** the primary public-data lookup does not require a user API key in the current implementation.
- **MusicBrainz:** genre catalog refresh uses public MusicBrainz endpoints and does not require a key in the current implementation.

## Data & Privacy

The repository ships a **sanitized empty SQLite baseline** containing the application schema and non-sensitive default settings only. It contains no operational songs, playlists, historical platform scans, account sessions, API keys, OAuth tokens or private backups.

The following runtime data files are retained because the application references them directly:

- `data/generos_curados_v130.csv`
- `data/genre_catalog_musicbrainz.txt`
- `data/starmaker_seed_v141.json`
- `data/playlist.db` — sanitized baseline only

User-created data and credentials remain local to the user's own database after use.

## Project Structure

```text
playlist-emotion-studio/
├── README.md
├── requirements.txt
├── .gitignore
├── INICIAR.bat
├── playlist_emotion_studio.py
├── data/
│   ├── playlist.db
│   ├── generos_curados_v130.csv
│   ├── genre_catalog_musicbrainz.txt
│   └── starmaker_seed_v141.json
└── docs/
    ├── architecture.md
    ├── integrations.md
    └── screenshots/
        └── README.md
```

## Project Status

**Version 1.6.1** — active development / portfolio release.

This release is intentionally a cleanup and publication patch. It normalizes the public project identity, removes historical deployment artifacts and private operational data, and preserves the existing application behavior rather than introducing a broad architectural rewrite.

## Roadmap

- Modularize the current single-file codebase into clearly separated UI, persistence and service modules.
- Add automated unit/integration tests around persistence and external service adapters.
- Improve packaging/distribution for end users.
- Add current V1.6.1+ screenshots and release documentation.

## Author

**Carlos Adrián Ledesma**  
GitHub: **@carlos-adrian-ledesma**

Copyright © 2026 Carlos Adrián Ledesma. All rights reserved. This source code is published for portfolio and evaluation purposes only. No permission is granted to copy, modify, redistribute, sublicense, or use it commercially without prior written authorization from the author.
