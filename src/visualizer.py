"""
src/visualizer.py
=================
Tüm OpenCV çizim operasyonları bu modülde toplanmıştır.
- Hiçbir iş mantığı içermez — çizmek için gereken verileri parametre olarak alır.
- Hiçbir karar vermez, hiçbir durumu saklamaz.

Public API:
  draw_person(frame, person_result)
  draw_hud(frame, frame_no, total_frames, fps, armed_count)
  draw_vertical_bar(img, x, y, w, h, percent, color=None)
"""

import cv2
from src import config as cfg
from src.scorer import score_to_level


# ── Dikey Tehdit Barı ──────────────────────────────────────────────
def draw_vertical_bar(img, x, y, w, h, percent, color=None):
    """
    Dikey tehdit göstergesi çizer.
    percent: 0–100 arası doluluk oranı
    color  : None ise yeşil→kırmızı gradient, verilmişse sabit renk
    """
    p = max(0.0, min(100.0, float(percent)))

    if color is None:
        t = 0.0 if p <= 10.0 else max(0.0, min(1.0, (p - 10.0) / 90.0))
        bar_color = (0, int(255 * (1.0 - t)), int(255 * t))
    else:
        bar_color = color

    # Arka plan
    cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (40, 40, 40), -1)
    # Dolgu
    fill_h = int(h * (p / 100.0))
    if fill_h > 0:
        fill_y1 = int(y + h - fill_h)
        cv2.rectangle(img, (int(x), fill_y1), (int(x + w), int(y + h)), bar_color, -1)
    # Çerçeve
    cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (255, 255, 255), 1)


# ── Kişi Çizimi ───────────────────────────────────────────────────
def draw_person(frame, person_result):
    """
    Tek bir kişi için tüm overlay'leri çizer:
      bbox, etiket, detay satırı, dikey bar, ARMED HISTORY yazısı

    person_result dict keys:
      tid, score, tags, bbox,
      has_weapon_now, in_history, newly_armed
    """
    tid           = person_result["tid"]
    score         = person_result["score"]
    tags          = person_result["tags"]
    px1, py1, px2, py2 = person_result["bbox"]
    has_weapon_now = person_result["has_weapon_now"]
    in_history    = person_result["in_history"]

    # ── Renk ve etiket ──
    if has_weapon_now:
        box_color  = cfg.COLOR_ARMED
        status_txt = f"ARMED | ID={tid} | score={score}"
    elif in_history:
        box_color  = cfg.COLOR_HISTORY
        status_txt = f"ARMED HISTORY | ID={tid}"
    else:
        box_color  = cfg.COLOR_NORMAL
        status_txt = f"{score_to_level(score)} | ID={tid} | score={score}"

    # ── Bbox ──
    cv2.rectangle(frame, (px1, py1), (px2, py2), box_color, 2)

    # ── Üst etiket ──
    cv2.putText(frame, status_txt,
                (px1, max(py1 - 10, 20)),
                cfg.FONT, cfg.FONT_SCALE_LABEL, box_color,
                cfg.FONT_THICK, cv2.LINE_AA)

    # ── Armed History banner (bbox içi) ──
    if in_history and not has_weapon_now:
        cv2.putText(frame, "!! ARMED HISTORY !!",
                    (px1 + 4, py1 + 18),
                    cfg.FONT, 0.5, (0, 0, 255), 2, cv2.LINE_AA)

    # ── Alt detay satırı ──
    detail = " | ".join(tags) if tags else ("PREV ARMED" if in_history else "NO TAG")
    cv2.putText(frame, detail,
                (px1, min(py2 + 20, frame.shape[0] - 10)),
                cfg.FONT, cfg.FONT_SCALE_DETAIL, (0, 255, 255),
                cfg.FONT_THICK, cv2.LINE_AA)

    # ── Dikey tehdit barı ──
    person_percent = min(score, 100)
    if in_history and person_percent == 0:
        person_percent = 15   # geçmişte silahlıysa barı küçük de olsa göster

    default_bar_w = 12
    pad           = 6
    bbox_h        = max(20, py2 - py1)
    avail_right   = frame.shape[1] - px2 - pad
    avail_left    = px1 - pad

    if avail_right >= default_bar_w:
        bar_x, bar_w = px2 + pad, default_bar_w
    elif avail_left >= default_bar_w:
        bar_x, bar_w = px1 - pad - default_bar_w, default_bar_w
    else:
        if avail_right >= avail_left:
            bar_w = max(6, avail_right); bar_x = px2 + pad
        else:
            bar_w = max(6, avail_left);  bar_x = px1 - pad - bar_w

    bar_color = (0, 0, 255) if in_history else None
    draw_vertical_bar(frame,
                      int(bar_x), int(py1), int(bar_w), int(bbox_h),
                      person_percent, color=bar_color)


# ── HUD ───────────────────────────────────────────────────────────
def draw_hud(frame, frame_no, total_frames, fps, armed_count):
    """Sol üst köşe — FPS, frame sayacı, armed ID sayısı."""
    cv2.putText(frame, f"FPS: {fps:.1f}",
                (20, 30), cfg.FONT, cfg.FONT_SCALE_FPS,
                (0, 255, 0), cfg.FONT_THICK, cv2.LINE_AA)

    cv2.putText(frame, f"Armed IDs: {armed_count}",
                (20, 55), cfg.FONT, 0.45,
                (0, 0, 255), 1, cv2.LINE_AA)

    if total_frames > 0:
        cv2.putText(frame, f"Frame: {frame_no}/{total_frames}",
                    (20, 75), cfg.FONT, 0.4,
                    (200, 200, 200), 1, cv2.LINE_AA)
