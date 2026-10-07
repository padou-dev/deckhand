from textual.app import App, ComposeResult
from textual.widgets import Footer, Header


class DeckhandApp(App):
    TITLE = "Deckhand"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


if __name__ == "__main__":
    app = DeckhandApp()
    app.run()