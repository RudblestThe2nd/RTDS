"""
main.py
=======
Giriş noktası — orchestrator.

Sorumluluklar:
  - Bağımlılıkları oluşturmak (Detector, Tracker, Logger, Pipeline)
  - Video / kamera döngüsünü yönetmek
  - ESC ile temiz çıkış sağlamak

Hiçbir tespit mantığı, çizim veya log detayı içermez.
"""

import cv2
import time
import sys

from src import config as cfg
from src.detector   import Detector
from src.tracker    import ArmedHistoryTracker
from src.logger     import ThreatLogger
from src.pipeline   import FramePipeline
from src.visualizer import draw_hud


def _is_image(path) -> bool:
    return isinstance(path, str) and path.lower().endswith(
        (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    )


def _open_window():
    cv2.namedWindow(cfg.WINDOW_NAME, cv2.WINDOW_NORMAL)
    if cfg.FULLSCREEN_MODE:
        cv2.setWindowProperty(cfg.WINDOW_NAME,
                              cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN)
    else:
        cv2.resizeWindow(cfg.WINDOW_NAME, cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT)


# ── Resim modu ────────────────────────────────────────────────────
def run_image(source, detector, logger):
    frame = cv2.imread(source)
    if frame is None:
        raise RuntimeError(f"Resim okunamadı: {source}")
    logger.write("Resim modu — tracking devre dışı")
    detector.predict(frame)   # sadece predict, tracking yok
    _open_window()
    cv2.imshow(cfg.WINDOW_NAME, frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ── Video / Kamera modu ───────────────────────────────────────────
def run_video(source, pipeline, logger, tracker):
    # SOURCE int ise (kamera index) doğrudan int gönder
    cap_src = int(source) if str(source).isdigit() else source
    cap = cv2.VideoCapture(cap_src)
    if not cap.isOpened():
        raise RuntimeError(f"Kaynak açılamadı: {source}")

    fps_src      = cap.get(cv2.CAP_PROP_FPS)
    if fps_src <= 0 or fps_src > 120:
        fps_src = 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    logger.write(f"Video: {width}x{height} @ {fps_src:.1f}fps | Toplam frame: {total_frames}\n")

    writer = None
    if cfg.SAVE_OUTPUT:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(cfg.OUTPUT_VIDEO, fourcc, fps_src, (width, height))

    _open_window()

    prev_time = time.time()
    show_fps  = 0.0
    frame_no  = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Akış bitti veya kaynak koptu.")
            break

        frame_no += 1

        # ── Ana pipeline ──
        pipeline.run(frame, frame_no, cap)

        # ── FPS hesabı ──
        now = time.time()
        dt  = now - prev_time
        prev_time = now
        if dt > 0:
            cur_fps  = 1.0 / dt
            show_fps = cur_fps if show_fps == 0 else (0.9 * show_fps + 0.1 * cur_fps)

        # ── HUD çiz ──
        draw_hud(frame, frame_no, total_frames, show_fps, tracker.count())

        cv2.imshow(cfg.WINDOW_NAME, frame)

        if writer is not None:
            writer.write(frame)

        if cv2.waitKey(1) & 0xFF == 27:   # ESC
            break

    cap.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()

    return frame_no


# ── Giriş Noktası ─────────────────────────────────────────────────
def main():
    # Bağımlılıkları oluştur
    logger   = ThreatLogger()
    detector = Detector()
    tracker  = ArmedHistoryTracker()
    pipeline = FramePipeline(detector, tracker, logger)

    # Oturum başlığı
    logger.header(cfg.SOURCE, cfg.MODEL_PATH, cfg.TRACKER)

    try:
        if _is_image(cfg.SOURCE):
            run_image(cfg.SOURCE, detector, logger)
            frame_no = 1
        else:
            frame_no = run_video(cfg.SOURCE, pipeline, logger, tracker)
    except Exception as e:
        logger.write(f"\n[HATA] {e}")
        raise
    finally:
        logger.close(frame_no, tracker.armed_ids)


if __name__ == "__main__":
    main()
