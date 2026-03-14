"""
launcher.py
===========
Threat Detection projesini başlatan grafik arayüz.
Modüler projeyle çalışır: src/config.py patch'lenir, main.py çalıştırılır.

Çalıştır: python launcher.py
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import sys
import os
import re
import cv2

# ── Proje kök dizini (launcher.py ile aynı yerde) ──────────────────
ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
MAIN_PATH   = os.path.join(ROOT_DIR, "main.py")
CONFIG_PATH = os.path.join(ROOT_DIR, "src", "config.py")

# ── Renk Paleti ─────────────────────────────────────────────────────
BG      = "#07090e"
SURFACE = "#0c1018"
BORDER  = "#1a2535"
CYAN    = "#00e5ff"
RED     = "#ff3355"
GREEN   = "#00e676"
YELLOW  = "#ffd60a"
DIM     = "#2a4060"
TEXT    = "#c8d8e8"
WHITE   = "#e0eef8"

MONO    = ("Courier New", 10)
MONO_SM = ("Courier New", 9)
LABEL   = ("Courier New", 10, "bold")
BIG     = ("Courier New", 14, "bold")


# ══════════════════════════════════════════════════════════════════
#  YARDIMCI
# ══════════════════════════════════════════════════════════════════

def patch_config(var_name: str, new_val: str) -> None:
    """src/config.py içindeki 'VAR = <eski>' satırını günceller."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        code = f.read()
    pattern     = rf'^({re.escape(var_name)}\s*=\s*).*$'
    replacement = rf'\g<1>{new_val}'
    new_code    = re.sub(pattern, replacement, code, count=1, flags=re.MULTILINE)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(new_code)


def list_cameras(max_idx: int = 6) -> list[tuple[int, str]]:
    """Kullanılabilir kameraları tarar."""
    found = []
    for i in range(max_idx):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            found.append((i, f"Kamera {i}  ({w}×{h})"))
            cap.release()
    return found


# ══════════════════════════════════════════════════════════════════
#  ANA PENCERE
# ══════════════════════════════════════════════════════════════════

class LauncherApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Threat Detection — Launcher")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.mode        = tk.StringVar(value="mp4")
        self.mp4_path    = tk.StringVar(value="")
        self.cam_index   = tk.IntVar(value=0)
        self.cameras: list[tuple[int, str]] = []
        self.scanning    = False

        self._build()
        self._center()
        self._show_mp4()     # varsayılan: mp4 paneli görünür

    # ─────────────────────────────────────────────────────────────
    #  UI İNŞA
    # ─────────────────────────────────────────────────────────────
    def _build(self):

        # ── Header ──
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=22, pady=(22, 0))
        tk.Label(hdr, text="⚠", font=("Courier New", 26, "bold"),
                 bg=BG, fg=RED).pack(side="left", padx=(0, 10))
        tf = tk.Frame(hdr, bg=BG)
        tf.pack(side="left")
        tk.Label(tf, text="THREAT DETECT",
                 font=("Courier New", 18, "bold"), bg=BG, fg=WHITE).pack(anchor="w")
        tk.Label(tf, text="Real-Time CCTV Tehdit Tespit Sistemi  ·  v4.0 Modular",
                 font=MONO_SM, bg=BG, fg=DIM).pack(anchor="w")

        self._sep()

        # ── Mod seçimi ──
        mod_box = self._box()
        tk.Label(mod_box, text="  KAYNAK SEÇ", font=LABEL,
                 bg=SURFACE, fg=CYAN).pack(anchor="w", padx=8, pady=(8, 4))

        btn_row = tk.Frame(mod_box, bg=SURFACE)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        self.rb_mp4 = self._radio(btn_row, "📁  MP4 / Video Dosyası", "mp4")
        self.rb_mp4.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.rb_cam = self._radio(btn_row, "📷  Kamera (Webcam / USB)", "camera")
        self.rb_cam.pack(side="left", expand=True, fill="x")

        # ── İçerik alanı (toggle buraya) ──
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="x", padx=22, pady=4)

        # ── MP4 paneli ──
        self.mp4_panel = tk.Frame(self.content, bg=SURFACE,
                                   highlightbackground=BORDER, highlightthickness=1)
        tk.Label(self.mp4_panel, text="  Dosya Yolu:", font=MONO_SM,
                 bg=SURFACE, fg=DIM).pack(anchor="w", padx=10, pady=(8, 2))
        pr = tk.Frame(self.mp4_panel, bg=SURFACE)
        pr.pack(fill="x", padx=10, pady=(0, 10))
        self.path_entry = tk.Entry(pr, textvariable=self.mp4_path,
                                    font=MONO, bg="#060a10", fg=CYAN,
                                    insertbackground=CYAN, bd=0,
                                    relief="flat", width=44)
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        tk.Button(pr, text="Gözat...", font=MONO_SM,
                  bg=BORDER, fg=TEXT, relief="flat", cursor="hand2",
                  activebackground=DIM, command=self._browse
                  ).pack(side="left", ipady=4, ipadx=10)

        # ── Kamera paneli ──
        self.cam_panel = tk.Frame(self.content, bg=SURFACE,
                                   highlightbackground=BORDER, highlightthickness=1)
        cam_top = tk.Frame(self.cam_panel, bg=SURFACE)
        cam_top.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(cam_top, text="  Kamera Seç:", font=MONO_SM,
                 bg=SURFACE, fg=DIM).pack(side="left")
        self.scan_btn = tk.Button(cam_top, text="↻ Tara", font=MONO_SM,
                                   bg=BORDER, fg=CYAN, relief="flat",
                                   cursor="hand2", command=self._scan)
        self.scan_btn.pack(side="right", ipadx=8, ipady=3)

        self.cam_listbox = tk.Listbox(
            self.cam_panel, font=MONO, bg="#060a10", fg=CYAN,
            selectbackground=BORDER, selectforeground=WHITE,
            activestyle="none", relief="flat", bd=0,
            highlightthickness=0, height=4
        )
        self.cam_listbox.pack(fill="x", padx=10)
        self.cam_listbox.bind("<<ListboxSelect>>", self._cam_selected)

        self.cam_status = tk.Label(self.cam_panel, text="↻ Tara butonuna bas",
                                    font=MONO_SM, bg=SURFACE, fg=DIM)
        self.cam_status.pack(pady=(4, 8))

        # ── Ayarlar ──
        self._sep()
        cfg_box = self._box()
        tk.Label(cfg_box, text="  AYARLAR", font=LABEL,
                 bg=SURFACE, fg=CYAN).pack(anchor="w", padx=8, pady=(8, 4))

        grid = tk.Frame(cfg_box, bg=SURFACE)
        grid.pack(padx=14, pady=(0, 12), fill="x")

        # CONF_THRESHOLD
        tk.Label(grid, text="CONF_THRESHOLD", font=MONO_SM,
                 bg=SURFACE, fg=DIM).grid(row=0, column=0, sticky="w", padx=(0,12), pady=3)
        self.conf_var = tk.StringVar(value="0.20")
        tk.Entry(grid, textvariable=self.conf_var, font=MONO,
                 bg="#060a10", fg=CYAN, width=8, bd=0,
                 relief="flat", insertbackground=CYAN
                 ).grid(row=0, column=1, sticky="w", ipady=4)
        tk.Label(grid, text="(0.05 – 0.90)", font=MONO_SM,
                 bg=SURFACE, fg=DIM).grid(row=0, column=2, sticky="w", padx=8)

        # EXPAND_SCALE
        tk.Label(grid, text="EXPAND_SCALE", font=MONO_SM,
                 bg=SURFACE, fg=DIM).grid(row=1, column=0, sticky="w", padx=(0,12), pady=3)
        self.expand_var = tk.StringVar(value="1.35")
        tk.Entry(grid, textvariable=self.expand_var, font=MONO,
                 bg="#060a10", fg=CYAN, width=8, bd=0,
                 relief="flat", insertbackground=CYAN
                 ).grid(row=1, column=1, sticky="w", ipady=4)
        tk.Label(grid, text="silah atama genişleme", font=MONO_SM,
                 bg=SURFACE, fg=DIM).grid(row=1, column=2, sticky="w", padx=8)

        # Checkboxlar
        self.interesting_var = tk.BooleanVar(value=True)
        self._chk(grid, "SHOW_ONLY_INTERESTING", self.interesting_var, 2)

        self.fullscreen_var = tk.BooleanVar(value=False)
        self._chk(grid, "FULLSCREEN_MODE", self.fullscreen_var, 3)

        self.save_var = tk.BooleanVar(value=False)
        self._chk(grid, "SAVE_OUTPUT  (output.mp4 kaydeder)", self.save_var, 4)

        # ── Model yolu ──
        self._sep()
        mdl_box = self._box()
        tk.Label(mdl_box, text="  MODEL YOLU", font=LABEL,
                 bg=SURFACE, fg=CYAN).pack(anchor="w", padx=8, pady=(8, 2))
        mr = tk.Frame(mdl_box, bg=SURFACE)
        mr.pack(fill="x", padx=10, pady=(0, 10))
        self.model_var = tk.StringVar(
            value=""
        )
        tk.Entry(mr, textvariable=self.model_var,
                 font=MONO_SM, bg="#060a10", fg=CYAN,
                 insertbackground=CYAN, bd=0, relief="flat", width=56
                 ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
        tk.Button(mr, text="Gözat...", font=MONO_SM,
                  bg=BORDER, fg=TEXT, relief="flat", cursor="hand2",
                  activebackground=DIM, command=self._browse_model
                  ).pack(side="left", ipady=4, ipadx=10)

        # ── Başlat ──
        self._sep()
        self.start_btn = tk.Button(
            self, text="▶  BAŞLAT",
            font=BIG, bg=RED, fg=WHITE,
            activebackground="#cc1133", activeforeground=WHITE,
            relief="flat", cursor="hand2", command=self._launch
        )
        self.start_btn.pack(fill="x", padx=22, ipady=14)

        self.status_var = tk.StringVar(value="Hazır — kaynak seç ve başlat")
        tk.Label(self, textvariable=self.status_var,
                 font=MONO_SM, bg=BG, fg=DIM).pack(pady=(6, 14))

    # ─────────────────────────────────────────────────────────────
    #  YARDIMCI WIDGET BUILDER'LAR
    # ─────────────────────────────────────────────────────────────
    def _box(self):
        f = tk.Frame(self, bg=SURFACE,
                     highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", padx=22, pady=(0, 2))
        return f

    def _sep(self):
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=22, pady=6)

    def _radio(self, parent, text, value):
        return tk.Radiobutton(
            parent, text=text, variable=self.mode, value=value,
            command=self._mode_changed,
            font=("Courier New", 11, "bold"), bg=SURFACE, fg=TEXT,
            selectcolor=SURFACE, activebackground=SURFACE,
            indicatoron=0, relief="flat", bd=0,
            padx=14, pady=10, cursor="hand2",
            highlightthickness=1, highlightbackground=BORDER
        )

    def _chk(self, parent, text, var, row):
        tk.Checkbutton(parent, text=text, variable=var,
                       font=MONO_SM, bg=SURFACE, fg=TEXT,
                       selectcolor=SURFACE, activebackground=SURFACE,
                       cursor="hand2"
                       ).grid(row=row, column=0, columnspan=3,
                               sticky="w", pady=2)

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ─────────────────────────────────────────────────────────────
    #  MOD TOGGLE
    # ─────────────────────────────────────────────────────────────
    def _mode_changed(self):
        self._update_radio_colors()
        if self.mode.get() == "mp4":
            self._show_mp4()
        else:
            self._show_cam()

    def _show_mp4(self):
        self.cam_panel.pack_forget()
        self.mp4_panel.pack(fill="x")

    def _show_cam(self):
        self.mp4_panel.pack_forget()
        self.cam_panel.pack(fill="x")
        if not self.cameras:
            self._scan()

    def _update_radio_colors(self):
        m = self.mode.get()
        self.rb_mp4.configure(
            fg=CYAN if m == "mp4"    else DIM,
            highlightbackground=CYAN if m == "mp4"    else BORDER)
        self.rb_cam.configure(
            fg=CYAN if m == "camera" else DIM,
            highlightbackground=CYAN if m == "camera" else BORDER)

    # ─────────────────────────────────────────────────────────────
    #  DOSYA SEÇİM
    # ─────────────────────────────────────────────────────────────
    def _browse(self):
        p = filedialog.askopenfilename(
            title="Video dosyası seç",
            filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov *.webm"), ("Tümü", "*.*")]
        )
        if p:
            self.mp4_path.set(p)

    def _browse_model(self):
        p = filedialog.askopenfilename(
            title="Model dosyası seç (.pt)",
            filetypes=[("PyTorch model", "*.pt"), ("Tümü", "*.*")]
        )
        if p:
            self.model_var.set(p)

    # ─────────────────────────────────────────────────────────────
    #  KAMERA TARAMA
    # ─────────────────────────────────────────────────────────────
    def _scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.scan_btn.configure(text="Taranıyor...", state="disabled")
        self.cam_listbox.delete(0, "end")
        self.cam_status.configure(text="Kameralar aranıyor...", fg=YELLOW)
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        cams = list_cameras()
        self.after(0, lambda: self._scan_done(cams))

    def _scan_done(self, cams):
        self.scanning = False
        self.scan_btn.configure(text="↻ Tara", state="normal")
        self.cameras = cams
        self.cam_listbox.delete(0, "end")
        if cams:
            for idx, label in cams:
                self.cam_listbox.insert("end", f"  {label}")
            self.cam_listbox.selection_set(0)
            self.cam_index.set(cams[0][0])
            self.cam_status.configure(text=f"{len(cams)} kamera bulundu ✓", fg=GREEN)
        else:
            self.cam_status.configure(
                text="Kamera bulunamadı — USB kamera bağlı mı?", fg=RED)

    def _cam_selected(self, _event):
        sel = self.cam_listbox.curselection()
        if sel and self.cameras and sel[0] < len(self.cameras):
            self.cam_index.set(self.cameras[sel[0]][0])

    # ─────────────────────────────────────────────────────────────
    #  VALİDASYON
    # ─────────────────────────────────────────────────────────────
    def _validate(self) -> bool:
        # Proje dosyaları mevcut mu?
        for path, name in [(MAIN_PATH, "main.py"), (CONFIG_PATH, "src/config.py")]:
            if not os.path.isfile(path):
                messagebox.showerror("Hata",
                    f"Proje dosyası bulunamadı: {name}\n"
                    f"launcher.py proje kök dizininde olmalı.")
                return False

        # Kaynak
        if self.mode.get() == "mp4":
            p = self.mp4_path.get().strip()
            if not p:
                messagebox.showerror("Hata", "Lütfen bir video dosyası seçin.")
                return False
            if not os.path.isfile(p):
                messagebox.showerror("Hata", f"Dosya bulunamadı:\n{p}")
                return False
        else:
            if not self.cameras:
                messagebox.showerror("Hata",
                    "Kamera bulunamadı.\n↻ Tara butonuna bas ve tekrar dene.")
                return False

        # Model
        m = self.model_var.get().strip()
        if not m:
            messagebox.showerror("Hata", "Model yolu boş olamaz.")
            return False
        if not os.path.isfile(m):
            if not messagebox.askyesno("Uyarı",
                f"Model dosyası bulunamadı:\n{m}\n\nYine de devam et?"):
                return False

        # CONF
        try:
            c = float(self.conf_var.get())
            assert 0.01 <= c <= 0.99
        except Exception:
            messagebox.showerror("Hata", "CONF_THRESHOLD 0.05 – 0.90 arasında olmalı.")
            return False

        # EXPAND_SCALE
        try:
            e = float(self.expand_var.get())
            assert 1.0 <= e <= 3.0
        except Exception:
            messagebox.showerror("Hata", "EXPAND_SCALE 1.0 – 3.0 arasında olmalı.")
            return False

        return True

    # ─────────────────────────────────────────────────────────────
    #  BAŞLAT
    # ─────────────────────────────────────────────────────────────
    def _launch(self):
        if not self._validate():
            return

        # ── src/config.py güncelle ──
        mode   = self.mode.get()
        source = self.mp4_path.get().strip() if mode == "mp4" else str(self.cam_index.get())

        try:
            # SOURCE: mp4 ise tırnaklı string, kamera ise int
            src_val = f'"{source}"' if mode == "mp4" else source
            patch_config("SOURCE",               src_val)
            patch_config("MODEL_PATH",           f'"{self.model_var.get().strip()}"')
            patch_config("CONF_THRESHOLD",       self.conf_var.get().strip())
            patch_config("EXPAND_SCALE",         self.expand_var.get().strip())
            patch_config("SHOW_ONLY_INTERESTING", str(self.interesting_var.get()))
            patch_config("FULLSCREEN_MODE",      str(self.fullscreen_var.get()))
            patch_config("SAVE_OUTPUT",          str(self.save_var.get()))
        except Exception as e:
            messagebox.showerror("Config Hatası", str(e))
            return

        self.status_var.set(f"Çalışıyor — kaynak: {source}")
        self.start_btn.configure(state="disabled", text="⏳  Çalışıyor...")

        def _run():
            try:
                subprocess.run(
                    [sys.executable, MAIN_PATH],
                    cwd=ROOT_DIR,
                    check=False
                )
            finally:
                self.after(0, self._done)

        threading.Thread(target=_run, daemon=True).start()

    def _done(self):
        self.start_btn.configure(state="normal", text="▶  BAŞLAT")
        self.status_var.set("Sistem kapandı — tekrar başlatmak için ▶ BAŞLAT")


# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
