import os
import pytesseract
import time
import mss
import numpy as np
import cv2

from obswebsocket import obsws, requests
from dotenv import load_dotenv

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from threading import Thread, Lock

load_dotenv()

obs_url = os.getenv("OBS_URL")
obs_port = int(os.getenv("OBS_PORT"))
obs_password = os.getenv("OBS_PASSWORD")

text_year = os.getenv("TEXT_YEAR")
monitor_index = int(os.getenv("SCT_MONITOR_INDEX"))

time_sleep = float(os.getenv("TIME_SLEEP_VERIFICATION"))

scene_camera = os.getenv("SCENE_CAMERA")
scene_monitor = os.getenv("SCENE_MONITOR")

path_to_watch = os.path.join(
    os.path.expanduser("~"),
    "Videos",
    "JWLibrary",
    ".SecondDisplay"
)

video_active = False
video_just_ended = False
ocr_state = None

lock = Lock()


# =========================
# OBS
# =========================
def connect_obs():
    while True:
        try:
            ws = obsws(obs_url, obs_port, obs_password)
            ws.connect()
            print("✅ Conectado ao OBS WebSocket")
            return ws
        except:
            print("❌ Falha ao conectar no OBS. Tentando novamente em 3s...")
            time.sleep(3)


# =========================
# WATCHDOG
# =========================
class JWHandler(FileSystemEventHandler):
    def on_created(self, event):
        global video_active
        if not event.is_directory and "_true" in os.path.basename(event.src_path):
            with lock:
                video_active = True
            print("📂 _true detectado")

    def on_deleted(self, event):
        global video_active, video_just_ended
        if not event.is_directory and "_true" in os.path.basename(event.src_path):
            with lock:
                video_active = False
                video_just_ended = True
            print("📂 _true removido")


def start_watchdog():
    global video_active

    if os.path.exists(path_to_watch):
        if any("_true" in f for f in os.listdir(path_to_watch)):
            video_active = True

        observer = Observer()
        observer.schedule(JWHandler(), path=path_to_watch, recursive=False)
        observer.start()
        print("👀 Monitorando pasta JWLibrary...")
    else:
        print("⚠️ Pasta não encontrada:", path_to_watch)


# =========================
# OCR INTELIGENTE
# =========================
def extract_text_region(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img

    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    pad = 150
    x = max(0, x - pad)
    y = max(0, y - pad)
    w = min(img.shape[1] - x, w + pad * 2)
    h = min(img.shape[0] - y, h + pad * 2)

    return img[y:y+h, x:x+w]


def detect_text_fast(sct, monitor):
    screenshot = sct.grab(monitor)
    img = np.array(screenshot)

    img = cv2.resize(img, None, fx=0.75, fy=0.75)

    region = extract_text_region(img)

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray, None, fx=2.0, fy=2.0)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(thresh, config="--psm 6")

    if text_year in text:
        return '1'
    else:
        return '2'


# =========================
# FUNÇÃO PARA GARANTIR MONITOR
# =========================
def get_monitor_safe(index):
    with mss.mss() as sct:
        while True:
            monitors = sct.monitors
            if len(monitors) > index:
                return monitors[index]
            else:
                print(f"⚠️ Monitor {index} não detectado ainda. Esperando 2s...")
                time.sleep(2)


# =========================
# OCR LOOP
# =========================
def run_ocr():
    global ocr_state

    with mss.mss() as sct:
        monitor2 = get_monitor_safe(monitor_index)
        last_detected = None

        while True:
            try:
                with lock:
                    is_video = video_active

                if is_video:
                    last_detected = None
                    time.sleep(0.5)
                    continue

                detected = detect_text_fast(sct, monitor2)

                if detected != last_detected:
                    with lock:
                        ocr_state = detected
                    last_detected = detected
                else:
                    with lock:
                        ocr_state = detected

                time.sleep(time_sleep)

            except Exception as e:
                print(f"⚠️ OCR erro: {e}")
                time.sleep(1)


# =========================
# MAIN LOOP
# =========================
def main_loop(ws):
    global video_just_ended

    last_state = None
    last_switch_time = 0
    min_switch_interval = 1.0

    while True:
        try:
            # --- Verifica conexão do OBS ---
            try:
                ws.call(requests.GetVersion())  # ping simples
            except:
                print("⚠️ Conexão com OBS perdida! Reconectando...")
                ws = connect_obs()

            with lock:
                is_video = video_active
                just_ended = video_just_ended
                current_ocr = ocr_state

                if video_just_ended:
                    video_just_ended = False

            if is_video:
                current_state = '2'
            elif current_ocr is not None:
                current_state = current_ocr
            else:
                time.sleep(0.05)
                continue

            now = time.time()

            if just_ended:
                last_switch_time = 0

            if (
                current_state != last_state and
                (now - last_switch_time) > min_switch_interval
            ):
                if current_state == '1':
                    ws.call(requests.SetCurrentProgramScene(sceneName=scene_camera))
                    print("🎥 Cena: CAMERA")
                else:
                    ws.call(requests.SetCurrentProgramScene(sceneName=scene_monitor))
                    print("🖥️ Cena: MONITOR")

                last_state = current_state
                last_switch_time = now

            time.sleep(0.05)

        except Exception as e:
            print(f"⚠️ Loop erro: {e}")
            time.sleep(1)


# =========================
# MAIN
# =========================
def main():
    ws = connect_obs()

    Thread(target=start_watchdog, daemon=True).start()
    Thread(target=run_ocr, daemon=True).start()

    main_loop(ws)


if __name__ == "__main__":
    main()