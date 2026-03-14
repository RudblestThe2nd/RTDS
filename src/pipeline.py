"""
src/pipeline.py
===============
FramePipeline — her video frame'inde çalışan ana orkestratör.

main.py döngüsü sadece şunu yapar:
    ok, frame = cap.read()
    frame = pipeline.run(frame, frame_no, cap)

İçeride sırayla:
  1. Detector   → YOLO track() → tespitler
  2. Scorer     → her kişi için tehdit skoru
  3. Tracker    → armed history güncelleme
  4. Logger     → log satırları + screenshot
  5. Visualizer → frame üzerine çizim
"""

import cv2
from src import config as cfg
from src.detector   import Detector
from src.scorer     import score_person
from src.tracker    import ArmedHistoryTracker
from src.visualizer import draw_person, draw_hud
from src.logger     import ThreatLogger


def _frame_timestamp(cap):
    ms      = cap.get(cv2.CAP_PROP_POS_MSEC) if cap else 0
    total_s = int(ms / 1000)
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


class FramePipeline:
    """
    Bağımlılıkları dışarıdan alır (dependency injection).
    Her modülü bağımsız test etmek mümkündür.
    """

    def __init__(self,
                 detector: Detector,
                 tracker:  ArmedHistoryTracker,
                 logger:   ThreatLogger):
        self.detector = detector
        self.tracker  = tracker
        self.logger   = logger

    # ──────────────────────────────────────────────────────────────
    def run(self, frame, frame_no: int, cap=None) -> list[dict]:
        """
        Tek frame'i işler, frame üzerine çizim yapar.

        Returns
        -------
        list[dict] — person_result listesi (main.py istatistik için kullanabilir)
        """
        ts = _frame_timestamp(cap)

        # ── 1. Tracker frame başlangıcı ──
        self.tracker.begin_frame()

        # ── 2. Tespit ──
        detections = self.detector.track(frame)

        # ── 3. Log — tüm tespitler ──
        self.logger.log_detections(ts, frame_no, detections["all"])

        # ── 4. Her kişi için ──
        person_results = []

        for person in detections["humans"]:
            tid  = person["track_id"]
            bbox = person["bbox"]

            # Skorlama
            result = score_person(bbox, detections, frame_shape=frame.shape)

            # Armed History güncelleme
            if result["has_weapon_now"] and tid != -1:
                if not self.tracker.is_armed(tid):
                    self.logger.log_newly_armed(tid, result["tags"], result["score"])
                self.tracker.register(tid)

            in_history  = self.tracker.is_armed(tid)
            newly_armed = self.tracker.is_newly_armed(tid)

            px1, py1, px2, py2 = bbox
            person_result = {
                "tid":           tid,
                "score":         result["score"],
                "tags":          result["tags"],
                "bbox":          bbox,
                "has_weapon_now": result["has_weapon_now"],
                "in_history":    in_history,
                "newly_armed":   newly_armed,
                "frame_no":      frame_no,
            }
            person_results.append(person_result)

            # Log — kişi detayı
            if result["score"] >= cfg.LOG_MIN_SCORE or in_history:
                self.logger.log_person(person_result)

            # Filtre — SHOW_ONLY_INTERESTING
            if cfg.SHOW_ONLY_INTERESTING and result["score"] == 0 and not in_history:
                continue

            # ── 5. Çizim ──
            draw_person(frame, person_result)

            # ── 6. Screenshot ──
            self.logger.take_screenshot(frame, person_result, ts)

        if detections["all"] or cfg.LOG_EVERY_FRAME:
            self.logger.blank()

        return person_results
