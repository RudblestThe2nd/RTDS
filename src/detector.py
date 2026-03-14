"""
src/detector.py
===============
YOLOv8 modelini saran Detector sınıfı.
- Model yükleme
- track() / predict() çağrısı
- Ham YOLO sonuçlarını kategorize edilmiş sözlüklere dönüştürme
- Label normalization (gun/pistol → handgun, knife → melee, vb.)
"""

from ultralytics import YOLO
from src import config as cfg


# Desteklenen label → standart isim eşlemesi
_LABEL_MAP = {
    # İnsan
    "human":         "human",
    "person":        "human",
    # Maske
    "mask":          "mask",
    # Tabanca
    "handgun":       "handgun",
    "gun":           "handgun",
    "pistol":        "handgun",
    # Melee
    "melee":         "melee",
    "knife":         "melee",
    "blade":         "melee",
    # Tüfek
    "rifle":         "rifle",
    "long_gun":      "rifle",
    "assault_rifle": "rifle",
}


class Detector:
    """YOLOv8 modelini yükler ve frame üzerinde tespit + tracking yapar."""

    def __init__(self):
        self.model = YOLO(cfg.MODEL_PATH)
        self.names = self.model.names

    # ──────────────────────────────────────────────────────────────
    def track(self, frame):
        """
        YOLO track() çağrısı yapar, sonuçları kategorize eder.

        Returns
        -------
        dict:
            {
              "humans":   [...],
              "masks":    [...],
              "handguns": [...],
              "melees":   [...],
              "rifles":   [...],
              "all":      [...],   # tüm tespitler (log için)
            }
        Her eleman: {"label", "std_label", "conf", "bbox", "track_id"}
        """
        results = self.model.track(
            source=frame,
            conf=cfg.CONF_THRESHOLD,
            persist=True,
            tracker=cfg.TRACKER,
            save=False,
            verbose=False,
        )
        return self._parse(results)

    # ──────────────────────────────────────────────────────────────
    def predict(self, frame):
        """Tracking olmadan tek frame predict (resim modu)."""
        results = self.model.predict(
            source=frame,
            conf=cfg.CONF_THRESHOLD,
            save=False,
            verbose=False,
        )
        return self._parse(results)

    # ──────────────────────────────────────────────────────────────
    def _parse(self, results):
        r     = results[0]
        boxes = r.boxes

        out = {"humans": [], "masks": [], "handguns": [],
               "melees": [], "rifles": [], "all": []}

        for box in boxes:
            cls_id   = int(box.cls[0].item())
            conf     = float(box.conf[0].item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            raw_label = self.names[cls_id].lower()
            std_label = _LABEL_MAP.get(raw_label, raw_label)
            track_id  = int(box.id[0].item()) if box.id is not None else -1

            item = {
                "label":     raw_label,
                "std_label": std_label,
                "conf":      conf,
                "bbox":      (x1, y1, x2, y2),
                "track_id":  track_id,
            }
            out["all"].append(item)

            if std_label == "human":
                out["humans"].append(item)
            elif std_label == "mask":
                out["masks"].append(item)
            elif std_label == "handgun":
                out["handguns"].append(item)
            elif std_label == "melee":
                out["melees"].append(item)
            elif std_label == "rifle":
                out["rifles"].append(item)

        return out
