from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


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
        width: 76;
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "quit")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_stay(self) -> None:
        self.dismiss(False)


class AskScreen(ModalScreen[str | None]):
    BINDINGS = [("escape", "cancel", "Cancel install")]

    DEFAULT_CSS = """
    AskScreen {
        align: center middle;
    }
    #dialog {
        width: 76;
        height: auto;
        padding: 1 2;
        border: round $accent;
        background: $surface;
    }
    #dialog Label {
        width: 100%;
    }
    #answer {
        margin: 1 0;
    }
    #note {
        color: $text-muted;
    }
    """

    def __init__(self, for_app, question, secret=False) -> None:
        super().__init__()
        self.for_app = for_app
        self.question = question
        self.secret = secret

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.question)
            yield Input(password=self.secret, id="answer")
            yield Label("Enter to confirm  ·  Esc to cancel the install", id="note")

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = f"{self.for_app} setup"
        self.query_one("#answer", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if not value:
            self.notify("This value is required.", severity="warning")
            return
        self.dismiss(value)

    def action_cancel(self) -> None:
        self.dismiss(None)