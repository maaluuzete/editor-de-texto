from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TextArea, Input, Label, Button
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual import on
import os

appStyle = """
QuitModal, InputModal {
    align: center middle;
}
.modalBox {
    width: 50;
    height: 12;
    padding: 1 2;
    background: $surface;
    border: tall $primary;
}
.modalTitle {
    content-align: center middle;
    width: 100%;
    margin-bottom: 1;
}
.btnRow {
    align: center middle;
    width: 100%;
    height: 3;
}
.btnRow Button {
    width: 15;
    margin: 0 1; 
}
"""

class QuitModal(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        with Vertical(classes="modalBox"):
            yield Label("Você tem alterações não salvas.\nDeseja realmente sair?", classes="modalTitle")
            with Horizontal(classes="btnRow"):
                yield Button("Sim", id="btnYes", variant="error")
                yield Button("Não", id="btnNo", variant="primary")

    @on(Button.Pressed, "#btnYes")
    def confirmExit(self):
        self.dismiss(True)

    @on(Button.Pressed, "#btnNo")
    def cancelExit(self):
        self.dismiss(False)

class InputModal(ModalScreen[str]):
    def __init__(self, promptText: str, **kwargs):
        super().__init__(**kwargs)
        self.promptText = promptText

    def compose(self) -> ComposeResult:
        with Vertical(classes="modalBox"):
            yield Label(self.promptText, classes="modalTitle")
            yield Input(id="fileInput", placeholder="Digite o caminho...")

    @on(Input.Submitted, "#fileInput")
    def submitInput(self, eventObj: Input.Submitted):
        self.dismiss(eventObj.value)

class EditorApp(App):
    CSS = appStyle
    BINDINGS = [
        Binding("ctrl+s", "saveFile", "Salvar"),
        Binding("ctrl+a", "saveAsFile", "Salvar Como"),
        Binding("ctrl+o", "openFile", "Abrir"),
        Binding("ctrl+q", "quitApp", "Sair")
    ]

    def __init__(self):
        super().__init__()
        self.currentFile = None
        self.isDirty = False
        self.isLoading = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield TextArea(id="editorArea")
        yield Footer()

    def on_mount(self):
        self.title = "Editor TUI"
        self.updateHeader()

    def updateHeader(self):
        nameStr = self.currentFile if self.currentFile else "Novo Arquivo"
        dirtyIndicator = "*" if self.isDirty else ""
        self.sub_title = f"{nameStr}{dirtyIndicator}"

    @on(TextArea.Changed, "#editorArea")
    def markDirty(self):
        if self.isLoading: return
        if not self.isDirty:
            self.isDirty = True
            self.updateHeader()

    def action_saveFile(self):
        if not self.currentFile:
            self.action_saveAsFile()
            return
        textAreaObj = self.query_one("#editorArea", TextArea)
        try:
            with open(self.currentFile, "w", encoding="utf-8") as fileObj:
                fileObj.write(textAreaObj.text)
            self.isDirty = False
            self.updateHeader()
            self.notify("Arquivo salvo com sucesso!")
        except Exception as errObj:
            self.notify(f"Erro ao salvar: {errObj}", severity="error")

    def action_saveAsFile(self):
        def handleSave(filePath: str | None):
            if filePath:
                self.currentFile = filePath
                self.action_saveFile()
        self.push_screen(InputModal("Salvar como:"), handleSave)

    def action_openFile(self):
        def handleOpen(filePath: str | None):
            if filePath:
                try:
                    if not os.path.exists(filePath):
                        raise FileNotFoundError("Arquivo não encontrado.")
                    with open(filePath, "r", encoding="utf-8") as fileObj:
                        contentStr = fileObj.read()
                    textAreaObj = self.query_one("#editorArea", TextArea)
                    self.isLoading = True
                    textAreaObj.text = contentStr
                    self.currentFile = filePath
                    self.isDirty = False
                    self.updateHeader()
                    self.isLoading = False
                    self.notify("Arquivo carregado!")
                except Exception as errObj:
                    self.isLoading = False
                    self.notify(f"Erro: {errObj}", severity="error")
        self.push_screen(InputModal("Abrir arquivo:"), handleOpen)

    def action_quitApp(self):
        if self.isDirty:
            def handleQuit(shouldQuit: bool | None):
                if shouldQuit: self.exit()
            self.push_screen(QuitModal(), handleQuit)
        else:
            self.exit()

if __name__ == "__main__":
    appObj = EditorApp()
    appObj.run()