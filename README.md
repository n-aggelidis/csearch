# CSearch

🌐 **English** | 🇩🇪 **Deutsch**

---


A graphical search tool for Linux, written in Python and PyQt6 with an explicit focus on document content search. 
CSearch uses `ripgrep-all` (`rga`) for all generic file types, `pdfgrep` for PDF documents, and a native search algorithm for Office documents (odt/docx).

###  Features

- **Multiple Search Terms**: Multiple search terms can be entered for the filename and file content. It finds all documents containing all search terms, regardless of their order.
- **Broad Format Support:**
  - **Office Documents:** Native, low-RAM, and parallelized search (multithreading) in `.odt` and `.docx` files using the Python `zipfile` module. This enables the search of text that is in the header or footer or some text fields of the documents, which tools like `odt2txt` for example do not support.
  - **PDFs:** Exact page numbers and context output thanks to `pdfgrep`. When opened, the PDF viewer jumps directly to the matched page.
  - **Other Formats:** Source code, log files, archives, E-Books, etc. (everything supported by `ripgrep-all`).
- **Clear Results Table:** Displays the filename, relative folder path, modification date, and a formatted text snippet with the highlighted search term.
- **Smart Context Menu:**
  - Open file / Open multiple files
  - Open containing folder
  - Copy file paths to clipboard
  - Double click to open file in standard application
- **Search History:** The latest search queries and paths are saved and available via dropdown.
- **Localization:** Automatic language detection (German / English).

### Screenshots

*(Hint: You can insert one or two images of your program here later. Just upload them to GitHub and link them here.)*

### Installation & Usage

#### Flatpak

```bash
flatpak install CSearch.flatpak
```

#### AppImage (biuld in Ubuntu 22.04)

```bash
chmod +x CSearch.AppImage
./CSearch.AppImage
```

#### Build Manually

1. Clone the repository:
   ```bash
   git clone https://github.com/n-aggelidis/CSearch.git
   cd CSearch
   ```
2. The following dependencies are required:
   - `python3`
   - `python3-pyqt6` 
   - `rga` (ripgrep-all)
   - `pdfgrep`

3. Start the program:
   ```bash
   python3 main.py
   ```

---

## Deutsch

Ein grafisches Suchwerkzeug (GUI) für Linux, geschrieben in Python und PyQt6 mit explizitem Fokus auf Inhaltssuche in Dokumenten. 
CSearch nutzt `ripgrep-all` (`rga`) für alle generischen Dateitypen, `pdfgrep` für PDF-Dokumente und einen nativen Suchalgorithmus für Office-Dokumente (odt/docx).

###  Features

- **Mehrere Suchbegriffe**: Für den Dateinamen und Dateiinhalt können mehrere Suchbegriffe eingegeben werden. Es werden alle Dokumente gefunden, die alle Suchbegriffe enthalten, wobei die Reihenfolge unerheblich ist.
- **Breite Formatunterstützung:**
  - **Office-Dokumente:** Native, RAM-schonende und parallelisierte Suche (Multithreading) in `.odt` und `.docx` Dateien mithilfe des Python `zipfile`-Moduls. Dies ermöglicht die Suche in der Kopf- und Fußzeile und manchen Textfeldern des Dokuments, die mit Werkzeugen wie `odt2txt` nicht gefunden werden. 
  - **PDFs:** Exakte Seitenzahlen und Kontext-Ausgabe dank `pdfgrep`. Beim Öffnen springt der PDF-Viewer direkt zur Treffer-Seite.
  - **Weitere Formate:** Quellcode, Logfiles, Archive, E-Books etc. (alles, was `ripgrep-all` unterstützt).
- **Übersichtliche Ergebnis-Tabelle:** Zeigt den Dateinamen, den relativen Ordnerpfad, das Änderungsdatum und einen formatierten Text-Ausschnitt mit dem gefundenen Suchwort.
- **Smartes Kontext-Menü:**
  - Datei öffnen / Mehrere Dateien öffnen
  - Beinhaltenden Ordner öffnen.
  - Dateipfade in die Zwischenablage kopieren.
  - Doppelklicken, um Datei im Standardprogramm zu öffnen
- **Such-Historie:** Die letzten Suchanfragen und Pfade werden gespeichert und stehen per Dropdown zur Verfügung.
- **Lokalisierung:** Automatische Spracherkennung (Deutsch / Englisch).

###  Screenshots

*(Tipp: Hier kannst du später ein oder zwei Bilder deines Programms einfügen. Lade sie einfach in GitHub hoch und verlinke sie hier.)*

###  Installation & Start

#### Flatpak

```bash
flatpak install CSearch.flatpak
```

#### AppImage (erstellt in Ubuntu 22.04)

```bash
chmod +x CSearch.AppImage
./CSearch.AppImage
```

#### Manuell bauen

1. Klone das Repository:
   ```bash
   git clone https://github.com/n-aggelidis/CSearch.git
   cd CSearch
   ```
2. Folgende Abhängigkeiten sind notwendig:
   - `python3`
   - `python3-pyqt6` 
   - `rga` (ripgrep-all)
   - `pdfgrep`

3. Programm starten mit:
   ```bash
   python3 main.py
   ```