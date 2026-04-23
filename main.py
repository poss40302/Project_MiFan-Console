import sys
import os
import time
import ctypes
import ctypes.wintypes
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, 
                             QSlider, QMenu, QDialog, QFormLayout, QLineEdit, 
                             QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
                             QStackedWidget)
from PyQt6.QtCore import Qt, QRect, QRectF, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QBrush, QFont, QPixmap, QIcon, QLinearGradient

from config_manager import ConfigManager
from backend import FanControllerThread
from autostart import set_autostart, is_autostart_enabled

APP_NAME = "MiFanCommander"
VERSION = "v1.9.0423"
RES_DIR = os.path.join(os.path.dirname(__file__), "Resourse")
CYAN = "#00ffff"
FONT_ZH = "Microsoft JhengHei"
FONT_EN = "Arial Narrow"

# --- Win32 Acrylic Helper ---
class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int), 
                ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_int)]

class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p), ("SizeOfData", ctypes.c_size_t)]

def set_acrylic_blur(hwnd):
    accent = ACCENTPOLICY()
    accent.AccentState = 4 # ACCENT_ENABLE_ACRYLICBLURBEHIND
    accent.GradientColor = 0x50000000 
    accent.AccentFlags = 2
    data = WINCOMPATTRDATA()
    data.Attribute = 19
    data.SizeOfData = ctypes.sizeof(accent)
    data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))

# --- Custom UI Components ---

class HSeparator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 5, self.width(), 5)
        grad.setColorAt(0, QColor(0, 255, 255, 0))
        grad.setColorAt(0.5, QColor(0, 255, 255, 40))
        grad.setColorAt(1, QColor(0, 255, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRect(0, 4, self.width(), 1)

class PillToggle(QPushButton):
    def __init__(self, on_pix_name="switch_on.png", parent=None):
        super().__init__(parent)
        self.setFixedSize(52, 26)
        self.is_on = False
        self.is_hovered = False
        self.on_pix = QPixmap(os.path.join(RES_DIR, on_pix_name))
        self.off_pix = QPixmap(os.path.join(RES_DIR, "switch_off.png"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def set_state(self, is_on):
        self.is_on = is_on
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True; self.update()
    def leaveEvent(self, event):
        self.is_hovered = False; self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pix = self.on_pix if self.is_on else self.off_pix
        painter.drawPixmap(self.rect(), pix)
        
        if self.is_hovered:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            painter.setBrush(QColor(0, 255, 255, 30))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(self.rect()), 13, 13)

class NatureButton(QPushButton):
    def __init__(self, level, parent=None):
        super().__init__(parent)
        self.level = level
        self.is_on = False
        self.is_hovered = False
        self.setFixedSize(32, 32)
        self.on_pix = QPixmap(os.path.join(RES_DIR, f"nature_{level}_on.png"))
        self.off_pix = QPixmap(os.path.join(RES_DIR, f"nature_{level}_off.png"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def set_active(self, active):
        self.is_on = active
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True; self.update()
    def leaveEvent(self, event):
        self.is_hovered = False; self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pix = self.on_pix if self.is_on else self.off_pix
        painter.drawPixmap(self.rect(), pix)
        
        if self.is_hovered:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            painter.setBrush(QColor(0, 255, 255, 40))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(self.rect())

class NeonSlider(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 18)
        self.value = 50
        self.is_hovered = False
        self.is_pressed = False
        self.frame_pix = QPixmap(os.path.join(RES_DIR, "SliderBar_frame.png"))
        self.inner_pix = QPixmap(os.path.join(RES_DIR, "SliderBar_Inner.png"))
        self.handle_pix = QPixmap(os.path.join(RES_DIR, "SliderBar_handle.png"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def set_value(self, val):
        self.value = max(0, min(100, val))
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True; self.update()
    def leaveEvent(self, event):
        self.is_hovered = False; self.update()

    def set_value(self, val):
        self.value = max(0, min(100, val))
        self.update()

    def update_val_from_x(self, x):
        v = int((x / self.width()) * 100)
        self.set_value(v)
        self.valueChanged.emit(self.value)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.update_val_from_x(event.position().x())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.update_val_from_x(event.position().x())
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = False
            event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        # PRECISION: 1% step
        step = 1 if delta > 0 else -1
        self.set_value(self.value + step)
        self.valueChanged.emit(self.value)
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Draw Frame
        painter.drawPixmap(self.rect(), self.frame_pix)
        
        # 2. Draw Inner
        progress_width = int(self.width() * (self.value / 100.0))
        if progress_width > 5:
            src_w = int(self.inner_pix.width() * (self.value / 100.0))
            painter.drawPixmap(QRect(0, 0, progress_width, self.height()), self.inner_pix, QRect(0, 0, src_w, self.inner_pix.height()))
        
        # 3. Hover High-light (NOW WITH STRONGER RADIANCE)
        if self.is_hovered:
            painter.save()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            painter.setBrush(QColor(0, 255, 255, 60)) # Increased Glow Strength
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(self.rect()), 9, 9)
            painter.restore()

        # 4. Draw Handle
        h_s = self.height()
        painter.drawPixmap(QRect(progress_width - h_s//2, 0, h_s, h_s), self.handle_pix)

class FanIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.is_running = False
        self.is_hovered = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(20)
        self.speed = 1.0
        self.conn_state = 0 # 0: OK, 1: LOCAL_OFF, 2: DEVICE_OFF
        self.on_pix = QPixmap(os.path.join(RES_DIR, "fan_blade.png"))
        self.off_pix = QPixmap(os.path.join(RES_DIR, "fan_blade_off.png"))
        self.wifi_err_pix = QPixmap(os.path.join(RES_DIR, "wifi_error.png"))
        self.device_err_pix = QPixmap(os.path.join(RES_DIR, "error_overlay.png"))
        self.setMouseTracking(True)

    def set_speed(self, running, speed=1.0):
        self.is_running = running
        self.speed = max(0.1, speed / 100.0)
        self.update()

    def update_angle(self):
        if self.is_running:
            self.angle = (self.angle + (15 * self.speed)) % 360
            self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if self.parent() and hasattr(self.parent(), "click"):
            self.parent().click()
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Button Base (Circular Bottom Plate - 60% opacity)
        path = QPainterPath()
        rect = self.rect().adjusted(2, 2, -2, -2)
        path.addEllipse(QRectF(rect))
        
        # High-light effect on hover (Alpha 180 for highlight, 153 for normal)
        base_color = QColor(60, 65, 70, 180) if self.is_hovered else QColor(40, 45, 50, 153)
        painter.fillPath(path, base_color)
        
        rim_alpha = 180 if self.is_hovered else 60
        painter.setPen(QPen(QColor(0, 255, 255, rim_alpha), 2 if self.is_hovered else 1.5))
        painter.drawEllipse(QRectF(rect))

        # Connectivity-based Rendering
        if self.conn_state == 1: # LOCAL_OFFLINE
            pix = self.wifi_err_pix
            painter.drawPixmap(self.rect().adjusted(10, 10, -10, -10), pix)
        elif self.conn_state == 2: # DEVICE_OFFLINE
            pix = self.device_err_pix
            painter.drawPixmap(self.rect().adjusted(5, 5, -5, -5), pix)
        else: # OK
            # Draw Fan Blade with rotation
            painter.save()
            painter.translate(self.width()/2, self.height()/2)
            painter.rotate(self.angle)
            pix = self.on_pix if self.is_running else self.off_pix
            painter.drawPixmap(QRect(-self.width()//2 + 8, -self.height()//2 + 8, self.width()-16, self.height()-16), pix)
            painter.restore()

class FanConsoleWindow(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.is_expanded = False
        self.power_on = False
        self.log_enabled = config_manager.get('log_enabled', False)
        
        # SLIDER THROTTLE
        self.slider_timer = QTimer(self)
        self.slider_timer.setSingleShot(True)
        self.slider_timer.timeout.connect(self.commit_slider_speed)
        self.last_slider_val = 0
        self.last_slider_interaction = 0 # Guard ONLY for SliderBar
        self.expected_speed = None # Smart Ack target
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.Tool |
                            Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")
        
        # DYNAMIC GEOMETRY DEFINITIONS
        self.compact_size = QSize(160, 160)
        self.panel_size = QSize(220, 410) # Optimized from 480px to 410px
        
        self.resize(self.compact_size)
        
        saved_x, saved_y = self.config_manager.get('window_x'), self.config_manager.get('window_y')
        if saved_x is not None and saved_y is not None:
            pos = QPoint(saved_x, saved_y)
            # Validate if the saved position is within any current screen
            is_visible = False
            for screen in QApplication.screens():
                if screen.geometry().contains(pos):
                    is_visible = True
                    break
            
            if is_visible:
                self.move(pos)
            else:
                # Reset to primary screen center if off-screen
                primary_geo = QApplication.primaryScreen().geometry()
                self.move(primary_geo.center() - QPoint(self.width()//2, self.height()//2))
        
        self.old_pos = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30) # Compact margins
        self.layout.setSpacing(18)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center everything always

        # 1. Power Area
        self.p_container = QWidget()
        self.p_container.setFixedSize(65, 65)
        self.pc_layout = QHBoxLayout(self.p_container)
        self.pc_layout.setContentsMargins(0, 0, 0, 0)
        self.pc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.power_btn = QPushButton()
        self.power_btn.setFixedSize(65, 65)
        self.power_btn.setFlat(True)
        self.power_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.power_btn.setStyleSheet("background: transparent; border: none;")
        self.power_btn.clicked.connect(self.toggle_power)
        
        self.btn_icon = FanIcon(self.power_btn)
        self.btn_icon.setGeometry(0, 0, 65, 65)
        # Enable mouse events for hover, click will be forwarded
        self.pc_layout.addWidget(self.power_btn)
        
        self.layout.addWidget(self.p_container, 0, Qt.AlignmentFlag.AlignHCenter)

        # 2. Controls
        self.controls = QWidget()
        self.c_layout = QVBoxLayout(self.controls)
        self.c_layout.setContentsMargins(0, 0, 0, 0)
        self.c_layout.setSpacing(12)
        self.c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def create_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont(FONT_ZH, 9, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {CYAN};")
            return lbl

        self.c_layout.addWidget(create_label("模式切換 / MODE"))
        mode_box = QHBoxLayout()
        mode_box.setSpacing(6)
        
        l_lbl = QLabel("直吹風", font=QFont(FONT_ZH, 8), styleSheet=f"color:{CYAN}")
        l_lbl.setFixedWidth(50); l_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mode_box.addWidget(l_lbl)
        # Use Custom Asset for Mode switch (Direct Blow = switch_on2)
        self.mode_toggle = PillToggle(on_pix_name="switch_on2.png")
        self.mode_toggle.clicked.connect(self.toggle_mode)
        mode_box.addWidget(self.mode_toggle)
        r_lbl = QLabel("自然風", font=QFont(FONT_ZH, 8), styleSheet=f"color:{CYAN}")
        r_lbl.setFixedWidth(50); r_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        mode_box.addWidget(r_lbl)
        self.c_layout.addLayout(mode_box)

        self.c_layout.addWidget(HSeparator())

        self.c_layout.addWidget(create_label("風量調節 / SPEED"))
        # Re-structured using QStackedWidget to prevent layout displacement
        self.speed_stack = QStackedWidget()
        self.speed_stack.setFixedHeight(45) # Reduced from 65 to 45 to minimize whitespace
        
        # Page 0: Normal Mode (Slider + Instant Label)
        self.normal_page = QWidget()
        self.normal_layout = QVBoxLayout(self.normal_page)
        self.normal_layout.setContentsMargins(0, 0, 0, 0); self.normal_layout.setSpacing(2) # Reduced spacing
        
        self.speed_slider = NeonSlider()
        self.speed_val_label = QLabel("0%", alignment=Qt.AlignmentFlag.AlignCenter)
        self.speed_val_label.setFont(QFont(FONT_EN, 11, QFont.Weight.Bold))
        self.speed_val_label.setStyleSheet(f"color: {CYAN};") # Removed negative margin to fix clipping
        
        self.normal_layout.addWidget(self.speed_slider, 0, Qt.AlignmentFlag.AlignCenter)
        self.normal_layout.addWidget(self.speed_val_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Page 1: Nature Mode (Step Buttons)
        self.nature_page = QWidget()
        self.nature_layout = QHBoxLayout(self.nature_page)
        self.nature_layout.setContentsMargins(0, 0, 0, 0); self.nature_layout.setSpacing(6)
        self.nature_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.levels = []
        for i in range(1, 5):
            b = NatureButton(i)
            b.clicked.connect(lambda ch, l=i: self.set_level(l))
            self.levels.append(b)
            self.nature_layout.addWidget(b)
            
        self.speed_stack.addWidget(self.normal_page) # index 0
        self.speed_stack.addWidget(self.nature_page) # index 1
        
        self.c_layout.addWidget(self.speed_stack)
        
        # Signal Connections
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.speed_slider.valueChanged.connect(self.on_slider_changed)

        self.c_layout.addWidget(HSeparator())

        self.c_layout.addWidget(create_label("擺頭設定 / OSCILLATE"))
        osc_box = QHBoxLayout()
        osc_box.setSpacing(6)
        
        o_l_lbl = QLabel("停止", font=QFont(FONT_ZH, 8), styleSheet=f"color:{CYAN}")
        o_l_lbl.setFixedWidth(50); o_l_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        osc_box.addWidget(o_l_lbl)
        
        self.osc_toggle = PillToggle()
        self.osc_toggle.clicked.connect(self.toggle_osc)
        osc_box.addWidget(self.osc_toggle)
        
        o_r_lbl = QLabel("啟用", font=QFont(FONT_ZH, 8), styleSheet=f"color:{CYAN}")
        o_r_lbl.setFixedWidth(50); o_r_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        osc_box.addWidget(o_r_lbl)
        self.c_layout.addLayout(osc_box)

        self.layout.addWidget(self.controls)
        self.controls.setVisible(False)

        self.anim = QPropertyAnimation(self, b"size")
        self.anim.setDuration(450); self.anim.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.backend = FanControllerThread(config_manager)
        self.backend.status_updated.connect(self.on_status_updated)
        self.backend.connectivity_updated.connect(self.on_connectivity_updated)
        self.backend.start()

    def enterEvent(self, event):
        self.backend.set_active(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_expanded:
            self.backend.set_active(False)
        super().leaveEvent(event)

    def on_connectivity_updated(self, state):
        # Update Icon State
        old_state = self.btn_icon.conn_state
        self.btn_icon.conn_state = state
        self.btn_icon.update()
        
        # 1. Auto-collapse on error
        if state != 0 and self.is_expanded:
            self.set_expanded(False)
            
        # 2. Auto-expand on recovery (if fan was already ON)
        if old_state != 0 and state == 0 and self.power_on:
            self.set_expanded(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Internal Backplate (60% Transparency)
        path = QPainterPath()
        # Radius mirrors the frame curvature (approx 45px for capsule)
        r = 45 if self.width() > 180 else 80
        path.addRoundedRect(QRectF(self.rect()), r, r)
        painter.fillPath(path, QColor(30, 35, 40, 153)) 

        # 2. Frame Drawing
        frame_pix = QPixmap(os.path.join(RES_DIR, "frame_master.png"))
        if not frame_pix.isNull():
            # Corrected logic: Use 3-part slicing for compact mode too, just with 0 middle height
            # and specific cap_src_h to maintain curvature ratio
            self.draw_3part_vertical(painter, frame_pix, self.rect(), 80)

    def draw_3part_vertical(self, painter, pix, rect, cap_src_h):
        # cap_src_h: The height of the top/bottom curved area in the source asset
        sw, sh = pix.width(), pix.height()
        dw, dh = rect.width(), rect.height()
        
        # Scaling ratio for the fixed width
        ratio = dw / sw
        # Scaled height of the top/bottom caps in destination
        cap_h = int(cap_src_h * ratio)
        
        # 1. Top Cap (Includes your power button slot and perfect curve)
        painter.drawPixmap(QRect(0, 0, dw, cap_h), pix, QRect(0, 0, sw, cap_src_h))
        
        # 2. Bottom Cap (Includes the bottom curve)
        painter.drawPixmap(QRect(0, dh - cap_h, dw, cap_h), pix, QRect(0, sh - cap_src_h, sw, cap_src_h))
        
        # 3. Middle Section (Stretched vertical lines)
        mid_h = dh - 2 * cap_h
        if mid_h > 0:
            painter.drawPixmap(QRect(0, cap_h, dw, mid_h), pix, QRect(0, cap_src_h, sw, sh - 2 * cap_src_h))

    def toggle_power(self):
        if self.btn_icon.conn_state != 0:
            return # Block expansion/power toggle if offline
            
        self.power_on = not self.power_on
        self.backend.set_power(self.power_on)
        self.set_expanded(self.power_on)

    def toggle_mode(self):
        m = "nature" if not self.mode_toggle.is_on else "normal"
        self.backend.set_mode(m)

    def on_slider_changed(self, v): 
        self.log_msg(f"滑桿數值變更: {v}% (物理按壓: {self.speed_slider.is_pressed})")
        self.last_slider_interaction = time.time()
        self.last_slider_val = v
        # Restart timer - only send after 300ms of no changes
        self.slider_timer.start(300)

    def commit_slider_speed(self):
        self.log_msg(f"提交滑桿最終風速: {self.last_slider_val}% (Urgent=True)")
        self.expected_speed = self.last_slider_val
        self.backend.set_speed(self.last_slider_val, urgent=True)

    def set_level(self, l): 
        self.expected_speed = l * 25
        self.backend.set_speed(l * 25, urgent=True)
    def toggle_osc(self): 
        self.backend.set_oscillate(not self.osc_toggle.is_on)

    def on_status_updated(self, status):
        speed = status.get('speed', 1)
        new_on = status.get('is_on', False)
        
        # SMART ACK CHECK: If speed matches expectation, release guard early
        if self.expected_speed is not None and speed == self.expected_speed:
            self.log_msg(f"接收狀態更新: speed={speed}. [Smart Ack: 達標解鎖]")
            self.last_slider_interaction = 0
            self.expected_speed = None

        # LOGGING DECISION
        is_p = self.speed_slider.is_pressed
        rem = 6.0 - (time.time() - self.last_slider_interaction)
        
        if is_p:
            self.log_msg(f"接收狀態更新: speed={speed}, on={new_on}. [決策: 鐵壁跳過] (原因: 正在拖動滑桿中)")
            return
        elif rem > 0 and self.last_slider_interaction > 0:
            self.log_msg(f"接收狀態更新: speed={speed}, on={new_on}. [決策: 跳過] (原因: 鎖定中, 剩餘 {rem:.2f}s)")
            return
        else:
            self.log_msg(f"接收狀態更新: speed={speed}, on={new_on}. [決策: 更新]")

        if new_on != self.power_on:
            self.power_on = new_on
            self.set_expanded(self.power_on)
        
        speed = status.get('speed', 1)
        mode = status.get('mode', 'normal').lower()
        osc = status.get('oscillate', False)
        
        self.btn_icon.set_speed(self.power_on, speed)
        
        # MODE MAPPING CORRECTOR (Explicit Logic)
        if mode == "nature":
            self.mode_toggle.on_pix = QPixmap(os.path.join(RES_DIR, "switch_on.png"))
            self.mode_toggle.set_state(True) # Right Side
        else: # normal
            self.mode_toggle.off_pix = QPixmap(os.path.join(RES_DIR, "switch_on2.png"))
            self.mode_toggle.set_state(False) # Left Side
        
        self.osc_toggle.set_state(osc)
        
        is_nature = (mode == "nature")
        self.speed_stack.setCurrentIndex(1 if is_nature else 0)
        
        # ONLY GUARD SLIDER/LEVEL UPDATES
        if time.time() - self.last_slider_interaction > 4.0:
            if is_nature:
                lv = round(speed / 25)
                for i, b in enumerate(self.levels): b.set_active((i+1) == lv)
            else:
                self.speed_slider.set_value(speed)
        
        # Sync label (redundancy but safe for initial load)
        self.update_speed_label(speed)

    def log_msg(self, msg):
        if not self.log_enabled: return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"{ts} | [UI]   | {msg}\n"
        try:
            with open("mifan_debug.log", "a", encoding="utf-8") as f:
                f.write(line)
        except Exception: pass

    def update_speed_label(self, value):
        """Instant UI feedback without waiting for backend polling"""
        self.speed_val_label.setText(f"{value}%")

    def set_expanded(self, expand):
        if self.is_expanded == expand: return
        self.is_expanded = expand
        
        # ANIMATE SIZE MORPHING
        self.anim.stop()
        self.anim.setStartValue(self.size())
        
        if expand:
            self.anim.setEndValue(self.panel_size)
            self.layout.setContentsMargins(32, 42, 32, 42)
            self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            QTimer.singleShot(250, lambda: self.controls.setVisible(True))
        else:
            self.controls.setVisible(False)
            self.anim.setEndValue(self.compact_size)
            self.layout.setContentsMargins(30, 30, 30, 30)
            self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.old_pos = event.globalPosition().toPoint()
        elif event.button() == Qt.MouseButton.RightButton: self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.old_pos:
            d = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + d); self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
            self.config_manager.set('window_x', self.pos().x()); self.config_manager.set('window_y', self.pos().y())

    def show_context_menu(self, pos):
        menu = QMenu(self)
        # VERSION HEADER
        ver_act = menu.addAction(f"MiFan Console {VERSION}"); ver_act.setEnabled(False)
        menu.addSeparator()
        
        auto_ena = is_autostart_enabled(APP_NAME)
        act_auto = menu.addAction("開機自動啟動"); act_auto.setCheckable(True); act_auto.setChecked(auto_ena)
        act_log = menu.addAction("輸出偵錯日誌 (Debug Log)"); act_log.setCheckable(True); act_log.setChecked(self.log_enabled)
        act_set = menu.addAction("通訊設定")
        menu.addSeparator()
        act_exit = menu.addAction("離開系統")
        menu.setStyleSheet(f"QMenu {{ background: #111; color:{CYAN}; border:1px solid {CYAN}; }} QMenu::item:selected {{ background:{CYAN}; color:#000; }}")
        action = menu.exec(pos)
        if action == act_exit: self.backend.stop(); sys.exit(0)
        elif action == act_auto: set_autostart(APP_NAME, not auto_ena)
        elif action == act_log:
            self.log_enabled = not self.log_enabled
            self.config_manager.set('log_enabled', self.log_enabled)
            self.backend.set_logging(self.log_enabled)
            self.log_msg(f"使用者變更日誌開關: {self.log_enabled}")
        elif action == act_set:
            if SettingsDialog(self.config_manager, self).exec(): self.backend.update_config()

class SettingsDialog(QDialog):
    def __init__(self, cm, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定"); self.cm = cm
        self.setStyleSheet(f"QDialog{{background:#111;color:{CYAN}}} QLabel{{color:{CYAN}}} QLineEdit{{background:#222;color:white;border:1px solid {CYAN}}} QPushButton{{background:{CYAN};color:black}}")
        l = QFormLayout(self)
        self.ip = QLineEdit(cm.get('fan_ip','')); self.tk = QLineEdit(cm.get('fan_token',''))
        l.addRow("IP:", self.ip); l.addRow("Token:", self.tk)
        b = QPushButton("儲存"); b.clicked.connect(self.save); l.addWidget(b)
    def save(self):
        self.cm.set('fan_ip', self.ip.text().strip()); self.cm.set('fan_token', self.tk.text().strip()); self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Priority 1: Use .ico for best compatibility, Priority 2: Use .png fallback
    ico_path = os.path.join(RES_DIR, "mifan_app_icon.ico")
    png_path = os.path.join(RES_DIR, "mifan_app_icon.png")
    
    if os.path.exists(ico_path): app.setWindowIcon(QIcon(ico_path))
    elif os.path.exists(png_path): app.setWindowIcon(QIcon(png_path))
    
    win = FanConsoleWindow(ConfigManager())
    win.show()
    sys.exit(app.exec())
