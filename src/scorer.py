"""
src/scorer.py
=============
Saf geometri + iş mantığı modülü.
- Hiçbir I/O, model çağrısı veya global state içermez.
- Bağımsız birim testlere uygundur.

Sorumluluklar:
  iou()               → iki bbox arasındaki kesişim oranı
  expanded_box()      → bbox'u merkez noktasından ölçekle genişletir
  weapon_belongs_to() → 2 aşamalı silah-kişi atama (IoU → expanded IoU)
  score_person()      → kişiye ait tespitlere göre tehdit skoru hesaplar
  score_to_level()    → sayısal skoru NONE/LOW/MEDIUM/HIGH seviyesine çevirir
"""

from src import config as cfg


# ── IoU ────────────────────────────────────────────────────────────
def iou(boxA, boxB):
    """Intersection over Union — iki (x1,y1,x2,y2) bbox arası."""
    ax1, ay1, ax2, ay2 = boxA
    bx1, by1, bx2, by2 = boxB
    ix1 = max(ax1, bx1);  iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2);  iy2 = min(ay2, by2)
    iw  = max(0, ix2 - ix1)
    ih  = max(0, iy2 - iy1)
    inter = iw * ih
    areaA = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    areaB = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = areaA + areaB - inter
    return 0.0 if union == 0 else inter / union


def box_inside(inner, outer, min_overlap=0.02):
    return iou(inner, outer) > min_overlap


# ── Expanded Box ───────────────────────────────────────────────────
def expanded_box(bbox, scale=None, frame_shape=None):
    """
    bbox'u merkez noktasından `scale` katı genişletir.
    frame_shape verilirse frame sınırına kırpar.
    """
    if scale is None:
        scale = cfg.EXPAND_SCALE
    x1, y1, x2, y2 = bbox
    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    hw = (x2 - x1) / 2.0 * scale
    hh = (y2 - y1) / 2.0 * scale
    nx1, ny1 = int(cx - hw), int(cy - hh)
    nx2, ny2 = int(cx + hw), int(cy + hh)
    if frame_shape is not None:
        H, W = frame_shape[:2]
        nx1 = max(0, nx1);  ny1 = max(0, ny1)
        nx2 = min(W - 1, nx2);  ny2 = min(H - 1, ny2)
    return (nx1, ny1, nx2, ny2)


# ── Silah Atama ────────────────────────────────────────────────────
def weapon_belongs_to(weapon_bbox, person_bbox, frame_shape=None):
    """
    2 aşamalı silah-kişi atama:
    1. Normal IoU kontrolü
    2. expanded_box ile 2. şans
    """
    if box_inside(weapon_bbox, person_bbox):
        return True
    exp = expanded_box(person_bbox, frame_shape=frame_shape)
    if box_inside(weapon_bbox, exp):
        return True
    return False


# ── Skorlama ───────────────────────────────────────────────────────
def score_person(person_bbox, detections, frame_shape=None):
    """
    Bir kişinin bbox'una göre tespitlerden tehdit skoru hesaplar.

    Parameters
    ----------
    person_bbox : tuple (x1,y1,x2,y2)
    detections  : Detector.track() döndürdüğü dict
    frame_shape : frame.shape (optional, expanded_box sınırı için)

    Returns
    -------
    dict:
        {
          "score":         int,
          "tags":          list[str],   # ["HANDGUN", "MASK", ...]
          "has_weapon_now": bool,
          "has_mask":      bool,
        }
    """
    masks    = detections.get("masks",    [])
    handguns = detections.get("handguns", [])
    melees   = detections.get("melees",   [])
    rifles   = detections.get("rifles",   [])

    has_mask    = any(box_inside(m["bbox"], person_bbox) for m in masks)
    has_handgun = any(weapon_belongs_to(g["bbox"], person_bbox, frame_shape) for g in handguns)
    has_melee   = any(weapon_belongs_to(m["bbox"], person_bbox, frame_shape) for m in melees)
    has_rifle   = any(weapon_belongs_to(r["bbox"], person_bbox, frame_shape) for r in rifles)

    score = 0
    tags  = []

    if has_mask:
        score += cfg.MASK_SCORE
        tags.append("MASK")
    if has_melee:
        score += cfg.MELEE_SCORE
        tags.append("MELEE")
    if has_handgun:
        score += cfg.HANDGUN_SCORE
        tags.append("HANDGUN")
    if has_rifle:
        score += cfg.RIFLE_SCORE
        tags.append("RIFLE")

    has_weapon_now = has_handgun or has_melee or has_rifle

    return {
        "score":          score,
        "tags":           tags,
        "has_weapon_now": has_weapon_now,
        "has_mask":       has_mask,
    }


# ── Seviye ─────────────────────────────────────────────────────────
def score_to_level(score):
    if score == 0:   return "NONE"
    elif score < 10: return "LOW"
    elif score < 20: return "MEDIUM"
    else:            return "HIGH"
