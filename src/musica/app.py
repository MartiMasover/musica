"""Tkinter desktop app for bulk audio metadata editing."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .metadata import (
    BulkMetadata,
    Track,
    apply_bulk_metadata,
    apply_fragment_cleanup,
    discover_audio_files,
    load_track,
    move_track,
    renumber_tracks,
    save_track,
)

COLUMNS = ("track", "title", "artist", "album", "year", "genre", "file")


class MusicaApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Musica - Editor massiu de metadades")
        self.geometry("1180x720")
        self.minsize(980, 560)

        self.folder = tk.StringVar(value="")
        self.recursive = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Selecciona una carpeta amb pistes d'àudio.")
        self.cleanup_fragment = tk.StringVar(value="")
        self.case_sensitive_cleanup = tk.BooleanVar(value=False)
        self.album = tk.StringVar(value="")
        self.artist = tk.StringVar(value="")
        self.album_artist = tk.StringVar(value="")
        self.year = tk.StringVar(value="")
        self.genre = tk.StringVar(value="")
        self.start_number = tk.IntVar(value=1)
        self.include_total = tk.BooleanVar(value=True)
        self.edit_vars = {
            "title": tk.StringVar(value=""),
            "artist": tk.StringVar(value=""),
            "album": tk.StringVar(value=""),
            "album_artist": tk.StringVar(value=""),
            "year": tk.StringVar(value=""),
            "genre": tk.StringVar(value=""),
            "track_number": tk.StringVar(value=""),
        }
        self.tracks: list[Track] = []
        self.selected_index: int | None = None
        self.drag_source_index: int | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, padding=10)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Button(top, text="Selecciona carpeta…", command=self.choose_folder).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Entry(top, textvariable=self.folder, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Checkbutton(top, text="Inclou subcarpetes", variable=self.recursive).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(top, text="Escaneja", command=self.scan_folder).grid(row=0, column=3)

        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        left = ttk.Frame(main)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        main.add(left, weight=3)

        self.tree = ttk.Treeview(left, columns=COLUMNS, show="headings", selectmode="browse")
        headings = {
            "track": "#",
            "title": "Títol",
            "artist": "Intèrpret",
            "album": "Àlbum",
            "year": "Any",
            "genre": "Gènere",
            "file": "Fitxer",
        }
        widths = {
            "track": 65,
            "title": 240,
            "artist": 170,
            "album": 190,
            "year": 70,
            "genre": 110,
            "file": 260,
        }
        for column in COLUMNS:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor=tk.W)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_release)

        scrollbar = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        reorder = ttk.Frame(left, padding=(0, 8, 0, 0))
        reorder.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Label(reorder, text="Reordena arrossegant una pista amb el ratolí o usa els botons:").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(reorder, text="Puja", command=lambda: self.move_selected(-1)).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(reorder, text="Baixa", command=lambda: self.move_selected(1)).grid(
            row=0, column=2, padx=(4, 0)
        )

        right = ttk.Notebook(main)
        main.add(right, weight=1)

        bulk_tab = ttk.Frame(right, padding=12)
        edit_tab = ttk.Frame(right, padding=12)
        right.add(bulk_tab, text="Canvis massius")
        right.add(edit_tab, text="Pista seleccionada")
        self._build_bulk_tab(bulk_tab)
        self._build_edit_tab(edit_tab)

        bottom = ttk.Frame(self, padding=(10, 0, 10, 10))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        ttk.Label(bottom, textvariable=self.status).grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text="Desa metadades", command=self.save_all).grid(
            row=0, column=1, padx=(8, 0)
        )

    def _build_bulk_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        row = 0
        ttk.Label(parent, text="Dades comunes de l'àlbum", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        row += 1
        for label, variable in (
            ("Àlbum", self.album),
            ("Intèrpret", self.artist),
            ("Artista de l'àlbum", self.album_artist),
            ("Any", self.year),
            ("Gènere", self.genre),
        ):
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)
            row += 1
        ttk.Button(parent, text="Aplica als fitxers carregats", command=self.apply_bulk).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(8, 16)
        )
        row += 1

        ttk.Separator(parent).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Label(parent, text="Neteja de títols", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        row += 1
        ttk.Label(parent, text="Text a eliminar").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=self.cleanup_fragment).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        ttk.Checkbutton(
            parent,
            text="Diferencia majúscules/minúscules",
            variable=self.case_sensitive_cleanup,
        ).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        ttk.Button(parent, text="Elimina aquest text de tots els títols", command=self.clean_titles).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(8, 16)
        )
        row += 1

        ttk.Separator(parent).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Label(parent, text="Numeració", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        row += 1
        ttk.Label(parent, text="Comença a").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Spinbox(parent, from_=1, to=999, textvariable=self.start_number, width=8).grid(
            row=row, column=1, sticky="w", pady=3
        )
        row += 1
        ttk.Checkbutton(parent, text="Inclou total (1/12)", variable=self.include_total).grid(
            row=row, column=0, columnspan=2, sticky="w"
        )
        row += 1
        ttk.Button(parent, text="Numera segons l'ordre actual", command=self.renumber).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_edit_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        ttk.Label(parent, text="Edita una pista concreta", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        labels = {
            "title": "Títol",
            "artist": "Intèrpret",
            "album": "Àlbum",
            "album_artist": "Artista de l'àlbum",
            "year": "Any",
            "genre": "Gènere",
            "track_number": "Número de pista",
        }
        for row, (field, label) in enumerate(labels.items(), start=1):
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(parent, textvariable=self.edit_vars[field]).grid(
                row=row, column=1, sticky="ew", pady=3
            )
        ttk.Button(parent, text="Aplica a la pista seleccionada", command=self.apply_selected_edit).grid(
            row=len(labels) + 1, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecciona la carpeta amb les pistes")
        if folder:
            self.folder.set(folder)
            self.scan_folder()

    def scan_folder(self) -> None:
        folder_value = self.folder.get()
        if not folder_value:
            messagebox.showinfo("Cap carpeta", "Selecciona una carpeta abans d'escanejar.")
            return
        folder = Path(folder_value)
        if not folder.exists():
            messagebox.showerror("Carpeta no trobada", f"No existeix: {folder}")
            return
        try:
            files = discover_audio_files(folder, recursive=self.recursive.get())
            self.tracks = [load_track(path) for path in files]
        except Exception as exc:  # noqa: BLE001 - show actionable GUI error
            messagebox.showerror("Error escanejant", str(exc))
            return
        self.selected_index = None
        self.refresh_table()
        self.status.set(f"S'han carregat {len(self.tracks)} pistes.")

    def refresh_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for index, track in enumerate(self.tracks):
            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    track.track_number,
                    track.title,
                    track.artist,
                    track.album,
                    track.year,
                    track.genre,
                    track.filename,
                ),
            )

    def on_select(self, _event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_index = int(selected[0])
        track = self.tracks[self.selected_index]
        for field, variable in self.edit_vars.items():
            variable.set(getattr(track, field))

    def on_drag_start(self, event: tk.Event) -> None:
        row_id = self.tree.identify_row(event.y)
        self.drag_source_index = int(row_id) if row_id else None

    def on_drag_release(self, event: tk.Event) -> None:
        if self.drag_source_index is None:
            return
        target_id = self.tree.identify_row(event.y)
        source_index = self.drag_source_index
        self.drag_source_index = None
        if not target_id:
            return
        target_index = int(target_id)
        if source_index == target_index:
            return
        self.tracks = move_track(self.tracks, source_index, target_index)
        self.selected_index = target_index
        self.refresh_table()
        self.tree.selection_set(str(target_index))
        self.tree.focus(str(target_index))
        self.status.set(
            "Ordre actualitzat. Prem 'Numera segons l'ordre actual' si vols regenerar els números de pista."
        )

    def move_selected(self, direction: int) -> None:
        if not self.require_tracks():
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Cap selecció", "Selecciona una pista de la taula.")
            return
        source_index = int(selected[0])
        target_index = source_index + direction
        if target_index < 0 or target_index >= len(self.tracks):
            return
        self.tracks = move_track(self.tracks, source_index, target_index)
        self.selected_index = target_index
        self.refresh_table()
        self.tree.selection_set(str(target_index))
        self.tree.focus(str(target_index))
        self.status.set(
            "Ordre actualitzat. Prem 'Numera segons l'ordre actual' si vols regenerar els números de pista."
        )

    def require_tracks(self) -> bool:
        if self.tracks:
            return True
        messagebox.showinfo("Cap pista", "Carrega una carpeta amb pistes abans de fer canvis.")
        return False

    def apply_bulk(self) -> None:
        if not self.require_tracks():
            return
        metadata = BulkMetadata(
            artist=self.artist.get(),
            album=self.album.get(),
            album_artist=self.album_artist.get(),
            year=self.year.get(),
            genre=self.genre.get(),
        )
        self.tracks = apply_bulk_metadata(self.tracks, metadata)
        self.refresh_table()
        self.status.set("Dades comunes aplicades. Revisa-les i prem 'Desa metadades'.")

    def clean_titles(self) -> None:
        if not self.require_tracks():
            return
        fragment = self.cleanup_fragment.get()
        if not fragment.strip():
            messagebox.showinfo("Text buit", "Indica el text repetit que vols eliminar.")
            return
        self.tracks = apply_fragment_cleanup(
            self.tracks,
            fragment,
            case_sensitive=self.case_sensitive_cleanup.get(),
        )
        self.refresh_table()
        self.status.set(f"S'ha eliminat '{fragment}' dels títols carregats.")

    def renumber(self) -> None:
        if not self.require_tracks():
            return
        self.tracks = renumber_tracks(
            self.tracks,
            start=self.start_number.get(),
            total=self.include_total.get(),
        )
        self.refresh_table()
        self.status.set("Pistes numerades segons l'ordre de la taula.")

    def apply_selected_edit(self) -> None:
        if self.selected_index is None:
            messagebox.showinfo("Cap selecció", "Selecciona una pista de la taula.")
            return
        current = self.tracks[self.selected_index]
        self.tracks[self.selected_index] = replace(
            current,
            **{field: variable.get() for field, variable in self.edit_vars.items()},
        )
        self.refresh_table()
        self.tree.selection_set(str(self.selected_index))
        self.status.set("Canvis aplicats a la pista seleccionada.")

    def save_all(self) -> None:
        if not self.require_tracks():
            return
        errors: list[str] = []
        for track in self.tracks:
            try:
                save_track(track)
            except Exception as exc:  # noqa: BLE001 - aggregate per-file GUI errors
                errors.append(f"{track.filename}: {exc}")
        if errors:
            messagebox.showerror("Alguns fitxers no s'han pogut desar", "\n".join(errors[:10]))
            self.status.set(f"S'han desat canvis amb {len(errors)} errors.")
            return
        messagebox.showinfo("Desat", "Metadades desades correctament.")
        self.status.set(f"Metadades desades en {len(self.tracks)} pistes.")


def main() -> None:
    app = MusicaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
