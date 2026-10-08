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

    installing = False
    confirm_quit = False

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
        if self.installing:
            self.notify("An install is already running.", severity="warning")
            return 
        selected = self.query_one(SelectionList).selected
        if not selected:
            self.notify("Nothing selected yet.", severity="warning")
            return
        self.install_apps(selected)

    @work(thread=True, exclusive=True)
    def install_apps(self, selected) -> None:
        self.installing = True
        try:
            total = len(selected)
            for number, app_id in enumerate(selected, start=1):
                self.call_from_thread(
                    self.set_status, f"Installing {app_id} ({number}/{total})..."
                )
                write_stack(self.catalog[app_id])

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
        finally:
            self.installing = False
            self.confirm_quit = False
            self.call_from_thread(self.set_status, "")

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

    def set_status(self, text) -> None:
        self.sub_title = text

    def action_quit(self) -> None:
        if self.installing and not self.confirm_quit:
            self.confirm_quit = True
            self.notify(
                "An install is still running. Press q again to quit anyway.",
                severity="warning",
            )
            return
        self.exit()

if __name__ == "__main__":
    app = DeckhandApp()
    app.run()