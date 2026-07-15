from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


APP_STYLE = """
QWidget {
    background: #f6f7fb;
    color: #20232a;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow { background: #f6f7fb; }
QGroupBox {
    background: white;
    border: 1px solid #dfe3ea;
    border-radius: 10px;
    margin-top: 12px;
    padding: 14px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
}
QListWidget, QPlainTextEdit, QLineEdit, QComboBox {
    background: white;
    border: 1px solid #cfd5df;
    border-radius: 7px;
    padding: 7px;
}
QListWidget { padding: 5px; }
QListWidget::item { padding: 7px; border-radius: 5px; }
QListWidget::item:selected { background: #dbeafe; color: #172554; }
QPushButton {
    background: white;
    border: 1px solid #cfd5df;
    border-radius: 7px;
    padding: 8px 14px;
}
QPushButton:hover { background: #eef2f7; }
QPushButton:disabled { color: #9aa3b2; background: #f0f2f5; }
QPushButton#primary {
    background: #2563eb;
    color: white;
    border: 1px solid #2563eb;
    font-weight: 600;
}
QPushButton#primary:hover { background: #1d4ed8; }
QPushButton#danger { color: #b42318; }
QProgressBar {
    background: #e8ebf0;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
}
QProgressBar::chunk { background: #2563eb; border-radius: 6px; }
QLabel#title { font-size: 20pt; font-weight: 700; color: #111827; }
QLabel#subtitle { color: #5f6b7a; }
QLabel#privacy {
    background: #ecfdf3;
    color: #166534;
    border: 1px solid #bbf7d0;
    border-radius: 7px;
    padding: 8px;
}
"""


class PdfList(QListWidget):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlternatingRowColors(False)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setMinimumHeight(185)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(
            url.toLocalFile().lower().endswith(".pdf")
            for url in event.mimeData().urls()
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".pdf")
        ]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()


class ConverterWorker(QObject):
    progress = Signal(int, int, str)
    converted = Signal(str, str)
    failed_file = Signal(str, str)
    finished = Signal(int, int, bool)

    def __init__(
        self,
        files: list[str],
        output_dir: str | None,
        ocr_mode: str,
        ocr_language: str,
        include_headers: bool,
        extract_images: bool,
        page_separators: bool,
    ) -> None:
        super().__init__()
        self.files = files
        self.output_dir = Path(output_dir) if output_dir else None
        self.ocr_mode = ocr_mode
        self.ocr_language = ocr_language
        self.include_headers = include_headers
        self.extract_images = extract_images
        self.page_separators = page_separators

    @staticmethod
    def available_path(path: Path) -> Path:
        if not path.exists():
            return path
        index = 2
        while True:
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    @Slot()
    def run(self) -> None:
        import pymupdf4llm

        success = 0
        failed = 0
        cancelled = False
        total = len(self.files)

        for index, source_text in enumerate(self.files, start=1):
            if QThread.currentThread().isInterruptionRequested():
                cancelled = True
                break

            source = Path(source_text)
            self.progress.emit(index, total, source.name)

            try:
                target_dir = self.output_dir or source.parent
                target_dir.mkdir(parents=True, exist_ok=True)
                target = self.available_path(target_dir / f"{source.stem}.md")

                kwargs = {
                    "ocr_language": self.ocr_language,
                    "header": self.include_headers,
                    "footer": self.include_headers,
                    "page_separators": self.page_separators,
                    "show_progress": False,
                }

                if self.ocr_mode == "never":
                    kwargs["use_ocr"] = False
                elif self.ocr_mode == "always":
                    kwargs["use_ocr"] = True
                    kwargs["force_ocr"] = True
                else:
                    kwargs["use_ocr"] = True

                if self.extract_images:
                    image_dir = target_dir / f"{source.stem}_images"
                    image_dir.mkdir(parents=True, exist_ok=True)
                    kwargs["write_images"] = True
                    kwargs["image_path"] = str(image_dir)

                markdown = pymupdf4llm.to_markdown(str(source), **kwargs)
                target.write_text(markdown, encoding="utf-8")
                success += 1
                self.converted.emit(str(source), str(target))
            except Exception as exc:
                failed += 1
                detail = f"{type(exc).__name__}: {exc}"
                self.failed_file.emit(str(source), detail)

        self.finished.emit(success, failed, cancelled)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.thread: QThread | None = None
        self.worker: ConverterWorker | None = None
        self.last_output: Path | None = None
        self.close_when_finished = False

        self.setWindowTitle("Yerel PDF → Markdown")
        self.resize(980, 720)
        self.setMinimumSize(780, 600)
        self.setAcceptDrops(True)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("PDF → Markdown")
        title.setObjectName("title")
        subtitle = QLabel(
            "PDF dosyalarını sürükleyin; Markdown çıktıları tamamen bilgisayarınızda oluşturulsun."
        )
        subtitle.setObjectName("subtitle")
        privacy = QLabel("● Yerel işlem — dosyalarınız internete gönderilmez")
        privacy.setObjectName("privacy")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(privacy)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 6, 0)

        files_group = QGroupBox("PDF dosyaları")
        files_layout = QVBoxLayout(files_group)
        drop_hint = QLabel("Dosyaları buraya sürükleyin veya ‘PDF Ekle’ düğmesini kullanın.")
        drop_hint.setObjectName("subtitle")
        self.file_list = PdfList()
        self.file_list.files_dropped.connect(self.add_files)
        files_layout.addWidget(drop_hint)
        files_layout.addWidget(self.file_list)

        file_buttons = QHBoxLayout()
        self.add_button = QPushButton("PDF Ekle")
        self.remove_button = QPushButton("Seçileni Kaldır")
        self.clear_button = QPushButton("Temizle")
        self.add_button.clicked.connect(self.choose_files)
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.file_list.clear)
        file_buttons.addWidget(self.add_button)
        file_buttons.addWidget(self.remove_button)
        file_buttons.addStretch()
        file_buttons.addWidget(self.clear_button)
        files_layout.addLayout(file_buttons)
        left_layout.addWidget(files_group)

        output_group = QGroupBox("Çıktı")
        output_layout = QVBoxLayout(output_group)
        self.same_folder = QCheckBox("Markdown dosyasını PDF’nin yanına kaydet")
        self.same_folder.setChecked(True)
        self.same_folder.toggled.connect(self.toggle_output_folder)
        folder_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Çıktı klasörü")
        self.output_edit.setEnabled(False)
        self.folder_button = QPushButton("Klasör Seç")
        self.folder_button.setEnabled(False)
        self.folder_button.clicked.connect(self.choose_output_folder)
        folder_row.addWidget(self.output_edit, 1)
        folder_row.addWidget(self.folder_button)
        output_layout.addWidget(self.same_folder)
        output_layout.addLayout(folder_row)
        left_layout.addWidget(output_group)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 0, 0, 0)

        settings_group = QGroupBox("Dönüştürme ayarları")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(12)

        self.ocr_combo = QComboBox()
        self.ocr_combo.addItem("Otomatik (önerilen)", "auto")
        self.ocr_combo.addItem("Her sayfada OCR", "always")
        self.ocr_combo.addItem("OCR kullanma", "never")

        self.language_edit = QLineEdit("tur+eng")
        self.language_edit.setToolTip("Tesseract dil kodları. Örnek: tur+eng")
        self.include_headers = QCheckBox("Üstbilgi ve altbilgileri dahil et")
        self.include_headers.setChecked(False)
        self.extract_images = QCheckBox("Görselleri ayrı klasöre çıkar")
        self.page_separators = QCheckBox("Sayfalar arasına ayraç ekle")

        settings_layout.addRow("OCR modu", self.ocr_combo)
        settings_layout.addRow("OCR dili", self.language_edit)
        settings_layout.addRow("", self.include_headers)
        settings_layout.addRow("", self.extract_images)
        settings_layout.addRow("", self.page_separators)
        right_layout.addWidget(settings_group)

        log_group = QGroupBox("İşlem günlüğü")
        log_layout = QVBoxLayout(log_group)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Dönüştürme sonuçları burada görünecek.")
        self.open_output_button = QPushButton("Son Çıktıyı Aç")
        self.open_output_button.setEnabled(False)
        self.open_output_button.clicked.connect(self.open_last_output)
        log_layout.addWidget(self.log, 1)
        log_layout.addWidget(self.open_output_button)
        right_layout.addWidget(log_group, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([530, 410])

        footer = QFrame()
        footer_layout = QGridLayout(footer)
        footer_layout.setContentsMargins(0, 4, 0, 0)
        self.status_label = QLabel("Hazır")
        self.status_label.setObjectName("subtitle")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.setObjectName("danger")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.convert_button = QPushButton("Markdown’a Dönüştür")
        self.convert_button.setObjectName("primary")
        self.convert_button.clicked.connect(self.start_conversion)

        footer_layout.addWidget(self.status_label, 0, 0, 1, 3)
        footer_layout.addWidget(self.progress, 1, 0)
        footer_layout.addWidget(self.cancel_button, 1, 1)
        footer_layout.addWidget(self.convert_button, 1, 2)
        footer_layout.setColumnStretch(0, 1)
        layout.addWidget(footer)

    @Slot(list)
    def add_files(self, paths: list[str]) -> None:
        existing = {
            self.file_list.item(index).data(Qt.UserRole)
            for index in range(self.file_list.count())
        }
        added = 0
        for raw_path in paths:
            path = Path(raw_path).resolve()
            if path.suffix.lower() != ".pdf" or not path.is_file():
                continue
            path_text = str(path)
            if path_text in existing:
                continue
            self.file_list.addItem(path.name)
            item = self.file_list.item(self.file_list.count() - 1)
            item.setData(Qt.UserRole, path_text)
            item.setToolTip(path_text)
            existing.add(path_text)
            added += 1
        if added:
            self.status_label.setText(f"{self.file_list.count()} PDF hazır")

    @Slot()
    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "PDF dosyalarını seç", "", "PDF Dosyaları (*.pdf)"
        )
        self.add_files(paths)

    @Slot()
    def remove_selected(self) -> None:
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        self.status_label.setText(f"{self.file_list.count()} PDF hazır")

    @Slot(bool)
    def toggle_output_folder(self, same_folder: bool) -> None:
        self.output_edit.setEnabled(not same_folder)
        self.folder_button.setEnabled(not same_folder)

    @Slot()
    def choose_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Çıktı klasörünü seç")
        if folder:
            self.output_edit.setText(folder)

    def set_busy(self, busy: bool) -> None:
        for widget in (
            self.add_button,
            self.remove_button,
            self.clear_button,
            self.convert_button,
            self.ocr_combo,
            self.language_edit,
            self.include_headers,
            self.extract_images,
            self.page_separators,
            self.same_folder,
        ):
            widget.setEnabled(not busy)
        self.file_list.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)
        if not self.same_folder.isChecked():
            self.output_edit.setEnabled(not busy)
            self.folder_button.setEnabled(not busy)

    @Slot()
    def start_conversion(self) -> None:
        if self.file_list.count() == 0:
            QMessageBox.information(self, "PDF gerekli", "Önce en az bir PDF ekleyin.")
            return

        output_dir: str | None = None
        if not self.same_folder.isChecked():
            output_dir = self.output_edit.text().strip()
            if not output_dir:
                QMessageBox.information(self, "Klasör gerekli", "Bir çıktı klasörü seçin.")
                return

        language = self.language_edit.text().strip() or "tur+eng"
        files = [
            self.file_list.item(index).data(Qt.UserRole)
            for index in range(self.file_list.count())
        ]

        self.log.clear()
        self.last_output = None
        self.open_output_button.setEnabled(False)
        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        self.set_busy(True)

        self.thread = QThread(self)
        self.worker = ConverterWorker(
            files=files,
            output_dir=output_dir,
            ocr_mode=self.ocr_combo.currentData(),
            ocr_language=language,
            include_headers=self.include_headers.isChecked(),
            extract_images=self.extract_images.isChecked(),
            page_separators=self.page_separators.isChecked(),
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.converted.connect(self.on_converted)
        self.worker.failed_file.connect(self.on_failed_file)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.clear_thread_references)
        self.thread.start()

    @Slot(int, int, str)
    def on_progress(self, current: int, total: int, name: str) -> None:
        self.progress.setValue(current - 1)
        self.status_label.setText(f"İşleniyor ({current}/{total}): {name}")
        self.log.appendPlainText(f"→ {name}")

    @Slot(str, str)
    def on_converted(self, source: str, target: str) -> None:
        self.last_output = Path(target)
        self.open_output_button.setEnabled(True)
        self.log.appendPlainText(f"  ✓ {target}\n")

    @Slot(str, str)
    def on_failed_file(self, source: str, error: str) -> None:
        self.log.appendPlainText(f"  ✗ {Path(source).name}: {error}\n")

    @Slot(int, int, bool)
    def on_finished(self, success: int, failed: int, cancelled: bool) -> None:
        self.progress.setValue(self.progress.maximum())
        self.set_busy(False)
        if cancelled:
            self.status_label.setText(f"İptal edildi — {success} dosya tamamlandı")
        else:
            self.status_label.setText(f"Tamamlandı — {success} başarılı, {failed} hatalı")
        if failed:
            QMessageBox.warning(
                self,
                "Bazı dosyalar dönüştürülemedi",
                "Ayrıntılar için işlem günlüğüne bakın. OCR hatası varsa Türkçe dil "
                "paketinin kurulu olduğundan emin olun.",
            )
        if self.close_when_finished:
            QTimer.singleShot(250, self.close)

    @Slot()
    def cancel_conversion(self) -> None:
        if self.thread and self.thread.isRunning():
            self.thread.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Geçerli dosya bitince iptal edilecek…")

    @Slot()
    def clear_thread_references(self) -> None:
        self.thread = None
        self.worker = None

    @Slot()
    def open_last_output(self) -> None:
        if self.last_output and self.last_output.exists():
            QDesktopServices.openUrl(self.last_output.parent.as_uri())

    def closeEvent(self, event) -> None:
        if self.thread and self.thread.isRunning():
            answer = QMessageBox.question(
                self,
                "Dönüştürme sürüyor",
                "İşlem devam ediyor. Uygulamayı kapatmak istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer == QMessageBox.No:
                event.ignore()
                return
            self.close_when_finished = True
            self.thread.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Geçerli dosya bitince uygulama kapatılacak…")
            event.ignore()
            return
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Yerel PDF to Markdown")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
