"""Application entry point."""

from gui.login_window import LoginWindow


def main() -> None:
	"""Launch the library management system."""
	app = LoginWindow()
	app.mainloop()


if __name__ == "__main__":
	main()
