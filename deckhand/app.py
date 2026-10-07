from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, SelectionList

from deckhand.catalog import load_catalog
from deckhand.generator import write_stack


class DeckhandApp(App):
    TITLE = "Deckhand"
    BINDINGS = [
        ("r", "review", "Review"),
        ("g", "generate", "Generate"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        options = []
        self.catalog = {}
        for entry in load_catalog():
            label = f"{entry['name']}  ({entry['category']})"
            options.append((label, entry["id"]))
            self.catalog[entry["id"]] = entry
        yield SelectionList(*options)

        yield Footer()

    def action_review(self) -> None:
        selected = self.query_one(SelectionList).selected
        if selected:
            self.notify("Selected: " + ", ".join(selected))
        else:
            self.notify("Nothing selected yet.", severity="warning")    

    def action_generate(self) -> None:
        selected = self.query_one(SelectionList).selected
        if not selected:
            self.notify("Nothing selected yet.", severity="warning")
            return

        for app_id in selected:
            compose_file = write_stack(self.catalog[app_id])
            if compose_file:
                self.notify(f"Created {compose_file}")
            else:
                self.notify(f"{app_id} already exists, skipped.", severity="warning")


if __name__ == "__main__":
    app = DeckhandApp()
    app.run()