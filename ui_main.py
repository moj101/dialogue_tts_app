# -*- coding: utf-8 -*-
"""
رابط کاربری اصلی برنامه.
"""

import re
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAction, QDialog,
    QDialogButtonBox, QMessageBox, QPlainTextEdit, QProgressBar, QCheckBox,
    QDoubleSpinBox, QAbstractItemView, QSplitter, QFrame, QStyle
)

from config import (
    DEFAULT_BASE_URL,
    DEFAULT_TTS_MODEL,
    AVAILABLE_LANGUAGES,
    AVAILABLE_AUDIO_FORMATS,
    AVAILABLE_VOICES,
    OUTPUT_DIR,
    BASE_DIR,
)
from db import DatabaseManager
from avalai_api import AvalaiAPI
from audio_utils import merge_audio_files, open_audio_file
from resources import get_standard_icon, load_app_icon


class AudioGenerationWorker(QThread):
    progress = pyqtSignal(int)
    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, api: AvalaiAPI, model: str, voice: str, text: str, speed: float, output_file: Path, parent=None):
        super().__init__(parent)
        self.api = api
        self.model = model
        self.voice = voice
        self.text = text
        self.speed = speed
        self.output_file = output_file

    def run(self):
        try:
            self.progress.emit(10)
            result = self.api.text_to_speech(
                model=self.model,
                voice=self.voice,
                text=self.text,
                speed=self.speed,
                output_file=self.output_file,
            )
            self.progress.emit(100)
            self.finished_ok.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class CostLookupWorker(QThread):
    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, api: AvalaiAPI, request_id: str, retries: int = 6, delay_seconds: int = 5, parent=None):
        super().__init__(parent)
        self.api = api
        self.request_id = request_id
        self.retries = retries
        self.delay_seconds = delay_seconds

    def run(self):
        try:
            result = self.api.lookup_transaction_cost_with_retry(
                request_id=self.request_id,
                retries=self.retries,
                delay_seconds=self.delay_seconds,
            )
            self.finished_ok.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("راهنمای استفاده از برنامه")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(800, 620)
        self.setWindowIcon(load_app_icon())
        self._build_ui()
        self.load_help_text()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("راهنمای استفاده از نرم‌افزار")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #1d4ed8;")

        desc = QLabel("این راهنما از فایل help_content.txt خوانده می‌شود و هر زمان قابل ویرایش است.")
        desc.setStyleSheet("color: #475569;")

        self.help_text = QPlainTextEdit()
        self.help_text.setReadOnly(True)

        reload_btn = QPushButton("بارگذاری مجدد فایل راهنما")
        reload_btn.setIcon(get_standard_icon(QStyle.SP_BrowserReload))
        reload_btn.clicked.connect(self.load_help_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.help_text)
        layout.addWidget(reload_btn)
        layout.addWidget(buttons)

    def load_help_text(self):
        help_file = Path(BASE_DIR) / "help_content.txt"
        if not help_file.exists():
            self.help_text.setPlainText(
                "فایل help_content.txt پیدا نشد.\n"
                "لطفاً این فایل را در پوشه اصلی پروژه قرار دهید."
            )
            return

        try:
            content = help_file.read_text(encoding="utf-8")
            self.help_text.setPlainText(content)
        except Exception as e:
            self.help_text.setPlainText(f"خطا در خواندن فایل راهنما:\n{e}")


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("درباره برنامه")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(560, 420)
        self.setWindowIcon(load_app_icon())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        card = QFrame()
        card_layout = QVBoxLayout(card)

        title = QLabel("نرم‌افزار تولید صدای گفتگو")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1d4ed8;")

        subtitle = QLabel("نسخه آزمایشی پایدار برای ساخت دیالوگ صوتی چندشخصیتی")
        subtitle.setStyleSheet("color: #475569;")

        desc = QLabel(
            "این نرم‌افزار برای دریافت دیالوگ متنی، مدیریت پروژه‌ها و شخصیت‌ها، "
            "تولید صدا، ذخیره تراکنش‌ها، استعلام هزینه و ساخت خروجی نهایی طراحی شده است."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("line-height: 1.8; color: #1f2937;")

        features = QLabel(
            "ویژگی‌ها:\n"
            "• تعریف و مدیریت پروژه‌ها\n"
            "• تعریف شخصیت‌ها با صدا و سرعت مجزا\n"
            "• تجزیه متن دیالوگ\n"
            "• ویرایش مستقیم خطوط در جدول\n"
            "• انتخاب دستی شخصیت برای هر خط\n"
            "• بازسازی فقط خطوط تغییرکرده\n"
            "• ثبت تراکنش و هزینه‌ها\n"
            "• ادغام فایل‌های صوتی"
        )
        features.setWordWrap(True)
        features.setStyleSheet("color: #334155;")

        designer = QLabel("طراح برنامه: مجتبی محمدی")
        designer.setStyleSheet("color: #334155; font-weight: bold;")

        email = QLabel("ایمیل: mojsoft@hotmai.com")
        email.setStyleSheet("color: #475569;")

        footer = QLabel("PyQt5 + Python + SQLite + AvalAI")
        footer.setStyleSheet("color: #64748b; font-style: italic;")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(10)
        card_layout.addWidget(desc)
        card_layout.addSpacing(8)
        card_layout.addWidget(features)
        card_layout.addStretch()
        card_layout.addWidget(designer)
        card_layout.addWidget(email)
        card_layout.addWidget(footer)

        layout.addWidget(card)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class AvalaiSettingsDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("تنظیمات AvalAI")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(560, 430)
        self.setWindowIcon(load_app_icon())
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.api_key_edit = QLineEdit()
        self.base_url_edit = QLineEdit()
        self.model_edit = QLineEdit()

        self.default_voice_combo = QComboBox()
        self.default_voice_combo.addItems(AVAILABLE_VOICES)

        self.default_speed_spin = QDoubleSpinBox()
        self.default_speed_spin.setRange(0.5, 3.0)
        self.default_speed_spin.setSingleStep(0.1)

        self.default_language_combo = QComboBox()
        for code, title in AVAILABLE_LANGUAGES:
            self.default_language_combo.addItem(title, code)

        self.default_format_combo = QComboBox()
        self.default_format_combo.addItems(AVAILABLE_AUDIO_FORMATS)

        self.enable_cost_management_check = QCheckBox("فعال‌سازی مدیریت هزینه و استعلام تراکنش")
        self.show_costs_check = QCheckBox("نمایش هزینه‌ها")
        self.log_transactions_check = QCheckBox("ثبت تراکنش‌ها")
        self.auto_lookup_cost_check = QCheckBox("استعلام خودکار هزینه پس از تولید صدا")

        self.lookup_request_id_edit = QLineEdit()
        self.lookup_btn = QPushButton("بررسی هزینه دقیق")
        self.lookup_btn.setIcon(get_standard_icon(QStyle.SP_FileDialogContentsView))
        self.test_btn = QPushButton("تست اتصال")
        self.test_btn.setIcon(get_standard_icon(QStyle.SP_DialogApplyButton))

        self.lookup_btn.clicked.connect(self.lookup_cost)
        self.test_btn.clicked.connect(self.test_connection)

        form.addRow("توکن API:", self.api_key_edit)
        form.addRow("آدرس پایه:", self.base_url_edit)
        form.addRow("مدل TTS:", self.model_edit)
        form.addRow("صدای پیش‌فرض:", self.default_voice_combo)
        form.addRow("سرعت پیش‌فرض:", self.default_speed_spin)
        form.addRow("زبان پیش‌فرض:", self.default_language_combo)
        form.addRow("فرمت پیش‌فرض:", self.default_format_combo)
        form.addRow("", self.enable_cost_management_check)
        form.addRow("", self.show_costs_check)
        form.addRow("", self.log_transactions_check)
        form.addRow("", self.auto_lookup_cost_check)
        form.addRow("request_id:", self.lookup_request_id_edit)
        form.addRow("", self.lookup_btn)
        form.addRow("", self.test_btn)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self):
        self.api_key_edit.setText(self.db.get_setting("avalai_api_key"))
        self.base_url_edit.setText(self.db.get_setting("avalai_base_url", DEFAULT_BASE_URL))
        self.model_edit.setText(self.db.get_setting("avalai_tts_model", DEFAULT_TTS_MODEL))

        voice = self.db.get_setting("avalai_default_voice", "nova")
        idx = self.default_voice_combo.findText(voice)
        if idx >= 0:
            self.default_voice_combo.setCurrentIndex(idx)

        speed = self.db.get_setting("avalai_default_speed", "1.0")
        self.default_speed_spin.setValue(float(speed))

        lang = self.db.get_setting("default_language_code", "fr")
        idx = self.default_language_combo.findData(lang)
        if idx >= 0:
            self.default_language_combo.setCurrentIndex(idx)

        fmt = self.db.get_setting("default_audio_format", "mp3")
        idx = self.default_format_combo.findText(fmt)
        if idx >= 0:
            self.default_format_combo.setCurrentIndex(idx)

        self.enable_cost_management_check.setChecked(self.db.get_setting("enable_cost_management", "1") == "1")
        self.show_costs_check.setChecked(self.db.get_setting("show_costs", "1") == "1")
        self.log_transactions_check.setChecked(self.db.get_setting("enable_transaction_logging", "1") == "1")
        self.auto_lookup_cost_check.setChecked(self.db.get_setting("auto_lookup_cost", "1") == "1")

    def test_connection(self):
        api_key = self.api_key_edit.text().strip()
        base_url = self.base_url_edit.text().strip()
        api = AvalaiAPI(api_key=api_key, base_url=base_url)
        if api.test_connection():
            QMessageBox.information(self, "اتصال", "تنظیمات اتصال معتبر است.")
        else:
            QMessageBox.warning(self, "اتصال", "مقادیر توکن یا آدرس پایه نامعتبر است.")

    def lookup_cost(self):
        api_key = self.api_key_edit.text().strip()
        request_id = self.lookup_request_id_edit.text().strip()

        if not api_key:
            QMessageBox.warning(self, "خطا", "توکن API وارد نشده است.")
            return

        if not request_id:
            QMessageBox.warning(self, "خطا", "request_id وارد نشده است.")
            return

        try:
            api = AvalaiAPI(api_key=api_key, base_url=self.base_url_edit.text().strip())
            result = api.lookup_transaction_cost_with_retry(request_id, retries=6, delay_seconds=5)
            msg = (
                f"هزینه دلار: {result.get('cost_usd') or 'نامشخص'}\n"
                f"هزینه تومان/ریال: {result.get('cost_irr') or 'نامشخص'}\n"
                f"تعداد تلاش: {result.get('attempt', '?')}"
            )
            QMessageBox.information(self, "نتیجه استعلام", msg)
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"استعلام هزینه ناموفق بود:\n{e}")

    def save_settings(self):
        self.db.set_setting("avalai_api_key", self.api_key_edit.text().strip())
        self.db.set_setting("avalai_base_url", self.base_url_edit.text().strip())
        self.db.set_setting("avalai_tts_model", self.model_edit.text().strip())
        self.db.set_setting("avalai_default_voice", self.default_voice_combo.currentText())
        self.db.set_setting("avalai_default_speed", str(self.default_speed_spin.value()))
        self.db.set_setting("default_language_code", self.default_language_combo.currentData())
        self.db.set_setting("default_audio_format", self.default_format_combo.currentText())
        self.db.set_setting("enable_cost_management", "1" if self.enable_cost_management_check.isChecked() else "0")
        self.db.set_setting("show_costs", "1" if self.show_costs_check.isChecked() else "0")
        self.db.set_setting("enable_transaction_logging", "1" if self.log_transactions_check.isChecked() else "0")
        self.db.set_setting("auto_lookup_cost", "1" if self.auto_lookup_cost_check.isChecked() else "0")
        QMessageBox.information(self, "ذخیره", "تنظیمات با موفقیت ذخیره شد.")
        self.accept()


class CharactersDialog(QDialog):
    def __init__(self, db: DatabaseManager, project_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.project_id = project_id
        self.selected_character_id = None
        self.setWindowTitle("مدیریت شخصیت‌ها")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(760, 470)
        self.setWindowIcon(load_app_icon())
        self._build_ui()
        self.load_characters()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "شناسه", "نام شخصیت", "زبان", "صدا", "سرعت", "توضیح لحن"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        form = QFormLayout()
        self.name_edit = QLineEdit()

        self.language_combo = QComboBox()
        for code, title in AVAILABLE_LANGUAGES:
            self.language_combo.addItem(title, code)

        self.voice_combo = QComboBox()
        self.voice_combo.addItems(AVAILABLE_VOICES)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 3.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(1.0)

        self.style_edit = QTextEdit()

        form.addRow("نام شخصیت:", self.name_edit)
        form.addRow("زبان:", self.language_combo)
        form.addRow("صدا:", self.voice_combo)
        form.addRow("سرعت:", self.speed_spin)
        form.addRow("توضیح لحن:", self.style_edit)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("افزودن")
        self.add_btn.setIcon(get_standard_icon(QStyle.SP_FileDialogNewFolder))
        self.edit_btn = QPushButton("ویرایش")
        self.edit_btn.setIcon(get_standard_icon(QStyle.SP_FileDialogDetailedView))
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setIcon(get_standard_icon(QStyle.SP_TrashIcon))
        self.close_btn = QPushButton("بستن")
        self.close_btn.setIcon(get_standard_icon(QStyle.SP_DialogCloseButton))

        self.add_btn.clicked.connect(self.add_character)
        self.edit_btn.clicked.connect(self.edit_character)
        self.delete_btn.clicked.connect(self.delete_character)
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def load_characters(self):
        rows = self.db.get_characters_by_project(self.project_id)
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["language_code"]))
            self.table.setItem(r, 3, QTableWidgetItem(row["voice_name"]))
            self.table.setItem(r, 4, QTableWidgetItem(str(row["speed"])))
            self.table.setItem(r, 5, QTableWidgetItem(row["style_note"] or ""))

    def on_row_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return

        self.selected_character_id = int(self.table.item(row, 0).text())
        self.name_edit.setText(self.table.item(row, 1).text())

        lang_code = self.table.item(row, 2).text()
        idx = self.language_combo.findData(lang_code)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

        voice_name = self.table.item(row, 3).text()
        idx = self.voice_combo.findText(voice_name)
        if idx >= 0:
            self.voice_combo.setCurrentIndex(idx)

        self.speed_spin.setValue(float(self.table.item(row, 4).text()))
        self.style_edit.setPlainText(self.table.item(row, 5).text())

    def add_character(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام شخصیت وارد نشده است.")
            return

        self.db.add_character(
            project_id=self.project_id,
            name=name,
            voice_name=self.voice_combo.currentText(),
            speed=self.speed_spin.value(),
            style_note=self.style_edit.toPlainText().strip(),
            language_code=self.language_combo.currentData(),
        )
        self.load_characters()

    def edit_character(self):
        if not self.selected_character_id:
            QMessageBox.warning(self, "خطا", "ابتدا یک شخصیت را انتخاب کنید.")
            return

        self.db.update_character(
            character_id=self.selected_character_id,
            name=self.name_edit.text().strip(),
            voice_name=self.voice_combo.currentText(),
            speed=self.speed_spin.value(),
            style_note=self.style_edit.toPlainText().strip(),
            language_code=self.language_combo.currentData(),
        )
        self.load_characters()

    def delete_character(self):
        if not self.selected_character_id:
            QMessageBox.warning(self, "خطا", "ابتدا یک شخصیت را انتخاب کنید.")
            return

        self.db.delete_character(self.selected_character_id)
        self.selected_character_id = None
        self.load_characters()


class ProjectsDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_project_id = None
        self.setWindowTitle("مدیریت و بارگذاری پروژه‌ها")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(950, 540)
        self.setWindowIcon(load_app_icon())
        self._build_ui()
        self.load_projects()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو در عنوان یا توضیحات پروژه")
        self.search_btn = QPushButton("جستجو")
        self.search_btn.setIcon(get_standard_icon(QStyle.SP_FileDialogContentsView))
        self.refresh_btn = QPushButton("تازه‌سازی")
        self.refresh_btn.setIcon(get_standard_icon(QStyle.SP_BrowserReload))

        self.search_btn.clicked.connect(self.load_projects)
        self.refresh_btn.clicked.connect(self.load_projects)

        top_layout.addWidget(self.search_edit)
        top_layout.addWidget(self.search_btn)
        top_layout.addWidget(self.refresh_btn)
        layout.addLayout(top_layout)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "شناسه", "عنوان", "زبان", "فرمت", "تاریخ ایجاد", "آخرین ویرایش"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.open_btn = QPushButton("بارگذاری پروژه")
        self.open_btn.setIcon(get_standard_icon(QStyle.SP_DialogOpenButton))
        self.delete_btn = QPushButton("حذف پروژه")
        self.delete_btn.setIcon(get_standard_icon(QStyle.SP_TrashIcon))
        self.close_btn = QPushButton("بستن")
        self.close_btn.setIcon(get_standard_icon(QStyle.SP_DialogCloseButton))

        self.open_btn.clicked.connect(self.accept_selection)
        self.delete_btn.clicked.connect(self.delete_selected_project)
        self.close_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def load_projects(self):
        keyword = self.search_edit.text().strip()
        rows = self.db.search_projects(keyword)

        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["title"] or ""))
            self.table.setItem(r, 2, QTableWidgetItem(row["language_code"] or ""))
            self.table.setItem(r, 3, QTableWidgetItem(row["audio_format"] or ""))
            self.table.setItem(r, 4, QTableWidgetItem(row["created_at"] or ""))
            self.table.setItem(r, 5, QTableWidgetItem(row["updated_at"] or ""))

    def get_selected_project_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return int(item.text())

    def accept_selection(self):
        project_id = self.get_selected_project_id()
        if not project_id:
            QMessageBox.warning(self, "خطا", "ابتدا یک پروژه را انتخاب کنید.")
            return
        self.selected_project_id = project_id
        self.accept()

    def delete_selected_project(self):
        project_id = self.get_selected_project_id()
        if not project_id:
            QMessageBox.warning(self, "خطا", "ابتدا یک پروژه را انتخاب کنید.")
            return

        result = QMessageBox.question(
            self,
            "تأیید حذف",
            "آیا از حذف پروژه انتخاب‌شده مطمئن هستید؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        self.db.delete_project(project_id)
        self.load_projects()
        QMessageBox.information(self, "موفق", "پروژه حذف شد.")


class TransactionsDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("هزینه‌ها و تراکنش‌ها")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1080, 560)
        self.setWindowIcon(load_app_icon())
        self._build_ui()
        self.load_projects()
        self.load_transactions()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        self.project_combo = QComboBox()
        self.project_combo.addItem("همه پروژه‌ها", None)

        self.request_id_edit = QLineEdit()
        self.request_id_edit.setPlaceholderText("request_id")

        self.search_btn = QPushButton("جستجو")
        self.search_btn.setIcon(get_standard_icon(QStyle.SP_FileDialogContentsView))
        self.refresh_btn = QPushButton("تازه‌سازی")
        self.refresh_btn.setIcon(get_standard_icon(QStyle.SP_BrowserReload))
        self.close_btn = QPushButton("بستن")
        self.close_btn.setIcon(get_standard_icon(QStyle.SP_DialogCloseButton))

        self.search_btn.clicked.connect(self.load_transactions)
        self.refresh_btn.clicked.connect(self.load_transactions)
        self.close_btn.clicked.connect(self.accept)

        filter_layout.addWidget(QLabel("پروژه:"))
        filter_layout.addWidget(self.project_combo)
        filter_layout.addWidget(QLabel("request_id:"))
        filter_layout.addWidget(self.request_id_edit)
        filter_layout.addWidget(self.search_btn)
        filter_layout.addWidget(self.refresh_btn)
        filter_layout.addWidget(self.close_btn)

        layout.addLayout(filter_layout)

        self.table = QTableWidget(0, 12)
        self.table.setHorizontalHeaderLabels([
            "شناسه", "تاریخ", "پروژه", "خط", "مدل", "صدا", "request_id",
            "هزینه دلار", "هزینه تومان", "وضعیت lookup", "تلاش‌ها", "خطای lookup"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def load_projects(self):
        self.project_combo.clear()
        self.project_combo.addItem("همه پروژه‌ها", None)
        for row in self.db.get_projects():
            self.project_combo.addItem(row["title"], row["id"])

    def load_transactions(self):
        project_id = self.project_combo.currentData()
        request_id = self.request_id_edit.text().strip()
        rows = self.db.get_transactions(project_id=project_id, request_id=request_id)

        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["created_at"] or ""))
            self.table.setItem(r, 2, QTableWidgetItem(row["project_title"] or ""))
            self.table.setItem(r, 3, QTableWidgetItem(str(row["line_number"] or "")))
            self.table.setItem(r, 4, QTableWidgetItem(row["model_name"] or ""))
            self.table.setItem(r, 5, QTableWidgetItem(row["voice_name"] or ""))
            self.table.setItem(r, 6, QTableWidgetItem(row["request_id"] or ""))
            self.table.setItem(r, 7, QTableWidgetItem(row["cost_usd"] or ""))
            self.table.setItem(r, 8, QTableWidgetItem(row["cost_irr"] or ""))
            self.table.setItem(r, 9, QTableWidgetItem(row["lookup_status"] or ""))
            self.table.setItem(r, 10, QTableWidgetItem(str(row["lookup_attempts"] or 0)))
            self.table.setItem(r, 11, QTableWidgetItem(row["lookup_error"] or ""))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_project_id = None
        self._loading_table = False

        self.audio_worker = None
        self.cost_worker = None
        self.pending_cost_line_id = None
        self.pending_cost_request_id = None
        self.pending_audio_context = None
        self.batch_changed_queue = []
        self.batch_all_queue = []

        self.setWindowTitle("نرم‌افزار تولید صدای گفتگو")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1380, 840)
        self.setWindowIcon(load_app_icon())

        self._build_ui()
        self._build_menu()
        self._connect_signals()
        self._load_defaults()

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("فایل")
        tools_menu = menu.addMenu("ابزارها")
        help_menu = menu.addMenu("راهنما")

        new_project_action = QAction(get_standard_icon(QStyle.SP_FileIcon), "پروژه جدید", self)
        open_project_action = QAction(get_standard_icon(QStyle.SP_DialogOpenButton), "بارگذاری پروژه", self)
        save_project_action = QAction(get_standard_icon(QStyle.SP_DialogSaveButton), "ذخیره پروژه", self)
        exit_action = QAction(get_standard_icon(QStyle.SP_DialogCloseButton), "خروج", self)

        avalai_settings_action = QAction(get_standard_icon(QStyle.SP_FileDialogDetailedView), "تنظیمات AvalAI", self)
        characters_action = QAction(get_standard_icon(QStyle.SP_DirIcon), "مدیریت شخصیت‌ها", self)
        transactions_action = QAction(get_standard_icon(QStyle.SP_FileDialogInfoView), "هزینه‌ها و تراکنش‌ها", self)

        help_action = QAction(get_standard_icon(QStyle.SP_MessageBoxInformation), "راهنمای استفاده", self)
        about_action = QAction(get_standard_icon(QStyle.SP_TitleBarMenuButton), "درباره برنامه", self)

        new_project_action.triggered.connect(self.new_project)
        open_project_action.triggered.connect(self.open_projects_dialog)
        save_project_action.triggered.connect(self.save_project)
        exit_action.triggered.connect(self.close)

        avalai_settings_action.triggered.connect(self.open_avalai_settings)
        characters_action.triggered.connect(self.open_characters_dialog)
        transactions_action.triggered.connect(self.open_transactions_dialog)

        help_action.triggered.connect(self.open_help_dialog)
        about_action.triggered.connect(self.open_about_dialog)

        file_menu.addAction(new_project_action)
        file_menu.addAction(open_project_action)
        file_menu.addAction(save_project_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        tools_menu.addAction(avalai_settings_action)
        tools_menu.addAction(characters_action)
        tools_menu.addAction(transactions_action)

        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        project_group = QGroupBox("اطلاعات پروژه")
        project_form = QFormLayout(project_group)

        self.project_title_edit = QLineEdit()
        self.project_desc_edit = QTextEdit()

        self.language_combo = QComboBox()
        for code, title in AVAILABLE_LANGUAGES:
            self.language_combo.addItem(title, code)

        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(AVAILABLE_AUDIO_FORMATS)

        self.output_dir_edit = QLineEdit()
        self.output_dir_btn = QPushButton("انتخاب مسیر")
        self.output_dir_btn.setIcon(get_standard_icon(QStyle.SP_DirOpenIcon))
        self.output_dir_btn.clicked.connect(self.select_output_dir)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.output_dir_edit)
        path_layout.addWidget(self.output_dir_btn)

        path_wrapper = QWidget()
        path_wrapper.setLayout(path_layout)

        project_form.addRow("عنوان پروژه:", self.project_title_edit)
        project_form.addRow("توضیحات:", self.project_desc_edit)
        project_form.addRow("زبان خروجی:", self.language_combo)
        project_form.addRow("فرمت خروجی:", self.audio_format_combo)
        project_form.addRow("مسیر ذخیره:", path_wrapper)

        main_layout.addWidget(project_group)

        splitter = QSplitter(Qt.Vertical)

        text_group = QGroupBox("متن خام دیالوگ")
        text_group.setMinimumHeight(180)
        text_layout = QVBoxLayout(text_group)
        self.raw_dialogue_edit = QTextEdit()
        self.parse_btn = QPushButton("تجزیه دیالوگ")
        self.parse_btn.setIcon(get_standard_icon(QStyle.SP_ArrowDown))
        self.clean_text_btn = QPushButton("پاک‌سازی متن")
        self.clean_text_btn.setIcon(get_standard_icon(QStyle.SP_BrowserReload))
        text_btn_layout = QHBoxLayout()
        text_btn_layout.addWidget(self.parse_btn)
        text_btn_layout.addWidget(self.clean_text_btn)
        text_layout.addWidget(self.raw_dialogue_edit)
        text_layout.addLayout(text_btn_layout)

        text_container = QWidget()
        text_container_layout = QVBoxLayout(text_container)
        text_container_layout.setContentsMargins(0, 0, 0, 0)
        text_container_layout.addWidget(text_group)

        dialogue_group = QGroupBox("خطوط دیالوگ")
        dialogue_group.setMinimumHeight(260)
        dialogue_layout = QVBoxLayout(dialogue_group)

        self.dialogue_table = QTableWidget(0, 11)
        self.dialogue_table.setHorizontalHeaderLabels([
            "شناسه", "شماره", "گوینده خام", "شخصیت", "متن", "صدا", "سرعت",
            "فایل صوتی", "request_id", "وضعیت", "تغییر"
        ])
        self.dialogue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dialogue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.dialogue_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dialogue_table.setAlternatingRowColors(True)
        dialogue_layout.addWidget(self.dialogue_table)

        op_layout = QHBoxLayout()
        self.remap_btn = QPushButton("اتصال مجدد شخصیت‌ها")
        self.remap_btn.setIcon(get_standard_icon(QStyle.SP_BrowserReload))
        self.generate_selected_btn = QPushButton("تولید صدای خط انتخاب‌شده")
        self.generate_selected_btn.setIcon(get_standard_icon(QStyle.SP_MediaPlay))
        self.generate_changed_btn = QPushButton("بازسازی خطوط تغییرکرده")
        self.generate_changed_btn.setIcon(get_standard_icon(QStyle.SP_BrowserReload))
        self.refresh_failed_costs_btn = QPushButton("به‌روزرسانی هزینه‌های ناموفق")
        self.refresh_failed_costs_btn.setIcon(get_standard_icon(QStyle.SP_BrowserReload))
        self.generate_all_btn = QPushButton("تولید صدای همه خطوط")
        self.generate_all_btn.setIcon(get_standard_icon(QStyle.SP_MediaSeekForward))
        self.play_btn = QPushButton("پخش فایل انتخاب‌شده")
        self.play_btn.setIcon(get_standard_icon(QStyle.SP_MediaPlay))
        self.merge_btn = QPushButton("ادغام فایل‌ها")
        self.merge_btn.setIcon(get_standard_icon(QStyle.SP_FileDialogListView))
        self.export_btn = QPushButton("ذخیره خروجی نهایی")
        self.export_btn.setIcon(get_standard_icon(QStyle.SP_DialogSaveButton))

        op_layout.addWidget(self.remap_btn)
        op_layout.addWidget(self.generate_selected_btn)
        op_layout.addWidget(self.generate_changed_btn)
        op_layout.addWidget(self.refresh_failed_costs_btn)
        op_layout.addWidget(self.generate_all_btn)
        op_layout.addWidget(self.play_btn)
        op_layout.addWidget(self.merge_btn)
        op_layout.addWidget(self.export_btn)

        dialogue_layout.addLayout(op_layout)

        table_container = QWidget()
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.addWidget(dialogue_group)

        splitter.addWidget(text_container)
        splitter.addWidget(table_container)
        splitter.setSizes([260, 420])
        splitter.setChildrenCollapsible(False)

        main_layout.addWidget(splitter)

        status_group = QGroupBox("وضعیت")
        status_layout = QVBoxLayout(status_group)

        top_status_layout = QHBoxLayout()
        self.connection_status_label = QLabel("وضعیت اتصال: نامشخص")
        self.last_cost_label = QLabel("هزینه آخرین درخواست: ---")
        top_status_layout.addWidget(self.connection_status_label)
        top_status_layout.addWidget(self.last_cost_label)

        self.progress_bar = QProgressBar()
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)

        status_layout.addLayout(top_status_layout)
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.log_edit)

        main_layout.addWidget(status_group)

    def _connect_signals(self):
        self.parse_btn.clicked.connect(self.parse_dialogue)
        self.clean_text_btn.clicked.connect(self.clean_raw_text)
        self.remap_btn.clicked.connect(self.remap_characters)
        self.generate_selected_btn.clicked.connect(self.generate_selected_audio)
        self.generate_changed_btn.clicked.connect(self.generate_changed_audio)
        self.generate_all_btn.clicked.connect(self.generate_all_audio)
        self.refresh_failed_costs_btn.clicked.connect(self.refresh_failed_costs)
        self.play_btn.clicked.connect(self.play_selected_audio)
        self.merge_btn.clicked.connect(self.merge_all_audio)
        self.export_btn.clicked.connect(self.export_final_audio)
        self.dialogue_table.itemChanged.connect(self.on_dialogue_item_changed)

    def _load_defaults(self):
        default_lang = self.db.get_setting("default_language_code", "fr")
        idx = self.language_combo.findData(default_lang)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

        default_format = self.db.get_setting("default_audio_format", "mp3")
        idx = self.audio_format_combo.findText(default_format)
        if idx >= 0:
            self.audio_format_combo.setCurrentIndex(idx)

        self.output_dir_edit.setText(str(OUTPUT_DIR))

        api_key = self.db.get_setting("avalai_api_key", "")
        base_url = self.db.get_setting("avalai_base_url", DEFAULT_BASE_URL)
        if api_key and base_url:
            self.connection_status_label.setText("وضعیت اتصال: تنظیم شده")
        else:
            self.connection_status_label.setText("وضعیت اتصال: تنظیم نشده")

    def log(self, text: str):
        self.log_edit.appendPlainText(text)

    def is_cost_management_enabled(self) -> bool:
        return self.db.get_setting("enable_cost_management", "1") == "1"

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "انتخاب مسیر ذخیره")
        if directory:
            self.output_dir_edit.setText(directory)

    def get_api_client(self) -> AvalaiAPI:
        api_key = self.db.get_setting("avalai_api_key", "")
        base_url = self.db.get_setting("avalai_base_url", DEFAULT_BASE_URL)

        if not api_key:
            raise ValueError("توکن AvalAI در تنظیمات ثبت نشده است.")

        return AvalaiAPI(api_key=api_key, base_url=base_url)

    def get_selected_line_id(self):
        row = self.dialogue_table.currentRow()
        if row < 0:
            return None

        item = self.dialogue_table.item(row, 0)
        if not item:
            return None

        try:
            return int(item.text())
        except Exception:
            return None

    def get_output_dir(self) -> Path:
        path = self.output_dir_edit.text().strip()
        if not path:
            path = str(OUTPUT_DIR)
        out_dir = Path(path)
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def get_project_audio_dir(self) -> Path:
        if not self.current_project_id:
            raise ValueError("پروژه‌ای انتخاب نشده است.")
        project_dir = self.get_output_dir() / f"project_{self.current_project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def require_project(self) -> bool:
        if not self.current_project_id:
            QMessageBox.warning(self, "خطا", "ابتدا پروژه را ذخیره کنید.")
            return False
        return True

    def normalize_text(self, text: str) -> str:
        text = text.replace("\u200c", " ")
        text = text.replace("\r", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def parse_dialogue_text(self, raw_text: str):
        lines = []
        raw_lines = raw_text.splitlines()

        line_no = 1
        for raw in raw_lines:
            raw = raw.strip()
            if not raw:
                continue

            speaker = ""
            text = raw

            if ":" in raw:
                speaker, text = raw.split(":", 1)
            elif "：" in raw:
                speaker, text = raw.split("：", 1)

            speaker = speaker.strip()
            text = self.normalize_text(text)

            lines.append({
                "line_number": line_no,
                "speaker_name": speaker,
                "text_content": text,
                "status": "draft",
            })
            line_no += 1

        return lines

    def new_project(self):
        if self.audio_worker or self.cost_worker:
            QMessageBox.information(self, "اطلاع", "ابتدا منتظر پایان عملیات جاری بمانید.")
            return

        self.current_project_id = None
        self.project_title_edit.clear()
        self.project_desc_edit.clear()
        self.raw_dialogue_edit.clear()
        self.dialogue_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.last_cost_label.setText("هزینه آخرین درخواست: ---")
        self.log("پروژه جدید ایجاد شد.")

    def save_project(self):
        title = self.project_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "خطا", "عنوان پروژه وارد نشده است.")
            return

        description = self.project_desc_edit.toPlainText().strip()
        language_code = self.language_combo.currentData()
        audio_format = self.audio_format_combo.currentText()
        output_dir = self.output_dir_edit.text().strip()
        raw_dialogue_text = self.raw_dialogue_edit.toPlainText()

        if self.current_project_id is None:
            self.current_project_id = self.db.create_project(
                title=title,
                description=description,
                language_code=language_code,
                audio_format=audio_format,
                output_dir=output_dir,
                raw_dialogue_text=raw_dialogue_text,
            )
            self.log(f"پروژه با شناسه {self.current_project_id} ذخیره شد.")
        else:
            self.db.update_project(
                project_id=self.current_project_id,
                title=title,
                description=description,
                language_code=language_code,
                audio_format=audio_format,
                output_dir=output_dir,
                raw_dialogue_text=raw_dialogue_text,
            )
            self.log("پروژه به‌روزرسانی شد.")

    def open_projects_dialog(self):
        if self.audio_worker or self.cost_worker:
            QMessageBox.information(self, "اطلاع", "ابتدا منتظر پایان عملیات جاری بمانید.")
            return

        dialog = ProjectsDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_project_id:
            self.load_project(dialog.selected_project_id)

    def load_project(self, project_id: int):
        row = self.db.get_project(project_id)
        if not row:
            QMessageBox.warning(self, "خطا", "پروژه پیدا نشد.")
            return

        self.current_project_id = row["id"]
        self.project_title_edit.setText(row["title"] or "")
        self.project_desc_edit.setPlainText(row["description"] or "")

        idx = self.language_combo.findData(row["language_code"])
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

        idx = self.audio_format_combo.findText(row["audio_format"])
        if idx >= 0:
            self.audio_format_combo.setCurrentIndex(idx)

        self.output_dir_edit.setText(row["output_dir"] or str(OUTPUT_DIR))
        self.raw_dialogue_edit.setPlainText(row["raw_dialogue_text"] or "")

        self.db.remap_dialogue_lines_characters(project_id)
        self.load_dialogue_lines()
        self.log(f"پروژه {row['title']} بارگذاری شد.")

    def clean_raw_text(self):
        text = self.raw_dialogue_edit.toPlainText()
        self.raw_dialogue_edit.setPlainText(self.normalize_text(text))
        self.log("متن خام پاک‌سازی شد.")

    def parse_dialogue(self):
        if not self.require_project():
            return

        raw_text = self.raw_dialogue_edit.toPlainText().strip()
        if not raw_text:
            QMessageBox.warning(self, "خطا", "متن دیالوگ وارد نشده است.")
            return

        parsed = self.parse_dialogue_text(raw_text)
        if not parsed:
            QMessageBox.warning(self, "خطا", "هیچ خط قابل پردازشی یافت نشد.")
            return

        self.db.clear_dialogue_lines(self.current_project_id)

        for item in parsed:
            char_row = None
            if item["speaker_name"]:
                char_row = self.db.get_character_by_name(self.current_project_id, item["speaker_name"])

            self.db.add_dialogue_line(
                project_id=self.current_project_id,
                line_number=item["line_number"],
                speaker_name=item["speaker_name"],
                character_id=char_row["id"] if char_row else None,
                text_content=item["text_content"],
                status="draft" if char_row else "no_character",
            )

        self.save_project()
        self.load_dialogue_lines()
        self.log(f"{len(parsed)} خط دیالوگ ذخیره شد.")

    def remap_characters(self):
        if not self.require_project():
            return

        self.db.remap_dialogue_lines_characters(self.current_project_id)
        self.load_dialogue_lines()
        self.log("اتصال مجدد خطوط به شخصیت‌ها انجام شد.")

    def _make_readonly_item(self, text: str):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def load_dialogue_lines(self):
        if not self.current_project_id:
            self.dialogue_table.setRowCount(0)
            return

        self._loading_table = True
        self.dialogue_table.blockSignals(True)

        rows = self.db.get_dialogue_lines(self.current_project_id)
        characters = self.db.get_characters_by_project(self.current_project_id)

        self.dialogue_table.setRowCount(0)

        for row in rows:
            r = self.dialogue_table.rowCount()
            self.dialogue_table.insertRow(r)

            self.dialogue_table.setItem(r, 0, self._make_readonly_item(str(row["id"])))
            self.dialogue_table.setItem(r, 1, self._make_readonly_item(str(row["line_number"])))

            speaker_item = QTableWidgetItem(row["speaker_name"] or "")
            self.dialogue_table.setItem(r, 2, speaker_item)

            combo = QComboBox()
            combo.addItem("بدون شخصیت", None)
            for ch in characters:
                combo.addItem(ch["name"], ch["id"])

            if row["character_id"]:
                idx = combo.findData(row["character_id"])
                if idx >= 0:
                    combo.setCurrentIndex(idx)

            combo.currentIndexChanged.connect(
                lambda _, line_id=row["id"], c=combo: self.on_character_combo_changed(line_id, c)
            )
            self.dialogue_table.setCellWidget(r, 3, combo)

            text_item = QTableWidgetItem(row["text_content"] or "")
            self.dialogue_table.setItem(r, 4, text_item)

            self.dialogue_table.setItem(r, 5, self._make_readonly_item(row["voice_name"] or ""))
            self.dialogue_table.setItem(r, 6, self._make_readonly_item(str(row["speed"] or "")))
            self.dialogue_table.setItem(r, 7, self._make_readonly_item(row["audio_file_path"] or ""))
            self.dialogue_table.setItem(r, 8, self._make_readonly_item(row["request_id"] or ""))

            status_text = row["status"] or ""
            cost_lookup_status = row["cost_lookup_status"] or "none"
            extra_parts = [status_text]

            if row["estimated_cost"]:
                extra_parts.append(f"هزینه: {row['estimated_cost']}")

            if cost_lookup_status and cost_lookup_status != "none":
                extra_parts.append(f"وضعیت هزینه: {cost_lookup_status}")

            if row["cost_lookup_attempts"]:
                extra_parts.append(f"تلاش: {row['cost_lookup_attempts']}")

            status_text = " | ".join([p for p in extra_parts if p])
            self.dialogue_table.setItem(r, 9, self._make_readonly_item(status_text))

            changed = "بله" if row["status"] == "modified" else ""
            change_item = self._make_readonly_item(changed)
            if row["status"] == "modified":
                change_item.setBackground(QColor("#fff3cd"))
            self.dialogue_table.setItem(r, 10, change_item)

            if row["status"] in ("modified", "no_character"):
                for col in range(self.dialogue_table.columnCount()):
                    item = self.dialogue_table.item(r, col)
                    if item:
                        item.setBackground(QColor("#fff8e1"))

        self.dialogue_table.blockSignals(False)
        self._loading_table = False

    def mark_line_modified(self, line_id: int, speaker_name: str, character_id, text_content: str):
        line = self.db.get_dialogue_line(line_id)
        if not line:
            return

        self.db.update_dialogue_line(
            line_id=line_id,
            speaker_name=speaker_name,
            character_id=character_id,
            text_content=text_content,
            audio_file_path=line["audio_file_path"] or "",
            request_id=line["request_id"] or "",
            estimated_cost=line["estimated_cost"] or "",
            status="modified" if character_id else "no_character",
        )

    def on_dialogue_item_changed(self, item):
        if self._loading_table:
            return

        row = item.row()
        col = item.column()

        if col not in (2, 4):
            return

        line_id_item = self.dialogue_table.item(row, 0)
        if not line_id_item:
            return

        line_id = int(line_id_item.text())
        speaker_name = (self.dialogue_table.item(row, 2).text() or "").strip()
        text_content = (self.dialogue_table.item(row, 4).text() or "").strip()

        combo = self.dialogue_table.cellWidget(row, 3)
        character_id = combo.currentData() if combo else None

        if col == 2 and speaker_name:
            char_row = self.db.get_character_by_name(self.current_project_id, speaker_name)
            if char_row and combo:
                idx = combo.findData(char_row["id"])
                if idx >= 0:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)
                    character_id = char_row["id"]

        self.mark_line_modified(line_id, speaker_name, character_id, text_content)
        self.load_dialogue_lines()

    def on_character_combo_changed(self, line_id: int, combo: QComboBox):
        if self._loading_table:
            return

        row = self.find_row_by_line_id(line_id)
        if row < 0:
            return

        speaker_name = (self.dialogue_table.item(row, 2).text() or "").strip()
        text_content = (self.dialogue_table.item(row, 4).text() or "").strip()
        character_id = combo.currentData()

        self.mark_line_modified(line_id, speaker_name, character_id, text_content)
        self.load_dialogue_lines()

    def find_row_by_line_id(self, line_id: int) -> int:
        for row in range(self.dialogue_table.rowCount()):
            item = self.dialogue_table.item(row, 0)
            if item and item.text().isdigit() and int(item.text()) == line_id:
                return row
        return -1

    def lookup_and_store_cost(self, line_id: int, request_id: str):
        if not self.is_cost_management_enabled():
            self.log("مدیریت هزینه غیرفعال است.")
            self.db.update_dialogue_line_cost_status(line_id, "disabled", 0, "cost management disabled")
            return

        if not request_id:
            self.log(f"استعلام هزینه برای خط {line_id} انجام نشد: request_id خالی است.")
            self.db.update_dialogue_line_cost_status(line_id, "failed", 0, "empty request_id")
            return

        auto_lookup = self.db.get_setting("auto_lookup_cost", "1") == "1"
        if not auto_lookup:
            self.db.update_dialogue_line_cost_status(line_id, "disabled", 0, "auto lookup disabled")
            return

        if self.cost_worker is not None:
            self.log("یک استعلام هزینه دیگر در حال اجرا است. این درخواست در حال حاضر نادیده گرفته شد.")
            return

        try:
            api = self.get_api_client()
            self.pending_cost_line_id = line_id
            self.pending_cost_request_id = request_id

            self.db.update_dialogue_line_cost_status(line_id, "pending", 0, "")
            self.db.update_transaction_lookup_status(request_id, "pending", 0, "")

            self.cost_worker = CostLookupWorker(api, request_id, retries=6, delay_seconds=5, parent=self)
            self.cost_worker.finished_ok.connect(self.on_cost_lookup_finished)
            self.cost_worker.failed.connect(self.on_cost_lookup_failed)
            self.cost_worker.start()

            self.log(f"استعلام هزینه برای request_id={request_id} در پس‌زمینه شروع شد.")
        except Exception as e:
            self.db.update_dialogue_line_cost_status(line_id, "failed", 0, str(e))
            self.db.update_transaction_lookup_status(request_id, "failed", 0, str(e))
            self.log(f"استعلام خودکار هزینه شروع نشد: {e}")

    def on_cost_lookup_finished(self, result: dict):
        line_id = self.pending_cost_line_id
        request_id = self.pending_cost_request_id

        if not line_id or not request_id:
            self.log("هشدار: نتیجه lookup دریافت شد اما line_id/request_id در وضعیت pending موجود نیست.")
            self.cost_worker = None
            return

        cost_usd = result.get("cost_usd", "")
        cost_irr = result.get("cost_irr", "")
        raw_response = result.get("raw_response", "")
        attempts = int(result.get("attempt", 0))
        ready = bool(result.get("ready", False))

        self.db.update_transaction_costs(
            request_id=request_id,
            cost_usd=cost_usd,
            cost_irr=cost_irr,
            raw_response=raw_response,
        )

        estimated_parts = []
        if cost_usd:
            estimated_parts.append(f"USD: {cost_usd}")
        if cost_irr:
            estimated_parts.append(f"IRR: {cost_irr}")
        estimated_cost = " | ".join(estimated_parts)

        if estimated_cost:
            self.db.update_dialogue_line_cost(line_id, estimated_cost)

        if ready:
            self.db.update_dialogue_line_cost_status(line_id, "done", attempts, "")
            self.db.update_transaction_lookup_status(request_id, "done", attempts, "")
            self.last_cost_label.setText(f"هزینه آخرین درخواست: {estimated_cost or 'نامشخص'}")
            self.log(f"هزینه request_id={request_id} با موفقیت ثبت شد. attempts={attempts}")
        else:
            self.db.update_dialogue_line_cost_status(line_id, "pending", attempts, "cost not ready yet")
            self.db.update_transaction_lookup_status(request_id, "pending", attempts, "cost not ready yet")
            self.log(f"lookup انجام شد ولی هنوز هزینه نهایی برای request_id={request_id} آماده نبود. attempts={attempts}")

        self.load_dialogue_lines()
        self.pending_cost_line_id = None
        self.pending_cost_request_id = None
        self.cost_worker = None

    def on_cost_lookup_failed(self, error_text: str):
        line_id = self.pending_cost_line_id
        request_id = self.pending_cost_request_id

        if line_id:
            self.db.update_dialogue_line_cost_status(line_id, "failed", 0, error_text)
        if request_id:
            self.db.update_transaction_lookup_status(request_id, "failed", 0, error_text)

        self.log(f"استعلام خودکار هزینه انجام نشد: {error_text}")
        if request_id:
            self.log(f"جزئیات: request_id={request_id}")
        self.log("فرمت درست lookup باید به شکل transaction_ids باشد و شناسه از هدر x-request-id گرفته شود.")
        self.log("تولید صدا انجام شده است و فقط استعلام هزینه ناموفق بوده است.")

        self.load_dialogue_lines()
        self.pending_cost_line_id = None
        self.pending_cost_request_id = None
        self.cost_worker = None

    def start_generate_audio_for_line(self, line_id: int, batch_mode: str = ""):
        line = self.db.get_dialogue_line(line_id)
        if not line:
            raise ValueError("خط دیالوگ پیدا نشد.")

        if not line["character_id"]:
            raise ValueError(f"برای گوینده «{line['speaker_name'] or 'نامشخص'}» شخصیت تعریف یا متصل نشده است.")

        model = self.db.get_setting("avalai_tts_model", DEFAULT_TTS_MODEL)
        default_voice = self.db.get_setting("avalai_default_voice", "nova")
        default_speed = float(self.db.get_setting("avalai_default_speed", "1.0"))
        audio_format = self.audio_format_combo.currentText()

        voice_name = line["voice_name"] or default_voice
        speed = float(line["speed"] or default_speed)
        text_content = line["text_content"] or ""

        if not text_content.strip():
            raise ValueError("متن خط دیالوگ خالی است.")

        project_audio_dir = self.get_project_audio_dir()
        safe_name = f"line_{line['line_number']:03d}_{line_id}.{audio_format}"
        output_file = project_audio_dir / safe_name

        api = self.get_api_client()
        self.pending_audio_context = {
            "line_id": line_id,
            "model": model,
            "voice_name": voice_name,
            "text_content": text_content,
            "batch_mode": batch_mode,
            "line_number": line["line_number"],
        }

        self.audio_worker = AudioGenerationWorker(
            api=api,
            model=model,
            voice=voice_name,
            text=text_content,
            speed=speed,
            output_file=output_file,
            parent=self,
        )
        self.audio_worker.progress.connect(self.progress_bar.setValue)
        self.audio_worker.finished_ok.connect(self.on_audio_generation_finished)
        self.audio_worker.failed.connect(self.on_audio_generation_failed)
        self.audio_worker.start()

    def on_audio_generation_finished(self, result: dict):
        ctx = self.pending_audio_context or {}
        line_id = ctx.get("line_id")
        model = ctx.get("model", "")
        voice_name = ctx.get("voice_name", "")
        text_content = ctx.get("text_content", "")
        batch_mode = ctx.get("batch_mode", "")
        line_number = ctx.get("line_number", "?")

        request_id = result.get("request_id", "")
        self.db.update_dialogue_line_audio(
            line_id=line_id,
            audio_file_path=result["output_file"],
            request_id=request_id,
            estimated_cost="",
            status="generated",
        )

        log_enabled = self.db.get_setting("enable_transaction_logging", "1") == "1"
        if log_enabled:
            self.db.add_transaction(
                project_id=self.current_project_id,
                dialogue_line_id=line_id,
                request_id=request_id,
                model_name=model,
                voice_name=voice_name,
                input_text=text_content,
                cost_usd="",
                cost_irr="",
                raw_response=result.get("raw_response", ""),
            )

        self.log(f"فایل صوتی خط {line_number} تولید شد: {result['output_file']}")
        if request_id:
            self.log(f"request_id: {request_id}")

        self.audio_worker = None
        self.pending_audio_context = None
        self.load_dialogue_lines()

        if self.is_cost_management_enabled():
            self.lookup_and_store_cost(line_id, request_id)

        if batch_mode == "changed":
            self.process_next_changed_line()
        elif batch_mode == "all":
            self.process_next_all_line()

    def on_audio_generation_failed(self, error_text: str):
        ctx = self.pending_audio_context or {}
        batch_mode = ctx.get("batch_mode", "")
        line_number = ctx.get("line_number", "?")

        self.progress_bar.setValue(0)
        self.audio_worker = None
        self.pending_audio_context = None
        self.log(f"خطا در تولید صدا برای خط {line_number}: {error_text}")

        if batch_mode == "changed":
            self.process_next_changed_line()
        elif batch_mode == "all":
            self.process_next_all_line()
        else:
            QMessageBox.critical(self, "خطا", error_text)

    def generate_selected_audio(self):
        if not self.require_project():
            return

        if self.audio_worker is not None:
            QMessageBox.information(self, "اطلاع", "یک عملیات تولید صدا در حال اجرا است. لطفاً صبر کنید.")
            return

        line_id = self.get_selected_line_id()
        if not line_id:
            QMessageBox.warning(self, "خطا", "ابتدا یک خط را از جدول انتخاب کنید.")
            return

        try:
            self.progress_bar.setValue(5)
            self.start_generate_audio_for_line(line_id)
        except Exception as e:
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "خطا", str(e))
            self.log(f"خطا در شروع تولید صدای خط: {e}")

    def generate_changed_audio(self):
        if not self.require_project():
            return

        if self.audio_worker is not None:
            QMessageBox.information(self, "اطلاع", "یک عملیات تولید صدا در حال اجرا است. لطفاً صبر کنید.")
            return

        rows = self.db.get_dialogue_lines(self.current_project_id)
        self.batch_changed_queue = [
            row["id"] for row in rows
            if row["status"] in ("modified", "no_character") or not row["audio_file_path"]
        ]

        if not self.batch_changed_queue:
            QMessageBox.information(self, "اطلاع", "هیچ خط تغییرکرده‌ای برای بازسازی وجود ندارد.")
            return

        self.log(f"بازسازی {len(self.batch_changed_queue)} خط تغییرکرده شروع شد.")
        self.process_next_changed_line()

    def process_next_changed_line(self):
        while self.batch_changed_queue:
            line_id = self.batch_changed_queue.pop(0)
            line = self.db.get_dialogue_line(line_id)
            if not line:
                continue

            if not line["character_id"]:
                self.log(f"خط {line['line_number']} به دلیل نداشتن شخصیت رد شد.")
                continue

            try:
                self.start_generate_audio_for_line(line_id, batch_mode="changed")
                return
            except Exception as e:
                self.log(f"خطا در بازسازی خط {line['line_number']}: {e}")

        self.load_dialogue_lines()
        self.progress_bar.setValue(100)
        self.log("بازسازی خطوط تغییرکرده پایان یافت.")

    def generate_all_audio(self):
        if not self.require_project():
            return

        if self.audio_worker is not None:
            QMessageBox.information(self, "اطلاع", "یک عملیات تولید صدا در حال اجرا است. لطفاً صبر کنید.")
            return

        rows = self.db.get_dialogue_lines(self.current_project_id)
        if not rows:
            QMessageBox.warning(self, "خطا", "هیچ خطی برای تولید وجود ندارد.")
            return

        self.batch_all_queue = [row["id"] for row in rows]
        self.log(f"تولید {len(self.batch_all_queue)} خط شروع شد.")
        self.process_next_all_line()

    def process_next_all_line(self):
        while self.batch_all_queue:
            line_id = self.batch_all_queue.pop(0)
            line = self.db.get_dialogue_line(line_id)
            if not line:
                continue

            try:
                self.start_generate_audio_for_line(line_id, batch_mode="all")
                return
            except Exception as e:
                self.log(f"خطا در خط {line['line_number']}: {e}")

        self.load_dialogue_lines()
        self.progress_bar.setValue(100)
        self.log("تولید همه خطوط پایان یافت.")

    def refresh_failed_costs(self):
        if not self.require_project():
            return

        if not self.is_cost_management_enabled():
            QMessageBox.information(self, "اطلاع", "مدیریت هزینه غیرفعال است.")
            return

        if self.cost_worker is not None:
            QMessageBox.information(self, "اطلاع", "یک استعلام هزینه در حال اجرا است. لطفاً صبر کنید.")
            return

        rows = self.db.get_dialogue_lines_with_failed_cost_lookup(self.current_project_id)
        if not rows:
            QMessageBox.information(self, "اطلاع", "هیچ خطی با هزینه ناموفق یا معلق پیدا نشد.")
            return

        row = rows[0]
        line_id = row["id"]
        request_id = (row["request_id"] or "").strip()

        if not request_id:
            self.log(f"خط {row['line_number']} request_id ندارد و رد شد.")
            return

        self.log(f"به‌روزرسانی هزینه برای خط {row['line_number']} شروع شد.")
        self.lookup_and_store_cost(line_id, request_id)

    def play_selected_audio(self):
        line_id = self.get_selected_line_id()
        if not line_id:
            QMessageBox.warning(self, "خطا", "ابتدا یک خط را انتخاب کنید.")
            return

        line = self.db.get_dialogue_line(line_id)
        if not line or not line["audio_file_path"]:
            QMessageBox.warning(self, "خطا", "برای این خط فایل صوتی ثبت نشده است.")
            return

        try:
            open_audio_file(line["audio_file_path"])
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def merge_all_audio(self):
        if not self.require_project():
            return

        rows = self.db.get_dialogue_lines(self.current_project_id)

        existing_files = []
        for row in rows:
            file_path = (row["audio_file_path"] or "").strip()
            if not file_path:
                continue
            if Path(file_path).exists():
                existing_files.append(file_path)
            else:
                self.log(f"فایل یافت نشد و نادیده گرفته شد: {file_path}")

        if not existing_files:
            QMessageBox.warning(self, "خطا", "هیچ فایل صوتی موجودی برای ادغام پیدا نشد.")
            return

        output_format = self.audio_format_combo.currentText()
        output_file = self.get_project_audio_dir() / f"merged_project_{self.current_project_id}.{output_format}"

        try:
            merge_audio_files(existing_files, str(output_file))
            self.log(f"فایل ادغام‌شده ساخته شد: {output_file}")
            QMessageBox.information(self, "موفق", f"فایل ادغام‌شده ساخته شد:\n{output_file}")
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def export_final_audio(self):
        if not self.require_project():
            return

        output_format = self.audio_format_combo.currentText()
        source_file = self.get_project_audio_dir() / f"merged_project_{self.current_project_id}.{output_format}"

        if not source_file.exists():
            QMessageBox.warning(self, "خطا", "ابتدا فایل‌ها را ادغام کنید.")
            return

        selected_file, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره خروجی نهایی",
            str(source_file),
            f"Audio Files (*.{output_format})"
        )
        if not selected_file:
            return

        try:
            data = source_file.read_bytes()
            Path(selected_file).write_bytes(data)
            self.log(f"خروجی نهایی ذخیره شد: {selected_file}")
            QMessageBox.information(self, "موفق", "خروجی نهایی ذخیره شد.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def open_avalai_settings(self):
        dialog = AvalaiSettingsDialog(self.db, self)
        dialog.exec_()
        self._load_defaults()

    def open_characters_dialog(self):
        if not self.require_project():
            return

        if self.audio_worker or self.cost_worker:
            QMessageBox.information(self, "اطلاع", "ابتدا منتظر پایان عملیات جاری بمانید.")
            return

        dialog = CharactersDialog(self.db, self.current_project_id, self)
        dialog.exec_()
        self.db.remap_dialogue_lines_characters(self.current_project_id)
        self.load_dialogue_lines()

    def open_transactions_dialog(self):
        dialog = TransactionsDialog(self.db, self)
        dialog.exec_()

    def open_help_dialog(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def open_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec_()