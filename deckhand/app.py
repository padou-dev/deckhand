from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Input, OptionList, SelectionList, Static
from textual.widgets.option_list import Option

from deckhand.catalog import load_catalog
from deckhand.generator import stack_exists, start_stack, write_stack
from deckhand.health import wait_until_ready, web_url
from deckhand.ports import busy_ports

LOGO = "\n".join([
    "╔╦╗╔═╗╔═╗╦╔═╦ ╦╔═╗╔╗╔╔╦╗",
    " ║║║╣ ║  ╠╩╗╠═╣╠═╣║║║ ║║",
    "═╩╝╚═╝╚═╝╩ ╩╩ ╩╩ ╩╝╚╝═╩╝",
])

TAGLINE = "Pick self-hosted apps, get clean Docker Compose setups."

class DeckhandApp(App):
    TITLE = "Deckhand"
    BINDINGS = [
        ("/", "focus_search", "Search"),
        ("escape", "focus_list", "Back to list"),
        ("r", "review", "Review"),
        ("i", "install", "Install"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    #logo {
        width: 100%;
        text-align: center;
        color: $accent;
        padding-top: 1;
    }
    #tagline {
        width: 100%;
        text-align: center;
        color: $text-muted;
        padding-bottom: 1;
    }
    #search {
        margin: 0 1;
    }
    #hints {
        color: $text-muted;
        padding: 0 2 1 2;
    }
    #categories {
        width: 22;
    }
    SelectionList {
        width: 1fr;
    }
    #categories, SelectionList, #details {
        border: round $primary-darken-2;
    }
    #categories:focus, SelectionList:focus {
        border: round $accent;
    }
    #details {
        width: 1fr;
        padding: 1 2;
    }
    """

    installing = False
    confirm_quit = False

    # --- Building the screen ---

    def compose(self) -> ComposeResult:
        self.catalog = {}
        for entry in load_catalog():
            self.catalog[entry["id"]] = entry

        self.chosen = set()
        self.category = "all"
        self.search = ""

        categories = sorted({entry["category"] for entry in self.catalog.values()})
        category_options = [Option("All", id="all")]
        for category in categories:
            category_options.append(Option(category.title(), id=category))

        yield Header()
        yield Header()
        yield Static(LOGO, id="logo")
        yield Static(TAGLINE, id="tagline")
        yield Input(placeholder="Search apps...", id="search")
        yield Static(
            "[b]/[/b] search  ·  [b]Tab[/b] switch panels  ·  "
            "[b]Space[/b] select  ·  [b]i[/b] install",
            id="hints",
        )
        with Horizontal():
            yield OptionList(*category_options, id="categories")
            yield SelectionList()
            yield Static("Highlight an app to see its details.", id="details")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "gruvbox"
        self.refresh_list()
        self.query_one(SelectionList).focus()
        self.query_one("#categories").border_title = "Categories"
        self.query_one(SelectionList).border_title = "Apps"
        self.query_one("#details").border_title = "Details"

    def refresh_list(self) -> None:
        search = self.search.lower()
        options = []
        for entry in self.catalog.values():
            if self.category != "all" and entry["category"] != self.category:
                continue
            searchable = f"{entry['name']} {entry['description']}".lower()
            if search not in searchable:
                continue
            options.append((entry["name"], entry["id"], entry["id"] in self.chosen))

        selection_list = self.query_one(SelectionList)
        selection_list.clear_options()
        selection_list.add_options(options)

    # --- Reacting to the user ---

    def on_input_changed(self, event: Input.Changed) -> None:
        self.search = event.value
        self.refresh_list()

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id != "categories":
            return
        self.category = event.option.id
        self.refresh_list()

    def on_selection_list_selection_toggled(self, event: SelectionList.SelectionToggled) -> None:
        app_id = event.selection.value
        if app_id in self.chosen:
            self.chosen.remove(app_id)
        else:
            self.chosen.add(app_id)

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

    # --- Actions (key bindings) ---

    def action_focus_search(self) -> None:
        self.query_one("#search").focus()

    def action_focus_list(self) -> None:
        self.query_one(SelectionList).focus()

    def action_review(self) -> None:
        if self.chosen:
            self.notify("Selected: " + ", ".join(sorted(self.chosen)))
        else:
            self.notify("Nothing selected yet.", severity="warning")

    def action_quit(self) -> None:
        if self.installing and not self.confirm_quit:
            self.confirm_quit = True
            self.notify(
                "An install is still running. Press q again to quit anyway.",
                severity="warning",
            )
            return
        self.exit()

    def action_install(self) -> None:
        if self.installing:
            self.notify("An install is already running.", severity="warning")
            return
        if not self.chosen:
            self.notify("Nothing selected yet.", severity="warning")
            return
        count = len(self.chosen)
        noun = "app" if count == 1 else "apps"
        self.notify(
            f"Installing {count} {noun}. You'll get a message as each one is ready. "
            "Please keep Deckhand open until the install finishes.",
            title="Install started",
            timeout=10,
        )
        self.install_apps(sorted(self.chosen))

    # --- Installing ---

    def set_status(self, text) -> None:
        self.sub_title = text

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
            self.call_from_thread(
                self.notify,
                "All installs finished. It's safe to quit Deckhand.",
                title="Done",
                timeout=20,
            )
        finally:
            self.installing = False
            self.confirm_quit = False
            self.call_from_thread(self.set_status, "")


if __name__ == "__main__":
    app = DeckhandApp()
    app.run()