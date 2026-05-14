"""Core helpers for scanning, cleaning and saving audio metadata."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path
import re
import shutil
import subprocess
from typing import Iterable

try:
    from mutagen import File as MutagenFile
except ModuleNotFoundError:  # pragma: no cover - exercised only without optional dependency
    MutagenFile = None

AUDIO_EXTENSIONS = {
    ".3gp",
    ".aac",
    ".aif",
    ".aiff",
    ".alac",
    ".ape",
    ".asf",
    ".dff",
    ".dsf",
    ".flac",
    ".m4a",
    ".m4b",
    ".m4p",
    ".mka",
    ".mkv",
    ".mp2",
    ".mp3",
    ".mp4",
    ".oga",
    ".ogg",
    ".opus",
    ".spx",
    ".tta",
    ".wav",
    ".weba",
    ".webm",
    ".wma",
    ".wv",
}

FFMPEG_METADATA_EXTENSIONS = {".mka", ".mkv", ".weba", ".webm"}

COMMON_AUDIO_KEYS = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "albumartist",
    "year": "date",
    "genre": "genre",
    "track_number": "tracknumber",
}

FFMPEG_METADATA_KEYS = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "album_artist",
    "year": "date",
    "genre": "genre",
    "track_number": "track",
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


def editable_values(track: Track) -> dict[str, str]:
    """Return the editable fields in a format shared by all tag writers."""

    return {
        "title": track.title,
        "artist": track.artist,
        "album": track.album,
        "album_artist": track.album_artist,
        "year": track.year,
        "genre": track.genre,
        "track_number": track.track_number,
    }


def is_ffmpeg_metadata_file(path: Path) -> bool:
    """Return whether a file should fall back to ffmpeg for tag writing."""

    return path.suffix.lower() in FFMPEG_METADATA_EXTENSIONS


def temporary_output_path(path: Path) -> Path:
    """Return a non-existing temporary output path next to the original file."""

    for index in range(1000):
        suffix = "" if index == 0 else f"-{index}"
        candidate = path.with_name(f".{path.stem}.musica-tmp{suffix}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"No s'ha pogut crear un nom temporal per a: {path}")


def save_track_with_ffmpeg(track: Track) -> None:
    """Write metadata by remuxing WebM/Matroska files with ffmpeg."""

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "Per desar metadades en fitxers WebM/Matroska cal tenir ffmpeg instal·lat "
            "i disponible al PATH. Instal·la ffmpeg o converteix el fitxer a MP3/FLAC/M4A."
        )

    output_path = temporary_output_path(track.path)
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(track.path),
        "-map",
        "0",
        "-c",
        "copy",
    ]
    values = editable_values(track)
    for field_name, metadata_key in FFMPEG_METADATA_KEYS.items():
        command.extend(["-metadata", f"{metadata_key}={values[field_name].strip()}"])
    command.append(str(output_path))

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        output_path.replace(track.path)
    except subprocess.CalledProcessError as exc:
        output_path.unlink(missing_ok=True)
        details = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(f"ffmpeg no ha pogut desar les metadades de {track.path}: {details}") from exc
    except Exception:
        output_path.unlink(missing_ok=True)
        raise


def save_track(track: Track) -> None:
    """Write the current metadata to an audio file."""

    if MutagenFile is None:
        if is_ffmpeg_metadata_file(track.path):
            save_track_with_ffmpeg(track)
            return
        raise RuntimeError("Instal·la la dependència 'mutagen' per desar metadades d'àudio.")
    audio = MutagenFile(track.path, easy=True)
    if audio is None:
        if is_ffmpeg_metadata_file(track.path):
            save_track_with_ffmpeg(track)
            return
        raise ValueError(f"No es pot llegir el fitxer d'àudio: {track.path}")
    if audio.tags is None:
        audio.add_tags()

    values = editable_values(track)
    for field_name, tag_key in COMMON_AUDIO_KEYS.items():
        value = values[field_name].strip()
        if value:
            audio.tags[tag_key] = [value]
        elif tag_key in audio.tags:
            del audio.tags[tag_key]
    try:
        audio.save()
    except Exception:
        if is_ffmpeg_metadata_file(track.path):
            save_track_with_ffmpeg(track)
            return
        raise


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


def move_track(tracks: Iterable[Track], source_index: int, target_index: int) -> list[Track]:
    """Return tracks with one item moved to a new visible position.

    The target index is the final position the source track should occupy after
    the move, matching the drag-and-drop behavior in the table.
    """

    track_list = list(tracks)
    if not track_list:
        return []
    if source_index < 0 or source_index >= len(track_list):
        raise IndexError("source_index fora de rang")
    if target_index < 0 or target_index >= len(track_list):
        raise IndexError("target_index fora de rang")
    if source_index == target_index:
        return track_list

    track = track_list.pop(source_index)
    track_list.insert(target_index, track)
    return track_list


def renumber_tracks(tracks: Iterable[Track], start: int = 1, total: bool = True) -> list[Track]:
    """Return new tracks numbered according to their current order."""

    track_list = list(tracks)
    count = len(track_list)
    updated: list[Track] = []
    for index, track in enumerate(track_list, start=start):
        number = f"{index}/{count}" if total else str(index)
        updated.append(replace(track, track_number=number))
    return updated
