class Localizer:
    current_lang = "en"

    _strings = {
        "app_title": {
            "en": "CSearch",
            "de": "CSearch"
        },
        "search_path": {
            "en": "Search path:",
            "de": "Suchpfad:"
        },
        "browse": {
            "en": "Browse...",
            "de": "Durchsuchen..."
        },
        "extensions": {
            "en": "File extensions:",
            "de": "Dateierweiterungen:"
        },
        "ext_placeholder": {
            "en": "e.g. pdf, txt, odt, docx, xml (empty = all)",
            "de": "z.B. pdf, txt, odt, docx, xml (leer = alle)"
        },
        "ext_tooltip": {
            "en": "Comma-separated list. Dots and spaces are ignored.",
            "de": "Kommagetrennte Liste. Punkte und Leerzeichen werden ignoriert."
        },
        "search_filename": {
            "en": "Search terms (file name):",
            "de": "Suchbegriffe (Dateiname):"
        },
        "filename_placeholder": {
            "en": "Term1, Term2, ...",
            "de": "Begriff1, Begriff2, ..."
        },
        "filename_tooltip": {
            "en": "Separate multiple words with commas. Files that contain ALL words will be found.\n"+
                  "Order of words is disregarded.",
            "de": "Mehrere Wörter mit Komma trennen. Dateien, die ALLE Wörter enthalten, werden gefunden.\n"+
                    "Reihenfolge der Wörter wird nicht berücksichtigt."
        },
        "search_content": {
            "en": "Search terms (file content):",
            "de": "Suchbegriffe (Dateiinhalt):"
        },
        "content_placeholder": {
            "en": "Term1, Term2, ...",
            "de": "Begriff1, Begriff2, ..."
        },
        "content_tooltip": {
            "en": "Separate multiple words with commas. File that contain ALL words will be found.\n"+
                  "Order of words is disregarded.",
            "de": "Mehrere Wörter mit Komma trennen. Dateien, die ALLE Wörter enthalten, werden gefunden.\n"+
                    "Reihenfolge der Wörter wird nicht berücksichtigt."
        },
        "subfolders": {
            "en": "Search subfolders",
            "de": "Unterordner durchsuchen"
        },
        "ignore_case": {
            "en": "Ignore case",
            "de": "Groß-/Kleinschreibung ignorieren"
        },
        "start_search": {
            "en": "Start search",
            "de": "Suche starten"
        },
        "header_name": {
            "en": "Name",
            "de": "Name"
        },
        "header_modified": {
            "en": "Modified",
            "de": "Geändert"
        },
        "header_folder": {
            "en": "Folder",
            "de": "Ordner"
        },
        "header_matches": {
            "en": "Matches",
            "de": "Treffer"
        },
        "search_running": {
            "en": "Search in progress",
            "de": "Suche läuft"
        },
        "search_completed": {
            "en": "Search completed. {0} matches in {1}s.",
            "de": "Suche abgeschlossen. {0} Treffer in {1}s."
        },
        "search_canceled": {
            "en": "Search canceled.",
            "de": "Suche abgebrochen."
        },
        "invalid_path": {
            "en": "Directory was not found!",
            "de": "Ordner wurde nicht gefunden!"
        },
        "error": {
            "en": "Error",
            "de": "Fehler"
        },
        "warning": {
            "en": "Warning",
            "de": "Warnung"
        },
        "file_not_found": {
            "en": "The file could not be found.",
            "de": "Die Datei konnte nicht gefunden werden."
        },
        "line_truncated": {
            "en": " ... [Line truncated]",
            "de": " ... [Zeile gekürzt]"
        },
        "lines_hidden": {
            "en": "<i>... further lines hidden (file too large)</i>",
            "de": "<i>... weitere Zeilen ausgeblendet (Datei zu groß)</i>"
        },
        "filename_match": {
            "en": "<Filename Match>",
            "de": "<Dateiname Match>"
        },
        "page": {
            "en": "Page",
            "de": "Seite"
        },
        "line": {
            "en": "Line",
            "de": "Zeile"
        },
        "cancel": {
            "en": "Cancel",
            "de": "Abbrechen"
        },
        "open_files": {
            "en": "Open ({0} files)",
            "de": "Öffnen ({0} Dateien)"
        },
        "open": {
            "en": "Open",
            "de": "Öffnen"
        },
        "open_with": {
            "en": "Open with...",
            "de": "Öffnen mit..."
        },
        "open_folder": {
            "en": "Open folder",
            "de": "Ordner öffnen"
        },
        "open_folder_all": {
            "en": "Open folder (all)",
            "de": "Ordner öffnen (alle)"
        },
        "copy_path": {
            "en": "Copy path",
            "de": "Pfad kopieren"
        },
        "copy_paths": {
            "en": "Copy paths",
            "de": "Pfade kopieren"
        },
        "paths_copied": {
            "en": "{0} path(s) copied.",
            "de": "{0} Pfad(e) kopiert."
        },
        "open_multiple_warning": {
            "en": "Do you really want to open {0} files simultaneously?",
            "de": "Möchtest du wirklich {0} Dateien gleichzeitig öffnen?"
        },
        "select_folder": {
            "en": "Select folder",
            "de": "Ordner wählen"
        },
        "search_app": {
            "en": "Search application...",
            "de": "Programm suchen..."
        },
        "program_start_error": {
            "en": "Program could not be started:\n{0}",
            "de": "Programm konnte nicht gestartet werden:\n{0}"
        },
        "clipboard_msg": {
            "en": "Page {0} opened. Search term in clipboard.",
            "de": "Seite {0} geöffnet. Suchwort in Zwischenablage."
        },
        "empty_search_terms": {
            "en": "Please enter at least one search term (file name or content).",
            "de": "Bitte gib mindestens einen Suchbegriff ein (Dateiname oder Inhalt)."
        }
    }

    @classmethod
    def set_language(cls, locale_name):
        if locale_name.startswith("de"):
            cls.current_lang = "de"
        else:
            cls.current_lang = "en"

    @classmethod
    def get(cls, key, *args):
        entry = cls._strings.get(key, {})
        text = entry.get(cls.current_lang, entry.get("en", f"[{key}]"))
        if args:
            return text.format(*args)
        return text