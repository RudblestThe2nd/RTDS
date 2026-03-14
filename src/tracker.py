"""
src/tracker.py
==============
ArmedHistoryTracker — oturum boyunca silahlı kişilerin track_id'lerini hatırlar.

Davranış:
  - armed_ids  : oturum boyunca HİÇ sıfırlanmaz
  - newly_added: her begin_frame() çağrısında temizlenir
                 → bir ID yalnızca ilk eklendiği frame'de "newly_armed" sayılır
  - Kişi kameradan çıkıp aynı ID ile geri dönse bile in_history=True kalır
"""


class ArmedHistoryTracker:

    def __init__(self):
        self._armed_ids:  set[int] = set()
        self._newly_added: set[int] = set()

    # ── Frame döngüsü başında çağrılır ────────────────────────────
    def begin_frame(self):
        """Her frame başında newly_added setini temizle."""
        self._newly_added.clear()

    # ── Güncelleme ─────────────────────────────────────────────────
    def register(self, track_id: int):
        """
        Bir kişiyi silahlı olarak kaydet.
        İlk kez ekleniyorsa newly_added'e de alınır.
        """
        if track_id == -1:
            return
        if track_id not in self._armed_ids:
            self._armed_ids.add(track_id)
            self._newly_added.add(track_id)

    # ── Sorgular ───────────────────────────────────────────────────
    def is_armed(self, track_id: int) -> bool:
        """Bu ID daha önce silahla görüldü mü?"""
        return track_id in self._armed_ids

    def is_newly_armed(self, track_id: int) -> bool:
        """Bu ID bu frame'de ilk kez mi eklendi?"""
        return track_id in self._newly_added

    # ── İstatistik ─────────────────────────────────────────────────
    @property
    def armed_ids(self) -> set[int]:
        return frozenset(self._armed_ids)

    def count(self) -> int:
        return len(self._armed_ids)

    def reset(self):
        """Oturum sıfırlama (test amaçlı)."""
        self._armed_ids.clear()
        self._newly_added.clear()
