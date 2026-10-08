from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmQuitScreen(ModalScreen[bool]):
    BINDINGS = [
        ("enter", "confirm", "Cancel install and quit"),
        ("escape", "stay", "Keep installing"),
    ]

    DEFAULT_CSS = """
    ConfirmQuitScreen {
        align: center middle;
    }
    #dialog {
        width: 64;
        height: auto;
        padding: 1 2;
        border: round $error;
        background: $surface;
    }
    #dialog Label {
        width: 100%;
    }
    #note {
        color: $text-muted;
        margin: 1 0;
    }
    #buttons {
        height: auto;
        align: center middle;
    }
    #buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, installing_name) -> None:
        super().__init__()
        self.installing_name = installing_name

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(
                f"{self.installing_name} is still installing. "
                "Quitting now will cancel it and remove its files."
            )
            yield Label("Apps already installed are kept.", id="note")
            with Horizontal(id="buttons"):
                yield Button("Cancel install and quit (Enter)", variant="error", id="quit")
                yield Button("Keep installing (Esc)", variant="primary", id="stay")

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = "Cancel install?"
        for button in self.query(Button):
            button.can_focus = False

    def action_confirm(self) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "quit")

    def action_stay(self) -> None:
        self.dismiss(False)