# Application entry point.

from gui.login_window import LoginWindow


# Start the application.
def main() -> None:
	app = LoginWindow()
	app.mainloop()


if __name__ == "__main__":
	main()
