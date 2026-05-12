"""Core helpers for scanning, cleaning and saving audio metadata."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path
import re
from typing import Iterable

try:
    from mutagen import File as MutagenFile
except ModuleNotFoundError:  # pragma: no cover - exercised only without optional dependency
    MutagenFile = None

AUDIO_EXTENSIONS = {
    ".aac",
    ".aiff",
    ".alac",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".opus",
    ".wav",
    ".wma",
}

COMMON_AUDIO_KEYS = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "albumartist",
    "year": "date",
    "genre": "genre",
    "track_number": "tracknumber",
}


@dataclass(slots=True)
class Track:
    """Editable metadata for one audio track."""

    path: Path
    title: str = ""
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    year: str = ""
    genre: str = ""
    track_number: str = ""

    @property
    def filename(self) -> str:
        return self.path.name


@dataclass(slots=True)
class BulkMetadata:
    """Values that can be applied to many tracks at once.

    Empty values are ignored so users can update only the fields they need.
    """

    artist: str = ""
    album: str = ""
    album_artist: str = ""
    year: str = ""
    genre: str = ""


def is_audio_file(path: Path) -> bool:
    """Return whether a path looks like a supported audio file."""

    return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS


def discover_audio_files(folder: Path, recursive: bool = False) -> list[Path]:
    """Find audio files in a folder, sorted by name for predictable ordering."""

    pattern = "**/*" if recursive else "*"
    return sorted(
        (path for path in folder.glob(pattern) if is_audio_file(path)),
        key=lambda path: path.name.lower(),
    )


def first_tag_value(audio, key: str) -> str:
    """Return the first string value for a mutagen easy tag key."""

    if audio is None or audio.tags is None:
        return ""
    value = audio.tags.get(key, [])
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def title_from_filename(path: Path) -> str:
    """Create a readable title from a filename when metadata is missing."""

    title = path.stem.replace("_", " ").strip()
    title = re.sub(r"\s+", " ", title)
    return title


def load_track(path: Path) -> Track:
    """Read editable metadata from one audio file.

    If a file has no title tag, the filename stem is used as a practical default.
    """

    if MutagenFile is None:
        raise RuntimeError("Instal·la la dependència 'mutagen' per llegir metadades d'àudio.")
    audio = MutagenFile(path, easy=True)
    title = first_tag_value(audio, COMMON_AUDIO_KEYS["title"]) or title_from_filename(path)
    return Track(
        path=path,
        title=title,
        artist=first_tag_value(audio, COMMON_AUDIO_KEYS["artist"]),
        album=first_tag_value(audio, COMMON_AUDIO_KEYS["album"]),
        album_artist=first_tag_value(audio, COMMON_AUDIO_KEYS["album_artist"]),
        year=first_tag_value(audio, COMMON_AUDIO_KEYS["year"]),
        genre=first_tag_value(audio, COMMON_AUDIO_KEYS["genre"]),
        track_number=first_tag_value(audio, COMMON_AUDIO_KEYS["track_number"]),
    )


def save_track(track: Track) -> None:
    """Write the current metadata to an audio file."""

    if MutagenFile is None:
        raise RuntimeError("Instal·la la dependència 'mutagen' per desar metadades d'àudio.")
    audio = MutagenFile(track.path, easy=True)
    if audio is None:
        raise ValueError(f"No es pot llegir el fitxer d'àudio: {track.path}")
    if audio.tags is None:
        audio.add_tags()

    values = {
        "title": track.title,
        "artist": track.artist,
        "album": track.album,
        "album_artist": track.album_artist,
        "year": track.year,
        "genre": track.genre,
        "track_number": track.track_number,
    }
    for field_name, tag_key in COMMON_AUDIO_KEYS.items():
        value = values[field_name].strip()
        if value:
            audio.tags[tag_key] = [value]
        elif tag_key in audio.tags:
            del audio.tags[tag_key]
    audio.save()


def clean_repeated_fragment(title: str, fragment: str, case_sensitive: bool = False) -> str:
    """Remove a repeated downloader/source fragment from a title.

    Surrounding separators commonly left in downloaded filenames are normalized too,
    so ``Maneras de Vivir_JPdownloader`` becomes ``Maneras de Vivir``.
    """

    fragment = fragment.strip()
    if not fragment:
        return title.strip()

    flags = 0 if case_sensitive else re.IGNORECASE
    cleaned = re.sub(re.escape(fragment), "", title, flags=flags)
    cleaned = re.sub(r"[\s._\-–—]+$", "", cleaned)
    cleaned = re.sub(r"^[\s._\-–—]+", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    return cleaned.strip()


def apply_fragment_cleanup(
    tracks: Iterable[Track], fragment: str, case_sensitive: bool = False
) -> list[Track]:
    """Return new tracks with the fragment removed from every title."""

    return [
        replace(
            track,
            title=clean_repeated_fragment(track.title, fragment, case_sensitive),
        )
        for track in tracks
    ]


def apply_bulk_metadata(tracks: Iterable[Track], metadata: BulkMetadata) -> list[Track]:
    """Apply non-empty album-wide metadata values to each track."""

    replacements = {
        field.name: getattr(metadata, field.name).strip()
        for field in fields(metadata)
        if getattr(metadata, field.name).strip()
    }
    return [replace(track, **replacements) for track in tracks]


def renumber_tracks(tracks: Iterable[Track], start: int = 1, total: bool = True) -> list[Track]:
    """Return new tracks numbered according to their current order."""

    track_list = list(tracks)
    count = len(track_list)
    updated: list[Track] = []
    for index, track in enumerate(track_list, start=start):
        number = f"{index}/{count}" if total else str(index)
        updated.append(replace(track, track_number=number))
    return updated
