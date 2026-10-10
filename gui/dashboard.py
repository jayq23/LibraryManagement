import logging
import math
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from ai_agent.chatbot import Chatbot
from gui.book_catalog_view import BookCatalogView
from gui.borrow_return_view import BorrowReturnView
from gui.category_view import CategoryView
from gui.chatbot_window import ChatbotView
from gui.member_view import MemberView
from gui.reports_view import ReportsView
from gui.reservation_view import ReservationView
from managers.report_manager import ReportManager

logger = logging.getLogger(__name__)

SYNC_INTERVAL_MS = 5000   # how often the dashboard re-reads the database
CHART_MONTHS = 6          # how many recent months the charts show

CARD_BG = "#1B252E"
BORDER = "#303D47"
GRID = "#2B3943"
TEXT = "#E8EDF0"
SOFT_TEXT = "#C5D0D6"
MUTED = "#7F909A"
TEAL, TEAL_DIM = "#2A9D9A", "#1E6E6C"
CORAL, CORAL_DIM = "#D17A67", "#8F5548"

METRIC_KEYS = ("total_books", "active_loans", "overdue", "members")


def _value(row, key, default=None):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def normalize_activity(rows) -> list[dict]:
    """Cleans monthly_activity() rows: safe numbers, short month labels, last N months only."""
    cleaned = []
    for row in rows or []:
        label = str(_value(row, "label", "") or "")
        try:
            loans = int(float(_value(row, "loans", 0) or 0))
            fines = float(_value(row, "fines", 0) or 0)
        except (TypeError, ValueError):
            loans, fines = 0, 0.0
        cleaned.append({
            "label": label.split()[0][:3] if label else "",
            "loans": loans,
            "fines": fines,
        })
    return cleaned[-CHART_MONTHS:]


def nice_axis(max_value: float, intervals: int = 4) -> tuple[float, float]:
    """Returns (step, axis_max) so the gridlines land on clean numbers."""
    if max_value <= 0:
        return 1, intervals
    magnitude = 10 ** math.floor(math.log10(max_value / intervals))
    for multiple in (1, 2, 5, 10):
        step = max(multiple * magnitude, 1)
        if step * intervals >= max_value:
            return step, step * intervals
    return max_value / intervals, max_value


def peso(value: float) -> str:
    value = float(value)
    return f"₱{value:,.0f}" if value.is_integer() else f"₱{value:,.2f}"


# ----------------------------------------------------------------------
# Chart widget
# ----------------------------------------------------------------------
class BarChart(ctk.CTkFrame):
    """Card with a big total, a caption, and a clean monthly bar chart."""

    def __init__(self, master, title, caption, color, dim_color, label_format, axis_format):
        super().__init__(master, fg_color=CARD_BG, border_color=BORDER, border_width=1, corner_radius=10)
        self.color = color
        self.dim_color = dim_color
        self.label_format = label_format
        self.axis_format = axis_format
        self.caption = caption
        self.points: list[tuple[str, float]] = []

        ctk.CTkLabel(
            self, text=title.upper(), text_color="#9AA7B0",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 0))
        self.total_label = ctk.CTkLabel(
            self, text="-", text_color=color, font=ctk.CTkFont(size=26, weight="bold"),
        )
        self.total_label.pack(anchor="w", padx=16, pady=(2, 0))
        self.caption_label = ctk.CTkLabel(self, text=caption, text_color=MUTED)
        self.caption_label.pack(anchor="w", padx=16, pady=(0, 2))

        self.canvas = ctk.CTkCanvas(self, height=180, bg=CARD_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.canvas.bind("<Configure>", lambda _event: self.draw())

    def set_data(self, points: list[tuple[str, float]], total_text: str) -> None:
        self.points = points
        self.total_label.configure(text=total_text)
        self.draw()

    @staticmethod
    def _bar(canvas, x0, y0, x1, y1, fill, radius=6):
        """Bar with rounded top corners and a flat bottom."""
        height = y1 - y0
        r = min(radius, (x1 - x0) / 2)
        if height <= r * 2:
            canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")
            return
        canvas.create_oval(x0, y0, x0 + 2 * r, y0 + 2 * r, fill=fill, outline="")
        canvas.create_oval(x1 - 2 * r, y0, x1, y0 + 2 * r, fill=fill, outline="")
        canvas.create_rectangle(x0 + r, y0, x1 - r, y0 + r + 1, fill=fill, outline="")
        canvas.create_rectangle(x0, y0 + r, x1, y1, fill=fill, outline="")

    def draw(self) -> None:
        canvas = self.canvas
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 150)

        if not self.points:
            canvas.create_text(width / 2, height / 2, text="No activity yet", fill=MUTED, font=("Helvetica", 11))
            return

        left, right, top, bottom = 52, 12, 22, 26
        plot_w = width - left - right
        plot_h = height - top - bottom
        base_y = top + plot_h

        step, axis_max = nice_axis(max(v for _, v in self.points))

        # Gridlines + y-axis labels
        for i in range(5):
            value = step * i
            y = base_y - plot_h * value / axis_max
            if i == 0:
                canvas.create_line(left, y, width - right, y, fill=BORDER)
            else:
                canvas.create_line(left, y, width - right, y, fill=GRID, dash=(2, 4))
            canvas.create_text(left - 8, y, text=self.axis_format(value), fill=MUTED, anchor="e", font=("Helvetica", 9))

        slot = plot_w / len(self.points)
        bar_w = min(slot * 0.5, 40)
        last = len(self.points) - 1

        for index, (label, value) in enumerate(self.points):
            is_current = index == last
            x = left + slot * (index + 0.5)
            fill = self.color if is_current else self.dim_color
            bar_h = plot_h * value / axis_max

            if value > 0:
                self._bar(canvas, x - bar_w / 2, base_y - bar_h, x + bar_w / 2, base_y, fill)
                canvas.create_text(
                    x, base_y - bar_h - 10, text=self.label_format(value),
                    fill=TEXT if is_current else SOFT_TEXT, font=("Helvetica", 9, "bold"),
                )
            else:
                canvas.create_line(x - bar_w / 2, base_y - 1, x + bar_w / 2, base_y - 1, fill=self.dim_color, width=2)

            canvas.create_text(
                x, base_y + 14, text=label,
                fill=TEXT if is_current else MUTED,
                font=("Helvetica", 9, "bold" if is_current else "normal"),
            )


# ----------------------------------------------------------------------
# Dashboard window
# ----------------------------------------------------------------------
class Dashboard(ctk.CTkToplevel):
    def __init__(self, login_window: ctk.CTk, user) -> None:
        super().__init__(login_window)
        self.login_window = login_window
        self.title("Viva La Vida")
        self.geometry("1040x680")
        self.minsize(820, 560)
        self.configure(fg_color="#111820")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.user = user
        self.username = user.username
        self.nav_buttons = {}
        self.active_panel = "Dashboard"
        self.active_view = None
        self.refresh_job = None
        self.metric_labels = {}
        self.loans_chart = None
        self.fines_chart = None
        self.subtitle_label = None
        self.last_sync = None
        self._snapshot = None

        # Persistent Chatbot session habang nakabukas ang Dashboard
        self.chatbot_instance = Chatbot()

        # Sidebar
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#18232D")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(24, 28))

        logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
        img = Image.open(logo_path)
        self.logo = ctk.CTkImage(light_image=img, dark_image=img, size=(46, 46))
        ctk.CTkLabel(brand, image=self.logo, text="").pack(side="left", padx=(0, 11))
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            brand_text, text="VIVA LA VIDA", text_color="#E8EDF0",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_text, text="LIBRARY DESK", text_color="#7F909A",
            font=ctk.CTkFont(size=9, weight="bold")
        ).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(sidebar, height=1, fg_color="#2B3943").pack(fill="x", padx=18, pady=(0, 18))

        for panel_name in ("Dashboard", "Members", "Books", "Categories", "Borrow / Return", "Reservations", "Reports", "Viva Library Assistant"):
            button = ctk.CTkButton(
                sidebar, text=panel_name, anchor="w",
                command=lambda name=panel_name: self.show_panel(name),
                height=42, corner_radius=7, fg_color="transparent",
                hover_color="#253540", text_color="#C5D0D6",
            )
            button.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[panel_name] = button

        ctk.CTkButton(
            sidebar, text="LOGOUT", anchor="center", command=self.close,
            height=42, corner_radius=7, fg_color="#253540", hover_color="#2A9D9A",
        ).pack(side="bottom", fill="x", padx=14, pady=22)

        # Main content
        content = ctk.CTkFrame(self, fg_color="#111820", corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew", padx=42, pady=36)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.page_content = ctk.CTkFrame(content, fg_color="transparent")
        self.page_content.grid(row=0, column=0, sticky="nsew")
        self.page_content.grid_columnconfigure(0, weight=1)
        self.page_content.grid_rowconfigure(2, weight=1)
        self.page_content.grid_rowconfigure(3, weight=0)

        self.show_panel("Dashboard")
        self.refresh_job = self.after(SYNC_INTERVAL_MS, self.refresh_live_data)

    def greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning"
        if hour < 18:
            return "Good afternoon"
        return "Good evening"

    def show_panel(self, panel_name: str) -> None:
        self.active_panel = panel_name
        self.active_view = None
        self.page_content.grid_rowconfigure(2, weight=1)
        self.page_content.grid_rowconfigure(3, weight=1 if panel_name == "Dashboard" else 0)

        for name, button in self.nav_buttons.items():
            button.configure(
                fg_color="#2A9D9A" if name == panel_name else "transparent",
                text_color="#FFFFFF" if name == panel_name else "#C5D0D6",
            )

        for widget in self.page_content.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        self.metric_labels = {}
        self.loans_chart = None
        self.fines_chart = None
        self.subtitle_label = None
        self._snapshot = None

        title = f"{self.greeting()}, {self.username}" if panel_name == "Dashboard" else panel_name
        subtitle = "Your library at a glance" if panel_name == "Dashboard" else ""

        ctk.CTkLabel(
            self.page_content, text=title, text_color="#E8EDF0",
            font=ctk.CTkFont(size=30, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        self.subtitle_label = ctk.CTkLabel(
            self.page_content, text=subtitle, text_color="#9AA7B0",
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        if panel_name == "Dashboard":
            try:
                metrics, activity = self.fetch_dashboard_data()
            except Exception as error:
                logger.error("Unable to load dashboard data", exc_info=error)
                ctk.CTkLabel(
                    self.page_content, text=f"Unable to load summary: {error}",
                    text_color="#D17A67",
                ).grid(row=2, column=0, sticky="nw", pady=(28, 0))
                return

            metric_grid = ctk.CTkFrame(self.page_content, fg_color="transparent")
            metric_grid.grid(row=2, column=0, sticky="new", pady=(28, 0))
            for index in range(4):
                metric_grid.grid_columnconfigure(index, weight=1)

            cards = (
                ("Total books", "total_books", "#2A9D9A"),
                ("Active loans", "active_loans", "#2A9D9A"),
                ("Overdue", "overdue", "#D17A67"),
                ("Members", "members", "#2A9D9A"),
            )
            for index, (label, key, accent) in enumerate(cards):
                card = ctk.CTkFrame(metric_grid, fg_color=CARD_BG, border_color=BORDER, border_width=1, corner_radius=10)
                card.grid(
                    row=0, column=index, sticky="nsew",
                    padx=(0 if index == 0 else 7, 7 if index < 3 else 0),
                )
                ctk.CTkLabel(
                    card, text=label.upper(), text_color="#9AA7B0",
                    font=ctk.CTkFont(size=10, weight="bold"),
                ).pack(anchor="w", padx=16, pady=(16, 7))
                value_label = ctk.CTkLabel(
                    card, text="0", text_color=accent,
                    font=ctk.CTkFont(size=30, weight="bold"),
                )
                value_label.pack(anchor="w", padx=16, pady=(0, 16))
                self.metric_labels[key] = value_label

            self.add_activity_charts()
            self.apply_dashboard_data(metrics, activity)
            self.set_sync_status(True)

        elif panel_name == "Books":
            self.active_view = BookCatalogView(self.page_content)
            self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        elif panel_name == "Categories":
            self.active_view = CategoryView(self.page_content)
            self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        elif panel_name == "Members":
            self.active_view = MemberView(self.page_content)
            self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        elif panel_name == "Borrow / Return":
            self.active_view = BorrowReturnView(self.page_content)
            self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        elif panel_name == "Reports":
            self.active_view = ReportsView(self.page_content)
            self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        elif panel_name == "Reservations":
            self.active_view = ReservationView(self.page_content)
            self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        elif panel_name == "Viva Library Assistant":
            self.active_view = ChatbotView(self.page_content, chatbot_instance=self.chatbot_instance)
            self.active_view.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        else:
            ctk.CTkLabel(
                self.page_content,
                text=f"{panel_name} content will appear here.",
                text_color="#9AA7B0",
            ).grid(row=2, column=0, sticky="nw", pady=24)

        if self.active_view and hasattr(self.active_view, "refresh"):
            try:
                self.active_view.refresh()
            except Exception:
                pass

    # Dashboard data + live sync
    @staticmethod
    def fetch_dashboard_data() -> tuple[dict, list[dict]]:
        """Reads fresh numbers from the database. Raises if either query fails."""
        reporter = ReportManager()
        metrics = reporter.summary()
        activity = normalize_activity(reporter.monthly_activity())
        return metrics, activity

    def add_activity_charts(self) -> None:
        wrapper = ctk.CTkFrame(self.page_content, fg_color="transparent")
        wrapper.grid(row=3, column=0, sticky="nsew", pady=(24, 0))
        wrapper.grid_columnconfigure(0, weight=1, uniform="charts")
        wrapper.grid_columnconfigure(1, weight=1, uniform="charts")
        wrapper.grid_rowconfigure(0, weight=1)

        self.loans_chart = BarChart(
            wrapper, "Loans per month", f"loans in the last {CHART_MONTHS} months",
            TEAL, TEAL_DIM,
            label_format=lambda v: f"{v:.0f}",
            axis_format=lambda v: f"{v:.0f}",
        )
        self.loans_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

        self.fines_chart = BarChart(
            wrapper, "Fines per month", f"fines in the last {CHART_MONTHS} months",
            CORAL, CORAL_DIM,
            label_format=lambda v: f"₱{v:,.0f}",
            axis_format=lambda v: f"₱{v:,.0f}",
        )
        self.fines_chart.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

    def apply_dashboard_data(self, metrics: dict, activity: list[dict]) -> None:
        """Updates the cards and charts, but only when the database numbers actually changed."""
        snapshot = (
            tuple(_value(metrics, key, 0) for key in METRIC_KEYS),
            tuple((a["label"], a["loans"], a["fines"]) for a in activity),
        )
        if snapshot == self._snapshot:
            return
        self._snapshot = snapshot

        for key, label in self.metric_labels.items():
            if label.winfo_exists():
                label.configure(text=str(_value(metrics, key, 0)))

        if self.loans_chart is not None and self.loans_chart.winfo_exists():
            total_loans = sum(a["loans"] for a in activity)
            self.loans_chart.set_data([(a["label"], a["loans"]) for a in activity], str(total_loans))

        if self.fines_chart is not None and self.fines_chart.winfo_exists():
            total_fines = sum(a["fines"] for a in activity)
            self.fines_chart.set_data([(a["label"], a["fines"]) for a in activity], peso(total_fines))

    def set_sync_status(self, ok: bool) -> None:
        """Shows when the dashboard last synced, or that the sync is failing."""
        if ok:
            self.last_sync = datetime.now().strftime("%I:%M:%S %p").lstrip("0")
        label = self.subtitle_label
        if self.active_panel != "Dashboard" or label is None or not label.winfo_exists():
            return
        if ok:
            label.configure(text=f"Your library at a glance  ·  Synced {self.last_sync}", text_color="#9AA7B0")
        else:
            label.configure(
                text=f"Can't reach the database, retrying...  ·  Last synced {self.last_sync or 'never'}",
                text_color="#D17A67",
            )

    def refresh_live_data(self):
        if not self.winfo_exists():
            return
        if self.active_panel == "Dashboard":
            self.refresh_dashboard_data()
        self.refresh_job = self.after(SYNC_INTERVAL_MS, self.refresh_live_data)

    def refresh_dashboard_data(self):
        try:
            metrics, activity = self.fetch_dashboard_data()
        except Exception as error:
            logger.warning("Dashboard sync failed: %s", error)
            self.set_sync_status(False)
            return
        self.apply_dashboard_data(metrics, activity)
        self.set_sync_status(True)

    def close(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.destroy()
        self.login_window.destroy()