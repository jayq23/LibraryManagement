"""Date and display formatting helpers."""

from datetime import date, timedelta


def due_date_from(start: date, loan_days: int = 14) -> date:
    return start + timedelta(days=loan_days)


def enable_mousewheel(scroll_frame) -> None:
    """Route wheel events to the scroll frame without replacing CustomTkinter bindings."""
    canvas = scroll_frame._parent_canvas
    root = scroll_frame.winfo_toplevel()
    canvases = getattr(root, "_library_scroll_canvases", [])
    if canvas not in canvases:
        canvases.append(canvas)
    root._library_scroll_canvases = canvases
    if getattr(root, "_library_wheel_bound", False):
        return

    def scroll(event):
        delta = getattr(event, "delta", 0)
        if getattr(event, "num", None) == 4 or delta > 0:
            steps = -1
        elif getattr(event, "num", None) == 5 or delta < 0:
            steps = 1
        else:
            return
        widget = event.widget
        for candidate in list(root._library_scroll_canvases):
            if not candidate.winfo_exists():
                root._library_scroll_canvases.remove(candidate)
                continue
            current = widget
            while current is not None:
                if current == candidate:
                    candidate.yview_scroll(steps, "units")
                    return
                current = getattr(current, "master", None)

    root.bind_all("<MouseWheel>", scroll, add="+")
    root.bind_all("<Button-4>", scroll, add="+")
    root.bind_all("<Button-5>", scroll, add="+")
    root._library_wheel_bound = True
