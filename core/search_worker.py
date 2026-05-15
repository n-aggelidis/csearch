import os
import re
import time
import subprocess
import html
import signal
import zipfile
from PyQt6 import QtCore

from .localizer import Localizer

class SearchWorker(QtCore.QThread):
    """ Background thread for executing the search """
    # Emits float timestamp instead of formatted date string
    match_found_signal = QtCore.pyqtSignal(str, str, str, float, str, str, int)
    finished_signal = QtCore.pyqtSignal(bool, float, str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_cancelled = False
        self.active_process = None

    def cancel(self):
        self.is_cancelled = True
        if self.active_process:
            try:
                # Terminate entire process group
                os.killpg(os.getpgid(self.active_process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass  # Process already dead
            except Exception as e:
                # Fallback if process groups are unsupported
                print(f"Warning while terminating process group: {e}")
                self.active_process.terminate()

    def filter_files(self, base_cmd, files, terms):
        current_files = files
        for term in terms:
            if not current_files or self.is_cancelled:
                return []
            next_files = []
            for i in range(0, len(current_files), 500):
                if self.is_cancelled: break
                chunk = current_files[i:i + 500]
                cmd = base_cmd + ["-l"]
                if self.params['ignore_case']: cmd.append("-i")
                cmd.extend(["--", term])
                cmd.extend(chunk)
                res = subprocess.run(
                    cmd, capture_output=True, text=True, errors='replace',
                    start_new_session=True
                )
                if res.stdout:
                    lines = [line.strip() for line in res.stdout.strip().split('\n') if line.strip()]
                    next_files.extend(lines)
            current_files = next_files
        return current_files

    def run(self):
        start_time = time.time()
        try:
            pdf_files = []
            other_files = []
            odt_files = []
            docx_files = []

            for root, dirs, files in os.walk(self.params['path']):
                if self.is_cancelled: break
                if not self.params['subfolders'] and root != self.params['path']: continue

                for file in files:
                    if self.params['extensions'] and not any(file.lower().endswith(ext) for ext in self.params['extensions']):
                        continue

                    file_lower = file.lower()
                    if not all(term in file_lower for term in self.params['filename_terms']):
                        continue

                    full_path = os.path.join(root, file)
                    if file_lower.endswith('.pdf'):
                        pdf_files.append(full_path)
                    elif file_lower.endswith('.odt'):
                        odt_files.append(full_path)
                    elif file_lower.endswith('.docx'):
                        docx_files.append(full_path)
                    else:
                        other_files.append(full_path)

            terms = self.params['content_terms']
            if not terms:
                for f in (pdf_files + odt_files + docx_files + other_files):
                    if self.is_cancelled: break
                    self.emit_file_only(f)
                self.finished_signal.emit(True, time.time() - start_time, "")
                return

            # Apply file-level AND filtering
            if len(terms) > 1:
                if other_files: other_files = self.filter_files(["rga"], other_files, terms)
                if pdf_files: pdf_files = self.filter_files(["pdfgrep"], pdf_files, terms)
                if odt_files: odt_files = self.filter_odt_files(odt_files, terms)
                if docx_files: docx_files = self.filter_docx_files(docx_files, terms)

            # Extract matches using OR regex for display
            regex = re.escape(terms[0]) if len(terms) == 1 else "|".join([re.escape(t) for t in terms])

            if other_files:
                self.run_grep(["rga", "-P", "-H", "-n", "-C", "8"], regex, other_files)
            if pdf_files:
                # pdfgrep uses -C for line context (v2.0+)
                self.run_grep(["pdfgrep", "-P", "-H", "-n", "-C", "8"], regex, pdf_files)
            if odt_files:
                self.run_native_zip_grep(regex, odt_files, "odt")
            if docx_files:
                self.run_native_zip_grep(regex, docx_files, "docx")

            elapsed = time.time() - start_time
            self.finished_signal.emit(not self.is_cancelled, elapsed, Localizer.get("search_canceled"))

        except Exception as e:
            self.finished_signal.emit(False, time.time() - start_time, str(e))

    def emit_file_only(self, filepath):
        fn, frel, mod = self.get_file_meta(filepath)
        self.match_found_signal.emit(filepath, fn, frel, mod, Localizer.get("filename_match"), "",1)

    def get_file_meta(self, filepath):
        file_name = os.path.basename(filepath)
        folder_rel = os.path.relpath(os.path.dirname(filepath), self.params['path'])
        folder_rel = "/" if folder_rel == "." else f"/{folder_rel}"
        
        try:
            mod_date = os.path.getmtime(filepath)
        except:
            mod_date = 0.0

        return file_name, folder_rel, mod_date

    def run_grep(self, base_cmd, regex, file_list):
        if self.params['ignore_case']: base_cmd.append("-i")
        base_cmd.extend(["--", regex])

        line_regex = re.compile(r'^(.*?)([:-])(\d+)\2(.*)$')

        for i in range(0, len(file_list), 500):
            if self.is_cancelled: break
            chunk = file_list[i:i + 500]
            self.active_process = subprocess.Popen(
                base_cmd + chunk, stdout=subprocess.PIPE, text=True, errors='replace',
                start_new_session=True
            )

            current_filepath = None
            all_match_lines = []  # Only lines with matches for the table
            full_context_buffer = []  # Full context for tooltip
            first_lno = 1  # Default page number
            current_pfx = ""

            def emit_current():
                if current_filepath and all_match_lines:
                    fn, frel, mod = self.get_file_meta(current_filepath)
                    table_text = " | ".join(all_match_lines)
                    tooltip_text = "\n".join(full_context_buffer)
                    # Append page number (first_lno) as integer
                    self.match_found_signal.emit(current_filepath, fn, frel, mod, table_text, tooltip_text,
                                                 int(first_lno))

            # Single loop for parsing data stream
            for line in self.active_process.stdout:
                if self.is_cancelled: break
                line = line.strip('\n')
                if line == '--':
                    full_context_buffer.append("-" * 30)
                    continue

                m = line_regex.match(line)
                if m:
                    fp, s1, lno, cont = m.groups()

                    if current_filepath != fp:
                        if current_filepath:
                            emit_current()

                        all_match_lines, full_context_buffer = [], []
                        current_filepath = fp
                        first_lno = lno
                        
                        is_pdf = fp.lower().endswith('.pdf')
                        current_pfx = Localizer.get("page") if is_pdf else Localizer.get("line")
                    elif not all_match_lines:
                        first_lno = lno

                    prefix = f"▶ {current_pfx}" if s1 == ':' else f"  {current_pfx}"
                    if s1 == ':':
                        all_match_lines.append(cont.strip())
                    
                    full_context_buffer.append(f"{prefix} {lno}: {cont.strip()}")

            # Send final remaining match after loop
            emit_current()

    def get_clean_zip_text(self, filepath, file_type):
        """ Extracts text from ODT or DOCX files """
        try:
            text_parts = []
            is_odt = file_type == 'odt'

            with zipfile.ZipFile(filepath, 'r') as z:
                for filename in z.namelist():
                    # Filter logic for relevant XML files
                    relevant = filename.endswith('.xml') and (is_odt or filename.startswith('word/'))

                    if relevant:
                        data = z.read(filename).decode('utf-8', errors='replace')

                        # Format-specific line breaks
                        if is_odt:
                            data = data.replace('</text:p>', '\n').replace('</text:h>', '\n')
                        else:
                            data = data.replace('</w:p>', '\n').replace('<w:br/>', '\n')

                        # Generic cleanup
                        data = html.unescape(re.sub(r'<[^>]*>', '', data))
                        text_parts.append(data)

            return "\n".join(text_parts)
        except Exception:
            return ""

    def run_native_zip_grep(self, regex, file_list, file_type):
        """ Searches text within ODT or DOCX files natively """
        flags = re.IGNORECASE if self.params['ignore_case'] else 0
        pattern = re.compile(regex, flags)

        for filepath in file_list:
            if self.is_cancelled: break

            clean_text = self.get_clean_zip_text(filepath, file_type)
            if not clean_text: continue

            lines = clean_text.split('\n')
            all_match_lines = []
            full_context_buffer = []

            # Find line numbers containing matches
            match_indices = []
            for i, line in enumerate(lines):
                if pattern.search(line):
                    match_indices.append(i)

            if not match_indices:
                continue

            # Collect matches for table view
            for i in match_indices:
                all_match_lines.append(lines[i].strip())

            # Build context tooltip (simulates -C 8 of rg)
            last_printed = -1
            pfx = Localizer.get("line")

            for i in match_indices:
                start = max(0, i - 8)
                end = min(len(lines), i + 9)

                # Insert separator for gaps between match blocks
                if start > last_printed + 1 and last_printed != -1:
                    full_context_buffer.append("-" * 30)

                for j in range(max(start, last_printed + 1), end):
                    line_text = lines[j].strip()

                    # Ignore empty XML lines in context for clarity
                    if not line_text and j not in match_indices:
                        continue

                    if j in match_indices:
                        full_context_buffer.append(f"▶ {pfx} {j + 1}: {line_text}")
                    else:
                        full_context_buffer.append(f"  {pfx} {j + 1}: {line_text}")

                last_printed = end - 1

            # Send to GUI
            if all_match_lines:
                fn, frel, mod = self.get_file_meta(filepath)
                table_text = " | ".join(all_match_lines)
                tooltip_text = "\n".join(full_context_buffer)
                self.match_found_signal.emit(filepath, fn, frel, mod, table_text, tooltip_text, 1)

    def filter_odt_files(self, file_list, terms):
        """ Fast pre-filtering entirely in RAM """
        valid_files = []
        for filepath in file_list:
            if self.is_cancelled: break

            content = self.get_clean_zip_text(filepath, "odt")
            if not content: continue

            if self.params['ignore_case']:
                content = content.lower()

            # Check if all search terms are present
            if all((t.lower() if self.params['ignore_case'] else t) in content for t in terms):
                valid_files.append(filepath)
        return valid_files


    def filter_docx_files(self, file_list, terms):
        """ Fast pre-filtering entirely in RAM """
        valid_files = []
        for filepath in file_list:
            if self.is_cancelled: break
            content = self.get_clean_zip_text(filepath, "docx")
            if not content: continue
            if self.params['ignore_case']: content = content.lower()
            if all((t.lower() if self.params['ignore_case'] else t) in content for t in terms):
                valid_files.append(filepath)
        return valid_files
