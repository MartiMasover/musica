from pathlib import Path

from musica.metadata import (
    BulkMetadata,
    Track,
    apply_bulk_metadata,
    apply_fragment_cleanup,
    clean_repeated_fragment,
    renumber_tracks,
    title_from_filename,
)


def test_clean_repeated_fragment_removes_downloader_suffix() -> None:
    assert clean_repeated_fragment("Maneras de Vivir_JPdownloader", "JPdownloader") == "Maneras de Vivir"


def test_clean_repeated_fragment_is_case_insensitive_by_default() -> None:
    assert clean_repeated_fragment("Cançó - jpDOWNLOADER", "JPdownloader") == "Cançó"


def test_title_from_filename_normalizes_underscores_and_spaces() -> None:
    assert title_from_filename(Path("01_Maneras__de_Vivir.mp3")) == "01 Maneras de Vivir"


def test_apply_bulk_metadata_keeps_existing_values_when_input_is_empty() -> None:
    tracks = [Track(Path("song.mp3"), title="Song", artist="Original", album="Old")]

    updated = apply_bulk_metadata(tracks, BulkMetadata(album="New", artist=""))

    assert updated[0].artist == "Original"
    assert updated[0].album == "New"


def test_renumber_tracks_can_include_total() -> None:
    tracks = [Track(Path("a.mp3")), Track(Path("b.mp3"))]

    updated = renumber_tracks(tracks)

    assert [track.track_number for track in updated] == ["1/2", "2/2"]


def test_apply_fragment_cleanup_returns_updated_track_titles() -> None:
    tracks = [Track(Path("a.mp3"), title="A_JPdownloader")]

    updated = apply_fragment_cleanup(tracks, "JPdownloader")

    assert updated[0].title == "A"
