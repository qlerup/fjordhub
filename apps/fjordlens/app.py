import hashlib
import shutil
import subprocess
import tempfile
import html
import ipaddress
import re
import hmac
import secrets
import io
import json
import os
import sqlite3
import zipfile
import unicodedata
import math
from contextlib import closing
from datetime import datetime, timedelta
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from flask import Flask, jsonify, render_template, request, send_from_directory, redirect, url_for, make_response, session, send_file
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import threading
from PIL import Image, ExifTags, ImageOps, ImageDraw, ImageFont
import piexif
import exifread
import requests
import reverse_geocoder as rg
import pycountry
import pyotp
import qrcode
import base64
import queue
try:
    # Enable HEIC/HEIF support via pillow-heif if available
    from pillow_heif import register_heif_opener, HeifFile  # type: ignore
    register_heif_opener()
except Exception:
    pass
try:
    import rawpy  # type: ignore
except Exception:
    rawpy = None  # type: ignore

import subprocess
import shutil
from urllib.parse import quote, unquote, urlparse, urlunparse
from werkzeug.utils import secure_filename

APP_PORT = 8080
# DATA_DIR is app state (db, cache, temp, secrets, etc.)
# UPLOAD_DIR can be split out to separate storage (e.g. NFS) for originals/converted uploads.
# THUMB_DIR can be split out independently for thumbnail storage.
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data")).resolve()
# If PHOTO_DIR is not set, default to a library folder inside DATA_DIR so no external mount is required
PHOTO_DIR = Path(os.environ.get("PHOTO_DIR", str(DATA_DIR / "library"))).resolve()
_THUMB_DIR_ENV = os.environ.get("THUMB_DIR") or os.environ.get("THUMBS_DIR")
THUMB_DIR = Path(_THUMB_DIR_ENV or str(DATA_DIR / "thumbs")).resolve()
CONVERT_DIR = DATA_DIR / "converted"
_UPLOAD_DIR_ENV = os.environ.get("UPLOAD_DIR") or os.environ.get("UPLOADS_DIR")
UPLOAD_DIR = Path(_UPLOAD_DIR_ENV or str(DATA_DIR / "uploads")).resolve()
TUS_TMP_DIR = DATA_DIR / "tus_uploads"
DB_PATH = DATA_DIR / "fjordlens.db"
INSTALL_STATE_PATH = DATA_DIR / "fjordlens.install.json"
INSTALL_STATE_LOCK = threading.Lock()
_SQLITE_JOURNAL_MODE_ENV = str(os.environ.get("SQLITE_JOURNAL_MODE", "") or "").strip().upper()
_SQLITE_JOURNAL_MODE_ALLOWED = {"DELETE", "WAL", "TRUNCATE", "PERSIST", "MEMORY", "OFF"}


def _linux_mount_fstype_for_path(path: Path) -> str:
    """Best-effort filesystem type lookup for a given path (Linux /proc/mounts)."""
    try:
        target = str(path.resolve()).replace("\\", "/")
    except Exception:
        target = str(path).replace("\\", "/")
    if not target.startswith("/"):
        return ""
    best_mount = ""
    best_fs = ""
    try:
        with Path("/proc/mounts").open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 3:
                    continue
                mount_raw = str(parts[1] or "")
                fs_type = str(parts[2] or "")
                mount = (
                    mount_raw
                    .replace("\\040", " ")
                    .replace("\\011", "\t")
                    .replace("\\012", "\n")
                    .replace("\\134", "\\")
                )
                mount = mount.rstrip("/") or "/"
                if target == mount or target.startswith(mount.rstrip("/") + "/") or mount == "/":
                    if len(mount) > len(best_mount):
                        best_mount = mount
                        best_fs = fs_type
    except Exception:
        return ""
    return best_fs.lower()


def _is_network_fstype(fs_type: str) -> bool:
    fs = str(fs_type or "").strip().lower()
    if not fs:
        return False
    return (
        fs.startswith("nfs")
        or fs.startswith("cifs")
        or fs.startswith("smb")
        or fs.startswith("fuse.sshfs")
        or fs.startswith("davfs")
        or fs.startswith("afp")
        or fs.startswith("ceph")
        or fs.startswith("gluster")
    )


DATA_DIR_FS_TYPE = _linux_mount_fstype_for_path(DATA_DIR)
UPLOAD_DIR_FS_TYPE = _linux_mount_fstype_for_path(UPLOAD_DIR)
THUMB_DIR_FS_TYPE = _linux_mount_fstype_for_path(THUMB_DIR)
if _SQLITE_JOURNAL_MODE_ENV in _SQLITE_JOURNAL_MODE_ALLOWED:
    SQLITE_JOURNAL_MODE = _SQLITE_JOURNAL_MODE_ENV
else:
    # Safe default: WAL on local storage, DELETE on network filesystems.
    SQLITE_JOURNAL_MODE = "DELETE" if _is_network_fstype(DATA_DIR_FS_TYPE) else "WAL"
try:
    SQLITE_BUSY_TIMEOUT_MS = int(os.environ.get("SQLITE_BUSY_TIMEOUT_MS", "10000") or 10000)
except Exception:
    SQLITE_BUSY_TIMEOUT_MS = 10000
SQLITE_BUSY_TIMEOUT_MS = max(1000, min(120000, SQLITE_BUSY_TIMEOUT_MS))
ENABLE_LIBRARY_SOURCE = (
    str(os.environ.get("ENABLE_LIBRARY_SOURCE", "0") or "0").strip().lower()
    in {"1", "true", "yes", "on"}
)
ENABLE_SCAN_FEATURES = (
    str(os.environ.get("ENABLE_SCAN_FEATURES", "0") or "0").strip().lower()
    in {"1", "true", "yes", "on"}
)
AI_URL = os.environ.get("AI_URL", "http://localhost:8001").rstrip("/")
try:
    AI_DESC_REQUEST_TIMEOUT_SEC = float(os.environ.get("AI_DESC_REQUEST_TIMEOUT_SEC", "120") or 120)
except Exception:
    AI_DESC_REQUEST_TIMEOUT_SEC = 120.0
AI_DESC_REQUEST_TIMEOUT_SEC = max(10.0, min(600.0, AI_DESC_REQUEST_TIMEOUT_SEC))
SHARE_DUCKDNS_BASE_URL = str(os.environ.get("SHARE_DUCKDNS_BASE_URL", "")).strip()
PHOTOFRAME_FRAMES_ENV = str(os.environ.get("PHOTOFRAME_FRAMES", "") or "").strip()
PHOTOFRAME_FRAMES_PATH = DATA_DIR / "photoframes.json"
try:
    PHOTOFRAME_STATUS_TIMEOUT_SEC = float(os.environ.get("PHOTOFRAME_STATUS_TIMEOUT_SEC", "2.5") or 2.5)
except Exception:
    PHOTOFRAME_STATUS_TIMEOUT_SEC = 2.5
PHOTOFRAME_STATUS_TIMEOUT_SEC = max(0.5, min(8.0, PHOTOFRAME_STATUS_TIMEOUT_SEC))
try:
    PHOTOFRAME_ONLINE_WINDOW_SEC = int(os.environ.get("PHOTOFRAME_ONLINE_WINDOW_SEC", "180") or 180)
except Exception:
    PHOTOFRAME_ONLINE_WINDOW_SEC = 180
PHOTOFRAME_ONLINE_WINDOW_SEC = max(30, min(3600, PHOTOFRAME_ONLINE_WINDOW_SEC))
try:
    PHOTOFRAME_SETTINGS_PROXY_TIMEOUT_SEC = float(os.environ.get("PHOTOFRAME_SETTINGS_PROXY_TIMEOUT_SEC", "20") or 20)
except Exception:
    PHOTOFRAME_SETTINGS_PROXY_TIMEOUT_SEC = 20.0
PHOTOFRAME_SETTINGS_PROXY_TIMEOUT_SEC = max(3.0, min(45.0, PHOTOFRAME_SETTINGS_PROXY_TIMEOUT_SEC))
try:
    PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC = int(os.environ.get("PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC", "600") or 600)
except Exception:
    PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC = 600
PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC = max(60, min(7200, PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC))
try:
    PHOTOFRAME_FEED_MAX_IMAGES = int(os.environ.get("PHOTOFRAME_FEED_MAX_IMAGES", "1200") or 1200)
except Exception:
    PHOTOFRAME_FEED_MAX_IMAGES = 1200
PHOTOFRAME_FEED_MAX_IMAGES = max(10, min(5000, PHOTOFRAME_FEED_MAX_IMAGES))
PHOTOFRAME_TEXT_ONLY = (str(os.environ.get("PHOTOFRAME_TEXT_ONLY", "0") or "0").strip().lower() in {"1", "true", "yes", "on"})
PHOTOFRAME_UPDATE_SOURCE_DIR_ENV = str(os.environ.get("PHOTOFRAME_UPDATE_SOURCE_DIR", "") or "").strip()
PHOTOFRAME_UPDATE_UPLOAD_DIR = DATA_DIR / "photoframe_updates"
try:
    PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES = int(os.environ.get("PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES", str(300 * 1024 * 1024)) or (300 * 1024 * 1024))
except Exception:
    PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES = 300 * 1024 * 1024
PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES = max(5 * 1024 * 1024, min(2 * 1024 * 1024 * 1024, PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES))
PHOTOFRAME_LATEST_VERSION_KEY = "photoframe_latest_version"
PHOTOFRAME_LATEST_VERSION_AT_KEY = "photoframe_latest_version_at"
APP_UPDATE_SERVICE_URL = str(os.environ.get("FJORDLENS_UPDATER_URL", "http://fjordlens-updater:8090") or "").strip().rstrip("/")
try:
    APP_UPDATE_SERVICE_TIMEOUT_SEC = float(os.environ.get("FJORDLENS_UPDATER_TIMEOUT_SEC", "20") or 20)
except Exception:
    APP_UPDATE_SERVICE_TIMEOUT_SEC = 20.0
APP_UPDATE_SERVICE_TIMEOUT_SEC = max(2.0, min(120.0, APP_UPDATE_SERVICE_TIMEOUT_SEC))
APP_UPDATE_STATE_DIR = DATA_DIR / "updater"
APP_UPDATE_STATE_PATH = APP_UPDATE_STATE_DIR / "update_state.json"
APP_UPDATE_STATE_LOCK = threading.RLock()
APP_UPDATE_AUTO_CHECK_DEFAULT_ENABLED = (
    str(os.environ.get("FJORDLENS_AUTO_UPDATE_CHECK", "1") or "1").strip().lower()
    in {"1", "true", "yes", "on"}
)
try:
    APP_UPDATE_AUTO_CHECK_DEFAULT_INTERVAL_MINUTES = int(
        os.environ.get("FJORDLENS_AUTO_UPDATE_CHECK_INTERVAL_MINUTES", "30") or 30
    )
except Exception:
    APP_UPDATE_AUTO_CHECK_DEFAULT_INTERVAL_MINUTES = 30
PHOTOFRAME_WIFI_COUNTRY_CHOICES = (
    ("DK", "Danmark"),
    ("SE", "Sverige"),
    ("NO", "Norge"),
    ("FI", "Finland"),
    ("DE", "Tyskland"),
    ("NL", "Holland"),
    ("GB", "Storbritannien"),
    ("US", "USA"),
    ("FR", "Frankrig"),
    ("ES", "Spanien"),
    ("IT", "Italien"),
)


def _normalize_ai_desc_model(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"qwen", "qwen-vl", "qwen_vl", "qwen2.5-vl", "qwen2_5_vl"}:
        return "qwen"
    return "light"


AI_ENV_ENABLED_DEFAULT = (os.environ.get("AI_ENABLED", "1") not in {"0", "false", "False"})
AI_ENV_AUTO_INGEST_DEFAULT = (os.environ.get("AI_AUTO_INGEST", "0") in {"1", "true", "True"})
AI_DESC_ENV_AUTO_INGEST_DEFAULT = (os.environ.get("AI_DESC_AUTO_INGEST", "0") in {"1", "true", "True"})
AI_DESC_MODEL_ENV_DEFAULT = _normalize_ai_desc_model(os.environ.get("AI_DESC_MODEL", "light"))
FACES_ENV_AUTO_INDEX_DEFAULT = (os.environ.get("FACES_AUTO_INDEX", "0") in {"1", "true", "True"})
HEIC_CONVERT_ON_UPLOAD_DEFAULT = (os.environ.get("HEIC_CONVERT_ON_UPLOAD", "0") in {"1", "true", "True"})
RAW_CONVERT_ON_UPLOAD_DEFAULT = str(os.environ.get("RAW_CONVERT_ON_UPLOAD", "1") or "1").strip().lower() not in {"0", "false", "no", "off"}
UPLOAD_WORKFLOW_MODE_GENTLE = "gentle"
UPLOAD_WORKFLOW_MODE_AGGRESSIVE = "aggressive"
UPLOAD_WORKFLOW_MODE_DEFAULT = UPLOAD_WORKFLOW_MODE_GENTLE
UPLOAD_WORKFLOW_FACE_BATCH_SIZE = 10
# Thumbnail generation currently uses PIL/ffmpeg and does not use GPU in this service.
UPLOAD_WORKFLOW_THUMBNAILS_USE_GPU = False
UPLOAD_DEST_UPLOADS = "uploads"
UPLOAD_DEST_LIBRARY = "library"
UPLOAD_DEST_DEFAULT = UPLOAD_DEST_UPLOADS
UPLOAD_DEST_CHOICES = {UPLOAD_DEST_UPLOADS, UPLOAD_DEST_LIBRARY}
LANG_DA = "da"
LANG_EN = "en"
LANG_CHOICES = {LANG_DA, LANG_EN}
DEFAULT_UI_LANGUAGE = LANG_DA
DEFAULT_SEARCH_LANGUAGE = LANG_DA
WEATHER_PROVIDER = "open-meteo"
WEATHER_HISTORY_API_URL = str(os.environ.get("WEATHER_HISTORY_API_URL", "https://archive-api.open-meteo.com/v1/archive") or "").strip()
WEATHER_GEOCODING_API_URL = str(os.environ.get("WEATHER_GEOCODING_API_URL", "https://geocoding-api.open-meteo.com/v1/search") or "").strip()
WEATHER_AUTO_FETCH = (
    str(os.environ.get("WEATHER_AUTO_FETCH", "1") or "1").strip().lower()
    in {"1", "true", "yes", "on"}
)
try:
    WEATHER_HISTORY_TIMEOUT_SEC = float(os.environ.get("WEATHER_HISTORY_TIMEOUT_SEC", "10") or 10)
except Exception:
    WEATHER_HISTORY_TIMEOUT_SEC = 10.0
WEATHER_HISTORY_TIMEOUT_SEC = max(2.0, min(30.0, WEATHER_HISTORY_TIMEOUT_SEC))
try:
    WEATHER_GEOCODING_TIMEOUT_SEC = float(os.environ.get("WEATHER_GEOCODING_TIMEOUT_SEC", "8") or 8)
except Exception:
    WEATHER_GEOCODING_TIMEOUT_SEC = 8.0
WEATHER_GEOCODING_TIMEOUT_SEC = max(2.0, min(30.0, WEATHER_GEOCODING_TIMEOUT_SEC))
WEATHER_HOURLY_FIELDS = (
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
)
WEATHER_CODE_LABELS: Dict[int, Tuple[str, str]] = {
    0: ("Klart", "Clear"),
    1: ("Overvejende klart", "Mainly clear"),
    2: ("Let skyet", "Partly cloudy"),
    3: ("Overskyet", "Overcast"),
    45: ("Tåge", "Fog"),
    48: ("Rimtåge", "Depositing rime fog"),
    51: ("Let støvregn", "Light drizzle"),
    53: ("Støvregn", "Drizzle"),
    55: ("Tæt støvregn", "Dense drizzle"),
    56: ("Let frysende støvregn", "Light freezing drizzle"),
    57: ("Frysende støvregn", "Freezing drizzle"),
    61: ("Let regn", "Light rain"),
    63: ("Regn", "Rain"),
    65: ("Kraftig regn", "Heavy rain"),
    66: ("Let frysende regn", "Light freezing rain"),
    67: ("Frysende regn", "Freezing rain"),
    71: ("Let sne", "Light snow"),
    73: ("Sne", "Snow"),
    75: ("Kraftig sne", "Heavy snow"),
    77: ("Snefnug", "Snow grains"),
    80: ("Lette regnbyger", "Light rain showers"),
    81: ("Regnbyger", "Rain showers"),
    82: ("Kraftige regnbyger", "Heavy rain showers"),
    85: ("Lette snebyger", "Light snow showers"),
    86: ("Kraftige snebyger", "Heavy snow showers"),
    95: ("Torden", "Thunderstorm"),
    96: ("Torden med let hagl", "Thunderstorm with slight hail"),
    99: ("Torden med hagl", "Thunderstorm with hail"),
}
# Enable AI-assisted query expansion via Qwen text when available
AI_QUERY_EXPAND_ENABLED = (
    str(os.environ.get("AI_QUERY_EXPAND", "1") or "1").strip().lower() in {"1", "true", "yes", "on"}
)
# Static directories (for icons and assets resolved outside templates)
STATIC_DIR = Path(__file__).parent / "static"
LOGOS_DIR = STATIC_DIR / "logos"
LOGOS_WEB_DIR = LOGOS_DIR / "web"
LOGOS_ICONS_DIR = LOGOS_DIR / "icons"
LOGOS_MAIN_DIR = LOGOS_DIR / "logos"
TEMPLATE_I18N: Dict[str, Dict[str, str]] = {
    LANG_DA: {
        "login_invalid_credentials": "Forkert brugernavn eller adgangskode",
        "setup_invalid_token": "Forkert setup-token",
        "setup_fill_fields": "Udfyld felterne",
        "setup_password_mismatch": "Adgangskoder matcher ikke",
        "invalid_code": "Ugyldig kode",
        "share_invalid_or_expired": "Share link er ugyldigt eller udlÃ¸bet.",
        "admin_user_created": "Bruger oprettet",
        "admin_cannot_delete_self": "Du kan ikke slette din egen bruger",
        "admin_user_not_found": "Bruger findes ikke",
        "admin_cannot_delete_last_admin": "Kan ikke slette den sidste admin",
        "admin_user_deleted": "Bruger slettet",
        "error_prefix": "Fejl:",
    },
    LANG_EN: {
        "login_invalid_credentials": "Invalid username or password",
        "setup_invalid_token": "Invalid setup token",
        "setup_fill_fields": "Please fill in all required fields",
        "setup_password_mismatch": "Passwords do not match",
        "invalid_code": "Invalid code",
        "share_invalid_or_expired": "Share link is invalid or expired.",
        "admin_user_created": "User created",
        "admin_cannot_delete_self": "You cannot delete your own user",
        "admin_user_not_found": "User not found",
        "admin_cannot_delete_last_admin": "Cannot delete the last admin",
        "admin_user_deleted": "User deleted",
        "error_prefix": "Error:",
    },
}

# Backwards-compat: ensure optional user columns exist
def _ensure_users_theme_mode_column(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("ALTER TABLE users ADD COLUMN theme_mode TEXT DEFAULT 'system'")
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
UPLOAD_DEFAULT_SUBDIR_BY_DEST = {
    UPLOAD_DEST_UPLOADS: "",
    UPLOAD_DEST_LIBRARY: "Photos",
}
FACE_MATCH_THRESHOLD = float(os.environ.get("FACE_MATCH_THRESHOLD", "0.5"))
FACE_MATCH_THRESHOLD_CENTROID = float(os.environ.get("FACE_MATCH_THRESHOLD_CENTROID", str(FACE_MATCH_THRESHOLD)))
_FACE_MAYBE_THRESHOLD_DEFAULT = max(0.0, FACE_MATCH_THRESHOLD_CENTROID - 0.12)
try:
    FACE_MAYBE_THRESHOLD = float(os.environ.get("FACE_MAYBE_THRESHOLD", str(_FACE_MAYBE_THRESHOLD_DEFAULT)) or _FACE_MAYBE_THRESHOLD_DEFAULT)
except Exception:
    FACE_MAYBE_THRESHOLD = _FACE_MAYBE_THRESHOLD_DEFAULT
FACE_MAYBE_THRESHOLD = max(0.0, min(FACE_MATCH_THRESHOLD_CENTROID, FACE_MAYBE_THRESHOLD))
VIDEO_FACE_SAMPLE_INTERVAL_SEC = float(os.environ.get("VIDEO_FACE_SAMPLE_INTERVAL_SEC", "3.0"))
VIDEO_FACE_SAMPLE_MAX_FRAMES = int(os.environ.get("VIDEO_FACE_SAMPLE_MAX_FRAMES", "24"))
VIDEO_FACE_SAMPLE_START_SEC = float(os.environ.get("VIDEO_FACE_SAMPLE_START_SEC", "0.5"))
VIDEO_FACE_DEDUPE_THRESHOLD = float(os.environ.get("VIDEO_FACE_DEDUPE_THRESHOLD", "0.92"))
AI_INGEST_THROTTLE_SEC = max(0.0, float(os.environ.get("AI_INGEST_THROTTLE_SEC", "0.04")))
FACES_INDEX_THROTTLE_SEC = max(0.0, float(os.environ.get("FACES_INDEX_THROTTLE_SEC", "0.06")))

RAW_EXTS = {".dng", ".cr2", ".cr3", ".nef", ".arw", ".rw2", ".raf", ".orf", ".srw", ".pef"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".heic", ".heif"} | RAW_EXTS


def _raw_to_jpeg(src: Path, dst: Path) -> None:
    """Convert RAW (incl. DNG) to JPEG.
    1) Try rawpy (preferred for quality)
    2) Fallback to ffmpeg thumbnail/extract if rawpy cannot decode
    Raises on failure.
    """
    last_error: Exception | None = None
    # First try rawpy if available
    if rawpy is not None:
        try:
            with rawpy.imread(str(src)) as raw:  # type: ignore
                rgb = raw.postprocess(
                    use_auto_wb=True,
                    no_auto_bright=True,
                    output_color=rawpy.ColorSpace.sRGB,  # type: ignore
                    output_bps=8,
                    gamma=None,
                    half_size=True,
                )
            Image.fromarray(rgb).save(dst, format="JPEG", quality=92, optimize=True)
            return
        except Exception as e:  # fall back to ffmpeg
            last_error = e
    # Next try ExifTool preview extraction (very robust for DNG)
    exiftool_error: Exception | None = None
    try:
        if shutil.which("exiftool"):
            for tag in ("PreviewImage", "JpgFromRaw", "ThumbnailImage"):
                try:
                    with open(dst, "wb") as outf:
                        subprocess.run(["exiftool", "-b", f"-{tag}", str(src)], check=True, stdout=outf)
                    if dst.exists() and dst.stat().st_size > 0:
                        return
                except Exception as et:
                    exiftool_error = et
                    if dst.exists():
                        try:
                            dst.unlink()
                        except Exception:
                            pass
        else:
            exiftool_error = RuntimeError("exiftool not available")
    except Exception as e:
        exiftool_error = e

    # Finally, try ffmpeg single-frame extraction (works for some RAWs with embedded preview)
    try:
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not available for RAW fallback")
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(dst),
        ]
        subprocess.run(cmd, check=True)
        if not dst.exists() or dst.stat().st_size == 0:
            raise RuntimeError("ffmpeg produced empty output")
        return
    except Exception as e:
        # Prefer reporting the rawpy error (if any) and exiftool error as context
        raise RuntimeError(f"RAW convert failed; rawpy={last_error!r}, exiftool={exiftool_error!r}, ffmpeg={e!r}")
VIDEO_EXTS = {".mp4", ".m4v", ".mov", ".avi", ".mkv", ".webm", ".3gp"}
SUPPORTED_EXTS = IMAGE_EXTS | VIDEO_EXTS
MOV_CONVERT_ON_UPLOAD_DEFAULT = str(os.environ.get("MOV_CONVERT_ON_UPLOAD", "1") or "1").strip().lower() not in {"0", "false", "no", "off"}
MOV_CONVERT_PRESET = str(os.environ.get("MOV_CONVERT_PRESET", "veryfast") or "veryfast").strip() or "veryfast"
try:
    MOV_CONVERT_CRF = int(os.environ.get("MOV_CONVERT_CRF", "23") or 23)
except Exception:
    MOV_CONVERT_CRF = 23
MOV_CONVERT_CRF = max(18, min(36, MOV_CONVERT_CRF))
MOV_CONVERT_AUDIO_BITRATE = str(os.environ.get("MOV_CONVERT_AUDIO_BITRATE", "128k") or "128k").strip() or "128k"
try:
    MOV_CONVERT_TIMEOUT_SEC = int(os.environ.get("MOV_CONVERT_TIMEOUT_SEC", "7200") or 7200)
except Exception:
    MOV_CONVERT_TIMEOUT_SEC = 7200
MOV_CONVERT_TIMEOUT_SEC = max(60, min(21600, MOV_CONVERT_TIMEOUT_SEC))


def _mov_to_mp4(src: Path, dst: Path) -> None:
    """Convert MOV uploads to browser-friendly MP4/H.264."""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg not available for MOV conversion")

    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.stem}.{secrets.token_hex(6)}.tmp{dst.suffix}")
    try:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-map_metadata",
            "0",
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            MOV_CONVERT_PRESET,
            "-crf",
            str(MOV_CONVERT_CRF),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            MOV_CONVERT_AUDIO_BITRATE,
            "-movflags",
            "+faststart",
            str(tmp),
        ]
        subprocess.run(cmd, check=True, timeout=MOV_CONVERT_TIMEOUT_SEC)
        if not tmp.exists() or tmp.stat().st_size <= 0:
            raise RuntimeError("ffmpeg produced empty output")
        os.replace(tmp, dst)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
try:
    UPLOAD_FOLDER_SYNC_MAX_FILES = int(os.environ.get("UPLOAD_FOLDER_SYNC_MAX_FILES", "800") or 800)
except Exception:
    UPLOAD_FOLDER_SYNC_MAX_FILES = 800
UPLOAD_FOLDER_SYNC_MAX_FILES = max(50, min(10000, UPLOAD_FOLDER_SYNC_MAX_FILES))
try:
    UPLOAD_FOLDER_SYNC_PREVIEW_MAX_FILES = int(os.environ.get("UPLOAD_FOLDER_SYNC_PREVIEW_MAX_FILES", "120") or 120)
except Exception:
    UPLOAD_FOLDER_SYNC_PREVIEW_MAX_FILES = 120
UPLOAD_FOLDER_SYNC_PREVIEW_MAX_FILES = max(10, min(1000, UPLOAD_FOLDER_SYNC_PREVIEW_MAX_FILES))
try:
    UPLOAD_FOLDER_SYNC_SETTLE_SEC = float(os.environ.get("UPLOAD_FOLDER_SYNC_SETTLE_SEC", "1.0") or 1.0)
except Exception:
    UPLOAD_FOLDER_SYNC_SETTLE_SEC = 1.0
UPLOAD_FOLDER_SYNC_SETTLE_SEC = max(0.0, min(30.0, UPLOAD_FOLDER_SYNC_SETTLE_SEC))
try:
    UPLOAD_FOLDER_SYNC_TTL_SEC = float(os.environ.get("UPLOAD_FOLDER_SYNC_TTL_SEC", "2.0") or 2.0)
except Exception:
    UPLOAD_FOLDER_SYNC_TTL_SEC = 2.0
UPLOAD_FOLDER_SYNC_TTL_SEC = max(0.0, min(60.0, UPLOAD_FOLDER_SYNC_TTL_SEC))
try:
    DIRECT_UPLOAD_POSTPROCESS_BATCH_SIZE = int(os.environ.get("DIRECT_UPLOAD_POSTPROCESS_BATCH_SIZE", "8") or 8)
except Exception:
    DIRECT_UPLOAD_POSTPROCESS_BATCH_SIZE = 8
DIRECT_UPLOAD_POSTPROCESS_BATCH_SIZE = max(1, min(100, DIRECT_UPLOAD_POSTPROCESS_BATCH_SIZE))
try:
    DIRECT_UPLOAD_POSTPROCESS_ITEM_PAUSE_SEC = float(os.environ.get("DIRECT_UPLOAD_POSTPROCESS_ITEM_PAUSE_SEC", "0.04") or 0.04)
except Exception:
    DIRECT_UPLOAD_POSTPROCESS_ITEM_PAUSE_SEC = 0.04
DIRECT_UPLOAD_POSTPROCESS_ITEM_PAUSE_SEC = max(0.0, min(2.0, DIRECT_UPLOAD_POSTPROCESS_ITEM_PAUSE_SEC))
try:
    DIRECT_UPLOAD_POSTPROCESS_BATCH_PAUSE_SEC = float(os.environ.get("DIRECT_UPLOAD_POSTPROCESS_BATCH_PAUSE_SEC", "0.25") or 0.25)
except Exception:
    DIRECT_UPLOAD_POSTPROCESS_BATCH_PAUSE_SEC = 0.25
DIRECT_UPLOAD_POSTPROCESS_BATCH_PAUSE_SEC = max(0.0, min(10.0, DIRECT_UPLOAD_POSTPROCESS_BATCH_PAUSE_SEC))
UPLOAD_ALLOWED_EXTENSIONS_SETTING = "upload_allowed_extensions"
PHOTOFRAME_VIDEO_PREPARE_ENABLED = str(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_ENABLED", "1") or "1").strip().lower() not in {"0", "false", "no", "off"}
try:
    PHOTOFRAME_VIDEO_PREPARE_MAX_PER_SCOPE = int(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_MAX_PER_SCOPE", "80") or 80)
except Exception:
    PHOTOFRAME_VIDEO_PREPARE_MAX_PER_SCOPE = 80
PHOTOFRAME_VIDEO_PREPARE_MAX_PER_SCOPE = max(0, min(800, PHOTOFRAME_VIDEO_PREPARE_MAX_PER_SCOPE))
try:
    PHOTOFRAME_VIDEO_PREPARE_MAX_PER_FEED = int(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_MAX_PER_FEED", "24") or 24)
except Exception:
    PHOTOFRAME_VIDEO_PREPARE_MAX_PER_FEED = 24
PHOTOFRAME_VIDEO_PREPARE_MAX_PER_FEED = max(0, min(200, PHOTOFRAME_VIDEO_PREPARE_MAX_PER_FEED))
try:
    PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX = int(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX", "240") or 240)
except Exception:
    PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX = 240
PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX = max(0, min(5000, PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX))
PHOTOFRAME_VIDEO_PREPARE_REQUEUE_ON_STATUS = str(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_REQUEUE_ON_STATUS", "1") or "1").strip().lower() not in {"0", "false", "no", "off"}
try:
    PHOTOFRAME_VIDEO_PREPARE_REQUEUE_MAX = int(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_REQUEUE_MAX", "4") or 4)
except Exception:
    PHOTOFRAME_VIDEO_PREPARE_REQUEUE_MAX = 4
PHOTOFRAME_VIDEO_PREPARE_REQUEUE_MAX = max(1, min(24, PHOTOFRAME_VIDEO_PREPARE_REQUEUE_MAX))
PHOTOFRAME_VIDEO_PREPARE_PRESET = str(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_PRESET", "veryfast") or "veryfast").strip() or "veryfast"
try:
    PHOTOFRAME_VIDEO_PREPARE_CRF = int(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_CRF", "24") or 24)
except Exception:
    PHOTOFRAME_VIDEO_PREPARE_CRF = 24
PHOTOFRAME_VIDEO_PREPARE_CRF = max(18, min(36, PHOTOFRAME_VIDEO_PREPARE_CRF))
try:
    PHOTOFRAME_VIDEO_PREPARE_TIMEOUT_SEC = int(os.environ.get("PHOTOFRAME_VIDEO_PREPARE_TIMEOUT_SEC", "1800") or 1800)
except Exception:
    PHOTOFRAME_VIDEO_PREPARE_TIMEOUT_SEC = 1800
PHOTOFRAME_VIDEO_PREPARE_TIMEOUT_SEC = max(60, min(7200, PHOTOFRAME_VIDEO_PREPARE_TIMEOUT_SEC))
THUMB_SIZE = (600, 600)
FACE_THUMB_VERSION = 6
PHASH_MATCH_THRESHOLD = int(os.environ.get("PHASH_MATCH_THRESHOLD", "8"))
GEOCODE_ENABLE = os.environ.get("GEOCODE_ENABLE", "1") not in {"0", "false", "False"}
GEOCODE_EMAIL = os.environ.get("GEOCODE_EMAIL", "fjordlens@example.com")
GEOCODE_TIMEOUT = int(os.environ.get("GEOCODE_TIMEOUT", "12"))
GEOCODE_RETRIES = int(os.environ.get("GEOCODE_RETRIES", "3"))
GEOCODE_DELAY = float(os.environ.get("GEOCODE_DELAY", "1.0"))  # courteous delay per request
GEOCODE_PROVIDER = os.environ.get("GEOCODE_PROVIDER", "rg").strip().lower()
GEOCODE_LANG = os.environ.get("GEOCODE_LANG", "da").strip().lower()


app = Flask(__name__)
APP_BUILD_ID = int(time.time())


def _normalize_lang(value: Optional[str], default: str = LANG_DA) -> str:
    v = str(value or "").strip().lower()
    return v if v in LANG_CHOICES else default


def _request_ui_language() -> str:
    try:
        if getattr(current_user, "is_authenticated", False):
            return _normalize_lang(getattr(current_user, "ui_language", None), LANG_DA)
    except Exception:
        pass
    raw = str(request.headers.get("Accept-Language") or "")
    for part in raw.split(","):
        code = part.split(";", 1)[0].strip().lower()
        if code.startswith("en"):
            return LANG_EN
        if code.startswith("da"):
            return LANG_DA
    return LANG_DA


def _ui_text(key: str, lang: Optional[str] = None) -> str:
    chosen = _normalize_lang(lang or _request_ui_language(), LANG_DA)
    return TEMPLATE_I18N.get(chosen, TEMPLATE_I18N[LANG_DA]).get(key, TEMPLATE_I18N[LANG_DA].get(key, key))


@app.context_processor
def inject_template_i18n():
    lang = _request_ui_language()
    return {
        "ui_lang": lang,
        "tt": lambda key: _ui_text(str(key), lang),
        "app_build": APP_BUILD_ID,
    }


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response


@app.route("/robots.txt")
def robots_txt():
    for candidate in (
        DATA_DIR / "robots.txt",
        Path(__file__).parent / "static" / "robots.txt",
    ):
        if candidate.exists():
            content = candidate.read_text(encoding="utf-8")
            break
    else:
        content = "User-agent: *\nDisallow: /admin\nDisallow: /api\n"
    from flask import Response
    resp = Response(content, mimetype="text/plain")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


# --- iOS/Android Home Screen icons at well-known root URLs ---
def _png_response(data: bytes):
    from flask import Response
    resp = Response(data, mimetype="image/png")
    try:
        resp.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    except Exception:
        pass
    return resp


def _logo_icon_source_path() -> Optional[Path]:
    for path in (
        LOGOS_WEB_DIR / "apple-touch-icon.png",
        LOGOS_WEB_DIR / "android-chrome-512x512.png",
        LOGOS_WEB_DIR / "pwa-maskable-512x512.png",
        LOGOS_ICONS_DIR / "apple-touch-icon.png",
        LOGOS_ICONS_DIR / "pwa-maskable-512x512.png",
        LOGOS_MAIN_DIR / "fjordlens-app-icon-master.png",
    ):
        if path.exists():
            return path
    return None


def _serve_logo_png(path: Optional[Path], target: Optional[int] = None):
    if not path or not path.exists():
        return ("", 404)
    if target:
        img = Image.open(str(path)).convert("RGBA")
        img = img.resize((target, target), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return _png_response(buf.getvalue())
    resp = send_file(str(path), mimetype="image/png")
    try:
        resp.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    except Exception:
        pass
    return resp


def _serve_logo_file(path: Path, mimetype: str):
    if not path.exists():
        return ("", 404)
    resp = send_file(str(path), mimetype=mimetype)
    try:
        resp.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    except Exception:
        pass
    return resp


@app.route("/api/qr")
def api_qr():
    """Generate a QR code PNG for the provided text (admin UI use).
    Query params:
      - text: The content to encode (URL or text)
      - box:  Box size (pixels per module), default 8, 2..16
      - border: Quiet zone modules, default 2, 1..8
    """
    try:
        raw = str(request.args.get("text") or "").strip()
        if not raw:
            return jsonify({"ok": False, "error": "Missing text"}), 400
        if len(raw) > 2048:
            return jsonify({"ok": False, "error": "Text too long"}), 400
        try:
            box = int(request.args.get("box") or 8)
        except Exception:
            box = 8
        try:
            border = int(request.args.get("border") or 2)
        except Exception:
            border = 2
        box = max(2, min(16, box))
        border = max(1, min(8, border))
        # Build QR image
        try:
            qr = qrcode.QRCode(
                version=None,
                box_size=box,
                border=border,
            )
            qr.add_data(raw)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
        except Exception:
            # Fallback simple generator
            img = qrcode.make(raw)
        buf = io.BytesIO()
        try:
            img.save(buf, 'PNG')
        except Exception as e:
            return jsonify({"ok": False, "error": f"QR save failed: {e}"}), 500
        return _png_response(buf.getvalue())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
def apple_touch_icon():
    return _serve_logo_png(LOGOS_WEB_DIR / "apple-touch-icon.png")

@app.route("/apple-touch-icon-180x180.png")
def apple_touch_icon_180():
    return _serve_logo_png(_logo_icon_source_path(), 180)

@app.route("/apple-touch-icon-167x167.png")
def apple_touch_icon_167():
    return _serve_logo_png(_logo_icon_source_path(), 167)

@app.route("/apple-touch-icon-152x152.png")
def apple_touch_icon_152():
    return _serve_logo_png(_logo_icon_source_path(), 152)

@app.route("/apple-touch-icon-120x120.png")
def apple_touch_icon_120():
    return _serve_logo_png(_logo_icon_source_path(), 120)

@app.route("/icon-192.png")
def icon_192():
    return _serve_logo_png(LOGOS_WEB_DIR / "android-chrome-192x192.png")


@app.route("/favicon-32x32.png")
def favicon_32_png():
    return _serve_logo_png(LOGOS_WEB_DIR / "favicon-32x32.png")


@app.route("/favicon-16x16.png")
def favicon_16_png():
    return _serve_logo_png(LOGOS_WEB_DIR / "favicon-16x16.png")

@app.route("/favicon.ico")
def favicon_ico():
    ico = LOGOS_WEB_DIR / "favicon.ico"
    if ico.exists():
        return _serve_logo_file(ico, "image/x-icon")
    return _serve_logo_png(LOGOS_WEB_DIR / "favicon-32x32.png")


@app.route("/site.webmanifest")
def site_webmanifest():
    return _serve_logo_file(LOGOS_WEB_DIR / "site.webmanifest", "application/manifest+json")


@app.route("/manifest.webmanifest")
def manifest_webmanifest():
    return _serve_logo_file(LOGOS_WEB_DIR / "manifest.webmanifest", "application/manifest+json")


@app.route("/browserconfig.xml")
def browserconfig_xml():
    return _serve_logo_file(LOGOS_WEB_DIR / "browserconfig.xml", "application/xml")

# --- Console color support (for Windows terminals and Docker logs) ---
ANSI_RESET = "\033[0m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"
ANSI_DIM = "\033[90m"

def _enable_windows_ansi() -> None:
    try:
        if os.name == "nt":
            import ctypes  # type: ignore
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            h = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        # Best-effort only; ignore if not a real console
        pass

_enable_windows_ansi()

def _classify_log_level(event: str, data: Dict[str, Any]) -> str:
    ev = (event or "").lower()
    if data.get("error") or ev == "error" or ev.endswith("_error") or ev.endswith("_fail") or ev == "ai_http_error":
        return "err"
    if ev in {"skip_unchanged", "no_new", "missing"} or ev.endswith("_check") or ("retry" in ev) or ("skip" in ev):
        return "warn"
    if ev.endswith("_done") or ev.endswith("_saved") or ev.endswith("_ok") or ev in {"indexed", "faces_detect", "faces_index_done", "face_saved", "upload_indexed", "rethumb_ok"}:
        return "ok"
    return "info"


def _get_secret_key() -> bytes:
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        try:
            return env_key.encode("utf-8")
        except Exception:
            return b"fjordlens-dev-secret-key"
    # Persist a random key under DATA_DIR so all workers share the same secret
    try:
        key_file = DATA_DIR / "secret.key"
        if key_file.exists():
            return key_file.read_bytes().strip()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key = os.urandom(32)
        key_file.write_bytes(key)
        return key
    except Exception:
        return b"fjordlens-dev-secret-key"


app.secret_key = _get_secret_key()

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Global scan control
scan_stop_event = threading.Event()
UPLOAD_POSTPROCESS_STOP_EVENT = threading.Event()
STOP_ALL_PROCESS_COOLDOWN_UNTIL = 0.0
UPLOAD_FOLDER_SYNC_LOCK = threading.Lock()
UPLOAD_FOLDER_SYNC_RUNNING: set[str] = set()
UPLOAD_FOLDER_SYNC_LAST_AT: Dict[str, float] = {}
DIRECT_UPLOAD_POSTPROCESS_USER = "__direct_uploads__"

# Simple in-memory log buffer for UI polling
from collections import deque
LOG_BUFFER: deque[Dict[str, Any]] = deque(maxlen=1000)
LOG_SEQ: int = 0
UPLOAD_PENDING_BY_USER: Dict[str, list[str]] = {}
UPLOAD_PENDING_LOCK = threading.Lock()
UPLOAD_POSTPROCESS_BY_USER: Dict[str, Dict[str, Any]] = {}
UPLOAD_POSTPROCESS_LOCK = threading.Lock()
UPLOAD_TRANSFER_ACTIVE_BY_USER: Dict[str, float] = {}
UPLOAD_TRANSFER_LOCK = threading.Lock()
UPLOAD_TRANSFER_TTL_SEC = 180.0
DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS: set[str] = set()
DIRECT_UPLOAD_POSTPROCESS_ACTIVE_LOCK = threading.Lock()
PHOTOFRAME_TOKENS_LOCK = threading.RLock()
PHOTOFRAME_VIDEO_PREPARE_QUEUE: "queue.Queue[str]" = queue.Queue()
PHOTOFRAME_VIDEO_PREPARE_LOCK = threading.Lock()
PHOTOFRAME_VIDEO_PREPARE_QUEUED: set[str] = set()
PHOTOFRAME_VIDEO_PREPARE_WORKER_STARTED = False


def log_event(event: str, **data: Any) -> None:
    global LOG_SEQ
    LOG_SEQ += 1
    t = now_iso()
    LOG_BUFFER.append({"id": LOG_SEQ, "t": t, "event": event, **data})
    # Console output with colors and proper newlines
    try:
        lvl = _classify_log_level(event, data)
        color = ANSI_DIM
        if lvl == "ok":
            color = ANSI_GREEN
        elif lvl == "warn":
            color = ANSI_YELLOW
        elif lvl == "err":
            color = ANSI_RED
        # Compact key=value payload
        parts = []
        for k, v in data.items():
            if v is None:
                continue
            try:
                if isinstance(v, (dict, list)):
                    sv = json.dumps(v, ensure_ascii=False)
                else:
                    sv = str(v)
            except Exception:
                sv = str(v)
            # keep lines readable
            if len(sv) > 300:
                sv = sv[:297] + "..."
            parts.append(f"{k}={sv}")
        extra = (" " + " ".join(parts)) if parts else ""
        print(f"{color}[{t}] {event}{extra}{ANSI_RESET}")
    except Exception:
        # Never let console formatting break logging
        pass


# --- AI helpers (CLIP service) ---
_AI_HEALTH_CACHE_TTL_SEC = 2.0
_ai_health_cache_lock = threading.Lock()
_ai_health_cache_at = 0.0
_ai_health_cache_payload: Dict[str, Any] = {"ok": False}


def _ai_health() -> dict:
    try:
        r = requests.get(f"{AI_URL}/health", timeout=5)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {"ok": False}


def _ai_health_cached(force: bool = False) -> Dict[str, Any]:
    """Fetch AI health with a short cache to avoid duplicate UI polling bursts."""
    global _ai_health_cache_at, _ai_health_cache_payload
    now = time.time()
    with _ai_health_cache_lock:
        if (not force) and _ai_health_cache_payload and (now - _ai_health_cache_at) < _AI_HEALTH_CACHE_TTL_SEC:
            return dict(_ai_health_cache_payload)

    payload = _ai_health()
    with _ai_health_cache_lock:
        _ai_health_cache_payload = dict(payload or {"ok": False})
        _ai_health_cache_at = now
        return dict(_ai_health_cache_payload)


def _runtime_device_label(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return "unknown"
    if raw in {"gpu", "cuda"} or raw.startswith("cuda"):
        return "gpu"
    if raw == "cpu":
        return "cpu"
    return raw


def _ai_runtime_info() -> Dict[str, Any]:
    health = _ai_health_cached()
    ai_device_raw = health.get("device")
    face_device_raw = health.get("face_device") or ai_device_raw
    qwen_device_raw = health.get("qwen_device") or ai_device_raw
    return {
        "service_ok": bool(health.get("ok")),
        "ai_device": _runtime_device_label(ai_device_raw),
        "face_device": _runtime_device_label(face_device_raw),
        "qwen_device": _runtime_device_label(qwen_device_raw),
        "ai_device_raw": ai_device_raw,
        "face_device_raw": face_device_raw,
        "qwen_device_raw": qwen_device_raw,
    }


def _ai_embed_text(text: str) -> Optional[list[float]]:
    try:
        r = requests.post(f"{AI_URL}/embed/text", json={"text": text}, timeout=20)
        if r.ok:
            return r.json().get("embedding")
    except Exception:
        pass
    return None


def _ai_expand_query_tags(text: str, language: Optional[str] = None) -> list[str]:
    if not AI_QUERY_EXPAND_ENABLED or not text or not AI_URL:
        return []
    payload = {"text": str(text), "language": str(language or "").strip() or None}
    try:
        r = requests.post(f"{AI_URL}/query/expand", json=payload, timeout=8)
        if r.ok:
            js = r.json() or {}
            tags = js.get("tags") or []
            if isinstance(tags, list):
                return [t for t in _normalize_ai_desc_tags(tags, max_tags=24) if t]
    except Exception:
        pass
    return []


def _ai_embed_image_path(path: Path) -> Optional[list[float]]:
    try:
        # Use a browser/AI-friendly copy for HEIC/HEIF
        rel_guess = None
        try:
            rel_guess = str(path.relative_to(PHOTO_DIR)).replace("\\", "/")
        except Exception:
            rel_guess = path.name
        ai_src = ensure_viewable_copy(path, rel_guess)
        with ai_src.open("rb") as f:
            # Use generic content-type to avoid server rejections
            files = {"file": (ai_src.name, f, "application/octet-stream")}
            r = requests.post(f"{AI_URL}/embed/image", files=files, timeout=60)
        if r.ok:
            try:
                return r.json().get("embedding")
            except Exception as e:
                log_event("ai_http_error", rel_path=str(path), error=f"json:{e}")
        else:
            detail = ""
            try:
                body = " ".join(str(r.text or "").split())
                if body:
                    detail = f" body:{body[:240]}"
            except Exception:
                detail = ""
            log_event("ai_http_error", rel_path=str(path), error=f"status:{r.status_code}{detail}")
    except Exception as e:
        log_event("ai_http_error", rel_path=str(path), error=str(e))
    return None


def _ai_tag_parts(value: Any) -> list[str]:
    return [p for p in re.split(r"[,;|]|\s+[–—-]\s+", str(value or "")) if p]


_AI_DESC_TAG_TRANSLATIONS: Dict[str, str] = {
    "activity": "aktivitet",
    "baby": "baby",
    "boy": "dreng",
    "child": "barn",
    "children": "børn",
    "family album": "familiealbum",
    "girl": "pige",
    "happy": "glad",
    "image": "billede",
    "january": "januar",
    "kid": "barn",
    "lady": "dame",
    "little": "lille",
    "man": "mand",
    "people": "personer",
    "person": "person",
    "photo": "foto",
    "picture": "foto",
    "sitting": "sidder",
    "small": "lille",
    "smile": "smiler",
    "smiling": "smiler",
    "woman": "kvinde",
}

_AI_DESC_TAG_STOPWORDS: set[str] = {
    "a",
    "an",
    "and",
    "at",
    "at være",
    "det",
    "der",
    "en",
    "er",
    "et",
    "for",
    "i",
    "jeg",
    "med",
    "of",
    "og",
    "on",
    "på",
    "som",
    "the",
    "til",
    "to",
    "være",
    "with",
}


def _clean_ai_tag(value: Any) -> str:
    tag = _repair_mojibake(str(value or "")).strip().lower()
    tag = tag.strip(" \t\r\n\"'`[]{}()")
    tag = re.sub(r"\s+", " ", tag)
    tag = _AI_DESC_TAG_TRANSLATIONS.get(tag, tag)
    if (
        not tag
        or len(tag) > 40
        or any(ch in tag for ch in "\n\r\t")
        or tag in _AI_DESC_TAG_STOPWORDS
        or tag in {"caption", "tags", "json", "null", "none"}
    ):
        return ""
    return tag


def _normalize_ai_desc_tags(value: Any, max_tags: int = 16) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    if isinstance(value, str):
        parts = _ai_tag_parts(value)
    elif isinstance(value, (list, tuple, set)):
        parts = []
        for item in value:
            parts.extend(_ai_tag_parts(item))
    else:
        parts = []
    for part in parts:
        tag = _clean_ai_tag(part)
        key = _fold_danish(tag)
        if not tag or key in seen:
            continue
        seen.add(key)
        out.append(tag)
        if len(out) >= max_tags:
            break
    return out


def _extract_ai_desc_json_object(value: Any) -> Optional[Dict[str, Any]]:
    raw = str(value or "").strip()
    if not raw or "{" not in raw or "}" not in raw:
        return None
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(raw[start : end + 1])
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _caption_tags_from_ai_desc_payload(payload: Dict[str, Any]) -> tuple[str, list[str]]:
    caption = ""
    for key in ("caption", "kort_beskrivelse", "description", "beskrivelse"):
        text = _repair_mojibake(str(payload.get(key) or "")).strip()
        if text:
            caption = text
            break
    if not caption:
        parts = [
            _repair_mojibake(str(payload.get("kort_beskrivelse") or "")).strip(),
            _repair_mojibake(str(payload.get("hvad_sker_der") or "")).strip(),
        ]
        caption = " ".join(part for part in parts if part and part != "-").strip()

    tag_values: list[Any] = []
    for key in ("tags", "samlede_soegeord", "søgeord", "soegeord", "keywords"):
        value = payload.get(key)
        if value:
            tag_values.append(value)

    people = payload.get("mennesker")
    if isinstance(people, dict):
        for key in ("pige_dreng_vurdering", "koen_og_alder", "soegeord_personer"):
            value = people.get(key)
            if value:
                tag_values.append(value)
        persons = people.get("personer")
        if isinstance(persons, list):
            for person in persons:
                if not isinstance(person, dict):
                    continue
                for key in ("rolle_i_billedet", "alderstrin", "visuel_koensvurdering", "soegeord"):
                    value = person.get(key)
                    if value:
                        tag_values.append(value)

    return caption, _normalize_ai_desc_tags(tag_values, max_tags=96)


def _json_list_or_empty(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, (tuple, set)):
        return list(raw)
    if raw in (None, "", "null"):
        return []
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _ai_desc_has_content(tags_raw: Any, caption_raw: Any = None) -> bool:
    if str(caption_raw or "").strip():
        return True
    return bool(_normalize_ai_desc_tags(_json_list_or_empty(tags_raw)))


def _store_photo_ai_description(conn: sqlite3.Connection, photo_id: int, tags: list[str], caption: Optional[str]) -> None:
    tag_source: list[Any] = list(tags or [])
    clean_caption_text = _repair_mojibake(str(caption or "")).strip()
    embedded_payload = _extract_ai_desc_json_object(clean_caption_text)
    if embedded_payload:
        embedded_caption, embedded_tags = _caption_tags_from_ai_desc_payload(embedded_payload)
        if embedded_caption:
            clean_caption_text = embedded_caption
        tag_source.extend(embedded_tags)

    clean_tags = _normalize_ai_desc_tags(tag_source, max_tags=96)
    clean_caption = clean_caption_text or None

    prev_ai_tags: list[str] = []
    prev_desc_tags: list[str] = []
    prev_meta: Dict[str, Any] = {}
    try:
        cur = conn.execute("SELECT ai_tags, metadata_json FROM photos WHERE id=?", (photo_id,)).fetchone()
        if cur:
            prev_ai_tags = _normalize_ai_desc_tags(_json_list_or_empty(cur["ai_tags"]), max_tags=96)
            prev_meta = _json_object(cur["metadata_json"])
            prev_ai_meta = prev_meta.get("ai") if isinstance(prev_meta.get("ai"), dict) else {}
            prev_desc_tags = _normalize_ai_desc_tags(prev_ai_meta.get("desc_tags"), max_tags=96)
    except Exception:
        pass

    prev_desc_keys = {_fold_danish(tag) for tag in prev_desc_tags}
    base_ai_tags = [tag for tag in prev_ai_tags if _fold_danish(tag) not in prev_desc_keys]
    merged_ai_tags = _normalize_ai_desc_tags([*base_ai_tags, *clean_tags], max_tags=128)
    meta = dict(prev_meta or {})
    ai_meta = dict(meta.get("ai") or {})
    ai_meta["tags"] = merged_ai_tags
    ai_meta["desc_tags"] = clean_tags
    ai_meta["desc_caption"] = clean_caption
    meta["ai"] = ai_meta

    conn.execute(
        "UPDATE photos SET ai_tags=?, ai_desc_tags=?, ai_desc_caption=?, metadata_json=? WHERE id=?",
        (
            json.dumps(merged_ai_tags, ensure_ascii=False),
            json.dumps(clean_tags, ensure_ascii=False),
            clean_caption,
            json.dumps(meta, ensure_ascii=False),
            photo_id,
        ),
    )


def _ai_describe_image_path(path: Path) -> Optional[Dict[str, Any]]:
    try:
        rel_guess = None
        try:
            rel_guess = str(path.relative_to(PHOTO_DIR)).replace("\\", "/")
        except Exception:
            rel_guess = path.name
        ai_src = ensure_viewable_copy(path, rel_guess)
        with ai_src.open("rb") as f:
            files = {"file": (ai_src.name, f, "application/octet-stream")}
            r = requests.post(f"{AI_URL}/describe/image", files=files, timeout=AI_DESC_REQUEST_TIMEOUT_SEC)
        if r.ok:
            js = r.json() or {}
            caption = str(js.get("caption") or "").strip()
            tags = _normalize_ai_desc_tags(js.get("tags"), max_tags=96)
            if not caption and not tags:
                return None
            return {
                "caption": caption or None,
                "tags": tags,
            }
        detail = ""
        body = ""
        try:
            body = " ".join(str(r.text or "").split())
            if body:
                detail = f" body:{body[:240]}"
        except Exception:
            detail = ""
            body = ""
        err = f"describe_status:{r.status_code}{detail}"
        log_event("ai_http_error", rel_path=str(path), error=err)
        if _is_ai_describe_runtime_error(int(r.status_code), body):
            raise AiDescribeRuntimeUnavailable(err)
    except AiDescribeRuntimeUnavailable:
        raise
    except Exception as e:
        log_event("ai_http_error", rel_path=str(path), error=f"describe_error:{e}")
    return None


class AiDescribeRuntimeUnavailable(RuntimeError):
    pass


def _is_ai_describe_runtime_error(status_code: int, body: str) -> bool:
    text = str(body or "").lower()
    if int(status_code or 0) < 500:
        return False
    needles = (
        "describe_image_failed",
        "cuda_load_failed",
        "quantize",
        "bitsandbytes",
        "out of memory",
        "dispatched on the cpu or the disk",
        "qwen",
    )
    return any(n in text for n in needles)


def _ai_stop_description_runtime(force: bool = False) -> Dict[str, Any]:
    try:
        r = requests.post(
            f"{AI_URL}/describe/stop",
            params={"hard": "1" if force else "0"},
            timeout=3,
        )
        detail: Dict[str, Any] = {"ok": bool(r.ok), "status": int(r.status_code)}
        try:
            detail["body"] = r.json()
        except Exception:
            body = str(r.text or "").strip()
            if body:
                detail["body"] = body[:240]
        return detail
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:240]}


def _ai_detect_faces_path(path: Path) -> Optional[list[Dict[str, Any]]]:
    """Send a viewable copy of the image to AI service for face detection/embeddings."""
    try:
        rel_guess = None
        try:
            rel_guess = str(path.relative_to(PHOTO_DIR)).replace("\\", "/")
        except Exception:
            rel_guess = path.name
        ai_src = ensure_viewable_copy(path, rel_guess)
        with ai_src.open("rb") as f:
            files = {"file": (ai_src.name, f, "application/octet-stream")}
            r = requests.post(f"{AI_URL}/faces/detect", files=files, timeout=90)
        if r.ok:
            js = r.json() or {}
            if js.get("ok") and isinstance(js.get("faces"), list):
                return js.get("faces")
    except Exception as e:
        log_event("error", rel_path=str(path), error=f"ai_faces: {e}")
    return None


def _ai_detect_faces_bytes(data: bytes, filename: str = "frame.jpg") -> Optional[list[Dict[str, Any]]]:
    """Send image bytes to AI service for face detection/embeddings."""
    try:
        files = {"file": (filename, data, "application/octet-stream")}
        r = requests.post(f"{AI_URL}/faces/detect", files=files, timeout=90)
        if r.ok:
            js = r.json() or {}
            if js.get("ok") and isinstance(js.get("faces"), list):
                return js.get("faces")
        else:
            log_event("ai_http_error", file=filename, error=f"status:{r.status_code}")
    except Exception as e:
        log_event("error", file=filename, error=f"ai_faces_bytes: {e}")
    return None


def _video_duration_seconds(path: Path) -> Optional[float]:
    """Get video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        r = subprocess.run(cmd, check=True, capture_output=True, text=True)
        val = float((r.stdout or "").strip())
        return val if val > 0 else None
    except Exception:
        return None


def _video_face_sample_timestamps(path: Path, rel_path: str) -> tuple[Optional[float], list[float]]:
    """Build sampling timestamps for video face detection."""
    duration = _video_duration_seconds(path)
    start = max(0.0, VIDEO_FACE_SAMPLE_START_SEC)
    interval = max(0.5, VIDEO_FACE_SAMPLE_INTERVAL_SEC)
    max_frames = max(1, VIDEO_FACE_SAMPLE_MAX_FRAMES)

    if not duration:
        ts = [start]
        log_event("faces_video_sampling", rel_path=rel_path, duration=None, samples=ts)
        return None, ts

    ts: list[float] = []
    t = start
    while t < duration and len(ts) < max_frames:
        ts.append(round(t, 3))
        t += interval

    if not ts:
        fallback = max(0.0, min(start, duration * 0.5))
        ts = [round(fallback, 3)]

    tail = max(0.0, duration - 0.2)
    if len(ts) < max_frames and tail > ts[-1] + (interval * 0.5):
        ts.append(round(tail, 3))

    log_event("faces_video_sampling", rel_path=rel_path, duration=round(duration, 2), sample_count=len(ts), samples=ts)
    return duration, ts


def _extract_video_frame_bytes(path: Path, rel_path: str, at_sec: float) -> Optional[bytes]:
    """Extract one JPEG frame from video at a timestamp."""
    target_sec = max(0.0, float(at_sec or 0.0))
    last_error: Optional[str] = None
    try:
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "face_frame.jpg"
            commands = [
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", f"{target_sec:.3f}", "-i", str(path),
                    "-frames:v", "1",
                    "-q:v", "3",
                    str(out_path),
                ],
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(path),
                    "-ss", f"{target_sec:.3f}",
                    "-frames:v", "1",
                    "-q:v", "3",
                    str(out_path),
                ],
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(path),
                    "-frames:v", "1",
                    "-q:v", "3",
                    str(out_path),
                ],
            ]

            for cmd in commands:
                try:
                    if out_path.exists():
                        out_path.unlink(missing_ok=True)
                    subprocess.run(cmd, check=True, timeout=25)
                    if out_path.exists() and out_path.stat().st_size > 0:
                        return out_path.read_bytes()
                except Exception as e:
                    last_error = str(e)
                    continue
    except Exception as e:
        last_error = str(e)

    if last_error:
        log_event("faces_video_frame_fail", rel_path=rel_path, at_sec=round(target_sec, 2), error=last_error)
    return None


def _dedupe_faces_by_embedding(faces: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Remove repeated detections of the same person across nearby video frames."""
    if not faces:
        return []
    thr = max(0.0, min(1.0, VIDEO_FACE_DEDUPE_THRESHOLD))
    ranked = sorted(faces, key=lambda f: float(f.get("confidence") or 0.0), reverse=True)
    kept: list[Dict[str, Any]] = []
    kept_embs: list[list[float]] = []
    for fc in ranked:
        emb = fc.get("embedding") or []
        if not emb:
            kept.append(fc)
            continue
        duplicate = False
        for ref in kept_embs:
            if _cosine(emb, ref) >= thr:
                duplicate = True
                break
        if duplicate:
            continue
        kept.append(fc)
        kept_embs.append(emb)
    return kept


def _ai_detect_faces_video_path(path: Path, rel_path: str) -> list[Dict[str, Any]]:
    """Detect faces from sampled video frames and return deduplicated detections."""
    _, timestamps = _video_face_sample_timestamps(path, rel_path)
    all_faces: list[Dict[str, Any]] = []
    frames_ok = 0
    for sec in timestamps:
        frame_bytes = _extract_video_frame_bytes(path, rel_path, sec)
        if not frame_bytes:
            continue
        frames_ok += 1
        faces = _ai_detect_faces_bytes(frame_bytes, filename=f"{path.stem}_t{sec:.2f}.jpg") or []
        log_event("faces_video_frame_detect", rel_path=rel_path, at_sec=round(sec, 2), count=len(faces))
        for fc in faces:
            if isinstance(fc, dict):
                fc["frame_sec"] = sec
                all_faces.append(fc)
    unique_faces = _dedupe_faces_by_embedding(all_faces)
    log_event(
        "faces_video_detect_done",
        rel_path=rel_path,
        sampled_frames=len(timestamps),
        decoded_frames=frames_ok,
        faces_total=len(all_faces),
        faces_unique=len(unique_faces),
    )
    return unique_faces


def _find_or_create_person_id(conn: sqlite3.Connection, emb: list[float]) -> tuple[int, bool, float]:
    """Return (person_id, created_new, score).
    1) Try matching against person centroids (if available)
    2) Fall back to nearest single-face embedding
    3) If below threshold, create new 'Ukendt-*' person
    """
    # 1) Try person centroids first (fewer comparisons; reflects prior merges = training)
    best_pid: Optional[int] = None
    best_score = -1.0
    try:
        rows = conn.execute("SELECT id, centroid_json FROM people WHERE centroid_json IS NOT NULL AND TRIM(centroid_json) != ''").fetchall()
        for row in rows:
            try:
                cvec = json.loads(row["centroid_json"]) if row["centroid_json"] else None
            except Exception:
                cvec = None
            if not cvec:
                continue
            sc = _cosine(emb, cvec)
            if sc > best_score:
                best_score = sc
                best_pid = int(row["id"]) if row["id"] is not None else None
    except Exception:
        pass

    if best_pid is not None and best_score >= FACE_MATCH_THRESHOLD_CENTROID:
        return int(best_pid), False, float(best_score)

    # 2) Fallback: nearest neighbor among all face embeddings
    best_pid = None
    best_score = -1.0
    try:
        rows = conn.execute("SELECT embedding_json, person_id FROM faces WHERE embedding_json IS NOT NULL").fetchall()
        for row in rows:
            try:
                vec = json.loads(row["embedding_json"]) if row["embedding_json"] else None
            except Exception:
                vec = None
            if not vec:
                continue
            sc = _cosine(emb, vec)
            if sc > best_score:
                best_score = sc
                best_pid = row["person_id"]
    except Exception:
        best_pid = None
        best_score = -1.0

    if best_pid is not None and best_score >= FACE_MATCH_THRESHOLD:
        return int(best_pid), False, float(best_score)

    # Create a new 'unknown' person with unique name
    base = "Ukendt"
    i = 1
    while True:
        name = f"{base}-{i}"
        try:
            cur = conn.execute("INSERT INTO people(name, created_at) VALUES(?,?)", (name, now_iso()))
            conn.commit()
            lr = getattr(cur, "lastrowid", None)
            pid_new = int(lr) if lr is not None else int(conn.execute("SELECT id FROM people WHERE name=? ORDER BY id DESC LIMIT 1", (name,)).fetchone()["id"])
            return pid_new, True, float(best_score)
        except Exception:
            i += 1


def _compute_centroid(vectors: list[list[float]]) -> Optional[list[float]]:
    try:
        if not vectors:
            return None
        L = max((len(v) for v in vectors if isinstance(v, list)), default=0)
        if L <= 0:
            return None
        acc = [0.0] * L
        n = 0
        for v in vectors:
            if not isinstance(v, list) or len(v) != L:
                continue
            for i, x in enumerate(v):
                acc[i] += float(x or 0.0)
            n += 1
        if n <= 0:
            return None
        return [x / float(n) for x in acc]
    except Exception:
        return None


def _recompute_person_centroid(conn: sqlite3.Connection, pid: int) -> dict:
    """Recompute centroid from all face embeddings for a given person and store on people.centroid_json."""
    try:
        rows = conn.execute("SELECT embedding_json FROM faces WHERE person_id=? AND embedding_json IS NOT NULL", (pid,)).fetchall()
        vecs: list[list[float]] = []
        for r in rows:
            try:
                v = json.loads(r["embedding_json"]) if r["embedding_json"] else None
            except Exception:
                v = None
            if isinstance(v, list) and v:
                vecs.append([float(x or 0.0) for x in v])
        centroid = _compute_centroid(vecs)
        if centroid is None:
            conn.execute("UPDATE people SET centroid_json=NULL WHERE id=?", (pid,))
            conn.commit()
            return {"ok": True, "id": pid, "faces": 0, "updated": False}
        conn.execute("UPDATE people SET centroid_json=? WHERE id=?", (json.dumps(centroid), pid))
        conn.commit()
        return {"ok": True, "id": pid, "faces": len(vecs), "updated": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _load_person_centroids(conn: sqlite3.Connection) -> list[tuple[int, list[float]]]:
    """Return list of (person_id, centroid_vec). Recompute missing on the fly."""
    out: list[tuple[int, list[float]]] = []
    try:
        rows = conn.execute("SELECT id, centroid_json FROM people").fetchall()
        for r in rows:
            pid = int(r["id"]) if r and r["id"] is not None else None
            if pid is None:
                continue
            try:
                c = json.loads(r["centroid_json"]) if r["centroid_json"] else None
            except Exception:
                c = None
            if not (isinstance(c, list) and c):
                # Recompute on demand
                res = _recompute_person_centroid(conn, pid)
                if res.get("ok") and res.get("updated"):
                    c = json.loads(conn.execute("SELECT centroid_json FROM people WHERE id=?", (pid,)).fetchone()["centroid_json"])  # type: ignore[index]
            if isinstance(c, list) and c:
                out.append((pid, [float(x or 0.0) for x in c]))
    except Exception:
        pass
    return out


def index_faces_for_photo(rel_path: str) -> int:
    """Detect faces for a photo/video and store into DB; updates people_count."""
    try:
        disk_path = _disk_path_from_rel_path(rel_path)
        if not disk_path.exists():
            return 0
        log_event("faces_index_start", rel_path=rel_path)
        is_video = disk_path.suffix.lower() in VIDEO_EXTS
        if is_video:
            faces = _ai_detect_faces_video_path(disk_path, rel_path)
            log_event("faces_detect", rel_path=rel_path, media="video", count=len(faces))
        else:
            faces = _ai_detect_faces_path(disk_path) or []
            log_event("faces_detect", rel_path=rel_path, media="image", count=len(faces))
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id, metadata_json FROM photos WHERE rel_path=?", (rel_path,)).fetchone()
            if not row:
                return 0
            photo_id = int(row["id"])
            # Clear previous faces for this photo (re-index)
            try:
                conn.execute("DELETE FROM faces WHERE photo_id=?", (photo_id,))
                conn.commit()
            except Exception:
                pass
            count = 0
            created_new = 0
            matched_existing = 0
            for fc in faces:
                emb = fc.get("embedding") or []
                bbox = fc.get("bbox") or [0, 0, 0, 0]
                try:
                    x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
                    bx, by = max(0, x1), max(0, y1)
                    bw, bh = max(0, x2 - x1), max(0, y2 - y1)
                except Exception:
                    bx = by = bw = bh = 0
                try:
                    if emb:
                        pid, created, score = _find_or_create_person_id(conn, emb)
                        if created:
                            created_new += 1
                        else:
                            matched_existing += 1
                    else:
                        pid, created, score = (None, False, -1.0)
                except Exception:
                    pid, created, score = (None, False, -1.0)
                try:
                    frame_sec_val = None
                    try:
                        if fc.get("frame_sec") is not None:
                            frame_sec_val = max(0.0, float(fc.get("frame_sec")))
                    except Exception:
                        frame_sec_val = None
                    conn.execute(
                        """
                        INSERT INTO faces(photo_id, person_id, bbox_x, bbox_y, bbox_w, bbox_h, embedding_json, confidence, frame_sec, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            photo_id,
                            pid,
                            bx, by, bw, bh,
                            json.dumps(emb, ensure_ascii=False),
                            float(fc.get("confidence") or 1.0),
                            frame_sec_val,
                            now_iso(),
                        ),
                    )
                    count += 1
                    log_event(
                        "face_saved",
                        rel_path=rel_path,
                        photo_id=photo_id,
                        person_id=pid,
                        bbox=[bx, by, bw, bh],
                        score=score,
                        frame_sec=fc.get("frame_sec"),
                    )
                except Exception as e:
                    log_event("error", rel_path=rel_path, error=f"face_insert: {e}")
            try:
                conn.execute("UPDATE photos SET people_count=?, faces_indexed_at=? WHERE id=?", (count, now_iso(), photo_id))
                conn.commit()
            except Exception:
                pass
            log_event("faces_index_done", rel_path=rel_path, faces=count, matched=matched_existing, created=created_new)
            # Optional: update centroids for any persons touched in this photo
            try:
                pids = [int(r["person_id"]) for r in conn.execute("SELECT DISTINCT person_id FROM faces WHERE photo_id=? AND person_id IS NOT NULL", (photo_id,)).fetchall()]
            except Exception:
                pids = []
            for pid in pids:
                try:
                    _recompute_person_centroid(conn, int(pid))
                except Exception:
                    pass
            return int(count)
    except Exception as e:
        log_event("error", rel_path=rel_path, error=f"index_faces_for_photo: {e}")
        return 0


    


# Zero-shot labels (initial simple vocabulary; can expand/customize later)
AI_LABELS: list[str] = [
    "person", "man", "woman", "child", "baby",
    "dog", "cat", "bird", "horse",
    "car", "bicycle", "motorcycle", "bus", "train", "boat", "airplane",
    "tree", "flower", "sky", "clouds", "sunset", "beach", "sea", "mountain", "snow", "forest", "city", "building", "house", "road", "street", "lake", "river",
    "food", "cake", "pizza", "drink", "coffee", "beer", "wine",
    "phone", "laptop", "computer", "keyboard", "book", "document",
    "lamp", "chair", "table", "bed", "sofa",
]
_LABEL_VECS: Optional[list[list[float]]] = None


def _ensure_label_vecs() -> list[list[float]]:
    global _LABEL_VECS
    if _LABEL_VECS is not None:
        return _LABEL_VECS
    vecs: list[list[float]] = []
    for t in AI_LABELS:
        v = _ai_embed_text(t)
        if v:
            vecs.append(v)
        else:
            vecs.append([0.0])
    _LABEL_VECS = vecs
    return vecs


def _classify_labels(img_vec: list[float], top_k: int = 5, thr: float = 0.24) -> list[str]:
    try:
        label_vecs = _ensure_label_vecs()
        scores = []
        for idx, lv in enumerate(label_vecs):
            sc = _cosine(img_vec, lv)
            scores.append((sc, idx))
        scores.sort(key=lambda x: x[0], reverse=True)
        out: list[str] = []
        for sc, idx in scores[: top_k * 2]:  # check a bit wider then filter by thr
            if sc >= thr:
                out.append(AI_LABELS[idx])
            if len(out) >= top_k:
                break
        return out
    except Exception:
        return []


AI_DESC_PROMPTS: list[Dict[str, Any]] = [
    {"prompt": "people swimming in water", "tags": ["personer", "svømning", "vand"]},
    {"prompt": "a person swimming at the beach", "tags": ["personer", "svømning", "strand"]},
    {"prompt": "a person running outdoors", "tags": ["personer", "løb", "udendørs"]},
    {"prompt": "a person riding a bicycle", "tags": ["personer", "cykling"]},
    {"prompt": "people hiking in nature", "tags": ["personer", "natur", "vandring"]},
    {"prompt": "a family having dinner", "tags": ["familie", "mad"]},
    {"prompt": "people on a beach", "tags": ["personer", "strand"]},
    {"prompt": "a person in the sea", "tags": ["personer", "hav", "vand"]},
    {"prompt": "a child on a swing at a playground", "tags": ["barn", "gynge", "gynger", "legeplads"]},
    {"prompt": "a girl swinging on a swing", "tags": ["pige", "barn", "gynge", "gynger"]},
    {"prompt": "a child playing on a playground slide", "tags": ["barn", "legeplads", "rutsjebane", "leger"]},
    {"prompt": "an indoor photo", "tags": ["indendørs"]},
    {"prompt": "an outdoor photo", "tags": ["udendørs"]},
]
_DESC_PROMPT_VECS: Optional[list[Tuple[str, list[str], list[float]]]] = None


def _ensure_desc_prompt_vecs() -> list[Tuple[str, list[str], list[float]]]:
    global _DESC_PROMPT_VECS
    if _DESC_PROMPT_VECS is not None:
        return _DESC_PROMPT_VECS
    vecs: list[Tuple[str, list[str], list[float]]] = []
    for item in AI_DESC_PROMPTS:
        prompt = str(item.get("prompt") or "").strip()
        tags = [str(t).strip().lower() for t in (item.get("tags") or []) if str(t).strip()]
        if not prompt or not tags:
            continue
        v = _ai_embed_text(prompt)
        if v:
            vecs.append((prompt, tags, v))
    _DESC_PROMPT_VECS = vecs
    return vecs


def _classify_descriptive_tags(img_vec: list[float], top_k: int = 6, thr: float = 0.235) -> list[str]:
    try:
        prompt_vecs = _ensure_desc_prompt_vecs()
        if not prompt_vecs:
            return []
        scored: list[Tuple[float, list[str]]] = []
        for _, tags, vec in prompt_vecs:
            scored.append((_cosine(img_vec, vec), tags))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[str] = []
        seen: set[str] = set()
        for score, tags in scored:
            if score < thr:
                continue
            for tag in tags:
                t = str(tag or "").strip().lower()
                if not t or t in seen:
                    continue
                seen.add(t)
                out.append(t)
                if len(out) >= top_k:
                    return out
        return out
    except Exception:
        return []


def _build_desc_caption(tags: list[str]) -> Optional[str]:
    vals = [str(t or "").strip().lower() for t in (tags or []) if str(t or "").strip()]
    if not vals:
        return None
    s = set(vals)
    if "personer" in s and "svømning" in s:
        if "strand" in s:
            return "personer der svømmer på stranden"
        if "hav" in s:
            return "personer der svømmer i havet"
        return "personer der svømmer"
    if "barn" in s and ("gynge" in s or "gynger" in s):
        return "barn der gynger"
    return ", ".join(vals[:4])


# --- 2FA trust helpers ---
def _ua_fingerprint() -> str:
    ua = (request.headers.get("User-Agent") or "").encode("utf-8", errors="ignore")
    return hashlib.sha256(ua).hexdigest()[:16]


def _sign_token(raw: str) -> str:
    key = app.secret_key if isinstance(app.secret_key, (bytes, bytearray)) else str(app.secret_key).encode()
    return hmac.new(key, raw.encode("utf-8"), hashlib.sha256).hexdigest()


def _make_trust_cookie(user_id: int, days: int) -> tuple[str, int]:
    if days <= 0:
        return ("", 0)
    now = int(time.time())
    exp = now + days * 86400
    fp = _ua_fingerprint()
    payload = f"{user_id}.{exp}.{fp}"
    sig = _sign_token(payload)
    token = f"{payload}.{sig}"
    return (token, exp - now)


def _parse_trust_cookie(val: str) -> Optional[dict]:
    try:
        user_s, exp_s, fp, sig = val.split(".", 3)
        raw = f"{user_s}.{exp_s}.{fp}"
        if _sign_token(raw) != sig:
            return None
        exp = int(exp_s)
        if exp < int(time.time()):
            return None
        return {"user_id": int(user_s), "exp": exp, "fp": fp}
    except Exception:
        return None


def _trust_cookie_valid_for(user_id: int) -> bool:
    val = request.cookies.get("fl_trust")
    if not val:
        return False
    data = _parse_trust_cookie(val)
    if not data:
        return False
    if data["user_id"] != int(user_id):
        return False
    if data.get("fp") != _ua_fingerprint():
        return False
    return True


class User(UserMixin):
    def __init__(
        self,
        id: int,
        username: str,
        role: Optional[str] = None,
        is_admin_fallback: Optional[bool] = None,
        ui_language: Optional[str] = None,
        search_language: Optional[str] = None,
        hub_user_id: Optional[int] = None,
    ):
        self.id = str(id)
        self.username = username
        self.hub_user_id = int(hub_user_id) if hub_user_id is not None else None
        role_norm = (role or ("admin" if is_admin_fallback else "user") or "user").strip().lower()
        if role_norm not in {"admin", "user"}:
            role_norm = "user"
        self.role = role_norm
        self.ui_language = _normalize_language(ui_language, DEFAULT_UI_LANGUAGE)
        self.search_language = _normalize_language(search_language, DEFAULT_SEARCH_LANGUAGE)

    @property
    def is_admin(self) -> bool:
        return (getattr(self, "role", "user") == "admin")

    @property
    def is_manager(self) -> bool:
        return False

    def can_manage_users(self) -> bool:
        return self.is_admin

    def can_maintain(self) -> bool:
        return self.is_admin


def _row_to_user(row: sqlite3.Row) -> Optional[User]:
    if not row:
        return None
    qr_url = None
    secret_out = None
    # if not enabled:  # (Uncomment and implement if needed)
    try:
        role = row["role"] if "role" in row.keys() else None
    except Exception:
        role = None
    try:
        ui_language = row["ui_language"] if "ui_language" in row.keys() else None
    except Exception:
        ui_language = None
    try:
        search_language = row["search_language"] if "search_language" in row.keys() else None
    except Exception:
        search_language = None
    try:
        hub_user_id = int(row["hub_user_id"]) if "hub_user_id" in row.keys() and row["hub_user_id"] is not None else None
    except Exception:
        hub_user_id = None
    is_admin_fallback = False
    try:
        is_admin_fallback = bool(row["is_admin"]) if "is_admin" in row.keys() else False
    except Exception:
        is_admin_fallback = False
    return User(int(row["id"]), row["username"], role, is_admin_fallback, ui_language, search_language, hub_user_id)


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    try:
        with closing(get_conn()) as conn:
            row = conn.execute(
                "SELECT id, username, is_admin, role, ui_language, search_language, hub_user_id FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return _row_to_user(row)
    except Exception:
        return None


def users_count() -> int:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        return int(row["c"]) if row else 0


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    CONVERT_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TUS_TMP_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOFRAME_UPDATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # Canonical upload subfolders used by the app
        (UPLOAD_DIR / "originals").mkdir(parents=True, exist_ok=True)
        (UPLOAD_DIR / "converted").mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _install_state_exists() -> bool:
    return INSTALL_STATE_PATH.exists()


def _install_state_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _mark_install_initialized(reason: str = "unknown") -> None:
    if _install_state_exists():
        return
    with INSTALL_STATE_LOCK:
        if _install_state_exists():
            return
        payload = {
            "app": "fjordlens",
            "initialized": True,
            "initialized_at": _install_state_now(),
            "reason": str(reason or "unknown"),
            "db_path": str(DB_PATH),
        }
        INSTALL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = INSTALL_STATE_PATH.with_name(f".{INSTALL_STATE_PATH.name}.{os.getpid()}.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, INSTALL_STATE_PATH)


def _ensure_install_state_for_existing_users() -> None:
    try:
        if users_count() > 0:
            _mark_install_initialized("existing-users")
    except Exception:
        pass


def _setup_locked_response():
    message = "FjordLens er allerede initialiseret, men databasen mangler eller er tom."
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": message, "recovery_required": True}), 503
    return render_template(
        "setup_locked.html",
        app_name="FjordLens",
        db_path=str(DB_PATH),
    ), 503


# Note: We intentionally avoid creating folders on startup.
# Startup initialization is deferred to usage sites (e.g., first upload).


def _queue_uploaded_rel(uploaded_by: str, rel_path: str) -> None:
    user = str(uploaded_by or "").strip() or "__unknown__"
    rel = str(rel_path or "").strip()
    if not rel:
        return
    with UPLOAD_PENDING_LOCK:
        bucket = UPLOAD_PENDING_BY_USER.setdefault(user, [])
        if rel in bucket:
            return
        bucket.append(rel)


def _cleanup_upload_transfer_active_locked(now_ts: Optional[float] = None) -> None:
    ts = float(now_ts or time.time())
    expired = [user for user, expires_at in UPLOAD_TRANSFER_ACTIVE_BY_USER.items() if float(expires_at or 0.0) <= ts]
    for user in expired:
        UPLOAD_TRANSFER_ACTIVE_BY_USER.pop(user, None)


def _set_upload_transfer_active(uploaded_by: str, active: bool) -> None:
    user = str(uploaded_by or "").strip() or "__unknown__"
    with UPLOAD_TRANSFER_LOCK:
        _cleanup_upload_transfer_active_locked()
        if active:
            UPLOAD_TRANSFER_ACTIVE_BY_USER[user] = time.time() + UPLOAD_TRANSFER_TTL_SEC
        else:
            UPLOAD_TRANSFER_ACTIVE_BY_USER.pop(user, None)


def _is_upload_transfer_active(uploaded_by: str) -> bool:
    user = str(uploaded_by or "").strip() or "__unknown__"
    with UPLOAD_TRANSFER_LOCK:
        _cleanup_upload_transfer_active_locked()
        return user in UPLOAD_TRANSFER_ACTIVE_BY_USER


def _any_upload_transfer_active() -> bool:
    with UPLOAD_TRANSFER_LOCK:
        _cleanup_upload_transfer_active_locked()
        return bool(UPLOAD_TRANSFER_ACTIVE_BY_USER)


def _any_regular_upload_postprocess_running() -> bool:
    with UPLOAD_POSTPROCESS_LOCK:
        for user, state in UPLOAD_POSTPROCESS_BY_USER.items():
            if user == DIRECT_UPLOAD_POSTPROCESS_USER:
                continue
            if bool((state or {}).get("running")):
                return True
    return False


def _pending_upload_rels_snapshot() -> set[str]:
    with UPLOAD_PENDING_LOCK:
        return {
            str(rel or "").strip()
            for rels in UPLOAD_PENDING_BY_USER.values()
            for rel in (rels or [])
            if str(rel or "").strip()
        }


def _pending_upload_count(uploaded_by: str) -> int:
    user = str(uploaded_by or "").strip() or "__unknown__"
    with UPLOAD_PENDING_LOCK:
        return len(UPLOAD_PENDING_BY_USER.get(user, []))


def _direct_upload_active_rels_snapshot() -> set[str]:
    with DIRECT_UPLOAD_POSTPROCESS_ACTIVE_LOCK:
        return set(DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS)


def _is_upload_postprocess_running(uploaded_by: str) -> bool:
    user = str(uploaded_by or "").strip() or "__unknown__"
    with UPLOAD_POSTPROCESS_LOCK:
        st = UPLOAD_POSTPROCESS_BY_USER.get(user) or {}
        return bool(st.get("running"))


def _ensure_upload_postprocess_running(uploaded_by: str) -> bool:
    """Start per-user upload postprocess worker if it is not already running."""
    user = str(uploaded_by or "").strip() or "__unknown__"
    workflow_mode = upload_workflow_mode()
    _clear_stop_all_barrier()
    with UPLOAD_POSTPROCESS_LOCK:
        st = dict(UPLOAD_POSTPROCESS_BY_USER.get(user) or {})
        if bool(st.get("running")):
            return False
        st.update(
            {
                "running": True,
                "started_at": now_iso(),
                "finished_at": None,
                "error": None,
                "result": None,
                "phase": "starting",
                "workflow_mode": workflow_mode,
                "process_status": None,
                "current_rel": None,
                "stage_processed": 0,
                "stage_total": 0,
            }
        )
        UPLOAD_POSTPROCESS_BY_USER[user] = st

    rels = _pop_uploaded_rels(user)
    if not rels:
        _set_upload_postprocess_state(
            user,
            {
                "running": False,
                "phase": "idle",
                "finished_at": now_iso(),
            },
        )
        return False

    try:
        threading.Thread(target=_upload_postprocess_worker, args=(user, rels), daemon=True).start()
        return True
    except Exception as e:
        _set_upload_postprocess_state(
            user,
            {
                "running": False,
                "phase": "error",
                "error": f"Unable to start postprocess worker: {e}",
                "finished_at": now_iso(),
            },
        )
        return False


def _set_upload_postprocess_state(uploaded_by: str, patch: Dict[str, Any]) -> None:
    user = str(uploaded_by or "").strip() or "__unknown__"
    with UPLOAD_POSTPROCESS_LOCK:
        cur = dict(UPLOAD_POSTPROCESS_BY_USER.get(user) or {})
        cur.update(patch)
        UPLOAD_POSTPROCESS_BY_USER[user] = cur


def _mark_upload_postprocess_starting(uploaded_by: str, workflow_mode: str, rel_count: int = 0) -> None:
    _set_upload_postprocess_state(
        uploaded_by,
        {
            "running": True,
            "started_at": now_iso(),
            "finished_at": None,
            "error": None,
            "result": None,
            "phase": "starting",
            "workflow_mode": workflow_mode,
            "process_status": None,
            "current_rel": None,
            "stage_processed": 0,
            "stage_total": max(0, int(rel_count or 0)),
        },
    )


def _clear_stop_all_barrier() -> None:
    global STOP_ALL_PROCESS_COOLDOWN_UNTIL
    STOP_ALL_PROCESS_COOLDOWN_UNTIL = 0.0
    UPLOAD_POSTPROCESS_STOP_EVENT.clear()


def _get_upload_postprocess_state(uploaded_by: str) -> Dict[str, Any]:
    user = str(uploaded_by or "").strip() or "__unknown__"
    with UPLOAD_POSTPROCESS_LOCK:
        return dict(UPLOAD_POSTPROCESS_BY_USER.get(user) or {})


def _request_client_ip() -> str:
    try:
        cf = str(request.headers.get("CF-Connecting-IP") or "").strip()
        if cf:
            return cf
        xff = str(request.headers.get("X-Forwarded-For") or "").strip()
        if xff:
            return xff.split(",", 1)[0].strip()
    except Exception:
        pass
    try:
        return str(request.remote_addr or "").strip()
    except Exception:
        return ""


def _request_public_base_url() -> str:
    try:
        xf_proto = str(request.headers.get("X-Forwarded-Proto") or "").split(",", 1)[0].strip().lower()
        xf_host = str(request.headers.get("X-Forwarded-Host") or "").split(",", 1)[0].strip()
        if xf_proto in {"http", "https"} and xf_host:
            return f"{xf_proto}://{xf_host}".rstrip("/")
    except Exception:
        pass
    try:
        cf_visitor = str(request.headers.get("CF-Visitor") or "").strip()
        host = str(request.headers.get("Host") or "").split(",", 1)[0].strip()
        if cf_visitor and host:
            parsed = json.loads(cf_visitor)
            if isinstance(parsed, dict):
                scheme = str(parsed.get("scheme") or "").strip().lower()
                if scheme in {"http", "https"}:
                    return f"{scheme}://{host}".rstrip("/")
    except Exception:
        pass
    try:
        req_parsed = urlparse(str(request.url or ""))
        request_base = f"{req_parsed.scheme}://{req_parsed.netloc}".rstrip("/")
        if request_base and "://" in request_base:
            return request_base
    except Exception:
        pass
    try:
        return request.url_root.rstrip("/")
    except Exception:
        return ""


def _request_client_country() -> Optional[str]:
    code = str(request.headers.get("CF-IPCountry") or "").strip().upper()
    if not code or code in {"XX", "T1"}:
        return None
    try:
        obj = pycountry.countries.get(alpha_2=code)
        return str(getattr(obj, "name", None) or code)
    except Exception:
        return code


def _describe_device(user_agent: str) -> str:
    ua = str(user_agent or "").strip()
    if not ua:
        return "Unknown"
    s = ua.lower()
    if "iphone" in s:
        platform = "iPhone"
    elif "ipad" in s:
        platform = "iPad"
    elif "android" in s:
        platform = "Android"
    elif "windows" in s:
        platform = "Windows"
    elif "mac os" in s or "macintosh" in s:
        platform = "macOS"
    elif "linux" in s:
        platform = "Linux"
    else:
        platform = "Unknown OS"

    if "edg/" in s:
        browser = "Edge"
    elif "chrome/" in s and "edg/" not in s:
        browser = "Chrome"
    elif "firefox/" in s:
        browser = "Firefox"
    elif "safari/" in s and "chrome/" not in s:
        browser = "Safari"
    else:
        browser = "Unknown browser"

    return f"{browser} on {platform}"


def _log_login_attempt(
    username_input: str,
    user_id: Optional[int],
    username_resolved: Optional[str],
    success: bool,
    event_type: str,
    reason: str,
) -> None:
    try:
        ip = _request_client_ip()[:80]
        ua = str(request.headers.get("User-Agent") or "").strip()[:500]
        device = _describe_device(ua)[:120]
        country = _request_client_country()
        with closing(get_conn()) as conn:
            conn.execute(
                """
                INSERT INTO login_audit(
                    at, username_input, user_id, username, success,
                    event_type, reason, ip, country, device, user_agent
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    now_iso(),
                    str(username_input or "")[:120],
                    int(user_id) if user_id is not None else None,
                    str(username_resolved or "")[:120] or None,
                    1 if success else 0,
                    str(event_type or "")[:50],
                    str(reason or "")[:120],
                    ip or None,
                    (str(country)[:120] if country else None),
                    device,
                    ua or None,
                ),
            )
            conn.commit()
    except Exception:
        pass


def _pop_uploaded_rels(uploaded_by: str) -> list[str]:
    user = str(uploaded_by or "").strip() or "__unknown__"
    with UPLOAD_PENDING_LOCK:
        rels = list(UPLOAD_PENDING_BY_USER.pop(user, []))
    out: list[str] = []
    seen: set[str] = set()
    for rel in rels:
        key = str(rel or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _recover_uploaded_rels_missing_postprocess(uploaded_by: str, limit: int = 5000) -> list[str]:
    user = _sanitize_share_visitor_name(str(uploaded_by or "").strip())
    if not user:
        return []
    cap = max(1, min(20000, int(limit or 5000)))
    try:
        with closing(get_conn()) as conn:
            rows = conn.execute(
                """
                SELECT rel_path
                FROM photos
                WHERE COALESCE(uploaded_by, '') = ?
                  AND rel_path LIKE 'uploads/%'
                  AND (thumb_name IS NULL OR TRIM(thumb_name) = '')
                ORDER BY COALESCE(imported_at, last_scanned_at, modified_fs, created_fs) ASC
                LIMIT ?
                """,
                (user, cap),
            ).fetchall()
        rels: list[str] = []
        seen: set[str] = set()
        for row in rows:
            rel = str(row["rel_path"] or "").strip()
            if not rel or rel in seen:
                continue
            try:
                if not _disk_path_from_rel_path(rel).exists():
                    continue
            except Exception:
                continue
            seen.add(rel)
            rels.append(rel)
        return rels
    except Exception:
        return []


def _postprocess_uploaded_rels(
    uploaded_by: str,
    rel_paths: list[str],
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    workflow_mode: Optional[str] = None,
    item_pause_sec: float = 0.0,
    stop_event: Optional[threading.Event] = None,
) -> Dict[str, Any]:
    user = str(uploaded_by or "").strip()
    rels = []
    seen: set[str] = set()
    for rel in (rel_paths or []):
        key = str(rel or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        rels.append(key)

    faces_enabled = faces_auto_index_enabled()
    ai_enabled = ai_auto_ingest_enabled()
    ai_desc_enabled = ai_desc_auto_ingest_enabled()
    mode = _normalize_upload_workflow_mode(workflow_mode or upload_workflow_mode())
    try:
        pause_sec = max(0.0, min(2.0, float(item_pause_sec or 0.0)))
    except Exception:
        pause_sec = 0.0

    def _should_stop() -> bool:
        return bool(stop_event and stop_event.is_set())

    def _pause_between_items() -> None:
        if pause_sec <= 0:
            return
        slept = 0.0
        while slept < pause_sec and not _should_stop():
            step = min(0.1, pause_sec - slept)
            time.sleep(step)
            slept += step

    def _emit_progress(payload: Dict[str, Any]) -> None:
        if not progress_cb:
            return
        try:
            progress_cb(payload)
        except Exception:
            pass

    _emit_progress({
        "phase": "metadata",
        "current_rel": None,
        "stage_processed": 0,
        "stage_total": len(rels),
    })

    indexed_ok: list[str] = []
    heic_converted_count = 0
    index_errors = 0
    for i, rel in enumerate(rels, start=1):
        if _should_stop():
            break
        _emit_progress({
            "phase": "metadata",
            "current_rel": rel,
            "stage_processed": max(0, i - 1),
            "stage_total": len(rels),
        })
        disk_path = _disk_path_from_rel_path(rel)
        extl = disk_path.suffix.lower()
        needs_mov_conversion = extl == ".mov" and mov_convert_on_upload_enabled()
        needs_conversion = (
            ((extl in {".heic", ".heif"}) and heic_convert_on_upload_enabled())
            or ((extl in RAW_EXTS) and raw_convert_on_upload_enabled())
            or needs_mov_conversion
        )

        # Reuse existing metadata for recovered/manual rows unless conversion is
        # pending for HEIC/RAW/MOV files.
        if not needs_conversion:
            checksum_ready = ""
            try:
                with closing(get_conn()) as conn:
                    row = conn.execute(
                        "SELECT checksum_sha256 FROM photos WHERE rel_path=?",
                        (rel,),
                    ).fetchone()
                if row:
                    checksum_ready = str(row["checksum_sha256"] or "").strip()
            except Exception:
                checksum_ready = ""
            if checksum_ready:
                indexed_ok.append(rel)
                _emit_progress({
                    "phase": "metadata",
                    "current_rel": rel,
                    "stage_processed": i,
                    "stage_total": len(rels),
                })
                _pause_between_items()
                continue

        orig_rel_for_convert = rel
        conversion_from_rel: Optional[str] = None
        conversion_from_ext: Optional[str] = None
        conversion_to_rel: Optional[str] = None
        conversion_to_ext: Optional[str] = None
        # Optional: convert HEIC/HEIF/RAW to JPEG and MOV to MP4.
        try:
            if needs_conversion and disk_path.exists():
                # Announce explicit converting phase in UI
                _emit_progress({
                    "phase": "converting",
                    "current_rel": orig_rel_for_convert,
                    "stage_processed": i,
                    "stage_total": len(rels),
                })
                new_rel = None
                new_path = None
                try:
                    target_suffix = ".mp4" if needs_mov_conversion else ".jpg"
                    orig_rel_norm = str(orig_rel_for_convert).replace("\\", "/").lstrip("/")
                    orig_is_upload = orig_rel_norm.startswith("uploads/")
                    # Determine destination path under uploads/converted/<subdir>/
                    sub_rel = ""
                    try:
                        if orig_rel_norm.startswith("uploads/originals/"):
                            sub_rel = orig_rel_norm[len("uploads/originals/"):]  # '<sub>/<file>'
                        elif orig_rel_norm.startswith("uploads/"):
                            sub_rel = orig_rel_norm[len("uploads/"):]  # '<sub>/<file>'
                        else:
                            sub_rel = Path(orig_rel_norm).name
                    except Exception:
                        sub_rel = Path(orig_rel_for_convert).name
                    subdir_only = str(Path(sub_rel).parent).replace("\\", "/").strip("./")
                    leaf_name = f"{Path(sub_rel).stem}{target_suffix}"
                    if orig_is_upload:
                        conv_dir = UPLOAD_DIR / "converted" / (subdir_only if subdir_only != '.' else '')
                        conv_dir.mkdir(parents=True, exist_ok=True)
                        new_path = conv_dir / leaf_name
                    else:
                        new_path = disk_path.with_suffix(target_suffix)
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                    # Avoid clobbering existing converted files by adding a numeric suffix.
                    if new_path.exists():
                        stem = new_path.stem
                        parent = new_path.parent
                        j = 1
                        while True:
                            cand = parent / f"{stem}_{j}{target_suffix}"
                            if not cand.exists():
                                new_path = cand
                                break
                            j += 1
                    if extl in {".heic", ".heif"}:
                        with Image.open(disk_path) as himg:
                            try:
                                himg = ImageOps.exif_transpose(himg)
                            except Exception:
                                pass
                            rgb = himg.convert("RGB")
                            exif_bytes = None
                            try:
                                exif_bytes = himg.info.get("exif") or himg.getexif().tobytes()
                            except Exception:
                                exif_bytes = None
                            save_kwargs = {"format": "JPEG", "quality": 92, "optimize": True}
                            if exif_bytes:
                                save_kwargs["exif"] = exif_bytes
                            rgb.save(new_path, **save_kwargs)
                    elif extl in RAW_EXTS:
                        # RAW â†’ JPEG via rawpy with ffmpeg fallback
                        _raw_to_jpeg(disk_path, new_path)
                    else:
                        _mov_to_mp4(disk_path, new_path)
                    # Preserve timestamps
                    try:
                        st = disk_path.stat()
                        os.utime(new_path, (st.st_atime, st.st_mtime))
                    except Exception:
                        pass
                    # Switch rel/disk_path to the converted copy (optionally keep the original under 'originals')
                    if orig_is_upload:
                        # Mirror uploaded source to /uploads/converted/<...>.
                        try:
                            if subdir_only not in {"", "."}:
                                tail = (Path(subdir_only) / new_path.name).as_posix()
                            else:
                                tail = new_path.name
                        except Exception:
                            tail = f"{Path(sub_rel).stem}{target_suffix}"
                        new_rel = f"uploads/converted/{tail}"
                    else:
                        # Library fallback
                        try:
                            orig_rel_path = Path(orig_rel_for_convert)
                            if str(orig_rel_path.parent).replace("\\", "/") not in {"", "."}:
                                new_rel = (orig_rel_path.parent / new_path.name).as_posix()
                            else:
                                new_rel = new_path.name
                        except Exception:
                            new_rel = str(orig_rel_for_convert) + target_suffix
                    rel = new_rel
                    disk_path = new_path
                    conversion_from_rel = orig_rel_for_convert
                    conversion_from_ext = extl
                    conversion_to_rel = rel
                    conversion_to_ext = str(new_path.suffix or "").lower() if new_path else target_suffix
                    try:
                        if extl in {".heic", ".heif"}:
                            event_name = "heic_converted"
                        elif extl in RAW_EXTS:
                            event_name = "raw_converted"
                        else:
                            event_name = "mov_converted"
                        log_event(event_name, rel_path=rel)
                    except Exception:
                        pass
                    heic_converted_count += 1
                    # Remove any stub row created under the original rel (usually uploads/originals).
                    try:
                        with closing(get_conn()) as conn:
                            conn.execute("DELETE FROM photos WHERE rel_path=?", (orig_rel_for_convert,))
                            conn.commit()
                    except Exception:
                        pass
                    # Optionally delete originals to save space.
                    try:
                        if extl in {".heic", ".heif"}:
                            keep = heic_keep_originals_enabled()
                            delete_event = "heic_original_deleted"
                        elif extl in RAW_EXTS:
                            keep = raw_keep_originals_enabled()
                            delete_event = "raw_original_deleted"
                        else:
                            keep = mov_keep_originals_enabled()
                            delete_event = "mov_original_deleted"
                        if not keep:
                            orig_path = _disk_path_from_rel_path(orig_rel_for_convert)
                            orig_path.unlink(missing_ok=True)
                            log_event(delete_event, rel_path=orig_rel_for_convert)
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        log_event("error", rel_path=str(rel), error=f"convert: {e}")
                    except Exception:
                        pass
        except Exception:
            pass
        if not disk_path.exists():
            index_errors += 1
            try:
                log_event("error", rel_path=rel, error="Upload file missing before post-process")
            except Exception:
                pass
            _pause_between_items()
            continue
        try:
            meta = extract_metadata(disk_path, rel, generate_thumb=False)
            if conversion_from_rel and conversion_to_rel:
                _attach_conversion_metadata(
                    meta,
                    from_rel_path=conversion_from_rel,
                    to_rel_path=conversion_to_rel,
                    from_ext=conversion_from_ext,
                    to_ext=conversion_to_ext or meta.get("ext"),
                )
            meta["uploaded_by"] = user
            upsert_photo(meta)
            indexed_ok.append(rel)
            try:
                log_event("upload_indexed", rel_path=rel, width=meta.get("width"), height=meta.get("height"), has_gps=bool(meta.get("gps_lat") and meta.get("gps_lon")))
            except Exception:
                pass
            # Emit progress after finishing this item
            _emit_progress({
                "phase": "metadata",
                "current_rel": rel,
                "stage_processed": i,
                "stage_total": len(rels),
            })
            _pause_between_items()
        except Exception as e:
            index_errors += 1
            try:
                log_event("error", rel_path=rel, error=f"postprocess_index: {e}")
            except Exception:
                pass
            _pause_between_items()

    thumb_errors = 0
    faces_done = 0
    faces_found = 0
    faces_errors = 0
    ai_done = 0
    ai_errors = 0
    ai_desc_done = 0
    ai_desc_errors = 0
    process_status: Optional[Dict[str, Dict[str, Any]]] = None

    if mode == UPLOAD_WORKFLOW_MODE_AGGRESSIVE:
        process_lock = threading.Lock()
        faces_metric_lock = threading.Lock()
        process_status = {
            "metadata": {
                "enabled": True,
                "running": False,
                "processed": len(rels),
                "total": len(rels),
                "errors": index_errors,
                "queued": 0,
                "in_flight": 0,
            },
            "thumbnails": {
                "enabled": True,
                "running": bool(indexed_ok),
                "processed": 0,
                "total": len(indexed_ok),
                "errors": 0,
                "queued": len(indexed_ok),
                "in_flight": 0,
            },
            "faces": {
                "enabled": bool(faces_enabled),
                "running": bool(faces_enabled and indexed_ok),
                "processed": 0,
                "total": len(indexed_ok) if faces_enabled else 0,
                "errors": 0,
                "queued": len(indexed_ok) if faces_enabled else 0,
                "in_flight": 0,
                "batch_size": int(UPLOAD_WORKFLOW_FACE_BATCH_SIZE),
            },
            "embeddings": {
                "enabled": bool(ai_enabled),
                "running": bool(ai_enabled and indexed_ok),
                "processed": 0,
                "total": len(indexed_ok) if ai_enabled else 0,
                "errors": 0,
                "queued": len(indexed_ok) if ai_enabled else 0,
                "in_flight": 0,
            },
            "descriptions": {
                "enabled": bool(ai_desc_enabled),
                "running": bool(ai_desc_enabled and indexed_ok),
                "processed": 0,
                "total": len(indexed_ok) if ai_desc_enabled else 0,
                "errors": 0,
                "queued": len(indexed_ok) if ai_desc_enabled else 0,
                "in_flight": 0,
            },
        }

        def _copy_process_status() -> Dict[str, Dict[str, Any]]:
            out: Dict[str, Dict[str, Any]] = {}
            with process_lock:
                for k, v in process_status.items():
                    out[k] = dict(v)
            return out

        def _update_stage(
            stage: str,
            processed_inc: int = 0,
            errors_inc: int = 0,
            in_flight_inc: int = 0,
            set_running: Optional[bool] = None,
        ) -> None:
            with process_lock:
                st = process_status.get(stage)
                if not st:
                    return
                if processed_inc:
                    st["processed"] = int(st.get("processed") or 0) + int(processed_inc)
                if errors_inc:
                    st["errors"] = int(st.get("errors") or 0) + int(errors_inc)
                if in_flight_inc:
                    st["in_flight"] = max(0, int(st.get("in_flight") or 0) + int(in_flight_inc))
                st["queued"] = max(
                    0,
                    int(st.get("total") or 0)
                    - int(st.get("processed") or 0)
                    - int(st.get("in_flight") or 0),
                )
                if set_running is not None:
                    st["running"] = bool(set_running)

        def _emit_parallel(current_rel: Optional[str] = None) -> None:
            md = process_status.get("metadata") or {}
            _emit_progress(
                {
                    "phase": "parallel",
                    "workflow_mode": mode,
                    "current_rel": current_rel,
                    "stage_processed": int(md.get("processed") or 0),
                    "stage_total": int(md.get("total") or 0),
                    "process_status": _copy_process_status(),
                }
            )

        def _thumb_worker() -> None:
            nonlocal thumb_errors
            for rel in indexed_ok:
                if _should_stop():
                    break
                err_inc = 0
                try:
                    disk_path = _disk_path_from_rel_path(rel)
                    if not disk_path.exists():
                        thumb_errors += 1
                        err_inc = 1
                    else:
                        stat = disk_path.stat()
                        thumb_name: Optional[str] = None
                        if disk_path.suffix.lower() in VIDEO_EXTS:
                            thumb_name = _make_video_thumb(disk_path, rel, stat.st_mtime, stat.st_size)
                        else:
                            with Image.open(disk_path) as img:
                                try:
                                    img = ImageOps.exif_transpose(img)
                                except Exception:
                                    pass
                                thumb_name = make_thumb(img, rel, stat.st_mtime, stat.st_size)
                        if thumb_name:
                            with closing(get_conn()) as conn:
                                conn.execute(
                                    "UPDATE photos SET thumb_name=?, last_scanned_at=? WHERE rel_path=?",
                                    (thumb_name, now_iso(), rel),
                                )
                                conn.commit()
                        else:
                            thumb_errors += 1
                            err_inc = 1
                except Exception as e:
                    thumb_errors += 1
                    err_inc = 1
                    try:
                        log_event("error", rel_path=rel, error=f"postprocess_thumb: {e}")
                    except Exception:
                        pass
                _update_stage("thumbnails", processed_inc=1, errors_inc=err_inc)
                _emit_parallel(rel)
            _update_stage("thumbnails", set_running=False)
            _emit_parallel()

        def _faces_worker() -> None:
            nonlocal faces_done, faces_found, faces_errors
            max_concurrency = max(1, int(UPLOAD_WORKFLOW_FACE_BATCH_SIZE))

            def _run_face_job(rel: str, start_event: threading.Event) -> None:
                nonlocal faces_done, faces_found, faces_errors
                err_inc = 0
                found_inc = 0
                try:
                    # Ensure each batch starts work simultaneously.
                    start_event.wait(timeout=5.0)
                    if _should_stop():
                        return
                    fc = index_faces_for_photo(rel)
                    try:
                        if int(fc or 0) > 0:
                            found_inc = 1
                    except Exception:
                        found_inc = 0
                    with faces_metric_lock:
                        faces_done += 1
                        faces_found += found_inc
                except Exception as e:
                    err_inc = 1
                    with faces_metric_lock:
                        faces_errors += 1
                    try:
                        log_event("error", rel_path=rel, error=f"postprocess_faces: {e}")
                    except Exception:
                        pass
                _update_stage("faces", processed_inc=1, errors_inc=err_inc, in_flight_inc=-1)
                _emit_parallel(rel)

            for start in range(0, len(indexed_ok), max_concurrency):
                if _should_stop():
                    break
                batch = indexed_ok[start : start + max_concurrency]
                if not batch:
                    continue
                try:
                    log_event("faces_batch_start", batch_size=len(batch), concurrent=len(batch), mode="simultaneous")
                except Exception:
                    pass

                start_event = threading.Event()
                started_threads: list[threading.Thread] = []
                for rel in batch:
                    try:
                        t = threading.Thread(target=_run_face_job, args=(rel, start_event), daemon=True)
                        t.start()
                        started_threads.append(t)
                    except Exception as e:
                        with faces_metric_lock:
                            faces_errors += 1
                        try:
                            log_event("error", rel_path=rel, error=f"postprocess_faces_start: {e}")
                        except Exception:
                            pass
                        _update_stage("faces", processed_inc=1, errors_inc=1)
                        _emit_parallel(rel)

                if started_threads:
                    _update_stage("faces", in_flight_inc=len(started_threads))
                    _emit_parallel()
                    start_event.set()

                for t in started_threads:
                    try:
                        t.join()
                    except Exception:
                        pass

            _update_stage("faces", set_running=False)
            _emit_parallel()

        def _embeddings_worker() -> None:
            nonlocal ai_done, ai_errors
            for rel in indexed_ok:
                if _should_stop():
                    break
                err_inc = 0
                try:
                    _embed_uploaded_photo_if_needed(rel)
                    ai_done += 1
                except Exception as e:
                    ai_errors += 1
                    err_inc = 1
                    try:
                        log_event("error", rel_path=rel, error=f"postprocess_ai: {e}")
                    except Exception:
                        pass
                _update_stage("embeddings", processed_inc=1, errors_inc=err_inc)
                _emit_parallel(rel)
            _update_stage("embeddings", set_running=False)
            _emit_parallel()

        def _descriptions_worker() -> None:
            nonlocal ai_desc_done, ai_desc_errors
            for rel in indexed_ok:
                if _should_stop():
                    break
                err_inc = 0
                try:
                    _describe_uploaded_photo_if_needed(rel)
                    ai_desc_done += 1
                except Exception as e:
                    ai_desc_errors += 1
                    err_inc = 1
                    try:
                        log_event("error", rel_path=rel, error=f"postprocess_ai_desc: {e}")
                    except Exception:
                        pass
                _update_stage("descriptions", processed_inc=1, errors_inc=err_inc)
                _emit_parallel(rel)
            _update_stage("descriptions", set_running=False)
            _emit_parallel()

        _emit_parallel()
        workers: list[threading.Thread] = []
        if indexed_ok and not _should_stop():
            workers.append(threading.Thread(target=_thumb_worker, daemon=True))
            if faces_enabled:
                workers.append(threading.Thread(target=_faces_worker, daemon=True))
            if ai_enabled:
                workers.append(threading.Thread(target=_embeddings_worker, daemon=True))
            if ai_desc_enabled:
                workers.append(threading.Thread(target=_descriptions_worker, daemon=True))
        for t in workers:
            try:
                t.start()
            except Exception:
                pass
        for t in workers:
            try:
                t.join()
            except Exception:
                pass
        with process_lock:
            for st in process_status.values():
                st["running"] = False
                st["in_flight"] = 0
                st["queued"] = max(0, int(st.get("total") or 0) - int(st.get("processed") or 0))
        _emit_parallel()
    else:
        _emit_progress(
            {
                "phase": "thumbnails",
                "current_rel": None,
                "stage_processed": 0,
                "stage_total": len(indexed_ok),
            }
        )
        for i, rel in enumerate(indexed_ok, start=1):
            if _should_stop():
                break
            _emit_progress(
                {
                    "phase": "thumbnails",
                    "current_rel": rel,
                    "stage_processed": max(0, i - 1),
                    "stage_total": len(indexed_ok),
                }
            )
            try:
                disk_path = _disk_path_from_rel_path(rel)
                if not disk_path.exists():
                    thumb_errors += 1
                    _pause_between_items()
                    continue
                stat = disk_path.stat()
                thumb_name: Optional[str] = None
                if disk_path.suffix.lower() in VIDEO_EXTS:
                    thumb_name = _make_video_thumb(disk_path, rel, stat.st_mtime, stat.st_size)
                else:
                    with Image.open(disk_path) as img:
                        try:
                            img = ImageOps.exif_transpose(img)
                        except Exception:
                            pass
                        thumb_name = make_thumb(img, rel, stat.st_mtime, stat.st_size)
                if thumb_name:
                    with closing(get_conn()) as conn:
                        conn.execute("UPDATE photos SET thumb_name=?, last_scanned_at=? WHERE rel_path=?", (thumb_name, now_iso(), rel))
                        conn.commit()
                else:
                    thumb_errors += 1
                _emit_progress(
                    {
                        "phase": "thumbnails",
                        "current_rel": rel,
                        "stage_processed": i,
                        "stage_total": len(indexed_ok),
                    }
                )
            except Exception as e:
                thumb_errors += 1
                try:
                    log_event("error", rel_path=rel, error=f"postprocess_thumb: {e}")
                except Exception:
                    pass
            _pause_between_items()

        if faces_enabled:
            _emit_progress(
                {
                    "phase": "faces",
                    "current_rel": None,
                    "stage_processed": 0,
                    "stage_total": len(indexed_ok),
                }
            )
            for i, rel in enumerate(indexed_ok, start=1):
                if _should_stop():
                    break
                _emit_progress(
                    {
                        "phase": "faces",
                        "current_rel": rel,
                        "stage_processed": max(0, i - 1),
                        "stage_total": len(indexed_ok),
                    }
                )
                try:
                    fc = index_faces_for_photo(rel)
                    faces_done += 1
                    try:
                        if int(fc or 0) > 0:
                            faces_found += 1
                    except Exception:
                        pass
                    _emit_progress(
                        {
                            "phase": "faces",
                            "current_rel": rel,
                            "stage_processed": i,
                            "stage_total": len(indexed_ok),
                        }
                    )
                except Exception as e:
                    faces_errors += 1
                    try:
                        log_event("error", rel_path=rel, error=f"postprocess_faces: {e}")
                    except Exception:
                        pass
                _pause_between_items()

        if ai_enabled:
            _emit_progress(
                {
                    "phase": "embeddings",
                    "current_rel": None,
                    "stage_processed": 0,
                    "stage_total": len(indexed_ok),
                }
            )
            for i, rel in enumerate(indexed_ok, start=1):
                if _should_stop():
                    break
                _emit_progress(
                    {
                        "phase": "embeddings",
                        "current_rel": rel,
                        "stage_processed": max(0, i - 1),
                        "stage_total": len(indexed_ok),
                    }
                )
                try:
                    _embed_uploaded_photo_if_needed(rel)
                    ai_done += 1
                    _emit_progress(
                        {
                            "phase": "embeddings",
                            "current_rel": rel,
                            "stage_processed": i,
                            "stage_total": len(indexed_ok),
                        }
                    )
                except Exception as e:
                    ai_errors += 1
                    try:
                        log_event("error", rel_path=rel, error=f"postprocess_ai: {e}")
                    except Exception:
                        pass
                _pause_between_items()

        if ai_desc_enabled:
            desc_total = len(indexed_ok)
            _emit_progress(
                {
                    "phase": "descriptions",
                    "current_rel": None,
                    "stage_processed": 0,
                    "stage_total": desc_total,
                }
            )
            for i, rel in enumerate(indexed_ok, start=1):
                if _should_stop():
                    break
                _emit_progress(
                    {
                        "phase": "descriptions",
                        "current_rel": rel,
                        "stage_processed": i,
                        "stage_total": desc_total,
                    }
                )
                try:
                    _describe_uploaded_photo_if_needed(rel)
                    ai_desc_done += 1
                except Exception as e:
                    ai_desc_errors += 1
                    try:
                        log_event("error", rel_path=rel, error=f"postprocess_ai_desc: {e}")
                    except Exception:
                        pass
                _pause_between_items()

    done_payload: Dict[str, Any] = {
        "phase": "stopped" if _should_stop() else "done",
        "workflow_mode": mode,
        "current_rel": None,
        "stage_processed": len(rels),
        "stage_total": len(rels),
    }
    if process_status is not None:
        done_payload["process_status"] = process_status
    _emit_progress(done_payload)

    result: Dict[str, Any] = {
        "ok": True,
        "workflow_mode": mode,
        "received": len(rels),
        "indexed": len(indexed_ok),
        "index_errors": index_errors,
        "thumb_errors": thumb_errors,
        "heic_converted": heic_converted_count,
        "faces_enabled": faces_enabled,
        "faces_done": faces_done,
        "faces_found": faces_found,
        "faces_errors": faces_errors,
        "ai_enabled": ai_enabled,
        "ai_done": ai_done,
        "ai_errors": ai_errors,
        "ai_desc_enabled": ai_desc_enabled,
        "ai_desc_done": ai_desc_done,
        "ai_desc_errors": ai_desc_errors,
        "stopped": _should_stop(),
    }
    if process_status is not None:
        result["process_status"] = process_status
    return result


def _upload_postprocess_worker(uploaded_by: str, initial_rels: list[str]) -> None:
    user = str(uploaded_by or "").strip() or "__unknown__"
    workflow_mode = upload_workflow_mode()
    _set_upload_postprocess_state(
        user,
        {
            "running": True,
            "started_at": now_iso(),
            "finished_at": None,
            "error": None,
            "result": None,
            "phase": "starting",
            "workflow_mode": workflow_mode,
            "process_status": None,
            "current_rel": None,
            "stage_processed": 0,
            "stage_total": 0,
        },
    )

    aggregate: Dict[str, Any] = {
        "ok": True,
        "workflow_mode": workflow_mode,
        "received": 0,
        "indexed": 0,
        "index_errors": 0,
        "heic_converted": 0,
        "faces_enabled": faces_auto_index_enabled(),
        "faces_done": 0,
        "faces_found": 0,
        "faces_errors": 0,
        "ai_enabled": ai_auto_ingest_enabled(),
        "ai_done": 0,
        "ai_errors": 0,
        "ai_desc_enabled": ai_desc_auto_ingest_enabled(),
        "ai_desc_done": 0,
        "ai_desc_errors": 0,
        "process_status": None,
    }

    batch = list(initial_rels or [])
    try:
        while batch:
            if UPLOAD_POSTPROCESS_STOP_EVENT.is_set():
                break
            if workflow_mode == UPLOAD_WORKFLOW_MODE_AGGRESSIVE and len(batch) < int(UPLOAD_WORKFLOW_FACE_BATCH_SIZE):
                gather_deadline = time.time() + 1.2
                while len(batch) < int(UPLOAD_WORKFLOW_FACE_BATCH_SIZE) and time.time() < gather_deadline and not UPLOAD_POSTPROCESS_STOP_EVENT.is_set():
                    time.sleep(0.12)
                    more = _pop_uploaded_rels(user)
                    if not more:
                        continue
                    batch.extend(more)
                    gather_deadline = time.time() + 0.35

            try:
                log_event("upload_postprocess_start", user=user, files=len(batch), workflow_mode=workflow_mode)
            except Exception:
                pass

            result = _postprocess_uploaded_rels(
                user,
                batch,
                progress_cb=lambda p: _set_upload_postprocess_state(user, p),
                workflow_mode=workflow_mode,
                stop_event=UPLOAD_POSTPROCESS_STOP_EVENT,
            )
            aggregate["received"] += int(result["received"] if "received" in result and result["received"] is not None else 0)
            aggregate["indexed"] += int(result["indexed"] if "indexed" in result and result["indexed"] is not None else 0)
            aggregate["index_errors"] += int(result["index_errors"] if "index_errors" in result and result["index_errors"] is not None else 0)
            aggregate["heic_converted"] += int(result["heic_converted"] if "heic_converted" in result and result["heic_converted"] is not None else 0)
            aggregate["faces_done"] += int(result["faces_done"] if "faces_done" in result and result["faces_done"] is not None else 0)
            aggregate["faces_found"] += int(result["faces_found"] if "faces_found" in result and result["faces_found"] is not None else 0)
            aggregate["faces_errors"] += int(result["faces_errors"] if "faces_errors" in result and result["faces_errors"] is not None else 0)
            aggregate["ai_done"] += int(result["ai_done"] if "ai_done" in result and result["ai_done"] is not None else 0)
            aggregate["ai_errors"] += int(result["ai_errors"] if "ai_errors" in result and result["ai_errors"] is not None else 0)
            aggregate["ai_desc_done"] += int(result["ai_desc_done"] if "ai_desc_done" in result and result["ai_desc_done"] is not None else 0)
            aggregate["ai_desc_errors"] += int(result["ai_desc_errors"] if "ai_desc_errors" in result and result["ai_desc_errors"] is not None else 0)
            aggregate["faces_enabled"] = bool(result["faces_enabled"] if "faces_enabled" in result else False)
            aggregate["ai_enabled"] = bool(result["ai_enabled"] if "ai_enabled" in result else False)
            aggregate["ai_desc_enabled"] = bool(result["ai_desc_enabled"] if "ai_desc_enabled" in result else False)
            if "process_status" in result:
                aggregate["process_status"] = result["process_status"]
                _set_upload_postprocess_state(user, {"process_status": result["process_status"], "workflow_mode": workflow_mode})

            try:
                log_event(
                    "upload_postprocess_done",
                    user=user,
                    workflow_mode=workflow_mode,
                    files=result["received"] if "received" in result else None,
                    indexed=result["indexed"] if "indexed" in result else None,
                    heic_converted=result["heic_converted"] if "heic_converted" in result else None,
                    faces_scanned=result["faces_done"] if "faces_done" in result else None,
                    faces_found=result["faces_found"] if "faces_found" in result else None,
                    index_errors=result["index_errors"] if "index_errors" in result else None,
                    faces_done=result["faces_done"] if "faces_done" in result else None,
                    faces_errors=result["faces_errors"] if "faces_errors" in result else None,
                    ai_done=result["ai_done"] if "ai_done" in result else None,
                    ai_errors=result["ai_errors"] if "ai_errors" in result else None,
                    ai_desc_done=result["ai_desc_done"] if "ai_desc_done" in result else None,
                    ai_desc_errors=result["ai_desc_errors"] if "ai_desc_errors" in result else None,
                )
            except Exception:
                pass

            if bool(result.get("stopped")) or UPLOAD_POSTPROCESS_STOP_EVENT.is_set():
                batch = []
            else:
                batch = _pop_uploaded_rels(user)

        _set_upload_postprocess_state(
            user,
            {
                "running": False,
                "finished_at": now_iso(),
                "result": aggregate,
                "error": None,
                "phase": "stopped" if UPLOAD_POSTPROCESS_STOP_EVENT.is_set() else "done",
                "workflow_mode": workflow_mode,
                "process_status": aggregate.get("process_status"),
                "current_rel": None,
                "stage_processed": int(aggregate["received"] if "received" in aggregate and aggregate["received"] is not None else 0),
                "stage_total": int(aggregate["received"] if "received" in aggregate and aggregate["received"] is not None else 0),
            },
        )
        try:
            log_event(
                "upload_postprocess_summary_done",
                user=user,
                workflow_mode=workflow_mode,
                files=aggregate["received"] if "received" in aggregate else None,
                indexed=aggregate["indexed"] if "indexed" in aggregate else None,
                heic_converted=aggregate["heic_converted"] if "heic_converted" in aggregate else None,
                faces_scanned=aggregate["faces_done"] if "faces_done" in aggregate else None,
                faces_found=aggregate["faces_found"] if "faces_found" in aggregate else None,
                index_errors=aggregate["index_errors"] if "index_errors" in aggregate else None,
                faces_errors=aggregate["faces_errors"] if "faces_errors" in aggregate else None,
                ai_done=aggregate["ai_done"] if "ai_done" in aggregate else None,
                ai_errors=aggregate["ai_errors"] if "ai_errors" in aggregate else None,
                ai_desc_done=aggregate["ai_desc_done"] if "ai_desc_done" in aggregate else None,
                ai_desc_errors=aggregate["ai_desc_errors"] if "ai_desc_errors" in aggregate else None,
            )
        except Exception:
            pass
    except Exception as e:
        _set_upload_postprocess_state(
            user,
            {
                "running": False,
                "finished_at": now_iso(),
                "error": str(e),
                "result": aggregate,
                "phase": "error",
                "workflow_mode": workflow_mode,
            },
        )


def _tus_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "Tus-Resumable": "1.0.0",
        "Tus-Version": "1.0.0",
        "Tus-Extension": "creation",
    }
    if extra:
        headers.update(extra)
    return headers


def _tus_require_version() -> Optional[Tuple[dict, int]]:
    ver = str(request.headers.get("Tus-Resumable") or "").strip()
    if ver != "1.0.0":
        return ({"ok": False, "error": "Missing or invalid Tus-Resumable"}, 412)
    return None


def _parse_tus_metadata(raw: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not raw:
        return out
    for pair in raw.split(","):
        part = str(pair or "").strip()
        if not part:
            continue
        chunks = part.split(" ", 1)
        if len(chunks) != 2:
            continue
        key = chunks[0].strip()
        value = chunks[1].strip()
        if not key:
            continue
        try:
            decoded = base64.b64decode(value).decode("utf-8") if value else ""
        except Exception:
            decoded = ""
        out[key] = decoded
    return out


def _tus_upload_paths(upload_id: str) -> Tuple[Path, Path]:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", upload_id or "")
    if not safe_id:
        raise ValueError("Invalid upload id")
    return (TUS_TMP_DIR / f"{safe_id}.bin", TUS_TMP_DIR / f"{safe_id}.json")


def _tus_load_meta(upload_id: str) -> Optional[Dict[str, Any]]:
    try:
        _, meta_path = _tus_upload_paths(upload_id)
        if not meta_path.exists():
            return None
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _tus_store_meta(upload_id: str, meta: Dict[str, Any]) -> None:
    _, meta_path = _tus_upload_paths(upload_id)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def _upsert_uploaded_stub(rel_path: str, disk_path: Path, uploaded_by: str) -> None:
    """Create/update a lightweight photo row right after upload commit.

    This lets the UI show newly uploaded files immediately (often as
    'Ingen thumbnail') while background postprocess fills metadata/thumb.
    """
    rel = str(rel_path or "").strip()
    if not rel:
        return
    try:
        st = disk_path.stat()
    except Exception:
        return

    ts_iso = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
    payload = {
        "rel_path": rel,
        "filename": disk_path.name,
        "ext": disk_path.suffix.lower(),
        "file_size": int(st.st_size),
        "created_fs": ts_iso,
        "modified_fs": ts_iso,
        "captured_at": ts_iso,
        "ai_tags": json.dumps([], ensure_ascii=False),
        "metadata_json": json.dumps({}, ensure_ascii=False),
        "exif_json": json.dumps({}, ensure_ascii=False),
        "uploaded_by": _sanitize_share_visitor_name(uploaded_by or "") or None,
        "imported_at": now_iso(),
        "last_scanned_at": now_iso(),
    }

    try:
        with closing(get_conn()) as conn:
            conn.execute(
                """
                INSERT INTO photos (
                    rel_path, filename, ext, file_size,
                    created_fs, modified_fs, captured_at,
                    ai_tags, metadata_json, exif_json,
                    uploaded_by, imported_at, last_scanned_at
                ) VALUES (
                    :rel_path, :filename, :ext, :file_size,
                    :created_fs, :modified_fs, :captured_at,
                    :ai_tags, :metadata_json, :exif_json,
                    :uploaded_by, :imported_at, :last_scanned_at
                )
                ON CONFLICT(rel_path) DO UPDATE SET
                    filename=excluded.filename,
                    ext=excluded.ext,
                    file_size=excluded.file_size,
                    modified_fs=excluded.modified_fs,
                    created_fs=COALESCE(photos.created_fs, excluded.created_fs),
                    captured_at=COALESCE(photos.captured_at, excluded.captured_at),
                    uploaded_by=COALESCE(photos.uploaded_by, excluded.uploaded_by),
                    last_scanned_at=excluded.last_scanned_at
                """,
                payload,
            )
            conn.commit()
    except Exception as e:
        try:
            log_event("error", rel_path=rel, error=f"upload_stub_upsert: {e}")
        except Exception:
            pass


def _commit_uploaded_file(
    target_dir: Path,
    rel_prefix: str,
    subdir: str,
    source_path: Path,
    original_name: str,
    last_modified_ms: Optional[int],
    uploaded_by: str,
    autostart_postprocess: bool = False,
) -> Tuple[bool, str, Optional[str]]:
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return (False, "", "Cannot create target directory")
    name = secure_filename(original_name or "")
    if not name:
        return (False, "", "Invalid filename")
    ext = Path(name).suffix.lower()
    if not _is_upload_extension_allowed(ext):
        return (False, "", _blocked_upload_file_error(name, ext))

    target = target_dir / name
    stem = Path(name).stem
    suffix = Path(name).suffix
    i = 1
    while target.exists():
        target = target_dir / f"{stem}_{i}{suffix}"
        i += 1

    shutil.move(str(source_path), str(target))
    try:
        if last_modified_ms:
            ts = float(last_modified_ms) / 1000.0
            os.utime(target, (ts, ts))
    except Exception:
        pass

    rel_leaf = f"{subdir}/{target.name}" if subdir else target.name
    rel = f"{rel_prefix}{rel_leaf}" if rel_prefix else rel_leaf
    try:
        _queue_uploaded_rel(uploaded_by, rel)
    except Exception as e:
        return (False, target.name, f"Queue fail: {target.name}: {e}")

    # Ensure postprocess runs in the container even if the browser refreshes/closes.
    if autostart_postprocess:
        try:
            _ensure_upload_postprocess_running(uploaded_by)
        except Exception as e:
            try:
                log_event("error", rel_path=rel, error=f"postprocess_autostart: {e}")
            except Exception:
                pass

    # Make file visible in UI immediately; all heavy work comes from postprocess.
    _upsert_uploaded_stub(rel, target, uploaded_by)
    return (True, target.name, None)


def _configure_sqlite_connection(conn: sqlite3.Connection) -> None:
    try:
        conn.execute(f"PRAGMA journal_mode={SQLITE_JOURNAL_MODE};")
    except Exception:
        pass
    try:
        conn.execute(f"PRAGMA busy_timeout={int(SQLITE_BUSY_TIMEOUT_MS)};")
    except Exception:
        pass
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=max(1.0, float(SQLITE_BUSY_TIMEOUT_MS) / 1000.0))
    conn.row_factory = sqlite3.Row
    _configure_sqlite_connection(conn)
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rel_path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                ext TEXT,
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                created_fs TEXT,
                modified_fs TEXT,
                captured_at TEXT,
                camera_make TEXT,
                camera_model TEXT,
                lens_model TEXT,
                iso INTEGER,
                focal_length REAL,
                f_number REAL,
                exposure_time TEXT,
                gps_lat REAL,
                gps_lon REAL,
                gps_name TEXT,
                checksum_sha256 TEXT,
                phash TEXT,
                phash_dct TEXT,
                dhash TEXT,
                ahash TEXT,
                thumb_name TEXT,
                favorite INTEGER DEFAULT 0,
                people_count INTEGER DEFAULT 0,
                faces_indexed_at TEXT,
                ai_tags TEXT,
                ai_desc_tags TEXT,
                ai_desc_caption TEXT,
                embedding_json TEXT,
                metadata_json TEXT,
                exif_json TEXT,
                uploaded_by TEXT,
                imported_at TEXT,
                last_scanned_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_photos_captured_at ON photos(captured_at);
            CREATE INDEX IF NOT EXISTS idx_photos_filename ON photos(filename);
                CREATE INDEX IF NOT EXISTS idx_photos_phash ON photos(phash);

                CREATE TABLE IF NOT EXISTS geo_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat_rounded INTEGER NOT NULL,
                    lon_rounded INTEGER NOT NULL,
                    country TEXT,
                    city TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_geo_cache ON geo_cache(lat_rounded, lon_rounded);
                CREATE TABLE IF NOT EXISTS weather_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat_rounded INTEGER NOT NULL,
                    lon_rounded INTEGER NOT NULL,
                    observed_hour TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(lat_rounded, lon_rounded, observed_hour, provider)
                );
                CREATE INDEX IF NOT EXISTS idx_weather_cache_key ON weather_cache(lat_rounded, lon_rounded, observed_hour, provider);
                CREATE TABLE IF NOT EXISTS place_geocode_cache (
                    query_key TEXT PRIMARY KEY,
                    city TEXT,
                    country TEXT,
                    latitude REAL,
                    longitude REAL,
                    provider TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TEXT NOT NULL
                );
            CREATE INDEX IF NOT EXISTS idx_photos_favorite ON photos(favorite);
            CREATE INDEX IF NOT EXISTS idx_photos_gps ON photos(gps_lat, gps_lon);
            CREATE INDEX IF NOT EXISTS idx_photos_phash ON photos(phash);

            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_id INTEGER NOT NULL,
                person_id INTEGER,
                bbox_x INTEGER,
                bbox_y INTEGER,
                bbox_w INTEGER,
                bbox_h INTEGER,
                embedding_json TEXT,
                confidence REAL,
                frame_sec REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(photo_id) REFERENCES photos(id),
                FOREIGN KEY(person_id) REFERENCES people(id)
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 1,
                role TEXT,
                hub_user_id INTEGER,
                hub_synced_at TEXT,
                ui_language TEXT DEFAULT 'da',
                search_language TEXT DEFAULT 'da',
                theme_mode TEXT DEFAULT 'system',
                totp_secret TEXT,
                totp_enabled INTEGER DEFAULT 0,
                totp_setup_done INTEGER DEFAULT 0,
                totp_remember_days INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS login_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                at TEXT NOT NULL,
                username_input TEXT,
                user_id INTEGER,
                username TEXT,
                success INTEGER NOT NULL DEFAULT 0,
                event_type TEXT,
                reason TEXT,
                ip TEXT,
                country TEXT,
                device TEXT,
                user_agent TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_login_audit_at ON login_audit(at);
            CREATE INDEX IF NOT EXISTS idx_login_audit_user_id ON login_audit(user_id);
            CREATE INDEX IF NOT EXISTS idx_login_audit_success ON login_audit(success);

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS user_folder_access (
                user_id INTEGER NOT NULL,
                folder_path TEXT NOT NULL,
                permission TEXT DEFAULT 'view',
                created_at TEXT NOT NULL,
                PRIMARY KEY(user_id, folder_path),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_user_folder_access_user ON user_folder_access(user_id);

            CREATE TABLE IF NOT EXISTS share_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                token_plain TEXT,
                share_name TEXT,
                folder_path TEXT NOT NULL,
                can_upload INTEGER DEFAULT 0,
                can_delete INTEGER DEFAULT 0,
                require_visitor_name INTEGER DEFAULT 0,
                link_use_duckdns INTEGER DEFAULT 0,
                password_hash TEXT,
                expires_at TEXT,
                revoked INTEGER DEFAULT 0,
                created_by_user_id INTEGER,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                FOREIGN KEY(created_by_user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS share_link_folders (
                share_id INTEGER NOT NULL,
                folder_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(share_id, folder_path),
                FOREIGN KEY(share_id) REFERENCES share_links(id)
            );
            CREATE INDEX IF NOT EXISTS idx_share_links_folder ON share_links(folder_path);
            CREATE INDEX IF NOT EXISTS idx_share_links_expires ON share_links(expires_at);
            CREATE INDEX IF NOT EXISTS idx_share_link_folders_share ON share_link_folders(share_id);
            
            -- Persisted folder preview selections (for uniform folder thumbnails)
            CREATE TABLE IF NOT EXISTS folder_previews (
                folder_path TEXT PRIMARY KEY,
                previews_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            -- Owner of private folders (visibility restricted unless ACL grants access)
            CREATE TABLE IF NOT EXISTS folder_owners (
                folder_path TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL
            );
            """
        )
        conn.commit()
        # Simple migration for old DBs
        # Add people.hidden if missing
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(people)").fetchall()]  # type: ignore[index]
            if "hidden" not in cols:
                conn.execute("ALTER TABLE people ADD COLUMN hidden INTEGER DEFAULT 0")
                conn.commit()
        except Exception:
            pass
        # Add people.centroid_json if missing (for face training)
        try:
            cols2 = [r[1] for r in conn.execute("PRAGMA table_info(people)").fetchall()]  # type: ignore[index]
            if "centroid_json" not in cols2:
                conn.execute("ALTER TABLE people ADD COLUMN centroid_json TEXT")
                conn.commit()
        except Exception:
            pass
        # Add faces.frame_sec if missing (video face thumbnails need the source frame timestamp)
        try:
            face_cols = [r[1] for r in conn.execute("PRAGMA table_info(faces)").fetchall()]  # type: ignore[index]
            if "frame_sec" not in face_cols:
                conn.execute("ALTER TABLE faces ADD COLUMN frame_sec REAL")
                conn.commit()
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN totp_secret TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN totp_enabled INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN totp_setup_done INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN totp_remember_days INTEGER DEFAULT 0")
        except Exception:
            pass
        # Add role column if missing and backfill values from is_admin
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN hub_user_id INTEGER")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN hub_synced_at TEXT")
        except Exception:
            pass
        try:
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_hub_user_id ON users(hub_user_id) WHERE hub_user_id IS NOT NULL")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN ui_language TEXT DEFAULT 'da'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN search_language TEXT DEFAULT 'da'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN theme_mode TEXT DEFAULT 'system'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE share_links ADD COLUMN password_hash TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE share_links ADD COLUMN token_plain TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE share_links ADD COLUMN link_use_duckdns INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE share_links ADD COLUMN share_name TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE photos ADD COLUMN uploaded_by TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE photos ADD COLUMN ai_desc_tags TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE photos ADD COLUMN ai_desc_caption TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE photos ADD COLUMN phash_dct TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE photos ADD COLUMN dhash TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE photos ADD COLUMN ahash TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE photos ADD COLUMN faces_indexed_at TEXT")
        except Exception:
            pass
        try:
            conn.execute(
                """
                UPDATE photos
                SET faces_indexed_at=COALESCE(NULLIF(faces_indexed_at, ''), last_scanned_at, imported_at, ?)
                WHERE COALESCE(people_count, 0) > 0
                  AND (faces_indexed_at IS NULL OR TRIM(faces_indexed_at) = '')
                """,
                (now_iso(),),
            )
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_photos_phash_dct ON photos(phash_dct)")
        except Exception:
            pass
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_photos_dhash ON photos(dhash)")
        except Exception:
            pass
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_photos_ahash ON photos(ahash)")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE share_links ADD COLUMN require_visitor_name INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE login_audit ADD COLUMN country TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE login_audit ADD COLUMN device TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE login_audit ADD COLUMN user_agent TEXT")
        except Exception:
            pass
        # Add per-folder permission for user_folder_access
        try:
            conn.execute("ALTER TABLE user_folder_access ADD COLUMN permission TEXT DEFAULT 'view'")
        except Exception:
            pass
        try:
            # Backfill NULL/empty permissions to 'view'
            conn.execute("UPDATE user_folder_access SET permission='view' WHERE permission IS NULL OR TRIM(permission)='' ")
        except Exception:
            pass
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS share_link_folders (
                    share_id INTEGER NOT NULL,
                    folder_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(share_id, folder_path),
                    FOREIGN KEY(share_id) REFERENCES share_links(id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_share_link_folders_share ON share_link_folders(share_id)")
            conn.commit()
        except Exception:
            pass
        try:
            share_cols = [r[1] for r in conn.execute("PRAGMA table_info(share_links)").fetchall()]  # type: ignore[index]
            has_token_plain = "token_plain" in share_cols
            has_token_hash = "token_hash" in share_cols
            has_legacy_token = "token" in share_cols
            if has_token_plain and has_legacy_token:
                conn.execute(
                    """
                    UPDATE share_links
                    SET token_plain = token
                    WHERE (token_plain IS NULL OR TRIM(token_plain)='')
                      AND token IS NOT NULL
                      AND TRIM(token)<>''
                    """
                )
            if has_token_hash and has_legacy_token:
                legacy_rows = conn.execute(
                    """
                    SELECT id, token FROM share_links
                    WHERE (token_hash IS NULL OR TRIM(token_hash)='')
                      AND token IS NOT NULL
                      AND TRIM(token)<>''
                    """
                ).fetchall()
                for lr in legacy_rows:
                    token_raw = str(lr["token"] or "").strip()
                    token_hash = _share_token_digest(token_raw)
                    if not token_hash:
                        continue
                    try:
                        conn.execute("UPDATE share_links SET token_hash=? WHERE id=?", (token_hash, int(lr["id"])))
                    except Exception:
                        continue
            conn.execute(
                """
                INSERT OR IGNORE INTO share_link_folders(share_id, folder_path, created_at)
                SELECT id, folder_path, COALESCE(created_at, ?)
                FROM share_links
                WHERE folder_path IS NOT NULL AND TRIM(folder_path)<>''
                """,
                (now_iso(),),
            )
            conn.execute(
                """
                UPDATE share_links
                SET share_name = ('uploads/' || folder_path)
                WHERE (share_name IS NULL OR TRIM(share_name)='')
                  AND folder_path IS NOT NULL
                  AND TRIM(folder_path)<>''
                """
            )
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute("UPDATE users SET role='admin' WHERE (role IS NULL OR role='') AND is_admin=1")
            conn.execute("UPDATE users SET role='user' WHERE (role IS NULL OR role='') AND is_admin=0")
            conn.execute("UPDATE users SET ui_language='da' WHERE ui_language IS NULL OR TRIM(ui_language)='' OR LOWER(ui_language) NOT IN ('da','en')")
            conn.execute("UPDATE users SET search_language='da' WHERE search_language IS NULL OR TRIM(search_language)='' OR LOWER(search_language) NOT IN ('da','en')")
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat_rounded INTEGER NOT NULL,
                    lon_rounded INTEGER NOT NULL,
                    observed_hour TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(lat_rounded, lon_rounded, observed_hour, provider)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_weather_cache_key ON weather_cache(lat_rounded, lon_rounded, observed_hour, provider)")
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS place_geocode_cache (
                    query_key TEXT PRIMARY KEY,
                    city TEXT,
                    country TEXT,
                    latitude REAL,
                    longitude REAL,
                    provider TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        except Exception:
            pass

        # Seed defaults for AI settings if not present
        try:
            row = conn.execute("SELECT value FROM settings WHERE key='ai_enabled'").fetchone()
            if not row:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_enabled", "1" if AI_ENV_ENABLED_DEFAULT else "0"))
            row2 = conn.execute("SELECT value FROM settings WHERE key='ai_auto_ingest'").fetchone()
            if not row2:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_auto_ingest", "1" if AI_ENV_AUTO_INGEST_DEFAULT else "0"))
            row2a = conn.execute("SELECT value FROM settings WHERE key='ai_desc_auto_ingest'").fetchone()
            if not row2a:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_desc_auto_ingest", "1" if AI_DESC_ENV_AUTO_INGEST_DEFAULT else "0"))
            row2aa = conn.execute("SELECT value FROM settings WHERE key='ai_desc_model'").fetchone()
            if not row2aa:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_desc_model", AI_DESC_MODEL_ENV_DEFAULT))
            row2ab = conn.execute("SELECT value FROM settings WHERE key='ai_desc_external_enabled'").fetchone()
            if not row2ab:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_desc_external_enabled", "0"))
            row2ac = conn.execute("SELECT value FROM settings WHERE key='ai_desc_external_folders'").fetchone()
            if not row2ac:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_desc_external_folders", "[]"))
            row2ad = conn.execute("SELECT value FROM settings WHERE key='ai_desc_external_tokens'").fetchone()
            if not row2ad:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_desc_external_tokens", "[]"))
            row2b = conn.execute("SELECT value FROM settings WHERE key='faces_auto_index'").fetchone()
            if not row2b:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("faces_auto_index", "1" if FACES_ENV_AUTO_INDEX_DEFAULT else "0"))
            row2c = conn.execute("SELECT value FROM settings WHERE key='ai_ingest_throttle_sec'").fetchone()
            if not row2c:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("ai_ingest_throttle_sec", str(AI_INGEST_THROTTLE_SEC)))
            row2d = conn.execute("SELECT value FROM settings WHERE key='faces_index_throttle_sec'").fetchone()
            if not row2d:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("faces_index_throttle_sec", str(FACES_INDEX_THROTTLE_SEC)))
            row3 = conn.execute("SELECT value FROM settings WHERE key='upload_destination'").fetchone()
            if not row3:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("upload_destination", UPLOAD_DEST_DEFAULT))
            row4 = conn.execute("SELECT value FROM settings WHERE key='upload_subdir'").fetchone()
            if not row4:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("upload_subdir", ""))
            row5 = conn.execute("SELECT value FROM settings WHERE key='upload_subdir_uploads'").fetchone()
            if not row5:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("upload_subdir_uploads", ""))
            row6 = conn.execute("SELECT value FROM settings WHERE key='upload_subdir_library'").fetchone()
            if not row6:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("upload_subdir_library", ""))
            row7 = conn.execute("SELECT value FROM settings WHERE key='upload_workflow_mode'").fetchone()
            if not row7:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("upload_workflow_mode", UPLOAD_WORKFLOW_MODE_DEFAULT))
            row7a = conn.execute("SELECT value FROM settings WHERE key='mov_convert_on_upload'").fetchone()
            if not row7a:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("mov_convert_on_upload", "1" if MOV_CONVERT_ON_UPLOAD_DEFAULT else "0"))
            row7b = conn.execute("SELECT value FROM settings WHERE key='raw_convert_on_upload'").fetchone()
            if not row7b:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", ("raw_convert_on_upload", "1" if RAW_CONVERT_ON_UPLOAD_DEFAULT else "0"))
            row8 = conn.execute("SELECT value FROM settings WHERE key=?", (UPLOAD_ALLOWED_EXTENSIONS_SETTING,)).fetchone()
            if not row8:
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", (UPLOAD_ALLOWED_EXTENSIONS_SETTING, json.dumps(sorted(SUPPORTED_EXTS))))
            conn.commit()
        except Exception:
            pass


DB_BOOTSTRAP_LOCK = threading.Lock()
DB_BOOTSTRAP_READY = False


def ensure_runtime_bootstrap() -> None:
    """One-time runtime bootstrap for DB schema and required data dirs."""
    global DB_BOOTSTRAP_READY
    if DB_BOOTSTRAP_READY:
        return
    with DB_BOOTSTRAP_LOCK:
        if DB_BOOTSTRAP_READY:
            return
        ensure_dirs()
        init_db()
        _ensure_install_state_for_existing_users()
        DB_BOOTSTRAP_READY = True


def _normalize_folder_acl_path(value: Optional[str]) -> str:
    raw = str(value or "").replace("\\", "/").strip()
    while "//" in raw:
        raw = raw.replace("//", "/")
    raw = raw.lstrip("/").rstrip("/")
    if raw in {"", "."}:
        return ""
    parts = [p.strip() for p in raw.split("/") if p.strip()]
    if any(p == ".." for p in parts):
        raise ValueError("invalid_folder")
    return "/".join(parts)


def _normalize_rel_path_for_acl(value: Optional[str]) -> str:
    rel = str(value or "").replace("\\", "/")
    while "//" in rel:
        rel = rel.replace("//", "/")
    rel = rel.lstrip("/")
    # Collapse framework storage roots so ACLs like 'uploads/foo' also cover
    # photos stored in 'uploads/originals/foo' and 'uploads/converted/foo'.
    if rel.startswith("uploads/originals/"):
        rel = "uploads/" + rel[len("uploads/originals/"):]
    elif rel.startswith("uploads/converted/"):
        rel = "uploads/" + rel[len("uploads/converted/"):]
    return rel


def _list_all_photo_folders(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT rel_path FROM photos").fetchall()
    folders: set[str] = set()

    # Include real upload folders from disk so admins can assign access
    # even before images are indexed in those folders.
    try:
        upload_dirs = _list_upload_subdirs(UPLOAD_DIR, limit=2000)
        for sub in upload_dirs:
            clean = _normalize_folder_acl_path(sub)
            if clean:
                folders.add(f"uploads/{clean}")
    except Exception:
        pass

    for r in rows:
        rel = _normalize_rel_path_for_acl(r["rel_path"])
        if not rel:
            continue
        # Canonicalize uploads paths so converted/originals are shown under the user folder
        rel_for_folder = rel
        if rel.startswith("uploads/originals/"):
            parts = rel.split("/", 2)
            if len(parts) >= 3:
                rel_for_folder = f"uploads/{parts[2]}"
            else:
                rel_for_folder = "uploads"
        elif rel.startswith("uploads/converted/"):
            parts = rel.split("/", 2)
            if len(parts) >= 3:
                rel_for_folder = f"uploads/{parts[2]}"
            else:
                rel_for_folder = "uploads"
        parent = rel_for_folder.rsplit("/", 1)[0] if "/" in rel_for_folder else ""
        if not parent:
            continue
        parts = [p for p in parent.split("/") if p]
        acc = ""
        for part in parts:
            acc = f"{acc}/{part}" if acc else part
            if acc == "uploads":
                continue
            folders.add(acc)
    return sorted(folders, key=lambda x: x.lower())


def _set_user_allowed_folders(conn: sqlite3.Connection, user_id: int, folders: list) -> list[dict]:
    """Persist per-folder access with permissions.
    Accepts list of strings (legacy: folder paths => 'view') or list of dicts
    like {"folder": "uploads/X", "permission": "view|upload|edit"}.
    Returns reduced list of {folder_path, permission} after normalization.
    """
    def _extract(item: object) -> tuple[str, str]:
        # Normalize various payload shapes
        if isinstance(item, str):
            return (_normalize_folder_acl_path(item), "view")
        try:
            # Support keys: folder, folder_path, path
            folder = None
            if isinstance(item, dict):
                folder = item.get("folder") or item.get("folder_path") or item.get("path")
                perm = str(item.get("permission") or item.get("perm") or "view").strip().lower()
            else:
                folder = None
                perm = "view"
            p = _normalize_folder_acl_path(folder)
            if perm not in {"view", "upload", "edit", "manage", "delete"}:
                perm = "view"
            # Collapse synonyms
            if perm in {"manage", "delete"}:
                perm = "edit"
            return (p, perm)
        except Exception:
            return ("", "view")

    cleaned: list[tuple[str, str]] = []
    for it in (folders or []):
        p, perm = _extract(it)
        if p:
            cleaned.append((p, perm))
    # Build final permission map keeping the highest permission for duplicates
    perm_rank = {"view": 1, "upload": 2, "edit": 3}
    def max_perm(a: str, b: str) -> str:
        return a if perm_rank.get(a, 0) >= perm_rank.get(b, 0) else b

    cleaned = sorted(set(cleaned), key=lambda x: (x[0].count("/"), x[0].lower()))
    perm_map: dict[str, str] = {}
    for path, perm in cleaned:
        cur = perm_map.get(path)
        perm_map[path] = perm if cur is None else max_perm(cur, perm)
        # Ensure all ancestors are at least 'view' to allow navigating to this folder
        parent = path.rsplit("/", 1)[0] if "/" in path else ""
        while parent:
            # Do NOT seed the absolute root 'uploads' with view, as that
            # would unintentionally grant access to all sibling folders.
            if parent == "uploads":
                break
            if parent not in perm_map:
                perm_map[parent] = "view"
            parent = parent.rsplit("/", 1)[0] if "/" in parent else ""

    reduced = sorted([(p, perm_map[p]) for p in perm_map.keys()], key=lambda x: x[0].lower())

    conn.execute("DELETE FROM user_folder_access WHERE user_id=?", (user_id,))
    if reduced:
        now = now_iso()
        conn.executemany(
            "INSERT INTO user_folder_access(user_id, folder_path, permission, created_at) VALUES(?,?,?,?)",
            [(user_id, p, perm, now) for (p, perm) in reduced],
        )
    return [{"folder_path": p, "permission": perm} for (p, perm) in reduced]


def _get_user_allowed_folders(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT folder_path, COALESCE(permission,'view') AS permission FROM user_folder_access WHERE user_id=? ORDER BY folder_path COLLATE NOCASE",
        (user_id,),
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        try:
            p = _normalize_folder_acl_path(r["folder_path"]) 
        except Exception:
            continue
        if not p:
            continue
        perm = str(r["permission"] or "view").strip().lower()
        if perm not in {"view", "upload", "edit"}:
            perm = "view"
        out.append({"folder_path": p, "permission": perm})
    return out


def _current_user_acl_prefixes(conn: Optional[sqlite3.Connection] = None) -> Optional[list[str]]:
    try:
        if getattr(current_user, "is_admin", False):
            return None
        uid = int(getattr(current_user, "id", 0) or 0)
        if uid <= 0:
            return None
    except Exception:
        return None

    def _load(c: sqlite3.Connection) -> list[str]:
        items = _get_user_allowed_folders(c, uid)
        out: list[str] = []
        for it in items:
            p = _normalize_folder_acl_path((it or {}).get("folder_path")) if isinstance(it, dict) else _normalize_folder_acl_path(it)
            # Ignore accidental or legacy entries that grant the root 'uploads'
            # folder, which would make all subfolders visible.
            if p and p != "uploads":
                # Canonicalize to rel path under 'uploads/' so checks align
                canon = p if p.startswith("uploads/") else f"uploads/{p}"
                out.append(canon)
        return out

    if conn is not None:
        rows = _load(conn)
    else:
        with closing(get_conn()) as conn2:
            rows = _load(conn2)
    if not rows:
        # No explicit ACLs â†’ no access (non-admin users)
        return []
    return rows


def _is_rel_path_allowed_for_current_user(rel_path: Optional[str], conn: Optional[sqlite3.Connection] = None) -> bool:
    rel = _normalize_rel_path_for_acl(rel_path)
    if not rel:
        return False
    prefixes = _current_user_acl_prefixes(conn)
    if prefixes is None:
        return True
    for p in prefixes:
        if rel == p or rel.startswith(p + "/"):
            return True
    return False


def _folder_owner_user_id_for_rel(rel_path: Optional[str], conn: Optional[sqlite3.Connection] = None) -> Optional[int]:
    rel = _normalize_rel_path_for_acl(rel_path)
    if not rel:
        return None
    try:
        if conn is None:
            with closing(get_conn()) as c:
                row = c.execute(
                    "SELECT user_id FROM folder_owners WHERE ? = folder_path OR ? LIKE folder_path || '/%' ORDER BY LENGTH(folder_path) DESC LIMIT 1",
                    (rel, rel),
                ).fetchone()
        else:
            row = conn.execute(
                "SELECT user_id FROM folder_owners WHERE ? = folder_path OR ? LIKE folder_path || '/%' ORDER BY LENGTH(folder_path) DESC LIMIT 1",
                (rel, rel),
            ).fetchone()
        if row:
            return int(row[0])
    except Exception:
        return None
    return None


def _is_rel_visible_for_current_user(rel_path: Optional[str], conn: Optional[sqlite3.Connection] = None) -> bool:
    # Admins can always see
    try:
        if getattr(current_user, "is_admin", False):
            return True
    except Exception:
        pass
    owner_uid = _folder_owner_user_id_for_rel(rel_path, conn)
    # If no owner, fall back to ACL logic only
    if owner_uid is None:
        return _is_rel_path_allowed_for_current_user(rel_path, conn)
    # Owner can always see
    try:
        if int(getattr(current_user, "id", 0) or 0) == int(owner_uid):
            return True
    except Exception:
        pass
    # Not owner: require explicit ACL match
    return _is_rel_path_allowed_for_current_user(rel_path, conn)


def _filter_public_items_by_current_user_acl(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    if not items:
        return items
    out: list[Dict[str, Any]] = []
    for item in items:
        rel = _normalize_rel_path_for_acl(item.get("rel_path"))
        if not rel:
            continue
        if _is_rel_visible_for_current_user(rel):
            out.append(item)
    return out


def _filter_folders_by_current_user_acl(folders: list[str], conn: Optional[sqlite3.Connection] = None) -> list[str]:
    out: list[str] = []
    for raw in folders:
        try:
            folder = _normalize_folder_acl_path(raw)
        except Exception:
            continue
        # Always include root label
        if not folder:
            out.append("")
            continue
        # Map bare subfolder paths to full rel under uploads for ACL checks
        rel_check = folder
        if folder and not folder.startswith("uploads/"):
            rel_check = f"uploads/{folder}"
        if _is_rel_visible_for_current_user(rel_check, conn):
            out.append(folder)
    # Only include root label when there is at least one visible folder
    if out and "" not in out:
        out.insert(0, "")
    seen: set[str] = set()
    deduped: list[str] = []
    for f in out:
        if f in seen:
            continue
        seen.add(f)
        deduped.append(f)
    return deduped


def _current_user_folder_permission_for_rel(rel_path: Optional[str], conn: Optional[sqlite3.Connection] = None) -> Optional[str]:
    """Return the effective permission for the current user on a rel path under uploads.
    Values: 'edit' > 'upload' > 'view'. None if no access.
    Admins and owners receive 'edit'.
    """
    rel = _normalize_rel_path_for_acl(rel_path)
    if not rel:
        return None
    try:
        if getattr(current_user, "is_admin", False):
            return "edit"
    except Exception:
        pass
    owner_uid = _folder_owner_user_id_for_rel(rel, conn)
    try:
        if owner_uid is not None and int(getattr(current_user, "id", 0) or 0) == int(owner_uid):
            return "edit"
    except Exception:
        pass
    # Load ACL rows and find the most specific match
    try:
        if conn is None:
            with closing(get_conn()) as c:
                rows = _get_user_allowed_folders(c, int(getattr(current_user, "id", 0) or 0))
        else:
            rows = _get_user_allowed_folders(conn, int(getattr(current_user, "id", 0) or 0))
    except Exception:
        rows = []
    best: Optional[tuple[str, str]] = None
    for r in rows:
        try:
            p = _normalize_folder_acl_path(r.get("folder_path"))
            perm = str(r.get("permission") or "view").strip().lower()
        except Exception:
            continue
        if not p or perm not in {"view", "upload", "edit"}:
            continue
        if rel == p or rel.startswith(p + "/"):
            if best is None or len(p) > len(best[0]):
                best = (p, perm)
    return best[1] if best else None


def _perm_allows(perm: Optional[str], required: str) -> bool:
    order = {"view": 1, "upload": 2, "edit": 3}
    a = order.get(str(perm or "").strip().lower(), 0)
    b = order.get(str(required or "").strip().lower(), 0)
    return a >= b


@app.before_request
def enforce_login_for_app():
    # Allow static assets without touching DB/bootstrap.
    if request.endpoint == "static" or (request.endpoint or "").startswith("static"):
        return None

    # Ensure DB/schema exists before auth/setup decisions.
    ensure_runtime_bootstrap()

    # Allow login/setup and selected public endpoints without auth
    open_endpoints = {
        "login",
        "verify_2fa",
        "setup",
        "hub_login",
        "api_health",
        "api_auth_session",
        "apple_touch_icon",
        "apple_touch_icon_180",
        "apple_touch_icon_167",
        "apple_touch_icon_152",
        "apple_touch_icon_120",
        "icon_192",
        "favicon_ico",
        "favicon_32_png",
        "favicon_16_png",
        "site_webmanifest",
        "manifest_webmanifest",
        "browserconfig_xml",
        "shared_folder_view",
        "api_share_info",
        "api_share_photos",
        "api_share_thumb",
        "api_share_viewable",
        "api_share_original",
        "api_share_auth",
        "api_share_upload",
        # Share-link TUS endpoints must bypass normal login
        "api_share_tus_options",
        "api_share_tus_create",
        "api_share_tus_head",
        "api_share_tus_file",
        "api_share_tus_file_override",
        "api_share_delete",
        "api_frame_feed",
        "api_frame_heartbeat",
        "api_frame_viewable",
        "api_frame_status_card",
        "api_frame_update_package",
        "api_frame_uploaded_update_package",
        "api_ai_describe_external_ping",
        "api_ai_describe_external_next",
        "api_ai_describe_external_image",
        "api_ai_describe_external_result",
    }
    if request.endpoint in open_endpoints:
        return None
    # Bootstrap: if no users exist, redirect to setup unless this install already ran.
    try:
        user_count = users_count()
        if user_count > 0:
            _ensure_install_state_for_existing_users()
        elif _fjordhub_managed():
            if request.endpoint not in {"login", "verify_2fa", "api_health"}:
                return redirect(url_for("login"))
            return None
        elif _install_state_exists() and request.endpoint not in {"setup", "api_health"}:
            return _setup_locked_response()
        elif request.endpoint != "setup":
            return redirect(url_for("setup"))
    except Exception:
        pass
    # Everything else (index + /api/* + file routes) requires auth
    if not current_user.is_authenticated:
        # For API calls, return 401 to avoid HTML in fetch
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return redirect(url_for("login", next=request.path))
    # Enforce initial 2FA setup only when 2FA is enabled but not completed
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT totp_enabled, totp_setup_done FROM users WHERE id= ?", (current_user.id,)).fetchone()
        if row and int(row["totp_enabled"] or 0) == 1 and int(row["totp_setup_done"] or 0) == 0 and request.endpoint not in {"setup_2fa", "logout", "static"}:
            return redirect(url_for("setup_2fa"))
    except Exception:
        pass


def _forbid_user_role_for_maintenance() -> Optional[Tuple[dict, int]]:
    """Return (resp, code) when current user is basic 'user' and tries to access maint/log features."""
    try:
        role = getattr(current_user, "role", "user")
    except Exception:
        role = "user"
    if role == "user":
        return ({"ok": False, "error": "Forbidden"}, 403)
    return None


def _normalize_language(value: Optional[str], default: str = DEFAULT_UI_LANGUAGE) -> str:
    lang = str(value or "").strip().lower()
    if lang in LANG_CHOICES:
        return lang
    return default


def _current_user_pref_languages() -> tuple[str, str]:
    ui_lang = _normalize_language(getattr(current_user, "ui_language", None), DEFAULT_UI_LANGUAGE)
    search_lang = _normalize_language(getattr(current_user, "search_language", None), DEFAULT_SEARCH_LANGUAGE)
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT ui_language, search_language FROM users WHERE id=?", (current_user.id,)).fetchone()
        if row:
            ui_lang = _normalize_language(row["ui_language"], ui_lang)
            search_lang = _normalize_language(row["search_language"], search_lang)
    except Exception:
        pass
    return (ui_lang, search_lang)


# --- App settings helpers ---
def _get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            if not row:
                return default
            try:
                return row["value"]  # sqlite3.Row
            except Exception:
                return row[0]
    except Exception:
        return default


def _set_setting(key: str, value: str) -> None:
    try:
        with closing(get_conn()) as conn:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            conn.commit()
    except Exception:
        pass


def _get_setting_bool(key: str, default: bool = False) -> bool:
    v = _get_setting(key, None)
    if v is None:
        return default
    return str(v).strip() not in {"0", "false", "False", "no", "off", ""}


def _parse_throttle_value(value: Any, default: float) -> float:
    try:
        v = float(value)
    except Exception:
        v = float(default)
    if v < 0:
        v = 0.0
    if v > 2.0:
        v = 2.0
    return round(v, 3)


def _get_setting_throttle(key: str, default: float) -> float:
    return _parse_throttle_value(_get_setting(key, str(default)), default)


AI_DESC_EXTERNAL_CLAIM_TTL_SEC = 30 * 60


def ai_feature_enabled() -> bool:
    return _get_setting_bool("ai_enabled", AI_ENV_ENABLED_DEFAULT)


def ai_auto_ingest_enabled() -> bool:
    return _get_setting_bool("ai_auto_ingest", AI_ENV_AUTO_INGEST_DEFAULT)


def heic_convert_on_upload_enabled() -> bool:
    # Controlled by setting; default comes from env (HEIC_CONVERT_ON_UPLOAD_DEFAULT)
    return _get_setting_bool("heic_convert_on_upload", HEIC_CONVERT_ON_UPLOAD_DEFAULT)


def mov_convert_on_upload_enabled() -> bool:
    return _get_setting_bool("mov_convert_on_upload", MOV_CONVERT_ON_UPLOAD_DEFAULT)


def raw_convert_on_upload_enabled() -> bool:
    return _get_setting_bool("raw_convert_on_upload", RAW_CONVERT_ON_UPLOAD_DEFAULT)


def mov_keep_originals_enabled() -> bool:
    # default True to keep safety unless explicitly disabled
    return _get_setting_bool("mov_keep_originals", True)


def heic_keep_originals_enabled() -> bool:
    # default True to keep safety unless explicitly disabled
    return _get_setting_bool("heic_keep_originals", True)


def raw_keep_originals_enabled() -> bool:
    # default True to keep safety unless explicitly disabled
    return _get_setting_bool("raw_keep_originals", True)


def ai_desc_auto_ingest_enabled() -> bool:
    if ai_desc_external_enabled():
        return False
    return _get_setting_bool("ai_desc_auto_ingest", AI_DESC_ENV_AUTO_INGEST_DEFAULT)


def ai_desc_external_enabled() -> bool:
    return _get_setting_bool("ai_desc_external_enabled", False)


def _generate_ai_desc_external_token() -> str:
    return "fldesc_" + secrets.token_urlsafe(32)


def _ai_desc_external_token_records() -> list[Dict[str, Any]]:
    raw = _get_setting("ai_desc_external_tokens", "[]")
    try:
        parsed = json.loads(str(raw or "[]"))
    except Exception:
        parsed = []
    if not isinstance(parsed, list):
        parsed = []

    out: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in parsed:
        if not isinstance(item, dict):
            continue
        token = str(item.get("token") or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        link_id = str(item.get("id") or "").strip() or hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
        out.append({
            "id": link_id,
            "token": token,
            "created_at": str(item.get("created_at") or "").strip() or now_iso(),
            "label": str(item.get("label") or "").strip(),
        })

    legacy = str(_get_setting("ai_desc_external_token", "") or "").strip()
    if legacy and legacy not in seen:
        out.append({
            "id": hashlib.sha256(legacy.encode("utf-8")).hexdigest()[:16],
            "token": legacy,
            "created_at": now_iso(),
            "label": "Ekstern AI behandling",
        })
    return out


def _save_ai_desc_external_token_records(records: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    cleaned: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            continue
        token = str(item.get("token") or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        cleaned.append({
            "id": str(item.get("id") or "").strip() or secrets.token_urlsafe(8),
            "token": token,
            "created_at": str(item.get("created_at") or "").strip() or now_iso(),
            "label": str(item.get("label") or "").strip(),
        })
    _set_setting("ai_desc_external_tokens", json.dumps(cleaned, ensure_ascii=False))
    current = str(_get_setting("ai_desc_external_token", "") or "").strip()
    if current not in {item["token"] for item in cleaned}:
        _set_setting("ai_desc_external_token", cleaned[-1]["token"] if cleaned else "")
    return cleaned


def _add_ai_desc_external_token(label: str = "") -> str:
    token = _generate_ai_desc_external_token()
    records = _ai_desc_external_token_records()
    records.append({
        "id": secrets.token_urlsafe(8),
        "token": token,
        "created_at": now_iso(),
        "label": str(label or "").strip(),
    })
    _save_ai_desc_external_token_records(records)
    _set_setting("ai_desc_external_token", token)
    return token


def _ai_desc_external_token() -> str:
    current = str(_get_setting("ai_desc_external_token", "") or "").strip()
    records = _ai_desc_external_token_records()
    active = {str(item.get("token") or "").strip() for item in records}
    if current and current in active:
        return current
    if records:
        token = str(records[-1].get("token") or "").strip()
        if token:
            _set_setting("ai_desc_external_token", token)
            return token
    return current


def _ensure_ai_desc_external_token() -> str:
    token = _ai_desc_external_token()
    if token:
        _save_ai_desc_external_token_records(_ai_desc_external_token_records())
        return token
    return _add_ai_desc_external_token()


def _ai_desc_external_public_links() -> list[Dict[str, Any]]:
    links: list[Dict[str, Any]] = []
    for item in _ai_desc_external_token_records():
        token = str(item.get("token") or "").strip()
        if not token:
            continue
        links.append({
            "id": str(item.get("id") or "").strip(),
            "created_at": str(item.get("created_at") or "").strip(),
            "label": str(item.get("label") or "").strip(),
            "token_hint": token[-6:],
            "connection_url": _ai_desc_external_connection_url(token),
            "current": hmac.compare_digest(token, _ai_desc_external_token()),
        })
    return links


def _ai_desc_external_auth_ok() -> bool:
    supplied = str(request.headers.get("X-API-Token") or request.headers.get("X-FjordLens-Token") or "").strip()
    auth = str(request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        supplied = auth.split(" ", 1)[1].strip()
    if not supplied:
        supplied = str(request.args.get("token") or "").strip()
    if not supplied:
        return False
    for item in _ai_desc_external_token_records():
        expected = str(item.get("token") or "").strip()
        if expected and hmac.compare_digest(supplied, expected):
            return True
    return False


def _ai_desc_external_require_auth():
    if not _ai_desc_external_auth_ok():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    return None


def _normalize_ai_desc_external_folders(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            parsed = [value]
    elif isinstance(value, (list, tuple, set)):
        parsed = list(value)
    else:
        parsed = []

    out: list[str] = []
    for item in parsed:
        try:
            folder = _normalize_folder_acl_path(item)
        except Exception:
            continue
        if folder and folder not in out:
            out.append(folder)
    return sorted(out, key=lambda x: x.lower())


def _ai_desc_external_folders() -> list[str]:
    return _normalize_ai_desc_external_folders(_get_setting("ai_desc_external_folders", "[]"))


def _set_ai_desc_external_folders(folders: list[str]) -> list[str]:
    cleaned = _normalize_ai_desc_external_folders(folders)
    _set_setting("ai_desc_external_folders", json.dumps(cleaned, ensure_ascii=False))
    return cleaned


def _ai_desc_external_rel_allowed(rel_path: str, folders: list[str]) -> bool:
    if not folders:
        return False
    rel = _normalize_rel_path_for_acl(rel_path)
    if not rel:
        return False
    for folder in folders:
        f = _normalize_folder_acl_path(folder)
        if f and (rel == f or rel.startswith(f + "/")):
            return True
    return False


def _ai_desc_external_missing_where() -> str:
    return """
        (
            ai_desc_tags IS NULL
            OR TRIM(ai_desc_tags) = ''
            OR TRIM(ai_desc_tags) IN ('[]', 'null')
            OR ai_desc_caption IS NULL
            OR TRIM(ai_desc_caption) = ''
        )
    """


def _parse_utc_iso_ts(raw: Any) -> Optional[float]:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text).timestamp()
    except Exception:
        return None


def _ai_desc_external_claim_is_fresh(meta: Dict[str, Any], now_ts: Optional[float] = None) -> bool:
    ai_meta = meta.get("ai") if isinstance(meta.get("ai"), dict) else {}
    claimed_at = _parse_utc_iso_ts((ai_meta or {}).get("desc_external_claimed_at"))
    if claimed_at is None:
        return False
    now_value = float(now_ts if now_ts is not None else time.time())
    return (now_value - claimed_at) < AI_DESC_EXTERNAL_CLAIM_TTL_SEC


def _mark_ai_desc_external_claim(conn: sqlite3.Connection, row: sqlite3.Row, worker: str = "") -> None:
    meta = _json_object(row["metadata_json"] if "metadata_json" in row.keys() else None)
    ai_meta = dict(meta.get("ai") or {})
    ai_meta["desc_external_claimed_at"] = now_iso()
    if worker:
        ai_meta["desc_external_worker"] = str(worker)[:120]
    meta["ai"] = ai_meta
    conn.execute("UPDATE photos SET metadata_json=? WHERE id=?", (json.dumps(meta, ensure_ascii=False), int(row["id"])))


def _mark_ai_desc_external_error(conn: sqlite3.Connection, photo_id: int, error: str) -> None:
    row = conn.execute("SELECT metadata_json FROM photos WHERE id=?", (photo_id,)).fetchone()
    meta = _json_object(row["metadata_json"] if row else None)
    ai_meta = dict(meta.get("ai") or {})
    ai_meta["desc_external_error"] = str(error or "")[:500]
    ai_meta["desc_external_error_at"] = now_iso()
    meta["ai"] = ai_meta
    conn.execute("UPDATE photos SET metadata_json=? WHERE id=?", (json.dumps(meta, ensure_ascii=False), photo_id))


def _mark_ai_desc_external_stored(conn: sqlite3.Connection, photo_id: int, worker: str = "") -> None:
    row = conn.execute("SELECT metadata_json FROM photos WHERE id=?", (photo_id,)).fetchone()
    meta = _json_object(row["metadata_json"] if row else None)
    ai_meta = dict(meta.get("ai") or {})
    ai_meta["desc_external_source"] = "external_worker"
    ai_meta["desc_external_completed_at"] = now_iso()
    ai_meta.pop("desc_external_error", None)
    ai_meta.pop("desc_external_error_at", None)
    if worker:
        ai_meta["desc_external_worker"] = str(worker)[:120]
    meta["ai"] = ai_meta
    conn.execute("UPDATE photos SET metadata_json=? WHERE id=?", (json.dumps(meta, ensure_ascii=False), photo_id))


def _ai_desc_external_counts(conn: sqlite3.Connection, folders: list[str]) -> Dict[str, int]:
    rows = conn.execute("SELECT rel_path, ai_desc_tags, ai_desc_caption, metadata_json FROM photos").fetchall()
    total = 0
    pending = 0
    described = 0
    ready = 0
    in_progress = 0
    unavailable = 0
    now_ts = time.time()
    for row in rows:
        if not _ai_desc_external_rel_allowed(row["rel_path"], folders):
            continue
        total += 1
        if _ai_desc_has_content(row["ai_desc_tags"], row["ai_desc_caption"]):
            described += 1
        else:
            pending += 1
            meta = _json_object(row["metadata_json"])
            if _ai_desc_external_claim_is_fresh(meta, now_ts):
                in_progress += 1
                continue
            try:
                src = _disk_path_from_rel_path(str(row["rel_path"] or ""))
                if src.exists() and src.is_file():
                    ready += 1
                else:
                    unavailable += 1
            except Exception:
                unavailable += 1
    return {
        "total": total,
        "pending": pending,
        "described": described,
        "ready": ready,
        "in_progress": in_progress,
        "unavailable": unavailable,
    }


def _ai_desc_external_connection_url(token: str) -> str:
    token = str(token or "").strip()
    if not token:
        return ""
    return f"{request.url_root.rstrip('/')}{url_for('api_ai_describe_external_ping')}?token={quote(token, safe='')}"


def _ai_desc_external_settings_payload(conn: Optional[sqlite3.Connection] = None, include_token: bool = True) -> Dict[str, Any]:
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    try:
        folders = _ai_desc_external_folders()
        available = _list_all_photo_folders(conn)
        counts = _ai_desc_external_counts(conn, folders)
        payload: Dict[str, Any] = {
            "ok": True,
            "enabled": ai_desc_external_enabled(),
            "folders": folders,
            "available_folders": available,
            "token_present": bool(_ai_desc_external_token()),
            **counts,
        }
        if include_token:
            token = _ai_desc_external_token()
            payload["token"] = token
            payload["connection_url"] = _ai_desc_external_connection_url(token)
        return payload
    finally:
        if close_conn:
            conn.close()


def ai_desc_model_enabled() -> str:
    return _normalize_ai_desc_model(_get_setting("ai_desc_model", AI_DESC_MODEL_ENV_DEFAULT))


def faces_auto_index_enabled() -> bool:
    return _get_setting_bool("faces_auto_index", FACES_ENV_AUTO_INDEX_DEFAULT)


def ai_ingest_throttle_enabled_sec() -> float:
    return _get_setting_throttle("ai_ingest_throttle_sec", AI_INGEST_THROTTLE_SEC)


def faces_index_throttle_enabled_sec() -> float:
    return _get_setting_throttle("faces_index_throttle_sec", FACES_INDEX_THROTTLE_SEC)


def _normalize_upload_workflow_mode(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"aggressive", "hard", "fast", "parallel"}:
        return UPLOAD_WORKFLOW_MODE_AGGRESSIVE
    return UPLOAD_WORKFLOW_MODE_GENTLE


def upload_workflow_mode() -> str:
    return _normalize_upload_workflow_mode(_get_setting("upload_workflow_mode", UPLOAD_WORKFLOW_MODE_DEFAULT))


def upload_workflow_is_aggressive() -> bool:
    return upload_workflow_mode() == UPLOAD_WORKFLOW_MODE_AGGRESSIVE


def _upload_workflow_settings_payload() -> Dict[str, Any]:
    mode = upload_workflow_mode()
    return {
        "ok": True,
        "mode": mode,
        "batch_size": int(UPLOAD_WORKFLOW_FACE_BATCH_SIZE),
        "thumbnails_use_gpu": bool(UPLOAD_WORKFLOW_THUMBNAILS_USE_GPU),
        "options": [UPLOAD_WORKFLOW_MODE_GENTLE, UPLOAD_WORKFLOW_MODE_AGGRESSIVE],
    }


def _default_upload_allowed_extensions() -> list[str]:
    return sorted({str(ext or "").strip().lower() for ext in SUPPORTED_EXTS if str(ext or "").strip()})


def _normalize_upload_extension(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    raw = raw.split("?", 1)[0].split("#", 1)[0].replace("\\", "/").strip()
    if "/" in raw:
        raw = raw.rsplit("/", 1)[-1]
    if raw.startswith("."):
        ext = raw
    else:
        suffix = Path(raw).suffix.lower()
        ext = suffix if suffix else f".{raw}"
    return ext if re.fullmatch(r"\.[a-z0-9]{1,16}", ext or "") else ""


def _parse_upload_extension_values(value: Any) -> list[Any]:
    if isinstance(value, str):
        return [part for part in re.split(r"[\s,;]+", value) if part]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return []


def _normalize_upload_extension_list(value: Any) -> tuple[list[str], list[str], list[str]]:
    allowed: list[str] = []
    seen: set[str] = set()
    invalid: list[str] = []
    for item in _parse_upload_extension_values(value):
        raw = str(item or "").strip()
        ext = _normalize_upload_extension(raw)
        if not ext:
            if raw:
                invalid.append(raw)
            continue
        if ext not in seen:
            seen.add(ext)
            allowed.append(ext)
    return (sorted(allowed), sorted(set(invalid)), [])


def upload_allowed_extensions() -> set[str]:
    defaults = set(_default_upload_allowed_extensions())
    raw = _get_setting(UPLOAD_ALLOWED_EXTENSIONS_SETTING, "")
    if raw is None or str(raw).strip() == "":
        return defaults
    try:
        parsed = json.loads(str(raw))
    except Exception:
        parsed = raw
    allowed, _, _ = _normalize_upload_extension_list(parsed)
    return set(allowed) if allowed else defaults


def _upload_file_types_settings_payload() -> Dict[str, Any]:
    supported = _default_upload_allowed_extensions()
    allowed = sorted(upload_allowed_extensions())
    allowed_set = set(allowed)
    blocked = [ext for ext in supported if ext not in allowed_set]
    custom = [ext for ext in allowed if ext not in set(supported)]
    return {
        "ok": True,
        "allowed_extensions": allowed,
        "blocked_extensions": blocked,
        "custom_extensions": custom,
        "default_extensions": supported,
        "supported_extensions": supported,
        "upload_accept": ",".join(allowed),
    }


def _is_upload_extension_allowed(ext: Any, allowed_exts: Optional[set[str]] = None) -> bool:
    clean = _normalize_upload_extension(ext)
    if not clean:
        return False
    allowed = allowed_exts if allowed_exts is not None else upload_allowed_extensions()
    return clean in allowed


def _blocked_upload_file_error(filename: str, ext: Any = None) -> str:
    clean = _normalize_upload_extension(ext if ext is not None else filename)
    label = clean or "uden filtype"
    name = str(filename or "").strip() or "fil"
    return f"Blokeret filtype ({label}): {name}"


def library_source_enabled() -> bool:
    return bool(ENABLE_LIBRARY_SOURCE)


def _disk_path_from_rel_path(rel_path: str) -> Path:
    rel = str(rel_path or "")
    if rel.startswith("uploads/"):
        leaf = rel.split("/", 1)[1] if "/" in rel else ""
        return UPLOAD_DIR / leaf
    return PHOTO_DIR / rel


def _photoframe_video_prepared_path(rel_path: str) -> Path:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    stem = Path(rel).with_suffix("")
    dest_rel = Path(f"{stem}_PF.mp4")
    return CONVERT_DIR / "photoframe_video" / dest_rel


def _prepare_video_for_photoframe(src: Path, rel_path: str) -> Path:
    ext = str(src.suffix or "").lower()
    if ext not in VIDEO_EXTS:
        return src
    if not PHOTOFRAME_VIDEO_PREPARE_ENABLED:
        return src
    if not src.exists():
        return src
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return src

    dest = _photoframe_video_prepared_path(rel_path)
    try:
        src_mtime = src.stat().st_mtime
    except Exception:
        src_mtime = 0.0

    try:
        if dest.exists() and dest.stat().st_size > 0 and dest.stat().st_mtime >= src_mtime:
            return dest
    except Exception:
        pass

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            PHOTOFRAME_VIDEO_PREPARE_PRESET,
            "-crf",
            str(PHOTOFRAME_VIDEO_PREPARE_CRF),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(tmp),
        ]
        subprocess.run(cmd, check=True, timeout=PHOTOFRAME_VIDEO_PREPARE_TIMEOUT_SEC)
        if (not tmp.exists()) or tmp.stat().st_size <= 0:
            raise RuntimeError("ffmpeg produced empty output")
        os.replace(tmp, dest)
        try:
            log_event("photoframe_video_prepared", rel_path=rel_path, prepared_path=str(dest))
        except Exception:
            pass
        return dest
    except Exception as e:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        try:
            log_event("error", rel_path=rel_path, error=f"photoframe_video_prepare: {e}")
        except Exception:
            pass
        return src


def _prepare_video_for_photoframe_rel(rel_path: str) -> None:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    if not rel:
        return
    if Path(rel).suffix.lower() not in VIDEO_EXTS:
        return
    src = _disk_path_from_rel_path(rel)
    if not src.exists():
        return
    _prepare_video_for_photoframe(src, rel)


def _photoframe_video_prepare_worker_loop() -> None:
    while True:
        rel_path = str(PHOTOFRAME_VIDEO_PREPARE_QUEUE.get() or "").strip()
        try:
            if rel_path:
                _prepare_video_for_photoframe_rel(rel_path)
        except Exception as e:
            try:
                log_event("error", rel_path=rel_path, error=f"photoframe_video_prepare_worker: {e}")
            except Exception:
                pass
        finally:
            with PHOTOFRAME_VIDEO_PREPARE_LOCK:
                if rel_path:
                    PHOTOFRAME_VIDEO_PREPARE_QUEUED.discard(rel_path)
            PHOTOFRAME_VIDEO_PREPARE_QUEUE.task_done()


def _ensure_photoframe_video_prepare_worker() -> None:
    global PHOTOFRAME_VIDEO_PREPARE_WORKER_STARTED
    if PHOTOFRAME_VIDEO_PREPARE_WORKER_STARTED:
        return
    with PHOTOFRAME_VIDEO_PREPARE_LOCK:
        if PHOTOFRAME_VIDEO_PREPARE_WORKER_STARTED:
            return
        threading.Thread(target=_photoframe_video_prepare_worker_loop, daemon=True).start()
        PHOTOFRAME_VIDEO_PREPARE_WORKER_STARTED = True


def _queue_photoframe_video_prepare(rel_path: str) -> bool:
    if not PHOTOFRAME_VIDEO_PREPARE_ENABLED:
        return False
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    if not rel:
        return False
    if Path(rel).suffix.lower() not in VIDEO_EXTS:
        return False
    _ensure_photoframe_video_prepare_worker()
    with PHOTOFRAME_VIDEO_PREPARE_LOCK:
        if rel in PHOTOFRAME_VIDEO_PREPARE_QUEUED:
            return False
        PHOTOFRAME_VIDEO_PREPARE_QUEUED.add(rel)
    PHOTOFRAME_VIDEO_PREPARE_QUEUE.put(rel)
    return True


def get_upload_destination() -> str:
    v = (_get_setting("upload_destination", UPLOAD_DEST_DEFAULT) or "").strip().lower()
    if v not in UPLOAD_DEST_CHOICES:
        return UPLOAD_DEST_DEFAULT
    return v


def _sanitize_folder_part_allow_spaces(part: str) -> str:
    """
    Keep folder names readable while preventing traversal and weird control chars.
    - Allow Unicode letters/numbers, space, '-', '_', '.', '()', '[]', '&', '+', ',', ';', '@', '!', '~', "'", '`', '^', '='
    - Strip trailing dot/space to avoid Windows quirks when developing locally
    """
    p = str(part or "").strip()
    if not p or p in {".", ".."}:
        raise ValueError("Ugyldig mappe")
    p = re.sub(r"\s+", " ", p)
    allowed_symbols = set(" _-().[]&+,;@!~'`^=")
    cleaned_chars: list[str] = []
    for ch in p:
        if ch in allowed_symbols:
            cleaned_chars.append(ch)
            continue
        # Keep all Unicode letters and numbers (e.g. Danish letters).
        cat = unicodedata.category(ch)
        if cat and cat[0] in {"L", "N"}:
            cleaned_chars.append(ch)
    p = "".join(cleaned_chars)
    p = p.rstrip(" .")
    if not p:
        raise ValueError("Ugyldig mappe")
    return p

def _normalize_upload_subdir(raw: Optional[str]) -> str:
    value = (raw or "").strip().replace("\\", "/")
    value = value.strip("/")
    if not value:
        return ""
    safe_parts: list[str] = []
    for part in value.split("/"):
        safe_parts.append(_sanitize_folder_part_allow_spaces(part))
    return "/".join(safe_parts)


def _upload_subdir_setting_key(destination: str) -> str:
    if destination == UPLOAD_DEST_LIBRARY:
        return "upload_subdir_library"
    return "upload_subdir_uploads"


def get_upload_subdir(destination: Optional[str] = None) -> str:
    dest = destination or get_upload_destination()
    try:
        by_dest = _get_setting(_upload_subdir_setting_key(dest), "")
        legacy = _get_setting("upload_subdir", "")
        raw = by_dest if (by_dest or "").strip() else legacy
        subdir = _normalize_upload_subdir(raw)
        # Migration: old default for uploads created nested /data/uploads/uploads.
        if dest == UPLOAD_DEST_UPLOADS and subdir.lower() == "uploads":
            try:
                _set_upload_subdir(dest, "")
            except Exception:
                pass
            return ""
        return subdir
    except Exception:
        return ""


def _set_upload_subdir(destination: str, subdir: str) -> None:
    safe = _normalize_upload_subdir(subdir)
    _set_setting(_upload_subdir_setting_key(destination), safe)
    # Keep legacy key in sync for backward compatibility
    _set_setting("upload_subdir", safe)


def _ensure_default_upload_subdir(destination: str, target_root: Path, current_subdir: str) -> str:
    if current_subdir:
        return current_subdir
    default_name = UPLOAD_DEFAULT_SUBDIR_BY_DEST.get(destination, "")
    if not default_name:
        return ""
    try:
        safe = _normalize_upload_subdir(default_name)
    except Exception:
        return ""
    try:
        target = target_root / safe
        target.mkdir(parents=True, exist_ok=True)
        if destination == UPLOAD_DEST_UPLOADS:
            # Keep internal storage roots mirrored for mapper folders.
            mirror = UPLOAD_DIR / "converted" / safe
            mirror.mkdir(parents=True, exist_ok=True)
        _set_upload_subdir(destination, safe)
        return safe
    except Exception:
        return ""
    if current_subdir:
        return current_subdir
    default_name = UPLOAD_DEFAULT_SUBDIR_BY_DEST.get(destination, "")
    if not default_name:
        return ""
    try:
        safe = _normalize_upload_subdir(default_name)
    except Exception:
        return ""
    try:
        target = target_root / safe
        target.mkdir(parents=True, exist_ok=True)
        _set_upload_subdir(destination, safe)
        return safe
    except Exception:
        return ""


def _list_upload_subdirs(base_dir: Path, limit: int = 400) -> list[str]:
    out: list[str] = [""]
    try:
        base = base_dir.resolve()
    except Exception:
        return out
    if not base.exists() or not base.is_dir():
        return out
    try:
        blocked_dir_names = {"@eadir", "#recycle"}
        for root, dirs, _files in os.walk(base):
            dirs[:] = sorted([
                d for d in dirs
                if (not d.startswith(".")) and (d.strip().lower() not in blocked_dir_names)
            ])
            for d in dirs:
                p = Path(root) / d
                try:
                    rel = str(p.relative_to(base)).replace("\\", "/")
                except Exception:
                    continue
                # Hide framework folders from folder pickers ('originals' and 'converted')
                parts = [seg for seg in rel.split("/") if seg]
                if any(seg.strip().lower() in blocked_dir_names for seg in parts):
                    continue
                if parts and parts[0] in {"originals", "converted"}:
                    # Do not surface internal storage roots as user folders
                    continue
                if rel and rel not in out:
                    out.append(rel)
                    if len(out) >= limit:
                        return out
    except Exception:
        return out
    return out


def _upload_settings_payload(destination: str) -> dict:
    saved_destination = get_upload_destination()
    subdir = get_upload_subdir(destination)
    target_root, _ = _upload_target_for_destination(destination)
    subdir = _ensure_default_upload_subdir(destination, target_root, subdir)
    folders = _list_upload_subdirs(target_root)
    folders = _filter_folders_by_current_user_acl(folders)
    if destination == UPLOAD_DEST_UPLOADS and "uploads" in folders:
        folders = [f for f in folders if f != "uploads"]
    if subdir and subdir not in folders:
        # Stored folder no longer exists on disk: remove stale reference
        _set_upload_subdir(destination, "")
        subdir = ""
    return {
        "ok": True,
        "destination": destination,
        "saved_destination": saved_destination,
        "subdir": subdir,
        "folders": folders,
        "photo_dir": str(PHOTO_DIR),
        "upload_dir": str(UPLOAD_DIR),
        "note": "Scan bruger filer direkte fra biblioteket og kopierer ikke.",
        "options": [
            {"value": UPLOAD_DEST_UPLOADS, "label": "KopiÃ©r til uploads-mappen"},
            {"value": UPLOAD_DEST_LIBRARY, "label": "KopiÃ©r til fotobiblioteket"},
        ],
    }


# --- Folder preview selections (persisted server-side) ---
def _normalize_folder_preview_key(value: Optional[str]) -> Optional[str]:
    """Normalize a folder key used by the Mapper view (relative path under uploads root).
    Empty string is allowed for root; otherwise validate via upload-subdir normalizer.
    Returns None if invalid.
    """
    try:
        raw = str(value or "").strip().replace("\\", "/")
        if raw == "":
            return ""
        return _normalize_upload_subdir(raw)
    except Exception:
        return None


def _ensure_folder_previews_table() -> None:
    try:
        with closing(get_conn()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS folder_previews (
                    folder_path TEXT PRIMARY KEY,
                    previews_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
    except Exception:
        pass


def _mapper_folder_from_rel(rel_path: str) -> str:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    base = rel
    if rel.startswith("uploads/originals/"):
        base = rel[len("uploads/originals/"):]
    elif rel.startswith("uploads/converted/"):
        base = rel[len("uploads/converted/"):]
    elif rel.startswith("uploads/"):
        base = rel[len("uploads/"):]
    parent = base.rsplit("/", 1)[0] if "/" in base else ""
    return parent


def _compute_and_store_folder_previews(folder_key: str) -> list[str]:
    # Build accepted prefixes under uploads
    f = str(folder_key or "").strip()
    # Avoid scanning the entire library for root previews; show placeholder instead
    if f == "":
        return []
    prefixes = [
        f"uploads/{f}",
        f"uploads/originals/{f}" if f else "uploads/originals",
        f"uploads/converted/{f}" if f else "uploads/converted",
    ]
    where = " OR ".join(["rel_path LIKE ? || '/%'"] * len(prefixes))
    with closing(get_conn()) as conn:
        # Limit scan size for performance; we'll prefer newest items and stop after we pick enough
        rows = conn.execute(
            f"SELECT * FROM photos WHERE {where} ORDER BY COALESCE(captured_at, modified_fs, created_fs) DESC LIMIT 800",
            prefixes,
        ).fetchall()
    rows = _dedupe_upload_storage_rows(rows)
    own: list[str] = []
    desc: list[str] = []
    seen: set[str] = set()
    for r in rows:
        try:
            rel = str(r["rel_path"] or "")
            if not rel:
                continue
            try:
                if not _disk_path_from_rel_path(rel).exists():
                    continue
            except Exception:
                continue
            thumb_name = str(r["thumb_name"] or "").strip()
            if thumb_name and not (THUMB_DIR / thumb_name).exists():
                continue
            pub = row_to_public(r)
            url = (
                pub.get("thumb_url")
                or pub.get("view_url")
                or pub.get("original_url")
                or pub.get("download_url")
            )
        except Exception:
            url = None
        if not url or url in seen:
            continue
        photo_folder = _mapper_folder_from_rel(rel)
        if photo_folder == f:
            own.append(url)
        else:
            if f == "" or photo_folder.startswith(f + "/"):
                desc.append(url)
        seen.add(url)
    ordered = own + desc
    if not ordered:
        try:
            with closing(get_conn()) as conn:
                conn.execute("DELETE FROM folder_previews WHERE folder_path=?", (f,))
                conn.commit()
        except Exception:
            pass
        return []
    pick: list[str]
    if len(ordered) >= 4:
        pick = ordered[:4]
    elif len(ordered) >= 2:
        pick = ordered[:2]
    else:
        pick = ordered[:1]
    payload = json.dumps(pick, ensure_ascii=False)
    now = now_iso()
    with closing(get_conn()) as conn:
        conn.execute(
            """
            INSERT INTO folder_previews(folder_path, previews_json, updated_at)
            VALUES(?,?,?)
            ON CONFLICT(folder_path) DO UPDATE SET
                previews_json=excluded.previews_json,
                updated_at=excluded.updated_at
            """,
            (f, payload, now),
        )
        conn.commit()
    return pick


@app.route("/api/folder-previews", methods=["GET"])
def api_folder_previews_get():
    _ensure_folder_previews_table()
    folders_raw = str(request.args.get("folders") or "").strip()
    if not folders_raw:
        return jsonify({"ok": True, "items": {}})
    keys_in = [p for p in (folders_raw.split(",") if folders_raw else [])]
    if not keys_in:
        return jsonify({"ok": True, "items": {}})
    keys: list[str] = []
    for k in keys_in:
        nk = _normalize_folder_preview_key(k)
        if nk is None:
            continue
        keys.append(nk)
    if not keys:
        return jsonify({"ok": True, "items": {}})
    for k in keys:
        try:
            _sync_upload_folder_from_disk(k, recursive=False, max_files=UPLOAD_FOLDER_SYNC_PREVIEW_MAX_FILES)
        except Exception:
            pass
    placeholders = ",".join(["?"] * len(keys))
    with closing(get_conn()) as conn:
        rows = conn.execute(
            f"SELECT folder_path, previews_json FROM folder_previews WHERE folder_path IN ({placeholders})",
            keys,
        ).fetchall()
    items: dict[str, list[str]] = {}
    for r in rows:
        try:
            key = str(r[0])
            urls = json.loads(str(r[1] or "[]")) or []
            if _folder_preview_urls_are_current(key, urls):
                items[key] = urls
        except Exception:
            pass
    # For any requested keys without saved previews, compute and store now
    for k in keys:
        if k not in items or not items[k]:
            try:
                items[k] = _compute_and_store_folder_previews(k)
            except Exception:
                items[k] = items.get(k, [])
    return jsonify({"ok": True, "items": items})


@app.route("/api/folder-previews", methods=["POST"])
def api_folder_previews_set():
    _ensure_folder_previews_table()
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}
    folder = _normalize_folder_preview_key(data.get("folder"))
    previews = data.get("previews") or []
    if folder is None:
        return jsonify({"ok": False, "error": "invalid_folder"}), 400
    # Accept only up to 4 URLs; lengths allowed: 1,2,4
    urls: list[str] = []
    for u in (previews or []):
        s = str(u or "").strip()
        if not s:
            continue
        if len(s) > 512:
            s = s[:512]
        urls.append(s)
        if len(urls) >= 4:
            break
    if len(urls) not in {1, 2, 4}:
        return jsonify({"ok": False, "error": "invalid_count"}), 400
    payload = json.dumps(urls, ensure_ascii=False)
    now = now_iso()
    with closing(get_conn()) as conn:
        conn.execute(
            """
            INSERT INTO folder_previews(folder_path, previews_json, updated_at)
            VALUES(?,?,?)
            ON CONFLICT(folder_path) DO UPDATE SET
                previews_json=excluded.previews_json,
                updated_at=excluded.updated_at
            """,
            (folder, payload, now),
        )
        conn.commit()
    return jsonify({"ok": True, "folder": folder, "previews": urls, "updated_at": now})


def _folder_preview_thumb_name_from_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    marker = "/api/thumbs/"
    idx = raw.find(marker)
    if idx < 0:
        return ""
    tail = raw[idx + len(marker):].split("?", 1)[0].split("#", 1)[0]
    try:
        tail = unquote(tail)
    except Exception:
        pass
    return re.sub(r"[^a-zA-Z0-9._-]", "", tail)


def _folder_preview_rel_belongs(folder_key: str, rel_path: Any) -> bool:
    f = str(folder_key or "").strip()
    if not f:
        return False
    photo_folder = _mapper_folder_from_rel(str(rel_path or ""))
    return photo_folder == f or photo_folder.startswith(f + "/")


def _folder_preview_urls_are_current(folder_key: str, urls: Any) -> bool:
    try:
        folder = _normalize_folder_preview_key(folder_key)
    except Exception:
        folder = None
    if folder is None or folder == "":
        return False
    clean = [str(u or "").strip() for u in (urls or []) if str(u or "").strip()]
    if len(clean) not in {1, 2, 4}:
        return False
    thumb_names = [_folder_preview_thumb_name_from_url(u) for u in clean]
    if any(not tn for tn in thumb_names):
        return False
    if any(not (THUMB_DIR / tn).exists() for tn in thumb_names):
        return False
    placeholders = ",".join(["?"] * len(set(thumb_names)))
    with closing(get_conn()) as conn:
        rows = conn.execute(
            f"SELECT rel_path, thumb_name FROM photos WHERE thumb_name IN ({placeholders})",
            sorted(set(thumb_names)),
        ).fetchall()
    by_thumb: dict[str, list[str]] = {}
    for row in rows:
        tn = str(row["thumb_name"] or "").strip()
        rel = str(row["rel_path"] or "").strip()
        if tn and rel:
            by_thumb.setdefault(tn, []).append(rel)
    for tn in thumb_names:
        rels = by_thumb.get(tn) or []
        if not rels:
            return False
        found_current = False
        for rel in rels:
            if not _folder_preview_rel_belongs(folder, rel):
                continue
            try:
                if not _disk_path_from_rel_path(rel).exists():
                    continue
            except Exception:
                continue
            found_current = True
            break
        if not found_current:
            return False
    return True


def _folder_preview_ancestor_keys(folder_key: str) -> list[str]:
    raw = str(folder_key or "").strip("/")
    if not raw:
        return []
    parts = [p for p in raw.split("/") if p]
    out: list[str] = []
    for i in range(len(parts), 0, -1):
        candidate = "/".join(parts[:i])
        nk = _normalize_folder_preview_key(candidate)
        if nk is not None and nk not in out:
            out.append(nk)
    return out


def _folder_preview_affected_keys_for_rels(rel_paths: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for rel in rel_paths or []:
        folder = _mapper_folder_from_rel(str(rel or ""))
        for key in _folder_preview_ancestor_keys(folder):
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


def _refresh_folder_previews_for_folders(folder_keys: Iterable[Any]) -> list[str]:
    refreshed: list[str] = []
    seen: set[str] = set()
    for raw in folder_keys or []:
        nk = _normalize_folder_preview_key(str(raw or ""))
        if nk is None or nk == "" or nk in seen:
            continue
        seen.add(nk)
        try:
            _compute_and_store_folder_previews(nk)
            refreshed.append(nk)
        except Exception:
            continue
    return refreshed


def _refresh_folder_previews_for_rel_paths(rel_paths: Iterable[Any]) -> list[str]:
    return _refresh_folder_previews_for_folders(_folder_preview_affected_keys_for_rels(rel_paths))


def _delete_thumb_files_if_unreferenced(thumb_names: Iterable[Any]) -> int:
    cleaned = sorted(
        {
            re.sub(r"[^a-zA-Z0-9._-]", "", str(tn or "").strip())
            for tn in (thumb_names or [])
            if str(tn or "").strip()
        }
    )
    cleaned = [tn for tn in cleaned if tn]
    if not cleaned:
        return 0
    placeholders = ",".join(["?"] * len(cleaned))
    with closing(get_conn()) as conn:
        rows = conn.execute(
            f"SELECT DISTINCT thumb_name FROM photos WHERE thumb_name IN ({placeholders})",
            cleaned,
        ).fetchall()
    still_used = {str(r["thumb_name"] or "").strip() for r in rows if str(r["thumb_name"] or "").strip()}
    removed = 0
    for tn in cleaned:
        if tn in still_used:
            continue
        try:
            p = THUMB_DIR / tn
            if p.exists():
                p.unlink()
                removed += 1
        except Exception:
            continue
    return removed


def _delete_missing_upload_photo_rows(rows: Iterable[sqlite3.Row]) -> dict:
    rows_list = list(rows or [])
    if not rows_list:
        return {"photos": 0, "faces": 0, "thumbs": 0, "preview_folders": []}
    ids: list[int] = []
    rels: list[str] = []
    thumbs: list[str] = []
    for r in rows_list:
        try:
            ids.append(int(r["id"]))
            rels.append(str(r["rel_path"] or ""))
            if r["thumb_name"]:
                thumbs.append(str(r["thumb_name"]))
        except Exception:
            continue
    if not ids:
        return {"photos": 0, "faces": 0, "thumbs": 0, "preview_folders": []}
    with closing(get_conn()) as conn:
        ph = ",".join(["?"] * len(ids))
        faces_removed = int(conn.execute(f"SELECT COUNT(*) AS c FROM faces WHERE photo_id IN ({ph})", ids).fetchone()["c"] or 0)
        conn.execute(f"DELETE FROM faces WHERE photo_id IN ({ph})", ids)
        conn.execute(f"DELETE FROM photos WHERE id IN ({ph})", ids)
        conn.commit()
    thumbs_removed = _delete_thumb_files_if_unreferenced(thumbs)
    preview_folders = _refresh_folder_previews_for_rel_paths(rels)
    return {
        "photos": len(ids),
        "faces": faces_removed,
        "thumbs": thumbs_removed,
        "preview_folders": preview_folders,
    }


def _prune_missing_upload_photos_for_folder(folder: str, *, recursive: bool = False, limit: int = 5000) -> dict:
    logical_folder = _normalize_upload_folder_for_disk_sync(folder)
    if not logical_folder:
        return {"photos": 0, "faces": 0, "thumbs": 0, "preview_folders": []}
    prefixes = [
        f"uploads/{logical_folder}",
        f"uploads/originals/{logical_folder}",
        f"uploads/converted/{logical_folder}",
    ]
    where = " OR ".join(["rel_path LIKE ? || '/%'"] * len(prefixes))
    cap = max(100, min(10000, int(limit or 5000)))
    with closing(get_conn()) as conn:
        rows = conn.execute(
            f"SELECT id, rel_path, thumb_name FROM photos WHERE {where} LIMIT ?",
            [*prefixes, cap],
        ).fetchall()
    missing: list[sqlite3.Row] = []
    for row in rows:
        rel = str(row["rel_path"] or "")
        photo_folder = _mapper_folder_from_rel(rel)
        if recursive:
            if not (photo_folder == logical_folder or photo_folder.startswith(logical_folder + "/")):
                continue
        elif photo_folder != logical_folder:
            continue
        try:
            if _disk_path_from_rel_path(rel).exists():
                continue
        except Exception:
            pass
        missing.append(row)
    return _delete_missing_upload_photo_rows(missing)


@app.route("/api/debug/acl", methods=["GET"])
def api_debug_acl():
    try:
        if not getattr(current_user, "is_admin", False):
            return jsonify({"ok": False, "error": "forbidden"}), 403
    except Exception:
        return jsonify({"ok": False, "error": "forbidden"}), 403
    prefixes = _current_user_acl_prefixes()
    try:
        raw = _list_upload_subdirs(UPLOAD_DIR, limit=2000)
        filtered = _filter_folders_by_current_user_acl(list(raw))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({
        "ok": True,
        "user": {
            "id": int(getattr(current_user, "id", 0) or 0),
            "is_admin": bool(getattr(current_user, "is_admin", False)),
        },
        "prefixes": prefixes,
        "raw": raw,
        "filtered": filtered,
    })


def _delete_indexed_photos_for_prefixes(rel_prefixes: Iterable[str]) -> dict:
    prefixes = [str(p or "").strip("/") for p in (rel_prefixes or []) if str(p or "").strip("/")]
    if not prefixes:
        return {"photos": 0, "faces": 0, "thumbs": 0, "preview_folders": []}

    where_parts: list[str] = []
    params: list[Any] = []
    for pref in prefixes:
        where_parts.append("(rel_path = ? OR rel_path LIKE ?)")
        params.extend([pref, pref + "/%"])

    q = "SELECT id, rel_path, thumb_name FROM photos WHERE " + " OR ".join(where_parts)
    with closing(get_conn()) as conn:
        rows = conn.execute(q, params).fetchall()
        if not rows:
            return {"photos": 0, "faces": 0, "thumbs": 0, "preview_folders": []}

        photo_ids = [int(r["id"]) for r in rows]
        thumbs = [str(r["thumb_name"]) for r in rows if r["thumb_name"]]
        rels = [str(r["rel_path"]) for r in rows if r["rel_path"]]

        ph = ",".join(["?"] * len(photo_ids))
        faces_removed = int(conn.execute(f"SELECT COUNT(*) AS c FROM faces WHERE photo_id IN ({ph})", photo_ids).fetchone()["c"] or 0)
        conn.execute(f"DELETE FROM faces WHERE photo_id IN ({ph})", photo_ids)
        conn.execute(f"DELETE FROM photos WHERE id IN ({ph})", photo_ids)
        conn.commit()

    thumbs_removed = _delete_thumb_files_if_unreferenced(thumbs)
    preview_folders = _refresh_folder_previews_for_rel_paths(rels)

    return {"photos": len(photo_ids), "faces": faces_removed, "thumbs": thumbs_removed, "preview_folders": preview_folders}


def _normalize_photo_rel_for_delete(rel_path: Any) -> str:
    try:
        rel = str(rel_path or "").replace("\\", "/").lstrip("/").strip()
    except Exception:
        return ""
    if not rel or ".." in rel:
        return ""
    return rel


def _upload_path_to_rel(path: Path) -> str:
    try:
        tail = str(path.resolve().relative_to(UPLOAD_DIR.resolve())).replace("\\", "/")
    except Exception:
        return ""
    return _normalize_photo_rel_for_delete(f"uploads/{tail}")


def _conversion_related_upload_rels(metadata_json_raw: Any) -> set[str]:
    out: set[str] = set()
    try:
        if isinstance(metadata_json_raw, dict):
            mj = metadata_json_raw
        else:
            raw = str(metadata_json_raw or "").strip()
            if not raw:
                return out
            mj = json.loads(raw)
    except Exception:
        return out
    if not isinstance(mj, dict):
        return out

    conv = mj.get("conversion")
    if isinstance(conv, dict):
        for key in ("from_rel_path", "to_rel_path"):
            rel = _normalize_photo_rel_for_delete(conv.get(key))
            if rel.startswith("uploads/"):
                out.add(rel)

    for key in ("converted_from_rel", "converted_to_rel"):
        rel = _normalize_photo_rel_for_delete(mj.get(key))
        if rel.startswith("uploads/"):
            out.add(rel)
    return out


def _related_photo_rel_paths_for_delete(rel_path: str, metadata_json_raw: Any = None) -> set[str]:
    rel = _normalize_photo_rel_for_delete(rel_path)
    if not rel:
        return set()

    rels: set[str] = {rel}

    # Prefer exact conversion links when present.
    rels.update(_conversion_related_upload_rels(metadata_json_raw))

    # Fallback for legacy rows without conversion metadata.
    if rel.startswith("uploads/"):
        conv_exts = (".mp4",) if Path(rel).suffix.lower() == ".mov" else None
        conv_path = _find_existing_converted_for_upload_rel(rel, extensions=conv_exts)
        if conv_path is not None:
            conv_rel = _upload_path_to_rel(conv_path)
            if conv_rel:
                rels.add(conv_rel)
        if rel.startswith("uploads/converted/"):
            orig_path = _find_existing_original_for_converted_rel(rel)
            if orig_path is not None:
                orig_rel = _upload_path_to_rel(orig_path)
                if orig_rel:
                    rels.add(orig_rel)

    return rels


def _delete_photo_disk_variants(rel_path: str, metadata_json_raw: Any = None, already_deleted: Optional[set[str]] = None) -> int:
    removed = 0
    for rel in _related_photo_rel_paths_for_delete(rel_path, metadata_json_raw):
        try:
            fp = _disk_path_from_rel_path(rel)
            key = str(fp.resolve(strict=False))
        except Exception:
            try:
                key = str(_disk_path_from_rel_path(rel))
            except Exception:
                continue
        if already_deleted is not None and key in already_deleted:
            continue
        try:
            if fp.exists() and fp.is_file():
                fp.unlink()
                removed += 1
                if already_deleted is not None:
                    already_deleted.add(key)
        except Exception:
            continue
    return removed


def _delete_indexed_photos_by_ids(photo_ids: Iterable[int]) -> dict:
    ids = sorted({int(pid) for pid in (photo_ids or []) if str(pid).isdigit()})
    if not ids:
        return {"photos": 0, "faces": 0, "files": 0, "thumbs": 0, "preview_folders": []}

    with closing(get_conn()) as conn:
        ph = ",".join(["?"] * len(ids))
        rows = conn.execute(
            f"SELECT id, rel_path, thumb_name, metadata_json FROM photos WHERE id IN ({ph})",
            ids,
        ).fetchall()
        if not rows:
            return {"photos": 0, "faces": 0, "files": 0, "thumbs": 0, "preview_folders": []}

        resolved_ids = [int(r["id"]) for r in rows]
        thumbs = [str(r["thumb_name"]) for r in rows if r["thumb_name"]]
        photo_file_refs = [
            (str(r["rel_path"]), r["metadata_json"])
            for r in rows
            if r["rel_path"]
        ]

        ph2 = ",".join(["?"] * len(resolved_ids))
        faces_removed = int(
            conn.execute(
                f"SELECT COUNT(*) AS c FROM faces WHERE photo_id IN ({ph2})",
                resolved_ids,
            ).fetchone()["c"]
            or 0
        )
        conn.execute(f"DELETE FROM faces WHERE photo_id IN ({ph2})", resolved_ids)
        conn.execute(f"DELETE FROM photos WHERE id IN ({ph2})", resolved_ids)
        conn.commit()

    thumbs_removed = _delete_thumb_files_if_unreferenced(thumbs)

    files_removed = 0
    deleted_keys: set[str] = set()
    for rel, metadata_json_raw in photo_file_refs:
        files_removed += _delete_photo_disk_variants(rel, metadata_json_raw, already_deleted=deleted_keys)
    preview_folders = _refresh_folder_previews_for_rel_paths([rel for rel, _ in photo_file_refs])

    return {
        "photos": len(resolved_ids),
        "faces": faces_removed,
        "thumbs": thumbs_removed,
        "files": files_removed,
        "preview_folders": preview_folders,
    }


def _share_token_digest(token: str) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    key = app.secret_key
    if isinstance(key, str):
        key_bytes = key.encode("utf-8", errors="ignore")
    elif isinstance(key, bytes):
        key_bytes = key
    else:
        key_bytes = str(key).encode("utf-8", errors="ignore")
    return hmac.new(key_bytes, raw.encode("utf-8", errors="ignore"), hashlib.sha256).hexdigest()


def _share_is_expired(expires_at: Optional[str]) -> bool:
    exp = str(expires_at or "").strip()
    if not exp:
        return False
    return exp <= now_iso()


def _share_expires_at_from_body(
    body: dict[str, Any],
    default_value: int = 7,
    default_unit: str = "days",
) -> tuple[Optional[str], Optional[str]]:
    has_expires_value = "expires_value" in body
    raw_value = body.get("expires_value")
    if not has_expires_value:
        expires_value = int(default_value)
    else:
        raw_text = str(raw_value or "").strip()
        if (not raw_text) or raw_text == "0":
            return None, None
        try:
            expires_value = int(raw_text)
        except Exception:
            return None, "Ugyldig udlÃ¸bsvÃ¦rdi"
        if expires_value < 0:
            return None, "Ugyldig udlÃ¸bsvÃ¦rdi"
        if expires_value == 0:
            return None, None
        if expires_value < 1:
            return None, "Ugyldig udlÃ¸bsvÃ¦rdi"

    expires_unit = str(body.get("expires_unit") or default_unit).strip().lower()
    if expires_unit not in {"hours", "days"}:
        expires_unit = default_unit if default_unit in {"hours", "days"} else "days"
    expires_hours = expires_value if expires_unit == "hours" else (expires_value * 24)
    expires_hours = max(1, min(expires_hours, 24 * 3650))
    expires_at = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat(timespec="seconds") + "Z"
    return expires_at, None


def _normalize_share_folder_path(value: Any) -> str:
    """Normalize share folder paths to canonical user-subdir form.

    Accepts legacy variants like:
    - uploads/<subdir>
    - originals/<subdir>
    - converted/<subdir>
    - uploads/originals/<subdir>
    - uploads/converted/<subdir>
    """
    try:
        folder = _normalize_upload_subdir(str(value or ""))
    except Exception:
        return ""
    if not folder:
        return ""

    prefixes = (
        "uploads/originals/",
        "uploads/converted/",
        "uploads/",
        "originals/",
        "converted/",
    )
    for pref in prefixes:
        if folder.startswith(pref):
            folder = folder[len(pref):]
            break

    try:
        folder = _normalize_upload_subdir(folder)
    except Exception:
        return ""
    if not folder:
        return ""
    if folder.lower() in {"uploads", "originals", "converted"}:
        return ""
    return folder


def _share_folder_rel_prefix(folder_path: str) -> str:
    folder = _normalize_share_folder_path(folder_path)
    return f"uploads/{folder}" if folder else "uploads"


def _share_folder_paths(conn: sqlite3.Connection, share_row: sqlite3.Row) -> list[str]:
    share_id = int(share_row["id"] or 0)
    rows = conn.execute(
        "SELECT folder_path FROM share_link_folders WHERE share_id=? ORDER BY folder_path COLLATE NOCASE",
        (share_id,),
    ).fetchall()
    values: list[str] = []
    for r in rows:
        fp = _normalize_share_folder_path(r["folder_path"])
        if fp and fp not in values:
            values.append(fp)
    if values:
        return values
    fallback = _normalize_share_folder_path(share_row["folder_path"])
    return [fallback] if fallback else []


def _share_rel_prefixes(folder_paths: list[str]) -> list[str]:
    prefixes: list[str] = []
    for fp in folder_paths:
        # Canonical UI prefix (virtual root)
        base = _share_folder_rel_prefix(fp)  # e.g. 'uploads/Tulle_og_Mor'
        # Physical storage variants for uploads (originals/converted)
        variants = [
            base,
            (f"uploads/originals/{fp}" if fp else "uploads/originals"),
            (f"uploads/converted/{fp}" if fp else "uploads/converted"),
        ]
        for v in variants:
            if v and v not in prefixes:
                prefixes.append(v)
    return prefixes


def _share_scope_sql(prefixes: list[str]) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    for rel_prefix in prefixes:
        clauses.append("(rel_path=? OR rel_path LIKE ?)")
        params.extend([rel_prefix, rel_prefix + "/%"])
    return " OR ".join(clauses), params


def _load_share_row_from_token(token: str) -> Optional[sqlite3.Row]:
    token_hash = _share_token_digest(token)
    if not token_hash:
        return None
    with closing(get_conn()) as conn:
        return conn.execute(
            "SELECT * FROM share_links WHERE token_hash=? LIMIT 1",
            (token_hash,),
        ).fetchone()


def _load_share_from_token(token: str, touch: bool = False) -> Optional[sqlite3.Row]:
    token_hash = _share_token_digest(token)
    if not token_hash:
        return None
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT * FROM share_links WHERE token_hash=? LIMIT 1",
            (token_hash,),
        ).fetchone()
        if not row:
            return None
        if int(row["revoked"] or 0) == 1:
            return None
        if _share_is_expired(row["expires_at"]):
            return None
        if touch:
            try:
                conn.execute("UPDATE share_links SET last_used_at=? WHERE id=?", (now_iso(), int(row["id"])))
                conn.commit()
            except Exception:
                pass
    return row


def _share_redirect_for_authenticated_user(token: str):
    """If a share is inactive, route logged-in users to normal app access when possible."""
    try:
        if not bool(getattr(current_user, "is_authenticated", False)):
            return None
    except Exception:
        return None

    share_row = _load_share_row_from_token(token)
    if not share_row:
        return None

    with closing(get_conn()) as conn:
        folder_paths = _share_folder_paths(conn, share_row)
        for fp in folder_paths:
            rel = f"uploads/{fp}" if fp else "uploads"
            if _is_rel_visible_for_current_user(rel, conn):
                return redirect(url_for("index", view="mapper", mappe=fp))
    return None


def _share_session_key(share_row: sqlite3.Row) -> str:
    return f"share_auth_{int(share_row['id'])}"


def _share_name_session_key(share_row: sqlite3.Row) -> str:
    return f"share_name_{int(share_row['id'])}"


def _sanitize_share_visitor_name(value: Any) -> str:
    name = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(name) > 80:
        name = name[:80].strip()
    return name


def _share_is_password_protected(share_row: sqlite3.Row) -> bool:
    return bool(str(share_row["password_hash"] or "").strip())


def _share_requires_visitor_name(share_row: sqlite3.Row) -> bool:
    try:
        return bool(int(share_row["require_visitor_name"] or 0))
    except Exception:
        return False


def _share_get_visitor_name(share_row: sqlite3.Row) -> str:
    # session is a dict-like object, .get() is valid here
    return _sanitize_share_visitor_name(session.get(_share_name_session_key(share_row)) or "")


def _share_is_authorized(share_row: sqlite3.Row) -> bool:
    # session is a dict-like object, .get() is valid here
    if _share_is_password_protected(share_row) and not bool(session.get(_share_session_key(share_row))):
        return False
    if _share_requires_visitor_name(share_row) and not _share_get_visitor_name(share_row):
        return False
    return True


def _normalize_share_base_url(raw: str) -> Optional[str]:
    value = str(raw or "").strip()
    if not value:
        return None
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", "")).rstrip("/")


def _normalize_photoframe_http_url(raw: Any) -> Optional[str]:
    value = str(raw or "").strip()
    if not value:
        return None
    if "://" not in value:
        value = f"http://{value}"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    path = str(parsed.path or "").rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _normalize_photoframe_base_url(raw: Any) -> Optional[str]:
    normalized = _normalize_photoframe_http_url(raw)
    if not normalized:
        return None
    parsed = urlparse(normalized)
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", "")).rstrip("/")


def _sanitize_photoframe_text(raw: Any, max_len: int = 120) -> str:
    value = re.sub(r"\s+", " ", str(raw or "")).strip()
    if max_len > 0 and len(value) > max_len:
        value = value[:max_len].strip()
    return value


def _sanitize_photoframe_photo_id(raw: Any) -> int:
    try:
        value = int(raw)
    except Exception:
        try:
            value = int(str(raw or "").strip())
        except Exception:
            return 0
    if value <= 0:
        return 0
    if value > 2_147_483_647:
        return 0
    return value


def _sanitize_photoframe_token_plain(raw: Any) -> str:
    token = str(raw or "").strip()
    if not token:
        return ""
    if len(token) > 256:
        token = token[:256].strip()
    if not re.match(r"^[A-Za-z0-9._~-]{8,256}$", token):
        return ""
    return token


def _normalize_photoframe_token_hash(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if re.match(r"^[a-f0-9]{64}$", value):
        return value
    return ""


def _sanitize_photoframe_update_job_id(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    if len(value) > 80:
        value = value[:80].strip()
    if not re.match(r"^[A-Za-z0-9._-]{4,80}$", value):
        return ""
    return value


def _sanitize_photoframe_update_sha256(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if re.match(r"^[a-f0-9]{64}$", value):
        return value
    return ""


def _sanitize_photoframe_update_status(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in {"queued", "downloading", "installing", "restarting", "success", "failed"}:
        return value
    return ""


def _normalize_photoframe_update_package_mode(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in {"restart_kiosk", "restartkiosk"}:
        return "restart-kiosk"
    if value in {"reset_device", "resetdevice"}:
        return "reset-device"
    if value in {"apply_settings", "applysettings"}:
        return "apply-settings"
    if value in {"scan_wifi", "scanwifi"}:
        return "scan-wifi"
    if value in {"start_settings_web", "startsettingsweb"}:
        return "start-settings-web"
    if value in {"stop_settings_web", "stopsettingsweb"}:
        return "stop-settings-web"
    if value in {"upload", "source-dir", "custom-url", "restart-kiosk", "reset-device", "apply-settings", "scan-wifi", "start-settings-web", "stop-settings-web"}:
        return value
    return ""


def _sanitize_photoframe_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return bool(raw)
    value = str(raw or "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return False


def _normalize_photoframe_device_name(raw: Any, max_len: int = 40) -> str:
    value = re.sub(r"\s+", " ", str(raw or "")).strip()
    value = re.sub(r"[^A-Za-z0-9 _.\-]", "", value)
    if max_len > 0 and len(value) > max_len:
        value = value[:max_len].strip()
    return value


def _normalize_photoframe_wifi_country(raw: Any) -> str:
    value = str(raw or "").strip().upper()
    if re.match(r"^[A-Z]{2}$", value):
        return value
    return ""


def _normalize_photoframe_interval_seconds(raw: Any, default: int = 5) -> int:
    try:
        value = int(str(raw or "").strip())
    except Exception:
        value = int(default)
    return max(1, min(60, value))


def _normalize_photoframe_wifi_secret(raw: Any, max_len: int = 128) -> str:
    value = str(raw or "")
    value = value.replace("\r", "").replace("\n", "").strip()
    if max_len > 0 and len(value) > max_len:
        value = value[:max_len]
    return value


def _sanitize_photoframe_wifi_scan_networks(raw: Any, max_items: int = 64) -> list[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[Dict[str, Any]] = []
    by_ssid: Dict[str, Dict[str, Any]] = {}
    for it in raw:
        if not isinstance(it, dict):
            continue
        ssid = _sanitize_photoframe_text(it.get("ssid"), 120)
        if not ssid:
            continue
        signal_raw = str(it.get("signal") or "").strip()
        try:
            signal = int(signal_raw)
        except Exception:
            signal = -1
        signal = max(-1, min(100, signal))
        security = _sanitize_photoframe_text(it.get("security"), 120)
        candidate = {
            "ssid": ssid,
            "signal": signal,
            "security": security,
        }
        key = ssid.lower()
        prev = by_ssid.get(key)
        if not prev:
            by_ssid[key] = candidate
            continue
        prev_signal = int(prev.get("signal", -1) or -1)
        if signal > prev_signal:
            by_ssid[key] = candidate
        elif (signal == prev_signal) and security and (not str(prev.get("security") or "").strip()):
            by_ssid[key] = candidate

    out = list(by_ssid.values())
    out.sort(key=lambda n: int(n.get("signal", -1) or -1), reverse=True)
    cap = max(1, min(200, int(max_items or 64)))
    if len(out) > cap:
        out = out[:cap]
    return out


def _decode_photoframe_wifi_scan_payload(raw: Any, max_len: int = 12000) -> list[Dict[str, Any]]:
    value = str(raw or "").strip()
    if not value:
        return []
    if len(value) > max_len:
        return []
    parsed: Any = None
    if value.startswith("["):
        try:
            parsed = json.loads(value)
        except Exception:
            parsed = None
    if parsed is None:
        try:
            padded = value + ("=" * ((4 - (len(value) % 4)) % 4))
            decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
            if len(decoded) > (max_len * 3):
                return []
            parsed = json.loads(decoded.decode("utf-8", errors="ignore"))
        except Exception:
            return []
    return _sanitize_photoframe_wifi_scan_networks(parsed, max_items=80)


def _sanitize_photoframe_settings_payload(raw: Any) -> tuple[Dict[str, Any], str]:
    if not isinstance(raw, dict):
        return ({}, "Ugyldigt settings payload")

    out: Dict[str, Any] = {}

    if "device_name" in raw:
        device_name = _normalize_photoframe_device_name(raw.get("device_name"), 40)
        if not device_name:
            return ({}, "Indtast et gyldigt enhedsnavn")
        out["device_name"] = device_name

    if "server_url" in raw:
        server_url_raw = str(raw.get("server_url") or "").strip()
        if server_url_raw:
            server_url = _normalize_photoframe_base_url(server_url_raw) or ""
            if not server_url:
                return ({}, "Server URL skal starte med http:// eller https://")
            out["server_url"] = server_url

    if "device_token" in raw:
        token_raw = str(raw.get("device_token") or "").strip()
        if token_raw:
            token = _sanitize_photoframe_token_plain(token_raw)
            if not token:
                return ({}, "Ugyldigt device token")
            out["device_token"] = token

    if "interval_seconds" in raw:
        interval_raw = str(raw.get("interval_seconds") or "").strip()
        if interval_raw:
            try:
                interval_val = int(interval_raw)
            except Exception:
                return ({}, "Tid pr billede skal være et tal mellem 1 og 60")
            if interval_val < 1 or interval_val > 60:
                return ({}, "Tid pr billede skal være mellem 1 og 60")
            out["interval_seconds"] = int(interval_val)

    if "wifi_country" in raw:
        country_raw = str(raw.get("wifi_country") or "").strip()
        if country_raw:
            country = _normalize_photoframe_wifi_country(country_raw)
            if not country:
                return ({}, "Landekode skal være 2 bogstaver (fx DK)")
            out["wifi_country"] = country

    ssid_raw = ""
    if "wifi_ssid" in raw:
        ssid_raw = _sanitize_photoframe_text(raw.get("wifi_ssid"), 120)
    if ssid_raw:
        out["wifi_ssid"] = ssid_raw
        password = _normalize_photoframe_wifi_secret(raw.get("wifi_password"), 128) if ("wifi_password" in raw) else ""
        out["wifi_password"] = password

    return (out, "")


def _decode_photoframe_settings_payload(raw: Any) -> Dict[str, Any]:
    parsed: Any = {}
    if isinstance(raw, dict):
        parsed = raw
    elif isinstance(raw, str):
        txt = str(raw or "").strip()
        if txt:
            try:
                parsed = json.loads(txt)
            except Exception:
                parsed = {}
    clean, _ = _sanitize_photoframe_settings_payload(parsed if isinstance(parsed, dict) else {})
    return clean if isinstance(clean, dict) else {}


def _sanitize_photoframe_feed_rev(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if not value:
        return ""
    if len(value) > 64:
        value = value[:64]
    if re.match(r"^[a-f0-9]{8,64}$", value):
        return value
    return ""


def _sanitize_photoframe_feed_sync_status(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in {"sending", "sent"}:
        return value
    return ""


def _sanitize_photoframe_feed_sync_count(raw: Any) -> int:
    try:
        value = int(raw or 0)
    except Exception:
        value = 0
    return max(0, min(100_000, value))


def _build_photoframe_entry(raw_item: Any, idx: int) -> Optional[Dict[str, Any]]:
    name = ""
    base_candidate = ""
    info_candidate = ""
    note = ""
    location = ""
    token_plain = ""
    token_hash_raw = ""
    token_hint_raw = ""
    created_at_raw = ""

    if isinstance(raw_item, str):
        base_candidate = raw_item.strip()
    elif isinstance(raw_item, dict):
        name = str(raw_item.get("name") or raw_item.get("label") or raw_item.get("title") or "").strip()
        base_candidate = str(
            raw_item.get("base_url")
            or raw_item.get("url")
            or raw_item.get("host")
            or raw_item.get("address")
            or ""
        ).strip()
        info_candidate = str(raw_item.get("info_url") or raw_item.get("status_url") or "").strip()
        note = str(raw_item.get("note") or raw_item.get("notes") or "").strip()
        location = str(raw_item.get("location") or "").strip()
        token_plain = str(raw_item.get("device_token") or raw_item.get("token") or "").strip()
        token_hash_raw = str(raw_item.get("token_hash") or raw_item.get("device_token_hash") or "").strip()
        token_hint_raw = str(raw_item.get("token_hint") or raw_item.get("token_last4") or "").strip()
        created_at_raw = str(raw_item.get("created_at") or "").strip()
    else:
        return None

    info_url = _normalize_photoframe_http_url(info_candidate) if info_candidate else None
    base_url = _normalize_photoframe_base_url(base_candidate) if base_candidate else None
    if not info_url and base_url:
        info_url = f"{base_url}/api/info"
    if not base_url and info_url:
        base_url = _normalize_photoframe_base_url(info_url)
    if not info_url:
        return None

    host_label = ""
    try:
        host_label = str(urlparse(base_url or info_url).hostname or "").strip()
    except Exception:
        host_label = ""
    if not name:
        name = host_label or f"Frame {idx + 1}"

    token_hash = _normalize_photoframe_token_hash(token_hash_raw)
    if (not token_hash) and token_plain:
        token_hash = _share_token_digest(token_plain)
    token_hint = _sanitize_photoframe_text(token_hint_raw, 16)
    if (not token_hint) and token_plain:
        token_hint = token_plain[-4:]
    created_at = _sanitize_photoframe_text(created_at_raw, 40)

    return {
        "id": re.sub(r"[^a-zA-Z0-9_-]+", "-", name.lower()).strip("-") or f"frame-{idx + 1}",
        "name": _sanitize_photoframe_text(name, 80),
        "base_url": base_url or "",
        "info_url": info_url,
        "location": _sanitize_photoframe_text(location, 80),
        "note": _sanitize_photoframe_text(note, 240),
        "token_hash": token_hash,
        "token_hint": token_hint,
        "created_at": created_at,
    }


def _parse_photoframe_entries(raw_value: str) -> list[Dict[str, Any]]:
    raw = str(raw_value or "").strip()
    if not raw:
        return []

    source_items: list[Any] = []
    parsed_json = None
    try:
        parsed_json = json.loads(raw)
    except Exception:
        parsed_json = None

    if isinstance(parsed_json, list):
        source_items = parsed_json
    elif isinstance(parsed_json, dict):
        frames = parsed_json.get("frames")
        if isinstance(frames, list):
            source_items = frames
    else:
        source_items = [v.strip() for v in re.split(r"[\r\n,;]+", raw) if str(v or "").strip()]

    out: list[Dict[str, Any]] = []
    seen_info_urls: set[str] = set()
    for idx, it in enumerate(source_items):
        entry = _build_photoframe_entry(it, idx)
        if not entry:
            continue
        info_url = str(entry.get("info_url") or "").strip()
        if not info_url or info_url in seen_info_urls:
            continue
        seen_info_urls.add(info_url)
        out.append(entry)
    return out


def _load_photoframe_entries() -> Tuple[list[Dict[str, Any]], str]:
    candidates: list[Tuple[str, str]] = []
    raw_setting = str(_get_setting("photoframe_frames", "") or "").strip()
    if raw_setting:
        candidates.append(("setting", raw_setting))
    if PHOTOFRAME_FRAMES_ENV:
        candidates.append(("env", PHOTOFRAME_FRAMES_ENV))
    try:
        if PHOTOFRAME_FRAMES_PATH.exists():
            raw_file = PHOTOFRAME_FRAMES_PATH.read_text(encoding="utf-8", errors="ignore").strip()
            if raw_file:
                candidates.append(("file", raw_file))
    except Exception:
        pass

    for source, raw in candidates:
        parsed = _parse_photoframe_entries(raw)
        if parsed:
            return parsed, source
    return [], "none"


def _photoframe_entries_to_setting_payload(entries: list[Dict[str, Any]]) -> str:
    frames: list[Dict[str, Any]] = []
    seen_info_urls: set[str] = set()
    for idx, it in enumerate(entries):
        entry = _build_photoframe_entry(it, idx)
        if not entry:
            continue
        info_url = str(entry.get("info_url") or "").strip()
        if (not info_url) or (info_url in seen_info_urls):
            continue
        seen_info_urls.add(info_url)

        item: Dict[str, Any] = {
            "name": str(entry.get("name") or "").strip(),
            "base_url": str(entry.get("base_url") or "").strip(),
            "info_url": info_url,
        }
        location = str(entry.get("location") or "").strip()
        note = str(entry.get("note") or "").strip()
        token_hash = _normalize_photoframe_token_hash(entry.get("token_hash"))
        token_hint = _sanitize_photoframe_text(entry.get("token_hint"), 16)
        created_at = _sanitize_photoframe_text(entry.get("created_at"), 40)

        if location:
            item["location"] = location
        if note:
            item["note"] = note
        if token_hash:
            item["token_hash"] = token_hash
        if token_hint:
            item["token_hint"] = token_hint
        if created_at:
            item["created_at"] = created_at

        frames.append(item)
    return json.dumps({"frames": frames}, ensure_ascii=False)


def _load_photoframe_token_records() -> list[Dict[str, Any]]:
    raw = str(_get_setting("photoframe_tokens", "") or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = None

    source_items: list[Any] = []
    if isinstance(parsed, list):
        source_items = parsed
    elif isinstance(parsed, dict):
        tokens = parsed.get("tokens")
        if isinstance(tokens, list):
            source_items = tokens

    out: list[Dict[str, Any]] = []
    for idx, it in enumerate(source_items):
        if not isinstance(it, dict):
            continue
        token_hash = _normalize_photoframe_token_hash(it.get("token_hash"))
        if not token_hash:
            continue
        rec_id = _sanitize_photoframe_text(it.get("id"), 64) or f"pf-token-{idx + 1}"
        token_hint = _sanitize_photoframe_text(it.get("token_hint") or it.get("token_last4"), 16)
        token_plain = _sanitize_photoframe_token_plain(it.get("token_plain") or it.get("token"))
        scope_mode = _normalize_photoframe_scope_mode(it.get("scope_mode"))
        allowed_folders = _normalize_photoframe_scope_folders(it.get("allowed_folders"))
        allowed_photo_ids = _normalize_photoframe_scope_photo_ids(it.get("allowed_photo_ids"))
        created_at = _sanitize_photoframe_text(it.get("created_at"), 40) or now_iso()
        last_seen_at = _sanitize_photoframe_text(it.get("last_seen_at"), 40)
        last_ip = _sanitize_photoframe_text(it.get("last_ip"), 120)
        last_local_ip = _sanitize_photoframe_text(it.get("last_local_ip"), 120)
        device_name = _sanitize_photoframe_text(it.get("device_name"), 80)
        last_user_agent = _sanitize_photoframe_text(it.get("last_user_agent"), 180)
        last_photo_id = _sanitize_photoframe_photo_id(it.get("last_photo_id"))
        last_photo_at = _sanitize_photoframe_text(it.get("last_photo_at"), 40)
        device_version = _sanitize_photoframe_text(it.get("device_version"), 80)
        update_job_id = _sanitize_photoframe_update_job_id(it.get("update_job_id"))
        update_status = _sanitize_photoframe_update_status(it.get("update_status"))
        update_message = _sanitize_photoframe_text(it.get("update_message"), 240)
        update_requested_at = _sanitize_photoframe_text(it.get("update_requested_at"), 40)
        update_started_at = _sanitize_photoframe_text(it.get("update_started_at"), 40)
        update_finished_at = _sanitize_photoframe_text(it.get("update_finished_at"), 40)
        update_last_report_at = _sanitize_photoframe_text(it.get("update_last_report_at"), 40)
        update_version = _sanitize_photoframe_text(it.get("update_version"), 80)
        if (not device_version) and update_version:
            device_version = update_version
        update_package_url = _normalize_photoframe_http_url(it.get("update_package_url") or it.get("update_url")) or ""
        update_package_mode = _normalize_photoframe_update_package_mode(it.get("update_package_mode"))
        if (not update_package_mode) and update_package_url:
            path_lower = str(urlparse(update_package_url).path or "").strip().lower()
            if "/update-upload/" in path_lower:
                update_package_mode = "upload"
            elif "/update-package/" in path_lower:
                update_package_mode = "source-dir"
        update_package_sha256 = _sanitize_photoframe_update_sha256(it.get("update_package_sha256"))
        last_server_base_url = _normalize_photoframe_base_url(it.get("last_server_base_url")) or ""
        feed_sync_status = _sanitize_photoframe_feed_sync_status(it.get("feed_sync_status"))
        feed_sync_sent_rev = _sanitize_photoframe_feed_rev(it.get("feed_sync_sent_rev"))
        feed_sync_sent_at = _sanitize_photoframe_text(it.get("feed_sync_sent_at"), 40)
        feed_sync_acked_rev = _sanitize_photoframe_feed_rev(it.get("feed_sync_acked_rev"))
        feed_sync_acked_at = _sanitize_photoframe_text(it.get("feed_sync_acked_at"), 40)
        feed_sync_count = _sanitize_photoframe_feed_sync_count(it.get("feed_sync_count"))
        wifi_scan_networks = _sanitize_photoframe_wifi_scan_networks(it.get("wifi_scan_networks"), max_items=80)
        wifi_scan_scanned_at = _sanitize_photoframe_text(it.get("wifi_scan_scanned_at"), 40)
        wifi_scan_error = _sanitize_photoframe_text(it.get("wifi_scan_error"), 240)
        update_settings_payload = _decode_photoframe_settings_payload(it.get("update_settings_payload"))
        settings_web_active = _sanitize_photoframe_bool(it.get("settings_web_active"))
        settings_web_started_at = _sanitize_photoframe_text(it.get("settings_web_started_at"), 40)
        settings_web_last_activity_at = _sanitize_photoframe_text(it.get("settings_web_last_activity_at"), 40)
        out.append(
            {
                "id": rec_id,
                "token_hash": token_hash,
                "token_hint": token_hint,
                "token_plain": token_plain,
                "scope_mode": scope_mode,
                "allowed_folders": allowed_folders,
                "allowed_photo_ids": allowed_photo_ids,
                "created_at": created_at,
                "last_seen_at": last_seen_at,
                "last_ip": last_ip,
                "last_local_ip": last_local_ip,
                "device_name": device_name,
                "last_user_agent": last_user_agent,
                "last_photo_id": last_photo_id,
                "last_photo_at": last_photo_at,
                "device_version": device_version,
                "update_job_id": update_job_id,
                "update_status": update_status,
                "update_message": update_message,
                "update_requested_at": update_requested_at,
                "update_started_at": update_started_at,
                "update_finished_at": update_finished_at,
                "update_last_report_at": update_last_report_at,
                "update_version": update_version,
                "update_package_url": update_package_url,
                "update_package_mode": update_package_mode,
                "update_package_sha256": update_package_sha256,
                "update_settings_payload": update_settings_payload,
                "last_server_base_url": last_server_base_url,
                "feed_sync_status": feed_sync_status,
                "feed_sync_sent_rev": feed_sync_sent_rev,
                "feed_sync_sent_at": feed_sync_sent_at,
                "feed_sync_acked_rev": feed_sync_acked_rev,
                "feed_sync_acked_at": feed_sync_acked_at,
                "feed_sync_count": feed_sync_count,
                "wifi_scan_networks": wifi_scan_networks,
                "wifi_scan_scanned_at": wifi_scan_scanned_at,
                "wifi_scan_error": wifi_scan_error,
                "settings_web_active": settings_web_active,
                "settings_web_started_at": settings_web_started_at,
                "settings_web_last_activity_at": settings_web_last_activity_at,
            }
        )
    return out


def _photoframe_update_field_names() -> tuple[str, ...]:
    return (
        "update_job_id",
        "update_status",
        "update_message",
        "update_requested_at",
        "update_started_at",
        "update_finished_at",
        "update_last_report_at",
        "update_version",
        "update_package_url",
        "update_package_mode",
        "update_package_sha256",
        "update_settings_payload",
    )


def _photoframe_settings_session_field_names() -> tuple[str, ...]:
    return (
        "settings_web_active",
        "settings_web_started_at",
        "settings_web_last_activity_at",
    )


def _photoframe_update_state_rev(rec: Dict[str, Any]) -> float:
    if not isinstance(rec, dict):
        return 0.0
    return max(
        _parse_iso_to_epoch(rec.get("update_last_report_at")),
        _parse_iso_to_epoch(rec.get("update_finished_at")),
        _parse_iso_to_epoch(rec.get("update_started_at")),
        _parse_iso_to_epoch(rec.get("update_requested_at")),
    )


def _photoframe_settings_session_state_rev(rec: Dict[str, Any]) -> float:
    if not isinstance(rec, dict):
        return 0.0
    return max(
        _parse_iso_to_epoch(rec.get("settings_web_last_activity_at")),
        _parse_iso_to_epoch(rec.get("settings_web_started_at")),
    )


def _photoframe_mark_settings_session_active(rec: Optional[Dict[str, Any]], seen_at: str = "") -> bool:
    if not isinstance(rec, dict):
        return False
    at = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    changed = False
    if not _sanitize_photoframe_bool(rec.get("settings_web_active")):
        rec["settings_web_active"] = True
        changed = True
    if not _sanitize_photoframe_text(rec.get("settings_web_started_at"), 40):
        rec["settings_web_started_at"] = at
        changed = True
    if _sanitize_photoframe_text(rec.get("settings_web_last_activity_at"), 40) != at:
        rec["settings_web_last_activity_at"] = at
        changed = True
    return changed


def _photoframe_touch_settings_session_activity(rec: Optional[Dict[str, Any]], seen_at: str = "") -> bool:
    if not isinstance(rec, dict):
        return False
    if not _sanitize_photoframe_bool(rec.get("settings_web_active")):
        return False
    at = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    if _sanitize_photoframe_text(rec.get("settings_web_last_activity_at"), 40) == at:
        return False
    rec["settings_web_last_activity_at"] = at
    if not _sanitize_photoframe_text(rec.get("settings_web_started_at"), 40):
        rec["settings_web_started_at"] = at
    return True


def _photoframe_mark_settings_session_closed(rec: Optional[Dict[str, Any]], seen_at: str = "") -> bool:
    if not isinstance(rec, dict):
        return False
    at = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    changed = False
    if _sanitize_photoframe_bool(rec.get("settings_web_active")):
        rec["settings_web_active"] = False
        changed = True
    if _sanitize_photoframe_text(rec.get("settings_web_last_activity_at"), 40) != at:
        rec["settings_web_last_activity_at"] = at
        changed = True
    return changed


def _photoframe_mark_stale_scan_if_needed(rec: Optional[Dict[str, Any]], seen_at: str) -> bool:
    if not isinstance(rec, dict):
        return False
    status = _sanitize_photoframe_update_status(rec.get("update_status"))
    if status != "queued":
        return False
    mode = _normalize_photoframe_update_package_mode(rec.get("update_package_mode"))
    if mode != "scan-wifi":
        return False
    requested_at = _sanitize_photoframe_text(rec.get("update_requested_at"), 40)
    requested_epoch = _parse_iso_to_epoch(requested_at)
    if requested_epoch <= 0:
        return False
    seen_epoch = _parse_iso_to_epoch(seen_at)
    if seen_epoch <= 0:
        seen_epoch = time.time()
    if (seen_epoch - requested_epoch) < 45.0:
        return False
    last_seen_epoch = _parse_iso_to_epoch(rec.get("last_seen_at"))
    if last_seen_epoch < (requested_epoch + 8.0):
        return False
    last_report_epoch = _parse_iso_to_epoch(rec.get("update_last_report_at"))
    if last_report_epoch > (requested_epoch + 1.0):
        return False

    rec["update_status"] = "failed"
    rec["update_message"] = "Wi-Fi scan fik ingen kvittering fra rammen. Opdater frame-softwaren og prøv igen."
    rec["update_last_report_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    if not _sanitize_photoframe_text(rec.get("update_started_at"), 40):
        rec["update_started_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    rec["update_finished_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    return True


def _photoframe_merge_wifi_scan_state(candidate: Dict[str, Any], existing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if (not isinstance(candidate, dict)) or (not isinstance(existing, dict)):
        return candidate

    candidate_scan_at = _sanitize_photoframe_text(candidate.get("wifi_scan_scanned_at"), 40)
    existing_scan_at = _sanitize_photoframe_text(existing.get("wifi_scan_scanned_at"), 40)
    candidate_scan_rev = _parse_iso_to_epoch(candidate_scan_at)
    existing_scan_rev = _parse_iso_to_epoch(existing_scan_at)

    candidate_networks = _sanitize_photoframe_wifi_scan_networks(candidate.get("wifi_scan_networks"), max_items=80)
    existing_networks = _sanitize_photoframe_wifi_scan_networks(existing.get("wifi_scan_networks"), max_items=80)
    candidate_error = _sanitize_photoframe_text(candidate.get("wifi_scan_error"), 240)
    existing_error = _sanitize_photoframe_text(existing.get("wifi_scan_error"), 240)

    use_existing = False
    if existing_scan_rev > (candidate_scan_rev + 0.001):
        use_existing = True
    elif existing_scan_rev >= (candidate_scan_rev - 0.001):
        if (not candidate_networks) and bool(existing_networks):
            use_existing = True
        elif (not candidate_error) and bool(existing_error) and (not candidate_networks):
            use_existing = True

    if use_existing:
        candidate["wifi_scan_networks"] = existing_networks
        candidate["wifi_scan_scanned_at"] = existing_scan_at
        candidate["wifi_scan_error"] = existing_error
    else:
        candidate["wifi_scan_networks"] = candidate_networks
        candidate["wifi_scan_scanned_at"] = candidate_scan_at
        candidate["wifi_scan_error"] = candidate_error
    return candidate


def _photoframe_merge_settings_session_state(candidate: Dict[str, Any], existing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if (not isinstance(candidate, dict)) or (not isinstance(existing, dict)):
        return candidate

    candidate_active = _sanitize_photoframe_bool(candidate.get("settings_web_active"))
    existing_active = _sanitize_photoframe_bool(existing.get("settings_web_active"))
    candidate_started = _sanitize_photoframe_text(candidate.get("settings_web_started_at"), 40)
    existing_started = _sanitize_photoframe_text(existing.get("settings_web_started_at"), 40)
    candidate_last_activity = _sanitize_photoframe_text(candidate.get("settings_web_last_activity_at"), 40)
    existing_last_activity = _sanitize_photoframe_text(existing.get("settings_web_last_activity_at"), 40)
    candidate_rev = _photoframe_settings_session_state_rev(candidate)
    existing_rev = _photoframe_settings_session_state_rev(existing)

    use_existing = False
    if existing_rev > (candidate_rev + 0.001):
        use_existing = True
    elif existing_active and (not candidate_active) and (existing_rev >= (candidate_rev - 0.001)):
        use_existing = True

    if use_existing:
        candidate["settings_web_active"] = existing_active
        candidate["settings_web_started_at"] = existing_started
        candidate["settings_web_last_activity_at"] = existing_last_activity
    else:
        candidate["settings_web_active"] = candidate_active
        candidate["settings_web_started_at"] = candidate_started
        candidate["settings_web_last_activity_at"] = candidate_last_activity
    return candidate


def _photoframe_merge_update_state(candidate: Dict[str, Any], existing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if (not isinstance(candidate, dict)) or (not isinstance(existing, dict)):
        return candidate

    existing_job = _sanitize_photoframe_update_job_id(existing.get("update_job_id"))
    candidate_job = _sanitize_photoframe_update_job_id(candidate.get("update_job_id"))
    candidate_status = _sanitize_photoframe_update_status(candidate.get("update_status"))
    existing_status = _sanitize_photoframe_update_status(existing.get("update_status"))
    existing_rev = _photoframe_update_state_rev(existing)
    candidate_rev = _photoframe_update_state_rev(candidate)
    active_states = {"queued", "downloading", "installing", "restarting"}
    if not existing_job:
        return _photoframe_merge_settings_session_state(_photoframe_merge_wifi_scan_state(candidate, existing), existing)
    # A freshly queued new job must win over stale persisted state.
    if candidate_job and (candidate_job != existing_job) and (candidate_status == "queued"):
        return _photoframe_merge_settings_session_state(_photoframe_merge_wifi_scan_state(candidate, existing), existing)
    # Protect an active persisted job from stale candidate snapshots that carry
    # no job id or a different (older) job id.
    if (existing_status in active_states) and (candidate_job != existing_job):
        candidate_terminal = candidate_status in {"success", "failed"}
        if (not candidate_terminal) or (candidate_rev <= (existing_rev + 0.001)):
            for key in _photoframe_update_field_names():
                candidate[key] = existing.get(key)
            if (not str(candidate.get("last_server_base_url") or "").strip()) and str(existing.get("last_server_base_url") or "").strip():
                candidate["last_server_base_url"] = _normalize_photoframe_base_url(existing.get("last_server_base_url")) or ""
            return _photoframe_merge_settings_session_state(_photoframe_merge_wifi_scan_state(candidate, existing), existing)

    rank = {
        "": 0,
        "queued": 1,
        "downloading": 2,
        "installing": 3,
        "restarting": 4,
        "success": 5,
        "failed": 5,
    }

    use_existing = False
    if existing_rev > (candidate_rev + 0.001):
        use_existing = True
    elif (existing_job == candidate_job) and (existing_rev >= (candidate_rev - 0.001)):
        if rank.get(existing_status, 0) > rank.get(candidate_status, 0):
            use_existing = True

    if use_existing:
        for key in _photoframe_update_field_names():
            candidate[key] = existing.get(key)

    if (not str(candidate.get("last_server_base_url") or "").strip()) and str(existing.get("last_server_base_url") or "").strip():
        candidate["last_server_base_url"] = _normalize_photoframe_base_url(existing.get("last_server_base_url")) or ""
    return _photoframe_merge_settings_session_state(_photoframe_merge_wifi_scan_state(candidate, existing), existing)


def _save_photoframe_token_records(records: list[Dict[str, Any]]) -> None:
    with PHOTOFRAME_TOKENS_LOCK:
        existing_by_hash: Dict[str, Dict[str, Any]] = {}
        try:
            for prev in _load_photoframe_token_records():
                h = _normalize_photoframe_token_hash(prev.get("token_hash"))
                if h and h not in existing_by_hash:
                    existing_by_hash[h] = prev
        except Exception:
            existing_by_hash = {}

        clean: list[Dict[str, Any]] = []
        seen_hashes: set[str] = set()
        for it in records:
            token_hash = _normalize_photoframe_token_hash(it.get("token_hash"))
            if (not token_hash) or (token_hash in seen_hashes):
                continue
            seen_hashes.add(token_hash)

            item = {
                "id": _sanitize_photoframe_text(it.get("id"), 64) or f"pf-token-{len(clean) + 1}",
                "token_hash": token_hash,
                "token_hint": _sanitize_photoframe_text(it.get("token_hint"), 16),
                "token_plain": _sanitize_photoframe_token_plain(it.get("token_plain") or it.get("token")),
                "scope_mode": _normalize_photoframe_scope_mode(it.get("scope_mode")),
                "allowed_folders": _normalize_photoframe_scope_folders(it.get("allowed_folders")),
                "allowed_photo_ids": _normalize_photoframe_scope_photo_ids(it.get("allowed_photo_ids")),
                "created_at": _sanitize_photoframe_text(it.get("created_at"), 40) or now_iso(),
                "last_seen_at": _sanitize_photoframe_text(it.get("last_seen_at"), 40),
                "last_ip": _sanitize_photoframe_text(it.get("last_ip"), 120),
                "last_local_ip": _sanitize_photoframe_text(it.get("last_local_ip"), 120),
                "device_name": _sanitize_photoframe_text(it.get("device_name"), 80),
                "last_user_agent": _sanitize_photoframe_text(it.get("last_user_agent"), 180),
                "last_photo_id": _sanitize_photoframe_photo_id(it.get("last_photo_id")),
                "last_photo_at": _sanitize_photoframe_text(it.get("last_photo_at"), 40),
                "device_version": _sanitize_photoframe_text(it.get("device_version"), 80),
                "update_job_id": _sanitize_photoframe_update_job_id(it.get("update_job_id")),
                "update_status": _sanitize_photoframe_update_status(it.get("update_status")),
                "update_message": _sanitize_photoframe_text(it.get("update_message"), 240),
                "update_requested_at": _sanitize_photoframe_text(it.get("update_requested_at"), 40),
                "update_started_at": _sanitize_photoframe_text(it.get("update_started_at"), 40),
                "update_finished_at": _sanitize_photoframe_text(it.get("update_finished_at"), 40),
                "update_last_report_at": _sanitize_photoframe_text(it.get("update_last_report_at"), 40),
                "update_version": _sanitize_photoframe_text(it.get("update_version"), 80),
                "update_package_url": _normalize_photoframe_http_url(it.get("update_package_url") or it.get("update_url")) or "",
                "update_package_mode": _normalize_photoframe_update_package_mode(it.get("update_package_mode")),
                "update_package_sha256": _sanitize_photoframe_update_sha256(it.get("update_package_sha256")),
                "update_settings_payload": _decode_photoframe_settings_payload(it.get("update_settings_payload")),
                "last_server_base_url": _normalize_photoframe_base_url(it.get("last_server_base_url")) or "",
                "feed_sync_status": _sanitize_photoframe_feed_sync_status(it.get("feed_sync_status")),
                "feed_sync_sent_rev": _sanitize_photoframe_feed_rev(it.get("feed_sync_sent_rev")),
                "feed_sync_sent_at": _sanitize_photoframe_text(it.get("feed_sync_sent_at"), 40),
                "feed_sync_acked_rev": _sanitize_photoframe_feed_rev(it.get("feed_sync_acked_rev")),
                "feed_sync_acked_at": _sanitize_photoframe_text(it.get("feed_sync_acked_at"), 40),
                "feed_sync_count": _sanitize_photoframe_feed_sync_count(it.get("feed_sync_count")),
                "wifi_scan_networks": _sanitize_photoframe_wifi_scan_networks(it.get("wifi_scan_networks"), max_items=80),
                "wifi_scan_scanned_at": _sanitize_photoframe_text(it.get("wifi_scan_scanned_at"), 40),
                "wifi_scan_error": _sanitize_photoframe_text(it.get("wifi_scan_error"), 240),
                "settings_web_active": _sanitize_photoframe_bool(it.get("settings_web_active")),
                "settings_web_started_at": _sanitize_photoframe_text(it.get("settings_web_started_at"), 40),
                "settings_web_last_activity_at": _sanitize_photoframe_text(it.get("settings_web_last_activity_at"), 40),
            }

            existing = existing_by_hash.get(token_hash)
            item = _photoframe_merge_update_state(item, existing)
            clean.append(item)

        if len(clean) > 500:
            clean = clean[-500:]
        _set_setting("photoframe_tokens", json.dumps({"tokens": clean}, ensure_ascii=False))


def _normalize_photoframe_scope_mode(raw: Any) -> str:
    mode = str(raw or "").strip().lower()
    if mode in {"folders", "photos"}:
        return mode
    return "all"


def _normalize_photoframe_scope_folders(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for it in raw:
        folder_raw: Any = it
        if isinstance(it, dict):
            folder_raw = it.get("folder") or it.get("folder_path") or it.get("path")
        try:
            folder = _normalize_folder_acl_path(str(folder_raw or ""))
            # Keep scope paths aligned with ACL path mapping so values like
            # uploads/originals/X collapse to uploads/X.
            folder = _normalize_folder_acl_path(_normalize_rel_path_for_acl(folder))
        except Exception:
            folder = ""
        if not folder or folder in seen:
            continue
        seen.add(folder)
        out.append(folder)
        if len(out) >= 2000:
            break
    return out


def _normalize_photoframe_scope_photo_ids(raw: Any) -> list[int]:
    if not isinstance(raw, list):
        return []
    out: list[int] = []
    seen: set[int] = set()
    for it in raw:
        try:
            pid = int(it)
        except Exception:
            continue
        if pid <= 0 or pid in seen:
            continue
        seen.add(pid)
        out.append(pid)
        if len(out) >= 10000:
            break
    return out


def _filter_photoframe_scope_photo_ids_to_images(photo_ids: list[int]) -> list[int]:
    ids = _normalize_photoframe_scope_photo_ids(photo_ids)
    if not ids:
        return []
    keep: set[int] = set()
    with closing(get_conn()) as conn:
        chunk_size = 800
        for offset in range(0, len(ids), chunk_size):
            batch = ids[offset: offset + chunk_size]
            if not batch:
                continue
            ph = ",".join(["?"] * len(batch))
            rows = conn.execute(
                f"""
                SELECT id, rel_path
                FROM photos
                WHERE id IN ({ph})
                """,
                tuple(batch),
            ).fetchall()
            for row in rows:
                try:
                    pid = int(row["id"])
                except Exception:
                    continue
                rel = str(row["rel_path"] or "")
                if Path(rel).suffix.lower() in VIDEO_EXTS:
                    continue
                keep.add(pid)
    return [pid for pid in ids if pid in keep]


def _photoframe_record_scope(rec: Optional[Dict[str, Any]]) -> tuple[str, list[str], list[int]]:
    if not isinstance(rec, dict):
        return ("all", [], [])
    mode = _normalize_photoframe_scope_mode(rec.get("scope_mode"))
    folders = _normalize_photoframe_scope_folders(rec.get("allowed_folders"))
    photos = _normalize_photoframe_scope_photo_ids(rec.get("allowed_photo_ids"))
    if mode == "folders" and not folders:
        return ("folders", [], [])
    if mode == "photos" and not photos:
        return ("photos", [], [])
    return (mode, folders, photos)


def _collect_photoframe_scope_video_rels(scope_mode: str, scope_folders: list[str], scope_photo_ids: list[int], limit: int) -> list[str]:
    max_items = max(0, int(limit or 0))
    if max_items <= 0:
        return []
    rels: list[str] = []
    seen: set[str] = set()

    with closing(get_conn()) as conn:
        rows: list[sqlite3.Row] = []
        mode = _normalize_photoframe_scope_mode(scope_mode)
        if mode == "photos":
            ids_for_query = _normalize_photoframe_scope_photo_ids(scope_photo_ids)
            if ids_for_query:
                rows_acc: list[sqlite3.Row] = []
                chunk_size = 800
                for offset in range(0, len(ids_for_query), chunk_size):
                    batch = ids_for_query[offset: offset + chunk_size]
                    if not batch:
                        continue
                    ph = ",".join(["?"] * len(batch))
                    rows_acc.extend(
                        conn.execute(
                            f"""
                            SELECT rel_path
                            FROM photos
                            WHERE id IN ({ph})
                            ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
                            """,
                            tuple(batch),
                        ).fetchall()
                    )
                    if len(rows_acc) >= max(100, max_items * 8):
                        break
                rows = rows_acc
        elif mode == "folders":
            prefixes: list[str] = []
            seen_prefixes: set[str] = set()
            for folder in _normalize_photoframe_scope_folders(scope_folders):
                for pref in _photoframe_scope_rel_prefixes(folder):
                    if pref in seen_prefixes:
                        continue
                    seen_prefixes.add(pref)
                    prefixes.append(pref)
                    if len(prefixes) >= 300:
                        break
                if len(prefixes) >= 300:
                    break
            if prefixes:
                conds: list[str] = []
                params: list[Any] = []
                for pref in prefixes:
                    conds.append("(rel_path=? OR rel_path LIKE ?)")
                    params.extend([pref, pref + "/%"])
                rows = conn.execute(
                    f"""
                    SELECT rel_path
                    FROM photos
                    WHERE {" OR ".join(conds)}
                    ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
                    LIMIT ?
                    """,
                    (*params, max(50, max_items * 6)),
                ).fetchall()
        else:
            ext_params = [f"%{ext}" for ext in sorted(VIDEO_EXTS)]
            ext_sql = " OR ".join(["LOWER(rel_path) LIKE ?"] * len(ext_params))
            rows = conn.execute(
                f"""
                SELECT rel_path
                FROM photos
                WHERE ({ext_sql})
                ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
                LIMIT ?
                """,
                (*ext_params, max_items),
            ).fetchall()

    for row in rows:
        rel = str(row["rel_path"] or "").replace("\\", "/").lstrip("/")
        if not rel or rel in seen:
            continue
        if Path(rel).suffix.lower() not in VIDEO_EXTS:
            continue
        seen.add(rel)
        rels.append(rel)
        if len(rels) >= max_items:
            break
    return rels


def _queue_photoframe_scope_video_prepare(scope_mode: str, scope_folders: list[str], scope_photo_ids: list[int]) -> int:
    if not PHOTOFRAME_VIDEO_PREPARE_ENABLED:
        return 0
    if _normalize_photoframe_scope_mode(scope_mode) not in {"photos", "folders"}:
        return 0
    try:
        rels = _collect_photoframe_scope_video_rels(
            scope_mode,
            scope_folders,
            scope_photo_ids,
            PHOTOFRAME_VIDEO_PREPARE_MAX_PER_SCOPE,
        )
    except Exception:
        return 0
    queued = 0
    for rel in rels:
        try:
            if _queue_photoframe_video_prepare(rel):
                queued += 1
        except Exception:
            continue
    return queued


def _is_photoframe_video_prepared(rel_path: str) -> bool:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    if (not rel) or (Path(rel).suffix.lower() not in VIDEO_EXTS):
        return False
    src = _disk_path_from_rel_path(rel)
    if not src.exists():
        return False
    dest = _photoframe_video_prepared_path(rel)
    try:
        if (not dest.exists()) or (dest.stat().st_size <= 0):
            return False
        return dest.stat().st_mtime >= src.stat().st_mtime
    except Exception:
        return False


def _photoframe_video_prepare_progress(scope_mode: str, scope_folders: list[str], scope_photo_ids: list[int]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "enabled": bool(PHOTOFRAME_VIDEO_PREPARE_ENABLED),
        "total": 0,
        "ready": 0,
        "queued": 0,
        "waiting": 0,
        "pending": 0,
        "pct": 0,
        "active": False,
        "capped": False,
        "sample_limit": int(PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX),
        "requeued": 0,
    }
    if (not PHOTOFRAME_VIDEO_PREPARE_ENABLED) or PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX <= 0:
        return out
    try:
        rels = _collect_photoframe_scope_video_rels(
            scope_mode,
            scope_folders,
            scope_photo_ids,
            PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX,
        )
    except Exception:
        rels = []

    total = int(len(rels))
    out["total"] = total
    out["capped"] = bool(
        PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX > 0 and total >= PHOTOFRAME_VIDEO_PREPARE_PROGRESS_MAX
    )
    if total <= 0:
        return out

    with PHOTOFRAME_VIDEO_PREPARE_LOCK:
        queued_rels = set(PHOTOFRAME_VIDEO_PREPARE_QUEUED)

    ready = 0
    queued = 0
    pending_rels: list[str] = []
    for rel in rels:
        is_prepared = _is_photoframe_video_prepared(rel)
        if is_prepared:
            ready += 1
            continue
        pending_rels.append(rel)
        if rel in queued_rels:
            queued += 1

    pending = max(0, total - ready)
    requeued = 0
    if pending > 0 and queued <= 0:
        max_requeue = min(PHOTOFRAME_VIDEO_PREPARE_REQUEUE_MAX, pending)
        for rel in pending_rels:
            if requeued >= max_requeue:
                break
            try:
                if _queue_photoframe_video_prepare(rel):
                    requeued += 1
            except Exception:
                continue
        if requeued > 0:
            queued += requeued
    if queued > pending:
        queued = pending
    waiting = max(0, pending - queued)
    pct = int(round((ready / max(1, total)) * 100))

    out["ready"] = int(ready)
    out["queued"] = int(queued)
    out["waiting"] = int(waiting)
    out["pending"] = int(pending)
    out["pct"] = max(0, min(100, pct))
    out["active"] = bool(pending > 0)
    out["requeued"] = int(requeued)
    return out


def _photoframe_scope_rel_prefixes(folder: str) -> list[str]:
    try:
        p = _normalize_folder_acl_path(folder)
    except Exception:
        return []
    if not p:
        return []
    out = [p]
    if p == "uploads":
        out.extend(["uploads/originals", "uploads/converted"])
    elif p.startswith("uploads/"):
        sub = p[len("uploads/"):].strip("/")
        if sub:
            out.extend([f"uploads/originals/{sub}", f"uploads/converted/{sub}"])
    dedup: list[str] = []
    seen: set[str] = set()
    for it in out:
        if it and it not in seen:
            seen.add(it)
            dedup.append(it)
    return dedup


def _photoframe_record_allows_photo(rec: Optional[Dict[str, Any]], photo_id: int, rel_path: str) -> bool:
    mode, folders, photos = _photoframe_record_scope(rec)
    if mode == "all":
        return True
    if mode == "photos":
        return int(photo_id) in set(_normalize_photoframe_scope_photo_ids(photos))
    rel_norm = _normalize_rel_path_for_acl(rel_path)
    for folder in _normalize_photoframe_scope_folders(folders):
        if rel_norm == folder or rel_norm.startswith(folder + "/"):
            return True
    return False


def _photoframe_status_preview(conn: sqlite3.Connection, rec: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    mode, scope_folders, scope_photo_ids = _photoframe_record_scope(rec)
    rows: list[sqlite3.Row] = []
    last_photo_id = _sanitize_photoframe_photo_id((rec or {}).get("last_photo_id") if isinstance(rec, dict) else 0)
    last_photo_at = _sanitize_photoframe_text((rec or {}).get("last_photo_at"), 40) if isinstance(rec, dict) else ""

    if last_photo_id:
        row = conn.execute(
            """
            SELECT id, rel_path, thumb_name, COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
            FROM photos
            WHERE id=?
            LIMIT 1
            """,
            (last_photo_id,),
        ).fetchone()
        if row:
            rel_path = str(row["rel_path"] or "")
            if _photoframe_record_allows_photo(rec, last_photo_id, rel_path):
                thumb_name = re.sub(r"[^a-zA-Z0-9._-]", "", str(row["thumb_name"] or ""))
                if thumb_name:
                    preview_at = last_photo_at or _sanitize_photoframe_text(row["updated_at"], 40)
                    return {
                        "preview_photo_id": last_photo_id,
                        "preview_thumb_url": f"/api/thumbs/{thumb_name}",
                        "preview_updated_at": preview_at,
                    }

    if mode == "photos":
        ids_for_query = _normalize_photoframe_scope_photo_ids(scope_photo_ids)[:900]
        if not ids_for_query:
            return {}
        ph = ",".join(["?"] * len(ids_for_query))
        rows = conn.execute(
            f"""
            SELECT id, rel_path, thumb_name, COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
            FROM photos
            WHERE id IN ({ph})
              AND thumb_name IS NOT NULL
              AND TRIM(thumb_name) <> ''
            ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
            LIMIT 80
            """,
            (*ids_for_query,),
        ).fetchall()
    elif mode == "folders":
        prefixes: list[str] = []
        seen_prefixes: set[str] = set()
        for folder in _normalize_photoframe_scope_folders(scope_folders):
            for pref in _photoframe_scope_rel_prefixes(folder):
                if pref in seen_prefixes:
                    continue
                seen_prefixes.add(pref)
                prefixes.append(pref)
                if len(prefixes) >= 300:
                    break
            if len(prefixes) >= 300:
                break
        if not prefixes:
            return {}
        conds: list[str] = []
        params: list[Any] = []
        for pref in prefixes:
            conds.append("(rel_path=? OR rel_path LIKE ?)")
            params.extend([pref, pref + "/%"])
        rows = conn.execute(
            f"""
            SELECT id, rel_path, thumb_name, COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
            FROM photos
            WHERE ({" OR ".join(conds)})
              AND thumb_name IS NOT NULL
              AND TRIM(thumb_name) <> ''
            ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
            LIMIT 80
            """,
            params,
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, rel_path, thumb_name, COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
            FROM photos
            WHERE thumb_name IS NOT NULL
              AND TRIM(thumb_name) <> ''
            ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
            LIMIT 20
            """
        ).fetchall()

    for row in rows:
        try:
            photo_id = int(row["id"])
        except Exception:
            continue
        rel_path = str(row["rel_path"] or "")
        if not _photoframe_record_allows_photo(rec, photo_id, rel_path):
            continue
        thumb_name = re.sub(r"[^a-zA-Z0-9._-]", "", str(row["thumb_name"] or ""))
        if not thumb_name:
            continue
        return {
            "preview_photo_id": photo_id,
            "preview_thumb_url": f"/api/thumbs/{thumb_name}",
            "preview_updated_at": _sanitize_photoframe_text(row["updated_at"], 40),
        }
    return {}


def _photoframe_token_lookup(token_plain: str) -> tuple[list[Dict[str, Any]], int, Optional[Dict[str, Any]]]:
    token_hash = _share_token_digest(token_plain)
    if not token_hash:
        return ([], -1, None)
    records = _load_photoframe_token_records()
    for idx, rec in enumerate(records):
        if str(rec.get("token_hash") or "").strip().lower() == token_hash:
            return (records, idx, rec)
    return (records, -1, None)


def _photoframe_find_record_by_id(records: list[Dict[str, Any]], target_id: str) -> tuple[int, Optional[Dict[str, Any]]]:
    target = _sanitize_photoframe_text(target_id, 64)
    if not target:
        return (-1, None)
    for idx, it in enumerate(records):
        rec_id = _sanitize_photoframe_text(it.get("id"), 64)
        if rec_id == target:
            return (idx, it)
    return (-1, None)


def _normalize_photoframe_proxy_ip(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    if value.startswith("[") and ("]" in value):
        value = value[1:value.find("]")]
    if "%" in value:
        value = value.split("%", 1)[0].strip()
    if (value.count(":") == 1) and ("." in value):
        host_part, port_part = value.rsplit(":", 1)
        if port_part.isdigit():
            value = host_part.strip()
    try:
        addr = ipaddress.ip_address(value)
    except Exception:
        return ""
    return addr.compressed


def _photoframe_settings_proxy_base_url(rec: Optional[Dict[str, Any]]) -> str:
    local_ip = _normalize_photoframe_proxy_ip((rec or {}).get("last_local_ip"))
    if local_ip:
        try:
            addr_local = ipaddress.ip_address(local_ip)
            if not (addr_local.is_private or addr_local.is_loopback or addr_local.is_link_local):
                addr_local = None
            if addr_local is None:
                raise ValueError("non-local")
            host_local = f"[{addr_local.compressed}]" if addr_local.version == 6 else addr_local.compressed
            return f"http://{host_local}:5001"
        except Exception:
            pass

    ip = _normalize_photoframe_proxy_ip((rec or {}).get("last_ip"))
    if not ip:
        return ""
    try:
        addr = ipaddress.ip_address(ip)
    except Exception:
        return ""
    # Preferred path is always frame-reported local IP. Fallback to the observed
    # request IP only when local IP is not available yet.
    if not (addr.is_private or addr.is_loopback or addr.is_link_local):
        return ""
    host = f"[{addr.compressed}]" if addr.version == 6 else addr.compressed
    return f"http://{host}:5001"


def _photoframe_queue_restart_command(rec: Optional[Dict[str, Any]]) -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return (False, "Mangler token-record")

    current_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    if current_status in {"downloading", "installing"}:
        return (False, "En opdatering kører allerede på enheden")

    job_id = _sanitize_photoframe_update_job_id(f"pfrst-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return (False, "Kunne ikke oprette restart-id")

    now = now_iso()
    current_version = _sanitize_photoframe_text(rec.get("device_version"), 80) or _sanitize_photoframe_text(rec.get("update_version"), 80)
    rec["update_job_id"] = job_id
    rec["update_status"] = "queued"
    rec["update_message"] = "Kiosk-genstart afventer enhed"
    rec["update_requested_at"] = now
    rec["update_started_at"] = ""
    rec["update_finished_at"] = ""
    rec["update_last_report_at"] = now
    rec["update_version"] = current_version
    rec["update_package_url"] = ""
    rec["update_package_mode"] = "restart-kiosk"
    rec["update_package_sha256"] = ""
    rec["update_settings_payload"] = {}
    return (True, job_id)


def _photoframe_queue_reset_command(rec: Optional[Dict[str, Any]]) -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return (False, "Mangler token-record")

    current_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    if current_status in {"downloading", "installing"}:
        return (False, "En opdatering kører allerede på enheden")

    job_id = _sanitize_photoframe_update_job_id(f"pfreset-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return (False, "Kunne ikke oprette reset-id")

    now = now_iso()
    current_version = _sanitize_photoframe_text(rec.get("device_version"), 80) or _sanitize_photoframe_text(rec.get("update_version"), 80)
    rec["update_job_id"] = job_id
    rec["update_status"] = "queued"
    rec["update_message"] = "Nulstilling afventer enhed"
    rec["update_requested_at"] = now
    rec["update_started_at"] = ""
    rec["update_finished_at"] = ""
    rec["update_last_report_at"] = now
    rec["update_version"] = current_version
    rec["update_package_url"] = ""
    rec["update_package_mode"] = "reset-device"
    rec["update_package_sha256"] = ""
    rec["update_settings_payload"] = {}
    return (True, job_id)


def _photoframe_queue_start_settings_web_command(rec: Optional[Dict[str, Any]]) -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return (False, "Mangler token-record")

    current_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    current_mode = _normalize_photoframe_update_package_mode(rec.get("update_package_mode"))
    if current_status in {"queued", "downloading", "installing", "restarting"}:
        if current_mode == "start-settings-web":
            existing_job = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
            if existing_job:
                return (True, existing_job)
        return (False, "En anden kommando kører allerede på enheden")

    job_id = _sanitize_photoframe_update_job_id(f"pfweb-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return (False, "Kunne ikke oprette settings-web-id")

    now = now_iso()
    current_version = _sanitize_photoframe_text(rec.get("device_version"), 80) or _sanitize_photoframe_text(rec.get("update_version"), 80)
    rec["update_job_id"] = job_id
    rec["update_status"] = "queued"
    rec["update_message"] = "Starter indstillingswebserver"
    rec["update_requested_at"] = now
    rec["update_started_at"] = ""
    rec["update_finished_at"] = ""
    rec["update_last_report_at"] = now
    rec["update_version"] = current_version
    rec["update_package_url"] = ""
    rec["update_package_mode"] = "start-settings-web"
    rec["update_package_sha256"] = ""
    rec["update_settings_payload"] = {}
    return (True, job_id)


def _photoframe_queue_stop_settings_web_command(rec: Optional[Dict[str, Any]], reason: str = "") -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return (False, "Mangler token-record")

    current_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    current_mode = _normalize_photoframe_update_package_mode(rec.get("update_package_mode"))
    if current_status in {"queued", "downloading", "installing", "restarting"}:
        if current_mode == "stop-settings-web":
            existing_job = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
            if existing_job:
                return (True, existing_job)
        return (False, "En anden kommando kører allerede på enheden")

    job_id = _sanitize_photoframe_update_job_id(f"pfwebstop-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return (False, "Kunne ikke oprette stop-id")

    now = now_iso()
    current_version = _sanitize_photoframe_text(rec.get("device_version"), 80) or _sanitize_photoframe_text(rec.get("update_version"), 80)
    message = _sanitize_photoframe_text(reason, 240) or "Lukker indstillingsforbindelse"
    rec["update_job_id"] = job_id
    rec["update_status"] = "queued"
    rec["update_message"] = message
    rec["update_requested_at"] = now
    rec["update_started_at"] = ""
    rec["update_finished_at"] = ""
    rec["update_last_report_at"] = now
    rec["update_version"] = current_version
    rec["update_package_url"] = ""
    rec["update_package_mode"] = "stop-settings-web"
    rec["update_package_sha256"] = ""
    rec["update_settings_payload"] = {}
    return (True, job_id)


def _photoframe_queue_wifi_scan_command(rec: Optional[Dict[str, Any]]) -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return (False, "Mangler token-record")

    current_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    current_mode = _normalize_photoframe_update_package_mode(rec.get("update_package_mode"))
    if current_status in {"queued", "downloading", "installing", "restarting"}:
        if current_mode == "scan-wifi":
            existing_job = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
            if existing_job:
                return (True, existing_job)
        return (False, "En anden kommando kører allerede på enheden")

    job_id = _sanitize_photoframe_update_job_id(f"pfscan-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return (False, "Kunne ikke oprette Wi-Fi scan-id")

    now = now_iso()
    current_version = _sanitize_photoframe_text(rec.get("device_version"), 80) or _sanitize_photoframe_text(rec.get("update_version"), 80)
    rec["update_job_id"] = job_id
    rec["update_status"] = "queued"
    rec["update_message"] = "Wi-Fi scan afventer enhed"
    rec["update_requested_at"] = now
    rec["update_started_at"] = ""
    rec["update_finished_at"] = ""
    rec["update_last_report_at"] = now
    rec["update_version"] = current_version
    rec["update_package_url"] = ""
    rec["update_package_mode"] = "scan-wifi"
    rec["update_package_sha256"] = ""
    rec["update_settings_payload"] = {}
    return (True, job_id)


def _photoframe_extract_settings_payload_from_request(req: Any) -> tuple[Dict[str, Any], str]:
    source: Dict[str, Any] = {}
    try:
        if req.is_json:
            body = req.get_json(silent=True) or {}
            if isinstance(body, dict):
                source = body
    except Exception:
        source = {}
    if not source:
        try:
            source = dict(req.form or {})
        except Exception:
            source = {}
    if not isinstance(source, dict):
        return ({}, "Ugyldig request payload")

    payload: Dict[str, Any] = {}
    for key in ("device_name", "server_url", "device_token", "interval_seconds", "wifi_country"):
        if key in source:
            payload[key] = source.get(key)

    ssid_present = ("wifi_ssid" in source) or ("ssid" in source)
    if ssid_present:
        payload["wifi_ssid"] = source.get("wifi_ssid", source.get("ssid"))
        payload["wifi_password"] = source.get("wifi_password", source.get("password", ""))

    clean_payload, err = _sanitize_photoframe_settings_payload(payload)
    if err:
        return ({}, err)
    if not clean_payload:
        return ({}, "Ingen gyldige indstillinger at sende")
    return (clean_payload, "")


def _photoframe_queue_settings_command(rec: Optional[Dict[str, Any]], settings_payload: Any) -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return (False, "Mangler token-record")

    clean_payload, err = _sanitize_photoframe_settings_payload(settings_payload if isinstance(settings_payload, dict) else {})
    if err:
        return (False, err)
    if not clean_payload:
        return (False, "Ingen gyldige indstillinger at sende")

    current_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    if current_status in {"queued", "downloading", "installing", "restarting"}:
        return (False, "En anden kommando kører allerede på enheden")

    job_id = _sanitize_photoframe_update_job_id(f"pfcfg-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return (False, "Kunne ikke oprette settings-id")

    now = now_iso()
    current_version = _sanitize_photoframe_text(rec.get("device_version"), 80) or _sanitize_photoframe_text(rec.get("update_version"), 80)
    rec["update_job_id"] = job_id
    rec["update_status"] = "queued"
    rec["update_message"] = "Indstillinger afventer enhed"
    rec["update_requested_at"] = now
    rec["update_started_at"] = ""
    rec["update_finished_at"] = ""
    rec["update_last_report_at"] = now
    rec["update_version"] = current_version
    rec["update_package_url"] = ""
    rec["update_package_mode"] = "apply-settings"
    rec["update_package_sha256"] = ""
    rec["update_settings_payload"] = clean_payload
    return (True, job_id)


def _photoframe_maybe_queue_settings_auto_stop(rec: Optional[Dict[str, Any]], seen_at: str) -> tuple[bool, str]:
    if not isinstance(rec, dict):
        return (False, "")
    if not _sanitize_photoframe_bool(rec.get("settings_web_active")):
        return (False, "")

    status = _sanitize_photoframe_update_status(rec.get("update_status"))
    if status in {"queued", "downloading", "installing", "restarting"}:
        return (False, "")

    now_epoch = _parse_iso_to_epoch(seen_at)
    if now_epoch <= 0:
        now_epoch = time.time()
    last_activity = _sanitize_photoframe_text(rec.get("settings_web_last_activity_at"), 40)
    if not last_activity:
        last_activity = _sanitize_photoframe_text(rec.get("settings_web_started_at"), 40)
    last_activity_epoch = _parse_iso_to_epoch(last_activity)
    if last_activity_epoch <= 0:
        return (False, "")

    idle_seconds = max(0.0, now_epoch - last_activity_epoch)
    if idle_seconds < float(PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC):
        return (False, "")

    idle_minutes = max(1, int(round(float(PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC) / 60.0)))
    reason = f"Lukker forbindelsen efter {idle_minutes} min inaktivitet"
    return _photoframe_queue_stop_settings_web_command(rec, reason=reason)


def _photoframe_settings_fallback_defaults(rec: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "device_name": _sanitize_photoframe_text((rec or {}).get("device_name"), 40),
        "server_url": _normalize_photoframe_base_url((rec or {}).get("last_server_base_url")) or "",
        "device_token": _sanitize_photoframe_token_plain((rec or {}).get("token_plain")),
        "interval_seconds": 5,
        "wifi_country": "DK",
        "wifi_ssid": "",
    }
    pending_payload = _decode_photoframe_settings_payload((rec or {}).get("update_settings_payload"))
    if isinstance(pending_payload, dict):
        if pending_payload.get("device_name"):
            defaults["device_name"] = _normalize_photoframe_device_name(pending_payload.get("device_name"), 40)
        if pending_payload.get("server_url"):
            defaults["server_url"] = _normalize_photoframe_base_url(pending_payload.get("server_url")) or defaults["server_url"]
        if pending_payload.get("device_token"):
            defaults["device_token"] = _sanitize_photoframe_token_plain(pending_payload.get("device_token"))
        if pending_payload.get("interval_seconds") is not None:
            defaults["interval_seconds"] = _normalize_photoframe_interval_seconds(pending_payload.get("interval_seconds"), 5)
        if pending_payload.get("wifi_country"):
            defaults["wifi_country"] = _normalize_photoframe_wifi_country(pending_payload.get("wifi_country")) or "DK"
        if pending_payload.get("wifi_ssid"):
            defaults["wifi_ssid"] = _sanitize_photoframe_text(pending_payload.get("wifi_ssid"), 120)
    return defaults


def _photoframe_settings_fallback_page(
    rec: Optional[Dict[str, Any]],
    proxy_root: str,
    status_code: int = 200,
    notice: str = "",
    error: str = "",
    transport_error: str = "",
    direct_available: bool = False,
):
    root = str(proxy_root or "").rstrip("/")
    defaults = _photoframe_settings_fallback_defaults(rec)
    update_status = _sanitize_photoframe_update_status((rec or {}).get("update_status"))
    update_message = _sanitize_photoframe_text((rec or {}).get("update_message"), 240)
    update_job_id = _sanitize_photoframe_update_job_id((rec or {}).get("update_job_id"))
    update_mode = _normalize_photoframe_update_package_mode((rec or {}).get("update_package_mode"))
    update_requested_at = _sanitize_photoframe_text((rec or {}).get("update_requested_at"), 40)
    update_last_report_at = _sanitize_photoframe_text((rec or {}).get("update_last_report_at"), 40)
    last_seen_at = _sanitize_photoframe_text((rec or {}).get("last_seen_at"), 40)
    last_ip = _sanitize_photoframe_text((rec or {}).get("last_ip"), 120) or _sanitize_photoframe_text((rec or {}).get("last_local_ip"), 120)
    device_name = _sanitize_photoframe_text((rec or {}).get("device_name"), 80) or "Fotoramme"
    wifi_scan_networks = _sanitize_photoframe_wifi_scan_networks((rec or {}).get("wifi_scan_networks"), max_items=80)
    wifi_scan_scanned_at = _sanitize_photoframe_text((rec or {}).get("wifi_scan_scanned_at"), 40)
    wifi_scan_error = _sanitize_photoframe_text((rec or {}).get("wifi_scan_error"), 240)
    settings_web_active = _sanitize_photoframe_bool((rec or {}).get("settings_web_active"))
    settings_web_started_at = _sanitize_photoframe_text((rec or {}).get("settings_web_started_at"), 40)
    settings_web_last_activity_at = _sanitize_photoframe_text((rec or {}).get("settings_web_last_activity_at"), 40)
    active_update_statuses = {"queued", "downloading", "installing", "restarting"}
    update_active = update_status in active_update_statuses
    scan_active = update_active and (update_mode == "scan-wifi")
    requested_epoch = _parse_iso_to_epoch(update_requested_at)
    last_seen_epoch = _parse_iso_to_epoch(last_seen_at)
    last_report_epoch = _parse_iso_to_epoch(update_last_report_at)
    wait_seconds = int(max(0.0, time.time() - requested_epoch)) if requested_epoch > 0 else 0
    scan_probably_stuck = bool(
        scan_active
        and (requested_epoch > 0)
        and (wait_seconds >= 35)
        and (last_seen_epoch >= (requested_epoch + 8.0))
        and (last_report_epoch <= (requested_epoch + 1.0))
    )
    settings_timeout_minutes = max(1, int(round(float(PHOTOFRAME_SETTINGS_IDLE_TIMEOUT_SEC) / 60.0)))
    session_idle_seconds = 0
    session_idle_source = settings_web_last_activity_at or settings_web_started_at
    session_idle_epoch = _parse_iso_to_epoch(session_idle_source)
    if settings_web_active and session_idle_epoch > 0:
        session_idle_seconds = int(max(0.0, time.time() - session_idle_epoch))
    auto_refresh_enabled = bool(update_active)

    options_html = []
    current_country = _normalize_photoframe_wifi_country(defaults.get("wifi_country")) or "DK"
    for code, label in PHOTOFRAME_WIFI_COUNTRY_CHOICES:
        selected = " selected" if current_country == code else ""
        options_html.append(f"<option value='{html.escape(code)}'{selected}>{html.escape(label)} ({html.escape(code)})</option>")
    countries = "".join(options_html)
    wifi_ssid_options = "".join([f"<option value='{html.escape(str(net.get('ssid') or ''))}'>" for net in wifi_scan_networks])

    wifi_scan_meta = []
    if wifi_scan_scanned_at:
        wifi_scan_meta.append(f"Sidst scannet: {wifi_scan_scanned_at}")
    if wifi_scan_error:
        wifi_scan_meta.append(f"Scan-fejl: {wifi_scan_error}")
    if wifi_scan_scanned_at and (not wifi_scan_networks) and (not wifi_scan_error):
        wifi_scan_meta.append("Scan gennemført, men ingen Wi-Fi netværk blev fundet")
    wifi_scan_meta_block = ""
    if wifi_scan_meta:
        wifi_scan_meta_block = f"<p class='meta'>{html.escape(' | '.join(wifi_scan_meta))}</p>"

    wifi_scan_list_block = ""
    if wifi_scan_networks:
        network_rows = []
        for net in wifi_scan_networks:
            ssid = _sanitize_photoframe_text(net.get("ssid"), 120) or "-"
            security = _sanitize_photoframe_text(net.get("security"), 120) or "Åbent netværk"
            signal_value = int(net.get("signal", -1) or -1)
            signal_label = str(signal_value) if signal_value >= 0 else "-"
            security_lower = str(security or "").strip().lower()
            is_open_network = bool((not security_lower) or ("åbent" in security_lower) or ("open" in security_lower))
            ssid_attr = html.escape(ssid, quote=True)
            network_rows.append(
                "<div class='network'>"
                f"<strong>{html.escape(ssid)}</strong>"
                f"<span>Signal: {html.escape(signal_label)}</span>"
                f"<span>{html.escape(security)}</span>"
                f"<button type='button' class='secondary pick-wifi' data-ssid='{ssid_attr}' data-open='{'1' if is_open_network else '0'}'>Forbind til Wi-Fi</button>"
                "</div>"
            )
        wifi_scan_list_block = "<div class='network-list'>" + "".join(network_rows) + "</div>"
    elif wifi_scan_scanned_at and not wifi_scan_error:
        wifi_scan_list_block = "<p class='meta'>Ingen Wi-Fi netværk fundet ved seneste scan.</p>"
    elif not wifi_scan_error:
        wifi_scan_list_block = "<p class='meta'>Ingen Wi-Fi netværk i cache endnu. Tryk \"Opdater Wi-Fi liste\".</p>"

    notice_block = ""
    err_text = _sanitize_photoframe_text(error, 320)
    note_text = _sanitize_photoframe_text(notice, 320)
    transport_text = _sanitize_photoframe_text(transport_error, 320)
    if err_text:
        notice_block = f"<div class='notice err'>{html.escape(err_text)}</div>"
    elif note_text:
        notice_block = f"<div class='notice ok'>{html.escape(note_text)}</div>"
    elif transport_text:
        notice_block = (
            "<div class='notice warn'>Kunne ikke åbne rammens lokale web-indstillinger. "
            "Du kan sende indstillinger via FjordLens i stedet.<br>"
            f"<span>{html.escape(transport_text)}</span></div>"
        )

    status_block = ""
    scan_wait_live_block = ""
    if update_status or update_message or update_job_id:
        parts = []
        if update_status:
            parts.append(f"Status: {update_status}")
        if update_mode:
            parts.append(f"Type: {update_mode}")
        if update_job_id:
            parts.append(f"Job: {update_job_id}")
        if update_message:
            parts.append(update_message)
        status_block = f"<div class='status'>{html.escape(' | '.join(parts))}</div>"
    if scan_active and wait_seconds > 0:
        scan_wait_live_block = (
            "<p class='meta'>"
            f"<span id='scan-wait-live' data-seconds='{int(wait_seconds)}'>Venter: {int(wait_seconds)}s</span>"
            "</p>"
        )

    scan_hint_block = ""
    if scan_active and (not scan_probably_stuck):
        scan_hint_block = "<p class='meta'>Venter på svar fra rammen. Siden opdateres automatisk hvert 3. sekund.</p>"
    elif scan_probably_stuck:
        scan_hint_block = (
            "<div class='notice warn'>Wi-Fi scan afventer stadig svar fra rammen. "
            "Hvis dette fortsætter, er frame-softwaren sandsynligvis for gammel til scan-funktionen. "
            "Opdater rammen til nyeste version og prøv igen.</div>"
        )

    settings_session_meta_parts = [f"Forbindelsen lukkes automatisk efter {settings_timeout_minutes} min inaktivitet."]
    if settings_web_active:
        settings_session_meta_parts.append("Status: aktiv")
        if settings_web_last_activity_at:
            settings_session_meta_parts.append(f"Sidste aktivitet: {settings_web_last_activity_at}")
        if settings_web_started_at:
            settings_session_meta_parts.append(f"Startet: {settings_web_started_at}")
    else:
        settings_session_meta_parts.append("Status: ikke aktiv")
    settings_session_meta_block = f"<p class='meta'>{html.escape(' | '.join(settings_session_meta_parts))}</p>"
    settings_session_idle_block = ""
    if settings_web_active and session_idle_seconds > 0:
        settings_session_idle_block = (
            "<p class='meta'>"
            f"<span id='settings-idle-live' data-seconds='{int(session_idle_seconds)}'>Inaktiv i {int(session_idle_seconds)}s</span>"
            "</p>"
        )

    page_script = (
        "<script>"
        "(function(){"
        "function bindLiveSeconds(id,prefix){"
        "var el=document.getElementById(id);"
        "if(!el){return;}"
        "var s=parseInt(el.getAttribute('data-seconds')||'0',10);"
        "if(!(s>=0)){s=0;}"
        "window.setInterval(function(){"
        "s+=1;"
        "el.textContent=prefix+s+'s';"
        "el.setAttribute('data-seconds',String(s));"
        "},1000);"
        "}"
        "bindLiveSeconds('scan-wait-live','Venter: ');"
        "bindLiveSeconds('settings-idle-live','Inaktiv i ');"
        "var ssidInput=document.querySelector(\"input[name='wifi_ssid']\");"
        "var pwInput=document.querySelector(\"input[name='wifi_password']\");"
        "var note=document.getElementById('wifi-select-note');"
        "var picks=document.querySelectorAll('.pick-wifi');"
        "for(var i=0;i<picks.length;i++){"
        "picks[i].addEventListener('click',function(){"
        "var ssid=(this.getAttribute('data-ssid')||'').trim();"
        "var isOpen=(this.getAttribute('data-open')==='1');"
        "if(!ssid||!ssidInput){return;}"
        "if(pwInput){"
        "if(isOpen){pwInput.value='';}"
        "else{"
        "var promptText='Skriv Wi-Fi kode til \"'+ssid+'\"';"
        "var entered=window.prompt(promptText,pwInput.value||'');"
        "if(entered===null){return;}"
        "pwInput.value=entered;"
        "}"
        "}"
        "ssidInput.value=ssid;"
        "if(note){"
        "if(isOpen){"
        "note.textContent='Valgt Wi-Fi: '+ssid+' (åbent netværk). Tryk \"Send indstillinger til rammen\" for at anvende.';"
        "}else{"
        "note.textContent='Valgt Wi-Fi: '+ssid+'. Koden er klar. Tryk \"Send indstillinger til rammen\" for at anvende.';"
        "}"
        "}"
        "});"
        "}"
    )
    if auto_refresh_enabled:
        target = html.escape(f"{root}/remote-settings", quote=True)
        page_script += (
            "var t=window.setTimeout(function(){"
            "if(document.visibilityState==='hidden'){return;}"
            f"window.location.replace('{target}');"
            "},3000);"
            "window.addEventListener('beforeunload',function(){try{clearTimeout(t);}catch(e){}});"
        )
    page_script += "})();</script>"

    if direct_available:
        intro_block = (
            f"<h1>Fjernindstillinger via FjordLens</h1><p>{html.escape(device_name)} er på lokalnettet. "
            "Indstillingerne nedenfor sendes via frame API, så visningen er den samme på lokal og fjern adgang.</p>"
        )
    else:
        intro_block = (
            f"<h1>Fjernindstillinger via FjordLens</h1><p>{html.escape(device_name)} kan ikke nås direkte på lokalnet lige nu. "
            "Indstillingerne nedenfor sendes som en kommando via frame API og anvendes ved næste heartbeat.</p>"
        )

    body = (
        "<!doctype html><html lang='da'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Photoframe fjernindstillinger</title>"
        "<style>"
        "body{font-family:Arial,Helvetica,sans-serif;background:#0f1318;color:#e6edf3;margin:0;padding:20px;}"
        ".card{max-width:860px;margin:0 auto;background:#171b21;border:1px solid #2f363d;border-radius:12px;padding:18px;}"
        "h1{font-size:22px;margin:0 0 8px;}p{line-height:1.45;color:#b9c4d0;}label{display:block;margin:10px 0 6px;font-weight:600;}"
        "input,select{width:100%;box-sizing:border-box;background:#0f141a;color:#e6edf3;border:1px solid #35404a;border-radius:8px;padding:10px;}"
        ".row{display:grid;grid-template-columns:1fr 1fr;gap:12px;}"
        ".row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}"
        ".notice{margin:10px 0 14px;padding:10px 12px;border-radius:8px;border:1px solid transparent;}"
        ".notice.ok{background:#14301f;border-color:#245c37;}"
        ".notice.warn{background:#2b240f;border-color:#6d5a22;}"
        ".notice.err{background:#32191b;border-color:#7f3d3d;}"
        ".status{margin:12px 0;padding:10px 12px;border-radius:8px;background:#111821;border:1px solid #2c3d4d;color:#c6d4e1;}"
        ".meta{font-size:13px;color:#9fb0bf;}"
        ".actions{display:flex;gap:10px;align-items:center;margin-top:14px;}"
        "button{background:#2f81f7;color:white;border:0;border-radius:8px;padding:10px 16px;cursor:pointer;font-weight:600;}"
        "button.secondary{background:#263243;color:#d7e5ff;border:1px solid #3f4f66;}"
        "button.danger{background:#7b2b2b;color:#fff;border:1px solid #a54747;}"
        "button:disabled{opacity:.6;cursor:not-allowed;}"
        ".link{color:#9cc2ff;text-decoration:none;font-size:14px;}"
        ".network-list{display:grid;grid-template-columns:1fr;gap:8px;margin-top:10px;}"
        ".network{display:grid;grid-template-columns:minmax(0,1.2fr) auto auto auto;gap:10px;align-items:center;padding:8px 10px;border:1px solid #2b3540;border-radius:8px;background:#0f141a;font-size:14px;}"
        ".network .pick-wifi{padding:6px 12px;font-size:13px;white-space:nowrap;}"
        "@media (max-width:780px){.row,.row3{grid-template-columns:1fr;}}"
        "@media (max-width:780px){.network{grid-template-columns:1fr;}}"
        "</style></head><body><div class='card'>"
        f"{intro_block}"
        f"{notice_block}"
        f"{status_block}"
        f"{scan_wait_live_block}"
        f"{scan_hint_block}"
        "<form method='post' action='" + html.escape(f"{root}/remote-settings/save") + "'>"
        "<input type='hidden' name='fallback_mode' value='1'>"
        "<div class='row'>"
        "<div><label>Navn på fotorammen</label>"
        f"<input name='device_name' value='{html.escape(str(defaults.get('device_name') or ''))}' placeholder='Fx Stue-Ramme'></div>"
        "<div><label>Tid pr billede (sekunder)</label>"
        f"<input type='number' name='interval_seconds' min='1' max='60' step='1' value='{int(defaults.get('interval_seconds') or 5)}'></div>"
        "</div>"
        "<div class='row3'>"
        "<div><label>Land</label><select name='wifi_country'>" + countries + "</select></div>"
        "<div><label>Wi-Fi SSID (valgfri)</label>"
        f"<input name='wifi_ssid' list='wifi-ssid-list' value='{html.escape(str(defaults.get('wifi_ssid') or ''))}' placeholder='Fx MitWiFi'></div>"
        "<div><label>Wi-Fi adgangskode (påkrævet for lukkede netværk)</label><input type='password' name='wifi_password' placeholder='Skriv Wi-Fi kode her'></div>"
        "</div>"
        "<datalist id='wifi-ssid-list'>" + wifi_ssid_options + "</datalist>"
        "<div class='row'>"
        "<div><label>Server URL</label>"
        f"<input name='server_url' value='{html.escape(str(defaults.get('server_url') or ''))}' placeholder='https://photos.ditdomaene.dk'></div>"
        "<div><label>Device token</label>"
        f"<input name='device_token' value='{html.escape(str(defaults.get('device_token') or ''))}' placeholder='Indsæt token fra FjordLens'></div>"
        "</div>"
        "<div class='actions'>"
        "<button type='submit' class='secondary' formaction='" + html.escape(f"{root}/wifi/scan") + "' formmethod='post' formnovalidate>Opdater Wi-Fi liste</button>"
        "</div>"
        f"{wifi_scan_meta_block}"
        f"{wifi_scan_list_block}"
        "<p id='wifi-select-note' class='meta'></p>"
        "<div class='actions'><button type='submit'>Send indstillinger til rammen</button>"
        f"<a class='link' href='{html.escape(root + '/remote-settings')}'>Opdater side</a></div>"
        "</form>"
        "<form method='post' action='" + html.escape(f"{root}/connection/close") + "'>"
        "<div class='actions'><button type='submit' class='secondary danger'>Luk forbindelsen</button></div>"
        "</form>"
        f"{settings_session_meta_block}"
        f"{settings_session_idle_block}"
        "<p class='meta'>"
        f"Sidst set: {html.escape(last_seen_at or 'ukendt')} | Sidste IP: {html.escape(last_ip or 'ukendt')}"
        "</p>"
        f"{page_script}"
        "</div></body></html>"
    )
    resp = make_response(body, int(status_code))
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


def _photoframe_settings_proxy_error_page(message: str, status_code: int = 502):
    msg = html.escape(_sanitize_photoframe_text(message, 400) or "Ukendt fejl")
    body = (
        "<!doctype html><html lang='da'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Photoframe indstillinger</title>"
        "<style>"
        "body{font-family:Arial,Helvetica,sans-serif;background:#121417;color:#f1f3f5;margin:0;padding:24px;}"
        ".card{max-width:760px;margin:0 auto;background:#1f2329;border:1px solid #343a40;border-radius:12px;padding:18px;}"
        "h1{font-size:22px;margin:0 0 10px;}p{line-height:1.45;color:#d0d7de;}"
        ".err{display:inline-block;margin-top:10px;padding:10px 12px;border-radius:8px;background:#3b2222;border:1px solid #7f3d3d;}"
        "</style></head><body><div class='card'>"
        "<h1>Kunne ikke åbne photoframe-indstillinger</h1>"
        "<p>Tjek at rammen er online og har sendt en lokal IP-adresse til FjordLens.</p>"
        f"<div class='err'>{msg}</div>"
        "</div></body></html>"
    )
    resp = make_response(body, int(status_code))
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


def _rewrite_photoframe_settings_html(body: str, proxy_root: str) -> str:
    root = str(proxy_root or "").rstrip("/")
    if not root:
        return body

    def _repl(match: re.Match) -> str:
        return f"{match.group(1)}{root}/"

    return re.sub(
        r"(?i)(\b(?:href|src|action|formaction)\s*=\s*[\"'])/(?!/)",
        _repl,
        str(body or ""),
    )


def _rewrite_photoframe_settings_location(location: str, proxy_root: str, target_base_url: str) -> str:
    loc = str(location or "").strip()
    if not loc:
        return ""
    root = str(proxy_root or "").rstrip("/")
    if not root:
        return loc
    if loc.startswith("/"):
        return f"{root}/{loc.lstrip('/')}"

    parsed = urlparse(loc)
    if (not parsed.scheme) and (not parsed.netloc):
        if loc.startswith("?") or loc.startswith("#"):
            return loc
        return f"{root}/{loc.lstrip('/')}"

    target = urlparse(str(target_base_url or ""))
    parsed_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    target_port = target.port or (443 if target.scheme == "https" else 80)
    same_host = str(parsed.hostname or "").strip().lower() == str(target.hostname or "").strip().lower()
    if same_host and (parsed_port == target_port):
        path = str(parsed.path or "/")
        new_path = f"{root}/{path.lstrip('/')}"
        return urlunparse(("", "", new_path, "", parsed.query, parsed.fragment))
    return loc


def _photoframe_proxy_response(upstream: requests.Response, proxy_root: str, target_base_url: str):
    content_type = str(upstream.headers.get("Content-Type") or "")
    is_html = "text/html" in content_type.lower()
    body_bytes = upstream.content or b""
    if is_html:
        encoding = str(upstream.encoding or "utf-8")
        try:
            body_text = body_bytes.decode(encoding, errors="replace")
        except Exception:
            body_text = body_bytes.decode("utf-8", errors="replace")
        body_bytes = _rewrite_photoframe_settings_html(body_text, proxy_root).encode("utf-8")

    resp = make_response(body_bytes, int(upstream.status_code))
    skip_headers = {
        "content-length",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "trailers",
        "upgrade",
        "set-cookie",
    }
    for key, value in upstream.headers.items():
        low = str(key or "").lower()
        if low in skip_headers:
            continue
        if low == "location":
            rewritten = _rewrite_photoframe_settings_location(value, proxy_root, target_base_url)
            if rewritten:
                resp.headers[key] = rewritten
            continue
        if is_html and (low == "content-type"):
            resp.headers[key] = "text/html; charset=utf-8"
            continue
        resp.headers[key] = value
    if is_html and ("Content-Type" not in resp.headers):
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


def _parse_iso_to_epoch(value: Any) -> float:
    raw = str(value or "").strip()
    if not raw:
        return 0.0
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return float(datetime.fromisoformat(raw).timestamp())
    except Exception:
        return 0.0


def _photoframe_update_presence_fields(rec: Dict[str, Any], req: Any, seen_at: str) -> None:
    if not isinstance(rec, dict):
        return
    rec["last_seen_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    rec["last_ip"] = _request_client_ip()
    local_ip_raw = ""
    try:
        local_ip_raw = str(req.args.get("local_ip") or req.headers.get("X-Photoframe-Local-IP") or "").strip()
    except Exception:
        local_ip_raw = ""
    local_ip = _normalize_photoframe_proxy_ip(local_ip_raw)
    if local_ip:
        try:
            local_addr = ipaddress.ip_address(local_ip)
            if local_addr.is_private or local_addr.is_loopback or local_addr.is_link_local:
                rec["last_local_ip"] = local_addr.compressed
        except Exception:
            pass
    rec["last_user_agent"] = _sanitize_photoframe_text(req.headers.get("User-Agent"), 180)
    frame_name = _sanitize_photoframe_text(
        req.headers.get("X-Photoframe-Name") or req.args.get("name"),
        80,
    )
    if frame_name:
        rec["device_name"] = frame_name
    frame_version = _sanitize_photoframe_text(
        req.headers.get("X-Photoframe-Version") or req.args.get("version"),
        80,
    )
    if frame_version:
        rec["device_version"] = frame_version
    # Prefer the exact base URL the frame is currently using for feed/heartbeat.
    # This avoids generating update package URLs on a different public host that
    # may enforce extra auth (401/403) compared to the frame's direct endpoint.
    try:
        req_base = _normalize_photoframe_base_url(str(getattr(req, "url_root", "")).rstrip("/"))
    except Exception:
        req_base = ""
    try:
        public_base = _normalize_photoframe_base_url(_request_public_base_url())
    except Exception:
        public_base = ""
    base = req_base or public_base
    if base:
        rec["last_server_base_url"] = base


def _photoframe_try_set_current_photo(
    conn: sqlite3.Connection,
    rec: Optional[Dict[str, Any]],
    photo_id_raw: Any,
    seen_at: str,
) -> int:
    if not isinstance(rec, dict):
        return 0
    photo_id = _sanitize_photoframe_photo_id(photo_id_raw)
    if photo_id <= 0:
        return 0
    row = conn.execute("SELECT rel_path FROM photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        return 0
    rel_path = str(row["rel_path"] or "")
    if not _photoframe_record_allows_photo(rec, photo_id, rel_path):
        return 0
    rec["last_photo_id"] = photo_id
    rec["last_photo_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    return photo_id


def _photoframe_location_from_row(row: Any) -> tuple[str, str, str]:
    city = ""
    country = ""
    location = ""
    gps_name = _sanitize_photoframe_text((row["gps_name"] if row is not None else ""), 120)

    mj_raw = ""
    try:
        mj_raw = str((row["metadata_json"] if row is not None else "") or "").strip()
    except Exception:
        mj_raw = ""
    if mj_raw:
        try:
            mj = json.loads(mj_raw)
            if isinstance(mj, dict):
                geo = mj.get("geo")
                if isinstance(geo, dict):
                    city = _sanitize_photoframe_text(geo.get("city"), 80)
                    country = _sanitize_photoframe_text(geo.get("country"), 80)
        except Exception:
            pass

    if city or country:
        location = ", ".join([x for x in [city, country] if x])
    elif gps_name:
        location = gps_name
        # Best effort split when gps_name already looks like "City, Country".
        parts = [p.strip() for p in gps_name.split(",") if p and p.strip()]
        if len(parts) >= 2:
            if not city:
                city = _sanitize_photoframe_text(parts[0], 80)
            if not country:
                country = _sanitize_photoframe_text(parts[-1], 80)

    return (
        _sanitize_photoframe_text(location, 120),
        _sanitize_photoframe_text(city, 80),
        _sanitize_photoframe_text(country, 80),
    )


def _photoframe_date_from_row(row: Any) -> str:
    captured_at = _sanitize_photoframe_text((row["captured_at"] if row is not None else ""), 40)
    if not captured_at:
        return ""

    # Prefer dates that clearly come from photo metadata.
    exif_raw = ""
    try:
        exif_raw = str((row["exif_json"] if row is not None else "") or "").strip()
    except Exception:
        exif_raw = ""
    if exif_raw:
        try:
            exif_map = json.loads(exif_raw)
            if isinstance(exif_map, dict):
                for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                    if str(exif_map.get(key) or "").strip():
                        return captured_at
        except Exception:
            pass

    # Fallback guard: if captured_at equals fs timestamps, treat as unknown.
    modified_fs = _sanitize_photoframe_text((row["modified_fs"] if row is not None else ""), 40)
    created_fs = _sanitize_photoframe_text((row["created_fs"] if row is not None else ""), 40)
    if captured_at and (captured_at not in {modified_fs, created_fs}):
        return captured_at
    return ""


def _photoframe_compute_feed_revision(images: list[Dict[str, Any]], scope_mode: str = "") -> str:
    h = hashlib.sha256()
    h.update(str(scope_mode or "").strip().lower().encode("utf-8", errors="ignore"))
    for item in images or []:
        pid = str((item or {}).get("id") or "").strip()
        updated_at = str((item or {}).get("updated_at") or "").strip()
        media_type = str((item or {}).get("media_type") or "").strip().lower()
        ext = str((item or {}).get("ext") or "").strip().lower()
        location = str((item or {}).get("location") or "").strip()
        city = str((item or {}).get("location_city") or "").strip()
        country = str((item or {}).get("location_country") or "").strip()
        captured_at = str((item or {}).get("captured_at") or "").strip()
        if not pid:
            continue
        h.update(b"|")
        h.update(pid.encode("utf-8", errors="ignore"))
        h.update(b"@")
        h.update(updated_at.encode("utf-8", errors="ignore"))
        h.update(b"#")
        h.update(media_type.encode("utf-8", errors="ignore"))
        h.update(b":")
        h.update(ext.encode("utf-8", errors="ignore"))
        h.update(b"^")
        h.update(location.encode("utf-8", errors="ignore"))
        h.update(b",")
        h.update(city.encode("utf-8", errors="ignore"))
        h.update(b",")
        h.update(country.encode("utf-8", errors="ignore"))
        h.update(b"~")
        h.update(captured_at.encode("utf-8", errors="ignore"))
    return _sanitize_photoframe_feed_rev(h.hexdigest()[:16])


def _photoframe_mark_feed_sync_sent(rec: Optional[Dict[str, Any]], feed_rev: str, feed_count: int, seen_at: str) -> bool:
    if not isinstance(rec, dict):
        return False
    rev = _sanitize_photoframe_feed_rev(feed_rev)
    if not rev:
        return False
    now_clean = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    count = _sanitize_photoframe_feed_sync_count(feed_count)
    sent_rev = _sanitize_photoframe_feed_rev(rec.get("feed_sync_sent_rev"))
    acked_rev = _sanitize_photoframe_feed_rev(rec.get("feed_sync_acked_rev"))
    status = _sanitize_photoframe_feed_sync_status(rec.get("feed_sync_status"))

    # If the frame already acknowledged this exact feed revision, keep "sent".
    if acked_rev and (acked_rev == rev):
        changed = False
        if status != "sent":
            rec["feed_sync_status"] = "sent"
            changed = True
        if sent_rev != rev:
            rec["feed_sync_sent_rev"] = rev
            changed = True
        if _sanitize_photoframe_feed_sync_count(rec.get("feed_sync_count")) != count:
            rec["feed_sync_count"] = count
            changed = True
        if not _sanitize_photoframe_text(rec.get("feed_sync_acked_at"), 40):
            rec["feed_sync_acked_at"] = now_clean
            changed = True
        return changed

    changed = False
    if status != "sending":
        rec["feed_sync_status"] = "sending"
        changed = True
    if sent_rev != rev:
        rec["feed_sync_sent_rev"] = rev
        changed = True
    if _sanitize_photoframe_feed_sync_count(rec.get("feed_sync_count")) != count:
        rec["feed_sync_count"] = count
        changed = True
    if _sanitize_photoframe_text(rec.get("feed_sync_sent_at"), 40) != now_clean:
        rec["feed_sync_sent_at"] = now_clean
        changed = True
    return changed


def _photoframe_apply_feed_sync_ack(rec: Optional[Dict[str, Any]], feed_rev_raw: Any, seen_at: str, allow_fallback: bool = False) -> bool:
    if not isinstance(rec, dict):
        return False
    now_clean = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    sent_rev = _sanitize_photoframe_feed_rev(rec.get("feed_sync_sent_rev"))
    rev = _sanitize_photoframe_feed_rev(feed_rev_raw)
    if not rev:
        if allow_fallback and sent_rev:
            rev = sent_rev
        else:
            return False
    # Ignore stale acknowledgements for older revisions.
    if sent_rev and rev and (rev != sent_rev):
        return False

    changed = False
    if _sanitize_photoframe_feed_sync_status(rec.get("feed_sync_status")) != "sent":
        rec["feed_sync_status"] = "sent"
        changed = True
    if _sanitize_photoframe_feed_rev(rec.get("feed_sync_acked_rev")) != rev:
        rec["feed_sync_acked_rev"] = rev
        changed = True
    if sent_rev != rev:
        rec["feed_sync_sent_rev"] = rev
        changed = True
    if _sanitize_photoframe_text(rec.get("feed_sync_acked_at"), 40) != now_clean:
        rec["feed_sync_acked_at"] = now_clean
        changed = True
    return changed


def _photoframe_mark_feed_sync_pending(rec: Optional[Dict[str, Any]], seen_at: str) -> bool:
    """Mark content sync as pending right after scope/content is saved.

    This shows "sending" immediately in FjordLens and prevents stale heartbeat
    acknowledgements from older feed revisions from flipping the state to sent.
    """
    if not isinstance(rec, dict):
        return False

    now_clean = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    scope_mode, scope_folders, scope_photo_ids = _photoframe_record_scope(rec)
    marker_payload = {
        "at": now_clean,
        "scope_mode": scope_mode,
        "folders": scope_folders[:400],
        "photo_ids": scope_photo_ids[:1200],
        "token_hash": _normalize_photoframe_token_hash(rec.get("token_hash")),
    }
    marker_raw = json.dumps(marker_payload, ensure_ascii=False, separators=(",", ":"))
    marker_rev = _sanitize_photoframe_feed_rev(hashlib.sha256(marker_raw.encode("utf-8", errors="ignore")).hexdigest()[:16])
    if not marker_rev:
        marker_rev = _sanitize_photoframe_feed_rev(hashlib.sha256(now_clean.encode("utf-8", errors="ignore")).hexdigest()[:16])

    changed = False
    if _sanitize_photoframe_feed_sync_status(rec.get("feed_sync_status")) != "sending":
        rec["feed_sync_status"] = "sending"
        changed = True
    if _sanitize_photoframe_feed_rev(rec.get("feed_sync_sent_rev")) != marker_rev:
        rec["feed_sync_sent_rev"] = marker_rev
        changed = True
    if _sanitize_photoframe_text(rec.get("feed_sync_sent_at"), 40) != now_clean:
        rec["feed_sync_sent_at"] = now_clean
        changed = True
    if _sanitize_photoframe_feed_rev(rec.get("feed_sync_acked_rev")):
        rec["feed_sync_acked_rev"] = ""
        changed = True
    if _sanitize_photoframe_text(rec.get("feed_sync_acked_at"), 40):
        rec["feed_sync_acked_at"] = ""
        changed = True
    if _sanitize_photoframe_feed_sync_count(rec.get("feed_sync_count")) != 0:
        rec["feed_sync_count"] = 0
        changed = True
    return changed


def _photoframe_update_command_payload(
    rec: Optional[Dict[str, Any]],
    token: str = "",
    request_base: str = "",
) -> Optional[Dict[str, Any]]:
    if not isinstance(rec, dict):
        return None
    job_id = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
    if not job_id:
        return None
    status = _sanitize_photoframe_update_status(rec.get("update_status"))
    if status not in {"queued", "downloading", "installing", "restarting"}:
        return None
    package_url = _normalize_photoframe_http_url(rec.get("update_package_url"))
    package_mode = str(rec.get("update_package_mode") or "").strip().lower()
    if (not package_mode) and package_url:
        path_lower = str(urlparse(package_url).path or "").strip().lower()
        if "/update-upload/" in path_lower:
            package_mode = "upload"
        elif "/update-package/" in path_lower:
            package_mode = "source-dir"
        elif package_url:
            package_mode = "custom-url"
    if package_mode in {"restart-kiosk", "restart_kiosk", "restartkiosk"}:
        out = {
            "job_id": job_id,
            "action": "restart_kiosk",
        }
        version = _sanitize_photoframe_text(rec.get("update_version"), 80)
        if version:
            out["version"] = version
        return out
    if package_mode in {"reset-device", "reset_device", "resetdevice"}:
        out = {
            "job_id": job_id,
            "action": "reset_device",
        }
        version = _sanitize_photoframe_text(rec.get("update_version"), 80)
        if version:
            out["version"] = version
        return out
    if package_mode in {"apply-settings", "apply_settings", "applysettings"}:
        settings_payload = _decode_photoframe_settings_payload(rec.get("update_settings_payload"))
        if not settings_payload:
            return None
        out = {
            "job_id": job_id,
            "action": "apply_settings",
            "settings": settings_payload,
        }
        version = _sanitize_photoframe_text(rec.get("update_version"), 80)
        if version:
            out["version"] = version
        return out
    if package_mode in {"scan-wifi", "scan_wifi", "scanwifi"}:
        out = {
            "job_id": job_id,
            "action": "scan_wifi",
        }
        version = _sanitize_photoframe_text(rec.get("update_version"), 80)
        if version:
            out["version"] = version
        return out
    if package_mode in {"start-settings-web", "start_settings_web", "startsettingsweb"}:
        out = {
            "job_id": job_id,
            "action": "start_settings_web",
        }
        version = _sanitize_photoframe_text(rec.get("update_version"), 80)
        if version:
            out["version"] = version
        return out
    if package_mode in {"stop-settings-web", "stop_settings_web", "stopsettingsweb"}:
        out = {
            "job_id": job_id,
            "action": "stop_settings_web",
        }
        version = _sanitize_photoframe_text(rec.get("update_version"), 80)
        if version:
            out["version"] = version
        return out

    safe_token = _sanitize_photoframe_token_plain(token)
    safe_base = _normalize_photoframe_base_url(request_base)
    if safe_token and safe_base and package_mode in {"upload", "source-dir"}:
        endpoint = "api_frame_uploaded_update_package" if package_mode == "upload" else "api_frame_update_package"
        package_url = f"{safe_base}{url_for(endpoint, token=safe_token, job_id=job_id, _external=False)}"

    if not package_url:
        return None
    out = {
        "job_id": job_id,
        "package_url": package_url,
    }
    package_sha = _sanitize_photoframe_update_sha256(rec.get("update_package_sha256"))
    if package_sha:
        out["package_sha256"] = package_sha
    version = _sanitize_photoframe_text(rec.get("update_version"), 80)
    if version:
        out["version"] = version
    return out


def _photoframe_apply_update_report(
    rec: Optional[Dict[str, Any]],
    job_id_raw: Any,
    status_raw: Any,
    message_raw: Any,
    version_raw: Any,
    seen_at: str,
) -> bool:
    if not isinstance(rec, dict):
        return False
    expected_job_id = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
    job_id = _sanitize_photoframe_update_job_id(job_id_raw)
    if (not expected_job_id) or (not job_id) or (job_id != expected_job_id):
        return False
    status = _sanitize_photoframe_update_status(status_raw)
    if not status:
        return False

    rec["update_status"] = status
    rec["update_last_report_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    message = _sanitize_photoframe_text(message_raw, 240)
    if message:
        rec["update_message"] = message
    version = _sanitize_photoframe_text(version_raw, 80)
    if version:
        rec["update_version"] = version
        if status == "success":
            rec["device_version"] = version
    if status in {"downloading", "installing", "restarting", "success", "failed"} and not _sanitize_photoframe_text(rec.get("update_started_at"), 40):
        rec["update_started_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
    mode = _normalize_photoframe_update_package_mode(rec.get("update_package_mode"))
    if mode == "start-settings-web":
        if status == "success":
            _photoframe_mark_settings_session_active(rec, seen_at)
        elif status == "failed":
            _photoframe_mark_settings_session_closed(rec, seen_at)
    elif mode == "stop-settings-web":
        if status == "success":
            _photoframe_mark_settings_session_closed(rec, seen_at)
        elif status == "failed":
            # Keep session marked active if stop failed, so auto-timeout can retry.
            _photoframe_mark_settings_session_active(rec, seen_at)
    if status in {"success", "failed"}:
        rec["update_finished_at"] = _sanitize_photoframe_text(seen_at, 40) or now_iso()
        if status == "success":
            rec["update_package_sha256"] = ""
        if _normalize_photoframe_update_package_mode(rec.get("update_package_mode")) == "apply-settings":
            rec["update_settings_payload"] = {}
    return True


def _is_photoframe_package_root(path: Path) -> bool:
    try:
        if not path.exists() or not path.is_dir():
            return False
        return (path / "app").is_dir() and (path / "viewer").is_dir() and (path / "scripts").is_dir()
    except Exception:
        return False


def _resolve_photoframe_package_root() -> Optional[Path]:
    candidates: list[Path] = []
    env_raw = PHOTOFRAME_UPDATE_SOURCE_DIR_ENV
    if env_raw:
        try:
            candidates.append(Path(env_raw).expanduser().resolve())
        except Exception:
            pass

    here = Path(__file__).resolve().parent
    candidates.extend(
        [
            here / "photoframe",
            here.parent / "photoframe",
            Path("/opt/photoframe"),
        ]
    )
    for cand in candidates:
        if _is_photoframe_package_root(cand):
            return cand
    return None


def _photoframe_uploaded_package_path(job_id: str) -> Optional[Path]:
    safe_job_id = _sanitize_photoframe_update_job_id(job_id)
    if not safe_job_id:
        return None
    return PHOTOFRAME_UPDATE_UPLOAD_DIR / f"{safe_job_id}.zip"


def _photoframe_cleanup_uploaded_packages(max_keep: int = 60, max_age_sec: int = 45 * 86400) -> None:
    try:
        PHOTOFRAME_UPDATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        return
    try:
        files = [p for p in PHOTOFRAME_UPDATE_UPLOAD_DIR.glob("*.zip") if p.is_file()]
    except Exception:
        return
    if not files:
        return
    now_ts = time.time()
    try:
        files_sorted = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:
        files_sorted = files
    for idx, fp in enumerate(files_sorted):
        try:
            st = fp.stat()
            age = max(0.0, now_ts - float(st.st_mtime))
            if idx >= max_keep or age > float(max_age_sec):
                fp.unlink(missing_ok=True)
        except Exception:
            continue


def _save_uploaded_photoframe_package(file_obj: Any, job_id: str) -> Tuple[Optional[Path], str, int, str]:
    dst_path = _photoframe_uploaded_package_path(job_id)
    if dst_path is None:
        return None, "", 0, "Ugyldigt update-id"

    try:
        PHOTOFRAME_UPDATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None, "", 0, "Kunne ikke oprette upload-mappe"

    src_stream = getattr(file_obj, "stream", None) or file_obj
    if src_stream is None:
        return None, "", 0, "Upload mangler data"

    tmp_path = PHOTOFRAME_UPDATE_UPLOAD_DIR / f".{dst_path.stem}.{secrets.token_hex(4)}.tmp"
    hasher = hashlib.sha256()
    total = 0
    try:
        with open(tmp_path, "wb") as out:
            while True:
                chunk = src_stream.read(1024 * 1024)
                if not chunk:
                    break
                if not isinstance(chunk, (bytes, bytearray)):
                    chunk = bytes(chunk)
                total += len(chunk)
                if total > PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES:
                    raise RuntimeError(f"Zip er for stor (max {PHOTOFRAME_UPDATE_UPLOAD_MAX_BYTES // (1024 * 1024)} MB)")
                hasher.update(chunk)
                out.write(chunk)
        if total <= 0:
            raise RuntimeError("Zip-filen er tom")
        if not zipfile.is_zipfile(tmp_path):
            raise RuntimeError("Filen er ikke en gyldig zip")
        with zipfile.ZipFile(tmp_path, "r") as zf:
            if not zf.namelist():
                raise RuntimeError("Zip-filen er tom")
        os.replace(tmp_path, dst_path)
        _photoframe_cleanup_uploaded_packages()
        return dst_path, hasher.hexdigest().lower(), total, ""
    except Exception as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return None, "", 0, str(exc)


def _infer_photoframe_version_from_filename(filename: Any) -> str:
    name = secure_filename(str(filename or "").strip())
    if not name:
        return ""
    stem = str(Path(name).stem or "").strip()
    if not stem:
        return ""
    stem = re.sub(r"(?i)^photoframe[-_. ]*", "", stem).strip(" ._-")
    return _sanitize_photoframe_text(stem, 80)


def _autogen_photoframe_upload_version() -> str:
    # Use local server time so the label directly reflects upload timestamp in FjordLens.
    now_local = datetime.now().astimezone()
    return _sanitize_photoframe_text(now_local.strftime("v%d-%m-%Y_%H:%M:%S"), 80)


def _probe_photoframe_status(entry: Dict[str, Any], checked_at: str) -> Dict[str, Any]:
    info_url = str(entry.get("info_url") or "").strip()
    start = time.perf_counter()
    online = False
    error = ""
    http_status: Optional[int] = None
    info_json: Dict[str, Any] = {}

    try:
        res = requests.get(info_url, timeout=PHOTOFRAME_STATUS_TIMEOUT_SEC)
        http_status = int(res.status_code)
        online = bool(res.ok)
        if online:
            try:
                payload = res.json()
                if isinstance(payload, dict):
                    info_json = payload
            except Exception:
                info_json = {}
        elif http_status is not None:
            error = f"HTTP {http_status}"
    except Exception as e:
        error = str(e)

    latency_ms = int(max(0.0, (time.perf_counter() - start) * 1000))
    setup_complete: Optional[bool] = None
    if "setup_complete" in info_json:
        try:
            setup_complete = bool(info_json.get("setup_complete"))
        except Exception:
            setup_complete = None

    return {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "base_url": entry.get("base_url"),
        "info_url": info_url,
        "location": entry.get("location") or "",
        "note": entry.get("note") or "",
        "online": bool(online),
        "http_status": http_status,
        "latency_ms": latency_ms,
        "error": error,
        "ip": str(info_json.get("ip") or "").strip(),
        "feed_url": str(info_json.get("feed_url") or "").strip(),
        "setup_complete": setup_complete,
        "checked_at": checked_at,
    }


def _build_share_link(token: str, use_duckdns: bool) -> Tuple[Optional[str], Optional[str]]:
    share_path = url_for("shared_folder_view", token=token, _external=False)
    if use_duckdns:
        configured = _get_setting("share_duckdns_base_url", SHARE_DUCKDNS_BASE_URL) or SHARE_DUCKDNS_BASE_URL
        base = _normalize_share_base_url(configured)
        if not base:
            return None, "DuckDNS-base URL mangler. SÃ¦t SHARE_DUCKDNS_BASE_URL i miljÃ¸variabler."
        return f"{base}{share_path}", None
    return url_for("shared_folder_view", token=token, _external=True), None


def _share_link_for_admin_row(row: sqlite3.Row) -> Optional[str]:
    token_plain = str(row["token_plain"] or "").strip()
    if not token_plain:
        return None
    use_duckdns = bool(int(row["link_use_duckdns"] or 0))
    link, err = _build_share_link(token_plain, use_duckdns)
    if link and not err:
        return link
    fallback, _ = _build_share_link(token_plain, False)
    return fallback


def _get_share_scoped_photo_row(conn: sqlite3.Connection, share_row: sqlite3.Row, photo_id: int) -> Optional[sqlite3.Row]:
    folder_paths = _share_folder_paths(conn, share_row)
    prefixes = _share_rel_prefixes(folder_paths)
    if not prefixes:
        return None
    where_sql, where_params = _share_scope_sql(prefixes)
    sql = f"SELECT * FROM photos WHERE id=? AND ({where_sql}) LIMIT 1"
    return conn.execute(sql, (int(photo_id), *where_params)).fetchone()


def _upload_target_for_destination(destination: str) -> Tuple[Path, str]:
    if destination == UPLOAD_DEST_LIBRARY:
        return PHOTO_DIR, ""
    # Place uploads under 'uploads/originals' so HEIC originals are kept separate from converted copies
    return (UPLOAD_DIR / "originals"), "uploads/originals/"


def _read_secret(name: str) -> Optional[str]:
    v = os.environ.get(name)
    if v:
        return v
    f = os.environ.get(f"{name}_FILE")
    if f and os.path.exists(f):
        try:
            return Path(f).read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return None


@app.route("/setup", methods=["GET", "POST"])
def setup():
    ensure_runtime_bootstrap()
    # If a user already exists, send to login
    if users_count() > 0:
        _ensure_install_state_for_existing_users()
        return redirect(url_for("login"))
    if _fjordhub_managed():
        return redirect(url_for("login"))
    if _install_state_exists():
        return _setup_locked_response()
    require_token = bool(_read_secret("SETUP_TOKEN"))
    if request.method == "POST":
        token = (request.form.get("token") or "").strip()
        if require_token and token != _read_secret("SETUP_TOKEN"):
            return render_template("setup.html", error=_ui_text("setup_invalid_token"), require_token=True)
        u = (request.form.get("username") or "").strip()
        p = request.form.get("password") or ""
        p2 = request.form.get("password2") or ""
        if not u or not p:
            return render_template("setup.html", error=_ui_text("setup_fill_fields"), require_token=require_token)
        if p != p2:
            return render_template("setup.html", error=_ui_text("setup_password_mismatch"), require_token=require_token)
        try:
            with closing(get_conn()) as conn:
                conn.execute(
                    "INSERT INTO users(username, password_hash, is_admin, role, created_at) VALUES (?,?,?,?,?)",
                    (u, generate_password_hash(p), 1, "admin", now_iso()),
                )
                conn.commit()
            _mark_install_initialized("first-admin-created")
            # Redirect directly to login after successful creation
            return redirect(url_for("login", created=1))
        except Exception as e:
            return render_template("setup.html", error=str(e), require_token=require_token)
    return render_template("setup.html", require_token=require_token)


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _hash_resample_filter() -> Any:
    resampling = getattr(Image, "Resampling", Image)
    return getattr(resampling, "LANCZOS", Image.BICUBIC)


def average_hash(img: Image.Image, hash_size: int = 8) -> str:
    gray = img.convert("L").resize((hash_size, hash_size), _hash_resample_filter())
    pixels = list(gray.getdata())
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p > avg else "0" for p in pixels)
    # binary -> hex string
    return f"{int(bits, 2):0{hash_size*hash_size//4}x}"


def difference_hash(img: Image.Image, hash_size: int = 8) -> str:
    gray = img.convert("L").resize((hash_size + 1, hash_size), _hash_resample_filter())
    pixels = list(gray.getdata())
    bits = []
    row_width = hash_size + 1
    for y in range(hash_size):
        offset = y * row_width
        for x in range(hash_size):
            bits.append("1" if pixels[offset + x] > pixels[offset + x + 1] else "0")
    return f"{int(''.join(bits), 2):0{hash_size*hash_size//4}x}"


def perceptual_hash(img: Image.Image, hash_size: int = 8, highfreq_factor: int = 4) -> str:
    size = hash_size * highfreq_factor
    gray = img.convert("L").resize((size, size), _hash_resample_filter())
    pixels = [float(p) for p in gray.getdata()]
    cos_cache = [
        [math.cos(((2 * x + 1) * u * math.pi) / (2 * size)) for x in range(size)]
        for u in range(hash_size)
    ]
    coeffs = []
    for v in range(hash_size):
        for u in range(hash_size):
            total = 0.0
            cos_u = cos_cache[u]
            cos_v = cos_cache[v]
            for y in range(size):
                row = y * size
                cv = cos_v[y]
                for x in range(size):
                    total += pixels[row + x] * cos_u[x] * cv
            coeffs.append(total)
    values = coeffs[1:] or coeffs
    sorted_values = sorted(values)
    median = sorted_values[len(sorted_values) // 2] if sorted_values else 0.0
    bits = "".join("1" if c > median else "0" for c in coeffs)
    return f"{int(bits, 2):0{hash_size*hash_size//4}x}"


def image_hashes(img: Image.Image) -> Dict[str, str]:
    ahash = average_hash(img)
    return {
        "ahash": ahash,
        "dhash": difference_hash(img),
        "phash_dct": perceptual_hash(img),
        # Keep the legacy phash column compatible with older duplicate code.
        "phash": ahash,
    }


def _rational_to_float(v: Any) -> Optional[float]:
    try:
        # EXIF kan returnere tuple (numerator, denominator)
        if isinstance(v, tuple) and len(v) == 2 and v[1] != 0:
            return float(v[0]) / float(v[1])
        # Nogle EXIF-objekter har numerator/denominator attributter
        if hasattr(v, "numerator") and hasattr(v, "denominator"):
            denom = getattr(v, "denominator", None)
            if denom:
                return float(getattr(v, "numerator", 0)) / float(denom)
        # Hvis det bare er et tal
        if isinstance(v, (int, float)):
            return float(v)
        # Hvis det er en string, prÃ¸v at konvertere
        if isinstance(v, str):
            return float(v)
    except Exception:
        return None
    return None


def _gps_to_deg(value: Any) -> Optional[float]:
    try:
        if not value or len(value) != 3:
            return None
        d = _rational_to_float(value[0])
        m = _rational_to_float(value[1])
        s = _rational_to_float(value[2])
        if d is None or m is None or s is None:
            return None
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return None


def parse_exif(img: Image.Image) -> Dict[str, Any]:
    exif_map: Dict[str, Any] = {}
    try:
        exif = img.getexif()
    except Exception:
        exif = None
    if not exif:
        # last resort: try GPS IFD if available in Pillow
        try:
            if hasattr(img, "getexif") and hasattr(ExifTags, "IFD"):
                gps_ifd = img.getexif().get_ifd(getattr(ExifTags, "IFD").GPS)  # type: ignore[attr-defined]
                if gps_ifd:
                    exif_map["GPSInfo"] = {ExifTags.GPSTAGS.get(k, str(k)): v for k, v in gps_ifd.items()}
                    # derive lat/lon
                    lat = _gps_to_deg(exif_map["GPSInfo"].get("GPSLatitude"))
                    lon = _gps_to_deg(exif_map["GPSInfo"].get("GPSLongitude"))
                    if lat is not None and exif_map["GPSInfo"].get("GPSLatitudeRef") in ("S", b"S"):
                        lat = -lat
                    if lon is not None and exif_map["GPSInfo"].get("GPSLongitudeRef") in ("W", b"W"):
                        lon = -lon
                    if lat is not None:
                        exif_map["_gps_lat"] = lat
                    if lon is not None:
                        exif_map["_gps_lon"] = lon
        except Exception:
            pass
        return exif_map

    for tag_id, value in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        try:
            if tag_name == "GPSInfo" and isinstance(value, dict):
                gps = {}
                for k, v in value.items():
                    gps_name = ExifTags.GPSTAGS.get(k, str(k))
                    gps[gps_name] = v
                exif_map["GPSInfo"] = gps
            elif isinstance(value, bytes):
                exif_map[tag_name] = f"<bytes:{len(value)}>"
            else:
                exif_map[tag_name] = value
        except Exception:
            exif_map[tag_name] = str(value)

    # If GPSInfo not present, try direct GPS IFD
    if "GPSInfo" not in exif_map:
        try:
            if hasattr(ExifTags, "IFD"):
                gps_ifd = exif.get_ifd(getattr(ExifTags, "IFD").GPS)  # type: ignore[attr-defined]
                if gps_ifd:
                    exif_map["GPSInfo"] = {ExifTags.GPSTAGS.get(k, str(k)): v for k, v in gps_ifd.items()}
        except Exception:
            pass

    # Pillow sometimes stores GPSInfo values without expanding GPSTAGS
    if "GPSInfo" in exif_map and isinstance(exif_map["GPSInfo"], dict):
        gps = exif_map["GPSInfo"]
        lat = _gps_to_deg(gps.get("GPSLatitude"))
        lon = _gps_to_deg(gps.get("GPSLongitude"))
        if lat is not None and gps.get("GPSLatitudeRef") in ("S", b"S"):
            lat = -lat
        if lon is not None and gps.get("GPSLongitudeRef") in ("W", b"W"):
            lon = -lon
        if lat is not None:
            exif_map["_gps_lat"] = lat
        if lon is not None:
            exif_map["_gps_lon"] = lon

    return exif_map


def _merge_if_missing(meta: Dict[str, Any], key: str, val: Any):
    if val is None:
        return
    if meta.get(key) is None or meta.get(key) == "":
        meta[key] = val


def _piexif_get_first(exif_dict: dict, ifd: str, tag: int) -> Optional[Any]:
    try:
        return exif_dict.get(ifd, {}).get(tag)
    except Exception:
        return None


def extract_exif_via_heif(path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        # If pillow_heif is unavailable, skip gracefully
        try:
            hf = HeifFile(path)  # type: ignore[name-defined]
        except NameError:
            return out
        exif_bytes = hf.info.get("exif") if isinstance(hf.info, dict) else None
        if not exif_bytes:
            return out
        exif_dict = piexif.load(exif_bytes)
        # DateTimeOriginal
        dto = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.DateTimeOriginal)
        if dto:
            try:
                out["captured_at"] = parse_captured_at({"DateTimeOriginal": dto.decode() if isinstance(dto, bytes) else str(dto)}, path.stat().st_mtime)
            except Exception:
                pass
        # Camera/Lens
        mke = _piexif_get_first(exif_dict, "0th", piexif.ImageIFD.Make)
        mdl = _piexif_get_first(exif_dict, "0th", piexif.ImageIFD.Model)
        lmd = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.LensModel)
        out["camera_make"] = mke.decode() if isinstance(mke, bytes) else mke
        out["camera_model"] = mdl.decode() if isinstance(mdl, bytes) else mdl
        out["lens_model"] = lmd.decode() if isinstance(lmd, bytes) else lmd
        # Exposure
        out["iso"] = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.ISOSpeedRatings) or _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.PhotographicSensitivity)
        out["f_number"] = _rational_to_float(_piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.FNumber))
        out["focal_length"] = _rational_to_float(_piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.FocalLength))
        et = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.ExposureTime)
        out["exposure_time"] = str(et) if et is not None else None
        # GPS
        gps = exif_dict.get("GPS", {})
        glat = gps.get(piexif.GPSIFD.GPSLatitude)
        glat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
        glon = gps.get(piexif.GPSIFD.GPSLongitude)
        glon_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)
        def conv_triplet(t):
            if not t:
                return None
            try:
                d = _rational_to_float(t[0])
                m = _rational_to_float(t[1])
                s = _rational_to_float(t[2])
                if d is None or m is None or s is None:
                    return None
                return d + (m / 60.0) + (s / 3600.0)
            except Exception:
                return None
        lat = conv_triplet(glat)
        lon = conv_triplet(glon)
        if lat is not None and (glat_ref in (b"S", "S")):
            lat = -lat
        if lon is not None and (glon_ref in (b"W", "W")):
            lon = -lon
        out["gps_lat"] = lat
        out["gps_lon"] = lon
    except Exception as e:
        log_event("error", rel_path=str(path), error=f"heif_exif: {e}")
    return out


def extract_exif_via_exifread(path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        with path.open("rb") as f:
            tags = exifread.process_file(f, details=False)
        # DateTimeOriginal
        for key in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
            if key in tags:
                dto = str(tags[key])
                out["captured_at"] = parse_captured_at({"DateTimeOriginal": dto.replace("/", ":")}, path.stat().st_mtime)
                break
        # Camera / Lens
        out["camera_make"] = str(tags.get("Image Make", "")) or None
        out["camera_model"] = str(tags.get("Image Model", "")) or None
        out["lens_model"] = str(tags.get("EXIF LensModel", "")) or None
        # GPS
        lat = tags.get("GPS GPSLatitude")
        lat_ref = str(tags.get("GPS GPSLatitudeRef", ""))
        lon = tags.get("GPS GPSLongitude")
        lon_ref = str(tags.get("GPS GPSLongitudeRef", ""))
        def to_float_gps(tag):
            try:
                vals = [float(v.num) / float(v.den) for v in tag.values]
                return vals[0] + vals[1] / 60.0 + vals[2] / 3600.0
            except Exception:
                return None
        if lat and lon:
            la = to_float_gps(lat)
            lo = to_float_gps(lon)
            if la is not None:
                if lat_ref.strip().upper().startswith("S"):
                    la = -la
                out["gps_lat"] = la
            if lo is not None:
                if lon_ref.strip().upper().startswith("W"):
                    lo = -lo
                out["gps_lon"] = lo
    except Exception as e:
        log_event("error", rel_path=str(path), error=f"exifread: {e}")
    return out


def extract_exif_via_piexif_file(path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        exif_dict = piexif.load(str(path))
        dto = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.DateTimeOriginal)
        if dto:
            out["captured_at"] = parse_captured_at({"DateTimeOriginal": dto.decode() if isinstance(dto, bytes) else str(dto)}, path.stat().st_mtime)
        mke = _piexif_get_first(exif_dict, "0th", piexif.ImageIFD.Make)
        mdl = _piexif_get_first(exif_dict, "0th", piexif.ImageIFD.Model)
        lmd = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.LensModel)
        out["camera_make"] = mke.decode() if isinstance(mke, bytes) else mke
        out["camera_model"] = mdl.decode() if isinstance(mdl, bytes) else mdl
        out["lens_model"] = lmd.decode() if isinstance(lmd, bytes) else lmd
        out["iso"] = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.ISOSpeedRatings) or _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.PhotographicSensitivity)
        out["f_number"] = _rational_to_float(_piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.FNumber))
        out["focal_length"] = _rational_to_float(_piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.FocalLength))
        et = _piexif_get_first(exif_dict, "Exif", piexif.ExifIFD.ExposureTime)
        out["exposure_time"] = str(et) if et is not None else None
        gps = exif_dict.get("GPS", {})
        glat = gps.get(piexif.GPSIFD.GPSLatitude)
        glat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
        glon = gps.get(piexif.GPSIFD.GPSLongitude)
        glon_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)
        def conv_triplet(t):
            if not t:
                return None
            try:
                d = _rational_to_float(t[0])
                m = _rational_to_float(t[1])
                s = _rational_to_float(t[2])
                if d is None or m is None or s is None:
                    return None
                return d + (m / 60.0) + (s / 3600.0)
            except Exception:
                return None
        lat = conv_triplet(glat)
        lon = conv_triplet(glon)
        if lat is not None and (glat_ref in (b"S", "S")):
            lat = -lat
        if lon is not None and (glon_ref in (b"W", "W")):
            lon = -lon
        out["gps_lat"] = lat
        out["gps_lon"] = lon
    except Exception as e:
        log_event("error", rel_path=str(path), error=f"piexif_file: {e}")
    return out


def parse_captured_at(exif_map: Dict[str, Any], file_mtime: float) -> str:
    for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
        raw = exif_map.get(key)
        if not raw:
            continue
        # EXIF often uses "YYYY:MM:DD HH:MM:SS"
        if isinstance(raw, bytes):
            raw = raw.decode(errors="ignore")
        raw = str(raw)
        for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.isoformat(timespec="seconds")
            except ValueError:
                pass
    return datetime.fromtimestamp(file_mtime).isoformat(timespec="seconds")


def build_ai_tags(filename: str, exif_map: Dict[str, Any], gps_lat: Optional[float], gps_lon: Optional[float]) -> list[str]:
    # Placeholder tags until real ONNX/CLIP/vision pipeline is added
    tags: set[str] = set()
    name = filename.lower()

    # Danish-friendly keyword hints
    keyword_groups = {
        "strand": {"strand", "beach", "kyst", "hav", "sea"},
        "solnedgang": {"solnedgang", "sunset", "aftenhimmel"},
        "skov": {"skov", "forest", "woods"},
        "bil": {"bil", "car", "tesla"},
        "familie": {"familie", "family", "middag", "jul"},
        "barn": {"barn", "kid", "baby", "child"},
    }
    for tag, words in keyword_groups.items():
        if any(w in name for w in words):
            tags.add(tag)

    if gps_lat is not None and gps_lon is not None:
        tags.update({"sted", "gps"})
    if exif_map.get("Model"):
        tags.add("kamera")
    if exif_map.get("LensModel"):
        tags.add("linse")

    return sorted(tags)


def make_thumb(img: Image.Image, rel_path: str, file_mtime: float, file_size: int, *, force: bool = False) -> str:
    key = hashlib.md5(f"{rel_path}|{file_mtime}|{file_size}".encode("utf-8")).hexdigest()
    thumb_name = f"{key}.jpg"
    thumb_path = THUMB_DIR / thumb_name
    try:
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    if thumb_path.exists() and not force:
        return thumb_name

    # For animated GIFs we use the first frame for a deterministic thumbnail.
    try:
        if getattr(img, "is_animated", False):
            img.seek(0)
    except Exception:
        pass

    thumb = img.convert("RGB").copy()
    try:
        thumb = ImageOps.exif_transpose(thumb)
    except Exception:
        pass
    thumb.thumbnail(THUMB_SIZE)
    thumb.save(thumb_path, format="JPEG", quality=85, optimize=True)
    return thumb_name


def _make_video_thumb(path: Path, rel_path: str, file_mtime: float, file_size: int) -> Optional[str]:
    """Extract a representative frame via ffmpeg and save as JPEG thumbnail.
    Returns the thumbnail file name or None on failure.
    """
    try:
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "frame.jpg"
            # Grab a frame at 0.5s; fall back to first frame if video is shorter
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", "0.5", "-i", str(path),
                "-frames:v", "1",
                str(out_path),
            ]
            subprocess.run(cmd, check=True)
            with Image.open(out_path) as img:
                return make_thumb(img, rel_path, file_mtime, file_size)
    except Exception as e:
        try:
            log_event("error", rel_path=rel_path, error=f"video_thumb: {e}")
        except Exception:
            pass
        return None


def ensure_viewable_copy(path: Path, rel_path: str) -> Path:
    """Return a path that browsers and AI can read.
    For assets under uploads/, place any ad-hoc conversions under uploads/converted/<subpath>.jpg
    instead of DATA/converted. For library files, keep using DATA/converted.
    If rawpy is unavailable for RAW formats, return original path.
    """
    ext = path.suffix.lower()
    if ext not in ({".heic", ".heif"} | RAW_EXTS):
        return path
    try:
        # Decide destination root
        under_uploads = str(rel_path).lstrip("/").startswith("uploads/")
        if under_uploads:
            # uploads/<subdir>/<file> -> uploads/converted/<subdir>/<stem>.jpg
            try:
                rel_norm = str(rel_path).replace("\\", "/").lstrip("/")
                if rel_norm.startswith("uploads/originals/"):
                    sub = rel_norm[len("uploads/originals/"):]
                elif rel_norm.startswith("uploads/"):
                    sub = rel_norm[len("uploads/"):]
                else:
                    sub = Path(rel_norm).name
            except Exception:
                sub = Path(rel_path).name
            subdir_only = str(Path(sub).parent).replace("\\", "/").strip("./")
            leaf_jpg = f"{Path(sub).stem}.jpg"
            dest = UPLOAD_DIR / "converted" / (subdir_only if subdir_only not in {"", "."} else "") / leaf_jpg
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Library: keep using DATA/converted
            suffix_tag = ext[1:].upper()
            dest_rel = Path(rel_path).with_suffix("")
            dest_rel = Path(f"{dest_rel}_{suffix_tag}.jpg")
            dest = CONVERT_DIR / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)

        # Rebuild if missing or source newer
        if (not dest.exists()) or (path.stat().st_mtime > dest.stat().st_mtime):
            if ext in {".heic", ".heif"}:
                with Image.open(path) as im:
                    try:
                        im = ImageOps.exif_transpose(im)
                    except Exception:
                        pass
                    rgb = im.convert("RGB")
                    rgb.save(dest, format="JPEG", quality=92, optimize=True)
            elif ext in RAW_EXTS:
                # Try rawpy first; fallback to ffmpeg
                _raw_to_jpeg(path, dest)
        return dest
    except Exception:
        return path


def extract_metadata(path: Path, rel_path: str, *, generate_thumb: bool = True) -> Dict[str, Any]:
    stat = path.stat()
    metadata: Dict[str, Any] = {
        "rel_path": rel_path,
        "filename": path.name,
        "ext": path.suffix.lower(),
        "file_size": stat.st_size,
        "created_fs": datetime.fromtimestamp(stat.st_ctime).isoformat(timespec="seconds"),
        "modified_fs": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }

    # Prepare common fields used by the DB layer; always provide placeholders
    exif_map: Dict[str, Any] = {}
    thumb_name = None
    phash = None
    phash_dct = None
    dhash = None
    ahash = None
    # Ensure all DB-bound fields exist (videos may not populate them)
    for k in (
        "width", "height", "camera_make", "camera_model", "lens_model",
        "iso", "focal_length", "f_number", "exposure_time",
        "gps_lat", "gps_lon", "gps_name",
    ):
        metadata[k] = None
    # Determine if file is a video (no EXIF parsing via Pillow)
    is_video = metadata["ext"] in VIDEO_EXTS
    if is_video:
        # Minimal fields for videos
        metadata.setdefault("captured_at", datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"))
        # Attempt to make a thumbnail from first frame
        if generate_thumb:
            tn = _make_video_thumb(path, rel_path, stat.st_mtime, stat.st_size)
            if tn:
                thumb_name = tn
    
    if not is_video:
        # Images: read via Pillow to populate EXIF-derived fields
        try:
            if path.suffix.lower() in RAW_EXTS:
                # Try to decode RAW for dimensions/thumb; fall back gracefully
                img: Image.Image | None = None
                if rawpy is not None:
                    try:
                        with rawpy.imread(str(path)) as raw:  # type: ignore
                            rgb = raw.postprocess(
                                use_auto_wb=True,
                                no_auto_bright=True,
                                output_color=rawpy.ColorSpace.sRGB,  # type: ignore
                                output_bps=8,
                                gamma=None,
                                half_size=True,
                            )
                        img = Image.fromarray(rgb)
                    except Exception:
                        img = None
                if img is not None:
                    try:
                        img = ImageOps.exif_transpose(img)
                    except Exception:
                        pass
                    metadata["width"], metadata["height"] = img.size
                    metadata.setdefault("captured_at", datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"))
                    if generate_thumb:
                        thumb_name = make_thumb(img, rel_path, stat.st_mtime, stat.st_size)
                    try:
                        hashes = image_hashes(img)
                        phash = hashes.get("phash")
                        phash_dct = hashes.get("phash_dct")
                        dhash = hashes.get("dhash")
                        ahash = hashes.get("ahash")
                    except Exception:
                        phash = None
                else:
                    # Could not decode; still set captured_at; ensure a viewable will be produced lazily
                    metadata.setdefault("captured_at", datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"))
            else:
                with Image.open(path) as img:
                    try:
                        img = ImageOps.exif_transpose(img)
                    except Exception:
                        pass
                    metadata["width"], metadata["height"] = img.size
                    exif_map = parse_exif(img)
                    metadata["captured_at"] = parse_captured_at(exif_map, stat.st_mtime)
                    metadata["camera_make"] = exif_map.get("Make")
                    metadata["camera_model"] = exif_map.get("Model")
                    metadata["lens_model"] = exif_map.get("LensModel")
                    metadata["iso"] = exif_map.get("ISOSpeedRatings") or exif_map.get("PhotographicSensitivity")
                    metadata["focal_length"] = _rational_to_float(exif_map.get("FocalLength"))
                    metadata["f_number"] = _rational_to_float(exif_map.get("FNumber"))
                    metadata["exposure_time"] = str(exif_map.get("ExposureTime")) if exif_map.get("ExposureTime") is not None else None
                    metadata["gps_lat"] = exif_map.get("_gps_lat")
                    metadata["gps_lon"] = exif_map.get("_gps_lon")
                    metadata["gps_name"] = None  # placeholder for future reverse geocoding
                    thumb_name = make_thumb(img, rel_path, stat.st_mtime, stat.st_size) if generate_thumb else None
                    try:
                        hashes = image_hashes(img)
                        phash = hashes.get("phash")
                        phash_dct = hashes.get("phash_dct")
                        dhash = hashes.get("dhash")
                        ahash = hashes.get("ahash")
                    except Exception:
                        phash = None
        except Exception as e:
            # Unsupported or damaged image: still index file-level info
            metadata.setdefault("captured_at", datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"))
            metadata["thumb_error"] = str(e)

    # Fallbacks to enrich missing EXIF (camera, lens, GPS, date)
    try:
        ext = path.suffix.lower()
        if ext in {".heic", ".heif"}:
            extra = extract_exif_via_heif(path)
        elif ext in {".jpg", ".jpeg", ".tif", ".tiff"}:
            # prefer piexif on file (robust GPS), then exifread as backup
            extra = extract_exif_via_piexif_file(path)
            if not extra.get("gps_lat") and not extra.get("gps_lon"):
                more = extract_exif_via_exifread(path)
                extra.update({k: v for k, v in more.items() if v is not None})
        else:
            extra = extract_exif_via_exifread(path)
        for k in ("captured_at", "camera_make", "camera_model", "lens_model", "iso", "f_number", "focal_length", "exposure_time", "gps_lat", "gps_lon"):
            if metadata.get(k) in (None, "") and extra.get(k) is not None:
                metadata[k] = extra[k]
                if k in ("gps_lat", "gps_lon"):
                    log_event("exif_fallback", rel_path=rel_path, field=k, value=str(extra[k]))
    except Exception as e:
        log_event("error", rel_path=rel_path, error=f"exif_fallback: {e}")

    # Reverse geocoding (country, city) if GPS present
    try:
        lat_raw = metadata.get("gps_lat")
        lon_raw = metadata.get("gps_lon")
        if GEOCODE_ENABLE and (lat_raw is not None) and (lon_raw is not None):
            lat = float(lat_raw)
            lon = float(lon_raw)
            country, city = reverse_geocode_with_cache(lat, lon)
            # Save into metadata_json and gps_name for quick display
            if country or city:
                mj = metadata.get("metadata_json") or {}
                geo = mj.get("geo", {})
                if country and not geo.get("country"):
                    geo["country"] = country
                if city and not geo.get("city"):
                    geo["city"] = city
                mj["geo"] = geo
                metadata["metadata_json"] = mj
                if not metadata.get("gps_name"):
                    metadata["gps_name"] = ", ".join([x for x in [city, country] if x])
    except Exception as e:
        log_event("error", rel_path=rel_path, error=f"geocode_outer: {e}")

    # If critical EXIF is missing (common when HEIC was re-encoded as JPG without metadata),
    # try to enrich from a sibling HEIC/HEIF with same basename â€” but ONLY if the images
    # are visually the same (verified via perceptual hash distance threshold).
    try:
        if (not metadata.get("gps_lat") and not metadata.get("gps_lon")) or (not metadata.get("lens_model")):
            # Consider any sibling with the same basename but different extension (supported types)
            cur_phash = phash
            if cur_phash is None:
                try:
                    with Image.open(path) as _img_tmp:
                        try:
                            _img_tmp = ImageOps.exif_transpose(_img_tmp)
                        except Exception:
                            pass
                        cur_phash = average_hash(_img_tmp)
                except Exception:
                    cur_phash = None

            if cur_phash is not None:
                exts_to_try = set()
                for ext in SUPPORTED_EXTS:
                    if ext.lower() != metadata.get("ext", path.suffix.lower()):
                        exts_to_try.add(ext.lower())
                        exts_to_try.add(ext.upper())
                for ext in exts_to_try:
                    cand = path.with_suffix(ext)
                    if not cand.exists():
                        continue
                    try:
                        with Image.open(cand) as himg:
                            try:
                                himg = ImageOps.exif_transpose(himg)
                            except Exception:
                                pass
                            h_exif = parse_exif(himg)
                            try:
                                cand_phash = average_hash(himg)
                            except Exception:
                                cand_phash = None
                            if not cand_phash:
                                continue
                            dist = _hamdist_hex(cur_phash, cand_phash)
                            if dist <= PHASH_MATCH_THRESHOLD:  # visual match threshold
                                log_event("enrich", rel_path=rel_path, from_path=str(cand), distance=dist)
                                if not metadata.get("captured_at"):
                                    metadata["captured_at"] = parse_captured_at(h_exif, stat.st_mtime)
                                if not metadata.get("camera_make"):
                                    metadata["camera_make"] = h_exif.get("Make")
                                if not metadata.get("camera_model"):
                                    metadata["camera_model"] = h_exif.get("Model")
                                if not metadata.get("lens_model"):
                                    metadata["lens_model"] = h_exif.get("LensModel")
                                if not metadata.get("iso"):
                                    metadata["iso"] = h_exif.get("ISOSpeedRatings") or h_exif.get("PhotographicSensitivity")
                                if not metadata.get("focal_length"):
                                    metadata["focal_length"] = _rational_to_float(h_exif.get("FocalLength"))
                                if not metadata.get("f_number"):
                                    metadata["f_number"] = _rational_to_float(h_exif.get("FNumber"))
                                if metadata.get("gps_lat") is None and h_exif.get("_gps_lat") is not None:
                                    metadata["gps_lat"] = h_exif.get("_gps_lat")
                                if metadata.get("gps_lon") is None and h_exif.get("_gps_lon") is not None:
                                    metadata["gps_lon"] = h_exif.get("_gps_lon")
                                break  # stop at first valid visual match
                    except Exception:
                        continue
    except Exception:
        pass

    metadata["checksum_sha256"] = sha256_file(path)
    metadata["phash"] = phash
    metadata["phash_dct"] = phash_dct
    metadata["dhash"] = dhash
    metadata["ahash"] = ahash
    metadata["thumb_name"] = thumb_name
    metadata["ai_tags"] = build_ai_tags(metadata["filename"], exif_map, metadata.get("gps_lat"), metadata.get("gps_lon"))
    metadata["exif_json"] = exif_map
    # Preserve any previously-added fields in metadata_json (e.g. geo from reverse geocoding)
    prev_mj = metadata.get("metadata_json") or {}
    mj: Dict[str, Any] = {**prev_mj}
    mj["file"] = {
        "rel_path": rel_path,
        "filename": path.name,
        "ext": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "created_fs": metadata["created_fs"],
        "modified_fs": metadata["modified_fs"],
    }
    mj["image"] = {"width": metadata.get("width"), "height": metadata.get("height")}
    mj["hashes"] = {
        "phash": phash_dct,
        "dhash": dhash,
        "ahash": ahash,
        "legacy_phash": phash,
    }
    mj["exif"] = exif_map
    # Add AI description tags and caption if present
    ai_desc_tags = metadata.get("ai_desc_tags")
    ai_desc_caption = metadata.get("ai_desc_caption")
    mj["ai"] = {
        "tags": metadata["ai_tags"],
        "desc_tags": ai_desc_tags if ai_desc_tags is not None else [],
        "desc_caption": ai_desc_caption if ai_desc_caption is not None else None,
        "embedding": None,
        "faces": []
    }
    metadata["metadata_json"] = mj
    _enrich_metadata_weather(metadata)
    return metadata


def reverse_geocode_with_cache(lat: float, lon: float) -> tuple[Optional[str], Optional[str]]:
    """Return (country, city) using cache and provider fallbacks."""
    lat_r = int(round(lat * 10000))
    lon_r = int(round(lon * 10000))
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT country, city FROM geo_cache WHERE lat_rounded=? AND lon_rounded=?",
            (lat_r, lon_r),
        ).fetchone()
    if row and (row["country"] or row["city"]):
        return row["country"], row["city"]

    country, city = reverse_geocode_providers(lat, lon)
    if country or city:
        with closing(get_conn()) as conn:
            conn.execute(
                "INSERT INTO geo_cache(lat_rounded, lon_rounded, country, city, created_at) VALUES (?,?,?,?,?)",
                (lat_r, lon_r, country, city, now_iso()),
            )
            conn.commit()
    return country, city


def _json_object(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _photo_weather_labels(code: Optional[int]) -> Tuple[str, str]:
    if code is None:
        return ("Ukendt vejr", "Unknown weather")
    return WEATHER_CODE_LABELS.get(int(code), (f"Vejrkode {code}", f"Weather code {code}"))


def _parse_photo_datetime(raw: Any) -> Optional[datetime]:
    txt = str(raw or "").strip()
    if not txt:
        return None
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(txt)
    except Exception:
        return None
    # EXIF/photo times are usually local wall-clock times. For weather matching we
    # keep that wall-clock hour and let Open-Meteo return local hourly data.
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def _nearest_weather_hour(dt: datetime) -> datetime:
    rounded = dt.replace(minute=0, second=0, microsecond=0)
    if dt.minute >= 30:
        rounded = rounded + timedelta(hours=1)
    return rounded


def _weather_cache_key(lat: float, lon: float, observed_hour: datetime) -> Tuple[int, int, str]:
    lat_r = int(round(float(lat) * 1000))
    lon_r = int(round(float(lon) * 1000))
    hour = observed_hour.isoformat(timespec="minutes")
    return (lat_r, lon_r, hour)


def _weather_text_key(value: Any) -> str:
    txt = unicodedata.normalize("NFKC", str(value or "")).strip().casefold()
    return re.sub(r"\s+", " ", txt)


def _weather_country_code(value: Any) -> str:
    txt = str(value or "").strip()
    if not txt:
        return ""
    if re.fullmatch(r"[A-Za-z]{2}", txt):
        return txt.upper()
    try:
        country = pycountry.countries.lookup(txt)
        code = getattr(country, "alpha_2", "")
        return str(code or "").upper()
    except Exception:
        return ""


def _weather_location_query_key(city: Any, country: Any = None) -> str:
    city_key = _weather_text_key(city)
    country_code = _weather_country_code(country)
    country_key = country_code or _weather_text_key(country)
    return f"{city_key}|{country_key}"


def _weather_payload_from_cache(lat_r: int, lon_r: int, observed_hour: str) -> Optional[Dict[str, Any]]:
    try:
        with closing(get_conn()) as conn:
            row = conn.execute(
                """
                SELECT payload_json FROM weather_cache
                WHERE lat_rounded=? AND lon_rounded=? AND observed_hour=? AND provider=?
                """,
                (lat_r, lon_r, observed_hour, WEATHER_PROVIDER),
            ).fetchone()
        if not row:
            return None
        payload = _json_object(row["payload_json"])
        return payload if payload else None
    except Exception:
        return None


def _store_weather_payload_in_cache(lat_r: int, lon_r: int, observed_hour: str, payload: Dict[str, Any]) -> None:
    try:
        with closing(get_conn()) as conn:
            conn.execute(
                """
                INSERT INTO weather_cache(lat_rounded, lon_rounded, observed_hour, provider, payload_json, created_at)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(lat_rounded, lon_rounded, observed_hour, provider) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    created_at=excluded.created_at
                """,
                (lat_r, lon_r, observed_hour, WEATHER_PROVIDER, json.dumps(payload, ensure_ascii=False, default=str), now_iso()),
            )
            conn.commit()
    except Exception:
        pass


def _place_geocode_from_cache(query_key: str) -> Optional[Tuple[float, float, Dict[str, Any]]]:
    try:
        with closing(get_conn()) as conn:
            row = conn.execute(
                """
                SELECT city, country, latitude, longitude, payload_json
                FROM place_geocode_cache
                WHERE query_key=?
                """,
                (query_key,),
            ).fetchone()
        if not row:
            return None
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        payload = _json_object(row["payload_json"])
        context = payload if payload else {}
        context.update(
            {
                "location_source": "city",
                "location_city": row["city"],
                "location_country": row["country"],
                "geocoded_latitude": lat,
                "geocoded_longitude": lon,
            }
        )
        return (lat, lon, context)
    except Exception:
        return None


def _store_place_geocode_cache(query_key: str, city: str, country: str, lat: float, lon: float, context: Dict[str, Any]) -> None:
    try:
        with closing(get_conn()) as conn:
            conn.execute(
                """
                INSERT INTO place_geocode_cache(query_key, city, country, latitude, longitude, provider, payload_json, created_at)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(query_key) DO UPDATE SET
                    city=excluded.city,
                    country=excluded.country,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    provider=excluded.provider,
                    payload_json=excluded.payload_json,
                    created_at=excluded.created_at
                """,
                (
                    query_key,
                    city,
                    country,
                    float(lat),
                    float(lon),
                    WEATHER_PROVIDER,
                    json.dumps(context, ensure_ascii=False, default=str),
                    now_iso(),
                ),
            )
            conn.commit()
    except Exception:
        pass


def _geocode_city_for_weather(city: Any, country: Any = None) -> Tuple[float, float, Dict[str, Any]]:
    city_txt = str(city or "").strip()
    country_txt = str(country or "").strip()
    if not city_txt:
        raise ValueError("Billedet mangler GPS-koordinater eller by")

    query_key = _weather_location_query_key(city_txt, country_txt)
    cached = _place_geocode_from_cache(query_key)
    if cached:
        return cached

    if not WEATHER_GEOCODING_API_URL:
        raise RuntimeError("Weather geocoding is disabled")

    params: Dict[str, Any] = {
        "name": city_txt,
        "count": 5,
        "language": "en",
        "format": "json",
    }
    country_code = _weather_country_code(country_txt)
    if country_code:
        params["countryCode"] = country_code

    resp = requests.get(WEATHER_GEOCODING_API_URL, params=params, timeout=WEATHER_GEOCODING_TIMEOUT_SEC)
    if resp.status_code >= 400:
        raise RuntimeError(f"Weather geocoding returned HTTP {resp.status_code}")
    data = resp.json()
    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list) or not results:
        raise ValueError("Kunne ikke finde byen til vejrdata")

    country_key = _weather_text_key(country_txt)
    best = None
    for result in results:
        if not isinstance(result, dict):
            continue
        if country_code and str(result.get("country_code") or "").upper() != country_code:
            continue
        if country_key and not country_code and _weather_text_key(result.get("country")) != country_key:
            continue
        best = result
        break
    if best is None:
        best = next((r for r in results if isinstance(r, dict)), None)
    if not isinstance(best, dict):
        raise ValueError("Kunne ikke finde byen til vejrdata")

    try:
        lat = float(best.get("latitude"))
        lon = float(best.get("longitude"))
    except Exception:
        raise ValueError("Byen havde ingen gyldige koordinater") from None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Byen havde ugyldige koordinater")

    context: Dict[str, Any] = {
        "location_source": "city",
        "location_city": city_txt,
        "location_country": country_txt or best.get("country"),
        "geocoded_name": best.get("name"),
        "geocoded_country": best.get("country"),
        "geocoded_country_code": best.get("country_code"),
        "geocoded_admin1": best.get("admin1"),
        "geocoded_latitude": lat,
        "geocoded_longitude": lon,
        "geocoding_provider": "Open-Meteo Geocoding API",
    }
    _store_place_geocode_cache(query_key, city_txt, country_txt, lat, lon, context)
    return (lat, lon, context)


def _weather_location_from_values(gps_lat: Any, gps_lon: Any, metadata_json: Any = None) -> Tuple[float, float, Dict[str, Any]]:
    try:
        lat = float(gps_lat)
        lon = float(gps_lon)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            mj = _json_object(metadata_json)
            geo = mj.get("geo") if isinstance(mj.get("geo"), dict) else {}
            return (
                lat,
                lon,
                {
                    "location_source": "gps",
                    "location_city": geo.get("city"),
                    "location_country": geo.get("country"),
                },
            )
    except Exception:
        pass

    mj = _json_object(metadata_json)
    geo = mj.get("geo") if isinstance(mj.get("geo"), dict) else {}
    city = str(geo.get("city") or mj.get("city") or "").strip()
    country = str(geo.get("country") or mj.get("country") or "").strip()
    if city:
        return _geocode_city_for_weather(city, country)
    raise ValueError("Billedet mangler GPS-koordinater eller by")


def _write_photo_weather_metadata(photo_id: int, payload: Optional[Dict[str, Any]]) -> None:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT metadata_json FROM photos WHERE id=?", (photo_id,)).fetchone()
        mj = _json_object(row["metadata_json"] if row else None)
        if payload:
            mj["weather"] = payload
        else:
            mj.pop("weather", None)
        mj.pop("weather_fetch_failed", None)
        conn.execute("UPDATE photos SET metadata_json=? WHERE id=?", (json.dumps(mj, ensure_ascii=False, default=str), photo_id))
        conn.commit()


def _mark_photo_weather_fetch_failed(photo_id: int) -> None:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT metadata_json FROM photos WHERE id=?", (photo_id,)).fetchone()
        if not row:
            return
        mj = _json_object(row["metadata_json"])
        mj.pop("weather", None)
        mj["weather_fetch_failed"] = True
        conn.execute("UPDATE photos SET metadata_json=? WHERE id=?", (json.dumps(mj, ensure_ascii=False, default=str), photo_id))
        conn.commit()


def _clear_photo_weather_metadata(conn: sqlite3.Connection, photo_id: int) -> None:
    row = conn.execute("SELECT metadata_json FROM photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        return
    mj = _json_object(row["metadata_json"])
    if "weather" not in mj and "weather_fetch_failed" not in mj:
        return
    mj.pop("weather", None)
    mj.pop("weather_fetch_failed", None)
    conn.execute("UPDATE photos SET metadata_json=? WHERE id=?", (json.dumps(mj, ensure_ascii=False, default=str), photo_id))


def _fetch_open_meteo_weather(
    lat: float,
    lon: float,
    captured_at: str,
    observed_hour: datetime,
    cache_key: str,
    location_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not WEATHER_HISTORY_API_URL:
        raise RuntimeError("Weather API is disabled")

    params = {
        "latitude": f"{float(lat):.6f}",
        "longitude": f"{float(lon):.6f}",
        "start_date": observed_hour.date().isoformat(),
        "end_date": observed_hour.date().isoformat(),
        "hourly": ",".join(WEATHER_HOURLY_FIELDS),
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
    }
    resp = requests.get(WEATHER_HISTORY_API_URL, params=params, timeout=WEATHER_HISTORY_TIMEOUT_SEC)
    if resp.status_code >= 400:
        raise RuntimeError(f"Weather API returned HTTP {resp.status_code}")
    data = resp.json()
    hourly = data.get("hourly") if isinstance(data, dict) else None
    if not isinstance(hourly, dict):
        raise RuntimeError("Weather API response has no hourly data")

    times = hourly.get("time")
    if not isinstance(times, list) or not times:
        raise RuntimeError("Weather API returned no hourly timestamps")

    target = observed_hour.replace(second=0, microsecond=0)
    best_idx = -1
    best_delta = None
    for idx, raw_time in enumerate(times):
        try:
            candidate = datetime.fromisoformat(str(raw_time)).replace(second=0, microsecond=0)
        except Exception:
            continue
        delta = abs((candidate - target).total_seconds())
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_idx = idx
    if best_idx < 0 or best_delta is None or best_delta > 7200:
        raise RuntimeError("Weather API had no matching hour")

    def pick(field: str) -> Any:
        vals = hourly.get(field)
        if not isinstance(vals, list) or best_idx >= len(vals):
            return None
        return vals[best_idx]

    raw_code = pick("weather_code")
    try:
        code = int(raw_code) if raw_code is not None else None
    except Exception:
        code = None
    label_da, label_en = _photo_weather_labels(code)
    units = data.get("hourly_units") if isinstance(data.get("hourly_units"), dict) else {}
    context = dict(location_context or {})

    payload: Dict[str, Any] = {
        "provider": WEATHER_PROVIDER,
        "source": "Open-Meteo Historical Weather API",
        "cache_key": cache_key,
        "fetched_at": now_iso(),
        "captured_at": str(captured_at or ""),
        "observed_at": str(times[best_idx]),
        "timezone": data.get("timezone") if isinstance(data, dict) else None,
        "timezone_abbreviation": data.get("timezone_abbreviation") if isinstance(data, dict) else None,
        "requested_latitude": float(lat),
        "requested_longitude": float(lon),
        "latitude": data.get("latitude") if isinstance(data, dict) else None,
        "longitude": data.get("longitude") if isinstance(data, dict) else None,
        "location_source": context.get("location_source") or "gps",
        "location_city": context.get("location_city"),
        "location_country": context.get("location_country"),
        "geocoded_name": context.get("geocoded_name"),
        "geocoded_country": context.get("geocoded_country"),
        "geocoded_country_code": context.get("geocoded_country_code"),
        "geocoded_admin1": context.get("geocoded_admin1"),
        "geocoded_latitude": context.get("geocoded_latitude"),
        "geocoded_longitude": context.get("geocoded_longitude"),
        "geocoding_provider": context.get("geocoding_provider"),
        "weather_code": code,
        "weather_label_da": label_da,
        "weather_label_en": label_en,
        "temperature_2m": pick("temperature_2m"),
        "temperature_2m_unit": units.get("temperature_2m", "°C"),
        "relative_humidity_2m": pick("relative_humidity_2m"),
        "relative_humidity_2m_unit": units.get("relative_humidity_2m", "%"),
        "precipitation": pick("precipitation"),
        "precipitation_unit": units.get("precipitation", "mm"),
        "rain": pick("rain"),
        "rain_unit": units.get("rain", "mm"),
        "snowfall": pick("snowfall"),
        "snowfall_unit": units.get("snowfall", "cm"),
        "cloud_cover": pick("cloud_cover"),
        "cloud_cover_unit": units.get("cloud_cover", "%"),
        "wind_speed_10m": pick("wind_speed_10m"),
        "wind_speed_10m_unit": units.get("wind_speed_10m", "m/s"),
        "wind_direction_10m": pick("wind_direction_10m"),
        "wind_direction_10m_unit": units.get("wind_direction_10m", "°"),
    }
    return payload


def get_or_fetch_weather_payload(
    captured_raw: Any,
    gps_lat: Any,
    gps_lon: Any,
    metadata_json: Any,
    *,
    force: bool = False,
) -> Tuple[Dict[str, Any], str]:
    captured_raw = str(captured_raw or "").strip()
    captured_dt = _parse_photo_datetime(captured_raw)
    if not captured_dt:
        raise ValueError("Billedet mangler dato/tid")

    lat, lon, location_context = _weather_location_from_values(gps_lat, gps_lon, metadata_json)
    observed_hour_dt = _nearest_weather_hour(captured_dt)
    lat_r, lon_r, observed_hour = _weather_cache_key(lat, lon, observed_hour_dt)
    cache_key = f"{WEATHER_PROVIDER}:{lat_r}:{lon_r}:{observed_hour}"

    if not force:
        cached = _weather_payload_from_cache(lat_r, lon_r, observed_hour)
        if cached:
            return (cached, "cache")

    payload = _fetch_open_meteo_weather(lat, lon, captured_raw, observed_hour_dt, cache_key, location_context)
    _store_weather_payload_in_cache(lat_r, lon_r, observed_hour, payload)
    return (payload, "api")


def _enrich_metadata_weather(metadata: Dict[str, Any]) -> None:
    if not WEATHER_AUTO_FETCH:
        return
    mj = metadata.get("metadata_json") if isinstance(metadata.get("metadata_json"), dict) else {}
    if isinstance(mj.get("weather"), dict):
        return
    captured_raw = metadata.get("captured_at") or metadata.get("modified_fs") or metadata.get("created_fs")
    try:
        payload, source = get_or_fetch_weather_payload(
            captured_raw,
            metadata.get("gps_lat"),
            metadata.get("gps_lon"),
            mj,
            force=False,
        )
        mj.pop("weather_fetch_failed", None)
        mj["weather"] = payload
        metadata["metadata_json"] = mj
        try:
            log_event(
                "weather_indexed",
                rel_path=str(metadata.get("rel_path") or ""),
                source=source,
                location_source=str(payload.get("location_source") or ""),
            )
        except Exception:
            pass
    except ValueError:
        pass
    except Exception as e:
        try:
            log_event("error", rel_path=str(metadata.get("rel_path") or "weather"), error=f"weather_index: {e}")
        except Exception:
            pass


def get_or_fetch_photo_weather(row: sqlite3.Row, force: bool = False) -> Tuple[Dict[str, Any], str]:
    photo_id = int(row["id"])
    mj = _json_object(row["metadata_json"])
    existing = mj.get("weather") if isinstance(mj.get("weather"), dict) else None
    if existing and not force:
        return (existing, "photo")

    captured_raw = str(row["captured_at"] or row["modified_fs"] or row["created_fs"] or "").strip()
    payload, source = get_or_fetch_weather_payload(
        captured_raw,
        row["gps_lat"],
        row["gps_lon"],
        mj,
        force=force,
    )
    _write_photo_weather_metadata(photo_id, payload)
    return (payload, source)


def _refresh_photo_weather_if_possible(photo_id: int, *, force: bool = False) -> None:
    if not WEATHER_AUTO_FETCH:
        return
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT * FROM photos WHERE id=?", (int(photo_id),)).fetchone()
        if row:
            get_or_fetch_photo_weather(row, force=force)
    except ValueError:
        pass
    except Exception as e:
        try:
            _mark_photo_weather_fetch_failed(int(photo_id))
        except Exception:
            pass
        try:
            log_event("error", rel_path=f"weather:{photo_id}", error=f"weather_refresh: {e}")
        except Exception:
            pass


def reverse_geocode_providers(lat: float, lon: float) -> tuple[Optional[str], Optional[str]]:
    """Try configured provider first, then fallbacks (Offline RG â†’ Nominatim â†’ BigDataCloud â†’ Photon)."""
    order: list[str] = []
    pref = GEOCODE_PROVIDER or "rg"
    if pref not in ("rg", "nominatim", "bigdatacloud", "photon"):
        pref = "rg"
    order.append(pref)
    for p in ("rg", "nominatim", "bigdatacloud", "photon"):
        if p not in order:
            order.append(p)

    last_err = None
    ua = {"User-Agent": f"FjordLens/1.0 ({GEOCODE_EMAIL})"}
    for prov in order:
        try:
            time.sleep(max(0.0, GEOCODE_DELAY))
            if prov == "rg":
                # Offline reverse geocoder (city-level, no network)
                try:
                    out = rg.search((lat, lon), mode=1, verbose=False)
                except TypeError:
                    # older versions don't support verbose arg
                    out = rg.search((lat, lon), mode=1)
                if out:
                    rec = out[0]
                    city = rec.get("name") or rec.get("admin1") or rec.get("admin2")
                    cc = rec.get("cc")
                    country = None
                    if cc:
                        try:
                            c = pycountry.countries.get(alpha_2=cc.upper())
                            country = getattr(c, "name", None)
                        except Exception:
                            country = cc
                    if country or city:
                        return country, city
            elif prov == "nominatim":
                r = requests.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 10, "addressdetails": 1},
                    headers=ua,
                    timeout=GEOCODE_TIMEOUT,
                )
                if r.status_code == 429:
                    last_err = "nominatim 429"
                    continue
                if r.ok:
                    js = r.json()
                    addr = js.get("address", {})
                    country = addr.get("country")
                    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet")
                    if country or city:
                        return country, city
            elif prov == "bigdatacloud":
                r = requests.get(
                    "https://api.bigdatacloud.net/data/reverse-geocode-client",
                    params={"latitude": lat, "longitude": lon, "localityLanguage": GEOCODE_LANG or "en"},
                    headers=ua,
                    timeout=GEOCODE_TIMEOUT,
                )
                if r.ok:
                    js = r.json()
                    country = js.get("countryName")
                    city = js.get("city") or js.get("locality") or js.get("principalSubdivision")
                    if country or city:
                        return country, city
            elif prov == "photon":
                r = requests.get(
                    "https://photon.komoot.io/reverse",
                    params={"lat": lat, "lon": lon, "lang": GEOCODE_LANG or "en"},
                    headers=ua,
                    timeout=GEOCODE_TIMEOUT,
                )
                if r.ok:
                    js = r.json()
                    feats = js.get("features") or []
                    if feats:
                        props = feats[0].get("properties", {})
                        country = props.get("country")
                        city = props.get("city") or props.get("town") or props.get("village") or props.get("state") or props.get("name")
                        if country or city:
                            return country, city
        except Exception as e:
            last_err = str(e)
            continue
    if last_err:
        log_event("error", rel_path="geocode", error=f"providers_failed: {last_err}")
    return None, None


def rescan_metadata(stop_event=None) -> Dict[str, Any]:
    init_db()
    log_event("rescan_start")
    scanned = 0
    updated = 0
    errors = 0
    missing = 0
    samples: list[str] = []

    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT id, rel_path, thumb_name,
                   gps_lat, gps_lon, lens_model, camera_make, camera_model,
                   captured_at, iso, focal_length, f_number,
                   gps_name, metadata_json
            FROM photos
            """
        ).fetchall()

    for row in rows:
        if stop_event and stop_event.is_set():
            break
        rel_path = row["rel_path"]
        disk_path = _disk_path_from_rel_path(rel_path)
        scanned += 1
        log_event("rescan_check", rel_path=rel_path)
        if not disk_path.exists():
            missing += 1
            log_event("missing", rel_path=rel_path)
            continue
        try:
            meta = extract_metadata(disk_path, rel_path, generate_thumb=False)
            # Preserve existing thumbnail name if we didn't regenerate
            if not meta.get("thumb_name"):
                meta["thumb_name"] = row["thumb_name"]
            # Determine if anything actually changes (subset of important fields)
            changed = False
            keys = [
                "gps_lat", "gps_lon", "lens_model", "camera_make", "camera_model",
                "captured_at", "iso", "focal_length", "f_number"
            ]
            for k in keys:
                old = row[k]
                new = meta.get(k)
                if old != new:
                    changed = True
                    break
            # If not changed yet, see if reverse-geocoded geo/city/country was added
            if not changed:
                try:
                    old_mj = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                except Exception:
                    old_mj = {}
                old_geo = (old_mj.get("geo") or {})
                new_mj = meta.get("metadata_json") or {}
                new_geo = (new_mj.get("geo") or {})
                old_city = old_geo.get("city")
                old_country = old_geo.get("country")
                new_city = new_geo.get("city")
                new_country = new_geo.get("country")
                if (new_city and new_city != old_city) or (new_country and new_country != old_country):
                    changed = True
                elif (meta.get("gps_name") or None) != (row["gps_name"] or None):
                    changed = True
                else:
                    old_weather = old_mj.get("weather") if isinstance(old_mj.get("weather"), dict) else None
                    new_weather = new_mj.get("weather") if isinstance(new_mj.get("weather"), dict) else None
                    if new_weather and (
                        not old_weather
                        or new_weather.get("cache_key") != old_weather.get("cache_key")
                        or new_weather.get("fetched_at") != old_weather.get("fetched_at")
                    ):
                        changed = True
            if changed:
                upsert_photo(meta)
                updated += 1
                log_event("rescan_updated", rel_path=rel_path)
            else:
                log_event("no_new", rel_path=rel_path)
        except Exception as e:
            errors += 1
            log_event("error", rel_path=rel_path, error=str(e))
            if len(samples) < 5:
                samples.append(f"{rel_path}: {e}")

    result = {
        "ok": True,
        "scanned": scanned,
        "updated": updated,
        "errors": errors,
        "missing": missing,
        "error_samples": samples,
    }
    log_event("rescan_done", scanned=scanned, updated=updated, errors=errors, missing=missing)
    return result


# --- Face indexing API ---
_faces_running = threading.Event()
faces_counts: Dict[str, int] = {"processed": 0, "total": 0}
last_faces_result: Optional[Dict[str, Any]] = None


def _is_faces_index_supported_rel(rel_path: str) -> bool:
    ext = Path(str(rel_path or "")).suffix.lower()
    return ext in SUPPORTED_EXTS


def _faces_index_coverage() -> Dict[str, int]:
    counts = {"total": 0, "indexed": 0, "missing": 0, "with_faces": 0, "faces": 0, "unsupported": 0}
    try:
        with closing(get_conn()) as conn:
            rows = conn.execute("SELECT rel_path, people_count, faces_indexed_at FROM photos").fetchall()
    except Exception:
        return counts

    for row in rows:
        if not _is_faces_index_supported_rel(row["rel_path"]):
            counts["unsupported"] += 1
            continue
        counts["total"] += 1
        people_count = int(row["people_count"] or 0)
        indexed_at = str(row["faces_indexed_at"] or "").strip()
        if indexed_at:
            counts["indexed"] += 1
        else:
            counts["missing"] += 1
        if people_count > 0:
            counts["with_faces"] += 1
            counts["faces"] += people_count
    return counts


def _index_faces_worker(all_photos: bool = False):
    global faces_counts, last_faces_result
    try:
        with closing(get_conn()) as conn:
            if all_photos:
                rows = conn.execute("SELECT rel_path FROM photos").fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT rel_path
                    FROM photos
                    WHERE faces_indexed_at IS NULL OR TRIM(faces_indexed_at) = ''
                    """
                ).fetchall()
        rows = [row for row in rows if _is_faces_index_supported_rel(row["rel_path"])]
        total = len(rows)
        faces_counts = {"processed": 0, "total": total}
        for row in rows:
            if not _faces_running.is_set():
                break
            rel = row["rel_path"]
            log_event("faces_index", rel_path=rel)
            index_faces_for_photo(rel)
            faces_counts["processed"] += 1
            face_delay = faces_index_throttle_enabled_sec()
            if face_delay > 0:
                time.sleep(face_delay)
        last_faces_result = {"ok": True, **faces_counts}
    finally:
        _faces_running.clear()


@app.route("/api/faces/index", methods=["POST"])
def api_faces_index():
    global faces_counts
    if _faces_running.is_set():
        return jsonify({"ok": False, "error": "Faces indexing already running"}), 409
    scope = (request.args.get("scope") or "").strip().lower()
    _set_setting("faces_auto_index", "1")
    if scope == "new":
        return jsonify({"ok": True, "running": False, "auto_index": True, "scope": "new"})

    _faces_running.set()
    faces_counts = {"processed": 0, "total": 0}
    all_photos = True if scope == "all" else (request.args.get("all") in {"1", "true", "True"})
    threading.Thread(target=_index_faces_worker, args=(all_photos,), daemon=True).start()
    return jsonify({"ok": True, "running": True, "auto_index": True, "scope": (scope or ("all" if all_photos else "missing"))})


@app.route("/api/faces/stop", methods=["POST"])
def api_faces_stop():
    _set_setting("faces_auto_index", "0")
    if _faces_running.is_set():
        _faces_running.clear()
        return jsonify({"ok": True, "running": True, "stopping": True, "auto_index": False})
    return jsonify({"ok": True, "running": False, "auto_index": False})


@app.route("/api/faces/status")
def api_faces_status():
    rt = _ai_runtime_info()
    resp: Dict[str, Any] = {
        "ok": True,
        "running": _faces_running.is_set(),
        "auto_index": faces_auto_index_enabled(),
        **faces_counts,
        "coverage": _faces_index_coverage(),
        "runtime": {
            "service_ok": rt["service_ok"],
            "ai": rt["ai_device"],
            "faces": rt["face_device"],
            "ai_raw": rt["ai_device_raw"],
            "faces_raw": rt["face_device_raw"],
        },
    }
    if not _faces_running.is_set() and last_faces_result:
        resp["last"] = last_faces_result
    return jsonify(resp)


def upsert_photo(meta: Dict[str, Any]) -> None:
    with closing(get_conn()) as conn:
        conn.execute(
            """
            INSERT INTO photos (
                rel_path, filename, ext, file_size, width, height, created_fs, modified_fs,
                captured_at, camera_make, camera_model, lens_model, iso, focal_length, f_number,
                exposure_time, gps_lat, gps_lon, gps_name, checksum_sha256, phash, phash_dct, dhash, ahash, thumb_name,
                favorite, people_count, faces_indexed_at, ai_tags, embedding_json, metadata_json, exif_json,
                uploaded_by, imported_at, last_scanned_at
            ) VALUES (
                :rel_path, :filename, :ext, :file_size, :width, :height, :created_fs, :modified_fs,
                :captured_at, :camera_make, :camera_model, :lens_model, :iso, :focal_length, :f_number,
                :exposure_time, :gps_lat, :gps_lon, :gps_name, :checksum_sha256, :phash, :phash_dct, :dhash, :ahash, :thumb_name,
                COALESCE((SELECT favorite FROM photos WHERE rel_path=:rel_path), 0),
                COALESCE((SELECT people_count FROM photos WHERE rel_path=:rel_path), 0),
                COALESCE((SELECT faces_indexed_at FROM photos WHERE rel_path=:rel_path), NULL),
                :ai_tags, COALESCE((SELECT embedding_json FROM photos WHERE rel_path=:rel_path), NULL),
                :metadata_json, :exif_json,
                COALESCE((SELECT uploaded_by FROM photos WHERE rel_path=:rel_path), :uploaded_by),
                COALESCE((SELECT imported_at FROM photos WHERE rel_path=:rel_path), :imported_at),
                :last_scanned_at
            )
            ON CONFLICT(rel_path) DO UPDATE SET
                filename=excluded.filename,
                ext=excluded.ext,
                file_size=excluded.file_size,
                width=excluded.width,
                height=excluded.height,
                created_fs=excluded.created_fs,
                modified_fs=excluded.modified_fs,
                captured_at=excluded.captured_at,
                camera_make=excluded.camera_make,
                camera_model=excluded.camera_model,
                lens_model=excluded.lens_model,
                iso=excluded.iso,
                focal_length=excluded.focal_length,
                f_number=excluded.f_number,
                exposure_time=excluded.exposure_time,
                gps_lat=excluded.gps_lat,
                gps_lon=excluded.gps_lon,
                gps_name=excluded.gps_name,
                checksum_sha256=excluded.checksum_sha256,
                phash=excluded.phash,
                phash_dct=excluded.phash_dct,
                dhash=excluded.dhash,
                ahash=excluded.ahash,
                thumb_name=excluded.thumb_name,
                ai_tags=excluded.ai_tags,
                metadata_json=excluded.metadata_json,
                exif_json=excluded.exif_json,
                uploaded_by=COALESCE(excluded.uploaded_by, uploaded_by),
                last_scanned_at=excluded.last_scanned_at
            """,
            {
                **meta,
                "ai_tags": json.dumps(meta.get("ai_tags", []), ensure_ascii=False),
                "metadata_json": json.dumps(meta.get("metadata_json", {}), ensure_ascii=False, default=str),
                "exif_json": json.dumps(meta.get("exif_json", {}), ensure_ascii=False, default=str),
                "uploaded_by": _sanitize_share_visitor_name(meta.get("uploaded_by") or "") or None,
                "imported_at": now_iso(),
                "last_scanned_at": now_iso(),
            },
        )
        conn.commit()


def iter_photo_files(root: Path, prefix: str = "") -> Iterable[Tuple[Path, str]]:
    if not root.exists():
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SUPPORTED_EXTS:
            continue
        # Skip Synology generated thumbnails and special folders
        name_upper = p.name.upper()
        if any(part == "@eaDir" for part in p.parts):
            continue
        if name_upper.startswith("SYNOPHOTO_THUMB_") or name_upper.startswith("SYNOPHOTO_CACHE_"):
            continue
        if p.name.startswith("._"):  # macOS resource forks
            continue
        try:
            rel = str(p.relative_to(root)).replace("\\", "/")
        except Exception:
            rel = p.name
        if prefix:
            rel = f"{prefix.rstrip('/')}/{rel}"
        yield p, rel


def scan_library(stop_event=None) -> Dict[str, Any]:
    init_db()
    log_event("scan_start")

    if library_source_enabled() and not PHOTO_DIR.exists():
        return {
            "ok": False,
            "error": f"Photo folder not found: {PHOTO_DIR}",
            "scanned": 0,
            "updated": 0,
            "errors": 0,
        }

    scanned = 0
    updated = 0
    errors = 0
    error_samples: list[str] = []

    with closing(get_conn()) as conn:
        existing = {
            row["rel_path"]: row
            for row in conn.execute(
                "SELECT rel_path, modified_fs, file_size, gps_lat, gps_lon, lens_model FROM photos"
            )
        }


    # Scan primary photo directory (optional)
    if library_source_enabled():
        for path, rel_path in iter_photo_files(PHOTO_DIR):
            if stop_event and stop_event.is_set():
                break
            scanned += 1
            try:
                log_event("scan_check", rel_path=rel_path)
                stat = path.stat()
                modified_fs = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
                file_size = stat.st_size
                prev = existing.get(rel_path)
                if prev:
                    unchanged = (prev["modified_fs"] == modified_fs and prev["file_size"] == file_size)
                    missing_meta = (prev["lens_model"] in (None, "")) or (prev["gps_lat"] is None and prev["gps_lon"] is None)
                    if unchanged and not missing_meta:
                        log_event("skip_unchanged", rel_path=rel_path)
                        log_event("no_new", rel_path=rel_path)
                        continue

                meta = extract_metadata(path, rel_path)
                upsert_photo(meta)
                updated += 1
                log_event("indexed", rel_path=rel_path)
            except Exception as e:
                errors += 1
                log_event("error", rel_path=rel_path, error=str(e))
                if len(error_samples) < 5:
                    error_samples.append(f"{rel_path}: {e}")

    # Also scan uploaded files stored under DATA_DIR/uploads (prefixed as 'uploads/...')
    for path, rel_path in iter_photo_files(UPLOAD_DIR, prefix="uploads"):
        if stop_event and stop_event.is_set():
            break
        scanned += 1
        try:
            log_event("scan_check", rel_path=rel_path)
            stat = path.stat()
            modified_fs = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
            file_size = stat.st_size
            prev = existing.get(rel_path)
            if prev:
                unchanged = (prev["modified_fs"] == modified_fs and prev["file_size"] == file_size)
                missing_meta = (prev["lens_model"] in (None, "")) or (prev["gps_lat"] is None and prev["gps_lon"] is None)
                if unchanged and not missing_meta:
                    log_event("skip_unchanged", rel_path=rel_path)
                    log_event("no_new", rel_path=rel_path)
                    continue

            meta = extract_metadata(path, rel_path)
            upsert_photo(meta)
            updated += 1
            log_event("indexed", rel_path=rel_path)
        except Exception as e:
            errors += 1
            log_event("error", rel_path=rel_path, error=str(e))
            if len(error_samples) < 5:
                error_samples.append(f"{rel_path}: {e}")

    result = {
        "ok": True,
        "photo_dir": str(PHOTO_DIR),
        "scanned": scanned,
        "updated": updated,
        "errors": errors,
        "error_samples": error_samples,
        "stopped": bool(stop_event.is_set()) if stop_event else False,
    }
    log_event("scan_done", scanned=scanned, updated=updated, errors=errors)
    return result


def _normalize_upload_folder_for_disk_sync(value: Optional[str]) -> str:
    folder = _normalize_folder_acl_path(value)
    if folder == "uploads":
        return ""
    if folder.startswith("uploads/"):
        folder = folder[len("uploads/"):]
    if folder in {"originals", "converted"}:
        return ""
    if folder.startswith("originals/"):
        folder = folder[len("originals/"):]
    elif folder.startswith("converted/"):
        folder = folder[len("converted/"):]
    return folder.strip("/")


def _safe_sync_child(base: Path, rel_folder: str) -> Optional[Path]:
    try:
        base_resolved = base.resolve()
        target = (base / rel_folder).resolve() if rel_folder else base_resolved
        target.relative_to(base_resolved)
        return target
    except Exception:
        return None


def _upload_folder_sync_roots(folder: str) -> list[tuple[Path, str, set[str]]]:
    f = str(folder or "").strip("/")
    roots: list[tuple[Path, str, set[str]]] = []

    def add(base: Path, rel_prefix: str, excluded_top_dirs: Optional[set[str]] = None) -> None:
        target = _safe_sync_child(base, f)
        if target is None:
            return
        roots.append((target, rel_prefix.rstrip("/"), set(excluded_top_dirs or set())))

    tail = f"/{f}" if f else ""
    add(UPLOAD_DIR / "originals", f"uploads/originals{tail}")
    add(UPLOAD_DIR / "converted", f"uploads/converted{tail}")
    add(UPLOAD_DIR, f"uploads{tail}", {"originals", "converted"} if not f else set())
    return roots


def _upload_storage_tail(rel_path: str) -> tuple[str, str]:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    if rel.startswith("uploads/originals/"):
        return "originals", rel[len("uploads/originals/"):]
    if rel.startswith("uploads/converted/"):
        return "converted", rel[len("uploads/converted/"):]
    if rel.startswith("uploads/"):
        return "direct", rel[len("uploads/"):]
    return "", rel


def _upload_display_key(rel_path: str) -> str:
    kind, tail = _upload_storage_tail(rel_path)
    if not kind or not tail:
        return str(rel_path or "")
    p = Path(tail.replace("\\", "/"))
    parent = str(p.parent).replace("\\", "/").strip(".").strip("/")
    stem = p.stem
    key_tail = f"{parent}/{stem}" if parent else stem
    return f"uploads/{key_tail}".lower()


def _upload_display_rank(rel_path: str) -> int:
    kind, _ = _upload_storage_tail(rel_path)
    if kind == "converted":
        return 0
    if kind == "originals":
        return 1
    if kind == "direct":
        return 2
    return 3


def _prefer_upload_rel(candidate_rel: str, current_rel: str) -> bool:
    cand_rank = _upload_display_rank(candidate_rel)
    cur_rank = _upload_display_rank(current_rel)
    if cand_rank != cur_rank:
        return cand_rank < cur_rank
    return str(candidate_rel or "").lower() < str(current_rel or "").lower()


def _dedupe_upload_storage_rows(rows: Iterable[sqlite3.Row]) -> list[sqlite3.Row]:
    ordered_keys: list[str] = []
    best_by_key: dict[str, sqlite3.Row] = {}
    for row in rows:
        rel = str(row["rel_path"] or "")
        key = _upload_display_key(rel) if rel.startswith("uploads/") else rel
        if key not in best_by_key:
            ordered_keys.append(key)
            best_by_key[key] = row
            continue
        current = best_by_key[key]
        if _prefer_upload_rel(rel, str(current["rel_path"] or "")):
            best_by_key[key] = row
    return [best_by_key[k] for k in ordered_keys if k in best_by_key]


def _dedupe_upload_sync_candidates(candidates: Iterable[tuple[Path, str]]) -> list[tuple[Path, str]]:
    ordered_keys: list[str] = []
    best_by_key: dict[str, tuple[Path, str]] = {}
    for path, rel in candidates:
        key = _upload_display_key(rel) if rel.startswith("uploads/") else rel
        if key not in best_by_key:
            ordered_keys.append(key)
            best_by_key[key] = (path, rel)
            continue
        _, current_rel = best_by_key[key]
        if _prefer_upload_rel(rel, current_rel):
            best_by_key[key] = (path, rel)
    return [best_by_key[k] for k in ordered_keys if k in best_by_key]


def _upload_rel_needs_postprocess_conversion(rel_path: str) -> bool:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    kind, _ = _upload_storage_tail(rel)
    if kind == "converted":
        return False
    ext = Path(rel).suffix.lower()
    if ext in {".heic", ".heif"}:
        if not heic_convert_on_upload_enabled():
            return False
        converted_exts = None
    elif ext == ".mov":
        if not mov_convert_on_upload_enabled():
            return False
        converted_exts = (".mp4",)
    elif ext in RAW_EXTS:
        if not raw_convert_on_upload_enabled():
            return False
        converted_exts = None
    else:
        return False
    try:
        converted = _find_existing_converted_for_upload_rel(rel, extensions=converted_exts)
        if converted is not None and converted.exists():
            return False
    except Exception:
        pass
    return True


def _iter_upload_sync_files(
    root: Path,
    rel_prefix: str,
    *,
    recursive: bool,
    excluded_top_dirs: Optional[set[str]] = None,
) -> Iterable[Tuple[Path, str]]:
    if not root.exists() or not root.is_dir():
        return
    excluded = {str(x or "").strip().lower() for x in (excluded_top_dirs or set()) if str(x or "").strip()}
    blocked_dir_names = {"@eadir", "#recycle"}
    try:
        iterator = root.rglob("*") if recursive else root.iterdir()
        for p in iterator:
            try:
                rel_parts = p.relative_to(root).parts
            except Exception:
                rel_parts = p.parts
            if rel_parts:
                top = str(rel_parts[0] or "").strip().lower()
                if top in excluded:
                    continue
            dir_parts = rel_parts[:-1] if p.is_file() else rel_parts
            skip = False
            for part in dir_parts:
                part_s = str(part or "")
                part_l = part_s.strip().lower()
                if part_l in blocked_dir_names or part_s.startswith("."):
                    skip = True
                    break
            if skip or not p.is_file():
                continue
            if p.suffix.lower() not in SUPPORTED_EXTS:
                continue
            name_upper = p.name.upper()
            if name_upper.startswith("SYNOPHOTO_THUMB_") or name_upper.startswith("SYNOPHOTO_CACHE_"):
                continue
            if p.name.startswith("._"):
                continue
            try:
                rel_leaf = str(p.relative_to(root)).replace("\\", "/")
            except Exception:
                rel_leaf = p.name
            rel = f"{rel_prefix.rstrip('/')}/{rel_leaf}" if rel_prefix else rel_leaf
            yield p, rel
    except Exception:
        return


def _existing_photo_rows_for_rels(rel_paths: list[str]) -> dict[str, sqlite3.Row]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for rel in rel_paths:
        key = str(rel or "").strip()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(key)
    if not cleaned:
        return {}
    out: dict[str, sqlite3.Row] = {}
    with closing(get_conn()) as conn:
        for i in range(0, len(cleaned), 500):
            chunk = cleaned[i : i + 500]
            placeholders = ",".join(["?"] * len(chunk))
            rows = conn.execute(
                f"SELECT rel_path, modified_fs, file_size, thumb_name, checksum_sha256 FROM photos WHERE rel_path IN ({placeholders})",
                chunk,
            ).fetchall()
            for row in rows:
                out[str(row["rel_path"])] = row
    return out


def _photo_row_needs_disk_sync(row: Optional[sqlite3.Row], stat: os.stat_result) -> bool:
    if row is None:
        return True
    modified_fs = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    try:
        same_mtime = str(row["modified_fs"] or "") == modified_fs
        same_size = int(row["file_size"] or -1) == int(stat.st_size)
    except Exception:
        return True
    if not (same_mtime and same_size):
        return True
    thumb_name = str(row["thumb_name"] or "").strip()
    if not thumb_name:
        try:
            checksum = str(row["checksum_sha256"] or "").strip()
        except Exception:
            checksum = ""
        return not bool(checksum)
    try:
        return not (THUMB_DIR / thumb_name).exists()
    except Exception:
        return True


def _start_direct_upload_postprocess(rel_paths: list[str]) -> bool:
    rels: list[str] = []
    seen: set[str] = set()
    for raw in rel_paths:
        rel = str(raw or "").replace("\\", "/").lstrip("/").strip()
        if not rel or rel in seen:
            continue
        seen.add(rel)
        rels.append(rel)
    if not rels:
        return False

    state_user = DIRECT_UPLOAD_POSTPROCESS_USER
    if UPLOAD_POSTPROCESS_STOP_EVENT.is_set():
        return False
    with DIRECT_UPLOAD_POSTPROCESS_ACTIVE_LOCK:
        rels = [rel for rel in rels if rel not in DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS]
        DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS.update(rels)
    if not rels:
        return False

    if _is_upload_postprocess_running(state_user):
        for rel in rels:
            _queue_uploaded_rel(state_user, rel)
        try:
            log_event("direct_upload_postprocess_queued", files=len(rels))
        except Exception:
            pass
        return True

    # Manual/direct folder imports must stay low priority so the UI remains usable.
    workflow_mode = UPLOAD_WORKFLOW_MODE_GENTLE
    _set_upload_postprocess_state(
        state_user,
        {
            "running": True,
            "started_at": now_iso(),
            "finished_at": None,
            "error": None,
            "result": None,
            "phase": "starting",
            "workflow_mode": workflow_mode,
            "process_status": None,
            "current_rel": None,
            "stage_processed": 0,
            "stage_total": len(rels),
            "overall_processed": 0,
            "overall_total": len(rels),
        },
    )

    aggregate: Dict[str, Any] = {
        "ok": True,
        "workflow_mode": workflow_mode,
        "received": 0,
        "indexed": 0,
        "index_errors": 0,
        "heic_converted": 0,
        "faces_enabled": faces_auto_index_enabled(),
        "faces_done": 0,
        "faces_found": 0,
        "faces_errors": 0,
        "ai_enabled": ai_auto_ingest_enabled(),
        "ai_done": 0,
        "ai_errors": 0,
        "ai_desc_enabled": ai_desc_auto_ingest_enabled(),
        "ai_desc_done": 0,
        "ai_desc_errors": 0,
        "process_status": None,
    }

    def merge_result(result: Dict[str, Any]) -> None:
        for key in (
            "received",
            "indexed",
            "index_errors",
            "heic_converted",
            "faces_done",
            "faces_found",
            "faces_errors",
            "ai_done",
            "ai_errors",
            "ai_desc_done",
            "ai_desc_errors",
        ):
            aggregate[key] += int(result[key] if key in result and result[key] is not None else 0)
        aggregate["faces_enabled"] = bool(result["faces_enabled"] if "faces_enabled" in result else False)
        aggregate["ai_enabled"] = bool(result["ai_enabled"] if "ai_enabled" in result else False)
        aggregate["ai_desc_enabled"] = bool(result["ai_desc_enabled"] if "ai_desc_enabled" in result else False)
        if "process_status" in result:
            aggregate["process_status"] = result["process_status"]

    def run() -> None:
        processed_total = 0
        known_total = len(rels)

        def set_direct_progress(progress: Dict[str, Any]) -> None:
            stage_processed = int(progress.get("stage_processed") or 0)
            pending_count = _pending_upload_count(state_user)
            payload = dict(
                progress,
                workflow_mode=workflow_mode,
                overall_processed=max(0, min(known_total, processed_total + stage_processed)),
                overall_total=max(known_total, processed_total + stage_processed),
            )
            if str(payload.get("phase") or "").lower() == "done" and (batch or pending_count > 0):
                payload["phase"] = "starting"
                payload["current_rel"] = None
            _set_upload_postprocess_state(
                state_user,
                payload,
            )

        try:
            batch = list(rels)
            while batch:
                if UPLOAD_POSTPROCESS_STOP_EVENT.is_set():
                    break
                chunk = batch[:DIRECT_UPLOAD_POSTPROCESS_BATCH_SIZE]
                batch = batch[DIRECT_UPLOAD_POSTPROCESS_BATCH_SIZE:]
                try:
                    log_event("direct_upload_postprocess_start", files=len(chunk), pending=len(batch), workflow_mode=workflow_mode)
                except Exception:
                    pass
                result = _postprocess_uploaded_rels(
                    "",
                    chunk,
                    progress_cb=set_direct_progress,
                    workflow_mode=workflow_mode,
                    item_pause_sec=DIRECT_UPLOAD_POSTPROCESS_ITEM_PAUSE_SEC,
                    stop_event=UPLOAD_POSTPROCESS_STOP_EVENT,
                )
                merge_result(result)
                processed_total += int(result.get("received") or len(chunk))
                try:
                    log_event(
                        "direct_upload_postprocess_done",
                        files=result.get("received"),
                        indexed=result.get("indexed"),
                        heic_converted=result.get("heic_converted"),
                        faces_done=result.get("faces_done"),
                        ai_done=result.get("ai_done"),
                        ai_desc_done=result.get("ai_desc_done"),
                    )
                except Exception:
                    pass
                if bool(result.get("stopped")) or UPLOAD_POSTPROCESS_STOP_EVENT.is_set():
                    batch = []
                    more = []
                else:
                    more = _pop_uploaded_rels(state_user)
                if more:
                    batch.extend(more)
                    known_total += len(more)
                state_patch = {
                    "workflow_mode": workflow_mode,
                    "overall_processed": max(0, processed_total),
                    "overall_total": max(known_total, processed_total),
                }
                if batch:
                    state_patch.update({"phase": "starting", "current_rel": None})
                _set_upload_postprocess_state(state_user, state_patch)
                if batch and DIRECT_UPLOAD_POSTPROCESS_BATCH_PAUSE_SEC > 0:
                    time.sleep(DIRECT_UPLOAD_POSTPROCESS_BATCH_PAUSE_SEC)

            _set_upload_postprocess_state(
                state_user,
                {
                    "running": False,
                    "finished_at": now_iso(),
                    "result": aggregate,
                    "error": None,
                    "phase": "stopped" if UPLOAD_POSTPROCESS_STOP_EVENT.is_set() else "done",
                    "workflow_mode": workflow_mode,
                    "process_status": aggregate.get("process_status"),
                    "current_rel": None,
                    "stage_processed": int(aggregate.get("received") or 0),
                    "stage_total": int(aggregate.get("received") or 0),
                    "overall_processed": int(aggregate.get("received") or 0),
                    "overall_total": max(int(aggregate.get("received") or 0), known_total),
                },
            )
        except Exception as e:
            _set_upload_postprocess_state(
                state_user,
                {
                    "running": False,
                    "finished_at": now_iso(),
                    "error": str(e),
                    "result": aggregate,
                    "phase": "error",
                    "workflow_mode": workflow_mode,
                },
            )
            try:
                log_event("error", rel_path="direct_upload_postprocess", error=str(e))
            except Exception:
                pass
        finally:
            with DIRECT_UPLOAD_POSTPROCESS_ACTIVE_LOCK:
                DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS.clear()

    try:
        threading.Thread(target=run, daemon=True).start()
        return True
    except Exception as e:
        with DIRECT_UPLOAD_POSTPROCESS_ACTIVE_LOCK:
            for rel in rels:
                DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS.discard(rel)
        _set_upload_postprocess_state(
            state_user,
            {
                "running": False,
                "finished_at": now_iso(),
                "error": f"Unable to start direct postprocess worker: {e}",
                "result": aggregate,
                "phase": "error",
                "workflow_mode": workflow_mode,
            },
        )
        try:
            log_event("error", rel_path="direct_upload_postprocess", error=f"start: {e}")
        except Exception:
            pass
        return False


def _sync_upload_folder_from_disk(
    folder: Optional[str],
    *,
    recursive: bool = False,
    max_files: Optional[int] = None,
    queue_postprocess: bool = False,
) -> Dict[str, Any]:
    try:
        logical_folder = _normalize_upload_folder_for_disk_sync(folder)
    except Exception:
        return {"ok": False, "error": "invalid_folder", "folder": str(folder or "")}

    def skipped(reason: str) -> Dict[str, Any]:
        return {
            "ok": True,
            "folder": logical_folder,
            "recursive": bool(recursive),
            "skipped": reason,
            "scanned": 0,
            "indexed": 0,
            "discovered": 0,
            "unchanged": 0,
            "pending_uploads": 0,
            "shadowed": 0,
            "postprocess_queued": 0,
            "unsettled": 0,
            "errors": 0,
        }

    if _any_upload_transfer_active():
        return skipped("uploading")

    if float(STOP_ALL_PROCESS_COOLDOWN_UNTIL or 0.0) > time.time():
        return skipped("stopped")

    if _any_regular_upload_postprocess_running():
        return skipped("upload_postprocess")

    cap = int(max_files or UPLOAD_FOLDER_SYNC_MAX_FILES)
    cap = max(1, min(UPLOAD_FOLDER_SYNC_MAX_FILES, cap))
    cache_key = f"{logical_folder}|{'r' if recursive else 'd'}|{cap}"
    now_ts = time.time()
    with UPLOAD_FOLDER_SYNC_LOCK:
        if cache_key in UPLOAD_FOLDER_SYNC_RUNNING:
            return {"ok": True, "folder": logical_folder, "skipped": "running"}
        last_at = float(UPLOAD_FOLDER_SYNC_LAST_AT.get(cache_key, 0.0) or 0.0)
        if UPLOAD_FOLDER_SYNC_TTL_SEC > 0 and (now_ts - last_at) < UPLOAD_FOLDER_SYNC_TTL_SEC:
            return {"ok": True, "folder": logical_folder, "skipped": "recent"}
        UPLOAD_FOLDER_SYNC_RUNNING.add(cache_key)

    discovered_rels: list[str] = []
    postprocess_rels: list[str] = []
    try:
        candidates: list[tuple[Path, str]] = []
        seen_rels: set[str] = set()
        limited = False
        for root, rel_prefix, excluded in _upload_folder_sync_roots(logical_folder):
            for path, rel in _iter_upload_sync_files(root, rel_prefix, recursive=recursive, excluded_top_dirs=excluded):
                if rel in seen_rels:
                    continue
                seen_rels.add(rel)
                candidates.append((path, rel))
                if len(candidates) >= cap:
                    limited = True
                    break
            if limited:
                break

        candidate_count = len(candidates)
        candidates = _dedupe_upload_sync_candidates(candidates)
        existing = _existing_photo_rows_for_rels([rel for _, rel in candidates])
        pending_upload_rels = _pending_upload_rels_snapshot()
        direct_active_rels = _direct_upload_active_rels_snapshot()
        scanned = 0
        indexed = 0
        unchanged = 0
        pending_uploads = 0
        shadowed = max(0, candidate_count - len(candidates))
        unsettled = 0
        errors = 0
        error_samples: list[str] = []

        for path, rel in candidates:
            scanned += 1
            try:
                stat = path.stat()
            except Exception as e:
                errors += 1
                if len(error_samples) < 5:
                    error_samples.append(f"{rel}: {e}")
                continue

            if UPLOAD_FOLDER_SYNC_SETTLE_SEC > 0 and (time.time() - float(stat.st_mtime)) < UPLOAD_FOLDER_SYNC_SETTLE_SEC:
                unsettled += 1
                continue

            prev = existing.get(rel)
            if rel in pending_upload_rels or rel in direct_active_rels:
                pending_uploads += 1
                continue
            if not _photo_row_needs_disk_sync(prev, stat):
                unchanged += 1
                if _upload_rel_needs_postprocess_conversion(rel):
                    postprocess_rels.append(rel)
                continue

            discovered_rels.append(rel)
            if _upload_rel_needs_postprocess_conversion(rel):
                postprocess_rels.append(rel)

        postprocess_queued_count = 0
        if queue_postprocess:
            postprocess_candidates = discovered_rels + postprocess_rels
            if _start_direct_upload_postprocess(postprocess_candidates):
                postprocess_queued_count = len(set(postprocess_candidates))

        try:
            missing_removed = _prune_missing_upload_photos_for_folder(logical_folder, recursive=recursive)
        except Exception:
            missing_removed = {"photos": 0, "faces": 0, "thumbs": 0, "preview_folders": []}

        result: Dict[str, Any] = {
            "ok": True,
            "folder": logical_folder,
            "recursive": bool(recursive),
            "scanned": scanned,
            "indexed": indexed,
            "discovered": len(discovered_rels),
            "unchanged": unchanged,
            "pending_uploads": pending_uploads,
            "shadowed": shadowed,
            "postprocess_queued": postprocess_queued_count,
            "unsettled": unsettled,
            "errors": errors,
            "limited": limited,
            "missing_removed": int(missing_removed.get("photos") or 0),
            "missing_thumbs_removed": int(missing_removed.get("thumbs") or 0),
            "preview_folders": missing_removed.get("preview_folders") or [],
        }
        if error_samples:
            result["error_samples"] = error_samples
        if indexed or discovered_rels or errors or unsettled or pending_uploads or int(missing_removed.get("photos") or 0):
            try:
                log_event("upload_folder_sync_done", **result)
            except Exception:
                pass
        return result
    finally:
        with UPLOAD_FOLDER_SYNC_LOCK:
            UPLOAD_FOLDER_SYNC_RUNNING.discard(cache_key)
            UPLOAD_FOLDER_SYNC_LAST_AT[cache_key] = time.time()


def _normalize_rel_for_view_candidate(value: Any) -> str:
    try:
        rel = str(value or "").replace("\\", "/").lstrip("/").strip()
    except Exception:
        return ""
    if not rel or ".." in rel:
        return ""
    return rel


def _resolve_row_view_rel_path(row_data: Dict[str, Any]) -> str:
    rel = _normalize_rel_for_view_candidate(row_data.get("rel_path") or row_data.get("filename"))
    if not rel:
        return ""

    ext = str((row_data.get("ext") or Path(rel).suffix or "")).strip().lower()
    is_video = ext in VIDEO_EXTS
    metadata = row_data.get("metadata_json") if isinstance(row_data.get("metadata_json"), dict) else {}
    candidates: list[str] = []

    # Prefer explicit conversion targets from metadata when present.
    try:
        conv = metadata.get("conversion") if isinstance(metadata, dict) else None
        if isinstance(conv, dict):
            c = _normalize_rel_for_view_candidate(conv.get("to_rel_path"))
            if c:
                candidates.append(c)
        c2 = _normalize_rel_for_view_candidate(metadata.get("converted_to_rel") if isinstance(metadata, dict) else None)
        if c2:
            candidates.append(c2)
    except Exception:
        pass

    # With upload conversion enabled, prefer browser-friendly converted copies.
    try:
        if (not is_video) and rel.startswith("uploads/") and ext in {".heic", ".heif"} and heic_convert_on_upload_enabled():
            conv_path = _find_existing_converted_for_upload_rel(rel)
            conv_rel = _normalize_rel_for_view_candidate(_upload_path_to_rel(conv_path) if conv_path is not None else "")
            if conv_rel:
                candidates.insert(0, conv_rel)
        if is_video and rel.startswith("uploads/") and ext == ".mov" and mov_convert_on_upload_enabled():
            conv_path = _find_existing_converted_for_upload_rel(rel, extensions=(".mp4",))
            conv_rel = _normalize_rel_for_view_candidate(_upload_path_to_rel(conv_path) if conv_path is not None else "")
            if conv_rel:
                candidates.insert(0, conv_rel)
    except Exception:
        pass

    # Safety net for stale upload rows: if rel_path is missing on disk, try converted mirror.
    try:
        if (not is_video) and rel.startswith("uploads/"):
            src = _disk_path_from_rel_path(rel)
            if not src.exists():
                conv_path = _find_existing_converted_for_upload_rel(rel)
                conv_rel = _normalize_rel_for_view_candidate(_upload_path_to_rel(conv_path) if conv_path is not None else "")
                if conv_rel:
                    candidates.insert(0, conv_rel)
        elif is_video and rel.startswith("uploads/") and ext == ".mov":
            src = _disk_path_from_rel_path(rel)
            if not src.exists():
                conv_path = _find_existing_converted_for_upload_rel(rel, extensions=(".mp4",))
                conv_rel = _normalize_rel_for_view_candidate(_upload_path_to_rel(conv_path) if conv_path is not None else "")
                if conv_rel:
                    candidates.insert(0, conv_rel)
    except Exception:
        pass

    seen: set[str] = set()
    for cand in [*candidates, rel]:
        norm = _normalize_rel_for_view_candidate(cand)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        try:
            if _disk_path_from_rel_path(norm).exists():
                return norm
        except Exception:
            continue
    return rel


def row_to_public(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    for key in ("ai_tags", "ai_desc_tags", "embedding_json", "metadata_json", "exif_json"):
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
        else:
            d[key] = [] if key in {"ai_tags", "ai_desc_tags"} else None
    d["ai_tags"] = _normalize_ai_desc_tags(d.get("ai_tags"), max_tags=64)
    d["ai_desc_tags"] = _normalize_ai_desc_tags(d.get("ai_desc_tags"), max_tags=96)
    if d.get("ai_desc_caption"):
        d["ai_desc_caption"] = _repair_mojibake(str(d.get("ai_desc_caption") or "")).strip()
    else:
        d["ai_desc_caption"] = None
    d["favorite"] = bool(d.get("favorite", 0))
    if d.get("thumb_name"):
        d["thumb_url"] = f"/api/thumbs/{d['thumb_name']}"
    else:
        d["thumb_url"] = None
    # Public URLs:
    # - original_url is what the viewer opens (prefer converted view when available)
    # - download_url remains the row rel_path for direct/original download semantics
    rel = _normalize_rel_for_view_candidate(d.get("rel_path") or d.get("filename"))
    view_rel = _resolve_row_view_rel_path(d)
    if rel:
        try:
            d["original_url"] = f"/api/viewable/{quote(view_rel or rel)}"
            d["download_url"] = f"/api/original/{quote(rel)}"
        except Exception:
            d["original_url"] = None
            d["download_url"] = None
    else:
        d["original_url"] = None
        d["download_url"] = None
    # Annotate media type
    try:
        ext = (d.get("ext") or "").lower()
        d["is_video"] = ext in VIDEO_EXTS
    except Exception:
        d["is_video"] = False
    # Friendly device and lens labels
    try:
        make = (d.get("camera_make") or "").strip()
        model = (d.get("camera_model") or "").strip()
        dev_label = " ".join([x for x in [make, model] if x]).strip()
        d["device_label"] = dev_label if dev_label else None
        lens = (d.get("lens_model") or "").strip()
        if lens and dev_label:
            # remove occurrences of device make/model in lens text (case-insensitive)
            lm = lens
            for s in {make, model, dev_label}:
                if s:
                    try:
                        lm = re.sub(re.escape(s), "", lm, flags=re.IGNORECASE)
                    except re.error:
                        pass
            lm = re.sub(r"\s{2,}", " ", lm).strip(" -,")
            d["lens_label"] = lm if lm else lens
        else:
            d["lens_label"] = lens or None
    except Exception:
        d["device_label"] = (d.get("camera_model") or d.get("camera_make"))
        d["lens_label"] = d.get("lens_model")
    return d


def _row_to_share_public(row: sqlite3.Row, token: str) -> Dict[str, Any]:
    d = row_to_public(row)
    pid = int(d.get("id") or 0)
    if pid > 0:
        d["thumb_url"] = url_for("api_share_thumb", token=token, photo_id=pid)
        d["original_url"] = url_for("api_share_viewable", token=token, photo_id=pid)
        d["download_url"] = url_for("api_share_original", token=token, photo_id=pid)
    return d


@app.route("/api/people")
def api_people_list():
    """List people with face counts and a sample thumbnail."""
    include_hidden = request.args.get("include_hidden") in {"1", "true", "True"}
    with closing(get_conn()) as conn:
        acl_prefixes = _current_user_acl_prefixes(conn)
        def _person_count(item: Dict[str, Any]) -> int:
            try:
                return max(0, int((item or {}).get("count") or 0))
            except Exception:
                return 0

        def _is_unknown_bucket(item: Dict[str, Any]) -> bool:
            if str((item or {}).get("id") or "").strip().lower() == "unknown":
                return True
            nm = str((item or {}).get("name") or "").strip().lower()
            return nm.startswith("ukendt") or nm.startswith("unknown")

        where = "" if include_hidden else "WHERE COALESCE(p.hidden,0)=0"
        rows = conn.execute(
            f"""
            SELECT p.id, p.name, COALESCE(p.hidden,0) AS hidden
            FROM people p
            {where}
            ORDER BY
              CASE WHEN LOWER(p.name) LIKE 'ukendt%' OR LOWER(p.name) LIKE 'unknown%'
                   THEN 1 ELSE 0 END,
              p.name COLLATE NOCASE ASC
            """
        ).fetchall()
        people = []
        for r in rows:
            pid = int(r["id"])
            name = r["name"]
            hidden = bool(int(r["hidden"] or 0))

            if acl_prefixes is None:
                cnt_row = conn.execute("SELECT COUNT(*) AS c FROM faces WHERE person_id=?", (pid,)).fetchone()
                cnt = int(cnt_row["c"] or 0) if cnt_row else 0
                face_row = conn.execute(
                    """
                    SELECT f.id
                    FROM faces f
                    LEFT JOIN photos ph ON ph.id = f.photo_id
                    WHERE f.person_id=?
                    ORDER BY CASE WHEN COALESCE(f.confidence, 0) >= 0.70 THEN 1 ELSE 0 END DESC,
                            CASE WHEN f.frame_sec IS NOT NULL THEN 1 ELSE 0 END DESC,
                             CASE
                               WHEN COALESCE(ph.width,0) > 0 AND COALESCE(ph.height,0) > 0
                                    AND (1.0 * COALESCE(f.bbox_w,0) * COALESCE(f.bbox_h,0)) / (1.0 * ph.width * ph.height) BETWEEN 0.02 AND 0.45
                               THEN 1 ELSE 0
                             END DESC,
                             CASE WHEN COALESCE(f.bbox_w,0) >= 72 AND COALESCE(f.bbox_h,0) >= 72 THEN 1 ELSE 0 END DESC,
                             CASE
                               WHEN COALESCE(f.bbox_h,0) > 0
                                    AND (1.0 * COALESCE(f.bbox_w,0) / COALESCE(f.bbox_h,1)) BETWEEN 0.55 AND 1.90
                               THEN 1 ELSE 0
                             END DESC,
                             COALESCE(f.confidence, 0) DESC,
                             (COALESCE(f.bbox_w, 0) * COALESCE(f.bbox_h, 0)) DESC,
                             f.id DESC
                    LIMIT 1
                    """,
                    (pid,),
                ).fetchone()
            else:
                clauses = []
                params: list[Any] = [pid]
                for pref in acl_prefixes:
                    clauses.append("(ph.rel_path=? OR ph.rel_path LIKE ?)")
                    params.extend([pref, pref + "/%"])
                where_acl = " OR ".join(clauses) if clauses else "0=1"
                cnt_row = conn.execute(
                    f"""
                    SELECT COUNT(*) AS c
                    FROM faces f
                    INNER JOIN photos ph ON ph.id = f.photo_id
                    WHERE f.person_id=? AND ({where_acl})
                    """,
                    params,
                ).fetchone()
                cnt = int(cnt_row["c"] or 0) if cnt_row else 0
                face_row = conn.execute(
                    f"""
                    SELECT f.id
                    FROM faces f
                    INNER JOIN photos ph ON ph.id = f.photo_id
                    WHERE f.person_id=? AND ({where_acl})
                    ORDER BY CASE WHEN COALESCE(f.confidence, 0) >= 0.70 THEN 1 ELSE 0 END DESC,
                            CASE WHEN f.frame_sec IS NOT NULL THEN 1 ELSE 0 END DESC,
                             CASE
                               WHEN COALESCE(ph.width,0) > 0 AND COALESCE(ph.height,0) > 0
                                    AND (1.0 * COALESCE(f.bbox_w,0) * COALESCE(f.bbox_h,0)) / (1.0 * ph.width * ph.height) BETWEEN 0.02 AND 0.45
                               THEN 1 ELSE 0
                             END DESC,
                             CASE WHEN COALESCE(f.bbox_w,0) >= 72 AND COALESCE(f.bbox_h,0) >= 72 THEN 1 ELSE 0 END DESC,
                             CASE
                               WHEN COALESCE(f.bbox_h,0) > 0
                                    AND (1.0 * COALESCE(f.bbox_w,0) / COALESCE(f.bbox_h,1)) BETWEEN 0.55 AND 1.90
                               THEN 1 ELSE 0
                             END DESC,
                             COALESCE(f.confidence, 0) DESC,
                             (COALESCE(f.bbox_w, 0) * COALESCE(f.bbox_h, 0)) DESC,
                             f.id DESC
                    LIMIT 1
                    """,
                    params,
                ).fetchone()

            thumb_url = f"/api/face-thumb/{int(face_row['id'])}" if face_row else None
            if face_row:
                try:
                    _enqueue_face_thumb_generation(int(face_row["id"]))
                except Exception:
                    pass
            if cnt > 0:
                people.append({"id": pid, "name": name, "count": cnt, "thumb_url": thumb_url, "hidden": hidden})

        if acl_prefixes is None:
            unk = conn.execute(
                "SELECT COUNT(DISTINCT photo_id) AS c FROM faces WHERE person_id IS NULL"
            ).fetchone()
            unk_count = int(unk["c"] or 0) if unk else 0
            frow = conn.execute(
                """
                SELECT f.id
                FROM faces f
                LEFT JOIN photos ph ON ph.id = f.photo_id
                WHERE f.person_id IS NULL
                ORDER BY CASE WHEN COALESCE(f.confidence, 0) >= 0.70 THEN 1 ELSE 0 END DESC,
                        CASE WHEN f.frame_sec IS NOT NULL THEN 1 ELSE 0 END DESC,
                         CASE
                           WHEN COALESCE(ph.width,0) > 0 AND COALESCE(ph.height,0) > 0
                                AND (1.0 * COALESCE(f.bbox_w,0) * COALESCE(f.bbox_h,0)) / (1.0 * ph.width * ph.height) BETWEEN 0.02 AND 0.45
                           THEN 1 ELSE 0
                         END DESC,
                         CASE WHEN COALESCE(f.bbox_w,0) >= 72 AND COALESCE(f.bbox_h,0) >= 72 THEN 1 ELSE 0 END DESC,
                         CASE
                           WHEN COALESCE(f.bbox_h,0) > 0
                                AND (1.0 * COALESCE(f.bbox_w,0) / COALESCE(f.bbox_h,1)) BETWEEN 0.55 AND 1.90
                           THEN 1 ELSE 0
                         END DESC,
                         COALESCE(f.confidence, 0) DESC,
                         (COALESCE(f.bbox_w, 0) * COALESCE(f.bbox_h, 0)) DESC,
                         f.id DESC
                LIMIT 1
                """
            ).fetchone()
        else:
            clauses = []
            params2: list[Any] = []
            for pref in acl_prefixes:
                clauses.append("(ph.rel_path=? OR ph.rel_path LIKE ?)")
                params2.extend([pref, pref + "/%"])
            where_acl = " OR ".join(clauses) if clauses else "0=1"
            unk = conn.execute(
                f"""
                SELECT COUNT(DISTINCT f.photo_id) AS c
                FROM faces f
                INNER JOIN photos ph ON ph.id = f.photo_id
                WHERE f.person_id IS NULL AND ({where_acl})
                """,
                params2,
            ).fetchone()
            unk_count = int(unk["c"] or 0) if unk else 0
            frow = conn.execute(
                f"""
                SELECT f.id
                FROM faces f
                INNER JOIN photos ph ON ph.id = f.photo_id
                WHERE f.person_id IS NULL AND ({where_acl})
                ORDER BY CASE WHEN COALESCE(f.confidence, 0) >= 0.70 THEN 1 ELSE 0 END DESC,
                        CASE WHEN f.frame_sec IS NOT NULL THEN 1 ELSE 0 END DESC,
                         CASE
                           WHEN COALESCE(ph.width,0) > 0 AND COALESCE(ph.height,0) > 0
                                AND (1.0 * COALESCE(f.bbox_w,0) * COALESCE(f.bbox_h,0)) / (1.0 * ph.width * ph.height) BETWEEN 0.02 AND 0.45
                           THEN 1 ELSE 0
                         END DESC,
                         CASE WHEN COALESCE(f.bbox_w,0) >= 72 AND COALESCE(f.bbox_h,0) >= 72 THEN 1 ELSE 0 END DESC,
                         CASE
                           WHEN COALESCE(f.bbox_h,0) > 0
                                AND (1.0 * COALESCE(f.bbox_w,0) / COALESCE(f.bbox_h,1)) BETWEEN 0.55 AND 1.90
                           THEN 1 ELSE 0
                         END DESC,
                         COALESCE(f.confidence, 0) DESC,
                         (COALESCE(f.bbox_w, 0) * COALESCE(f.bbox_h, 0)) DESC,
                         f.id DESC
                LIMIT 1
                """,
                params2,
            ).fetchone()

        if unk_count > 0:
            thumb_url = f"/api/face-thumb/{int(frow['id'])}" if frow else None
            if frow:
                try:
                    _enqueue_face_thumb_generation(int(frow["id"]))
                except Exception:
                    pass
            people.append({"id": "unknown", "name": "Ukendte", "count": unk_count, "thumb_url": thumb_url})

        # Suggest likely existing person names for auto-unknown buckets.
        # These remain unknown until user confirms (manual merge/rename).
        try:
            person_items_by_id: Dict[int, Dict[str, Any]] = {}
            person_ids: list[int] = []
            for item in people:
                try:
                    pid_i = int((item or {}).get("id"))
                except Exception:
                    continue
                person_items_by_id[pid_i] = item
                person_ids.append(pid_i)

            if person_ids:
                placeholders = ",".join("?" for _ in person_ids)
                crows = conn.execute(
                    f"SELECT id, centroid_json FROM people WHERE id IN ({placeholders})",
                    person_ids,
                ).fetchall()

                centroid_by_id: Dict[int, list[float]] = {}
                for cr in crows:
                    try:
                        pid_i = int(cr["id"])
                        raw_c = json.loads(cr["centroid_json"]) if cr["centroid_json"] else None
                        if isinstance(raw_c, list) and raw_c:
                            centroid_by_id[pid_i] = [float(x or 0.0) for x in raw_c]
                    except Exception:
                        continue

                known_pool: list[tuple[int, str, list[float]]] = []
                unknown_targets: list[int] = []
                for pid_i, item in person_items_by_id.items():
                    cvec = centroid_by_id.get(pid_i)
                    if not cvec:
                        continue
                    name_i = str((item or {}).get("name") or "")
                    if _is_unknown_bucket(item):
                        unknown_targets.append(pid_i)
                    else:
                        known_pool.append((pid_i, name_i, cvec))

                if known_pool and unknown_targets and FACE_MAYBE_THRESHOLD < FACE_MATCH_THRESHOLD_CENTROID:
                    for upid in unknown_targets:
                        uvec = centroid_by_id.get(upid)
                        if not uvec:
                            continue
                        best_pid: Optional[int] = None
                        best_name = ""
                        best_score = -1.0
                        for kpid, kname, kvec in known_pool:
                            sc = _cosine(uvec, kvec)
                            if sc > best_score:
                                best_score = sc
                                best_pid = kpid
                                best_name = kname

                        if (
                            best_pid is not None
                            and best_name
                            and best_score >= FACE_MAYBE_THRESHOLD
                            and best_score < FACE_MATCH_THRESHOLD_CENTROID
                        ):
                            target = person_items_by_id.get(upid)
                            if target is not None:
                                target["maybe_person_id"] = int(best_pid)
                                target["maybe_person_name"] = str(best_name)
                                target["maybe_score"] = round(float(best_score), 4)
        except Exception:
            pass

        people.sort(
            key=lambda item: (
                1 if _is_unknown_bucket(item) else 0,
                -_person_count(item),
                str((item or {}).get("name") or "").casefold(),
            )
        )
    return jsonify({"ok": True, "items": people})


@app.route("/api/people/<int:pid>/train", methods=["POST"])
def api_people_train_one(pid: int):
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    try:
        with closing(get_conn()) as conn:
            person = conn.execute("SELECT id FROM people WHERE id=?", (pid,)).fetchone()
            if not person:
                return jsonify({"ok": False, "error": "Person not found"}), 404
            result = _recompute_person_centroid(conn, pid)
        return jsonify(result), (200 if result.get("ok") else 500)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/people/train", methods=["POST"])
def api_people_train_all():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    out = {"ok": True, "trained": 0}
    try:
        with closing(get_conn()) as conn:
            rows = conn.execute("SELECT id FROM people").fetchall()
            for r in rows:
                pid = int(r["id"]) if r and r["id"] is not None else None
                if pid is None:
                    continue
                res = _recompute_person_centroid(conn, pid)
                if res.get("ok"):
                    out["trained"] += 1
        return jsonify(out)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/faces/match-unknown", methods=["POST"])
def api_faces_match_unknown():
    """Try to match previously unknown faces (person_id IS NULL) against known person centroids."""
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    body = request.get_json(silent=True) or {}
    try:
        limit_val = body.get("limit")
        limit = int(limit_val) if (limit_val is not None) else None
    except Exception:
        limit = None
    scanned = 0
    matched = 0
    try:
        with closing(get_conn()) as conn:
            # Ensure centroids ready
            cents = _load_person_centroids(conn)
            if not cents:
                return jsonify({"ok": True, "scanned": 0, "matched": 0})
            # Load unknown faces
            sql = "SELECT id, embedding_json FROM faces WHERE person_id IS NULL AND embedding_json IS NOT NULL"
            if isinstance(limit, int) and limit > 0:
                sql += f" LIMIT {int(limit)}"
            rows = conn.execute(sql).fetchall()
            for r in rows:
                try:
                    fid = int(r["id"]) if r and r["id"] is not None else None
                    if fid is None:
                        continue
                    try:
                        vec = json.loads(r["embedding_json"]) if r["embedding_json"] else None
                    except Exception:
                        vec = None
                    if not (isinstance(vec, list) and vec):
                        continue
                    scanned += 1
                    # Find best centroid match
                    best_pid = None
                    best_sc = -1.0
                    for pid, cvec in cents:
                        sc = _cosine(vec, cvec)
                        if sc > best_sc:
                            best_sc = sc
                            best_pid = pid
                    if best_pid is not None and best_sc >= FACE_MATCH_THRESHOLD_CENTROID:
                        try:
                            conn.execute("UPDATE faces SET person_id=? WHERE id=?", (int(best_pid), fid))
                            matched += 1
                        except Exception:
                            pass
                except Exception:
                    # Ignore malformed rows and continue matching others
                    pass
            try:
                conn.commit()
            except Exception:
                pass
        return jsonify({"ok": True, "scanned": scanned, "matched": matched})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/people/<int:pid>/hide", methods=["POST"])
def api_people_hide(pid: int):
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    try:
        data = request.get_json(silent=True) or {}
        val = data.get("hidden")
        hidden = 1 if (val in (1, True, "1", "true", "True", None)) else 0
        with closing(get_conn()) as conn:
            conn.execute("UPDATE people SET hidden=? WHERE id=?", (hidden, pid))
            conn.commit()
        return jsonify({"ok": True, "id": pid, "hidden": bool(hidden)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/people/<int:pid>/photos")
def api_people_photos(pid: int):
    """List photos that include a given person id."""
    items: list[Dict[str, Any]] = []
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT p.*
            FROM photos p
            INNER JOIN faces f ON f.photo_id = p.id
            WHERE f.person_id = ?
            ORDER BY COALESCE(p.captured_at, p.modified_fs, p.created_fs) DESC
            """,
            (pid,),
        ).fetchall()
        for r in rows:
            if _is_rel_path_allowed_for_current_user(r["rel_path"], conn):
                items.append(row_to_public(r))
    return jsonify({"ok": True, "items": items})


@app.route("/api/people/unknown/photos-faces")
def api_people_unknown_photos_faces():
    items: list[Dict[str, Any]] = []
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT p.*, f.id as face_id, f.bbox_x, f.bbox_y, f.bbox_w, f.bbox_h
            FROM photos p
            INNER JOIN faces f ON f.photo_id = p.id
            WHERE f.person_id IS NULL
            ORDER BY COALESCE(p.captured_at, p.modified_fs, p.created_fs) DESC, f.id DESC
            """
        ).fetchall()
        # Group faces per photo
        by_photo: Dict[int, Dict[str, Any]] = {}
        for r in rows:
            if not _is_rel_path_allowed_for_current_user(r["rel_path"], conn):
                continue
            pid_ = int(r["id"])  # photo id
            if pid_ not in by_photo:
                by_photo[pid_] = row_to_public(r)
                by_photo[pid_]["faces"] = []
            try:
                w = float(r["width"] or 0) or 1.0
                h = float(r["height"] or 0) or 1.0
            except Exception:
                w, h = 1.0, 1.0
            x = max(0.0, float(r["bbox_x"] or 0) / w)
            y = max(0.0, float(r["bbox_y"] or 0) / h)
            bw = max(0.0, float(r["bbox_w"] or 0) / w)
            bh = max(0.0, float(r["bbox_h"] or 0) / h)
            by_photo[pid_]["faces"].append({"x": x, "y": y, "w": bw, "h": bh, "id": int(r["face_id"])})
    items = list(by_photo.values())
    return jsonify({"ok": True, "items": items})


@app.route("/api/face-thumb/<int:face_id>")
def api_face_thumb(face_id: int):
    # Serve cached face thumbnail; if missing/stale, queue background generation and return a lightweight placeholder.
    try:
        with closing(get_conn()) as conn:
            r = conn.execute(
                "SELECT f.bbox_x, f.bbox_y, f.bbox_w, f.bbox_h, p.rel_path, p.thumb_name FROM faces f INNER JOIN photos p ON p.id = f.photo_id WHERE f.id=?",
                (face_id,),
            ).fetchone()
        if not r:
            return ("Not found", 404)
        src_rel = r["rel_path"]
        if not _is_rel_path_allowed_for_current_user(src_rel):
            return ("Forbidden", 403)

        out_name = _face_thumb_name(face_id)
        out_path = THUMB_DIR / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        src_path = (UPLOAD_DIR / src_rel.split("/", 1)[1]) if src_rel.startswith("uploads/") else (PHOTO_DIR / src_rel)
        view_path = ensure_viewable_copy(src_path, src_rel)
        source_mtime = 0.0
        try:
            source_mtime = float(view_path.stat().st_mtime)
        except Exception:
            source_mtime = 0.0

        is_ready = False
        try:
            is_ready = out_path.exists() and (out_path.stat().st_mtime >= source_mtime)
        except Exception:
            is_ready = False

        if is_ready:
            resp = send_from_directory(str(THUMB_DIR), out_name)
            resp.headers["Cache-Control"] = "no-store"
            return resp

        _enqueue_face_thumb_generation(face_id)

        # Never build synchronously here: many concurrent requests can spike memory/CPU.
        # Background worker will create the face thumb; until then return a tiny placeholder.
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'>"
            "<rect width='64' height='64' fill='#1a2233'/>"
            "<circle cx='32' cy='24' r='12' fill='#8aa0c8'/>"
            "<rect x='14' y='40' width='36' height='16' rx='8' fill='#8aa0c8'/>"
            "</svg>"
        )
        resp = make_response(svg, 200)
        resp.headers["Content-Type"] = "image/svg+xml"
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        return (str(e), 500)


_face_thumb_queue: "queue.Queue[int]" = queue.Queue()
_face_thumb_worker_started = False
_face_thumb_lock = threading.Lock()
_face_thumb_queued: set[int] = set()

# HEIC bulk conversion worker
heic_convert_thread = None
last_heic_convert_result: Optional[Dict[str, Any]] = None
heic_convert_progress: Dict[str, Any] = {"total": 0, "processed": 0, "errors": 0}
mov_convert_thread = None
last_mov_convert_result: Optional[Dict[str, Any]] = None
mov_convert_progress: Dict[str, Any] = {"total": 0, "processed": 0, "errors": 0}


def _face_thumb_name(face_id: int) -> str:
    return f"face_{int(face_id)}_v{int(FACE_THUMB_VERSION)}.jpg"


def _build_face_thumb(face_id: int) -> bool:
    try:
        with closing(get_conn()) as conn:
            r = conn.execute(
                "SELECT f.bbox_x, f.bbox_y, f.bbox_w, f.bbox_h, f.embedding_json, f.frame_sec, p.id AS photo_id, p.rel_path, p.thumb_name, p.width AS src_w, p.height AS src_h FROM faces f INNER JOIN photos p ON p.id = f.photo_id WHERE f.id=?",
                (face_id,),
            ).fetchone()
        if not r:
            return False
        src_rel = r["rel_path"]
        src_path = (UPLOAD_DIR / src_rel.split("/", 1)[1]) if src_rel.startswith("uploads/") else (PHOTO_DIR / src_rel)
        view_path = ensure_viewable_copy(src_path, src_rel)

        out_name = _face_thumb_name(face_id)
        out_path = THUMB_DIR / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        needs_build = True
        try:
            needs_build = (not out_path.exists()) or (view_path.stat().st_mtime > out_path.stat().st_mtime)
        except Exception:
            needs_build = True

        if not needs_build:
            return True

        def _crop_and_save(img: Image.Image, bx: int, by: int, bw: int, bh: int) -> bool:
            try:
                im = img.convert("RGB")
                iw = max(1, int(im.width))
                ih = max(1, int(im.height))

                x = int(bx or 0)
                y = int(by or 0)
                w = max(1, int(bw or 1))
                h = max(1, int(bh or 1))

                # Clamp bbox to image bounds first.
                x1 = max(0, min(iw - 1, x))
                y1 = max(0, min(ih - 1, y))
                x2 = max(x1 + 1, min(iw, x1 + w))
                y2 = max(y1 + 1, min(ih, y1 + h))

                # Expand around face center with context while staying inside bounds.
                fw = max(1, x2 - x1)
                fh = max(1, y2 - y1)
                pad = int(max(fw, fh) * 0.30)
                cx1 = max(0, x1 - pad)
                cy1 = max(0, y1 - pad)
                cx2 = min(iw, x2 + pad)
                cy2 = min(ih, y2 + pad)

                if cx2 <= cx1 or cy2 <= cy1:
                    side = max(1, min(iw, ih))
                    left = max(0, (iw - side) // 2)
                    top = max(0, (ih - side) // 2)
                    cx1, cy1, cx2, cy2 = left, top, min(iw, left + side), min(ih, top + side)

                crop = im.crop((cx1, cy1, cx2, cy2))
                crop.thumbnail((300, 300))
                crop.save(out_path, format="JPEG", quality=90, optimize=True)
                return True
            except Exception:
                return False

        def _save_full_thumb(img: Image.Image) -> bool:
            try:
                im = img.convert("RGB")
                try:
                    im = ImageOps.exif_transpose(im)
                except Exception:
                    pass
                im.thumbnail((300, 300))
                im.save(out_path, format="JPEG", quality=90, optimize=True)
                return True
            except Exception:
                return False

        if Path(src_rel).suffix.lower() in VIDEO_EXTS:
            bbox_x = int(r["bbox_x"] or 0)
            bbox_y = int(r["bbox_y"] or 0)
            bbox_w = int(r["bbox_w"] or 1)
            bbox_h = int(r["bbox_h"] or 1)
            bbox_is_usable = bbox_w > 2 and bbox_h > 2

            target_emb: list[float] = []
            try:
                raw_emb = json.loads(r["embedding_json"]) if r["embedding_json"] else []
                if isinstance(raw_emb, list) and raw_emb:
                    target_emb = [float(x or 0.0) for x in raw_emb]
            except Exception:
                target_emb = []

            frame_cache: Dict[float, Optional[bytes]] = {}
            detect_cache: Dict[float, list[Dict[str, Any]]] = {}

            def _frame_bytes_for(sec: float) -> Optional[bytes]:
                s = round(max(0.0, float(sec or 0.0)), 3)
                if s not in frame_cache:
                    frame_cache[s] = _extract_video_frame_bytes(src_path, src_rel, s)
                return frame_cache[s]

            def _detected_faces_for(sec: float) -> list[Dict[str, Any]]:
                s = round(max(0.0, float(sec or 0.0)), 3)
                if s in detect_cache:
                    return detect_cache[s]
                frame_bytes = _frame_bytes_for(s)
                if not frame_bytes:
                    detect_cache[s] = []
                    return []
                faces_raw = _ai_detect_faces_bytes(frame_bytes, filename=f"{Path(src_rel).stem}_thumb_{s:.2f}.jpg") or []
                faces_norm: list[Dict[str, Any]] = []
                for fc in faces_raw:
                    if isinstance(fc, dict):
                        faces_norm.append(fc)
                detect_cache[s] = faces_norm
                return faces_norm

            def _pick_best_detected_bbox(faces_here: list[Dict[str, Any]]) -> Optional[tuple[int, int, int, int]]:
                best_bbox: Optional[tuple[int, int, int, int]] = None
                best_score = -10_000.0
                best_sim = -10_000.0
                for fc in faces_here:
                    bbox_fc = fc.get("bbox") or [0, 0, 0, 0]
                    try:
                        x1, y1, x2, y2 = [int(round(float(v))) for v in bbox_fc[:4]]
                        bw_fc = max(1, x2 - x1)
                        bh_fc = max(1, y2 - y1)
                    except Exception:
                        continue

                    conf = float(fc.get("confidence") or 0.0)
                    sim = -10_000.0
                    if target_emb:
                        emb_fc = fc.get("embedding") or []
                        if isinstance(emb_fc, list) and emb_fc:
                            try:
                                sim = _cosine(target_emb, [float(x or 0.0) for x in emb_fc])
                            except Exception:
                                sim = -10_000.0

                    score = conf * 0.2
                    if target_emb:
                        if sim > -5_000.0:
                            score += (sim * 2.0)
                        else:
                            score -= 0.25
                    else:
                        score += conf

                    if score > best_score:
                        best_score = score
                        best_sim = sim
                        best_bbox = (x1, y1, bw_fc, bh_fc)

                if not best_bbox:
                    return None

                # If we have target embedding and multiple candidates, require
                # at least a weak similarity before trusting detector match.
                if target_emb and len(faces_here) > 1 and best_sim < 0.18:
                    return None

                return best_bbox

            frame_sec: Optional[float] = None
            try:
                if r["frame_sec"] is not None:
                    frame_sec = max(0.0, float(r["frame_sec"]))
            except Exception:
                frame_sec = None

            base_sec = frame_sec if frame_sec is not None else max(0.0, VIDEO_FACE_SAMPLE_START_SEC)
            sec_candidates: list[float] = []
            _seen_secs: set[float] = set()
            for sec_raw in [base_sec, base_sec - 0.25, base_sec + 0.25, base_sec + 0.90]:
                sec_val = round(max(0.0, float(sec_raw or 0.0)), 3)
                if sec_val in _seen_secs:
                    continue
                _seen_secs.add(sec_val)
                sec_candidates.append(sec_val)

            # Prefer detector-assisted crop in sampled frames and match by
            # embedding, so we hit the same person even if stored bbox is stale
            # or was generated in another frame scale.
            for sec in sec_candidates:
                frame_bytes = _frame_bytes_for(sec)
                if not frame_bytes:
                    continue
                faces_here = _detected_faces_for(sec)
                bbox_match = _pick_best_detected_bbox(faces_here)
                if not bbox_match:
                    continue
                try:
                    x_fc, y_fc, bw_fc, bh_fc = bbox_match
                    with Image.open(io.BytesIO(frame_bytes)) as im_src:
                        if _crop_and_save(im_src, x_fc, y_fc, bw_fc, bh_fc):
                            return True
                except Exception:
                    continue

            if bbox_is_usable:
                for sec in sec_candidates:
                    frame_bytes = _frame_bytes_for(sec)
                    if not frame_bytes:
                        continue
                    try:
                        with Image.open(io.BytesIO(frame_bytes)) as im_src:
                            if _crop_and_save(im_src, bbox_x, bbox_y, bbox_w, bbox_h):
                                return True
                    except Exception:
                        continue

            # For legacy rows without frame_sec, try cropping from the cached
            # video thumbnail by scaling bbox from source dimensions.
            thumb_name = re.sub(r"[^a-zA-Z0-9._-]", "", str(r["thumb_name"] or ""))
            if thumb_name:
                thumb_path = THUMB_DIR / thumb_name
                if thumb_path.exists():
                    try:
                        with Image.open(thumb_path) as im_thumb:
                            if bbox_is_usable:
                                try:
                                    src_w = int(r["src_w"] or 0)
                                    src_h = int(r["src_h"] or 0)
                                except Exception:
                                    src_w, src_h = 0, 0
                                if src_w > 0 and src_h > 0:
                                    sx = float(im_thumb.width) / float(src_w)
                                    sy = float(im_thumb.height) / float(src_h)
                                    scaled_x = int(round(bbox_x * sx))
                                    scaled_y = int(round(bbox_y * sy))
                                    scaled_w = max(1, int(round(bbox_w * sx)))
                                    scaled_h = max(1, int(round(bbox_h * sy)))
                                    if _crop_and_save(im_thumb, scaled_x, scaled_y, scaled_w, scaled_h):
                                        return True
                    except Exception:
                        pass

            if thumb_name:
                thumb_path = THUMB_DIR / thumb_name
                if thumb_path.exists():
                    try:
                        with Image.open(thumb_path) as im_thumb:
                            if _save_full_thumb(im_thumb):
                                return True
                    except Exception:
                        pass

            for sec in sec_candidates:
                frame_bytes = _frame_bytes_for(sec)
                if not frame_bytes:
                    continue
                try:
                    with Image.open(io.BytesIO(frame_bytes)) as im_src:
                        if _save_full_thumb(im_src):
                            return True
                except Exception:
                    continue
            return False

        # First attempt: crop from original/viewable source.
        try:
            # IMPORTANT:
            # Face bbox coordinates are produced by ai_service/app.py using
            # Image.open(...).convert("RGB") without EXIF transpose.
            # So crop in the same pixel space (no exif_transpose here), otherwise
            # some rotated images get wrong crops.
            with Image.open(view_path) as im_src:
                if _crop_and_save(
                    im_src,
                    int(r["bbox_x"] or 0),
                    int(r["bbox_y"] or 0),
                    int(r["bbox_w"] or 1),
                    int(r["bbox_h"] or 1),
                ):
                    return True
        except Exception:
            pass

        return False
    except Exception as e:
        try:
            log_event("error", error=f"face_thumb_bg: {e}", face_id=face_id)
        except Exception:
            pass
        return False


def _face_thumb_worker_loop() -> None:
    while True:
        try:
            face_id = int(_face_thumb_queue.get())
        except Exception:
            continue
        try:
            _build_face_thumb(face_id)
        finally:
            with _face_thumb_lock:
                _face_thumb_queued.discard(face_id)
            _face_thumb_queue.task_done()


def _ensure_face_thumb_worker() -> None:
    global _face_thumb_worker_started
    if _face_thumb_worker_started:
        return
    with _face_thumb_lock:
        if _face_thumb_worker_started:
            return
        threading.Thread(target=_face_thumb_worker_loop, daemon=True).start()
        _face_thumb_worker_started = True


def _enqueue_face_thumb_generation(face_id: int) -> None:
    _ensure_face_thumb_worker()
    with _face_thumb_lock:
        if face_id in _face_thumb_queued:
            return
        _face_thumb_queued.add(face_id)
    _face_thumb_queue.put(face_id)


@app.route("/api/face-thumb/status/<int:face_id>")
def api_face_thumb_status(face_id: int):
    """Lightweight readiness check for a face thumbnail.
    Returns {ready: bool, url: str, v: int} where url contains a cache-busting
    version param based on mtime when ready.
    """
    try:
        with closing(get_conn()) as conn:
            r = conn.execute(
                "SELECT f.bbox_x, f.bbox_y, f.bbox_w, f.bbox_h, p.rel_path, p.thumb_name FROM faces f INNER JOIN photos p ON p.id = f.photo_id WHERE f.id=?",
                (face_id,),
            ).fetchone()
        if not r:
            return jsonify({"ok": False, "ready": False, "error": "not_found"}), 404
        src_rel = r["rel_path"]
        if not _is_rel_path_allowed_for_current_user(src_rel):
            return jsonify({"ok": False, "ready": False, "error": "forbidden"}), 403

        out_name = _face_thumb_name(face_id)
        out_path = THUMB_DIR / out_name
        src_path = (UPLOAD_DIR / src_rel.split("/", 1)[1]) if src_rel.startswith("uploads/") else (PHOTO_DIR / src_rel)
        view_path = ensure_viewable_copy(src_path, src_rel)
        try:
            source_mtime = float(view_path.stat().st_mtime)
        except Exception:
            source_mtime = 0.0
        ready = False
        ver = 0
        try:
            ready = out_path.exists() and (out_path.stat().st_mtime >= source_mtime)
            if ready:
                ver = int(out_path.stat().st_mtime)
        except Exception:
            ready = False
        if not ready:
            _enqueue_face_thumb_generation(face_id)
        url = f"/api/face-thumb/{face_id}" + (f"?v={ver}" if ver else "")
        return jsonify({"ok": True, "ready": bool(ready), "url": url, "v": ver})
    except Exception as e:
        return jsonify({"ok": False, "ready": False, "error": str(e)}), 500


@app.route("/api/people/unknown/photos")
def api_people_unknown_photos():
    items: list[Dict[str, Any]] = []
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT p.*
            FROM photos p
            INNER JOIN faces f ON f.photo_id = p.id
            WHERE f.person_id IS NULL
            ORDER BY COALESCE(p.captured_at, p.modified_fs, p.created_fs) DESC
            """
        ).fetchall()
        for r in rows:
            if _is_rel_path_allowed_for_current_user(r["rel_path"], conn):
                items.append(row_to_public(r))
    return jsonify({"ok": True, "items": items})


@app.route("/api/people/<int:pid>/rename", methods=["POST"])
def api_people_rename(pid: int):
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    if not new_name:
        return jsonify({"ok": False, "error": "Missing name"}), 400
    try:
        with closing(get_conn()) as conn:
            src = conn.execute("SELECT id, name FROM people WHERE id=?", (pid,)).fetchone()
            if not src:
                return jsonify({"ok": False, "error": "Person not found"}), 404

            existing = conn.execute("SELECT id, name FROM people WHERE LOWER(name)=LOWER(?)", (new_name,)).fetchone()
            if existing and int(existing["id"]) != int(pid):
                target_id = int(existing["id"])
                conn.execute("UPDATE faces SET person_id=? WHERE person_id=?", (target_id, pid))
                conn.execute("DELETE FROM people WHERE id=?", (pid,))
                conn.commit()
                # Recompute centroid for target person after merge
                try:
                    _recompute_person_centroid(conn, target_id)
                except Exception:
                    pass
                return jsonify({
                    "ok": True,
                    "merged": True,
                    "from_id": pid,
                    "to_id": target_id,
                    "name": str(existing["name"] or new_name),
                })

            conn.execute("UPDATE people SET name=? WHERE id=?", (new_name, pid))
            conn.commit()
        # Recompute centroid for renamed person as well (no-op if unchanged)
        try:
            with closing(get_conn()) as conn2:
                _recompute_person_centroid(conn2, pid)
        except Exception:
            pass
        return jsonify({"ok": True, "id": pid, "name": new_name, "merged": False})
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "error": "Name already exists"}), 409
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def _cosine(a: list[float], b: list[float]) -> float:
    try:
        import math
        if not a or not b:
            return -1.0
        s = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a)) or 1.0
        nb = math.sqrt(sum(y*y for y in b)) or 1.0
        return s / (na * nb)
    except Exception:
        return -1.0


def _json_embedding(value: Any) -> Optional[list[float]]:
    try:
        emb = json.loads(value) if isinstance(value, str) else value
        if isinstance(emb, list) and emb:
            return [float(x or 0.0) for x in emb]
    except Exception:
        pass
    return None


QUERY_STOPWORDS_DA = {
    "der", "som", "og", "i", "på", "ved", "til", "af", "for", "med",
    "en", "et", "den", "det", "de", "er", "at", "om", "fra", "har",
    "var", "blev", "bliver", "kan", "skal", "vil", "foto", "billede",
    "billeder",
}

QUERY_STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "at", "for", "with", "by",
    "is", "are", "was", "were", "be", "being", "been", "that", "this", "these", "those",
}


DANISH_SYNONYM_GROUPS = [
    {
        "person", "personer", "menneske", "mennesker", "people", "mand", "kvinde",
        "man", "woman", "child", "children", "kid", "kids", "barn", "børn", "boern",
    },
    {
        "pige", "piger", "girl", "girls", "datter", "barn", "børn", "boern",
        "child", "children", "kid", "kids",
    },
    {
        "dreng", "drenge", "boy", "boys", "søn", "soen", "barn", "børn", "boern",
        "child", "children", "kid", "kids",
    },
    {"baby", "spædbarn", "spaedbarn", "infant", "nyfødt", "nyfoedt", "barn", "child"},
    {"mor", "mama", "mother", "kvinde", "woman"},
    {"far", "papa", "father", "mand", "man"},
    {"strand", "beach", "hav", "kyst"},
    {"hav", "sea", "ocean", "strand", "kyst", "vand", "water"},
    {"pool", "swimmingpool", "bassin", "vand", "water"},
    {"skov", "forest", "woods"},
    {"bil", "car", "auto", "tesla"},
    {"solnedgang", "sunset", "aftenhimmel"},
    {"kamera", "camera"},
    {"familie", "family", "jul", "middag"},
    {"løber", "løb", "loeb", "running", "runner", "jogging"},
    {"cykler", "cykle", "cykel", "cycling", "bicycle", "bike"},
    {
        "svømmer", "svøm", "svømme", "svømning", "bader", "bade", "badning",
        "svommer", "svoemmer", "swim", "swimming", "bathing",
    },
    {
        "gynge", "gynger", "gyngende", "gyngestativ", "legeplads",
        "swing", "swings", "swinging", "playground",
    },
    {"rutsjebane", "rutchebane", "slide", "slides", "sliding", "legeplads"},
    {"leger", "lege", "leg", "play", "playing", "legeplads"},
]


def _repair_mojibake(text: str) -> str:
    raw = str(text or "")
    if "Ã" not in raw and "Â" not in raw:
        return raw
    try:
        fixed = raw.encode("latin1").decode("utf-8")
        if fixed:
            return fixed
    except Exception:
        pass
    return raw


def _fold_danish(text: str) -> str:
    folded = _repair_mojibake(str(text or "")).lower()
    for src, dst in (
        ("æ", "ae"),
        ("ø", "oe"),
        ("å", "aa"),
        ("ä", "a"),
        ("ö", "o"),
        ("ü", "u"),
    ):
        folded = folded.replace(src, dst)
    folded = unicodedata.normalize("NFKD", folded)
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


DANISH_SEARCH_SUFFIXES = (
    "ernes", "ende", "erne", "ene", "ers", "ens", "ets", "ere",
    "en", "et", "er", "es", "e", "r", "s",
)


def _search_term_variants(term: str) -> set[str]:
    base = re.sub(r"[^0-9a-z]+", "", _fold_danish(term))
    if not base:
        return set()
    variants = {base}
    for suffix in DANISH_SEARCH_SUFFIXES:
        if base.endswith(suffix) and len(base) - len(suffix) >= 3:
            variants.add(base[: -len(suffix)])
    return variants


SYNONYM_LOOKUP: Dict[str, set[str]] = {}
for _group in DANISH_SYNONYM_GROUPS:
    expanded: set[str] = set()
    for _term in _group:
        expanded.update(_search_term_variants(_term))
    for _term in expanded:
        SYNONYM_LOOKUP.setdefault(_term, set()).update(expanded)


def _query_term_groups(q: str, search_language: str = DEFAULT_SEARCH_LANGUAGE) -> list[set[str]]:
    q = _repair_mojibake(q or "").strip().lower()
    if not q:
        return []
    lang = _normalize_language(search_language, DEFAULT_SEARCH_LANGUAGE)
    stopwords = QUERY_STOPWORDS_DA if lang == LANG_DA else QUERY_STOPWORDS_EN
    stopword_keys = {_fold_danish(w) for w in stopwords}
    raw_words = [w for w in re.findall(r"[\w\-]+", q, flags=re.UNICODE) if w]
    groups: list[set[str]] = []
    for w in raw_words:
        variants = {v for v in _search_term_variants(w) if v and v not in stopword_keys}
        if not variants:
            continue
        group: set[str] = set()
        for variant in variants:
            group.update(SYNONYM_LOOKUP.get(variant, {variant}))
        if group:
            groups.append(group)
    return groups


def matches_search(photo: Dict[str, Any], q: str, search_language: str = DEFAULT_SEARCH_LANGUAGE) -> bool:
    term_groups = _query_term_groups(q, search_language)
    if not term_groups:
        return True

    fields = [
        str(photo.get("filename") or "").lower(),
        str(photo.get("rel_path") or "").lower(),
        str(photo.get("camera_make") or "").lower(),
        str(photo.get("camera_model") or "").lower(),
        str(photo.get("lens_model") or "").lower(),
        str(photo.get("gps_name") or "").lower(),
        " ".join((photo.get("ai_tags") or [])).lower(),
        " ".join((photo.get("ai_desc_tags") or [])).lower(),
        str(photo.get("ai_desc_caption") or "").lower(),
        str(photo.get("people_names") or "").lower(),
        str(photo.get("captured_at") or "").lower(),
        str(photo.get("metadata_json") or "").lower(),
    ]
    blob = " ".join(fields)
    blob_folded = _fold_danish(blob)

    matched = 0
    for group in term_groups:
        if any(term and term in blob_folded for term in group):
            matched += 1

    if matched == len(term_groups):
        return True
    if len(term_groups) >= 3:
        minimum = max(2, (len(term_groups) * 2 + 2) // 3)
        return matched >= minimum
    return False


def _photo_contains_any_tags(photo: Dict[str, Any], tags: list[str]) -> bool:
    try:
        if not tags:
            return False
        fields = [
            " ".join((photo.get("ai_tags") or [])).lower(),
            " ".join((photo.get("ai_desc_tags") or [])).lower(),
            str(photo.get("ai_desc_caption") or "").lower(),
            str(photo.get("people_names") or "").lower(),
        ]
        blob_folded = _fold_danish(" ".join(fields))
        for t in tags:
            tv = _fold_danish(t)
            if tv and tv in blob_folded:
                return True
    except Exception:
        return False
    return False


def query_photos(
    view: str,
    sort: str,
    folder: Optional[str] = None,
    offset: int | None = None,
    limit: int | None = None,
    direct_only: bool = False,
) -> list[Dict[str, Any]]:
    sort_map = {
        "date_desc": "COALESCE(captured_at, modified_fs, created_fs) DESC",
        "date_asc": "COALESCE(captured_at, modified_fs, created_fs) ASC",
        "name_asc": "filename ASC",
        "name_desc": "filename DESC",
        "size_desc": "file_size DESC",
        "size_asc": "file_size ASC",
    }
    order_by = sort_map.get(sort, sort_map["date_desc"])

    where = []
    params: list[Any] = []
    # Always exclude Synology auto-thumbs and @eaDir content from results
    where.append("(UPPER(filename) NOT LIKE 'SYNOPHOTO_THUMB_%' AND UPPER(filename) NOT LIKE 'SYNOPHOTO_CACHE_%')")
    where.append("(rel_path NOT LIKE '%/@eaDir/%')")
    if view == "favorites":
        where.append("favorite = 1")
    elif view == "steder":
        # Only include photos with explicit coordinates so the map can plot them
        where.append("(gps_lat IS NOT NULL AND gps_lon IS NOT NULL)")
    elif view == "kameraer":
        where.append("(camera_model IS NOT NULL AND camera_model != '')")
    elif view == "personer":
        where.append("people_count > 0")  # future face-service
    elif view == "recent":
        where.append("1=1")

    # Optional folder filter: include canonical uploads path AND
    # internal originals/converted mirrors under the same user folder.
    if folder or direct_only:
        # Browsing/filtering must accept existing on-disk names (e.g. Synology system folders)
        # while still blocking traversal input.
        try:
            raw = _normalize_folder_acl_path(str(folder or ""))
        except Exception:
            raw = ""
        # Strip optional 'uploads/' prefix for consistent handling
        f = raw[8:] if raw.startswith("uploads/") else raw
        if f == "uploads":
            f = ""
        # If caller passed 'originals/<sub>' or 'converted/<sub>', fold to base '<sub>'
        if f.startswith("originals/"):
            f_base = f[len("originals/"):]
        elif f.startswith("converted/"):
            f_base = f[len("converted/"):]
        else:
            f_base = f

        # Build all accepted rel_path prefixes for this logical folder
        if f_base:
            prefixes = [
                f"uploads/{f_base}",
                f"uploads/originals/{f_base}",
                f"uploads/converted/{f_base}",
            ]
        else:
            prefixes = [
                "uploads",
                "uploads/originals",
                "uploads/converted",
            ]
        # Deduplicate while preserving order
        seen = set()
        uniq_prefixes = []
        for pfx in prefixes:
            if pfx and pfx not in seen:
                uniq_prefixes.append(pfx)
                seen.add(pfx)

        if uniq_prefixes:
            if direct_only:
                # Direct folder view: include only immediate files under each logical
                # storage prefix, not deeper descendants.
                parts = []
                for pfx in uniq_prefixes:
                    parts.append("(rel_path LIKE ? || '/%' AND instr(substr(rel_path, length(?) + 2), '/') = 0)")
                    params.extend([pfx, pfx])
                where.append("(" + " OR ".join(parts) + ")")
            else:
                # Build OR chain: (rel_path LIKE ?||'/%' OR ...)
                where.append("(" + " OR ".join(["rel_path LIKE ? || '/%'"] * len(uniq_prefixes)) + ")")
                params.extend(uniq_prefixes)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT
            photos.*,
            COALESCE((
                SELECT GROUP_CONCAT(name, ' ')
                FROM (
                    SELECT DISTINCT p2.name AS name
                    FROM faces f2
                    INNER JOIN people p2 ON p2.id = f2.person_id
                    WHERE f2.photo_id = photos.id
                      AND COALESCE(p2.hidden, 0) = 0
                )
            ), '') AS people_names
        FROM photos
        {where_sql}
        ORDER BY {order_by}
    """
    dedupe_paged_uploads = bool(isinstance(limit, int) and limit > 0)
    if isinstance(limit, int) and limit > 0:
        raw_limit = int(limit)
        if dedupe_paged_uploads:
            raw_limit = max(raw_limit, int(offset or 0) + (int(limit) * 6))
        sql += f"\n    LIMIT {raw_limit}"
        if (not dedupe_paged_uploads) and isinstance(offset, int) and offset > 0:
            sql += f" OFFSET {int(offset)}"

    with closing(get_conn()) as conn:
        rows = conn.execute(sql, params).fetchall()
        rows = _dedupe_upload_storage_rows(rows)
        if dedupe_paged_uploads:
            start = max(0, int(offset or 0))
            end = start + int(limit)
            rows = rows[start:end]
        return [row_to_public(r) for r in rows]


def _hamdist_hex(a: str, b: str) -> int:
    try:
        va = int(a, 16)
        vb = int(b, 16)
        return (va ^ vb).bit_count()
    except Exception:
        return 64  # max for 64-bit pHash


def _clamp_hash_distance_arg(name: str, default: int) -> int:
    try:
        value = int(request.args.get(name, str(default)))
    except Exception:
        value = int(default)
    return max(0, min(64, value))


def _photo_hash_value(row_data: Dict[str, Any], key: str) -> str:
    if key == "ahash":
        return str(row_data.get("ahash") or row_data.get("phash") or "").strip().lower()
    if key == "phash_dct":
        return str(row_data.get("phash_dct") or "").strip().lower()
    return str(row_data.get(key) or "").strip().lower()


def _compute_photo_hashes_from_disk(rel_path: str) -> Dict[str, str]:
    try:
        path = _disk_path_from_rel_path(rel_path)
        if not path.exists() or path.suffix.lower() in VIDEO_EXTS:
            return {}
        with Image.open(path) as img:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            return image_hashes(img)
    except Exception:
        return {}


def _ensure_photo_hashes(conn: sqlite3.Connection, row_data: Dict[str, Any]) -> Dict[str, Any]:
    rel_path = str(row_data.get("rel_path") or "").strip()
    if not rel_path:
        return row_data
    has_all = all(_photo_hash_value(row_data, key) for key in ("ahash", "dhash", "phash_dct"))
    if has_all:
        return row_data

    hashes = _compute_photo_hashes_from_disk(rel_path)
    if not hashes:
        return row_data

    next_data = dict(row_data)
    for key in ("ahash", "dhash", "phash_dct", "phash"):
        if hashes.get(key):
            next_data[key] = hashes[key]

    try:
        conn.execute(
            """
            UPDATE photos
            SET ahash=?, dhash=?, phash_dct=?, phash=COALESCE(NULLIF(phash, ''), ?)
            WHERE id=?
            """,
            (
                next_data.get("ahash"),
                next_data.get("dhash"),
                next_data.get("phash_dct"),
                next_data.get("phash"),
                int(next_data.get("id") or 0),
            ),
        )
        conn.commit()
    except Exception:
        pass
    return next_data


def _similar_hash_match(
    distances: Dict[str, int],
    thresholds: Dict[str, int],
) -> tuple[bool, int, int]:
    pass_count = 0
    for key in ("phash", "dhash", "ahash"):
        if int(distances.get(key) or 64) <= int(thresholds.get(key) or 0):
            pass_count += 1

    combined = (
        int(distances.get("phash") or 64)
        + int(distances.get("dhash") or 64)
        + int(distances.get("ahash") or 64)
    )
    combined_threshold = (
        int(thresholds.get("phash") or 0)
        + int(thresholds.get("dhash") or 0)
        + int(thresholds.get("ahash") or 0)
    )
    if pass_count >= 2:
        return True, pass_count, combined
    if pass_count >= 1 and combined <= combined_threshold:
        return True, pass_count, combined
    return False, pass_count, combined


@app.route("/api/duplicates")
def api_duplicates():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    try:
        dist_thr = int(request.args.get("distance", "5"))
    except ValueError:
        dist_thr = 5
    min_group = max(2, int(request.args.get("min", "2")))

    with closing(get_conn()) as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, filename, rel_path, file_size, phash, checksum_sha256, thumb_name, captured_at FROM photos WHERE phash IS NOT NULL"
        ).fetchall()]

    # Exact duplicates by checksum
    by_checksum: dict[str, list[dict]] = {}
    for r in rows:
        c = r.get("checksum_sha256")
        if c:
            by_checksum.setdefault(c, []).append(r)
    checksum_groups = [v for v in by_checksum.values() if len(v) >= min_group]

    # Exact duplicates by equal phash
    by_phash: dict[str, list[dict]] = {}
    for r in rows:
        p = r.get("phash")
        if p:
            by_phash.setdefault(p, []).append(r)
    phash_exact_groups = [v for v in by_phash.values() if len(v) >= min_group]

    # Near duplicates by small Hamming distance of pHash
    # Bucket by first 4 hex chars to avoid O(n^2)
    buckets: dict[str, list[dict]] = {}
    for r in rows:
        p = r.get("phash")
        if not p:
            continue
        key = p[:4]
        buckets.setdefault(key, []).append(r)

    visited: set[int] = set()
    # exclude items already in exact groups
    for g in checksum_groups + phash_exact_groups:
        for it in g:
            visited.add(int(it["id"]))

    near_groups: list[list[dict]] = []
    for arr in buckets.values():
        n = len(arr)
        if n < 2:
            continue
        # Build adjacency by threshold
        comp_map: dict[int, set[int]] = {}
        ids = [int(x["id"]) for x in arr]
        for i in range(n):
            for j in range(i + 1, n):
                a, b = arr[i], arr[j]
                if int(a["id"]) in visited and int(b["id"]) in visited:
                    continue
                d = _hamdist_hex(a["phash"], b["phash"])
                if d <= dist_thr:
                    comp_map.setdefault(int(a["id"]), set()).add(int(b["id"]))
                    comp_map.setdefault(int(b["id"]), set()).add(int(a["id"]))
        # Connected components
        seen: set[int] = set()
        for root in ids:
            if root in seen or root not in comp_map:
                continue
            stack = [root]
            comp_ids: set[int] = set()
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                comp_ids.add(cur)
                for nb in comp_map.get(cur, set()):
                    if nb not in seen:
                        stack.append(nb)
            if len(comp_ids) >= min_group:
                group_items = [next(x for x in arr if int(x["id"]) == cid) for cid in comp_ids]
                near_groups.append(group_items)

    # Prepare payload (limit size in thumbs only)
    def _pub(it: dict) -> dict:
        out = {
            "id": it["id"],
            "filename": it["filename"],
            "rel_path": it["rel_path"],
            "file_size": it["file_size"],
            "phash": it["phash"],
            "checksum": it["checksum_sha256"],
            "captured_at": it.get("captured_at"),
        }
        if it.get("thumb_name"):
            out["thumb_url"] = f"/api/thumbs/{it['thumb_name']}"
        else:
            out["thumb_url"] = None
        return out

    resp = {
        "ok": True,
        "distance": dist_thr,
        "groups": [
            {"reason": "checksum", "items": [[_pub(it) for it in g] for g in checksum_groups]},
            {"reason": "phash_equal", "items": [[_pub(it) for it in g] for g in phash_exact_groups]},
            {"reason": "phash_near", "items": [[_pub(it) for it in g] for g in near_groups]},
        ],
        "counts": {
            "checksum": len(checksum_groups),
            "phash_equal": len(phash_exact_groups),
            "phash_near": len(near_groups),
        },
    }
    return jsonify(resp)


@app.route("/api/duplicates/merge", methods=["POST"])
def api_duplicates_merge():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    data = request.get_json(silent=True) or {}
    keep_id = int(data.get("keep_id") or 0)
    drop_id = int(data.get("drop_id") or 0)
    copy_meta = bool(data.get("copy_metadata", True))
    delete_file = bool(data.get("delete_file", True))
    if not keep_id or not drop_id or keep_id == drop_id:
        return jsonify({"ok": False, "error": "Invalid keep/drop ids"}), 400
    try:
        with closing(get_conn()) as conn:
            keep = conn.execute("SELECT * FROM photos WHERE id=?", (keep_id,)).fetchone()
            drop = conn.execute("SELECT * FROM photos WHERE id=?", (drop_id,)).fetchone()
            if not keep or not drop:
                return jsonify({"ok": False, "error": "Photo not found"}), 404

            # Optionally copy metadata when missing on the kept photo
            if copy_meta:
                upd: dict[str, Any] = {}
                cols_simple = [
                    "captured_at", "camera_make", "camera_model", "lens_model",
                    "iso", "focal_length", "f_number", "exposure_time",
                    "gps_lat", "gps_lon", "gps_name",
                ]
                for col in cols_simple:
                    if (keep[col] is None or keep[col] == "") and (drop[col] is not None and drop[col] != ""):
                        upd[col] = drop[col]
                # Merge JSON-ish columns
                def _first(v):
                    return None if v in (None, "", "null") else v
                ai_tags_keep = _first(keep["ai_tags"])
                ai_tags_drop = _first(drop["ai_tags"])
                if ai_tags_drop and not ai_tags_keep:
                    upd["ai_tags"] = ai_tags_drop
                ai_desc_keep = _first(keep["ai_desc_tags"])
                ai_desc_drop = _first(drop["ai_desc_tags"])
                if ai_desc_drop and not ai_desc_keep:
                    upd["ai_desc_tags"] = ai_desc_drop
                if (keep["ai_desc_caption"] in (None, "")) and _first(drop["ai_desc_caption"]):
                    upd["ai_desc_caption"] = drop["ai_desc_caption"]
                if (keep["embedding_json"] in (None, "")) and _first(drop["embedding_json"]):
                    upd["embedding_json"] = drop["embedding_json"]
                if (keep["metadata_json"] in (None, "")) and _first(drop["metadata_json"]):
                    upd["metadata_json"] = drop["metadata_json"]
                if (keep["exif_json"] in (None, "")) and _first(drop["exif_json"]):
                    upd["exif_json"] = drop["exif_json"]
                if upd:
                    sets = ", ".join([f"{k}=?" for k in upd.keys()])
                    conn.execute(f"UPDATE photos SET {sets} WHERE id=?", (*upd.values(), keep_id))

            # Move faces to kept photo, then delete the dropped one
            try:
                moved = conn.execute("SELECT COUNT(*) AS c FROM faces WHERE photo_id=?", (drop_id,)).fetchone()
                moved_n = int(moved["c"] or 0) if moved else 0
                if moved_n:
                    conn.execute("UPDATE faces SET photo_id=? WHERE photo_id=?", (keep_id, drop_id))
                    cur_keep_pc = conn.execute("SELECT people_count FROM photos WHERE id=?", (keep_id,)).fetchone()
                    pc = int(cur_keep_pc["people_count"] or 0) if cur_keep_pc else 0
                    conn.execute("UPDATE photos SET people_count=? WHERE id=?", (pc + moved_n, keep_id))
            except Exception:
                pass

            # Resolve disk path for the dropped photo
            drop_rel = str(drop["rel_path"] or "")
            drop_metadata_json = drop["metadata_json"]
            conn.execute("DELETE FROM photos WHERE id=?", (drop_id,))
            conn.commit()
        # Optionally remove file from disk
        if delete_file and drop_rel:
            try:
                _delete_photo_disk_variants(drop_rel, drop_metadata_json)
            except Exception:
                pass
        return jsonify({"ok": True, "kept": keep_id, "removed": drop_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def _metadata_score_row(row: sqlite3.Row) -> int:
    if not row:
        return 0
    def _has(v):
        return 1 if (v not in (None, "", "null")) else 0
    fields = [
        "captured_at", "camera_make", "camera_model", "lens_model",
        "iso", "focal_length", "f_number", "exposure_time",
        "gps_lat", "gps_lon", "gps_name",
        "ai_tags", "ai_desc_tags", "ai_desc_caption",
        "embedding_json", "metadata_json", "exif_json",
    ]
    sc = 0
    for f in fields:
        sc += _has(row[f])
    # light bonus: larger file size often means original
    try:
        fs = int(row["file_size"] or 0)
        sc += 1 if fs > 0 else 0
    except Exception:
        pass
    # bonus for having GPS
    try:
        has_gps = (row["gps_lat"] is not None) and (row["gps_lon"] is not None)
    except Exception:
        has_gps = False
    if has_gps:
        sc += 1
    return sc


@app.route("/api/duplicates/merge-auto", methods=["POST"])
def api_duplicates_merge_auto():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    data = request.get_json(silent=True) or {}
    a_id = int(data.get("id1") or 0)
    b_id = int(data.get("id2") or 0)
    if not a_id or not b_id or a_id == b_id:
        return jsonify({"ok": False, "error": "Invalid ids"}), 400
    try:
        with closing(get_conn()) as conn:
            a = conn.execute("SELECT * FROM photos WHERE id=?", (a_id,)).fetchone()
            b = conn.execute("SELECT * FROM photos WHERE id=?", (b_id,)).fetchone()
            if not a or not b:
                return jsonify({"ok": False, "error": "Photo not found"}), 404
            sa = _metadata_score_row(a)
            sb = _metadata_score_row(b)
            # Tie-breakers: prefer GPS, then larger file, else lower id keeps
            def _prefers_x(has_gps_row):
                try:
                    return 1 if (has_gps_row["gps_lat"] is not None and has_gps_row["gps_lon"] is not None) else 0
                except Exception:
                    return 0
            if sa > sb:
                keep_id, drop_id = int(a["id"]), int(b["id"])
            elif sb > sa:
                keep_id, drop_id = int(b["id"]), int(a["id"])
            else:
                if _prefers_x(a) > _prefers_x(b):
                    keep_id, drop_id = int(a["id"]), int(b["id"])
                elif _prefers_x(b) > _prefers_x(a):
                    keep_id, drop_id = int(b["id"]), int(a["id"])
                else:
                    fa = int(a["file_size"] or 0)
                    fbz = int(b["file_size"] or 0)
                    if fa >= fbz:
                        keep_id, drop_id = int(a["id"]), int(b["id"])
                    else:
                        keep_id, drop_id = int(b["id"]), int(a["id"])

        # Reuse the regular merge logic by calling it inline
        log_event("dupe_merge_auto", kept=keep_id, drop=drop_id)
        return api_duplicates_merge_impl(keep_id, drop_id)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def api_duplicates_merge_impl(keep_id: int, drop_id: int):
    try:
        with closing(get_conn()) as conn:
            keep = conn.execute("SELECT * FROM photos WHERE id=?", (keep_id,)).fetchone()
            drop = conn.execute("SELECT * FROM photos WHERE id=?", (drop_id,)).fetchone()
            if not keep or not drop:
                return jsonify({"ok": False, "error": "Photo not found"}), 404
            # Copy metadata if missing on keep
            upd: dict[str, Any] = {}
            cols_simple = [
                "captured_at", "camera_make", "camera_model", "lens_model",
                "iso", "focal_length", "f_number", "exposure_time",
                "gps_lat", "gps_lon", "gps_name",
            ]
            for col in cols_simple:
                if (keep[col] is None or keep[col] == "") and (drop[col] is not None and drop[col] != ""):
                    upd[col] = drop[col]
            def _first(v):
                return None if v in (None, "", "null") else v
            if _first(drop["ai_tags"]) and not _first(keep["ai_tags"]):
                upd["ai_tags"] = drop["ai_tags"]
            if _first(drop["ai_desc_tags"]) and not _first(keep["ai_desc_tags"]):
                upd["ai_desc_tags"] = drop["ai_desc_tags"]
            if _first(drop["ai_desc_caption"]) and not _first(keep["ai_desc_caption"]):
                upd["ai_desc_caption"] = drop["ai_desc_caption"]
            if _first(drop["embedding_json"]) and not _first(keep["embedding_json"]):
                upd["embedding_json"] = drop["embedding_json"]
            if _first(drop["metadata_json"]) and not _first(keep["metadata_json"]):
                upd["metadata_json"] = drop["metadata_json"]
            if _first(drop["exif_json"]) and not _first(keep["exif_json"]):
                upd["exif_json"] = drop["exif_json"]
            if upd:
                sets = ", ".join([f"{k}=?" for k in upd.keys()])
                conn.execute(f"UPDATE photos SET {sets} WHERE id=?", (*upd.values(), keep_id))

            # Move faces from drop to keep
            try:
                moved = conn.execute("SELECT COUNT(*) AS c FROM faces WHERE photo_id=?", (drop_id,)).fetchone()
                moved_n = int(moved["c"] or 0) if moved else 0
                if moved_n:
                    conn.execute("UPDATE faces SET photo_id=? WHERE photo_id=?", (keep_id, drop_id))
                    cur_keep_pc = conn.execute("SELECT people_count FROM photos WHERE id=?", (keep_id,)).fetchone()
                    pc = int(cur_keep_pc["people_count"] or 0) if cur_keep_pc else 0
                    conn.execute("UPDATE photos SET people_count=? WHERE id=?", (pc + moved_n, keep_id))
            except Exception:
                pass

            drop_rel = str(drop["rel_path"] or "")
            drop_metadata_json = drop["metadata_json"]
            conn.execute("DELETE FROM photos WHERE id=?", (drop_id,))
            conn.commit()
        # Remove file from disk if exists
        try:
            if drop_rel:
                _delete_photo_disk_variants(drop_rel, drop_metadata_json)
        except Exception:
            pass
        return jsonify({"ok": True, "kept": keep_id, "removed": drop_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/")
def index():
    try:
        with closing(get_conn()) as conn:
            row = conn.execute(
                "SELECT id, username, role, ui_language, search_language, theme_mode FROM users WHERE id=?",
                (current_user.id,),
            ).fetchone()
        role = row["role"] if row and row["role"] else getattr(current_user, "role", None)
        profile = {
            "id": int(row["id"]) if row else int(current_user.id),
            "username": (row["username"] if row else getattr(current_user, "username", "")),
            "role": (role or "user"),
            "ui_language": _normalize_language((row["ui_language"] if row else None), DEFAULT_UI_LANGUAGE),
            "search_language": _normalize_language((row["search_language"] if row else None), DEFAULT_SEARCH_LANGUAGE),
            "theme_mode": (str((row["theme_mode"] if row else "system") or "system").lower() if row else "system"),
        }
    except Exception:
        role = None
        profile = {
            "id": int(getattr(current_user, "id", 0) or 0),
            "username": getattr(current_user, "username", ""),
            "role": (getattr(current_user, "role", None) or "user"),
            "ui_language": _normalize_language(getattr(current_user, "ui_language", None), DEFAULT_UI_LANGUAGE),
            "search_language": _normalize_language(getattr(current_user, "search_language", None), DEFAULT_SEARCH_LANGUAGE),
            "theme_mode": "system",
        }
    return render_template(
        "index.html",
        user_role=(role or "user"),
        user_profile=profile,
        scan_enabled=bool(ENABLE_SCAN_FEATURES),
    )


@app.route("/s/<token>")
def shared_folder_view(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        fallback = _share_redirect_for_authenticated_user(token)
        if fallback is not None:
            return fallback
        return render_template("login.html", error=_ui_text("share_invalid_or_expired")), 404
    return render_template("shared_folder.html", share_token=token)


@app.route("/api/share/<token>/auth", methods=["POST"])
def api_share_auth(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    body = request.get_json(silent=True) or {}
    visitor_name = _sanitize_share_visitor_name(body.get("visitor_name") or "")
    if _share_requires_visitor_name(share) and not visitor_name:
        return jsonify({"ok": False, "error": "Navn er pÃ¥krÃ¦vet"}), 400

    if not _share_is_password_protected(share):
        session[_share_session_key(share)] = 1
        if _share_requires_visitor_name(share):
            session[_share_name_session_key(share)] = visitor_name
        return jsonify({"ok": True, "visitor_name": _share_get_visitor_name(share)})

    password = str(body.get("password") or "")
    if not password:
        return jsonify({"ok": False, "error": "Mangler adgangskode"}), 400

    stored = str(share["password_hash"] or "")
    if not stored or not check_password_hash(stored, password):
        return jsonify({"ok": False, "error": "Forkert adgangskode"}), 401

    session[_share_session_key(share)] = 1
    if _share_requires_visitor_name(share):
        session[_share_name_session_key(share)] = visitor_name
    return jsonify({"ok": True, "visitor_name": _share_get_visitor_name(share)})


@app.route("/api/shares", methods=["POST"])
def api_create_share():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    body = request.get_json(silent=True) or {}
    raw_folder_paths = body.get("folder_paths")
    folder_paths_raw: list[str]
    if isinstance(raw_folder_paths, list):
        folder_paths_raw = [str(v or "") for v in raw_folder_paths]
    else:
        folder_paths_raw = [str(body.get("folder_path") or "")]

    folder_paths: list[str] = []
    for raw in folder_paths_raw:
        try:
            fp = _normalize_share_folder_path(raw)
        except Exception:
            fp = ""
        if fp and fp not in folder_paths:
            folder_paths.append(fp)
    if not folder_paths:
        return jsonify({"ok": False, "error": "VÃ¦lg mindst Ã©n mappe"}), 400

    base = UPLOAD_DIR.resolve()
    for folder_path in folder_paths:
        # Accept both canonical uploads/<subdir> and internal storage roots like
        # uploads/originals/<subdir> or uploads/converted/<subdir>.
        candidates = [
            (UPLOAD_DIR / folder_path),
            (UPLOAD_DIR / "originals" / folder_path),
            (UPLOAD_DIR / "converted" / folder_path),
        ]
        found = False
        for cand in candidates:
            try:
                target = cand.resolve()
                target.relative_to(base)
            except Exception:
                continue
            if target.exists() and target.is_dir():
                found = True
                break
        if not found:
            return jsonify({"ok": False, "error": f"Mappen findes ikke: {folder_path}"}), 404

    share_name = str(body.get("share_name") or "").strip()
    if len(share_name) > 120:
        share_name = share_name[:120].strip()
    if not share_name:
        if len(folder_paths) == 1:
            share_name = f"uploads/{folder_paths[0]}"
        else:
            share_name = f"{len(folder_paths)} mapper"

    perm = str(body.get("permission") or "view").strip().lower()
    can_upload = 0
    can_delete = 0
    if perm == "upload":
        can_upload = 1
    elif perm in {"manage", "delete"}:
        can_upload = 1
        can_delete = 1
    elif perm != "view":
        return jsonify({"ok": False, "error": "Ugyldig rettighed"}), 400

    expires_at, expires_error = _share_expires_at_from_body(body, default_value=7, default_unit="days")
    if expires_error:
        return jsonify({"ok": False, "error": expires_error}), 400

    password_enabled = bool(body.get("password_enabled"))
    require_visitor_name = bool(body.get("require_visitor_name"))
    use_duckdns = bool(body.get("use_duckdns"))
    password_raw = str(body.get("password") or "")
    password_hash = None
    if password_enabled:
        if len(password_raw) < 4:
            return jsonify({"ok": False, "error": "Adgangskode skal vÃ¦re mindst 4 tegn"}), 400
        password_hash = generate_password_hash(password_raw)

    token = secrets.token_urlsafe(24)
    token_hash = _share_token_digest(token)
    created_at = now_iso()
    primary_folder_path = folder_paths[0]
    with closing(get_conn()) as conn:
        cur = conn.execute(
            """
            INSERT INTO share_links(token_hash, token_plain, share_name, folder_path, can_upload, can_delete, require_visitor_name, link_use_duckdns, password_hash, expires_at, revoked, created_by_user_id, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                token_hash,
                token,
                share_name,
                primary_folder_path,
                int(can_upload),
                int(can_delete),
                1 if require_visitor_name else 0,
                1 if use_duckdns else 0,
                password_hash,
                expires_at,
                0,
                int(getattr(current_user, "id", 0) or 0),
                created_at,
            ),
        )
        share_id = int(cur.lastrowid or 0)
        for fp in folder_paths:
            conn.execute(
                "INSERT OR IGNORE INTO share_link_folders(share_id, folder_path, created_at) VALUES(?,?,?)",
                (share_id, fp, created_at),
            )
        conn.commit()

    link, link_error = _build_share_link(token, use_duckdns)
    if link_error or not link:
        return jsonify({"ok": False, "error": link_error or "Kunne ikke oprette share-link"}), 400
    return jsonify(
        {
            "ok": True,
            "link": link,
            "share_name": share_name,
            "folder_path": primary_folder_path,
            "folder_paths": folder_paths,
            "permission": perm,
            "can_upload": bool(can_upload),
            "can_delete": bool(can_delete),
            "require_visitor_name": bool(require_visitor_name),
            "password_enabled": bool(password_hash),
            "expires_at": expires_at,
        }
    )


@app.route("/api/share/<token>/info")
def api_share_info(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401
    with closing(get_conn()) as conn:
        folder_paths = _share_folder_paths(conn, share)
    folder_label = f"uploads/{folder_paths[0]}" if len(folder_paths) == 1 else f"{len(folder_paths)} mapper"
    share_name = str(share["share_name"] or "").strip() if "share_name" in share.keys() else ""
    if not share_name:
        share_name = folder_label
    visitor_name = _share_get_visitor_name(share)
    upload_types = _upload_file_types_settings_payload()
    return jsonify(
        {
            "ok": True,
            "share_name": share_name,
            "folder_path": folder_paths[0] if folder_paths else "",
            "folder_paths": folder_paths,
            "folder_count": len(folder_paths),
            "folder_labels": [f"uploads/{fp}" for fp in folder_paths],
            "folder_label": folder_label,
            "can_upload": bool(int(share["can_upload"] or 0)),
            "can_delete": bool(int(share["can_delete"] or 0)),
            "require_visitor_name": _share_requires_visitor_name(share),
            "visitor_name": visitor_name,
            "password_enabled": _share_is_password_protected(share),
            "expires_at": share["expires_at"],
            "upload_allowed_extensions": upload_types["allowed_extensions"],
            "upload_blocked_extensions": upload_types["blocked_extensions"],
            "upload_accept": upload_types["upload_accept"],
        }
    )


@app.route("/api/share/<token>/photos")
def api_share_photos(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401

    with closing(get_conn()) as conn:
        folder_paths = _share_folder_paths(conn, share)
    for fp in folder_paths:
        try:
            _sync_upload_folder_from_disk(fp, recursive=True, max_files=UPLOAD_FOLDER_SYNC_MAX_FILES)
        except Exception:
            pass
    prefixes = _share_rel_prefixes(folder_paths)
    if not prefixes:
        return jsonify({"ok": False, "error": "Ugyldig share-mappe"}), 400
    where_sql, where_params = _share_scope_sql(prefixes)

    with closing(get_conn()) as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM photos
            WHERE ({where_sql})
            ORDER BY COALESCE(captured_at, modified_fs, created_fs) DESC, id DESC
            """,
            tuple(where_params),
        ).fetchall()

    rows = _dedupe_upload_storage_rows(rows)
    items = [_row_to_share_public(r, token) for r in rows]
    return jsonify({"ok": True, "items": items})


@app.route("/api/share/<token>/thumb/<int:photo_id>")
def api_share_thumb(token: str, photo_id: int):
    share = _load_share_from_token(token)
    if not share or not _share_is_authorized(share):
        return ("Forbidden", 403)
    with closing(get_conn()) as conn:
        row = _get_share_scoped_photo_row(conn, share, photo_id)
    if not row or not row["thumb_name"]:
        return ("Not found", 404)
    return send_from_directory(THUMB_DIR, str(row["thumb_name"]))


@app.route("/api/share/<token>/original/<int:photo_id>")
def api_share_original(token: str, photo_id: int):
    share = _load_share_from_token(token)
    if not share or not _share_is_authorized(share):
        return ("Forbidden", 403)
    with closing(get_conn()) as conn:
        row = _get_share_scoped_photo_row(conn, share, photo_id)
    if not row:
        return ("Not found", 404)

    safe_rel = str(row["rel_path"] or "").replace("..", "").lstrip("/")
    if safe_rel.startswith("uploads/"):
        return send_from_directory(str(UPLOAD_DIR), safe_rel[len("uploads/"):])
    return ("Forbidden", 403)


@app.route("/api/share/<token>/view/<int:photo_id>")
def api_share_viewable(token: str, photo_id: int):
    share = _load_share_from_token(token)
    if not share or not _share_is_authorized(share):
        return ("Forbidden", 403)
    with closing(get_conn()) as conn:
        row = _get_share_scoped_photo_row(conn, share, photo_id)
    if not row:
        return ("Not found", 404)

    safe_rel = str(row["rel_path"] or "").replace("..", "").lstrip("/")
    if not safe_rel.startswith("uploads/"):
        return ("Forbidden", 403)
    src = UPLOAD_DIR / safe_rel[len("uploads/"):]
    if not src.exists():
        return ("Not found", 404)

    view_path = ensure_viewable_copy(src, safe_rel)
    try:
        vp = str(view_path)
        if vp.startswith(str(CONVERT_DIR)):
            rel_conv = str(view_path.relative_to(CONVERT_DIR)).replace("\\", "/")
            return send_from_directory(CONVERT_DIR, rel_conv)
        return send_from_directory(UPLOAD_DIR, safe_rel[len("uploads/"):])
    except Exception as e:
        return (str(e), 500)


@app.route("/api/share/<token>/upload", methods=["POST"])
def api_share_upload(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401
    if int(share["can_upload"] or 0) != 1:
        return jsonify({"ok": False, "error": "Upload ikke tilladt"}), 403

    with closing(get_conn()) as conn:
        folder_paths = _share_folder_paths(conn, share)
    folder_path = folder_paths[0] if folder_paths else ""
    if not folder_path:
        return jsonify({"ok": False, "error": "Ugyldig share-mappe"}), 400
    uploader_name = _share_get_visitor_name(share)
    if _share_requires_visitor_name(share) and not uploader_name:
        return jsonify({"ok": False, "name_required": True, "error": "Navn er pÃ¥krÃ¦vet"}), 401
    uploader_label = uploader_name or "Share-bruger"

    # Store physical files under internal originals root, mirroring user uploads
    target_dir = (UPLOAD_DIR / "originals" / folder_path)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Kan ikke oprette upload-destination: {e}"}), 500

    files = request.files.getlist("files") or []
    if not files:
        return jsonify({"ok": False, "error": "No files"}), 400

    saved = []
    errors: list[str] = []
    # Use the same commit + postprocess flow as user uploads
    rel_prefix = "uploads/originals/"
    uploaded_by = uploader_label
    allowed_upload_exts = upload_allowed_extensions()
    for f in files:
        try:
            name = secure_filename(f.filename or "")
            if not name:
                continue
            ext = Path(name).suffix.lower()
            if not _is_upload_extension_allowed(ext, allowed_upload_exts):
                errors.append(_blocked_upload_file_error(name, ext))
                try:
                    log_event("share_upload_skip_blocked_file_type", filename=name, ext=ext)
                except Exception:
                    pass
                continue

            # Write to a temporary file first to reuse _commit_uploaded_file semantics
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                f.stream.seek(0)
                shutil.copyfileobj(f.stream, tmp)
                tmp_path = Path(tmp.name)

            ok, saved_name, err = _commit_uploaded_file(
                target_dir=target_dir,
                rel_prefix=rel_prefix,
                subdir=folder_path,
                source_path=tmp_path,
                original_name=name,
                last_modified_ms=None,
                uploaded_by=uploaded_by,
                autostart_postprocess=False,
            )
            if ok:
                saved.append(saved_name)
            else:
                errors.append(err or f"Commit failed: {name}")
        except Exception as e:
            errors.append(str(e))

    # Ensure the postprocess worker runs for this uploader label
    try:
        _ensure_upload_postprocess_running(uploaded_by)
    except Exception as e:
        try:
            log_event("error", error=f"share_postprocess_autostart: {e}")
        except Exception:
            pass

    return jsonify({"ok": bool(saved) or not errors, "saved": saved, "errors": errors})


# --- Share-link TUS endpoints (no login; token-based auth) ---
@app.route("/api/share/<token>/upload/tus", methods=["OPTIONS"])
@app.route("/api/share/<token>/upload/tus/<upload_id>", methods=["OPTIONS"])
def api_share_tus_options(token: str, upload_id: Optional[str] = None):
    resp = make_response("", 204)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS, POST, HEAD, PATCH"
    resp.headers["Access-Control-Allow-Headers"] = "Tus-Resumable, Upload-Length, Upload-Offset, Upload-Metadata, Content-Type, X-HTTP-Method-Override"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/share/<token>/upload/tus", methods=["POST"])
def api_share_tus_create(token: str):
    fb = _tus_require_version()
    if fb:
        return jsonify(fb[0]), fb[1], _tus_headers()

    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404, _tus_headers()
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401, _tus_headers()
    if int(share["can_upload"] or 0) != 1:
        return jsonify({"ok": False, "error": "Upload ikke tilladt"}), 403, _tus_headers()

    try:
        TUS_TMP_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    try:
        upload_length = int(str(request.headers.get("Upload-Length") or "0").strip())
    except Exception:
        upload_length = -1
    if upload_length < 0:
        return jsonify({"ok": False, "error": "Invalid Upload-Length"}), 400, _tus_headers()

    meta = _parse_tus_metadata(str(request.headers.get("Upload-Metadata") or ""))
    filename = str(meta.get("filename") or "").strip()
    if not filename:
        return jsonify({"ok": False, "error": "Missing filename"}), 400, _tus_headers()
    filename_ext = Path(secure_filename(filename) or filename).suffix.lower()
    if not _is_upload_extension_allowed(filename_ext):
        try:
            log_event("share_upload_skip_blocked_file_type", filename=filename, ext=filename_ext)
        except Exception:
            pass
        return jsonify({
            "ok": False,
            "error": _blocked_upload_file_error(filename, filename_ext),
            "blocked_extension": filename_ext,
        }), 415, _tus_headers()

    # Determine target dir from share's primary folder
    with closing(get_conn()) as conn:
        folder_paths = _share_folder_paths(conn, share)
    folder_path = folder_paths[0] if folder_paths else ""
    try:
        subdir = _normalize_share_folder_path(folder_path)
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldig share-mappe"}), 400, _tus_headers()
    # Store physical files under internal originals root to mirror user uploads
    target_dir = (UPLOAD_DIR / "originals" / subdir) if subdir else (UPLOAD_DIR / "originals")
    rel_prefix = "uploads/originals/"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Kan ikke oprette upload-destination: {e}"}), 500, _tus_headers()

    upload_id = secrets.token_urlsafe(18)
    data_path, _ = _tus_upload_paths(upload_id)
    try:
        with data_path.open("wb"):
            pass
    except Exception as e:
        return jsonify({"ok": False, "error": f"Unable to create upload: {e}"}), 500, _tus_headers()

    try:
        last_modified_ms = int(str(meta.get("lastModified") or "0").strip() or "0")
    except Exception:
        last_modified_ms = 0

    uploader_label = _share_get_visitor_name(share) or "Share-bruger"
    upload_meta: Dict[str, Any] = {
        "id": upload_id,
        "filename": filename,
        "destination": UPLOAD_DEST_UPLOADS,
        "subdir": subdir,
        "upload_length": upload_length,
        "upload_offset": 0,
        "target_dir": str(target_dir),
        "rel_prefix": rel_prefix,
        "last_modified_ms": last_modified_ms,
        # Label uploaded_by with visitor name for UI chips
        "uploaded_by": uploader_label,
        "created_at": now_iso(),
    }
    _tus_store_meta(upload_id, upload_meta)

    try:
        log_event("share_tus_created", upload_id=upload_id, filename=filename, subdir=subdir, upload_length=upload_length)
    except Exception:
        pass

    resp = make_response("", 201)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Location"] = url_for("api_share_tus_file", token=token, upload_id=upload_id)
    resp.headers["Upload-Offset"] = "0"
    return resp


@app.route("/api/share/<token>/upload/tus/<upload_id>", methods=["HEAD"])
def api_share_tus_head(token: str, upload_id: str):
    fb = _tus_require_version()
    if fb:
        return jsonify(fb[0]), fb[1], _tus_headers()

    meta = _tus_load_meta(upload_id)
    if not meta:
        return jsonify({"ok": False, "error": "Upload not found"}), 404, _tus_headers()

    data_path, _ = _tus_upload_paths(upload_id)
    offset = int(meta.get("upload_offset") or 0)
    try:
        if data_path.exists():
            offset = int(data_path.stat().st_size)
    except Exception:
        pass

    resp = make_response("", 204)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Upload-Offset"] = str(max(0, offset))
    resp.headers["Upload-Length"] = str(int(meta.get("upload_length") or 0))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/share/<token>/upload/tus/<upload_id>", methods=["PATCH"])
def api_share_tus_file(token: str, upload_id: str):
    fb = _tus_require_version()
    if fb:
        return jsonify(fb[0]), fb[1], _tus_headers()
    if str(request.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower() != "application/offset+octet-stream":
        return jsonify({"ok": False, "error": "Invalid Content-Type"}), 415, _tus_headers()

    meta = _tus_load_meta(upload_id)
    if not meta:
        return jsonify({"ok": False, "error": "Upload not found"}), 404, _tus_headers()

    data_path, meta_path = _tus_upload_paths(upload_id)
    if not data_path.exists():
        return jsonify({"ok": False, "error": "Upload data missing"}), 410, _tus_headers()

    try:
        req_offset = int(str(request.headers.get("Upload-Offset") or "0").strip())
    except Exception:
        return jsonify({"ok": False, "error": "Invalid Upload-Offset"}), 400, _tus_headers()

    current_size = int(data_path.stat().st_size)
    try:
        log_event("share_tus_patch", upload_id=upload_id, req_offset=req_offset, current_size=current_size)
    except Exception:
        pass
    if req_offset != current_size:
        resp = make_response("", 409)
        for k, v in _tus_headers().items():
            resp.headers[k] = v
        resp.headers["Upload-Offset"] = str(current_size)
        return resp

    body = request.get_data(cache=False, as_text=False) or b""
    try:
        with data_path.open("ab") as fh:
            if body:
                fh.write(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Unable to write upload chunk: {e}"}), 500, _tus_headers()

    new_offset = int(data_path.stat().st_size)
    total_length = int(meta.get("upload_length") or 0)
    meta["upload_offset"] = new_offset
    _tus_store_meta(upload_id, meta)

    if total_length > 0 and new_offset >= total_length:
        target_dir = Path(str(meta.get("target_dir") or ""))
        rel_prefix = str(meta.get("rel_prefix") or "uploads/")
        subdir = str(meta.get("subdir") or "")
        filename = str(meta.get("filename") or "")
        uploaded_by = str(meta.get("uploaded_by") or f"share:{token}")
        try:
            last_modified_ms = int(meta.get("last_modified_ms") or 0)
        except Exception:
            last_modified_ms = 0

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            ok, saved_name, err = _commit_uploaded_file(
                target_dir=target_dir,
                rel_prefix=rel_prefix,
                subdir=subdir,
                source_path=data_path,
                original_name=filename,
                last_modified_ms=last_modified_ms,
                uploaded_by=uploaded_by,
                autostart_postprocess=False,
            )
            try:
                meta_path.unlink(missing_ok=True)
            except Exception:
                pass
            if ok:
                try:
                    log_event("share_tus_done", saved=1, errors=0)
                except Exception:
                    pass
            else:
                try:
                    log_event("error", filename=filename, error=err)
                except Exception:
                    pass
                return jsonify({"ok": False, "error": err or "Upload finalize failed"}), 500, _tus_headers({"Upload-Offset": str(new_offset)})
        except Exception as e:
            return jsonify({"ok": False, "error": f"Upload finalize failed: {e}"}), 500, _tus_headers({"Upload-Offset": str(new_offset)})

    resp = make_response("", 204)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Upload-Offset"] = str(new_offset)
    resp.headers["Cache-Control"] = "no-store"
    return resp

# Allow proxies that block PATCH to use POST + X-HTTP-Method-Override: PATCH
@app.route("/api/share/<token>/upload/tus/<upload_id>", methods=["POST"])
def api_share_tus_file_override(token: str, upload_id: str):
    method_override = str(request.headers.get("X-HTTP-Method-Override") or "").strip().upper()
    if method_override == "PATCH":
        return api_share_tus_file(token, upload_id)
    return jsonify({"ok": False, "error": "Unsupported method"}), 405, _tus_headers()


@app.route("/api/share/<token>/upload/transfer-state", methods=["POST"])
def api_share_upload_transfer_state(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401
    if int(share["can_upload"] or 0) != 1:
        return jsonify({"ok": False, "error": "Upload ikke tilladt"}), 403
    data = request.get_json(silent=True) or {}
    active = bool(data.get("active"))
    uploaded_by = _share_get_visitor_name(share) or "Share-bruger"
    _set_upload_transfer_active(uploaded_by, active)
    return jsonify({"ok": True, "active": _is_upload_transfer_active(uploaded_by)})


@app.route("/api/share/<token>/upload/postprocess", methods=["POST"])
def api_share_upload_postprocess(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401
    if int(share["can_upload"] or 0) != 1:
        return jsonify({"ok": False, "error": "Upload ikke tilladt"}), 403

    uploaded_by = _share_get_visitor_name(share) or "Share-bruger"
    workflow_mode = upload_workflow_mode()
    if _is_upload_transfer_active(uploaded_by):
        with UPLOAD_PENDING_LOCK:
            pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
        return jsonify({
            "ok": False,
            "error": "Upload er stadig i gang",
            "uploading": True,
            "started": False,
            "running": False,
            "pending": pending_count,
            "workflow_mode": workflow_mode,
        }), 409
    rels = _pop_uploaded_rels(uploaded_by)

    if _is_upload_postprocess_running(uploaded_by):
        for rel in rels:
            _queue_uploaded_rel(uploaded_by, rel)
        running_state = _get_upload_postprocess_state(uploaded_by)
        with UPLOAD_PENDING_LOCK:
            pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
        return jsonify({
            "ok": True,
            "started": False,
            "running": True,
            "pending": pending_count,
            "workflow_mode": running_state.get("workflow_mode") if isinstance(running_state, dict) else workflow_mode,
            "process_status": running_state.get("process_status") if isinstance(running_state, dict) else None,
        })

    if not rels:
        rels = _recover_uploaded_rels_missing_postprocess(uploaded_by)

    if not rels:
        state = _get_upload_postprocess_state(uploaded_by)
        return jsonify({
            "ok": True,
            "started": False,
            "running": bool(state.get("running")) if isinstance(state, dict) else False,
            "pending": 0,
            "recoverable_pending": 0,
            "workflow_mode": (state.get("workflow_mode") if isinstance(state, dict) else None) or workflow_mode,
            "process_status": state.get("process_status") if isinstance(state, dict) else None,
            "result": state.get("result") if isinstance(state, dict) else None,
            "error": state.get("error") if isinstance(state, dict) else None,
        })

    _clear_stop_all_barrier()
    _mark_upload_postprocess_starting(uploaded_by, workflow_mode, len(rels))
    threading.Thread(target=_upload_postprocess_worker, args=(uploaded_by, rels), daemon=True).start()
    with UPLOAD_PENDING_LOCK:
        pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
    return jsonify({"ok": True, "started": True, "running": True, "pending": pending_count, "queued": len(rels), "workflow_mode": workflow_mode})


@app.route("/api/share/<token>/upload/postprocess/status")
def api_share_upload_postprocess_status(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401
    if int(share["can_upload"] or 0) != 1:
        return jsonify({"ok": False, "error": "Upload ikke tilladt"}), 403

    uploaded_by = _share_get_visitor_name(share) or "Share-bruger"
    workflow_mode = upload_workflow_mode()
    state = _get_upload_postprocess_state(uploaded_by)
    with UPLOAD_PENDING_LOCK:
        pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
    if not state:
        return jsonify({"ok": True, "running": False, "pending": pending_count, "workflow_mode": workflow_mode, "process_status": None, "result": None, "error": None, "phase": None, "current_rel": None, "stage_processed": 0, "stage_total": 0})
    return jsonify(
        {
            "ok": True,
            "running": bool(state.get("running")),
            "pending": pending_count,
            "workflow_mode": state.get("workflow_mode") or workflow_mode,
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
            "result": state.get("result"),
            "error": state.get("error"),
            "phase": state.get("phase"),
            "process_status": state.get("process_status"),
            "current_rel": state.get("current_rel"),
            "stage_processed": int(state.get("stage_processed") or 0),
            "stage_total": int(state.get("stage_total") or 0),
        }
    )


@app.route("/api/share/<token>/delete", methods=["POST"])
def api_share_delete(token: str):
    share = _load_share_from_token(token, touch=True)
    if not share:
        return jsonify({"ok": False, "error": "Share ugyldig eller udlÃ¸bet"}), 404
    if not _share_is_authorized(share):
        return jsonify({
            "ok": False,
            "password_required": _share_is_password_protected(share),
            "name_required": _share_requires_visitor_name(share),
            "error": "Adgang krÃ¦ves",
        }), 401
    if int(share["can_delete"] or 0) != 1:
        return jsonify({"ok": False, "error": "Sletning ikke tilladt"}), 403

    body = request.get_json(silent=True) or {}
    raw_ids = body.get("photo_ids")
    if not isinstance(raw_ids, list):
        return jsonify({"ok": False, "error": "Angiv photo_ids"}), 400
    ids = [int(pid) for pid in raw_ids if str(pid).isdigit()]
    if not ids:
        return jsonify({"ok": False, "error": "Ingen billeder valgt"}), 400

    with closing(get_conn()) as conn:
        allowed_ids: list[int] = []
        for pid in ids:
            row = _get_share_scoped_photo_row(conn, share, pid)
            if row:
                allowed_ids.append(int(row["id"]))

    if not allowed_ids:
        return jsonify({"ok": False, "error": "Ingen gyldige billeder valgt"}), 400

    removed = _delete_indexed_photos_by_ids(allowed_ids)
    return jsonify({"ok": True, "removed": removed, "deleted_ids": allowed_ids})


@app.route("/api/health")
def api_health():
    sqlite_effective_mode = SQLITE_JOURNAL_MODE
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("PRAGMA journal_mode").fetchone()
            if row and len(row):
                sqlite_effective_mode = str(row[0] or sqlite_effective_mode).upper()
    except Exception:
        pass
    return jsonify({
        "ok": True,
        "photo_dir": str(PHOTO_DIR),
        "photo_dir_exists": PHOTO_DIR.exists(),
        "data_dir": str(DATA_DIR),
        "data_dir_fs_type": DATA_DIR_FS_TYPE,
        "upload_dir": str(UPLOAD_DIR),
        "upload_dir_fs_type": UPLOAD_DIR_FS_TYPE,
        "thumb_dir": str(THUMB_DIR),
        "thumb_dir_fs_type": THUMB_DIR_FS_TYPE,
        "db_path": str(DB_PATH),
        "sqlite_journal_mode_configured": SQLITE_JOURNAL_MODE,
        "sqlite_journal_mode_effective": sqlite_effective_mode,
        "sqlite_busy_timeout_ms": int(SQLITE_BUSY_TIMEOUT_MS),
        "library_source_enabled": bool(ENABLE_LIBRARY_SOURCE),
        "scan_features_enabled": bool(ENABLE_SCAN_FEATURES),
        "rawpy_available": bool(rawpy is not None),
        "ai": _ai_health(),
    })


def _require_admin_for_app_update() -> Optional[Tuple[dict, int]]:
    if not getattr(current_user, "is_admin", False):
        return ({"ok": False, "error": "Forbidden"}, 403)
    return None


def _app_update_clamp_interval_minutes(value: Any) -> int:
    try:
        minutes = int(float(value))
    except Exception:
        minutes = APP_UPDATE_AUTO_CHECK_DEFAULT_INTERVAL_MINUTES
    return max(5, min(1440, minutes))


def _app_update_default_state() -> Dict[str, Any]:
    interval = _app_update_clamp_interval_minutes(APP_UPDATE_AUTO_CHECK_DEFAULT_INTERVAL_MINUTES)
    return {
        "running": False,
        "status": "idle",
        "started_at": "",
        "finished_at": "",
        "returncode": None,
        "job_id": "",
        "auto_check_enabled": bool(APP_UPDATE_AUTO_CHECK_DEFAULT_ENABLED),
        "auto_check_interval_minutes": interval,
        "last_check_at": "",
        "last_check_source": "",
        "last_auto_check_at": "",
        "next_auto_check_at": "",
        "next_auto_check_epoch": 0,
    }


def _app_update_set_next_auto_check(state: Dict[str, Any], from_epoch: Optional[float] = None) -> Dict[str, Any]:
    base = float(from_epoch or time.time())
    interval_sec = _app_update_clamp_interval_minutes(state.get("auto_check_interval_minutes")) * 60
    next_epoch = base + interval_sec
    state["next_auto_check_epoch"] = next_epoch
    state["next_auto_check_at"] = datetime.utcfromtimestamp(next_epoch).replace(microsecond=0).isoformat() + "Z"
    return state


def _app_update_normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    merged = _app_update_default_state()
    merged.update(state or {})
    merged["auto_check_enabled"] = bool(merged.get("auto_check_enabled"))
    merged["auto_check_interval_minutes"] = _app_update_clamp_interval_minutes(merged.get("auto_check_interval_minutes"))
    try:
        merged["next_auto_check_epoch"] = float(merged.get("next_auto_check_epoch") or 0)
    except Exception:
        merged["next_auto_check_epoch"] = 0
    if merged.get("auto_check_enabled"):
        if float(merged.get("next_auto_check_epoch") or 0) <= 0:
            _app_update_set_next_auto_check(merged)
    else:
        merged["next_auto_check_epoch"] = 0
        merged["next_auto_check_at"] = ""
    return merged


def _app_update_read_state_local() -> Dict[str, Any]:
    with APP_UPDATE_STATE_LOCK:
        try:
            if APP_UPDATE_STATE_PATH.exists():
                raw = json.loads(APP_UPDATE_STATE_PATH.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    return _app_update_normalize_state(raw)
        except Exception:
            pass
    return _app_update_normalize_state({})


def _app_update_write_state_local(state: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _app_update_normalize_state(state)
    with APP_UPDATE_STATE_LOCK:
        APP_UPDATE_STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = APP_UPDATE_STATE_PATH.with_suffix(APP_UPDATE_STATE_PATH.suffix + ".tmp")
        tmp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(APP_UPDATE_STATE_PATH)
    return normalized


def _app_update_settings_payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    s = _app_update_normalize_state(state)
    return {
        "ok": True,
        "auto_check_enabled": bool(s.get("auto_check_enabled")),
        "auto_check_interval_minutes": _app_update_clamp_interval_minutes(s.get("auto_check_interval_minutes")),
        "last_check_at": str(s.get("last_check_at") or ""),
        "last_check_source": str(s.get("last_check_source") or ""),
        "last_auto_check_at": str(s.get("last_auto_check_at") or ""),
        "next_auto_check_at": str(s.get("next_auto_check_at") or ""),
    }


def _app_update_is_legacy_not_found(proxy_response: Any, proxy_status: Any) -> bool:
    try:
        if int(proxy_status) != 404:
            return False
    except Exception:
        return False
    try:
        data = proxy_response.get_json(silent=True) if proxy_response is not None else {}
    except Exception:
        data = {}
    err = str((data or {}).get("error") or "").strip().lower()
    return err == "not found"


def _app_update_proxy(path: str, method: str = "GET", payload: Optional[dict] = None, timeout: Optional[float] = None):
    if not APP_UPDATE_SERVICE_URL:
        return jsonify(
            {
                "ok": False,
                "available": False,
                "service_reachable": False,
                "error": "FjordLens updater-service er ikke konfigureret.",
            }
        ), 503
    clean_path = "/" + str(path or "").strip("/")
    url = f"{APP_UPDATE_SERVICE_URL}{clean_path}"
    try:
        resp = requests.request(
            method.upper(),
            url,
            json=(payload if payload is not None else None),
            timeout=float(timeout or APP_UPDATE_SERVICE_TIMEOUT_SEC),
        )
        try:
            data = resp.json()
        except Exception:
            data = {"ok": False, "error": (resp.text or "")[:500] or "Updater-service svarede ikke med JSON."}
        if isinstance(data, dict):
            data.setdefault("service_reachable", True)
            data.setdefault("updater_url", APP_UPDATE_SERVICE_URL)
        return jsonify(data), resp.status_code
    except Exception as e:
        return jsonify(
            {
                "ok": False,
                "available": False,
                "service_reachable": False,
                "updater_url": APP_UPDATE_SERVICE_URL,
                "error": "FjordLens updater-service er ikke tilgaengelig.",
                "detail": str(e),
            }
        ), 503


@app.route("/api/app-update/status", methods=["GET"])
@login_required
def api_app_update_status():
    fb = _require_admin_for_app_update()
    if fb:
        return jsonify(fb[0]), fb[1]
    return _app_update_proxy("/status", method="GET", timeout=5)


@app.route("/api/app-update/check", methods=["POST"])
@login_required
def api_app_update_check():
    fb = _require_admin_for_app_update()
    if fb:
        return jsonify(fb[0]), fb[1]
    return _app_update_proxy("/check", method="POST", payload={}, timeout=90)


@app.route("/api/app-update/start", methods=["POST"])
@login_required
def api_app_update_start():
    fb = _require_admin_for_app_update()
    if fb:
        return jsonify(fb[0]), fb[1]
    body = request.get_json(silent=True) or {}
    cleanup = True
    if "cleanup" in body:
        cleanup = bool(body.get("cleanup"))
    return _app_update_proxy("/start", method="POST", payload={"cleanup": cleanup}, timeout=10)


@app.route("/api/app-update/settings", methods=["GET", "POST"])
@login_required
def api_app_update_settings():
    fb = _require_admin_for_app_update()
    if fb:
        return jsonify(fb[0]), fb[1]
    if request.method == "GET":
        proxy_response, proxy_status = _app_update_proxy("/settings", method="GET", timeout=5)
        if not _app_update_is_legacy_not_found(proxy_response, proxy_status):
            return proxy_response, proxy_status
        return jsonify(_app_update_settings_payload_from_state(_app_update_read_state_local())), 200
    body = request.get_json(silent=True) or {}
    payload = {
        "auto_check_enabled": bool(body.get("auto_check_enabled")),
        "auto_check_interval_minutes": body.get("auto_check_interval_minutes"),
    }
    proxy_response, proxy_status = _app_update_proxy("/settings", method="POST", payload=payload, timeout=10)
    if not _app_update_is_legacy_not_found(proxy_response, proxy_status):
        return proxy_response, proxy_status

    state = _app_update_read_state_local()
    state["auto_check_enabled"] = bool(payload.get("auto_check_enabled"))
    state["auto_check_interval_minutes"] = payload.get("auto_check_interval_minutes")
    if state.get("auto_check_enabled"):
        _app_update_set_next_auto_check(state)
    else:
        state["next_auto_check_epoch"] = 0
        state["next_auto_check_at"] = ""
    saved_state = _app_update_write_state_local(state)
    return jsonify(_app_update_settings_payload_from_state(saved_state)), 200


@app.route("/api/photoframes/status", methods=["GET"])
@login_required
def api_photoframes_status():
    checked_at = now_iso()
    now_ts = time.time()
    records = _load_photoframe_token_records()
    latest_version = _sanitize_photoframe_text(_get_setting(PHOTOFRAME_LATEST_VERSION_KEY, ""), 80)
    latest_version_at = _sanitize_photoframe_text(_get_setting(PHOTOFRAME_LATEST_VERSION_AT_KEY, ""), 40)
    records_sorted = sorted(
        records,
        key=lambda r: str(r.get("created_at") or ""),
    )
    items: list[Dict[str, Any]] = []
    with closing(get_conn()) as conn:
        for idx, rec in enumerate(records_sorted, start=1):
            rec_id = _sanitize_photoframe_text(rec.get("id"), 64) or f"pf-token-{idx}"
            token_hint = _sanitize_photoframe_text(rec.get("token_hint"), 16)
            token_plain = _sanitize_photoframe_token_plain(rec.get("token_plain"))
            scope_mode, scope_folders, scope_photo_ids = _photoframe_record_scope(rec)
            last_seen_at = _sanitize_photoframe_text(rec.get("last_seen_at"), 40)
            seen_ts = _parse_iso_to_epoch(last_seen_at)
            online = bool(seen_ts and ((now_ts - seen_ts) <= PHOTOFRAME_ONLINE_WINDOW_SEC))
            settings_base = _photoframe_settings_proxy_base_url(rec)
            device_name = _sanitize_photoframe_text(rec.get("device_name"), 80)
            name = device_name or (f"Fotoramme {idx}")
            update_job_id = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
            update_status = _sanitize_photoframe_update_status(rec.get("update_status"))
            update_message = _sanitize_photoframe_text(rec.get("update_message"), 240)
            update_requested_at = _sanitize_photoframe_text(rec.get("update_requested_at"), 40)
            update_started_at = _sanitize_photoframe_text(rec.get("update_started_at"), 40)
            update_finished_at = _sanitize_photoframe_text(rec.get("update_finished_at"), 40)
            update_last_report_at = _sanitize_photoframe_text(rec.get("update_last_report_at"), 40)
            update_version = _sanitize_photoframe_text(rec.get("update_version"), 80)
            update_package_mode = _normalize_photoframe_update_package_mode(rec.get("update_package_mode"))
            settings_web_active = _sanitize_photoframe_bool(rec.get("settings_web_active"))
            settings_web_started_at = _sanitize_photoframe_text(rec.get("settings_web_started_at"), 40)
            settings_web_last_activity_at = _sanitize_photoframe_text(rec.get("settings_web_last_activity_at"), 40)
            feed_sync_status = _sanitize_photoframe_feed_sync_status(rec.get("feed_sync_status"))
            feed_sync_sent_at = _sanitize_photoframe_text(rec.get("feed_sync_sent_at"), 40)
            feed_sync_acked_at = _sanitize_photoframe_text(rec.get("feed_sync_acked_at"), 40)
            feed_sync_count = _sanitize_photoframe_feed_sync_count(rec.get("feed_sync_count"))
            local_ip = _sanitize_photoframe_text(rec.get("last_local_ip"), 120)
            net_ip = _sanitize_photoframe_text(rec.get("last_ip"), 120)
            display_ip = net_ip or local_ip
            device_version = _sanitize_photoframe_text(rec.get("device_version"), 80) or _sanitize_photoframe_text(rec.get("update_version"), 80)
            version_status = "unknown"
            if latest_version:
                if device_version and (device_version == latest_version):
                    version_status = "latest"
                elif device_version:
                    version_status = "outdated"
            error = ""
            if not last_seen_at:
                error = "Ingen forbindelse endnu"
            elif not online:
                error = "Offline"
            preview = _photoframe_status_preview(conn, rec)

            items.append(
                {
                    "id": rec_id,
                    "name": name,
                    "base_url": "",
                    "info_url": "",
                    "location": "",
                    "note": "",
                    "online": online,
                    "http_status": 200 if online else None,
                    "latency_ms": None,
                    "error": error,
                    "ip": display_ip,
                    "net_ip": net_ip,
                    "local_ip": local_ip,
                    "feed_url": "",
                    "setup_complete": None,
                    "checked_at": checked_at,
                    "settings_proxy_url": f"/api/photoframes/{quote(rec_id, safe='')}/settings-proxy",
                    "settings_available": bool(settings_base),
                    "token_hint": token_hint,
                    "token_available": bool(token_plain),
                    "scope_mode": scope_mode,
                    "allowed_folder_count": len(scope_folders),
                    "allowed_photo_count": len(scope_photo_ids),
                    "last_seen_at": last_seen_at,
                    "created_at": _sanitize_photoframe_text(rec.get("created_at"), 40),
                    "preview_photo_id": preview.get("preview_photo_id"),
                    "preview_thumb_url": _sanitize_photoframe_text(preview.get("preview_thumb_url"), 300),
                    "preview_updated_at": _sanitize_photoframe_text(preview.get("preview_updated_at"), 40),
                    "update_job_id": update_job_id,
                    "update_status": update_status,
                    "update_message": update_message,
                    "update_requested_at": update_requested_at,
                    "update_started_at": update_started_at,
                    "update_finished_at": update_finished_at,
                    "update_last_report_at": update_last_report_at,
                    "update_version": update_version,
                    "update_package_mode": update_package_mode,
                    "settings_web_active": settings_web_active,
                    "settings_web_started_at": settings_web_started_at,
                    "settings_web_last_activity_at": settings_web_last_activity_at,
                    "device_version": device_version,
                    "version_status": version_status,
                    "content_sync_status": feed_sync_status,
                    "content_sync_sent_at": feed_sync_sent_at,
                    "content_sync_acked_at": feed_sync_acked_at,
                    "content_sync_count": feed_sync_count,
                }
            )

    return jsonify(
        {
            "ok": True,
            "items": items,
            "count": len(items),
            "checked_at": checked_at,
            "source": "tokens",
            "config_path": "settings:photoframe_tokens",
            "timeout_sec": PHOTOFRAME_STATUS_TIMEOUT_SEC,
            "latest_version": latest_version,
            "latest_version_at": latest_version_at,
        }
    )


@app.route("/api/photoframes", methods=["POST"])
@login_required
def api_photoframes_create():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    token = secrets.token_urlsafe(24)
    created_at = now_iso()
    records = _load_photoframe_token_records()
    records.append(
        {
            "id": f"pf-token-{int(time.time())}-{secrets.token_hex(3)}",
            "token_hash": _share_token_digest(token),
            "token_hint": token[-4:],
            "token_plain": token,
            "scope_mode": "all",
            "allowed_folders": [],
            "allowed_photo_ids": [],
            "created_at": created_at,
            "device_version": "",
            "update_job_id": "",
            "update_status": "",
            "update_message": "",
            "update_requested_at": "",
            "update_started_at": "",
            "update_finished_at": "",
            "update_last_report_at": "",
            "update_version": "",
            "update_package_url": "",
            "update_package_sha256": "",
            "update_settings_payload": {},
            "feed_sync_status": "",
            "feed_sync_sent_rev": "",
            "feed_sync_sent_at": "",
            "feed_sync_acked_rev": "",
            "feed_sync_acked_at": "",
            "feed_sync_count": 0,
            "wifi_scan_networks": [],
            "wifi_scan_scanned_at": "",
            "wifi_scan_error": "",
            "settings_web_active": False,
            "settings_web_started_at": "",
            "settings_web_last_activity_at": "",
        }
    )
    _save_photoframe_token_records(records)

    server_url = _request_public_base_url() or request.url_root.rstrip("/")
    feed_url = f"{server_url}/api/frame/{token}/feed"
    return jsonify(
        {
            "ok": True,
            "token": token,
            "server_url": server_url,
            "feed_url": feed_url,
            "created_at": created_at,
        }
    )


@app.route("/api/photoframes/<token_id>/token", methods=["GET"])
@login_required
def api_photoframes_get_token(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id"}), 400

    records = _load_photoframe_token_records()
    for rec in records:
        rec_id = _sanitize_photoframe_text(rec.get("id"), 64)
        if rec_id != target_id:
            continue
        token_plain = _sanitize_photoframe_token_plain(rec.get("token_plain"))
        if not token_plain:
            return jsonify({"ok": False, "error": "Token kan ikke vises for denne post. Opret evt. en ny token."}), 404
        return jsonify(
            {
                "ok": True,
                "id": rec_id,
                "token": token_plain,
                "token_hint": _sanitize_photoframe_text(rec.get("token_hint"), 16),
                "name": _sanitize_photoframe_text(rec.get("device_name"), 80),
            }
        )

    return jsonify({"ok": False, "error": "Token ikke fundet"}), 404


@app.route("/api/photoframes/<token_id>/update", methods=["POST"])
@login_required
def api_photoframes_trigger_update(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id"}), 400

    records = _load_photoframe_token_records()
    rec_idx = -1
    rec: Optional[Dict[str, Any]] = None
    for idx, it in enumerate(records):
        rec_id = _sanitize_photoframe_text(it.get("id"), 64)
        if rec_id == target_id:
            rec_idx = idx
            rec = it
            break
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Token ikke fundet"}), 404

    body: Dict[str, Any] = {}
    upload_zip = None
    content_type = str(request.content_type or "").lower()
    if "multipart/form-data" in content_type:
        try:
            body = dict(request.form or {})
        except Exception:
            body = {}
        upload_zip = (
            request.files.get("package_zip")
            or request.files.get("package")
            or request.files.get("file")
        )
    else:
        body_json = request.get_json(silent=True)
        if isinstance(body_json, dict):
            body = body_json

    requested_version = _sanitize_photoframe_text(body.get("version"), 80)
    requested_sha = _sanitize_photoframe_update_sha256(body.get("package_sha256"))
    requested_url = _normalize_photoframe_http_url(body.get("package_url"))

    job_id = _sanitize_photoframe_update_job_id(f"pfupd-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return jsonify({"ok": False, "error": "Kunne ikke oprette update-id"}), 500

    token_plain = _sanitize_photoframe_token_plain(rec.get("token_plain"))
    if not token_plain:
        return jsonify({"ok": False, "error": "Token kan ikke bruges til update-link. Opret ny token."}), 400
    frame_preferred_base = _normalize_photoframe_base_url(rec.get("last_server_base_url"))
    request_base = frame_preferred_base or _request_public_base_url() or request.url_root.rstrip("/")

    package_url = requested_url or ""
    package_mode = "custom-url" if requested_url else "source-dir"
    upload_mode = False
    upload_bytes = 0
    if upload_zip is not None:
        filename = secure_filename(str(getattr(upload_zip, "filename", "") or ""))
        if not filename:
            return jsonify({"ok": False, "error": "Vaelg en zip-fil foerst"}), 400
        # Upload-based updates always get an auto-generated timestamp version.
        requested_version = _autogen_photoframe_upload_version()
        _, uploaded_sha, upload_bytes, upload_err = _save_uploaded_photoframe_package(upload_zip, job_id)
        if upload_err:
            return jsonify({"ok": False, "error": f"Zip upload fejlede: {upload_err}"}), 400
        requested_sha = uploaded_sha
        package_url = f"{request_base}{url_for('api_frame_uploaded_update_package', token=token_plain, job_id=job_id, _external=False)}"
        upload_mode = True
        package_mode = "upload"
    elif not package_url:
        package_root = _resolve_photoframe_package_root()
        if not package_root:
            return jsonify(
                {
                    "ok": False,
                    "error": "Ingen opdateringskilde fundet. Saet PHOTOFRAME_UPDATE_SOURCE_DIR, upload zip, eller send package_url i request body.",
                }
            ), 400
        package_url = f"{request_base}{url_for('api_frame_update_package', token=token_plain, job_id=job_id, _external=False)}"

    now = now_iso()
    rec["update_job_id"] = job_id
    rec["update_status"] = "queued"
    rec["update_message"] = "Venter p\u00e5 enheden"
    rec["update_requested_at"] = now
    rec["update_started_at"] = ""
    rec["update_finished_at"] = ""
    rec["update_last_report_at"] = now
    rec["update_version"] = requested_version
    rec["update_package_url"] = package_url
    rec["update_package_mode"] = package_mode
    rec["update_package_sha256"] = requested_sha
    rec["update_settings_payload"] = {}
    _save_photoframe_token_records(records)
    if requested_version:
        _set_setting(PHOTOFRAME_LATEST_VERSION_KEY, requested_version)
        _set_setting(PHOTOFRAME_LATEST_VERSION_AT_KEY, now)

    return jsonify(
        {
            "ok": True,
            "id": target_id,
            "job_id": job_id,
            "status": "queued",
            "package_url": package_url,
            "source": "upload" if upload_mode else ("custom-url" if requested_url else "source-dir"),
            "upload_bytes": upload_bytes if upload_mode else 0,
            "version": requested_version or None,
            "requested_at": now,
        }
    )


@app.route("/api/photoframes/<token_id>/restart", methods=["POST"])
@login_required
def api_photoframes_restart_kiosk(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id"}), 400

    records = _load_photoframe_token_records()
    rec_idx = -1
    rec: Optional[Dict[str, Any]] = None
    for idx, it in enumerate(records):
        rec_id = _sanitize_photoframe_text(it.get("id"), 64)
        if rec_id == target_id:
            rec_idx = idx
            rec = it
            break
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Token ikke fundet"}), 404

    ok_restart, restart_info = _photoframe_queue_restart_command(rec)
    if not ok_restart:
        return jsonify({"ok": False, "error": restart_info or "Kunne ikke sende kiosk-genstart"}), 409
    job_id = str(restart_info or "").strip()
    _save_photoframe_token_records(records)

    return jsonify(
        {
            "ok": True,
            "id": target_id,
            "job_id": job_id,
            "status": "queued",
            "requested_at": _sanitize_photoframe_text(rec.get("update_requested_at"), 40) or now_iso(),
        }
    )


@app.route("/api/photoframes/<token_id>/reset", methods=["POST"])
@login_required
def api_photoframes_reset_device(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id"}), 400

    records = _load_photoframe_token_records()
    rec_idx = -1
    rec: Optional[Dict[str, Any]] = None
    for idx, it in enumerate(records):
        rec_id = _sanitize_photoframe_text(it.get("id"), 64)
        if rec_id == target_id:
            rec_idx = idx
            rec = it
            break
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Token ikke fundet"}), 404

    ok_reset, reset_info = _photoframe_queue_reset_command(rec)
    if not ok_reset:
        return jsonify({"ok": False, "error": reset_info or "Kunne ikke sende nulstilling"}), 409
    job_id = str(reset_info or "").strip()
    _save_photoframe_token_records(records)

    return jsonify(
        {
            "ok": True,
            "id": target_id,
            "job_id": job_id,
            "status": "queued",
            "requested_at": _sanitize_photoframe_text(rec.get("update_requested_at"), 40) or now_iso(),
        }
    )


@app.route("/api/photoframes/<token_id>/settings-command", methods=["POST"])
@login_required
def api_photoframes_settings_command(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Kun administrator kan sende fjernindstillinger."}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id."}), 400

    records = _load_photoframe_token_records()
    rec_idx = -1
    rec: Optional[Dict[str, Any]] = None
    for idx, it in enumerate(records):
        rec_id = _sanitize_photoframe_text(it.get("id"), 64)
        if rec_id == target_id:
            rec_idx = idx
            rec = it
            break
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Fotoramme blev ikke fundet."}), 404

    settings_payload, err = _photoframe_extract_settings_payload_from_request(request)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    ok_queue, queue_info = _photoframe_queue_settings_command(rec, settings_payload)
    if not ok_queue:
        return jsonify({"ok": False, "error": queue_info or "Kunne ikke sende indstillinger"}), 409
    job_id = str(queue_info or "").strip()
    _save_photoframe_token_records(records)

    return jsonify(
        {
            "ok": True,
            "id": target_id,
            "job_id": job_id,
            "status": "queued",
            "requested_at": _sanitize_photoframe_text(rec.get("update_requested_at"), 40) or now_iso(),
        }
    )


@app.route("/api/photoframes/<token_id>/update/cancel", methods=["POST"])
@login_required
def api_photoframes_cancel_update(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id"}), 400

    records = _load_photoframe_token_records()
    rec_idx = -1
    rec: Optional[Dict[str, Any]] = None
    for idx, it in enumerate(records):
        rec_id = _sanitize_photoframe_text(it.get("id"), 64)
        if rec_id == target_id:
            rec_idx = idx
            rec = it
            break
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Token ikke fundet"}), 404

    current_job_id = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
    current_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    if (not current_job_id) and (not current_status):
        return jsonify(
            {
                "ok": True,
                "id": target_id,
                "status": "idle",
                "message": "Ingen aktiv opdatering",
            }
        )

    now = now_iso()
    prev_status = current_status or "queued"

    # Cancel command delivery and mark as stopped in UI.
    rec["update_job_id"] = ""
    rec["update_status"] = "failed"
    rec["update_message"] = "Stoppet manuelt fra FjordLens"
    rec["update_last_report_at"] = now
    if not _sanitize_photoframe_text(rec.get("update_started_at"), 40):
        rec["update_started_at"] = now
    rec["update_finished_at"] = now
    rec["update_package_url"] = ""
    rec["update_package_mode"] = ""
    rec["update_package_sha256"] = ""
    rec["update_settings_payload"] = {}

    _save_photoframe_token_records(records)
    return jsonify(
        {
            "ok": True,
            "id": target_id,
            "status": "cancelled",
            "previous_status": prev_status,
            "finished_at": now,
        }
    )


@app.route("/api/photoframes/update-all", methods=["POST"])
@login_required
def api_photoframes_trigger_update_all():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    records = _load_photoframe_token_records()
    if not records:
        return jsonify({"ok": False, "error": "Ingen fotorammer fundet"}), 400

    content_type = str(request.content_type or "").lower()
    if "multipart/form-data" not in content_type:
        return jsonify({"ok": False, "error": "Upload zip som multipart/form-data"}), 400

    try:
        body = dict(request.form or {})
    except Exception:
        body = {}
    upload_zip = (
        request.files.get("package_zip")
        or request.files.get("package")
        or request.files.get("file")
    )
    if upload_zip is None:
        return jsonify({"ok": False, "error": "Vaelg en zip-fil foerst"}), 400

    filename = secure_filename(str(getattr(upload_zip, "filename", "") or ""))
    if not filename:
        return jsonify({"ok": False, "error": "Vaelg en zip-fil foerst"}), 400

    # Global zip rollout always gets an auto-generated timestamp version.
    requested_version = _autogen_photoframe_upload_version()

    job_id = _sanitize_photoframe_update_job_id(f"pfupd-{int(time.time())}-{secrets.token_hex(4)}")
    if not job_id:
        return jsonify({"ok": False, "error": "Kunne ikke oprette update-id"}), 500

    _, uploaded_sha, upload_bytes, upload_err = _save_uploaded_photoframe_package(upload_zip, job_id)
    if upload_err:
        return jsonify({"ok": False, "error": f"Zip upload fejlede: {upload_err}"}), 400

    request_base_default = _request_public_base_url() or request.url_root.rstrip("/")
    now = now_iso()
    queued = 0
    skipped = 0
    for rec in records:
        if not isinstance(rec, dict):
            skipped += 1
            continue
        token_plain = _sanitize_photoframe_token_plain(rec.get("token_plain"))
        if not token_plain:
            skipped += 1
            continue
        frame_preferred_base = _normalize_photoframe_base_url(rec.get("last_server_base_url"))
        request_base = frame_preferred_base or request_base_default
        package_url = f"{request_base}{url_for('api_frame_uploaded_update_package', token=token_plain, job_id=job_id, _external=False)}"
        rec["update_job_id"] = job_id
        rec["update_status"] = "queued"
        rec["update_message"] = "Venter p\u00e5 enheden"
        rec["update_requested_at"] = now
        rec["update_started_at"] = ""
        rec["update_finished_at"] = ""
        rec["update_last_report_at"] = now
        rec["update_version"] = requested_version
        rec["update_package_url"] = package_url
        rec["update_package_mode"] = "upload"
        rec["update_package_sha256"] = uploaded_sha
        rec["update_settings_payload"] = {}
        queued += 1

    if queued <= 0:
        return jsonify({"ok": False, "error": "Ingen gyldige tokens at opdatere"}), 400

    _save_photoframe_token_records(records)
    if requested_version:
        _set_setting(PHOTOFRAME_LATEST_VERSION_KEY, requested_version)
        _set_setting(PHOTOFRAME_LATEST_VERSION_AT_KEY, now)

    return jsonify(
        {
            "ok": True,
            "job_id": job_id,
            "status": "queued",
            "queued_count": queued,
            "skipped_count": skipped,
            "upload_bytes": upload_bytes,
            "version": requested_version or None,
            "requested_at": now,
        }
    )


@app.route("/api/photoframes/<token_id>", methods=["DELETE"])
@login_required
def api_photoframes_delete(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id"}), 400

    records = _load_photoframe_token_records()
    kept = [r for r in records if _sanitize_photoframe_text(r.get("id"), 64) != target_id]
    if len(kept) == len(records):
        return jsonify({"ok": False, "error": "Token ikke fundet"}), 404

    _save_photoframe_token_records(kept)
    return jsonify({"ok": True, "deleted_id": target_id, "count": len(kept)})


@app.route("/api/photoframes/<token_id>/settings-ready", methods=["POST"])
@login_required
def api_photoframes_settings_ready(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Kun administrator kan åbne fjernindstillinger."}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id."}), 400

    records = _load_photoframe_token_records()
    _, rec = _photoframe_find_record_by_id(records, target_id)
    if not rec:
        return jsonify({"ok": False, "error": "Fotoramme blev ikke fundet."}), 404

    settings_proxy_url = f"/api/photoframes/{quote(target_id, safe='')}/settings-proxy"

    body = request.get_json(silent=True) or {}
    wait_raw = request.args.get("wait_sec")
    if wait_raw is None:
        wait_raw = body.get("wait_sec")
    try:
        wait_sec = float(wait_raw) if wait_raw is not None else 22.0
    except Exception:
        wait_sec = 22.0
    wait_sec = max(6.0, min(45.0, wait_sec))

    active_mode = _normalize_photoframe_update_package_mode(rec.get("update_package_mode"))
    active_status = _sanitize_photoframe_update_status(rec.get("update_status"))
    start_job_id = ""
    reused_existing_job = False
    if active_mode == "start-settings-web" and active_status in {"queued", "downloading", "installing", "restarting"}:
        start_job_id = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
        reused_existing_job = bool(start_job_id)

    if not start_job_id:
        ok_start, start_info = _photoframe_queue_start_settings_web_command(rec)
        if not ok_start:
            return jsonify(
                {
                    "ok": False,
                    "error": start_info or "Kunne ikke starte indstillinger på rammen.",
                    "settings_url": settings_proxy_url,
                    "fallback_available": True,
                }
            ), 409
        start_job_id = _sanitize_photoframe_update_job_id(start_info)
        if not start_job_id:
            return jsonify(
                {
                    "ok": False,
                    "error": "Kunne ikke oprette gyldigt settings-web job-id.",
                    "settings_url": settings_proxy_url,
                    "fallback_available": True,
                }
            ), 409
        _save_photoframe_token_records(records)

    started_at = time.time()
    deadline = started_at + wait_sec
    last_status = ""
    last_message = ""
    seen_at = ""
    while time.time() < deadline:
        records = _load_photoframe_token_records()
        rec_idx, current_rec = _photoframe_find_record_by_id(records, target_id)
        if rec_idx < 0 or not current_rec:
            return jsonify({"ok": False, "error": "Fotoramme blev ikke fundet."}), 404

        current_job_id = _sanitize_photoframe_update_job_id(current_rec.get("update_job_id"))
        current_status = _sanitize_photoframe_update_status(current_rec.get("update_status"))
        current_mode = _normalize_photoframe_update_package_mode(current_rec.get("update_package_mode"))
        current_message = _sanitize_photoframe_text(current_rec.get("update_message"), 240)
        current_seen_at = _sanitize_photoframe_text(current_rec.get("last_seen_at"), 40)

        if current_job_id == start_job_id:
            last_status = current_status
            last_message = current_message
            seen_at = current_seen_at
            if current_status == "success":
                if _photoframe_mark_settings_session_active(current_rec, now_iso()):
                    _save_photoframe_token_records(records)
                return jsonify(
                    {
                        "ok": True,
                        "settings_url": settings_proxy_url,
                        "start_acknowledged": True,
                        "start_job_id": start_job_id,
                        "reused_existing_job": reused_existing_job,
                        "seen_at": seen_at or None,
                    }
                )
            if current_status == "failed":
                err = current_message or "Rammen kunne ikke starte indstillinger."
                return jsonify(
                    {
                        "ok": False,
                        "error": err,
                        "settings_url": settings_proxy_url,
                        "fallback_available": True,
                        "start_acknowledged": False,
                        "start_job_id": start_job_id,
                        "reused_existing_job": reused_existing_job,
                    }
                ), 409
        elif current_mode == "start-settings-web" and current_status == "success":
            if _photoframe_mark_settings_session_active(current_rec, now_iso()):
                _save_photoframe_token_records(records)
            return jsonify(
                {
                    "ok": True,
                    "settings_url": settings_proxy_url,
                    "start_acknowledged": True,
                    "start_job_id": current_job_id or start_job_id,
                    "reused_existing_job": True,
                    "seen_at": current_seen_at or None,
                }
            )

        try:
            time.sleep(1.0)
        except Exception:
            pass

    msg = "Ingen kvittering for settings-webserver fra rammen inden timeout."
    if last_status:
        msg = f"{msg} Sidste status: {last_status}."
    if last_message:
        msg = f"{msg} Besked: {last_message}"

    return jsonify(
        {
            "ok": False,
            "error": msg,
            "settings_url": settings_proxy_url,
            "fallback_available": True,
            "start_acknowledged": False,
            "start_job_id": start_job_id or None,
            "reused_existing_job": reused_existing_job,
        }
    ), 409


@app.route("/api/photoframes/<token_id>/settings-proxy", defaults={"subpath": "remote-settings"}, methods=["GET", "POST"])
@app.route("/api/photoframes/<token_id>/settings-proxy/", defaults={"subpath": "remote-settings"}, methods=["GET", "POST"])
@app.route("/api/photoframes/<token_id>/settings-proxy/<path:subpath>", methods=["GET", "POST"])
@login_required
def api_photoframes_settings_proxy(token_id: str, subpath: str):
    if not getattr(current_user, "is_admin", False):
        return _photoframe_settings_proxy_error_page("Kun administrator kan åbne fjernindstillinger.", 403)

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return _photoframe_settings_proxy_error_page("Ugyldigt token-id.", 400)

    records = _load_photoframe_token_records()
    _, rec = _photoframe_find_record_by_id(records, target_id)
    if not rec:
        return _photoframe_settings_proxy_error_page("Fotoramme blev ikke fundet.", 404)

    proxy_root = f"/api/photoframes/{quote(target_id, safe='')}/settings-proxy"
    clean_subpath = re.sub(r"/+", "/", str(subpath or "").strip()).lstrip("/")
    if not clean_subpath:
        clean_subpath = "remote-settings"
    method = str(request.method or "GET").upper()
    settings_root = clean_subpath.split("/", 1)[0]
    is_settings_entry = (method == "GET") and (settings_root in {"remote-settings", "settings"})
    is_settings_save_post = (method == "POST") and (clean_subpath in {"remote-settings/save", "settings/save", "wifi/connect"})
    is_settings_scan_post = (method == "POST") and (clean_subpath in {"wifi/scan", "remote-settings/scan", "settings/scan"})
    is_settings_close_post = (method == "POST") and (clean_subpath in {"connection/close", "remote-settings/close", "settings/close"})
    is_settings_related = bool(
        settings_root in {"remote-settings", "settings"}
        or clean_subpath.startswith("remote-settings/")
        or clean_subpath.startswith("settings/")
        or clean_subpath.startswith("wifi/")
    )

    if is_settings_related and (not is_settings_close_post):
        if _photoframe_touch_settings_session_activity(rec, now_iso()):
            _save_photoframe_token_records(records)

    def _fallback_submit(transport_error: str = ""):
        settings_payload, err = _photoframe_extract_settings_payload_from_request(request)
        if err:
            return _photoframe_settings_fallback_page(
                rec,
                proxy_root,
                status_code=400,
                error=err,
                transport_error=transport_error,
            )
        ok_queue, queue_info = _photoframe_queue_settings_command(rec, settings_payload)
        if not ok_queue:
            return _photoframe_settings_fallback_page(
                rec,
                proxy_root,
                status_code=409,
                error=queue_info or "Kunne ikke sende indstillinger",
                transport_error=transport_error,
            )
        _save_photoframe_token_records(records)
        job_id = _sanitize_photoframe_update_job_id(queue_info)
        return redirect(
            f"{proxy_root}/remote-settings?queued=1&job_id={quote(job_id, safe='')}",
            code=303,
        )

    def _queue_scan_submit(transport_error: str = ""):
        ok_scan, scan_info = _photoframe_queue_wifi_scan_command(rec)
        if not ok_scan:
            return _photoframe_settings_fallback_page(
                rec,
                proxy_root,
                status_code=409,
                error=scan_info or "Kunne ikke starte Wi-Fi scan",
                transport_error=transport_error,
            )
        _save_photoframe_token_records(records)
        job_id = _sanitize_photoframe_update_job_id(scan_info)
        return redirect(
            f"{proxy_root}/remote-settings?scan_queued=1&scan_job_id={quote(job_id, safe='')}",
            code=303,
        )

    def _queue_close_submit():
        ok_close, close_info = _photoframe_queue_stop_settings_web_command(
            rec,
            reason="Lukker indstillingsforbindelse",
        )
        if not ok_close:
            return _photoframe_settings_fallback_page(
                rec,
                proxy_root,
                status_code=409,
                error=close_info or "Kunne ikke lukke forbindelsen",
            )
        _save_photoframe_token_records(records)
        job_id = _sanitize_photoframe_update_job_id(close_info)
        return redirect(
            f"{proxy_root}/remote-settings?close_queued=1&close_job_id={quote(job_id, safe='')}",
            code=303,
        )

    def _entry_notice_from_query() -> str:
        notes: list[str] = []
        queued = str(request.args.get("queued") or "").strip().lower() in {"1", "true", "yes", "on"}
        job_id = _sanitize_photoframe_update_job_id(request.args.get("job_id"))
        if queued:
            txt = "Indstillinger sendt. Rammen anvender dem ved næste heartbeat."
            if job_id:
                txt = f"{txt} Job: {job_id}"
            notes.append(txt)
        scan_queued = str(request.args.get("scan_queued") or "").strip().lower() in {"1", "true", "yes", "on"}
        scan_job_id = _sanitize_photoframe_update_job_id(request.args.get("scan_job_id"))
        if scan_queued:
            txt = "Wi-Fi scan sendt til rammen."
            if scan_job_id:
                txt = f"{txt} Job: {scan_job_id}"
            notes.append(txt)
        close_queued = str(request.args.get("close_queued") or "").strip().lower() in {"1", "true", "yes", "on"}
        close_job_id = _sanitize_photoframe_update_job_id(request.args.get("close_job_id"))
        if close_queued:
            txt = "Luk forbindelsen sendt til rammen."
            if close_job_id:
                txt = f"{txt} Job: {close_job_id}"
            notes.append(txt)
        return " ".join([n for n in notes if n]).strip()

    target_base_url = _photoframe_settings_proxy_base_url(rec)
    # Always use the FjordLens fallback UI for settings entry.
    # This keeps a consistent desktop/mobile layout across local and remote access.
    if is_settings_entry:
        notice = _entry_notice_from_query()
        return _photoframe_settings_fallback_page(
            rec,
            proxy_root,
            notice=notice,
            direct_available=bool(target_base_url),
        )
    # All settings writes go via the existing frame heartbeat command channel.
    if is_settings_save_post:
        return _fallback_submit()
    if is_settings_scan_post:
        return _queue_scan_submit()
    if is_settings_close_post:
        return _queue_close_submit()
    if not target_base_url:
        return _photoframe_settings_proxy_error_page(
            "Rammen har ingen brugbar lokal IP endnu. Brug fallback-fjernindstillinger og prøv igen.",
            409,
        )

    target_url = f"{target_base_url}/{clean_subpath}"
    raw_query = request.query_string.decode("utf-8", errors="ignore").strip()
    if raw_query:
        target_url = f"{target_url}?{raw_query}"

    headers: Dict[str, str] = {}
    for header_name in ("Content-Type", "Accept", "Accept-Language"):
        value = str(request.headers.get(header_name) or "").strip()
        if value:
            headers[header_name] = value
    body_bytes = request.get_data(cache=False) if method in {"POST", "PUT", "PATCH", "DELETE"} else None

    def _proxy_request_once() -> tuple[Optional[requests.Response], str]:
        try:
            out = requests.request(
                method=method,
                url=target_url,
                headers=headers or None,
                data=body_bytes,
                timeout=PHOTOFRAME_SETTINGS_PROXY_TIMEOUT_SEC,
                allow_redirects=False,
            )
            return out, ""
        except Exception as exc:
            return None, str(exc)

    upstream, upstream_error = _proxy_request_once()
    if upstream is None:
        extra = " Vent et par sekunder og prøv igen."
        if is_settings_save_post:
            return _fallback_submit(
                transport_error=f"Forbindelse til fotorammen fejlede ({target_base_url}): {upstream_error or 'ukendt fejl'}{extra}",
            )
        if is_settings_entry:
            return _photoframe_settings_fallback_page(
                rec,
                proxy_root,
                notice=_entry_notice_from_query(),
                transport_error=f"Forbindelse til fotorammen fejlede ({target_base_url}): {upstream_error or 'ukendt fejl'}{extra}",
            )
        return _photoframe_settings_proxy_error_page(
            f"Forbindelse til fotorammen fejlede ({target_base_url}): {upstream_error or 'ukendt fejl'}{extra}",
            409,
        )

    try:
        upstream_status = int(getattr(upstream, "status_code", 0) or 0)
    except Exception:
        upstream_status = 0
    if upstream_status >= 500:
        extra = ""
        if upstream_error:
            extra = f" Sidste fejl: {upstream_error}".strip()
        transport_msg = f"Fotorammen svarede med HTTP {upstream_status} fra {target_base_url}. Tjek at photoframe-app er oppe.{extra}"
        if is_settings_save_post:
            return _fallback_submit(transport_error=transport_msg)
        if is_settings_entry:
            return _photoframe_settings_fallback_page(
                rec,
                proxy_root,
                notice=_entry_notice_from_query(),
                transport_error=transport_msg,
            )
        return _photoframe_settings_proxy_error_page(
            transport_msg,
            409,
        )

    try:
        return _photoframe_proxy_response(upstream, proxy_root, target_base_url)
    except Exception as exc:
        return _photoframe_settings_proxy_error_page(
            f"Kunne ikke gengive svar fra fotorammen ({target_base_url}): {exc}",
            409,
        )


@app.route("/api/photoframes/<token_id>/scope", methods=["GET", "PUT"])
@login_required
def api_photoframes_scope(token_id: str):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    target_id = _sanitize_photoframe_text(token_id, 64)
    if not target_id:
        return jsonify({"ok": False, "error": "Ugyldigt token-id"}), 400

    records = _load_photoframe_token_records()
    rec_idx = -1
    rec: Optional[Dict[str, Any]] = None
    for idx, it in enumerate(records):
        rec_id = _sanitize_photoframe_text(it.get("id"), 64)
        if rec_id == target_id:
            rec_idx = idx
            rec = it
            break
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Token ikke fundet"}), 404

    if request.method == "GET":
        scope_mode, folders, photo_ids = _photoframe_record_scope(rec)
        if scope_mode == "photos":
            filtered_photo_ids = _filter_photoframe_scope_photo_ids_to_images(photo_ids)
            if filtered_photo_ids != photo_ids:
                records[rec_idx]["allowed_photo_ids"] = filtered_photo_ids
                _save_photoframe_token_records(records)
                photo_ids = filtered_photo_ids
        return jsonify(
            {
                "ok": True,
                "id": target_id,
                "scope_mode": scope_mode,
                "allowed_folders": folders,
                "allowed_photo_ids": photo_ids,
                "allowed_folder_count": len(folders),
                "allowed_photo_count": len(photo_ids),
            }
        )

    body = request.get_json(silent=True) or {}
    scope_mode = _normalize_photoframe_scope_mode(body.get("scope_mode"))
    allowed_folders = _normalize_photoframe_scope_folders(body.get("allowed_folders"))
    allowed_photo_ids = _normalize_photoframe_scope_photo_ids(body.get("allowed_photo_ids"))

    if scope_mode == "all":
        allowed_folders = []
        allowed_photo_ids = []
    elif scope_mode == "folders":
        allowed_photo_ids = []
    elif scope_mode == "photos":
        allowed_folders = []
        allowed_photo_ids = _filter_photoframe_scope_photo_ids_to_images(allowed_photo_ids)

    records[rec_idx]["scope_mode"] = scope_mode
    records[rec_idx]["allowed_folders"] = allowed_folders
    records[rec_idx]["allowed_photo_ids"] = allowed_photo_ids
    _photoframe_mark_feed_sync_pending(records[rec_idx], now_iso())
    _save_photoframe_token_records(records)

    return jsonify(
        {
            "ok": True,
            "id": target_id,
            "scope_mode": scope_mode,
            "allowed_folders": allowed_folders,
            "allowed_photo_ids": allowed_photo_ids,
            "allowed_folder_count": len(allowed_folders),
            "allowed_photo_count": len(allowed_photo_ids),
        }
    )


@app.route("/api/photoframes/available-folders", methods=["GET"])
@login_required
def api_photoframes_available_folders():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    with closing(get_conn()) as conn:
        folders = _list_all_photo_folders(conn)
    return jsonify({"ok": True, "items": folders, "count": len(folders)})


@app.route("/api/photoframes/available-photos", methods=["GET"])
@login_required
def api_photoframes_available_photos():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    q = str(request.args.get("q") or "").strip()
    ids_raw = str(request.args.get("ids") or "").strip()
    folder_raw = str(request.args.get("folder") or "").strip()
    try:
        limit = int(request.args.get("limit", "120") or 120)
    except Exception:
        limit = 120
    limit = max(20, min(500, limit))
    db_limit = min(2000, max(limit, limit * 4))

    selected_ids: list[int] = []
    if ids_raw:
        for part in re.split(r"[,\s;]+", ids_raw):
            part = str(part or "").strip()
            if not part:
                continue
            try:
                pid = int(part)
            except Exception:
                continue
            if pid > 0 and pid not in selected_ids:
                selected_ids.append(pid)
            # SQLite has a bind variable ceiling (often 999), so keep this below it.
            if len(selected_ids) >= 900:
                break

    params: list[Any] = []
    where_parts: list[str] = []
    if q:
        q_like = f"%{q}%"
        if q.isdigit():
            where_parts.append("(id=? OR rel_path LIKE ?)")
            params.extend([int(q), q_like])
        else:
            where_parts.append("rel_path LIKE ?")
            params.append(q_like)

    folder = ""
    if folder_raw:
        try:
            folder = _normalize_folder_acl_path(folder_raw)
        except Exception:
            folder = ""
        prefixes = _photoframe_scope_rel_prefixes(folder) if folder else []
        if prefixes:
            conds: list[str] = []
            for pref in prefixes:
                conds.append("(rel_path=? OR rel_path LIKE ?)")
                params.extend([pref, pref + "/%"])
            where_parts.append("(" + " OR ".join(conds) + ")")
        else:
            # Explicit folder provided but no valid prefixes -> no rows.
            where_parts.append("0")

    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

    with closing(get_conn()) as conn:
        rows = conn.execute(
            f"""
            SELECT id, rel_path, thumb_name, COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
            FROM photos
            {where_sql}
            ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
            LIMIT ?
            """,
            (*params, db_limit),
        ).fetchall()

        extra_rows: list[sqlite3.Row] = []
        if selected_ids:
            ph = ",".join(["?"] * len(selected_ids))
            extra_rows = conn.execute(
                f"""
                SELECT id, rel_path, thumb_name, COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
                FROM photos
                WHERE id IN ({ph})
                ORDER BY id DESC
                """,
                selected_ids,
            ).fetchall()

    by_id: dict[int, Dict[str, Any]] = {}
    ordered: list[int] = []
    for src in [rows, extra_rows]:
        for r in src:
            try:
                pid = int(r["id"])
            except Exception:
                continue
            if pid in by_id:
                continue
            rel = str(r["rel_path"] or "").replace("\\", "/")
            label = rel.rsplit("/", 1)[-1] if "/" in rel else rel
            thumb_name = re.sub(r"[^a-zA-Z0-9._-]", "", str(r["thumb_name"] or ""))
            ext = str(Path(rel).suffix or "").lower()
            if ext in VIDEO_EXTS:
                continue
            by_id[pid] = {
                "id": pid,
                "rel_path": rel,
                "label": label or f"Photo #{pid}",
                "ext": ext,
                "is_video": False,
                "is_gif": bool(ext == ".gif"),
                "updated_at": _sanitize_photoframe_text(r["updated_at"], 40),
                "selected": pid in selected_ids,
                "thumb_url": f"/api/thumbs/{thumb_name}" if thumb_name else "",
            }
            ordered.append(pid)

    max_items = min(3000, limit + len(selected_ids))
    items = [by_id[pid] for pid in ordered[:max_items]]
    return jsonify({"ok": True, "items": items, "count": len(items)})


def _render_photoframe_status_image(frame_name: str, token_hint: str, generated_at: str) -> io.BytesIO:
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), (8, 16, 32))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 56)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.rectangle([(0, 0), (width, 96)], fill=(18, 34, 62))
    draw.text((48, 26), "FjordLens connection OK", fill=(240, 246, 255), font=body_font)
    draw.text((48, 150), "Photoframe is connected", fill=(245, 250, 255), font=title_font)
    draw.text((48, 290), f"Frame: {frame_name or 'Unknown'}", fill=(200, 220, 255), font=body_font)
    draw.text((48, 350), f"Token: ***{token_hint or '----'}", fill=(200, 220, 255), font=body_font)
    draw.text((48, 410), f"Server time: {generated_at}", fill=(200, 220, 255), font=body_font)
    draw.text((48, 650), "This test screen is served by FjordLens.", fill=(160, 185, 230), font=small_font)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90, optimize=True)
    out.seek(0)
    return out


@app.route("/api/frame/<token>/status-card.jpg", methods=["GET"])
def api_frame_status_card(token: str):
    _, rec_idx, rec = _photoframe_token_lookup(token)
    if rec_idx < 0 or not rec:
        return ("Forbidden", 403)

    frame_name = _sanitize_photoframe_text(rec.get("device_name"), 80)
    if not frame_name:
        frame_name = _sanitize_photoframe_text(request.args.get("name"), 80)
    token_hint = _sanitize_photoframe_text(rec.get("token_hint"), 16)
    generated_at = now_iso()

    payload = _render_photoframe_status_image(frame_name, token_hint, generated_at)
    resp = send_file(payload, mimetype="image/jpeg")
    try:
        resp.headers["Cache-Control"] = "no-store, max-age=0"
    except Exception:
        pass
    return resp


@app.route("/api/frame/<token>/update-package/<job_id>.zip", methods=["GET"])
def api_frame_update_package(token: str, job_id: str):
    records, rec_idx, rec = _photoframe_token_lookup(token)
    if rec_idx < 0 or not rec:
        return ("Forbidden", 403)
    safe_job_id = _sanitize_photoframe_update_job_id(job_id)
    rec_job_id = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
    if (not safe_job_id) or (not rec_job_id) or (safe_job_id != rec_job_id):
        return ("Not found", 404)

    package_root = _resolve_photoframe_package_root()
    if not package_root:
        return ("No update package source available", 404)

    wanted_entries = [
        "app",
        "viewer",
        "scripts",
        "config",
        "systemd",
        "update.sh",
        "README.txt",
        "install.sh",
    ]

    tmp = tempfile.TemporaryFile()
    with zipfile.ZipFile(tmp, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_name in wanted_entries:
            source = package_root / rel_name
            if not source.exists():
                continue
            if source.is_file():
                try:
                    zf.write(str(source), arcname=str(rel_name))
                except Exception:
                    continue
                continue
            for fp in source.rglob("*"):
                if not fp.is_file():
                    continue
                try:
                    arcname = str(fp.relative_to(package_root)).replace("\\", "/")
                    zf.write(str(fp), arcname=arcname)
                except Exception:
                    continue
    tmp.seek(0)
    resp = send_file(
        tmp,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"photoframe-update-{safe_job_id}.zip",
    )
    try:
        resp.headers["Cache-Control"] = "no-store, max-age=0"
    except Exception:
        pass
    return resp


@app.route("/api/frame/<token>/update-upload/<job_id>.zip", methods=["GET"])
def api_frame_uploaded_update_package(token: str, job_id: str):
    records, rec_idx, rec = _photoframe_token_lookup(token)
    if rec_idx < 0 or not rec:
        return ("Forbidden", 403)
    safe_job_id = _sanitize_photoframe_update_job_id(job_id)
    rec_job_id = _sanitize_photoframe_update_job_id(rec.get("update_job_id"))
    if (not safe_job_id) or (not rec_job_id) or (safe_job_id != rec_job_id):
        return ("Not found", 404)

    pkg_path = _photoframe_uploaded_package_path(safe_job_id)
    if pkg_path is None or (not pkg_path.exists()) or (not pkg_path.is_file()):
        return ("Not found", 404)
    resp = send_file(
        str(pkg_path),
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"photoframe-upload-{safe_job_id}.zip",
    )
    try:
        resp.headers["Cache-Control"] = "no-store, max-age=0"
    except Exception:
        pass
    return resp


@app.route("/api/frame/<token>/feed", methods=["GET"])
def api_frame_feed(token: str):
    records, rec_idx, rec = _photoframe_token_lookup(token)
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Invalid token"}), 404

    now = now_iso()
    active_record = records[rec_idx] if (0 <= rec_idx < len(records)) else rec
    _photoframe_update_presence_fields(active_record, request, now)
    _photoframe_maybe_queue_settings_auto_stop(active_record, now)
    _save_photoframe_token_records(records)
    current_photo_raw = request.args.get("current_photo_id") or request.headers.get("X-Photoframe-Current-Photo-Id")
    scope_mode, scope_folders, scope_photo_ids = _photoframe_record_scope(active_record)

    request_base = str(request.url_root or "").rstrip("/") or _request_public_base_url()

    if PHOTOFRAME_TEXT_ONLY:
        status_url = f"{request_base}{url_for('api_frame_status_card', token=token, _external=False)}?t={int(time.time())}"
        update_cmd = _photoframe_update_command_payload(active_record, token=token, request_base=request_base)
        return jsonify(
            {
                "ok": True,
                "images": [
                    {
                        "id": "connection-status",
                        "url": status_url,
                        "updated_at": now,
                        "media_type": "image",
                        "ext": ".png",
                    }
                ],
                "count": 1,
                "generated_at": now,
                "mode": "text-only",
                "message": "FjordLens connection OK",
                "update": update_cmd,
            }
        )

    updated_current_photo_id = 0
    with closing(get_conn()) as conn:
        updated_current_photo_id = _photoframe_try_set_current_photo(conn, active_record, current_photo_raw, now)
        if scope_mode == "photos":
            ids_for_query = _normalize_photoframe_scope_photo_ids(scope_photo_ids)[:900]
            if not ids_for_query:
                rows = []
            else:
                ph = ",".join(["?"] * len(ids_for_query))
                rows = conn.execute(
                    f"""
                    SELECT
                        id,
                        rel_path,
                        captured_at,
                        created_fs,
                        modified_fs,
                        gps_name,
                        metadata_json,
                        exif_json,
                        COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
                    FROM photos
                    WHERE id IN ({ph})
                    ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
                    LIMIT ?
                    """,
                    (*ids_for_query, PHOTOFRAME_FEED_MAX_IMAGES),
                ).fetchall()
        elif scope_mode == "folders":
            prefixes: list[str] = []
            seen_prefixes: set[str] = set()
            for folder in _normalize_photoframe_scope_folders(scope_folders):
                for pref in _photoframe_scope_rel_prefixes(folder):
                    if pref in seen_prefixes:
                        continue
                    seen_prefixes.add(pref)
                    prefixes.append(pref)
                    if len(prefixes) >= 300:
                        break
                if len(prefixes) >= 300:
                    break
            if not prefixes:
                rows = []
            else:
                conds: list[str] = []
                params: list[Any] = []
                for pref in prefixes:
                    conds.append("(rel_path=? OR rel_path LIKE ?)")
                    params.extend([pref, pref + "/%"])
                rows = conn.execute(
                    f"""
                    SELECT
                        id,
                        rel_path,
                        captured_at,
                        created_fs,
                        modified_fs,
                        gps_name,
                        metadata_json,
                        exif_json,
                        COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
                    FROM photos
                    WHERE {" OR ".join(conds)}
                    ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
                    LIMIT ?
                    """,
                    (*params, PHOTOFRAME_FEED_MAX_IMAGES),
                ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    id,
                    rel_path,
                    captured_at,
                    created_fs,
                    modified_fs,
                    gps_name,
                    metadata_json,
                    exif_json,
                    COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) AS updated_at
                FROM photos
                ORDER BY COALESCE(captured_at, modified_fs, created_fs, imported_at, last_scanned_at) DESC, id DESC
                LIMIT ?
                """,
                (PHOTOFRAME_FEED_MAX_IMAGES,),
            ).fetchall()
    if updated_current_photo_id > 0:
        _save_photoframe_token_records(records)

    if rows:
        safe_rows = []
        for row in rows:
            try:
                pid = int(row["id"])
            except Exception:
                continue
            rel = str(row["rel_path"] or "")
            if _photoframe_record_allows_photo(active_record, pid, rel):
                try:
                    src = _disk_path_from_rel_path(rel)
                    if not src.exists():
                        safe_rel = rel.replace("..", "").lstrip("/")
                        if not safe_rel:
                            continue
                        converted = CONVERT_DIR / safe_rel
                        if not converted.exists():
                            continue
                except Exception:
                    continue
                safe_rows.append(row)
        rows = safe_rows

    images: list[Dict[str, Any]] = []
    for row in rows:
        try:
            photo_id = int(row["id"])
        except Exception:
            continue
        rel_path = str(row["rel_path"] or "")
        media_ext = str(Path(rel_path).suffix or "").lower()
        if media_ext in VIDEO_EXTS:
            continue
        updated_at = _sanitize_photoframe_text(row["updated_at"], 40)
        location, location_city, location_country = _photoframe_location_from_row(row)
        captured_at = _photoframe_date_from_row(row)
        images.append(
            {
                "id": str(photo_id),
                "url": f"{request_base}{url_for('api_frame_viewable', token=token, photo_id=photo_id, _external=False)}",
                "updated_at": updated_at or now,
                "media_type": "image",
                "ext": media_ext,
                "location": location,
                "location_city": location_city,
                "location_country": location_country,
                "captured_at": captured_at,
            }
        )

    feed_message = ""
    if not images:
        if scope_mode == "folders" and not _normalize_photoframe_scope_folders(scope_folders):
            feed_message = "Ingen mapper valgt til denne fotoramme endnu"
        elif scope_mode == "photos" and not _normalize_photoframe_scope_photo_ids(scope_photo_ids):
            feed_message = "Ingen billeder valgt til denne fotoramme endnu"
        elif scope_mode in {"folders", "photos"}:
            feed_message = "Ingen billeder matcher valget til denne fotoramme endnu"
        else:
            feed_message = "Ingen billeder i feedet endnu"

    feed_rev = _photoframe_compute_feed_revision(images, scope_mode=scope_mode)
    if _photoframe_mark_feed_sync_sent(active_record, feed_rev, len(images), now):
        _save_photoframe_token_records(records)

    update_cmd = _photoframe_update_command_payload(active_record, token=token, request_base=request_base)
    return jsonify(
        {
            "ok": True,
            "images": images,
            "count": len(images),
            "feed_rev": feed_rev,
            "generated_at": now,
            "message": feed_message,
            "update": update_cmd,
        }
    )


@app.route("/api/frame/<token>/heartbeat", methods=["GET"])
def api_frame_heartbeat(token: str):
    records, rec_idx, rec = _photoframe_token_lookup(token)
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Invalid token"}), 404

    now = now_iso()
    active_record = records[rec_idx] if (0 <= rec_idx < len(records)) else rec
    _photoframe_update_presence_fields(active_record, request, now)
    current_photo_raw = request.args.get("photo_id") or request.headers.get("X-Photoframe-Current-Photo-Id")
    update_job_raw = request.args.get("update_job_id") or request.headers.get("X-Photoframe-Update-Job-Id")
    update_status_raw = request.args.get("update_status") or request.headers.get("X-Photoframe-Update-Status")
    update_message_raw = request.args.get("update_message") or request.headers.get("X-Photoframe-Update-Message")
    update_version_raw = request.args.get("update_version") or request.headers.get("X-Photoframe-Update-Version")
    feed_rev_raw = request.args.get("feed_rev") or request.headers.get("X-Photoframe-Feed-Rev")
    wifi_scan_sent_raw = request.args.get("wifi_scan_sent") or request.headers.get("X-Photoframe-Wifi-Scan-Sent")
    wifi_scan_payload_raw = request.args.get("wifi_scan_payload") or request.headers.get("X-Photoframe-Wifi-Scan-Payload")
    wifi_scan_error_raw = request.args.get("wifi_scan_error") or request.headers.get("X-Photoframe-Wifi-Scan-Error")
    wifi_scan_scanned_at_raw = request.args.get("wifi_scan_scanned_at") or request.headers.get("X-Photoframe-Wifi-Scan-Scanned-At")
    current_photo_id = 0
    with closing(get_conn()) as conn:
        current_photo_id = _photoframe_try_set_current_photo(conn, active_record, current_photo_raw, now)
    report_applied = _photoframe_apply_update_report(
        active_record,
        update_job_raw,
        update_status_raw,
        update_message_raw,
        update_version_raw,
        now,
    )
    if not report_applied:
        _photoframe_mark_stale_scan_if_needed(active_record, now)
    _photoframe_apply_feed_sync_ack(
        active_record,
        feed_rev_raw,
        now,
        allow_fallback=False,
    )
    wifi_scan_sent = _sanitize_photoframe_bool(wifi_scan_sent_raw) or bool(str(wifi_scan_payload_raw or "").strip()) or bool(str(wifi_scan_error_raw or "").strip())
    if wifi_scan_sent:
        active_record["wifi_scan_networks"] = _decode_photoframe_wifi_scan_payload(wifi_scan_payload_raw, max_len=12000)
        active_record["wifi_scan_error"] = _sanitize_photoframe_text(wifi_scan_error_raw, 240)
        active_record["wifi_scan_scanned_at"] = _sanitize_photoframe_text(wifi_scan_scanned_at_raw, 40) or now
    _photoframe_maybe_queue_settings_auto_stop(active_record, now)
    _save_photoframe_token_records(records)

    latest_photo_id = _sanitize_photoframe_photo_id(active_record.get("last_photo_id") if isinstance(active_record, dict) else 0)
    if latest_photo_id <= 0:
        latest_photo_id = current_photo_id
    heartbeat_base = str(request.url_root or "").rstrip("/")
    update_cmd = _photoframe_update_command_payload(active_record, token=token, request_base=heartbeat_base)
    return jsonify(
        {
            "ok": True,
            "seen_at": now,
            "photo_id": latest_photo_id or None,
            "update_job_id": _sanitize_photoframe_update_job_id(active_record.get("update_job_id") if isinstance(active_record, dict) else ""),
            "update_status": _sanitize_photoframe_update_status(active_record.get("update_status") if isinstance(active_record, dict) else ""),
            "content_sync_status": _sanitize_photoframe_feed_sync_status(active_record.get("feed_sync_status") if isinstance(active_record, dict) else ""),
            "content_sync_rev": _sanitize_photoframe_feed_rev(active_record.get("feed_sync_sent_rev") if isinstance(active_record, dict) else ""),
            "update": update_cmd,
        }
    )


@app.route("/api/frame/<token>/wifi-scan-report", methods=["POST"])
def api_frame_wifi_scan_report(token: str):
    records, rec_idx, rec = _photoframe_token_lookup(token)
    if rec_idx < 0 or not rec:
        return jsonify({"ok": False, "error": "Invalid token"}), 404

    now = now_iso()
    active_record = records[rec_idx] if (0 <= rec_idx < len(records)) else rec
    _photoframe_update_presence_fields(active_record, request, now)

    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        body = {}

    job_id = _sanitize_photoframe_update_job_id(body.get("job_id"))
    status = _sanitize_photoframe_update_status(body.get("status"))
    message = _sanitize_photoframe_text(body.get("message"), 240)
    version = _sanitize_photoframe_text(body.get("version"), 80)
    if status:
        target_job = job_id or _sanitize_photoframe_update_job_id(active_record.get("update_job_id"))
        status_msg = message or _sanitize_photoframe_text(body.get("error"), 240)
        _photoframe_apply_update_report(active_record, target_job, status, status_msg, version, now)

    networks_provided = ("networks" in body)
    scan_networks = _sanitize_photoframe_wifi_scan_networks(body.get("networks"), max_items=80) if networks_provided else _sanitize_photoframe_wifi_scan_networks(active_record.get("wifi_scan_networks"), max_items=80)
    scan_error = _sanitize_photoframe_text(body.get("error"), 240) if ("error" in body) else _sanitize_photoframe_text(active_record.get("wifi_scan_error"), 240)
    scanned_at = _sanitize_photoframe_text(body.get("scanned_at"), 40) or now
    if networks_provided:
        active_record["wifi_scan_networks"] = scan_networks
        active_record["wifi_scan_scanned_at"] = scanned_at
        active_record["wifi_scan_error"] = scan_error
    elif ("error" in body):
        active_record["wifi_scan_scanned_at"] = scanned_at
        active_record["wifi_scan_error"] = scan_error

    _save_photoframe_token_records(records)
    return jsonify(
        {
            "ok": True,
            "seen_at": now,
            "job_id": job_id or None,
            "status": status or None,
            "network_count": len(scan_networks) if networks_provided else None,
        }
    )


@app.route("/api/frame/<token>/view/<int:photo_id>", methods=["GET"])
def api_frame_viewable(token: str, photo_id: int):
    records, rec_idx, rec = _photoframe_token_lookup(token)
    if rec_idx < 0 or not rec:
        return ("Forbidden", 403)

    active_record = records[rec_idx] if (0 <= rec_idx < len(records)) else rec
    now = now_iso()
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT rel_path FROM photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        return ("Not found", 404)
    rel_path = str(row["rel_path"] or "")
    if not _photoframe_record_allows_photo(active_record, int(photo_id), rel_path):
        return ("Forbidden", 403)

    try:
        with closing(get_conn()) as conn:
            _photoframe_update_presence_fields(active_record, request, now)
            _photoframe_try_set_current_photo(conn, active_record, int(photo_id), now)
        _save_photoframe_token_records(records)
    except Exception:
        pass

    safe_rel = rel_path.replace("..", "").lstrip("/")
    if not safe_rel:
        return ("Not found", 404)
    src = _disk_path_from_rel_path(safe_rel)
    if not src.exists():
        cand = CONVERT_DIR / safe_rel
        if cand.exists():
            return send_from_directory(CONVERT_DIR, safe_rel)
        return ("Not found", 404)

    if src.suffix.lower() in VIDEO_EXTS:
        return ("Not found", 404)
    view_path = ensure_viewable_copy(src, safe_rel)
    try:
        vp = str(view_path)
        if vp.startswith(str(CONVERT_DIR)):
            rel_conv = str(view_path.relative_to(CONVERT_DIR)).replace("\\", "/")
            resp = send_from_directory(CONVERT_DIR, rel_conv)
            try:
                resp.headers["Cache-Control"] = "public, max-age=86400"
            except Exception:
                pass
            return resp
        if safe_rel.startswith("uploads/"):
            resp = send_from_directory(UPLOAD_DIR, safe_rel[len("uploads/"):])
            try:
                resp.headers["Cache-Control"] = "public, max-age=86400"
            except Exception:
                pass
            return resp
        resp = send_from_directory(PHOTO_DIR, safe_rel)
        try:
            resp.headers["Cache-Control"] = "public, max-age=86400"
        except Exception:
            pass
        return resp
    except Exception as e:
        return (str(e), 500)



# Start scan in thread
scan_thread = None
rescan_thread = None
last_rescan_result: Optional[Dict[str, Any]] = None
rethumb_thread = None
last_rethumb_result: Optional[Dict[str, Any]] = None


def _scan_disabled_error() -> Dict[str, Any]:
    return {"ok": False, "error": "Scan-funktioner er deaktiveret"}

@app.route("/api/scan", methods=["POST"])
def api_scan():
    if not ENABLE_SCAN_FEATURES:
        return jsonify(_scan_disabled_error()), 403
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global scan_thread
    if scan_thread and scan_thread.is_alive():
        return jsonify({"ok": False, "error": "Scan already running"}), 409
    scan_stop_event.clear()
    def run_scan():
        scan_library(stop_event=scan_stop_event)
    scan_thread = threading.Thread(target=run_scan, daemon=True)
    scan_thread.start()
    return jsonify({"ok": True, "started": True})

# Stop scan
@app.route("/api/scan/stop", methods=["POST"])
def api_scan_stop():
    if not ENABLE_SCAN_FEATURES:
        return jsonify(_scan_disabled_error()), 403
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    scan_stop_event.set()
    return jsonify({"ok": True, "stopped": True})

# Scan status
@app.route("/api/scan/status")
def api_scan_status():
    if not ENABLE_SCAN_FEATURES:
        return jsonify({"ok": True, "running": False, "disabled": True})
    running = bool(scan_thread and scan_thread.is_alive())
    return jsonify({"ok": True, "running": running})


@app.route("/api/rescan", methods=["POST"])
def api_rescan():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global rescan_thread, last_rescan_result
    if rescan_thread and rescan_thread.is_alive():
        return jsonify({"ok": False, "error": "Rescan already running"}), 409
    scan_stop_event.clear()
    last_rescan_result = None

    def run_rescan():
        global last_rescan_result
        last_rescan_result = rescan_metadata(stop_event=scan_stop_event)

    rescan_thread = threading.Thread(target=run_rescan, daemon=True)
    rescan_thread.start()
    return jsonify({"ok": True, "started": True})


@app.route("/api/rescan/status")
def api_rescan_status():
    running = bool(rescan_thread and rescan_thread.is_alive())
    resp: Dict[str, Any] = {"ok": True, "running": running}
    if not running and last_rescan_result is not None:
        resp["result"] = last_rescan_result
    return jsonify(resp)


def rethumb_all(stop_event=None) -> Dict[str, Any]:
    init_db()
    log_event("rethumb_start")
    total = 0
    errors = 0
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT rel_path FROM photos").fetchall()
    for row in rows:
        if stop_event and stop_event.is_set():
            break
        rel_path = row["rel_path"]
        p = _disk_path_from_rel_path(rel_path)
        if not p.exists():
            continue
        try:
            stat = p.stat()
            with Image.open(p) as img:
                try:
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass
                make_thumb(img, rel_path, stat.st_mtime, stat.st_size, force=True)
            total += 1
            log_event("rethumb_ok", rel_path=rel_path)
        except Exception as e:
            errors += 1
            log_event("error", rel_path=rel_path, error=str(e))
    res = {"ok": True, "processed": total, "errors": errors}
    log_event("rethumb_done", processed=total, errors=errors)
    return res


@app.route("/api/rethumb", methods=["POST"])
def api_rethumb():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global rethumb_thread, last_rethumb_result
    if rethumb_thread and rethumb_thread.is_alive():
        return jsonify({"ok": False, "error": "Rethumb already running"}), 409
    scan_stop_event.clear()
    last_rethumb_result = None

    def run_rethumb():
        global last_rethumb_result
        last_rethumb_result = rethumb_all(stop_event=scan_stop_event)

    rethumb_thread = threading.Thread(target=run_rethumb, daemon=True)
    rethumb_thread.start()
    return jsonify({"ok": True, "started": True})


@app.route("/api/rethumb/status")
def api_rethumb_status():
    running = bool(rethumb_thread and rethumb_thread.is_alive())
    resp: Dict[str, Any] = {"ok": True, "running": running}
    if not running and last_rethumb_result is not None:
        resp["result"] = last_rethumb_result
    return jsonify(resp)


def rethumb_missing(stop_event=None) -> Dict[str, Any]:
    init_db()
    log_event("rethumb_missing_start")
    total = 0
    errors = 0
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT rel_path, thumb_name FROM photos"
        ).fetchall()
    for row in rows:
        if stop_event and stop_event.is_set():
            break
        rel_path = row["rel_path"]
        try:
            p = PHOTO_DIR / rel_path if not rel_path.startswith("uploads/") else UPLOAD_DIR / rel_path[len("uploads/"):]
            if not p.exists():
                continue
            stat = p.stat()
            expected_ok = False
            prev = str(row["thumb_name"] or "").strip()
            if prev:
                tp = THUMB_DIR / prev
                try:
                    expected_ok = tp.exists() and (tp.stat().st_mtime >= stat.st_mtime)
                except Exception:
                    expected_ok = False
            if expected_ok:
                continue
            # Need (re)thumb
            tn: Optional[str] = None
            if p.suffix.lower() in VIDEO_EXTS:
                tn = _make_video_thumb(p, rel_path, stat.st_mtime, stat.st_size)
            else:
                with Image.open(p) as img:
                    try:
                        img = ImageOps.exif_transpose(img)
                    except Exception:
                        pass
                    tn = make_thumb(img, rel_path, stat.st_mtime, stat.st_size)
            if tn:
                with closing(get_conn()) as conn:
                    conn.execute("UPDATE photos SET thumb_name=?, last_scanned_at=? WHERE rel_path=?", (tn, now_iso(), rel_path))
                    conn.commit()
                total += 1
                log_event("rethumb_missing_ok", rel_path=rel_path)
            else:
                errors += 1
        except Exception as e:
            errors += 1
            log_event("error", rel_path=rel_path, error=f"rethumb_missing: {e}")
    res = {"ok": True, "processed": total, "errors": errors}
    log_event("rethumb_missing_done", processed=total, errors=errors)
    return res


@app.route("/api/rethumb/missing", methods=["POST"])
def api_rethumb_missing():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global rethumb_thread, last_rethumb_result
    if rethumb_thread and rethumb_thread.is_alive():
        return jsonify({"ok": False, "error": "Rethumb already running"}), 409
    scan_stop_event.clear()
    last_rethumb_result = None

    def run_rethumb_missing():
        global last_rethumb_result
        last_rethumb_result = rethumb_missing(stop_event=scan_stop_event)

    rethumb_thread = threading.Thread(target=run_rethumb_missing, daemon=True)
    rethumb_thread.start()
    return jsonify({"ok": True, "started": True})


def _thread_is_alive(thread_obj: Any) -> bool:
    try:
        return bool(thread_obj and thread_obj.is_alive())
    except Exception:
        return False


def _drain_queue_nowait(q: "queue.Queue[Any]") -> int:
    removed = 0
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            break
        except Exception:
            break
        else:
            removed += 1
            try:
                q.task_done()
            except Exception:
                pass
    return removed


@app.route("/api/processes/stop-all", methods=["POST"])
def api_stop_all_processes():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    global STOP_ALL_PROCESS_COOLDOWN_UNTIL
    STOP_ALL_PROCESS_COOLDOWN_UNTIL = time.time() + 120.0
    scan_stop_event.set()
    UPLOAD_POSTPROCESS_STOP_EVENT.set()
    ai_desc_stop_event.set()
    runtime_stop = _ai_stop_description_runtime(force=True)

    try:
        _set_setting("ai_auto_ingest", "0")
        _set_setting("ai_desc_auto_ingest", "0")
        _set_setting("faces_auto_index", "0")
    except Exception:
        pass

    if _faces_running.is_set():
        _faces_running.clear()

    with UPLOAD_PENDING_LOCK:
        pending_uploads = sum(len(v or []) for v in UPLOAD_PENDING_BY_USER.values())
        UPLOAD_PENDING_BY_USER.clear()
    with UPLOAD_TRANSFER_LOCK:
        active_transfers = len(UPLOAD_TRANSFER_ACTIVE_BY_USER)
        UPLOAD_TRANSFER_ACTIVE_BY_USER.clear()
    with DIRECT_UPLOAD_POSTPROCESS_ACTIVE_LOCK:
        direct_active = len(DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS)
        DIRECT_UPLOAD_POSTPROCESS_ACTIVE_RELS.clear()
    with UPLOAD_POSTPROCESS_LOCK:
        upload_states = 0
        for user, state in list(UPLOAD_POSTPROCESS_BY_USER.items()):
            cur = dict(state or {})
            if cur.get("running") or cur.get("phase") not in {None, "", "done", "stopped", "error"}:
                upload_states += 1
            cur.update(
                {
                    "running": False,
                    "finished_at": now_iso(),
                    "phase": "stopped",
                    "current_rel": None,
                    "error": None,
                }
            )
            UPLOAD_POSTPROCESS_BY_USER[user] = cur

    with UPLOAD_FOLDER_SYNC_LOCK:
        sync_running = len(UPLOAD_FOLDER_SYNC_RUNNING)
        UPLOAD_FOLDER_SYNC_LAST_AT.clear()

    with PHOTOFRAME_VIDEO_PREPARE_LOCK:
        photoframe_queued = len(PHOTOFRAME_VIDEO_PREPARE_QUEUED)
        PHOTOFRAME_VIDEO_PREPARE_QUEUED.clear()
    photoframe_queue_drained = _drain_queue_nowait(PHOTOFRAME_VIDEO_PREPARE_QUEUE)

    running_snapshot = {
        "scan": _thread_is_alive(scan_thread),
        "rescan": _thread_is_alive(rescan_thread),
        "rethumb": _thread_is_alive(rethumb_thread),
        "heic_convert": _thread_is_alive(heic_convert_thread),
        "raw_convert": _thread_is_alive(raw_convert_thread),
        "mov_convert": _thread_is_alive(mov_convert_thread),
        "ai": bool(ai_running),
        "ai_desc": bool(ai_desc_running),
        "faces": bool(_faces_running.is_set()),
        "upload_postprocess": upload_states,
        "upload_transfers": active_transfers,
        "direct_upload_active": direct_active,
        "folder_sync_running": sync_running,
        "photoframe_video_queued": max(photoframe_queued, photoframe_queue_drained),
    }
    try:
        log_event("stop_all_processes", **running_snapshot, pending_uploads=pending_uploads)
    except Exception:
        pass
    return jsonify(
        {
            "ok": True,
            "stopping": True,
            "pending_uploads_cleared": pending_uploads,
            "runtime_stop": runtime_stop,
            "running": running_snapshot,
        }
    )


# --- AI: embeddings + search ---
ai_thread = None
ai_running = False
ai_counts: Dict[str, int] = {"embedded": 0, "failed": 0, "total": 0}
last_ai_result: Optional[Dict[str, Any]] = None
ai_desc_thread = None
ai_desc_running = False
ai_desc_counts: Dict[str, int] = {"described": 0, "failed": 0, "total": 0}
last_ai_desc_result: Optional[Dict[str, Any]] = None
ai_desc_stop_event = threading.Event()


def _is_ai_embedding_supported_rel(rel_path: str) -> bool:
    ext = Path(str(rel_path or "")).suffix.lower()
    return ext in IMAGE_EXTS


def _ai_embedding_coverage() -> Dict[str, int]:
    counts = {"total": 0, "embedded": 0, "missing": 0, "unsupported": 0}
    try:
        with closing(get_conn()) as conn:
            rows = conn.execute("SELECT rel_path, embedding_json FROM photos").fetchall()
    except Exception:
        return counts

    for row in rows:
        if not _is_ai_embedding_supported_rel(row["rel_path"]):
            counts["unsupported"] += 1
            continue
        counts["total"] += 1
        if str(row["embedding_json"] or "").strip():
            counts["embedded"] += 1
        else:
            counts["missing"] += 1
    return counts


def _similar_rel_folder_key(rel_path: Any) -> str:
    rel = str(rel_path or "").replace("\\", "/").strip().strip("/")
    if not rel:
        return ""
    folder = rel.rsplit("/", 1)[0] if "/" in rel else ""
    if folder == "uploads":
        folder = ""
    elif folder.startswith("uploads/"):
        folder = folder[len("uploads/") :]
    if folder.startswith("converted/"):
        folder = folder[len("converted/") :]
    if folder.startswith("originals/"):
        folder = folder[len("originals/") :]
    return folder.strip("/")


def _ai_embedding_coverage_for_source_folder(conn: sqlite3.Connection, source_rel_path: str) -> Dict[str, Any]:
    folder_key = _similar_rel_folder_key(source_rel_path)
    counts: Dict[str, Any] = {
        "folder": folder_key,
        "total": 0,
        "embedded": 0,
        "missing": 0,
        "unsupported": 0,
    }
    try:
        rows = conn.execute("SELECT rel_path, embedding_json FROM photos").fetchall()
    except Exception:
        return counts

    for row in rows:
        rel = str(row["rel_path"] or "")
        if _similar_rel_folder_key(rel) != folder_key:
            continue
        if not _is_rel_path_allowed_for_current_user(rel, conn):
            continue
        if not _is_ai_embedding_supported_rel(rel):
            counts["unsupported"] += 1
            continue
        counts["total"] += 1
        if str(row["embedding_json"] or "").strip():
            counts["embedded"] += 1
        else:
            counts["missing"] += 1
    return counts


def _embed_one_photo(photo_id: int, rel_path: str) -> bool:
    if not _is_ai_embedding_supported_rel(rel_path):
        log_event("ai_embed_skip_unsupported", rel_path=rel_path)
        return False
    disk_path = _disk_path_from_rel_path(rel_path)
    if not disk_path.exists():
        return False
    emb = _ai_embed_image_path(disk_path)
    if not emb:
        return False

    with closing(get_conn()) as conn:
        conn.execute("UPDATE photos SET embedding_json=? WHERE id=?", (json.dumps(emb), photo_id))
        conn.commit()

    try:
        tags = _classify_labels(emb)
    except Exception:
        tags = []

    if tags:
        try:
            with closing(get_conn()) as conn:
                cur = conn.execute("SELECT ai_tags FROM photos WHERE id=?", (photo_id,)).fetchone()
                prev = []
                if cur and cur["ai_tags"]:
                    try:
                        prev = json.loads(cur["ai_tags"]) or []
                    except Exception:
                        prev = []
                merged = sorted({*(prev or []), *tags})
                conn.execute("UPDATE photos SET ai_tags=? WHERE id=?", (json.dumps(merged, ensure_ascii=False), photo_id))
                conn.commit()
        except Exception:
            pass

    return True


def _embed_missing_photos(stop_event=None) -> Dict[str, Any]:
    global ai_running, ai_counts, last_ai_result
    ai_running = True
    ai_counts = {"embedded": 0, "failed": 0, "total": 0}
    log_event("ai_embed_start")
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT id, rel_path FROM photos WHERE (embedding_json IS NULL OR embedding_json = '')"
        ).fetchall()
    rows = [row for row in rows if _is_ai_embedding_supported_rel(row["rel_path"])]
    for row in rows:
        if stop_event and stop_event.is_set():
            break
        pid = int(row["id"])
        rel = row["rel_path"]
        ai_counts["total"] += 1
        try:
            if _embed_one_photo(pid, rel):
                ai_counts["embedded"] += 1
                log_event("ai_embed_ok", rel_path=rel)
            else:
                ai_counts["failed"] += 1
                log_event("ai_embed_fail", rel_path=rel)
        except Exception:
            ai_counts["failed"] += 1
            log_event("ai_embed_fail", rel_path=rel)
        ai_delay = ai_ingest_throttle_enabled_sec()
        if ai_delay > 0:
            time.sleep(ai_delay)
    ai_running = False
    last_ai_result = {"ok": True, **ai_counts}
    log_event("ai_embed_done", **ai_counts)
    return last_ai_result


def _embed_uploaded_photo_if_needed(rel_path: str) -> None:
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id, embedding_json FROM photos WHERE rel_path=?", (rel_path,)).fetchone()
        if not row:
            return
        if not _is_ai_embedding_supported_rel(rel_path):
            log_event("ai_embed_skip_unsupported", rel_path=rel_path, source="upload")
            return
        if row["embedding_json"]:
            return
        pid = int(row["id"])
        if _embed_one_photo(pid, rel_path):
            log_event("ai_embed_ok", rel_path=rel_path, source="upload")
        else:
            log_event("ai_embed_fail", rel_path=rel_path, source="upload")
    except Exception as e:
        log_event("ai_embed_fail", rel_path=rel_path, source="upload", error=str(e))


def _describe_one_photo_light(photo_id: int, rel_path: str) -> bool:
    emb = None
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT embedding_json FROM photos WHERE id=?", (photo_id,)).fetchone()
    if row and row["embedding_json"]:
        try:
            emb = json.loads(row["embedding_json"])
        except Exception:
            emb = None

    if not emb:
        if not _embed_one_photo(photo_id, rel_path):
            return False
        with closing(get_conn()) as conn:
            row2 = conn.execute("SELECT embedding_json FROM photos WHERE id=?", (photo_id,)).fetchone()
        if row2 and row2["embedding_json"]:
            try:
                emb = json.loads(row2["embedding_json"])
            except Exception:
                emb = None
    if not emb:
        return False

    tags = _classify_descriptive_tags(emb)
    caption = _build_desc_caption(tags)
    with closing(get_conn()) as conn:
        _store_photo_ai_description(conn, photo_id, tags or [], caption)
        conn.commit()
    return bool(caption or tags)


def _describe_one_photo_qwen(photo_id: int, rel_path: str) -> bool:
    try:
        src = _disk_path_from_rel_path(rel_path)
        if not src.exists() or not src.is_file():
            return False
        result = _ai_describe_image_path(src)
        if not result:
            return False
        tags = _normalize_ai_desc_tags(result.get("tags"), max_tags=96)
        caption = str(result.get("caption") or "").strip() or _build_desc_caption(tags)
        with closing(get_conn()) as conn:
            _store_photo_ai_description(conn, photo_id, tags or [], caption)
            conn.commit()
        return bool(caption or tags)
    except AiDescribeRuntimeUnavailable:
        raise
    except Exception:
        return False


def _describe_one_photo(photo_id: int, rel_path: str) -> bool:
    model = ai_desc_model_enabled()
    if model == "qwen":
        return _describe_one_photo_qwen(photo_id, rel_path)
    return _describe_one_photo_light(photo_id, rel_path)


def _describe_missing_photos(stop_event=None, include_existing: bool = False) -> Dict[str, Any]:
    global ai_desc_running, ai_desc_counts, last_ai_desc_result
    ai_desc_running = True
    ai_desc_counts = {"described": 0, "failed": 0, "total": 0}
    log_event("ai_desc_start", include_existing=bool(include_existing))
    stopped = False
    try:
        with closing(get_conn()) as conn:
            if include_existing:
                rows = conn.execute(
                    """
                    SELECT id, rel_path
                    FROM photos
                    ORDER BY COALESCE(captured_at, imported_at, created_fs, modified_fs, rel_path) ASC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, rel_path
                    FROM photos
                    WHERE (
                        ai_desc_tags IS NULL
                        OR TRIM(ai_desc_tags) = ''
                        OR TRIM(ai_desc_tags) IN ('[]', 'null')
                        OR ai_desc_caption IS NULL
                        OR TRIM(ai_desc_caption) = ''
                    )
                    """
                ).fetchall()
        for row in rows:
            if stop_event and stop_event.is_set():
                stopped = True
                break
            pid = int(row["id"])
            rel = row["rel_path"]
            ai_desc_counts["total"] += 1
            try:
                ok = _describe_one_photo(pid, rel)
                if stop_event and stop_event.is_set():
                    stopped = True
                    break
                if ok:
                    ai_desc_counts["described"] += 1
                    log_event("ai_desc_ok", rel_path=rel)
                else:
                    ai_desc_counts["failed"] += 1
                    log_event("ai_desc_fail", rel_path=rel)
            except AiDescribeRuntimeUnavailable as exc:
                ai_desc_counts["failed"] += 1
                stopped = True
                log_event("ai_desc_runtime_error_stop", rel_path=rel, error=str(exc))
                break
            except Exception:
                if stop_event and stop_event.is_set():
                    stopped = True
                    break
                ai_desc_counts["failed"] += 1
                log_event("ai_desc_fail", rel_path=rel)
            ai_delay = ai_ingest_throttle_enabled_sec()
            if ai_delay > 0:
                slept = 0.0
                while slept < ai_delay:
                    if stop_event and stop_event.is_set():
                        stopped = True
                        break
                    step = min(0.25, ai_delay - slept)
                    time.sleep(step)
                    slept += step
                if stopped:
                    break
    finally:
        if stop_event and stop_event.is_set():
            stopped = True
        ai_desc_running = False
        last_ai_desc_result = {"ok": True, "stopped": stopped, **ai_desc_counts}
        if stopped:
            log_event("ai_desc_stopped", **ai_desc_counts)
        else:
            log_event("ai_desc_done", **ai_desc_counts)
    return last_ai_desc_result


def _describe_uploaded_photo_if_needed(rel_path: str) -> None:
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id, ai_desc_tags, ai_desc_caption FROM photos WHERE rel_path=?", (rel_path,)).fetchone()
        if not row:
            return
        if _ai_desc_has_content(row["ai_desc_tags"], row["ai_desc_caption"]):
            return
        pid = int(row["id"])
        if _describe_one_photo(pid, rel_path):
            log_event("ai_desc_ok", rel_path=rel_path, source="upload")
        else:
            log_event("ai_desc_fail", rel_path=rel_path, source="upload")
    except Exception as e:
        log_event("ai_desc_fail", rel_path=rel_path, source="upload", error=str(e))


def _clear_all_ai_tags_and_descriptions(conn: sqlite3.Connection) -> tuple[int, int]:
    rows = conn.execute("SELECT id, ai_tags, ai_desc_tags, ai_desc_caption, metadata_json FROM photos").fetchall()
    cleared = 0
    ai_clear_keys = {
        "tags",
        "desc_tags",
        "desc_caption",
        "desc_external_claimed_at",
        "desc_external_worker",
        "desc_external_error",
        "desc_external_error_at",
        "desc_external_source",
        "desc_external_completed_at",
    }
    root_clear_keys = {"ai_tags", "ai_desc_tags", "ai_desc_caption"}

    def has_raw_content(value: Any) -> bool:
        text = str(value or "").strip()
        return bool(text and text.lower() not in {"[]", "null"})

    for row in rows:
        raw_meta = row["metadata_json"]
        meta = _json_object(raw_meta)
        meta_changed = False
        had_content = bool(
            has_raw_content(row["ai_tags"])
            or has_raw_content(row["ai_desc_tags"])
            or str(row["ai_desc_caption"] or "").strip()
        )

        ai_meta = meta.get("ai") if isinstance(meta.get("ai"), dict) else None
        if ai_meta:
            cleaned_ai = dict(ai_meta)
            for key in ai_clear_keys:
                if key in cleaned_ai:
                    cleaned_ai.pop(key, None)
                    meta_changed = True
                    had_content = True
            if meta_changed:
                if cleaned_ai:
                    meta["ai"] = cleaned_ai
                else:
                    meta.pop("ai", None)

        for key in root_clear_keys:
            if key in meta:
                meta.pop(key, None)
                meta_changed = True
                had_content = True

        if not had_content and not meta_changed:
            continue

        conn.execute(
            "UPDATE photos SET ai_tags=?, ai_desc_tags=?, ai_desc_caption=?, metadata_json=? WHERE id=?",
            (
                json.dumps([], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                None,
                json.dumps(meta, ensure_ascii=False, default=str) if meta_changed else raw_meta,
                int(row["id"]),
            ),
        )
        cleared += 1

    return cleared, len(rows)


@app.route("/api/ai/ingest", methods=["POST"])
def api_ai_ingest():
    global ai_thread
    if ai_thread and ai_thread.is_alive():
        return jsonify({"ok": False, "error": "AI ingest already running"}), 409
    scope = (request.args.get("scope") or "").strip().lower()
    _set_setting("ai_auto_ingest", "1")
    if scope == "new":
        return jsonify({"ok": True, "started": False, "running": False, "auto_ingest": True, "scope": "new"})
    scan_stop_event.clear()
    def run():
        _embed_missing_photos(stop_event=scan_stop_event)
    ai_thread = threading.Thread(target=run, daemon=True)
    ai_thread.start()
    return jsonify({"ok": True, "started": True, "auto_ingest": True, "scope": (scope or "all")})


@app.route("/api/ai/stop", methods=["POST"])
def api_ai_stop():
    _set_setting("ai_auto_ingest", "0")
    if not ai_running:
        return jsonify({"ok": True, "running": False, "auto_ingest": False})
    scan_stop_event.set()
    return jsonify({"ok": True, "running": True, "stopping": True, "auto_ingest": False})


@app.route("/api/ai/status")
def api_ai_status():
    rt = _ai_runtime_info()
    resp: Dict[str, Any] = {
        "ok": True,
        "running": ai_running,
        "auto_ingest": ai_auto_ingest_enabled(),
        **ai_counts,
        "coverage": _ai_embedding_coverage(),
        "runtime": {
            "service_ok": rt["service_ok"],
            "ai": rt["ai_device"],
            "faces": rt["face_device"],
            "ai_raw": rt["ai_device_raw"],
            "faces_raw": rt["face_device_raw"],
        },
    }
    if not ai_running and last_ai_result:
        resp["last"] = last_ai_result
    return jsonify(resp)


@app.route("/api/ai/describe/ingest", methods=["POST"])
def api_ai_describe_ingest():
    global ai_desc_thread
    if ai_desc_external_enabled():
        return jsonify({"ok": False, "error": "external_ai_descriptions_enabled", "external": True}), 409
    if ai_desc_thread and ai_desc_thread.is_alive():
        return jsonify({"ok": False, "error": "AI description ingest already running"}), 409
    scope = (request.args.get("scope") or "").strip().lower()
    _set_setting("ai_desc_auto_ingest", "1")
    if scope == "new":
        return jsonify({"ok": True, "started": False, "running": False, "auto_ingest": True, "scope": "new", "model": ai_desc_model_enabled()})
    ai_desc_stop_event.clear()

    def run():
        _describe_missing_photos(stop_event=ai_desc_stop_event)

    ai_desc_thread = threading.Thread(target=run, daemon=True)
    ai_desc_thread.start()
    return jsonify({"ok": True, "started": True, "auto_ingest": True, "scope": (scope or "all"), "model": ai_desc_model_enabled()})


@app.route("/api/ai/describe/stop", methods=["POST"])
def api_ai_describe_stop():
    _set_setting("ai_desc_auto_ingest", "0")
    force = str(request.args.get("force") or request.args.get("hard") or "").strip().lower() in {"1", "true", "yes", "on"}
    ai_desc_stop_event.set()
    runtime_stop = _ai_stop_description_runtime(force=force)
    if not ai_desc_running:
        return jsonify({"ok": True, "running": False, "stopping": False, "force": force, "auto_ingest": False, "runtime_stop": runtime_stop})
    if force:
        log_event("ai_desc_force_stop", runtime=runtime_stop)
    else:
        log_event("ai_desc_stop_requested", runtime=runtime_stop)
    return jsonify({"ok": True, "running": True, "stopping": True, "force": force, "auto_ingest": False, "runtime_stop": runtime_stop})


@app.route("/api/ai/describe/status")
def api_ai_describe_status():
    model = ai_desc_model_enabled()
    external_payload = _ai_desc_external_settings_payload(include_token=False)
    external_enabled = bool(external_payload.get("enabled"))
    rt = (
        {"service_ok": True, "ai_device": "external", "qwen_device": "external", "face_device": "external", "ai_device_raw": "external", "qwen_device_raw": "external", "face_device_raw": "external"}
        if external_enabled
        else _ai_runtime_info()
    )
    resp: Dict[str, Any] = {
        "ok": True,
        "running": False if external_enabled else ai_desc_running,
        "stopping": False if external_enabled else bool(ai_desc_running and ai_desc_stop_event.is_set()),
        "auto_ingest": ai_desc_auto_ingest_enabled(),
        "model": model,
        "model_options": ["light", "qwen"],
        "request_timeout_sec": AI_DESC_REQUEST_TIMEOUT_SEC,
        "external": external_payload,
        **ai_desc_counts,
        "runtime": {
            "service_ok": rt["service_ok"],
            "describe": ("external" if external_enabled else (rt["qwen_device"] if model == "qwen" else rt["ai_device"])),
            "ai": rt["ai_device"],
            "qwen": rt["qwen_device"],
            "faces": rt["face_device"],
            "ai_raw": rt["ai_device_raw"],
            "qwen_raw": rt["qwen_device_raw"],
            "faces_raw": rt["face_device_raw"],
        },
    }
    if not ai_desc_running and last_ai_desc_result:
        resp["last"] = last_ai_desc_result
    return jsonify(resp)


@app.route("/api/ai/describe/model", methods=["POST"])
def api_ai_describe_model():
    global ai_desc_thread
    if ai_desc_external_enabled():
        return jsonify({"ok": False, "error": "external_ai_descriptions_enabled", "external": True}), 409
    payload = request.get_json(silent=True) or {}
    model = _normalize_ai_desc_model(payload.get("model"))
    scope = str(payload.get("scope") or "new").strip().lower()
    if scope not in {"new", "all"}:
        scope = "new"

    _set_setting("ai_desc_model", model)

    started = False
    running_now = bool(ai_desc_running or (ai_desc_thread and ai_desc_thread.is_alive()))
    auto_enabled = ai_desc_auto_ingest_enabled()

    if scope == "all" and auto_enabled:
        if running_now:
            return jsonify({"ok": False, "error": "AI description ingest already running", "running": True, "model": model}), 409

        ai_desc_stop_event.clear()

        def run():
            _describe_missing_photos(stop_event=ai_desc_stop_event, include_existing=True)

        ai_desc_thread = threading.Thread(target=run, daemon=True)
        ai_desc_thread.start()
        started = True
        running_now = True

    return jsonify(
        {
            "ok": True,
            "model": model,
            "scope": scope,
            "auto_ingest": ai_desc_auto_ingest_enabled(),
            "running": running_now,
            "started": started,
        }
    )


@app.route("/api/ai/describe/rerun", methods=["POST"])
def api_ai_describe_rerun():
    """Re-run descriptions for all photos, replacing each item only after a new result succeeds."""
    global ai_desc_thread
    if ai_desc_external_enabled():
        return jsonify({"ok": False, "error": "external_ai_descriptions_enabled", "external": True}), 409
    if ai_desc_thread and ai_desc_thread.is_alive():
        return jsonify({"ok": False, "error": "AI description ingest already running"}), 409

    ai_desc_stop_event.clear()

    def run():
        _describe_missing_photos(stop_event=ai_desc_stop_event, include_existing=True)

    ai_desc_thread = threading.Thread(target=run, daemon=True)
    ai_desc_thread.start()
    log_event("ai_desc_rerun_started", model=ai_desc_model_enabled())
    return jsonify({
        "ok": True,
        "started": True,
        "running": True,
        "model": ai_desc_model_enabled(),
    })


@app.route("/api/ai/describe/clear", methods=["POST"])
def api_ai_describe_clear():
    global ai_desc_counts, last_ai_desc_result
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    running_now = bool(ai_desc_running or (ai_desc_thread and ai_desc_thread.is_alive()))
    if running_now:
        return jsonify({"ok": False, "error": "AI description ingest already running"}), 409
    try:
        with closing(get_conn()) as conn:
            cleared, total = _clear_all_ai_tags_and_descriptions(conn)
            conn.commit()
    except Exception as e:
        return jsonify({"ok": False, "error": f"clear_ai_desc_failed: {e}"}), 500

    ai_desc_counts = {"described": 0, "failed": 0, "total": 0}
    last_ai_desc_result = {"ok": True, "cleared": cleared, "total": total}
    log_event("ai_desc_clear", cleared=cleared, total=total)
    return jsonify({"ok": True, "cleared": cleared, "total": total})


@app.route("/api/ai/describe/external/settings", methods=["GET", "POST"])
def api_ai_describe_external_settings():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    if request.method == "GET":
        with closing(get_conn()) as conn:
            return jsonify(_ai_desc_external_settings_payload(conn, include_token=True))

    payload = request.get_json(silent=True) or {}
    enabled = bool(payload.get("enabled"))
    rotate_token = bool(payload.get("rotate_token"))
    folders = _normalize_ai_desc_external_folders(payload.get("folders"))

    if rotate_token:
        token = _add_ai_desc_external_token()
    else:
        token = _ai_desc_external_token()
    if enabled and not token:
        token = _ensure_ai_desc_external_token()
    elif token:
        _save_ai_desc_external_token_records(_ai_desc_external_token_records())
        _set_setting("ai_desc_external_token", token)

    _set_ai_desc_external_folders(folders)
    _set_setting("ai_desc_external_enabled", "1" if enabled else "0")
    if enabled:
        _set_setting("ai_desc_auto_ingest", "0")
        ai_desc_stop_event.set()

    with closing(get_conn()) as conn:
        resp = _ai_desc_external_settings_payload(conn, include_token=True)
    resp["token"] = token or resp.get("token") or ""
    resp["connection_url"] = _ai_desc_external_connection_url(resp["token"])
    return jsonify(resp)


@app.route("/api/ai/describe/external/links")
def api_ai_describe_external_links():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    return jsonify({"ok": True, "links": _ai_desc_external_public_links()})


@app.route("/api/ai/describe/external/links/<link_id>", methods=["DELETE"])
def api_ai_describe_external_link_delete(link_id: str):
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    target = str(link_id or "").strip()
    records = _ai_desc_external_token_records()
    kept = [item for item in records if str(item.get("id") or "").strip() != target]
    if len(kept) == len(records):
        return jsonify({"ok": False, "error": "not_found"}), 404

    removed_current = str(_get_setting("ai_desc_external_token", "") or "").strip() not in {
        str(item.get("token") or "").strip() for item in kept
    }
    _save_ai_desc_external_token_records(kept)
    if removed_current:
        _set_setting("ai_desc_external_token", str(kept[-1].get("token") or "").strip() if kept else "")
    return jsonify({
        "ok": True,
        "links": _ai_desc_external_public_links(),
        "token": _ai_desc_external_token(),
        "connection_url": _ai_desc_external_connection_url(_ai_desc_external_token()),
    })


@app.route("/api/ai/describe/external/ping")
def api_ai_describe_external_ping():
    auth = _ai_desc_external_require_auth()
    if auth:
        return auth
    with closing(get_conn()) as conn:
        payload = _ai_desc_external_settings_payload(conn, include_token=False)
    payload["server_time"] = now_iso()
    return jsonify(payload)


def _next_ai_desc_external_photo(conn: sqlite3.Connection, worker: str = "") -> Optional[sqlite3.Row]:
    folders = _ai_desc_external_folders()
    if not folders:
        return None
    rows = conn.execute(
        f"""
        SELECT id, rel_path, filename, ai_desc_tags, ai_desc_caption, metadata_json
        FROM photos
        WHERE {_ai_desc_external_missing_where()}
        ORDER BY COALESCE(captured_at, imported_at, created_fs, modified_fs, rel_path) ASC
        LIMIT 500
        """
    ).fetchall()
    now_ts = time.time()
    for row in rows:
        rel = str(row["rel_path"] or "")
        if not _ai_desc_external_rel_allowed(rel, folders):
            continue
        src = _disk_path_from_rel_path(rel)
        if not src.exists() or not src.is_file():
            continue
        meta = _json_object(row["metadata_json"])
        if _ai_desc_external_claim_is_fresh(meta, now_ts):
            continue
        _mark_ai_desc_external_claim(conn, row, worker=worker)
        conn.commit()
        return row
    return None


@app.route("/api/ai/describe/external/next")
def api_ai_describe_external_next():
    auth = _ai_desc_external_require_auth()
    if auth:
        return auth
    if not ai_desc_external_enabled():
        return jsonify({"ok": False, "error": "external_ai_descriptions_disabled"}), 409

    worker = str(request.args.get("worker") or request.headers.get("X-Worker-Name") or "").strip()
    with closing(get_conn()) as conn:
        row = _next_ai_desc_external_photo(conn, worker=worker)
        counts = _ai_desc_external_counts(conn, _ai_desc_external_folders())
    if not row:
        return jsonify({"ok": True, "item": None, **counts})

    image_url = url_for("api_ai_describe_external_image", photo_id=int(row["id"]))
    return jsonify(
        {
            "ok": True,
            "item": {
                "photo_id": int(row["id"]),
                "rel_path": row["rel_path"],
                "filename": row["filename"],
                "image_url": image_url,
            },
            **counts,
        }
    )


@app.route("/api/ai/describe/external/image/<int:photo_id>")
def api_ai_describe_external_image(photo_id: int):
    auth = _ai_desc_external_require_auth()
    if auth:
        return auth
    if not ai_desc_external_enabled():
        return jsonify({"ok": False, "error": "external_ai_descriptions_disabled"}), 409

    folders = _ai_desc_external_folders()
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT id, rel_path, filename FROM photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not_found"}), 404
    rel = str(row["rel_path"] or "")
    if not _ai_desc_external_rel_allowed(rel, folders):
        return jsonify({"ok": False, "error": "not_in_external_scope"}), 403
    src = _disk_path_from_rel_path(rel)
    if not src.exists() or not src.is_file():
        return jsonify({"ok": False, "error": "file_missing"}), 404

    try:
        view_path = ensure_viewable_copy(src, rel)
    except Exception:
        view_path = src
    download_name = Path(str(row["filename"] or view_path.name)).with_suffix(view_path.suffix or Path(str(row["filename"] or "image.jpg")).suffix).name
    return send_file(str(view_path), as_attachment=False, download_name=download_name)


@app.route("/api/ai/describe/external/result", methods=["POST"])
def api_ai_describe_external_result():
    auth = _ai_desc_external_require_auth()
    if auth:
        return auth
    if not ai_desc_external_enabled():
        return jsonify({"ok": False, "error": "external_ai_descriptions_disabled"}), 409

    payload = request.get_json(silent=True) or {}
    try:
        photo_id = int(payload.get("photo_id") or payload.get("id") or 0)
    except Exception:
        photo_id = 0
    if photo_id <= 0:
        return jsonify({"ok": False, "error": "invalid_photo_id"}), 400

    worker = str(payload.get("worker") or request.headers.get("X-Worker-Name") or "").strip()
    error = str(payload.get("error") or "").strip()
    caption = str(payload.get("caption") or "").strip()
    tags = _normalize_ai_desc_tags(payload.get("tags"), max_tags=96)

    with closing(get_conn()) as conn:
        row = conn.execute("SELECT id, rel_path FROM photos WHERE id=?", (photo_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "not_found"}), 404
        if not _ai_desc_external_rel_allowed(str(row["rel_path"] or ""), _ai_desc_external_folders()):
            return jsonify({"ok": False, "error": "not_in_external_scope"}), 403

        if error and not (caption or tags):
            _mark_ai_desc_external_error(conn, photo_id, error)
            conn.commit()
            log_event("ai_desc_external_fail", rel_path=row["rel_path"], error=error[:240], worker=worker)
            counts = _ai_desc_external_counts(conn, _ai_desc_external_folders())
            return jsonify({"ok": True, "stored": False, "error_recorded": True, **counts})

        if not caption and not tags:
            return jsonify({"ok": False, "error": "empty_description"}), 400

        _store_photo_ai_description(conn, photo_id, tags or [], caption or _build_desc_caption(tags))
        _mark_ai_desc_external_stored(conn, photo_id, worker=worker)
        conn.commit()
        log_event("ai_desc_external_ok", rel_path=row["rel_path"], worker=worker)
        counts = _ai_desc_external_counts(conn, _ai_desc_external_folders())
    return jsonify({"ok": True, "stored": True, "photo_id": photo_id, **counts})


@app.route("/api/ai/search")
def api_ai_search():
    q = (request.args.get("q") or "").strip()
    limit = max(1, min(200, int(request.args.get("limit", "60"))))
    if not q:
        return jsonify({"items": [], "count": 0})
    vec = _ai_embed_text(q)
    if not vec:
        return jsonify({"items": [], "count": 0, "error": "embed_failed"})
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT * FROM photos WHERE embedding_json IS NOT NULL AND embedding_json != ''").fetchall()
    scored = []
    for r in rows:
        try:
            emb = json.loads(r["embedding_json"]) if r["embedding_json"] else None
            sc = _cosine(vec, emb) if emb else -1.0
            scored.append((sc, r))
        except Exception:
            continue
    scored.sort(key=lambda x: x[0], reverse=True)
    items = [row_to_public(r) for (s, r) in scored[:limit] if s > -0.5]
    items = _filter_public_items_by_current_user_acl(items)
    return jsonify({"items": items, "count": len(items), "q": q})


@app.route("/api/ai/hardware/qwen/unload", methods=["POST"])
def api_ai_hardware_qwen_unload():
    try:
        r = requests.post(f"{AI_URL}/qwen/unload", timeout=5)
        if r.ok:
            try:
                js = r.json()
            except Exception:
                js = {"ok": True}
            return jsonify({"ok": True, **(js or {})})
        return jsonify({"ok": False, "status": int(r.status_code)}), int(r.status_code or 500)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)[:240]}), 502


@app.route("/api/photos/<int:photo_id>/similar")
def api_similar(photo_id: int):
    limit = max(1, min(200, int(request.args.get("limit", "60"))))
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not_found"}), 404
    if not _is_rel_path_allowed_for_current_user(row["rel_path"]):
        return jsonify({"ok": False, "error": "not_found"}), 404
    source_folder_key = _similar_rel_folder_key(str(row["rel_path"] or ""))
    emb = None
    try:
        emb = json.loads(row["embedding_json"]) if row["embedding_json"] else None
    except Exception:
        emb = None
    if not emb:
        # compute on the fly
        p = PHOTO_DIR / row["rel_path"]
        emb = _ai_embed_image_path(p)
        if not emb:
            return jsonify({"ok": False, "error": "embed_failed"}), 500
        with closing(get_conn()) as conn:
            conn.execute("UPDATE photos SET embedding_json=? WHERE id=?", (json.dumps(emb), photo_id))
            conn.commit()
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT * FROM photos WHERE embedding_json IS NOT NULL AND embedding_json != '' AND id<>?", (photo_id,)).fetchall()
    scored = []
    for r in rows:
        rel = str(r["rel_path"] or "")
        if _similar_rel_folder_key(rel) != source_folder_key:
            continue
        try:
            e2 = json.loads(r["embedding_json"]) if r["embedding_json"] else None
            s = _cosine(emb, e2) if e2 else -1.0
            scored.append((s, r))
        except Exception:
            continue
    scored.sort(key=lambda x: x[0], reverse=True)
    items = [row_to_public(r) for (s, r) in scored[:limit] if s > -0.5]
    items = _filter_public_items_by_current_user_acl(items)
    return jsonify({"items": items, "count": len(items)})


@app.route("/api/photos/<int:photo_id>/similar-phash")
def api_similar_phash(photo_id: int):
    limit = max(1, min(200, int(request.args.get("limit", "120"))))
    method = str(request.args.get("mode") or request.args.get("method") or "hash").strip().lower()
    if method not in {"hash", "ai", "hybrid"}:
        method = "hash"
    try:
        ai_min_similarity = float(request.args.get("ai_min_similarity", request.args.get("ai_min", "0.88")))
    except Exception:
        ai_min_similarity = 0.88
    if ai_min_similarity > 1.0:
        ai_min_similarity = ai_min_similarity / 100.0
    ai_min_similarity = max(-1.0, min(1.0, ai_min_similarity))
    phash_thr = _clamp_hash_distance_arg("phash_distance", _clamp_hash_distance_arg("distance", 9))
    dhash_thr = _clamp_hash_distance_arg("dhash_distance", 12)
    ahash_thr = _clamp_hash_distance_arg("ahash_distance", 12)
    thresholds = {"phash": phash_thr, "dhash": dhash_thr, "ahash": ahash_thr}

    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT id, rel_path, phash, phash_dct, dhash, ahash FROM photos WHERE id=?",
            (photo_id,),
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "not_found"}), 404
        if not _is_rel_path_allowed_for_current_user(row["rel_path"], conn):
            return jsonify({"ok": False, "error": "not_found"}), 404

        source_folder_key = _similar_rel_folder_key(str(row["rel_path"] or ""))
        source_row = conn.execute("SELECT * FROM photos WHERE id=?", (photo_id,)).fetchone()
        source_item = row_to_public(source_row) if source_row else None
        ai_folder_coverage = _ai_embedding_coverage_for_source_folder(conn, str(row["rel_path"] or ""))
        hash_distances_by_id: dict[int, Dict[str, int]] = {}
        hash_quality_by_id: dict[int, float] = {}
        hash_rank_by_id: dict[int, int] = {}
        ai_similarity_by_id: dict[int, float] = {}
        ai_rank_by_id: dict[int, int] = {}

        def hash_results() -> list[int]:
            seed = _ensure_photo_hashes(conn, dict(row))
            seed_hashes = {
                "phash": _photo_hash_value(seed, "phash_dct"),
                "dhash": _photo_hash_value(seed, "dhash"),
                "ahash": _photo_hash_value(seed, "ahash"),
            }
            if not all(seed_hashes.values()):
                return []

            candidates = conn.execute(
                """
                SELECT id, rel_path, phash, phash_dct, dhash, ahash
                FROM photos
                WHERE id<>?
                  AND (
                    phash IS NOT NULL OR phash_dct IS NOT NULL OR dhash IS NOT NULL OR ahash IS NOT NULL
                  )
                """,
                (photo_id,),
            ).fetchall()
            broad_ahash_prefilter = max(ahash_thr + 12, ahash_thr * 2, 24)
            combined_threshold = max(1, phash_thr + dhash_thr + ahash_thr)

            def scan_candidates(full_scan: bool = False) -> list[tuple[int, int, int, int, int, int]]:
                scored_rows: list[tuple[int, int, int, int, int, int]] = []
                for r in candidates:
                    candidate = dict(r)
                    rel = str(candidate.get("rel_path") or "")
                    if _similar_rel_folder_key(rel) != source_folder_key:
                        continue
                    if not _is_rel_path_allowed_for_current_user(rel, conn):
                        continue

                    candidate_ahash = _photo_hash_value(candidate, "ahash")
                    has_all_candidate_hashes = all(
                        _photo_hash_value(candidate, key) for key in ("ahash", "dhash", "phash_dct")
                    )
                    if not has_all_candidate_hashes:
                        if candidate_ahash and not full_scan:
                            ahash_dist = _hamdist_hex(seed_hashes["ahash"], candidate_ahash)
                            if ahash_dist > broad_ahash_prefilter:
                                continue
                        candidate = _ensure_photo_hashes(conn, candidate)

                    candidate_hashes = {
                        "phash": _photo_hash_value(candidate, "phash_dct"),
                        "dhash": _photo_hash_value(candidate, "dhash"),
                        "ahash": _photo_hash_value(candidate, "ahash"),
                    }
                    if not all(candidate_hashes.values()):
                        continue

                    distances = {
                        "phash": _hamdist_hex(seed_hashes["phash"], candidate_hashes["phash"]),
                        "dhash": _hamdist_hex(seed_hashes["dhash"], candidate_hashes["dhash"]),
                        "ahash": _hamdist_hex(seed_hashes["ahash"], candidate_hashes["ahash"]),
                    }
                    matched, pass_count, combined = _similar_hash_match(distances, thresholds)
                    if not matched:
                        continue

                    pid = int(candidate.get("id") or 0)
                    hash_distances_by_id[pid] = {
                        "phash": int(distances["phash"]),
                        "dhash": int(distances["dhash"]),
                        "ahash": int(distances["ahash"]),
                        "combined": int(combined),
                        "matched_hashes": int(pass_count),
                    }
                    hash_quality_by_id[pid] = max(0.0, min(1.0, 1.0 - (float(combined) / float(combined_threshold + 12))))
                    scored_rows.append((
                        0 if pass_count >= 2 else 1,
                        combined,
                        int(distances["phash"]),
                        int(distances["dhash"]),
                        int(distances["ahash"]),
                        pid,
                    ))
                return scored_rows

            scored = scan_candidates(full_scan=False)
            if not scored:
                scored = scan_candidates(full_scan=True)
            scored.sort(key=lambda x: (x[0], x[1], x[2], x[3], x[4], -x[5]))
            ordered: list[int] = []
            seen: set[int] = set()
            for rank, (_match_rank, _combined, _pd, _dd, _ad, pid) in enumerate(scored):
                if pid in seen:
                    continue
                seen.add(pid)
                hash_rank_by_id[pid] = rank
                ordered.append(pid)
            return ordered

        def ai_results() -> list[int]:
            source_emb = _json_embedding(source_row["embedding_json"] if source_row else None)
            if not source_emb and source_row and _is_ai_embedding_supported_rel(str(source_row["rel_path"] or "")):
                src = _disk_path_from_rel_path(str(source_row["rel_path"] or ""))
                source_emb = _ai_embed_image_path(src) if src.exists() else None
                if source_emb:
                    conn.execute("UPDATE photos SET embedding_json=? WHERE id=?", (json.dumps(source_emb), photo_id))
                    conn.commit()
            if not source_emb:
                return []

            rows = conn.execute(
                """
                SELECT id, rel_path, embedding_json
                FROM photos
                WHERE id<>?
                  AND embedding_json IS NOT NULL
                  AND embedding_json != ''
                """,
                (photo_id,),
            ).fetchall()
            scored: list[tuple[float, int]] = []
            for r in rows:
                rel = str(r["rel_path"] or "")
                if _similar_rel_folder_key(rel) != source_folder_key:
                    continue
                if not _is_rel_path_allowed_for_current_user(rel, conn):
                    continue
                emb = _json_embedding(r["embedding_json"])
                if not emb:
                    continue
                similarity = _cosine(source_emb, emb)
                if similarity < ai_min_similarity:
                    continue
                pid = int(r["id"] or 0)
                ai_similarity_by_id[pid] = float(similarity)
                scored.append((float(similarity), pid))
            scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
            ordered = []
            for rank, (_score, pid) in enumerate(scored):
                ai_rank_by_id[pid] = rank
                ordered.append(pid)
            return ordered

        hash_ids = hash_results() if method in {"hash", "hybrid"} else []
        ai_ids = ai_results() if method in {"ai", "hybrid"} else []

        if method == "hash":
            ordered_ids = hash_ids[:limit]
        elif method == "ai":
            ordered_ids = ai_ids[:limit]
        else:
            union_ids = set(hash_ids[: max(limit * 2, 120)])
            union_ids.update(ai_ids[: max(limit * 2, 120)])

            def hybrid_score(pid: int) -> tuple[float, int, int, int]:
                ai_sim = ai_similarity_by_id.get(pid)
                ai_norm = max(0.0, min(1.0, ((float(ai_sim) + 1.0) / 2.0))) if ai_sim is not None else 0.0
                hash_quality = float(hash_quality_by_id.get(pid, 0.0))
                both_bonus = 0.08 if (pid in ai_similarity_by_id and pid in hash_distances_by_id) else 0.0
                combined_score = (ai_norm * 0.68) + (hash_quality * 0.32) + both_bonus
                return (
                    combined_score,
                    -int(ai_rank_by_id.get(pid, 999999)),
                    -int(hash_rank_by_id.get(pid, 999999)),
                    int(pid),
                )

            ordered_ids = sorted(union_ids, key=hybrid_score, reverse=True)[:limit]

        if not ordered_ids:
            return jsonify({
                "ok": True,
                "items": [],
                "count": 0,
                "distance": phash_thr,
                "distances": thresholds,
                "ai_min_similarity": round(ai_min_similarity, 4),
                "source_item": source_item,
                "ai_folder_coverage": ai_folder_coverage,
                "method": method,
                "source": "ai_embedding" if method == "ai" else ("hash_ai_hybrid" if method == "hybrid" else "multi_hash_near"),
            })

        top_ids = ordered_ids
        ph = ",".join(["?"] * len(top_ids))
        rows = conn.execute(f"SELECT * FROM photos WHERE id IN ({ph})", top_ids).fetchall()
        by_id = {int(r["id"]): r for r in rows}

        items = []
        for pid in top_ids:
            r = by_id.get(pid)
            if not r:
                continue
            pub = row_to_public(r)
            distances = hash_distances_by_id.get(pid)
            if distances:
                pub["distance"] = int(distances.get("combined") or 0)
                pub["hash_distances"] = distances
            if pid in ai_similarity_by_id:
                pub["ai_similarity"] = round(float(ai_similarity_by_id[pid]), 6)
            items.append(pub)

    return jsonify({
        "ok": True,
        "items": items,
        "count": len(items),
        "distance": phash_thr,
        "distances": thresholds,
        "ai_min_similarity": round(ai_min_similarity, 4),
        "source_item": source_item,
        "ai_folder_coverage": ai_folder_coverage,
        "method": method,
        "source": "ai_embedding" if method == "ai" else ("hash_ai_hybrid" if method == "hybrid" else "multi_hash_near"),
    })


@app.route("/api/photos/<int:photo_id>/ai-tags", methods=["POST"])
def api_ai_tags(photo_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT id, rel_path, embedding_json, ai_tags FROM photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not_found"}), 404
    if not _is_rel_path_allowed_for_current_user(row["rel_path"]):
        return jsonify({"ok": False, "error": "not_found"}), 404
    try:
        emb = json.loads(row["embedding_json"]) if row["embedding_json"] else None
        if not emb:
            p = PHOTO_DIR / row["rel_path"]
            emb = _ai_embed_image_path(p)
            if not emb:
                return jsonify({"ok": False, "error": "embed_failed"}), 500
            with closing(get_conn()) as conn:
                conn.execute("UPDATE photos SET embedding_json=? WHERE id=?", (json.dumps(emb), photo_id))
                conn.commit()
        tags = _classify_labels(emb)
        with closing(get_conn()) as conn:
            prev = []
            if row["ai_tags"]:
                try:
                    prev = json.loads(row["ai_tags"]) or []
                except Exception:
                    prev = []
            merged = sorted({*(prev or []), *(tags or [])})
            conn.execute("UPDATE photos SET ai_tags=? WHERE id=?", (json.dumps(merged, ensure_ascii=False), photo_id))
            conn.commit()
        return jsonify({"ok": True, "tags": merged})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def clear_index() -> Dict[str, Any]:
    init_db()
    log_event("clear_start")
    thumbs_deleted = 0
    converted_deleted = 0
    # Delete thumbs safely inside THUMB_DIR only
    for p in THUMB_DIR.glob("*"):
        try:
            if p.is_file():
                p.unlink(missing_ok=True)
                thumbs_deleted += 1
        except Exception as e:
            log_event("error", rel_path=str(p), error=str(e))

    # Delete converted cache safely inside CONVERT_DIR (may contain subfolders)
    try:
        for p in CONVERT_DIR.rglob("*"):
            try:
                if p.is_file():
                    p.unlink(missing_ok=True)
                    converted_deleted += 1
            except Exception as e:
                log_event("error", rel_path=str(p), error=str(e))
        # Optionally clean up empty directories
        for d in sorted([x for x in CONVERT_DIR.rglob("*") if x.is_dir()], key=lambda x: len(str(x)), reverse=True):
            try:
                d.rmdir()
            except Exception:
                pass
    except Exception as e:
        log_event("error", rel_path="converted_clear", error=str(e))

    try:
        with closing(get_conn()) as conn:
            photos = conn.execute("SELECT COUNT(*) AS c FROM photos").fetchone()["c"]
            faces = conn.execute("SELECT COUNT(*) AS c FROM faces").fetchone()["c"]
            people = conn.execute("SELECT COUNT(*) AS c FROM people").fetchone()["c"]
            conn.execute("DELETE FROM faces")
            conn.execute("DELETE FROM people")
            conn.execute("DELETE FROM photos")
            # Commit deletes before VACUUM (cannot VACUUM inside a transaction)
            conn.commit()
            conn.execute("VACUUM")
            conn.commit()
    except Exception as e:
        log_event("error", rel_path="db_clear", error=str(e))
        return {"ok": False, "error": str(e)}

    res = {"ok": True, "removed": {"photos": photos, "faces": faces, "people": people, "thumbs": thumbs_deleted, "converted": converted_deleted}}
    log_event("clear_done", **res["removed"])  # type: ignore[arg-type]
    return res


@app.route("/api/clear", methods=["POST"])
def api_clear():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    # Do not touch PHOTO_DIR; only DB + thumbs in DATA_DIR
    result = clear_index()
    return jsonify(result), 200


def _safe_rmtree_contents(root: Path) -> dict:
    """Delete all contents inside 'root' without removing the root directory itself.
    Returns counts of removed files and directories.
    """
    removed_files = 0
    removed_dirs = 0
    try:
        if not root.exists():
            return {"files": 0, "dirs": 0}
        # Remove files first
        for p in root.rglob("*"):
            try:
                if p.is_file():
                    p.unlink(missing_ok=True)
                    removed_files += 1
            except Exception:
                pass
        # Then attempt to remove empty directories deepest-first
        for d in sorted([x for x in root.rglob("*") if x.is_dir()], key=lambda x: len(str(x)), reverse=True):
            try:
                d.rmdir()
                removed_dirs += 1
            except Exception:
                pass
    except Exception:
        pass
    return {"files": removed_files, "dirs": removed_dirs}


@app.route("/api/factory-reset", methods=["POST"])
def api_factory_reset():
    # Admin-only: full wipe of app-generated data and DB
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    try:
        # Stop any background processing
        try:
            scan_stop_event.set()
        except Exception:
            pass

        # Clear runtime upload queues
        try:
            with UPLOAD_PENDING_LOCK:
                UPLOAD_PENDING_BY_USER.clear()
        except Exception:
            pass

        # No eager directory creation; proceed directly to clearing
        # Step 1: Clear index (DB photos/faces/people) and thumbs using existing helper
        clear_res = clear_index()

        # Step 2: Remove additional caches and uploads
        converted = _safe_rmtree_contents(CONVERT_DIR)
        uploads = _safe_rmtree_contents(UPLOAD_DIR)
        tus_tmp = _safe_rmtree_contents(TUS_TMP_DIR)

        # Step 3: Clear non-user content tables (shares, geo cache)
        geo_deleted = 0
        weather_deleted = 0
        place_geocode_deleted = 0
        share_deleted = 0
        share_folders_deleted = 0
        login_audit_deleted = 0
        try:
            with closing(get_conn()) as conn:
                try:
                    row = conn.execute("SELECT COUNT(*) AS c FROM geo_cache").fetchone()
                    geo_deleted = int(row["c"]) if row else 0
                    conn.execute("DELETE FROM geo_cache")
                except Exception:
                    pass
                try:
                    row = conn.execute("SELECT COUNT(*) AS c FROM weather_cache").fetchone()
                    weather_deleted = int(row["c"]) if row else 0
                    conn.execute("DELETE FROM weather_cache")
                except Exception:
                    pass
                try:
                    row = conn.execute("SELECT COUNT(*) AS c FROM place_geocode_cache").fetchone()
                    place_geocode_deleted = int(row["c"]) if row else 0
                    conn.execute("DELETE FROM place_geocode_cache")
                except Exception:
                    pass
                try:
                    row = conn.execute("SELECT COUNT(*) AS c FROM share_link_folders").fetchone()
                    share_folders_deleted = int(row["c"]) if row else 0
                    conn.execute("DELETE FROM share_link_folders")
                except Exception:
                    pass
                try:
                    row = conn.execute("SELECT COUNT(*) AS c FROM share_links").fetchone()
                    share_deleted = int(row["c"]) if row else 0
                    conn.execute("DELETE FROM share_links")
                except Exception:
                    pass
                # Optional: clear login audit to reduce DB size on reset (keeps users)
                try:
                    row = conn.execute("SELECT COUNT(*) AS c FROM login_audit").fetchone()
                    login_audit_deleted = int(row["c"]) if row else 0
                    conn.execute("DELETE FROM login_audit")
                except Exception:
                    pass
                conn.commit()
                try:
                    conn.execute("VACUUM")
                    conn.commit()
                except Exception:
                    pass
        except Exception:
            pass

        # Reset in-memory logs
        try:
            global LOG_SEQ
            LOG_BUFFER.clear()
            LOG_SEQ = 0
        except Exception:
            pass

        # Do not recreate directories here; they will be created lazily on use (e.g., first upload)

        payload = {
            "ok": True,
            "removed": {
                "photos": (clear_res.get("removed", {}) or {}).get("photos", 0),
                "faces": (clear_res.get("removed", {}) or {}).get("faces", 0),
                "people": (clear_res.get("removed", {}) or {}).get("people", 0),
                "thumbs": (clear_res.get("removed", {}) or {}).get("thumbs", 0),
                "converted_files": converted.get("files", 0),
                "converted_dirs": converted.get("dirs", 0),
                "uploads_files": uploads.get("files", 0),
                "uploads_dirs": uploads.get("dirs", 0),
                "tus_tmp_files": tus_tmp.get("files", 0),
                "tus_tmp_dirs": tus_tmp.get("dirs", 0),
                "geo_rows": geo_deleted,
                "weather_rows": weather_deleted,
                "place_geocode_rows": place_geocode_deleted,
                "share_links": share_deleted,
                "share_link_folders": share_folders_deleted,
                "login_audit": login_audit_deleted,
            },
            # No redirect to setup; users are preserved
        }
        log_event("factory_reset_done", **payload["removed"])  # type: ignore[arg-type]
        return jsonify(payload), 200
    except Exception as e:
        log_event("error", rel_path="factory_reset", error=str(e))
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/photos")
def api_photos():
    q = request.args.get("q", "").strip()
    view = request.args.get("view", "library")
    sort = request.args.get("sort", "date_desc")
    folder = request.args.get("folder")
    direct_only = str(request.args.get("direct") or "").strip().lower() in {"1", "true", "yes", "on"}
    try:
        offset = int(str(request.args.get("offset") or "0"))
    except Exception:
        offset = 0
    try:
        limit = int(str(request.args.get("limit") or "0"))
    except Exception:
        limit = 0
    # Sanitize
    offset = max(0, offset)
    # Default to no limit unless client requests it; cap to avoid abuse
    if limit <= 0:
        limit = None
    else:
        limit = max(1, min(2000, limit))
    requested_lang = request.args.get("search_lang")
    _, user_lang = _current_user_pref_languages()
    search_language = _normalize_language(requested_lang, user_lang)

    try:
        disk_sync: Optional[Dict[str, Any]] = None
        if view == "mapper":
            try:
                sync_folder = _normalize_upload_folder_for_disk_sync(folder)
                sync_rel = f"uploads/{sync_folder}" if sync_folder else "uploads"
                if _is_rel_visible_for_current_user(sync_rel):
                    disk_sync = _sync_upload_folder_from_disk(
                        sync_folder,
                        recursive=not direct_only,
                        max_files=UPLOAD_FOLDER_SYNC_MAX_FILES,
                        queue_postprocess=True,
                    )
            except Exception as sync_err:
                disk_sync = {"ok": False, "error": str(sync_err)}
        items = query_photos(view, sort, folder=folder, offset=offset, limit=limit, direct_only=direct_only)
        if q:
            # Try AI-assisted expansion to widen matches when helpful
            expand_tags: list[str] = []
            if AI_QUERY_EXPAND_ENABLED:
                try:
                    expand_tags = _ai_expand_query_tags(q, language=search_language)
                except Exception:
                    expand_tags = []
            if expand_tags:
                items = [
                    p for p in items
                    if matches_search(p, q, search_language=search_language) or _photo_contains_any_tags(p, expand_tags)
                ]
            else:
                items = [p for p in items if matches_search(p, q, search_language=search_language)]
        items = _filter_public_items_by_current_user_acl(items)
        # Provide pagination hints. When limited, we cannot know total cheaply without extra COUNT.
        has_more = bool(limit) and (len(items) >= int(limit or 0))
        next_offset = (offset or 0) + len(items)
        return jsonify({
            "items": items,
            "count": len(items),
            "query": q,
            "view": view,
            "sort": sort,
            "folder": folder,
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "next_offset": next_offset,
            "search_lang": search_language,
            "disk_sync": disk_sync,
        })
    except Exception as e:
        try:
            log_event("error", rel_path="api/photos", error=str(e), view=view, sort=sort, folder=str(folder or ""))
        except Exception:
            pass
        return jsonify({
            "items": [],
            "count": 0,
            "query": q,
            "view": view,
            "sort": sort,
            "folder": folder,
            "search_lang": search_language,
            "ok": False,
            "error": str(e),
        }), 200


@app.route("/api/photos/<int:photo_id>")
def api_photo_detail(photo_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Not found"}), 404
    if not _is_rel_path_allowed_for_current_user(row["rel_path"]):
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "item": row_to_public(row)})


@app.route("/api/photos/<int:photo_id>/weather", methods=["POST"])
@login_required
def api_photo_weather(photo_id: int):
    data = request.get_json(silent=True) or {}
    force = bool(data.get("force"))
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Not found"}), 404
        if not _is_rel_path_allowed_for_current_user(row["rel_path"]):
            return jsonify({"ok": False, "error": "Not found"}), 404

        weather, source = get_or_fetch_photo_weather(row, force=force)
        with closing(get_conn()) as conn:
            fresh = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
        return jsonify({"ok": True, "weather": weather, "source": source, "item": row_to_public(fresh)})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        try:
            _mark_photo_weather_fetch_failed(int(photo_id))
        except Exception:
            pass
        try:
            log_event("error", rel_path=f"weather:{photo_id}", error=str(e))
        except Exception:
            pass
        return jsonify({"ok": False, "error": str(e)}), 502


@app.route("/api/photos/<int:photo_id>/captured-at", methods=["POST"])
@login_required
def api_update_captured_at(photo_id: int):
    try:
        data = request.get_json(silent=True) or {}
        raw = str(data.get("captured_at") or "").strip()
        if not raw:
            return jsonify({"ok": False, "error": "Missing date"}), 400
        # Accept 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DDTHH:MM:SS' (local)
        if len(raw) == 16:
            raw = raw + ":00"
        try:
            dt = datetime.fromisoformat(raw)
        except Exception:
            return jsonify({"ok": False, "error": "Invalid date format"}), 400
        iso = dt.isoformat(timespec="seconds")
        with closing(get_conn()) as conn:
            # Update DB
            conn.execute("UPDATE photos SET captured_at=? WHERE id=?", (iso, photo_id))
            _clear_photo_weather_metadata(conn, photo_id)
            row = conn.execute("SELECT rel_path FROM photos WHERE id=?", (photo_id,)).fetchone()
            conn.commit()
        # Update file mtime to help sorting when EXIF is absent
        try:
            rel = row["rel_path"] if row else None
            if rel:
                safe_rel = rel.replace("..", "").lstrip("/")
                if safe_rel.startswith("uploads/"):
                    fpath = UPLOAD_DIR / safe_rel[len("uploads/"):]
                else:
                    fpath = PHOTO_DIR / safe_rel
                if fpath.exists():
                    ts = dt.timestamp()
                    os.utime(fpath, (ts, ts))
        except Exception:
            pass
        _refresh_photo_weather_if_possible(photo_id, force=False)
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT * FROM photos WHERE id=?", (photo_id,)).fetchone()
        return jsonify({"ok": True, "item": row_to_public(row)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/photos/<int:photo_id>/gps", methods=["POST"])
@login_required
def api_update_gps(photo_id: int):
    try:
        data = request.get_json(silent=True) or {}
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            return jsonify({"ok": False, "error": "Missing coordinates"}), 400
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except Exception:
            return jsonify({"ok": False, "error": "Invalid coordinates"}), 400
        if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
            return jsonify({"ok": False, "error": "Invalid coordinates"}), 400
        country, city = reverse_geocode_with_cache(lat_f, lon_f)
        name = ", ".join([x for x in [city, country] if x]) if (country or city) else None
        with closing(get_conn()) as conn:
            # Update columns + metadata_json.geo
            row0 = conn.execute("SELECT metadata_json FROM photos WHERE id=?", (photo_id,)).fetchone()
            mj = {}
            try:
                mj = json.loads(row0["metadata_json"]) if row0 and row0["metadata_json"] else {}
            except Exception:
                mj = {}
            geo = mj.get("geo", {})
            if country: geo["country"] = country
            if city: geo["city"] = city
            mj["geo"] = geo
            mj.pop("weather", None)
            mj.pop("weather_fetch_failed", None)
            conn.execute(
                "UPDATE photos SET gps_lat=?, gps_lon=?, gps_name=?, metadata_json=? WHERE id=?",
                (lat_f, lon_f, name, json.dumps(mj, ensure_ascii=False), photo_id),
            )
            conn.commit()
        _refresh_photo_weather_if_possible(photo_id, force=False)
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT * FROM photos WHERE id=?", (photo_id,)).fetchone()
        return jsonify({"ok": True, "item": row_to_public(row)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/photos/<int:photo_id>/favorite", methods=["POST"])
def api_toggle_favorite(photo_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT favorite FROM photos WHERE id = ?", (photo_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Not found"}), 404
        new_val = 0 if int(row["favorite"] or 0) else 1
        conn.execute("UPDATE photos SET favorite = ? WHERE id = ?", (new_val, photo_id))
        conn.commit()
    return jsonify({"ok": True, "favorite": bool(new_val)})


@app.route("/api/photos/delete", methods=["POST"])
@login_required
def api_delete_photos():
    try:
        data = request.get_json(silent=True) or {}
        raw_ids = data.get("photo_ids")
        if not isinstance(raw_ids, list):
            return jsonify({"ok": False, "error": "Angiv photo_ids"}), 400
        ids = [int(pid) for pid in raw_ids if str(pid).isdigit()]
        if not ids:
            return jsonify({"ok": False, "error": "Ingen billeder valgt"}), 400
        allowed: list[int] = []
        with closing(get_conn()) as conn:
            ph = ",".join(["?"] * len(ids))
            rows = conn.execute(f"SELECT id, rel_path FROM photos WHERE id IN ({ph})", ids).fetchall()
            for r in rows:
                rel = str(r[1] or "")
                # Require edit permission on the containing folder
                if _perm_allows(_current_user_folder_permission_for_rel(rel, conn), "edit"):
                    allowed.append(int(r[0]))
        if not allowed:
            return jsonify({"ok": False, "error": "Ingen slette-adgang"}), 403
        removed = _delete_indexed_photos_by_ids(allowed)
        return jsonify({"ok": True, "removed": removed, "deleted_ids": allowed, "preview_folders": removed.get("preview_folders") or []})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/filters")
def api_filters():
    with closing(get_conn()) as conn:
        acl_prefixes = _current_user_acl_prefixes(conn)
        if acl_prefixes is None:
            total = conn.execute("SELECT COUNT(*) AS c FROM photos").fetchone()["c"]
            favorites = conn.execute("SELECT COUNT(*) AS c FROM photos WHERE favorite = 1").fetchone()["c"]
            places = conn.execute("SELECT COUNT(*) AS c FROM photos WHERE gps_lat IS NOT NULL OR gps_name IS NOT NULL").fetchone()["c"]
            cameras = [r["camera_model"] for r in conn.execute(
                "SELECT DISTINCT camera_model FROM photos WHERE camera_model IS NOT NULL AND camera_model != '' ORDER BY camera_model"
            ).fetchall()]
        else:
            conds = []
            params: list[Any] = []
            for pref in acl_prefixes:
                conds.append("(rel_path=? OR rel_path LIKE ?)")
                params.extend([pref, pref + "/%"])
            acl_where = " OR ".join(conds) if conds else "0=1"
            total = conn.execute(f"SELECT COUNT(*) AS c FROM photos WHERE ({acl_where})", params).fetchone()["c"]
            favorites = conn.execute(f"SELECT COUNT(*) AS c FROM photos WHERE favorite = 1 AND ({acl_where})", params).fetchone()["c"]
            places = conn.execute(f"SELECT COUNT(*) AS c FROM photos WHERE (gps_lat IS NOT NULL OR gps_name IS NOT NULL) AND ({acl_where})", params).fetchone()["c"]
            cameras = [r["camera_model"] for r in conn.execute(
                f"SELECT DISTINCT camera_model FROM photos WHERE camera_model IS NOT NULL AND camera_model != '' AND ({acl_where}) ORDER BY camera_model",
                params,
            ).fetchall()]
    return jsonify({
        "total": total,
        "favorites": favorites,
        "places": places,
        "cameras": cameras,
        "ai_search_ready": False,
        "ai_note": "AI sÃ¸gning/ansigter er klargjort i data-modellen, men ONNX/CLIP service er nÃ¦ste trin.",
    })


@app.route("/api/thumbs/<path:thumb_name>")
def api_thumb_file(thumb_name: str):
    # Serve hashed thumbnail names with aggressive caching
    safe = re.sub(r"[^a-zA-Z0-9._-]", "", str(thumb_name or ""))
    if not safe:
        return ("Not found", 404)
    p = THUMB_DIR / safe
    if not p.exists() or not p.is_file():
        return ("Not found", 404)
    resp = send_from_directory(str(THUMB_DIR), safe)
    # Filename is content-addressed (md5), safe to cache long-term
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


def _cleanup_orphan_thumbs(dry_run: bool = False) -> dict:
    """Remove thumbnails on disk that are no longer referenced in DB.
    Preserves current photo thumbnails (photos.thumb_name) and generated face_* thumbs.
    Returns {removed, bytes_freed}.
    """
    used: set[str] = set()
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT thumb_name FROM photos WHERE thumb_name IS NOT NULL").fetchall()
        for r in rows:
            tn = str(r["thumb_name"] or "").strip()
            if tn:
                used.add(tn)
        # Protect existing face thumbs
        face_rows = conn.execute("SELECT id FROM faces").fetchall()
        for fr in face_rows:
            try:
                used.add(f"face_{int(fr['id'])}.jpg")
            except Exception:
                continue

    removed = 0
    bytes_freed = 0
    try:
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    for p in THUMB_DIR.glob("*"):
        try:
            if not p.is_file():
                continue
            name = p.name
            if name in used:
                continue
            size = p.stat().st_size
            if not dry_run:
                try:
                    p.unlink(missing_ok=True)  # type: ignore[call-arg]
                except TypeError:
                    try:
                        p.unlink()
                    except Exception:
                        continue
            removed += 1
            bytes_freed += int(size or 0)
        except Exception:
            continue
    return {"removed": removed, "bytes_freed": bytes_freed}


@app.route("/api/thumbs/cleanup", methods=["POST"])
def api_thumbs_cleanup():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    dry = str((request.args.get("dry") or "").strip().lower()) in {"1", "true", "yes"}
    res = _cleanup_orphan_thumbs(dry_run=dry)
    return jsonify({"ok": True, **res, "dry_run": dry})
def api_thumbs(thumb_name: str):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT rel_path FROM photos WHERE thumb_name=? LIMIT 1", (thumb_name,)).fetchone()
    if row and not _is_rel_path_allowed_for_current_user(row["rel_path"]):
        return ("Forbidden", 403)
    return send_from_directory(THUMB_DIR, thumb_name)


@app.route("/api/original/<path:rel_path>")
def api_original(rel_path: str):
    # Serve original file safely from PHOTO_DIR
    # Prevent path escape
    safe_rel = rel_path.replace("..", "").lstrip("/")
    if not _is_rel_path_allowed_for_current_user(safe_rel):
        return ("Forbidden", 403)
    # If uploaded file (prefixed with 'uploads/'), serve from UPLOAD_DIR
    if safe_rel.startswith("uploads/"):
        up_rel = safe_rel[len("uploads/"):]
        return send_from_directory(str(UPLOAD_DIR), up_rel)
    if not library_source_enabled():
        return ("Not found", 404)
    directory = str(PHOTO_DIR)
    return send_from_directory(directory, safe_rel)


@app.route("/api/viewable/<path:rel_path>")
def api_viewable(rel_path: str):
    # Return a browser/AI-friendly version; convert HEICâ†’JPEG into CONVERT_DIR when needed
    safe_rel = rel_path.replace("..", "").lstrip("/")
    if not _is_rel_path_allowed_for_current_user(safe_rel):
        return ("Forbidden", 403)
    if safe_rel.startswith("uploads/"):
        src = UPLOAD_DIR / safe_rel[len("uploads/"):]
    else:
        if not library_source_enabled():
            return ("Not found", 404)
        src = PHOTO_DIR / safe_rel
    if not src.exists():
        # Fallback: maybe already a converted file reference
        cand = CONVERT_DIR / safe_rel
        if cand.exists():
            return send_from_directory(CONVERT_DIR, safe_rel)
        return ("Not found", 404)
    view_path = ensure_viewable_copy(src, safe_rel)
    # Serve from the appropriate root
    try:
        vp = str(view_path.resolve(strict=False))
        convert_root = str(CONVERT_DIR.resolve(strict=False))
        uploads_root = str(UPLOAD_DIR.resolve(strict=False))
        photo_root = str(PHOTO_DIR.resolve(strict=False))
        if vp.startswith(convert_root):
            rel_conv = str(view_path.relative_to(CONVERT_DIR)).replace("\\", "/")
            resp = send_from_directory(CONVERT_DIR, rel_conv)
            try: resp.headers["Cache-Control"] = "public, max-age=86400"  # 1 day
            except Exception: pass
            return resp
        if vp.startswith(uploads_root):
            rel_up = str(view_path.relative_to(UPLOAD_DIR)).replace("\\", "/")
            resp = send_from_directory(UPLOAD_DIR, rel_up)
            try: resp.headers["Cache-Control"] = "public, max-age=86400"
            except Exception: pass
            return resp
        if vp.startswith(photo_root):
            rel_photo = str(view_path.relative_to(PHOTO_DIR)).replace("\\", "/")
            resp = send_from_directory(PHOTO_DIR, rel_photo)
            try: resp.headers["Cache-Control"] = "public, max-age=86400"
            except Exception: pass
            return resp
        # Last-resort fallback to original request path
        if safe_rel.startswith("uploads/"):
            resp = send_from_directory(UPLOAD_DIR, safe_rel[len("uploads/"):])
            try: resp.headers["Cache-Control"] = "public, max-age=86400"
            except Exception: pass
            return resp
        resp = send_from_directory(PHOTO_DIR, safe_rel)
        try: resp.headers["Cache-Control"] = "public, max-age=86400"
        except Exception: pass
        return resp
    except Exception as e:
        return (str(e), 500)


def _find_existing_converted_for_upload_rel(rel_path: str, extensions: Optional[Iterable[str]] = None) -> Optional[Path]:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    if rel.startswith("uploads/originals/"):
        tail = rel[len("uploads/originals/"):]
    elif rel.startswith("uploads/converted/"):
        tail = rel[len("uploads/converted/"):]
    elif rel.startswith("uploads/"):
        tail = rel[len("uploads/"):]
    else:
        return None
    base = Path(tail).with_suffix("")
    parent = base.parent
    stem = base.name
    found: list[Path] = []
    exts = tuple(
        (e if str(e or "").startswith(".") else f".{e}").lower()
        for e in (extensions or (".jpg", ".jpeg", ".png", ".webp"))
        if str(e or "").strip()
    )
    for ext in exts:
        cand = UPLOAD_DIR / "converted" / parent / f"{stem}{ext}"
        if cand.exists() and cand.is_file():
            found.append(cand)
    if found:
        try:
            return sorted(found, key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)[0]
        except Exception:
            return found[0]

    # Fallback: include collision-resolved names like stem_1.jpg, stem_2.jpg, ...
    conv_parent = UPLOAD_DIR / "converted" / parent
    if not conv_parent.exists() or not conv_parent.is_dir():
        return None
    try:
        for ext in exts:
            for cand in conv_parent.glob(f"{stem}_*{ext}"):
                if cand.exists() and cand.is_file():
                    found.append(cand)
    except Exception:
        return None
    if found:
        try:
            return sorted(found, key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)[0]
        except Exception:
            return found[0]
    return None


def _find_existing_original_for_converted_rel(rel_path: str) -> Optional[Path]:
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")
    if rel.startswith("uploads/converted/"):
        tail = rel[len("uploads/converted/"):]
    else:
        return None
    base = Path(tail).with_suffix("")
    orig_dir = UPLOAD_DIR / "originals" / base.parent
    if not orig_dir.exists() or not orig_dir.is_dir():
        return None
    try:
        candidates = sorted(orig_dir.glob(f"{base.name}.*"))
    except Exception:
        candidates = []
    for cand in candidates:
        if cand.exists() and cand.is_file():
            return cand
    return None


def _resolve_download_path(src: Path, rel_path: str, mode: str) -> Path:
    """Resolve download file for requested mode.
    - original: use original path (if row points at converted, try mirrored original first)
    - converted: for uploads/*, ONLY use existing mirrored converted file by filename;
      otherwise fall back to original. No ad-hoc conversion for uploads during download.
      For library files outside uploads/*, keep existing viewable fallback behavior.
    """
    mode_norm = str(mode or "converted").strip().lower()
    rel = str(rel_path or "").replace("\\", "/").lstrip("/")

    if mode_norm == "original":
        if rel.startswith("uploads/converted/"):
            orig = _find_existing_original_for_converted_rel(rel)
            if orig is not None and orig.exists():
                return orig
        return src

    # converted
    if rel.startswith("uploads/"):
        converted_exts = (".mp4",) if Path(rel).suffix.lower() in {".mov", ".mp4"} else None
        converted = _find_existing_converted_for_upload_rel(rel, extensions=converted_exts)
        if converted is not None and converted.exists():
            return converted
        if rel.startswith("uploads/converted/"):
            orig = _find_existing_original_for_converted_rel(rel)
            if orig is not None and orig.exists():
                return orig
        return src

    # Non-upload/library paths: keep previous behavior
    return ensure_viewable_copy(src, rel)


@app.route("/api/photos/download/<int:photo_id>")
def api_photo_download(photo_id: int):
    """Download a single photo as attachment.
    Query param mode=converted|original. Converted prefers a browser-friendly copy
    if available, otherwise falls back to the original.
    """
    mode = str(request.args.get("mode") or "converted").strip().lower()
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        return ("Not found", 404)
    rel = str(row["rel_path"] or "").replace("..", "").lstrip("/")
    if not rel or not _is_rel_path_allowed_for_current_user(rel):
        return ("Forbidden", 403)

    # Resolve physical file path
    src = (UPLOAD_DIR / rel[len("uploads/"):]) if rel.startswith("uploads/") else (PHOTO_DIR / rel)
    use_path = _resolve_download_path(src, rel, mode)
    if not use_path.exists():
        return ("Not found", 404)

    filename = use_path.name
    try:
        return send_file(str(use_path), as_attachment=True, download_name=filename)
    except TypeError:
        return send_file(str(use_path), as_attachment=True)


@app.route("/api/photos/download-zip", methods=["POST"])
def api_photos_download_zip():
    """Zip and download multiple photos.
    Body: { photo_ids: [int], mode: 'converted'|'original' }
    """
    body = request.get_json(silent=True) or {}
    raw_ids = body.get("photo_ids")
    mode = str(body.get("mode") or "converted").strip().lower()
    if not isinstance(raw_ids, list) or not raw_ids:
        return jsonify({"ok": False, "error": "Angiv photo_ids"}), 400
    ids = [int(pid) for pid in raw_ids if str(pid).isdigit()]
    if not ids:
        return jsonify({"ok": False, "error": "Ingen gyldige billeder valgt"}), 400

    with closing(get_conn()) as conn:
        rows = conn.execute(
            f"SELECT * FROM photos WHERE id IN ({','.join(['?']*len(ids))})",
            tuple(ids),
        ).fetchall()

    files = []  # list[(Path, name)]
    for r in rows:
        try:
            rel = str(r["rel_path"] or "").replace("..", "").lstrip("/")
            if not rel or not _is_rel_path_allowed_for_current_user(rel):
                continue
            src = (UPLOAD_DIR / rel[len("uploads/"):]) if rel.startswith("uploads/") else (PHOTO_DIR / rel)
            use_path = _resolve_download_path(src, rel, mode)
            if not use_path.exists():
                continue
            files.append((use_path, use_path.name))
        except Exception:
            continue
    if not files:
        return ("Not found", 404)

    import tempfile, zipfile
    tmp = tempfile.TemporaryFile()
    with zipfile.ZipFile(tmp, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        used = set()
        for p, name in files:
            base = name
            if base in used:
                stem = Path(base).stem
                suff = Path(base).suffix
                i = 2
                while f"{stem}_{i}{suff}" in used:
                    i += 1
                base = f"{stem}_{i}{suff}"
            used.add(base)
            try:
                zf.write(p, arcname=base)
            except Exception:
                continue
    try:
        tmp.seek(0)
        fname = f"fjordlens_download_{len(files)}.zip"
        return send_file(tmp, mimetype="application/zip", as_attachment=True, download_name=fname)
    except TypeError:
        tmp.seek(0)
        return send_file(tmp, mimetype="application/zip", as_attachment=True)


@app.route("/api/debug/sample")
def api_debug_sample():
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM photos ORDER BY id DESC LIMIT 1").fetchone()
    return jsonify(row_to_public(row) if row else {"empty": True})


@app.route("/api/logs")
def api_logs():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    try:
        after = int(request.args.get("after", "0"))
    except ValueError:
        after = 0
    items = [itm for itm in list(LOG_BUFFER) if int(itm.get("id", 0)) > after]
    next_id = (items[-1]["id"] if items else (LOG_BUFFER[-1]["id"] if LOG_BUFFER else after))
    return jsonify({"items": items[:200], "next": next_id})


@app.route("/api/settings/upload-destination", methods=["GET", "POST"])
def api_settings_upload_destination():
    # Only protect write operations; reads are allowed for basic users (payload is ACL-filtered)
    if request.method == "POST":
        fb = _forbid_user_role_for_maintenance()
        if fb:
            return jsonify(fb[0]), fb[1]
        body = request.get_json(silent=True) or {}
        destination_raw = body.get("destination")
        destination = get_upload_destination() if destination_raw is None else str(destination_raw).strip().lower()
        if destination not in UPLOAD_DEST_CHOICES:
            return jsonify({"ok": False, "error": "Ugyldigt upload-destination-valg"}), 400
        if "subdir" in body:
            try:
                subdir = _normalize_upload_subdir(str(body.get("subdir") or ""))
            except Exception:
                return jsonify({"ok": False, "error": "Ugyldig undermappe"}), 400
            _set_upload_subdir(destination, subdir)
        _set_setting("upload_destination", destination)
        return jsonify(_upload_settings_payload(destination))

    requested = str(request.args.get("destination") or "").strip().lower()
    current = requested if requested in UPLOAD_DEST_CHOICES else get_upload_destination()
    try:
        payload = _upload_settings_payload(current)
        return jsonify(payload)
    except Exception as e:
        # Log and fall back to a minimal, safe payload so UI can render
        try:
            log_event("error", error=f"upload_destination_get: {e}")
        except Exception:
            pass
        try:
            opts = [
                {"value": "uploads", "label": "KopiÃ©r til uploads-mappen"},
                {"value": "library", "label": "Flyt (hurtigt) til bibliotek"},
            ]
        except Exception:
            opts = []
        return jsonify({
            "ok": True,
            "destination": current,
            "saved_destination": get_upload_destination(),
            "subdir": "",
            "folders": [],
            "photo_dir": str(PHOTO_DIR),
            "upload_dir": str(UPLOAD_DIR),
            "note": "(fallback) Mapper kunne ikke hentes",
            "options": opts,
        })


@app.route("/api/settings/upload-folder", methods=["POST"])
def api_settings_upload_folder():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    body = request.get_json(silent=True) or {}
    destination_raw = body.get("destination")
    destination = get_upload_destination() if destination_raw is None else str(destination_raw).strip().lower()
    if destination not in UPLOAD_DEST_CHOICES:
        return jsonify({"ok": False, "error": "Ugyldigt upload-destination-valg"}), 400

    try:
        parent_subdir = _normalize_upload_subdir(str(body.get("parent") or ""))
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldig overmappe"}), 400

    # Permission check: creating under uploads requires 'edit' on parent, or admin
    if destination == UPLOAD_DEST_UPLOADS:
        if parent_subdir:
            base_rel = f"uploads/{parent_subdir}"
            perm = _current_user_folder_permission_for_rel(base_rel)
            if not _perm_allows(perm, "edit") and not getattr(current_user, "is_admin", False):
                return jsonify({"ok": False, "error": "Ingen rettighed til at oprette i denne mappe"}), 403
        else:
            # Creating directly under uploads root limited to admins
            if not getattr(current_user, "is_admin", False):
                return jsonify({"ok": False, "error": "Kun admin kan oprette i rodmappen"}), 403

    try:
        new_subdir_input = _normalize_upload_subdir(str(body.get("path") or ""))
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldigt mappenavn"}), 400
    if not new_subdir_input:
        return jsonify({"ok": False, "error": "Angiv en mappe"}), 400

    # Create path relative to selected parent folder when parent is provided
    new_subdir = f"{parent_subdir}/{new_subdir_input}" if parent_subdir else new_subdir_input
    try:
        new_subdir = _normalize_upload_subdir(new_subdir)
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400

    if destination == UPLOAD_DEST_UPLOADS:
        # Canonicalize internal storage roots so mapper paths stay logical
        # (no nested uploads/originals/originals or uploads/converted/originals).
        if new_subdir == "originals" or new_subdir == "converted":
            return jsonify({"ok": False, "error": "Ugyldigt mappenavn"}), 400
        if new_subdir.startswith("originals/"):
            new_subdir = new_subdir[len("originals/"):]
        elif new_subdir.startswith("converted/"):
            new_subdir = new_subdir[len("converted/"):]
        if not new_subdir:
            return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400

    target_root, _ = _upload_target_for_destination(destination)
    try:
        target_root.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    try:
        base = target_root.resolve()
        target = (target_root / new_subdir).resolve()
        target.relative_to(base)
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400

    try:
        target.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Kunne ikke oprette mappe: {e}"}), 400

    if destination == UPLOAD_DEST_UPLOADS:
        try:
            mirror_root = (UPLOAD_DIR / "converted").resolve()
            mirror_target = (UPLOAD_DIR / "converted" / new_subdir).resolve()
            mirror_target.relative_to(mirror_root)
            mirror_target.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return jsonify({"ok": False, "error": f"Kunne ikke oprette konverteret mappe: {e}"}), 400

    _set_upload_subdir(destination, new_subdir)
    # Record folder owner for access control (owner and admins can always see; others need explicit ACL)
    try:
        owner_path = f"uploads/{new_subdir}" if destination == UPLOAD_DEST_UPLOADS else new_subdir
        with closing(get_conn()) as conn:
            conn.execute("INSERT OR REPLACE INTO folder_owners(folder_path, user_id) VALUES (?,?)", (owner_path, int(getattr(current_user, 'id', 0) or 0)))
            conn.commit()
    except Exception:
        pass
    payload = _upload_settings_payload(destination)
    payload["created"] = new_subdir
    return jsonify(payload)


@app.route("/api/settings/upload-folder-delete", methods=["POST"])
def api_settings_upload_folder_delete():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    body = request.get_json(silent=True) or {}
    destination = str(body.get("destination") or "uploads").strip().lower()
    if destination != UPLOAD_DEST_UPLOADS:
        return jsonify({"ok": False, "error": "Sletning understÃ¸ttes kun i uploads-mappen"}), 400

    raw_paths = body.get("paths")
    if isinstance(raw_paths, str):
        raw_paths = [raw_paths]
    if not isinstance(raw_paths, list):
        return jsonify({"ok": False, "error": "Angiv liste af mapper"}), 400

    normalized: list[str] = []
    for rp in raw_paths:
        try:
            safe = _normalize_upload_subdir(str(rp or ""))
        except Exception:
            return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400
        if destination == UPLOAD_DEST_UPLOADS:
            # Canonicalize internal storage prefixes to logical mapper path
            # so deleting "foo/bar" always targets both originals/ and converted/.
            if safe == "originals" or safe == "converted":
                safe = ""
            elif safe.startswith("originals/"):
                safe = safe[len("originals/"):]
            elif safe.startswith("converted/"):
                safe = safe[len("converted/"):]
        if safe:
            normalized.append(safe)
    if not normalized:
        return jsonify({"ok": False, "error": "VÃ¦lg mindst Ã©n mappe"}), 400

    # Keep top-most selected folders only (children of selected parents are redundant)
    normalized = sorted(set(normalized), key=lambda x: (x.count("/"), x.lower()))
    selected: list[str] = []
    for path in normalized:
        if any(path == p or path.startswith(p + "/") for p in selected):
            continue
        selected.append(path)

    target_root, rel_prefix = _upload_target_for_destination(destination)
    try:
        base = target_root.resolve()
        mirror_root: Optional[Path] = None
        mirror_base: Optional[Path] = None
        legacy_root: Optional[Path] = None
        legacy_base: Optional[Path] = None
        if destination == UPLOAD_DEST_UPLOADS:
            try:
                mirror_root = (UPLOAD_DIR / "converted")
                mirror_base = mirror_root.resolve()
            except Exception:
                mirror_root = None
                mirror_base = None
            try:
                legacy_root = UPLOAD_DIR
                legacy_base = legacy_root.resolve()
            except Exception:
                legacy_root = None
                legacy_base = None
    except Exception:
        return jsonify({"ok": False, "error": "Upload-rodmappe kunne ikke lÃ¦ses"}), 500

    deleted: list[str] = []
    missing: list[str] = []
    for subdir in selected:
        # Enforce per-folder manage permission
        base_rel = f"uploads/{subdir}" if subdir else "uploads"
        perm = _current_user_folder_permission_for_rel(base_rel)
        if not _perm_allows(perm, "edit"):
            return jsonify({"ok": False, "error": f"Ingen slette-adgang til '{subdir}'"}), 403
        deleted_any = False
        try:
            target = (target_root / subdir).resolve()
            target.relative_to(base)
        except Exception:
            return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400

        if target.exists() and target.is_dir():
            try:
                shutil.rmtree(target)
                deleted_any = True
            except Exception as e:
                return jsonify({"ok": False, "error": f"Kunne ikke slette mappe '{subdir}': {e}"}), 400

        if mirror_root is not None and mirror_base is not None:
            try:
                mirror_target = (mirror_root / subdir).resolve()
                mirror_target.relative_to(mirror_base)
            except Exception:
                return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400
            if mirror_target.exists() and mirror_target.is_dir():
                try:
                    shutil.rmtree(mirror_target)
                    deleted_any = True
                except Exception as e:
                    return jsonify({"ok": False, "error": f"Kunne ikke slette konverteret mappe '{subdir}': {e}"}), 400

        if legacy_root is not None and legacy_base is not None:
            try:
                legacy_target = (legacy_root / subdir).resolve()
                legacy_target.relative_to(legacy_base)
            except Exception:
                return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400
            if legacy_target.exists() and legacy_target.is_dir():
                try:
                    shutil.rmtree(legacy_target)
                    deleted_any = True
                except Exception as e:
                    return jsonify({"ok": False, "error": f"Kunne ikke slette legacy mappe '{subdir}': {e}"}), 400

        if deleted_any:
            deleted.append(subdir)
        else:
            missing.append(subdir)

    # Clean stale selected subdir setting if deleted
    current_subdir = get_upload_subdir(destination)
    if current_subdir and any(current_subdir == d or current_subdir.startswith(d + "/") for d in deleted):
        _set_upload_subdir(destination, "")

    # Purge index rows for folders we deleted and for stale DB-only folders that no longer exist on disk.
    cleanup_folders = sorted(set(deleted + missing), key=lambda x: (x.count("/"), x.lower()))
    rel_prefixes = [f"{rel_prefix}{d}" if rel_prefix else d for d in cleanup_folders]
    if destination == UPLOAD_DEST_UPLOADS:
        rel_prefixes.extend([f"uploads/converted/{d}" for d in cleanup_folders])
        rel_prefixes.extend([f"uploads/{d}" for d in cleanup_folders])
    removed = _delete_indexed_photos_for_prefixes(rel_prefixes)
    try:
        with closing(get_conn()) as conn:
            for folder in cleanup_folders:
                conn.execute(
                    "DELETE FROM folder_previews WHERE folder_path=? OR folder_path LIKE ?",
                    (folder, folder + "/%"),
                )
            conn.commit()
    except Exception:
        pass

    payload = _upload_settings_payload(destination)
    payload["deleted"] = deleted
    payload["missing"] = missing
    payload["removed_photos"] = removed.get("photos", 0)
    payload["removed_faces"] = removed.get("faces", 0)
    payload["removed_thumbs"] = removed.get("thumbs", 0)
    payload["preview_folders"] = sorted(
        set((removed.get("preview_folders") or []) + [k for folder in cleanup_folders for k in _folder_preview_ancestor_keys(folder)] + cleanup_folders),
        key=lambda x: (str(x).count("/"), str(x).lower()),
    )
    return jsonify(payload)


def _replace_path_prefix(value: Any, old_prefix: str, new_prefix: str) -> str:
    raw = str(value or "").replace("\\", "/").strip("/")
    old = str(old_prefix or "").replace("\\", "/").strip("/")
    new = str(new_prefix or "").replace("\\", "/").strip("/")
    if not raw or not old or not new:
        return raw
    if raw == old:
        return new
    pref = old + "/"
    if raw.startswith(pref):
        return new + raw[len(old):]
    return raw


def _merge_permission_value(a: Optional[str], b: Optional[str]) -> str:
    order = {"view": 1, "upload": 2, "edit": 3}
    va = str(a or "view").strip().lower()
    vb = str(b or "view").strip().lower()
    if va not in order:
        va = "view"
    if vb not in order:
        vb = "view"
    return va if order[va] >= order[vb] else vb


def _apply_upload_folder_rename_db(old_subdir: str, new_subdir: str) -> dict:
    old_sub = _normalize_upload_subdir(old_subdir)
    new_sub = _normalize_upload_subdir(new_subdir)
    if not old_sub or not new_sub:
        return {"photos_renamed": 0, "photos_conflicts_removed": 0}

    old_acl = f"uploads/{old_sub}"
    new_acl = f"uploads/{new_sub}"
    old_share_default = f"uploads/{old_sub}"
    conflict_thumbs: list[str] = []
    photos_renamed = 0
    photos_conflicts_removed = 0

    photo_prefix_pairs = [
        (f"uploads/originals/{old_sub}", f"uploads/originals/{new_sub}"),
        (f"uploads/converted/{old_sub}", f"uploads/converted/{new_sub}"),
        (f"uploads/{old_sub}", f"uploads/{new_sub}"),
    ]

    def _map_photo_rel(rel_path: str) -> str:
        rel = str(rel_path or "").replace("\\", "/").lstrip("/")
        for old_pref, new_pref in photo_prefix_pairs:
            if rel == old_pref:
                return new_pref
            if rel.startswith(old_pref + "/"):
                return new_pref + rel[len(old_pref):]
        return rel

    with closing(get_conn()) as conn:
        # Keep active upload target in sync when it points into renamed folder
        for key in ("upload_subdir_uploads", "upload_subdir"):
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            if not row:
                continue
            before = str(row["value"] or "")
            after = _replace_path_prefix(before, old_sub, new_sub)
            if after != before:
                conn.execute("UPDATE settings SET value=? WHERE key=?", (after, key))

        # ACL references
        acl_rows = conn.execute(
            """
            SELECT user_id, folder_path, permission, created_at
            FROM user_folder_access
            WHERE folder_path=? OR folder_path LIKE ?
            """,
            (old_acl, old_acl + "/%"),
        ).fetchall()
        for r in acl_rows:
            uid = int(r["user_id"] or 0)
            prev_path = str(r["folder_path"] or "")
            next_path = _replace_path_prefix(prev_path, old_acl, new_acl)
            if not next_path or next_path == prev_path:
                continue
            perm = str(r["permission"] or "view").strip().lower()
            if perm not in {"view", "upload", "edit"}:
                perm = "view"
            existing = conn.execute(
                "SELECT permission FROM user_folder_access WHERE user_id=? AND folder_path=? LIMIT 1",
                (uid, next_path),
            ).fetchone()
            if existing:
                merged = _merge_permission_value(existing["permission"], perm)
                conn.execute(
                    "UPDATE user_folder_access SET permission=? WHERE user_id=? AND folder_path=?",
                    (merged, uid, next_path),
                )
            else:
                conn.execute(
                    "INSERT INTO user_folder_access(user_id, folder_path, permission, created_at) VALUES(?,?,?,?)",
                    (uid, next_path, perm, str(r["created_at"] or now_iso())),
                )
        conn.execute(
            "DELETE FROM user_folder_access WHERE folder_path=? OR folder_path LIKE ?",
            (old_acl, old_acl + "/%"),
        )

        # Folder owners
        owner_rows = conn.execute(
            "SELECT folder_path, user_id FROM folder_owners WHERE folder_path=? OR folder_path LIKE ?",
            (old_acl, old_acl + "/%"),
        ).fetchall()
        for r in owner_rows:
            prev_path = str(r["folder_path"] or "")
            next_path = _replace_path_prefix(prev_path, old_acl, new_acl)
            if not next_path or next_path == prev_path:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO folder_owners(folder_path, user_id) VALUES(?,?)",
                (next_path, int(r["user_id"] or 0)),
            )
        conn.execute(
            "DELETE FROM folder_owners WHERE folder_path=? OR folder_path LIKE ?",
            (old_acl, old_acl + "/%"),
        )

        # Folder previews
        preview_rows = conn.execute(
            "SELECT folder_path, previews_json, updated_at FROM folder_previews WHERE folder_path=? OR folder_path LIKE ?",
            (old_sub, old_sub + "/%"),
        ).fetchall()
        for r in preview_rows:
            prev_path = str(r["folder_path"] or "")
            next_path = _replace_path_prefix(prev_path, old_sub, new_sub)
            if not next_path or next_path == prev_path:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO folder_previews(folder_path, previews_json, updated_at) VALUES(?,?,?)",
                (next_path, str(r["previews_json"] or "[]"), str(r["updated_at"] or now_iso())),
            )
        conn.execute(
            "DELETE FROM folder_previews WHERE folder_path=? OR folder_path LIKE ?",
            (old_sub, old_sub + "/%"),
        )

        # Share folder references (multi-folder shares)
        slf_rows = conn.execute(
            "SELECT share_id, folder_path, created_at FROM share_link_folders WHERE folder_path=? OR folder_path LIKE ?",
            (old_sub, old_sub + "/%"),
        ).fetchall()
        for r in slf_rows:
            prev_path = str(r["folder_path"] or "")
            next_path = _replace_path_prefix(prev_path, old_sub, new_sub)
            if not next_path or next_path == prev_path:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO share_link_folders(share_id, folder_path, created_at) VALUES(?,?,?)",
                (int(r["share_id"] or 0), next_path, str(r["created_at"] or now_iso())),
            )
        conn.execute(
            "DELETE FROM share_link_folders WHERE folder_path=? OR folder_path LIKE ?",
            (old_sub, old_sub + "/%"),
        )

        # Share primary folder + default share_name
        share_rows = conn.execute(
            "SELECT id, folder_path, share_name FROM share_links WHERE folder_path=? OR folder_path LIKE ?",
            (old_sub, old_sub + "/%"),
        ).fetchall()
        for r in share_rows:
            prev_path = str(r["folder_path"] or "")
            next_path = _replace_path_prefix(prev_path, old_sub, new_sub)
            if not next_path or next_path == prev_path:
                continue
            share_name = str(r["share_name"] or "").strip()
            next_share_name = share_name
            if share_name == f"uploads/{prev_path}" or share_name == old_share_default:
                next_share_name = f"uploads/{next_path}"
            conn.execute(
                "UPDATE share_links SET folder_path=?, share_name=? WHERE id=?",
                (next_path, next_share_name, int(r["id"] or 0)),
            )

        # Indexed photo rel_path references
        where_parts: list[str] = []
        where_params: list[Any] = []
        for old_pref, _new_pref in photo_prefix_pairs:
            where_parts.append("(rel_path=? OR rel_path LIKE ?)")
            where_params.extend([old_pref, old_pref + "/%"])
        photo_rows = conn.execute(
            f"SELECT id, rel_path FROM photos WHERE {' OR '.join(where_parts)}",
            tuple(where_params),
        ).fetchall()
        for r in photo_rows:
            pid = int(r["id"] or 0)
            prev_rel = str(r["rel_path"] or "")
            next_rel = _map_photo_rel(prev_rel)
            if not next_rel or next_rel == prev_rel:
                continue
            conflict = conn.execute(
                "SELECT id, thumb_name FROM photos WHERE rel_path=? AND id<>? LIMIT 1",
                (next_rel, pid),
            ).fetchone()
            if conflict:
                conflict_id = int(conflict["id"] or 0)
                conn.execute("DELETE FROM faces WHERE photo_id=?", (conflict_id,))
                conn.execute("DELETE FROM photos WHERE id=?", (conflict_id,))
                thumb_name = str(conflict["thumb_name"] or "").strip()
                if thumb_name:
                    conflict_thumbs.append(thumb_name)
                photos_conflicts_removed += 1
            conn.execute("UPDATE photos SET rel_path=? WHERE id=?", (next_rel, pid))
            photos_renamed += 1

        conn.commit()

    # Best-effort cleanup of stale thumbs from removed conflict rows
    for tn in sorted(set(conflict_thumbs)):
        try:
            p = THUMB_DIR / tn
            if p.exists():
                p.unlink()
        except Exception:
            continue

    return {"photos_renamed": photos_renamed, "photos_conflicts_removed": photos_conflicts_removed}


@app.route("/api/settings/upload-folder-rename", methods=["POST"])
def api_settings_upload_folder_rename():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    body = request.get_json(silent=True) or {}
    destination = str(body.get("destination") or "uploads").strip().lower()
    if destination != UPLOAD_DEST_UPLOADS:
        return jsonify({"ok": False, "error": "OmdÃ¸bning understÃ¸ttes kun i uploads-mappen"}), 400

    try:
        old_subdir = _normalize_upload_subdir(str(body.get("path") or ""))
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400
    if old_subdir == "originals" or old_subdir == "converted":
        old_subdir = ""
    elif old_subdir.startswith("originals/"):
        old_subdir = old_subdir[len("originals/"):]
    elif old_subdir.startswith("converted/"):
        old_subdir = old_subdir[len("converted/"):]
    if not old_subdir:
        return jsonify({"ok": False, "error": "Rodmappen kan ikke omdÃ¸bes"}), 400

    new_name_raw = str(body.get("new_name") or "").strip()
    if not new_name_raw:
        return jsonify({"ok": False, "error": "Angiv nyt navn"}), 400
    try:
        new_name = _sanitize_folder_part_allow_spaces(new_name_raw)
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldigt nyt mappenavn"}), 400

    parent_subdir = old_subdir.rsplit("/", 1)[0] if "/" in old_subdir else ""
    new_subdir = f"{parent_subdir}/{new_name}" if parent_subdir else new_name
    try:
        new_subdir = _normalize_upload_subdir(new_subdir)
    except Exception:
        return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400

    if old_subdir.lower() == new_subdir.lower():
        return jsonify({"ok": False, "error": "Det nye navn skal vÃ¦re anderledes"}), 400

    base_rel = f"uploads/{old_subdir}"
    perm = _current_user_folder_permission_for_rel(base_rel)
    if not _perm_allows(perm, "edit"):
        return jsonify({"ok": False, "error": f"Ingen omdÃ¸b-adgang til '{old_subdir}'"}), 403

    roots = [UPLOAD_DIR / "originals", UPLOAD_DIR / "converted", UPLOAD_DIR]
    operations: list[tuple[Path, Path]] = []
    protected_roots: set[Path] = set()
    for root in roots:
        try:
            base = root.resolve()
            protected_roots.add(base)
            src = (root / old_subdir).resolve()
            dst = (root / new_subdir).resolve()
            src.relative_to(base)
            dst.relative_to(base)
        except Exception:
            return jsonify({"ok": False, "error": "Ugyldig mappe-sti"}), 400
        if src.exists() and src.is_dir():
            if dst.exists():
                return jsonify({"ok": False, "error": f"MÃ¥lmappen findes allerede: {new_subdir}"}), 409
            operations.append((src, dst))

    if not operations:
        return jsonify({"ok": False, "error": f"Mappen findes ikke: {old_subdir}"}), 404

    moved: list[tuple[Path, Path]] = []
    try:
        for src, dst in operations:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            moved.append((src, dst))
    except Exception as e:
        for src, dst in reversed(moved):
            try:
                if dst.exists() and not src.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    dst.rename(src)
            except Exception:
                pass
        return jsonify({"ok": False, "error": f"Kunne ikke omdÃ¸be mappe: {e}"}), 400

    try:
        db_stats = _apply_upload_folder_rename_db(old_subdir, new_subdir)
    except Exception as e:
        for src, dst in reversed(moved):
            try:
                if dst.exists() and not src.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    dst.rename(src)
            except Exception:
                pass
        return jsonify({"ok": False, "error": f"Kunne ikke opdatere database: {e}"}), 500

    # Remove now-empty old parent directories where safe
    for src, _dst in moved:
        cur = src.parent
        while True:
            try:
                cur_res = cur.resolve()
            except Exception:
                break
            if cur_res in protected_roots:
                break
            try:
                cur.rmdir()
            except Exception:
                break
            cur = cur.parent

    payload = _upload_settings_payload(destination)
    payload["old_path"] = old_subdir
    payload["new_path"] = new_subdir
    payload["photos_renamed"] = int(db_stats.get("photos_renamed", 0))
    payload["photos_conflicts_removed"] = int(db_stats.get("photos_conflicts_removed", 0))
    return jsonify(payload)


@app.route("/api/settings/dns", methods=["GET", "POST"])
def api_settings_dns():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        raw = str(body.get("duckdns_base_url") or "").strip()
        if raw:
            normalized = _normalize_share_base_url(raw)
            if not normalized:
                return jsonify({"ok": False, "error": "Ugyldig URL. Brug fx https://photos.eksempel.dk"}), 400
            _set_setting("share_duckdns_base_url", normalized)
        else:
            _set_setting("share_duckdns_base_url", "")

    saved = str(_get_setting("share_duckdns_base_url", "") or "").strip()
    env_default = str(SHARE_DUCKDNS_BASE_URL or "").strip()
    effective = saved or env_default
    return jsonify(
        {
            "ok": True,
            "duckdns_base_url": saved,
            "effective_duckdns_base_url": effective,
            "using_env_default": bool(env_default and not saved),
        }
    )


@app.route("/api/settings/dns/effective", methods=["GET"])
def api_settings_dns_effective():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    saved = str(_get_setting("share_duckdns_base_url", "") or "").strip()
    env_default = str(SHARE_DUCKDNS_BASE_URL or "").strip()
    effective = saved or env_default
    normalized = _normalize_share_base_url(effective)
    return jsonify(
        {
            "ok": True,
            "effective_duckdns_base_url": normalized or "",
            "duckdns_configured": bool(normalized),
            "using_env_default": bool(env_default and not saved and normalized),
        }
    )


@app.route("/api/settings/heic", methods=["GET", "POST"])
def api_settings_heic():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        conv = body.get("convert_on_upload")
        keep = body.get("keep_originals")
        if conv is not None:
            _set_setting("heic_convert_on_upload", "1" if bool(conv) else "0")
        if keep is not None:
            _set_setting("heic_keep_originals", "1" if bool(keep) else "0")

    return jsonify(
        {
            "ok": True,
            "convert_on_upload": heic_convert_on_upload_enabled(),
            "keep_originals": heic_keep_originals_enabled(),
            "env_default_convert": HEIC_CONVERT_ON_UPLOAD_DEFAULT,
        }
    )


@app.route("/api/settings/raw", methods=["GET", "POST"])
def api_settings_raw():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        conv = body.get("convert_on_upload")
        keep = body.get("keep_originals")
        if conv is not None:
            _set_setting("raw_convert_on_upload", "1" if bool(conv) else "0")
        if keep is not None:
            _set_setting("raw_keep_originals", "1" if bool(keep) else "0")

    return jsonify(
        {
            "ok": True,
            "convert_on_upload": raw_convert_on_upload_enabled(),
            "keep_originals": raw_keep_originals_enabled(),
            "env_default_convert": RAW_CONVERT_ON_UPLOAD_DEFAULT,
        }
    )


@app.route("/api/settings/mov", methods=["GET", "POST"])
def api_settings_mov():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        conv = body.get("convert_on_upload")
        keep = body.get("keep_originals")
        if conv is not None:
            _set_setting("mov_convert_on_upload", "1" if bool(conv) else "0")
        if keep is not None:
            _set_setting("mov_keep_originals", "1" if bool(keep) else "0")

    return jsonify(
        {
            "ok": True,
            "convert_on_upload": mov_convert_on_upload_enabled(),
            "keep_originals": mov_keep_originals_enabled(),
            "env_default_convert": MOV_CONVERT_ON_UPLOAD_DEFAULT,
        }
    )


def _normalize_rel_for_conversion(value: Any) -> str:
    try:
        return str(value or "").replace("\\", "/").lstrip("/").strip()
    except Exception:
        return ""


def _normalize_ext_for_conversion(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        raw_norm = raw.replace("\\", "/")
    except Exception:
        raw_norm = raw
    leaf = raw_norm.split("/")[-1]
    ext = Path(leaf).suffix.lower()
    if not ext:
        compact = re.sub(r"[^a-zA-Z0-9.]", "", raw_norm).lower()
        if compact:
            ext = compact if compact.startswith(".") else f".{compact}"
    if ext == ".":
        return ""
    return ext


def _attach_conversion_metadata(
    meta: Dict[str, Any],
    *,
    from_rel_path: str,
    to_rel_path: str,
    from_ext: Optional[str] = None,
    to_ext: Optional[str] = None,
) -> None:
    if not isinstance(meta, dict):
        return

    from_rel = _normalize_rel_for_conversion(from_rel_path)
    to_rel = _normalize_rel_for_conversion(to_rel_path)
    from_ext_norm = _normalize_ext_for_conversion(from_ext or from_rel)
    to_ext_norm = _normalize_ext_for_conversion(to_ext or meta.get("ext") or to_rel)

    mj_raw = meta.get("metadata_json")
    mj: Dict[str, Any] = dict(mj_raw) if isinstance(mj_raw, dict) else {}
    conv_raw = mj.get("conversion")
    conv: Dict[str, Any] = dict(conv_raw) if isinstance(conv_raw, dict) else {}

    if from_rel:
        conv["from_rel_path"] = from_rel
        mj["converted_from_rel"] = from_rel
    if to_rel:
        conv["to_rel_path"] = to_rel
    if from_ext_norm:
        conv["from_ext"] = from_ext_norm
        mj["converted_from_ext"] = from_ext_norm
    if to_ext_norm:
        conv["to_ext"] = to_ext_norm
        mj["converted_to_ext"] = to_ext_norm

    conv["converted"] = True
    conv["converted_at"] = now_iso()
    mj["conversion"] = conv
    meta["metadata_json"] = mj


def _convert_existing_heic(stop_event=None) -> Dict[str, Any]:
    init_db()
    log_event("heic_bulk_start")
    processed = 0
    errors = 0
    # HEIC/HEIF only in this function
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT rel_path, uploaded_by FROM photos WHERE LOWER(rel_path) LIKE '%.heic' OR LOWER(rel_path) LIKE '%.heif'").fetchall()
    # initialize global progress snapshot
    try:
        global heic_convert_progress
        heic_convert_progress = {"total": len(rows), "processed": 0, "errors": 0}
    except Exception:
        pass
    for r in rows:
        if stop_event and stop_event.is_set():
            break
        try:
            orig_rel = r["rel_path"]
            src = _disk_path_from_rel_path(orig_rel)
            if not src.exists():
                continue

            new_rel = str(Path(orig_rel).with_suffix(".jpg")).replace("\\", "/")
            dst: Path

            if orig_rel.startswith("uploads/"):
                try:
                    if orig_rel.startswith("uploads/originals/"):
                        parts = orig_rel.split("/", 2)
                        sub_rel = parts[2] if len(parts) >= 3 else Path(orig_rel).name
                    else:
                        parts = orig_rel.split("/", 1)
                        sub_rel = parts[1] if len(parts) >= 2 else Path(orig_rel).name
                except Exception:
                    sub_rel = Path(orig_rel).name

                subdir_only = str(Path(sub_rel).parent).replace("\\", "/").strip("./")
                leaf_jpg = f"{Path(sub_rel).stem}.jpg"
                conv_dir = UPLOAD_DIR / "converted" / (subdir_only if subdir_only not in {"", "."} else "")
                conv_dir.mkdir(parents=True, exist_ok=True)
                dst = conv_dir / leaf_jpg
                if dst.exists():
                    i = 1
                    stem = Path(leaf_jpg).stem
                    while True:
                        cand = conv_dir / f"{stem}_{i}.jpg"
                        if not cand.exists():
                            dst = cand
                            break
                        i += 1
                tail = (
                    Path(sub_rel).with_suffix(".jpg").name
                    if subdir_only in {"", "."}
                    else (Path(subdir_only) / Path(sub_rel).with_suffix(".jpg").name).as_posix()
                )
                new_rel = f"uploads/converted/{tail}"
            else:
                dst = src.with_suffix(".jpg")
                dst.parent.mkdir(parents=True, exist_ok=True)

            extl = src.suffix.lower()
            if extl in {".heic", ".heif"}:
                with Image.open(src) as himg:
                    try:
                        himg = ImageOps.exif_transpose(himg)
                    except Exception:
                        pass
                    rgb = himg.convert("RGB")
                    exif_bytes = None
                    try:
                        exif_bytes = himg.info.get("exif") or himg.getexif().tobytes()
                    except Exception:
                        exif_bytes = None
                    save_kwargs = {"format": "JPEG", "quality": 92, "optimize": True}
                    if exif_bytes:
                        save_kwargs["exif"] = exif_bytes
                    rgb.save(dst, **save_kwargs)
            else:
                # Skip non-HEIC in this function
                continue

            try:
                st = src.stat()
                os.utime(dst, (st.st_atime, st.st_mtime))
            except Exception:
                pass

            meta = extract_metadata(dst, new_rel, generate_thumb=True)
            _attach_conversion_metadata(
                meta,
                from_rel_path=orig_rel,
                to_rel_path=new_rel,
                from_ext=extl,
                to_ext=str(dst.suffix or "").lower() or meta.get("ext"),
            )
            try:
                # Preserve original uploader if known
                up_by = r.get("uploaded_by") if isinstance(r, dict) else (r["uploaded_by"] if "uploaded_by" in r.keys() else None)
            except Exception:
                up_by = None
            if up_by:
                meta["uploaded_by"] = str(up_by)
            upsert_photo(meta)
            try:
                with closing(get_conn()) as conn2:
                    conn2.execute("DELETE FROM photos WHERE rel_path=?", (orig_rel,))
                    conn2.commit()
            except Exception:
                pass
            try:
                if not heic_keep_originals_enabled():
                    src.unlink(missing_ok=True)
            except Exception:
                pass
            processed += 1
            log_event("heic_converted", rel_path=new_rel)
        except Exception as e:
            errors += 1
            log_event("error", rel_path=str(r["rel_path"]), error=f"heic_bulk: {e}")
        # Update progress after each item
        try:
            heic_convert_progress = {"total": len(rows), "processed": processed, "errors": errors}
        except Exception:
            pass
    res = {"ok": True, "processed": processed, "errors": errors}
    log_event("heic_bulk_done", **res)
    # final snapshot stays available in status until next run
    try:
        heic_convert_progress = {"total": len(rows), "processed": processed, "errors": errors}
    except Exception:
        pass
    return res


@app.route("/api/heic/convert-existing", methods=["POST"])
def api_heic_convert_existing():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global heic_convert_thread, last_heic_convert_result, heic_convert_progress
    if heic_convert_thread and heic_convert_thread.is_alive():
        return jsonify({"ok": False, "error": "HEIC-konvertering kÃ¸rer allerede"}), 409
    scan_stop_event.clear()
    last_heic_convert_result = None
    try:
        heic_convert_progress = {"total": 0, "processed": 0, "errors": 0}
    except Exception:
        pass

    def run_bulk():
        global last_heic_convert_result
        last_heic_convert_result = _convert_existing_heic(stop_event=scan_stop_event)

    heic_convert_thread = threading.Thread(target=run_bulk, daemon=True)
    heic_convert_thread.start()
    return jsonify({"ok": True, "started": True})


@app.route("/api/heic/convert-existing/status")
def api_heic_convert_existing_status():
    running = bool(heic_convert_thread and heic_convert_thread.is_alive())
    return jsonify({
        "ok": True,
        "running": running,
        "result": (last_heic_convert_result if not running else None),
        "progress": (heic_convert_progress if running else None),
    })


# --- RAW bulk conversion (DNG/RAW) ---
raw_convert_thread: Optional[threading.Thread] = None
last_raw_convert_result: Optional[Dict[str, Any]] = None
raw_convert_progress: Optional[Dict[str, Any]] = None


def _convert_existing_raw(stop_event=None) -> Dict[str, Any]:
    init_db()
    log_event("raw_bulk_start")
    processed = 0
    errors = 0
    patterns = [f"%{ext.lower()}" for ext in RAW_EXTS]
    where = " OR ".join(["LOWER(rel_path) LIKE ?" for _ in patterns])
    with closing(get_conn()) as conn:
        rows = conn.execute(f"SELECT rel_path, uploaded_by FROM photos WHERE {where}", tuple(patterns)).fetchall()
    global raw_convert_progress
    try:
        raw_convert_progress = {"total": len(rows), "processed": 0, "errors": 0}
    except Exception:
        pass
    for r in rows:
        if stop_event and stop_event.is_set():
            break
        try:
            orig_rel = r["rel_path"]
            src = _disk_path_from_rel_path(orig_rel)
            if not src.exists():
                continue
            # Determine destination under uploads/converted/ mirroring path
            if orig_rel.startswith("uploads/"):
                try:
                    if orig_rel.startswith("uploads/originals/"):
                        parts = orig_rel.split("/", 2)
                        sub_rel = parts[2] if len(parts) >= 3 else Path(orig_rel).name
                    else:
                        parts = orig_rel.split("/", 1)
                        sub_rel = parts[1] if len(parts) >= 2 else Path(orig_rel).name
                except Exception:
                    sub_rel = Path(orig_rel).name
                subdir_only = str(Path(sub_rel).parent).replace("\\", "/").strip("./")
                leaf_jpg = f"{Path(sub_rel).stem}.jpg"
                conv_dir = UPLOAD_DIR / "converted" / (subdir_only if subdir_only not in {"", "."} else "")
                conv_dir.mkdir(parents=True, exist_ok=True)
                dst = conv_dir / leaf_jpg
                if dst.exists():
                    i = 1
                    stem = Path(leaf_jpg).stem
                    while True:
                        cand = conv_dir / f"{stem}_{i}.jpg"
                        if not cand.exists():
                            dst = cand
                            break
                        i += 1
                tail = (
                    Path(sub_rel).with_suffix(".jpg").name
                    if subdir_only in {"", "."}
                    else (Path(subdir_only) / Path(sub_rel).with_suffix(".jpg").name).as_posix()
                )
                new_rel = f"uploads/converted/{tail}"
            else:
                dst = src.with_suffix(".jpg")
                dst.parent.mkdir(parents=True, exist_ok=True)
                new_rel = str(Path(orig_rel).with_suffix(".jpg")).replace("\\", "/")

            # RAW â†’ JPEG
            if rawpy is None:
                raise RuntimeError("RAW conversion requires rawpy")
            with rawpy.imread(str(src)) as raw:  # type: ignore
                rgb = raw.postprocess(
                    use_auto_wb=True,
                    no_auto_bright=True,
                    output_color=rawpy.ColorSpace.sRGB,  # type: ignore
                    output_bps=8,
                    gamma=None,
                    half_size=True,
                )
            Image.fromarray(rgb).save(dst, format="JPEG", quality=92, optimize=True)
            try:
                st = src.stat()
                os.utime(dst, (st.st_atime, st.st_mtime))
            except Exception:
                pass
            meta = extract_metadata(dst, new_rel, generate_thumb=True)
            _attach_conversion_metadata(
                meta,
                from_rel_path=orig_rel,
                to_rel_path=new_rel,
                from_ext=src.suffix.lower(),
                to_ext=str(dst.suffix or "").lower() or meta.get("ext"),
            )
            try:
                up_by = r.get("uploaded_by") if isinstance(r, dict) else (r["uploaded_by"] if "uploaded_by" in r.keys() else None)
            except Exception:
                up_by = None
            if up_by:
                meta["uploaded_by"] = str(up_by)
            upsert_photo(meta)
            try:
                with closing(get_conn()) as conn2:
                    conn2.execute("DELETE FROM photos WHERE rel_path=?", (orig_rel,))
                    conn2.commit()
            except Exception:
                pass
            try:
                if not raw_keep_originals_enabled():
                    src.unlink(missing_ok=True)
            except Exception:
                pass
            processed += 1
            log_event("raw_converted", rel_path=new_rel)
        except Exception as e:
            errors += 1
            log_event("error", rel_path=str(r["rel_path"]), error=f"raw_bulk: {e}")
        try:
            raw_convert_progress = {"total": len(rows), "processed": processed, "errors": errors}
        except Exception:
            pass
    res = {"ok": True, "processed": processed, "errors": errors}
    log_event("raw_bulk_done", **res)
    try:
        raw_convert_progress = {"total": len(rows), "processed": processed, "errors": errors}
    except Exception:
        pass
    return res


@app.route("/api/raw/convert-existing", methods=["POST"])
def api_raw_convert_existing():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global raw_convert_thread, last_raw_convert_result, raw_convert_progress
    if raw_convert_thread and raw_convert_thread.is_alive():
        return jsonify({"ok": False, "error": "RAW-konvertering kÃ¸rer allerede"}), 409
    scan_stop_event.clear()
    last_raw_convert_result = None
    try:
        raw_convert_progress = {"total": 0, "processed": 0, "errors": 0}
    except Exception:
        pass

    def run_bulk():
        global last_raw_convert_result
        last_raw_convert_result = _convert_existing_raw(stop_event=scan_stop_event)

    raw_convert_thread = threading.Thread(target=run_bulk, daemon=True)
    raw_convert_thread.start()
    return jsonify({"ok": True, "started": True})


@app.route("/api/raw/convert-existing/status")
def api_raw_convert_existing_status():
    running = bool(raw_convert_thread and raw_convert_thread.is_alive())
    return jsonify({
        "ok": True,
        "running": running,
        "result": (last_raw_convert_result if not running else None),
        "progress": (raw_convert_progress if running else None),
    })


def _convert_existing_mov(stop_event=None) -> Dict[str, Any]:
    init_db()
    log_event("mov_bulk_start")
    processed = 0
    errors = 0
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT rel_path, uploaded_by FROM photos WHERE LOWER(rel_path) LIKE '%.mov'").fetchall()
    global mov_convert_progress
    try:
        mov_convert_progress = {"total": len(rows), "processed": 0, "errors": 0}
    except Exception:
        pass
    for r in rows:
        if stop_event and stop_event.is_set():
            break
        try:
            orig_rel = r["rel_path"]
            src = _disk_path_from_rel_path(orig_rel)
            if not src.exists():
                continue

            if orig_rel.startswith("uploads/"):
                try:
                    if orig_rel.startswith("uploads/originals/"):
                        parts = orig_rel.split("/", 2)
                        sub_rel = parts[2] if len(parts) >= 3 else Path(orig_rel).name
                    else:
                        parts = orig_rel.split("/", 1)
                        sub_rel = parts[1] if len(parts) >= 2 else Path(orig_rel).name
                except Exception:
                    sub_rel = Path(orig_rel).name
                subdir_only = str(Path(sub_rel).parent).replace("\\", "/").strip("./")
                leaf_mp4 = f"{Path(sub_rel).stem}.mp4"
                conv_dir = UPLOAD_DIR / "converted" / (subdir_only if subdir_only not in {"", "."} else "")
                conv_dir.mkdir(parents=True, exist_ok=True)
                dst = conv_dir / leaf_mp4
                if dst.exists():
                    i = 1
                    stem = Path(leaf_mp4).stem
                    while True:
                        cand = conv_dir / f"{stem}_{i}.mp4"
                        if not cand.exists():
                            dst = cand
                            break
                        i += 1
                tail = dst.name if subdir_only in {"", "."} else (Path(subdir_only) / dst.name).as_posix()
                new_rel = f"uploads/converted/{tail}"
            else:
                dst = src.with_suffix(".mp4")
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    i = 1
                    stem = dst.stem
                    while True:
                        cand = dst.parent / f"{stem}_{i}.mp4"
                        if not cand.exists():
                            dst = cand
                            break
                        i += 1
                new_rel = str(Path(orig_rel).with_name(dst.name)).replace("\\", "/")

            _mov_to_mp4(src, dst)
            try:
                st = src.stat()
                os.utime(dst, (st.st_atime, st.st_mtime))
            except Exception:
                pass

            meta = extract_metadata(dst, new_rel, generate_thumb=True)
            _attach_conversion_metadata(
                meta,
                from_rel_path=orig_rel,
                to_rel_path=new_rel,
                from_ext=src.suffix.lower(),
                to_ext=str(dst.suffix or "").lower() or meta.get("ext"),
            )
            try:
                up_by = r.get("uploaded_by") if isinstance(r, dict) else (r["uploaded_by"] if "uploaded_by" in r.keys() else None)
            except Exception:
                up_by = None
            if up_by:
                meta["uploaded_by"] = str(up_by)
            upsert_photo(meta)
            try:
                with closing(get_conn()) as conn2:
                    conn2.execute("DELETE FROM photos WHERE rel_path=?", (orig_rel,))
                    conn2.commit()
            except Exception:
                pass
            try:
                if not mov_keep_originals_enabled():
                    src.unlink(missing_ok=True)
            except Exception:
                pass
            processed += 1
            log_event("mov_converted", rel_path=new_rel)
        except Exception as e:
            errors += 1
            log_event("error", rel_path=str(r["rel_path"]), error=f"mov_bulk: {e}")
        try:
            mov_convert_progress = {"total": len(rows), "processed": processed, "errors": errors}
        except Exception:
            pass
    res = {"ok": True, "processed": processed, "errors": errors}
    log_event("mov_bulk_done", **res)
    try:
        mov_convert_progress = {"total": len(rows), "processed": processed, "errors": errors}
    except Exception:
        pass
    return res


@app.route("/api/mov/convert-existing", methods=["POST"])
def api_mov_convert_existing():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global mov_convert_thread, last_mov_convert_result, mov_convert_progress
    if mov_convert_thread and mov_convert_thread.is_alive():
        return jsonify({"ok": False, "error": "MOV-konvertering kører allerede"}), 409
    scan_stop_event.clear()
    last_mov_convert_result = None
    try:
        mov_convert_progress = {"total": 0, "processed": 0, "errors": 0}
    except Exception:
        pass

    def run_bulk():
        global last_mov_convert_result
        last_mov_convert_result = _convert_existing_mov(stop_event=scan_stop_event)

    mov_convert_thread = threading.Thread(target=run_bulk, daemon=True)
    mov_convert_thread.start()
    return jsonify({"ok": True, "started": True})


@app.route("/api/mov/convert-existing/status")
def api_mov_convert_existing_status():
    running = bool(mov_convert_thread and mov_convert_thread.is_alive())
    return jsonify({
        "ok": True,
        "running": running,
        "result": (last_mov_convert_result if not running else None),
        "progress": (mov_convert_progress if running else None),
    })


@app.route("/api/settings/ai-performance", methods=["GET", "POST"])
def api_settings_ai_performance():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        ai_throttle = _parse_throttle_value(body.get("ai_ingest_throttle_sec"), AI_INGEST_THROTTLE_SEC)
        faces_throttle = _parse_throttle_value(body.get("faces_index_throttle_sec"), FACES_INDEX_THROTTLE_SEC)
        _set_setting("ai_ingest_throttle_sec", str(ai_throttle))
        _set_setting("faces_index_throttle_sec", str(faces_throttle))

    return jsonify(
        {
            "ok": True,
            "ai_ingest_throttle_sec": ai_ingest_throttle_enabled_sec(),
            "faces_index_throttle_sec": faces_index_throttle_enabled_sec(),
            "runtime_applies_without_restart": True,
        }
    )


@app.route("/api/settings/upload-workflow", methods=["GET", "POST"])
def api_settings_upload_workflow():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        mode = _normalize_upload_workflow_mode(body.get("mode"))
        _set_setting("upload_workflow_mode", mode)

    return jsonify(_upload_workflow_settings_payload())


@app.route("/api/settings/upload-file-types", methods=["GET", "POST"])
def api_settings_upload_file_types():
    if request.method == "POST":
        fb = _forbid_user_role_for_maintenance()
        if fb:
            return jsonify(fb[0]), fb[1]
        body = request.get_json(silent=True) or {}
        if bool(body.get("reset")):
            allowed = _default_upload_allowed_extensions()
        else:
            raw_values = body.get("allowed_extensions", body.get("extensions", None))
            if raw_values is None:
                return jsonify({"ok": False, "error": "Manglende filtype-liste"}), 400
            allowed, invalid, _unsupported = _normalize_upload_extension_list(raw_values)
            if invalid:
                return jsonify({"ok": False, "error": "Ugyldige filtyper: " + ", ".join(invalid[:12])}), 400
            if not allowed:
                return jsonify({"ok": False, "error": "Whitelist må ikke være tom"}), 400
        _set_setting(UPLOAD_ALLOWED_EXTENSIONS_SETTING, json.dumps(sorted(allowed)))
    return jsonify(_upload_file_types_settings_payload())


# --- Upload endpoint (drag & drop) ---
@app.route("/api/upload/transfer-state", methods=["POST"])
@login_required
def api_upload_transfer_state():
    data = request.get_json(silent=True) or {}
    active = bool(data.get("active"))
    uploaded_by = str(getattr(current_user, "username", "") or "")
    _set_upload_transfer_active(uploaded_by, active)
    return jsonify({"ok": True, "active": _is_upload_transfer_active(uploaded_by)})


@app.route("/api/upload/tus", methods=["OPTIONS"])
@app.route("/api/upload/tus/<upload_id>", methods=["OPTIONS"])
@login_required
def api_upload_tus_options(upload_id: Optional[str] = None):
    resp = make_response("", 204)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS, POST, HEAD, PATCH"
    resp.headers["Access-Control-Allow-Headers"] = "Tus-Resumable, Upload-Length, Upload-Offset, Upload-Metadata, Content-Type, X-HTTP-Method-Override"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/upload/tus", methods=["POST"])
@login_required
def api_upload_tus_create():
    fb = _tus_require_version()
    if fb:
        return jsonify(fb[0]), fb[1], _tus_headers()

    try:
        TUS_TMP_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Will fail later when writing if path is unusable
        pass
    try:
        upload_length = int(str(request.headers.get("Upload-Length") or "0").strip())
    except Exception:
        upload_length = -1
    if upload_length < 0:
        return jsonify({"ok": False, "error": "Invalid Upload-Length"}), 400, _tus_headers()

    meta = _parse_tus_metadata(str(request.headers.get("Upload-Metadata") or ""))
    filename = str(meta.get("filename") or "").strip()
    if not filename:
        return jsonify({"ok": False, "error": "Missing filename"}), 400, _tus_headers()
    filename_ext = Path(secure_filename(filename) or filename).suffix.lower()
    if not _is_upload_extension_allowed(filename_ext):
        try:
            log_event("upload_skip_blocked_file_type", filename=filename, ext=filename_ext)
        except Exception:
            pass
        return jsonify({
            "ok": False,
            "error": _blocked_upload_file_error(filename, filename_ext),
            "blocked_extension": filename_ext,
        }), 415, _tus_headers()

    destination = get_upload_destination()
    destination_override = str(meta.get("destination") or "").strip().lower()
    if destination_override:
        if destination_override not in UPLOAD_DEST_CHOICES:
            return jsonify({"ok": False, "error": "Ugyldig upload-destination"}), 400, _tus_headers()
        destination = destination_override

    subdir = get_upload_subdir(destination)
    subdir_override_raw = meta.get("subdir")
    if subdir_override_raw is not None:
        try:
            subdir = _normalize_upload_subdir(str(subdir_override_raw or ""))
        except Exception:
            return jsonify({"ok": False, "error": "Ugyldig upload-undermappe"}), 400, _tus_headers()

    target_root, rel_prefix = _upload_target_for_destination(destination)
    subdir = _ensure_default_upload_subdir(destination, target_root, subdir)
    target_dir = (target_root / subdir) if subdir else target_root
    # Enforce per-folder upload permission when uploading to user folders
    if destination == UPLOAD_DEST_UPLOADS:
        base_rel = f"uploads/{subdir}" if subdir else "uploads"
        perm = _current_user_folder_permission_for_rel(base_rel)
        if not _perm_allows(perm, "upload"):
            return jsonify({"ok": False, "error": "Ingen upload-adgang til denne mappe"}), 403, _tus_headers()
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Kan ikke oprette upload-destination: {e}"}), 500, _tus_headers()

    upload_id = secrets.token_urlsafe(18)
    data_path, _ = _tus_upload_paths(upload_id)
    try:
        with data_path.open("wb"):
            pass
    except Exception as e:
        return jsonify({"ok": False, "error": f"Unable to create upload: {e}"}), 500, _tus_headers()

    try:
        last_modified_ms = int(str(meta.get("lastModified") or "0").strip() or "0")
    except Exception:
        last_modified_ms = 0

    upload_meta: Dict[str, Any] = {
        "id": upload_id,
        "filename": filename,
        "destination": destination,
        "subdir": subdir,
        "upload_length": upload_length,
        "upload_offset": 0,
        "target_dir": str(target_dir),
        "rel_prefix": rel_prefix,
        "last_modified_ms": last_modified_ms,
        "uploaded_by": str(getattr(current_user, "username", "") or ""),
        "created_at": now_iso(),
    }
    _tus_store_meta(upload_id, upload_meta)

    try:
        log_event("upload_tus_created", upload_id=upload_id, filename=filename, destination=destination, subdir=subdir, upload_length=upload_length)
    except Exception:
        pass

    resp = make_response("", 201)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Location"] = url_for("api_upload_tus_file", upload_id=upload_id)
    resp.headers["Upload-Offset"] = "0"
    return resp


@app.route("/api/upload/tus/<upload_id>", methods=["HEAD"])
@login_required
def api_upload_tus_head(upload_id: str):
    fb = _tus_require_version()
    if fb:
        return jsonify(fb[0]), fb[1], _tus_headers()

    meta = _tus_load_meta(upload_id)
    if not meta:
        return jsonify({"ok": False, "error": "Upload not found"}), 404, _tus_headers()

    data_path, _ = _tus_upload_paths(upload_id)
    offset = int(meta.get("upload_offset") or 0)
    try:
        if data_path.exists():
            offset = int(data_path.stat().st_size)
    except Exception:
        pass

    resp = make_response("", 204)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Upload-Offset"] = str(max(0, offset))
    resp.headers["Upload-Length"] = str(int(meta.get("upload_length") or 0))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/upload/tus/<upload_id>", methods=["PATCH"])
@login_required
def api_upload_tus_file(upload_id: str):
    fb = _tus_require_version()
    if fb:
        return jsonify(fb[0]), fb[1], _tus_headers()
    if str(request.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower() != "application/offset+octet-stream":
        return jsonify({"ok": False, "error": "Invalid Content-Type"}), 415, _tus_headers()

    meta = _tus_load_meta(upload_id)
    if not meta:
        return jsonify({"ok": False, "error": "Upload not found"}), 404, _tus_headers()

    data_path, meta_path = _tus_upload_paths(upload_id)
    if not data_path.exists():
        return jsonify({"ok": False, "error": "Upload data missing"}), 410, _tus_headers()

    try:
        req_offset = int(str(request.headers.get("Upload-Offset") or "0").strip())
    except Exception:
        return jsonify({"ok": False, "error": "Invalid Upload-Offset"}), 400, _tus_headers()

    current_size = int(data_path.stat().st_size)
    if req_offset != current_size:
        resp = make_response("", 409)
        for k, v in _tus_headers().items():
            resp.headers[k] = v
        resp.headers["Upload-Offset"] = str(current_size)
        return resp

    body = request.get_data(cache=False, as_text=False) or b""
    try:
        with data_path.open("ab") as fh:
            if body:
                fh.write(body)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Unable to write upload chunk: {e}"}), 500, _tus_headers()

    new_offset = int(data_path.stat().st_size)
    total_length = int(meta.get("upload_length") or 0)
    meta["upload_offset"] = new_offset
    _tus_store_meta(upload_id, meta)

    if total_length > 0 and new_offset >= total_length:
        target_dir = Path(str(meta.get("target_dir") or ""))
        rel_prefix = str(meta.get("rel_prefix") or "")
        subdir = str(meta.get("subdir") or "")
        filename = str(meta.get("filename") or "")
        uploaded_by = str(meta.get("uploaded_by") or "")
        try:
            last_modified_ms = int(meta.get("last_modified_ms") or 0)
        except Exception:
            last_modified_ms = 0

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            ok, saved_name, err = _commit_uploaded_file(
                target_dir=target_dir,
                rel_prefix=rel_prefix,
                subdir=subdir,
                source_path=data_path,
                original_name=filename,
                last_modified_ms=last_modified_ms,
                uploaded_by=uploaded_by,
                autostart_postprocess=False,
            )
            try:
                meta_path.unlink(missing_ok=True)
            except Exception:
                pass
            if ok:
                try:
                    log_event("upload_done", saved=1, errors=0)
                except Exception:
                    pass
            else:
                try:
                    log_event("error", filename=filename, error=err)
                except Exception:
                    pass
                return jsonify({"ok": False, "error": err or "Upload finalize failed"}), 500, _tus_headers({"Upload-Offset": str(new_offset)})
        except Exception as e:
            return jsonify({"ok": False, "error": f"Upload finalize failed: {e}"}), 500, _tus_headers({"Upload-Offset": str(new_offset)})

    resp = make_response("", 204)
    for k, v in _tus_headers().items():
        resp.headers[k] = v
    resp.headers["Upload-Offset"] = str(new_offset)
    resp.headers["Cache-Control"] = "no-store"
    return resp

# Allow proxies that block PATCH to use POST + X-HTTP-Method-Override: PATCH
@app.route("/api/upload/tus/<upload_id>", methods=["POST"])
@login_required
def api_upload_tus_file_override(upload_id: str):
    method_override = str(request.headers.get("X-HTTP-Method-Override") or "").strip().upper()
    if method_override == "PATCH":
        return api_upload_tus_file(upload_id)
    return jsonify({"ok": False, "error": "Unsupported method"}), 405, _tus_headers()


@app.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    if not current_user.is_authenticated:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    # Direct uploads: create only the specific target directory when needed
    destination = get_upload_destination()
    destination_override = str(request.form.get("destination") or "").strip().lower()
    if destination_override:
        if destination_override not in UPLOAD_DEST_CHOICES:
            return jsonify({"ok": False, "error": "Ugyldig upload-destination"}), 400
        destination = destination_override

    subdir = get_upload_subdir(destination)
    subdir_override_raw = request.form.get("subdir")
    if subdir_override_raw is not None:
        try:
            subdir = _normalize_upload_subdir(str(subdir_override_raw or ""))
        except Exception:
            return jsonify({"ok": False, "error": "Ugyldig upload-undermappe"}), 400

    target_root, rel_prefix = _upload_target_for_destination(destination)
    subdir = _ensure_default_upload_subdir(destination, target_root, subdir)
    target_dir = (target_root / subdir) if subdir else target_root
    # Enforce per-folder upload permission when uploading to user folders
    if destination == UPLOAD_DEST_UPLOADS:
        base_rel = f"uploads/{subdir}" if subdir else "uploads"
        perm = _current_user_folder_permission_for_rel(base_rel)
        if not _perm_allows(perm, "upload"):
            return jsonify({"ok": False, "error": "Ingen upload-adgang til denne mappe"}), 403
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Kan ikke oprette upload-destination: {e}"}), 500
    files = request.files.getlist("files") or []
    try:
        log_event("upload_start", count=len(files), destination=destination, subdir=subdir)
    except Exception:
        pass
    if not files:
        return jsonify({"ok": False, "error": "No files"}), 400
    saved = []
    errors: list[str] = []
    # Optional client-side metadata (array of {name,lastModified})
    client_meta = {}
    try:
        meta_raw = request.form.get("meta")
        if meta_raw:
            for entry in json.loads(meta_raw):
                n = str(entry.get("name"))
                lm = int(entry.get("lastModified")) if entry.get("lastModified") is not None else None
                if n and lm:
                    client_meta[n] = lm
    except Exception:
        client_meta = {}
    allowed_upload_exts = upload_allowed_extensions()
    uploaded_by = str(getattr(current_user, "username", "") or "")
    for f in files:
        tmp_path: Optional[Path] = None
        try:
            name = secure_filename(f.filename or "")
            if not name:
                continue
            ext = Path(name).suffix.lower()
            if not _is_upload_extension_allowed(ext, allowed_upload_exts):
                errors.append(_blocked_upload_file_error(name, ext))
                try: log_event("upload_skip_blocked_file_type", filename=name, ext=ext)
                except Exception: pass
                continue
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = Path(tmp.name)
            f.save(str(tmp_path))
            lm_ms = client_meta.get(f.filename) or client_meta.get(name)
            ok, saved_name, err = _commit_uploaded_file(
                target_dir=target_dir,
                rel_prefix=rel_prefix,
                subdir=subdir,
                source_path=tmp_path,
                original_name=name,
                last_modified_ms=lm_ms,
                uploaded_by=uploaded_by,
                autostart_postprocess=False,
            )
            if ok:
                saved.append(saved_name)
                try: log_event("upload_saved", filename=name, saved_name=saved_name, path=str(target_dir / saved_name))
                except Exception: pass
            else:
                errors.append(err or f"Commit failed: {name}")
                try:
                    if tmp_path and tmp_path.exists():
                        tmp_path.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception as e:
            errors.append(str(e))
            try: log_event("error", filename=(f.filename if f else None), error=str(e))
            except Exception: pass
            try:
                if tmp_path and tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
    try:
        log_event("upload_done", saved=len(saved), errors=len(errors))
    except Exception:
        pass
    return jsonify({"ok": bool(saved) or not errors, "saved": saved, "errors": errors})


@app.route("/api/upload/postprocess", methods=["POST"])
@login_required
def api_upload_postprocess():
    uploaded_by = str(getattr(current_user, "username", "") or "")
    workflow_mode = upload_workflow_mode()
    if _is_upload_transfer_active(uploaded_by):
        with UPLOAD_PENDING_LOCK:
            pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
        return jsonify({
            "ok": False,
            "error": "Upload er stadig i gang",
            "uploading": True,
            "started": False,
            "running": False,
            "pending": pending_count,
            "workflow_mode": workflow_mode,
        }), 409
    rels = _pop_uploaded_rels(uploaded_by)

    if _is_upload_postprocess_running(uploaded_by):
        for rel in rels:
            _queue_uploaded_rel(uploaded_by, rel)
        running_state = _get_upload_postprocess_state(uploaded_by)
        running_mode = running_state.get("workflow_mode") if isinstance(running_state, dict) else None
        with UPLOAD_PENDING_LOCK:
            pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
        return jsonify({"ok": True, "started": False, "running": True, "pending": pending_count, "workflow_mode": running_mode or workflow_mode, "process_status": (running_state.get("process_status") if isinstance(running_state, dict) else None)})

    if not rels:
        rels = _recover_uploaded_rels_missing_postprocess(uploaded_by)

    if not rels:
        state = _get_upload_postprocess_state(uploaded_by)
        if state:
            with UPLOAD_PENDING_LOCK:
                pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
            recoverable_count = 0 if bool(state.get("running")) else len(_recover_uploaded_rels_missing_postprocess(uploaded_by, limit=5000))
            return jsonify({"ok": True, "started": False, "running": bool(state.get("running")), "pending": pending_count, "recoverable_pending": recoverable_count, "workflow_mode": state.get("workflow_mode") or workflow_mode, "process_status": state.get("process_status"), "result": state.get("result"), "error": state.get("error")})
        recoverable_count = len(_recover_uploaded_rels_missing_postprocess(uploaded_by, limit=5000))
        return jsonify({"ok": True, "started": False, "running": False, "pending": 0, "recoverable_pending": recoverable_count, "workflow_mode": workflow_mode, "process_status": None, "result": {"ok": True, "workflow_mode": workflow_mode, "received": 0, "indexed": 0, "index_errors": 0, "faces_enabled": faces_auto_index_enabled(), "faces_done": 0, "faces_errors": 0, "ai_enabled": ai_auto_ingest_enabled(), "ai_done": 0, "ai_errors": 0, "ai_desc_enabled": ai_desc_auto_ingest_enabled(), "ai_desc_done": 0, "ai_desc_errors": 0}})

    _clear_stop_all_barrier()
    _mark_upload_postprocess_starting(uploaded_by, workflow_mode, len(rels))
    threading.Thread(target=_upload_postprocess_worker, args=(uploaded_by, rels), daemon=True).start()
    with UPLOAD_PENDING_LOCK:
        pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
    return jsonify({"ok": True, "started": True, "running": True, "pending": pending_count, "queued": len(rels), "workflow_mode": workflow_mode})


@app.route("/api/upload/postprocess/status")
@login_required
def api_upload_postprocess_status():
    uploaded_by = str(getattr(current_user, "username", "") or "")
    workflow_mode = upload_workflow_mode()
    state = _get_upload_postprocess_state(uploaded_by)
    with UPLOAD_PENDING_LOCK:
        pending_count = len(UPLOAD_PENDING_BY_USER.get((uploaded_by or "").strip() or "__unknown__", []))
    recoverable_count = 0
    if not state or not bool(state.get("running")):
        recoverable_count = len(_recover_uploaded_rels_missing_postprocess(uploaded_by, limit=5000))
    if not state:
        return jsonify({"ok": True, "running": False, "pending": pending_count, "recoverable_pending": recoverable_count, "workflow_mode": workflow_mode, "process_status": None, "result": None, "error": None, "phase": None, "current_rel": None, "stage_processed": 0, "stage_total": 0})
    return jsonify(
        {
            "ok": True,
            "running": bool(state.get("running")),
            "pending": pending_count,
            "recoverable_pending": recoverable_count,
            "workflow_mode": state.get("workflow_mode") or workflow_mode,
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
            "result": state.get("result"),
            "error": state.get("error"),
            "phase": state.get("phase"),
            "process_status": state.get("process_status"),
            "current_rel": state.get("current_rel"),
            "stage_processed": int(state.get("stage_processed") or 0),
            "stage_total": int(state.get("stage_total") or 0),
        }
    )


@app.route("/api/upload/direct-postprocess/status")
@login_required
def api_upload_direct_postprocess_status():
    state_user = DIRECT_UPLOAD_POSTPROCESS_USER
    workflow_mode = upload_workflow_mode()
    state = _get_upload_postprocess_state(state_user)
    with UPLOAD_PENDING_LOCK:
        pending_count = len(UPLOAD_PENDING_BY_USER.get(state_user, []))
    if not state:
        return jsonify(
            {
                "ok": True,
                "running": False,
                "pending": pending_count,
                "workflow_mode": workflow_mode,
                "process_status": None,
                "result": None,
                "error": None,
                "phase": None,
                "current_rel": None,
                "stage_processed": 0,
                "stage_total": 0,
                "overall_processed": 0,
                "overall_total": pending_count,
            }
        )
    overall_processed = int(state.get("overall_processed") or state.get("stage_processed") or 0)
    overall_total = int(state.get("overall_total") or state.get("stage_total") or 0)
    if bool(state.get("running")) and pending_count > 0:
        overall_total += pending_count
    overall_total = max(overall_total, overall_processed)
    return jsonify(
        {
            "ok": True,
            "running": bool(state.get("running")),
            "pending": pending_count,
            "workflow_mode": state.get("workflow_mode") or workflow_mode,
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
            "result": state.get("result"),
            "error": state.get("error"),
            "phase": state.get("phase"),
            "process_status": state.get("process_status"),
            "current_rel": state.get("current_rel"),
            "stage_processed": int(state.get("stage_processed") or 0),
            "stage_total": int(state.get("stage_total") or 0),
            "overall_processed": overall_processed,
            "overall_total": overall_total,
        }
    )


@app.route("/api/upload/folder-sync/status")
@login_required
def api_upload_folder_sync_status():
    folder = request.args.get("folder")
    direct_only = str(request.args.get("direct") or "").strip().lower() in {"1", "true", "yes", "on"}
    try:
        sync_folder = _normalize_upload_folder_for_disk_sync(folder)
        sync_rel = f"uploads/{sync_folder}" if sync_folder else "uploads"
        if not _is_rel_visible_for_current_user(sync_rel):
            return jsonify({"ok": False, "error": "forbidden"}), 403
        disk_sync = _sync_upload_folder_from_disk(
            sync_folder,
            recursive=not direct_only,
            max_files=UPLOAD_FOLDER_SYNC_MAX_FILES,
            queue_postprocess=True,
        )
    except Exception as e:
        disk_sync = {"ok": False, "error": str(e), "folder": str(folder or "")}

    state_user = DIRECT_UPLOAD_POSTPROCESS_USER
    post_state = _get_upload_postprocess_state(state_user)
    with UPLOAD_PENDING_LOCK:
        pending_count = len(UPLOAD_PENDING_BY_USER.get(state_user, []))
    return jsonify(
        {
            "ok": True,
            "disk_sync": disk_sync,
            "postprocess": {
                "running": bool(post_state.get("running")) if post_state else False,
                "pending": pending_count,
                "phase": post_state.get("phase") if post_state else None,
                "workflow_mode": post_state.get("workflow_mode") if post_state else upload_workflow_mode(),
                "process_status": post_state.get("process_status") if post_state else None,
                "stage_processed": int(post_state.get("stage_processed") or 0) if post_state else 0,
                "stage_total": int(post_state.get("stage_total") or 0) if post_state else 0,
            },
        }
    )


@app.route("/api/logs/clear", methods=["POST"])
def api_logs_clear():
    fb = _forbid_user_role_for_maintenance()
    if fb:
        return jsonify(fb[0]), fb[1]
    global LOG_SEQ
    LOG_BUFFER.clear()
    LOG_SEQ = 0
    return jsonify({"ok": True})


# --- Authentication routes ---
def _safe_auth_next_url(value: Optional[str] = None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return url_for("index")
    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc or raw.startswith("//"):
        return url_for("index")
    if not raw.startswith("/"):
        return url_for("index")
    return raw


def _no_store_response(resp):
    try:
        resp.headers["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        resp.headers["Vary"] = "Cookie"
    except Exception:
        pass
    return resp


def _complete_managed_login(local_user: User, username_input: str, success_reason: str, next_url: Optional[str] = None):
    safe_next = _safe_auth_next_url(next_url)
    try:
        with closing(get_conn()) as conn:
            row = conn.execute(
                "SELECT id, username, is_admin, role, totp_enabled, totp_secret, totp_setup_done, totp_remember_days FROM users WHERE id=?",
                (int(local_user.id),),
            ).fetchone()
    except Exception:
        row = None

    if row is not None and int(row["totp_enabled"] or 0) == 1:
        setup_done = int(row["totp_setup_done"] or 0)
        totp_secret = row["totp_secret"]
        if not totp_secret or setup_done == 0:
            _log_login_attempt(username_input, int(local_user.id), str(local_user.username), True, "login_password", "2fa_setup_required")
            login_user(local_user)
            return _no_store_response(redirect(url_for("setup_2fa")))
        if _trust_cookie_valid_for(int(local_user.id)):
            _log_login_attempt(username_input, int(local_user.id), str(local_user.username), True, "login_success", "fjordhub_trusted_device")
            login_user(local_user)
            return _no_store_response(redirect(safe_next))
        session["2fa_user_id"] = int(local_user.id)
        _log_login_attempt(username_input, int(local_user.id), str(local_user.username), True, "login_password", "2fa_required")
        return _no_store_response(redirect(url_for("verify_2fa", next=safe_next)))

    _log_login_attempt(username_input, int(local_user.id), str(local_user.username), True, "login_success", success_reason)
    login_user(local_user)
    return _no_store_response(redirect(safe_next))


@app.route("/login", methods=["GET", "POST"])
def login():
    ensure_runtime_bootstrap()
    if _fjordhub_managed():
        if current_user.is_authenticated:
            return _no_store_response(redirect(_safe_auth_next_url(request.args.get("next"))))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            hub_user = _hub_authenticate(username, password)
            if hub_user:
                local_user = _ensure_managed_local_user(hub_user)
                return _complete_managed_login(local_user, username, "fjordhub_ok", request.args.get("next"))
            _log_login_attempt(username, None, None, False, "login_failed", "fjordhub_invalid")
            return _no_store_response(make_response(render_template("login.html", error=_ui_text("login_invalid_credentials"))))
        created = True if (request.args.get("created") in ("1", "true", "True")) else False
        return _no_store_response(make_response(render_template("login.html", created=created)))
    if users_count() == 0:
        if _install_state_exists():
            return _setup_locked_response()
        return _no_store_response(redirect(url_for("setup")))
    _ensure_install_state_for_existing_users()
    if current_user.is_authenticated:
        return _no_store_response(redirect(_safe_auth_next_url(request.args.get("next"))))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        with closing(get_conn()) as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, is_admin, role, totp_enabled, totp_secret, totp_setup_done, totp_remember_days FROM users WHERE username=?",
                (username,),
            ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            if int(row["totp_enabled"] or 0) == 1:
                # If 2FA is enabled but not set up yet, send to setup
                try:
                    keys = set(row.keys())
                except Exception:
                    keys = set()
                setup_done = int(row["totp_setup_done"] or 0) if ("totp_setup_done" in keys) else 0
                totp_secret = row["totp_secret"] if ("totp_secret" in keys) else None
                if not totp_secret or setup_done == 0:
                    _log_login_attempt(username, int(row["id"]), str(row["username"]), True, "login_password", "2fa_setup_required")
                    user = _row_to_user(row)
                    login_user(user)
                    return _no_store_response(redirect(url_for("setup_2fa")))
                # Otherwise require 2FA unless trusted cookie is valid
                if _trust_cookie_valid_for(int(row["id"])):
                    _log_login_attempt(username, int(row["id"]), str(row["username"]), True, "login_success", "trusted_device")
                    user = _row_to_user(row)
                    login_user(user)
                    return _no_store_response(redirect(_safe_auth_next_url(request.args.get("next"))))
                from flask import session
                session["2fa_user_id"] = int(row["id"])
                _log_login_attempt(username, int(row["id"]), str(row["username"]), True, "login_password", "2fa_required")
                return _no_store_response(redirect(url_for("verify_2fa", next=request.args.get("next"))))
            _log_login_attempt(username, int(row["id"]), str(row["username"]), True, "login_success", "password_ok")
            user = _row_to_user(row)
            login_user(user)
            return _no_store_response(redirect(_safe_auth_next_url(request.args.get("next"))))
        _log_login_attempt(username, None, None, False, "login_failed", "invalid_credentials")
        return _no_store_response(make_response(render_template("login.html", error=_ui_text("login_invalid_credentials"))))
    created = True if (request.args.get("created") in ("1", "true", "True")) else False
    return _no_store_response(make_response(render_template("login.html", created=created)))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return _no_store_response(redirect(url_for("login")))


@app.route("/hub-login")
def hub_login():
    if not _fjordhub_managed():
        return _no_store_response(redirect(url_for("login")))
    token = request.args.get("token", "").strip()
    if not token:
        return _no_store_response(redirect(url_for("login")))
    result = _hub_api("/api/hub/sso-verify", {"token": token}, method="GET")
    if not result.get("ok"):
        return _no_store_response(redirect(url_for("login")))
    try:
        local_user = _ensure_managed_local_user(result)
        return _complete_managed_login(local_user, str(result.get("username", "")), "hub_sso", url_for("index"))
    except Exception:
        return _no_store_response(redirect(url_for("login")))


@app.route("/api/auth/session", methods=["GET"])
def api_auth_session():
    return _no_store_response(jsonify({
        "ok": True,
        "authenticated": bool(current_user.is_authenticated),
    }))


@app.route("/login/2fa", methods=["GET", "POST"])
def verify_2fa():
    from flask import session
    if current_user.is_authenticated:
        return _no_store_response(redirect(_safe_auth_next_url(request.args.get("next"))))
    uid = session.get("2fa_user_id")
    if not uid:
        return _no_store_response(redirect(url_for("login")))
    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id, username, is_admin, role, totp_secret, totp_remember_days FROM users WHERE id= ?", (uid,)).fetchone()
        if not row or not row["totp_secret"]:
            return _no_store_response(redirect(url_for("login")))
        totp = pyotp.TOTP(row["totp_secret"]) 
        if totp.verify(code, valid_window=1):
            _log_login_attempt(str(row["username"]), int(row["id"]), str(row["username"]), True, "login_2fa", "2fa_ok")
            user = _row_to_user(row)
            resp = redirect(_safe_auth_next_url(request.args.get("next")))
            login_user(user)
            # mark that initial setup is completed
            with closing(get_conn()) as conn:
                conn.execute("UPDATE users SET totp_setup_done=1 WHERE id=?", (current_user.id,))
                conn.commit()
            session.pop("2fa_user_id", None)
            # Set trusted-device cookie automatically if preference > 0
            pref_days = int(row["totp_remember_days"] or 0) if row else 0
            if pref_days > 0:
                token, max_age = _make_trust_cookie(int(row["id"]), pref_days)
                if token:
                    resp.set_cookie("fl_trust", token, max_age=max_age, httponly=True, samesite="Lax", path="/")
            return _no_store_response(resp)
        _log_login_attempt(str(row["username"]), int(row["id"]), str(row["username"]), False, "login_2fa", "invalid_code")
        return _no_store_response(make_response(render_template("2fa_verify.html", error=_ui_text("invalid_code"))))
    # GET
    return _no_store_response(make_response(render_template("2fa_verify.html")))


@app.route("/account/2fa", methods=["GET", "POST"])
@login_required
def setup_2fa():
    # Generate secret if missing
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT totp_secret, totp_enabled, totp_remember_days FROM users WHERE id=?",
            (current_user.id,),
        ).fetchone()
    secret = row["totp_secret"] if row else None
    if not secret:
        secret = pyotp.random_base32()
        with closing(get_conn()) as conn:
            conn.execute("UPDATE users SET totp_secret=? WHERE id=?", (secret, current_user.id))
            conn.commit()
    enabled_flag = int(row["totp_enabled"] or 0) if row else 0
    # Only prepare QR/secret for template when not enabled
    data_url = None
    if enabled_flag == 0:
        issuer = "FjordLens"
        user_label = f"{issuer}:{current_user.username}"
        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user_label, issuer_name=issuer)
        img = qrcode.make(otp_uri)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    if request.method == "POST":
        action = (request.form.get("action") or "").strip()
        # Verify code for any sensitive change (disable/change remember)
        code = (request.form.get("code") or "").strip()
        if action in {"disable", "remember", "save"}:
            if not pyotp.TOTP(secret).verify(code, valid_window=1):
                rdays = int(row["totp_remember_days"] or 0) if row else 0
                # For 'save', we only require code if changes are sensitive; we re-check below
                if action != "save":
                    return render_template("2fa_setup.html", qrcode_url=data_url, secret=None, enabled=row["totp_enabled"], error=_ui_text("invalid_code"), remember_days=rdays)
        if action == "disable":
            with closing(get_conn()) as conn:
                conn.execute("UPDATE users SET totp_enabled=0 WHERE id=?", (current_user.id,))
                conn.commit()
            rdays = int(row["totp_remember_days"] or 0) if row else 0
            # Clear trusted-device cookie when disabling 2FA
            resp = make_response(render_template("2fa_setup.html", qrcode_url=None, secret=None, enabled=False, ok=True, remember_days=rdays))
            resp.set_cookie("fl_trust", "", max_age=0)
            return resp
        if action == "save":
            try:
                new_days = max(0, min(30, int(request.form.get("days") or 0)))
            except ValueError:
                new_days = 0
            disable = (request.form.get("disable") in ("1", "on", "true", "True"))
            cur_days = int(row["totp_remember_days"] or 0) if row else 0
            cur_enabled = int(row["totp_enabled"] or 0) if row else 0
            needs_code = (cur_enabled == 1) and (disable or (new_days != cur_days))
            if needs_code and not pyotp.TOTP(secret).verify(code, valid_window=1):
                return render_template("2fa_setup.html", qrcode_url=(data_url if enabled_flag == 0 else None), secret=(secret if enabled_flag == 0 else None), enabled=cur_enabled, error=_ui_text("invalid_code"), remember_days=cur_days)
            enabled_after = cur_enabled
            with closing(get_conn()) as conn:
                if disable and cur_enabled == 1:
                    conn.execute("UPDATE users SET totp_enabled=0 WHERE id=?", (current_user.id,))
                    enabled_after = 0
                # Always update days to what the user chose
                conn.execute("UPDATE users SET totp_remember_days=? WHERE id=?", (new_days, current_user.id))
                conn.commit()
            resp = make_response(render_template("2fa_setup.html", qrcode_url=(data_url if enabled_after == 0 else None), secret=(secret if enabled_after == 0 else None), enabled=bool(enabled_after), ok=True, remember_days=new_days))
            # Manage trusted-device cookie according to new days and enabled state
            if enabled_after == 1 and new_days > 0:
                token, max_age = _make_trust_cookie(int(current_user.id), new_days)
                if token:
                    resp.set_cookie("fl_trust", token, max_age=max_age, httponly=True, samesite="Lax", path="/")
            else:
                resp.set_cookie("fl_trust", "", max_age=0)
            return resp
        if action == "remember":
            try:
                days = max(0, min(30, int(request.form.get("days") or 0)))
            except ValueError:
                days = 0
            with closing(get_conn()) as conn:
                conn.execute("UPDATE users SET totp_remember_days=? WHERE id=?", (days, current_user.id))
                conn.commit()
            # Set/refresh trusted-device cookie immediately after successful verification
            resp = make_response(render_template("2fa_setup.html", qrcode_url=(data_url if enabled_flag == 0 else None), secret=(secret if enabled_flag == 0 else None), enabled=row["totp_enabled"], ok=True, remember_days=days))
            if days > 0:
                token, max_age = _make_trust_cookie(int(current_user.id), days)
                if token:
                    resp.set_cookie("fl_trust", token, max_age=max_age, httponly=True, samesite="Lax", path="/")
            else:
                resp.set_cookie("fl_trust", "", max_age=0)
            return resp
        # enable flow (also accept preferred remember days)
        if pyotp.TOTP(secret).verify(code, valid_window=1):
            try:
                days = max(0, min(30, int(request.form.get("days") or 0)))
            except ValueError:
                days = 0
            with closing(get_conn()) as conn:
                conn.execute("UPDATE users SET totp_enabled=1, totp_setup_done=1, totp_remember_days=? WHERE id=?", (days, current_user.id))
                conn.commit()
            resp = make_response(render_template("2fa_setup.html", qrcode_url=None, secret=None, enabled=True, ok=True, remember_days=days))
            if days > 0:
                token, max_age = _make_trust_cookie(int(current_user.id), days)
                if token:
                    resp.set_cookie("fl_trust", token, max_age=max_age, httponly=True, samesite="Lax", path="/")
            return resp
        rdays = int(row["totp_remember_days"] or 0) if row else 0
        return render_template("2fa_setup.html", qrcode_url=(data_url if enabled_flag == 0 else None), secret=(secret if enabled_flag == 0 else None), enabled=row["totp_enabled"], error=_ui_text("invalid_code"), remember_days=rdays)
    rdays = int(row["totp_remember_days"] or 0) if row else 0
    return render_template("2fa_setup.html", qrcode_url=(data_url if enabled_flag == 0 else None), secret=(secret if enabled_flag == 0 else None), enabled=row["totp_enabled"], remember_days=rdays) 


@app.route("/admin/users", methods=["GET", "POST"]) 
@login_required
def admin_users():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    msg = None
    if _fjordhub_managed() and request.method == "POST":
        return redirect(url_for("index"))
    if request.method == "POST":
        action = (request.form.get("action") or "create").strip()
        if action == "create":
            u = (request.form.get("username") or "").strip()
            p = request.form.get("password") or ""
            role = (request.form.get("role") or "user").strip().lower()
            enforce_2fa = 1 if (request.form.get("enforce_2fa") in ("1", "on", "true", "True")) else 0
            if role not in {"admin", "user"}:
                role = "user"
            if u and p:
                try:
                    with closing(get_conn()) as conn:
                        conn.execute(
                            "INSERT INTO users(username, password_hash, is_admin, role, totp_enabled, totp_setup_done, created_at) VALUES (?,?,?,?,?,?,?)",
                            (u, generate_password_hash(p), 1 if role == "admin" else 0, role, enforce_2fa, 0, now_iso()),
                        )
                        conn.commit()
                    msg = _ui_text("admin_user_created")
                except Exception as e:
                    msg = f"{_ui_text('error_prefix')} {e}"
        elif action == "delete":
            try:
                uid = int(request.form.get("user_id") or 0)
            except Exception:
                uid = 0
            if uid:
                if str(uid) == str(current_user.id):
                    msg = _ui_text("admin_cannot_delete_self")
                else:
                    try:
                        with closing(get_conn()) as conn:
                            row = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
                            if not row:
                                msg = _ui_text("admin_user_not_found")
                            else:
                                r = (row["role"] or "user").lower()
                                if r == "admin":
                                    c = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin' AND id<>?", (uid,)).fetchone()
                                    if not c or int(c["c"]) <= 0:
                                        msg = _ui_text("admin_cannot_delete_last_admin")
                                    else:
                                        conn.execute("DELETE FROM users WHERE id=?", (uid,))
                                        conn.commit()
                                        msg = _ui_text("admin_user_deleted")
                                else:
                                    conn.execute("DELETE FROM users WHERE id=?", (uid,))
                                    conn.commit()
                                    msg = _ui_text("admin_user_deleted")
                    except Exception as e:
                        msg = f"{_ui_text('error_prefix')} {e}"
    with closing(get_conn()) as conn:
        users = conn.execute("SELECT id, username, is_admin, role, totp_enabled, created_at FROM users ORDER BY id").fetchall()
    return render_template("admin_users.html", users=users, msg=msg)


# --- JSON APIs for embedded UI ---
@app.route("/api/admin/users", methods=["GET", "POST"])
@login_required
def api_admin_users():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    if _fjordhub_managed():
        return _api_admin_users_managed()
    if request.method == "GET":
        with closing(get_conn()) as conn:
            rows = conn.execute("SELECT id, username, role, is_admin, totp_enabled, ui_language, search_language, created_at FROM users ORDER BY id").fetchall()
            all_folders = _list_all_photo_folders(conn)
            # Be robust across older DBs that may miss the 'permission' column
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(user_folder_access)").fetchall()]  # type: ignore[index]
                has_perm = "permission" in cols
            except Exception:
                has_perm = False
            if has_perm:
                acl_rows = conn.execute("SELECT user_id, folder_path, COALESCE(permission,'view') AS permission FROM user_folder_access ORDER BY folder_path COLLATE NOCASE").fetchall()
            else:
                acl_rows = conn.execute("SELECT user_id, folder_path FROM user_folder_access ORDER BY folder_path COLLATE NOCASE").fetchall()
            audit_rows = conn.execute(
                """
                SELECT id, at, username_input, user_id, username, success, event_type, reason, ip, country, device
                FROM login_audit
                ORDER BY id DESC
                LIMIT 300
                """
            ).fetchall()
        by_user_acl: dict[int, list[dict]] = {}
        for ar in acl_rows:
            try:
                uid = int(ar["user_id"])
                folder_path = _normalize_folder_acl_path(ar["folder_path"])
            except Exception:
                continue
            if not folder_path:
                continue
            perm = str((ar["permission"] if "permission" in ar.keys() else "view") or "view").strip().lower()
            if perm not in {"view", "upload", "edit"}:
                perm = "view"
            by_user_acl.setdefault(uid, []).append({"folder_path": folder_path, "permission": perm})
        items = []
        for r in rows:
            allowed_folders = by_user_acl.get(int(r["id"]), [])
            items.append({
                "id": int(r["id"]),
                "username": r["username"],
                "role": (r["role"] or ("admin" if int(r["is_admin"] or 0) else "user")),
                "is_admin": bool(r["is_admin"] or 0),
                "managed_by_fjordhub": False,
                "totp_enabled": bool(r["totp_enabled"] or 0),
                "ui_language": _normalize_language(r["ui_language"], DEFAULT_UI_LANGUAGE),
                "search_language": _normalize_language(r["search_language"], DEFAULT_SEARCH_LANGUAGE),
                "allowed_folders": allowed_folders,
                "created_at": r["created_at"],
            })
        login_audit = []
        for ar in audit_rows:
            login_audit.append(
                {
                    "id": int(ar["id"] or 0),
                    "at": ar["at"],
                    "username_input": str(ar["username_input"] or ""),
                    "user_id": int(ar["user_id"]) if ar["user_id"] is not None else None,
                    "username": str(ar["username"] or ""),
                    "success": bool(int(ar["success"] or 0)),
                    "event_type": str(ar["event_type"] or ""),
                    "reason": str(ar["reason"] or ""),
                    "ip": str(ar["ip"] or ""),
                    "country": str(ar["country"] or ""),
                    "device": str(ar["device"] or ""),
                }
            )
        return jsonify({"ok": True, "items": items, "available_folders": all_folders, "login_audit": login_audit})
    # POST create user
    data = request.get_json(silent=True) or {}
    u = (data.get("username") or "").strip()
    p = data.get("password") or ""
    role = (data.get("role") or "user").strip().lower()
    ui_language = _normalize_language(data.get("ui_language"), DEFAULT_UI_LANGUAGE)
    search_language = _normalize_language(data.get("search_language"), DEFAULT_SEARCH_LANGUAGE)
    theme_mode = str((data.get("theme_mode") or "system")).lower()
    if theme_mode not in ("system", "light", "dark"):
        theme_mode = "system"
    raw_allowed = data.get("allowed_folders")
    allowed_folders = raw_allowed if isinstance(raw_allowed, list) else []
    if role not in {"admin", "user"}:
        role = "user"
    if not u or not p:
        return jsonify({"ok": False, "error": "username_password_required"}), 400
    try:
        with closing(get_conn()) as conn:
            cur = conn.execute(
                "INSERT INTO users(username, password_hash, is_admin, role, ui_language, search_language, created_at) VALUES (?,?,?,?,?,?,?)",
                (u, generate_password_hash(p), 1 if role == "admin" else 0, role, ui_language, search_language, now_iso()),
            )
            # Some SQLite drivers/types may expose lastrowid as Optional
            uid_raw = getattr(cur, "lastrowid", None)
            if uid_raw is None:
                row = conn.execute("SELECT id FROM users WHERE username=? ORDER BY id DESC LIMIT 1", (u,)).fetchone()
                uid = int(row["id"]) if row else 0
            else:
                uid = int(uid_raw)
            # Ensure permission column exists before writing ACL rows
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(user_folder_access)").fetchall()]  # type: ignore[index]
                if "permission" not in cols:
                    conn.execute("ALTER TABLE user_folder_access ADD COLUMN permission TEXT DEFAULT 'view'")
            except Exception:
                pass
            _set_user_allowed_folders(conn, uid, allowed_folders)
            conn.commit()
        _hub_sync_user(u, role)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ── FjordHub integration ──────────────────────────────────────────────────────

_FJORDHUB_API_KEY = os.environ.get("FJORDHUB_API_KEY", "")
_FJORDHUB_URL = os.environ.get("FJORDHUB_URL", "")
_FJORDHUB_APP_ID = os.environ.get("FJORDHUB_APP_ID", "fjordlens")


def _fjordhub_managed() -> bool:
    return bool(_FJORDHUB_URL and _FJORDHUB_API_KEY and _FJORDHUB_APP_ID)


def _hub_authorized() -> bool:
    if not _FJORDHUB_API_KEY:
        return False
    return request.headers.get("X-Hub-Key") == _FJORDHUB_API_KEY


def _hub_api(path: str, payload: Optional[dict] = None, method: str = "POST") -> dict:
    if not _fjordhub_managed():
        return {"ok": False, "error": "FjordHub integration er ikke aktiv."}
    data = dict(payload or {})
    data.setdefault("app_id", _FJORDHUB_APP_ID)
    url = f"{_FJORDHUB_URL.rstrip('/')}{path}"
    headers = {"X-Hub-Key": _FJORDHUB_API_KEY}
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=data, headers=headers, timeout=6)
        elif method.upper() == "DELETE":
            response = requests.delete(url, json=data, headers=headers, timeout=6)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=data, headers=headers, timeout=6)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=6)
        try:
            body = response.json()
        except Exception:
            body = {}
        if not response.ok and "ok" not in body:
            body = {"ok": False, "error": f"FjordHub svarede HTTP {response.status_code}"}
        return body
    except Exception as exc:
        return {"ok": False, "error": f"Kunne ikke kontakte FjordHub: {exc}"}


def _hub_authenticate(username: str, password: str) -> Optional[dict]:
    result = _hub_api(
        "/api/hub/apps/authenticate",
        {"username": username, "password": password},
    )
    user = result.get("user")
    return user if result.get("ok") and isinstance(user, dict) else None


def _hub_list_users() -> list[dict]:
    result = _hub_api("/api/hub/apps/users", {}, method="GET")
    return result.get("items", []) if result.get("ok") and isinstance(result.get("items"), list) else []


def _hub_create_user(payload: dict) -> dict:
    return _hub_api("/api/hub/apps/users", payload, method="POST")


def _hub_update_user_role(user_id: int, role: str) -> dict:
    return _hub_api(f"/api/hub/apps/users/{int(user_id)}", {"role": role}, method="PATCH")


def _hub_delete_user_access(user_id: int) -> dict:
    return _hub_api(f"/api/hub/apps/users/{int(user_id)}", {}, method="DELETE")


FJORDHUB_MANAGED_PASSWORD_HASH = "fjordhub-managed"


def _coerce_hub_user_id(value: Any) -> Optional[int]:
    try:
        hub_user_id = int(value)
        return hub_user_id if hub_user_id > 0 else None
    except Exception:
        return None


def _coerce_hub_role(value: Any) -> str:
    return "admin" if str(value or "user").strip().lower() == "admin" else "user"


def _ensure_hub_user_columns(conn: sqlite3.Connection) -> None:
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]  # type: ignore[index]
    except Exception:
        cols = []
    if "hub_user_id" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN hub_user_id INTEGER")
    if "hub_synced_at" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN hub_synced_at TEXT")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_hub_user_id ON users(hub_user_id) WHERE hub_user_id IS NOT NULL")


def _acl_permission_max(left: str, right: str) -> str:
    rank = {"view": 1, "upload": 2, "edit": 3}
    left_clean = str(left or "view").strip().lower()
    right_clean = str(right or "view").strip().lower()
    if left_clean not in rank:
        left_clean = "view"
    if right_clean not in rank:
        right_clean = "view"
    return left_clean if rank[left_clean] >= rank[right_clean] else right_clean


def _merge_managed_user_rows(conn: sqlite3.Connection, source_id: int, target_id: int) -> None:
    if int(source_id) == int(target_id):
        return

    source_acl = conn.execute(
        "SELECT folder_path, COALESCE(permission,'view') AS permission FROM user_folder_access WHERE user_id=?",
        (int(source_id),),
    ).fetchall()
    for row in source_acl:
        folder_path = _normalize_folder_acl_path(row["folder_path"])
        if not folder_path:
            continue
        permission = str(row["permission"] or "view").strip().lower()
        existing = conn.execute(
            "SELECT permission FROM user_folder_access WHERE user_id=? AND folder_path=?",
            (int(target_id), folder_path),
        ).fetchone()
        if existing:
            merged = _acl_permission_max(str(existing["permission"] or "view"), permission)
            conn.execute(
                "UPDATE user_folder_access SET permission=? WHERE user_id=? AND folder_path=?",
                (merged, int(target_id), folder_path),
            )
        else:
            conn.execute(
                "INSERT INTO user_folder_access(user_id, folder_path, permission, created_at) VALUES(?,?,?,?)",
                (int(target_id), folder_path, permission if permission in {"view", "upload", "edit"} else "view", now_iso()),
            )

    conn.execute("DELETE FROM user_folder_access WHERE user_id=?", (int(source_id),))
    for table, column in (
        ("login_audit", "user_id"),
        ("share_links", "created_by_user_id"),
        ("folder_owners", "user_id"),
    ):
        try:
            conn.execute(f"UPDATE {table} SET {column}=? WHERE {column}=?", (int(target_id), int(source_id)))
        except Exception:
            pass

    row = conn.execute("SELECT password_hash FROM users WHERE id=?", (int(source_id),)).fetchone()
    if row is not None and str(row["password_hash"] or "") == FJORDHUB_MANAGED_PASSWORD_HASH:
        conn.execute("DELETE FROM users WHERE id=?", (int(source_id),))
    else:
        conn.execute("UPDATE users SET hub_user_id=NULL, hub_synced_at=NULL WHERE id=?", (int(source_id),))


def _hub_user_id_for_local_user(local_user_id: int) -> int:
    with closing(get_conn()) as conn:
        try:
            _ensure_hub_user_columns(conn)
            row = conn.execute(
                "SELECT id, hub_user_id, password_hash FROM users WHERE id=?",
                (int(local_user_id),),
            ).fetchone()
        except Exception:
            row = None
    if not row:
        return int(local_user_id)
    hub_user_id = _coerce_hub_user_id(row["hub_user_id"])
    if hub_user_id:
        return hub_user_id
    if str(row["password_hash"] or "") == FJORDHUB_MANAGED_PASSWORD_HASH:
        return int(row["id"])
    return int(local_user_id)


def _delete_local_managed_user(local_user_id: int) -> None:
    with closing(get_conn()) as conn:
        _ensure_hub_user_columns(conn)
        row = conn.execute(
            "SELECT id, password_hash, hub_user_id FROM users WHERE id=?",
            (int(local_user_id),),
        ).fetchone()
        if row is None:
            return
        if row["hub_user_id"] is None and str(row["password_hash"] or "") != FJORDHUB_MANAGED_PASSWORD_HASH:
            return
        conn.execute("DELETE FROM user_folder_access WHERE user_id=?", (int(local_user_id),))
        try:
            conn.execute("UPDATE login_audit SET user_id=NULL WHERE user_id=?", (int(local_user_id),))
        except Exception:
            pass
        try:
            conn.execute("UPDATE share_links SET created_by_user_id=NULL WHERE created_by_user_id=?", (int(local_user_id),))
        except Exception:
            pass
        try:
            conn.execute("DELETE FROM folder_owners WHERE user_id=?", (int(local_user_id),))
        except Exception:
            pass
        conn.execute("DELETE FROM users WHERE id=?", (int(local_user_id),))
        conn.commit()


def _ensure_managed_local_user(hub_user: dict) -> User:
    hub_user_id = _coerce_hub_user_id(hub_user.get("id"))
    if not hub_user_id:
        raise ValueError("FjordHub bruger mangler id.")
    username = str(hub_user.get("username") or "").strip()
    if not username:
        raise ValueError("FjordHub bruger mangler brugernavn.")
    role = _coerce_hub_role(hub_user.get("role"))
    ui_language = _normalize_language(hub_user.get("language"), DEFAULT_UI_LANGUAGE)
    with closing(get_conn()) as conn:
        _ensure_hub_user_columns(conn)
        row = conn.execute(
            "SELECT * FROM users WHERE hub_user_id=? LIMIT 1",
            (hub_user_id,),
        ).fetchone()
        username_row = conn.execute(
            "SELECT * FROM users WHERE lower(username)=lower(?) LIMIT 1",
            (username,),
        ).fetchone()
        legacy_row = conn.execute(
            "SELECT * FROM users WHERE id=? AND password_hash=? LIMIT 1",
            (hub_user_id, FJORDHUB_MANAGED_PASSWORD_HASH),
        ).fetchone()

        target = row or username_row or legacy_row
        if row is not None and username_row is not None and int(row["id"]) != int(username_row["id"]):
            _merge_managed_user_rows(conn, int(row["id"]), int(username_row["id"]))
            target = username_row
        elif row is None and legacy_row is not None and username_row is not None and int(legacy_row["id"]) != int(username_row["id"]):
            _merge_managed_user_rows(conn, int(legacy_row["id"]), int(username_row["id"]))
            target = username_row

        if target is not None:
            local_user_id = int(target["id"])
            current_search_language = _normalize_language(
                target["search_language"] if "search_language" in target.keys() else None,
                DEFAULT_SEARCH_LANGUAGE,
            )
            conn.execute(
                """
                UPDATE users
                SET username=?, password_hash=?, is_admin=?, role=?,
                    hub_user_id=?, hub_synced_at=?, ui_language=?, search_language=?
                WHERE id=?
                """,
                (
                    username,
                    FJORDHUB_MANAGED_PASSWORD_HASH,
                    1 if role == "admin" else 0,
                    role,
                    hub_user_id,
                    now_iso(),
                    ui_language,
                    current_search_language,
                    local_user_id,
                ),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO users(username, password_hash, is_admin, role, hub_user_id, hub_synced_at, ui_language, search_language, created_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    username,
                    FJORDHUB_MANAGED_PASSWORD_HASH,
                    1 if role == "admin" else 0,
                    role,
                    hub_user_id,
                    now_iso(),
                    ui_language,
                    DEFAULT_SEARCH_LANGUAGE,
                    now_iso(),
                ),
            )
            local_user_id = int(cur.lastrowid)
        row = conn.execute(
            "SELECT id, username, is_admin, role, ui_language, search_language, hub_user_id FROM users WHERE id=?",
            (local_user_id,),
        ).fetchone()
        conn.commit()
    user = _row_to_user(row)
    if user is None:
        raise RuntimeError("Kunne ikke oprette lokal FjordHub-profil.")
    return user


def _managed_user_item(hub_user: dict, allowed_folders: list[dict] | None = None) -> dict:
    local_user = _ensure_managed_local_user(hub_user)
    hub_user_id = _coerce_hub_user_id(hub_user.get("id")) or getattr(local_user, "hub_user_id", None)
    return {
        "id": int(local_user.id),
        "hub_user_id": hub_user_id,
        "username": local_user.username,
        "role": local_user.role,
        "is_admin": local_user.is_admin,
        "managed_by_fjordhub": True,
        "totp_enabled": False,
        "ui_language": local_user.ui_language,
        "search_language": local_user.search_language,
        "allowed_folders": allowed_folders or [],
        "created_at": str(hub_user.get("created_at") or ""),
    }


def _managed_acl_by_user(conn) -> dict[int, list[dict]]:
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(user_folder_access)").fetchall()]
        has_perm = "permission" in cols
        if has_perm:
            rows = conn.execute(
                "SELECT user_id, folder_path, COALESCE(permission,'view') AS permission FROM user_folder_access ORDER BY folder_path COLLATE NOCASE"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT user_id, folder_path FROM user_folder_access ORDER BY folder_path COLLATE NOCASE"
            ).fetchall()
    except Exception:
        rows = []
    by_user: dict[int, list[dict]] = {}
    for row in rows:
        folder_path = _normalize_folder_acl_path(row["folder_path"])
        if not folder_path:
            continue
        perm = str((row["permission"] if "permission" in row.keys() else "view") or "view").strip().lower()
        if perm not in {"view", "upload", "edit"}:
            perm = "view"
        by_user.setdefault(int(row["user_id"]), []).append({"folder_path": folder_path, "permission": perm})
    return by_user


def _api_admin_users_managed():
    if request.method == "GET":
        hub_users = _hub_list_users()
        with closing(get_conn()) as conn:
            all_folders = _list_all_photo_folders(conn)
            acl_by_user = _managed_acl_by_user(conn)
        items: list[dict] = []
        for user in hub_users:
            if not isinstance(user, dict):
                continue
            try:
                item = _managed_user_item(user)
                item["allowed_folders"] = acl_by_user.get(int(item["id"]), [])
                items.append(item)
            except Exception as exc:
                app.logger.warning("Could not sync FjordHub user into FjordLens: %s", exc)
        return jsonify({
            "ok": True,
            "managed_by_fjordhub": True,
            "items": items,
            "available_folders": all_folders,
            "login_audit": [],
        })

    data = request.get_json(silent=True) or {}
    role = str(data.get("role") or "user").strip().lower()
    if role not in {"admin", "user"}:
        role = "user"
    result = _hub_create_user({
        "username": str(data.get("username") or "").strip(),
        "password": str(data.get("password") or ""),
        "role": role,
        "language": _normalize_language(data.get("ui_language"), DEFAULT_UI_LANGUAGE),
    })
    if not result.get("ok"):
        return jsonify({"ok": False, "error": result.get("error") or "Kunne ikke oprette bruger i FjordHub"}), 400
    hub_user = result.get("user") or result.get("item") or {}
    item = _managed_user_item(hub_user if isinstance(hub_user, dict) else {})
    ui_language = _normalize_language(data.get("ui_language"), DEFAULT_UI_LANGUAGE)
    search_language = _normalize_language(data.get("search_language"), DEFAULT_SEARCH_LANGUAGE)
    with closing(get_conn()) as conn:
        conn.execute(
            "UPDATE users SET ui_language=?, search_language=? WHERE id=?",
            (ui_language, search_language, int(item["id"])),
        )
        conn.commit()
    item["ui_language"] = ui_language
    item["search_language"] = search_language
    raw_allowed = data.get("allowed_folders")
    if isinstance(raw_allowed, list):
        with closing(get_conn()) as conn:
            _set_user_allowed_folders(conn, int(item["id"]), raw_allowed)
            updated_allowed = _managed_acl_by_user(conn).get(int(item["id"]), [])
            conn.commit()
        item["allowed_folders"] = updated_allowed
    return jsonify({"ok": True, "item": item})


def _hub_sync_user(username: str, role: str) -> None:
    if not _fjordhub_managed():
        return
    _hub_create_user({"username": username, "role": role})


@app.route("/api/hub/users", methods=["GET", "POST"])
def hub_users():
    if not _hub_authorized():
        return jsonify({"ok": False, "error": "Uautoriseret"}), 401
    if _fjordhub_managed():
        return jsonify({"ok": False, "error": "Lokal bruger-provisionering er slået fra i FjordHub-managed mode."}), 410
    if request.method == "GET":
        with closing(get_conn()) as conn:
            rows = conn.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY id"
            ).fetchall()
        return jsonify({"ok": True, "items": [
            {"id": r["id"], "username": r["username"], "role": r["role"] or "user", "created_at": r["created_at"]}
            for r in rows
        ]})
    data = request.get_json(silent=True) or {}
    u = str(data.get("username") or "").strip()
    p = str(data.get("password") or "")
    role = str(data.get("role") or "user").strip().lower()
    if role not in ("admin", "user"):
        role = "user"
    if not u or not p:
        return jsonify({"ok": False, "error": "username og password påkrævet"}), 400
    if len(p) < 6:
        return jsonify({"ok": False, "error": "Adgangskode skal være mindst 6 tegn"}), 400
    try:
        with closing(get_conn()) as conn:
            conn.execute(
                "INSERT INTO users(username, password_hash, is_admin, role, ui_language, search_language, created_at) VALUES (?,?,?,?,?,?,?)",
                (u, generate_password_hash(p), 1 if role == "admin" else 0, role, DEFAULT_UI_LANGUAGE, DEFAULT_SEARCH_LANGUAGE, now_iso()),
            )
            conn.commit()
        return jsonify({"ok": True}), 201
    except Exception as exc:
        if "UNIQUE" in str(exc) or "unique" in str(exc).lower():
            return jsonify({"ok": False, "error": "Brugernavn findes allerede"}), 409
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/hub/users/<int:user_id>", methods=["PATCH", "DELETE"])
def hub_user(user_id: int):
    if not _hub_authorized():
        return jsonify({"ok": False, "error": "Uautoriseret"}), 401
    if _fjordhub_managed():
        return jsonify({"ok": False, "error": "Lokal bruger-provisionering er slået fra i FjordHub-managed mode."}), 410
    if request.method == "DELETE":
        with closing(get_conn()) as conn:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
        return jsonify({"ok": True})
    data = request.get_json(silent=True) or {}
    role = str(data.get("role") or "user").strip().lower()
    if role not in ("admin", "user"):
        return jsonify({"ok": False, "error": "Ugyldig rolle"}), 400
    with closing(get_conn()) as conn:
        conn.execute(
            "UPDATE users SET role=?, is_admin=? WHERE id=?",
            (role, 1 if role == "admin" else 0, user_id),
        )
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/shares", methods=["GET"])
@login_required
def api_admin_shares_list():
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    include_inactive = request.args.get("include_inactive") in {"1", "true", "True"}
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
             SELECT s.id, s.share_name, s.folder_path, s.can_upload, s.can_delete, s.password_hash,
                 s.token_plain, s.link_use_duckdns, s.require_visitor_name,
                   s.expires_at, s.revoked, s.created_at, s.last_used_at, s.created_by_user_id,
                   u.username AS created_by_username
            FROM share_links s
            LEFT JOIN users u ON u.id = s.created_by_user_id
            ORDER BY s.created_at DESC
            """
        ).fetchall()
        folder_rows = conn.execute(
            "SELECT share_id, folder_path FROM share_link_folders ORDER BY folder_path COLLATE NOCASE"
        ).fetchall()

    folders_by_share: dict[int, list[str]] = {}
    for fr in folder_rows:
        try:
            sid = int(fr["share_id"] or 0)
        except Exception:
            continue
        fp = _normalize_share_folder_path(fr["folder_path"])
        if not sid or not fp:
            continue
        bucket = folders_by_share.setdefault(sid, [])
        if fp not in bucket:
            bucket.append(fp)

    items: list[dict[str, Any]] = []
    for r in rows:
        revoked = bool(int(r["revoked"] or 0))
        expired = _share_is_expired(r["expires_at"])
        active = (not revoked) and (not expired)
        if not include_inactive and not active:
            continue

        can_upload = bool(int(r["can_upload"] or 0))
        can_delete = bool(int(r["can_delete"] or 0))
        permission = "view"
        if can_upload and can_delete:
            permission = "manage"
        elif can_upload:
            permission = "upload"

        share_id = int(r["id"])
        folder_paths = list(folders_by_share.get(share_id, []))
        if not folder_paths:
            fallback = _normalize_share_folder_path(r["folder_path"])
            if fallback:
                folder_paths = [fallback]
        share_name = str(r["share_name"] or "").strip()
        if not share_name:
            if len(folder_paths) == 1:
                share_name = f"uploads/{folder_paths[0]}"
            elif folder_paths:
                share_name = f"{len(folder_paths)} mapper"

        link = _share_link_for_admin_row(r)

        items.append(
            {
                "id": share_id,
                "share_name": share_name,
                "folder_path": (folder_paths[0] if folder_paths else _normalize_share_folder_path(r["folder_path"])),
                "folder_paths": folder_paths,
                "folder_count": len(folder_paths),
                "permission": permission,
                "can_upload": can_upload,
                "can_delete": can_delete,
                "require_visitor_name": bool(int(r["require_visitor_name"] or 0)),
                "use_duckdns": bool(int(r["link_use_duckdns"] or 0)),
                "password_enabled": bool(str(r["password_hash"] or "").strip()),
                "expires_at": r["expires_at"],
                "created_at": r["created_at"],
                "last_used_at": r["last_used_at"],
                "revoked": revoked,
                "expired": expired,
                "active": active,
                "created_by_user_id": int(r["created_by_user_id"] or 0),
                "created_by_username": (r["created_by_username"] or ""),
                "link": link,
                "link_available": bool(link),
            }
        )

    return jsonify({"ok": True, "items": items})


@app.route("/api/admin/shares/<int:share_id>/revoke", methods=["POST"])
@login_required
def api_admin_shares_revoke(share_id: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    with closing(get_conn()) as conn:
        row = conn.execute("SELECT id, revoked FROM share_links WHERE id=?", (int(share_id),)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Share-link findes ikke"}), 404
        if int(row["revoked"] or 0) == 1:
            return jsonify({"ok": True, "already_revoked": True})
        conn.execute("UPDATE share_links SET revoked=1 WHERE id=?", (int(share_id),))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/shares/<int:share_id>/extend", methods=["POST"])
@login_required
def api_admin_shares_extend(share_id: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    body = request.get_json(silent=True) or {}
    expires_at, expires_error = _share_expires_at_from_body(body, default_value=7, default_unit="days")
    if expires_error:
        return jsonify({"ok": False, "error": expires_error}), 400

    with closing(get_conn()) as conn:
        row = conn.execute("SELECT id, revoked FROM share_links WHERE id=?", (int(share_id),)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Share-link findes ikke"}), 404
        if int(row["revoked"] or 0) == 1:
            return jsonify({"ok": False, "error": "Share-link er tilbagekaldt"}), 400
        conn.execute("UPDATE share_links SET expires_at=? WHERE id=?", (expires_at, int(share_id)))
        conn.commit()

    return jsonify({"ok": True, "expires_at": expires_at})


@app.route("/api/admin/shares/<int:share_id>/activate", methods=["POST"])
@login_required
def api_admin_shares_activate(share_id: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    body = request.get_json(silent=True) or {}
    expires_at, expires_error = _share_expires_at_from_body(body, default_value=7, default_unit="days")
    if expires_error:
        return jsonify({"ok": False, "error": expires_error}), 400

    with closing(get_conn()) as conn:
        row = conn.execute("SELECT id FROM share_links WHERE id=?", (int(share_id),)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Share-link findes ikke"}), 404
        conn.execute("UPDATE share_links SET revoked=0, expires_at=? WHERE id=?", (expires_at, int(share_id)))
        conn.commit()

    return jsonify({"ok": True, "expires_at": expires_at})


@app.route("/api/admin/shares/<int:share_id>", methods=["PUT"])
@login_required
def api_admin_shares_update(share_id: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    body = request.get_json(silent=True) or {}
    raw_folder_paths = body.get("folder_paths")
    folder_paths_raw: list[str]
    if isinstance(raw_folder_paths, list):
        folder_paths_raw = [str(v or "") for v in raw_folder_paths]
    else:
        folder_paths_raw = [str(body.get("folder_path") or "")]

    folder_paths: list[str] = []
    for raw in folder_paths_raw:
        try:
            fp = _normalize_share_folder_path(raw)
        except Exception:
            fp = ""
        if fp and fp not in folder_paths:
            folder_paths.append(fp)
    if not folder_paths:
        return jsonify({"ok": False, "error": "VÃ¦lg mindst Ã©n mappe"}), 400

    base = UPLOAD_DIR.resolve()
    for folder_path in folder_paths:
        candidates = [
            (UPLOAD_DIR / folder_path),
            (UPLOAD_DIR / "originals" / folder_path),
            (UPLOAD_DIR / "converted" / folder_path),
        ]
        found = False
        for cand in candidates:
            try:
                target = cand.resolve()
                target.relative_to(base)
            except Exception:
                continue
            if target.exists() and target.is_dir():
                found = True
                break
        if not found:
            return jsonify({"ok": False, "error": f"Mappen findes ikke: {folder_path}"}), 404

    share_name = str(body.get("share_name") or "").strip()
    if len(share_name) > 120:
        share_name = share_name[:120].strip()
    if not share_name:
        if len(folder_paths) == 1:
            share_name = f"uploads/{folder_paths[0]}"
        else:
            share_name = f"{len(folder_paths)} mapper"

    perm = str(body.get("permission") or "view").strip().lower()
    can_upload = 0
    can_delete = 0
    if perm == "upload":
        can_upload = 1
    elif perm in {"manage", "delete"}:
        can_upload = 1
        can_delete = 1
    elif perm != "view":
        return jsonify({"ok": False, "error": "Ugyldig rettighed"}), 400

    expires_at, expires_error = _share_expires_at_from_body(body, default_value=7, default_unit="days")
    if expires_error:
        return jsonify({"ok": False, "error": expires_error}), 400

    password_enabled = bool(body.get("password_enabled"))
    require_visitor_name = bool(body.get("require_visitor_name"))
    use_duckdns = bool(body.get("use_duckdns"))
    password_raw = str(body.get("password") or "")

    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM share_links WHERE id=?",
            (int(share_id),),
        ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Share-link findes ikke"}), 404

        existing_password_hash = str(row["password_hash"] or "").strip()
        password_hash: Optional[str]
        if not password_enabled:
            password_hash = None
        else:
            if password_raw:
                if len(password_raw) < 4:
                    return jsonify({"ok": False, "error": "Adgangskode skal vÃ¦re mindst 4 tegn"}), 400
                password_hash = generate_password_hash(password_raw)
            elif existing_password_hash:
                password_hash = existing_password_hash
            else:
                return jsonify({"ok": False, "error": "Adgangskode skal vÃ¦re mindst 4 tegn"}), 400

        now = now_iso()
        primary_folder_path = folder_paths[0]
        conn.execute(
            """
            UPDATE share_links
               SET share_name=?,
                   folder_path=?,
                   can_upload=?,
                   can_delete=?,
                   require_visitor_name=?,
                   link_use_duckdns=?,
                   password_hash=?,
                   expires_at=?
             WHERE id=?
            """,
            (
                share_name,
                primary_folder_path,
                int(can_upload),
                int(can_delete),
                1 if require_visitor_name else 0,
                1 if use_duckdns else 0,
                password_hash,
                expires_at,
                int(share_id),
            ),
        )
        conn.execute("DELETE FROM share_link_folders WHERE share_id=?", (int(share_id),))
        for fp in folder_paths:
            conn.execute(
                "INSERT OR IGNORE INTO share_link_folders(share_id, folder_path, created_at) VALUES(?,?,?)",
                (int(share_id), fp, now),
            )
        conn.commit()

    return jsonify(
        {
            "ok": True,
            "id": int(share_id),
            "share_name": share_name,
            "folder_path": folder_paths[0],
            "folder_paths": folder_paths,
            "permission": perm,
            "can_upload": bool(can_upload),
            "can_delete": bool(can_delete),
            "require_visitor_name": bool(require_visitor_name),
            "password_enabled": bool(password_hash),
            "use_duckdns": bool(use_duckdns),
            "expires_at": expires_at,
        }
    )


@app.route("/api/admin/shares/<int:share_id>", methods=["DELETE"])
@login_required
def api_admin_shares_delete(share_id: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    with closing(get_conn()) as conn:
        row = conn.execute("SELECT id FROM share_links WHERE id=?", (int(share_id),)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Share-link findes ikke"}), 404
        conn.execute("DELETE FROM share_link_folders WHERE share_id=?", (int(share_id),))
        conn.execute("DELETE FROM share_links WHERE id=?", (int(share_id),))
        conn.commit()

    return jsonify({"ok": True})


@app.route("/api/admin/users/<int:uid>", methods=["DELETE", "PUT"])
@login_required
def api_admin_users_delete(uid: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    if _fjordhub_managed():
        if request.method == "PUT":
            data = request.get_json(silent=True) or {}
            role = str(data.get("role") or "user").strip().lower()
            if role not in {"admin", "user"}:
                return jsonify({"ok": False, "error": "invalid_role"}), 400
            with closing(get_conn()) as conn:
                _ensure_hub_user_columns(conn)
                row = conn.execute(
                    "SELECT id, username, hub_user_id FROM users WHERE id=?",
                    (int(uid),),
                ).fetchone()
            if row is None:
                return jsonify({"ok": False, "error": "not_found"}), 404
            requested_username = str(data.get("username") or row["username"] or "").strip()
            if requested_username.lower() != str(row["username"] or "").strip().lower():
                return jsonify({"ok": False, "error": "username_managed_by_fjordhub"}), 400
            if str(data.get("password") or "").strip():
                return jsonify({"ok": False, "error": "password_managed_by_fjordhub"}), 400
            if str(uid) == str(current_user.id) and role != "admin":
                return jsonify({"ok": False, "error": "cannot_demote_self"}), 400
            hub_user_id = _hub_user_id_for_local_user(uid)
            result = _hub_update_user_role(hub_user_id, role)
            if not result.get("ok"):
                return jsonify({"ok": False, "error": result.get("error") or "update_failed"}), 400
            ui_language = _normalize_language(data.get("ui_language"), DEFAULT_UI_LANGUAGE)
            search_language = _normalize_language(data.get("search_language"), DEFAULT_SEARCH_LANGUAGE)
            with closing(get_conn()) as conn:
                conn.execute(
                    "UPDATE users SET ui_language=?, search_language=? WHERE id=?",
                    (ui_language, search_language, int(uid)),
                )
                conn.commit()
            item = _managed_user_item(
                result.get("user") or result.get("item") or {"id": hub_user_id, "username": row["username"], "role": role}
            )
            item["ui_language"] = ui_language
            item["search_language"] = search_language
            raw_allowed = data.get("allowed_folders")
            if isinstance(raw_allowed, list):
                with closing(get_conn()) as conn:
                    _set_user_allowed_folders(conn, int(uid), raw_allowed)
                    item["allowed_folders"] = _managed_acl_by_user(conn).get(int(uid), [])
                    conn.commit()
            return jsonify({"ok": True, "item": item})
        if str(uid) == str(current_user.id):
            return jsonify({"ok": False, "error": "cannot_delete_self"}), 400
        hub_user_id = _hub_user_id_for_local_user(uid)
        result = _hub_delete_user_access(hub_user_id)
        if not result.get("ok"):
            return jsonify({"ok": False, "error": result.get("error") or "delete_failed"}), 400
        _delete_local_managed_user(uid)
        return jsonify({"ok": True})
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        new_username = (data.get("username") or "").strip()
        new_password = data.get("password") or ""
        new_role_raw = data.get("role")
        new_role = None
        if new_role_raw is not None:
            new_role = str(new_role_raw).strip().lower()
            if new_role not in {"admin", "user"}:
                return jsonify({"ok": False, "error": "invalid_role"}), 400
        ui_language = _normalize_language(data.get("ui_language"), DEFAULT_UI_LANGUAGE)
        search_language = _normalize_language(data.get("search_language"), DEFAULT_SEARCH_LANGUAGE)
        raw_allowed = data.get("allowed_folders")
        allowed_folders = raw_allowed if isinstance(raw_allowed, list) else None
        if not new_username:
            return jsonify({"ok": False, "error": "username_required"}), 400
        try:
            with closing(get_conn()) as conn:
                row = conn.execute("SELECT id, role FROM users WHERE id=?", (uid,)).fetchone()
                if not row:
                    return jsonify({"ok": False, "error": "not_found"}), 404

                cur_role = (row["role"] or "user").lower()
                target_role = new_role or cur_role

                if cur_role == "admin" and target_role != "admin":
                    c = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin' AND id<>?", (uid,)).fetchone()
                    if not c or int(c["c"]) <= 0:
                        return jsonify({"ok": False, "error": "last_admin"}), 400

                if new_password:
                    conn.execute(
                        "UPDATE users SET username=?, password_hash=?, role=?, is_admin=?, ui_language=?, search_language=? WHERE id=?",
                        (
                            new_username,
                            generate_password_hash(new_password),
                            target_role,
                            1 if target_role == "admin" else 0,
                            ui_language,
                            search_language,
                            uid,
                        ),
                    )
                else:
                    conn.execute(
                        "UPDATE users SET username=?, role=?, is_admin=?, ui_language=?, search_language=? WHERE id=?",
                        (
                            new_username,
                            target_role,
                            1 if target_role == "admin" else 0,
                            ui_language,
                            search_language,
                            uid,
                        ),
                    )
                if allowed_folders is not None:
                    _set_user_allowed_folders(conn, uid, allowed_folders)
                conn.commit()
            return jsonify({"ok": True})
        except sqlite3.IntegrityError:
            return jsonify({"ok": False, "error": "username_exists"}), 409
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    if str(uid) == str(current_user.id):
        return jsonify({"ok": False, "error": "cannot_delete_self"}), 400
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
            if not row:
                return jsonify({"ok": False, "error": "not_found"}), 404
            r = (row["role"] or "user").lower()
            if r == "admin":
                c = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin' AND id<>?", (uid,)).fetchone()
                if not c or int(c["c"]) <= 0:
                    return jsonify({"ok": False, "error": "last_admin"}), 400
            conn.execute("DELETE FROM user_folder_access WHERE user_id=?", (uid,))
            conn.execute("DELETE FROM users WHERE id=?", (uid,))
            conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/admin/users/<int:uid>/folders", methods=["PUT"])
@login_required
def api_admin_user_folders(uid: int):
    if not getattr(current_user, "is_admin", False):
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    data = request.get_json(silent=True) or {}
    raw_allowed = data.get("allowed_folders")
    if not isinstance(raw_allowed, list):
        return jsonify({"ok": False, "error": "invalid_allowed_folders"}), 400
    try:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id FROM users WHERE id=?", (uid,)).fetchone()
            if not row:
                return jsonify({"ok": False, "error": "not_found"}), 404
            # Ensure permission column exists for legacy DBs
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(user_folder_access)").fetchall()]  # type: ignore[index]
                if "permission" not in cols:
                    conn.execute("ALTER TABLE user_folder_access ADD COLUMN permission TEXT DEFAULT 'view'")
            except Exception:
                pass
            reduced = _set_user_allowed_folders(conn, uid, raw_allowed)
            conn.commit()
        return jsonify({"ok": True, "allowed_folders": reduced})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/me", methods=["GET"])
@login_required
def api_me():
    try:
        with closing(get_conn()) as conn:
            try:
                row = conn.execute(
                    "SELECT id, username, role, is_admin, ui_language, search_language, theme_mode FROM users WHERE id=?",
                    (current_user.id,),
                ).fetchone()
            except sqlite3.OperationalError as e:
                if 'no such column' in str(e).lower() and 'theme_mode' in str(e).lower():
                    _ensure_users_theme_mode_column(conn)
                    row = conn.execute(
                        "SELECT id, username, role, is_admin, ui_language, search_language FROM users WHERE id=?",
                        (current_user.id,),
                    ).fetchone()
                else:
                    raise
        if not row:
            return jsonify({"ok": False, "error": "not_found"}), 404
        raw_role = str((row["role"] if "role" in row.keys() else "") or "").strip().lower()
        if raw_role not in {"admin", "user"}:
            try:
                raw_role = "admin" if bool(row["is_admin"]) else "user"
            except Exception:
                raw_role = "user"
        return jsonify(
            {
                "ok": True,
                "item": {
                    "id": int(row["id"]),
                    "username": row["username"],
                    "role": raw_role,
                    "ui_language": _normalize_language(row["ui_language"], DEFAULT_UI_LANGUAGE),
                    "search_language": _normalize_language(row["search_language"], DEFAULT_SEARCH_LANGUAGE),
                    "theme_mode": (str(((row["theme_mode"] if "theme_mode" in row.keys() else "system") or "system")).lower()),
                },
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/me/profile", methods=["POST"])
@login_required
def api_me_profile():
    data = request.get_json(silent=True) or {}
    new_username = (data.get("username") or "").strip()
    new_password = data.get("password") or ""
    ui_language = _normalize_language(data.get("ui_language"), DEFAULT_UI_LANGUAGE)
    search_language = _normalize_language(data.get("search_language"), DEFAULT_SEARCH_LANGUAGE)
    theme_mode = str((data.get("theme_mode") or "system")).lower()
    if theme_mode not in ("system", "light", "dark"):
        theme_mode = "system"

    if not new_username:
        return jsonify({"ok": False, "error": "username_required"}), 400

    try:
        with closing(get_conn()) as conn:
            try:
                if new_password:
                    conn.execute(
                        "UPDATE users SET username=?, password_hash=?, ui_language=?, search_language=?, theme_mode=? WHERE id=?",
                        (
                            new_username,
                            generate_password_hash(new_password),
                            ui_language,
                            search_language,
                            theme_mode,
                            current_user.id,
                        ),
                    )
                else:
                    conn.execute(
                        "UPDATE users SET username=?, ui_language=?, search_language=?, theme_mode=? WHERE id=?",
                        (new_username, ui_language, search_language, theme_mode, current_user.id),
                    )
                conn.commit()
            except sqlite3.OperationalError as e:
                if 'no such column' in str(e).lower() and 'theme_mode' in str(e).lower():
                    _ensure_users_theme_mode_column(conn)
                    if new_password:
                        conn.execute(
                            "UPDATE users SET username=?, password_hash=?, ui_language=?, search_language=? WHERE id=?",
                            (
                                new_username,
                                generate_password_hash(new_password),
                                ui_language,
                                search_language,
                                current_user.id,
                            ),
                        )
                    else:
                        conn.execute(
                            "UPDATE users SET username=?, ui_language=?, search_language=? WHERE id=?",
                            (new_username, ui_language, search_language, current_user.id),
                        )
                    conn.commit()
                else:
                    raise

        try:
            current_user.username = new_username
            current_user.ui_language = ui_language
            current_user.search_language = search_language
        except Exception:
            pass

        return jsonify(
            {
                "ok": True,
                "item": {
                    "id": int(current_user.id),
                    "username": new_username,
                    "role": getattr(current_user, "role", "user"),
                    "ui_language": ui_language,
                    "search_language": search_language,
                    "theme_mode": theme_mode,
                },
            }
        )
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "error": "username_exists"}), 409
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/me/2fa", methods=["GET", "POST"])
@login_required
def api_me_2fa():
    # fetch current state
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT totp_secret, totp_enabled, totp_remember_days FROM users WHERE id=?",
            (current_user.id,),
        ).fetchone()
    secret = row["totp_secret"] if row else None
    enabled = bool(row["totp_enabled"] or 0) if row else False
    remember_days = int(row["totp_remember_days"] or 0) if row else 0

    if request.method == "GET":
        # Only show secret/QR during initial setup (not enabled yet)
        qr_url = None
        secret_out = None
        if not enabled:
            if not secret:
                secret = pyotp.random_base32()
                with closing(get_conn()) as conn:
                    conn.execute("UPDATE users SET totp_secret=? WHERE id=?", (secret, current_user.id))
                    conn.commit()
            issuer = "FjordLens"
            user_label = f"{issuer}:{current_user.username}"
            otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user_label, issuer_name=issuer)
            img = qrcode.make(otp_uri)
            buf = io.BytesIO()
            img.save(buf, "PNG")
            qr_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
            secret_out = secret
        return jsonify({
            "ok": True,
            "enabled": enabled,
            "remember_days": remember_days,
            "secret": secret_out,  # null when enabled
            "qr": qr_url,          # null when enabled
            "user": current_user.username,
        })

    # POST: actions
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()
    code = (data.get("code") or "").strip()
    days = int(data.get("days") or 0)

    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT totp_secret, totp_enabled, totp_remember_days FROM users WHERE id=?",
            (current_user.id,),
        ).fetchone()
    secret = row["totp_secret"] if row else None
    if not secret:
        secret = pyotp.random_base32()
        with closing(get_conn()) as conn:
            conn.execute("UPDATE users SET totp_secret=? WHERE id=?", (secret, current_user.id))
            conn.commit()

    if action == "regen":
        # Regenerate secret; if already enabled, require current valid code to rotate
        if enabled:
            if not pyotp.TOTP(secret).verify(code, valid_window=1):
                return jsonify({"ok": False, "error": "invalid_code"}), 400
        secret = pyotp.random_base32()
        with closing(get_conn()) as conn:
            conn.execute("UPDATE users SET totp_secret=?, totp_enabled=0, totp_setup_done=0 WHERE id=?", (secret, current_user.id))
            conn.commit()
        issuer = "FjordLens"
        user_label = f"{issuer}:{current_user.username}"
        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user_label, issuer_name=issuer)
        img = qrcode.make(otp_uri)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        return jsonify({"ok": True, "qr": data_url})

    if action in {"enable", "disable", "remember", "save"}:
        if not pyotp.TOTP(secret).verify(code, valid_window=1):
            return jsonify({"ok": False, "error": "invalid_code"}), 400
        with closing(get_conn()) as conn:
            if action == "disable":
                conn.execute("UPDATE users SET totp_enabled=0 WHERE id=?", (current_user.id,))
            elif action in {"enable", "save", "remember"}:
                days = max(0, min(30, int(days or 0)))
                conn.execute("UPDATE users SET totp_enabled=1, totp_setup_done=1, totp_remember_days=? WHERE id=?", (days, current_user.id))
            conn.commit()
        return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "unknown_action"}), 400


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
