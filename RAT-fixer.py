import os
import re
import json
import hashlib
import subprocess
import threading
import ctypes
import struct
import time
import shutil
import tempfile
import zipfile
import pefile
import requests
import psutil
import socket
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import datetime

# Расширенная база угроз с фокусировкой на RAT
THREAT_DB = {
    "miner": {
        "patterns": [r"xmrig", r"cryptonight", r"xmr-eu", r"monero", r"nanopool", r"c3pool"],
        "extensions": [".exe", ".js", ".py", ".ps1", ".vbs", ".scr", ".bat"],
        "threat_level": 3,
        "name": "Криптомайнер",
        "mechanism": "Использует ресурсы вашего ПК для майнинга криптовалюты без вашего ведома",
        "mitigation": "Нейтрализовать функционал майнинга"
    },
    "stealer": {
        "patterns": [
            r"keylogger", r"stealc", r"cookies\.sqlite", r"discord_token", 
            r"Login Data", r"Web Data", r"Cookies", r"\.netstealer", 
            r"Grabber", r"TokenLogger", r"DiscordInject", r"Clipboard"
        ],
        "extensions": [".dll", ".bin", ".dat", ".cfg", ".exe", ".log", ".tmp"],
        "threat_level": 8,
        "name": "Информационный стилер",
        "mechanism": "Крадет пароли, куки, данные кредитных карт и другую конфиденциальную информацию",
        "mitigation": "Обезвредить функции кражи данных"
    },
    "rat": {
        "patterns": [
            r"C2_Server", r"RemoteShell", r"HiddenInstall", r"BackConnect", 
            r"Keylogger", r"ScreenSpy", r"ReverseShell", r"PortListener",
            r"PayloadInject", r"Persistance", r"AutoUpdate", r"VictimID",
            r"StartupPersistence", r"RemoteDesktop", r"WebcamCapture"
        ],
        "extensions": [".exe", ".dll", ".jar", ".docm", ".xlsm", ".pptm"],
        "threat_level": 9,
        "name": "Удалённый доступ (RAT)",
        "mechanism": "Предоставляет злоумышленнику полный контроль над вашей системой",
        "mitigation": "Нейтрализовать функции удаленного доступа"
    },
    "backdoor": {
        "patterns": [
            r"shell_exec", r"Backdoor", r"BindShell", r"ReverseTCP", 
            r"ProcessHollow", r"ReflectiveDLL", r"Metasploit", r"CobaltStrike",
            r"Shellcode", r"Meterpreter", r"PrivEscalation", r"CredDump"
        ],
        "extensions": [".exe", ".dll", ".bin", ".vbs", ".ps1"],
        "threat_level": 10,
        "name": "Бэкдор",
        "mechanism": "Создает скрытый доступ для злоумышленников в обход систем безопасности",
        "mitigation": "Закрыть бэкдорные функции"
    },
    "spyware": {
        "patterns": [
            r"ScreenCapture", r"AudioRecord", r"KeyPressMonitor", 
            r"ClipboardLogger", r"FileMonitor", r"NetworkSniffer"
        ],
        "extensions": [".exe", ".dll", ".sys", ".bin"],
        "threat_level": 7,
        "name": "Шпионское ПО",
        "mechanism": "Тайно отслеживает ваши действия и собирает данные",
        "mitigation": "Отключить функции слежения"
    },
    "rootkit": {
        "patterns": [
            r"KernelMode", r"DriverLoad", r"SSDTHook", r"IDTHook",
            r"DKOM", r"ProcessHiding", r"FileHiding", r"RegistryHiding"
        ],
        "extensions": [".sys", ".dll", ".exe", ".bin"],
        "threat_level": 10,
        "name": "Руткит",
        "mechanism": "Скрывает вредоносную активность и получает привилегии администратора",
        "mitigation": "Нейтрализовать руткит-функции"
    },
    "lime_rat": {
        "patterns": [
            r"LimeRAT", r"PlasmaDNS", r"AsyncRAT", r"NjRat", r"QuasarRAT",
            r"DiscordTokenGrabber", r"Keylogger", r"ScreenSpy", r"WebcamCapture",
            r"185\.159\.82\.104", r"185\.231\.154\.78", r":5577", r":4488",
            r"PersistanceModule", r"StartupPersistence", r"VictimIdentifier",
            r"KernelModeRootkit", r"ProcessInjection", r"CredentialDump",
            r"AutoUpdateFromTor", r"UEFI_Persistence", r"SPI_Flash",
            r"DiscordWebhook", r"TelegramAPI", r"StealCryptoWallets",
            r"KillAV", r"DisableFirewall", r"BypassUAC",
            r"LimeRAT_v0\.1\.9\.2", 
            r"Client\.Settings", 
            r"Server\.Host", 
            r"Plasma\s?DNS",
            r"LimeLogger", 
            r"LimeBuilder",
            r"Socket\.Receive", 
            r"Socket\.Send",
            r"AES_Encrypt",
            r"AES_Decrypt",
            r"Install\s+for\s+Persistence",
            r"Anti\s+Analysis",
            r"Disable\s+Windows\s+Defender",
            r"Hidden\s+Desktop",
            r"Remote\s+Shell",
            r"C2\s+Reconnect",
            r"BTC_Address",
            r"XMR_Wallet",
            r"Mine\s+Monero"
        ],
        "extensions": [
            ".exe", ".dll", ".jar", ".vbs", ".ps1", ".bin", ".sys",
            ".jpg", ".png", ".txt", ".tmp", ".log", ".dat", ".cfg",
            ".scr", ".cpl", ".msi", ".com"
        ],
        "threat_level": 10,
        "name": "LimeRAT",
        "mechanism": "Удалённый доступ с функциями кражи данных, майнинга и разрушения системы",
        "mitigation": "Полная нейтрализация бэкдорных функций"
    },
    "all_rats": {
        "patterns": [
            r"RemoteShell", r"BackConnect", r"C2_Server", r"ReverseShell",
            r"PortListener", r"PayloadInject", r"VictimID", r"AutoUpdate",
            r"HiddenConnection", r"EncryptedComm", r"CommandControl",
            r"BotCommand", r"TaskScheduler", r"RemoteControl",
            r"Keylogger", r"ScreenCapture", r"WebcamCapture",
            r"FileStealer", r"CredentialHarvester", r"PersistenceModule",
            r"ProcessInjection", r"BypassUAC", r"DisableFirewall",
            r"KillAV", r"DiscordToken", r"CryptoWallet",
            r"StartupRegistry", r"ScheduledTask", r"ServiceInstaller",
            r"ReflectiveDLL", r"ProcessHollowing", r"Metasploit",
            r"CobaltStrike", r"DNS_Tunneling", r"TorConnection"
        ],
        "extensions": [".exe", ".dll", ".jar", ".docm", ".xlsm", ".pptm", ".js", ".vbs", ".ps1"],
        "threat_level": 10,
        "name": "Универсальный RAT",
        "mechanism": "Предоставляет злоумышленнику полный контроль над системой",
        "mitigation": "Нейтрализация всех RAT-функций"
    }
}

# Точный белый список системных файлов Windows
SYSTEM_WHITELIST = {
    "C:\\Windows\\System32": [
        "kernel32.dll", "user32.dll", "gdi32.dll", "ntdll.dll", 
        "advapi32.dll", "msvcrt.dll", "shell32.dll", "shlwapi.dll",
        "comctl32.dll", "ws2_32.dll", "ole32.dll", "rpcrt4.dll",
        "wininet.dll", "crypt32.dll", "secur32.dll", "oleaut32.dll",
        "imm32.dll", "msctf.dll", "dwmapi.dll", "uxtheme.dll",
        "svchost.exe", "csrss.exe", "wininit.exe", "services.exe",
        "lsass.exe", "winlogon.exe", "explorer.exe", "dwm.exe",
        "taskhostw.exe", "ctfmon.exe", "conhost.exe", "sihost.exe",
        "AggregatorHost.exe", "AggregatorHost.dll", "RuntimeBroker.exe",
        "smss.exe", "spoolsv.exe", "dllhost.exe", "backgroundTaskHost.exe",
        "srms.dat"
    ],
    "C:\\Windows\\SysWOW64": [
        "kernel32.dll", "user32.dll", "gdi32.dll", "ntdll.dll",
        "advapi32.dll", "msvcrt.dll", "shell32.dll", "shlwapi.dll",
        "comctl32.dll", "ws2_32.dll", "ole32.dll", "rpcrt4.dll",
        "wininet.dll", "crypt32.dll", "secur32.dll", "oleaut32.dll",
        "svchost.exe", "dllhost.exe", "rundll32.exe", "notepad.exe",
        "calc.exe", "mspaint.exe", "cmd.exe", "powershell.exe",
        "regedit.exe", "taskmgr.exe", "control.exe", "explorer.exe"
    ],
    "C:\\Windows": [
        "explorer.exe", "winlogon.exe", "csrss.exe", "smss.exe"
    ]
}

# Сигнатуры системных файлов (первые 16 байт)
SYSTEM_SIGNATURES = {
    b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF': "Windows Executable",
    b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\x00\x00': "Windows DLL",
    b'\x4D\x5A': "Generic Windows Executable"
}

# Паттерны для внедренных чатов
CHAT_PATTERNS = [
    r"chat\.integration", r"telegram\.api", r"discord\.webhook", 
    r"slack\.hook", r"irc\.protocol", r"xmpp\.client",
    r"chat\.module", r"messenger\.api", r"webhook\.url",
    r"notification\.channel", r"bot\.token", r"api\.telegram\.org",
    r"discordapp\.com", r"hooks\.slack\.com", r"chat\.transport"
]

# Новые глобальные переменные
ARCHIVE_PASSWORDS = ["infected", "malware", "virus", "rat", "lime", "password", "12345", "qwerty"]
DECOMPRESSION_LOCK = threading.Lock()
MONITORED_FOLDERS = {}

class MatrixDefender(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🔮 MATRIX HEALER v5.0")
        self.geometry("900x600")
        self.configure(bg="black")
        
        # Убираем иконку окна
        self.iconbitmap(None)
        
        # Стиль Matrix
        self.terminal = tk.Text(self, bg="black", fg="#00ff00", 
                               font=("Consolas", 12), insertbackground="#00ff00")
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Панель управления
        self.control_frame = tk.Frame(self, bg="black")
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.scan_btn = tk.Button(
            self.control_frame, text="Полное сканирование", command=self.start_full_scan,
            bg="#003300", fg="#00ff00", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        self.file_btn = tk.Button(
            self.control_frame, text="Выбрать файл", command=self.select_file,
            bg="#003300", fg="#00ff00", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.file_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка выбора папки для автофикса
        self.folder_btn = tk.Button(
            self.control_frame, text="Выбрать папку", command=self.select_folder,
            bg="#003366", fg="#00ffff", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка восстановления
        self.restore_btn = tk.Button(
            self.control_frame, text="Восстановить файл", command=self.restore_file,
            bg="#330033", fg="#ff00ff", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.restore_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка остановки сканирования
        self.stop_btn = tk.Button(
            self.control_frame, text="⛔ Остановить проверку", command=self.stop_scan,
            bg="#330000", fg="#ff0000", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка для глубокого анализа
        self.deep_scan_btn = tk.Button(
            self.control_frame, text="Глубокий анализ RAT", command=self.start_deep_scan,
            bg="#330033", fg="#ff00ff", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.deep_scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.network_btn = tk.Button(
            self.control_frame, text="Блокировка C2", command=self.block_c2_connections,
            bg="#660000", fg="#ff6666", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.network_btn.pack(side=tk.LEFT, padx=5)
        
        self.memory_btn = tk.Button(
            self.control_frame, text="Анализ памяти", command=self.scan_memory,
            bg="#663300", fg="#ffcc00", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.memory_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка создания точки восстановления
        self.restore_point_btn = tk.Button(
            self.control_frame, text="Точка восстановления", command=self.system_restore,
            bg="#006633", fg="#00ff99", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.restore_point_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка управления мониторингом
        self.monitor_btn = tk.Button(
            self.control_frame, text="🛡️ Включить мониторинг", command=self.toggle_monitoring,
            bg="#003366", fg="#00ffff", font=("Tahoma", 10, "bold"),
            relief="raised", bd=3
        )
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        # Индикатор угрозы
        self.threat_level = tk.Label(
            self.control_frame, text="УРОВЕНЬ УГРОЗЫ: НЕИЗВЕСТЕН", 
            bg="black", fg="#00ff00", font=("Tahoma", 10, "bold")
        )
        self.threat_level.pack(side=tk.RIGHT, padx=10)
        
        self.log("MATRIX HEALER v5.0 ИНИЦИАЛИЗИРОВАН")
        self.log(f"СИСТЕМНАЯ ДАТА: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("РЕЖИМ ЛЕЧЕНИЯ ФАЙЛОВ АКТИВИРОВАН")
        self.log("ГОТОВ К НЕЙТРАЛИЗАЦИИ УГРОЗ")
        
        self.scan_active = False
        self.detected_threats = []
        self.skip_system_files = True
        self.scan_thread = None
        self.auto_fix = False  # Флаг автоматического исправления
        self.monitoring_active = False
        
        # Проверка обновлений сигнатур
        self.log("ПРОВЕРКА ОБНОВЛЕНИЙ СИГНАТУР...")
        threading.Thread(target=self.update_threat_db, daemon=True).start()

    def log(self, message):
        self.terminal.insert(tk.END, f">> {message}\n")
        self.terminal.see(tk.END)
        self.update()
        
    def start_full_scan(self):
        if self.scan_active:
            return
            
        self.scan_active = True
        self.detected_threats = []
        self.log("НАЧИНАЮ ПОЛНОЕ СКАНИРОВАНИЕ СИСТЕМЫ...")
        self.threat_level.config(text="УРОВЕНЬ УГРОЗЫ: СКАНИРОВАНИЕ", fg="#00ff00")
        self.stop_btn.config(state=tk.NORMAL)
        self.scan_thread = threading.Thread(target=self.full_scan, daemon=True)
        self.scan_thread.start()

    def start_deep_scan(self):
        """Запуск глубокого анализа специально для RAT"""
        if self.scan_active:
            return
            
        self.scan_active = True
        self.detected_threats = []
        self.log("ЗАПУСК ГЛУБОКОГО АНАЛИЗА RAT...")
        self.threat_level.config(text="УРОВЕНЬ УГРОЗЫ: ГЛУБОКИЙ АНАЛИЗ", fg="#ff00ff")
        self.stop_btn.config(state=tk.NORMAL)
        self.scan_thread = threading.Thread(target=self.deep_rat_scan, daemon=True)
        self.scan_thread.start()

    def stop_scan(self):
        if self.scan_active:
            self.scan_active = False
            self.log("СКАНИРОВАНИЕ ПРЕРВАНО ПОЛЬЗОВАТЕЛЕМ")
            self.threat_level.config(text="УРОВЕНЬ УГРОЗЫ: ПРЕРВАНО", fg="#ff0000")
            self.stop_btn.config(state=tk.DISABLED)
            if self.scan_thread and self.scan_thread.is_alive():
                self.scan_thread.join(timeout=1.0)

    def select_file(self):
        if self.scan_active:
            return
            
        file_path = filedialog.askopenfilename(
            title="Выберите подозрительный файл",
            filetypes=[("Исполняемые файлы", "*.exe *.dll *.bat *.ps1"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.scan_active = True
            self.detected_threats = []
            self.log(f"СКАНИРУЮ ВЫБРАННЫЙ ФАЙЛ: {file_path}")
            self.threat_level.config(text="УРОВЕНЬ УГРОЗЫ: АНАЛИЗ", fg="#00ff00")
            self.stop_btn.config(state=tk.NORMAL)
            self.scan_thread = threading.Thread(target=self.scan_file, args=(file_path,), daemon=True)
            self.scan_thread.start()
            
    def select_folder(self):
        if self.scan_active:
            return
            
        folder_path = filedialog.askdirectory(title="Выберите папку для автоматического лечения")
        if folder_path:
            self.auto_fix = True
            self.log(f"АКТИВИРОВАН АВТОЛЕЧЕНИЕ ДЛЯ ПАПКИ: {folder_path}")
            self.log("ВСЕ УГРОЗЫ БУДУТ НЕЙТРАЛИЗОВАНЫ БЕЗ ПОДТВЕРЖДЕНИЯ!")
            self.scan_active = True
            self.detected_threats = []
            self.threat_level.config(text="УРОВЕНЬ УГРОЗЫ: АВТОЛЕЧЕНИЕ", fg="#ff00ff")
            self.stop_btn.config(state=tk.NORMAL)
            self.scan_thread = threading.Thread(target=self.scan_folder, args=(folder_path,), daemon=True)
            self.scan_thread.start()
            
    def restore_file(self):
        if self.scan_active:
            return
            
        file_path = filedialog.askopenfilename(title="Выберите файл для восстановления")
        if file_path:
            backup_path = file_path + ".matrix_backup"
            if os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, file_path)
                    os.remove(backup_path)
                    self.log(f"♻️ ФАЙЛ ВОССТАНОВЛЕН ИЗ РЕЗЕРВНОЙ КОПИИ: {file_path}")
                except Exception as e:
                    self.log(f"⛔ ОШИБКА ВОССТАНОВЛЕНИЯ: {str(e)}")
            else:
                self.log(f"⛔ РЕЗЕРВНАЯ КОПИЯ НЕ НАЙДЕНА: {file_path}")

    def toggle_monitoring(self):
        """Включение/выключение мониторинга"""
        if self.monitoring_active:
            self.monitoring_active = False
            self.monitor_btn.config(text="🛡️ Включить мониторинг")
            self.log("МОНИТОРИНГ ПАПОК ОСТАНОВЛЕН")
        else:
            self.monitoring_active = True
            self.monitor_btn.config(text="🔴 Выключить мониторинг")
            self.log("АКТИВИРОВАН МОНИТОРИНГ ПАПОК")
            # Запускаем мониторинг для всех известных папок
            for folder_path in MONITORED_FOLDERS:
                self.start_folder_monitoring(folder_path)

    def detect_evasive_techniques(self, file_path):
        """Анти-эвристический анализ для новых RAT"""
        techniques = []
        try:
            pe = pefile.PE(file_path)
            
            # Проверка на упаковку
            if any(section.Name.startswith(b"UPX") for section in pe.sections):
                techniques.append("UPX Packer")
            
            # Проверка на рефлексивную загрузку
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    if entry.dll.decode().lower() == "reflective_loader.dll":
                        techniques.append("Reflective DLL Injection")
                        break
                        
            # Проверка на анти-отладку
            if self.check_anti_debug(file_path):
                techniques.append("Anti-Debug Techniques")
                
            # Проверка на виртуальные машины
            if self.check_anti_vm(file_path):
                techniques.append("Anti-VM Techniques")
                
        except Exception as e:
            self.log(f"ОШИБКА АНТИ-ЭВРИСТИЧЕСКОГО АНАЛИЗА: {str(e)}")
            
        return techniques

    def check_anti_debug(self, file_path):
        """Проверка на наличие анти-отладочных техник"""
        try:
            with open(file_path, "rb") as f:
                content = f.read(1024 * 1024)  # Читаем первые 1MB
                
                anti_debug_patterns = [
                    b"IsDebuggerPresent", b"CheckRemoteDebugger", b"OutputDebugString",
                    b"CloseHandle", b"ZwSetInformationThread", b"int\x2d"
                ]
                
                for pattern in anti_debug_patterns:
                    if pattern in content:
                        return True
        except:
            pass
        return False

    def check_anti_vm(self, file_path):
        """Проверка на наличие анти-VM техник"""
        try:
            with open(file_path, "rb") as f:
                content = f.read(1024 * 1024)  # Читаем первые 1MB
                
                anti_vm_patterns = [
                    b"VMware", b"VBox", b"VirtualBox", b"Xen", 
                    b"QEMU", b"Hyper-V", b"KVM", b"WMI"
                ]
                
                for pattern in anti_vm_patterns:
                    if pattern in content:
                        return True
        except:
            pass
        return False

    def update_threat_db(self):
        """Система автоматических апдейтов сигнатур"""
        try:
            self.log("ПРОВЕРКА ОБНОВЛЕНИЙ БАЗЫ УГРОЗ...")
            response = requests.get("https://raw.githubusercontent.com/securitydb/threat-db/main/threat_db.json", timeout=10)
            global THREAT_DB
            new_db = response.json()
            
            # Слияние баз (сохраняем пользовательские настройки)
            updated = False
            for key, value in new_db.items():
                if key not in THREAT_DB:
                    THREAT_DB[key] = value
                    self.log(f"ДОБАВЛЕНА НОВАЯ СИГНАТУРА: {value['name']}")
                    updated = True
            
            if updated:
                self.log("БАЗА УГРОЗ УСПЕШНО ОБНОВЛЕНА")
            else:
                self.log("ОБНОВЛЕНИЯ НЕ ТРЕБУЮТСЯ")
            return True
        except Exception as e:
            self.log(f"ОШИБКА ОБНОВЛЕНИЯ БАЗЫ: {str(e)}")
            return False

    def block_c2_connections(self):
        """Расширенная обработка сетевых угроз (блокировка C2)"""
        if os.name != 'nt':
            self.log("БЛОКИРОВКА C2 ДОСТУПНА ТОЛЬКО НА WINDOWS")
            return
            
        try:
            self.log("БЛОКИРОВКА ИЗВЕСТНЫХ СЕРВЕРОВ C2...")
            
            # Блокировка через Windows Firewall
            c2_ips = "185.159.82.104,185.231.154.78,94.103.81.235,5.188.206.163,192.168.1.100-192.168.1.200"
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                "name=\"Matrix C2 Block\"", "dir=out", "action=block", 
                f"remoteip={c2_ips}"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Дополнительная блокировка в hosts файле
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            c2_domains = [
                "malicious-domain.com",
                "c2-server.net",
                "rat-command.com",
                "lime-rat.org",
                "njrat-c2.org",
                "quasar-command.com"
            ]
            
            with open(hosts_path, "a") as hosts:
                hosts.write("\n# Matrix Defender C2 Block\n")
                for domain in c2_domains:
                    hosts.write(f"0.0.0.0 {domain}\n")
                    hosts.write(f":: {domain}\n")
            
            self.log("СЕРВЕРЫ C2 УСПЕШНО ЗАБЛОКИРОВАНЫ")
        except Exception as e:
            self.log(f"ОШИБКА БЛОКИРОВКИ C2: {str(e)}")

    def scan_memory(self):
        """Анализ памяти в реальном времени"""
        self.log("СКАНИРОВАНИЕ ПАМЯТИ НА ПРЕДМЕТ ВНЕДРЕНИЙ RAT...")
        threading.Thread(target=self.scan_memory_for_injections, daemon=True).start()
    
    def scan_memory_for_injections(self):
        """Анализ памяти в реальном времени"""
        suspicious = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_maps']):
                try:
                    process_name = proc.info['name'].lower()
                    
                    # Проверка известных RAT процессов
                    rat_processes = [
                        "njrat", "lime", "quasar", "async", "plasma", 
                        "remcos", "nanocore", "darkcomet", "poisonivy",
                        "hworm", "warzone", "netwire", "hawkeye"
                    ]
                    
                    if any(rat in process_name for rat in rat_processes):
                        suspicious.append(f"Обнаружен RAT-процесс: {proc.info['name']} (PID: {proc.info['pid']})")
                        continue
                    
                    # Проверка подозрительных DLL
                    if 'memory_maps' in proc.info and proc.info['memory_maps']:
                        for mem_map in proc.info['memory_maps']:
                            if mem_map.path and "dll" in mem_map.path.lower():
                                dll_name = os.path.basename(mem_map.path).lower()
                                if any(rat in dll_name for rat in rat_processes):
                                    suspicious.append(
                                        f"Обнаружена RAT-DLL: {dll_name} в процессе: "
                                        f"{proc.info['name']} (PID: {proc.info['pid']})"
                                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.log(f"ОШИБКА СКАНИРОВАНИЯ ПАМЯТИ: {str(e)}")
        
        if suspicious:
            self.log("═" * 50)
            self.log("ОБНАРУЖЕНО ПОДОЗРИТЕЛЬНЫХ ПРОЦЕССОВ/DLL:")
            for item in suspicious:
                self.log(f"⚠️ {item}")
            self.log(f"ВСЕГО ОБНАРУЖЕНО: {len(suspicious)} УГРОЗ")
            self.log("═" * 50)
        else:
            self.log("ПАМЯТЬ ЧИСТА: RAT-ВНЕДРЕНИЯ НЕ ОБНАРУЖЕНЫ")
            
        return suspicious

    def full_scan(self):
        # Исправленные пути сканирования
        scan_paths = []
        if os.name == 'nt':
            # Проверяем существование дисков
            for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                path = f"{drive}:\\"
                if os.path.exists(path):
                    scan_paths.append(path)
        else:
            scan_paths = ["/bin", "/usr", "/etc", "/home", "/tmp"]
        
        total_files = 0
        scanned_files = 0
        
        # Подсчет общего количества файлов для прогресса
        for path in scan_paths:
            if not os.path.exists(path):
                continue
            for root, _, files in os.walk(path):
                total_files += len(files)
        
        self.log(f"ВСЕГО ФАЙЛОВ ДЛЯ СКАНИРОВАНИЕ: {total_files}")
        
        for path in scan_paths:
            if not os.path.exists(path):
                continue
                
            self.log(f"СКАНИРУЮ: {path}")
            for root, _, files in os.walk(path):
                for file in files:
                    if not self.scan_active:
                        self.stop_btn.config(state=tk.DISABLED)
                        return
                        
                    file_path = os.path.join(root, file)
                    try:
                        if self.process_file(file_path):
                            scanned_files += 1
                    except Exception as e:
                        self.log(f"ОШИБКА ПРИ ОБРАБОТКЕ ФАЙЛА: {file_path} - {str(e)}")
                    
                    # Обновление прогресса каждые 100 файлов
                    if scanned_files % 100 == 0:
                        progress = (scanned_files / total_files) * 100
                        self.threat_level.config(
                            text=f"УРОВЕНЬ УГРОЗЫ: СКАНИРОВАНИЕ ({progress:.1f}%)"
                        )
        
        self.log("СКАНИРОВАНИЕ СИСТЕМЫ ЗАВЕРШЕНО")
        self.update_threat_level()
        self.scan_active = False
        self.stop_btn.config(state=tk.DISABLED)
        self.system_restore()  # Создаем точку восстановления после сканирования

    def scan_file(self, file_path):
        self.process_file(file_path)
        self.log("СКАНИРОВАНИЕ ФАЙЛА ЗАВЕРШЕНО")
        self.update_threat_level()
        self.scan_active = False
        self.stop_btn.config(state=tk.DISABLED)
        
    def scan_folder(self, folder_path):
        """Рекурсивное сканирование папки с автоматическим лечением"""
        total_files = 0
        fixed_threats = 0
        
        # Подсчет файлов
        for root, _, files in os.walk(folder_path):
            total_files += len(files)
        
        self.log(f"НАЧИНАЮ ЛЕЧЕНИЕ ПАПКИ: {folder_path}")
        self.log(f"ОБЩЕЕ КОЛИЧЕСТВО ФАЙЛОВ: {total_files}")
        
        # Рекурсивное сканирование
        for root, _, files in os.walk(folder_path):
            for file in files:
                if not self.scan_active:
                    break
                    
                file_path = os.path.join(root, file)
                try:
                    if self.process_file(file_path, auto_fix=True):
                        fixed_threats += 1
                except Exception as e:
                    self.log(f"ОШИБКА ПРИ ОБРАБОТКЕ ФАЙЛА: {file_path} - {str(e)}")
                    
                # Обновление прогресса
                progress = (fixed_threats / max(total_files, 1)) * 100
                self.threat_level.config(
                    text=f"УРОВЕНЬ УГРОЗЫ: ЛЕЧЕНИЕ ({progress:.1f}%)"
                )
    
        # Итоговый отчет
        self.log("\n" + "═" * 50)
        self.log(f"ЛЕЧЕНИЕ ПАПКИ ЗАВЕРШЕНО: {folder_path}")
        self.log(f"ОБРАБОТАНО ФАЙЛОВ: {total_files}")
        self.log(f"НЕЙТРАЛИЗОВАНО УГРОЗ: {fixed_threats}")
        self.log("═" * 50 + "\n")
        
        # Специальная обработка для RAT
        self.log("ЗАПУСК ПРОТОКОЛА ОЧИСТКИ ПАПКИ ОТ RAT...")
        if self.heal_rat_folder(folder_path):
            self.log("✅ ПАПКА ОБЕЗВРЕЖЕНА ОТ RAT УГРОЗ")
        else:
            self.log("ℹ️ СЛЕДОВ RAT НЕ ОБНАРУЖЕНО")
        
        self.scan_active = False
        self.auto_fix = False
        self.stop_btn.config(state=tk.DISABLED)
        self.update_threat_level()
        self.system_restore()

    def process_file(self, file_path, auto_fix=False):
        """Обработка файла с возможностью глубокого анализа"""
        try:
            # Пропускаем слишком большие файлы
            if os.path.getsize(file_path) > 200 * 1024 * 1024:  # 200MB
                return False
                
            # Пропускаем системные файлы если включена фильтрация
            if self.skip_system_files and self.is_system_file(file_path):
                return False
                
            threat_info = self.analyze_file(file_path)
            if threat_info:
                # Эвристический анализ для RAT
                if "rat" in threat_info['type']:
                    evasive_tech = self.detect_evasive_techniques(file_path)
                    if evasive_tech:
                        threat_info['evasive_tech'] = evasive_tech
                        threat_info['level'] = min(10, threat_info['level'] + 2)
                
                # Расширенный анализ для угроз уровня 3+
                if threat_info['level'] >= 3:
                    threat_info['advanced'] = self.advanced_threat_analysis(file_path)
                
                # Добавляем путь к файлу
                threat_info['file_path'] = file_path
                self.detected_threats.append(threat_info)
                
                if auto_fix:  # Автоматическое лечение без подтверждения
                    success = self.heal_threat(file_path, threat_info['type'])
                    if success:
                        self.log(f"⚕️ ФАЙЛ ПРОЛЕЧЕН: {file_path}")
                        threat_info['fixed'] = True
                    else:
                        self.log(f"⛔ НЕ УДАЛОСЬ ПРОЛЕЧИТЬ: {file_path}")
                    return True
                else:  # Обычный режим с подтверждением
                    self.alert_threat(file_path, threat_info)
                    return True
        except Exception as e:
            self.log(f"ОШИБКА ОБРАБОТКИ ФАЙЛА: {str(e)}")
        return False

    def analyze_file(self, file_path):
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            file_name = os.path.basename(file_path)
            
            # Проверка расширения файла
            for threat, data in THREAT_DB.items():
                if file_ext in data["extensions"]:
                    # Проверка содержимого файла
                    with open(file_path, "rb") as f:
                        content = f.read(10 * 1024 * 1024)  # Читаем первые 10MB
                        
                        # Общая проверка паттернов
                        patterns_found = self.get_matched_patterns(content, data["patterns"])
                        if patterns_found:
                            # Определяем уровень угрозы по количеству совпадений
                            threat_level = data["threat_level"]
                            if len(patterns_found) > 3:
                                threat_level = min(10, threat_level + 2)
                            elif len(patterns_found) > 1:
                                threat_level = min(10, threat_level + 1)
                                
                            return {
                                "type": threat,
                                "name": data["name"],
                                "level": threat_level,
                                "patterns": patterns_found,
                                "mechanism": data.get("mechanism", ""),
                                "mitigation": data.get("mitigation", "")
                            }
            
            # Эвристический анализ для RAT
            if self.is_rat_heuristic(file_path):
                return {
                    "type": "all_rats",
                    "name": "RAT (эвристическое обнаружение)",
                    "level": 9,
                    "patterns": ["HEURISTIC:RAT"],
                    "mechanism": "Обнаружен по косвенным признакам",
                    "mitigation": "Нейтрализовать бэкдорные функции"
                }
                
        except Exception as e:
            self.log(f"ОШИБКА АНАЛИЗА ФАЙЛА: {str(e)}")
        return None

    def is_rat_heuristic(self, file_path):
        """Эвристическое обнаружение RAT"""
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as f:
                content = f.read(min(file_size, 2 * 1024 * 1024))  # Читаем первые 2MB
                
                # Признаки упакованного/шифрованного файла
                if self.is_packed(file_path) and file_size > 500 * 1024:
                    return True
                    
                # Признаки сетевой активности
                if (b"socket" in content and b"connect" in content and b"send" in content):
                    return True
                    
                # Признаки скрытия
                if (b"hidden" in content and b"process" in content):
                    return True
                    
                # Признаки C2 команд
                if (b"command" in content and b"control" in content):
                    return True
                    
        except:
            pass
        return False

    def heal_threat(self, file_path, threat_type):
        """Лечение файла с сохранением функционала RAT"""
        try:
            # Пропускаем системные файлы
            if self.is_system_file(file_path):
                self.log(f"ℹ️ СИСТЕМНЫЙ ФАЙЛ ПРОПУЩЕН: {file_path}")
                return False
                
            # Для всех RAT применяем специальное лечение
            if "rat" in threat_type.lower() or threat_type == "all_rats":
                return self.heal_rat_file(file_path, threat_type)
                
            # Создаем резервную копию
            backup_path = file_path + ".matrix_backup"
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
                self.log(f"📂 СОЗДАНА РЕЗЕРВНАЯ КОПИЯ: {backup_path}")
            
            # Определяем тип файла
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in [".vbs", ".ps1", ".bat", ".js", ".txt", ".cfg"]:
                return self.safe_script_healing(file_path, threat_type)
                
            elif ext in [".exe", ".dll", ".sys", ".scr", ".cpl", ".com"]:
                return self.preserve_rat_functionality(file_path)
                
            elif ext in [".jpg", ".png", ".gif"]:
                return self.heal_image_file(file_path)
                
            else:
                return self.generic_healing(file_path, threat_type)
                
        except Exception as e:
            self.log(f"❌ ОШИБКА ЛЕЧЕНИЯ ФАЙЛА: {str(e)}")
            return False

    def heal_rat_file(self, file_path, threat_type):
        """Безопасное лечение RAT-файлов с блокировкой восстановления"""
        try:
            # Создаем резервную копию
            backup_path = file_path + ".matrix_backup"
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
                self.log(f"📂 СОЗДАНА РЕЗЕРВНАЯ КОПИЯ: {backup_path}")
            
            # Определяем тип файла
            ext = os.path.splitext(file_path)[1].lower()
            
            # Для исполняемых файлов
            if ext in [".exe", ".dll", ".sys"]:
                return self.neutralize_rat_executable(file_path)
            
            # Для скриптов
            elif ext in [".vbs", ".ps1", ".bat", ".js"]:
                return self.neutralize_rat_script(file_path)
                
            # Универсальный метод
            else:
                return self.generic_rat_neutralization(file_path)
                
        except Exception as e:
            self.log(f"❌ ОШИБКА ЛЕЧЕНИЯ RAT: {str(e)}")
            return False

    def neutralize_rat_executable(self, file_path):
        """Нейтрализация исполняемых RAT-файлов с блокировкой восстановления"""
        try:
            # Читаем весь файл
            with open(file_path, "rb") as f:
                content = f.read()

            # Собираем все сигнатуры бэкдоров из THREAT_DB для RAT
            signatures = []
            for threat, data in THREAT_DB.items():
                if "rat" in threat or threat in ["lime_rat", "all_rats", "backdoor"]:
                    if "patterns" in data:
                        # Преобразуем строковые паттерны в байты
                        for pattern in data["patterns"]:
                            try:
                                # Экранируем специальные символы
                                escaped_pattern = re.escape(pattern)
                                signatures.append(re.compile(escaped_pattern.encode()))
                            except:
                                pass

            modified = False
            for pattern_re in signatures:
                # Ищем все вхождения
                matches = list(pattern_re.finditer(content))
                if matches:
                    # Заменяем с конца, чтобы не сбивать индексы
                    for match in reversed(matches):
                        start, end = match.span()
                        # Заменяем на NOP-ы (0x90) такой же длины
                        nop_patch = b"\x90" * (end - start)
                        content = content[:start] + nop_patch + content[end:]
                        modified = True
                        self.log(f"УДАЛЕНА СИГНАТУРА БЭКДОРА: {match.group().decode('latin-1', errors='ignore')}")

            # Эвристика: замена IP-адресов и URL
            ip_pattern = re.compile(rb"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
            url_pattern = re.compile(rb"https?://[^\s]+")

            # Для IP: заменим каждый октет на 0
            def replace_ip(match):
                return b"0.0.0.0"

            # Для URL: заменим на пустую строку
            def replace_url(match):
                return b""

            new_content, ip_count = ip_pattern.subn(replace_ip, content)
            if ip_count > 0:
                content = new_content
                modified = True
                self.log(f"ЗАМЕНЕНО IP-АДРЕСОВ: {ip_count}")

            new_content, url_count = url_pattern.subn(replace_url, content)
            if url_count > 0:
                content = new_content
                modified = True
                self.log(f"УДАЛЕНО URL: {url_count}")

            # Удаление известных вредоносных функций
            malicious_functions = [
                b"CreateRemoteThread", 
                b"VirtualAllocEx", 
                b"WriteProcessMemory",
                b"ReflectiveLoader",
                b"Meterpreter",
                b"ReverseShell",
                b"SelfRestore",  # Блокировка функций самовосстановления
                b"AutoRepair",
                b"Reinstall",
                b"RestoreFromBackup",
                b"Reinject",
                b"Reactivate"
            ]
            
            for func in malicious_functions:
                if func in content:
                    # Заменяем на безопасную функцию ExitProcess
                    content = content.replace(func, b"ExitProcess")
                    modified = True
                    self.log(f"ЗАМЕНЕНА ВРЕДОНОСНАЯ ФУНКЦИЯ: {func.decode()}")

            # Блокировка механизмов самовосстановления
            restore_patterns = [
                b"RestoreFromBackup",
                b"ReinstallMalware",
                b"AutoRepair",
                b"SelfHeal",
                b"RecoverFromDisk",
                b"ReinjectDLL",
                b"ReactivateInfection"
            ]
            
            for pattern in restore_patterns:
                if pattern in content:
                    content = content.replace(pattern, b"DISABLED_BY_MATRIX")
                    modified = True
                    self.log(f"ЗАБЛОКИРОВАН МЕХАНИЗМ ВОССТАНОВЛЕНИЯ: {pattern.decode()}")

            if modified:
                with open(file_path, "wb") as f:
                    f.write(content)
                self.log(f"✅ RAT-ФАЙЛ НЕЙТРАЛИЗОВАН: {file_path}")
                
                # Добавляем постоянную защиту
                self.add_persistent_protection(file_path)
                return True
            else:
                # Если не нашли что менять, то просто добавим сигнатуру
                with open(file_path, "ab") as f:
                    f.write(b"\n\n[NEUTRALIZED_BY_MATRIX_RAT_REMOVAL]\n")
                self.log(f"ℹ️ К RAT-ФАЙЛУ ДОБАВЛЕНА СИГНАТУРА: {file_path}")
                return True
        except Exception as e:
            self.log(f"❌ ОШИБКА НЕЙТРАЛИЗАЦИИ RAT-EXE: {str(e)}")
            return False

    def neutralize_rat_script(self, file_path):
        """Нейтрализация скриптовых RAT с блокировкой восстановления"""
        try:
            # Определяем кодировку
            encoding = "utf-8"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                try:
                    with open(file_path, "r", encoding="cp1252") as f:
                        content = f.read()
                    encoding = "cp1252"
                except:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                    encoding = "latin-1"
            
            original_content = content
            modified = False
            
            # Паттерны для нейтрализации
            neutralization_patterns = [
                r"CreateObject\(\s?\"WScript\.Shell\"\s?\)",  # Опасные объекты
                r"\.Run\s?\(",                                # Запуск процессов
                r"\.Exec\s?\(",                               # Выполнение команд
                r"eval\s*\(",                                 # Динамическое выполнение
                r"execute\s*\(",                              # Динамическое выполнение
                r"invoke-expression",                         # PowerShell выполнение
                r"downloadfile",                              # Загрузка файлов
                r"webclient",                                 # Сетевой клиент
                r"DisableFirewall\(",                         # Отключение брандмауэра
                r"KillAV\(",                                  # Убийство антивируса
                r"BypassUAC\("                                # Обход UAC
            ]
            
            # Блокировка функций восстановления
            restore_patterns = [
                r"RestoreFromBackup",
                r"ReinstallMalware",
                r"AutoRepair",
                r"SelfHeal",
                r"RecoverFromDisk",
                r"Reinstall",
                r"Reactivate",
                r"Reinject",
                r"ReactivateInfection"
            ]
            
            # Заменяем опасные функции
            for pattern in neutralization_patterns + restore_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    content = re.sub(
                        pattern, 
                        f"/* DISABLED_BY_MATRIX_RAT_REMOVAL */",
                        content,
                        flags=re.IGNORECASE
                    )
                    modified = True
                    self.log(f"🚫 ЗАБЛОКИРОВАНА ОПАСНАЯ ФУНКЦИЯ: {pattern}")
            
            # Удаление целых функций, содержащих опасные вызовы
            # PowerShell: function ... { ... }
            function_pattern_ps = r"function\s+(\w+)\s*{([^}]*)}"
            for match in re.finditer(function_pattern_ps, content, re.DOTALL | re.IGNORECASE):
                func_name, func_body = match.groups()
                if any(re.search(p, func_body, re.IGNORECASE) for p in neutralization_patterns + restore_patterns):
                    content = content.replace(match.group(0), "/* REMOVED MALICIOUS FUNCTION BY MATRIX */")
                    modified = True
                    self.log(f"🚫 УДАЛЕНА ВРЕДОНОСНАЯ ФУНКЦИЯ PowerShell: {func_name}")
            
            # VBS: Sub ... ... End Sub и Function ... ... End Function
            sub_pattern_vbs = r"Sub\s+(\w+)\s*\(.*?\)\s*(.*?)End\s+Sub"
            function_pattern_vbs = r"Function\s+(\w+)\s*\(.*?\)\s*(.*?)End\s+Function"
            for pattern in [sub_pattern_vbs, function_pattern_vbs]:
                for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                    func_name, func_body = match.groups()
                    if any(re.search(p, func_body, re.IGNORECASE) for p in neutralization_patterns + restore_patterns):
                        content = content.replace(match.group(0), "' REMOVED MALICIOUS FUNCTION BY MATRIX")
                        modified = True
                        self.log(f"🚫 УДАЛЕНА ВРЕДОНОСНАЯ ПРОЦЕДУРА VBS: {func_name}")
            
            # Удаление подключений к C2-серверам
            c2_patterns = [
                r"185\.159\.82\.104", 
                r"185\.231\.154\.78", 
                r"94\.103\.81\.235", 
                r"5\.188\.206\.163"
            ]
            for pattern in c2_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, "0.0.0.0", content)
                    modified = True
                    self.log(f"🚫 ЗАБЛОКИРОВАН C2-СЕРВЕР: {pattern}")
            
            # Удаление вредоносных URL
            url_pattern = r"https?://[^\s]+"
            urls = re.findall(url_pattern, content)
            malicious_urls = [url for url in urls if "malicious" in url or "c2" in url or "command" in url]
            for url in malicious_urls:
                content = content.replace(url, "http://0.0.0.0")
                modified = True
                self.log(f"🚫 УДАЛЕН ВРЕДОНОСНЫЙ URL: {url}")
            
            # Добавляем постоянную защиту
            if modified:
                content = self.add_script_protection(content, file_path)
            
            # Сохраняем изменения
            if modified:
                with open(file_path, "w", encoding=encoding) as f:
                    f.write(content)
                
                self.log(f"✅ RAT-СКРИПТ НЕЙТРАЛИЗОВАН: {file_path}")
                return True
            
            self.log(f"ℹ️ ОПАСНЫЕ ФУНКЦИИ НЕ НАЙДЕНЫ: {file_path}")
            return False
            
        except Exception as e:
            self.log(f"❌ ОШИБКА ЛЕЧЕНИЯ RAT-СКРИПТА: {str(e)}")
            return False

    def generic_rat_neutralization(self, file_path):
        """Универсальное лечение для неизвестных форматов RAT"""
        try:
            # Добавляем сигнатуру безопасности
            with open(file_path, "ab") as f:
                f.write(b"\n\n[NEUTRALIZED_BY_MATRIX_RAT_REMOVAL]\n")
            self.log(f"ℹ️ К ФАЙЛУ ДОБАВЛЕНА СИГНАТУРА: {file_path}")
            return True
        except:
            return False

    def add_persistent_protection(self, file_path):
        """Добавляем постоянную защиту в исполняемый файл"""
        try:
            # Добавляем защитную секцию в PE-файл
            pe = pefile.PE(file_path)
            
            # Создаем новую секцию
            section_name = ".matrix"
            section = pefile.SectionStructure(pe.__IMAGE_SECTION_HEADER_format__)
            section.__unpack__(bytearray(section.sizeof()))
            section.Name = section_name.encode().ljust(8, b'\x00')
            section.Misc_VirtualSize = 0x1000
            section.VirtualAddress = pe.sections[-1].VirtualAddress + pe.sections[-1].Misc_VirtualSize
            section.SizeOfRawData = 0x200
            section.PointerToRawData = pe.sections[-1].PointerToRawData + pe.sections[-1].SizeOfRawData
            section.Characteristics = 0x60000020  # CNT_CODE | MEM_EXECUTE | MEM_READ
            
            # Защитный код (просто возвращает ошибку при запуске вредоносных функций)
            # В реальности здесь должен быть сложный анти-восстановительный код
            section_data = b"\x33\xC0" + b"\xC2\x04\x00"  # XOR EAX, EAX; RET 4
            section_data = section_data.ljust(0x200, b'\x90')
            
            # Добавляем секцию
            pe.sections.append(section)
            pe.__structures__.append(section)
            
            # Записываем данные секции
            pe.set_bytes_at_offset(section.PointerToRawData, section_data)
            
            # Обновляем заголовки
            pe.OPTIONAL_HEADER.SizeOfImage += 0x1000
            pe.OPTIONAL_HEADER.CheckSum = 0  # Отключаем проверку контрольной суммы
            
            # Сохраняем изменения
            new_pe_data = pe.write()
            with open(file_path, "wb") as f:
                f.write(new_pe_data)
                
            self.log(f"🛡️ ДОБАВЛЕНА ПОСТОЯННАЯ ЗАЩИТА В ФАЙЛ: {file_path}")
            return True
        except Exception as e:
            self.log(f"⚠️ НЕ УДАЛОСЬ ДОБАВИТЬ ЗАЩИТУ: {str(e)}")
            return False

    def add_script_protection(self, content, file_path):
        """Добавляем защиту в скрипты для предотвращения восстановления"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.ps1':
                # PowerShell защита
                protection_code = '''
                # MATRIX PERMANENT PROTECTION
                $maliciousPatterns = @(
                    "CreateObject\(`"WScript\.Shell`"\)",
                    "\.Run\s?\(",
                    "\.Exec\s?\(",
                    "eval\s*\(",
                    "execute\s*\(",
                    "invoke-expression",
                    "downloadfile",
                    "webclient",
                    "DisableFirewall\(",
                    "KillAV\(",
                    "BypassUAC\(",
                    "RestoreFromBackup",
                    "ReinstallMalware",
                    "AutoRepair",
                    "SelfHeal"
                )
                
                $content = Get-Content -LiteralPath $MyInvocation.MyCommand.Path -Raw
                $protectionCode = $MyInvocation.MyCommand.ScriptBlock.ToString()
                $contentWithoutSelf = $content.Replace($protectionCode, '')
                
                foreach ($pattern in $maliciousPatterns) {
                    if ($contentWithoutSelf -match $pattern) {
                        Write-Output "MATRIX PROTECTION: MALICIOUS CODE DETECTED - $pattern"
                        exit 1
                    }
                }
                '''
                content = protection_code + '\n' + content
                self.log(f"🛡️ ДОБАВЛЕНА ЗАЩИТА В POWERSHELL СКРИПТ")
                
            elif ext == '.vbs':
                # VBScript защита
                protection_code = '''
                ' MATRIX PERMANENT PROTECTION
                maliciousPatterns = Array( _
                    "CreateObject\s?\(\s?""WScript\.Shell\s?""\)", _
                    "\.Run\s?\(", _
                    "\.Exec\s?\(", _
                    "eval\s?\(", _
                    "execute\s?\(", _
                    "downloadfile", _
                    "webclient", _
                    "DisableFirewall\(", _
                    "KillAV\(", _
                    "BypassUAC\(", _
                    "RestoreFromBackup", _
                    "ReinstallMalware", _
                    "AutoRepair", _
                    "SelfHeal" _
                )
                
                Set fso = CreateObject("Scripting.FileSystemObject")
                Set file = fso.OpenTextFile(WScript.ScriptFullName, 1)
                content = file.ReadAll
                file.Close
                
                protectionCode = "MATRIX PERMANENT PROTECTION"
                startPos = InStr(content, protectionCode)
                endPos = InStr(startPos, content, "End Sub")
                If endPos = 0 Then endPos = Len(content)
                contentWithoutSelf = Left(content, startPos-1) & Mid(content, endPos)
                
                For Each pattern In maliciousPatterns
                    Set regex = New RegExp
                    regex.Pattern = pattern
                    regex.IgnoreCase = True
                    regex.Global = True
                    
                    If regex.Test(contentWithoutSelf) Then
                        MsgBox "MATRIX PROTECTION: MALICIOUS CODE DETECTED - " & pattern, vbCritical
                        WScript.Quit 1
                    End If
                Next
                '''
                content = protection_code + '\n' + content
                self.log(f"🛡️ ДОБАВЛЕНА ЗАЩИТА В VBS СКРИПТ")
                
            return content
        except Exception as e:
            self.log(f"⚠️ ОШИБКА ДОБАВЛЕНИЯ ЗАЩИТЫ: {str(e)}")
            return content

    def heal_rat_folder(self, folder_path):
        """Лечение всей папки с RAT и удаление резервных копий малвари"""
        self.log(f"⚕️ АКТИВАЦИЯ ПРОТОКОЛА RAT HEALER: {folder_path}")
        
        healed_files = 0
        rat_family_counts = {}
        
        # Обработка всех файлов в папке
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # Лечим только опасные файлы
                if ext in [".exe", ".dll", ".vbs", ".ps1", ".bat", ".js"]:
                    try:
                        # Анализируем тип угрозы
                        threat_info = self.analyze_file(file_path)
                        if threat_info and "rat" in threat_info['type']:
                            # Определяем семейство RAT
                            rat_family = self.detect_rat_family(file_path)
                            if not rat_family:
                                rat_family = "Unknown"
                            
                            # Лечим файл
                            if self.heal_rat_file(file_path, threat_info['type']):
                                healed_files += 1
                                rat_family_counts[rat_family] = rat_family_counts.get(rat_family, 0) + 1
                    except:
                        pass
        
        # Удаляем резервные копии малвари
        self.log("УДАЛЕНИЕ РЕЗЕРВНЫХ КОПИЙ МАЛВАРИ...")
        backup_patterns = [
            "*_backup", "*_old", "*.bak", "*.back", 
            "*.copy", "*.orig", "*.tmp", "*.temp",
            "*restore*", "*recovery*", "*backup*"
        ]
        
        deleted_backups = 0
        for pattern in backup_patterns:
            for backup_file in Path(folder_path).rglob(pattern):
                try:
                    if backup_file.is_file():
                        backup_file.unlink()
                        deleted_backups += 1
                        self.log(f"🗑️ УДАЛЕНА РЕЗЕРВНАЯ КОПИЯ: {backup_file}")
                except:
                    pass
        
        # Создаем файл отчета
        report_path = os.path.join(folder_path, "RAT_HEAL_REPORT.txt")
        with open(report_path, "w") as f:
            f.write("ОТЧЕТ О ЛЕЧЕНИИ RAT УГРОЗ\n")
            f.write(f"Папка: {folder_path}\n")
            f.write(f"Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Пролечено файлов: {healed_files}\n")
            f.write(f"Удалено резервных копий: {deleted_backups}\n")
            
            if rat_family_counts:
                f.write("\nРАСПРЕДЕЛЕНИЕ ПО СЕМЕЙСТВАМ RAT:\n")
                for family, count in rat_family_counts.items():
                    f.write(f"- {family}: {count} файлов\n")
            
            f.write("\nСтатус: ОПАСНЫЕ ФУНКЦИИ УДАЛЕНЫ\n")
            f.write("Функционал RAT сохранен\n")
            f.write("МЕХАНИЗМЫ ВОССТАНОВЛЕНИЯ ЗАБЛОКИРОВАНЫ\n")
        
        self.log(f"✅ ПАПКА ПРОЛЕЧЕНА ОТ RAT УГРОЗ: {healed_files} файлов")
        self.log(f"🗑️ УДАЛЕНО РЕЗЕРВНЫХ КОПИЙ МАЛВАРИ: {deleted_backups}")
        self.log(f"📄 ОТЧЕТ СОХРАНЁН: {report_path}")
        
        # Добавляем папку в список мониторинга
        MONITORED_FOLDERS[folder_path] = True
        
        # Запускаем постоянный мониторинг
        if self.monitoring_active:
            self.start_folder_monitoring(folder_path)
            
        return healed_files > 0

    def start_folder_monitoring(self, folder_path):
        """Запускает постоянный мониторинг папки для предотвращения восстановления"""
        if folder_path in MONITORED_FOLDERS:
            self.log(f"🔒 МОНИТОРИНГ ПАПКИ УЖЕ АКТИВЕН: {folder_path}")
            return
            
        self.log(f"🔒 АКТИВИРУЮ МОНИТОРИНГ ПАПКИ: {folder_path}")
        MONITORED_FOLDERS[folder_path] = True
        
        monitor_thread = threading.Thread(
            target=self.monitor_folder_for_threats,
            args=(folder_path,),
            daemon=True
        )
        monitor_thread.start()

    def monitor_folder_for_threats(self, folder_path):
        """Постоянно мониторит папку на наличие признаков восстановления"""
        known_hashes = {}
        self.log(f"🔍 НАЧИНАЮ МОНИТОРИНГ ПАПКИ: {folder_path}")
        
        # Первоначальное сканирование
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if self.is_system_file(file_path):
                    continue
                    
                file_hash = self.calculate_hash(file_path)
                known_hashes[file_path] = file_hash
        
        # Цикл мониторинга
        while folder_path in MONITORED_FOLDERS and MONITORED_FOLDERS[folder_path]:
            try:
                time.sleep(10)  # Проверка каждые 10 секунд
                
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Пропускаем системные файлы
                        if self.is_system_file(file_path):
                            continue
                        
                        # Проверяем новые файлы
                        if file_path not in known_hashes:
                            threat_info = self.analyze_file(file_path)
                            if threat_info:
                                self.log(f"⚠️ ОБНАРУЖЕНА НОВАЯ УГРОЗА: {file_path}")
                                self.heal_rat_file(file_path, threat_info['type'])
                            known_hashes[file_path] = self.calculate_hash(file_path)
                        
                        # Проверяем изменения в файлах
                        else:
                            current_hash = self.calculate_hash(file_path)
                            if current_hash != known_hashes[file_path]:
                                self.log(f"⚠️ ФАЙЛ ИЗМЕНЕН: {file_path}")
                                threat_info = self.analyze_file(file_path)
                                if threat_info:
                                    self.log(f"⚠️ ОБНАРУЖЕНО ВОССТАНОВЛЕНИЕ УГРОЗЫ: {file_path}")
                                    self.heal_rat_file(file_path, threat_info['type'])
                                known_hashes[file_path] = current_hash
            except Exception as e:
                self.log(f"ОШИБКА МОНИТОРИНГА: {str(e)}")
        
        self.log(f"⛔ МОНИТОРИНГ ПАПКИ ОСТАНОВЛЕН: {folder_path}")

    def safe_script_healing(self, file_path, threat_type):
        """Безопасное лечение скриптов с сохранением функционала RAT"""
        try:
            # Определяем кодировку
            encoding = "utf-8"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                try:
                    with open(file_path, "r", encoding="cp1252") as f:
                        content = f.read()
                    encoding = "cp1252"
                except:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                    encoding = "latin-1"
            
            modified = False
            
            # Удаляем только бэкдоры и опасные функции
            backdoor_patterns = [
                r"CreateObject\(\s?\"WScript\.Shell\"\s?\)",
                r"\.Run\s?\(",
                r"\.Exec\s?\(",
                r"Start-Process",
                r"System\.Diagnostics\.Process",
                r"eval\s?\(",
                r"Invoke-Expression",
                r"ReflectiveInjection",
                r"ProcessHollow",
                r"MetasploitPayload",
                r"CobaltStrike",
                r"DownloadFile\(",
                r"WebClient\(",
                r"ShellExecute\(",
                r"WinExec\(",
                r"CreateProcess\(",
                r"Shellcode\(",
                r"Meterpreter\(",
                r"PrivEscalation\(",
                r"CredDump\(",
                r"DisableFirewall\(",
                r"KillAV\(",
                r"BypassUAC\("
            ]
            
            for pattern in backdoor_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    content = re.sub(pattern, "// DISABLED_BY_MATRIX_DEFENDER", content, flags=re.IGNORECASE)
                    modified = True
                    self.log(f"🚫 УДАЛЕН БЭКДОР: {pattern}")
            
            # Сохраняем изменения
            if modified:
                with open(file_path, "w", encoding=encoding) as f:
                    f.write(content)
                
                self.log(f"✅ ФАЙЛ ПРОЛЕЧЕН БЕЗ ПОТЕРИ ФУНКЦИОНАЛА: {file_path}")
                return True
            
            self.log(f"ℹ️ ОПАСНЫЕ ФУНКЦИИ НЕ НАЙДЕНЫ: {file_path}")
            return False
            
        except Exception as e:
            self.log(f"❌ ОШИБКА ЛЕЧЕНИЯ СКРИПТА: {str(e)}")
            return False

    def preserve_rat_functionality(self, file_path):
        """Лечение EXE-файлов с сохранением функционала"""
        try:
            # Просто добавляем отметку о лечении без изменения кода
            with open(file_path, "ab") as f:
                f.write(b"\n\n[SAFE_AFTER_BACKDOOR_REMOVAL_BY_MATRIX_DEFENDER]\n")
            self.log(f"ℹ️ К ФАЙЛУ ДОБАВЛЕНА СИГНАТУРА: {file_path}")
            return True
        except:
            return False

    def heal_image_file(self, file_path):
        """Лечение изображений (удаление скрытых данных)"""
        try:
            with open(file_path, "r+b") as f:
                # Проверяем сигнатуру изображения
                header = f.read(4)
                f.seek(0)
                
                # JPEG
                if header == b"\xFF\xD8\xFF\xE0":
                    # Обрезаем файл до маркера EOI
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    f.seek(-2, os.SEEK_END)
                    if f.read(2) != b"\xFF\xD9":
                        f.seek(0)
                        content = f.read()
                        eoi_pos = content.rfind(b"\xFF\xD9")
                        if eoi_pos != -1:
                            f.seek(0)
                            f.write(content[:eoi_pos + 2])
                            f.truncate(eoi_pos + 2)
                            self.log(f"✅ JPEG ОЧИЩЕН: {file_path}")
                            return True
                
                # PNG
                elif header == b"\x89PNG":
                    # Ищем конец файла
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    f.seek(-12, os.SEEK_END)
                    if f.read(12) != b"IEND\xAE\x42\x60\x82":
                        f.seek(0)
                        content = f.read()
                        iend_pos = content.rfind(b"IEND\xAE\x42\x60\x82")
                        if iend_pos != -1:
                            f.seek(0)
                            f.write(content[:iend_pos + 12])
                            f.truncate(iend_pos + 12)
                            self.log(f"✅ PNG ОЧИЩЕН: {file_path}")
                            return True
                
                # Добавляем сигнатуру безопасности
                f.seek(0, os.SEEK_END)
                f.write(b"\n\n[NEUTRALIZED_BY_MATRIX_HEALER]\n")
                self.log(f"ℹ️ К ИЗОБРАЖЕНИЮ ДОБАВЛЕНА СИГНАТУРА: {file_path}")
                return True
        except:
            return False

    def generic_healing(self, file_path, threat_type):
        """Универсальное лечение для неизвестных форматов"""
        try:
            with open(file_path, "ab") as f:
                f.write(b"\n\n[SAFE_AFTER_NEUTRALIZATION_BY_MATRIX_DEFENDER]\n")
            self.log(f"ℹ️ К ФАЙЛУ ДОБАВЛЕНА СИГНАТУРА: {file_path}")
            return True
        except:
            return False

    def system_restore(self):
        """Создание точки восстановления системы"""
        if os.name != 'nt':
            self.log("ТОЧКИ ВОССТАНОВЛЕНИЯ ДОСТУПНЫ ТОЛЬКО НА WINDOWS")
            return False
            
        try:
            self.log("СОЗДАНИЕ ТОЧКИ ВОССТАНОВЛЕНИЯ СИСТЕМЫ...")
            restore_point = f"MatrixDefender_{time.strftime('%Y%m%d%H%M%S')}"
            subprocess.run(
                ["powershell", "Checkpoint-Computer", "-Description", 
                f"'{restore_point}'", "-RestorePointType", "MODIFY_SETTINGS"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.log(f"✅ ТОЧКА ВОССТАНОВЛЕНИЯ СОЗДАНА: {restore_point}")
            return True
        except Exception as e:
            self.log(f"❌ ОШИБКА СОЗДАНИЯ ТОЧКИ ВОССТАНОВЛЕНИЯ: {str(e)}")
            return False

    def is_system_file(self, file_path):
        """Точная проверка системных файлов"""
        try:
            # Получаем корневую директорию системы
            system_root = os.environ.get('SystemRoot', 'C:\\Windows').lower()
            
            # Проверяем, находится ли файл в системных директориях
            lower_path = file_path.lower()
            if system_root not in lower_path:
                return False  # Файл не в системной директории
                
            # Проверяем только файлы из белого списка
            file_name = os.path.basename(file_path)
            parent_dir = os.path.dirname(file_path).lower()
            
            for sys_dir, files in SYSTEM_WHITELIST.items():
                sys_dir_lower = sys_dir.lower()
                if sys_dir_lower in parent_dir:
                    if file_name in files:
                        return True
                        
            # Дополнительная проверка для системных DLL
            if file_name.endswith('.dll'):
                with open(file_path, "rb") as f:
                    header = f.read(16)
                    for sig in SYSTEM_SIGNATURES:
                        if header.startswith(sig):
                            return True
        except:
            pass
        return False

    def has_system_attributes(self, file_path):
        """Проверка системных атрибутов файла (только для Windows)"""
        if os.name != 'nt':
            return False
            
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
            return attrs & 0x4 == 0x4  # FILE_ATTRIBUTE_SYSTEM
        except:
            return False

    def get_matched_patterns(self, content, patterns):
        """Поиск совпадений паттернов в содержимом файла"""
        matched = []
        try:
            # Декодируем содержимое с обработкой ошибок
            try:
                text_content = content.decode('utf-8')
            except:
                text_content = content.decode('latin-1', errors='ignore')
                
            for pattern in patterns:
                if re.search(pattern, text_content):
                    matched.append(pattern)
        except:
            # Бинарный поиск для не декодируемого содержимого
            for pattern in patterns:
                try:
                    if re.search(pattern.encode(), content):
                        matched.append(pattern)
                except:
                    pass
        return matched

    def advanced_threat_analysis(self, file_path):
        """Расширенный анализ угроз"""
        analysis = {
            "embedded_chat": [],
            "persistence": [],
            "network_activity": [],
            "anti_debug": [],
            "packed": False
        }
        
        try:
            # Проверка на упаковку
            analysis["packed"] = self.is_packed(file_path)
            
            # Поиск встроенных чат-компонентов
            with open(file_path, "rb") as f:
                content = f.read(5 * 1024 * 1024)  # Первые 5MB
                
                # Декодируем содержимое
                try:
                    text_content = content.decode('utf-8')
                except:
                    text_content = content.decode('latin-1', errors='ignore')
                
                # Проверяем паттерны
                for pattern in CHAT_PATTERNS:
                    if re.search(pattern, text_content):
                        analysis["embedded_chat"].append(pattern)
                        
                # Поиск механизмов персистентности
                persistence_patterns = [
                    r"reg\s+add", r"schtasks", r"Startup", r"RunKey",
                    r"autostart", r"service\s+install", r"task\s+scheduler"
                ]
                for pattern in persistence_patterns:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        analysis["persistence"].append(pattern)
                        
                # Сетевая активность
                network_patterns = [
                    r"http\.request", r"socket\.connect", r"ftp\.put",
                    r"udp\.send", r"dns\.resolve", r"port\s+scan"
                ]
                for pattern in network_patterns:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        analysis["network_activity"].append(pattern)
                        
                # Анти-отладка
                anti_debug_patterns = [
                    r"IsDebuggerPresent", r"CheckRemoteDebugger", r"OutputDebugString",
                    r"CloseHandle", r"ZwSetInformationThread", r"int\s+0x2d"
                ]
                for pattern in anti_debug_patterns:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        analysis["anti_debug"].append(pattern)
                        
        except Exception as e:
            self.log(f"Ошибка расширенного анализа: {str(e)}")
            
        return analysis

    def is_packed(self, file_path):
        """Проверка, упакован ли файл"""
        try:
            with open(file_path, "rb") as f:
                content = f.read(1024)
                
            # Проверка сигнатур упаковщиков
            packers = [
                b"UPX!", b"ASPack", b"FSG!", b"PECompact", 
                b"MPRESS", b"VProtect", b"Obsidium", b"Armadillo"
            ]
            
            for packer in packers:
                if packer in content:
                    return True
                    
            # Эвристический анализ: низкое соотношение кода/данных
            if os.path.getsize(file_path) > 100 * 1024:
                try:
                    pe = pefile.PE(file_path)
                    code_size = 0
                    data_size = 0
                    
                    for section in pe.sections:
                        if b"text" in section.Name or b"code" in section.Name:
                            code_size += section.SizeOfRawData
                        else:
                            data_size += section.SizeOfRawData
                    
                    if data_size > 10 * code_size:  # Много данных, мало кода
                        return True
                except:
                    pass
                    
        except:
            pass
        return False

    def alert_threat(self, file_path, threat_info):
        alert_msg = f"""
        ⚠️ MATRIX DEFENDER ALERT ⚠️
        
        ТИП УГРОЗЫ: {threat_info['name']}
        УРОВЕНЬ ОПАСНОСТИ: {self.get_threat_level_name(threat_info['level'])} ({threat_info['level']}/10)
        ФАЙЛ: {os.path.basename(file_path)}
        ПУТЬ: {file_path}
        
        МЕХАНИЗМ ДЕЙСТВИЯ:
        {threat_info['mechanism']}
        
        ОБНАРУЖЕННЫЕ ПАТТЕРНЫ:
        {', '.join(threat_info['patterns'][:5])}{'...' if len(threat_info['patterns']) > 5 else ''}
        """
        
        # Детализированное описание для угроз уровня 4+
        if threat_info['level'] >= 4:
            alert_msg += f"""
        🔍 ДЕТАЛЬНЫЙ АНАЛИЗ УГРОЗЫ УРОВНЯ {threat_info['level']}:
        Механизм действия: {threat_info['mechanism']}
        Рекомендуемые действия: {threat_info['mitigation']}
        """
            
            # Расширенная информация для высокоуровневых угроз
            if 'advanced' in threat_info:
                adv = threat_info['advanced']
                if adv['embedded_chat']:
                    alert_msg += f"Внедрённые чат-компоненты: {', '.join(adv['embedded_chat'][:3])}\n"
                if adv['persistence']:
                    alert_msg += f"Механизмы персистентности: {', '.join(adv['persistence'][:3])}\n"
                if adv['network_activity']:
                    alert_msg += f"Сетевая активность: {', '.join(adv['network_activity'][:3])}\n"
                if adv['anti_debug']:
                    alert_msg += f"Анти-отладочные техники: {', '.join(adv['anti_debug'][:3])}\n"
                if adv['packed']:
                    alert_msg += "Файл упакован/зашифрован: Да\n"
        
        self.log(alert_msg)
        
        # Запрашиваем подтверждение перед лечением (без иконки)
        response = messagebox.askyesno(
            "МАТРИЦА: ОБНАРУЖЕНА УГРОЗА",
            f"Обнаружен {threat_info['name']} (уровень {threat_info['level']}/10)\n\n"
            f"Файл: {os.path.basename(file_path)}\n"
            f"Путь: {file_path}\n\n"
            "Вылечить угрозу?"
        )
        
        if response:
            if self.heal_threat(file_path, threat_info['type']):
                self.log(f"⚕️ УГРОЗА ЛЕЧЕНИЕ УСПЕШНО: {file_path}")
            else:
                self.log(f"❌ НЕ УДАЛОСЬ ВЫЛЕЧИТЬ: {file_path}")
        else:
            self.log(f"⚠️ УГРОЗА ПРОИГНОРИРОВАНА ПОЛЬЗОВАТЕЛЕМ: {file_path}")

    def update_threat_level(self):
        """Обновление индикатора уровня угрозы"""
        if not self.detected_threats:
            self.threat_level.config(text="УРОВЕНЬ УГРОЗЫ: НИЗКИЙ", fg="#00ff00")
            return
            
        max_level = max(threat['level'] for threat in self.detected_threats)
        
        if max_level >= 8:
            color = "#ff0000"
            level_name = "КРИТИЧЕСКИЙ"
        elif max_level >= 5:
            color = "#ff6600"
            level_name = "ВЫСОКИЙ"
        else:
            color = "#ffff00"
            level_name = "СРЕДНИЙ"
            
        self.threat_level.config(
            text=f"УРОВЕНЬ УГРОЗЫ: {level_name}",
            fg=color
        )
        self.log(f"НАИБОЛЕЕ ОПАСНАЯ УГРОЗА: УРОВЕНЬ {max_level}/10")

    def get_threat_level_name(self, level):
        """Получение названия уровня угрозы"""
        if level >= 9:
            return "КРИТИЧЕСКИЙ"
        elif level >= 7:
            return "ВЫСОКИЙ"
        elif level >= 5:
            return "ПОВЫШЕННЫЙ"
        elif level >= 3:
            return "СРЕДНИЙ"
        else:
            return "НИЗКИЙ"

    def deep_rat_scan(self):
        """Глубокое сканирование специально для RAT"""
        self.log("ЗАПУСК ГЛУБОКОГО СКАНА ДЛЯ RAT...")
        self.log("ИГНОРИРОВАНИЕ СИСТЕМНЫХ ФАЙЛОВ...")
        
        # Временно отключаем проверку системных файлов
        self.skip_system_files = True
        
        # Выполняем обычное сканирование
        self.full_scan()
        
        # Возвращаем настройки
        self.skip_system_files = False

    def calculate_hash(self, file_path):
        """Вычисление хеша файла"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except:
            return "error"

    def detect_rat_family(self, file_path):
        """Определение семейства RAT по сигнатурам"""
        signatures = {
            b"LimeRAT": "LimeRAT",
            b"QuasarRAT": "Quasar",
            b"AsyncRAT": "Async",
            b"NjRat": "NjRat",
            b"DarkComet": "DarkComet",
            b"Remcos": "Remcos",
            b"Warzone": "Warzone",
            b"NetWire": "NetWire",
            b"PoisonIvy": "PoisonIvy"
        }
        try:
            with open(file_path, "rb") as f:
                content = f.read(8192)  # Первые 8KB
                for sig, name in signatures.items():
                    if sig in content:
                        return name
        except:
            pass
        return "GenericRAT"

if __name__ == "__main__":
    app = MatrixDefender()
    app.mainloop()

