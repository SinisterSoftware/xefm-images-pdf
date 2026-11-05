import unittest
from pathlib import Path
from types import SimpleNamespace

from images_pdf.actions import images_to_pdf


class Context:
    def __init__(self):
        self.pane = SimpleNamespace(selected=lambda: [], focused=SimpleNamespace(
            is_file=True, path=r"C:\input\photo.png"))
        self.other = SimpleNamespace(path=r"C:\output")
        self.choices = []
        self.commands = []
        self.messages = []

    def choose(self, title, items, *, on_result, **kwargs):
        self.choices.append((items, on_result))

    def input(self, prompt, default, *, title, on_accept):
        on_accept(default)

    def run_program(self, command):
        self.commands.append(command)

    def message(self, text):
        self.messages.append(text)


class ImageActionTests(unittest.TestCase):
    def test_default_conversion_uses_packaged_script(self):
        ctx = Context()
        images_to_pdf(ctx)
        ctx.choices.pop()[1](0)
        command = ctx.commands[0]
        self.assertEqual(Path(command[1]).name, "convert.py")
        self.assertTrue(Path(command[1]).is_file())
        self.assertEqual(command[command.index("--paper") + 1], "A4")
        self.assertEqual(command[command.index("--orient") + 1], "auto")

    def test_rejects_nonlocal_output(self):
        ctx = Context()
        ctx.other.path = "ssh://example/folder"
        images_to_pdf(ctx)
        self.assertTrue(ctx.messages)
        self.assertFalse(ctx.choices)
