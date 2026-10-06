# Integrations

## StarMaker

### Current primary path

The V1.6.x StarMaker workspace primarily uses `StarMakerDirectAPIClient`, which queries the public JSON endpoint used by StarMaker's web search flow and normalizes compatible song/artist results for local matching and aggregation.

### Stored data

Depending on user actions, the SQLite database can store public StarMaker identifiers, URLs, titles, artists, compatible track variants, recording counts, match confidence, snapshots, scan status and local diagnostic logs.

### Credentials

The primary public-data flow does not require a StarMaker account credential or private API token.

### Legacy/fallback code

The source still contains public-web discovery, native-search and headless-browser helpers. They were retained because the codebase still references parts of that infrastructure. V1.6.1 does not perform a deep service-layer refactor or delete uncertain fallback code.

## YouTube Data API

### Purpose

`YouTubeClient` can search for a likely video when a song is not yet identified and can refresh public metadata for a known video ID.

The current schema supports fields for video/channel identification, views, likes, comments, publication date, duration and match confidence.

### Credentials

A YouTube Data API key is required for YouTube API requests. Users enter their own key in Settings. The public repository contains no API key.

### Local storage

The API key and YouTube quota counter are stored in local SQLite settings. The sanitized public database initializes the API-key field as empty.

## Spotify Web API

### Purpose

`SpotifyClient` searches and stores verifiable track metadata including Spotify track ID/URL, title, artist, album, release date, duration, explicit flag, ISRC and match confidence.

### Authentication

The application uses OAuth 2.0 Authorization Code with PKCE.

- Required from the user: Spotify Client ID.
- Client Secret: not used by this implementation.
- Redirect URI: `http://127.0.0.1/callback`.
- Access/refresh tokens are generated only after the user authorizes the app.

### Local storage

Client ID, access token, refresh token and token expiry are stored locally in SQLite. All of these values are blank/zero in the public sanitized database.

## MusicBrainz

### Purpose

`MusicBrainzGenreClient` is used for genre research and for refreshing the local genre/style catalog.

### Credentials

No API key is required by the current implementation.

### Local storage

The refreshed catalog can be written to `data/genre_catalog_musicbrainz.txt`. Song-level MusicBrainz identifiers and genre research metadata are stored in SQLite when the user performs those workflows.

## Network and Offline Behavior

The application does not require an external service to open. Network calls occur when the user invokes platform lookup/refresh features (or related background actions). With the sanitized baseline database and no credentials configured, the local library/UI can still initialize without requiring YouTube or Spotify authorization.
