import os
import sys
import json
import time
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QSlider, QSpinBox, QDateEdit,
    QSplitter, QProgressBar, QMessageBox, QFileDialog, QFrame,
    QScrollArea, QAbstractItemView, QSizePolicy, QTextBrowser,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QTimer, QUrl
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rc('axes', unicode_minus=False)


import config
from services.firestore_service import (
    seed_sample_data_if_empty, get_all_data, add_data,
    update_data, delete_data, get_data_summary,
    list_conversations, get_conversation, save_conversation,
    delete_conversation, FIREBASE_INITIALIZED
)
from services.ai_service import generate_ai_chat_response, plan_10_suno_prompts
from services.suno_service import generate_suno_music, check_suno_status, download_audio_to_pc


# =====================================================================
# Modern Dark Theme Stylesheet (QSS)
# =====================================================================
DARK_STYLE = """
QMainWindow {
    background-color: #0f172a;
}
QWidget {
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
    font-size: 13px;
}
QFrame.card {
    background-color: #1e293b;
    border-radius: 12px;
    border: 1px solid #334155;
    padding: 12px;
}
QFrame.subcard {
    background-color: #182234;
    border-radius: 8px;
    border: 1px solid #283548;
    padding: 8px;
}
QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #0f172a;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background-color: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
    border-bottom: none;
}
QTabBar::tab:hover:!selected {
    background-color: #334155;
    color: #f8fafc;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}
QPushButton.btn-secondary {
    background-color: #334155;
    color: #f1f5f9;
}
QPushButton.btn-secondary:hover {
    background-color: #475569;
}
QPushButton.btn-success {
    background-color: #059669;
    color: #ffffff;
}
QPushButton.btn-success:hover {
    background-color: #047857;
}
QPushButton.btn-danger {
    background-color: #dc2626;
    color: #ffffff;
}
QPushButton.btn-danger:hover {
    background-color: #b91c1c;
}
QPushButton.btn-purple {
    background-color: #7c3aed;
    color: #ffffff;
}
QPushButton.btn-purple:hover {
    background-color: #6d28d9;
}
QPushButton.btn-chip {
    background-color: #1e293b;
    border: 1px solid #3b82f6;
    color: #93c5fd;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 11px;
}
QPushButton.btn-chip:hover {
    background-color: #2563eb;
    color: #ffffff;
}
QLineEdit, QTextEdit, QDateEdit, QSpinBox {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QSpinBox:focus {
    border: 1px solid #3b82f6;
}
QTextBrowser {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 10px;
}
QTableWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #334155;
    color: #f1f5f9;
}
QTableWidget::item {
    padding: 6px;
}
QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #0f172a;
    color: #94a3b8;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #334155;
    font-weight: bold;
}
QScrollBar:vertical {
    background: #0f172a;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #8b5cf6);
    border-radius: 5px;
}
QSlider::groove:horizontal {
    border: 1px solid #334155;
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #3b82f6;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #93c5fd;
}
QRadioButton {
    color: #f1f5f9;
    spacing: 8px;
    font-size: 12px;
    font-weight: 500;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #64748b;
    background-color: #1e293b;
}
QRadioButton::indicator:checked {
    border-color: #3b82f6;
    background-color: #2563eb;
}
"""


# =====================================================================
# Background Worker Threads
# =====================================================================
class ChatWorker(QThread):
    finished = pyqtSignal(str, str, dict, list)
    error = pyqtSignal(str)

    def __init__(self, user_message: str, conv_id: Optional[str]):
        super().__init__()
        self.user_message = user_message
        self.conv_id = conv_id

    def run(self):
        try:
            ai_reply, saved_conv_id, summary_context, suno_prompts = generate_ai_chat_response(
                self.user_message, self.conv_id
            )
            self.finished.emit(ai_reply, saved_conv_id, summary_context or {}, suno_prompts or [])
        except Exception as e:
            self.error.emit(str(e))


class SunoPlanWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, mood: str, condition: str, custom_request: str, include_lyrics: bool = True):
        super().__init__()
        self.mood = mood
        self.condition = condition
        self.custom_request = custom_request
        self.include_lyrics = include_lyrics

    def run(self):
        try:
            prompts = plan_10_suno_prompts(
                self.mood, self.condition, self.custom_request, self.include_lyrics
            )
            self.finished.emit(prompts)
        except Exception as e:
            self.error.emit(str(e))


class SunoGenerateWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, prompt: str, tags: str, title: str, lyrics: str):
        super().__init__()
        self.prompt = prompt
        self.tags = tags
        self.title = title
        self.lyrics = lyrics

    def run(self):
        try:
            res = generate_suno_music(self.prompt, self.tags, self.title, self.lyrics)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))


class SunoStatusWorker(QThread):
    status_updated = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def run(self):
        try:
            res = check_suno_status(self.task_id)
            self.status_updated.emit(res)
        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, audio_url: str, file_name: str, save_dir: Optional[str] = None):
        super().__init__()
        self.audio_url = audio_url
        self.file_name = file_name
        self.save_dir = save_dir

    def run(self):
        try:
            res = download_audio_to_pc(self.audio_url, self.file_name, self.save_dir)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))


# =====================================================================
# Main Application Window
# =====================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("나만의 AI 비서 & Suno AI 음악 스튜디오 (PyQt5)")
        self.resize(1200, 820)
        self.setMinimumSize(1000, 700)

        # State
        self.current_conv_id: Optional[str] = None
        self.all_data: List[Dict[str, Any]] = []
        self.current_editing_id: Optional[str] = None
        self.suno_prompts_cache: List[Dict[str, Any]] = []
        self.current_task_id: Optional[str] = None
        self.current_audio_url: Optional[str] = None

        # Media Player
        self.media_player = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.media_player.positionChanged.connect(self.on_player_position_changed)
        self.media_player.durationChanged.connect(self.on_player_duration_changed)
        self.media_player.stateChanged.connect(self.on_player_state_changed)

        # Polling Timer for Suno
        self.suno_poll_timer = QTimer(self)
        self.suno_poll_timer.setInterval(3500)
        self.suno_poll_timer.timeout.connect(self.poll_suno_status)

        # Setup UI
        self.init_ui()

        # Seed sample data on first start if needed
        seed_sample_data_if_empty()

        # Load initial data
        self.refresh_data_tab()
        self.load_conversations_tab()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Top Brand Header
        header = self.create_header()
        main_layout.addWidget(header)

        # 2. Main Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tab_chat = self.create_chat_tab()
        self.tab_data = self.create_data_tab()
        self.tab_music = self.create_music_tab()
        self.tab_history = self.create_history_tab()

        self.tabs.addTab(self.tab_chat, "💬 AI 비서 대화")
        self.tabs.addTab(self.tab_data, "📊 컨디션 데이터 (CRUD & 차트)")
        self.tabs.addTab(self.tab_music, "🎵 Suno AI 스튜디오")
        self.tabs.addTab(self.tab_history, "🕰️ 대화 기록 보관소")

        main_layout.addWidget(self.tabs)

        # 3. Bottom Status Bar
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)

    # -----------------------------------------------------------------
    # Top Header
    # -----------------------------------------------------------------
    def create_header(self) -> QWidget:
        header_frame = QFrame()
        header_frame.setProperty("class", "card")
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(12, 10, 12, 10)

        title_layout = QVBoxLayout()
        title_label = QLabel("🤖 나만의 AI 비서 & Suno AI 음악 생성 스튜디오")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #f8fafc;")

        subtitle_label = QLabel(
            "시계열 컨디션/기분 분석 • 문맥 주입 AI 비서 • 10가지 Suno 음악 기획 & 내 PC 저장"
        )
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Database badge
        db_type = "Firestore 온라인" if FIREBASE_INITIALIZED else "로컬 DB (local_db.json)"
        db_badge = QLabel(f"💾 {db_type}")
        db_badge.setStyleSheet(
            "background-color: #1e293b; color: #10b981; border: 1px solid #10b981; "
            "border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: bold;"
        )
        layout.addWidget(db_badge)

        return header_frame

    # -----------------------------------------------------------------
    # Tab 1: AI Chat Tab
    # -----------------------------------------------------------------
    def create_chat_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Top Context Injection Badge Banner
        self.chat_summary_badge = QLabel("📊 컨디션 데이터 요약을 불러오는 중...")
        self.chat_summary_badge.setStyleSheet(
            "background-color: #1e293b; color: #60a5fa; border-left: 4px solid #3b82f6; "
            "padding: 8px 12px; border-radius: 6px; font-weight: bold;"
        )
        layout.addWidget(self.chat_summary_badge)

        # Quick chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)
        chips_label = QLabel("빠른 질문:")
        chips_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        chips_layout.addWidget(chips_label)

        quick_questions = [
            ("🎤 가사 포함 힐링곡 10선", "피곤한데 힐링 음악 (가사 포함) 10가지 기획해줘"),
            ("🎹 가사 미포함 연주곡 10선", "집중할 때 들을 연주곡 (가사 포함하지 않음) 10가지 기획해줘"),
            ("💡 오늘 컨디션 분석", "오늘 내 컨디션과 추세 분석해줘"),
            ("⚡ 신나는 보컬곡", "기분 전환용 신나는 보컬곡 추천해줘")
        ]
        for label, q in quick_questions:
            btn = QPushButton(label)
            btn.setProperty("class", "btn-chip")
            btn.clicked.connect(lambda checked, text=q: self.send_quick_chat(text))
            chips_layout.addWidget(btn)

        chips_layout.addStretch()
        layout.addLayout(chips_layout)

        # Chat history display (QTextBrowser)
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.anchorClicked.connect(self.on_chat_link_clicked)
        layout.addWidget(self.chat_display, stretch=1)

        # Welcome message
        self.append_chat_message(
            "assistant",
            "안녕하세요! 당신만을 위한 **AI 비서**입니다. 😊<br>"
            "저장된 시계열 컨디션 데이터를 바탕으로 현재 상태를 고려하여 대화를 나누고, "
            "어울리는 맞춤형 10가지 Suno AI 음악을 추천해 드립니다.<br>"
            "오늘 컨디션이나 기분은 어떠신가요?"
        )

        # Input Row
        input_frame = QFrame()
        input_frame.setProperty("class", "card")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 6, 8, 6)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("비서에게 메시지를 입력하세요... (Enter를 누르면 전송됩니다)")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input, stretch=1)

        self.btn_send_chat = QPushButton("전송")
        self.btn_send_chat.clicked.connect(self.send_chat_message)
        input_layout.addWidget(self.btn_send_chat)

        btn_new_chat = QPushButton("새 대화")
        btn_new_chat.setProperty("class", "btn-secondary")
        btn_new_chat.clicked.connect(self.reset_chat_session)
        input_layout.addWidget(btn_new_chat)

        layout.addWidget(input_frame)

        return widget

    def send_quick_chat(self, text: str):
        self.chat_input.setText(text)
        self.send_chat_message()

    def send_chat_message(self):
        text = self.chat_input.text().strip()
        if not text:
            return

        self.chat_input.clear()
        self.append_chat_message("user", text)

        self.btn_send_chat.setEnabled(False)
        self.chat_input.setEnabled(False)
        self.append_chat_message("assistant", "⏳ <i>컨디션 요약 데이터를 분석하여 답변을 생성 중입니다...</i>", temp=True)

        self.chat_worker = ChatWorker(text, self.current_conv_id)
        self.chat_worker.finished.connect(self.on_chat_success)
        self.chat_worker.error.connect(self.on_chat_error)
        self.chat_worker.start()

    def on_chat_success(self, ai_reply: str, conv_id: str, summary_ctx: dict, suno_prompts: list):
        self.btn_send_chat.setEnabled(True)
        self.chat_input.setEnabled(True)
        self.chat_input.setFocus()
        self.current_conv_id = conv_id

        # Update summary badge
        if summary_ctx:
            avg_val = summary_ctx.get("metrics", {}).get("average", "N/A")
            trend = summary_ctx.get("trend", "보통")
            period = summary_ctx.get("period", "")
            self.chat_summary_badge.setText(
                f"📊 최근 컨디션 요약: 기간({period}) | 평균 {avg_val}/10 ({trend}) 반영 중"
            )

        # Remove temp loading message and append reply
        self.remove_temp_chat_message()
        self.append_chat_message("assistant", ai_reply)

        # If suno prompts generated in response
        if suno_prompts and len(suno_prompts) > 0:
            self.suno_prompts_cache = suno_prompts
            prompts_html = "<br><div style='background-color:#1e293b; padding:10px; border-radius:8px; border:1px solid #3b82f6;'>"
            prompts_html += "<b style='color:#60a5fa;'>🎵 맞춤형 Suno AI 음악 프롬프트 10가지가 기획되었습니다!</b><br><br>"
            for idx, p in enumerate(suno_prompts[:5]):
                prompts_html += f"<b>#{idx+1} {p.get('title')}</b> ({p.get('mood_keyword')})<br>"
                prompts_html += f"<span style='color:#94a3b8; font-size:11px;'>{p.get('suno_prompt')}</span><br>"
                prompts_html += f"<a href='suno_select:{idx}' style='color:#38bdf8; text-decoration:none; font-weight:bold;'>▶ 이 곡 Suno 스튜디오로 전송하기</a><br><br>"
            prompts_html += "<span style='color:#cbd5e1; font-size:11px;'>👉 전체 10개 곡은 상단 <b>[Suno AI 스튜디오]</b> 탭에서 확인하실 수 있습니다.</span></div>"
            self.append_chat_message("assistant", prompts_html)

            # Auto load into Music tab
            self.load_suno_prompts_into_table(suno_prompts)

        # Refresh conversations history
        self.load_conversations_tab()

    def on_chat_error(self, err_msg: str):
        self.btn_send_chat.setEnabled(True)
        self.chat_input.setEnabled(True)
        self.remove_temp_chat_message()
        self.append_chat_message("assistant", f"❌ <b>오류 발생:</b> {err_msg}")

    def on_chat_link_clicked(self, url: QUrl):
        url_str = url.toString()
        if url_str.startswith("suno_select:"):
            try:
                idx = int(url_str.split(":")[1])
                if idx < len(self.suno_prompts_cache):
                    self.populate_suno_form(self.suno_prompts_cache[idx])
                    self.tabs.setCurrentWidget(self.tab_music)
            except Exception as e:
                print(f"Error handling link: {e}")

    def append_chat_message(self, role: str, message: str, temp: bool = False):
        time_str = datetime.now().strftime("%H:%M")
        if role == "user":
            html = f"""
            <div style='margin-bottom: 12px; text-align: right;'>
                <div style='display: inline-block; background-color: #2563eb; color: #ffffff;
                            padding: 10px 14px; border-radius: 12px; border-bottom-right-radius: 2px;
                            max-width: 80%; text-align: left; font-size: 13px;'>
                    {message.replace(chr(10), '<br>')}
                </div>
                <div style='font-size: 10px; color: #64748b; margin-top: 2px;'>{time_str} • 나</div>
            </div>
            """
        else:
            temp_id = " id='temp_msg'" if temp else ""
            formatted = message.replace("\n", "<br>")
            html = f"""
            <div{temp_id} style='margin-bottom: 12px; text-align: left;'>
                <div style='font-size: 11px; color: #60a5fa; font-weight: bold; margin-bottom: 4px;'>🤖 AI 비서</div>
                <div style='display: inline-block; background-color: #1e293b; color: #f1f5f9;
                            padding: 12px 16px; border-radius: 12px; border-bottom-left-radius: 2px;
                            border: 1px solid #334155; max-width: 85%; font-size: 13px; line-height: 1.5;'>
                    {formatted}
                </div>
                <div style='font-size: 10px; color: #64748b; margin-top: 2px;'>{time_str}</div>
            </div>
            """
        self.chat_display.append(html)

    def remove_temp_chat_message(self):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)

    def reset_chat_session(self):
        self.current_conv_id = None
        self.chat_display.clear()
        self.append_chat_message("assistant", "새 대화 세션이 시작되었습니다. 무엇을 도와드릴까요?")

    # -----------------------------------------------------------------
    # Tab 2: Data Management (CRUD & Time-Series Chart)
    # -----------------------------------------------------------------
    def create_data_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Top KPI Summary Cards
        kpi_frame = QFrame()
        kpi_frame.setProperty("class", "card")
        kpi_layout = QHBoxLayout(kpi_frame)

        self.kpi_period = self.create_kpi_widget("📅 기록 기간", "로딩 중...")
        self.kpi_count = self.create_kpi_widget("🔢 총 데이터 수", "0개")
        self.kpi_avg = self.create_kpi_widget("⭐ 평균 컨디션", "0.0 / 10")
        self.kpi_range = self.create_kpi_widget("🏆 최고 / 최저", "0 / 0")
        self.kpi_trend = self.create_kpi_widget("📈 최근 트렌드", "보통")

        kpi_layout.addWidget(self.kpi_period)
        kpi_layout.addWidget(self.kpi_count)
        kpi_layout.addWidget(self.kpi_avg)
        kpi_layout.addWidget(self.kpi_range)
        kpi_layout.addWidget(self.kpi_trend)
        layout.addWidget(kpi_frame)

        # Main Splitter (Left: CRUD Form & Table, Right: Matplotlib Chart)
        splitter = QSplitter(Qt.Horizontal)

        # --- Left Panel ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Form Card
        form_card = QFrame()
        form_card.setProperty("class", "card")
        form_layout = QVBoxLayout(form_card)

        form_title = QLabel("📝 컨디션/기분 데이터 등록 및 수정")
        form_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        form_layout.addWidget(form_title)

        input_row1 = QHBoxLayout()
        input_row1.addWidget(QLabel("날짜:"))
        self.input_date = QDateEdit()
        self.input_date.setCalendarPopup(True)
        self.input_date.setDate(QDate.currentDate())
        input_row1.addWidget(self.input_date)

        input_row1.addWidget(QLabel("컨디션 지수 (1~10):"))
        self.slider_val = QSlider(Qt.Horizontal)
        self.slider_val.setRange(1, 10)
        self.slider_val.setValue(7)

        self.spin_val = QSpinBox()
        self.spin_val.setRange(1, 10)
        self.spin_val.setValue(7)

        self.slider_val.valueChanged.connect(self.spin_val.setValue)
        self.spin_val.valueChanged.connect(self.slider_val.setValue)

        input_row1.addWidget(self.slider_val)
        input_row1.addWidget(self.spin_val)
        form_layout.addLayout(input_row1)

        input_row2 = QHBoxLayout()
        input_row2.addWidget(QLabel("메모:"))
        self.input_memo = QLineEdit()
        self.input_memo.setPlaceholderText("기분, 수면 상태, 피로도, 일기 등 간단 메모")
        input_row2.addWidget(self.input_memo)
        form_layout.addLayout(input_row2)

        btn_row = QHBoxLayout()
        self.btn_save_data = QPushButton("➕ 데이터 추가")
        self.btn_save_data.setProperty("class", "btn-success")
        self.btn_save_data.clicked.connect(self.on_save_data_clicked)
        btn_row.addWidget(self.btn_save_data)

        self.btn_cancel_edit = QPushButton("취소")
        self.btn_cancel_edit.setProperty("class", "btn-secondary")
        self.btn_cancel_edit.setVisible(False)
        self.btn_cancel_edit.clicked.connect(self.cancel_data_edit)
        btn_row.addWidget(self.btn_cancel_edit)

        form_layout.addLayout(btn_row)
        left_layout.addWidget(form_card)

        # Table Card
        table_card = QFrame()
        table_card.setProperty("class", "card")
        table_layout = QVBoxLayout(table_card)

        table_header = QHBoxLayout()
        self.table_count_label = QLabel("📋 저장된 데이터 목록 (0건)")
        self.table_count_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        table_header.addWidget(self.table_count_label)
        table_header.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 날짜/메모 검색...")
        self.search_input.textChanged.connect(self.filter_data_table)
        table_header.addWidget(self.search_input)
        table_layout.addLayout(table_header)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["날짜", "지수", "메모", "수정", "삭제"])
        self.data_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.data_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.data_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.data_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.data_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table_layout.addWidget(self.data_table)

        left_layout.addWidget(table_card, stretch=1)
        splitter.addWidget(left_widget)

        # --- Right Panel: Matplotlib Chart ---
        right_widget = QFrame()
        right_widget.setProperty("class", "card")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)

        chart_title = QLabel("📈 시계열 컨디션 변화 추세 (최근 기록 시각화)")
        chart_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        chart_title.setStyleSheet("color: #60a5fa;")
        right_layout.addWidget(chart_title)

        # Matplotlib Figure & Canvas
        self.figure = Figure(figsize=(6, 5), facecolor='#1e293b')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.canvas)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 5)

        layout.addWidget(splitter)
        return widget

    def create_kpi_widget(self, title: str, default_val: str) -> QWidget:
        box = QFrame()
        box.setProperty("class", "subcard")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(8, 6, 8, 6)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v_lbl = QLabel(default_val)
        v_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        v_lbl.setStyleSheet("color: #f8fafc;")

        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        box.val_label = v_lbl
        return box

    def refresh_data_tab(self):
        try:
            self.all_data = get_all_data()
            summary = get_data_summary()

            # Update KPI
            self.kpi_period.val_label.setText(summary.get("period", "N/A"))
            self.kpi_count.val_label.setText(f"{summary.get('count', 0)}개")
            metrics = summary.get("metrics", {})
            self.kpi_avg.val_label.setText(f"{metrics.get('average', 0)} / 10")
            self.kpi_range.val_label.setText(f"{metrics.get('max', 0)} / {metrics.get('min', 0)}")
            self.kpi_trend.val_label.setText(summary.get("trend", "보통"))

            # Update chat badge
            self.chat_summary_badge.setText(
                f"📊 최근 컨디션 요약: 기간({summary.get('period')}) | 총 {summary.get('count')}개 | 평균 {metrics.get('average')}/10 ({summary.get('trend')})"
            )

            # Populate Table
            self.populate_data_table(self.all_data)

            # Draw Chart
            self.draw_chart(self.all_data)
        except Exception as e:
            print(f"Error refreshing data tab: {e}")

    def populate_data_table(self, items: List[Dict[str, Any]]):
        self.table_count_label.setText(f"📋 저장된 데이터 목록 ({len(items)}건)")
        self.data_table.setRowCount(0)

        # Show items in descending date order
        sorted_items = sorted(items, key=lambda x: x.get("date", ""), reverse=True)

        for row_idx, item in enumerate(sorted_items):
            self.data_table.insertRow(row_idx)

            # Date
            date_item = QTableWidgetItem(str(item.get("date", "")))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.data_table.setItem(row_idx, 0, date_item)

            # Value with color
            val = item.get("value", 0)
            val_item = QTableWidgetItem(f"{val} 점")
            val_item.setTextAlignment(Qt.AlignCenter)
            if val >= 8:
                val_item.setForeground(QColor("#10b981"))
            elif val >= 5:
                val_item.setForeground(QColor("#38bdf8"))
            else:
                val_item.setForeground(QColor("#f59e0b"))
            self.data_table.setItem(row_idx, 1, val_item)

            # Memo
            memo_item = QTableWidgetItem(str(item.get("memo", "")))
            self.data_table.setItem(row_idx, 2, memo_item)

            # Edit Button
            btn_edit = QPushButton("수정")
            btn_edit.setProperty("class", "btn-secondary")
            btn_edit.setStyleSheet("padding: 2px 8px; font-size: 11px;")
            doc_id = item.get("id")
            btn_edit.clicked.connect(lambda checked, i=item: self.start_edit_data(i))
            self.data_table.setCellWidget(row_idx, 3, btn_edit)

            # Delete Button
            btn_del = QPushButton("삭제")
            btn_del.setProperty("class", "btn-danger")
            btn_del.setStyleSheet("padding: 2px 8px; font-size: 11px;")
            btn_del.clicked.connect(lambda checked, d_id=doc_id: self.delete_data_item(d_id))
            self.data_table.setCellWidget(row_idx, 4, btn_del)

    def filter_data_table(self, text: str):
        query = text.strip().lower()
        if not query:
            self.populate_data_table(self.all_data)
            return

        filtered = [
            item for item in self.all_data
            if query in str(item.get("date", "")).lower() or query in str(item.get("memo", "")).lower()
        ]
        self.populate_data_table(filtered)

    def start_edit_data(self, item: Dict[str, Any]):
        self.current_editing_id = item.get("id")
        d_str = item.get("date", "")
        try:
            qdate = QDate.fromString(d_str, "yyyy-MM-dd")
            if qdate.isValid():
                self.input_date.setDate(qdate)
        except Exception:
            pass

        val = int(item.get("value", 7))
        self.slider_val.setValue(val)
        self.spin_val.setValue(val)
        self.input_memo.setText(item.get("memo", ""))

        self.btn_save_data.setText("✏️ 수정 완료")
        self.btn_save_data.setProperty("class", "btn-purple")
        self.btn_save_data.setStyle(self.btn_save_data.style())
        self.btn_cancel_edit.setVisible(True)

    def cancel_data_edit(self):
        self.current_editing_id = None
        self.input_date.setDate(QDate.currentDate())
        self.slider_val.setValue(7)
        self.input_memo.clear()
        self.btn_save_data.setText("➕ 데이터 추가")
        self.btn_save_data.setProperty("class", "btn-success")
        self.btn_save_data.setStyle(self.btn_save_data.style())
        self.btn_cancel_edit.setVisible(False)

    def on_save_data_clicked(self):
        entry_date = self.input_date.date().toString("yyyy-MM-dd")
        val = self.spin_val.value()
        memo = self.input_memo.text().strip()

        if not memo:
            memo = f"컨디션 {val}점"

        entry = {
            "date": entry_date,
            "value": val,
            "memo": memo
        }

        try:
            if self.current_editing_id:
                update_data(self.current_editing_id, entry)
                QMessageBox.information(self, "성공", "데이터가 성공적으로 수정되었습니다.")
            else:
                add_data(entry)
                QMessageBox.information(self, "성공", "새 데이터가 성공적으로 등록되었습니다.")
            self.cancel_data_edit()
            self.refresh_data_tab()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")

    def delete_data_item(self, doc_id: str):
        reply = QMessageBox.question(
            self, "삭제 확인", "이 데이터를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                delete_data(doc_id)
                self.refresh_data_tab()
            except Exception as e:
                QMessageBox.critical(self, "오류", f"삭제 실패: {e}")

    def draw_chart(self, items: List[Dict[str, Any]]):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#111827')

        if not items:
            ax.text(0.5, 0.5, "표시할 데이터가 없습니다.", color="#94a3b8",
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            self.canvas.draw()
            return

        # Sort chronologically for chart
        sorted_items = sorted(items, key=lambda x: x.get("date", ""))[-35:]  # last 35 points

        dates = []
        values = []
        for i in sorted_items:
            try:
                dt = datetime.strptime(i.get("date"), "%Y-%m-%d")
                dates.append(dt)
                values.append(float(i.get("value", 0)))
            except Exception:
                continue

        if not dates:
            self.canvas.draw()
            return

        # Plot line with markers
        ax.plot(dates, values, color='#3b82f6', linewidth=2.5, marker='o',
                markersize=5, markerfacecolor='#93c5fd', markeredgecolor='#1d4ed8', label="컨디션 지수")
        ax.fill_between(dates, values, color='#3b82f6', alpha=0.2)

        # Plot average horizontal line
        avg_val = sum(values) / len(values)
        ax.axhline(avg_val, color='#10b981', linestyle='--', linewidth=1.5,
                   label=f"평균 ({avg_val:.1f})")

        # Styling
        ax.set_ylim(0, 11)
        ax.set_ylabel("컨디션 점수 (1~10)", color="#cbd5e1", fontsize=10)
        ax.set_title("최근 35개 기록 컨디션 지수 트렌드", color="#f8fafc", fontsize=11, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.3, color='#475569')

        ax.tick_params(colors='#94a3b8', labelsize=8)
        for spine in ax.spines.values():
            spine.set_color('#334155')

        # Date formatting on X axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        self.figure.autofmt_xdate(rotation=30)

        ax.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#f1f5f9', loc='upper left')
        self.figure.tight_layout()
        self.canvas.draw()

    # -----------------------------------------------------------------
    # Tab 3: Suno AI Studio (Prompts, Generation, PC Download)
    # -----------------------------------------------------------------
    def create_music_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Step 1: Prompt Planning Card
        plan_card = QFrame()
        plan_card.setProperty("class", "card")
        plan_layout = QVBoxLayout(plan_card)

        plan_title = QLabel("🎵 1단계: 내 기분 & 컨디션 기반 10가지 Suno 음악 프롬프트 자동 기획")
        plan_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        plan_title.setStyleSheet("color: #a855f7;")
        plan_layout.addWidget(plan_title)

        inputs_layout = QHBoxLayout()
        self.music_input_mood = QLineEdit()
        self.music_input_mood.setPlaceholderText("기분 (예: 편안함, 잔잔함, 우울, 신남)")
        self.music_input_mood.setText("잔잔하고 편안한")

        self.music_input_condition = QLineEdit()
        self.music_input_condition.setPlaceholderText("컨디션 (예: 피곤함, 활기참, 번아웃)")
        self.music_input_condition.setText("하루 일과 후 피곤함")

        self.music_input_custom = QLineEdit()
        self.music_input_custom.setPlaceholderText("추가 요청 (예: 로파이 어쿠스틱 기타 연주곡, 가사 없는 곡)")
        self.music_input_custom.setText("부드러운 피아노와 로파이 비트")

        inputs_layout.addWidget(QLabel("기분:"))
        inputs_layout.addWidget(self.music_input_mood)
        inputs_layout.addWidget(QLabel("컨디션:"))
        inputs_layout.addWidget(self.music_input_condition)
        inputs_layout.addWidget(QLabel("스타일/요청:"))
        inputs_layout.addWidget(self.music_input_custom)
        plan_layout.addLayout(inputs_layout)

        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("가사 설정:"))
        self.radio_lyrics_yes = QRadioButton("🎤 가사 포함 (보컬 곡)")
        self.radio_lyrics_no = QRadioButton("🎹 가사 포함하지 않음 (연주곡/Instrumental)")
        self.radio_lyrics_yes.setChecked(True)

        self.lyrics_group = QButtonGroup(self)
        self.lyrics_group.addButton(self.radio_lyrics_yes)
        self.lyrics_group.addButton(self.radio_lyrics_no)

        options_layout.addWidget(self.radio_lyrics_yes)
        options_layout.addWidget(self.radio_lyrics_no)
        options_layout.addStretch()

        self.btn_plan_prompts = QPushButton("✨ 10가지 프롬프트 기획")
        self.btn_plan_prompts.setProperty("class", "btn-purple")
        self.btn_plan_prompts.clicked.connect(self.plan_suno_prompts)
        options_layout.addWidget(self.btn_plan_prompts)

        plan_layout.addLayout(options_layout)
        layout.addWidget(plan_card)

        # 2. Step 2 & 3: Splitter for Table and Generator
        mid_splitter = QSplitter(Qt.Horizontal)

        # Prompts List Table
        list_card = QFrame()
        list_card.setProperty("class", "card")
        list_layout = QVBoxLayout(list_card)

        list_header = QHBoxLayout()
        list_title = QLabel("📋 기획된 10가지 맞춤 음악 목록 (클릭 시 아래 입력)")
        list_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        list_header.addWidget(list_title)
        list_header.addStretch()

        btn_export_sheets = QPushButton("📊 구글시트(CSV) 저장")
        btn_export_sheets.setProperty("class", "btn-chip")
        btn_export_sheets.clicked.connect(self.export_prompts_to_sheets)
        list_header.addWidget(btn_export_sheets)
        list_layout.addLayout(list_header)

        self.prompts_table = QTableWidget()
        self.prompts_table.setColumnCount(4)
        self.prompts_table.setHorizontalHeaderLabels(["#", "곡 제목", "테마 키워드", "Suno 스타일 태그"])
        self.prompts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.prompts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.prompts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.prompts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.prompts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.prompts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.prompts_table.itemClicked.connect(self.on_prompt_row_clicked)
        list_layout.addWidget(self.prompts_table)

        mid_splitter.addWidget(list_card)

        # Generation & Download Panel
        gen_card = QFrame()
        gen_card.setProperty("class", "card")
        gen_layout = QVBoxLayout(gen_card)

        gen_title = QLabel("🎧 2단계: Suno AI 음원 생성 & 내 PC 다운로드")
        gen_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        gen_title.setStyleSheet("color: #38bdf8;")
        gen_layout.addWidget(gen_title)

        # Form fields
        form_grid = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("곡 제목:"))
        self.gen_input_title = QLineEdit()
        self.gen_input_title.setPlaceholderText("음원 제목")
        row1.addWidget(self.gen_input_title)
        form_grid.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("스타일 태그:"))
        self.gen_input_tags = QLineEdit()
        self.gen_input_tags.setPlaceholderText("예: lo-fi chill hop, acoustic piano, 75 bpm")
        row2.addWidget(self.gen_input_tags)
        form_grid.addLayout(row2)

        row3 = QVBoxLayout()
        row3.addWidget(QLabel("프롬프트 상세:"))
        self.gen_input_prompt = QTextEdit()
        self.gen_input_prompt.setMaximumHeight(65)
        row3.addWidget(self.gen_input_prompt)
        form_grid.addLayout(row3)

        row4 = QVBoxLayout()
        row4.addWidget(QLabel("가사 (또는 [Instrumental]):"))
        self.gen_input_lyrics = QTextEdit()
        self.gen_input_lyrics.setMaximumHeight(65)
        self.gen_input_lyrics.setText("[Instrumental]")
        row4.addWidget(self.gen_input_lyrics)
        form_grid.addLayout(row4)

        gen_layout.addLayout(form_grid)

        # Generate Button & Status
        self.btn_generate_suno = QPushButton("🚀 Suno 음원 생성 요청 (Apiframe v2)")
        self.btn_generate_suno.setProperty("class", "btn-success")
        self.btn_generate_suno.clicked.connect(self.start_suno_generation)
        gen_layout.addWidget(self.btn_generate_suno)

        # Status Bar & Progress
        self.suno_progress = QProgressBar()
        self.suno_progress.setRange(0, 0)  # indeterminate marquee
        self.suno_progress.setVisible(False)
        gen_layout.addWidget(self.suno_progress)

        self.suno_status_label = QLabel("생성 대기 중...")
        self.suno_status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        gen_layout.addWidget(self.suno_status_label)

        # Audio Player Controls
        player_frame = QFrame()
        player_frame.setProperty("class", "subcard")
        p_layout = QVBoxLayout(player_frame)

        p_ctrl_layout = QHBoxLayout()
        self.btn_play_audio = QPushButton("▶ 재생")
        self.btn_play_audio.setEnabled(False)
        self.btn_play_audio.clicked.connect(self.toggle_audio_playback)
        p_ctrl_layout.addWidget(self.btn_play_audio)

        self.btn_stop_audio = QPushButton("⏹ 정지")
        self.btn_stop_audio.setEnabled(False)
        self.btn_stop_audio.clicked.connect(self.stop_audio_playback)
        p_ctrl_layout.addWidget(self.btn_stop_audio)

        self.player_slider = QSlider(Qt.Horizontal)
        self.player_slider.setRange(0, 100)
        self.player_slider.sliderMoved.connect(self.set_player_position)
        p_ctrl_layout.addWidget(self.player_slider, stretch=1)

        self.player_time_label = QLabel("00:00 / 00:00")
        self.player_time_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        p_ctrl_layout.addWidget(self.player_time_label)

        p_layout.addLayout(p_ctrl_layout)
        gen_layout.addWidget(player_frame)

        # PC Download Controls
        dl_frame = QFrame()
        dl_frame.setProperty("class", "subcard")
        dl_layout = QHBoxLayout(dl_frame)

        self.dl_path_label = QLabel(f"📁 저장 폴더: {config.MUSIC_DOWNLOAD_DIR}")
        self.dl_path_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        dl_layout.addWidget(self.dl_path_label, stretch=1)

        self.btn_download_pc = QPushButton("💾 내 PC로 다운로드")
        self.btn_download_pc.setEnabled(False)
        self.btn_download_pc.clicked.connect(self.download_generated_audio)
        dl_layout.addWidget(self.btn_download_pc)

        btn_open_folder = QPushButton("📂 폴더 열기")
        btn_open_folder.setProperty("class", "btn-secondary")
        btn_open_folder.clicked.connect(self.open_download_folder)
        dl_layout.addWidget(btn_open_folder)

        gen_layout.addWidget(dl_frame)

        mid_splitter.addWidget(gen_card)
        mid_splitter.setStretchFactor(0, 5)
        mid_splitter.setStretchFactor(1, 5)

        layout.addWidget(mid_splitter, stretch=1)
        return widget

    def plan_suno_prompts(self):
        mood = self.music_input_mood.text().strip() or "편안함"
        condition = self.music_input_condition.text().strip() or "보통"
        custom = self.music_input_custom.text().strip()
        include_lyrics = self.radio_lyrics_yes.isChecked()

        self.btn_plan_prompts.setEnabled(False)
        self.btn_plan_prompts.setText("기획 중...")

        self.plan_worker = SunoPlanWorker(mood, condition, custom, include_lyrics)
        self.plan_worker.finished.connect(self.on_plan_success)
        self.plan_worker.error.connect(self.on_plan_error)
        self.plan_worker.start()

    def on_plan_success(self, prompts: List[Dict[str, Any]]):
        self.btn_plan_prompts.setEnabled(True)
        self.btn_plan_prompts.setText("✨ 10가지 프롬프트 기획")
        self.suno_prompts_cache = prompts
        self.load_suno_prompts_into_table(prompts)
        QMessageBox.information(self, "기획 완료", "10가지 맞춤형 Suno AI 음악 프롬프트가 성공적으로 생성되었습니다!")

    def on_plan_error(self, err_msg: str):
        self.btn_plan_prompts.setEnabled(True)
        self.btn_plan_prompts.setText("✨ 10가지 프롬프트 기획")
        QMessageBox.warning(self, "기획 오류", f"프롬프트 기획 중 오류가 발생했습니다:\n{err_msg}")

    def load_suno_prompts_into_table(self, prompts: List[Dict[str, Any]]):
        self.prompts_table.setRowCount(0)
        for row_idx, p in enumerate(prompts):
            self.prompts_table.insertRow(row_idx)

            idx_item = QTableWidgetItem(f"#{row_idx + 1}")
            idx_item.setTextAlignment(Qt.AlignCenter)
            self.prompts_table.setItem(row_idx, 0, idx_item)

            title_item = QTableWidgetItem(str(p.get("title", "")))
            title_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.prompts_table.setItem(row_idx, 1, title_item)

            mood_item = QTableWidgetItem(str(p.get("mood_keyword", "")))
            self.prompts_table.setItem(row_idx, 2, mood_item)

            style_item = QTableWidgetItem(str(p.get("suno_prompt", "")))
            self.prompts_table.setItem(row_idx, 3, style_item)

        if prompts and len(prompts) > 0:
            self.populate_suno_form(prompts[0])

    def on_prompt_row_clicked(self, item: QTableWidgetItem):
        row = item.row()
        if row < len(self.suno_prompts_cache):
            self.populate_suno_form(self.suno_prompts_cache[row])

    def populate_suno_form(self, p: Dict[str, Any]):
        self.gen_input_title.setText(p.get("title", ""))
        self.gen_input_tags.setText(p.get("suno_prompt", ""))
        self.gen_input_prompt.setText(f"{p.get('title')} - {p.get('mood_keyword', '')}")
        lyrics = p.get("lyrics", "[Instrumental]")
        self.gen_input_lyrics.setText(lyrics or "[Instrumental]")

    def export_prompts_to_sheets(self):
        from export_to_sheets import export_10_prompts_to_csv
        prompts = self.suno_prompts_cache if self.suno_prompts_cache else None
        target_path, _ = QFileDialog.getSaveFileName(
            self, "구글시트용 CSV 파일 저장",
            os.path.join(config.MUSIC_DOWNLOAD_DIR, "suno_prompts_10.csv"),
            "CSV Files (*.csv)"
        )
        if target_path:
            saved_file = export_10_prompts_to_csv(target_path, prompts)
            reply = QMessageBox.information(
                self, "저장 완료",
                f"10개의 항목, 내용, 프롬프트가 구글시트 호환 CSV로 저장되었습니다!\n\n경로: {saved_file}\n\n구글 드라이브나 구글시트(sheets.new)로 드래그하여 바로 열 수 있습니다.\n\n저장 폴더를 여시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                try:
                    os.startfile(os.path.dirname(saved_file))
                except Exception:
                    pass

    def start_suno_generation(self):
        title = self.gen_input_title.text().strip() or "Suno_AI_Track"
        tags = self.gen_input_tags.text().strip()
        prompt = self.gen_input_prompt.toPlainText().strip()
        lyrics = self.gen_input_lyrics.toPlainText().strip()

        if not prompt and not tags:
            QMessageBox.warning(self, "입력 확인", "프롬프트 또는 스타일 태그를 입력해주세요.")
            return

        self.btn_generate_suno.setEnabled(False)
        self.suno_progress.setVisible(True)
        self.suno_status_label.setText("🚀 Suno API (Apiframe v2)로 생성을 요청하는 중...")

        self.gen_worker = SunoGenerateWorker(prompt, tags, title, lyrics)
        self.gen_worker.finished.connect(self.on_generate_success)
        self.gen_worker.error.connect(self.on_generate_error)
        self.gen_worker.start()

    def on_generate_success(self, res: Dict[str, Any]):
        task_id = res.get("task_id")
        self.current_task_id = task_id
        if not task_id:
            self.on_generate_error("Task ID를 받지 못했습니다.")
            return

        self.suno_status_label.setText(f"⏳ 작업 접수 완료 (Task ID: {task_id}). 음원 생성 대기 중 (약 20~40초 소요)...")
        self.suno_poll_timer.start()

    def on_generate_error(self, err: str):
        self.btn_generate_suno.setEnabled(True)
        self.suno_progress.setVisible(False)
        self.suno_status_label.setText(f"❌ 음원 생성 요청 실패: {err}")
        QMessageBox.critical(self, "생성 실패", f"Suno 음원 생성 요청에 실패했습니다:\n{err}")

    def poll_suno_status(self):
        if not self.current_task_id:
            self.suno_poll_timer.stop()
            return

        self.status_worker = SunoStatusWorker(self.current_task_id)
        self.status_worker.status_updated.connect(self.on_status_updated)
        self.status_worker.start()

    def on_status_updated(self, res: Dict[str, Any]):
        status = res.get("status", "").upper()
        audio_url = res.get("audio_url")

        if status == "SUCCESS" and audio_url:
            self.suno_poll_timer.stop()
            self.btn_generate_suno.setEnabled(True)
            self.suno_progress.setVisible(False)
            self.current_audio_url = audio_url

            self.suno_status_label.setText("🎉 음원 생성이 성공적으로 완료되었습니다!")
            self.btn_play_audio.setEnabled(True)
            self.btn_download_pc.setEnabled(True)

            # Load into media player
            self.media_player.setMedia(QMediaContent(QUrl(audio_url)))
            QMessageBox.information(self, "생성 완료", "Suno 음원 생성이 완료되었습니다!\n이제 재생하거나 내 PC로 다운로드할 수 있습니다.")

        elif status in ["FAILED", "ERROR"]:
            self.suno_poll_timer.stop()
            self.btn_generate_suno.setEnabled(True)
            self.suno_progress.setVisible(False)
            self.suno_status_label.setText("❌ 음원 생성에 실패했습니다.")
            QMessageBox.critical(self, "실패", "음원 생성 작업이 실패했습니다. 다른 프롬프트로 다시 시도해 주세요.")
        else:
            self.suno_status_label.setText(f"⏳ 생성 진행 중... ({status}) - 잠시만 기다려주세요.")

    # Audio Player Handlers
    def toggle_audio_playback(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop_audio_playback(self):
        self.media_player.stop()

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.btn_play_audio.setText("⏸ 일시정지")
            self.btn_stop_audio.setEnabled(True)
        else:
            self.btn_play_audio.setText("▶ 재생")
            if state == QMediaPlayer.StoppedState:
                self.btn_stop_audio.setEnabled(False)

    def on_player_position_changed(self, position):
        if not self.player_slider.isSliderDown():
            self.player_slider.setValue(position)
        self.update_player_time_label(position, self.media_player.duration())

    def on_player_duration_changed(self, duration):
        self.player_slider.setRange(0, duration)
        self.update_player_time_label(self.media_player.position(), duration)

    def set_player_position(self, position):
        self.media_player.setPosition(position)

    def update_player_time_label(self, position: int, duration: int):
        pos_sec = position // 1000
        dur_sec = duration // 1000
        pos_str = f"{pos_sec // 60:02d}:{pos_sec % 60:02d}"
        dur_str = f"{dur_sec // 60:02d}:{dur_sec % 60:02d}"
        self.player_time_label.setText(f"{pos_str} / {dur_str}")

    # PC Download Handlers
    def download_generated_audio(self):
        if not self.current_audio_url:
            QMessageBox.warning(self, "다운로드 불가", "다운로드할 생성된 음원 URL이 없습니다.")
            return

        title = self.gen_input_title.text().strip() or "suno_music"
        safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip() + ".mp3"

        self.btn_download_pc.setEnabled(False)
        self.btn_download_pc.setText("다운로드 중...")

        self.dl_worker = DownloadWorker(self.current_audio_url, safe_name, config.MUSIC_DOWNLOAD_DIR)
        self.dl_worker.finished.connect(self.on_download_success)
        self.dl_worker.error.connect(self.on_download_error)
        self.dl_worker.start()

    def on_download_success(self, res: Dict[str, Any]):
        self.btn_download_pc.setEnabled(True)
        self.btn_download_pc.setText("💾 내 PC로 다운로드")
        f_path = res.get("file_path", "")
        reply = QMessageBox.information(
            self, "다운로드 완료",
            f"음원이 내 PC에 성공적으로 저장되었습니다!\n\n경로: {f_path}\n\n저장 폴더를 여시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.open_download_folder()

    def on_download_error(self, err: str):
        self.btn_download_pc.setEnabled(True)
        self.btn_download_pc.setText("💾 내 PC로 다운로드")
        QMessageBox.critical(self, "다운로드 실패", f"다운로드 중 오류가 발생했습니다:\n{err}")

    def open_download_folder(self):
        folder = config.MUSIC_DOWNLOAD_DIR
        today_str = datetime.now().strftime("%Y-%m-%d")
        sub_folder = os.path.join(folder, today_str)
        target = sub_folder if os.path.exists(sub_folder) else folder

        if not os.path.exists(target):
            os.makedirs(target, exist_ok=True)

        try:
            os.startfile(target)
        except Exception as e:
            QMessageBox.warning(self, "폴더 열기 실패", f"폴더를 열 수 없습니다: {e}")

    # -----------------------------------------------------------------
    # Tab 4: Conversation History
    # -----------------------------------------------------------------
    def create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("🕰️ 저장된 대화 기록 보관소")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_row.addWidget(title)
        header_row.addStretch()

        btn_refresh = QPushButton("🔄 새로고침")
        btn_refresh.setProperty("class", "btn-secondary")
        btn_refresh.clicked.connect(self.load_conversations_tab)
        header_row.addWidget(btn_refresh)
        layout.addLayout(header_row)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["ID", "일시", "메시지 수", "요약", "작업"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.history_table)

        return widget

    def load_conversations_tab(self):
        try:
            convs = list_conversations()
            self.history_table.setRowCount(0)

            for row_idx, c in enumerate(convs):
                self.history_table.insertRow(row_idx)

                cid = c.get("id", "")
                id_item = QTableWidgetItem(cid[:8] + "...")
                id_item.setToolTip(cid)
                self.history_table.setItem(row_idx, 0, id_item)

                time_str = c.get("updated_at") or c.get("created_at") or "N/A"
                if len(time_str) > 19:
                    time_str = time_str[:19].replace("T", " ")
                time_item = QTableWidgetItem(time_str)
                self.history_table.setItem(row_idx, 1, time_item)

                msgs = c.get("messages", [])
                cnt_item = QTableWidgetItem(f"{len(msgs)}개")
                cnt_item.setTextAlignment(Qt.AlignCenter)
                self.history_table.setItem(row_idx, 2, cnt_item)

                # Summary: first user message snippet
                snippet = "대화 없음"
                for m in msgs:
                    if m.get("role") == "user":
                        snippet = m.get("content", "")[:40]
                        break
                self.history_table.setItem(row_idx, 3, QTableWidgetItem(snippet))

                # Load button
                btn_load = QPushButton("📂 불러오기")
                btn_load.setProperty("class", "btn-secondary")
                btn_load.setStyleSheet("padding: 2px 8px; font-size: 11px;")
                btn_load.clicked.connect(lambda checked, conv_data=c: self.load_conversation_into_chat(conv_data))
                self.history_table.setCellWidget(row_idx, 4, btn_load)
        except Exception as e:
            print(f"Error loading conversations: {e}")

    def load_conversation_into_chat(self, conv: Dict[str, Any]):
        self.current_conv_id = conv.get("id")
        self.chat_display.clear()

        msgs = conv.get("messages", [])
        if not msgs:
            self.append_chat_message("assistant", "이 대화에는 저장된 메시지가 없습니다.")
        else:
            for m in msgs:
                self.append_chat_message(m.get("role", "user"), m.get("content", ""))

        self.tabs.setCurrentWidget(self.tab_chat)
        QMessageBox.information(self, "불러오기 완료", "선택한 대화 기록이 채팅창에 로드되었습니다.")

    # -----------------------------------------------------------------
    # Status Bar
    # -----------------------------------------------------------------
    def create_status_bar(self) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet("background-color: #0f172a; border-top: 1px solid #1e293b; padding: 4px;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 2, 4, 2)

        api_status = []
        if config.OPENAI_API_KEY:
            api_status.append("OpenAI ✔")
        if config.GEMINI_API_KEY:
            api_status.append("Gemini ✔")
        if config.APIFRAME_API_KEY:
            api_status.append("Suno(Apiframe) ✔")

        status_txt = " • ".join(api_status) if api_status else "API 키 설정 필요"
        lbl_apis = QLabel(f"연결된 AI 서비스: {status_txt}")
        lbl_apis.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl_apis)

        layout.addStretch()

        lbl_dir = QLabel(f"다운로드 기본 폴더: {config.MUSIC_DOWNLOAD_DIR}")
        lbl_dir.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl_dir)

        return frame


# =====================================================================
# Application Entry Point
# =====================================================================
def main():
    # Enable High-DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
