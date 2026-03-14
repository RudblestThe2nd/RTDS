"""
src/logger.py
=============
ThreatLogger — terminal + dosya eş zamanlı log sistemi.

Sorumluluklar:
  - Oturum log dosyası oluşturma ve yönetme
  - log() ile terminal + dosyaya eş zamanlı yazma
  - Screenshot alma (2 mod: ARMED cooldown / ARMED_HISTORY_NEW bypass)
  - Oturum özeti yazma ve kapatma
"""

import os
import time
import cv2
from datetime import datetime
from src import config as cfg


class ThreatLogger:

    def __init__(self):
        os.makedirs(cfg.LOG_DIR,        exist_ok=True)
        os.makedirs(cfg.SCREENSHOT_DIR, exist_ok=True)

        self._log_path = os.path.join(
            cfg.LOG_DIR,
            f"threat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        self._file          = open(self._log_path, "w", encoding="utf-8")
        self._ss_last: dict = {}   # {track_id: last_time}

    # ── Log ───────────────────────────────────────────────────────
    def write(self, msg: str):
        """Terminal + dosyaya eş zamanlı yazar."""
        print(msg)
        self._file.write(msg + "\n")
        self._file.flush()

    def header(self, source, model_path, tracker):
        sep = "=" * 60
        self.write(sep)
        self.write("THREAT DETECTION LOG  (w/ Tracking)")
        self.write(f"Başlangıç : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.write(f"Kaynak    : {source}")
        self.write(f"Model     : {model_path}")
        self.write(f"Tracker   : {tracker}")
        self.write(sep + "\n")

    def log_detections(self, ts, frame_no, all_detections):
        if all_detections:
            det_str = "  ".join(
                f"{d['label']}({d['conf']:.2f})[ID:{d['track_id']}]"
                for d in all_detections
            )
            self.write(f"[{ts} | F#{frame_no:06d}] {det_str}")
        elif cfg.LOG_EVERY_FRAME:
            self.write(f"[{ts} | F#{frame_no:06d}] Tespit yok")

    def log_person(self, person_result):
        """Bir kişinin skor ve etiket bilgisini yazar."""
        tid        = person_result["tid"]
        score      = person_result["score"]
        tags       = person_result["tags"]
        in_history = person_result["in_history"]
        has_weapon = person_result["has_weapon_now"]

        if score < cfg.LOG_MIN_SCORE and not in_history:
            return

        from src.scorer import score_to_level
        level        = score_to_level(score)
        tag_str      = ", ".join(tags) if tags else "temiz"
        history_flag = " [ARMED HISTORY]" if in_history and not has_weapon else ""
        self.write(f"  ID={tid} | score={score} | level={level} | tags=[{tag_str}]{history_flag}")

    def log_newly_armed(self, tid, tags, score):
        self.write(f"  !! YENİ TEHLİKELİ KİŞİ: ID={tid} | tags={tags} | score={score}")

    def blank(self):
        self.write("")

    # ── Screenshot ────────────────────────────────────────────────
    def take_screenshot(self, frame, person_result, ts):
        """
        Screenshot alır.
        Reason:
          ARMED             → cooldown kontrolü (SCREENSHOT_COOLDOWN)
          ARMED_HISTORY_NEW → cooldown bypass, anında alır
        """
        pd     = person_result
        reason = None

        if pd["newly_armed"]:
            reason = "ARMED_HISTORY_NEW"
        elif pd["has_weapon_now"] and pd["score"] >= cfg.SCREENSHOT_MIN_SCORE:
            reason = "ARMED"

        if reason is None:
            return

        tid = pd["tid"]
        now = time.time()

        if reason != "ARMED_HISTORY_NEW":
            last = self._ss_last.get(tid, 0)
            if now - last < cfg.SCREENSHOT_COOLDOWN:
                return
        self._ss_last[tid] = now

        tag_str   = "_".join(pd["tags"]) if pd["tags"] else "clean"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename  = (
            f"{reason}_F{pd['frame_no']:06d}_{ts.replace(':','-')}"
            f"_ID{tid}_sc{pd['score']}_{tag_str}_{timestamp}.png"
        )
        filepath = os.path.join(cfg.SCREENSHOT_DIR, filename)
        cv2.imwrite(filepath, frame)
        self.write(f"  >> SS [{reason}]: {filepath}")

    # ── Kapanış ───────────────────────────────────────────────────
    def close(self, frame_no, armed_ids):
        sep = "=" * 60
        self.write(f"\n{sep}")
        self.write(f"Bitiş         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Frame: {frame_no}")
        self.write(f"Tehlikeli ID'ler ({len(armed_ids)}): {sorted(armed_ids)}")
        self.write(f"Log           : {self._log_path}")
        self.write(f"Görseller     : {cfg.SCREENSHOT_DIR}/")
        self.write(sep)
        self._file.close()
        print(f"\nTamamlandı. Tehlikeli ID'ler: {sorted(armed_ids)}")
        print(f"Log: {self._log_path} | Görseller: {cfg.SCREENSHOT_DIR}/")

    @property
    def log_path(self):
        return self._log_path
