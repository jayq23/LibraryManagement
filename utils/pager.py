# Reusable pagination bar for the list screens.
#
# CustomTkinter widgets are expensive to create, so the screens only build the
# rows of the current page (25 by default) instead of every record at once.

import customtkinter as ctk


def paginate(items: list, page: int, page_size: int) -> tuple[list, int, int]:
    # Return (items on this page, corrected page index, total number of pages).
    pages = max(1, -(-len(items) // page_size))
    page = max(0, min(page, pages - 1))
    start = page * page_size
    return items[start:start + page_size], page, pages


def scroll_to_top(scrollable) -> None:
    # Jump a CTkScrollableFrame back to the top after the page changes.
    try:
        scrollable._parent_canvas.yview_moveto(0)
    except Exception:
        pass


class Pager(ctk.CTkFrame):
    # Prev / Next bar. Call slice(items) inside the screen's render method.

    def __init__(self, master, on_change, page_size: int = 25):
        super().__init__(master, fg_color="transparent")
        self.on_change = on_change
        self.page_size = page_size
        self.page = 0
        self.pages = 1
        self.scroll_target = None  # Set to the scrollable list so it resets to the top.

        self.prev_btn = ctk.CTkButton(
            self,
            text="Prev",
            command=self.prev_page,
            width=70,
            height=30,
            corner_radius=6,
            fg_color="#253540",
            hover_color="#344650",
        )
        self.prev_btn.pack(side="left")

        self.label = ctk.CTkLabel(self, text="Page 1 of 1", text_color="#A6B1B8")
        self.label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(
            self,
            text="Next",
            command=self.next_page,
            width=70,
            height=30,
            corner_radius=6,
            fg_color="#253540",
            hover_color="#344650",
        )
        self.next_btn.pack(side="right")

    def reset(self) -> None:
        self.page = 0

    def slice(self, items: list) -> list:
        visible, self.page, self.pages = paginate(items, self.page, self.page_size)
        self.label.configure(text=f"Page {self.page + 1} of {self.pages}  ·  {len(items)} total")
        self.prev_btn.configure(state="normal" if self.page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.page < self.pages - 1 else "disabled")
        return visible

    def prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self.on_change()
            scroll_to_top(self.scroll_target)

    def next_page(self) -> None:
        if self.page < self.pages - 1:
            self.page += 1
            self.on_change()
            scroll_to_top(self.scroll_target)
