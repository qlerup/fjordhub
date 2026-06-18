import sys
import tempfile
import threading
import traceback
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from io import BytesIO
from pathlib import Path
from tkinter import BOTH, DISABLED, END, LEFT, NORMAL, RIGHT, VERTICAL, W, filedialog, messagebox
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

import requests

import ai_billedbeskriver as core


try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


IMAGE_FILETYPES = [
    ("Billedfiler", "*.jpg *.jpeg *.png *.webp *.gif *.bmp *.tif *.tiff *.svg"),
    ("JPEG", "*.jpg *.jpeg"),
    ("PNG", "*.png"),
    ("Alle filer", "*.*"),
]


class BilledbeskriverApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("AI Billedbeskriver")
        self.geometry("1120x740")
        self.minsize(900, 620)

        self.image_path = tk.StringVar(value="")
        self.model = tk.StringVar(value=core.MODEL)
        self.ollama_url = tk.StringVar(value=core.OLLAMA_BASE_URL)
        self.server_url = tk.StringVar(value="")
        self.api_token = tk.StringVar(value="")
        self.connection_link = tk.StringVar(value="")
        self.status = tk.StringVar(value="Vælg et billede for at starte.")
        self.external_counts_text = tk.StringVar(value="")

        self.preview_original = None
        self.preview_photo = None
        self.busy = False
        self.external_running = False
        self.external_run_total = 0
        self.external_processed = 0
        self.external_stop_event = threading.Event()
        self.ollama_retry_lock = threading.Lock()
        self.external_slots = []

        self._build_ui()
        self._apply_style()

        if len(sys.argv) > 1:
            self.set_image_path(" ".join(sys.argv[1:]).strip().strip('"'))

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f6f8")
        style.configure("Toolbar.TFrame", background="#eef1f4")
        style.configure("Panel.TFrame", background="#ffffff", borderwidth=1, relief="solid")
        style.configure("TLabel", background="#f5f6f8", foreground="#17202a")
        style.configure("Panel.TLabel", background="#ffffff", foreground="#17202a")
        style.configure("Status.TLabel", background="#eef1f4", foreground="#334155")
        style.configure("TButton", padding=(12, 7))
        style.configure("Primary.TButton", padding=(14, 8))
        style.configure("TEntry", padding=5)

    def _build_ui(self):
        root = ttk.Frame(self, padding=14)
        root.pack(fill=BOTH, expand=True)

        toolbar = ttk.Frame(root, style="Toolbar.TFrame", padding=10)
        toolbar.pack(fill="x")

        self.choose_button = ttk.Button(
            toolbar,
            text="Vælg billede",
            command=self.choose_image,
        )
        self.choose_button.pack(side=LEFT)

        self.analyze_button = ttk.Button(
            toolbar,
            text="Analyser",
            style="Primary.TButton",
            command=self.start_analysis,
            state=DISABLED,
        )
        self.analyze_button.pack(side=LEFT, padx=(8, 0))

        self.copy_button = ttk.Button(
            toolbar,
            text="Kopier tekst",
            command=self.copy_result,
            state=DISABLED,
        )
        self.copy_button.pack(side=LEFT, padx=(8, 0))

        settings = ttk.Frame(toolbar, style="Toolbar.TFrame")
        settings.pack(side=RIGHT)

        ttk.Label(settings, text="Ollama", style="Status.TLabel").grid(row=0, column=0, sticky=W, padx=(0, 6))
        ttk.Entry(settings, textvariable=self.ollama_url, width=24).grid(row=0, column=1, padx=(0, 14))

        ttk.Label(settings, text="Model", style="Status.TLabel").grid(row=0, column=2, sticky=W, padx=(0, 6))
        ttk.Entry(settings, textvariable=self.model, width=18).grid(row=0, column=3)

        path_row = ttk.Frame(root, padding=(0, 10, 0, 8))
        path_row.pack(fill="x")
        ttk.Label(path_row, textvariable=self.image_path).pack(side=LEFT, fill="x", expand=True)

        external_row = ttk.Frame(root, style="Toolbar.TFrame", padding=10)
        external_row.pack(fill="x", pady=(0, 10))
        ttk.Label(external_row, text="Forbindelseslink", style="Status.TLabel").grid(row=0, column=0, sticky=W, padx=(0, 6))
        ttk.Entry(external_row, textvariable=self.connection_link, width=72).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.external_start_button = ttk.Button(
            external_row,
            text="Kør ekstern kø",
            command=self.start_external_worker,
        )
        self.external_start_button.grid(row=0, column=2, padx=(0, 6))
        self.external_stop_button = ttk.Button(
            external_row,
            text="Stop",
            command=self.stop_external_worker,
            state=DISABLED,
        )
        self.external_stop_button.grid(row=0, column=3)
        ttk.Label(
            external_row,
            textvariable=self.external_counts_text,
            style="Status.TLabel",
        ).grid(row=1, column=0, columnspan=4, sticky=W, pady=(8, 0))
        external_row.columnconfigure(1, weight=1)

        self.single_body = ttk.PanedWindow(root, orient="horizontal")
        self.single_body.pack(fill=BOTH, expand=True)

        preview_panel = ttk.Frame(self.single_body, style="Panel.TFrame", padding=12)
        result_panel = ttk.Frame(self.single_body, style="Panel.TFrame", padding=12)
        self.single_body.add(preview_panel, weight=2)
        self.single_body.add(result_panel, weight=3)

        self.preview_label = ttk.Label(
            preview_panel,
            text="Intet billede valgt",
            anchor="center",
            justify="center",
            style="Panel.TLabel",
        )
        self.preview_label.pack(fill=BOTH, expand=True)
        self.preview_label.bind("<Configure>", lambda _event: self.render_preview())

        ttk.Label(result_panel, text="Beskrivelse", style="Panel.TLabel").pack(anchor=W)
        self.result_text = ScrolledText(
            result_panel,
            wrap="word",
            height=20,
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
            borderwidth=1,
            relief="solid",
        )
        self.result_text.pack(fill=BOTH, expand=True, pady=(8, 0))

        self.external_slots_container = ttk.Frame(root, style="Toolbar.TFrame", padding=0)
        self.external_slots_canvas = tk.Canvas(
            self.external_slots_container,
            background="#eef1f4",
            borderwidth=0,
            highlightthickness=0,
        )
        self.external_slots_scrollbar = ttk.Scrollbar(
            self.external_slots_container,
            orient=VERTICAL,
            command=self.external_slots_canvas.yview,
        )
        self.external_slots_frame = ttk.Frame(self.external_slots_canvas, style="Toolbar.TFrame", padding=0)
        self.external_slots_window = self.external_slots_canvas.create_window(
            (0, 0),
            window=self.external_slots_frame,
            anchor="nw",
        )
        self.external_slots_canvas.configure(yscrollcommand=self.external_slots_scrollbar.set)
        self.external_slots_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.external_slots_scrollbar.pack(side=RIGHT, fill="y")
        self.external_slots_frame.bind("<Configure>", self._sync_external_slots_scrollregion)
        self.external_slots_canvas.bind("<Configure>", self._sync_external_slots_canvas_width)

        statusbar = ttk.Frame(root, style="Toolbar.TFrame", padding=(10, 8))
        statusbar.pack(fill="x", pady=(10, 0))
        self.progress = ttk.Progressbar(statusbar, mode="indeterminate", length=160)
        self.progress.pack(side=LEFT, padx=(0, 10))
        ttk.Label(statusbar, textvariable=self.status, style="Status.TLabel").pack(side=LEFT, fill="x", expand=True)

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="Vælg billede",
            filetypes=IMAGE_FILETYPES,
        )
        if path:
            self.set_image_path(path)

    def set_image_path(self, raw_path):
        try:
            path = Path(raw_path).expanduser().resolve()
        except Exception:
            messagebox.showerror("Fejl", "Kunne ikke læse billedstien.")
            return

        if not path.exists() or not path.is_file():
            messagebox.showerror("Fejl", f"Billedfilen blev ikke fundet:\n{path}")
            return

        self.image_path.set(str(path))
        self.analyze_button.configure(state=NORMAL)
        self.copy_button.configure(state=DISABLED)
        self.result_text.delete("1.0", END)
        self.status.set("Billede valgt. Tryk Analyser.")
        self.show_single_layout()
        self.load_preview(path)

    def show_single_layout(self):
        if hasattr(self, "external_slots_container"):
            self.external_slots_container.pack_forget()
        if hasattr(self, "single_body") and not self.single_body.winfo_ismapped():
            self.single_body.pack(fill=BOTH, expand=True)

    def _sync_external_slots_scrollregion(self, _event=None):
        if not hasattr(self, "external_slots_canvas"):
            return
        self.external_slots_canvas.configure(scrollregion=self.external_slots_canvas.bbox("all"))

    def _sync_external_slots_canvas_width(self, event=None):
        if not hasattr(self, "external_slots_canvas"):
            return
        width = max(1, event.width if event is not None else self.external_slots_canvas.winfo_width())
        self.external_slots_canvas.itemconfigure(self.external_slots_window, width=width)
        self._sync_external_slots_scrollregion()

    def show_external_slots_layout(self, slot_count):
        slot_count = max(1, min(8, int(slot_count or 1)))
        if slot_count <= 1:
            self.show_single_layout()
            return

        if hasattr(self, "single_body"):
            self.single_body.pack_forget()
        self.external_slots_container.pack(fill=BOTH, expand=True)
        for child in self.external_slots_frame.winfo_children():
            child.destroy()
        for col in range(4):
            self.external_slots_frame.columnconfigure(col, weight=0, uniform="", minsize=0)
        for row in range(8):
            self.external_slots_frame.rowconfigure(row, weight=0, uniform="", minsize=0)

        self.external_slots = []
        columns = 2 if slot_count > 1 else 1
        for col in range(columns):
            self.external_slots_frame.columnconfigure(col, weight=1, uniform="external_slots")
        rows = (slot_count + columns - 1) // columns
        for row in range(rows):
            self.external_slots_frame.rowconfigure(
                row,
                weight=1,
                uniform="external_slots",
                minsize=340 if rows > 1 else 0,
            )

        for index in range(slot_count):
            row = index // columns
            col = index % columns
            card = ttk.Frame(self.external_slots_frame, style="Panel.TFrame", padding=8)
            card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

            title = tk.StringVar(value=f"Slot {index + 1}: venter")
            ttk.Label(card, textvariable=title, style="Panel.TLabel").pack(anchor=W)

            preview = ttk.Label(
                card,
                text="Venter på billede",
                anchor="center",
                justify="center",
                style="Panel.TLabel",
            )
            preview.pack(fill=BOTH, expand=True, pady=(6, 6))

            text = ScrolledText(
                card,
                wrap="word",
                height=8,
                font=("Segoe UI", 9),
                padx=8,
                pady=8,
                borderwidth=1,
                relief="solid",
            )
            text.pack(fill=BOTH, expand=True)

            slot = {
                "title": title,
                "preview": preview,
                "text": text,
                "original": None,
                "photo": None,
            }
            self.external_slots.append(slot)
            preview.bind("<Configure>", lambda _event, i=index: self.render_external_slot_preview(i))
        self.after_idle(self._sync_external_slots_scrollregion)

    def load_preview(self, path):
        self.preview_original = None
        self.preview_photo = None

        if Image is None or ImageTk is None:
            self.preview_label.configure(text=path.name, image="")
            return

        try:
            with Image.open(path) as img:
                img.seek(0)
                self.preview_original = img.copy()
            self.render_preview()
        except Exception:
            self.preview_label.configure(
                text=f"Preview kunne ikke vises.\n{path.name}",
                image="",
            )

    def load_preview_bytes(self, image_bytes, filename=""):
        self.preview_original = None
        self.preview_photo = None
        display_name = str(filename or "Aktuelt billede").strip()

        if Image is None or ImageTk is None:
            self.preview_label.configure(text=display_name, image="")
            return

        try:
            with Image.open(BytesIO(image_bytes or b"")) as img:
                img.seek(0)
                self.preview_original = img.copy()
            self.render_preview()
        except Exception:
            self.preview_label.configure(
                text=f"Preview kunne ikke vises.\n{display_name}",
                image="",
            )

    def render_preview(self):
        if self.preview_original is None or ImageTk is None:
            return

        width = max(240, self.preview_label.winfo_width() - 24)
        height = max(240, self.preview_label.winfo_height() - 24)

        img = self.preview_original.copy()
        img.thumbnail((width, height))
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=self.preview_photo, text="")

    def update_external_slot(self, slot_index, filename="", status="", image_bytes=None, text=None, error=None):
        if slot_index is None or slot_index < 0 or slot_index >= len(self.external_slots):
            return
        slot = self.external_slots[slot_index]
        display_name = str(filename or f"Slot {slot_index + 1}").strip()
        status_text = str(status or "").strip()
        slot["title"].set(f"{slot_index + 1}: {display_name}" + (f" · {status_text}" if status_text else ""))

        if image_bytes is not None:
            slot["original"] = None
            slot["photo"] = None
            if Image is None or ImageTk is None:
                slot["preview"].configure(text=display_name, image="")
            else:
                try:
                    with Image.open(BytesIO(image_bytes or b"")) as img:
                        img.seek(0)
                        slot["original"] = img.copy()
                    self.render_external_slot_preview(slot_index)
                except Exception:
                    slot["preview"].configure(text=f"Preview kunne ikke vises.\n{display_name}", image="")

        if text is not None or error is not None:
            box = slot["text"]
            box.delete("1.0", END)
            if error is not None:
                box.insert("1.0", f"Fejl:\n{error}")
            else:
                box.insert("1.0", text or "")

    def render_external_slot_preview(self, slot_index):
        if ImageTk is None or slot_index < 0 or slot_index >= len(self.external_slots):
            return
        slot = self.external_slots[slot_index]
        original = slot.get("original")
        preview = slot.get("preview")
        if original is None or preview is None:
            return

        width = max(180, preview.winfo_width() - 16)
        height = max(160, preview.winfo_height() - 16)
        img = original.copy()
        img.thumbnail((width, height))
        slot["photo"] = ImageTk.PhotoImage(img)
        preview.configure(image=slot["photo"], text="")

    def set_busy(self, busy):
        self.busy = busy
        interactive_busy = bool(busy or self.external_running)
        state = DISABLED if interactive_busy else NORMAL
        self.choose_button.configure(state=state)
        self.analyze_button.configure(state=state if self.image_path.get() and not interactive_busy else DISABLED)
        if hasattr(self, "external_start_button"):
            self.external_start_button.configure(state=DISABLED if busy or self.external_running else NORMAL)
        if hasattr(self, "external_stop_button"):
            self.external_stop_button.configure(state=NORMAL if self.external_running else DISABLED)
        if busy:
            self.copy_button.configure(state=DISABLED)

        if busy:
            self.progress.stop()
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
        elif not self.external_running:
            self.progress.stop()

    def start_analysis(self):
        if self.busy:
            return

        raw_path = self.image_path.get().strip()
        if not raw_path:
            messagebox.showwarning("Mangler billede", "Vælg et billede først.")
            return

        self.result_text.delete("1.0", END)
        self.status.set("Starter analyse...")
        self.set_busy(True)

        worker = threading.Thread(
            target=self._analysis_worker,
            args=(Path(raw_path), self.model.get().strip(), self.ollama_url.get().strip()),
            daemon=True,
        )
        worker.start()

    def _analysis_worker(self, path, model, ollama_url):
        try:
            self.after(0, self.status.set, "Tjekker Ollama og model...")
            core.MODEL = model or core.DEFAULT_VISION_MODEL
            core.OLLAMA_BASE_URL = core.normaliser_ollama_base_url(ollama_url or "http://localhost:11434")
            self.after(0, self.ollama_url.set, core.OLLAMA_BASE_URL)
            self.after(0, self.model.set, core.MODEL)

            text, _caption, _tags, _parsed = self.analyze_image_path(path)

            self.after(0, self.finish_analysis, text, None)
        except Exception as exc:
            details = str(exc).strip() or traceback.format_exc()
            self.after(0, self.finish_analysis, "", details)

    def analyze_image_path(self, path, check_model=True):
        if check_model:
            core.tjek_model_kan_laese_billeder(core.MODEL)

        self.after(0, self.status.set, "Læser billede...")
        image_b64 = core.laes_billede_base64(path)

        self.after(0, self.status.set, "Sender billede til Ollama...")
        raw = core.spoerg_ollama_om_billede(image_b64)

        try:
            parsed = core.udtraek_json(raw)
            parsed = core.forbedr_personfokus(parsed)
            text = self.format_result(parsed)
            caption, tags = core.parsed_to_caption_tags(parsed)
            return text, caption, tags, parsed
        except Exception:
            text = "Modellen returnerede ikke gyldig JSON. Råt svar:\n\n" + raw
            return text, raw, [], None

    def finish_analysis(self, text, error):
        self.set_busy(False)

        if error:
            self.status.set("Analysen fejlede.")
            self.copy_button.configure(state=DISABLED)
            messagebox.showerror("Fejl", error)
            return

        self.result_text.delete("1.0", END)
        self.result_text.insert("1.0", text)
        self.copy_button.configure(state=NORMAL)
        self.status.set("Færdig.")

    def start_external_worker(self):
        if self.busy or self.external_running:
            return

        try:
            server, token = self.parse_connection_link(self.connection_link.get())
        except Exception as exc:
            messagebox.showwarning("Ugyldigt forbindelseslink", str(exc))
            return

        if not server or not token:
            messagebox.showwarning("Mangler forbindelse", "Indsæt forbindelseslinket fra FjordLens først.")
            return
        self.server_url.set(server)
        self.api_token.set(token)

        self.external_running = True
        self.external_run_total = 0
        self.external_processed = 0
        parallel_count = 1
        self.show_external_slots_layout(parallel_count)
        self.external_counts_text.set("")
        self.external_stop_event.clear()
        self.set_busy(False)
        self.status.set("Forbinder til ekstern FjordLens-kø...")

        worker = threading.Thread(
            target=self._external_worker,
            args=(server, token, self.model.get().strip(), self.ollama_url.get().strip(), parallel_count),
            daemon=True,
        )
        worker.start()

    def stop_external_worker(self):
        self.external_stop_event.set()
        self.status.set("Stopper efter nuværende billede(r)...")

    def _server_headers(self, token):
        return {
            "Authorization": f"Bearer {token}",
            "X-Worker-Name": "AI Billedbeskriver Windows",
        }

    def parse_connection_link(self, raw):
        text = str(raw or "").strip().strip('"').strip("'")
        if not text:
            raise ValueError("Indsæt forbindelseslinket fra FjordLens først.")

        if "://" not in text:
            text = f"http://{text}"

        parsed = urlparse(text)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Forbindelseslinket skal være et link fra FjordLens.")

        query = parse_qs(parsed.query)
        fragment = parse_qs(parsed.fragment)
        token = (
            (query.get("token") or query.get("api_token") or query.get("fjordlens_token") or [""])[0]
            or (fragment.get("token") or fragment.get("api_token") or fragment.get("fjordlens_token") or [""])[0]
        ).strip()
        if not token:
            raise ValueError("Forbindelseslinket mangler token.")

        path = parsed.path or ""
        marker = "/api/ai/describe/external"
        if marker in path:
            base_path = path.split(marker, 1)[0]
        else:
            base_path = path.rstrip("/")
        server = urlunparse((parsed.scheme, parsed.netloc, base_path, "", "", "")).rstrip("/")
        if not server:
            raise ValueError("Kunne ikke læse serveradressen fra forbindelseslinket.")
        return server, token

    def _as_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _external_counts_from_payload(self, payload):
        data = payload if isinstance(payload, dict) else {}
        return {
            key: self._as_int(data.get(key), 0)
            for key in ("total", "pending", "described", "ready", "in_progress", "unavailable")
            if key in data
        }

    def update_external_progress(self, processed, run_total, counts=None, message=""):
        counts = counts if isinstance(counts, dict) else {}
        processed = max(0, self._as_int(processed, 0))
        ready = self._as_int(counts.get("ready", counts.get("pending", 0)), 0)
        pending = self._as_int(counts.get("pending", ready), ready)
        described = self._as_int(counts.get("described", 0), 0)
        total = self._as_int(counts.get("total", 0), 0)
        in_progress = self._as_int(counts.get("in_progress", 0), 0)
        unavailable = self._as_int(counts.get("unavailable", 0), 0)
        run_total = max(self._as_int(run_total, 0), processed)

        self.external_processed = processed
        self.external_run_total = run_total

        self.progress.stop()
        self.progress.configure(mode="determinate", maximum=max(1, run_total), value=min(processed, max(1, run_total)))

        parts = [
            f"Klar til analyse: {ready}",
            f"Behandlet i denne kørsel: {processed}/{run_total}",
        ]
        if total:
            parts.append(f"Beskrivelser i valgte mapper: {described}/{total}")
        if pending:
            parts.append(f"Mangler: {pending}")
        if in_progress:
            parts.append(f"I gang: {in_progress}")
        if unavailable:
            parts.append(f"Utilgængelige filer: {unavailable}")
        self.external_counts_text.set(" · ".join(parts))

        if message:
            self.status.set(message)

    def _external_worker_sequential(self, server, token, model, ollama_url):
        processed = 0
        run_total = 0
        try:
            core.MODEL = model or core.DEFAULT_VISION_MODEL
            core.OLLAMA_BASE_URL = core.normaliser_ollama_base_url(ollama_url or "http://localhost:11434")
            self.after(0, self.model.set, core.MODEL)
            self.after(0, self.ollama_url.set, core.OLLAMA_BASE_URL)

            ping_url = urljoin(server + "/", "api/ai/describe/external/ping")
            ping = requests.get(ping_url, headers=self._server_headers(token), timeout=20)
            if not ping.ok:
                raise RuntimeError(f"Server/token blev afvist ({ping.status_code}).")
            try:
                ping_data = ping.json() or {}
            except Exception:
                ping_data = {}
            ping_counts = self._external_counts_from_payload(ping_data)
            run_total = max(ping_counts.get("ready", ping_counts.get("pending", 0)), 0)
            self.after(
                0,
                self.update_external_progress,
                processed,
                run_total,
                ping_counts,
                f"Forbundet. Klar til analyse: {run_total}.",
            )

            while not self.external_stop_event.is_set():
                next_url = urljoin(server + "/", "api/ai/describe/external/next?worker=windows")
                r = requests.get(next_url, headers=self._server_headers(token), timeout=30)
                if not r.ok:
                    raise RuntimeError(f"Kunne ikke hente næste billede ({r.status_code}): {r.text[:200]}")

                data = r.json() or {}
                counts = self._external_counts_from_payload(data)
                item = data.get("item")
                if not item:
                    ready = counts.get("ready", counts.get("pending", 0))
                    self.after(
                        0,
                        self.update_external_progress,
                        processed,
                        run_total,
                        counts,
                        f"Ingen ledige billeder i ekstern kø. Klar til analyse: {ready}.",
                    )
                    break

                photo_id = int(item.get("photo_id") or 0)
                filename = str(item.get("filename") or f"photo-{photo_id}.jpg")
                image_url = urljoin(server + "/", str(item.get("image_url") or ""))
                run_total = max(run_total, processed + 1 + counts.get("ready", 0))
                current_number = min(processed + 1, max(1, run_total))
                self.after(
                    0,
                    self.update_external_progress,
                    processed,
                    run_total,
                    counts,
                    f"Henter billede {current_number}/{run_total}: {filename}",
                )

                img_response = requests.get(image_url, headers=self._server_headers(token), timeout=120)
                if not img_response.ok:
                    raise RuntimeError(f"Kunne ikke hente billedet ({img_response.status_code}).")
                image_bytes = img_response.content
                self.after(0, self.load_preview_bytes, image_bytes, filename)

                suffix = Path(filename).suffix or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = Path(tmp.name)

                try:
                    self.after(
                        0,
                        self.update_external_progress,
                        processed,
                        run_total,
                        counts,
                        f"Analyserer billede {current_number}/{run_total}: {filename}",
                    )
                    text, caption, tags, _parsed = self.analyze_image_path(tmp_path)
                finally:
                    try:
                        tmp_path.unlink(missing_ok=True)
                    except Exception:
                        pass

                result_url = urljoin(server + "/", "api/ai/describe/external/result")
                payload = {
                    "photo_id": photo_id,
                    "caption": caption or text,
                    "tags": tags,
                    "worker": "AI Billedbeskriver Windows",
                }
                post = requests.post(
                    result_url,
                    json=payload,
                    headers=self._server_headers(token),
                    timeout=60,
                )
                if not post.ok:
                    raise RuntimeError(f"Serveren afviste resultatet ({post.status_code}): {post.text[:200]}")

                processed += 1
                try:
                    post_counts = self._external_counts_from_payload(post.json() or {})
                except Exception:
                    post_counts = counts
                run_total = max(run_total, processed + post_counts.get("ready", 0))
                self.after(0, self.result_text.delete, "1.0", END)
                self.after(0, self.result_text.insert, "1.0", text)
                self.after(
                    0,
                    self.update_external_progress,
                    processed,
                    run_total,
                    post_counts,
                    f"Sendt tilbage til serveren. Behandlet: {processed}/{run_total}.",
                )

            self.after(0, self._external_worker_finished, None, processed, run_total)
        except Exception as exc:
            self.after(0, self._external_worker_finished, str(exc), processed, run_total)

    def _fetch_external_next(self, server, token):
        next_url = urljoin(server + "/", "api/ai/describe/external/next?worker=windows")
        response = requests.get(next_url, headers=self._server_headers(token), timeout=30)
        if not response.ok:
            raise RuntimeError(f"Kunne ikke hente næste billede ({response.status_code}): {response.text[:200]}")
        data = response.json() or {}
        return data, self._external_counts_from_payload(data), data.get("item")

    def _post_external_error(self, server, token, photo_id, error_message):
        result_url = urljoin(server + "/", "api/ai/describe/external/result")
        try:
            requests.post(
                result_url,
                json={
                    "photo_id": int(photo_id or 0),
                    "error": str(error_message or "Analyse fejlede")[:500],
                    "worker": "AI Billedbeskriver Windows",
                },
                headers=self._server_headers(token),
                timeout=30,
            )
        except Exception:
            pass

    def _process_external_item(self, server, token, item, counts, display_number, run_total, processed_snapshot, slot_index=None):
        photo_id = int(item.get("photo_id") or 0)
        filename = str(item.get("filename") or f"photo-{photo_id}.jpg")
        image_url = urljoin(server + "/", str(item.get("image_url") or ""))

        self.after(
            0,
            self.update_external_progress,
            processed_snapshot,
            run_total,
            counts,
            f"Henter billede {display_number}/{run_total}: {filename}",
        )

        img_response = requests.get(image_url, headers=self._server_headers(token), timeout=120)
        if not img_response.ok:
            raise RuntimeError(f"Kunne ikke hente billedet ({img_response.status_code}).")
        image_bytes = img_response.content
        if slot_index is None:
            self.after(0, self.load_preview_bytes, image_bytes, filename)
        else:
            self.after(0, self.update_external_slot, slot_index, filename, "hentet", image_bytes, None, None)

        suffix = Path(filename).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(image_bytes)
            tmp_path = Path(tmp.name)

        try:
            try:
                self.after(
                    0,
                    self.update_external_progress,
                    processed_snapshot,
                    run_total,
                    counts,
                    f"Analyserer billede {display_number}/{run_total}: {filename}",
                )
                if slot_index is not None:
                    self.after(0, self.update_external_slot, slot_index, filename, "analyserer", None, None, None)
                text, caption, tags, _parsed = self.analyze_image_path(tmp_path, check_model=False)
            except Exception as exc:
                message = str(exc).strip() or traceback.format_exc()
                if "500 Server Error" in message:
                    if slot_index is not None:
                        self.after(0, self.update_external_slot, slot_index, filename, "retryer efter Ollama-fejl", None, None, None)
                    with self.ollama_retry_lock:
                        text, caption, tags, _parsed = self.analyze_image_path(tmp_path, check_model=False)
                else:
                    raise
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

        result_url = urljoin(server + "/", "api/ai/describe/external/result")
        payload = {
            "photo_id": photo_id,
            "caption": caption or text,
            "tags": tags,
            "worker": "AI Billedbeskriver Windows",
        }
        post = requests.post(
            result_url,
            json=payload,
            headers=self._server_headers(token),
            timeout=60,
        )
        if not post.ok:
            raise RuntimeError(f"Serveren afviste resultatet ({post.status_code}): {post.text[:200]}")

        if slot_index is not None:
            self.after(0, self.update_external_slot, slot_index, filename, "sendt", None, text, None)

        try:
            post_counts = self._external_counts_from_payload(post.json() or {})
        except Exception:
            post_counts = counts

        return {
            "filename": filename,
            "text": text,
            "counts": post_counts,
        }

    def _external_worker(self, server, token, model, ollama_url, parallel_count=1):
        processed = 0
        run_total = 0
        try:
            parallel_count = 1
            core.MODEL = model or core.DEFAULT_VISION_MODEL
            core.OLLAMA_BASE_URL = core.normaliser_ollama_base_url(ollama_url or "http://localhost:11434")
            self.after(0, self.model.set, core.MODEL)
            self.after(0, self.ollama_url.set, core.OLLAMA_BASE_URL)
            self.after(0, self.status.set, "Tjekker Ollama og model...")
            core.tjek_model_kan_laese_billeder(core.MODEL)

            ping_url = urljoin(server + "/", "api/ai/describe/external/ping")
            ping = requests.get(ping_url, headers=self._server_headers(token), timeout=20)
            if not ping.ok:
                raise RuntimeError(f"Server/token blev afvist ({ping.status_code}).")
            try:
                ping_data = ping.json() or {}
            except Exception:
                ping_data = {}
            ping_counts = self._external_counts_from_payload(ping_data)
            run_total = max(ping_counts.get("ready", ping_counts.get("pending", 0)), 0)
            self.after(
                0,
                self.update_external_progress,
                processed,
                run_total,
                ping_counts,
                f"Forbundet. Klar til analyse: {run_total}. Kører 1 ad gangen.",
            )

            active = {}
            free_slots = list(range(parallel_count)) if parallel_count > 1 else [None]
            no_more_items = False
            with ThreadPoolExecutor(max_workers=parallel_count) as executor:
                while True:
                    while (
                        not self.external_stop_event.is_set()
                        and not no_more_items
                        and len(active) < parallel_count
                        and free_slots
                    ):
                        _data, counts, item = self._fetch_external_next(server, token)
                        if not item:
                            ready = counts.get("ready", counts.get("pending", 0))
                            no_more_items = True
                            message = (
                                f"Ingen flere ledige billeder. Afslutter de {len(active)} igangværende."
                                if active
                                else f"Ingen ledige billeder i ekstern kø. Klar til analyse: {ready}."
                            )
                            self.after(0, self.update_external_progress, processed, run_total, counts, message)
                            break

                        run_total = max(run_total, processed + len(active) + 1 + counts.get("ready", 0))
                        display_number = min(processed + len(active) + 1, max(1, run_total))
                        slot_index = free_slots.pop(0)
                        if slot_index is not None:
                            filename = str(item.get("filename") or f"photo-{int(item.get('photo_id') or 0)}.jpg")
                            self.after(0, self.update_external_slot, slot_index, filename, "venter", None, "", None)
                        future = executor.submit(
                            self._process_external_item,
                            server,
                            token,
                            item,
                            counts,
                            display_number,
                            run_total,
                            processed,
                            slot_index,
                        )
                        active[future] = {"item": item, "slot": slot_index}

                    if not active:
                        break

                    done, _pending = wait(active.keys(), timeout=0.2, return_when=FIRST_COMPLETED)
                    if not done:
                        continue

                    for future in done:
                        meta = active.pop(future, {}) or {}
                        item = meta.get("item") or {}
                        slot_index = meta.get("slot")
                        try:
                            result = future.result()
                        except Exception as exc:
                            error = str(exc).strip() or traceback.format_exc()
                            filename = str(item.get("filename") or f"photo-{int(item.get('photo_id') or 0)}.jpg")
                            self._post_external_error(server, token, int(item.get("photo_id") or 0), error)
                            if slot_index is not None:
                                self.after(0, self.update_external_slot, slot_index, filename, "fejl", None, None, error)
                            result = {"filename": filename, "text": "", "counts": {}, "error": error}
                        processed += 1
                        post_counts = result.get("counts") or {}
                        run_total = max(run_total, processed + len(active) + post_counts.get("ready", 0))
                        text = result.get("text") or ""
                        filename = result.get("filename") or "billede"
                        if slot_index is None:
                            self.after(0, self.result_text.delete, "1.0", END)
                            self.after(0, self.result_text.insert, "1.0", text or result.get("error") or "")
                        free_slots.append(slot_index)
                        self.after(
                            0,
                            self.update_external_progress,
                            processed,
                            run_total,
                            post_counts,
                            f"Sendt tilbage: {filename}. Behandlet: {processed}/{run_total}. I gang: {len(active)}.",
                        )

                    if self.external_stop_event.is_set() and not active:
                        break

            self.after(0, self._external_worker_finished, None, processed, run_total)
        except Exception as exc:
            self.after(0, self._external_worker_finished, str(exc), processed, run_total)

    def _external_worker_finished(self, error, processed, run_total):
        self.external_running = False
        self.external_stop_event.clear()
        self.set_busy(False)
        if error:
            self.status.set("Ekstern behandling fejlede.")
            messagebox.showerror("Ekstern behandling", error)
            return
        self.status.set(f"Ekstern behandling færdig. Behandlet: {processed}/{run_total}.")

    def format_result(self, parsed):
        mennesker = parsed.get("mennesker") if isinstance(parsed, dict) else {}
        if not isinstance(mennesker, dict):
            mennesker = {}
        personer = mennesker.get("personer")
        if not isinstance(personer, list):
            personer = []

        lines = [
            f"Kort: {core.as_text(parsed.get('kort_beskrivelse'))}",
            "",
            f"Hvad sker der: {core.as_text(parsed.get('hvad_sker_der'))}",
            "",
            "Mennesker:",
            f"- Antal: {core.as_text(mennesker.get('antal'))}",
            f"- Hvad laver de: {core.as_text(mennesker.get('hvad_laver_de'))}",
            f"- Køn/alder: {core.as_text(mennesker.get('koen_og_alder'))}",
            f"- Pige/dreng: {core.as_text(mennesker.get('pige_dreng_vurdering'))}",
            f"- Søgeord: {core.as_search_words(mennesker.get('soegeord_personer'))}",
        ]

        for index, person in enumerate(personer, start=1):
            if not isinstance(person, dict):
                continue

            label = core.as_text(person.get("label"))
            if label == "-":
                label = f"Person {index}"

            lines.extend(
                [
                    "",
                    f"{label}:",
                    f"- Rolle: {core.as_text(person.get('rolle_i_billedet'))}",
                    f"- Personkategori: {core.person_kategori(person)}",
                    f"- Visuel kønsvurdering: {core.as_text(person.get('visuel_koensvurdering'))}",
                    f"- Beskrivelse: {core.as_text(person.get('beskrivelse'))}",
                    f"- Søgeord: {core.as_search_words(person.get('soegeord'))}",
                ]
            )

        lines.extend(
            [
                "",
                f"Samlede søgeord: {core.as_search_words(parsed.get('samlede_soegeord'))}",
                "",
                f"Objekter og miljø: {core.as_text(parsed.get('objekter_og_miljoe'))}",
                "",
                f"Usikkerheder: {core.as_text(parsed.get('usikkerheder'))}",
            ]
        )

        return "\n".join(lines)

    def copy_result(self):
        text = self.result_text.get("1.0", END).strip()
        if not text:
            return

        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.set("Teksten er kopieret.")


if __name__ == "__main__":
    app = BilledbeskriverApp()
    app.mainloop()
