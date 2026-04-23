import time
import queue
import threading
import os
from datetime import datetime
try:
    import netifaces
except ImportError:
    netifaces = None

from PyQt6.QtCore import QThread, pyqtSignal
from miio import FanP5
from miio.integrations.fan.dmaker.fan import OperationMode

class FanControllerThread(QThread):
    status_updated = pyqtSignal(dict)
    connection_error = pyqtSignal(str)
    connectivity_updated = pyqtSignal(int) # 0: OK, 1: LOCAL_OFF, 2: DEVICE_OFF

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.running = True
        self.is_active = False # For smart frequency toggle
        self.command_queue = queue.Queue()
        self.interrupt_event = threading.Event()
        self.fan = None
        self.log_enabled = self.config_manager.get('log_enabled', False)
        self.log_file = "mifan_debug.log"
        self._init_fan()

    def log_msg(self, msg):
        if not self.log_enabled:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"{ts} | [BACK] | {msg}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def set_logging(self, enabled):
        self.log_enabled = enabled
        self.log_msg(f"日誌功能已{'開啟' if enabled else '關閉'}")

    def _init_fan(self):
        ip = self.config_manager.get('fan_ip')
        token = self.config_manager.get('fan_token')
        if ip and token:
            try:
                self.fan = FanP5(ip, token)
            except Exception:
                self.fan = None

    def set_active(self, active: bool):
        """Called by UI when hovered or expanded to increase frequency"""
        self.is_active = active
        if active:
            self.interrupt_event.set()

    def update_config(self):
        self._init_fan()
        self.interrupt_event.set()

    def set_power(self, on: bool):
        self.command_queue.put(('power', on))
        self.interrupt_event.set()

    def set_speed(self, speed: int, urgent=False):
        self.command_queue.put(('speed', speed))
        if urgent:
            self.interrupt_event.set()

    def set_mode(self, mode_str: str):
        self.command_queue.put(('mode', mode_str))
        self.interrupt_event.set()

    def set_oscillate(self, oscillate: bool):
        self.command_queue.put(('oscillate', oscillate))
        self.interrupt_event.set()

    def check_local_network(self):
        """Check if local machine has a functional network interface and gateway"""
        import socket
        
        # 1. Primary Gold Standard: Host IP enumeration
        try:
            hostname = socket.gethostname()
            _, _, ips = socket.gethostbyname_ex(hostname)
            if not any(not ip.startswith("127.") for ip in ips):
                return False
        except Exception:
            pass 
            
        # 2. Secondary Method: netifaces
        if netifaces:
            try:
                gws = netifaces.gateways()
                if 'default' in gws and (netifaces.AF_INET in gws['default']):
                    gw_info = gws['default'][netifaces.AF_INET]
                    if gw_info and len(gw_info) > 0 and gw_info[0]:
                        return True
            except Exception:
                pass 

        # 3. Tertiary Method: Socket routing hint
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80)) 
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip != "127.0.0.1"
        except Exception:
            return False

    def run(self):
        while self.running:
            # Clear event at start of loop
            self.interrupt_event.clear()
            
            # 1. Connectivity Check
            conn_state = 0 # Assume OK
            if not self.check_local_network():
                conn_state = 1 # LOCAL_OFFLINE
            
            # 2. Process pending commands (Deduplicated)
            if conn_state == 0:
                pending_cmds = {}
                while not self.command_queue.empty():
                    cmd, val = self.command_queue.get()
                    pending_cmds[cmd] = val # Latest command wins
                
                if self.fan:
                    for cmd, val in pending_cmds.items():
                        try:
                            if cmd == 'power':
                                self.log_msg(f"執行電源指令: {'開啟' if val else '關閉'}")
                                if val: self.fan.on()
                                else: self.fan.off()
                            elif cmd == 'speed':
                                self.log_msg(f"執行風速指令: {val}%")
                                self.fan.set_speed(val)
                            elif cmd == 'mode':
                                self.log_msg(f"執行模式指令: {val}")
                                if val.lower() == 'nature':
                                    self.fan.set_mode(OperationMode.Nature)
                                else:
                                    self.fan.set_mode(OperationMode.Normal)
                            elif cmd == 'oscillate':
                                self.log_msg(f"執行擺頭指令: {'開啟' if val else '關閉'}")
                                self.fan.set_oscillate(val)
                        except Exception as e:
                            self.log_msg(f"指令執行錯誤 [{cmd}]: {e}")

            # 3. Fetch status
            if conn_state == 0:
                if self.fan:
                    try:
                        status = self.fan.status()
                        data = {
                            'is_on': status.is_on,
                            'speed': status.speed,
                            'mode': status.mode.name.lower() if hasattr(status.mode, 'name') else str(status.mode).lower(),
                            'oscillate': status.oscillate,
                            'model': self.config_manager.get('fan_model', 'dmaker.fan.p5')
                        }
                        self.log_msg(f"狀態輪詢成功: speed={data['speed']}, on={data['is_on']}, mode={data['mode']}")
                        self.status_updated.emit(data)
                    except Exception:
                        conn_state = 2 # DEVICE_OFFLINE
                else:
                    conn_state = 2 # No fan init failed
            
            # 4. Broadcast Connectivity
            self.connectivity_updated.emit(conn_state)

            # 5. Smart Adaptive Polling (using interruptible wait)
            if conn_state != 0:
                wait_time = 2.0
            elif self.is_active:
                wait_time = 1.0
            else:
                wait_time = 2.5
            
            # Only wait if no new commands arrived during processing
            if self.command_queue.empty():
                self.interrupt_event.wait(wait_time)

    def stop(self):
        self.running = False
        self.interrupt_event.set() # Wake up to exit
        self.wait()
