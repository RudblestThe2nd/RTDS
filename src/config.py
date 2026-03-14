"""
src/config.py
=============
Tüm sabitler, path'ler ve eşik değerleri tek yerden yönetilir.
Hiçbir modül doğrudan sabit içermez — hepsi buradan okur.
"""

import cv2

# ── Model ──────────────────────────────────────────────────────────
MODEL_PATH = "/home/berkay/Desktop/fine_tune_runs/merged_ft_15ep_safe2/weights/best.pt"

# ── Kaynak ─────────────────────────────────────────────────────────
# mp4/avi/mkv yolu, resim yolu veya kamera index (0, 1, 2 ...)
SOURCE = "/home/berkay/Downloads/vid2.mp4"

# ── Tespit ─────────────────────────────────────────────────────────
CONF_THRESHOLD = 0.20
TRACKER        = "bytetrack.yaml"   # "botsort.yaml" da kullanılabilir
EXPAND_SCALE   = 1.35

# ── Tehdit Puanlama ────────────────────────────────────────────────
MASK_SCORE    = 10
MELEE_SCORE   = 25
HANDGUN_SCORE = 40
RIFLE_SCORE   = 50

# ── Pencere ────────────────────────────────────────────────────────
WINDOW_NAME           = "Threat Detection"
WINDOW_WIDTH          = 1366
WINDOW_HEIGHT         = 1024
FULLSCREEN_MODE       = False
SHOW_ONLY_INTERESTING = True

# ── Video Çıktısı ──────────────────────────────────────────────────
SAVE_OUTPUT  = False
OUTPUT_VIDEO = "output.mp4"

# ── Log ────────────────────────────────────────────────────────────
LOG_DIR         = "logs"
LOG_EVERY_FRAME = False   # Her frame'i logla (verbose mod)
LOG_MIN_SCORE   = 0

# ── Screenshot ─────────────────────────────────────────────────────
SCREENSHOT_DIR       = "screenshots"
SCREENSHOT_MIN_SCORE = 10
SCREENSHOT_COOLDOWN  = 2.0   # saniye — ARMED_HISTORY_NEW'de bypass edilir

# ── Görsel / Font ──────────────────────────────────────────────────
FONT              = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_LABEL  = 0.45
FONT_SCALE_DETAIL = 0.35
FONT_SCALE_FPS    = 0.5
FONT_THICK        = 1

COLOR_NORMAL  = (255, 255, 255)   # beyaz  — silahsız kişi
COLOR_ARMED   = (0,   0,   255)   # kırmızı — aktif silah tespiti
COLOR_HISTORY = (0,   0,   200)   # koyu kırmızı — geçmişte silah görüldü
