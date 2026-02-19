import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
import os
import threading
import time
import datetime
import re
import webbrowser
import random
import math

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SeaChecker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SeaChecker v2.0")
        self.geometry("1240x940")
        self.minsize(1140, 840)

        self.ACCENT = "#00eaff"
        self.SUCCESS = "#00ff9d"
        self.WARNING = "#ff6b6b"
        self.DARK_BG = "#0c1018"
        self.CARD_BG = "#161b22"

        self.configure(fg_color=self.DARK_BG)

        self.selected_files = []
        self.current_pattern = ctk.StringVar(value="pekora.zip/auth/accountlogin")
        self.only_logpass = ctk.BooleanVar(value=False)

        self.new_shablons = False # not edit this pj

        self.secret_chaos = ctk.BooleanVar(value=False)

        self.is_searching = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.found_count = 0
        self.unique_results = set()
        self.start_time = None

        self.language = "RU"
        self.ru_texts = self._ru_texts()
        self.en_texts = self._en_texts()

        self.gradient_colors = [
            "#ff0066", "#ff3399", "#ff66cc", "#ff99ff", "#cc99ff", "#9999ff",
            "#6666ff", "#3399ff", "#00ccff", "#00ffff", "#00ffcc", "#00ff99",
            "#33ff66", "#66ff33", "#99ff00", "#ccff00", "#ffff00", "#ffcc00",
            "#ff9900", "#ff6600", "#ff3300", "#ff0066", "#cc0066", "#990066",
            "#660066", "#330066", "#003366", "#006699", "#009999", "#00cc99"
        ]
        self.gradient_idx = 0

        self.create_ui()
        self.current_pattern.trace_add("write", self.on_pattern_change)
        self.secret_chaos.trace_add("write", self.secret_chaos_mode)

        self.after(450, self.animate_title)

    def _ru_texts(self):
        return {
            "title": "SeaChecker",
            "mode": "Режим поиска",
            "files": "Файлы",
            "selected": "Выбрано:",
            "select_btn": "Выбрать файлы",
            "start": "СТАРТ",
            "pause": "ПАУЗА",
            "resume": "ПРОДОЛЖИТЬ",
            "stop": "СТОП",
            "save": "СОХРАНИТЬ",
            "found": "Найдено строк:",
            "unique": "Уникальных:",
            "time": "Время:",
            "results": "Результаты",
            "ready": "Готов к работе",
            "searching": "Поиск...",
            "paused": "На паузе",
            "stopped": "Остановлено",
            "completed": "Поиск завершён",
            "only_logpass": "Только login:pass",
            "custom": "Свой шаблон",
            "enter_pat": "Введите шаблон поиска:",
            "settings": "Настройки",
            "secret": "Не нажимай меня",
            "error_no_files": "Выберите хотя бы один файл",
            "saved_to": "Сохранено в",
            "no_results": "Нет результатов для сохранения",
            "chaos_title": "ОШИБКА 1337",
            "chaos_msg": "Сосиска вертолёт успешно захватил ваш ПК.\nБелка скоро придёт за вами...",
        }

    def _en_texts(self):
        return {
            "title": "SeaChecker",
            "mode": "Search Mode",
            "files": "Files",
            "selected": "Selected:",
            "select_btn": "Select Files",
            "start": "START",
            "pause": "PAUSE",
            "resume": "RESUME",
            "stop": "STOP",
            "save": "SAVE",
            "found": "Found lines:",
            "unique": "Unique:",
            "time": "Time:",
            "results": "Results",
            "ready": "Ready",
            "searching": "Searching...",
            "paused": "Paused",
            "stopped": "Stopped",
            "completed": "Search finished",
            "only_logpass": "Only login:pass",
            "custom": "Custom pattern",
            "enter_pat": "Enter custom pattern:",
            "settings": "Settings",
            "secret": "Don't press me",
            "error_no_files": "Please select at least one file",
            "saved_to": "Saved to",
            "no_results": "No results to save",
            "chaos_title": "ERROR 1337",
            "chaos_msg": "Sausage helicopter has successfully hijacked your PC.\nThe squirrel is coming for you soon...",
        }

    def t(self, key):
        texts = self.en_texts if self.language == "ENG" else self.ru_texts
        return texts.get(key, key)

    def create_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16,8))

        self.title_label = ctk.CTkLabel(header, text=self.t("title"), font=("Helvetica", 42, "bold"),
                                        text_color=self.gradient_colors[0])
        self.title_label.pack(side="left")

        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="left", padx=40)

        ctk.CTkButton(lang_frame, text="RU", width=70, command=lambda: self.set_language("RU")).pack(side="left", padx=4)
        ctk.CTkButton(lang_frame, text="ENG", width=70, command=lambda: self.set_language("ENG")).pack(side="left", padx=4)

        ctk.CTkButton(header, text="Telegram", width=130, fg_color="#006699", hover_color="#004c75",
                      command=lambda: webbrowser.open("https://t.me/seachecker")).pack(side="right")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=8)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self.modes_frame = ctk.CTkFrame(main, fg_color=self.CARD_BG, corner_radius=12)
        self.modes_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,12), padx=4)

        self.mode_label = ctk.CTkLabel(self.modes_frame, text=self.t("mode"), font=("Segoe UI", 14, "bold"))
        self.mode_label.pack(anchor="w", padx=18, pady=(14,4))

        self.modes_container = None
        self.rebuild_modes_panel()

        file_frame = ctk.CTkFrame(self.modes_frame, fg_color="transparent")
        file_frame.pack(fill="x", padx=18, pady=12)

        self.files_label = ctk.CTkLabel(file_frame, text=self.t("files"), font=("Segoe UI", 14, "bold"))
        self.files_label.pack(side="left")

        self.file_label = ctk.CTkLabel(file_frame, text=f"{self.t('selected')} 0", text_color="#cccccc")
        self.file_label.pack(side="left", padx=20)

        ctk.CTkButton(file_frame, text=self.t("select_btn"), width=160, command=self.select_files).pack(side="right")

        ctk.CTkCheckBox(self.modes_frame, text=self.t("only_logpass"), variable=self.only_logpass,
                        font=("Segoe UI", 13)).pack(anchor="w", padx=18, pady=8)

        ctrl = ctk.CTkFrame(main, fg_color=self.CARD_BG, corner_radius=12)
        ctrl.grid(row=0, column=2, sticky="nse", padx=(12,4), pady=(0,12))

        btns = ctk.CTkFrame(ctrl, fg_color="transparent")
        btns.pack(fill="x", padx=18, pady=16)

        self.start_btn = ctk.CTkButton(btns, text=self.t("start"), width=140, height=50,
                                       fg_color="#00cc77", hover_color="#00aa66", text_color="white",
                                       font=("Segoe UI", 14, "bold"), command=self.start_search)
        self.start_btn.pack(side="left", padx=6)

        self.pause_btn = ctk.CTkButton(btns, text=self.t("pause"), width=140, height=50,
                                       fg_color="#ffaa33", hover_color="#dd8822", text_color="white",
                                       font=("Segoe UI", 14, "bold"), state="disabled", command=self.toggle_pause)
        self.pause_btn.pack(side="left", padx=6)

        self.stop_btn = ctk.CTkButton(btns, text=self.t("stop"), width=140, height=50,
                                      fg_color="#ff5555", hover_color="#dd3333", text_color="white",
                                      font=("Segoe UI", 14, "bold"), state="disabled", command=self.stop_search)
        self.stop_btn.pack(side="left", padx=6)

        self.save_btn = ctk.CTkButton(btns, text=self.t("save"), width=140, height=50,
                                      fg_color="#3366ff", hover_color="#2244dd", text_color="white",
                                      font=("Segoe UI", 14, "bold"), command=self.save_results)
        self.save_btn.pack(side="right", padx=12)

        res_frame = ctk.CTkFrame(main, fg_color=self.CARD_BG, corner_radius=12)
        res_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

        hdr = ctk.CTkFrame(res_frame, fg_color="transparent")
        hdr.pack(fill="x", padx=18, pady=(12,6))

        self.results_label = ctk.CTkLabel(hdr, text=self.t("results"), font=("Segoe UI", 16, "bold"))
        self.results_label.pack(side="left")

        self.stats_lbl = ctk.CTkLabel(hdr, text=f"{self.t('found')} 0 • {self.t('unique')} 0",
                                      font=("Segoe UI", 13), text_color="#cccccc")
        self.stats_lbl.pack(side="left", padx=40)

        self.time_lbl = ctk.CTkLabel(hdr, text="00:00", font=("Consolas", 13))
        self.time_lbl.pack(side="right")

        self.result_text = ctk.CTkTextbox(res_frame, font=("Consolas", 11.5),
                                          fg_color="#0a0e14", text_color="#e8e8ff")
        self.result_text.pack(fill="both", expand=True, padx=12, pady=(0,12))

        self.status = ctk.CTkLabel(self, text=self.t("ready"), height=36,
                                   fg_color="#11151e", text_color="#aaddff", anchor="w", padx=20)
        self.status.pack(fill="x", side="bottom")

        settings_frame = ctk.CTkFrame(main, fg_color=self.CARD_BG, corner_radius=12)
        settings_frame.grid(row=1, column=2, sticky="nse", padx=(12,4), pady=4)

        ctk.CTkLabel(settings_frame, text=self.t("settings"), font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=8)

        ctk.CTkCheckBox(settings_frame, text=self.t("secret"), variable=self.secret_chaos,
                        font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=4)

    def on_pattern_change(self, *args):
        pat = self.current_pattern.get()
        if pat == "Custom":
            title = self.t("custom")
            prompt = self.t("enter_pat")
            custom_pat = simpledialog.askstring(title, prompt, parent=self)
            if custom_pat and custom_pat.strip():
                self.current_pattern.set(custom_pat.strip())
            else:
                self.current_pattern.set("pekora.zip/auth/accountlogin")

    def secret_chaos_mode(self, *args):
        if self.secret_chaos.get():
            self.after(3000, self.activate_chaos)

    def activate_chaos(self):
        self.title_label.configure(text_color="#ff0000")
        self.after(200, lambda: self.title_label.configure(text_color="#00ff00"))
        self.after(400, lambda: self.title_label.configure(text_color="#ffff00"))
        self.after(600, lambda: self.title_label.configure(text_color="#ff00ff"))

        nonsense = ["ХАХАХА", "ПИЗДЕЦ", "СОСИСКА", "ВЕРТОЛЁТ", "БЕЛКА ИДЁТ", "228", "ЛОХ"]
        self.start_btn.configure(text=random.choice(nonsense))
        self.pause_btn.configure(text=random.choice(nonsense))
        self.stop_btn.configure(text=random.choice(nonsense))
        self.save_btn.configure(text=random.choice(nonsense))

        self.result_text.insert("end", "\n\nСОСИСКА ВЕРТОЛЁТ ЗАХВАТИЛ ТВОЙ ПК!!!\n")
        self.result_text.insert("end", "Белка уже в пути... беги сука...\n\n")

        self.after(5000, lambda: messagebox.showerror(
            self.t("chaos_title"),
            self.t("chaos_msg")
        ))

    def animate_title(self):
        self.gradient_idx = (self.gradient_idx + 1) % len(self.gradient_colors)
        base_color = self.gradient_colors[self.gradient_idx]

        pulse = math.sin(time.time() * 2) * 0.15 + 0.85

        r = int(int(base_color[1:3], 16) * pulse)
        g = int(int(base_color[3:5], 16) * pulse)
        b = int(int(base_color[5:7], 16) * pulse)

        pulsed_color = f"#{r:02x}{g:02x}{b:02x}"

        self.title_label.configure(text_color=pulsed_color)
        self.after(450, self.animate_title)

    def rebuild_modes_panel(self):
        if hasattr(self, 'modes_container') and self.modes_container:
            self.modes_container.destroy()

        if self.new_shablons:
            self.modes_container = ctk.CTkScrollableFrame(self.modes_frame, fg_color="transparent",
                                                          orientation="horizontal", height=64)
            self.modes_container.pack(fill="x", padx=12, pady=(0,10))
            layout = "horizontal"
        else:
            self.modes_container = ctk.CTkFrame(self.modes_frame, fg_color="transparent")
            self.modes_container.pack(fill="x", padx=12, pady=(0,10))
            layout = "grid"

        modes_list = [
            ("pekora.zip/auth/accountlogin", "#00ff9d"),
            ("ecsr.io/auth/login",           "#00d4ff"),
            ("Ecsr.io & Pekora.zip",         "#ff79c6"),
            ("kornet.lat",                   "#c77dff"),
            ("pwndab.xyz",                   "#ff9500"),
            ("bbblox.fit",                   "#ff4d6d"),
            ("All In",                       "#64dfdf"),
            ("Custom",                       "#adb5bd"),
        ]

        if layout == "horizontal":
            for txt, col in modes_list:
                ctk.CTkRadioButton(self.modes_container, text=txt, variable=self.current_pattern, value=txt,
                                   fg_color=col, hover_color=col, text_color="white",
                                   font=("Segoe UI", 11.5)).pack(side="left", padx=10, pady=4)
        else:
            col = 0
            row = 0
            for txt, col_color in modes_list:
                rb = ctk.CTkRadioButton(self.modes_container, text=txt, variable=self.current_pattern, value=txt,
                                        fg_color=col_color, hover_color=col_color, text_color="white",
                                        font=("Segoe UI", 11.5))
                rb.grid(row=row, column=col, padx=8, pady=6, sticky="w")
                col += 1
                if col > 2:
                    col = 0
                    row += 1

    def set_language(self, lang):
        self.language = lang
        self.update_ui_texts()
        self.rebuild_modes_panel()

    def update_ui_texts(self):
        self.mode_label.configure(text=self.t("mode"))
        self.files_label.configure(text=self.t("files"))
        self.file_label.configure(text=f"{self.t('selected')} {len(self.selected_files)}" if self.selected_files else f"{self.t('selected')} 0")
        self.status.configure(text=self.t("ready") if not self.is_searching else self.t("searching"))

    def select_files(self):
        fs = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        if fs:
            self.selected_files = list(fs)
            cnt = len(fs)
            names = ", ".join(os.path.basename(f) for f in fs[:3])
            if cnt > 3:
                names += f" +{cnt-3}"
            self.file_label.configure(text=f"{self.t('selected')} {cnt} · {names}")

    def start_search(self):
        if not self.selected_files:
            messagebox.showwarning("Ошибка" if self.language == "RU" else "Warning",
                                   self.t("error_no_files"))
            return

        self.is_searching = True
        self.is_paused = False
        self.pause_event.set()
        self.found_count = 0
        self.unique_results.clear()
        self.start_time = time.time()

        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")

        self.result_text.delete("0.0", "end")
        self.status.configure(text=self.t("searching"), text_color=self.ACCENT)

        threading.Thread(target=self.search_thread, daemon=True).start()
        self.after(300, self.update_ui_loop)

    def search_thread(self):
        current = self.current_pattern.get()
        only_clean = self.only_logpass.get()

        search_terms = {
            "pekora.zip/auth/accountlogin": "pekora.zip/auth/accountlogin",
            "ecsr.io/auth/login":           "ecsr.io/auth/login",
            "Ecsr.io & Pekora.zip":         ["ecsr.io/auth/login", "pekora.zip/auth/accountlogin"],
            "kornet.lat":                   "kornet.lat",
            "pwndab.xyz":                   "pwndab.xyz",
            "bbblox.fit":                   "bbblox.fit",
            "All In":                       ["kornet.lat", "pwndab.xyz", "bbblox.fit", "ecsr.io/auth/login"],
        }

        targets = search_terms.get(current, [current]) if isinstance(search_terms.get(current), list) else [current]

        for idx, filepath in enumerate(self.selected_files, 1):
            if not self.is_searching: break
            self.pause_event.wait()

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for lineno, rawline in enumerate(f, 1):
                        if not self.is_searching: break
                        if self.is_paused:
                            self.pause_event.wait()

                        line = rawline.strip()
                        if not line: continue

                        matched = False
                        tag = ""

                        for term in targets:
                            if term in line:
                                matched = True
                                tag = term
                                break

                        if matched:
                            result = line

                            if only_clean:
                                m = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)[:|\s;]+([^\s;]+)', line)
                                if m:
                                    result = f"{m.group(1)}:{m.group(2)}"
                                else:
                                    parts = re.split(r'[:|\s;]{1,4}', line.strip(), maxsplit=1)
                                    if len(parts) >= 2 and '@' in parts[0]:
                                        result = f"{parts[0]}:{parts[1].split()[0]}"
                                    else:
                                        result = line

                            else:
                                if tag not in ["pekora.zip/auth/accountlogin", "ecsr.io/auth/login"]:
                                    result = f"[{tag}] {os.path.basename(filepath)} | line {lineno}: {line}"
                                else:
                                    result = f"[{tag}] {line}"

                            key = result.strip()
                            if key not in self.unique_results:
                                self.unique_results.add(key)
                                self.found_count += 1
                                self.after(0, lambda r=result+"\n": [
                                    self.result_text.insert("end", r),
                                    self.result_text.see("end"),
                                    self.stats_lbl.configure(text=f"{self.t('found')} {self.found_count} • {self.t('unique')} {len(self.unique_results)}")
                                ])

            except Exception as e:
                self.after(0, lambda fn=os.path.basename(filepath), err=str(e):
                           self.result_text.insert("end", f"Ошибка чтения {fn}: {err}\n"))

        self.after(0, self.finish_search)

    def finish_search(self):
        self.is_searching = False
        self.is_paused = False
        elapsed = time.time() - self.start_time if self.start_time else 0
        dur = str(datetime.timedelta(seconds=int(elapsed)))
        uniq = len(self.unique_results)

        msg = f"{self.t('completed')} | {self.t('found')} {self.found_count} | {self.t('unique')} {uniq} | {self.t('time')} {dur}"
        self.status.configure(text=msg, text_color=self.SUCCESS)
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")

    def update_ui_loop(self):
        if not self.is_searching: return
        elapsed = time.time() - self.start_time if self.start_time else 0
        mm, ss = divmod(int(elapsed), 60)
        self.time_lbl.configure(text=f"{mm:02d}:{ss:02d}")
        self.after(400, self.update_ui_loop)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_event.clear()
            self.pause_btn.configure(text=self.t("resume"))
            self.status.configure(text=self.t("paused"))
        else:
            self.pause_event.set()
            self.pause_btn.configure(text=self.t("pause"))
            self.status.configure(text=self.t("searching"))

    def stop_search(self):
        self.is_searching = False
        self.is_paused = False
        self.pause_event.set()
        self.status.configure(text=self.t("stopped"), text_color=self.WARNING)
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")

    def save_results(self):
        text = self.result_text.get("0.0", "end").strip()
        if not text:
            messagebox.showinfo("Info", self.t("no_results"))
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status.configure(text=f"{self.t('saved_to')} {os.path.basename(path)}")

    def set_language(self, lang):
        self.language = lang
        self.update_ui_texts()
        self.rebuild_modes_panel()

    def update_ui_texts(self):
        self.mode_label.configure(text=self.t("mode"))
        self.files_label.configure(text=self.t("files"))
        self.file_label.configure(text=f"{self.t('selected')} {len(self.selected_files)}" if self.selected_files else f"{self.t('selected')} 0")
        self.status.configure(text=self.t("ready") if not self.is_searching else self.t("searching"))

    def select_files(self):
        fs = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        if fs:
            self.selected_files = list(fs)
            cnt = len(fs)
            names = ", ".join(os.path.basename(f) for f in fs[:3])
            if cnt > 3:
                names += f" +{cnt-3}"
            self.file_label.configure(text=f"{self.t('selected')} {cnt} · {names}")

if __name__ == "__main__":
    SeaChecker().mainloop()
