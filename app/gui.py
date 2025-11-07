# app/gui.py
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import asyncio
from loguru import logger
import sys
import io


class LogCapture(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, s):
        super().write(s)
        if s.strip():
            self.text_widget.insert(tk.END, s)
            self.text_widget.see(tk.END)


class ParserGUI:
    def __init__(self, settings):
        self.settings = settings
        self.root = tk.Tk()
        self.root.title("Reestr Parser Monitor")
        self.root.geometry("800x600")

        self.status_label = tk.Label(self.root, text="Status: Idle", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.stats_label = tk.Label(self.root, text="Stats: Codes: 0, Names: 0, Files: 0, Errors: 0",
                                    font=("Arial", 10))
        self.stats_label.pack()

        self.log_text = scrolledtext.ScrolledText(self.root, state='normal', height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.start_button = tk.Button(self.root, text="Start", command=self.start_parser)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_parser, state='disabled')
        self.stop_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.is_running = False
        self.parser_thread = None

        # Redirect logs to GUI
        self.log_capture = LogCapture(self.log_text)
        logger.remove()  # Убираем стандартный вывод
        logger.add(self.log_capture, format="{time} {level} {message}", level="INFO")

    def start_parser(self):
        if self.is_running:
            return
        self.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Status: Running...")
        self.parser_thread = Thread(target=self._run_parser)
        self.parser_thread.daemon = True
        self.parser_thread.start()

    def stop_parser(self):
        self.is_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Status: Stopping...")
        logger.info("Stopping parser...")

    def _run_parser(self):
        # Импортируем main_loop внутри функции, чтобы избежать циклической зависимости
        from app.main import main_loop
        try:
            asyncio.run(main_loop(self.settings, self))
        except Exception as e:
            logger.error(f"Parser crashed: {e}")
        finally:
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_label.config(text="Status: Idle")

    def update_stats(self, codes=0, names=0, files=0, errors=0):
        self.stats_label.config(text=f"Stats: Codes: {codes}, Names: {names}, Files: {files}, Errors: {errors}")

    def run(self):
        self.root.mainloop()
