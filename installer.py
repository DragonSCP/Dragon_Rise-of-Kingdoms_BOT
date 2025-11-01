#!/usr/bin/env python3
# installer.py
# Instalador para Windows: cria estrutura do Dragon Bot, venv, instala deps, cria atalhos.

import os
import sys
import shutil
import subprocess
import getpass
import time
import textwrap

# -------------------------
# Configuração padrão
# -------------------------
DEFAULT_INSTALL_DIR = r"C:\Program Files\Dragon_Rise-of-Kingdoms_BOT"
PROGRAM_NAME = "Dragon Bot - Rise of Kingdoms"
MAIN_SCRIPT = "main_gui.py"
REQUIREMENTS = """streamlit==1.38.0
ultralytics==8.3.0
opencv-python==4.10.0
mss==9.0.1
pyautogui==0.9.54
pytesseract==0.3.10
pywin32==306
pyyaml==6.0.2
numpy==2.1.0
scipy==1.14.1
pillow==10.4.0
"""

# -------------------------
# Utilitários
# -------------------------
def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run(cmd, check=True, shell=False):
    if isinstance(cmd, (list,tuple)):
        print("EXEC >", " ".join(cmd))
    else:
        print("EXEC >", cmd)
    return subprocess.run(cmd, check=check, shell=shell)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    print("Created dir:", path)

def write_file(path, content, mode="w"):
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)
    print("Wrote file:", path)

# Fallback para criar atalho se win32com não estiver disponível
def create_shortcut(target, args, shortcut_path, icon=None):
    """
    Tenta criar .lnk com win32com. Se não disponível, cria um .bat como fallback.
    """
    try:
        import pythoncom
        from win32com.shell import shell, shellcon
        from win32com.client import Dispatch
    except Exception:
        # fallback: criar BAT que executa o target
        bat_path = os.path.splitext(shortcut_path)[0] + ".bat"
        bat_content = f'@echo off\r\n"{target}" {args if args else ""}\r\npause\r\n'
        write_file(bat_path, bat_content)
        print("Fallback: criado arquivo BAT em vez de .lnk:", bat_path)
        return bat_path

    Shell = Dispatch('WScript.Shell')
    lnk = Shell.CreateShortCut(shortcut_path)
    lnk.Targetpath = target
    lnk.Arguments = args or ""
    if icon:
        lnk.IconLocation = icon
    lnk.WorkingDirectory = os.path.dirname(target)
    lnk.save()
    print("Criado atalho .lnk:", shortcut_path)
    return shortcut_path

# -------------------------
# Conteúdo do projeto (templates)
# -------------------------
# Aqui eu incluo os arquivos principais (conteúdo simplificado, preserve conforme precisa)
README_MD = """# Dragon Bot - Rise of Kingdoms (2025 Full Auto)

Bot PC-native para RoK v1.0.91. Automatiza: login, collect, upgrade, train, farm barbs.
"""

LICENSE = "MIT License\n\nCopyright (c) 2025 DragonSCP\n"

CONFIG_YAML = """game:
  launcher_path: 'C:\\\\Program Files\\\\BlueStacks_nxt\\\\Bluestacks.exe'
  working_dir: 'C:\\\\Program Files\\\\BlueStacks_nxt'
  window_title_contains: 'Rise of Kingdoms'
tasks:
  collect_resources: true
  upgrade_buildings: true
  train_troops: true
  farm_barbarians: true
human_behavior:
  click_variance: 10
  min_delay: 0.8
  max_delay: 2.5
  error_chance: 0.05
paths:
  model: 'models/rok_2025_yolov8.pt'
  logs: 'logs/bot.log'
"""

ACCOUNTS_YAML = "accounts:\n  - email: exemplo@gmail.com\n    password: senha\n    kingdom: 1234\n"

INSTALL_BAT = r"""@echo off
echo Instalando Dragon Bot...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Pronto! Rode main_gui.py
pause
"""

GITIGNORE = "__pycache__/\n*.pyc\nlogs/\nscreenshots/\nvenv/\n.env\n"

MODEL_README = "Baixe YOLO: https://drive.google.com/file/d/exemplo/view (24MB)\n"

# Para main_gui e src, usarei versões compactas (mantenha/edite conforme seu repo original)
MAIN_GUI_PY = textwrap.dedent(r'''
import tkinter as tk
import yaml, threading, time, random
from src.window import *
from src.game import RoKGame
from src.farm import BarbarianFarmer
from src.anti_ban import AntiBan

class DragonBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dragon Bot - Rise of Kingdoms 2025")
        self.root.geometry("600x500")
        self.running = False
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="DRAGON BOT\nRise of Kingdoms 2025", font=("Arial", 16, "bold"), fg="#D4AF37").pack(pady=10)
        self.tasks = {k: tk.BooleanVar(value=True) for k in ["Collect", "Upgrade", "Train", "Farm"]}
        for t, v in self.tasks.items():
            tk.Checkbutton(self.root, text=t, variable=v).pack(anchor=tk.W, padx=40)
        btn = tk.Frame(self.root); btn.pack(pady=20)
        tk.Button(btn, text="Iniciar Bot", command=self.start, bg="#228B22", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(btn, text="Parar", command=self.stop, bg="#8B0000", fg="white").pack(side=tk.LEFT, padx=10)
        self.log = tk.Text(self.root, height=10, state=tk.DISABLED)
        self.log.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    def log_msg(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{time.strftime('%H:%M')}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def start(self):
        if self.running: return
        self.running = True
        threading.Thread(target=self.run_bot, daemon=True).start()

    def run_bot(self):
        self.log_msg("Iniciando...")
        try:
            config = yaml.safe_load(open('config.yaml'))
            accounts = yaml.safe_load(open('accounts.yaml'))['accounts']
        except Exception as e:
            self.log_msg("Erro lendo config/accounts: " + str(e))
            return
        for acc in accounts:
            if not self.running: break
            start_rok_game(config['game']['launcher_path'], config['game']['working_dir'])
            time.sleep(15)
            hwnd, _ = find_rok_window()
            if hwnd: focus_window(hwnd)
            game = RoKGame(config)
            game.login(acc['email'], acc['password'])
            anti_ban = AntiBan(config['paths']['logs'])
            farmer = BarbarianFarmer(config)
            for _ in range(100):
                if not self.running: break
                anti_ban.human_pause()
                if self.tasks['Collect'].get(): game.collect_all()
                if self.tasks['Upgrade'].get(): game.upgrade_if_possible()
                if self.tasks['Farm'].get():
                    barb = farmer.find_nearest_barb()
                    if barb: farmer.attack(barb)
                time.sleep(random.uniform(180, 300))
        self.log_msg("Concluído.")

    def stop(self):
        self.running = False
        self.log_msg("Parando...")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    DragonBotGUI().run()
''')

SRC_WINDOW = textwrap.dedent(r'''
import win32gui, win32con, subprocess, time

def find_rok_window(t="Rise of Kingdoms"):
    def enum(hwnd, res):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if t in title and "launcher" not in title.lower():
                res.append((hwnd, title))
    w = []
    win32gui.EnumWindows(enum, w)
    return w[0] if w else (None, None)

def focus_window(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)

def start_rok_game(exe, wd):
    try:
        subprocess.Popen([exe], cwd=wd)
    except Exception as e:
        print("Erro ao iniciar executável:", e)
''')

SRC_CAPTURE = textwrap.dedent(r'''
import mss, numpy as np, cv2

class ScreenCapture:
    def __init__(self): self.sct = mss.mss()
    def capture(self):
        img = self.sct.grab(self.sct.monitors[1])
        return cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
''')

SRC_DETECTOR = textwrap.dedent(r'''
from ultralytics import YOLO
import pytesseract, cv2, os, numpy as np

class RoKDetector:
    def __init__(self, path):
        self.use_yolo = os.path.exists(path)
        if self.use_yolo:
            try:
                self.model = YOLO(path)
            except Exception as e:
                print("Falha ao carregar modelo YOLO:", e)
                self.use_yolo = False
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

    def detect_resources(self, frame):
        if self.use_yolo:
            res = self.model(frame, conf=0.3)[0]
            out = []
            for box in res.boxes:
                label = res.names[int(box.cls[0])]
                if label in ['farm','lumber','stone','gold','collect_button']:
                    x1,y1,x2,y2 = map(int, box.xyxy[0])
                    out.append({'center': ((x1+x2)//2, (y1+y2)//2)})
            return out
        else:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, (20,100,100), (30,255,255))
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rects = [cv2.boundingRect(c) for c in cnts]
            out = []
            for (x,y,w,h), c in zip(rects, cnts):
                area = cv2.contourArea(c)
                if 500 < area < 10000:
                    out.append({'center': (x+w//2, y+h//2)})
            return out

    def detect_enemies(self, frame):
        return self.detect_resources(frame)

    def read_text(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return pytesseract.image_to_string(gray)
''')

SRC_ACTIONS = textwrap.dedent(r'''
import pyautogui, random, time, numpy as np

pyautogui.PAUSE = 0.01

class GameActions:
    def __init__(self, cfg): self.cfg = cfg['human_behavior']
    def click(self, x, y):
        if random.random() < self.cfg.get('error_chance', 0.05):
            x += random.randint(-40,40); y += random.randint(-40,40)
        x += random.randint(-self.cfg.get('click_variance', 10), self.cfg.get('click_variance',10))
        y += random.randint(-self.cfg.get('click_variance', 10), self.cfg.get('click_variance',10))
        pyautogui.click(x, y)
        time.sleep(random.uniform(self.cfg.get('min_delay',0.5), self.cfg.get('max_delay',1.5)))
    def bezier_swipe(self, start, end):
        self.click(*end)
''')

SRC_GAME = textwrap.dedent(r'''
import pyautogui, time
from src.capture import ScreenCapture
from src.detector import RoKDetector
from src.actions import GameActions

class RoKGame:
    def __init__(self, cfg):
        self.cap = ScreenCapture()
        self.det = RoKDetector(cfg['paths']['model'])
        self.act = GameActions(cfg)
    def login(self, e, p):
        try:
            screen = self.cap.capture()
            if "email" in self.det.read_text(screen).lower():
                self.act.click(600,400); pyautogui.write(e); time.sleep(0.5)
                self.act.click(600,500); pyautogui.write(p); time.sleep(0.5)
                self.act.click(800,700); time.sleep(15)
        except Exception as ex:
            print("Login falhou:", ex)
    def collect_all(self):
        for r in self.det.detect_resources(self.cap.capture()):
            self.act.click(*r['center']); time.sleep(1)
    def upgrade_if_possible(self):
        if 'upgrade' in self.det.read_text(self.cap.capture()).lower():
            self.act.click(960,540)
''')

SRC_FARM = textwrap.dedent(r'''
import numpy as np, time
from scipy.spatial.distance import euclidean
from src.capture import ScreenCapture
from src.detector import RoKDetector
from src.actions import GameActions

class BarbarianFarmer:
    def __init__(self, cfg):
        self.cap = ScreenCapture()
        self.det = RoKDetector(cfg['paths']['model'])
        self.act = GameActions(cfg)
    def find_nearest_barb(self):
        barbs = self.det.detect_enemies(self.cap.capture())
        if not barbs: return None
        dists = [euclidean((960,540), b['center']) for b in barbs]
        return barbs[int(np.argmin(dists))]
    def attack(self, barb):
        self.act.bezier_swipe((960,540), barb['center'])
        time.sleep(3); self.act.click(1200,800)
''')

SRC_ANTI_BAN = textwrap.dedent(r'''
import random, time, datetime, logging

class AntiBan:
    def __init__(self, log): logging.basicConfig(filename=log, level=logging.INFO)
    def human_pause(self):
        r = random.random()
        if r < 0.1: time.sleep(random.uniform(30,120))
        elif r < 0.3: time.sleep(random.uniform(5,15))
    def daily_cycle(self):
        h = datetime.datetime.now().hour
        if h in [2,3,4,5] and random.random() < 0.7:
            time.sleep(random.uniform(1800,3600))
''')

# -------------------------
# Função principal do instalador
# -------------------------
def main():
    print("=== Dragon Bot Installer ===\n")
    if not is_admin():
        print("Esse instalador pede privilégios de administrador.")
        print("Reexecute como administrador (botão direito -> Run as administrator).")
        # allow user to continue, but warn
        cont = input("Deseja continuar mesmo sem admin? (pode não conseguir criar atalhos/Program Files) [y/N]: ").strip().lower()
        if cont != "y":
            return

    # Pergunta caminho de instalação
    install_dir = input(f"Caminho de instalação [{DEFAULT_INSTALL_DIR}]: ").strip()
    if not install_dir:
        install_dir = DEFAULT_INSTALL_DIR
    install_dir = os.path.abspath(install_dir)

    if os.path.exists(install_dir):
        ans = input(f"{install_dir} já existe. Remover e recriar? [y/N]: ").strip().lower()
        if ans == "y":
            try:
                shutil.rmtree(install_dir)
            except Exception as e:
                print("Erro removendo pasta existente:", e)
                return

    # Cria estrutura
    ensure_dir(install_dir)
    for sub in ("src", "models", "logs", "screenshots"):
        ensure_dir(os.path.join(install_dir, sub))

    # Escreve arquivos principais
    write_file(os.path.join(install_dir, "README.md"), README_MD)
    write_file(os.path.join(install_dir, "LICENSE"), LICENSE)
    write_file(os.path.join(install_dir, "requirements.txt"), REQUIREMENTS)
    write_file(os.path.join(install_dir, "config.yaml"), CONFIG_YAML)
    write_file(os.path.join(install_dir, "accounts.yaml"), ACCOUNTS_YAML)
    write_file(os.path.join(install_dir, "install.bat"), INSTALL_BAT)
    write_file(os.path.join(install_dir, "models\\README_model.txt"), MODEL_README)
    write_file(os.path.join(install_dir, ".gitignore"), GITIGNORE)
    write_file(os.path.join(install_dir, MAIN_SCRIPT), MAIN_GUI_PY)

    # src files
    src_dir = os.path.join(install_dir, "src")
    write_file(os.path.join(src_dir, "__init__.py"), "")
    write_file(os.path.join(src_dir, "window.py"), SRC_WINDOW)
    write_file(os.path.join(src_dir, "capture.py"), SRC_CAPTURE)
    write_file(os.path.join(src_dir, "detector.py"), SRC_DETECTOR)
    write_file(os.path.join(src_dir, "actions.py"), SRC_ACTIONS)
    write_file(os.path.join(src_dir, "game.py"), SRC_GAME)
    write_file(os.path.join(src_dir, "farm.py"), SRC_FARM)
    write_file(os.path.join(src_dir, "anti_ban.py"), SRC_ANTI_BAN)

    print("\nArquivos criados em:", install_dir)

    # Criar virtualenv e instalar dependências?
    make_venv = input("Criar venv e instalar requirements? [Y/n]: ").strip().lower()
    if make_venv != "n":
        try:
            venv_path = os.path.join(install_dir, "venv")
            print("Criando venv em", venv_path)
            run([sys.executable, "-m", "venv", venv_path])
            pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
            print("Instalando packages (pode demorar)...")
            run([pip_exe, "install", "-r", os.path.join(install_dir, "requirements.txt")])
            print("Dependências instaladas.")
        except Exception as e:
            print("Erro ao criar venv / instalar deps:", e)

    # Criar atalho na Área de Trabalho e Menu Iniciar
    desktop = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")
    start_menu = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", PROGRAM_NAME)
    ensure_dir(start_menu)
    target = os.path.join(install_dir, sys.executable) if "venv" not in install_dir else os.path.join(install_dir, "venv", "Scripts", "python.exe")
    # preferir usar o python do venv se existir
    if os.path.exists(os.path.join(install_dir, "venv", "Scripts", "python.exe")):
        target = os.path.join(install_dir, "venv", "Scripts", "python.exe")
    # atalho que executa "python main_gui.py" no install_dir
    args = f'"{os.path.join(install_dir, MAIN_SCRIPT)}"'
    desktop_shortcut = os.path.join(desktop, f"{PROGRAM_NAME}.lnk")
    start_shortcut = os.path.join(start_menu, f"{PROGRAM_NAME}.lnk")
    create_shortcut(target, args, desktop_shortcut)
    create_shortcut(target, args, start_shortcut)

    # criar uninstall script
    uninstall_path = os.path.join(install_dir, "uninstall.bat")
    uninstall_content = f"""@echo off
taskkill /im {os.path.basename(sys.executable)} /f 2>nul
rmdir /s /q "{install_dir}"
echo Desinstalado {PROGRAM_NAME}
pause
"""
    write_file(uninstall_path, uninstall_content)

    print("\nInstalação concluída.\nAtalho na Área de Trabalho e Menu Iniciar criados.")
    launch = input("Deseja abrir o programa agora? [y/N]: ").strip().lower()
    if launch == "y":
        try:
            # abre com o python do venv se existir
            python_to_run = target
            run([python_to_run, os.path.join(install_dir, MAIN_SCRIPT)])
        except Exception as e:
            print("Erro ao abrir o programa:", e)

if __name__ == "__main__":
    main()
