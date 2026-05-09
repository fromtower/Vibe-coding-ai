from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from database import get_notice_count, save_to_db, search_notices
from models import process_to_documents
from scraper import fetch_ice_notices


class NoticeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("영남대 정보통신공학과 공지사항 검색")
        self.geometry("960x580")
        self.resizable(True, True)
        self._results: list[dict] = []
        self._setup_styles()
        self._build_ui()
        self._refresh_count()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")  # macOS 네이티브 테마 우회
        style.configure("Search.TButton", background="#4CAF50", foreground="black",
                        font=("", 11), padding=(10, 4))
        style.map("Search.TButton", background=[("active", "#388E3C")])
        style.configure("Crawl.TButton", background="#1976D2", foreground="black",
                        font=("", 11), padding=(10, 4))
        style.map("Crawl.TButton", background=[("active", "#1565C0")])
        style.configure("Treeview", background="#1e1e1e", foreground="white",
                        fieldbackground="#1e1e1e", rowheight=24)
        style.configure("Treeview.Heading", background="#2d2d2d", foreground="white")
        style.map("Treeview", background=[("selected", "#0057b8")])

    # ── UI 구성 ───────────────────────────────────────────────
    def _build_ui(self):
        # 상단 컨트롤
        top = tk.Frame(self, padx=12, pady=10)
        top.pack(fill=tk.X)

        tk.Label(top, text="검색어", font=("", 11)).pack(side=tk.LEFT)
        self.query_var = tk.StringVar()
        entry = tk.Entry(top, textvariable=self.query_var, width=28, font=("", 11))
        entry.pack(side=tk.LEFT, padx=(6, 0))
        entry.bind("<Return>", lambda _: self._search())
        entry.focus()

        tk.Label(top, text="카테고리", font=("", 11)).pack(side=tk.LEFT, padx=(14, 4))
        self.cat_var = tk.StringVar(value="전체")
        ttk.Combobox(
            top,
            textvariable=self.cat_var,
            values=["전체", "장학", "학사", "일반", "취업"],
            width=7,
            state="readonly",
            font=("", 11),
        ).pack(side=tk.LEFT)

        ttk.Button(
            top, text="검색", command=self._search, style="Search.TButton",
        ).pack(side=tk.LEFT, padx=(10, 4))

        ttk.Button(
            top, text="공지 수집", command=self._crawl, style="Crawl.TButton",
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar()
        tk.Label(top, textvariable=self.status_var, fg="#666", font=("", 10)).pack(
            side=tk.RIGHT
        )

        # 결과 테이블
        mid = tk.Frame(self, padx=12)
        mid.pack(fill=tk.BOTH, expand=True)

        cols = ("카테고리", "제목", "날짜")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("카테고리", text="카테고리")
        self.tree.heading("제목", text="제목")
        self.tree.heading("날짜", text="날짜")
        self.tree.column("카테고리", width=80, anchor="center")
        self.tree.column("제목", width=720)
        self.tree.column("날짜", width=100, anchor="center")

        vsb = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # URL 바
        bot = tk.Frame(self, padx=12, pady=8)
        bot.pack(fill=tk.X)
        tk.Label(bot, text="URL", font=("", 10), fg="#555").pack(side=tk.LEFT)
        self.url_var = tk.StringVar()
        tk.Entry(
            bot, textvariable=self.url_var, state="readonly",
            fg="#1565C0", font=("", 10),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))

        tk.Button(
            bot, text="복사", font=("", 10),
            command=self._copy_url,
        ).pack(side=tk.LEFT)

    # ── 동작 ──────────────────────────────────────────────────
    def _search(self):
        query = self.query_var.get().strip()
        if not query:
            return
        cat = self.cat_var.get()
        category = None if cat == "전체" else cat

        self._results = search_notices(query, category=category)
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self._results:
            self.tree.insert("", tk.END, values=(r["category"], r["title"], r["date"]))

        count = len(self._results)
        self.status_var.set(f"검색 결과 {count}건")

    def _on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        self.url_var.set(self._results[idx]["url"])

    def _crawl(self):
        self.status_var.set("공지 수집 중...")
        self.update()

        def task():
            try:
                raw = []
                for page in range(4):
                    raw += fetch_ice_notices(offset=page * 10)
                docs = process_to_documents(raw)
                inserted = save_to_db(docs)
                total = get_notice_count()
                self.after(0, lambda: self.status_var.set(
                    f"수집 완료 — 신규 {inserted}건 / 전체 {total}건"
                ))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("수집 오류", str(exc)))

        threading.Thread(target=task, daemon=True).start()

    def _copy_url(self):
        url = self.url_var.get()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.status_var.set("URL 복사됨!")

    def _refresh_count(self):
        count = get_notice_count()
        self.status_var.set(f"DB {count}건 저장됨")
