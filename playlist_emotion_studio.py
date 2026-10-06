from __future__ import annotations

import base64
import concurrent.futures
import csv
import difflib
import hashlib
import html
import http.server
import json
import math
import os
import re
import secrets
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

APP_NAME = "Playlist Emotion Studio"
VERSION = "1.6.1"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "playlist.db"
GENRE_CATALOG_PATH = BASE_DIR / "data" / "genre_catalog_musicbrainz.txt"
CURATED_GENRE_PATH = BASE_DIR / "data" / "generos_curados_v130.csv"
STARMAKER_BASE = "https://www.starmakerstudios.com"
STARMAKER_SEARCH_URL = STARMAKER_BASE + "/en/songSearch"
STARMAKER_API_SEARCH_URL = "https://api.starmakerstudios.com/web/union/search"
STARMAKER_AUTO_PAGES = [
    ("Global · Songbook", STARMAKER_BASE + "/en/songs", "GLOBAL", "catalog"),
    ("Global · Top Songs", STARMAKER_BASE + "/en/playlist/starmaker-top-songs/294", "GLOBAL", "playlist"),
    ("English Favorites", STARMAKER_BASE + "/en/song-languages/english-favorites/1", "EN", "language"),
    ("Latin Flow", STARMAKER_BASE + "/en/song-languages/latin-flow/4", "LATIN", "language"),
    ("Rock", STARMAKER_BASE + "/en/genre/rock/2256", "ROCK", "genre"),
    ("Latin", STARMAKER_BASE + "/en/genre/%EB%9D%BC%ED%8B%B4/2829", "LATIN", "genre"),
    ("US Top 100", STARMAKER_BASE + "/en/playlist/us-top-100-de-esta-semana/1357", "US", "chart"),
    ("MX Top 100", STARMAKER_BASE + "/en/playlist/mx-top-100-da-semana/1370", "MX", "chart"),
    ("JP Top 100", STARMAKER_BASE + "/en/playlist/jp-top-100-this-week/1373", "JP", "chart"),
    ("PH Top 100", STARMAKER_BASE + "/en/playlist/ph-top-100-tuan-nay/1359", "PH", "chart"),
    ("VN Top 100", STARMAKER_BASE + "/en/playlist/vn-top-100-this-week/1360", "VN", "chart"),
]
STARMAKER_TTL_HOURS = 24
STARMAKER_ARTIST_TTL_HOURS = 168
STARMAKER_RESCUE_TTL_HOURS = 168
STARMAKER_RESCUE_MISS_TTL_HOURS = 2
STARMAKER_RATE_DELAY = 0.20
STARMAKER_RESCUE_DELAY = 0.22
STARMAKER_RESCUE_MAX_URLS = 12
STARMAKER_SINGER_DIRECTORY_URL = STARMAKER_BASE + "/en/singers"
# Buscadores públicos utilizados únicamente para DESCUBRIR URLs oficiales.
# Los datos musicales se leen siempre después desde starmakerstudios.com.
# RSS/Lite van primero porque devuelven HTML/XML más estable que las páginas JS modernas.
STARMAKER_DISCOVERY_ENGINES = [
    ("BingRSS", "https://www.bing.com/search?format=rss&q={query}"),
    ("DuckDuckGoLite", "https://lite.duckduckgo.com/lite/?q={query}"),
    ("Google", "https://www.google.com/search?num=20&q={query}"),
    ("Brave", "https://search.brave.com/search?source=web&q={query}"),
    ("DuckDuckGo", "https://html.duckduckgo.com/html/?q={query}"),
    ("Bing", "https://www.bing.com/search?q={query}&count=20"),
    ("Yahoo", "https://search.yahoo.com/search?p={query}"),
]
STARMAKER_SEED_PATH = BASE_DIR / "data" / "starmaker_seed_v141.json"

COLORS = {
    "bg": "#080D1B",
    "panel": "#11192C",
    "panel2": "#18233C",
    "card": "#15213A",
    "line": "#384766",
    "line_soft": "#273653",
    "text": "#F2F5FF",
    "muted": "#A7B1C9",
    "accent": "#FF3B8D",
    "accent_hover": "#FF5AA1",
    "accent2": "#7C5CFF",
    "accent2_hover": "#927AFF",
    "teal": "#19C6C2",
    "aqua": "#229FB2",
    "positive": "#2FBF71",
    "neutral": "#D6A23C",
    "negative": "#E25763",
    "danger": "#B63E57",
    "danger_hover": "#D04A67",
    "warning": "#D6913A",
    "white": "#FFFFFF",
}

SOURCES = [
    "RockRomanticos",
    "InternacionalRockRomanticos",
    "CumbiaReguettonCuartetoFiesta",
    "MusicaAcusticaYpiano",
    "Programador_20",
]
EMOTIONS = ["Positiva", "Neutra", "Negativa"]
LEVELS = ["Principal", "Secundaria"]

UI_LANGUAGES = {"es": "Español", "en": "English", "ja": "日本語", "fil": "Filipino"}
TRANSLATIONS = {
    "en": {
        "Resumen":"Dashboard",
            "Biblioteca":"Library",
            "Emoción positiva":"Positive emotion",
            "Emoción neutra":"Neutral emotion",
            "Emoción negativa":"Negative emotion",
        "Programador":"Show planner",
            "Plataformas":"Platforms",
            "Configuración":"Settings",
            "Buscar":"Search",
            "Canción":"Song",
            "Artista":"Artist",
            "Género":"Genre",
            "País":"Country",
            "Año":"Year",
            "Duración":"Duration",
            "Origen":"Source",
            "Emoción":"Emotion",
            "Nivel":"Level",
        "Principal":"Primary",
            "Secundaria":"Secondary",
            "Nueva canción":"New song",
            "Editar":"Edit",
            "Eliminar":"Delete",
            "Subir":"Move up",
            "Bajar":"Move down",
            "Cambiar nivel":"Change level",
            "Cancelar":"Cancel",
            "Guardar canción":"Save song",
            "Limpiar filtros":"Clear filters",
        "Nueva playlist":"New playlist",
            "Renombrar":"Rename",
            "Duplicar playlist":"Duplicate playlist",
            "Datos del show":"Show data",
            "Quitar":"Remove",
            "Agregar al programador →":"Add to show planner →",
        "Resumen operativo":"Intelligence Dashboard",
            "Catálogo":"Catalog",
            "Ranking / Evolución":"Ranking / Trends",
            "Playlist actual":"Current playlist",
            "Actualizar seleccionada":"Update selected",
            "Actualizar identificadas":"Refresh identified",
            "Completar faltantes":"Find missing",
        "Idioma":"Language",
            "General":"General",
            "Apariencia":"Appearance",
            "Datos / respaldo":"Data / backup",
            "Diagnóstico":"Diagnostics",
            "Guardar configuración":"Save settings",
            "Respaldar base SQLite":"Backup SQLite database",
            "Exportar biblioteca CSV":"Export library CSV",
        "Conectar Spotify":"Connect Spotify",
            "Desconectar Spotify":"Disconnect Spotify",
            "YouTube API":"YouTube API",
            "Estado":"Status",
            "Encontrada":"Found",
            "Sin datos":"No data",
            "Última actualización":"Last updated",
            "Cobertura":"Coverage",
            "Grabaciones":"Recordings",
            "Pistas":"Tracks",
            "Vistas":"Views",
            "Me gusta":"Likes",
            "Comentarios":"Comments",
            "Canal":"Channel",
            "Álbum":"Album",
            "Lanzamiento":"Release",
            "Explícita":"Explicit",
            "Sí":"Yes",
            "No":"No",
    },
    "ja": {
        "Resumen":"ダッシュボード",
            "Biblioteca":"ライブラリ",
            "Emoción positiva":"ポジティブ感情",
            "Emoción neutra":"ニュートラル感情",
            "Emoción negativa":"ネガティブ感情",
        "Programador":"ショープランナー",
            "Plataformas":"プラットフォーム",
            "Configuración":"設定",
            "Buscar":"検索",
            "Canción":"曲",
            "Artista":"アーティスト",
            "Género":"ジャンル",
            "País":"国",
            "Año":"年",
            "Duración":"長さ",
            "Origen":"コレクション",
            "Emoción":"感情",
            "Nivel":"レベル",
        "Principal":"メイン",
            "Secundaria":"サブ",
            "Nueva canción":"新しい曲",
            "Editar":"編集",
            "Eliminar":"削除",
            "Subir":"上へ",
            "Bajar":"下へ",
            "Cambiar nivel":"レベル変更",
            "Cancelar":"キャンセル",
            "Guardar canción":"曲を保存",
            "Limpiar filtros":"フィルター解除",
        "Nueva playlist":"新規プレイリスト",
            "Renombrar":"名前変更",
            "Duplicar playlist":"複製",
            "Datos del show":"ショー情報",
            "Quitar":"削除",
            "Agregar al programador →":"ショーに追加 →",
        "Resumen operativo":"インテリジェンス・ダッシュボード",
            "Catálogo":"カタログ",
            "Ranking / Evolución":"ランキング / 推移",
            "Playlist actual":"現在のプレイリスト",
            "Actualizar seleccionada":"選択項目を更新",
            "Actualizar identificadas":"識別済みを更新",
            "Completar faltantes":"未取得を検索",
        "Idioma":"言語",
            "General":"一般",
            "Apariencia":"外観",
            "Datos / respaldo":"データ / バックアップ",
            "Diagnóstico":"診断",
            "Guardar configuración":"設定を保存",
            "Respaldar base SQLite":"SQLiteをバックアップ",
            "Exportar biblioteca CSV":"ライブラリCSVを出力",
        "Conectar Spotify":"Spotifyに接続",
            "Desconectar Spotify":"Spotifyを切断",
            "YouTube API":"YouTube API",
            "Estado":"状態",
            "Encontrada":"見つかりました",
            "Sin datos":"データなし",
            "Última actualización":"最終更新",
            "Cobertura":"カバー率",
            "Grabaciones":"録音数",
            "Pistas":"トラック",
            "Vistas":"再生回数",
            "Me gusta":"高評価",
            "Comentarios":"コメント",
            "Canal":"チャンネル",
            "Álbum":"アルバム",
            "Lanzamiento":"リリース",
            "Explícita":"Explicit",
            "Sí":"はい",
            "No":"いいえ",
    },
    "fil": {
        "Resumen":"Dashboard",
            "Biblioteca":"Aklatan",
            "Emoción positiva":"Positibong emosyon",
            "Emoción neutra":"Neutral na emosyon",
            "Emoción negativa":"Negatibong emosyon",
        "Programador":"Tagaplano ng show",
            "Plataformas":"Mga platform",
            "Configuración":"Mga setting",
            "Buscar":"Maghanap",
            "Canción":"Kanta",
            "Artista":"Artista",
            "Género":"Genre",
            "País":"Bansa",
            "Año":"Taon",
            "Duración":"Tagal",
            "Origen":"Koleksiyon",
            "Emoción":"Emosyon",
            "Nivel":"Antas",
        "Principal":"Pangunahin",
            "Secundaria":"Pangalawa",
            "Nueva canción":"Bagong kanta",
            "Editar":"I-edit",
            "Eliminar":"Tanggalin",
            "Subir":"Itaas",
            "Bajar":"Ibaba",
            "Cambiar nivel":"Palitan ang antas",
            "Cancelar":"Kanselahin",
            "Guardar canción":"I-save ang kanta",
            "Limpiar filtros":"I-clear ang filter",
        "Nueva playlist":"Bagong playlist",
            "Renombrar":"Palitan ang pangalan",
            "Duplicar playlist":"Kopyahin ang playlist",
            "Datos del show":"Detalye ng show",
            "Quitar":"Alisin",
            "Agregar al programador →":"Idagdag sa show →",
        "Resumen operativo":"Intelligence Dashboard",
            "Catálogo":"Katalogo",
            "Ranking / Evolución":"Ranking / Trend",
            "Playlist actual":"Kasalukuyang playlist",
            "Actualizar seleccionada":"I-update ang napili",
            "Actualizar identificadas":"I-refresh ang natukoy",
            "Completar faltantes":"Hanapin ang kulang",
        "Idioma":"Wika",
            "General":"Pangkalahatan",
            "Apariencia":"Itsura",
            "Datos / respaldo":"Data / backup",
            "Diagnóstico":"Diagnostics",
            "Guardar configuración":"I-save ang settings",
            "Respaldar base SQLite":"I-backup ang SQLite",
            "Exportar biblioteca CSV":"I-export ang library CSV",
        "Conectar Spotify":"Ikonekta ang Spotify",
            "Desconectar Spotify":"Idiskonekta ang Spotify",
            "YouTube API":"YouTube API",
            "Estado":"Status",
            "Encontrada":"Nahanap",
            "Sin datos":"Walang data",
            "Última actualización":"Huling update",
            "Cobertura":"Coverage",
            "Grabaciones":"Mga recording",
            "Pistas":"Mga track",
            "Vistas":"Views",
            "Me gusta":"Likes",
            "Comentarios":"Comments",
            "Canal":"Channel",
            "Álbum":"Album",
            "Lanzamiento":"Release",
            "Explícita":"Explicit",
            "Sí":"Oo",
            "No":"Hindi",
    },
}

def ui_tr(text: str, lang: str = "es") -> str:
    return TRANSLATIONS.get(lang, {}).get(text, text)


def parse_iso8601_duration(value: str) -> int:
    """Convierte duraciones ISO 8601 simples de YouTube (PT#H#M#S) a segundos."""
    m = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", value or "")
    if not m:
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h*3600+mi*60+s


def set_windows_dpi_awareness():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def duration_to_seconds(value: str) -> int:
    value = (value or "").strip()
    m = re.match(r"^(\d+):(\d{1,2})$", value)
    if m:
        return int(m.group(1)) * 60 + min(59, int(m.group(2)))
    try:
        return int(round(float(value) * 60))
    except Exception:
        return 0


def seconds_to_human(seconds: int) -> str:
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} h {m:02d} min"
    return f"{m} min {s:02d} s"


def format_int(v) -> str:
    if v in (None, ""):
        return "—"
    try:
        return f"{int(v):,}".replace(",", ".")
    except Exception:
        return str(v)


def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_genre_catalog(db=None) -> list[str]:
    """Catálogo operativo de géneros.

    El archivo local se puede actualizar desde MusicBrainz. Se combina con los
    géneros ya presentes en la biblioteca para no ocultar clasificaciones manuales.
    """
    values = set()
    try:
        if GENRE_CATALOG_PATH.exists():
            for line in GENRE_CATALOG_PATH.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    values.add(line)
    except Exception:
        pass
    if db is not None:
        try:
            values.update(x for x in db.distinct("genre") if x)
        except Exception:
            pass
    return sorted(values, key=lambda x: x.casefold())


class SearchableCombobox(ttk.Combobox):
    """Combobox editable que reduce la lista mientras se escribe."""

    def __init__(self, master=None, values=None, **kwargs):
        self._all_values = list(values or [])
        super().__init__(master, values=self._all_values, **kwargs)
        self.bind("<KeyRelease>", self._filter, add="+")
        self.bind("<FocusIn>", lambda e: self.configure(values=self._all_values), add="+")

    def set_all_values(self, values):
        self._all_values = list(values or [])
        self.configure(values=self._all_values)

    def _filter(self, event=None):
        if event and event.keysym in {"Up", "Down", "Left", "Right", "Return", "Escape", "Tab"}:
            return
        q = self.get().strip().casefold()
        if not q:
            vals = self._all_values
        else:
            vals = [v for v in self._all_values if q in v.casefold()]
        self.configure(values=vals[:800])


class ScrollSurface(tk.Frame):
    """Superficie con scroll global horizontal/vertical y borde visible."""

    def __init__(self, master, min_width=1120, min_height=720, **kwargs):
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.min_width = min_width
        self.min_height = min_height
        self.canvas = tk.Canvas(
            self, bg=COLORS["bg"], bd=0, highlightthickness=1,
            highlightbackground=COLORS["line"], highlightcolor=COLORS["accent"]
        )
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.inner = tk.Frame(self.canvas, bg=COLORS["bg"])
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._sync, add="+")
        self.canvas.bind("<Configure>", self._sync, add="+")
        self.canvas.bind("<MouseWheel>", self._wheel, add="+")
        self.canvas.bind("<Shift-MouseWheel>", self._shift_wheel, add="+")

    def _sync(self, event=None):
        self.update_idletasks()
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        rw = max(self.min_width, self.inner.winfo_reqwidth(), cw)
        rh = max(self.min_height, self.inner.winfo_reqheight(), ch)
        try:
            self.canvas.itemconfigure(self.window_id, width=rw, height=rh)
            self.canvas.configure(scrollregion=(0, 0, rw, rh))
        except tk.TclError:
            pass

    def _wheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _shift_wheel(self, event):
        if event.delta:
            self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")


class MusicBrainzGenreClient:
    """Investigador de género basado en metadatos públicos de MusicBrainz.

    Respeta el límite público de una petición por segundo. Los géneros son etiquetas
    editoriales/comunitarias, por lo que se guarda también la fuente y la confianza.
    """
    API = "https://musicbrainz.org/ws/2"
    _rate_lock = threading.Lock()
    _last_request = 0.0

    @classmethod
    def _throttle(cls):
        with cls._rate_lock:
            wait = 1.05 - (time.monotonic() - cls._last_request)
            if wait > 0:
                time.sleep(wait)
            cls._last_request = time.monotonic()

    @classmethod
    def _get_json(cls, endpoint: str, params: dict):
        cls._throttle()
        q = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{cls.API}/{endpoint}?{q}",
            headers={
                "User-Agent": f"{APP_NAME}/{VERSION} (genre metadata research)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=18) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _artist_probe(artist: str) -> str:
        # Para créditos múltiples, el primer artista suele dar mejores coincidencias.
        a = re.split(r"\s+(?:ft\.?|feat\.?|x|&|and|y)\s+|,", artist or "", maxsplit=1, flags=re.I)[0]
        return a.strip() or (artist or "").strip()

    @classmethod
    def fetch_all_genres(cls, cancel_event=None) -> list[str]:
        if cancel_event and cancel_event.is_set():
            return []
        # MusicBrainz ofrece /genre/all?fmt=txt como lista completa en una sola petición.
        cls._throttle()
        req = urllib.request.Request(
            f"{cls.API}/genre/all?fmt=txt",
            headers={"User-Agent": f"{APP_NAME}/{VERSION} (genre catalog)", "Accept": "text/plain"},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        return sorted({line.strip() for line in text.splitlines() if line.strip()},
            key=lambda x: x.casefold())

    @classmethod
    def research_track(cls, artist: str, song: str) -> dict:
        artist_probe = cls._artist_probe(artist)
        def esc(v):
            return (v or "").replace('"', "\"")
        query = f'recording:"{esc(song)}" AND artist:"{esc(artist_probe)}"'
        search = cls._get_json("recording/", {"query": query, "fmt": "json", "limit": 5})
        recordings = search.get("recordings", [])
        if not recordings:
            return {"genre": "", "source": "MusicBrainz · sin coincidencia", "confidence": 0,
                    "recording_id": "", "artist_id": ""}
        best = max(recordings, key=lambda r: int(r.get("score", 0) or 0))
        score = int(best.get("score", 0) or 0)
        rid = best.get("id", "")
        artist_credits = best.get("artist-credit", []) or []
        artist_id = ""
        for ac in artist_credits:
            if isinstance(ac, dict) and isinstance(ac.get("artist"), dict):
                artist_id = ac["artist"].get("id", "")
                if artist_id:
                    break
        rec = cls._get_json(f"recording/{rid}", {"inc": "genres+artist-credits", "fmt": "json"})
        genres = rec.get("genres", []) or []
        source = "MusicBrainz · grabación"
        if not genres and artist_id:
            art = cls._get_json(f"artist/{artist_id}", {"inc": "genres", "fmt": "json"})
            genres = art.get("genres", []) or []
            source = "MusicBrainz · artista"
            score = min(score, 82)
        ranked = sorted(genres, key=lambda g: int(g.get("count", 0) or 0), reverse=True)
        names = []
        for g in ranked:
            name = (g.get("name") or "").strip()
            if name and name.casefold() not in {x.casefold() for x in names}:
                names.append(name)
            if len(names) >= 3:
                break
        return {
            "genre": " / ".join(names),
            "source": source if names else "MusicBrainz · sin género asignado",
            "confidence": score if names else 0,
            "recording_id": rid,
            "artist_id": artist_id,
        }


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_match_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = re.sub(r"\b(feat(?:uring)?|ft)\.?\b", " ", value)
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def compact_count(value) -> str:
    if value in (None, ""):
        return "Sin datos"
    try:
        n = int(value)
    except Exception:
        return str(value)
    for div, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if n >= div:
            x = n / div
            return f"{x:.1f}{suffix}".replace(".0", "")
    return str(n)


def parse_compact_count(text: str):
    if not text:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*([KMB])?\s+(?:recordings|grabaciones|gravações|gravacoes)\b",
        text,
        re.I)
    if not m:
        return None
    num = float(m.group(1).replace(",", "."))
    mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get((m.group(2) or "").upper(), 1)
    return int(round(num * mult))


def match_confidence(local_artist: str, local_song: str, remote_artist: str, remote_song: str) -> int:
    la, ls = normalize_match_text(local_artist), normalize_match_text(local_song)
    ra, rs = normalize_match_text(remote_artist), normalize_match_text(remote_song)
    if ls and rs and ls == rs and la and ra and (la == ra or la in ra or ra in la):
        return 100
    title = difflib.SequenceMatcher(None, ls, rs).ratio() if ls and rs else 0.0
    artist = difflib.SequenceMatcher(None, la, ra).ratio() if la and ra else 0.0
    return max(0, min(100, int(round(title * 70 + artist * 30))))



class _StarMakerTokenParser(HTMLParser):
    """Tokenizador tolerante para las páginas SSR públicas de StarMaker."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens = []
        self._href_stack = []
        self._current_href = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower()=="a":
            href = dict(attrs).get("href", "") or ""
            self._href_stack.append(self._current_href)
            self._current_href = href

    def handle_endtag(self, tag):
        if tag.lower()=="a":
            self._current_href = self._href_stack.pop() if self._href_stack else ""

    def handle_data(self, data):
        s = re.sub(r"\s+", " ", data or "").strip()
        if s:
            self.tokens.append((s, self._current_href))


def _sm_variant(title: str) -> str:
    t = (title or "").strip()
    m = re.search(r"\(([^)]{2,60})\)\s*$", t)
    if m:
        return m.group(1).strip()
    tags = []
    for word, label in [("piano", "Piano"),
        ("acoustic", "Acoustic"),
        ("acústic", "Acoustic"),
        ("short", "Short"),
        ("remix", "Remix"),
        ("live", "Live"),
        ("slowed", "Slowed"),
        ("male", "Male"),
        ("female", "Female"),
        ("lower", "Lower key"),
        ("higher", "Higher key")]:
        if word in t.casefold() and label not in tags:
            tags.append(label)
    return " / ".join(tags)


def _sm_base_title(value: str) -> str:
    """Título canónico de la obra para StarMaker.

    V1.4.5 prioriza coincidencia por TÍTULO exacto y sólo elimina marcadores que no
    cambian la identidad de la obra: feat./ft., acústico, piano, karaoke, live, etc.
    Remix se detecta por separado para poder excluirlo cuando la ficha local no es remix.
    """
    t = (value or "").strip()
    # Colaboradores suelen venir dentro del título remoto: "Danza Kuduro (feat. Don Omar)".
    t = re.sub(r"\((?:feat(?:uring)?|ft)\.?\s+[^)]*\)", " ", t, flags=re.I)
    t = re.sub(r"\b(?:feat(?:uring)?|ft)\.?\s+[^—–|\[]+$", " ", t, flags=re.I)
    tag = (
        '(?:acoustic|acústic[oa]?|piano|karaoke|instrumental|short(?: '
        'version)?|live|slowed|lower(?: key)?|higher(?: key)?|male|female|deluxe|remix|versio'
        'n|versión)'
    )
    t = re.sub(r"\((?=[^)]*\b"+tag+r"\b)[^)]*\)", " ", t, flags=re.I)
    t = re.sub(r"\[(?=[^]]*\b"+tag+r"\b)[^]]*\]", " ", t, flags=re.I)
    t = re.sub(r"\s*[—–-]\s*(?=[^—–-]*\b"+tag+r"\b)[^—–-]*$", " ", t, flags=re.I)
    t = re.sub(r"\b(?:karaoke|instrumental)\b", " ", t, flags=re.I)
    return normalize_match_text(t)


def _sm_split_artists(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw:
        return []
    raw = re.sub(r"\b(?:feat(?:uring)?|ft)\.?\b", " & ", raw, flags=re.I)
    parts = re.split(r"\s*(?:&|/|,|\bx\b|\by\b|\band\b)\s*", raw, flags=re.I)
    out = []
    for part in [raw]+parts:
        part = re.sub(r"\s+", " ", part).strip(" -–—|·")
        if len(part)>=2 and normalize_match_text(part) and normalize_match_text(part) not in {normalize_match_text(x) for x in out}:
            out.append(part)
    return out


def _sm_is_remix(value: str) -> bool:
    return "remix" in normalize_match_text(value)

def _sm_public_key(title: str, artist: str, url: str="") -> str:
    parsed = StarMakerPublicClient.parse_public_url(url) if url else {"public_id":""}
    if parsed.get("public_id"):
        return "id:"+parsed["public_id"]
    return "txt:"+normalize_match_text(title)+"|"+normalize_match_text(artist)


class StarMakerInterpretiveAI:
    """Motor interpretativo LOCAL V1.4.7.

    No usa un LLM externo ni inventa datos. Interpreta señales públicas ya obtenidas:
    título, artista atribuido, artista de contexto, slug de la URL, variante y uploader.
    Su objetivo es reconocer la MISMA OBRA aunque StarMaker la publique con otro
    intérprete, un usuario que subió el backing track o una variante acústica/piano.
    """
    STOP = {"the", "a", "an", "el", "la", "los", "las", "de", "del", "y", "and", "of", "en", "un", "una"}

    @staticmethod
    def _tokens(value):
        n = normalize_match_text(value)
        return [t for t in n.split() if t and t not in StarMakerInterpretiveAI.STOP]

    @classmethod
    def title_strength(cls, value):
        base = _sm_base_title(value)
        toks = cls._tokens(base)
        # Títulos largos/distintivos permiten reconocer covers con otro intérprete.
        if len(toks)>=5:
            return 1.0
        if len(toks)==4:
            return 0.94
        if len(toks)==3 and len(base)>=15:
            return 0.88
        if len(toks)==3:
            return 0.80
        if len(toks)==2 and len(base)>=18:
            return 0.72
        if len(toks)==2:
            return 0.58
        return 0.30

    @classmethod
    def score(cls, local_song, remote):
        local_title = (local_song["song"] or "").strip()
        remote_title = (remote["title"] or "").strip()
        lb = _sm_base_title(local_title)
        rb = _sm_base_title(remote_title)
        if not lb or not rb:
            return {"accept":False, "score":0, "reason":"sin título comparable", "match_type":"Descartada"}
        local_remix = _sm_is_remix(local_title+" "+(local_song["genre"] or ""))
        remote_remix = _sm_is_remix(remote_title+" "+(remote["variant"] or ""))
        if local_remix != remote_remix:
            return {"accept":False, "score":0, "reason":"remix incompatible", "match_type":"Descartada"}
        seq = difflib.SequenceMatcher(None, lb, rb).ratio()
        lt = set(cls._tokens(lb))
        rt = set(cls._tokens(rb))
        jac = (len(lt&rt)/len(lt|rt)) if (lt|rt) else 0.0
        exact_title = (lb==rb)
        title_score = 1.0 if exact_title else max(seq, jac)

        local_artists = [normalize_match_text(x) for x in _sm_split_artists(local_song["artist"] or "") if normalize_match_text(x)]
        remote_values = []
        for key in ("artist", "source_label", "uploaded_by"):
            raw = (remote[key] if key in remote.keys() else "") or ""
            remote_values += [normalize_match_text(x) for x in _sm_split_artists(raw) if normalize_match_text(x)]
            n = normalize_match_text(raw)
            if n:
                remote_values.append(n)
        url = ((remote["url"] if "url" in remote.keys() else "") or (remote["source_url"] if "source_url" in remote.keys() else "") or "")
        slug = normalize_match_text(urllib.parse.unquote(urllib.parse.urlparse(url).path))
        artist_score = 0.0
        artist_reason = ""
        for la in local_artists:
            for ra in remote_values:
                if la==ra:
                    artist_score = max(artist_score, 1.0)
                    artist_reason = "artista exacto"
                elif len(la)>=6 and len(ra)>=6:
                    rr = difflib.SequenceMatcher(None, la, ra).ratio()
                    if rr>artist_score:
                        artist_score = rr
                        artist_reason = "artista aproximado"
            if la and la in slug:
                artist_score = max(artist_score, 0.98)
                artist_reason = "artista en URL"

        strength = cls.title_strength(local_title)
        reasons = []
        if exact_title:
            reasons.append("título de obra exacto")
        elif title_score>=0.92:
            reasons.append("título casi exacto")
        if artist_score>=0.92:
            reasons.append(artist_reason or "artista compatible")

        # Regla principal: con artista fuerte, título exacto/casi exacto.
        if title_score>=0.94 and artist_score>=0.78:
            score = int(round(74*title_score+26*artist_score))
            return {"accept":True,
                "score":min(100, score),
                "reason":"; ".join(reasons),
                "match_type":"Exacta / variante"}

        # IA interpretativa de cover: título MUY distintivo permite otro intérprete/uploader.
        # Evita falsos positivos en títulos genéricos como Yellow, Woman, Perfect, Angel, etc.
        if exact_title and strength>=0.88:
            score = int(round(78+12*strength+8*artist_score))
            reasons.append("título suficientemente distintivo para cover/uploader alternativo")
            return {"accept":True,
                "score":min(94, score),
                "reason":"; ".join(reasons),
                "match_type":"Cover / intérprete alternativo"}

        # Tres palabras algo menos distintivas: exige al menos una pista de contexto.
        if exact_title and strength>=0.78 and artist_score>=0.35:
            score = int(round(72+15*strength+10*artist_score))
            reasons.append("obra probable por título + contexto")
            return {"accept":True,
                "score":min(90, score),
                "reason":"; ".join(reasons),
                "match_type":"Interpretativa"}

        return {"accept":False,
            "score":int(round(70*title_score+30*artist_score)),
            "reason":"evidencia insuficiente",
            "match_type":"Revisar"}

class StarMakerPublicClient:
    """Cliente deliberadamente conservador: sólo páginas públicas oficiales."""
    USER_AGENT = f"Mozilla/5.0 PlaylistEmotionStudio/{VERSION} (+StarMaker public API only)"

    @staticmethod
    def _official_url(url: str) -> bool:
        try:
            host = (urllib.parse.urlparse(url).hostname or "").casefold()
            return host == "starmakerstudios.com" or host.endswith(".starmakerstudios.com")
        except Exception:
            return False

    @classmethod
    def get_text(cls, url: str, timeout: int = 12) -> str:
        if not cls._official_url(url):
            raise ValueError("Sólo se permiten URLs públicas oficiales de StarMaker")
        req = urllib.request.Request(url,
            headers={"User-Agent": cls.USER_AGENT, "Accept-Language": "en-US,en;q=0.8"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(2_500_000)
            charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")

    @staticmethod
    def parse_public_url(url: str) -> dict:
        url = (url or "").strip()
        if not url:
            return {"type": "unknown", "public_id": "", "url": ""}
        p = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(p.query)
        path = p.path or ""
        kind = "unknown"
        public_id = ""
        if "/song/" in path:
            kind = "song"
            m = re.search(r"/(\d+)(?:/)?$", path)
            public_id = m.group(1) if m else ""
        elif "/singer/" in path:
            kind = "singer"
            m = re.search(r"/(\d+)(?:/)?$", path)
            public_id = m.group(1) if m else ((q.get("id") or q.get("singerId") or q.get("singerid") or [""])[0])
        elif "/playlist/" in path:
            kind = "playlist"
            m = re.search(r"/(\d+)(?:/)?$", path)
            public_id = m.group(1) if m else ((q.get("id") or q.get("playlistId") or q.get("playlistid") or [""])[0])
        elif "playrecording" in path.casefold() or any(k.casefold()=="recordingid" for k in q):
            kind = "recording"
            public_id = (q.get("recordingId") or q.get("recordingid") or [""])[0]
        elif "/live/" in path.casefold() or "liveid" in {k.casefold() for k in q}:
            kind = "live"
            public_id = (q.get("liveid") or q.get("liveId") or [""])[0]
        elif "profileinfo" in path.casefold() or any(k.casefold()=="userid" for k in q):
            kind = "profile"
            public_id = (q.get("userId") or q.get("userid") or [""])[0]
        elif "songsearch" in path.casefold():
            kind = "search"
        return {"type": kind, "public_id": str(public_id or ""), "url": url}

    @staticmethod
    def _strip_tags(source: str) -> str:
        source = re.sub(r"<script\b[^>]*>.*?</script>", " ", source, flags=re.I|re.S)
        source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I|re.S)
        source = re.sub(r"<[^>]+>", " ", source)
        return re.sub(r"\s+", " ", html.unescape(source)).strip()

    @classmethod
    def parse_public_page(cls, source: str, url: str = "") -> dict:
        text = cls._strip_tags(source)
        title = ""
        artist = ""
        variant = ""
        count = parse_compact_count(text)
        mt = re.search(r"<title[^>]*>(.*?)</title>", source, re.I|re.S)
        page_title = html.unescape(re.sub(r"<[^>]+>", "", mt.group(1))).strip() if mt else ""
        # Títulos oficiales suelen ser: Sing X's Songs... o "Song - Artist | StarMaker".
        m = re.search(r"Sing\s+(.+?)['’]s\s+Songs", page_title, re.I)
        if m:
            artist = m.group(1).strip()
        # Para páginas individuales se intenta JSON-LD/meta OG sin asumir un formato único.
        for key, target in ((r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', "title"),
                            (r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
                                "description")):
            mm = re.search(key, source, re.I)
            if mm and target == "title":
                cand = html.unescape(mm.group(1)).strip()
                cand = re.sub(r"\s*[-|]\s*StarMaker.*$", "", cand, flags=re.I)
                if cand and "song" not in cand.casefold():
                    title = cand
        parsed = cls.parse_public_url(url)
        return {"title": title, "artist": artist, "variant": variant, "recordings_count": count,
                "starmaker_song_id": parsed.get("public_id", ""), "source_url": url}

    @classmethod
    def parse_catalog_page(cls,
        source: str,
        url: str,
        label: str="",
        region_code: str="",
        source_kind: str="catalog") -> list[dict]:
        """Extrae canción, artista y contador de las páginas públicas SSR.
        No depende de APIs privadas ni de login.
        """
        parser = _StarMakerTokenParser()
        try:
            parser.feed(source)
        except Exception:
            pass
        tokens = parser.tokens
        out = []
        seen = set()
        pos = 0
        for i, (txt, href) in enumerate(tokens):
            if not re.search(r"\b(recordings|grabaciones)\b", txt, re.I):
                continue
            count = parse_compact_count(txt)
            if count is None:
                continue
            title = ""
            artist = ""
            song_href = ""
            title_idx = None
            # El título suele ser un <a href=/song/...> cercano al contador.
            for j in range(i-1, max(-1, i-12), -1):
                t, h = tokens[j]
                if h and "/song/" in h:
                    title = t.strip()
                    song_href = h
                    title_idx = j
                    break
            # Fallback para HTML donde el href está en otro elemento del card.
            if not title:
                vals = []
                for j in range(max(0, i-6), i):
                    t, h = tokens[j]
                    if t.casefold() in {"points", "sing", "cantar", "lyrics", "recordings", "grabaciones"}:
                        continue
                    if re.fullmatch(r"\d+(?:[.,]\d+)?\s*[KMB]?", t, re.I):
                        continue
                    vals.append((j, t, h))
                if len(vals)>=2:
                    title_idx, title, song_href = vals[-2]
            if not title:
                continue
            # Artista: texto útil entre el título y el contador, preferentemente sin href /song/.
            start = (title_idx+1) if title_idx is not None else max(0, i-5)
            candidates = []
            for j in range(start, i):
                t, h = tokens[j]
                low = t.casefold()
                if low in {"points", "sing", "cantar", "lyrics", "recordings", "grabaciones", "play"}:
                    continue
                if "recordings" in low or "grabaciones" in low:
                    continue
                if t==title:
                    continue
                candidates.append(t)
            artist = candidates[-1].strip() if candidates else ""
            if not artist:
                continue
            full_url = urllib.parse.urljoin(url, song_href) if song_href else ""
            key = _sm_public_key(title, artist, full_url)
            if key in seen:
                continue
            seen.add(key)
            pos+=1
            info = cls.parse_public_url(full_url) if full_url else {"public_id":""}
            out.append({"public_key":key, "starmaker_song_id":info.get("public_id", ""), "url":full_url,
                        "title":title, "artist":artist, "variant":_sm_variant(title), "recordings_count":count,
                        "source_url":url, "source_label":label or url, "source_kind":source_kind,
                        "region_code":region_code, "position":pos})
        # Fallback basado en texto visible. Sirve si el SSR no conserva hrefs en el card.
        if not out:
            visible = cls._strip_tags(source)
            pat = re.compile((
                '(.{2,100}?)\\s+(?:Points\\s+)?(.{2,80}?)\\s+(\\d+(?:[.,]\\d+)?\\s*[KMB]?)\\s+(?:recordings|'
                'grabaciones)\\s+(?:Sing|Cantar)'
            ),
                re.I)
            for m in pat.finditer(visible):
                title = re.sub(r"\s+", " ", m.group(1)).strip(" -|·")
                artist = re.sub(r"\s+", " ", m.group(2)).strip(" -|·")
                # Evita arrastrar encabezados largos al título.
                title = title.split(" songs ")[-1].strip()
                count = parse_compact_count(m.group(3)+" recordings")
                if not title or not artist or count is None:
                    continue
                key = _sm_public_key(title, artist)
                if key in seen:
                    continue
                seen.add(key)
                pos+=1
                out.append({"public_key":key, "starmaker_song_id":"", "url":"", "title":title, "artist":artist,
                            "variant":_sm_variant(title), "recordings_count":count, "source_url":url,
                            "source_label":label or url,
                                "source_kind":source_kind,
                                "region_code":region_code,
                                "position":pos})
        return out

    @classmethod
    def parse_singer_directory_page(cls, source: str, url: str) -> dict:
        """Devuelve artistas y subdirectorios públicos encontrados en una página /singers."""
        parser = _StarMakerTokenParser()
        try:
            parser.feed(source)
        except Exception:
            pass
        artists = []
        categories = []
        seen_a = set()
        seen_c = set()
        for txt, href in parser.tokens:
            if not href:
                continue
            full = urllib.parse.urljoin(url, href)
            path = (urllib.parse.urlparse(full).path or "").casefold()
            name = re.sub(r"\s+", " ", txt or "").strip()
            if "/singer/" in path and "/singers/" not in path and name:
                info = cls.parse_public_url(full)
                # V1.4.3: StarMaker puede publicar varias páginas distintas para el mismo artista
                # (por ejemplo /singer/.../2302340 y /singer/...?...id=779). No colapsarlas por nombre.
                pid = (info.get("public_id") or "").strip()
                key = ("id:"+pid) if pid else ("url:"+full)
                if key and key not in seen_a:
                    seen_a.add(key)
                    artists.append({"artist_key":str(key),
                        "starmaker_artist_id":pid,
                        "artist_name":name,
                        "url":full,
                        "source_url":url})
            elif "/singers/" in path and full.rstrip("/")!=url.rstrip("/") and full not in seen_c:
                seen_c.add(full)
                categories.append(full)
        return {"artists":artists, "categories":categories}

    @classmethod
    def crawl_singer_directory(cls, timeout: int=15, max_categories: int=40) -> tuple[list[dict], int, int]:
        """Descubre el directorio público de artistas sin API privada ni autenticación."""
        artists = []
        seen = {}
        ok = failed = 0
        source = cls.get_text(STARMAKER_SINGER_DIRECTORY_URL, timeout=timeout)
        ok+=1
        root = cls.parse_singer_directory_page(source, STARMAKER_SINGER_DIRECTORY_URL)
        for a in root["artists"]:
            seen[a["url"]] = a
        cats = root["categories"][:max_categories]
        for cu in cats:
            try:
                src = cls.get_text(cu, timeout=timeout)
                ok+=1
                parsed = cls.parse_singer_directory_page(src, cu)
                for a in parsed["artists"]:
                    seen[a["url"]] = a
            except Exception:
                failed+=1
            time.sleep(STARMAKER_RATE_DELAY)
        artists = list(seen.values())
        return artists, ok, failed

    @classmethod
    def crawl_public_page(cls,
        label: str,
        url: str,
        region_code: str="",
        source_kind: str="catalog",
        timeout: int=15) -> list[dict]:
        source = cls.get_text(url, timeout=timeout)
        return cls.parse_catalog_page(source, url, label, region_code, source_kind)

    @classmethod
    def inspect_url(cls, url: str, timeout: int = 12) -> dict:
        info = cls.parse_public_url(url)
        if info["type"] in {"song", "singer", "playlist"}:
            source = cls.get_text(url, timeout=timeout)
            info.update(cls.parse_public_page(source, url))
        return info

    @staticmethod
    def _compact_number_any(text: str):
        if not text:
            return None
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*([KMB])?", str(text), re.I)
        if not m:
            return None
        try:
            num = float(m.group(1).replace(",", "."))
        except:
            return None
        mult = {"K":1_000, "M":1_000_000, "B":1_000_000_000}.get((m.group(2) or "").upper(), 1)
        return int(round(num*mult))

    @classmethod
    def _parse_visible_cover_metrics(cls, source: str) -> dict:
        """Métricas visibles de la sección Grabaciones/Recordings de una ficha pública.

        No equivalen al total de grabaciones de la pista. Se guardan por separado como
        covers visibles y reproducciones visibles para no inventar una métrica agregada.
        """
        parser = _StarMakerTokenParser()
        try:
            parser.feed(source or "")
        except Exception:
            pass
        toks = parser.tokens
        start = None
        end = len(toks)
        for i, (t, h) in enumerate(toks):
            if re.fullmatch(r"(?:Grabaciones|Recordings|Gravações)", t.strip(), re.I):
                start = i+1
                break
        if start is None:
            return {"visible_covers_count":0, "visible_plays_sum":None, "visible_plays_max":None}
        for j in range(start, len(toks)):
            t = toks[j][0].strip()
            if re.fullmatch((
                '(?:Te Podría Gustar|You May Also Like|You Might Like|Listas de reproducción '
                'relacionadas|Related Playlists|Playlists relacionadas)'
            ),
                t,
                re.I):
                end = j
                break
        plays = []
        for t, h in toks[start:end]:
            if re.search(r"\b(?:reproducciones|plays|visualizações|views)\b", t, re.I):
                n = cls._compact_number_any(t)
                if n is not None:
                    plays.append(n)
        return {"visible_covers_count":len(plays),
            "visible_plays_sum":sum(plays) if plays else None,
            "visible_plays_max":max(plays) if plays else None}

    @classmethod
    def parse_song_detail(cls,
        source: str,
        url: str,
        local_artist: str="",
        local_song: str="") -> tuple[dict|None,
        list[dict]]:
        """Extrae una pista individual pública y tarjetas relacionadas visibles.

        V1.4.4 conserva existencia aunque no haya contador agregado y, además, registra
        covers/reproducciones visibles como métrica distinta.
        """
        visible = cls._strip_tags(source)
        parsed = cls.parse_public_url(url)
        title = ""
        artist = ""
        uploaded_by = ""
        mh = re.search(r"<h1[^>]*>(.*?)</h1>", source, re.I|re.S)
        if mh:
            title = html.unescape(re.sub(r"<[^>]+>", " ", mh.group(1))).strip()
        if not title:
            mt = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', source, re.I)
            if mt:
                title = html.unescape(mt.group(1)).strip()
        title = re.sub(r"\s*[-|]\s*(?:Lyrics.*|StarMaker.*)$", "", title, flags=re.I).strip()
        # Uploader público, cuando la ficha lo expone.
        # Artista/uploader: usa tokens alrededor del H1; es más robusto que el texto colapsado.
        parser = _StarMakerTokenParser()
        try:
            parser.feed(source)
        except Exception:
            pass
        for i, (t, h) in enumerate(parser.tokens):
            mt = re.match(r"^(?:Uploaded by|Subido por|Enviado por)\s*(.*)$", t, re.I)
            if mt:
                rest = mt.group(1).strip(" -|·")
                if rest:
                    uploaded_by = rest[:120]
                elif i+1<len(parser.tokens):
                    uploaded_by = parser.tokens[i+1][0].strip(" -|·")[:120]
                break
        nt = normalize_match_text(title)
        if nt:
            for i, (t, h) in enumerate(parser.tokens):
                if normalize_match_text(t)==nt:
                    for j in range(i+1, min(len(parser.tokens), i+8)):
                        cand = parser.tokens[j][0].strip(" -|·")
                        if not cand or re.search(r"^(?:Uploaded by|Subido por|Enviado por|Track Preview|Vista previa|Lyrics|Letra|Grabaciones|Recordings)$",
                            cand,
                            re.I):
                            continue
                        if uploaded_by and normalize_match_text(cand)==normalize_match_text(uploaded_by):
                            continue
                        artist = cand[:120]
                        break
                    if artist:
                        break
        # URL slug suele conservar artista aunque la pista haya sido subida por un usuario.
        slug = urllib.parse.unquote(urllib.parse.urlparse(url).path).casefold()
        local_artist_norm = normalize_match_text(local_artist)
        slug_norm = normalize_match_text(slug).replace(" ", "")
        if local_artist and local_artist_norm.replace(" ", "") in slug_norm:
            artist = local_artist
        count = None
        # 1) Campo estructurado explícito: es la evidencia más fuerte para el total de esta pista.
        json_pat = (
            '["\\\'](?:recordingsCount|recordingCount|recording_count|record_count|singCount|sing_c'
            'ount)["\\\']\\s*[:=]\\s*["\\\']?(\\d+(?:[.,]\\d+)?\\s*[KMB]?)'
        )
        mm = re.search(json_pat, source, re.I)
        if mm:
            count = parse_compact_count(mm.group(1)+" recordings")
        # 2) Texto visible SOLO antes de las tarjetas relacionadas. Evita adjudicar a la pista
        #    los 47K/25K/etc. de "Te Podría Gustar".
        if count is None:
            head_visible = re.split((
                '\\b(?:Te Podría Gustar|You May Also Like|You Might Like|Listas de reproducción '
                'relacionadas|Related Playlists|Playlists relacionadas)\\b'
            ),
                visible,
                1,
                flags=re.I)[0]
            mm = re.search(r'(\d+(?:[.,]\d+)?\s*[KMB]?)\s+(?:recordings|grabaciones|gravações|gravacoes)\b',
                head_visible,
                re.I)
            if mm:
                count = parse_compact_count(mm.group(1)+" recordings")
        metrics = cls._parse_visible_cover_metrics(source)
        direct = None
        if title:
            verified = False
            la = local_artist_norm
            ls = _sm_base_title(local_song)
            rt = _sm_base_title(title)
            if la and (la in normalize_match_text(artist) or la.replace(" ", "") in slug_norm):
                verified = True
            if ls and rt and (ls==rt or difflib.SequenceMatcher(None, ls, rt).ratio()>=0.90):
                verified = verified or bool(local_artist)
            direct = {"public_key":_sm_public_key(title, artist or local_artist, url),
                "starmaker_song_id":parsed.get("public_id", ""),
                "url":url,
                    "title":title,
                        "artist":artist or local_artist,
                        "variant":_sm_variant(title),
                        "uploaded_by":uploaded_by,
                        "recordings_count":count,
                    "visible_covers_count":metrics["visible_covers_count"],
                        "visible_plays_sum":metrics["visible_plays_sum"],
                        "visible_plays_max":metrics["visible_plays_max"],
                    "source_url":url,
                        "source_label":local_artist or artist,
                        "source_kind":"search" if verified else "search-title",
                    "region_code":"", "position":None}
        related = cls.parse_catalog_page(source, url, artist or local_artist, "", "related")
        return direct, related

    @classmethod
    def crawl_song_detail(cls,
        url: str,
        local_artist: str="",
        local_song: str="",
        timeout: int=15) -> tuple[dict|None,
        list[dict]]:
        source = cls.get_text(url, timeout=timeout)
        return cls.parse_song_detail(source, url, local_artist, local_song)


class StarMakerWebDiscoveryClient:
    """Descubre URLs públicas oficiales para artistas/canciones ausentes del índice.

    Los buscadores públicos se usan SOLAMENTE como índice de descubrimiento. Los datos
    musicales se leen después desde starmakerstudios.com. Esto permite rescatar pistas
    subidas por usuarios que no aparecen en los directorios generales de StarMaker.
    """
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153 Safari/537.36"

    @classmethod
    def _get(cls, url, timeout=12):
        req = urllib.request.Request(url,
            headers={"User-Agent":cls.USER_AGENT, "Accept-Language":"en-US,en;q=0.8"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(1_500_000).decode(resp.headers.get_content_charset() or "utf-8",
                errors="replace")

    @staticmethod
    def _urls_from_html(source, kinds=("song", )):
        """Extrae URLs oficiales StarMaker desde HTML, XML/RSS y redirects de buscadores.

        V1.4.4 corrige una traba importante: Bing/Yahoo/Google suelen envolver el destino
        en redirects o Base64, por lo que V1.4.3 veía el resultado pero no recuperaba la URL.
        """
        import base64
        raw = source or ""
        variants = [raw, html.unescape(raw).replace("\\/", "/")]
        # Repetir unquote ayuda con URLs dobles codificadas dentro de parámetros.
        try:
            once = urllib.parse.unquote(variants[-1])
            twice = urllib.parse.unquote(once)
            variants.extend([once, twice])
        except Exception:
            pass
        src = "\n".join(dict.fromkeys(variants))
        kind_pat = "(?:"+"|".join(re.escape(k) for k in kinds)+")"
        found = []
        def add(u):
            if not u:
                return
            try:
                u = html.unescape(str(u)).replace("\\/", "/").strip().strip('\"\'<>')
                u = urllib.parse.unquote(u)
                if u.startswith("//"):
                    u = "https:"+u
                if not u.startswith("http"):
                    return
                info = StarMakerPublicClient.parse_public_url(u)
                if StarMakerPublicClient._official_url(u) and info.get("type") in set(kinds):
                    found.append(u)
            except Exception:
                pass
        # URLs directas en HTML o RSS/XML.
        pattern = rf'https?://(?:www\.)?starmakerstudios\.com/(?:[A-Za-z]{{2}}(?:-[A-Za-z]{{2}})?/)?{kind_pat}/[^"<>\s&]+'
        for m in re.finditer(pattern, src, re.I):
            add(m.group(0).rstrip(".,);'\""))
        for m in re.finditer(r'<link[^>]*>\s*(https?://[^<]+)\s*</link>', src, re.I):
            add(m.group(1))
        # DuckDuckGo: uddg=URL. Google: /url?q=URL. Yahoo: RU=URL. Redirects genéricos.
        for key in ("uddg", "q", "url", "u", "RU", "r", "target", "dest", "destination"):
            for m in re.finditer(r'(?:[?&]|\b)'+re.escape(key)+r'=([^&"<>\s]+)', src, re.I):
                val = html.unescape(m.group(1))
                for _ in range(3):
                    try:
                        dec = urllib.parse.unquote(val)
                        if dec==val:
                            break
                        val = dec
                    except Exception:
                        break
                add(val)
                # Bing usa u=a1<base64url>.
                if key.lower()=="u":
                    token = val
                    if token.startswith("a1"):
                        token = token[2:]
                    if re.fullmatch(r'[A-Za-z0-9_\-+/=]{16,}', token or ""):
                        try:
                            pad = '='*((4-len(token)%4)%4)
                            dec = base64.urlsafe_b64decode((token+pad).encode()).decode('utf-8', 'ignore')
                            add(dec)
                        except Exception:
                            pass
        # Algunos resultados de Bing incrustan el token base64 sin un parámetro fácil de aislar.
        for m in re.finditer(r'\ba1(aHR0cHM6Ly9[A-Za-z0-9_\-+/=]{12,})', src):
            try:
                token = m.group(1)
                pad = '='*((4-len(token)%4)%4)
                add(base64.urlsafe_b64decode((token+pad).encode()).decode('utf-8', 'ignore'))
            except Exception:
                pass
        out = []
        seen = set()
        for u in found:
            try:
                pp = urllib.parse.urlparse(u)
                q = urllib.parse.parse_qsl(pp.query, keep_blank_values=True)
                q = [(k, v) for k,
                    v in q if k.casefold() not in {"utm_source",
                        "utm_medium",
                        "utm_campaign",
                        "utm_content",
                        "utm_term",
                        "rut"}]
                u = urllib.parse.urlunparse((pp.scheme or "https",
                    pp.netloc,
                    pp.path,
                    pp.params,
                    urllib.parse.urlencode(q),
                    ""))
            except Exception:
                pass
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    @classmethod
    def _discover_queries(cls, queries, kinds, timeout=12, max_urls=STARMAKER_RESCUE_MAX_URLS):
        """Busca en varios índices públicos y acumula resultados, sin detenerse en el primer hit.

        V1.4.3 paraba apenas una consulta devolvía algo; si ese algo era una versión incorrecta,
        nunca probaba las variantes /es/, sin acentos o título+artista. V1.4.4 acumula hasta el límite.
        """
        errors = []
        out = []
        seen = set()
        used = []
        for qi, query in enumerate(queries):
            encoded = urllib.parse.quote_plus(query)
            for name, tpl in STARMAKER_DISCOVERY_ENGINES:
                try:
                    source = cls._get(tpl.format(query=encoded), timeout=timeout)
                    urls = cls._urls_from_html(source, kinds=kinds)
                    if urls:
                        used.append(name)
                    for u in urls:
                        if u not in seen:
                            seen.add(u)
                            out.append(u)
                            if len(out)>=max_urls:
                                return out, "+".join(dict.fromkeys(used)), errors
                except Exception as exc:
                    errors.append(f"{name}: {exc}")
            # Si ya resolvimos URLs con al menos dos formulaciones, evitamos consultas innecesarias.
            # Cuando no aparece nada, sí recorre todas las formas de rescate.
            if out and qi>=1:
                break
        return out, "+".join(dict.fromkeys(used)), errors

    @classmethod
    def _discover_queries_parallel(cls, queries, kinds, timeout=7, max_urls=24):
        """V1.4.7: consulta varios índices EN PARALELO con tiempo global acotado."""
        tasks = []
        for q in queries:
            encoded = urllib.parse.quote_plus(q)
            for name, tpl in STARMAKER_DISCOVERY_ENGINES:
                tasks.append((name, tpl.format(query=encoded)))
        found = []
        seen = set()
        used = []
        errors = []
        def one(item):
            name, url = item
            try:
                source = cls._get(url, timeout=timeout)
                return name, cls._urls_from_html(source, kinds=kinds), None
            except Exception as exc:
                return name, [], str(exc)
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=min(12, max(1, len(tasks))))
        futs = [ex.submit(one, t) for t in tasks]
        try:
            try:
                for fut in concurrent.futures.as_completed(futs, timeout=max(timeout+2, 8)):
                    name, urls, err = fut.result()
                    if err:
                        errors.append(f"{name}: {err}")
                    if urls:
                        used.append(name)
                    for u in urls:
                        if u not in seen:
                            seen.add(u)
                            found.append(u)
                            if len(found)>=max_urls:
                                return found, "+".join(dict.fromkeys(used)), errors
            except concurrent.futures.TimeoutError:
                errors.append("Índices públicos: tiempo límite global alcanzado")
        finally:
            for f in futs:
                if not f.done():
                    f.cancel()
            # MUY IMPORTANTE: no esperar a que terminen índices bloqueados/filtrados.
            ex.shutdown(wait=False, cancel_futures=True)
        return found, "+".join(dict.fromkeys(used)), errors

    @staticmethod
    def _query_forms(value):
        raw = re.sub(r"\s+", " ", (value or "").strip())
        if not raw:
            return []
        ascii_v = ''.join(c for c in unicodedata.normalize('NFKD', raw) if not unicodedata.combining(c))
        vals = [raw]
        if ascii_v.casefold()!=raw.casefold():
            vals.append(ascii_v)
        # Variantes de signos usadas a menudo en títulos subidos por usuarios.
        compact = re.sub(r"[^\w\s]", " ", ascii_v, flags=re.UNICODE)
        compact = re.sub(r"\s+", " ", compact).strip()
        if compact and normalize_match_text(compact)!=normalize_match_text(raw):
            vals.append(compact)
        return list(dict.fromkeys(vals))

    @classmethod
    def discover_artist(cls, artist, timeout=12, max_urls=12):
        forms = cls._query_forms(artist)
        queries = []
        for a in forms:
            queries += [
                f'site:starmakerstudios.com/en/singer/ "{a}"',
                f'site:starmakerstudios.com/es/singer/ "{a}"',
                f'site:starmakerstudios.com/pt-BR/singer/ "{a}"',
                f'site:starmakerstudios.com singer "{a}" StarMaker',
                f'"{a}" "StarMaker" singer songs',
            ]
        return cls._discover_queries(list(dict.fromkeys(queries)), ("singer", ), timeout, max_urls)

    @classmethod
    def discover(cls, artist, song, timeout=12, max_urls=STARMAKER_RESCUE_MAX_URLS):
        artist_forms = cls._query_forms(artist) or [artist or ""]
        song_forms = cls._query_forms(song) or [song or ""]
        queries = []
        # Primero título+artista exactos en varios locales; luego formas más flexibles para uploads de usuarios.
        for t in song_forms[:3]:
            for a in artist_forms[:3]:
                queries += [
                    f'site:starmakerstudios.com/en/song/ "{t}" "{a}"',
                    f'site:starmakerstudios.com/es/song/ "{t}" "{a}"',
                    f'site:starmakerstudios.com/pt-BR/song/ "{t}" "{a}"',
                    f'site:starmakerstudios.com "{t}" "{a}" StarMaker',
                    f'"{t}" "{a}" "StarMaker" lyrics karaoke',
                ]
            # Último recurso: título exacto sin exigir artista visible; luego se valida la ficha oficial.
            queries += [f'site:starmakerstudios.com/song/ "{t}" StarMaker', f'"{t}" "StarMaker" karaoke']
        return cls._discover_queries(list(dict.fromkeys(queries)), ("song", ), timeout, max_urls)


    @classmethod
    def discover_exact(cls, artist, song, timeout=7, max_urls=24):
        """V1.4.7: descubrimiento puntual rápido, paralelo e interpretativo.

        Prueba título+artista y título solo. Acepta /song/ y /singer/ como fuentes
        de candidatos; la IA interpretativa decide después si pertenecen a la misma obra.
        """
        a = re.sub(r"\s+", " ", (artist or "").strip())
        t = re.sub(r"\s+", " ", (song or "").strip())
        if not t:
            return [], "", []
        af = cls._query_forms(a)[:2] if a else [""]
        tf = cls._query_forms(t)[:3]
        queries = []
        for title in tf:
            for art in af:
                if art:
                    queries += [
                        f'site:starmakerstudios.com/song/ "{title}" "{art}"',
                        f'site:starmakerstudios.com "{title}" "{art}" StarMaker',
                    ]
            queries += [
                f'site:starmakerstudios.com/song/ "{title}" StarMaker',
                f'"{title}" "StarMaker" karaoke',
            ]
        return cls._discover_queries_parallel(list(dict.fromkeys(queries)),
            ("song", "singer"),
            timeout,
            max_urls)



class _CDPWebSocket:
    """Cliente WebSocket mínimo para Chrome DevTools Protocol.

    Implementado sólo con biblioteca estándar. Se conecta únicamente al puerto
    local de Edge/Chrome iniciado por Playlist Emotion Studio.
    """

    def __init__(self, ws_url, timeout=8):
        p = urllib.parse.urlparse(ws_url)
        if p.scheme != 'ws' or p.hostname not in {'127.0.0.1', 'localhost'}:
            raise ValueError('CDP sólo permite WebSocket local')
        self.sock = socket.create_connection((p.hostname, p.port), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(secrets.token_bytes(16)).decode('ascii')
        path = p.path or '/'
        if p.query:
            path+='?'+p.query
        req = (f"GET {path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
             f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: http://127.0.0.1\r\n\r\n")
        self.sock.sendall(req.encode('ascii'))
        data = b''
        while b'\r\n\r\n' not in data and len(data)<65536:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            data+=chunk
        if b' 101 ' not in data.split(b'\r\n', 1)[0]:
            raise RuntimeError('Edge/Chrome no aceptó la conexión CDP')
        self._id = 0


    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

    @staticmethod
    def _recv_exact(sock, n):
        out = b''
        while len(out)<n:
            c = sock.recv(n-len(out))
            if not c:
                raise ConnectionError('CDP cerró la conexión')
            out+=c
        return out

    def _send_text(self, text):
        payload = text.encode('utf-8')
        mask = secrets.token_bytes(4)
        n = len(payload)
        head = bytearray([0x81])
        if n<126:
            head.append(0x80|n)
        elif n<65536:
            head.append(0x80|126)
            head.extend(struct.pack('!H', n))
        else:
            head.append(0x80|127)
            head.extend(struct.pack('!Q', n))
        head.extend(mask)
        enc = bytes(b ^ mask[i%4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(head)+enc)

    def _send_control(self, opcode, payload=b''):
        mask = secrets.token_bytes(4)
        n = min(len(payload), 125)
        payload = payload[:n]
        head = bytes([0x80|opcode, 0x80|n])+mask
        enc = bytes(b ^ mask[i%4] for i, b in enumerate(payload))
        self.sock.sendall(head+enc)

    def _recv_message(self):
        fragments = []
        while True:
            h = self._recv_exact(self.sock, 2)
            b1, b2 = h[0], h[1]
            opcode = b1&0x0f
            fin = bool(b1&0x80)
            n = b2&0x7f
            if n==126:
                n = struct.unpack('!H', self._recv_exact(self.sock, 2))[0]
            elif n==127:
                n = struct.unpack('!Q', self._recv_exact(self.sock, 8))[0]
            masked = bool(b2&0x80)
            mask = self._recv_exact(self.sock, 4) if masked else None
            data = self._recv_exact(self.sock, n) if n else b''
            if mask:
                data = bytes(b ^ mask[i%4] for i, b in enumerate(data))
            if opcode==0x8:
                raise ConnectionError('CDP cerró el WebSocket')
            if opcode==0x9:
                self._send_control(0xA, data)
                continue
            if opcode in (0x1, 0x0):
                fragments.append(data)
                if fin:
                    return b''.join(fragments).decode('utf-8', 'replace')

    def call(self, method, params=None, timeout=10):
        self._id+=1
        wanted = self._id
        self.sock.settimeout(timeout)
        self._send_text(json.dumps({'id':wanted, 'method':method, 'params':params or {}}, ensure_ascii=False))
        deadline = time.time()+timeout
        while time.time()<deadline:
            obj = json.loads(self._recv_message())
            if obj.get('id')==wanted:
                if 'error' in obj:
                    raise RuntimeError(f"CDP {method}: {obj['error']}")
                return obj.get('result', {})
        raise TimeoutError(f'CDP sin respuesta: {method}')



class StarMakerDirectAPIClient:
    """V1.5.0: cliente directo al endpoint público usado por el buscador web de StarMaker.

    Endpoint observado desde DevTools del Songbook oficial:
      GET https://api.starmakerstudios.com/web/union/search?keyword=...&source=web

    No usa navegador, buscadores externos, login, cookies ni tokens. Devuelve JSON con
    artists, best y songs; record_count es el contador bruto de grabaciones por pista.
    """
    SEARCH_URL = STARMAKER_API_SEARCH_URL
    USER_AGENT = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/154.0.0.0 Safari/537.36'
    )

    @classmethod
    def _request_json(cls, keyword, timeout=10):
        params = urllib.parse.urlencode({"keyword":(keyword or "").strip(), "source":"web"})
        url = cls.SEARCH_URL+"?"+params
        headers = {
            "User-Agent":cls.USER_AGENT,
            "Accept":"application/json, text/plain, */*",
            "Accept-Language":"es-AR,es;q=0.9,en;q=0.8",
            "Origin":"https://www.starmakerstudios.com",
            "Referer":"https://www.starmakerstudios.com/",
            "Cache-Control":"no-cache",
            "Pragma":"no-cache",
        }
        last = None
        for attempt in range(3):
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    raw = r.read()
                    charset = "utf-8"
                    ctype = r.headers.get_content_charset() if hasattr(r.headers,
                        "get_content_charset") else None
                    if ctype:
                        charset = ctype
                    data = json.loads(raw.decode(charset, "replace"))
                    if not isinstance(data, dict):
                        raise ValueError("Respuesta StarMaker no es un objeto JSON")
                    return data, url
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code not in (429, 500, 502, 503, 504):
                    raise
                wait = 1.0*(attempt+1)
                try:
                    ra = exc.headers.get("Retry-After")
                    if ra:
                        wait = max(wait, float(ra))
                except Exception:
                    pass
                time.sleep(min(wait, 4.0))
            except Exception as exc:
                last = exc
                if attempt>=2:
                    break
                time.sleep(0.7*(attempt+1))
        raise RuntimeError(f"API StarMaker no respondió: {last}")

    @staticmethod
    def _entry(song, source_url, bucket="songs"):
        if not isinstance(song, dict):
            return None
        sid = str(song.get("id") or "").strip()
        title = str(song.get("title") or "").strip()
        artist = str(song.get("artist") or "").strip()
        if not sid or not title:
            return None
        count = song.get("record_count")
        try:
            count = int(count) if count is not None else None
        except Exception:
            count = None
        uploader = str(song.get("description") or "").strip()
        rinfo = song.get("r_info") or ""
        region = ""
        try:
            obj = json.loads(rinfo) if isinstance(rinfo, str) and rinfo.strip().startswith("{") else {}
            region = str(obj.get("r_country") or "").strip()
        except Exception:
            pass
        # No dependemos de reconstruir una URL amigable /song/. El ID público es suficiente
        # para deduplicar; source_url conserva la consulta API exacta y trazable.
        return {
            "public_key":"id:"+sid,
            "starmaker_song_id":sid,
            "url":"",
            "title":title,
            "artist":artist or uploader or "StarMaker",
            "variant":_sm_variant(title),
            "uploaded_by":uploader,
            "recordings_count":count,
            "source_url":source_url,
            "source_label":artist,
            "source_kind":"direct_api",
            "region_code":region,
            "position":None,
            "visible_covers_count":0,
            "visible_plays_sum":None,
            "visible_plays_max":None,
            "api_bucket":bucket,
        }

    @classmethod
    def parse_response(cls, data, source_url=""):
        entries = []
        artists = []
        for a in (data.get("artists") or []):
            if not isinstance(a, dict):
                continue
            name = str(a.get("name") or "").strip()
            aid = str(a.get("artist_id") or a.get("id") or "").strip()
            if name:
                artists.append({"artist_key":aid or normalize_match_text(name), "starmaker_artist_id":aid,
                                "artist_name":name, "url":"", "source_url":source_url})
        best = data.get("best") or {}
        if isinstance(best, dict) and best.get("type")=="song":
            e = cls._entry(best.get("song") or {}, source_url, "best")
            if e:
                entries.append(e)
        for item in (data.get("songs") or []):
            e = cls._entry(item, source_url, "songs")
            if e:
                entries.append(e)
        # Dedupe exacto por ID: si best también reaparece en songs, no se suma dos veces.
        uniq = {}
        for e in entries:
            k = e.get("public_key")
            if not k:
                continue
            old = uniq.get(k)
            if old is None or (e.get("recordings_count") is not None and (old.get("recordings_count") is None or e.get("recordings_count",
                0)>old.get("recordings_count",
                0))):
                uniq[k] = e
        return list(uniq.values()), artists

    @classmethod
    def search(cls, artist, song, timeout=10, second_pass=True):
        queries = []
        title = (song or "").strip()
        art = (artist or "").strip()
        if title:
            queries.append(title)
        all_entries = []
        all_artists = []
        diagnostics = []
        urls = []
        for ix, q in enumerate(queries):
            data, url = cls._request_json(q, timeout=timeout)
            urls.append(url)
            ent, arts = cls.parse_response(data, url)
            all_entries.extend(ent)
            all_artists.extend(arts)
            diagnostics.append(f"API '{q}': {len(ent)} pista(s)")
        # La segunda consulta título+artista sólo se usa cuando la primera no ofrece ninguna
        # evidencia aceptable del artista/título local, evitando llamadas innecesarias.
        if second_pass and title and art:
            fake_song = {"song":title, "artist":art, "genre":""}
            accepted = False
            for e in all_entries:
                try:
                    if StarMakerInterpretiveAI.score(fake_song, e).get("accept"):
                        accepted = True
                        break
                except Exception:
                    pass
            if not accepted:
                q = title+" "+art
                data, url = cls._request_json(q, timeout=timeout)
                urls.append(url)
                ent, arts = cls.parse_response(data, url)
                all_entries.extend(ent)
                all_artists.extend(arts)
                diagnostics.append(f"API '{q}': {len(ent)} pista(s)")
        uniq = {}
        for e in all_entries:
            if e.get("public_key"):
                uniq[e["public_key"]] = e
        auniq = {}
        for a in all_artists:
            auniq[a.get("artist_key") or normalize_match_text(a.get("artist_name", ""))] = a
        return list(uniq.values()), list(auniq.values()), {"engine":"StarMakerDirectAPI",
            "detail":" · ".join(diagnostics),
            "urls":urls}

class StarMakerNativeSearchClient:
    """V1.4.9: usa el buscador PROPIO de StarMaker, no Bing/DDG/Google.

    Abre /es/songSearch en Edge/Chrome headless, escribe la consulta como un usuario,
    espera los resultados dinámicos y extrae todas las fichas /song/ visibles.
    Los buscadores externos quedan sólo como último fallback.
    """
    SEARCH_URL = STARMAKER_BASE + '/es/songSearch'

    @staticmethod
    def _browser_candidates():
        return StarMakerHeadlessBrowserClient._browser_candidates()

    @staticmethod
    def _local_json(port, path, method='GET', timeout=5):
        req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8', 'replace'))

    @classmethod
    def _launch(cls, timeout=12):
        browsers = cls._browser_candidates()
        if not browsers:
            raise RuntimeError('No se encontró Edge/Chrome para usar el buscador nativo de StarMaker')
        last = None
        for browser in browsers:
            tmp = tempfile.mkdtemp(prefix='pes_sm_native_')
            proc = None
            try:
                cmd = [browser, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
                     '--disable-extensions', '--disable-sync', '--disable-background-networking',
                     '--disable-blink-features=AutomationControlled',
                         '--remote-debugging-port=0',
                         '--remote-allow-origins=*',
                     '--user-data-dir='+tmp,
                     (
                         '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                         'like Gecko) Chrome/153.0.0.0 Safari/537.36'
                     ),
                     cls.SEARCH_URL]
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      creationflags=(0x08000000 if sys.platform=='win32' else 0))
                active = Path(tmp)/'DevToolsActivePort'
                deadline = time.time()+timeout
                while time.time()<deadline and not active.exists():
                    if proc.poll() is not None:
                        break
                    time.sleep(0.10)
                if not active.exists():
                    raise RuntimeError('Edge/Chrome no abrió DevToolsActivePort')
                lines = active.read_text(encoding='utf-8', errors='replace').splitlines()
                port = int(lines[0])
                deadline = time.time()+timeout
                target = None
                while time.time()<deadline:
                    try:
                        arr = cls._local_json(port, '/json/list', timeout=2)
                        pages = [x for x in arr if x.get('type')=='page' and x.get('webSocketDebuggerUrl')]
                        if pages:
                            target = next((x for x in pages if 'starmakerstudios.com' in (x.get('url') or '')),
                                pages[0])
                            break
                    except Exception:
                        pass
                    time.sleep(0.15)
                if not target:
                    raise RuntimeError('No se encontró la pestaña CDP de StarMaker')
                ws = _CDPWebSocket(target['webSocketDebuggerUrl'], timeout=timeout)
                ws.call('Runtime.enable', timeout=5)
                ws.call('Page.enable', timeout=5)
                return proc, tmp, ws, browser
            except Exception as exc:
                last = str(exc)
                if proc:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError('Buscador nativo StarMaker no disponible: '+(last or 'sin detalle'))

    @staticmethod
    def _eval(ws, expression, timeout=10):
        r = ws.call('Runtime.evaluate',
            {'expression':expression, 'returnByValue':True, 'awaitPromise':True},
            timeout=timeout)
        return (((r or {}).get('result') or {}).get('value'))

    @classmethod
    def _wait_ready(cls, ws, timeout=12):
        deadline = time.time()+timeout
        while time.time()<deadline:
            try:
                if cls._eval(ws, 'document.readyState', timeout=2) in ('interactive', 'complete'):
                    return
            except Exception:
                pass
            time.sleep(0.2)

    @classmethod
    def _set_query(cls, ws, query):
        # Primero enfoca y vacía el input desde el DOM; luego escribe mediante CDP Input.insertText.
        # Esto dispara el flujo de entrada del navegador de forma más parecida a una persona que
        # asignar .value directamente, importante en páginas React/Vue con estado controlado.
        js = (
            "(() => {\n          const inputs=[...document.querySelectorAll('input')];\n"
            '          const score=(x)=>{\n'
            "            const s=((x.placeholder||'')+' '+(x.getAttribute('aria-label')||'')+' "
            "'+(x.name||'')).toLowerCase();\n"
            '            return (/search|buscar|song|canci|singer|artista/.test(s)?10:0)+(x.type='
            "=='search'?5:0);\n          };\n"
            '          const el=inputs.sort((a,b)=>score(b)-score(a))[0];\n'
            "          if(!el)return JSON.stringify({ok:false,reason:'input-not-found',inputs:inp"
            'uts.length,title:document.title});\n          el.focus();\n'
            "          const desc=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'val"
            "ue');\n          if(desc&&desc.set)desc.set.call(el,''); else el.value='';\n"
            "          el.dispatchEvent(new Event('input',{bubbles:true}));\n"
            "          return JSON.stringify({ok:true,placeholder:el.placeholder||'',title:docume"
            'nt.title});\n        })()'
        )
        raw = cls._eval(ws, js, timeout=5)
        try:
            state = json.loads(raw or '{}')
        except Exception:
            state = {'ok':False, 'reason':'invalid-js-result'}
        if not state.get('ok'):
            return state
        ws.call('Input.insertText', {'text':query}, timeout=5)
        ws.call('Input.dispatchKeyEvent',
            {'type':'keyDown', 'key':'Enter', 'code':'Enter', 'windowsVirtualKeyCode':13, 'nativeVirtualKeyCode':13},
            timeout=5)
        ws.call('Input.dispatchKeyEvent',
            {'type':'keyUp', 'key':'Enter', 'code':'Enter', 'windowsVirtualKeyCode':13, 'nativeVirtualKeyCode':13},
            timeout=5)
        return state

    @classmethod
    def _extract(cls, ws, max_results=80):
        js = (
            '(() => {\n          const out=[]; const seen=new Set();\n'
            '          const links=[...document.querySelectorAll(\'a[href*="/song/"]\')];\n'
            '          for(const a of links){\n'
            "            const href=a.href||''; if(!href||seen.has(href))continue; "
            'seen.add(href);\n            let n=a, best=a;\n            for(let i=0;i<8 && n;i++){\n'
            "              const tx=(n.innerText||'').trim();\n"
            '              if(tx && tx.length<1200)best=n;\n'
            '              if(/recordings|grabaciones|gravações|gravacoes/i.test(tx)){best=n;brea'
            'k;}\n              n=n.parentElement;\n            }\n'
            "            out.push({href,anchor:(a.innerText||'').trim(),text:(best.innerText||'')"
            '.trim()});\n          }\n          return JSON.stringify({url:location.href,title:docu'
            "ment.title,body:(document.body&&document.body.innerText||'').slice(0,2500),items:out"
            '});\n        })()'
        )
        raw = cls._eval(ws, js, timeout=8)
        try:
            return json.loads(raw or '{}')
        except Exception:
            return {'items':[], 'body':'', 'title':''}

    @staticmethod
    def _entry_from_item(item, local_artist='', local_song=''):
        url = item.get('href', '')
        text = (item.get('text') or '').strip()
        anchor = (item.get('anchor') or '').strip()
        lines = [re.sub(r'\s+', ' ', x).strip() for x in text.splitlines() if re.sub(r'\s+', ' ', x).strip()]
        def action(x):
            return bool(re.fullmatch(r'(?:cantar|sing|play|reproducir|ver más|view more|points)',
                x,
                re.I)) or bool(re.search(r'\b(?:recordings|grabaciones|gravações|gravacoes)\b',
                x,
                re.I))
        clean = [x for x in lines if not action(x)]
        title = anchor if anchor and not action(anchor) else (clean[0] if clean else '')
        artist = ''
        for x in clean:
            if normalize_match_text(x)!=normalize_match_text(title):
                artist = x
                break
        count = parse_compact_count(text)
        info = StarMakerPublicClient.parse_public_url(url)
        sid = info.get('public_id', '')
        if not title:
            title = local_song
        if not artist:
            artist = local_artist
        return {'public_key':('id:'+sid if sid else _sm_public_key(title, artist, url)),
                'starmaker_song_id':sid, 'url':url, 'title':title, 'artist':artist,
                'variant':_sm_variant(title), 'uploaded_by':'', 'recordings_count':count,
                'source_url':url, 'source_label':artist, 'source_kind':'native_search',
                'region_code':'',
                    'position':None,
                    'visible_covers_count':0,
                    'visible_plays_sum':None,
                    'visible_plays_max':None}

    @classmethod
    def search(cls, artist, song, timeout=28, max_results=80):
        proc = tmp = ws = None
        browser = ''
        diagnostics = []
        all_items = []
        try:
            proc, tmp, ws, browser = cls._launch(timeout=min(timeout, 15))
            cls._wait_ready(ws, timeout=10)
            queries = []
            base = (song or '').strip()
            art = (artist or '').strip()
            if base:
                queries.append(base)
            if base and art:
                queries.append(base+' '+art)
            for query in dict.fromkeys(queries):
                st = cls._set_query(ws, query)
                diagnostics.append(f"consulta '{query}': {st.get('reason') or 'input OK'}")
                if not st.get('ok'):
                    continue
                best = {'items':[]}
                deadline = time.time()+9
                while time.time()<deadline:
                    time.sleep(0.55)
                    cur = cls._extract(ws, max_results)
                    if len(cur.get('items') or [])>len(best.get('items') or []):
                        best = cur
                    if len(best.get('items') or [])>=3:
                        break
                for _ in range(2):
                    try:
                        cls._eval(ws, 'window.scrollTo(0,document.body.scrollHeight); true', timeout=2)
                    except Exception:
                        pass
                    time.sleep(0.7)
                    cur = cls._extract(ws, max_results)
                    if len(cur.get('items') or [])>len(best.get('items') or []):
                        best = cur
                diagnostics.append(f"'{query}': {len(best.get('items') or [])} enlace(s) /song/")
                all_items.extend(best.get('items') or [])
                if len(all_items)>=max_results:
                    break
            seen = set()
            entries = []
            for item in all_items:
                u = item.get('href', '')
                if not u or u in seen:
                    continue
                seen.add(u)
                e = cls._entry_from_item(item, artist, song)
                if StarMakerPublicClient._official_url(u):
                    entries.append(e)
                if len(entries)>=max_results:
                    break
            return entries, {'browser':Path(browser).name if browser else '',
                'queries':len(queries),
                'raw_results':len(all_items),
                'unique_results':len(entries),
                'detail':' | '.join(diagnostics)}
        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)


class StarMakerHeadlessBrowserClient:
    """Fallback V1.4.9: usa Edge/Chrome en modo headless para descubrir y leer
    páginas PÚBLICAS cuando los buscadores bloquean urllib con 429/Too Many Requests.
    No usa login, cookies de cuenta, APIs privadas ni automatiza credenciales.
    """

    @staticmethod
    def _browser_candidates():
        vals = []
        for exe in ("msedge.exe", "msedge", "chrome.exe", "chrome", "chromium.exe", "chromium"):
            q = shutil.which(exe)
            if q:
                vals.append(q)
        env = os.environ
        for root in (env.get("PROGRAMFILES(X86)"), env.get("PROGRAMFILES"), env.get("LOCALAPPDATA")):
            if not root:
                continue
            for rel in (r"Microsoft\Edge\Application\msedge.exe",
                r"Google\Chrome\Application\chrome.exe",
                r"Chromium\Application\chrome.exe"):
                q = str(Path(root)/rel)
                if Path(q).exists():
                    vals.append(q)
        out = []
        seen = set()
        for x in vals:
            k = os.path.normcase(os.path.abspath(x))
            if k not in seen:
                seen.add(k)
                out.append(x)
        return out

    @classmethod
    def available(cls):
        return bool(cls._browser_candidates())

    @classmethod
    def dump_dom(cls, url, timeout=20):
        browsers = cls._browser_candidates()
        if not browsers:
            raise RuntimeError("No se encontró Edge/Chrome para el fallback de navegador interno")
        last = None
        for browser in browsers:
            tmp = tempfile.mkdtemp(prefix="pes_sm_")
            try:
                cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                     "--disable-background-networking", "--disable-sync", "--disable-extensions",
                     "--user-data-dir="+tmp, "--dump-dom", url]
                cp = subprocess.run(cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    creationflags=(0x08000000 if sys.platform=="win32" else 0))
                dom = (cp.stdout or "").strip()
                if dom and "<html" in dom.casefold():
                    return dom
                last = (cp.stderr or cp.stdout or f"exit {cp.returncode}")[:500]
            except Exception as exc:
                last = str(exc)
            finally:
                try:
                    shutil.rmtree(tmp, ignore_errors=True)
                except Exception:
                    pass
        raise RuntimeError("Navegador interno sin DOM utilizable: "+(last or "sin detalle"))

    @classmethod
    def discover_exact(cls, artist, song, timeout=22, max_urls=30):
        """Descubre URLs oficiales usando un navegador REAL, sólo para una canción.
        Se activa como fallback tras 429/timeouts de búsquedas HTTP.
        """
        q1 = f'site:starmakerstudios.com/song/ "{song}" "{artist}"'
        q2 = f'site:starmakerstudios.com/singer/ "{artist}" StarMaker'
        q3 = f'site:starmakerstudios.com "{song}" "{artist}" StarMaker'
        search_urls = [
            "https://www.bing.com/search?q="+urllib.parse.quote_plus(q1)+"&count=20",
            "https://www.bing.com/search?q="+urllib.parse.quote_plus(q2)+"&count=20",
            "https://www.google.com/search?num=20&q="+urllib.parse.quote_plus(q1),
            "https://www.google.com/search?num=20&q="+urllib.parse.quote_plus(q3),
        ]
        out = []
        seen = set()
        errors = []
        for su in search_urls:
            try:
                dom = cls.dump_dom(su, timeout=timeout)
                for u in StarMakerWebDiscoveryClient._urls_from_html(dom, kinds=("song", "singer")):
                    if u not in seen:
                        seen.add(u)
                        out.append(u)
                        if len(out)>=max_urls:
                            return out, errors
            except Exception as exc:
                errors.append(str(exc))
        return out, errors

    @classmethod
    def crawl_song_detail(cls, url, local_artist="", local_song="", timeout=20):
        dom = cls.dump_dom(url, timeout=timeout)
        return StarMakerPublicClient.parse_song_detail(dom, url, local_artist, local_song)

    @classmethod
    def crawl_public_page(cls, artist, url, region="", kind="artist", timeout=20):
        dom = cls.dump_dom(url, timeout=timeout)
        return StarMakerPublicClient.parse_catalog_page(dom, url, artist, region, kind)


class Database:

    def __init__(self, path: Path = DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            raise FileNotFoundError(f"No se encontró la base inicial: {self.path}")
        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys=ON")
        self._apply_v110_migration()
        self._apply_v120_migration()
        self._apply_v130_migration()
        self._apply_v140_migration()
        self._apply_v141_migration()
        self._apply_v142_migration()
        self._apply_v143_migration()
        self._apply_v144_migration()
        self._apply_v160_migration()


    def _apply_v140_migration(self):
        """Esquema V1.4.0. Idempotente y sin modificar canciones existentes."""
        def cols(table):
            return {r[1] for r in self.con.execute(f"PRAGMA table_info({table})").fetchall()}
        setlist_cols = cols("setlists")
        additions = {
            "show_type": "TEXT NOT NULL DEFAULT 'Normal'",
            "platform": "TEXT NOT NULL DEFAULT 'StarMaker'",
            "status": "TEXT NOT NULL DEFAULT 'Borrador'",
            "starmaker_live_url": "TEXT NOT NULL DEFAULT ''",
            "starmaker_live_id": "TEXT NOT NULL DEFAULT ''",
            "timezone": "TEXT NOT NULL DEFAULT ''",
            "strategy_notes": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in setlist_cols:
                self.con.execute(f"ALTER TABLE setlists ADD COLUMN {name} {definition}")
        self.con.executescript((
            '\n            CREATE TABLE IF NOT EXISTS starmaker_song_status(\n'
            '                song_id INTEGER PRIMARY KEY REFERENCES songs(id) ON DELETE CASCADE,\n'
            "                status TEXT NOT NULL DEFAULT 'Sin investigar',\n"
            "                notes TEXT NOT NULL DEFAULT '',\n"
            "                last_checked_at TEXT NOT NULL DEFAULT ''\n            );\n"
            '            CREATE TABLE IF NOT EXISTS starmaker_tracks(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
            '                song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,\n'
            "                starmaker_song_id TEXT NOT NULL DEFAULT '',\n"
            "                starmaker_url TEXT NOT NULL DEFAULT '',\n"
            "                title TEXT NOT NULL DEFAULT '', artist TEXT NOT NULL DEFAULT '', "
            "variant TEXT NOT NULL DEFAULT '',\n"
            "                uploaded_by TEXT NOT NULL DEFAULT '', recordings_count INTEGER,\n"
            "                source_url TEXT NOT NULL DEFAULT '', match_confidence INTEGER NOT "
            'NULL DEFAULT 0,\n                is_selected INTEGER NOT NULL DEFAULT 0, '
            "last_checked_at TEXT NOT NULL DEFAULT '',\n"
            '                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT '
            'NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                UNIQUE(song_id, starmaker_url)\n'
            '            );\n            CREATE TABLE IF NOT EXISTS starmaker_snapshots(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
            '                starmaker_track_id INTEGER NOT NULL REFERENCES starmaker_tracks(id) '
            'ON DELETE CASCADE,\n                checked_at TEXT NOT NULL DEFAULT '
            'CURRENT_TIMESTAMP, recordings_count INTEGER\n            );\n'
            '            CREATE TABLE IF NOT EXISTS starmaker_links(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER REFERENCES '
            'songs(id) ON DELETE SET NULL,\n'
            "                url TEXT NOT NULL, link_type TEXT NOT NULL DEFAULT 'unknown', "
            "public_id TEXT NOT NULL DEFAULT '',\n"
            '                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(url)\n'
            '            );\n            CREATE TABLE IF NOT EXISTS starmaker_log(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL '
            "DEFAULT CURRENT_TIMESTAMP,\n                operation TEXT NOT NULL DEFAULT '', "
            "result TEXT NOT NULL DEFAULT '', error TEXT NOT NULL DEFAULT ''\n            );\n"
            '            CREATE TABLE IF NOT EXISTS show_performances(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
            '                setlist_id INTEGER REFERENCES setlists(id) ON DELETE SET NULL,\n'
            '                song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,\n'
            "                performance_date TEXT NOT NULL DEFAULT '', starmaker_live_id TEXT "
            "NOT NULL DEFAULT '',\n                starmaker_live_url TEXT NOT NULL DEFAULT '', "
            'position_in_show INTEGER,\n                viewers_peak INTEGER, viewers_average '
            'INTEGER, likes INTEGER, gifts_coins INTEGER,\n'
            '                new_followers INTEGER, comments_count INTEGER, notes TEXT NOT NULL '
            "DEFAULT '',\n                data_source TEXT NOT NULL DEFAULT 'Manual', created_at "
            'TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,\n'
            '                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP\n            );\n'
            '            CREATE TABLE IF NOT EXISTS show_audience_country(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
            '                show_performance_id INTEGER NOT NULL REFERENCES '
            'show_performances(id) ON DELETE CASCADE,\n'
            '                country TEXT NOT NULL, audience_count INTEGER, audience_percent '
            "REAL,\n                source TEXT NOT NULL DEFAULT 'Manual'\n            );\n"
            '            CREATE INDEX IF NOT EXISTS idx_sm_tracks_song ON '
            'starmaker_tracks(song_id);\n            CREATE INDEX IF NOT EXISTS '
            'idx_sm_tracks_public_id ON starmaker_tracks(starmaker_song_id);\n'
            '            CREATE INDEX IF NOT EXISTS idx_sm_snapshots_track_date ON '
            'starmaker_snapshots(starmaker_track_id,checked_at);\n'
            '            CREATE INDEX IF NOT EXISTS idx_show_perf_setlist ON '
            'show_performances(setlist_id);\n'
            '            CREATE INDEX IF NOT EXISTS idx_show_perf_song ON '
            'show_performances(song_id);\n            CREATE INDEX IF NOT EXISTS '
            'idx_show_country_perf ON show_audience_country(show_performance_id);\n        '
        ))
        self.con.execute("INSERT INTO settings(key,value) VALUES('patch_v1_4_0_schema','1') ON CONFLICT(key) DO UPDATE SET value='1'")
        self.con.commit()


    def _apply_v141_migration(self):
        """AutoData V1.4.1: índice público local + charts + ejecuciones de rastreo."""
        self.con.executescript((
            '\n            CREATE TABLE IF NOT EXISTS starmaker_public_catalog(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
            '                public_key TEXT NOT NULL UNIQUE,\n'
            "                starmaker_song_id TEXT NOT NULL DEFAULT '',\n"
            "                url TEXT NOT NULL DEFAULT '',\n"
            "                title TEXT NOT NULL DEFAULT '', artist TEXT NOT NULL DEFAULT '', "
            "variant TEXT NOT NULL DEFAULT '',\n"
            "                normalized_title TEXT NOT NULL DEFAULT '', normalized_artist TEXT "
            "NOT NULL DEFAULT '',\n                recordings_count INTEGER,\n"
            "                source_url TEXT NOT NULL DEFAULT '', source_label TEXT NOT NULL "
            "DEFAULT '',\n                source_kind TEXT NOT NULL DEFAULT 'catalog', "
            "region_code TEXT NOT NULL DEFAULT '', position INTEGER,\n"
            "                uploaded_by TEXT NOT NULL DEFAULT '', visible_covers_count INTEGER "
            'NOT NULL DEFAULT 0,\n                visible_plays_sum INTEGER, visible_plays_max '
            'INTEGER,\n                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, '
            'last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP\n            );\n'
            '            CREATE TABLE IF NOT EXISTS starmaker_auto_match(\n'
            '                song_id INTEGER PRIMARY KEY REFERENCES songs(id) ON DELETE CASCADE,\n'
            "                public_key TEXT NOT NULL DEFAULT '', confidence INTEGER NOT NULL "
            "DEFAULT 0,\n                status TEXT NOT NULL DEFAULT 'Sin datos', updated_at "
            'TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP\n            );\n'
            '            CREATE TABLE IF NOT EXISTS starmaker_chart_presence(\n'
            '                public_key TEXT NOT NULL, chart_code TEXT NOT NULL, chart_name TEXT '
            "NOT NULL DEFAULT '',\n                position INTEGER, first_seen_at TEXT NOT NULL "
            'DEFAULT CURRENT_TIMESTAMP,\n                last_seen_at TEXT NOT NULL DEFAULT '
            'CURRENT_TIMESTAMP,\n                PRIMARY KEY(public_key,chart_code)\n            );\n'
            '            CREATE TABLE IF NOT EXISTS starmaker_scan_runs(\n'
            '                id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL '
            "DEFAULT CURRENT_TIMESTAMP,\n                finished_at TEXT NOT NULL DEFAULT '', "
            "status TEXT NOT NULL DEFAULT 'running',\n"
            '                pages_ok INTEGER NOT NULL DEFAULT 0, pages_failed INTEGER NOT NULL '
            'DEFAULT 0,\n                entries_found INTEGER NOT NULL DEFAULT 0, matched_songs '
            "INTEGER NOT NULL DEFAULT 0,\n                message TEXT NOT NULL DEFAULT ''\n"
            '            );\n            CREATE INDEX IF NOT EXISTS idx_sm_public_norm ON '
            'starmaker_public_catalog(normalized_title,normalized_artist);\n'
            '            CREATE INDEX IF NOT EXISTS idx_sm_public_recordings ON '
            'starmaker_public_catalog(recordings_count);\n'
            '            CREATE INDEX IF NOT EXISTS idx_sm_chart_code ON '
            'starmaker_chart_presence(chart_code,position);\n        '
        ))
        self.con.execute("INSERT INTO settings(key,value) VALUES('patch_v1_4_1_schema','1') ON CONFLICT(key) DO UPDATE SET value='1'")
        self.con.commit()
        # Caché inicial verificable: permite que V1.4.1 muestre datos desde el primer arranque,
        # aun antes del primer rastreo de red. Luego AutoData los actualiza desde StarMaker.
        loaded = self.con.execute("SELECT value FROM settings WHERE key='starmaker_seed_v141_loaded'").fetchone()
        if (not loaded or loaded[0] != '1') and STARMAKER_SEED_PATH.exists():
            try:
                seed = json.loads(STARMAKER_SEED_PATH.read_text(encoding='utf-8'))
                self.sm_ingest_entries(seed)
                self.sm_auto_match()
                self.con.execute((
                    "INSERT INTO settings(key,value) VALUES('starmaker_seed_v141_loaded','1') ON "
                    "CONFLICT(key) DO UPDATE SET value='1'"
                ))
                self.con.commit()
            except Exception as exc:
                try:
                    self.log_starmaker("Seed V1.4.1", "No cargado", str(exc))
                except Exception:
                    pass

    def _apply_v142_migration(self):
        """V1.4.2 Deep Match: directorio de artistas + todas las variantes públicas compatibles."""
        self.con.executescript((
            '\n            CREATE TABLE IF NOT EXISTS starmaker_artist_directory(\n'
            '                artist_key TEXT PRIMARY KEY,\n'
            "                starmaker_artist_id TEXT NOT NULL DEFAULT '',\n"
            "                artist_name TEXT NOT NULL DEFAULT '',\n"
            "                normalized_artist TEXT NOT NULL DEFAULT '',\n"
            "                url TEXT NOT NULL DEFAULT '',\n"
            "                source_url TEXT NOT NULL DEFAULT '',\n"
            '                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,\n'
            '                last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP\n            );\n'
            '            CREATE TABLE IF NOT EXISTS starmaker_artist_scan_state(\n'
            '                artist_key TEXT PRIMARY KEY,\n'
            "                last_scan_at TEXT NOT NULL DEFAULT '',\n"
            "                status TEXT NOT NULL DEFAULT 'Pendiente',\n"
            '                entries_found INTEGER NOT NULL DEFAULT 0,\n'
            "                error TEXT NOT NULL DEFAULT ''\n            );\n"
            '            CREATE TABLE IF NOT EXISTS starmaker_song_matches(\n'
            '                song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,\n'
            '                public_key TEXT NOT NULL,\n'
            '                confidence INTEGER NOT NULL DEFAULT 0,\n'
            "                match_type TEXT NOT NULL DEFAULT '',\n"
            '                included_in_total INTEGER NOT NULL DEFAULT 0,\n'
            '                is_primary INTEGER NOT NULL DEFAULT 0,\n'
            '                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,\n'
            '                PRIMARY KEY(song_id, public_key)\n            );\n'
            '            CREATE INDEX IF NOT EXISTS idx_sm_artist_norm ON '
            'starmaker_artist_directory(normalized_artist);\n'
            '            CREATE INDEX IF NOT EXISTS idx_sm_artist_url ON '
            'starmaker_artist_directory(url);\n'
            '            CREATE INDEX IF NOT EXISTS idx_sm_song_matches_song ON '
            'starmaker_song_matches(song_id,included_in_total,is_primary);\n'
            '            CREATE INDEX IF NOT EXISTS idx_sm_song_matches_public ON '
            'starmaker_song_matches(public_key);\n        '
        ))
        first = self.con.execute("SELECT value FROM settings WHERE key='patch_v1_4_2_initialized'").fetchone()
        self.con.execute("INSERT INTO settings(key,value) VALUES('patch_v1_4_2_schema','1') ON CONFLICT(key) DO UPDATE SET value='1'")
        if not first:
            # Fuerza un primer rastreo profundo aun si V1.4.1 se actualizó hace pocas horas.
            self.con.execute((
                "INSERT INTO settings(key,value) VALUES('starmaker_last_auto_scan','') ON "
                "CONFLICT(key) DO UPDATE SET value='' "
            ))
            self.con.execute((
                "INSERT INTO settings(key,value) VALUES('patch_v1_4_2_initialized','1') ON "
                "CONFLICT(key) DO UPDATE SET value='1'"
            ))
        self.con.commit()
        if not first:
            try:
                self.sm_auto_match()
            except Exception:
                pass

    def _apply_v143_migration(self):
        """V1.4.3 Coverage Recovery: rescate título por título y páginas duplicadas de artista."""
        self.con.executescript("""
            CREATE TABLE IF NOT EXISTS starmaker_rescue_state(
                song_id INTEGER PRIMARY KEY REFERENCES songs(id) ON DELETE CASCADE,
                last_scan_at TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Pendiente',
                urls_found INTEGER NOT NULL DEFAULT 0,
                entries_found INTEGER NOT NULL DEFAULT 0,
                engine TEXT NOT NULL DEFAULT '',
                error TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_sm_rescue_status ON starmaker_rescue_state(status,last_scan_at);
        """)
        first = self.con.execute("SELECT value FROM settings WHERE key='patch_v1_4_3_initialized'").fetchone()
        self.con.execute("INSERT INTO settings(key,value) VALUES('patch_v1_4_3_schema','1') ON CONFLICT(key) DO UPDATE SET value='1'")
        if not first:
            # Fuerza reconstrucción del directorio con IDs de query y varias páginas por artista.
            self.con.execute("DELETE FROM starmaker_artist_scan_state")
            self.con.execute((
                "INSERT INTO settings(key,value) VALUES('starmaker_last_auto_scan','') ON "
                "CONFLICT(key) DO UPDATE SET value=''"
            ))
            self.con.execute((
                "INSERT INTO settings(key,value) VALUES('patch_v1_4_3_initialized','1') ON "
                "CONFLICT(key) DO UPDATE SET value='1'"
            ))
        self.con.commit()


    def _apply_v144_migration(self):
        """V1.4.4 Exhaustive Resolver: retry manual + métricas visibles de covers."""
        cols = {r[1] for r in self.con.execute("PRAGMA table_info(starmaker_public_catalog)").fetchall()}
        additions = {
            "uploaded_by":"TEXT NOT NULL DEFAULT ''",
            "visible_covers_count":"INTEGER NOT NULL DEFAULT 0",
            "visible_plays_sum":"INTEGER",
            "visible_plays_max":"INTEGER",
        }
        for name, ddl in additions.items():
            if name not in cols:
                self.con.execute(f"ALTER TABLE starmaker_public_catalog ADD COLUMN {name} {ddl}")
        first = self.con.execute("SELECT value FROM settings WHERE key='patch_v1_4_4_initialized'").fetchone()
        self.con.execute("INSERT INTO settings(key,value) VALUES('patch_v1_4_4_schema','1') ON CONFLICT(key) DO UPDATE SET value='1'")
        if not first:
            # Los 'Sin resultado' de V1.4.3 deben poder reintentarse inmediatamente con el resolver nuevo.
            self.con.execute("DELETE FROM starmaker_rescue_state WHERE status NOT LIKE 'Encontrada%'")
            self.con.execute("DELETE FROM starmaker_artist_scan_state WHERE status<>'OK'")
            self.con.execute((
                "INSERT INTO settings(key,value) VALUES('starmaker_last_auto_scan','') ON "
                "CONFLICT(key) DO UPDATE SET value=''"
            ))
            self.con.execute((
                "INSERT INTO settings(key,value) VALUES('patch_v1_4_4_initialized','1') ON "
                "CONFLICT(key) DO UPDATE SET value='1'"
            ))
        self.con.commit()

    def _apply_v160_migration(self):
        """Intelligence Dashboard and platform metadata layer introduced in V1.6.0."""
        cols = {r[1] for r in self.con.execute("PRAGMA table_info(songs)").fetchall()}
        additions = {
            "youtube_channel_id":"TEXT NOT NULL DEFAULT ''",
            "youtube_comments":"INTEGER",
            "youtube_published_at":"TEXT NOT NULL DEFAULT ''",
            "youtube_duration_seconds":"INTEGER",
            "youtube_match_confidence":"INTEGER NOT NULL DEFAULT 0",
            "spotify_track_id":"TEXT NOT NULL DEFAULT ''",
            "spotify_title":"TEXT NOT NULL DEFAULT ''",
            "spotify_artist":"TEXT NOT NULL DEFAULT ''",
            "spotify_album":"TEXT NOT NULL DEFAULT ''",
            "spotify_release_date":"TEXT NOT NULL DEFAULT ''",
            "spotify_duration_ms":"INTEGER",
            "spotify_explicit":"INTEGER",
            "spotify_isrc":"TEXT NOT NULL DEFAULT ''",
            "spotify_match_confidence":"INTEGER NOT NULL DEFAULT 0",
        }
        for name, ddl in additions.items():
            if name not in cols:
                self.con.execute(f"ALTER TABLE songs ADD COLUMN {name} {ddl}")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_songs_youtube_video_id ON songs(youtube_video_id)")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_songs_spotify_track_id ON songs(spotify_track_id)")
        defaults = {
            "ui_language":"es",
            "youtube_search_daily_limit":"40",
            "youtube_search_day":"",
            "youtube_search_count":"0",
            "spotify_client_id":"",
            "spotify_redirect_base":"http://127.0.0.1/callback",
            "spotify_access_token":"",
            "spotify_refresh_token":"",
            "spotify_token_expires_at":"0",
            "patch_v1_6_0_schema":"1",
        }
        for k, v in defaults.items():
            self.con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO NOTHING",
                (k, v))
        self.con.commit()

    def close(self):
        try:
            self.con.close()
        except Exception:
            pass

    def setting(self, key: str, default="") -> str:
        row = self.con.execute("SELECT value FROM settings WHERE key=?", (key, )).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        self.con.execute(
            "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.con.commit()

    def dashboard(self):
        total = self.con.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
        unique = self.con.execute(
            "SELECT COUNT(*) FROM (SELECT lower(artist),lower(song) FROM songs GROUP BY lower(artist),lower(song))"
        ).fetchone()[0]
        seconds = self.con.execute("SELECT COALESCE(SUM(duration_seconds),0) FROM songs").fetchone()[0]
        countries = self.con.execute(
            "SELECT COUNT(DISTINCT country) FROM songs WHERE trim(country)<>''"
        ).fetchone()[0]
        emotions = dict(self.con.execute(
            "SELECT emotion_type, COUNT(*) FROM songs GROUP BY emotion_type"
        ).fetchall())
        levels = dict(self.con.execute(
            "SELECT emotion_level, COUNT(*) FROM songs GROUP BY emotion_level"
        ).fetchall())
        sources = self.con.execute(
            "SELECT source_sheet, COUNT(*) n FROM songs GROUP BY source_sheet ORDER BY n DESC"
        ).fetchall()
        return {
            "total": total, "unique": unique, "seconds": seconds, "countries": countries,
            "emotions": emotions, "levels": levels, "sources": sources,
        }


    def intelligence_dashboard(self):
        base = self.dashboard()
        total = base["total"]
        sm_found = self.con.execute("SELECT COUNT(DISTINCT song_id) FROM starmaker_song_matches WHERE included_in_total=1").fetchone()[0]
        sm_recordings = self.con.execute("""SELECT COALESCE(SUM(x.total),0) FROM (
            SELECT m.song_id,SUM(COALESCE(p.recordings_count,0)) total
            FROM starmaker_song_matches m JOIN starmaker_public_catalog p ON p.public_key=m.public_key
            WHERE m.included_in_total=1 GROUP BY m.song_id) x""").fetchone()[0]
        sm_tracks = self.con.execute("SELECT COUNT(*) FROM starmaker_song_matches WHERE included_in_total=1").fetchone()[0]
        yt_found = self.con.execute("SELECT COUNT(*) FROM songs WHERE trim(youtube_video_id)<>''").fetchone()[0]
        sp_found = self.con.execute("SELECT COUNT(*) FROM songs WHERE trim(spotify_track_id)<>''").fetchone()[0]
        sl = self.con.execute("SELECT * FROM setlists ORDER BY updated_at DESC,id DESC LIMIT 1").fetchone()
        playlist = None
        if sl:
            q = self.con.execute((
                'SELECT COUNT(*),COALESCE(SUM(s.duration_seconds),0) FROM setlist_items si JOIN '
                'songs s ON s.id=si.song_id WHERE si.setlist_id=?'
            ),
                (sl["id"], )).fetchone()
            playlist = {"id":sl["id"],
                "name":sl["name"],
                "songs":int(q[0]),
                "seconds":int(q[1] or 0),
                "target_minutes":int(sl["target_minutes"] or 0)}
        top_sm = self.con.execute((
            'SELECT s.song,s.artist,SUM(COALESCE(p.recordings_count,0)) recordings\n'
            '            FROM starmaker_song_matches m JOIN starmaker_public_catalog p ON '
            'p.public_key=m.public_key JOIN songs s ON s.id=m.song_id\n'
            '            WHERE m.included_in_total=1 GROUP BY m.song_id ORDER BY recordings DESC '
            'LIMIT 10'
        )).fetchall()
        top_source = self.con.execute("SELECT source_sheet,COUNT(*) n FROM songs GROUP BY source_sheet ORDER BY n DESC LIMIT 1").fetchone()
        top_genre = self.con.execute("SELECT genre,COUNT(*) n FROM songs WHERE trim(genre)<>'' GROUP BY genre ORDER BY n DESC LIMIT 1").fetchone()
        return {**base, "sm_found":sm_found, "sm_recordings":sm_recordings, "sm_tracks":sm_tracks,
                "sm_coverage":(sm_found*100.0/total if total else 0.0),
                    "youtube_found":yt_found,
                    "spotify_found":sp_found,
                "youtube_coverage":(yt_found*100.0/total if total else 0.0),
                    "spotify_coverage":(sp_found*100.0/total if total else 0.0),
                "playlist":playlist, "top_sm":top_sm, "top_source":top_source, "top_genre":top_genre}

    def platform_rows(self, search="", limit=5000):
        where = "1=1"
        params = []
        if search.strip():
            q = "%"+search.strip()+"%"
            where = "(s.song LIKE ? COLLATE NOCASE OR s.artist LIKE ? COLLATE NOCASE)"
            params = [q, q]
        sql = f"""SELECT s.*,
          (SELECT COUNT(*) FROM starmaker_song_matches m WHERE m.song_id=s.id AND m.included_in_total=1) sm_tracks,
          (SELECT SUM(p.recordings_count) FROM starmaker_song_matches m JOIN starmaker_public_catalog p ON p.public_key=m.public_key WHERE m.song_id=s.id AND m.included_in_total=1 AND p.recordings_count IS NOT NULL) sm_recordings
          FROM songs s WHERE {where} ORDER BY s.position,s.artist COLLATE NOCASE,s.song COLLATE NOCASE LIMIT ?"""
        return self.con.execute(sql, params+[limit]).fetchall()

    def save_youtube_metadata(self, song_id:int, data:dict):
        fields = ["youtube_video_id",
            "youtube_title",
            "youtube_channel",
            "youtube_channel_id",
            "youtube_views",
            "youtube_likes",
            "youtube_comments",
            "youtube_published_at",
            "youtube_duration_seconds",
            "youtube_match_confidence",
            "youtube_updated_at"]
        vals = [data.get(k) for k in fields]
        self.con.execute("UPDATE songs SET "+",".join(f"{k}=?" for k in fields)+",updated_at=CURRENT_TIMESTAMP WHERE id=?",
            vals+[song_id])
        self.con.commit()

    def save_spotify_metadata(self, song_id:int, data:dict):
        fields = ["spotify_track_id",
            "spotify_title",
            "spotify_artist",
            "spotify_album",
            "spotify_release_date",
            "spotify_duration_ms",
            "spotify_explicit",
            "spotify_isrc",
            "spotify_url",
            "spotify_match_confidence",
            "spotify_updated_at"]
        vals = [data.get(k) for k in fields]
        self.con.execute("UPDATE songs SET "+",".join(f"{k}=?" for k in fields)+",updated_at=CURRENT_TIMESTAMP WHERE id=?",
            vals+[song_id])
        self.con.commit()

    def youtube_search_allowance(self):
        day = today_iso()
        stored = self.setting("youtube_search_day", "")
        count = int(self.setting("youtube_search_count", "0") or 0)
        limit = int(self.setting("youtube_search_daily_limit", "40") or 40)
        if stored!=day:
            count = 0
            self.set_setting("youtube_search_day", day)
            self.set_setting("youtube_search_count", "0")
        return max(0, limit-count), count, limit

    def youtube_register_search(self, n=1):
        remaining, count, limit = self.youtube_search_allowance()
        new = min(limit, count+int(n))
        self.set_setting("youtube_search_count", str(new))
        return max(0, limit-new)

    def distinct(self, field: str):
        if field not in {"genre", "country", "source_sheet"}:
            return []
        return [r[0] for r in self.con.execute(
            f"SELECT DISTINCT {field} FROM songs WHERE trim({field})<>'' ORDER BY {field} COLLATE NOCASE"
        ).fetchall()]

    def songs(self, search="", source="", emotion="", level="", genre="", country="", year="", limit=5000):
        where = ["1=1"]
        params = []
        if search.strip():
            q = f"%{search.strip()}%"
            where.append((
                '(artist LIKE ? COLLATE NOCASE OR song LIKE ? COLLATE NOCASE OR description LIKE ? '
                'COLLATE NOCASE OR notes LIKE ? COLLATE NOCASE)'
            ))
            params += [q, q, q, q]
        # V1.3.4: el origen es una categoría, no texto libre.
        # Debe coincidir EXACTAMENTE para evitar que "RockRomanticos"
        # también encuentre "InternacionalRockRomanticos".
        if source.strip():
            where.append("trim(source_sheet)=? COLLATE NOCASE")
            params.append(source.strip())
        if emotion:
            where.append("emotion_type=?")
            params.append(emotion)
        if level:
            where.append("emotion_level=?")
            params.append(level)
        if genre.strip():
            where.append("genre LIKE ? COLLATE NOCASE")
            params.append(f"%{genre.strip()}%")
        if country.strip():
            where.append("country LIKE ? COLLATE NOCASE")
            params.append(f"%{country.strip()}%")
        if year.strip():
            where.append("year LIKE ? COLLATE NOCASE")
            params.append(f"%{year.strip()}%")
        sql = f"""
        SELECT * FROM songs WHERE {' AND '.join(where)}
        ORDER BY CASE emotion_type WHEN 'Positiva' THEN 1 WHEN 'Neutra' THEN 2 WHEN 'Negativa' THEN 3 ELSE 9 END,
                 CASE emotion_level WHEN 'Principal' THEN 1 WHEN 'Secundaria' THEN 2 ELSE 9 END,
                 position, artist COLLATE NOCASE, song COLLATE NOCASE
        LIMIT ?"""
        params.append(limit)
        return self.con.execute(sql, params).fetchall()

    def get_song(self, song_id: int):
        return self.con.execute("SELECT * FROM songs WHERE id=?", (song_id, )).fetchone()

    def _apply_v110_migration(self):
        """Corrige la inversión Principal/Secundaria una sola vez y normaliza el orden global.

        V1.0 importó los niveles al revés. El marcador en settings evita que el cambio
        vuelva a ejecutarse en arranques posteriores.
        """
        marker = "patch_v1_1_0_levels_swapped"
        if self.setting(marker, "") == "1":
            return
        try:
            self.con.execute("BEGIN IMMEDIATE")
            self.con.execute(
                """UPDATE songs
                   SET emotion_level = CASE emotion_level
                       WHEN 'Principal' THEN 'Secundaria'
                       WHEN 'Secundaria' THEN 'Principal'
                       ELSE emotion_level END,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE emotion_level IN ('Principal','Secundaria')"""
            )
            # V1.0 numeraba por biblioteca de origen. V1.1 usa un orden único por
            # Tipo de emoción + Nivel, evitando #1 repetidos en una misma pestaña.
            for emotion in EMOTIONS:
                for level in LEVELS:
                    rows = self.con.execute(
                        """SELECT id FROM songs
                           WHERE emotion_type=? AND emotion_level=?
                           ORDER BY source_sheet COLLATE NOCASE, position, id""",
                        (emotion, level),
                    ).fetchall()
                    for i, row in enumerate(rows, 1):
                        self.con.execute(
                            "UPDATE songs SET position=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            (i, row[0]),
                        )
            self.con.execute(
                "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (marker, "1"),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise

    def _apply_v120_migration(self):
        """Retira General como nivel de canción y añade trazabilidad de género."""
        marker = "patch_v1_2_0_schema"
        if self.setting(marker, "") == "1":
            return
        try:
            self.con.execute("BEGIN IMMEDIATE")
            cols = {r[1] for r in self.con.execute("PRAGMA table_info(songs)").fetchall()}
            additions = {
                "genre_original": "TEXT NOT NULL DEFAULT ''",
                "genre_source": "TEXT NOT NULL DEFAULT ''",
                "genre_confidence": "INTEGER NOT NULL DEFAULT 0",
                "genre_checked_at": "TEXT NOT NULL DEFAULT ''",
                "musicbrainz_recording_id": "TEXT NOT NULL DEFAULT ''",
                "musicbrainz_artist_id": "TEXT NOT NULL DEFAULT ''",
            }
            for name, ddl in additions.items():
                if name not in cols:
                    self.con.execute(f"ALTER TABLE songs ADD COLUMN {name} {ddl}")
            self.con.execute("UPDATE songs SET genre_original=genre WHERE trim(genre_original)='' AND trim(genre)<>''")
            self.con.execute((
                "UPDATE songs SET genre_source='Importado del Excel · categoría amplia' WHERE "
                "trim(genre_source)='' AND trim(genre)<>''"
            ))
            # General deja de ser un nivel asignable. Si hubiese algún registro accidental,
            # se conserva como Secundaria para que nunca quede oculto.
            self.con.execute("UPDATE songs SET emotion_level='Secundaria', updated_at=CURRENT_TIMESTAMP WHERE emotion_level='General'")
            for emotion in EMOTIONS:
                for level in LEVELS:
                    rows = self.con.execute(
                        "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? ORDER BY position,id",
                        (emotion, level),
                    ).fetchall()
                    self._rewrite_order(emotion, level, [r[0] for r in rows])
            self.con.execute(
                "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (marker, "1"),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise

    def _apply_v130_migration(self):
        """Aplica el catálogo curado V1.3.0 a todas las coincidencias artista+canción.

        Conserva genre_original como trazabilidad del Excel/V1.x y sólo sustituye el
        campo operativo genre. El marcador impide reaplicar el catálogo en cada inicio.
        """
        marker = "patch_v1_3_0_curated_genres"
        if self.setting(marker, "") == "1" or not CURATED_GENRE_PATH.exists():
            return
        def nk(value):
            import unicodedata
            value = (value or "").strip().lower().replace("’", "'").replace("`", "'")
            value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))
            return re.sub(r"\s+", " ", value)
        mapping = {}
        with CURATED_GENRE_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            for item in csv.DictReader(f):
                mapping[(nk(item.get("artist")), nk(item.get("song")))] = item
        try:
            self.con.execute("BEGIN IMMEDIATE")
            rows = self.con.execute("SELECT id,artist,song FROM songs").fetchall()
            matched = 0
            for row in rows:
                item = mapping.get((nk(row["artist"]), nk(row["song"])))
                if not item:
                    continue
                genre = (item.get("genre") or "").strip()
                source = (item.get("source") or "Catálogo curado V1.3.0").strip()
                try:
                    confidence = int(item.get("confidence") or 0)
                except Exception:
                    confidence = 0
                self.con.execute(
                    """UPDATE songs SET genre=?, genre_source=?, genre_confidence=?,
                       genre_checked_at=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (genre, f"V1.3 · {source}", confidence, today_iso(), row["id"]),
                )
                matched+=1
            self.con.execute(
                "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (marker, "1"),
            )
            self.con.execute(
                "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                ("patch_v1_3_0_genres_matched", str(matched)),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise

    def distinct_years(self):
        vals = [str(r[0]).strip() for r in self.con.execute(
            "SELECT DISTINCT year FROM songs WHERE trim(year)<>''"
        ).fetchall()]
        def key(v):
            m = re.search(r"\d{4}", v)
            return int(m.group()) if m else -1
        return sorted(set(vals), key=lambda v: (key(v), v), reverse=True)

    def update_song_genre_research(self, song_id: int, result: dict, min_confidence: int = 60):
        row = self.get_song(song_id)
        if not row:
            return False
        genre = (result.get("genre") or "").strip()
        conf = int(result.get("confidence") or 0)
        source = (result.get("source") or "").strip()
        rid = (result.get("recording_id") or "").strip()
        aid = (result.get("artist_id") or "").strip()
        # Sólo reemplaza el género si hay una coincidencia razonable. Siempre guarda trazabilidad.
        if genre and conf >= min_confidence:
            self.con.execute(
                (
                    'UPDATE songs SET genre=?, genre_source=?, genre_confidence=?, genre_checked_at=?,\n'
                    '                   musicbrainz_recording_id=?, musicbrainz_artist_id=?, '
                    'updated_at=CURRENT_TIMESTAMP WHERE id=?'
                ),
                (genre, source, conf, today_iso(), rid, aid, song_id),
            )
            changed = True
        else:
            self.con.execute(
                (
                    'UPDATE songs SET genre_source=?, genre_confidence=?, genre_checked_at=?,\n'
                    '                   musicbrainz_recording_id=?, musicbrainz_artist_id=?, '
                    'updated_at=CURRENT_TIMESTAMP WHERE id=?'
                ),
                (source, conf, today_iso(), rid, aid, song_id),
            )
            changed = False
        self.con.commit()
        return changed

    def count_group(self, emotion, level):
        return self.con.execute(
            "SELECT COUNT(*) FROM songs WHERE emotion_type=? AND emotion_level=?",
            (emotion, level),
        ).fetchone()[0]

    def normalize_group(self, emotion, level):
        rows = self.con.execute(
            "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? ORDER BY position,id",
            (emotion, level),
        ).fetchall()
        for i, row in enumerate(rows, 1):
            self.con.execute("UPDATE songs SET position=? WHERE id=?", (i, row[0]))

    def _rewrite_order(self, emotion: str, level: str, ordered_ids: list[int]):
        # Dos pasadas evitan posiciones ambiguas durante movimientos complejos.
        for i, sid in enumerate(ordered_ids, 1):
            self.con.execute(
                "UPDATE songs SET position=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (100000 + i, sid),
            )
        for i, sid in enumerate(ordered_ids, 1):
            self.con.execute(
                "UPDATE songs SET position=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (i, sid),
            )

    def save_song(self, data: dict, song_id: int | None = None):
        sec = duration_to_seconds(data.get("duration", ""))
        data = dict(data)
        data["duration_seconds"] = sec
        target_emotion = data["emotion_type"]
        target_level = data["emotion_level"]
        requested_pos = int(data.get("position") or 0)

        try:
            self.con.execute("BEGIN IMMEDIATE")
            if song_id:
                old = self.get_song(song_id)
                old_genre = old["genre"]
                old_group = (old["emotion_type"], old["emotion_level"])
                fields = ["source_sheet",
                    "artist",
                    "song",
                    "country",
                    "year",
                    "duration",
                    "duration_seconds",
                    "genre",
                    "emotion_type",
                    "emotion_level",
                    "description",
                    "notes"]
                set_sql = ",".join(f"{f}=?" for f in fields)
                # Se pone temporalmente al final; luego se inserta exactamente en la posición pedida.
                self.con.execute(
                    f"UPDATE songs SET {set_sql}, position=999999, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    [data.get(f, "") for f in fields] + [song_id],
                )
                if data.get("genre", "").strip() != (old_genre or "").strip():
                    self.con.execute(
                        (
                            "UPDATE songs SET genre_source='Manual', genre_confidence=100, genre_checked_at=?, "
                            'updated_at=CURRENT_TIMESTAMP WHERE id=?'
                        ),
                        (today_iso(), song_id),
                    )
                if old_group != (target_emotion, target_level):
                    self.normalize_group(*old_group)
                self.normalize_group(target_emotion, target_level)
            else:
                self.con.execute(
                    (
                        'INSERT INTO songs(source_sheet,source_row,position,artist,song,country,year,duration'
                        ',duration_seconds,genre,emotion_type,emotion_level,description,notes)\n'
                        '                    VALUES (?,?,999999,?,?,?,?,?,?,?,?,?,?,?)'
                    ),
                    (data["source_sheet"], 0, data["artist"], data["song"], data.get("country", ""), data.get("year", ""), data.get("duration", ""), sec, data.get("genre", ""), target_emotion, target_level, data.get("description", ""), data.get("notes", "")),
                )
                song_id = self.con.execute("SELECT last_insert_rowid()").fetchone()[0]
                if data.get("genre", "").strip():
                    self.con.execute(
                        (
                            "UPDATE songs SET genre_original=?, genre_source='Manual', genre_confidence=100, "
                            'genre_checked_at=? WHERE id=?'
                        ),
                        (data.get("genre", "").strip(), today_iso(), song_id),
                    )
                self.normalize_group(target_emotion, target_level)

            maxpos = self.count_group(target_emotion, target_level)
            if requested_pos <= 0:
                requested_pos = maxpos
            requested_pos = max(1, min(maxpos, requested_pos))
            ids = [r[0] for r in self.con.execute(
                "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? ORDER BY position,id",
                (target_emotion, target_level),
            ).fetchall()]
            if song_id in ids:
                ids.remove(song_id)
            ids.insert(requested_pos - 1, song_id)
            self._rewrite_order(target_emotion, target_level, ids)
            self.con.commit()
            return song_id
        except Exception:
            self.con.rollback()
            raise

    def delete_song(self, song_id: int):
        row = self.get_song(song_id)
        if not row:
            return
        try:
            self.con.execute("BEGIN IMMEDIATE")
            self.con.execute("DELETE FROM songs WHERE id=?", (song_id, ))
            self.normalize_group(row["emotion_type"], row["emotion_level"])
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise

    def move_song(self, song_id: int, new_position: int):
        row = self.get_song(song_id)
        if not row:
            return False
        emotion, level = row["emotion_type"], row["emotion_level"]
        ids = [r[0] for r in self.con.execute(
            "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? ORDER BY position,id",
            (emotion, level),
        ).fetchall()]
        if song_id not in ids:
            return False
        ids.remove(song_id)
        idx = max(0, min(len(ids), int(new_position) - 1))
        ids.insert(idx, song_id)
        try:
            self.con.execute("BEGIN IMMEDIATE")
            self._rewrite_order(emotion, level, ids)
            self.con.commit()
            return True
        except Exception:
            self.con.rollback()
            raise

    def move_song_relative(self, song_id: int, target_id: int, before: bool = True):
        """Mueve una canción completa antes/después de otra dentro del mismo nivel emocional."""
        if song_id == target_id:
            return False
        row = self.get_song(song_id)
        target = self.get_song(target_id)
        if not row or not target:
            return False
        if (row["emotion_type"], row["emotion_level"]) != (target["emotion_type"], target["emotion_level"]):
            return False
        emotion, level = row["emotion_type"], row["emotion_level"]
        ids = [r[0] for r in self.con.execute(
            "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? ORDER BY position,id",
            (emotion, level),
        ).fetchall()]
        if song_id not in ids or target_id not in ids:
            return False
        ids.remove(song_id)
        idx = ids.index(target_id)
        if not before:
            idx += 1
        ids.insert(idx, song_id)
        try:
            self.con.execute("BEGIN IMMEDIATE")
            self._rewrite_order(emotion, level, ids)
            self.con.commit()
            return True
        except Exception:
            self.con.rollback()
            raise

    def move_song_to_level(self, song_id: int, target_level: str, target_position: int):
        """Transfiere una canción entre Principal y Secundaria dentro de la misma emoción.

        La operación es atómica: compacta el nivel de origen, inserta la fila completa
        en la posición elegida del nivel destino y renumera ambos grupos 1..N.
        """
        if target_level not in LEVELS:
            raise ValueError("Nivel de destino inválido")
        row = self.get_song(song_id)
        if not row:
            return False
        emotion = row["emotion_type"]
        source_level = row["emotion_level"]
        if source_level == target_level:
            return self.move_song(song_id, target_position)
        try:
            self.con.execute("BEGIN IMMEDIATE")
            source_ids = [r[0] for r in self.con.execute(
                "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? AND id<>? ORDER BY position,id",
                (emotion, source_level, song_id),
            ).fetchall()]
            target_ids = [r[0] for r in self.con.execute(
                "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? ORDER BY position,id",
                (emotion, target_level),
            ).fetchall()]
            pos = max(1, min(len(target_ids) + 1, int(target_position or (len(target_ids) + 1))))
            self.con.execute(
                "UPDATE songs SET emotion_level=?, position=999999, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (target_level, song_id),
            )
            self._rewrite_order(emotion, source_level, source_ids)
            target_ids.insert(pos - 1, song_id)
            self._rewrite_order(emotion, target_level, target_ids)
            self.con.commit()
            return True
        except Exception:
            self.con.rollback()
            raise

    @staticmethod
    def _norm_source(value: str) -> str:
        return (value or "").strip().casefold()

    def origin_rows(self, emotion: str, level: str, source: str):
        """Devuelve SOLO las filas del origen exacto dentro de emoción+nivel.

        A diferencia de los filtros de búsqueda (que admiten coincidencias parciales),
        las transferencias Principal ↔ Secundaria deben trabajar con una colección
        inequívoca para no mezclar bibliotecas.
        """
        source = (source or "").strip()
        return self.con.execute(
            """SELECT id, position, song, artist, country, year, duration, genre, description, source_sheet,
                      emotion_type, emotion_level
               FROM songs
               WHERE emotion_type=? AND emotion_level=?
                 AND trim(source_sheet)=? COLLATE NOCASE
               ORDER BY position, id""",
            (emotion, level, source),
        ).fetchall()

    def count_origin_group(self, emotion: str, level: str, source: str) -> int:
        source = (source or "").strip()
        return int(self.con.execute(
            """SELECT COUNT(*) FROM songs
               WHERE emotion_type=? AND emotion_level=?
                 AND trim(source_sheet)=? COLLATE NOCASE""",
            (emotion, level, source),
        ).fetchone()[0])

    def origin_position(self, song_id: int) -> int | None:
        row = self.get_song(song_id)
        if not row:
            return None
        ids = [r["id"] for r in self.origin_rows(
            row["emotion_type"], row["emotion_level"], row["source_sheet"]
        )]
        try:
            return ids.index(song_id) + 1
        except ValueError:
            return None

    def move_song_to_level_by_origin(self, song_id: int, target_level: str, transfer_spec: dict):
        """Transfiere una fila entre niveles respetando emoción y origen exactos.

        ``transfer_spec`` puede ser:
          {"mode":"relative", "reference_id":123, "before":True}
          {"mode":"edge", "edge":"first"}
          {"mode":"edge", "edge":"last"}

        La operación se resuelve por ID de referencia y no por un número global
        mostrado en pantalla. Eso evita que una canción termine en otro origen si
        existen filas ocultas o si la numeración global cambia.
        """
        if target_level not in LEVELS:
            raise ValueError("Nivel de destino inválido")
        row = self.get_song(song_id)
        if not row:
            return False
        emotion = row["emotion_type"]
        source_level = row["emotion_level"]
        source = (row["source_sheet"] or "").strip()
        if source_level == target_level:
            return False

        mode = (transfer_spec or {}).get("mode", "")
        reference_id = transfer_spec.get("reference_id") if transfer_spec else None
        before = bool((transfer_spec or {}).get("before", True))
        edge = (transfer_spec or {}).get("edge", "")

        # Validación fuerte de la referencia ANTES de tocar la base.
        ref = None
        if mode == "relative":
            if not reference_id:
                raise ValueError("Falta la canción de referencia")
            ref = self.get_song(int(reference_id))
            if not ref:
                raise ValueError("La canción de referencia ya no existe")
            if ref["emotion_type"] != emotion or ref["emotion_level"] != target_level:
                raise ValueError("La referencia no pertenece al destino emocional seleccionado")
            if self._norm_source(ref["source_sheet"]) != self._norm_source(source):
                raise ValueError("La referencia pertenece a otro origen. Operación cancelada para proteger el orden.")
        elif mode == "edge":
            if edge not in {"first", "last"}:
                raise ValueError("Extremo de destino inválido")
        else:
            raise ValueError("Especificación de transferencia inválida")

        try:
            self.con.execute("BEGIN IMMEDIATE")

            # Orden global actual de ambos niveles. La base conserva un único position
            # por emoción+nivel, pero la elección visual se hace dentro del origen.
            source_ids = [r[0] for r in self.con.execute(
                "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? AND id<>? ORDER BY position,id",
                (emotion, source_level, song_id),
            ).fetchall()]
            target_ids = [r[0] for r in self.con.execute(
                "SELECT id FROM songs WHERE emotion_type=? AND emotion_level=? ORDER BY position,id",
                (emotion, target_level),
            ).fetchall()]

            # Identifica en el destino las filas del MISMO origen exacto.
            target_source_ids = []
            for sid in target_ids:
                rr = self.get_song(sid)
                if rr and self._norm_source(rr["source_sheet"]) == self._norm_source(source):
                    target_source_ids.append(sid)

            if mode == "relative":
                if int(reference_id) not in target_ids:
                    raise ValueError("La referencia ya no pertenece al nivel destino")
                idx = target_ids.index(int(reference_id))
                if not before:
                    idx += 1
            else:
                if target_source_ids:
                    indexes = [target_ids.index(sid) for sid in target_source_ids]
                    idx = min(indexes) if edge == "first" else max(indexes) + 1
                else:
                    # Si el origen todavía no tiene filas en el destino, se crea su
                    # primer elemento al final sin alterar otros bloques existentes.
                    idx = len(target_ids)

            self.con.execute(
                "UPDATE songs SET emotion_level=?, position=999999, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (target_level, song_id),
            )
            self._rewrite_order(emotion, source_level, source_ids)
            target_ids.insert(idx, song_id)
            self._rewrite_order(emotion, target_level, target_ids)
            self.con.commit()
            return True
        except Exception:
            self.con.rollback()
            raise

    def emotion_rows(self, emotion: str, level: str, search="", source="", genre="", country="", year=""):
        where = ["emotion_type=?", "emotion_level=?"]
        params = [emotion, level]
        if search.strip():
            q = f"%{search.strip()}%"
            where.append("(artist LIKE ? COLLATE NOCASE OR song LIKE ? COLLATE NOCASE OR description LIKE ? COLLATE NOCASE)")
            params += [q, q, q]
        # V1.3.4: Origen usa coincidencia exacta. Género, país y año
        # continúan admitiendo coincidencias parciales para facilitar la búsqueda.
        if source.strip():
            where.append("trim(source_sheet)=? COLLATE NOCASE")
            params.append(source.strip())
        for col, val in [("genre", genre), ("country", country), ("year", year)]:
            if val.strip():
                where.append(f"{col} LIKE ? COLLATE NOCASE")
                params.append(f"%{val.strip()}%")
        return self.con.execute(
            f"""SELECT id, position, song, artist, country, year, duration, genre, description, source_sheet,
                       emotion_type, emotion_level
                FROM songs WHERE {' AND '.join(where)}
                ORDER BY position, artist COLLATE NOCASE, song COLLATE NOCASE""",
            params,
        ).fetchall()

    # Setlists

    def setlists(self):
        return self.con.execute("SELECT * FROM setlists ORDER BY id DESC").fetchall()

    def create_setlist(self, name: str):
        cur = self.con.execute("INSERT INTO setlists(name,target_minutes) VALUES (?,80)", (name, ))
        self.con.commit()
        return cur.lastrowid

    def update_setlist(self, setlist_id: int, **kwargs):
        allowed = {"name",
            "event_date",
            "event_time",
            "audience_country",
            "target_minutes",
            "notes",
            "show_type",
            "platform",
            "status",
            "starmaker_live_url",
            "starmaker_live_id",
            "timezone",
            "strategy_notes"}
        fields = [(k, v) for k, v in kwargs.items() if k in allowed]
        if not fields:
            return
        sql = ",".join(f"{k}=?" for k, _ in fields)
        self.con.execute(f"UPDATE setlists SET {sql}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            [v for _, v in fields] + [setlist_id])
        self.con.commit()

    def delete_setlist(self, setlist_id: int):
        self.con.execute("DELETE FROM setlists WHERE id=?", (setlist_id, ))
        self.con.commit()

    def get_setlist(self, setlist_id: int):
        return self.con.execute("SELECT * FROM setlists WHERE id=?", (setlist_id, )).fetchone()

    def duplicate_setlist(self, setlist_id: int, new_name: str):
        row = self.get_setlist(setlist_id)
        if not row:
            return None
        fields = ["event_date",
            "event_time",
            "audience_country",
            "target_minutes",
            "notes",
            "show_type",
            "platform",
            "status",
            "starmaker_live_url",
            "starmaker_live_id",
            "timezone",
            "strategy_notes"]
        cur = self.con.execute(
            (
                'INSERT INTO setlists(name,event_date,event_time,audience_country,target_minutes,note'
                's,show_type,platform,status,starmaker_live_url,starmaker_live_id,timezone,strategy_n'
                'otes)\n               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'
            ),
            [new_name] + [row[f] for f in fields],
        )
        new_id = cur.lastrowid
        for item in self.con.execute("SELECT song_id,position FROM setlist_items WHERE setlist_id=? ORDER BY position,id",
            (setlist_id, )).fetchall():
            self.con.execute("INSERT INTO setlist_items(setlist_id,song_id,position) VALUES (?,?,?)",
                (new_id, item[0], item[1]))
        self.con.commit()
        return new_id

    def setlist_items(self, setlist_id: int):
        return self.con.execute(
            """SELECT si.id item_id,si.position,s.* FROM setlist_items si
               JOIN songs s ON s.id=si.song_id WHERE si.setlist_id=? ORDER BY si.position""", (setlist_id, )
        ).fetchall()

    def add_to_setlist(self, setlist_id: int, song_id: int):
        pos = self.con.execute("SELECT COALESCE(MAX(position),0)+1 FROM setlist_items WHERE setlist_id=?",
            (setlist_id, )).fetchone()[0]
        self.con.execute("INSERT INTO setlist_items(setlist_id,song_id,position) VALUES (?,?,?)",
            (setlist_id, song_id, pos))
        self.con.commit()

    def remove_setlist_item(self, setlist_id: int, item_id: int):
        self.con.execute("DELETE FROM setlist_items WHERE id=?", (item_id, ))
        self._normalize_setlist(setlist_id)
        self.con.commit()

    def _normalize_setlist(self, setlist_id: int):
        rows = self.con.execute("SELECT id FROM setlist_items WHERE setlist_id=? ORDER BY position,id",
            (setlist_id, )).fetchall()
        for i, r in enumerate(rows, 1):
            self.con.execute("UPDATE setlist_items SET position=? WHERE id=?", (i, r[0]))

    def move_setlist_item(self, setlist_id: int, item_id: int, new_pos: int):
        rows = [r[0] for r in self.con.execute("SELECT id FROM setlist_items WHERE setlist_id=? ORDER BY position,id",
            (setlist_id, )).fetchall()]
        if item_id not in rows:
            return
        rows.remove(item_id)
        idx = max(0, min(len(rows), int(new_pos)-1))
        rows.insert(idx, item_id)
        # Two-pass renumbering avoids collisions with UNIQUE(setlist_id, position).
        for i, iid in enumerate(rows, 1):
            self.con.execute("UPDATE setlist_items SET position=? WHERE id=?", (100000 + i, iid))
        for i, iid in enumerate(rows, 1):
            self.con.execute("UPDATE setlist_items SET position=? WHERE id=?", (i, iid))
        self.con.commit()


    # StarMaker public data + own show data

    def starmaker_set_status(self, song_id: int, status: str, notes: str = ""):
        self.con.execute((
            'INSERT INTO starmaker_song_status(song_id,status,notes,last_checked_at) VALUES '
            '(?,?,?,?)\n                          ON CONFLICT(song_id) DO UPDATE SET '
            'status=excluded.status,notes=excluded.notes,last_checked_at=excluded.last_checked_at'
        ),
                         (song_id, status, notes, now_iso()))
        self.con.commit()

    def starmaker_tracks_for_song(self, song_id: int):
        return self.con.execute("SELECT * FROM starmaker_tracks WHERE song_id=? ORDER BY is_selected DESC, recordings_count DESC, id",
            (song_id, )).fetchall()

    def upsert_starmaker_track(self, song_id: int, data: dict, select: bool = False):
        url = (data.get("starmaker_url") or data.get("source_url") or "").strip()
        if not url:
            raise ValueError("Falta URL StarMaker")
        if select:
            self.con.execute("UPDATE starmaker_tracks SET is_selected=0 WHERE song_id=?", (song_id, ))
        self.con.execute((
            'INSERT INTO starmaker_tracks(song_id,starmaker_song_id,starmaker_url,title,artist,va'
            'riant,uploaded_by,recordings_count,source_url,match_confidence,is_selected,last_chec'
            'ked_at)\n                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)\n'
            '                          ON CONFLICT(song_id,starmaker_url) DO UPDATE SET\n'
            '                            starmaker_song_id=excluded.starmaker_song_id,title=exclu'
            'ded.title,artist=excluded.artist,variant=excluded.variant,\n'
            '                            uploaded_by=excluded.uploaded_by,recordings_count=COALES'
            'CE(excluded.recordings_count,starmaker_tracks.recordings_count),\n'
            '                            source_url=excluded.source_url,match_confidence=excluded'
            '.match_confidence,is_selected=CASE WHEN excluded.is_selected=1 THEN 1 ELSE '
            'starmaker_tracks.is_selected END,\n'
            '                            last_checked_at=excluded.last_checked_at,updated_at=CURR'
            'ENT_TIMESTAMP'
        ),
                         (song_id,
                             data.get("starmaker_song_id", ""),
                             url,
                             data.get("title", ""),
                             data.get("artist", ""),
                             data.get("variant", ""),
                             data.get("uploaded_by", ""),
                             data.get("recordings_count"),
                             data.get("source_url", url),
                             int(data.get("match_confidence") or 0),
                             1 if select else 0,
                             now_iso()))
        track = self.con.execute("SELECT * FROM starmaker_tracks WHERE song_id=? AND starmaker_url=?",
            (song_id, url)).fetchone()
        status = "Encontrada" if select else ("Coincidencia dudosa" if int(data.get("match_confidence") or 0)<80 else "Encontrada")
        self.con.execute((
            'INSERT INTO starmaker_song_status(song_id,status,notes,last_checked_at) VALUES '
            '(?,?,?,?)\n                          ON CONFLICT(song_id) DO UPDATE SET '
            'status=excluded.status,last_checked_at=excluded.last_checked_at'
        ),
                              (song_id, status, "", now_iso()))
        if data.get("recordings_count") is not None and track:
            self.con.execute("INSERT INTO starmaker_snapshots(starmaker_track_id,checked_at,recordings_count) VALUES (?,?,?)",
                (track["id"], now_iso(), int(data["recordings_count"])))
        self.con.commit()
        return int(track["id"]) if track else None

    def select_starmaker_track(self, song_id: int, track_id: int):
        self.con.execute("UPDATE starmaker_tracks SET is_selected=CASE WHEN id=? THEN 1 ELSE 0 END WHERE song_id=?",
            (track_id, song_id))
        self.starmaker_set_status(song_id, "Encontrada")

    def add_starmaker_snapshot(self, track_id: int, recordings_count):
        checked = now_iso()
        self.con.execute("INSERT INTO starmaker_snapshots(starmaker_track_id,checked_at,recordings_count) VALUES (?,?,?)",
            (track_id, checked, recordings_count))
        self.con.execute("UPDATE starmaker_tracks SET recordings_count=?,last_checked_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (recordings_count, checked, track_id))
        self.con.commit()

    def starmaker_catalog(self, search="", emotion="", source="", genre="", availability="Todos"):
        where = ["1=1"]
        params = []
        if search.strip():
            q = f"%{search.strip()}%"
            where.append("(s.song LIKE ? COLLATE NOCASE OR s.artist LIKE ? COLLATE NOCASE)")
            params += [q, q]
        if emotion:
            where.append("s.emotion_type=?")
            params.append(emotion)
        if source:
            where.append("trim(s.source_sheet)=? COLLATE NOCASE")
            params.append(source.strip())
        if genre.strip():
            where.append("s.genre LIKE ? COLLATE NOCASE")
            params.append(f"%{genre.strip()}%")
        if availability=="Sí":
            where.append("EXISTS(SELECT 1 FROM starmaker_tracks x WHERE x.song_id=s.id AND x.is_selected=1)")
        elif availability=="No":
            where.append("COALESCE(ss.status,'')='No encontrada'")
        elif availability=="Sin investigar":
            where.append("ss.song_id IS NULL AND NOT EXISTS(SELECT 1 FROM starmaker_tracks x WHERE x.song_id=s.id)")
        sql = f"""SELECT s.id,s.song,s.artist,s.emotion_type,s.source_sheet,s.genre,
                  COALESCE(ss.status,CASE WHEN t.id IS NOT NULL THEN 'Encontrada' ELSE 'Sin investigar' END) sm_status,
                  t.id track_id,t.starmaker_url,t.starmaker_song_id,t.variant,t.recordings_count,t.last_checked_at,t.match_confidence
                  FROM songs s LEFT JOIN starmaker_song_status ss ON ss.song_id=s.id
                  LEFT JOIN starmaker_tracks t ON t.song_id=s.id AND t.is_selected=1
                  WHERE {' AND '.join(where)}
                  ORDER BY CASE s.emotion_type WHEN 'Positiva' THEN 1 WHEN 'Neutra' THEN 2 WHEN 'Negativa' THEN 3 ELSE 9 END,s.position,s.artist COLLATE NOCASE,s.song COLLATE NOCASE LIMIT 5000"""
        return self.con.execute(sql, params).fetchall()

    def starmaker_popularity(self):
        rows = self.con.execute((
            'SELECT t.*,s.song,s.artist,s.emotion_type,s.source_sheet,s.genre\n'
            '                                 FROM starmaker_tracks t JOIN songs s ON '
            's.id=t.song_id WHERE t.is_selected=1\n'
            '                                 ORDER BY COALESCE(t.recordings_count,-1) '
            'DESC,s.song'
        )).fetchall()
        out = []
        for r in rows:
            snaps = self.con.execute((
                'SELECT recordings_count,checked_at FROM starmaker_snapshots WHERE '
                'starmaker_track_id=? AND recordings_count IS NOT NULL ORDER BY checked_at DESC,id '
                'DESC LIMIT 2'
            ),
                (r["id"], )).fetchall()
            latest = snaps[0][0] if snaps else r["recordings_count"]
            prev = snaps[1][0] if len(snaps)>1 else None
            change = (latest-prev) if latest is not None and prev is not None else None
            pct = (change*100.0/prev) if change is not None and prev not in (None, 0) else None
            out.append((r, latest, prev, change, pct))
        return out

    def save_starmaker_link(self, url: str, link_type: str, public_id: str = "", song_id=None):
        self.con.execute((
            'INSERT INTO starmaker_links(song_id,url,link_type,public_id) VALUES (?,?,?,?) ON '
            'CONFLICT(url) DO UPDATE SET song_id=excluded.song_id,link_type=excluded.link_type,pu'
            'blic_id=excluded.public_id'
        ),
            (song_id, url, link_type, public_id))
        self.con.commit()

    def log_starmaker(self, operation: str, result: str = "", error: str = ""):
        self.con.execute("INSERT INTO starmaker_log(operation,result,error) VALUES (?,?,?)",
            (operation, result, error))
        self.con.commit()

    def starmaker_logs(self, limit=200):
        return self.con.execute("SELECT * FROM starmaker_log ORDER BY id DESC LIMIT ?", (limit, )).fetchall()

    def starmaker_summary(self):
        total = self.con.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
        researched = self.con.execute("SELECT COUNT(DISTINCT song_id) FROM starmaker_song_status").fetchone()[0]
        found = self.con.execute("SELECT COUNT(DISTINCT song_id) FROM starmaker_tracks WHERE is_selected=1").fetchone()[0]
        nofound = self.con.execute("SELECT COUNT(*) FROM starmaker_song_status WHERE status='No encontrada'").fetchone()[0]
        pending = self.con.execute("SELECT COUNT(*) FROM starmaker_song_status WHERE status='Coincidencia dudosa'").fetchone()[0]
        recs = self.con.execute((
            'SELECT COALESCE(SUM(recordings_count),0) FROM starmaker_tracks WHERE is_selected=1 '
            'AND recordings_count IS NOT NULL'
        )).fetchone()[0]
        shows = self.con.execute("SELECT COUNT(*) FROM show_performances").fetchone()[0]
        top = self.con.execute((
            'SELECT s.song,s.artist,t.recordings_count FROM starmaker_tracks t JOIN songs s ON '
            's.id=t.song_id\n                                WHERE t.is_selected=1 AND '
            't.recordings_count IS NOT NULL ORDER BY t.recordings_count DESC LIMIT 1'
        )).fetchone()
        return {"total":total,
            "researched":researched,
            "found":found,
            "not_found":nofound,
            "pending":pending,
            "recordings":recs,
            "shows":shows,
            "top":top}

    def save_show_performance(self, values: dict, audience_rows=None):
        fields = ["setlist_id",
            "song_id",
            "performance_date",
            "starmaker_live_id",
            "starmaker_live_url",
            "position_in_show",
            "viewers_peak",
            "viewers_average",
            "likes",
            "gifts_coins",
            "new_followers",
            "comments_count",
            "notes",
            "data_source"]
        vals = [values.get(f) for f in fields]
        cur = self.con.execute(f"INSERT INTO show_performances({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",
            vals)
        pid = cur.lastrowid
        for row in audience_rows or []:
            self.con.execute((
                'INSERT INTO show_audience_country(show_performance_id,country,audience_count,audienc'
                'e_percent,source) VALUES (?,?,?,?,?)'
            ),
                (pid,
                    row.get("country", ""),
                    row.get("audience_count"),
                    row.get("audience_percent"),
                    row.get("source", "Manual")))
        self.con.commit()
        return pid

    def show_performances(self, setlist_id=None):
        where = "WHERE p.setlist_id=?" if setlist_id else ""
        params = (setlist_id, ) if setlist_id else ()
        return self.con.execute(f"""SELECT p.*,s.song,s.artist,sl.name setlist_name FROM show_performances p
                                  JOIN songs s ON s.id=p.song_id LEFT JOIN setlists sl ON sl.id=p.setlist_id {where}
                                  ORDER BY p.performance_date DESC,p.id DESC""", params).fetchall()

    def import_show_csv(self, path: str):
        count = 0
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                song = (row.get("song") or row.get("cancion") or "").strip()
                artist = (row.get("artist") or row.get("artista") or "").strip()
                found = self.con.execute("SELECT id FROM songs WHERE lower(song)=lower(?) AND (?='' OR lower(artist)=lower(?)) ORDER BY id LIMIT 1",
                    (song, artist, artist)).fetchone()
                if not found:
                    continue
                def num(k):
                    v = (row.get(k) or "").strip()
                    try:
                        return int(v.replace(".", "").replace(",", "")) if v else None
                    except:
                        return None
                vals = {"setlist_id":None,
                    "song_id":found[0],
                    "performance_date":row.get("performance_date") or row.get("fecha") or "",
                    "starmaker_live_id":row.get("starmaker_live_id") or "",
                    "starmaker_live_url":row.get("starmaker_live_url") or "",
                    "position_in_show":num("position_in_show"),
                    "viewers_peak":num("viewers_peak"),
                    "viewers_average":num("viewers_average"),
                    "likes":num("likes"),
                    "gifts_coins":num("gifts_coins"),
                    "new_followers":num("new_followers"),
                    "comments_count":num("comments_count"),
                    "notes":row.get("notes") or "",
                    "data_source":"CSV"}
                self.save_show_performance(vals)
                count+=1
        return count

    def show_analytics(self):
        countries = self.con.execute("""SELECT a.country,COUNT(DISTINCT a.show_performance_id) shows,
                   SUM(COALESCE(a.audience_count,0)) audience,AVG(a.audience_percent) avg_percent
                   FROM show_audience_country a GROUP BY a.country ORDER BY audience DESC,a.country""").fetchall()
        emotions = self.con.execute((
            'SELECT s.emotion_type label,COUNT(*) performances,AVG(p.viewers_average) '
            'avg_viewers,\n                   SUM(COALESCE(p.likes,0)) '
            'likes,SUM(COALESCE(p.gifts_coins,0)) coins\n'
            '                   FROM show_performances p JOIN songs s ON s.id=p.song_id GROUP BY '
            's.emotion_type ORDER BY performances DESC'
        )).fetchall()
        origins = self.con.execute((
            'SELECT s.source_sheet label,COUNT(*) performances,AVG(p.viewers_average) '
            'avg_viewers,\n                   SUM(COALESCE(p.likes,0)) '
            'likes,SUM(COALESCE(p.gifts_coins,0)) coins\n'
            '                   FROM show_performances p JOIN songs s ON s.id=p.song_id GROUP BY '
            's.source_sheet ORDER BY performances DESC'
        )).fetchall()
        genres = self.con.execute((
            'SELECT s.genre label,COUNT(*) performances,AVG(p.viewers_average) avg_viewers,\n'
            '                   SUM(COALESCE(p.likes,0)) likes,SUM(COALESCE(p.gifts_coins,0)) '
            'coins\n                   FROM show_performances p JOIN songs s ON s.id=p.song_id '
            "WHERE trim(s.genre)<>'' GROUP BY s.genre ORDER BY performances DESC LIMIT 100"
        )).fetchall()
        songs = self.con.execute((
            'SELECT s.song,s.artist,COUNT(*) performances,AVG(p.viewers_average) avg_viewers,\n'
            '                   SUM(COALESCE(p.likes,0)) likes,SUM(COALESCE(p.gifts_coins,0)) '
            'coins,MAX(p.performance_date) last_date\n'
            '                   FROM show_performances p JOIN songs s ON s.id=p.song_id GROUP BY '
            's.id ORDER BY performances DESC,coins DESC LIMIT 100'
        )).fetchall()
        return {"countries":countries, "emotions":emotions, "origins":origins, "genres":genres, "songs":songs}

    def starmaker_show_score_rows(self, emotion="", source="", genre=""):
        rows = self.sm_catalog_auto(emotion=emotion, source=source, genre=genre, availability="Sí")
        out = []
        for r in rows:
            count = r["recordings_count"]
            pop = min(60.0, 10.0*math.log10((count or 0)+1)) if count is not None else 0.0
            snaps = []
            if r["track_id"]:
                snaps = self.con.execute((
                    'SELECT recordings_count FROM starmaker_snapshots WHERE starmaker_track_id=? AND '
                    'recordings_count IS NOT NULL ORDER BY checked_at DESC,id DESC LIMIT 2'
                ),
                    (r["track_id"], )).fetchall()
            growth = 0.0
            growth_txt = "Sin historial suficiente"
            if len(snaps)>=2 and snaps[1][0] not in (None, 0):
                pct = (snaps[0][0]-snaps[1][0])*100.0/snaps[1][0]
                growth = max(0.0, min(20.0, pct))
                growth_txt = f"cambio {pct:+.1f}%"
            perf = self.con.execute((
                'SELECT COUNT(*),COALESCE(AVG(COALESCE(likes,0)),0),COALESCE(AVG(COALESCE(gifts_coins'
                ',0)),0) FROM show_performances WHERE song_id=?'
            ),
                (r["id"], )).fetchone()
            personal = min(20.0,
                (perf[0] or 0)*3 + math.log10((perf[1] or 0)+(perf[2] or 0)+1)*2) if perf[0] else 0.0
            score = round(pop+growth+personal, 1)
            reasons = []
            if count is not None:
                reasons.append(f"{compact_count(count)} grabaciones StarMaker")
            reasons.append(growth_txt)
            reasons.append(f"{perf[0]} shows propios" if perf[0] else "sin shows propios")
            out.append((score, r, "; ".join(reasons)))
        return sorted(out, key=lambda x:x[0], reverse=True)


    # StarMaker Exact Sum Resolver V1.4.5
    @staticmethod
    def _sm_artist_canon(value):
        n = normalize_match_text(value)
        n = re.sub(r"\b(?:points|acoustic|acustico|piano|karaoke|instrumental|version|versión|cover)\b", " ", n)
        n = re.sub(r"^the\s+", "", n)
        return re.sub(r"\s+", " ", n).strip()

    def _sm_exact_artist_ok(self, song, remote):
        """Valida artista sin confundir títulos genéricos (Camila ≠ Camila Cabello)."""
        local_parts = [self._sm_artist_canon(x) for x in _sm_split_artists(song["artist"])]
        remote_values = []
        for raw in (remote["artist"],
            remote["source_label"] if (remote["source_kind"] or "") in {"artist",
                "search",
                "search-title",
                "related"} else ""):
            remote_values += [self._sm_artist_canon(x) for x in _sm_split_artists(raw or "")]
            c = self._sm_artist_canon(raw or "")
            if c:
                remote_values.append(c)
        local_parts = [x for x in dict.fromkeys(local_parts) if x]
        remote_values = [x for x in dict.fromkeys(remote_values) if x]
        for la in local_parts:
            for ra in remote_values:
                if la==ra:
                    return True
                # Colaboraciones/etiquetas: sólo containment seguro para nombres de 2+ palabras.
                if len(la.split())>=2 and (f" {la} " in f" {ra} " or f" {ra} " in f" {la} "):
                    return True
                if len(la)>=7 and len(ra)>=7 and difflib.SequenceMatcher(None, la, ra).ratio()>=0.90:
                    return True
        return False

    def sm_exact_match(self, song_ids=None):
        """V1.4.5: suma TODAS las pistas de la misma obra por título exacto.

        Se incluyen original, acústico, piano, live, short, lower/higher y uploads de usuarios.
        Si la ficha local no es remix, cualquier pista marcada como remix queda afuera.
        La identidad del artista se usa como control anti-falsos-positivos, no como uploader.
        """
        public = self.con.execute("SELECT * FROM starmaker_public_catalog WHERE trim(title)<>''").fetchall()
        if song_ids:
            qs = ','.join('?' for _ in song_ids)
            songs = self.con.execute(f"SELECT * FROM songs WHERE id IN ({qs})", list(song_ids)).fetchall()
        else:
            songs = self.con.execute("SELECT * FROM songs ORDER BY id").fetchall()
        by_title = {}
        for r in public:
            b = _sm_base_title(r["title"])
            by_title.setdefault(b, []).append(r)
        matched = 0
        for song in songs:
            base = _sm_base_title(song["song"])
            local_remix = _sm_is_remix((song["song"] or "")+" "+(song["genre"] or ""))
            candidates = []
            for r in by_title.get(base, []):
                remote_remix = _sm_is_remix((r["title"] or "")+" "+(r["variant"] or ""))
                if local_remix != remote_remix:
                    continue
                if not self._sm_exact_artist_ok(song, r):
                    continue
                # Exactitud de obra = título base idéntico. Artist/uploader ya fue validado arriba.
                score = 100 if normalize_match_text(song["song"])==normalize_match_text(r["title"]) else 96
                candidates.append((score, r))
            # Dedup real por public_key; distintos uploads/IDs se conservan y SUMAN.
            uniq = {r["public_key"]:(sc, r) for sc, r in candidates}
            candidates = list(uniq.values())
            candidates.sort(key=lambda x:(x[0], x[1]["recordings_count"] if x[1]["recordings_count"] is not None else -1),
                reverse=True)
            self.con.execute("DELETE FROM starmaker_song_matches WHERE song_id=?", (song["id"], ))
            if not candidates:
                self.con.execute((
                    'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                    "VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key='',confidence=0,stat"
                    "us='Sin coincidencia interpretativa',updated_at=excluded.updated_at"
                ),
                    (song["id"], "", 0, "Sin coincidencia interpretativa", now_iso()))
                continue
            primary = candidates[0][1]
            for sc, r in candidates:
                self.con.execute((
                    'INSERT INTO starmaker_song_matches(song_id,public_key,confidence,match_type,included'
                    '_in_total,is_primary,updated_at) VALUES(?,?,?,?,?,?,?)'
                ),
                    (song["id"],
                        r["public_key"],
                        sc,
                        "Exacta / variante",
                        1,
                        1 if r["public_key"]==primary["public_key"] else 0,
                        now_iso()))
                internal_url = r["url"] or (r["source_url"]+"#exact-"+str(r["id"]))
                data = {"starmaker_song_id":r["starmaker_song_id"],
                    "starmaker_url":internal_url,
                    "source_url":r["source_url"],
                    "title":r["title"],
                    "artist":r["artist"],
                    "variant":r["variant"],
                    "recordings_count":r["recordings_count"],
                    "match_confidence":sc}
                self.upsert_starmaker_track(song["id"], data, select=(r["public_key"]==primary["public_key"]))
            self.con.execute((
                'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                'VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key=excluded.public_key,'
                'confidence=excluded.confidence,status=excluded.status,updated_at=excluded.updated_at'
            ),
                (song["id"],
                    primary["public_key"],
                    candidates[0][0],
                    "Encontrada IA interpretativa",
                    now_iso()))
            matched+=1
        self.con.commit()
        return matched

    def sm_known_artist_urls(self, artist, limit=16):
        """Devuelve páginas públicas de artista YA conocidas por la base local.

        V1.4.7 evita depender siempre de Bing/DDG: si el rastreo histórico ya conoce
        una página de Celia Cruz, Coldplay, Chayanne, etc., la búsqueda individual la
        reutiliza inmediatamente.
        """
        target = self._sm_artist_canon(artist)
        cands = []
        if not target:
            return []
        try:
            rows = self.con.execute("SELECT artist_name,url FROM starmaker_artist_directory WHERE trim(url)<>''").fetchall()
        except Exception:
            rows = []
        for r in rows:
            rn = self._sm_artist_canon(r["artist_name"] or "")
            if not rn:
                continue
            ratio = difflib.SequenceMatcher(None, target, rn).ratio()
            if target==rn or ratio>=0.86 or (len(target)>=8 and (target in rn or rn in target)):
                cands.append((1.0 if target==rn else ratio, r["url"]))
        # También rescata source_url de catálogos de artista ya procesados.
        try:
            rows = self.con.execute((
                'SELECT DISTINCT artist,source_label,source_url,source_kind FROM '
                "starmaker_public_catalog WHERE trim(source_url)<>''"
            )).fetchall()
        except Exception:
            rows = []
        for r in rows:
            if (r["source_kind"] or "") not in {"artist", "search", "search-title", "related"}:
                continue
            for raw in (r["artist"] or "", r["source_label"] or ""):
                rn = self._sm_artist_canon(raw)
                if not rn:
                    continue
                ratio = difflib.SequenceMatcher(None, target, rn).ratio()
                if target==rn or ratio>=0.90:
                    u = r["source_url"] or ""
                    if StarMakerPublicClient.parse_public_url(u).get("type")=="singer":
                        cands.append((ratio, u))
                    break
        out = []
        seen = set()
        for _, u in sorted(cands, key=lambda x:x[0], reverse=True):
            if u and u not in seen:
                seen.add(u)
                out.append(u)
                if len(out)>=limit:
                    break
        return out

    def sm_interpretive_match(self, song_ids=None):
        """V1.4.7: IA interpretativa local para reconocer la misma OBRA.

        No inventa métricas. Usa sólo pistas públicas ya indexadas y explica por qué
        cada una se considera compatible. Permite covers/otros intérpretes cuando el
        título es suficientemente distintivo, pero mantiene controles fuertes para
        títulos genéricos como Yellow, Woman, Perfect, Angel, etc.
        """
        public = self.con.execute("SELECT * FROM starmaker_public_catalog WHERE trim(title)<>''").fetchall()
        if song_ids:
            qs = ','.join('?' for _ in song_ids)
            songs = self.con.execute(f"SELECT * FROM songs WHERE id IN ({qs})", list(song_ids)).fetchall()
        else:
            songs = self.con.execute("SELECT * FROM songs ORDER BY id").fetchall()
        # Índice por primer token para no comparar todo con todo.
        buckets = {}
        for r in public:
            b = _sm_base_title(r["title"])
            tok = (b.split()[:1] or [""])[0]
            buckets.setdefault(tok, []).append(r)
        matched = 0
        for song in songs:
            lb = _sm_base_title(song["song"])
            tok = (lb.split()[:1] or [""])[0]
            pool = buckets.get(tok, []) if tok else public
            accepted = []
            for r in pool:
                rb = _sm_base_title(r["title"] or "")
                # Pre-filtro flexible: exacto, containment o similitud alta.
                if lb!=rb and not (lb in rb or rb in lb) and difflib.SequenceMatcher(None,
                    lb,
                    rb).ratio()<0.82:
                    continue
                dec = StarMakerInterpretiveAI.score(song, r)
                if dec["accept"]:
                    accepted.append((dec["score"], dec["match_type"], dec["reason"], r))
            uniq = {}
            for item in accepted:
                key = item[3]["public_key"]
                if key not in uniq or item[0]>uniq[key][0]:
                    uniq[key] = item
            accepted = sorted(uniq.values(),
                key=lambda x:(x[0], x[3]["recordings_count"] if x[3]["recordings_count"] is not None else -1),
                reverse=True)
            self.con.execute("DELETE FROM starmaker_song_matches WHERE song_id=?", (song["id"], ))
            if not accepted:
                self.con.execute((
                    'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                    "VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key='',confidence=0,stat"
                    "us='Sin coincidencia interpretativa',updated_at=excluded.updated_at"
                ),
                    (song["id"], "", 0, "Sin coincidencia interpretativa", now_iso()))
                continue
            primary = accepted[0][3]
            self.con.execute("UPDATE starmaker_tracks SET is_selected=0 WHERE song_id=?", (song["id"], ))
            for sc, mtype, reason, r in accepted:
                self.con.execute((
                    'INSERT INTO starmaker_song_matches(song_id,public_key,confidence,match_type,included'
                    '_in_total,is_primary,updated_at) VALUES(?,?,?,?,?,?,?)'
                ),
                    (song["id"],
                        r["public_key"],
                        sc,
                        mtype,
                        1,
                        1 if r["public_key"]==primary["public_key"] else 0,
                        now_iso()))
                internal_url = r["url"] or (r["source_url"]+"#interpretive-"+str(r["id"]))
                data = {"starmaker_song_id":r["starmaker_song_id"],
                    "starmaker_url":internal_url,
                    "source_url":r["source_url"],
                    "title":r["title"],
                    "artist":r["artist"],
                    "variant":r["variant"],
                    "recordings_count":r["recordings_count"],
                    "match_confidence":sc}
                self.upsert_starmaker_track(song["id"], data, select=(r["public_key"]==primary["public_key"]))
            self.con.execute((
                'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                'VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key=excluded.public_key,'
                'confidence=excluded.confidence,status=excluded.status,updated_at=excluded.updated_at'
            ),
                (song["id"], primary["public_key"], accepted[0][0], "Encontrada IA interpretativa", now_iso()))
            matched+=1
        self.con.commit()
        return matched

    def sm_exact_missing(self, song_ids=None):
        if song_ids:
            qs = ','.join('?' for _ in song_ids)
            return self.con.execute(f"SELECT s.* FROM songs s LEFT JOIN (SELECT DISTINCT song_id FROM starmaker_song_matches WHERE included_in_total=1) m ON m.song_id=s.id WHERE s.id IN ({qs}) AND m.song_id IS NULL ORDER BY s.artist COLLATE NOCASE,s.song COLLATE NOCASE",
                list(song_ids)).fetchall()
        return self.sm_unmatched_songs()

    # StarMaker Coverage Recovery V1.4.3

    def sm_ingest_artists(self, artists):
        n = 0
        for a in artists:
            name = (a.get("artist_name") or "").strip()
            url = (a.get("url") or "").strip()
            key = str(a.get("artist_key") or a.get("starmaker_artist_id") or normalize_match_text(name)).strip()
            if not name or not url or not key:
                continue
            self.con.execute((
                'INSERT INTO starmaker_artist_directory(artist_key,starmaker_artist_id,artist_name,no'
                'rmalized_artist,url,source_url,last_seen_at)\n'
                '                VALUES(?,?,?,?,?,?,?) ON CONFLICT(artist_key) DO UPDATE SET '
                'starmaker_artist_id=excluded.starmaker_artist_id,artist_name=excluded.artist_name,no'
                'rmalized_artist=excluded.normalized_artist,url=excluded.url,source_url=excluded.sour'
                'ce_url,last_seen_at=excluded.last_seen_at'
            ),
                (key,
                    a.get("starmaker_artist_id", ""),
                    name,
                    normalize_match_text(name),
                    url,
                    a.get("source_url", ""),
                    now_iso()))
            n+=1
        self.con.commit()
        return n

    def sm_local_artist_queries(self):
        out = {}
        for r in self.con.execute("SELECT DISTINCT artist FROM songs WHERE trim(artist)<>'' ORDER BY artist").fetchall():
            for part in _sm_split_artists(r[0]):
                n = normalize_match_text(part)
                if len(n)>=2:
                    out.setdefault(n, part)
        return out

    def sm_target_artist_pages(self):
        """Devuelve TODAS las páginas públicas plausibles para cada artista local.
        V1.4.2 colapsaba duplicados; StarMaker mantiene varias páginas/IDs para un mismo artista.
        """
        local = self.sm_local_artist_queries()
        remote = [dict(r) for r in self.con.execute("SELECT * FROM starmaker_artist_directory ORDER BY artist_name,url").fetchall()]
        targets = []
        seen = set()
        by_norm = {}
        for r in remote:
            rn = r.get("normalized_artist") or normalize_match_text(r.get("artist_name", ""))
            by_norm.setdefault(rn, []).append(r)
        for norm, display in local.items():
            hits = list(by_norm.get(norm, []))
            if not hits:
                scored = []
                for r in remote:
                    rn = r.get("normalized_artist") or ""
                    if not rn:
                        continue
                    score = difflib.SequenceMatcher(None, norm, rn).ratio()
                    if norm in rn or rn in norm:
                        score = max(score, 0.94 if min(len(norm), len(rn))>=5 else score)
                    # Nombres con una palabra distintiva pueden aparecer con colaboraciones.
                    nw = set(norm.split())
                    rw = set(rn.split())
                    over = len(nw & rw)/max(1, len(nw))
                    score = max(score, 0.88+0.08*over if over>=0.75 and len(norm)>=5 else score)
                    if score>=0.88:
                        scored.append((score, r))
                scored.sort(key=lambda x:x[0], reverse=True)
                hits = [r for _, r in scored[:6]]
            for hit in hits:
                url = (hit.get("url") or "").strip()
                if not url or url in seen:
                    continue
                seen.add(url)
                targets.append((display, hit))
        return targets

    def sm_unmatched_songs(self):
        return self.con.execute((
            'SELECT s.* FROM songs s LEFT JOIN (SELECT DISTINCT song_id FROM '
            'starmaker_song_matches WHERE included_in_total=1) m ON m.song_id=s.id WHERE '
            'm.song_id IS NULL ORDER BY s.artist COLLATE NOCASE,s.song COLLATE NOCASE'
        )).fetchall()

    def sm_rescue_due(self, song_id, hours=STARMAKER_RESCUE_TTL_HOURS, force=False):
        if force:
            return True
        row = self.con.execute("SELECT last_scan_at,status FROM starmaker_rescue_state WHERE song_id=?",
            (song_id, )).fetchone()
        if not row or not row[0]:
            return True
        ttl = hours if str(row[1] or "").startswith("Encontrada") else STARMAKER_RESCUE_MISS_TTL_HOURS
        try:
            return (datetime.now()-datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")).total_seconds()>=ttl*3600
        except:
            return True

    def sm_mark_rescue(self, song_id, status, urls_found=0, entries_found=0, engine="", error=""):
        self.con.execute((
            'INSERT INTO starmaker_rescue_state(song_id,last_scan_at,status,urls_found,entries_fo'
            'und,engine,error) VALUES(?,?,?,?,?,?,?)\n'
            '            ON CONFLICT(song_id) DO UPDATE SET last_scan_at=excluded.last_scan_at,st'
            'atus=excluded.status,urls_found=excluded.urls_found,entries_found=excluded.entries_f'
            'ound,engine=excluded.engine,error=excluded.error'
        ),
            (song_id, now_iso(), status, int(urls_found or 0), int(entries_found or 0), engine, str(error or "")))
        self.con.commit()

    def sm_artist_scan_due(self, artist_key, hours=STARMAKER_ARTIST_TTL_HOURS):
        row = self.con.execute("SELECT last_scan_at FROM starmaker_artist_scan_state WHERE artist_key=?",
            (str(artist_key), )).fetchone()
        if not row or not row[0]:
            return True
        try:
            return (datetime.now()-datetime.strptime(row[0],
                "%Y-%m-%d %H:%M:%S")).total_seconds()>=hours*3600
        except:
            return True

    def sm_mark_artist_scan(self, artist_key, status, entries=0, error=""):
        self.con.execute((
            'INSERT INTO starmaker_artist_scan_state(artist_key,last_scan_at,status,entries_found'
            ',error) VALUES(?,?,?,?,?)\n            ON CONFLICT(artist_key) DO UPDATE SET '
            'last_scan_at=excluded.last_scan_at,status=excluded.status,entries_found=excluded.ent'
            'ries_found,error=excluded.error'
        ),
            (str(artist_key), now_iso(), status, int(entries or 0), str(error or "")))
        self.con.commit()

    def _sm_auto_score_v142(self, song, remote):
        local_title = normalize_match_text(song["song"])
        remote_title = normalize_match_text(remote["title"])
        local_base = _sm_base_title(song["song"])
        remote_base = _sm_base_title(remote["title"])
        local_artist = normalize_match_text(song["artist"])
        remote_artist = normalize_match_text(remote["artist"])
        context_artist = normalize_match_text(remote["source_label"] if (remote["source_kind"] or "") in {"artist",
            "search",
            "related"} else "")
        # El contexto de una página pública de artista cuenta como evidencia válida. Esto incluye pistas subidas por usuarios listadas bajo ese artista.
        artist_scores = []
        for la in [normalize_match_text(x) for x in _sm_split_artists(song["artist"])]+[local_artist]:
            if not la:
                continue
            for ra in (remote_artist, context_artist):
                if not ra:
                    continue
                if la==ra:
                    artist_scores.append(1.0)
                elif la in ra or ra in la:
                    artist_scores.append(0.96)
                else:
                    artist_scores.append(difflib.SequenceMatcher(None, la, ra).ratio())
        artist_score = max(artist_scores or [0.0])
        if local_base and remote_base:
            if local_base==remote_base:
                title_score = 1.0
            elif local_base in remote_base or remote_base in local_base:
                title_score = 0.94
            else:
                title_score = difflib.SequenceMatcher(None, local_base, remote_base).ratio()
        else:
            title_score = difflib.SequenceMatcher(None,
                local_title,
                remote_title).ratio() if local_title and remote_title else 0.0
        # Casos de pistas de usuarios como "Yellow - Coldplay" o "Yellow by Coldplay".
        if local_base and local_base in remote_title and any(a and a in remote_title for a in [normalize_match_text(x) for x in _sm_split_artists(song["artist"])]):
            title_score = max(title_score, 0.97)
            artist_score = max(artist_score, 0.95)
        score = int(round(title_score*72+artist_score*28))
        lt = self._sm_version_tokens(song["song"]+" "+(song["genre"] or ""))
        rt = self._sm_version_tokens(remote["title"]+" "+(remote["variant"] or ""))
        local_remix = _sm_is_remix(song["song"]+" "+(song["genre"] or ""))
        remote_remix = _sm_is_remix(remote["title"]+" "+(remote["variant"] or ""))
        if lt and rt:
            score += 5 if lt & rt else -8
        elif rt and not lt:
            score-=5
        elif lt and not rt:
            score-=4
        if remote_remix and not local_remix:
            score-=8
        if local_remix and not remote_remix:
            score-=12
        return max(0, min(100, score)), title_score, artist_score, local_remix, remote_remix

    def sm_auto_match(self, song_ids=None):
        """V1.4.2: relaciona TODAS las pistas públicas compatibles; elige una primaria y suma variantes no-remix."""
        public = self.con.execute("SELECT * FROM starmaker_public_catalog WHERE trim(title)<>'' AND trim(artist)<>''").fetchall()
        if not public:
            return 0
        if song_ids:
            qs = ','.join('?' for _ in song_ids)
            songs = self.con.execute(f"SELECT * FROM songs WHERE id IN ({qs})", list(song_ids)).fetchall()
        else:
            songs = self.con.execute("SELECT * FROM songs ORDER BY id").fetchall()
        by_first = {}
        for r in public:
            base = _sm_base_title(r["title"])
            k = (base or r["normalized_title"] or "")[:1]
            by_first.setdefault(k, []).append(r)
        matched = 0
        for s in songs:
            local_base = _sm_base_title(s["song"])
            cand = by_first.get(local_base[:1], public)
            ranked = []
            for r in cand:
                remote_base = _sm_base_title(r["title"])
                title_ratio = difflib.SequenceMatcher(None,
                    local_base,
                    remote_base).ratio() if local_base and remote_base else 0
                if title_ratio<0.50 and not (local_base and local_base in (r["normalized_title"] or "")):
                    continue
                score, ts, ascore, local_remix, remote_remix = self._sm_auto_score_v142(s, r)
                search_context = (r["source_kind"] or "") in {"search", "related"}
                if score<66 or ts<0.62 or (ascore<0.50 and not (search_context and ts>=0.94)):
                    continue
                exact = (normalize_match_text(s["song"])==normalize_match_text(r["title"]) and (ascore>=0.90 or search_context))
                match_type = "Exacta" if exact and not remote_remix else ("Remix" if remote_remix else ("Pista pública" if search_context else "Variante compatible"))
                included = (score>=76 and ts>=0.76 and (ascore>=0.68 or (search_context and ts>=0.94)) and (local_remix or not remote_remix))
                if local_remix:
                    included = included and remote_remix
                ranked.append((score, r, match_type, 1 if included else 0))
            ranked.sort(key=lambda x:(x[3], x[0], x[1]["recordings_count"] or -1), reverse=True)
            self.con.execute("DELETE FROM starmaker_song_matches WHERE song_id=?", (s["id"], ))
            for score, r, mtype, included in ranked:
                self.con.execute((
                    'INSERT INTO starmaker_song_matches(song_id,public_key,confidence,match_type,included'
                    '_in_total,is_primary,updated_at) VALUES(?,?,?,?,?,?,?)'
                ),
                    (s["id"], r["public_key"], score, mtype, included, 0, now_iso()))
            included_rows = [x for x in ranked if x[3]]
            best = included_rows[0] if included_rows else None
            if not best:
                status = "Revisar coincidencias" if ranked else "Sin coincidencia en índice profundo"
                conf = ranked[0][0] if ranked else 0
                pk = ranked[0][1]["public_key"] if ranked else ""
                self.con.execute((
                    'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                    'VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key=excluded.public_key,'
                    'confidence=excluded.confidence,status=excluded.status,updated_at=excluded.updated_at'
                ),
                    (s["id"], pk, conf, status, now_iso()))
                continue
            score, r, mtype, _ = best
            self.con.execute("UPDATE starmaker_song_matches SET is_primary=1 WHERE song_id=? AND public_key=?",
                (s["id"], r["public_key"]))
            self.con.execute((
                'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                'VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key=excluded.public_key,'
                'confidence=excluded.confidence,status=excluded.status,updated_at=excluded.updated_at'
            ),
                (s["id"], r["public_key"], score, "Encontrada automática", now_iso()))
            # Guarda TODAS las pistas compatibles para conservar variantes y snapshots. Sólo una queda seleccionada.
            self.con.execute("UPDATE starmaker_tracks SET is_selected=0 WHERE song_id=?", (s["id"], ))
            for sc, rr, mt, inc in included_rows:
                internal_url = rr["url"] or (rr["source_url"]+"#autodata-"+str(rr["id"]))
                data = {"starmaker_song_id":rr["starmaker_song_id"],
                    "starmaker_url":internal_url,
                    "source_url":rr["source_url"],
                    "title":rr["title"],
                    "artist":rr["artist"],
                    "variant":rr["variant"],
                    "recordings_count":rr["recordings_count"],
                    "match_confidence":sc}
                self.upsert_starmaker_track(s["id"], data, select=(rr["public_key"]==r["public_key"]))
                tr = self.con.execute("SELECT id FROM starmaker_tracks WHERE song_id=? AND starmaker_url=?",
                    (s["id"], internal_url)).fetchone()
                if tr:
                    day = today_iso()+"%"
                    ids = self.con.execute("SELECT id FROM starmaker_snapshots WHERE starmaker_track_id=? AND checked_at LIKE ? ORDER BY id DESC",
                        (tr["id"], day)).fetchall()
                    for extra in ids[1:]:
                        self.con.execute("DELETE FROM starmaker_snapshots WHERE id=?", (extra[0], ))
            matched+=1
        self.con.commit()
        return matched

    def sm_song_aggregate(self, song_id):
        rows = self.con.execute((
            'SELECT m.public_key,m.confidence,m.match_type,m.is_primary,p.title,p.artist,p.varian'
            't,p.recordings_count,p.url,p.source_label,p.source_kind,\n'
            '                   p.uploaded_by,p.visible_covers_count,p.visible_plays_sum,p.visibl'
            'e_plays_max\n            FROM starmaker_song_matches m JOIN starmaker_public_catalog '
            'p ON p.public_key=m.public_key\n'
            '            WHERE m.song_id=? AND m.included_in_total=1 ORDER BY m.is_primary '
            'DESC,m.confidence DESC,COALESCE(p.recordings_count,-1) DESC'
        ),
                (song_id, )).fetchall()
        known = [r["recordings_count"] for r in rows if r["recordings_count"] is not None]
        total = sum(known) if known else None
        primary = next((r for r in rows if r["is_primary"]), rows[0] if rows else None)
        covers = sum(int(r["visible_covers_count"] or 0) for r in rows)
        visible_sums = [int(r["visible_plays_sum"]) for r in rows if r["visible_plays_sum"] is not None]
        visible_max = [int(r["visible_plays_max"]) for r in rows if r["visible_plays_max"] is not None]
        return {"rows":rows, "count":len(rows), "total":total, "primary":primary,
                "visible_covers":covers, "visible_plays_sum":sum(visible_sums) if visible_sums else None,
                "visible_plays_max":max(visible_max) if visible_max else None}

    # StarMaker AutoData base + Coverage Recovery V1.4.3

    def sm_begin_scan(self):
        cur = self.con.execute("INSERT INTO starmaker_scan_runs(status) VALUES('running')")
        self.con.commit()
        return cur.lastrowid

    def sm_finish_scan(self, run_id, status, ok, failed, entries, matched, message=""):
        self.con.execute((
            'UPDATE starmaker_scan_runs SET finished_at=?,status=?,pages_ok=?,pages_failed=?,entr'
            'ies_found=?,matched_songs=?,message=? WHERE id=?'
        ),
            (now_iso(), status, ok, failed, entries, matched, message, run_id))
        self.set_setting("starmaker_last_auto_scan", now_iso())

    def sm_last_scan(self):
        return self.con.execute("SELECT * FROM starmaker_scan_runs ORDER BY id DESC LIMIT 1").fetchone()

    def sm_scan_stale(self, hours=STARMAKER_TTL_HOURS):
        raw = self.setting("starmaker_last_auto_scan", "")
        if not raw:
            return True
        try:
            return (datetime.now()-datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")).total_seconds() >= hours*3600
        except:
            return True

    def sm_ingest_entries(self, entries):
        n = 0
        for e in entries:
            title = (e.get("title") or "").strip()
            artist = (e.get("artist") or "").strip()
            key = (e.get("public_key") or _sm_public_key(title, artist, e.get("url") or "")).strip()
            if not title or not artist or not key:
                continue
            self.con.execute((
                'INSERT INTO starmaker_public_catalog(public_key,starmaker_song_id,url,title,artist,v'
                'ariant,normalized_title,normalized_artist,recordings_count,source_url,source_label,s'
                'ource_kind,region_code,position,last_seen_at,uploaded_by,visible_covers_count,visibl'
                'e_plays_sum,visible_plays_max)\n'
                '                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON '
                'CONFLICT(public_key) DO UPDATE SET\n'
                "                starmaker_song_id=CASE WHEN excluded.starmaker_song_id<>'' THEN "
                'excluded.starmaker_song_id ELSE starmaker_public_catalog.starmaker_song_id END,\n'
                "                url=CASE WHEN excluded.url<>'' THEN excluded.url ELSE "
                'starmaker_public_catalog.url END,title=excluded.title,artist=excluded.artist,variant'
                '=excluded.variant,\n                normalized_title=excluded.normalized_title,normal'
                'ized_artist=excluded.normalized_artist,recordings_count=COALESCE(excluded.recordings'
                '_count,starmaker_public_catalog.recordings_count),\n'
                '                source_url=excluded.source_url,source_label=excluded.source_label,so'
                'urce_kind=excluded.source_kind,region_code=excluded.region_code,position=excluded.po'
                'sition,last_seen_at=excluded.last_seen_at,\n'
                "                uploaded_by=CASE WHEN excluded.uploaded_by<>'' THEN "
                'excluded.uploaded_by ELSE starmaker_public_catalog.uploaded_by END,\n'
                '                visible_covers_count=MAX(starmaker_public_catalog.visible_covers_cou'
                'nt,excluded.visible_covers_count),\n'
                '                visible_plays_sum=COALESCE(excluded.visible_plays_sum,starmaker_publ'
                'ic_catalog.visible_plays_sum),visible_plays_max=COALESCE(excluded.visible_plays_max,'
                'starmaker_public_catalog.visible_plays_max)'
            ),
                (key,
                    e.get("starmaker_song_id", ""),
                    e.get("url", ""),
                    title,
                    artist,
                    e.get("variant", ""),
                    normalize_match_text(title),
                    normalize_match_text(artist),
                    e.get("recordings_count"),
                    e.get("source_url", ""),
                    e.get("source_label", ""),
                    e.get("source_kind", "catalog"),
                    e.get("region_code", ""),
                    e.get("position"),
                    now_iso(),
                    e.get("uploaded_by", ""),
                    int(e.get("visible_covers_count") or 0),
                    e.get("visible_plays_sum"),
                    e.get("visible_plays_max")))
            if e.get("source_kind")=="chart" and e.get("region_code"):
                self.con.execute((
                    'INSERT INTO starmaker_chart_presence(public_key,chart_code,chart_name,position,last_'
                    'seen_at) VALUES(?,?,?,?,?)\n                    ON CONFLICT(public_key,chart_code) '
                    'DO UPDATE SET chart_name=excluded.chart_name,position=excluded.position,last_seen_at'
                    '=excluded.last_seen_at'
                ),
                    (key,
                        e.get("region_code"),
                        e.get("source_label", e.get("region_code")),
                        e.get("position"),
                        now_iso()))
            n+=1
        self.con.commit()
        return n

    @staticmethod
    def _sm_version_tokens(value):
        v = normalize_match_text(value)
        return {x for x in ["piano",
            "acoustic",
            "acustico",
            "short",
            "remix",
            "live",
            "slowed",
            "male",
            "female",
            "lower",
            "higher",
            "deluxe"] if x in v}

    def _sm_auto_score(self, song, remote):
        base = match_confidence(song["artist"], song["song"], remote["artist"], remote["title"])
        lt = self._sm_version_tokens(song["song"]+" "+(song["genre"] or ""))
        rt = self._sm_version_tokens(remote["title"]+" "+(remote["variant"] or ""))
        if lt and rt:
            base += 8 if lt & rt else -18
        elif lt and not rt:
            base-=10
        elif rt and not lt:
            base-=5
        return max(0, min(100, base))

    def sm_auto_match_v141_legacy(self, song_ids=None):
        public = self.con.execute("SELECT * FROM starmaker_public_catalog WHERE trim(title)<>'' AND trim(artist)<>''").fetchall()
        if not public:
            return 0
        if song_ids:
            qs = ','.join('?' for _ in song_ids)
            songs = self.con.execute(f"SELECT * FROM songs WHERE id IN ({qs})", list(song_ids)).fetchall()
        else:
            songs = self.con.execute("SELECT * FROM songs ORDER BY id").fetchall()
        # Reduce candidates by normalized title first token for speed while retaining fuzzy fallback.
        by_first = {}
        for r in public:
            k = (r["normalized_title"] or "")[:1]
            by_first.setdefault(k, []).append(r)
        matched = 0
        for s in songs:
            ns = normalize_match_text(s["song"])
            cand = by_first.get(ns[:1], public)
            ranked = []
            for r in cand:
                title_ratio = difflib.SequenceMatcher(None, ns, r["normalized_title"] or "").ratio()
                if title_ratio<0.58:
                    continue
                score = self._sm_auto_score(s, r)
                ranked.append((score, r))
            ranked.sort(key=lambda x:(x[0], x[1]["recordings_count"] or -1), reverse=True)
            best = ranked[0] if ranked else None
            if not best or best[0]<72:
                self.con.execute((
                    'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                    "VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key='',confidence=0,stat"
                    "us='Sin coincidencia en índice',updated_at=excluded.updated_at"
                ),
                    (s["id"], "", 0, "Sin coincidencia en índice", now_iso()))
                continue
            score, r = best
            status = "Encontrada automática" if score>=88 else "Revisar coincidencia"
            self.con.execute((
                'INSERT INTO starmaker_auto_match(song_id,public_key,confidence,status,updated_at) '
                'VALUES(?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET public_key=excluded.public_key,'
                'confidence=excluded.confidence,status=excluded.status,updated_at=excluded.updated_at'
            ),
                (s["id"], r["public_key"], score, status, now_iso()))
            if score>=88:
                internal_url = r["url"] or (r["source_url"]+"#autodata-"+str(r["id"]))
                data = {"starmaker_song_id":r["starmaker_song_id"],
                    "starmaker_url":internal_url,
                    "source_url":r["source_url"],
                    "title":r["title"],
                    "artist":r["artist"],
                    "variant":r["variant"],
                    "recordings_count":r["recordings_count"],
                    "match_confidence":score}
                # evita generar múltiples snapshots iguales el mismo día
                existing = self.con.execute("SELECT id,recordings_count FROM starmaker_tracks WHERE song_id=? AND starmaker_url=?",
                    (s["id"], internal_url)).fetchone()
                self.upsert_starmaker_track(s["id"], data, select=True)
                if existing:
                    tr = self.con.execute("SELECT id FROM starmaker_tracks WHERE song_id=? AND starmaker_url=?",
                        (s["id"], internal_url)).fetchone()
                    if tr:
                        # borra duplicados del mismo día dejando el último
                        day = today_iso()+"%"
                        ids = self.con.execute("SELECT id FROM starmaker_snapshots WHERE starmaker_track_id=? AND checked_at LIKE ? ORDER BY id DESC",
                            (tr["id"], day)).fetchall()
                        for extra in ids[1:]:
                            self.con.execute("DELETE FROM starmaker_snapshots WHERE id=?", (extra[0], ))
                matched+=1
            else:
                self.starmaker_set_status(s["id"], "Coincidencia dudosa", f"AutoData {score}/100")
        self.con.commit()
        return matched

    def sm_chart_codes_for_song(self, song_id):
        row = self.con.execute("SELECT public_key FROM starmaker_auto_match WHERE song_id=?",
            (song_id, )).fetchone()
        if not row or not row[0]:
            return ""
        vals = [r[0] for r in self.con.execute("SELECT chart_code FROM starmaker_chart_presence WHERE public_key=? ORDER BY chart_code",
            (row[0], )).fetchall()]
        return ", ".join(vals)

    def sm_trend(self, track_id, days):
        latest = self.con.execute((
            'SELECT recordings_count,checked_at FROM starmaker_snapshots WHERE '
            'starmaker_track_id=? AND recordings_count IS NOT NULL ORDER BY checked_at DESC,id '
            'DESC LIMIT 1'
        ),
            (track_id, )).fetchone()
        if not latest:
            return (None, None)
        try:
            target = datetime.strptime(latest["checked_at"], "%Y-%m-%d %H:%M:%S").timestamp()-days*86400
        except:
            return (None, None)
        rows = self.con.execute((
            'SELECT recordings_count,checked_at FROM starmaker_snapshots WHERE '
            'starmaker_track_id=? AND recordings_count IS NOT NULL ORDER BY checked_at'
        ),
            (track_id, )).fetchall()
        ref = None
        for r in rows:
            try:
                ts = datetime.strptime(r["checked_at"], "%Y-%m-%d %H:%M:%S").timestamp()
            except:
                continue
            if ts<=target:
                ref = r
        if not ref or ref["recordings_count"] in (None, 0):
            return (None, None)
        change = latest["recordings_count"]-ref["recordings_count"]
        pct = change*100.0/ref["recordings_count"]
        return change, pct

    def sm_catalog_auto(self, search="", emotion="", source="", genre="", availability="Todos"):
        # Filtra primero con la consulta existente; disponibilidad se recalcula por matches profundos.
        rows = self.starmaker_catalog(search, emotion, source, genre, "Todos")
        out = []
        for r in rows:
            d = dict(r)
            agg = self.sm_song_aggregate(r["id"])
            primary = agg["primary"]
            d["variant_count"] = agg["count"]
            d["recordings_total"] = agg["total"]
            d["primary_recordings"] = primary["recordings_count"] if primary else None
            d["recordings_count"] = agg["total"]
            d["variant"] = (primary["variant"] or primary["title"]) if primary else (r["variant"] or "")
            d["visible_covers"] = agg.get("visible_covers", 0)
            d["visible_plays_sum"] = agg.get("visible_plays_sum")
            d["visible_plays_max"] = agg.get("visible_plays_max")
            d["charts"] = self.sm_chart_codes_for_song(r["id"])
            d["trend7"] = self.sm_trend(r["track_id"], 7)[1] if r["track_id"] else None
            d["trend30"] = self.sm_trend(r["track_id"], 30)[1] if r["track_id"] else None
            am = self.con.execute("SELECT status,confidence FROM starmaker_auto_match WHERE song_id=?",
                (r["id"], )).fetchone()
            d["sm_status"] = ("Encontrada" if d["recordings_count"] is not None else "Encontrada · sin total") if agg["count"] else ((am["status"] if am else "Sin investigar") or "Sin investigar")
            d["match_confidence"] = (am["confidence"] if am else None)
            if availability=="Sí" and not agg["count"]:
                continue
            if availability=="No" and agg["count"]:
                continue
            if availability=="Sin investigar" and am:
                continue
            out.append(d)
        return out

    def sm_public_summary(self):
        base = self.starmaker_summary()
        base["indexed"] = self.con.execute("SELECT COUNT(*) FROM starmaker_public_catalog").fetchone()[0]
        base["found"] = self.con.execute("SELECT COUNT(DISTINCT song_id) FROM starmaker_song_matches WHERE included_in_total=1").fetchone()[0]
        base["recordings"] = self.con.execute((
            'SELECT COALESCE(SUM(recordings_count),0) FROM starmaker_public_catalog WHERE '
            'public_key IN (SELECT DISTINCT public_key FROM starmaker_song_matches WHERE '
            'included_in_total=1)'
        )).fetchone()[0]
        base["pages"] = self.con.execute("SELECT COALESCE(SUM(pages_ok),0) FROM (SELECT pages_ok FROM starmaker_scan_runs ORDER BY id DESC LIMIT 1)").fetchone()[0]
        base["charts"] = self.con.execute("SELECT COUNT(DISTINCT public_key||':'||chart_code) FROM starmaker_chart_presence").fetchone()[0]
        base["last_scan"] = self.setting("starmaker_last_auto_scan", "") or "Sin actualizar"
        base["artists_indexed"] = self.con.execute("SELECT COUNT(*) FROM starmaker_artist_directory").fetchone()[0]
        base["artist_pages_scanned"] = self.con.execute("SELECT COUNT(*) FROM starmaker_artist_scan_state WHERE status='OK'").fetchone()[0]
        base["rescued"] = self.con.execute("SELECT COUNT(*) FROM starmaker_rescue_state WHERE status LIKE 'Encontrada%'").fetchone()[0]
        top = self.con.execute((
            'SELECT s.song,s.artist,SUM(COALESCE(p.recordings_count,0)) recordings_count FROM '
            'starmaker_song_matches m JOIN songs s ON s.id=m.song_id JOIN '
            'starmaker_public_catalog p ON p.public_key=m.public_key WHERE m.included_in_total=1 '
            'GROUP BY s.id ORDER BY recordings_count DESC LIMIT 1'
        )).fetchone()
        base["top"] = top
        return base

    def sm_chart_rows(self):
        return self.con.execute((
            'SELECT c.chart_code,c.chart_name,c.position,p.title,p.artist,p.recordings_count,p.pu'
            'blic_key,c.last_seen_at\n            FROM starmaker_chart_presence c JOIN '
            'starmaker_public_catalog p ON p.public_key=c.public_key\n'
            '            ORDER BY c.chart_code,c.position,p.recordings_count DESC'
        )).fetchall()

    def sm_playlist_analysis(self, setlist_id):
        items = self.setlist_items(setlist_id)
        rows = []
        total = found = high = medium = low = charts = 0
        for it in items:
            agg = self.sm_song_aggregate(it["id"])
            tr = agg["primary"]
            cnt = agg["total"]
            ch = self.sm_chart_codes_for_song(it["id"])
            if agg["count"]:
                found+=1
                total+=cnt or 0
            if cnt is not None:
                if cnt>=100000:
                    high+=1
                elif cnt>=10000:
                    medium+=1
                else:
                    low+=1
            if ch:
                charts+=1
            rows.append((it, tr, ch, agg["count"], cnt))
        return {"items":rows,
            "songs":len(items),
            "found":found,
            "missing":len(items)-found,
            "total":total,
            "high":high,
            "medium":medium,
            "low":low,
            "charts":charts}

    # Stats

    def save_stats(self, song_id: int, values: dict):
        fields = [
            "youtube_video_id",
                "youtube_title",
                "youtube_channel",
                "youtube_views",
                "youtube_likes",
                "youtube_top_country",
                "youtube_updated_at",
            "spotify_url", "spotify_streams", "spotify_top_country", "spotify_updated_at",
        ]
        vals = [values.get(f) for f in fields]
        sql = ",".join(f"{f}=?" for f in fields)
        self.con.execute(f"UPDATE songs SET {sql}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            vals + [song_id])
        self.con.commit()

    def import_stats_csv(self, path: str):
        updated = 0
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            for row in rd:
                artist = (row.get("artist") or row.get("artista") or "").strip()
                song = (row.get("song") or row.get("cancion") or row.get("canción") or "").strip()
                if not song:
                    continue
                found = self.con.execute(
                    "SELECT id FROM songs WHERE lower(song)=lower(?) AND (?='' OR lower(artist)=lower(?)) ORDER BY id LIMIT 1",
                    (song, artist, artist),
                ).fetchone()
                if not found:
                    continue
                mapping = {
                    "youtube_views": row.get("youtube_views") or row.get("youtube_vistas"),
                    "youtube_top_country": row.get("youtube_top_country") or row.get("youtube_pais") or row.get("youtube_país"),
                    "spotify_streams": row.get("spotify_streams") or row.get("spotify_reproducciones"),
                    "spotify_top_country": row.get("spotify_top_country") or row.get("spotify_pais") or row.get("spotify_país"),
                    "spotify_url": row.get("spotify_url") or "",
                }
                for k in ("youtube_views", "spotify_streams"):
                    try:
                        mapping[k] = int(str(mapping[k]).replace(".", "").replace(",", "")) if mapping[k] not in (None,
                            "") else None
                    except Exception:
                        mapping[k] = None
                current = self.get_song(found[0])
                vals = {f: current[f] for f in [
                    "youtube_video_id",
                        "youtube_title",
                        "youtube_channel",
                        "youtube_views",
                        "youtube_likes",
                        "youtube_top_country",
                        "youtube_updated_at",
                    "spotify_url", "spotify_streams", "spotify_top_country", "spotify_updated_at",
                ]}
                vals.update({k:v for k, v in mapping.items() if v not in (None, "")})
                if mapping.get("spotify_streams") is not None:
                    vals["spotify_updated_at"] = today_iso()
                if mapping.get("youtube_views") is not None:
                    vals["youtube_updated_at"] = today_iso()
                self.save_stats(found[0], vals)
                updated += 1
        return updated

    def export_library_csv(self, path: str):
        rows = self.con.execute("SELECT * FROM songs ORDER BY source_sheet,emotion_type,emotion_level,position").fetchall()
        fields = [
            "id",
                "source_sheet",
                "position",
                "artist",
                "song",
                "country",
                "year",
                "duration",
                "genre",
                "emotion_type",
                "emotion_level",
                "description",
                "notes",
            "youtube_video_id",
                "youtube_title",
                "youtube_channel",
                "youtube_views",
                "youtube_likes",
                "youtube_comments",
                "youtube_published_at",
                "youtube_duration_seconds",
                "youtube_match_confidence",
                "youtube_updated_at",
            "spotify_track_id",
                "spotify_title",
                "spotify_artist",
                "spotify_album",
                "spotify_release_date",
                "spotify_duration_ms",
                "spotify_explicit",
                "spotify_isrc",
                "spotify_url",
                "spotify_match_confidence",
                "spotify_updated_at"
        ]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=fields)
            wr.writeheader()
            for r in rows:
                wr.writerow({k:r[k] for k in fields})


class YouTubeClient:
    SEARCH = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS = "https://www.googleapis.com/youtube/v3/videos"

    @staticmethod
    def _get(url: str, params: dict):
        req_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(req_url, headers={"User-Agent": f"{APP_NAME}/{VERSION}"})
        with urllib.request.urlopen(req, timeout=18) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _score_candidate(artist:str, song:str, title:str, channel:str):
        ns = normalize_match_text(song)
        na = normalize_match_text(artist)
        nt = normalize_match_text(title)
        nc = normalize_match_text(channel)
        clean = nt
        for token in ("official video",
            "official audio",
            "official music video",
            "lyrics",
            "lyric video",
            "audio"):
            clean = clean.replace(token, "").strip()
        title_score = difflib.SequenceMatcher(None, ns, clean).ratio()*65
        artist_score = max(difflib.SequenceMatcher(None, na, nc).ratio(),
            difflib.SequenceMatcher(None, na, nt).ratio())*25
        bonus = 0
        low = (title+" "+channel).lower()
        if "official" in low:
            bonus+=7
        if "topic" in low:
            bonus+=4
        if any(x in low for x in ("karaoke", "cover", "reaction", "tutorial")):
            bonus-=18
        if "remix" in low and "remix" not in song.lower():
            bonus-=12
        return max(0, min(100, int(round(title_score+artist_score+bonus))))

    @classmethod
    def search(cls, api_key: str, artist: str, song: str):
        data = cls._get(cls.SEARCH,
            {"part":"snippet",
                "type":"video",
                "videoCategoryId":"10",
                "maxResults":8,
                "q":f"{artist} {song}",
                "key":api_key})
        out = []
        for item in data.get("items", []):
            sn = item.get("snippet", {})
            vid = item.get("id", {}).get("videoId", "")
            if not vid:
                continue
            score = cls._score_candidate(artist, song, sn.get("title", ""), sn.get("channelTitle", ""))
            out.append({"video_id":vid,
                "title":sn.get("title", ""),
                "channel":sn.get("channelTitle", ""),
                "channel_id":sn.get("channelId", ""),
                "published_at":sn.get("publishedAt", ""),
                "confidence":score})
        out.sort(key=lambda x:x["confidence"], reverse=True)
        return out

    @classmethod
    def stats(cls, api_key: str, video_id: str, confidence:int=0):
        data = cls._get(cls.VIDEOS,
            {"part":"snippet,statistics,contentDetails", "id":video_id, "key":api_key})
        if not data.get("items"):
            raise ValueError("YouTube no devolvió ese video.")
        item = data["items"][0]
        st = item.get("statistics", {})
        sn = item.get("snippet", {})
        cd = item.get("contentDetails", {})
        return {"youtube_video_id":video_id,
            "youtube_title":sn.get("title", ""),
            "youtube_channel":sn.get("channelTitle", ""),
            "youtube_channel_id":sn.get("channelId", ""),
                "youtube_views":int(st["viewCount"]) if st.get("viewCount") is not None else None,
                    "youtube_likes":int(st["likeCount"]) if st.get("likeCount") is not None else None,
                "youtube_comments":int(st["commentCount"]) if st.get("commentCount") is not None else None,
                    "youtube_published_at":sn.get("publishedAt", ""),
                "youtube_duration_seconds":parse_iso8601_duration(cd.get("duration", "")),
                    "youtube_match_confidence":int(confidence or 0),
                    "youtube_updated_at":now_iso()}

    @classmethod
    def stats_many(cls, api_key:str, video_ids:list[str]):
        out = {}
        ids = [x for x in dict.fromkeys(video_ids) if x]
        for i in range(0, len(ids), 50):
            batch = ids[i:i+50]
            data = cls._get(cls.VIDEOS,
                {"part":"snippet,statistics,contentDetails", "id":",".join(batch), "key":api_key})
            for item in data.get("items", []):
                vid = item.get("id", "")
                st = item.get("statistics", {})
                sn = item.get("snippet", {})
                cd = item.get("contentDetails", {})
                out[vid] = {"youtube_video_id":vid,
                    "youtube_title":sn.get("title", ""),
                    "youtube_channel":sn.get("channelTitle", ""),
                    "youtube_channel_id":sn.get("channelId", ""),
                          "youtube_views":int(st["viewCount"]) if st.get("viewCount") is not None else None,
                              "youtube_likes":int(st["likeCount"]) if st.get("likeCount") is not None else None,
                          "youtube_comments":int(st["commentCount"]) if st.get("commentCount") is not None else None,
                              "youtube_published_at":sn.get("publishedAt", ""),
                          "youtube_duration_seconds":parse_iso8601_duration(cd.get("duration", "")),
                              "youtube_updated_at":now_iso()}
        return out


class SpotifyClient:
    API = "https://api.spotify.com/v1"
    AUTH = "https://accounts.spotify.com/authorize"
    TOKEN = "https://accounts.spotify.com/api/token"

    @staticmethod
    def _json_request(url, headers=None, data=None, method=None, timeout=20):
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"Spotify HTTP {exc.code}: {body[:300]}")

    @classmethod
    def _post_form(cls, url, params):
        return cls._json_request(url,
            {"Content-Type":"application/x-www-form-urlencoded", "User-Agent":f"{APP_NAME}/{VERSION}"},
            urllib.parse.urlencode(params).encode(),
            "POST")

    @classmethod
    def ensure_token(cls, db):
        token = db.setting("spotify_access_token", "")
        expires = float(db.setting("spotify_token_expires_at", "0") or 0)
        if token and time.time()<expires-45:
            return token
        refresh = db.setting("spotify_refresh_token", "")
        client_id = db.setting("spotify_client_id", "").strip()
        if not refresh or not client_id:
            return ""
        data = cls._post_form(cls.TOKEN,
            {"grant_type":"refresh_token", "refresh_token":refresh, "client_id":client_id})
        token = data.get("access_token", "")
        
        if not token:
            return ""
        db.set_setting("spotify_access_token", token)
        db.set_setting("spotify_token_expires_at", str(time.time()+int(data.get("expires_in", 3600))))
        if data.get("refresh_token"):
            db.set_setting("spotify_refresh_token", data["refresh_token"])
        return token

    @classmethod
    def connect_pkce(cls, db, timeout=180):
        client_id = db.setting("spotify_client_id", "").strip()
        if not client_id:
            raise ValueError("Ingresá primero el Client ID de Spotify.")
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state = secrets.token_urlsafe(18)
        result = {}
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                result.update({k:(v[0] if v else "") for k, v in q.items()})
                body = b"<html><body style='font-family:Segoe UI;background:#080D1B;color:#fff'><h2>Spotify conectado</h2><p>Podes volver a Playlist Emotion Studio.</p></body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass
        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        redirect = f"http://127.0.0.1:{port}/callback"
        params = {"client_id":client_id,
            "response_type":"code",
            "redirect_uri":redirect,
            "code_challenge_method":"S256",
            "code_challenge":challenge,
            "state":state}
        webbrowser.open(cls.AUTH+"?"+urllib.parse.urlencode(params))
        server.timeout = timeout
        server.handle_request()
        server.server_close()
        if result.get("state")!=state:
            raise RuntimeError("Spotify no devolvió un estado OAuth válido.")
        if result.get("error"):
            raise RuntimeError("Spotify: "+result["error"])
        code = result.get("code", "")
        if not code:
            raise RuntimeError("No se recibió el código de autorización de Spotify.")
        data = cls._post_form(cls.TOKEN,
            {"client_id":client_id,
                "grant_type":"authorization_code",
                "code":code,
                "redirect_uri":redirect,
                "code_verifier":verifier})
        token = data.get("access_token", "")
        if not token:
            raise RuntimeError("Spotify no devolvió access_token.")
        db.set_setting("spotify_access_token", token)
        db.set_setting("spotify_refresh_token",
            data.get("refresh_token", "") or db.setting("spotify_refresh_token", ""))
        db.set_setting("spotify_token_expires_at", str(time.time()+int(data.get("expires_in", 3600))))
        return True

    @classmethod
    def _api_get(cls, db, path, params=None):
        token = cls.ensure_token(db)
        if not token:
            raise RuntimeError("Spotify no está conectado. Configuración → Spotify → Conectar Spotify.")
        url = cls.API+path+("?"+urllib.parse.urlencode(params) if params else "")
        return cls._json_request(url, {"Authorization":"Bearer "+token, "User-Agent":f"{APP_NAME}/{VERSION}"})

    @staticmethod
    def _score_candidate(artist, song, item):
        title = item.get("name", "")
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        ns = normalize_match_text(song)
        na = normalize_match_text(artist)
        nt = normalize_match_text(title)
        nar = normalize_match_text(artists)
        score = difflib.SequenceMatcher(None, ns, nt).ratio()*70+difflib.SequenceMatcher(None, na, nar).ratio()*30
        low = title.lower()
        if "remix" in low and "remix" not in song.lower():
            score-=18
        if any(x in low for x in ("karaoke", "tribute")):
            score-=20
        return max(0, min(100, int(round(score))))

    @classmethod
    def search_track(cls, db, artist, song):
        # Consulta pública autenticada; no requiere scopes de usuario.
        data = cls._api_get(db, "/search", {"q":f'track:"{song}" artist:"{artist}"', "type":"track", "limit":10})
        container = data.get("tracks") or data.get("items") or {}
        items = container.get("items", []) if isinstance(container, dict) else []
        ranked = []
        for item in items:
            score = cls._score_candidate(artist, song, item)
            ranked.append((score, item))
        ranked.sort(key=lambda x:x[0], reverse=True)
        if not ranked:
            return None
        score, item = ranked[0]
        album = item.get("album") or {}
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        external = item.get("external_ids") or {}
        urls = item.get("external_urls") or {}
        return {"spotify_track_id":item.get("id", "") or "",
            "spotify_title":item.get("name", "") or "",
            "spotify_artist":artists,
            "spotify_album":album.get("name", "") or "",
                "spotify_release_date":album.get("release_date", "") or "",
                    "spotify_duration_ms":item.get("duration_ms"),
                    "spotify_explicit":1 if item.get("explicit") else 0,
                "spotify_isrc":external.get("isrc", "") or "",
                    "spotify_url":urls.get("spotify", "") or "",
                    "spotify_match_confidence":score,
                    "spotify_updated_at":now_iso()}

    @classmethod
    def refresh_track(cls, db, track_id):
        item = cls._api_get(db, "/tracks/"+urllib.parse.quote(track_id))
        album = item.get("album") or {}
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        external = item.get("external_ids") or {}
        urls = item.get("external_urls") or {}
        return {"spotify_track_id":item.get("id", track_id),
            "spotify_title":item.get("name", "") or "",
            "spotify_artist":artists,
            "spotify_album":album.get("name", "") or "",
                "spotify_release_date":album.get("release_date", "") or "",
                    "spotify_duration_ms":item.get("duration_ms"),
                    "spotify_explicit":1 if item.get("explicit") else 0,
                "spotify_isrc":external.get("isrc", "") or "",
                    "spotify_url":urls.get("spotify", "") or "",
                    "spotify_updated_at":now_iso()}


class StyledButton(tk.Button):

    def __init__(self, master, text, command=None, accent=False, danger=False, **kwargs):
        if accent:
            bg, active = COLORS["accent"], COLORS["accent_hover"]
        elif danger:
            bg, active = COLORS["danger"], COLORS["danger_hover"]
        else:
            bg, active = COLORS["panel2"], COLORS["accent2"]
        super().__init__(
            master, text=text, command=command, bg=bg, fg=COLORS["white"],
            activebackground=active, activeforeground=COLORS["white"],
            relief="flat", bd=0, highlightthickness=1, highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"], padx=12, pady=7,
            font=("Segoe UI", 9, "bold"), cursor="hand2", **kwargs
        )


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.language = self.db.setting("ui_language", "es") or "es"
        self.title(f"{APP_NAME} · V{VERSION}")
        self.geometry("1500x900")
        self.minsize(960, 620)
        self.configure(bg=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._setup_style()
        self.views = {}
        self.current_view = None
        self._build_shell()
        self.show("dashboard")

    def tr(self, text):
        return ui_tr(text, self.language)

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview",
            background=COLORS["panel"],
            fieldbackground=COLORS["panel"],
            foreground=COLORS["text"],
            rowheight=28,
            borderwidth=1,
            relief="solid",
            font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
            background=COLORS["panel2"],
            foreground=COLORS["text"],
            relief="flat",
            font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
            background=[("selected", COLORS["accent2"])],
            foreground=[("selected", COLORS["white"])])
        style.configure("TCombobox",
            fieldbackground=COLORS["panel2"],
            background=COLORS["panel2"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"])
        style.configure("TNotebook", background=COLORS["panel"], borderwidth=1)
        style.configure("TNotebook.Tab",
            background=COLORS["panel2"],
            foreground=COLORS["text"],
            padding=(15, 8),
            font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
            background=[("selected", COLORS["accent2"])],
            foreground=[("selected", COLORS["white"])])
        style.configure("Horizontal.TProgressbar",
            troughcolor=COLORS["panel2"],
            background=COLORS["teal"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["teal"],
            darkcolor=COLORS["teal"])

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg="#070B16", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        top = tk.Canvas(self.sidebar, height=150, bg="#070B16", highlightthickness=0)
        top.pack(fill="x")
        w = 220
        top.create_polygon(0, 0, w, 0, w, 74, 140, 114, 0, 62, fill="#111B34", outline="")
        top.create_polygon(0, 84, 75, 120, 36, 150, 0, 150, fill=COLORS["accent2"], outline="")
        top.create_line(15, 30, 195, 115, fill=COLORS["accent"], width=2)
        top.create_line(35, 38, 203, 102, fill=COLORS["teal"], width=1)
        top.create_oval(22, 27, 34, 39, fill=COLORS["teal"], outline="")
        top.create_text(20, 62, anchor="w", text="PLAYLIST", fill=COLORS["white"], font=("Segoe UI", 20, "bold"))
        top.create_text(20,
            91,
            anchor="w",
            text="EMOTION STUDIO",
            fill=COLORS["accent"],
            font=("Segoe UI", 10, "bold"))
        top.create_text(20,
            118,
            anchor="w",
            text="Intelligence · UVE · Shows",
            fill=COLORS["muted"],
            font=("Segoe UI", 8))
        nav = [("dashboard", "▦  "+self.tr("Resumen")),
            ("library", "♫  "+self.tr("Biblioteca")),
            ("positive", "＋  "+self.tr("Emoción positiva")),
            ("neutral", "◇  "+self.tr("Emoción neutra")),
            ("negative", "−  "+self.tr("Emoción negativa")),
            ("setlist", "≡  "+self.tr("Programador")),
            ("starmaker", "★  StarMaker"),
            ("stats", "◫  "+self.tr("Plataformas")),
            ("settings", "⚙  "+self.tr("Configuración"))]
        self.nav_buttons = {}
        for key, label in nav:
            b = tk.Button(self.sidebar,
                text=label,
                anchor="w",
                command=lambda k=key:self.show(k),
                bg="#070B16",
                fg=COLORS["muted"],
                activebackground=COLORS["panel2"],
                activeforeground=COLORS["white"],
                relief="flat",
                bd=0,
                padx=20,
                pady=11,
                font=("Segoe UI", 10),
                cursor="hand2")
            b.pack(fill="x")
            self.nav_buttons[key] = b
        tk.Frame(self.sidebar, bg=COLORS["line"], height=1).pack(fill="x", padx=18, pady=12)
        total = self.db.con.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
        slc = self.db.con.execute("SELECT COUNT(*) FROM setlists").fetchone()[0]
        self.sidebar_status = tk.Label(self.sidebar,
            text=f"SQLite · {total} canciones\n{slc} playlist(s) · V{VERSION}",
            justify="left",
            bg="#070B16",
            fg=COLORS["muted"],
            font=("Segoe UI", 8))
        self.sidebar_status.pack(anchor="w", padx=20)
        self.content = tk.Frame(self, bg=COLORS["bg"], highlightthickness=1, highlightbackground=COLORS["line"])
        self.content.pack(side="left", fill="both", expand=True)

    def apply_language(self, root):
        def walk(w):
            try:
                txt = w.cget("text")
                if txt and isinstance(txt, str):
                    new = ui_tr(txt, self.language)
                    if new!=txt:
                        w.configure(text=new)
            except Exception:
                pass
            if isinstance(w, ttk.Notebook):
                try:
                    for tab in w.tabs():
                        txt = w.tab(tab, "text")
                        w.tab(tab, text=ui_tr(txt, self.language))
                except Exception:
                    pass
            try:
                for ch in w.winfo_children():
                    walk(ch)
            except Exception:
                pass
        walk(root)

    def show(self, key):
        if self.current_view:
            self.current_view.pack_forget()
        if key not in self.views:
            if key=="dashboard":
                view = DashboardView(self.content, self)
            elif key=="library":
                view = LibraryView(self.content, self)
            elif key=="positive":
                view = EmotionView(self.content, self, "Positiva")
            elif key=="neutral":
                view = EmotionView(self.content, self, "Neutra")
            elif key=="negative":
                view = EmotionView(self.content, self, "Negativa")
            elif key=="setlist":
                view = SetlistView(self.content, self)
            elif key=="starmaker":
                view = StarMakerView(self.content, self)
            elif key=="stats":
                view = PlatformsView(self.content, self)
            else:
                view = SettingsView(self.content, self)
            self.views[key] = view
        self.current_view = self.views[key]
        self.current_view.pack(fill="both", expand=True)
        if hasattr(self.current_view, "refresh"):
            self.current_view.refresh()
        self.apply_language(self.current_view)
        for k, b in self.nav_buttons.items():
            b.configure(bg=COLORS["panel2"] if k==key else "#070B16",
                fg=COLORS["white"] if k==key else COLORS["muted"])

    def open_library_song(self, song_id:int):
        self.show("library")
        self.views["library"].select_song(song_id)

    def on_close(self):
        self.db.close()
        self.destroy()


class BaseView(tk.Frame):

    def __init__(self, master, app:App, title:str, subtitle:str):
        super().__init__(master, bg=COLORS["bg"])
        self.app = app
        self.db = app.db
        self.surface = ScrollSurface(self, min_width=1100, min_height=720)
        self.surface.pack(fill="both", expand=True, padx=5, pady=5)
        host = self.surface.inner
        head = tk.Frame(host, bg=COLORS["bg"], height=86)
        head.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(head,
            text=app.tr(title),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(head,
            text=app.tr(subtitle),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9)).pack(anchor="w",
            pady=(4, 0))
        self.body = tk.Frame(host, bg=COLORS["bg"])
        self.body.pack(fill="both", expand=True, padx=28, pady=(0, 24))


class DashboardView(BaseView):

    def __init__(self, master, app):
        super().__init__(master,
            app,
            "Resumen operativo",
            "Intelligence Dashboard: biblioteca, UVE, StarMaker, plataformas y preparación del próximo show.")
        self.cards = tk.Frame(self.body, bg=COLORS["bg"])
        self.cards.pack(fill="x")
        self.mid = tk.Frame(self.body, bg=COLORS["bg"])
        self.mid.pack(fill="both", expand=True, pady=(14, 0))
        self.bottom = tk.Frame(self.body, bg=COLORS["bg"])
        self.bottom.pack(fill="x", pady=(14, 0))

    def _card(self, parent, col, label, value, sub, color):
        f = tk.Frame(parent, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["line"])
        f.grid(row=col//3, column=col%3, sticky="nsew", padx=5, pady=5)
        parent.grid_columnconfigure(col%3, weight=1)
        tk.Label(f,
            text=label.upper(),
            bg=COLORS["card"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).pack(anchor="w",
            padx=14,
            pady=(11, 2))
        tk.Label(f,
            text=value,
            bg=COLORS["card"],
            fg=color,
            font=("Segoe UI", 18, "bold")).pack(anchor="w",
            padx=14)
        tk.Label(f,
            text=sub,
            bg=COLORS["card"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8)).pack(anchor="w",
            padx=14,
            pady=(2, 10))

    def refresh(self):
        for host in (self.cards, self.mid, self.bottom):
            for w in host.winfo_children():
                w.destroy()
        d = self.db.intelligence_dashboard()
        pl = d.get("playlist")
        specs = [("Canciones", format_int(d["total"]), "biblioteca activa", COLORS["text"]),
            ("StarMaker", f"{d['sm_found']}/{d['total']}", f"{d['sm_coverage']:.1f}% cobertura", COLORS["accent"]),
            ("Grabaciones", compact_count(d["sm_recordings"]), f"{d['sm_tracks']} pistas compatibles", COLORS["teal"]),
            ("Playlist activa", pl["name"] if pl else "—", f"{pl['songs']} canciones" if pl else "sin playlist", COLORS["accent2"]),
            ("Duración show", seconds_to_human(pl["seconds"]) if pl else "—", f"objetivo {pl['target_minutes']} min" if pl else "sin datos", COLORS["aqua"]),
            ("Plataformas",
                f"YT {d['youtube_found']} · SP {d['spotify_found']}",
                f"{d['youtube_coverage']:.0f}% / {d['spotify_coverage']:.0f}%",
                COLORS["positive"])]
        for i, s in enumerate(specs):
            self._card(self.cards, i, *s)
        left = tk.Frame(self.mid, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        right = tk.Frame(self.mid, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        right.pack(side="left", fill="both", expand=True, padx=(7, 0))
        tk.Label(left,
            text="TOP 10 · STARMAKER",
            bg=COLORS["panel"],
            fg=COLORS["accent"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=14,
            pady=(12, 4))
        canvas = tk.Canvas(left, bg=COLORS["panel"], highlightthickness=0, height=320)
        canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.after(40, lambda:self._draw_top(canvas, d["top_sm"]))
        tk.Label(right,
            text="UVE + REPERTORIO",
            bg=COLORS["panel"],
            fg=COLORS["teal"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=14,
            pady=(12, 8))
        total = max(1, d["total"])
        for name, color in (("Positiva", COLORS["positive"]),
            ("Neutra", COLORS["neutral"]),
            ("Negativa", COLORS["negative"])):
            n = d["emotions"].get(name, 0)
            row = tk.Frame(right, bg=COLORS["panel"])
            row.pack(fill="x", padx=14, pady=5)
            tk.Label(row,
                text=f"{name}: {n}",
                width=18,
                anchor="w",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=("Segoe UI", 9, "bold")).pack(side="left")
            bar = tk.Canvas(row, height=12, bg=COLORS["panel2"], highlightthickness=0)
            bar.pack(side="left", fill="x", expand=True)
            bar.update_idletasks()
            bar.create_rectangle(0, 0, max(3, bar.winfo_width()*n/total), 12, fill=color, outline="")
        src = d.get("top_source")
        gen = d.get("top_genre")
        tk.Label(right,
            text=f"Origen dominante: {src['source_sheet'] if src else '—'}",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 9)).pack(anchor="w",
            padx=14,
            pady=(16, 4))
        tk.Label(right,
            text=f"Género dominante: {gen['genre'] if gen else '—'}",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 9)).pack(anchor="w",
            padx=14,
            pady=4)
        if pl:
            sm = self.db.sm_playlist_analysis(pl["id"])
            txt = f"PRÓXIMO SHOW · {pl['name']}   |   {sm['songs']} canciones · {seconds_to_human(pl['seconds'])} · {sm['found']} con StarMaker · {sm['high']} uso alto · {sm['medium']} medio · {sm['low']} bajo"
        else:
            txt = "PRÓXIMO SHOW · No hay playlist activa"
        tk.Label(self.bottom,
            text=txt,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=16,
            pady=14).pack(fill="x")
        cov = tk.Frame(self.bottom, bg=COLORS["panel"])
        cov.pack(fill="x", pady=(8, 0))
        tk.Label(cov,
            text=f"Cobertura de datos  ·  StarMaker {d['sm_found']}/{d['total']}  ·  YouTube {d['youtube_found']}/{d['total']}  ·  Spotify {d['spotify_found']}/{d['total']}",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            padx=14,
            pady=10).pack(anchor="w")

    def _draw_top(self, c, rows):
        try:
            if not c.winfo_exists():
                return
            c.delete("all")
            w = max(520, c.winfo_width())
        except Exception:
            return
        maxv = max([int(r["recordings"] or 0) for r in rows]+[1])
        y = 10
        if not rows:
            c.create_text(12, 20, anchor="nw", text="Sin datos StarMaker todavía", fill=COLORS["muted"])
            return
        for r in rows[:10]:
            val = int(r["recordings"] or 0)
            label = f"{r['song']} — {r['artist']}"
            c.create_text(8, y+8, anchor="w", text=label[:42], fill=COLORS["text"], font=("Segoe UI", 8))
            x0 = 205
            x1 = w-70
            bw = (x1-x0)*(val/maxv)
            c.create_rectangle(x0, y, x1, y+16, fill=COLORS["panel2"], outline="")
            c.create_rectangle(x0, y, x0+bw, y+16, fill=COLORS["accent"], outline="")
            c.create_text(w-62,
                y+8,
                anchor="w",
                text=compact_count(val),
                fill=COLORS["teal"],
                font=("Segoe UI", 8, "bold"))
            y+=29


class SongEditorDialog(tk.Toplevel):
    """Editor por bloques con paneles redimensionables y scroll global."""

    def __init__(self, master, db: Database, row=None, defaults=None):
        super().__init__(master)
        self.db = db
        self.result = None
        self.row = row
        self.title("Editar canción" if row else "Nueva canción")
        self.geometry("1040x720")
        self.minsize(760, 520)
        self.configure(bg=COLORS["bg"])
        self.transient(master.winfo_toplevel())
        self.grab_set()

        values = {
            "source_sheet": SOURCES[0], "position": "", "song": "", "artist": "", "genre": "",
            "country": "", "year": "", "duration": "", "emotion_type": "Positiva",
            "emotion_level": "Principal", "description": "", "notes": "",
        }
        if defaults:
            values.update({k: v for k, v in defaults.items() if v not in (None, "")})
        if row is not None:
            for k in values:
                try:
                    values[k] = row[k] if row[k] is not None else ""
                except Exception:
                    pass

        self.surface = ScrollSurface(self, min_width=940, min_height=650)
        self.surface.pack(fill="both", expand=True, padx=6, pady=6)
        host = self.surface.inner

        head = tk.Frame(host, bg=COLORS["bg"])
        head.pack(fill="x", padx=24, pady=(18, 10))
        tk.Label(head,
            text="FICHA DE CANCIÓN",
            bg=COLORS["bg"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(head,
            text="Datos separados por función. Los paneles se pueden ampliar arrastrando sus divisores.",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 16, "bold")).pack(anchor="w",
            pady=(2, 0))

        outer = tk.PanedWindow(host,
            orient="vertical",
            bg=COLORS["line"],
            bd=0,
            sashwidth=8,
            sashpad=2,
            showhandle=True,
            handlesize=10)
        outer.pack(fill="both", expand=True, padx=24, pady=(0, 10))
        top = tk.PanedWindow(outer,
            orient="horizontal",
            bg=COLORS["line"],
            bd=0,
            sashwidth=8,
            sashpad=2,
            showhandle=True,
            handlesize=10)
        identity = self._card(top, "01 · IDENTIDAD MUSICAL")
        classification = self._card(top, "02 · CLASIFICACIÓN")
        top.add(identity, minsize=360, stretch="always")
        top.add(classification, minsize=390, stretch="always")
        content = self._card(outer, "03 · DESCRIPCIÓN Y NOTAS")
        outer.add(top, minsize=285, stretch="always")
        outer.add(content, minsize=240, stretch="always")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=1)

        self.vars = {}
        self._entry(identity, "song", "Canción", values["song"], 0, 0, span=2)
        self._entry(identity, "artist", "Artista / autor / banda", values["artist"], 1, 0, span=2)
        self._entry(identity, "year", "Año", values["year"], 2, 0)
        self._entry(identity, "duration", "Duración (mm:ss)", values["duration"], 2, 1)

        self._combo(classification,
            "source_sheet",
            "Origen / colección",
            values["source_sheet"],
            0,
            0,
            self.db.distinct("source_sheet") or SOURCES,
            editable=True)
        self._combo(classification,
            "genre",
            "Género / subgénero",
            values["genre"],
            0,
            1,
            load_genre_catalog(self.db),
            editable=True,
            searchable=True)
        self._combo(classification,
            "country",
            "País",
            values["country"],
            1,
            0,
            self.db.distinct("country"),
            editable=True)
        self._combo(classification,
            "emotion_type",
            "Tipo emocional",
            values["emotion_type"],
            1,
            1,
            EMOTIONS,
            editable=False)
        self._combo(classification,
            "emotion_level",
            "Nivel emocional",
            values["emotion_level"] if values["emotion_level"] in LEVELS else "Secundaria",
            2,
            0,
            LEVELS,
            editable=False)
        self._entry(classification, "position", "Posición", values["position"], 2, 1)
        tk.Label(classification,
            text="Origen identifica la colección. No determina el género musical.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8)).grid(row=8,
            column=0,
            columnspan=2,
            sticky="w",
            padx=12,
            pady=(7, 10))

        tk.Label(content,
            text="Descripción / vibración / función",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).grid(row=1,
            column=0,
            sticky="w",
            padx=12,
            pady=(8, 3))
        tk.Label(content,
            text="Notas",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).grid(row=1,
            column=1,
            sticky="w",
            padx=12,
            pady=(8, 3))
        self.description = tk.Text(content,
            height=8,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            highlightthickness=1,
            highlightbackground=COLORS["line_soft"])
        self.notes = tk.Text(content,
            height=8,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            highlightthickness=1,
            highlightbackground=COLORS["line_soft"])
        self.description.grid(row=2, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))
        self.notes.grid(row=2, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))
        self.description.insert("1.0", str(values["description"]))
        self.notes.insert("1.0", str(values["notes"]))

        self.minutes = tk.Label(identity,
            text="Duración calculada: 0,00 min",
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 8, "bold"))
        self.minutes.grid(row=8, column=0, columnspan=2, sticky="w", padx=12, pady=(2, 8))
        self.vars["duration"].trace_add("write", lambda *_: self._update_minutes())
        self._update_minutes()

        foot = tk.Frame(host, bg=COLORS["bg"])
        foot.pack(fill="x", padx=24, pady=(0, 20))
        tk.Label(foot,
            text="La posición se aplica dentro de Tipo emocional + Nivel.",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8)).pack(side="left")
        StyledButton(foot, "Cancelar", self.destroy).pack(side="right", padx=(8, 0))
        StyledButton(foot, "Guardar canción", self._save, accent=True).pack(side="right")
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-s>", lambda e: self._save())
        self.after(50, lambda: self.focus_force())

    def _card(self, parent, title):
        f = tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        tk.Label(f,
            text=title,
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 9, "bold")).grid(row=0,
            column=0,
            columnspan=4,
            sticky="w",
            padx=12,
            pady=(10, 2))
        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=1)
        return f

    def _entry(self, parent, key, label, value, row, col, span=1):
        r = row + 1
        tk.Label(parent,
            text=label,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).grid(row=r*2-1,
            column=col,
            columnspan=span,
            sticky="w",
            padx=12,
            pady=(7, 3))
        var = tk.StringVar(value=str(value))
        e = tk.Entry(parent,
            textvariable=var,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["line_soft"],
            highlightcolor=COLORS["accent"])
        e.grid(row=r*2, column=col, columnspan=span, sticky="ew", padx=12, ipady=6)
        self.vars[key] = var
        return e

    def _combo(self, parent, key, label, value, row, col, values, editable=False, searchable=False):
        r = row + 1
        tk.Label(parent,
            text=label,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).grid(row=r*2-1,
            column=col,
            sticky="w",
            padx=12,
            pady=(7, 3))
        var = tk.StringVar(value=str(value))
        cls = SearchableCombobox if searchable else ttk.Combobox
        cb = cls(parent, textvariable=var, values=values, state="normal" if editable else "readonly")
        cb.grid(row=r*2, column=col, sticky="ew", padx=12)
        self.vars[key] = var
        return cb

    def _update_minutes(self):
        sec = duration_to_seconds(self.vars["duration"].get())
        self.minutes.config(text=f"Duración calculada: {sec/60:.2f} min".replace(".", ","))

    def _save(self):
        d = {k: v.get().strip() for k, v in self.vars.items()}
        d["description"] = self.description.get("1.0", "end").strip()
        d["notes"] = self.notes.get("1.0", "end").strip()
        if not d["song"]:
            messagebox.showwarning("Dato requerido", "Ingresá el nombre de la canción.", parent=self)
            return
        if not d["source_sheet"] or not d["emotion_type"] or not d["emotion_level"]:
            messagebox.showwarning("Clasificación requerida",
                "Completá origen, tipo emocional y nivel.",
                parent=self)
            return
        try:
            d["position"] = int(d.get("position") or 0)
        except ValueError:
            messagebox.showwarning("Posición inválida",
                "La posición debe ser un número entero.",
                parent=self)
            return
        self.result = d
        self.destroy()


class LibraryView(BaseView):
    COLUMNS = ("pos",
        "song",
        "artist",
        "genre",
        "country",
        "emotion",
        "level",
        "year",
        "duration",
        "source")

    def __init__(self, master, app):
        super().__init__(master,
            app,
            "Biblioteca de canciones",
            "Filtros automáticos, género independiente del origen y paneles redimensionables.")
        self.selected_id = None
        self._filter_after = None
        self._drag_id = None
        self._drag_target = None
        self._drag_before = True

        actions = tk.Frame(self.body,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"])
        actions.pack(fill="x", pady=(0, 8))
        tk.Label(actions,
            text="ACCIONES",
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 8, "bold")).pack(side="left",
            padx=(12, 8))
        StyledButton(actions,
            "+ Nueva canción",
            self.new_song,
            accent=True).pack(side="left",
            padx=4,
            pady=8)
        StyledButton(actions, "Editar", self.edit_song).pack(side="left", padx=4)
        StyledButton(actions, "Eliminar", self.delete_song, danger=True).pack(side="left", padx=4)
        tk.Frame(actions, bg=COLORS["line"], width=1).pack(side="left", fill="y", padx=8, pady=8)
        StyledButton(actions, "↑ Subir", lambda: self.move_delta(-1)).pack(side="left", padx=4)
        StyledButton(actions, "↓ Bajar", lambda: self.move_delta(1)).pack(side="left", padx=4)
        StyledButton(actions, "Mover a #", self.move_to).pack(side="left", padx=4)
        StyledButton(actions, "⇄ Cambiar nivel", self.change_level, accent=True).pack(side="left", padx=4)
        StyledButton(actions, "Limpiar filtros", self.clear_filters).pack(side="right", padx=10)

        filters = tk.Frame(self.body,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"])
        filters.pack(fill="x", pady=(0, 10))
        self.search_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.emotion_var = tk.StringVar()
        self.level_var = tk.StringVar()
        self.genre_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.year_var = tk.StringVar()
        row1 = tk.Frame(filters, bg=COLORS["panel"])
        row1.pack(fill="x")
        row2 = tk.Frame(filters, bg=COLORS["panel"])
        row2.pack(fill="x", pady=(0, 2))
        self._filter_field(row1, "Buscar", self.search_var, 0, entry=True)
        self._filter_field(row1,
            "Origen",
            self.source_var,
            1,
            values=self.db.distinct("source_sheet") or SOURCES,
            editable=True)
        self._filter_field(row1, "Emoción", self.emotion_var, 2, values=[""] + EMOTIONS, editable=False)
        self._filter_field(row1, "Nivel", self.level_var, 3, values=[""] + LEVELS, editable=False)
        self._filter_field(row2,
            "Género",
            self.genre_var,
            0,
            values=self.db.distinct("genre"),
            editable=True)
        self._filter_field(row2,
            "País",
            self.country_var,
            1,
            values=self.db.distinct("country"),
            editable=True)
        self._filter_field(row2, "Año", self.year_var, 2, values=self.db.distinct_years(), editable=True)
        tk.Label(row2,
            text="FILTRADO AUTOMÁTICO",
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 8, "bold")).grid(row=1,
            column=3,
            sticky="e",
            padx=12,
            pady=(0, 9))
        for frame, count in ((row1, 4), (row2, 4)):
            for i in range(count):
                frame.grid_columnconfigure(i, weight=1)
        for var in [self.search_var,
            self.source_var,
            self.emotion_var,
            self.level_var,
            self.genre_var,
            self.country_var,
            self.year_var]:
            var.trace_add("write", self._schedule_refresh)

        split = tk.PanedWindow(self.body,
            orient="horizontal",
            bg=COLORS["line"],
            sashwidth=9,
            sashpad=2,
            showhandle=True,
            handlesize=11,
            bd=0,
            relief="flat")
        split.pack(fill="both", expand=True)
        table_frame = tk.Frame(split,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"])
        detail_frame = tk.Frame(split,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"])
        split.add(table_frame, minsize=690, stretch="always")
        split.add(detail_frame, minsize=280, stretch="always")

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings", selectmode="browse")
        headers = {"pos":"#",
            "song":"Canción",
            "artist":"Artista",
            "genre":"Género",
            "country":"País",
            "emotion":"Emoción",
            "level":"Nivel",
            "year":"Año",
            "duration":"Duración",
            "source":"Origen"}
        widths = {"pos":44,
            "song":160,
            "artist":130,
            "genre":150,
            "country":90,
            "emotion":70,
            "level":76,
            "year":52,
            "duration":62,
            "source":118}
        for c in self.COLUMNS:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c,
                width=widths[c],
                anchor="center" if c in {"pos", "emotion", "level", "year", "duration"} else "w",
                stretch=c in {"song", "artist", "genre"})
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        self.status = tk.Label(table_frame,
            text="",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            anchor="w",
            font=("Segoe UI", 8))
        self.status.grid(row=2, column=0, sticky="ew", padx=8, pady=6)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._load_selection)
        self.tree.bind("<Double-1>", lambda e:self.edit_song())
        self.tree.bind("<ButtonPress-1>", self._drag_start, add="+")
        self.tree.bind("<B1-Motion>", self._drag_motion, add="+")
        self.tree.bind("<ButtonRelease-1>", self._drag_end, add="+")
        self._build_detail(detail_frame)
        self.refresh()

    def _filter_field(self, parent, label, var, col, entry=False, values=None, editable=True):
        tk.Label(parent,
            text=label.upper(),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 7, "bold")).grid(row=0,
            column=col,
            sticky="w",
            padx=7,
            pady=(8, 3))
        if entry:
            w = tk.Entry(parent,
                textvariable=var,
                bg=COLORS["panel2"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLORS["line_soft"])
        else:
            w = ttk.Combobox(parent,
                textvariable=var,
                values=values or [],
                state="normal" if editable else "readonly")
        w.grid(row=1, column=col, sticky="ew", padx=7, pady=(0, 9))
        return w

    def _build_detail(self, p):
        tk.Label(p,
            text="DETALLE DE LA FILA",
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=16,
            pady=(15, 4))
        tk.Label(p,
            text="Seleccioná una canción. Doble clic para editar.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8)).pack(anchor="w",
            padx=16,
            pady=(0, 12))
        self.detail_title = tk.Label(p,
            text="Sin selección",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            justify="left",
            wraplength=330,
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground=COLORS["line_soft"])
        self.detail_title.pack(fill="x", padx=16)
        self.detail_meta = tk.Label(p,
            text="",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 9),
            anchor="nw",
            justify="left",
            wraplength=330)
        self.detail_meta.pack(fill="x", padx=16, pady=12)
        tk.Label(p,
            text="DESCRIPCIÓN",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).pack(anchor="w",
            padx=16)
        self.detail_desc = tk.Text(p,
            height=10,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            relief="flat",
            wrap="word",
            highlightthickness=1,
            highlightbackground=COLORS["line_soft"])
        self.detail_desc.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        self.detail_desc.configure(state="disabled")
        tk.Label(p,
            text="↕ Arrastrá la fila completa. El divisor central también se puede arrastrar para ampliar tabla o detalle.",
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 8),
            wraplength=330,
            justify="left").pack(anchor="w",
            padx=16,
            pady=(0, 14))

    def _schedule_refresh(self, *_):
        if not hasattr(self, "tree"):
            return
        if self._filter_after:
            try:
                self.after_cancel(self._filter_after)
            except Exception:
                pass
        self._filter_after = self.after(140, self.refresh)

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        self._filter_after = None
        selected = self.selected_id
        rows = self.db.songs(self.search_var.get(),
            self.source_var.get(),
            self.emotion_var.get(),
            self.level_var.get(),
            self.genre_var.get(),
            self.country_var.get(),
            self.year_var.get())
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("",
                "end",
                iid=str(r["id"]),
                values=(r["position"],
                    r["song"],
                    r["artist"],
                    r["genre"],
                    r["country"],
                    r["emotion_type"],
                    r["emotion_level"],
                    r["year"],
                    r["duration"],
                    r["source_sheet"]))
        self.status.config(text=f"{len(rows)} canciones visibles · géneros V1.3 · filtros automáticos · orden = Tipo emocional + Nivel + Posición")
        if selected and self.tree.exists(str(selected)):
            self.tree.selection_set(str(selected))
            self.tree.focus(str(selected))
            self.tree.see(str(selected))
        elif selected:
            self.selected_id = None
            self._show_detail(None)

    def _load_selection(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_id = int(sel[0])
        self._show_detail(self.db.get_song(self.selected_id))

    def _show_detail(self, row):
        if not row:
            self.detail_title.config(text="Sin selección")
            self.detail_meta.config(text="")
            self.detail_desc.configure(state="normal")
            self.detail_desc.delete("1.0", "end")
            self.detail_desc.configure(state="disabled")
            return
        self.detail_title.config(text=f"#{row['position']} · {row['song']}\n{row['artist']}")
        source = row["genre_source"] if "genre_source" in row.keys() else ""
        confidence = row["genre_confidence"] if "genre_confidence" in row.keys() else 0
        genre_line = f"Género: {row['genre']}"
        if source:
            genre_line += f"\nFuente género: {source}" + (f" · confianza {confidence}%" if confidence else "")
        meta = (f"Emoción: {row['emotion_type']} · {row['emotion_level']}\nOrigen: {row['source_sheet']}\n{genre_line}\nPaís: {row['country']}\nAño: {row['year']} · Duración: {row['duration']}")
        self.detail_meta.config(text=meta)
        self.detail_desc.configure(state="normal")
        self.detail_desc.delete("1.0", "end")
        self.detail_desc.insert("1.0", row["description"] or "")
        self.detail_desc.configure(state="disabled")

    def _editor_defaults(self):
        return {"source_sheet":self.source_var.get() or (self.db.distinct("source_sheet") or SOURCES)[0],
            "genre":self.genre_var.get(),
            "country":self.country_var.get(),
            "year":self.year_var.get(),
            "emotion_type":self.emotion_var.get() or "Positiva",
            "emotion_level":self.level_var.get() or "Principal"}

    def new_song(self):
        dlg = SongEditorDialog(self, self.db, defaults=self._editor_defaults())
        self.wait_window(dlg)
        if dlg.result:
            sid = self.db.save_song(dlg.result)
            self.clear_filters(silent=True)
            self.select_song(sid)

    def edit_song(self):
        if not self.selected_id:
            messagebox.showinfo("Editar", "Seleccioná una fila primero.", parent=self)
            return
        row = self.db.get_song(self.selected_id)
        dlg = SongEditorDialog(self, self.db, row=row)
        self.wait_window(dlg)
        if dlg.result:
            self.db.save_song(dlg.result, self.selected_id)
            self.refresh()
            self.select_song(self.selected_id)

    def delete_song(self):
        if not self.selected_id:
            messagebox.showinfo("Eliminar", "Seleccioná una fila primero.", parent=self)
            return
        row = self.db.get_song(self.selected_id)
        if messagebox.askyesno("Eliminar canción",
            f"¿Eliminar '{row['song']}' de la biblioteca?\n\nTambién se quitará de programadores donde esté usada.",
            parent=self):
            self.db.delete_song(self.selected_id)
            self.selected_id = None
            self._show_detail(None)
            self.refresh()

    def _visible_same_group_ids(self):
        if not self.selected_id:
            return []
        row = self.db.get_song(self.selected_id)
        if not row:
            return []
        ids = []
        for iid in self.tree.get_children():
            try:
                sid = int(iid)
            except Exception:
                continue
            rr = self.db.get_song(sid)
            if rr and (rr["emotion_type"],
                rr["emotion_level"]) == (row["emotion_type"],
                row["emotion_level"]):
                ids.append(sid)
        return ids

    def move_delta(self, delta):
        if not self.selected_id:
            return
        ids = self._visible_same_group_ids()
        if self.selected_id not in ids:
            return
        idx = ids.index(self.selected_id)
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(ids):
            return
        target_id = ids[new_idx]
        self.db.move_song_relative(self.selected_id, target_id, before=(delta < 0))
        self.refresh()
        self.select_song(self.selected_id, preserve_filters=True)

    def move_to(self):
        if not self.selected_id:
            messagebox.showinfo("Mover", "Seleccioná una fila primero.", parent=self)
            return
        ids = self._visible_same_group_ids()
        if self.selected_id not in ids or not ids:
            return
        pos = simpledialog.askinteger(
            "Mover fila completa",
            f"Nueva posición VISIBLE dentro del grupo filtrado (1–{len(ids)}):",
            minvalue=1, maxvalue=len(ids), parent=self
        )
        if not pos:
            return
        rest = [sid for sid in ids if sid!=self.selected_id]
        if not rest:
            return
        insert_idx = max(0, min(len(rest), pos-1))
        if insert_idx>=len(rest):
            self.db.move_song_relative(self.selected_id, rest[-1], before=False)
        else:
            self.db.move_song_relative(self.selected_id, rest[insert_idx], before=True)
        self.refresh()
        self.select_song(self.selected_id, preserve_filters=True)

    def change_level(self):
        if not self.selected_id:
            messagebox.showinfo("Cambiar nivel", "Seleccioná una canción primero.", parent=self)
            return
        row = self.db.get_song(self.selected_id)
        target = "Principal" if row["emotion_level"] == "Secundaria" else "Secundaria"
        dlg = LevelTransferDialog(self, self.db, row, target)
        self.wait_window(dlg)
        if dlg.result:
            self.db.move_song_to_level_by_origin(self.selected_id, target, dlg.result)
            # Mantiene la canción visible aunque el filtro de nivel actual la excluya.
            self.level_var.set(target)
            self.refresh()
            self.select_song(self.selected_id, preserve_filters=True)

    def research_selected_genre(self):
        if not self.selected_id:
            messagebox.showinfo("Investigar género", "Seleccioná una canción primero.", parent=self)
            return
        row = self.db.get_song(self.selected_id)
        GenreResearchDialog(self, self.db, [dict(row)], on_done=self.refresh)

    def research_all_genres(self):
        rows = [dict(r) for r in self.db.songs(limit=10000)]
        if not rows:
            return
        if not messagebox.askyesno("Investigar biblioteca",
            f"Se consultarán {len(rows)} registros en MusicBrainz.\n\nEl servicio público exige como máximo una petición por segundo y cada canción puede requerir más de una consulta, por lo que el proceso puede tardar varios minutos.\n\nSólo se reemplaza el género cuando la coincidencia tiene confianza suficiente. ¿Continuar?",
            parent=self):
            return
        GenreResearchDialog(self, self.db, rows, on_done=self.refresh)

    def _drag_start(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            self._drag_id = None
            return
        self._drag_id = iid
        self._drag_target = None
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.selected_id = int(iid)
        self._show_detail(self.db.get_song(self.selected_id))

    def _drag_motion(self, event):
        if not self._drag_id:
            return
        target = self.tree.identify_row(event.y)
        if not target or target==self._drag_id:
            return
        src = self.db.get_song(int(self._drag_id))
        dst = self.db.get_song(int(target))
        if not src or not dst or (src["emotion_type"],
            src["emotion_level"])!=(dst["emotion_type"],
            dst["emotion_level"]):
            self.status.config(text="Para reordenar, origen y destino deben pertenecer al mismo Tipo emocional + Nivel.")
            self._drag_target = None
            return
        bbox = self.tree.bbox(target)
        before = True if not bbox else event.y<bbox[1]+bbox[3]/2
        self._drag_target = target
        self._drag_before = before
        target_index = self.tree.index(target)+(0 if before else 1)
        try:
            self.tree.move(self._drag_id, "", target_index)
        except Exception:
            pass
        self.status.config(text=f"Soltá para mover #{src['position']} {'antes' if before else 'después'} de #{dst['position']} · {dst['song']}")

    def _drag_end(self, event):
        if self._drag_id and self._drag_target:
            sid = int(self._drag_id)
            tid = int(self._drag_target)
            if self.db.move_song_relative(sid, tid, self._drag_before):
                self.selected_id = sid
        self._drag_id = None
        self._drag_target = None
        self.refresh()
        if self.selected_id and self.tree.exists(str(self.selected_id)):
            self.tree.selection_set(str(self.selected_id))
            self.tree.focus(str(self.selected_id))
            self.tree.see(str(self.selected_id))
            self._load_selection()

    def clear_filters(self, silent=False):
        for v in [self.search_var,
            self.source_var,
            self.emotion_var,
            self.level_var,
            self.genre_var,
            self.country_var,
            self.year_var]:
            v.set("")
        if not silent:
            self.refresh()

    def select_song(self, song_id, preserve_filters=False):
        if not preserve_filters:
            for v in [self.search_var,
                self.source_var,
                self.emotion_var,
                self.level_var,
                self.genre_var,
                self.country_var,
                self.year_var]:
                v.set("")
        self.selected_id = song_id
        self.refresh()
        if self.tree.exists(str(song_id)):
            self.tree.selection_set(str(song_id))
            self.tree.focus(str(song_id))
            self.tree.see(str(song_id))
            self._load_selection()


class GenreResearchDialog(tk.Toplevel):

    def __init__(self, master, db:Database, rows:list[dict], on_done=None):
        super().__init__(master)
        self.db = db
        self.rows = rows
        self.on_done = on_done
        self.cancel_event = threading.Event()
        self.changed = 0
        self.done_count = 0
        self.title("Investigación de género · MusicBrainz")
        self.geometry("650x270")
        self.resizable(True, False)
        self.configure(bg=COLORS["bg"])
        self.transient(master.winfo_toplevel())
        panel = tk.Frame(self, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        panel.pack(fill="both", expand=True, padx=14, pady=14)
        tk.Label(panel,
            text="INVESTIGADOR DE GÉNEROS",
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=16,
            pady=(14, 3))
        self.label = tk.Label(panel,
            text="Preparando…",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=590)
        self.label.pack(fill="x", padx=16, pady=(3, 10))
        self.progress = ttk.Progressbar(panel, maximum=max(1, len(rows)), value=0)
        self.progress.pack(fill="x", padx=16, pady=8)
        self.status = tk.Label(panel,
            text="No se deduce el género desde la carpeta de origen.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8))
        self.status.pack(anchor="w", padx=16, pady=(2, 8))
        foot = tk.Frame(panel, bg=COLORS["panel"])
        foot.pack(fill="x", padx=16, pady=(0, 14))
        StyledButton(foot, "Cancelar", self.cancel, danger=True).pack(side="right")
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        threading.Thread(target=self._worker, daemon=True).start()

    def cancel(self):
        self.cancel_event.set()
        self.status.config(text="Cancelando al terminar la consulta actual…")

    def _worker(self):
        for i, row in enumerate(self.rows, 1):
            if self.cancel_event.is_set():
                break
            artist = row.get("artist", "")
            song = row.get("song", "")
            self.after(0,
                lambda i=i,
                a=artist,
                s=song:self.label.config(text=f"{i}/{len(self.rows)} · {a} — {s}"))
            try:
                result = MusicBrainzGenreClient.research_track(artist, song)
            except Exception as exc:
                result = {"genre":"",
                    "source":f"Error MusicBrainz: {exc}",
                    "confidence":0,
                    "recording_id":"",
                    "artist_id":""}
            self.after(0, lambda sid=row["id"], r=result, i=i:self._apply(sid, r, i))
        self.after(0, self._finish)

    def _apply(self, sid, result, i):
        try:
            if self.db.update_song_genre_research(sid, result):
                self.changed+=1
        except Exception as exc:
            self.status.config(text=f"No se pudo guardar un resultado: {exc}")
        self.done_count = i
        self.progress["value"] = i
        g = result.get("genre") or "sin género verificable"
        self.status.config(text=f"Resultado: {g} · fuente: {result.get('source','')} · confianza {result.get('confidence',0)}%")

    def _finish(self):
        if self.winfo_exists():
            self.status.config(text=f"Finalizado: {self.done_count} revisados · {self.changed} géneros actualizados." + (" Proceso cancelado." if self.cancel_event.is_set() else ""))
            if self.on_done:
                try:
                    self.on_done()
                except Exception:
                    pass
            self.after(2200, self.destroy)


class LevelTransferDialog(tk.Toplevel):
    """Selector de destino por ORIGEN para Principal ↔ Secundaria.

    V1.3.3 aplica exactamente la misma lógica en Positiva, Neutra y Negativa,
    en ambos sentidos. El origen se compara de forma exacta y la inserción se
    expresa mediante el ID de una canción de referencia, evitando depender de
    números globales que pueden cambiar al renumerar la base.
    """

    def __init__(self, master, db: Database, row, target_level: str):
        super().__init__(master)
        self.db = db
        self.row = row
        self.target_level = target_level
        self.result = None
        self.source = (row["source_sheet"] or "").strip()
        self.all_target_rows = []
        self.visible_rows = []
        self.local_index = {}
        self.selected_reference_id = None
        self.search_var = tk.StringVar()
        self.title(f"Mover a {target_level} · {self.source or 'sin origen'}")
        self.geometry("1040x700")
        self.minsize(820, 560)
        self.configure(bg=COLORS["bg"])
        self.transient(master)
        self.grab_set()
        self._build()

    def _emotion_color(self):
        return {
            "Positiva": COLORS["positive"],
            "Neutra": COLORS["neutral"],
            "Negativa": COLORS["negative"],
        }.get(self.row["emotion_type"], COLORS["accent"])

    def _build(self):
        outer = tk.Frame(self, bg=COLORS["bg"], padx=20, pady=18)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer, text="CAMBIAR NIVEL · MISMA EMOCIÓN · MISMO ORIGEN",
            bg=COLORS["bg"], fg=COLORS["accent_hover"],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        tk.Label(
            outer, text=f"{self.row['song']} · {self.row['artist']}",
            bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI", 16, "bold"),
            wraplength=980, justify="left"
        ).pack(anchor="w", pady=(5, 3))

        origin_pos = self.db.origin_position(int(self.row["id"])) or "—"
        tk.Label(
            outer,
            text=(f"{self.row['emotion_type']} · {self.row['emotion_level']} · "
                  f"Origen #{origin_pos} / Global #{self.row['position']}  →  {self.target_level}"),
            bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 10))

        info = tk.Frame(
            outer, bg=COLORS["panel"], highlightthickness=1,
            highlightbackground=COLORS["line"]
        )
        info.pack(fill="x", pady=(0, 10))
        tk.Frame(info, bg=self._emotion_color(), width=7).pack(side="left", fill="y")
        info_text = tk.Frame(info, bg=COLORS["panel"])
        info_text.pack(side="left", fill="both", expand=True, padx=12, pady=9)
        tk.Label(
            info_text,
            text=f"{self.row['emotion_type']} · {self.target_level} · ORIGEN: {self.source or '(sin origen)'}",
            bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        tk.Label(
            info_text,
            text=("La lista de destino está aislada por tres claves: emoción + nivel + origen exacto. "
                  "No puede mostrar canciones de otra colección. Elegí una canción y colocá la fila "
                  "antes o después; el programa renumera automáticamente ambas listas."),
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9),
            wraplength=930, justify="left"
        ).pack(anchor="w", pady=(3, 0))

        search = tk.Frame(outer, bg=COLORS["panel"], highlightthickness=1,
                          highlightbackground=COLORS["line"])
        search.pack(fill="x", pady=(0, 10))
        tk.Label(search, text="BUSCAR DENTRO DE ESTE ORIGEN", bg=COLORS["panel"],
                 fg=COLORS["muted"], font=("Segoe UI", 8, "bold")).pack(side="left", padx=(12, 8), pady=9)
        entry = tk.Entry(search, textvariable=self.search_var, bg=COLORS["panel2"],
                         fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat",
                         highlightthickness=1, highlightbackground=COLORS["line_soft"])
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8, ipady=5)
        StyledButton(search,
            "Limpiar",
            lambda: self.search_var.set("")).pack(side="right",
            padx=(0, 8),
            pady=7)
        self.search_var.trace_add("write", lambda *_: self._refresh_tree())

        table = tk.Frame(
            outer, bg=COLORS["panel"], highlightthickness=1,
            highlightbackground=COLORS["line"]
        )
        table.pack(fill="both", expand=True)
        self.table_title = tk.Label(
            table, text="", bg=COLORS["panel"], fg=COLORS["accent_hover"],
            font=("Segoe UI", 9, "bold")
        )
        self.table_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(9, 6))

        cols = ("local", "global", "song", "artist", "genre", "year", "duration")
        self.tree = ttk.Treeview(table, columns=cols, show="headings", selectmode="browse", height=13)
        headings = {
            "local": "Origen #", "global": "Global #", "song": "Canción",
            "artist": "Artista", "genre": "Género", "year": "Año", "duration": "Duración"
        }
        widths = {
            "local": 72, "global": 72, "song": 290, "artist": 210,
            "genre": 210, "year": 60, "duration": 75
        }
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c,
                width=widths[c],
                anchor="center" if c in {"local", "global", "year", "duration"} else "w",
                             stretch=c in {"song", "artist", "genre"})
        vs = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 0))
        vs.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(0, 0))
        hs.grid(row=2, column=0, sticky="ew", padx=(10, 0), pady=(0, 10))
        table.grid_rowconfigure(1, weight=1)
        table.grid_columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._pick_row)
        self.tree.bind("<Double-1>", self._double_click)

        controls = tk.Frame(
            outer, bg=COLORS["panel"], highlightthickness=1,
            highlightbackground=COLORS["line"]
        )
        controls.pack(fill="x", pady=(10, 0))
        self.choice_label = tk.Label(
            controls, text="Seleccioná una canción del mismo origen para decidir dónde insertar.",
            bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9),
            anchor="w", justify="left"
        )
        self.choice_label.pack(fill="x", padx=12, pady=(10, 4))

        buttons = tk.Frame(controls, bg=COLORS["panel"])
        buttons.pack(fill="x", padx=8, pady=(2, 8))
        self.before_btn = StyledButton(buttons, "Insertar ANTES", self._insert_before, accent=True)
        self.before_btn.pack(side="left", padx=4, pady=4)
        self.after_btn = StyledButton(buttons, "Insertar DESPUÉS", self._insert_after)
        self.after_btn.pack(side="left", padx=4, pady=4)
        StyledButton(buttons, "Primera del origen", self._first_of_source).pack(side="left", padx=4, pady=4)
        StyledButton(buttons, "Última del origen", self._last_of_source).pack(side="left", padx=4, pady=4)
        StyledButton(buttons, "Cancelar", self.destroy).pack(side="right", padx=4, pady=4)

        self._load_target_rows()
        self._refresh_tree()
        entry.focus_set()

    def _load_target_rows(self):
        # Consulta exacta: no usa LIKE ni coincidencia parcial para el origen.
        self.all_target_rows = list(self.db.origin_rows(
            self.row["emotion_type"], self.target_level, self.source
        ))
        self.local_index = {int(r["id"]): i for i, r in enumerate(self.all_target_rows, 1)}

    def _refresh_tree(self):
        if not hasattr(self, "tree"):
            return
        q = (self.search_var.get() or "").strip().casefold()
        self.tree.delete(*self.tree.get_children())
        if q:
            self.visible_rows = [
                r for r in self.all_target_rows
                if q in (r["song"] or "").casefold()
                or q in (r["artist"] or "").casefold()
                or q in (r["genre"] or "").casefold()
                or q in (r["year"] or "").casefold()
            ]
        else:
            self.visible_rows = list(self.all_target_rows)

        total_global = self.db.count_group(self.row["emotion_type"], self.target_level)
        self.table_title.config(
            text=(f"DESTINO REAL · {self.row['emotion_type']} / {self.target_level} / "
                  f"{self.source or '(sin origen)'} · {len(self.all_target_rows)} del origen · "
                  f"{total_global} totales en el nivel")
        )
        for r in self.visible_rows:
            sid = int(r["id"])
            self.tree.insert(
                "", "end", iid=str(sid),
                values=(self.local_index.get(sid, "—"), r["position"], r["song"], r["artist"],
                        r["genre"], r["year"], r["duration"])
            )

        self.selected_reference_id = None
        if not self.all_target_rows:
            self.choice_label.config(
                text=(f"Todavía no hay canciones en {self.row['emotion_type']} / {self.target_level} "
                      f"para el origen '{self.source}'. Usá 'Primera del origen' o 'Última del origen'.")
            )
            self.before_btn.config(state="disabled")
            self.after_btn.config(state="disabled")
        else:
            self.before_btn.config(state="normal")
            self.after_btn.config(state="normal")
            if q and not self.visible_rows:
                self.choice_label.config(text="La búsqueda no encontró canciones dentro de este origen.")
            else:
                self.choice_label.config(text="Seleccioná una canción del mismo origen para decidir dónde insertar.")

    def _pick_row(self, event=None):
        sel = self.tree.selection()
        if not sel:
            self.selected_reference_id = None
            return
        try:
            sid = int(sel[0])
        except Exception:
            return
        if sid not in self.local_index:
            return
        self.selected_reference_id = sid
        vals = self.tree.item(sel[0], "values")
        self.choice_label.config(
            text=(f"Seleccionada: Origen #{vals[0]} · Global #{vals[1]} · {vals[2]} · {vals[3]}. "
                  "Elegí insertar antes o después.")
        )

    def _double_click(self, event=None):
        self._pick_row()
        if self.selected_reference_id is not None:
            self._insert_before()

    def _insert_before(self):
        if self.selected_reference_id is None:
            messagebox.showinfo(
                "Elegir posición", "Seleccioná primero una canción del mismo origen.", parent=self
            )
            return
        self.result = {"mode": "relative", "reference_id": self.selected_reference_id, "before": True}
        self.destroy()

    def _insert_after(self):
        if self.selected_reference_id is None:
            messagebox.showinfo(
                "Elegir posición", "Seleccioná primero una canción del mismo origen.", parent=self
            )
            return
        self.result = {"mode": "relative", "reference_id": self.selected_reference_id, "before": False}
        self.destroy()

    def _first_of_source(self):
        self.result = {"mode": "edge", "edge": "first"}
        self.destroy()

    def _last_of_source(self):
        self.result = {"mode": "edge", "edge": "last"}
        self.destroy()


class EmotionView(BaseView):

    def __init__(self, master, app, emotion):
        color = {"Positiva":COLORS["positive"],
            "Neutra":COLORS["neutral"],
            "Negativa":COLORS["negative"]}[emotion]
        super().__init__(master,
            app,
            f"Emoción {emotion.lower()}",
            "Principal ↔ Secundaria · filtros automáticos por origen, género, país y año.")
        self.emotion = emotion
        self.color = color
        self._filter_after = None
        self._drag_tree = None
        self._drag_id = None
        self._drag_target = None
        self._drag_before = True
        self.hero = tk.Frame(self.body,
            bg=COLORS["panel"],
            height=90,
            highlightthickness=1,
            highlightbackground=COLORS["line"])
        self.hero.pack(fill="x", pady=(0, 8))
        self.hero.pack_propagate(False)
        filters = tk.Frame(self.body,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"])
        filters.pack(fill="x", pady=(0, 8))
        self.search_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.genre_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self._filter_field(filters, "Buscar", self.search_var, 0, entry=True)
        self._filter_field(filters, "Origen", self.source_var, 1, self.db.distinct("source_sheet") or SOURCES)
        self._filter_field(filters, "Género", self.genre_var, 2, self.db.distinct("genre"))
        self._filter_field(filters, "País", self.country_var, 3, self.db.distinct("country"))
        self._filter_field(filters, "Año", self.year_var, 4, self.db.distinct_years())
        StyledButton(filters, "Limpiar", self.clear_filters).grid(row=1, column=5, padx=8, pady=(0, 9))
        for i in range(5):
            filters.grid_columnconfigure(i, weight=1)
        for v in [self.search_var, self.source_var, self.genre_var, self.country_var, self.year_var]:
            v.trace_add("write", self._schedule_refresh)
        actions = tk.Frame(self.body,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"])
        actions.pack(fill="x", pady=(0, 8))
        tk.Label(actions,
            text="FILA SELECCIONADA",
            bg=COLORS["panel"],
            fg=COLORS["accent_hover"],
            font=("Segoe UI", 8, "bold")).pack(side="left",
            padx=12)
        StyledButton(actions, "↑ Subir", lambda:self.move_delta(-1)).pack(side="left", padx=4, pady=7)
        StyledButton(actions, "↓ Bajar", lambda:self.move_delta(1)).pack(side="left", padx=4)
        StyledButton(actions, "Mover a #", self.move_to).pack(side="left", padx=4)
        self.level_button = StyledButton(actions, "→ Pasar de nivel", self.change_level, accent=True)
        self.level_button.pack(side="left", padx=4)
        StyledButton(actions, "Editar", self.edit_selected).pack(side="left", padx=4)
        StyledButton(actions, "Eliminar", self.delete_selected, danger=True).pack(side="left", padx=4)
        tk.Label(actions,
            text="Arrastrá una fila completa para reordenarla.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8)).pack(side="right",
            padx=12)
        self.nb = ttk.Notebook(self.body)
        self.nb.pack(fill="both", expand=True)
        self.trees = {}
        for level in LEVELS:
            f = tk.Frame(self.nb, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
            self.nb.add(f, text=level)
            cols = ("pos", "song", "artist", "genre", "country", "year", "duration", "source", "description")
            tree = ttk.Treeview(f, columns=cols, show="headings", selectmode="browse")
            labels = {"pos":"#",
                "song":"Canción",
                "artist":"Artista",
                "genre":"Género",
                "country":"País",
                "year":"Año",
                "duration":"Duración",
                "source":"Origen",
                "description":"Descripción / función"}
            widths = {"pos":48,
                "song":200,
                "artist":165,
                "genre":190,
                "country":110,
                "year":58,
                "duration":72,
                "source":155,
                "description":330}
            for c in cols:
                tree.heading(c, text=labels[c])
                tree.column(c, width=widths[c], stretch=c in {"song", "artist", "description", "genre"})
            vs = ttk.Scrollbar(f, orient="vertical", command=tree.yview)
            hs = ttk.Scrollbar(f, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
            tree.grid(row=0, column=0, sticky="nsew")
            vs.grid(row=0, column=1, sticky="ns")
            hs.grid(row=1, column=0, sticky="ew")
            f.grid_rowconfigure(0, weight=1)
            f.grid_columnconfigure(0, weight=1)
            tree.bind("<Double-1>", lambda e, t=tree:self.edit_selected(t))
            tree.bind("<ButtonPress-1>", lambda e, t=tree:self._drag_start(e, t), add="+")
            tree.bind("<B1-Motion>", lambda e, t=tree:self._drag_motion(e, t), add="+")
            tree.bind("<ButtonRelease-1>", lambda e, t=tree:self._drag_end(e, t), add="+")
            self.trees[level] = tree
        self.nb.bind("<<NotebookTabChanged>>", self._tab_changed)
        self.after(30, self._update_level_button)
        self.refresh()

    def _tab_changed(self, event=None):
        self.after(20, self._update_level_button)
        self.after(20, self.refresh)

    def _update_level_button(self):
        if not hasattr(self, "level_button") or not hasattr(self, "nb"):
            return
        try:
            level, _ = self._active_level_tree()
        except Exception:
            return
        target = "Principal" if level == "Secundaria" else "Secundaria"
        self.level_button.config(text=f"→ Pasar a {target}")

    def change_level(self):
        sid, tree = self._selected()
        if not sid:
            messagebox.showinfo("Cambiar nivel", "Seleccioná una fila primero.", parent=self)
            return
        row = self.db.get_song(sid)
        target = "Principal" if row["emotion_level"] == "Secundaria" else "Secundaria"
        dlg = LevelTransferDialog(self, self.db, row, target)
        self.wait_window(dlg)
        if not dlg.result:
            return
        self.db.move_song_to_level_by_origin(sid, target, dlg.result)
        # Abre automáticamente la pestaña destino y conserva la selección.
        self.nb.select(LEVELS.index(target))
        self.refresh()
        target_tree = self.trees[target]
        if target_tree.exists(str(sid)):
            target_tree.selection_set(str(sid))
            target_tree.focus(str(sid))
            target_tree.see(str(sid))
        self._update_level_button()

    def _filter_field(self, parent, label, var, col, values=None, entry=False):
        tk.Label(parent,
            text=label.upper(),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 7, "bold")).grid(row=0,
            column=col,
            sticky="w",
            padx=7,
            pady=(8, 3))
        if entry:
            w = tk.Entry(parent,
                textvariable=var,
                bg=COLORS["panel2"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLORS["line_soft"])
        else:
            w = ttk.Combobox(parent, textvariable=var, values=values or [], state="normal")
        w.grid(row=1, column=col, sticky="ew", padx=7, pady=(0, 9))
        return w

    def _schedule_refresh(self, *_):
        if self._filter_after:
            try:
                self.after_cancel(self._filter_after)
            except Exception:
                pass
        self._filter_after = self.after(140, self.refresh)

    def clear_filters(self):
        self.search_var.set("")
        self.source_var.set("")
        self.genre_var.set("")
        self.country_var.set("")
        self.year_var.set("")
        self.refresh()

    def refresh(self):
        self._filter_after = None
        key = {"Positiva":"general_positive",
            "Neutra":"general_neutral",
            "Negativa":"general_negative"}[self.emotion]
        for w in self.hero.winfo_children():
            w.destroy()
        tk.Frame(self.hero, bg=self.color, width=8).pack(side="left", fill="y")
        text = tk.Frame(self.hero, bg=COLORS["panel"])
        text.pack(side="left", fill="both", expand=True, padx=16)
        tk.Label(text,
            text=f"EMOCIÓN GENERAL · {self.db.setting(key,'')}",
            bg=COLORS["panel"],
            fg=self.color,
            font=("Segoe UI", 13, "bold")).pack(anchor="w",
            pady=(15, 3))
        counts = [f"{lv}: {self.db.count_group(self.emotion,lv)}" for lv in LEVELS]
        tk.Label(text,
            text="  ·  ".join(counts),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9)).pack(anchor="w")
        for level, tree in self.trees.items():
            selected = tree.selection()
            selected = selected[0] if selected else None
            tree.delete(*tree.get_children())
            rows = self.db.emotion_rows(self.emotion,
                level,
                self.search_var.get(),
                self.source_var.get(),
                self.genre_var.get(),
                self.country_var.get(),
                self.year_var.get())
            for r in rows:
                tree.insert("",
                    "end",
                    iid=str(r["id"]),
                    values=(r["position"],
                        r["song"],
                        r["artist"],
                        r["genre"],
                        r["country"],
                        r["year"],
                        r["duration"],
                        r["source_sheet"],
                        r["description"]))
            if selected and tree.exists(selected):
                tree.selection_set(selected)
                tree.focus(selected)
                tree.see(selected)

    def _active_level_tree(self):
        idx = self.nb.index(self.nb.select())
        level = LEVELS[idx]
        return level, self.trees[level]

    def _selected(self, tree=None):
        if tree is None:
            _, tree = self._active_level_tree()
        sel = tree.selection()
        return (int(sel[0]), tree) if sel else (None, tree)

    def move_delta(self, delta):
        sid, tree = self._selected()
        if not sid:
            return
        ids = [int(i) for i in tree.get_children()]
        if sid not in ids:
            return
        idx = ids.index(sid)
        new_idx = idx+delta
        if new_idx<0 or new_idx>=len(ids):
            return
        target_id = ids[new_idx]
        self.db.move_song_relative(sid, target_id, before=(delta<0))
        self.refresh()
        if tree.exists(str(sid)):
            tree.selection_set(str(sid))
            tree.focus(str(sid))
            tree.see(str(sid))

    def move_to(self):
        sid, tree = self._selected()
        if not sid:
            messagebox.showinfo("Mover", "Seleccioná una fila primero.", parent=self)
            return
        ids = [int(i) for i in tree.get_children()]
        if sid not in ids or not ids:
            return
        pos = simpledialog.askinteger(
            "Mover fila completa",
            f"Nueva posición VISIBLE con los filtros actuales (1–{len(ids)}):",
            minvalue=1, maxvalue=len(ids), parent=self
        )
        if not pos:
            return
        rest = [x for x in ids if x!=sid]
        if not rest:
            return
        insert_idx = max(0, min(len(rest), pos-1))
        if insert_idx>=len(rest):
            self.db.move_song_relative(sid, rest[-1], before=False)
        else:
            self.db.move_song_relative(sid, rest[insert_idx], before=True)
        self.refresh()
        if tree.exists(str(sid)):
            tree.selection_set(str(sid))
            tree.focus(str(sid))
            tree.see(str(sid))

    def edit_selected(self, tree=None):
        sid, tree = self._selected(tree)
        if not sid:
            messagebox.showinfo("Editar", "Seleccioná una fila primero.", parent=self)
            return
        row = self.db.get_song(sid)
        dlg = SongEditorDialog(self, self.db, row=row)
        self.wait_window(dlg)
        if dlg.result:
            self.db.save_song(dlg.result, sid)
            self.refresh()

    def delete_selected(self):
        sid, tree = self._selected()
        if not sid:
            messagebox.showinfo("Eliminar", "Seleccioná una fila primero.", parent=self)
            return
        row = self.db.get_song(sid)
        if messagebox.askyesno("Eliminar canción", f"¿Eliminar '{row['song']}'?", parent=self):
            self.db.delete_song(sid)
            self.refresh()

    def _drag_start(self, event, tree):
        iid = tree.identify_row(event.y)
        if not iid:
            self._drag_id = None
            return
        self._drag_tree = tree
        self._drag_id = iid
        self._drag_target = None
        tree.selection_set(iid)
        tree.focus(iid)

    def _drag_motion(self, event, tree):
        if tree is not self._drag_tree or not self._drag_id:
            return
        target = tree.identify_row(event.y)
        if not target or target==self._drag_id:
            return
        bbox = tree.bbox(target)
        before = True if not bbox else event.y<bbox[1]+bbox[3]/2
        self._drag_target = target
        self._drag_before = before
        target_index = tree.index(target)+(0 if before else 1)
        try:
            tree.move(self._drag_id, "", target_index)
        except Exception:
            pass

    def _drag_end(self, event, tree):
        sid = int(self._drag_id) if self._drag_id else None
        if tree is self._drag_tree and self._drag_id and self._drag_target:
            self.db.move_song_relative(int(self._drag_id), int(self._drag_target), self._drag_before)
        self._drag_tree = None
        self._drag_id = None
        self._drag_target = None
        self.refresh()
        if sid and tree.exists(str(sid)):
            tree.selection_set(str(sid))
            tree.focus(str(sid))
            tree.see(str(sid))

class SetlistView(BaseView):

    def __init__(self, master, app):
        super().__init__(master,
            app,
            "Programador de shows",
            "Armá playlists con nombre, filtrá por emoción/origen/género y conservá el orden manual del show.")
        self.current_setlist_id = None
        self._filter_after = None
        top = tk.Frame(self.body, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top,
            text="PLAYLIST / SHOW",
            bg=COLORS["panel"],
            fg=COLORS["accent"],
            font=("Segoe UI", 10, "bold")).pack(side="left",
            padx=12)
        self.setlist_var = tk.StringVar()
        self.setlist_combo = ttk.Combobox(top, textvariable=self.setlist_var, state="readonly", width=35)
        self.setlist_combo.pack(side="left", padx=6, pady=9)
        self.setlist_combo.bind("<<ComboboxSelected>>", lambda e:self._select_setlist())
        StyledButton(top, "+ Nueva playlist", self.new_setlist, accent=True).pack(side="left", padx=4)
        StyledButton(top, "Renombrar", self.rename_setlist).pack(side="left", padx=4)
        StyledButton(top, "Datos del show", self.edit_setlist).pack(side="left", padx=4)
        StyledButton(top, "Duplicar", self.duplicate_setlist).pack(side="left", padx=4)
        StyledButton(top, "Eliminar", self.delete_setlist, danger=True).pack(side="left", padx=4)
        self.summary = tk.Label(top, text="", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9, "bold"))
        self.summary.pack(side="right", padx=10)

        panes = tk.PanedWindow(self.body, orient="horizontal", bg=COLORS["bg"], sashwidth=7)
        panes.pack(fill="both", expand=True)
        left = tk.Frame(panes, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        right = tk.Frame(panes, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        panes.add(left, minsize=480)
        panes.add(right, minsize=650)
        filters = tk.Frame(left, bg=COLORS["panel"])
        filters.pack(fill="x", padx=8, pady=8)
        self.song_search = tk.StringVar()
        self.source_var = tk.StringVar()
        self.emotion_var = tk.StringVar()
        self.genre_var = tk.StringVar()
        self.level_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.sm_var = tk.StringVar(value="Todos")
        self.order_var = tk.StringVar(value="Biblioteca")
        specs = [("BUSCAR", self.song_search, None),
            ("EMOCIÓN", self.emotion_var, [""]+EMOTIONS),
            ("ORIGEN", self.source_var, [""]+self.db.distinct("source_sheet")),
            ("GÉNERO", self.genre_var, [""]+self.db.distinct("genre")),
            ("NIVEL", self.level_var, [""]+LEVELS),
            ("PAÍS", self.country_var, [""]+self.db.distinct("country")),
            ("STARMAKER", self.sm_var, ["Todos", "Disponible", "No encontrado", "Sin investigar"]),
            ("ORDEN", self.order_var, ["Biblioteca", "Mayor popularidad StarMaker"])]
        for i, (label, var, values) in enumerate(specs):
            r = i//2
            c = i%2
            box = tk.Frame(filters, bg=COLORS["panel"])
            box.grid(row=r, column=c, sticky="ew", padx=4, pady=3)
            filters.grid_columnconfigure(c, weight=1)
            tk.Label(box,
                text=label,
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 7, "bold")).pack(anchor="w")
            if values is None:
                w = tk.Entry(box,
                    textvariable=var,
                    bg=COLORS["panel2"],
                    fg=COLORS["text"],
                    insertbackground=COLORS["text"],
                    relief="flat")
            else:
                w = ttk.Combobox(box,
                    textvariable=var,
                    values=values,
                    state="readonly" if label in {"EMOCIÓN", "NIVEL", "STARMAKER"} else "normal")
            w.pack(fill="x", ipady=4 if values is None else 0)
        StyledButton(filters,
            "Limpiar filtros",
            self.clear_filters).grid(row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=4,
            pady=(4, 0))
        for v in [self.song_search,
            self.source_var,
            self.emotion_var,
            self.genre_var,
            self.level_var,
            self.country_var,
            self.sm_var,
            self.order_var]:
            v.trace_add("write", self._schedule_filter)

        treebox = tk.Frame(left, bg=COLORS["panel"])
        treebox.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        cols = ("song", "artist", "emotion", "source", "genre", "duration", "sm")
        self.song_tree = ttk.Treeview(treebox, columns=cols, show="headings", selectmode="browse")
        hdr = {"song":"Canción",
            "artist":"Artista",
            "emotion":"Emoción",
            "source":"Origen",
            "genre":"Género",
            "duration":"Dur.",
            "sm":"StarMaker"}
        widths = {"song":180, "artist":135, "emotion":75, "source":145, "genre":145, "duration":55, "sm":90}
        for c in cols:
            self.song_tree.heading(c, text=hdr[c])
            self.song_tree.column(c, width=widths[c], stretch=c in {"song", "artist", "source", "genre"})
        vs = ttk.Scrollbar(treebox, orient="vertical", command=self.song_tree.yview)
        hs = ttk.Scrollbar(treebox, orient="horizontal", command=self.song_tree.xview)
        self.song_tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.song_tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        treebox.grid_rowconfigure(0, weight=1)
        treebox.grid_columnconfigure(0, weight=1)
        self.song_tree.bind("<Double-1>", lambda e:self.add_selected())
        StyledButton(left,
            "Agregar a la playlist  →",
            self.add_selected,
            accent=True).pack(fill="x",
            padx=8,
            pady=(0, 8))

        tools = tk.Frame(right, bg=COLORS["panel"])
        tools.pack(fill="x", padx=10, pady=10)
        StyledButton(tools, "↑ Subir", lambda:self.move_item(-1)).pack(side="left", padx=3)
        StyledButton(tools, "↓ Bajar", lambda:self.move_item(1)).pack(side="left", padx=3)
        StyledButton(tools, "Mover a…", self.move_item_to).pack(side="left", padx=3)
        StyledButton(tools, "Quitar", self.remove_item, danger=True).pack(side="left", padx=3)
        StyledButton(tools, "Exportar CSV", self.export_setlist).pack(side="right", padx=3)
        box = tk.Frame(right, bg=COLORS["panel"])
        box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        cols = ("pos",
            "song",
            "artist",
            "genre",
            "country",
            "emotion",
            "level",
            "year",
            "duration",
            "source",
            "sm",
            "sm_count",
            "description")
        self.set_tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        hdr = {"pos":"#",
            "song":"Canción",
            "artist":"Artista",
            "genre":"Género",
            "country":"País",
            "emotion":"Emoción",
            "level":"Nivel",
            "year":"Año",
            "duration":"Dur.",
            "source":"Origen",
            "sm":"StarMaker",
            "sm_count":"Grab. SM",
            "description":"Descripción"}
        widths = {"pos":42,
            "song":170,
            "artist":135,
            "genre":135,
            "country":90,
            "emotion":70,
            "level":75,
            "year":50,
            "duration":55,
            "source":130,
            "sm":80,
            "sm_count":80,
            "description":250}
        for c in cols:
            self.set_tree.heading(c, text=hdr[c])
            self.set_tree.column(c, width=widths[c], stretch=c in {"song", "artist", "description"})
        vs = ttk.Scrollbar(box, orient="vertical", command=self.set_tree.yview)
        hs = ttk.Scrollbar(box, orient="horizontal", command=self.set_tree.xview)
        self.set_tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.set_tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

    def _schedule_filter(self, *_):
        if self._filter_after:
            try:
                self.after_cancel(self._filter_after)
            except:
                pass
        self._filter_after = self.after(180, self.refresh_songs)

    def clear_filters(self):
        for v in [self.song_search,
            self.source_var,
            self.emotion_var,
            self.genre_var,
            self.level_var,
            self.country_var]:
            v.set("")
        self.sm_var.set("Todos")
        self.order_var.set("Biblioteca")

    def refresh(self):
        rows = self.db.setlists()
        names = [f"{r['id']} · {r['name']}" for r in rows]
        self.setlist_combo["values"] = names
        if not rows:
            self.current_setlist_id = self.db.create_setlist("Nueva playlist")
            return self.refresh()
        if self.current_setlist_id not in [r['id'] for r in rows]:
            self.current_setlist_id = rows[0]['id']
        current = next(r for r in rows if r['id']==self.current_setlist_id)
        self.setlist_var.set(f"{current['id']} · {current['name']}")
        self.refresh_songs()
        self.refresh_setlist()

    def _select_setlist(self):
        try:
            self.current_setlist_id = int(self.setlist_var.get().split("·", 1)[0].strip())
        except:
            return
        self.refresh_setlist()

    def refresh_songs(self):
        if not hasattr(self, "song_tree"):
            return
        self._filter_after = None
        self.song_tree.delete(*self.song_tree.get_children())
        rows = list(self.db.songs(search=self.song_search.get(),
            source=self.source_var.get(),
            emotion=self.emotion_var.get(),
            level=self.level_var.get(),
            genre=self.genre_var.get(),
            country=self.country_var.get(),
            limit=5000))
        if self.order_var.get()=="Mayor popularidad StarMaker":
            def sm_count(row):
                ts = self.db.starmaker_tracks_for_song(row["id"])
                t = next((x for x in ts if x["is_selected"]), None)
                return t["recordings_count"] if t and t["recordings_count"] is not None else -1
            rows.sort(key=sm_count, reverse=True)
        sm_filter = self.sm_var.get()
        for r in rows:
            tracks = self.db.starmaker_tracks_for_song(r["id"])
            selected = next((x for x in tracks if x["is_selected"]), None)
            status = self.db.con.execute("SELECT status FROM starmaker_song_status WHERE song_id=?",
                (r["id"], )).fetchone()
            st = status[0] if status else ("Disponible" if selected else "Sin investigar")
            if sm_filter=="Disponible" and not selected:
                continue
            if sm_filter=="No encontrado" and st!="No encontrada":
                continue
            if sm_filter=="Sin investigar" and (status or tracks):
                continue
            self.song_tree.insert("",
                "end",
                iid=str(r["id"]),
                values=(r["song"],
                    r["artist"],
                    r["emotion_type"],
                    r["source_sheet"],
                    r["genre"],
                    r["duration"],
                    "Sí" if selected else ("No" if st=="No encontrada" else "—")))

    def refresh_setlist(self):
        if not self.current_setlist_id:
            return
        rows = self.db.setlist_items(self.current_setlist_id)
        self.set_tree.delete(*self.set_tree.get_children())
        seconds = 0
        for r in rows:
            seconds+=r["duration_seconds"] or 0
            tracks = self.db.starmaker_tracks_for_song(r["id"])
            selected = next((x for x in tracks if x["is_selected"]), None)
            self.set_tree.insert("",
                "end",
                iid=str(r["item_id"]),
                values=(r["position"],
                    r["song"],
                    r["artist"],
                    r["genre"],
                    r["country"],
                    r["emotion_type"],
                    r["emotion_level"],
                    r["year"],
                    r["duration"],
                    r["source_sheet"],
                    "Sí" if selected else "—",
                    compact_count(selected["recordings_count"]) if selected else "Sin datos",
                    r["description"]))
        sl = self.db.get_setlist(self.current_setlist_id)
        target = (sl["target_minutes"] if sl else 80)
        status = (sl["status"] if sl else "")
        self.summary.config(text=f"{len(rows)} canciones · {seconds_to_human(seconds)} · objetivo {target} min · {status}")

    def add_selected(self):
        if not self.current_setlist_id:
            return
        sel = self.song_tree.selection()
        if sel:
            self.db.add_to_setlist(self.current_setlist_id, int(sel[0]))
            self.refresh_setlist()

    def remove_item(self):
        sel = self.set_tree.selection()
        if sel:
            self.db.remove_setlist_item(self.current_setlist_id, int(sel[0]))
            self.refresh_setlist()

    def move_item(self, delta):
        sel = self.set_tree.selection()
        if not sel:
            return
        iid = int(sel[0])
        current = int(self.set_tree.item(sel[0], "values")[0])
        self.db.move_setlist_item(self.current_setlist_id, iid, max(1, current+delta))
        self.refresh_setlist()
        self.set_tree.selection_set(str(iid))
        self.set_tree.see(str(iid))

    def move_item_to(self):
        sel = self.set_tree.selection()
        if not sel:
            return
        n = len(self.set_tree.get_children())
        pos = simpledialog.askinteger("Mover fila completa",
            f"Nueva posición (1–{n}):",
            minvalue=1,
            maxvalue=n,
            parent=self)
        if pos:
            iid = int(sel[0])
            self.db.move_setlist_item(self.current_setlist_id, iid, pos)
            self.refresh_setlist()
            self.set_tree.selection_set(str(iid))
            self.set_tree.see(str(iid))

    def new_setlist(self):
        name = simpledialog.askstring("Nueva playlist", "Nombre de la playlist / show:", parent=self)
        if name:
            self.current_setlist_id = self.db.create_setlist(name.strip())
            self.refresh()

    def rename_setlist(self):
        row = self.db.get_setlist(self.current_setlist_id) if self.current_setlist_id else None
        if not row:
            return
        name = simpledialog.askstring("Renombrar playlist",
            "Nuevo nombre:",
            initialvalue=row["name"],
            parent=self)
        if name and name.strip():
            self.db.update_setlist(self.current_setlist_id, name=name.strip())
            self.refresh()

    def duplicate_setlist(self):
        row = self.db.get_setlist(self.current_setlist_id) if self.current_setlist_id else None
        if not row:
            return
        name = simpledialog.askstring("Duplicar playlist",
            "Nombre de la copia:",
            initialvalue=row["name"]+" — copia",
            parent=self)
        if name and name.strip():
            self.current_setlist_id = self.db.duplicate_setlist(self.current_setlist_id, name.strip())
            self.refresh()

    def edit_setlist(self):
        row = self.db.get_setlist(self.current_setlist_id) if self.current_setlist_id else None
        if not row:
            return
        win = tk.Toplevel(self)
        win.title("Datos del show")
        win.configure(bg=COLORS["panel"])
        win.geometry("560x720")
        win.transient(self)
        win.grab_set()
        surface = ScrollSurface(win, min_width=500, min_height=650)
        surface.pack(fill="both", expand=True)
        host = surface.inner
        fields = {}
        specs = [("name", "Nombre del show", row["name"], None),
            ("event_date", "Fecha AAAA-MM-DD", row["event_date"], None),
            ("event_time", "Hora HH:MM", row["event_time"], None),
            ("audience_country", "País / audiencia", row["audience_country"], None),
            ("target_minutes", "Duración objetivo (min)", str(row["target_minutes"]), None),
            ("show_type", "Tipo de show", row["show_type"], ["Normal", "PK", "Dueto", "Evento", "Especial", "Ensayo"]),
            ("platform", "Plataforma", row["platform"], ["StarMaker", "Otra"]),
            ("status", "Estado", row["status"], ["Borrador", "Preparado", "Realizado", "Archivado"]),
            ("starmaker_live_url", "URL Live StarMaker", row["starmaker_live_url"], None),
            ("starmaker_live_id", "Live ID", row["starmaker_live_id"], None),
            ("timezone", "Zona horaria", row["timezone"], None)]
        for key, label, val, choices in specs:
            tk.Label(host,
                text=label,
                bg=COLORS["panel"],
                fg=COLORS["muted"]).pack(anchor="w",
                padx=18,
                pady=(9, 3))
            v = tk.StringVar(value=val)
            w = ttk.Combobox(host,
                textvariable=v,
                values=choices,
                state="readonly") if choices else tk.Entry(host,
                textvariable=v,
                bg=COLORS["panel2"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                relief="flat")
            w.pack(fill="x", padx=18, ipady=5 if not choices else 0)
            fields[key] = v
        tk.Label(host,
            text="Notas",
            bg=COLORS["panel"],
            fg=COLORS["muted"]).pack(anchor="w",
            padx=18,
            pady=(9, 3))
        notes = tk.Text(host,
            height=4,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat")
        notes.pack(fill="x", padx=18)
        notes.insert("1.0", row["notes"])
        tk.Label(host,
            text="Notas de estrategia",
            bg=COLORS["panel"],
            fg=COLORS["muted"]).pack(anchor="w",
            padx=18,
            pady=(9, 3))
        strategy = tk.Text(host,
            height=4,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat")
        strategy.pack(fill="x", padx=18)
        strategy.insert("1.0", row["strategy_notes"])
        def save():
            try:
                target = int(fields["target_minutes"].get() or 80)
            except:
                target = 80
            vals = {k:v.get().strip() for k, v in fields.items()}
            vals["target_minutes"] = target
            vals["notes"] = notes.get("1.0", "end").strip()
            vals["strategy_notes"] = strategy.get("1.0", "end").strip()
            self.db.update_setlist(self.current_setlist_id, **vals)
            win.destroy()
            self.refresh()
        StyledButton(host, "Guardar datos", save, accent=True).pack(pady=16)

    def delete_setlist(self):
        if self.current_setlist_id and messagebox.askyesno("Eliminar playlist",
            "¿Eliminar esta playlist? Las canciones de Biblioteca no se borrarán.",
            parent=self):
            self.db.delete_setlist(self.current_setlist_id)
            self.current_setlist_id = None
            self.refresh()

    def export_setlist(self):
        if not self.current_setlist_id:
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="playlist_show.csv")
        if not path:
            return
        rows = self.db.setlist_items(self.current_setlist_id)
        fields = ["position",
            "song",
            "artist",
            "genre",
            "country",
            "emotion_type",
            "emotion_level",
            "year",
            "duration",
            "source_sheet",
            "description"]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k:r[k] for k in fields})
        messagebox.showinfo("Exportado", f"Playlist exportada:\n{path}")

class CandidateDialog(tk.Toplevel):

    def __init__(self, parent, candidates):
        super().__init__(parent)
        self.result = None
        self.title("Elegir video de YouTube")
        self.geometry("760x360")
        self.configure(bg=COLORS["panel"])
        self.transient(parent)
        self.grab_set()
        tk.Label(self,
            text="Confirmá el video correcto antes de guardar sus vistas",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 12, "bold")).pack(anchor="w",
            padx=16,
            pady=14)
        tree = ttk.Treeview(self, columns=("title", "channel", "id"), show="headings")
        tree.heading("title", text="Título")
        tree.heading("channel", text="Canal")
        tree.heading("id", text="Video ID")
        tree.column("title", width=390)
        tree.column("channel", width=190)
        tree.column("id", width=120)
        tree.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        for i, c in enumerate(candidates):
            tree.insert("", "end", iid=str(i), values=(c["title"], c["channel"], c["video_id"]))
        if candidates:
            tree.selection_set("0")
        def choose():
            sel = tree.selection()
            
            if sel:
                self.result = candidates[int(sel[0])]
            self.destroy()
        StyledButton(self, "Usar este video", choose, accent=True).pack(pady=(0, 14))
        tree.bind("<Double-1>", lambda e:choose())
        self.wait_window()


class StarMakerView(BaseView):
    """StarMaker Direct API workspace introduced in V1.6.0: summary, catalog, trends and playlist analysis."""

    def __init__(self, master, app):
        super().__init__(master,
            app,
            "StarMaker",
            "Direct API: búsqueda JSON, suma de variantes compatibles, ranking, evolución y análisis de playlist.")
        self.selected_song_id = None
        self._catalog_after = None
        self._scan_running = False
        self.nb = ttk.Notebook(self.body)
        self.nb.pack(fill="both", expand=True)
        self.tab_summary = tk.Frame(self.nb, bg=COLORS["bg"])
        self.tab_catalog = tk.Frame(self.nb, bg=COLORS["bg"])
        self.tab_pop = tk.Frame(self.nb, bg=COLORS["bg"])
        self.tab_playlist = tk.Frame(self.nb, bg=COLORS["bg"])
        for tab, title in [(self.tab_summary, "Resumen"),
            (self.tab_catalog, "Catálogo"),
            (self.tab_pop, "Ranking / Evolución"),
            (self.tab_playlist, "Playlist actual")]:
            self.nb.add(tab, text=self.app.tr(title))
        self._build_summary()
        self._build_catalog()
        self._build_popularity()
        self._build_playlist()
        try:
            self.db.sm_interpretive_match()
        except Exception:
            pass
        self.refresh()

    def _build_summary(self):
        self.cards = {}
        wrap = tk.Frame(self.tab_summary, bg=COLORS["bg"])
        wrap.pack(fill="x", padx=10, pady=10)
        labels = [("total", "Biblioteca"),
            ("found", "Encontradas"),
            ("coverage", "Cobertura"),
            ("recordings", "Grabaciones"),
            ("tracks", "Pistas compatibles"),
            ("last_scan", "Última actualización")]
        for i, (key, label) in enumerate(labels):
            card = tk.Frame(wrap, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
            card.grid(row=i//3, column=i%3, sticky="nsew", padx=5, pady=5)
            wrap.grid_columnconfigure(i%3, weight=1)
            tk.Label(card,
                text=self.app.tr(label),
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 8, "bold")).pack(anchor="w",
                padx=14,
                pady=(12, 3))
            v = tk.Label(card,
                text="—",
                bg=COLORS["panel"],
                fg=COLORS["teal"] if key in {"recordings", "coverage"} else COLORS["accent_hover"],
                font=("Segoe UI", 18, "bold"))
            v.pack(anchor="w", padx=14, pady=(0, 12))
            self.cards[key] = v
        tools = tk.Frame(self.tab_summary, bg=COLORS["panel"])
        tools.pack(fill="x", padx=10, pady=6)
        StyledButton(tools,
            "Completar faltantes",
            self.auto_update,
            accent=True).pack(side="left",
            padx=5,
            pady=8)
        StyledButton(tools, "Recalcular coincidencias", self.rebuild_matches).pack(side="left", padx=5)
        self.scan_status = tk.Label(tools,
            text="Listo",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9))
        self.scan_status.pack(side="left", padx=14)
        self.progress = ttk.Progressbar(tools, mode="determinate", maximum=1)
        self.progress.pack(side="right", fill="x", expand=True, padx=8)
        self.top_song = tk.Label(self.tab_summary,
            text="",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=16,
            pady=14)
        self.top_song.pack(fill="x", padx=10, pady=8)
        tk.Message(self.tab_summary,
            text=(
                'Motor Direct API: consulta el endpoint JSON oficial observado en el buscador web de '
                'StarMaker. No usa Google/Bing/Chrome. La evolución de 7/30 días aparece cuando '
                'existen snapshots históricos separados por tiempo.'
            ),
            width=1050,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            padx=16,
            pady=14,
            highlightthickness=1,
            highlightbackground=COLORS["line"]).pack(fill="x",
            padx=10,
            pady=8)

    def _build_catalog(self):
        top = tk.Frame(self.tab_catalog, bg=COLORS["panel"])
        top.pack(fill="x", padx=8, pady=8)
        self.sm_search = tk.StringVar()
        self.sm_emotion = tk.StringVar()
        self.sm_source = tk.StringVar()
        self.sm_genre = tk.StringVar()
        self.sm_avail = tk.StringVar(value="Todos")
        specs = [("Buscar", self.sm_search, None),
            ("Emoción", self.sm_emotion, [""]+EMOTIONS),
            ("Origen", self.sm_source, [""]+self.db.distinct("source_sheet")),
            ("Género", self.sm_genre, [""]+self.db.distinct("genre")),
            ("StarMaker", self.sm_avail, ["Todos", "Sí", "No", "Sin investigar"])]
        for i, (label, var, vals) in enumerate(specs):
            box = tk.Frame(top, bg=COLORS["panel"])
            box.grid(row=0, column=i, sticky="ew", padx=4)
            top.grid_columnconfigure(i, weight=1)
            tk.Label(box,
                text=self.app.tr(label).upper(),
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 7, "bold")).pack(anchor="w")
            w = tk.Entry(box,
                textvariable=var,
                bg=COLORS["panel2"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                relief="flat") if vals is None else ttk.Combobox(box,
                textvariable=var,
                values=vals,
                state="readonly" if label in {"Emoción", "StarMaker"} else "normal")
            w.pack(fill="x", ipady=4 if vals is None else 0)
            var.trace_add("write", self._schedule_catalog)
        actions = tk.Frame(self.tab_catalog, bg=COLORS["panel"])
        actions.pack(fill="x", padx=8, pady=(0, 8))
        StyledButton(actions,
            "Actualizar seleccionada",
            self.search_selected_song,
            accent=True).pack(side="left",
            padx=4,
            pady=7)
        StyledButton(actions, "Completar faltantes", self.auto_update).pack(side="left", padx=4)
        StyledButton(actions,
            "Actualizar playlist actual",
            self.update_current_playlist).pack(side="left",
            padx=4)
        StyledButton(actions, "Recalcular coincidencias", self.rebuild_matches).pack(side="left", padx=4)
        StyledButton(actions, "Sugerir para el show", self.suggest_show).pack(side="right", padx=4)
        box = tk.Frame(self.tab_catalog, bg=COLORS["panel"])
        box.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        cols = ("song",
            "artist",
            "emotion",
            "source",
            "genre",
            "status",
            "tracks",
            "recordings",
            "trend7",
            "trend30",
            "variant",
            "updated",
            "confidence")
        self.cat_tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        hdr = {"song":"Canción",
            "artist":"Artista",
            "emotion":"Emoción",
            "source":"Origen",
            "genre":"Género",
            "status":"StarMaker",
            "tracks":"Pistas",
            "recordings":"Grabaciones",
            "trend7":"7 días",
            "trend30":"30 días",
            "variant":"Pista principal",
            "updated":"Actualizada",
            "confidence":"Conf."}
        widths = {"song":190,
            "artist":150,
            "emotion":75,
            "source":135,
            "genre":125,
            "status":130,
            "tracks":55,
            "recordings":100,
            "trend7":70,
            "trend30":70,
            "variant":150,
            "updated":125,
            "confidence":55}
        for c in cols:
            self.cat_tree.heading(c, text=self.app.tr(hdr[c]))
            self.cat_tree.column(c, width=widths[c], stretch=c in {"song", "artist", "source", "genre"})
        vs = ttk.Scrollbar(box, orient="vertical", command=self.cat_tree.yview)
        hs = ttk.Scrollbar(box, orient="horizontal", command=self.cat_tree.xview)
        self.cat_tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.cat_tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)
        self.cat_tree.bind("<<TreeviewSelect>>", self._cat_select)
        self.cat_tree.bind("<Double-1>", lambda e:self.search_selected_song())

    def _build_popularity(self):
        tools = tk.Frame(self.tab_pop, bg=COLORS["panel"])
        tools.pack(fill="x", padx=8, pady=8)
        self.pop_sort = tk.StringVar(value="Mayor cantidad de grabaciones")
        ttk.Combobox(tools,
            textvariable=self.pop_sort,
            values=["Mayor cantidad de grabaciones", "Mayor crecimiento 7 días", "Mayor crecimiento 30 días", "Sin historial"],
            state="readonly",
            width=30).pack(side="left",
            padx=5)
        self.pop_sort.trace_add("write", lambda *_:self.refresh_popularity())
        StyledButton(tools, "Completar faltantes", self.auto_update, accent=True).pack(side="left", padx=5)
        cols = ("song", "artist", "variant", "current", "d7", "d30", "updated")
        self.pop_tree = ttk.Treeview(self.tab_pop, columns=cols, show="headings")
        for c, txt, w in [("song", "Canción", 210),
            ("artist", "Artista", 165),
            ("variant", "Pista principal", 160),
            ("current", "Grabaciones", 100),
            ("d7", "Tend. 7d", 85),
            ("d30", "Tend. 30d", 90),
            ("updated", "Actualizada", 145)]:
            self.pop_tree.heading(c, text=self.app.tr(txt))
            self.pop_tree.column(c, width=w)
        self.pop_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _build_playlist(self):
        top = tk.Frame(self.tab_playlist, bg=COLORS["panel"])
        top.pack(fill="x", padx=8, pady=8)
        tk.Label(top,
            text="PLAYLIST",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).pack(side="left",
            padx=5)
        self.pl_var = tk.StringVar()
        self.pl_combo = ttk.Combobox(top, textvariable=self.pl_var, state="readonly", width=38)
        self.pl_combo.pack(side="left", padx=5)
        self.pl_combo.bind("<<ComboboxSelected>>", lambda e:self.refresh_playlist_analysis())
        StyledButton(top,
            "Analizar playlist",
            self.refresh_playlist_analysis,
            accent=True).pack(side="left",
            padx=5)
        StyledButton(top, "Actualizar datos", self.update_current_playlist).pack(side="left", padx=5)
        self.pl_summary = tk.Message(self.tab_playlist,
            text="",
            width=1100,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
            padx=14,
            pady=12)
        self.pl_summary.pack(fill="x", padx=8, pady=(0, 8))
        cols = ("pos", "song", "artist", "recordings", "level", "status")
        self.pl_tree = ttk.Treeview(self.tab_playlist, columns=cols, show="headings")
        for c, txt, w in [("pos", "#", 45),
            ("song", "Canción", 240),
            ("artist", "Artista", 180),
            ("recordings", "Grabaciones", 110),
            ("level", "Uso SM", 90),
            ("status", "Estado", 170)]:
            self.pl_tree.heading(c, text=self.app.tr(txt))
            self.pl_tree.column(c, width=w)
        self.pl_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def refresh(self):
        self.refresh_summary()
        self.refresh_catalog()
        self.refresh_popularity()
        self.refresh_playlist_combo()

    def refresh_summary(self):
        d = self.db.intelligence_dashboard()
        self.cards["total"].config(text=str(d["total"]))
        self.cards["found"].config(text=str(d["sm_found"]))
        self.cards["coverage"].config(text=f"{d['sm_coverage']:.1f}%")
        self.cards["recordings"].config(text=compact_count(d["sm_recordings"]))
        self.cards["tracks"].config(text=str(d["sm_tracks"]))
        self.cards["last_scan"].config(text=self.db.setting("starmaker_last_auto_scan", "") or "—")
        top = d["top_sm"][0] if d["top_sm"] else None
        self.top_song.config(text=f"Más utilizada: {top['artist']} — {top['song']} · {compact_count(top['recordings'])} grabaciones compatibles" if top else "Todavía sin datos StarMaker")

    def _schedule_catalog(self, *_):
        if self._catalog_after:
            try:
                self.after_cancel(self._catalog_after)
            except Exception:
                pass
        self._catalog_after = self.after(180, self.refresh_catalog)

    def refresh_catalog(self):
        if not hasattr(self, "cat_tree"):
            return
        self._catalog_after = None
        self.cat_tree.delete(*self.cat_tree.get_children())
        avail = self.sm_avail.get()
        avail = {"Sí":"Sí", "No":"No", "Sin investigar":"Sin investigar"}.get(avail, "Todos")
        for r in self.db.sm_catalog_auto(self.sm_search.get(),
            self.sm_emotion.get(),
            self.sm_source.get(),
            self.sm_genre.get(),
            avail):
            f = lambda x:"—" if x is None else f"{x:+.1f}%"
            self.cat_tree.insert("",
                "end",
                iid=str(r["id"]),
                values=(r["song"],
                    r["artist"],
                    r["emotion_type"],
                    r["source_sheet"],
                    r["genre"],
                    r["sm_status"],
                    r.get("variant_count", 0),
                    compact_count(r["recordings_count"]),
                    f(r["trend7"]),
                    f(r["trend30"]),
                    r["variant"] or "—",
                    r["last_checked_at"] or "—",
                    r["match_confidence"] if r["match_confidence"] is not None else "—"))

    def _cat_select(self, *_):
        sel = self.cat_tree.selection()
        self.selected_song_id = int(sel[0]) if sel else None

    def search_selected_song(self):
        if self._scan_running:
            return messagebox.showinfo("StarMaker", "Hay una búsqueda en curso.")
        if not self.selected_song_id:
            return messagebox.showinfo("StarMaker", "Seleccioná una canción y hacé doble clic.")
        sid = int(self.selected_song_id)
        song = self.db.get_song(sid)
        self._scan_running = True
        self.scan_status.config(text=f"API StarMaker: {song['artist']} — {song['song']}…")
        self.progress.configure(maximum=1, value=0)
        def work():
            bg = None
            errors = []
            try:
                bg = Database(self.db.path)
                entries, artists, diag = StarMakerDirectAPIClient.search(song["artist"],
                    song["song"],
                    timeout=12,
                    second_pass=True)
                if artists:
                    bg.sm_ingest_artists(artists)
                if entries:
                    bg.sm_ingest_entries(entries)
                bg.sm_interpretive_match([sid])
                bg.set_setting("starmaker_last_auto_scan", now_iso())
                agg = bg.sm_song_aggregate(sid)
                rows = [dict(r) for r in agg["rows"]]
            except Exception as exc:
                errors = [str(exc)]
                agg = {"count":0, "total":None}
                rows = []
            finally:
                if bg:
                    try:
                        bg.close()
                    except Exception:
                        pass
            self.after(0, lambda:self._single_done(song, agg, rows, errors))
        threading.Thread(target=work, daemon=True).start()

    def _single_done(self, song, agg, rows, errors):
        self._scan_running = False
        self.progress["value"] = 1
        self.scan_status.config(text="Listo")
        self.refresh()
        win = tk.Toplevel(self)
        win.title(f"StarMaker · {song['song']}")
        win.geometry("980x580")
        win.configure(bg=COLORS["bg"])
        tk.Label(win,
            text=f"{song['song']} — {song['artist']}",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 15, "bold")).pack(anchor="w",
            padx=16,
            pady=(14, 4))
        tk.Label(win,
            text=f"{agg.get('count',0)} pista(s) compatible(s) · Total: {compact_count(agg.get('total'))}",
            bg=COLORS["bg"],
            fg=COLORS["teal"],
            font=("Segoe UI", 10, "bold")).pack(anchor="w",
            padx=16,
            pady=(0, 10))
        tree = ttk.Treeview(win, columns=("title", "artist", "count", "conf"), show="headings")
        
        for c, txt, w in [("title", "Pista StarMaker", 330),
            ("artist", "Artista / uploader", 230),
            ("count", "Grabaciones", 120),
            ("conf", "Conf.", 70)]:
            tree.heading(c, text=txt)
            tree.column(c, width=w)
        for r in rows:
            tree.insert("",
                "end",
                values=(r.get("title", "") or "",
                    r.get("artist", "") or "",
                    compact_count(r.get("recordings_count")),
                    r.get("confidence", 0)))
        tree.pack(fill="both", expand=True, padx=16, pady=8)
        tk.Label(win,
            text=(" | ".join(errors) if errors else "Fuente: StarMaker Direct API"),
            bg=COLORS["bg"],
            fg=COLORS["warning"] if errors else COLORS["muted"]).pack(anchor="w",
            padx=16,
            pady=(0, 12))

    def rebuild_matches(self):
        n = self.db.sm_interpretive_match()
        self.refresh()
        messagebox.showinfo("StarMaker", f"Coincidencias recalculadas: {n}")

    def auto_update(self, silent=False, song_ids=None):
        if self._scan_running:
            return
        self._scan_running = True
        self.progress["value"] = 0
        self.scan_status.config(text="Preparando API StarMaker…")
        def work():
            bg = None
            checked = found = failed = 0
            try:
                bg = Database(self.db.path)
                missing = [dict(r) for r in bg.sm_exact_missing(song_ids)]
                total = max(1, len(missing))
                self.after(0, lambda:self.progress.configure(maximum=total))
                for ix, s in enumerate(missing, 1):
                    checked+=1
                    self.after(0,
                        lambda i=ix,
                        n=s['song'],
                        tt=len(missing):(self.progress.configure(value=i-1),
                            self.scan_status.config(text=f"StarMaker: {n} ({i}/{tt})")))
                    try:
                        rows, artists, _ = StarMakerDirectAPIClient.search(s["artist"],
                            s["song"],
                            timeout=10,
                            second_pass=True)
                        if artists:
                            bg.sm_ingest_artists(artists)
                        if rows:
                            bg.sm_ingest_entries(rows)
                        bg.sm_interpretive_match([s["id"]])
                        bg.set_setting("starmaker_last_auto_scan", now_iso())
                        found+=1 if bg.sm_song_aggregate(s["id"])["count"] else 0
                    except Exception:
                        failed+=1
                    time.sleep(.12)
            finally:
                if bg:
                    try:
                        bg.close()
                    except Exception:
                        pass
            self.after(0, lambda:self._batch_done(checked, found, failed, silent))
        threading.Thread(target=work, daemon=True).start()

    def _batch_done(self, checked, found, failed, silent):
        self._scan_running = False
        self.progress["value"] = self.progress["maximum"]
        self.scan_status.config(text=f"Listo: {checked} consultadas · {found} encontradas · {failed} fallos")
        self.refresh()
        if not silent:
            messagebox.showinfo("StarMaker",
                f"Consulta terminada.\n\nConsultadas: {checked}\nEncontradas: {found}\nFallos: {failed}")

    def update_current_playlist(self):
        sid = self._selected_playlist_id()
        if not sid:
            return messagebox.showinfo("StarMaker", "No hay playlist seleccionada.")
        ids = [r["id"] for r in self.db.setlist_items(sid)]
        self.auto_update(song_ids=ids) if ids else messagebox.showinfo("StarMaker",
            "La playlist no tiene canciones.")

    def refresh_popularity(self):
        if not hasattr(self, "pop_tree"):
            return
        rows = list(self.db.sm_catalog_auto(availability="Sí"))
        mode = self.pop_sort.get()
        if mode=="Mayor crecimiento 7 días":
            rows.sort(key=lambda r:(r["trend7"] is not None, r["trend7"] or -1e99), reverse=True)
        elif mode=="Mayor crecimiento 30 días":
            rows.sort(key=lambda r:(r["trend30"] is not None, r["trend30"] or -1e99), reverse=True)
        elif mode=="Sin historial":
            rows = [r for r in rows if r["trend7"] is None and r["trend30"] is None]
        else:
            rows.sort(key=lambda r:r["recordings_count"] if r["recordings_count"] is not None else -1,
                reverse=True)
        self.pop_tree.delete(*self.pop_tree.get_children())
        f = lambda x:"—" if x is None else f"{x:+.1f}%"
        for r in rows:
            self.pop_tree.insert("",
                "end",
                values=(r["song"],
                    r["artist"],
                    r["variant"] or "—",
                    compact_count(r["recordings_count"]),
                    f(r["trend7"]),
                    f(r["trend30"]),
                    r["last_checked_at"] or "—"))

    def refresh_playlist_combo(self):
        rows = self.db.setlists()
        vals = [f"{r['id']} · {r['name']}" for r in rows]
        self.pl_combo["values"] = vals
        if vals and self.pl_var.get() not in vals:
            self.pl_var.set(vals[0])
        self.refresh_playlist_analysis()

    def _selected_playlist_id(self):
        try:
            return int(self.pl_var.get().split("·", 1)[0].strip()) if self.pl_var.get() else None
        except:
            return None

    def refresh_playlist_analysis(self):
        if not hasattr(self, "pl_tree"):
            return
        self.pl_tree.delete(*self.pl_tree.get_children())
        sid = self._selected_playlist_id()
        if not sid:
            self.pl_summary.config(text="No hay playlist seleccionada.")
            return
        d = self.db.sm_playlist_analysis(sid)
        self.pl_summary.config(text=f"{d['songs']} canciones · {d['found']} con datos StarMaker · {d['missing']} sin datos · {d['high']} uso alto · {d['medium']} medio · {d['low']} bajo · {compact_count(d['total'])} grabaciones compatibles")
        for idx, (it, tr, ch, variants, cnt) in enumerate(d["items"], 1):
            level = "Sin datos" if cnt is None else ("Alto" if cnt>=100000 else "Medio" if cnt>=10000 else "Bajo")
            self.pl_tree.insert("",
                "end",
                values=(idx,
                    it["song"],
                    it["artist"],
                    compact_count(cnt),
                    level,
                    (f"Encontrada · {variants} pista(s)" if variants else "Sin datos")))

    def suggest_show(self):
        rows = self.db.starmaker_show_score_rows(self.sm_emotion.get(),
            self.sm_source.get(),
            self.sm_genre.get())[:30]
        if not rows:
            return messagebox.showinfo("Índice Show", "Sin datos suficientes.")
        win = tk.Toplevel(self)
        win.title("ÍNDICE SHOW · métrica interna")
        win.geometry("980x560")
        win.configure(bg=COLORS["bg"])
        tree = ttk.Treeview(win, columns=("score", "song", "artist", "reason"), show="headings")
        for c, txt, w in [("score", "Índice Show", 90),
            ("song", "Canción", 220),
            ("artist", "Artista", 180),
            ("reason", "Motivo trazable", 450)]:
            tree.heading(c, text=txt)
            tree.column(c, width=w)
        for score, r, reason in rows:
            tree.insert("", "end", values=(score, r["song"], r["artist"], reason))
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(win,
            text="Métrica interna de Playlist Emotion Studio. No es una métrica oficial de StarMaker.",
            bg=COLORS["bg"],
            fg=COLORS["muted"]).pack(pady=(0, 10))


class PlatformsView(BaseView):

    def __init__(self, master, app):
        super().__init__(master,
            app,
            "Plataformas",
            "Datos automáticos y trazables de StarMaker, YouTube Data API y Spotify Web API.")
        self.selected_id = None
        self._busy = False
        panes = tk.PanedWindow(self.body, orient="horizontal", bg=COLORS["bg"], sashwidth=7)
        panes.pack(fill="both", expand=True)
        left = tk.Frame(panes, bg=COLORS["panel"])
        right = tk.Frame(panes, bg=COLORS["panel"])
        panes.add(left, minsize=460)
        panes.add(right, minsize=720)
        self.search = tk.StringVar()
        bar = tk.Frame(left, bg=COLORS["panel"])
        bar.pack(fill="x", padx=10, pady=10)
        tk.Entry(bar,
            textvariable=self.search,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat").pack(side="left",
            fill="x",
            expand=True,
            ipady=6)
        StyledButton(bar, "Buscar", self.refresh).pack(side="left", padx=(6, 0))
        self.search.trace_add("write", lambda *_:self.after(220, self.refresh))
        self.tree = ttk.Treeview(left,
            columns=("song", "artist", "sm", "yt", "sp"),
            show="headings",
            selectmode="browse")
        for c, txt, w in [("song", "Canción", 180),
            ("artist", "Artista", 140),
            ("sm", "StarMaker", 85),
            ("yt", "YouTube", 75),
            ("sp", "Spotify", 75)]:
            self.tree.heading(c, text=self.app.tr(txt))
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.load)
        self.combo = tk.Label(right,
            text="Seleccioná una canción",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 14, "bold"),
            anchor="w",
            padx=16,
            pady=12)
        self.combo.pack(fill="x", padx=10, pady=(10, 6))
        acts = tk.Frame(right, bg=COLORS["panel"])
        acts.pack(fill="x", padx=10, pady=(0, 6))
        StyledButton(acts,
            "Actualizar seleccionada",
            self.update_selected_all,
            accent=True).pack(side="left",
            padx=3)
        StyledButton(acts, "Abrir YouTube", self.open_youtube).pack(side="left", padx=3)
        StyledButton(acts, "Abrir Spotify", self.open_spotify).pack(side="left", padx=3)
        self.status = tk.Label(acts, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8))
        self.status.pack(side="right", padx=6)
        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tab_sm = tk.Frame(self.nb, bg=COLORS["panel"])
        self.tab_yt = tk.Frame(self.nb, bg=COLORS["panel"])
        self.tab_sp = tk.Frame(self.nb, bg=COLORS["panel"])
        self.nb.add(self.tab_sm, text="StarMaker")
        self.nb.add(self.tab_yt, text="YouTube")
        self.nb.add(self.tab_sp, text="Spotify")
        self.fields = {}
        self._build_sm()
        self._build_yt()
        self._build_sp()

    def _field(self, parent, key, label):
        row = tk.Frame(parent, bg=COLORS["panel"])
        row.pack(fill="x", padx=14, pady=5)
        tk.Label(row,
            text=self.app.tr(label),
            width=24,
            anchor="w",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold")).pack(side="left")
        v = tk.StringVar(value="—")
        tk.Label(row,
            textvariable=v,
            anchor="w",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            font=("Segoe UI", 9),
            padx=9,
            pady=6).pack(side="left",
            fill="x",
            expand=True)
        self.fields[key] = v

    def _build_sm(self):
        tk.Label(self.tab_sm,
            text="STARMAKER DIRECT API",
            bg=COLORS["panel"],
            fg=COLORS["accent"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=14,
            pady=(14, 6))
        for k, l in [("sm_status", "Estado"),
            ("sm_tracks", "Pistas"),
            ("sm_recordings", "Grabaciones"),
            ("sm_primary", "Pista principal"),
            ("sm_conf", "Conf."),
            ("sm_updated", "Última actualización")]:
            self._field(self.tab_sm, k, l)
        StyledButton(self.tab_sm,
            "Actualizar StarMaker",
            self.update_starmaker,
            accent=True).pack(anchor="w",
            padx=14,
            pady=12)

    def _build_yt(self):
        tk.Label(self.tab_yt,
            text="YOUTUBE DATA API",
            bg=COLORS["panel"],
            fg=COLORS["teal"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=14,
            pady=(14, 6))
        for k, l in [("yt_status", "Estado"),
            ("yt_title", "Video identificado"),
            ("yt_channel", "Canal"),
            ("yt_views", "Vistas"),
            ("yt_likes", "Me gusta"),
            ("yt_comments", "Comentarios"),
            ("yt_published", "Fecha de publicación"),
            ("yt_duration", "Duración del video"),
            ("yt_conf", "Conf."),
            ("yt_updated", "Última actualización")]:
            self._field(self.tab_yt, k, l)
        row = tk.Frame(self.tab_yt, bg=COLORS["panel"])
        row.pack(fill="x", padx=14, pady=12)
        StyledButton(row, "Actualizar YouTube", self.update_youtube, accent=True).pack(side="left")
        StyledButton(row,
            "Actualizar identificadas",
            self.refresh_youtube_identified).pack(side="left",
            padx=6)
        StyledButton(row, "Completar faltantes", self.discover_youtube_missing).pack(side="left")
        tk.Message(self.tab_yt,
            text=(
                'La identificación inicial usa search.list y respeta un límite diario local '
                'configurable. Una vez identificado el Video ID, las actualizaciones usan '
                'videos.list y no vuelven a buscar.'
            ),
            width=690,
            bg=COLORS["panel2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            padx=10,
            pady=8).pack(fill="x",
            padx=14,
            pady=(0, 12))

    def _build_sp(self):
        tk.Label(self.tab_sp,
            text="SPOTIFY WEB API",
            bg=COLORS["panel"],
            fg=COLORS["accent2_hover"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=14,
            pady=(14, 6))
        for k, l in [("sp_status", "Estado"),
            ("sp_title", "Título Spotify"),
            ("sp_artist", "Artista Spotify"),
            ("sp_album", "Álbum"),
            ("sp_release", "Lanzamiento"),
            ("sp_duration", "Duración oficial"),
            ("sp_explicit", "Explícita"),
            ("sp_isrc", "ISRC"),
            ("sp_conf", "Conf."),
            ("sp_updated", "Última actualización")]:
            self._field(self.tab_sp, k, l)
        row = tk.Frame(self.tab_sp, bg=COLORS["panel"])
        row.pack(fill="x", padx=14, pady=12)
        StyledButton(row, "Actualizar Spotify", self.update_spotify, accent=True).pack(side="left")
        StyledButton(row, "Completar faltantes", self.discover_spotify_missing).pack(side="left", padx=6)
        tk.Message(self.tab_sp,
            text=(
                'Spotify no publica streams exactos ni país principal en la Web API. Esta ficha usa '
                'únicamente metadatos verificables: track, artista, álbum, lanzamiento, duración, '
                'explicit e ISRC.'
            ),
            width=690,
            bg=COLORS["panel2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            padx=10,
            pady=8).pack(fill="x",
            padx=14,
            pady=(0, 12))

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        keep = self.selected_id
        self.tree.delete(*self.tree.get_children())
        for r in self.db.platform_rows(self.search.get()):
            self.tree.insert("",
                "end",
                iid=str(r["id"]),
                values=(r["song"],
                    r["artist"],
                    compact_count(r["sm_recordings"]) if r["sm_tracks"] else "—",
                    "✓" if r["youtube_video_id"] else "—",
                    "✓" if r["spotify_track_id"] else "—"))
        if keep and self.tree.exists(str(keep)):
            self.tree.selection_set(str(keep))
            self.tree.see(str(keep))
            self._load_values()

    def load(self, event=None):
        sel = self.tree.selection()
        self.selected_id = int(sel[0]) if sel else None
        self._load_values()

    def _load_values(self):
        if not self.selected_id:
            return
        r = self.db.con.execute((
            'SELECT s.*,(SELECT COUNT(*) FROM starmaker_song_matches m WHERE m.song_id=s.id AND '
            'm.included_in_total=1) sm_tracks,(SELECT SUM(p.recordings_count) FROM '
            'starmaker_song_matches m JOIN starmaker_public_catalog p ON '
            'p.public_key=m.public_key WHERE m.song_id=s.id AND m.included_in_total=1) '
            'sm_recordings FROM songs s WHERE s.id=?'
        ),
            (self.selected_id, )).fetchone()
        agg = self.db.sm_song_aggregate(self.selected_id)
        primary = agg["primary"]
        self.combo.config(text=f"{r['artist']} — {r['song']}   ·   UVE {r['emotion_type']} / {r['emotion_level']}")
        vals = {"sm_status":"Encontrada" if agg["count"] else "Sin datos",
            "sm_tracks":str(agg["count"]),
            "sm_recordings":compact_count(agg["total"]),
            "sm_primary":primary["title"] if primary else "—",
            "sm_conf":str(primary["confidence"]) if primary else "—",
            "sm_updated":self.db.setting("starmaker_last_auto_scan", "") or "—",
              "yt_status":"Encontrada" if r["youtube_video_id"] else "Sin datos",
                  "yt_title":r["youtube_title"] or "—",
                  "yt_channel":r["youtube_channel"] or "—",
                  "yt_views":compact_count(r["youtube_views"]),
                  "yt_likes":compact_count(r["youtube_likes"]),
                  "yt_comments":compact_count(r["youtube_comments"]),
                  "yt_published":r["youtube_published_at"] or "—",
                  "yt_duration":seconds_to_human(r["youtube_duration_seconds"] or 0) if r["youtube_duration_seconds"] else "—",
                  "yt_conf":str(r["youtube_match_confidence"] or "—"),
                  "yt_updated":r["youtube_updated_at"] or "—",
              "sp_status":"Encontrada" if r["spotify_track_id"] else "Sin datos",
                  "sp_title":r["spotify_title"] or "—",
                  "sp_artist":r["spotify_artist"] or "—",
                  "sp_album":r["spotify_album"] or "—",
                  "sp_release":r["spotify_release_date"] or "—",
                  "sp_duration":seconds_to_human(int((r["spotify_duration_ms"] or 0)/1000)) if r["spotify_duration_ms"] else "—",
                  "sp_explicit":"Sí" if r["spotify_explicit"]==1 else "No" if r["spotify_explicit"]==0 and r["spotify_track_id"] else "—",
                  "sp_isrc":r["spotify_isrc"] or "—",
                  "sp_conf":str(r["spotify_match_confidence"] or "—"),
                  "sp_updated":r["spotify_updated_at"] or "—"}
        for k, v in vals.items():
            self.fields[k].set(v)

    def _bg(self, fn):
        if self._busy:
            return messagebox.showinfo("Plataformas", "Hay una actualización en curso.")
        self._busy = True
        self.status.config(text="Actualizando…")
        def run():
            try:
                msg = fn()
                self.after(0, lambda:self._done(msg, None))
            except Exception as e:
                self.after(0, lambda:self._done("", e))
        threading.Thread(target=run, daemon=True).start()

    def _done(self, msg, err):
        self._busy = False
        self.status.config(text="Listo" if not err else "Error")
        self.refresh()
        if err:
            messagebox.showerror("Plataformas", str(err))
        elif msg:
            messagebox.showinfo("Plataformas", msg)

    def update_starmaker(self):
        if not self.selected_id:
            return
        sid = self.selected_id
        song = dict(self.db.get_song(sid))
        def work():
            bg = Database(self.db.path)
            try:
                entries, artists, _ = StarMakerDirectAPIClient.search(song["artist"],
                    song["song"],
                    timeout=12,
                    second_pass=True)
                if artists:
                    bg.sm_ingest_artists(artists)
                if entries:
                    bg.sm_ingest_entries(entries)
                bg.sm_interpretive_match([sid])
                bg.set_setting("starmaker_last_auto_scan", now_iso())
                a = bg.sm_song_aggregate(sid)
                return f"StarMaker: {a['count']} pistas · {compact_count(a['total'])} grabaciones compatibles."
            finally:
                bg.close()
        self._bg(work)

    def update_youtube(self):
        if not self.selected_id:
            return
        sid = self.selected_id
        song = dict(self.db.get_song(sid))
        key = self.db.setting("youtube_api_key", "").strip()
        if not key:
            return messagebox.showwarning("YouTube", "Configurá la YouTube Data API key en Configuración.")
        def work():
            db = Database(self.db.path)
            try:
                vid = song.get("youtube_video_id") or ""
                conf = int(song.get("youtube_match_confidence") or 0)
                if not vid:
                    rem, _, _ = db.youtube_search_allowance()
                    if rem<=0:
                        raise RuntimeError("Se alcanzó el límite diario local de búsquedas YouTube.")
                    cands = YouTubeClient.search(key, song["artist"], song["song"])
                    db.youtube_register_search(1)
                    if not cands:
                        raise RuntimeError("YouTube no encontró candidatos.")
                    best = cands[0]
                    if best["confidence"]<62:
                        raise RuntimeError(f"Coincidencia YouTube demasiado débil ({best['confidence']}/100): {best['title']}")
                    vid = best["video_id"]
                    conf = best["confidence"]
                data = YouTubeClient.stats(key, vid, conf)
                db.save_youtube_metadata(sid, data)
                return f"YouTube actualizado · {data['youtube_title']} · {compact_count(data['youtube_views'])} vistas."
            finally:
                db.close()
        self._bg(work)

    def refresh_youtube_identified(self):
        key = self.db.setting("youtube_api_key", "").strip()
        if not key:
            return messagebox.showwarning("YouTube", "Configurá la API key.")
        def work():
            db = Database(self.db.path)
            try:
                rows = db.con.execute("SELECT id,youtube_video_id,youtube_match_confidence FROM songs WHERE trim(youtube_video_id)<>''").fetchall()
                stats = YouTubeClient.stats_many(key, [r["youtube_video_id"] for r in rows])
                n = 0
                for r in rows:
                    if r["youtube_video_id"] in stats:
                        d = stats[r["youtube_video_id"]]
                        d["youtube_match_confidence"] = r["youtube_match_confidence"] or 0
                        db.save_youtube_metadata(r["id"], d)
                        n+=1
                return f"YouTube: {n} videos identificados actualizados."
            finally:
                db.close()
        self._bg(work)

    def discover_youtube_missing(self):
        key = self.db.setting("youtube_api_key", "").strip()
        if not key:
            return messagebox.showwarning("YouTube", "Configurá la API key.")
        def work():
            db = Database(self.db.path)
            try:
                rem, _, limit = db.youtube_search_allowance()
                rows = db.con.execute("SELECT * FROM songs WHERE trim(youtube_video_id)='' ORDER BY id LIMIT ?",
                    (rem, )).fetchall()
                found = 0
                for r in rows:
                    c = YouTubeClient.search(key, r["artist"], r["song"])
                    db.youtube_register_search(1)
                    if c and c[0]["confidence"]>=62:
                        d = YouTubeClient.stats(key, c[0]["video_id"], c[0]["confidence"])
                        db.save_youtube_metadata(r["id"], d)
                        found+=1
                    time.sleep(.08)
                return f"YouTube: {found}/{len(rows)} faltantes identificadas. Límite diario configurado: {limit}."
            finally:
                db.close()
        self._bg(work)

    def update_spotify(self):
        if not self.selected_id:
            return
        sid = self.selected_id
        song = dict(self.db.get_song(sid))
        def work():
            db = Database(self.db.path)
            try:
                if song.get("spotify_track_id"):
                    d = SpotifyClient.refresh_track(db, song["spotify_track_id"])
                    d["spotify_match_confidence"] = song.get("spotify_match_confidence") or 0
                else:
                    d = SpotifyClient.search_track(db, song["artist"], song["song"])
                    if not d:
                        raise RuntimeError("Spotify no encontró la canción.")
                    if d["spotify_match_confidence"]<65:
                        raise RuntimeError(f"Coincidencia Spotify demasiado débil ({d['spotify_match_confidence']}/100): {d['spotify_title']}")
                db.save_spotify_metadata(sid, d)
                return f"Spotify actualizado · {d['spotify_title']} — {d['spotify_artist']}."
            finally:
                db.close()
        self._bg(work)

    def discover_spotify_missing(self):
        def work():
            db = Database(self.db.path)
            try:
                SpotifyClient.ensure_token(db) or (_ for _ in ()).throw(RuntimeError("Spotify no está conectado."))
                rows = db.con.execute("SELECT * FROM songs WHERE trim(spotify_track_id)='' ORDER BY id LIMIT 50").fetchall()
                found = 0
                for r in rows:
                    try:
                        d = SpotifyClient.search_track(db, r["artist"], r["song"])
                        if d and d["spotify_match_confidence"]>=65:
                            db.save_spotify_metadata(r["id"], d)
                            found+=1
                    except Exception:
                        pass
                    time.sleep(.18)
                return f"Spotify: {found}/{len(rows)} faltantes identificadas en este lote."
            finally:
                db.close()
        self._bg(work)

    def update_selected_all(self):
        if not self.selected_id:
            return
        # StarMaker primero; YouTube/Spotify se ejecutan por separado para respetar credenciales/cuotas.
        self.update_starmaker()
        self.nb.select(self.tab_sm)
        messagebox.showinfo("Plataformas",
            (
                'Se inició StarMaker. Para YouTube y Spotify usá sus botones: cada API respeta sus '
                'propias credenciales y cuotas.'
            ))

    def open_youtube(self):
        if not self.selected_id:
            return
        r = self.db.get_song(self.selected_id)
        webbrowser.open("https://www.youtube.com/watch?v="+r["youtube_video_id"] if r["youtube_video_id"] else "https://www.youtube.com/results?search_query="+urllib.parse.quote_plus(f"{r['artist']} {r['song']}"))

    def open_spotify(self):
        if not self.selected_id:
            return
        r = self.db.get_song(self.selected_id)
        webbrowser.open(r["spotify_url"] if r["spotify_url"] else "https://open.spotify.com/search/"+urllib.parse.quote(f"{r['artist']} {r['song']}"))


class SettingsView(BaseView):

    def __init__(self, master, app):
        super().__init__(master,
            app,
            "Configuración",
            "Idioma, APIs, Spotify OAuth, apariencia, respaldo y diagnóstico.")
        self.nb = ttk.Notebook(self.body)
        self.nb.pack(fill="both", expand=True)
        self.tabs = {}
        for key, title in [("general", "General"),
            ("language", "Idioma"),
            ("youtube", "YouTube API"),
            ("spotify", "Spotify"),
            ("appearance", "Apariencia"),
            ("data", "Datos / respaldo"),
            ("diag", "Diagnóstico")]:
            f = tk.Frame(self.nb, bg=COLORS["bg"])
            self.nb.add(f, text=self.app.tr(title))
            self.tabs[key] = f
        self.gp = tk.StringVar()
        self.gn = tk.StringVar()
        self.gneg = tk.StringVar()
        self.lang_var = tk.StringVar()
        self.key = tk.StringVar()
        self.yt_limit = tk.StringVar()
        self.sp_client = tk.StringVar()
        self.sp_status = tk.StringVar(value="—")
        self._build_general()
        self._build_language()
        self._build_youtube()
        self._build_spotify()
        self._build_appearance()
        self._build_data()
        self._build_diag()

    def _entry_row(self, parent, label, var, secret=False):
        row = tk.Frame(parent, bg=COLORS["panel"])
        row.pack(fill="x", padx=18, pady=8)
        tk.Label(row,
            text=self.app.tr(label),
            width=28,
            anchor="w",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Entry(row,
            textvariable=var,
            show="•" if secret else "",
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["line_soft"]).pack(side="left",
            fill="x",
            expand=True,
            ipady=7)

    def _panel(self, parent):
        f = tk.Frame(parent, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["line"])
        f.pack(fill="x", padx=8, pady=8)
        return f

    def _build_general(self):
        p = self._panel(self.tabs["general"])
        self._entry_row(p, "Emoción general positiva", self.gp)
        self._entry_row(p, "Emoción general neutra", self.gn)
        self._entry_row(p, "Emoción general negativa", self.gneg)
        StyledButton(p, "Guardar configuración", self.save, accent=True).pack(anchor="w", padx=18, pady=12)

    def _build_language(self):
        p = self._panel(self.tabs["language"])
        tk.Label(p,
            text=self.app.tr("Idioma de interfaz"),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold")).pack(anchor="w",
            padx=18,
            pady=(16, 6))
        ttk.Combobox(p,
            textvariable=self.lang_var,
            values=list(UI_LANGUAGES.values()),
            state="readonly",
            width=30).pack(anchor="w",
            padx=18,
            pady=6)
        StyledButton(p,
            "Guardar configuración",
            self.save_language,
            accent=True).pack(anchor="w",
            padx=18,
            pady=10)
        tk.Message(p,
            text=(
                'La interfaz se puede mostrar en Español, English, 日本語 y Filipino. Los títulos, '
                'artistas, descripciones UVE y demás datos musicales NO se traducen ni se modifican. '
                'El cambio completo se aplica al reiniciar.'
            ),
            width=900,
            bg=COLORS["panel2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            padx=12,
            pady=10).pack(fill="x",
            padx=18,
            pady=(4, 16))

    def _build_youtube(self):
        p = self._panel(self.tabs["youtube"])
        self._entry_row(p, "YouTube Data API key", self.key, True)
        self._entry_row(p, "Máximo de búsquedas nuevas por día", self.yt_limit)
        row = tk.Frame(p, bg=COLORS["panel"])
        row.pack(fill="x", padx=18, pady=10)
        StyledButton(row, "Guardar configuración", self.save, accent=True).pack(side="left")
        self.yt_status = tk.Label(row, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8))
        self.yt_status.pack(side="left", padx=12)
        tk.Message(p,
            text=(
                'YouTube Data API: las canciones ya identificadas se actualizan con videos.list. El '
                'descubrimiento de nuevas canciones usa search.list y está limitado por cuota; el '
                'programa lleva un contador diario local para no gastar búsquedas innecesarias.'
            ),
            width=900,
            bg=COLORS["panel2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            padx=12,
            pady=10).pack(fill="x",
            padx=18,
            pady=(0, 16))

    def _build_spotify(self):
        p = self._panel(self.tabs["spotify"])
        self._entry_row(p, "Spotify Client ID", self.sp_client)
        tk.Label(p,
            text="Redirect URI a registrar en Spotify Developer Dashboard: http://127.0.0.1/callback",
            bg=COLORS["panel"],
            fg=COLORS["teal"],
            font=("Consolas", 9)).pack(anchor="w",
            padx=18,
            pady=6)
        row = tk.Frame(p, bg=COLORS["panel"])
        row.pack(fill="x", padx=18, pady=10)
        StyledButton(row, "Guardar configuración", self.save, accent=True).pack(side="left")
        StyledButton(row, "Conectar Spotify", self.connect_spotify).pack(side="left", padx=6)
        StyledButton(row, "Desconectar Spotify", self.disconnect_spotify, danger=True).pack(side="left")
        tk.Label(row,
            textvariable=self.sp_status,
            bg=COLORS["panel"],
            fg=COLORS["teal"],
            font=("Segoe UI", 9, "bold")).pack(side="left",
            padx=12)
        tk.Message(p,
            text=(
                'La conexión usa Authorization Code + PKCE: no se guarda Client Secret. Spotify abre '
                'una autorización en el navegador y vuelve a 127.0.0.1. El programa usa la Web API '
                'sólo para metadatos verificables; no inventa streams ni país principal.'
            ),
            width=900,
            bg=COLORS["panel2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            padx=12,
            pady=10).pack(fill="x",
            padx=18,
            pady=(0, 16))

    def _build_appearance(self):
        p = self._panel(self.tabs["appearance"])
        tk.Label(p,
            text="PALETA INTELLIGENCE",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 11, "bold")).pack(anchor="w",
            padx=18,
            pady=(16, 10))
        row = tk.Frame(p, bg=COLORS["panel"])
        row.pack(fill="x", padx=18, pady=8)
        for name, key in [("Rosa", "accent"),
            ("Violeta", "accent2"),
            ("Turquesa", "teal"),
            ("Azul verdoso", "aqua"),
            ("Positiva", "positive"),
            ("Neutra", "neutral"),
            ("Negativa", "negative")]:
            f = tk.Frame(row, bg=COLORS[key], width=110, height=55)
            f.pack(side="left", padx=4)
            f.pack_propagate(False)
            tk.Label(f,
                text=name,
                bg=COLORS[key],
                fg=COLORS["white"],
                font=("Segoe UI", 8, "bold")).pack(expand=True)
        tk.Message(p,
            text=(
                'La V1.6.1 usa azul oscuro + rosa + violeta + turquesa. Los colores UVE '
                'positivo/neutro/negativo se mantienen semánticos.'
            ),
            width=900,
            bg=COLORS["panel2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            padx=12,
            pady=10).pack(fill="x",
            padx=18,
            pady=(8, 16))

    def _build_data(self):
        p = self._panel(self.tabs["data"])
        row = tk.Frame(p, bg=COLORS["panel"])
        row.pack(fill="x", padx=18, pady=16)
        StyledButton(row, "Respaldar base SQLite", self.backup, accent=True).pack(side="left")
        StyledButton(row, "Exportar biblioteca CSV", self.export).pack(side="left", padx=8)
        StyledButton(row, "Actualizar géneros MusicBrainz", self.update_genre_catalog).pack(side="left")
        self.genre_status = tk.Label(p, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8))
        self.genre_status.pack(anchor="w", padx=18, pady=(0, 16))

    def _build_diag(self):
        p = self._panel(self.tabs["diag"])
        self.diag_text = tk.Text(p,
            height=10,
            bg=COLORS["panel2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Consolas", 9))
        self.diag_text.pack(fill="x", padx=18, pady=(16, 8))
        StyledButton(p, "Actualizar diagnóstico", self.refresh_diag).pack(anchor="w", padx=18, pady=(0, 8))
        self.log_tree = ttk.Treeview(p, columns=("time", "op", "result", "error"), show="headings", height=10)
        for c, txt, w in [("time", "Hora", 145),
            ("op", "Operación", 160),
            ("result", "Resultado", 380),
            ("error", "Error", 380)]:
            self.log_tree.heading(c, text=txt)
            self.log_tree.column(c, width=w)
        self.log_tree.pack(fill="both", expand=True, padx=18, pady=(0, 16))

    def refresh(self):
        self.key.set(self.db.setting("youtube_api_key", ""))
        self.yt_limit.set(self.db.setting("youtube_search_daily_limit", "40"))
        self.gp.set(self.db.setting("general_positive", "Felicidad"))
        self.gn.set(self.db.setting("general_neutral", "Emoción neutra"))
        self.gneg.set(self.db.setting("general_negative", "Tristeza"))
        self.sp_client.set(self.db.setting("spotify_client_id", ""))
        code = self.db.setting("ui_language", "es")
        self.lang_var.set(UI_LANGUAGES.get(code, "Español"))
        self.genre_status.config(text=f"Catálogo local: {len(load_genre_catalog(self.db))} géneros/estilos.")
        rem, count, limit = self.db.youtube_search_allowance()
        self.yt_status.config(text=f"Búsquedas nuevas hoy: {count}/{limit} · restantes {rem}")
        try:
            connected = bool(SpotifyClient.ensure_token(self.db))
        except Exception:
            connected = bool(self.db.setting("spotify_refresh_token", ""))
        self.sp_status.set("🟢 Conectado" if connected else "⚪ No conectado")
        self.refresh_diag()

    def save(self):
        self.db.set_setting("youtube_api_key", self.key.get().strip())
        self.db.set_setting("youtube_search_daily_limit",
            str(max(1, min(100, int(self.yt_limit.get() or 40)))))
        self.db.set_setting("general_positive", self.gp.get().strip() or "Felicidad")
        self.db.set_setting("general_neutral", self.gn.get().strip() or "Emoción neutra")
        self.db.set_setting("general_negative", self.gneg.get().strip() or "Tristeza")
        self.db.set_setting("spotify_client_id", self.sp_client.get().strip())
        messagebox.showinfo("Configuración", "Configuración guardada.")
        self.refresh()

    def save_language(self):
        code = next((k for k, v in UI_LANGUAGES.items() if v==self.lang_var.get()), "es")
        self.db.set_setting("ui_language", code)
        messagebox.showinfo("Idioma",
            "Idioma guardado. Reiniciá Playlist Emotion Studio para aplicar toda la interfaz.")

    def connect_spotify(self):
        self.db.set_setting("spotify_client_id", self.sp_client.get().strip())
        if not self.sp_client.get().strip():
            return messagebox.showwarning("Spotify", "Ingresá el Client ID.")
        self.sp_status.set("Autorizando…")
        def work():
            bg = Database(self.db.path)
            try:
                SpotifyClient.connect_pkce(bg)
                self.after(0,
                    lambda:(self.sp_status.set("🟢 Conectado"),
                        messagebox.showinfo("Spotify", "Spotify conectado correctamente.")))
            except Exception as e:
                self.after(0, lambda:self._spotify_error(e))
            finally:
                bg.close()
        threading.Thread(target=work, daemon=True).start()

    def _spotify_error(self, e):
        self.sp_status.set("🔴 Error")
        messagebox.showerror("Spotify", str(e))

    def disconnect_spotify(self):
        for k in ("spotify_access_token", "spotify_refresh_token", "spotify_token_expires_at"):
            self.db.set_setting(k, "" if k!="spotify_token_expires_at" else "0")
        self.sp_status.set("⚪ No conectado")

    def backup(self):
        path = filedialog.asksaveasfilename(defaultextension=".db",
            filetypes=[("SQLite", "*.db")],
            initialfile=f"playlist_backup_{datetime.now():%Y%m%d_%H%M}.db")
        if path:
            self.db.con.commit()
            shutil.copy2(self.db.path, path)
            messagebox.showinfo("Respaldo", f"Base respaldada:\n{path}")

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="biblioteca_completa.csv")
        if path:
            self.db.export_library_csv(path)
            messagebox.showinfo("Exportado", f"Biblioteca exportada:\n{path}")

    def update_genre_catalog(self):
        self.genre_status.config(text="Actualizando MusicBrainz…")
        def work():
            try:
                vals = MusicBrainzGenreClient.fetch_all_genres()
                GENRE_CATALOG_PATH.write_text("\n".join(vals)+"\n", encoding="utf-8") if vals else None
                self.after(0,
                    lambda:self.genre_status.config(text=f"MusicBrainz: {len(vals)} géneros/estilos." if vals else "Sin resultados."))
            except Exception as exc:
                self.after(0, lambda:messagebox.showerror("MusicBrainz", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def refresh_diag(self):
        if not hasattr(self, "diag_text"):
            return
        d = self.db.intelligence_dashboard()
        txt = f"Playlist Emotion Studio V{VERSION}\nDB: {self.db.path}\nCanciones: {d['total']}\nStarMaker: {d['sm_found']} encontradas / {compact_count(d['sm_recordings'])} grabaciones\nYouTube identificadas: {d['youtube_found']}\nSpotify identificadas: {d['spotify_found']}\nIdioma: {self.db.setting('ui_language','es')}\nStarMaker engine: Direct API JSON\n"
        self.diag_text.delete("1.0", "end")
        self.diag_text.insert("1.0", txt)
        self.log_tree.delete(*self.log_tree.get_children())
        for r in self.db.starmaker_logs(80):
            self.log_tree.insert("", "end", values=(r["created_at"], r["operation"], r["result"], r["error"]))


def main():
    set_windows_dpi_awareness()
    app = App()
    if os.environ.get("APP_SMOKE_TEST") == "1":
        app.after(250, app.destroy)
    app.mainloop()


if __name__ == "__main__":
    main()
