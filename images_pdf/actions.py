"""Convert selected images to PDF."""

import os
from pathlib import Path

from xefm.user_api import xefm_python

EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp", ".jfif", ".heic", ".avif")
LAYOUTS = ("1x1", "2x1", "1x2", "2x2", "3x2", "2x3", "3x3", "4x4")


def images_to_pdf(ctx):
    """Convert images in the active pane to a PDF in the other pane."""
    files = [entry for entry in ctx.pane.selected()
             if entry.is_file and str(entry.path).lower().endswith(EXTS)]
    if not files:
        entry = ctx.pane.focused
        if entry is None or not entry.is_file or not str(entry.path).lower().endswith(EXTS):
            ctx.message("画像ファイルを選択してください")
            return
        files = [entry]
    paths = [str(entry.path) for entry in files]
    output_dir = str(ctx.other.path)
    if "://" in output_dir:
        ctx.message("PDFの保存先にはローカルフォルダを指定してください")
        return
    multi = len(paths) > 1
    first = os.path.splitext(os.path.basename(paths[0]))[0]
    default = f"{first}_ほか{len(paths) - 1}件.pdf" if multi else first + ".pdf"
    values = {"paper": "A4", "orient": "portrait" if multi else "auto",
              "layout": "1x1", "sort": False, "caption": False}

    def run(name):
        if not name or not name.strip():
            return
        output = os.path.join(output_dir, os.path.basename(name.strip()))
        args = ["--out", output, "--paper", values["paper"], "--orient", values["orient"]]
        if multi:
            cols, rows = values["layout"].split("x")
            args += ["--cols", cols, "--rows", rows]
            if values["sort"]:
                args.append("--sort")
        if values["caption"]:
            args.append("--caption")
        ctx.run_program([xefm_python, str(Path(__file__).with_name("convert.py")), *args, *paths])

    def choose_value(key, choices):
        def picked(index):
            if index is not None:
                values[key] = choices[index]
            options()
        ctx.choose(key, choices, on_result=picked)

    def options():
        items = [f"保存ファイル名を入力: {default}", f"用紙: {values['paper']}",
                 f"向き: {values['orient']}"]
        keys = ["paper", "orient"]
        choices = [("A4", "A3"), ("portrait", "landscape") if multi
                   else ("auto", "portrait", "landscape")]
        if multi:
            items += [f"配置: {values['layout']}", f"名前順: {values['sort']}"]
            keys += ["layout", "sort"]
            choices += [LAYOUTS, (False, True)]
        items.append(f"名前表示: {values['caption']}")
        keys.append("caption")
        choices.append((False, True))

        def picked(index):
            if index is None:
                return
            if index == 0:
                ctx.input("保存ファイル名", default, title="Images to PDF", on_accept=run)
            else:
                choice = choices[index - 1]
                if isinstance(choice[0], bool):
                    values[keys[index - 1]] = not values[keys[index - 1]]
                    options()
                else:
                    choose_value(keys[index - 1], choice)
        ctx.choose("Images to PDF", items, on_result=picked)

    options()
