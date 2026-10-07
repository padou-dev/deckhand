from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, SelectionList

from deckhand.catalog import load_catalog


class DeckhandApp(App):
    TITLE = "Deckhand"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()

        options = []
        for entry in load_catalog():
            label = f"{entry['name']}  ({entry['category']})"
            options.append((label, entry["id"]))
        yield SelectionList(*options)

        yield Footer()


if __name__ == "__main__":
    app = DeckhandApp()
    app.run()