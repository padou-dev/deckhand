from textual.app import App, ComposeResult
from textual import work
from textual.containers import Horizontal
from textual.widgets import Footer, Header, SelectionList, Static

from deckhand.catalog import load_catalog
from deckhand.generator import start_stack, write_stack

class DeckhandApp(App):
    TITLE = "Deckhand"
    BINDINGS = [
        ("r", "review", "Review"),
        ("i", "install", "Install"),
        ("q", "quit", "Quit"),
    ]
    CSS = """
    SelectionList {
        width: 1fr;
    }
    #details {
        width: 1fr;
        padding: 1 2;
        border: round $accent;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        options = []
        self.catalog = {}
        for entry in load_catalog():
            label = f"{entry['name']}  ({entry['category']})"
            options.append((label, entry["id"]))
            self.catalog[entry["id"]] = entry

        with Horizontal():
            yield SelectionList(*options)
            yield Static("Highlight an app to see its details.", id="details")

        yield Footer()

    def action_review(self) -> None:
        selected = self.query_one(SelectionList).selected
        if selected:
            self.notify("Selected: " + ", ".join(selected))
        else:
            self.notify("Nothing selected yet.", severity="warning")    

    def action_install(self) -> None:
        selected = self.query_one(SelectionList).selected
        if not selected:
            self.notify("Nothing selected yet.", severity="warning")
            return
        self.install_apps(selected)

    @work(thread=True, exclusive=True)
    def install_apps(self, selected) -> None:
        for app_id in selected:
            write_stack(self.catalog[app_id])
            self.call_from_thread(self.notify, f"Starting {app_id}...")

            result = start_stack(app_id)
            if result.returncode == 0:
                self.call_from_thread(self.notify, f"{app_id} is running.")
            else:
                self.call_from_thread(
                    self.notify,
                    f"{app_id} failed: {result.stderr.strip()}",
                    severity="error",
                    timeout=15,
                )

    def on_selection_list_selection_highlighted(self, event) -> None:
        entry = self.catalog[event.selection.value]
        architectures = ", ".join(entry["architectures"])

        details = (
            f"[b]{entry['name']}[/b]\n\n"
            f"{entry['description']}\n\n"
            f"Category: {entry['category']}\n"
            f"Web port: {entry['web_port']}\n"
            f"Runs on: {architectures}"
        )
        self.query_one("#details", Static).update(details)

if __name__ == "__main__":
    app = DeckhandApp()
    app.run()