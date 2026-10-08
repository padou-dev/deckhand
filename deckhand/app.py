from textual.app import App, ComposeResult
from textual import work
from textual.containers import Horizontal
from textual.widgets import Footer, Header, SelectionList, Static

from deckhand.catalog import load_catalog
from deckhand.generator import stack_exists, start_stack, write_stack
from deckhand.ports import busy_ports
from deckhand.health import wait_until_ready, web_url

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
                entry = self.catalog[app_id]
                self.call_from_thread(
                    self.set_status, f"Installing {app_id} ({number}/{total})..."
                )

                if not stack_exists(app_id):
                    busy = busy_ports(entry)
                    if busy:
                        ports_text = ", ".join(str(port) for port in busy)
                        self.call_from_thread(
                            self.notify,
                            f"{app_id} skipped: port {ports_text} already in use.",
                            severity="error",
                            timeout=15,
                        )
                        continue

                write_stack(entry)
                result = start_stack(app_id)
                if result.returncode != 0:
                    self.call_from_thread(
                        self.notify,
                        f"{app_id} failed: {result.stderr.strip()}",
                        severity="error",
                        timeout=15,
                    )
                    continue

                url = web_url(entry)
                self.call_from_thread(
                    self.set_status, f"Waiting for {app_id} to start..."
                )
                if wait_until_ready(url):
                    self.call_from_thread(
                        self.notify,
                        f"{entry['name']} is ready at {url}",
                        timeout=20,
                    )
                else:
                    self.call_from_thread(
                        self.notify,
                        f"{entry['name']} started but isn't responding yet. "
                        f"Try {url} in a minute.",
                        severity="warning",
                        timeout=20,
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