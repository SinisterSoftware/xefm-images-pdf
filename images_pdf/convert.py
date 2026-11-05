"""画像を PDF に変換する (Pillow のみ。追加ソフト不要)

- 未選択: カーソル下の画像を1枚変換。複数選択: 指定のレイアウトでまとめて1つの PDF にする
- 設定は引数で受け取る。引数なしなら A4・向き自動・1枚/ページ
- 写真は EXIF の向きで天地を補正。透過画像は白背景に合成。
- 各ページは 200dpi のラスタ画像として PDF 化する (文字は検索不可)。
"""
import argparse
import os
import shlex
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageOps

Image.MAX_IMAGE_PIXELS = None
DPI = 200
MM = DPI / 25.4
PAPERS = {"A4": (210, 297), "A3": (297, 420)}
EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp", ".jfif", ".heic", ".avif")
MARGIN_MM = 10
GAP_MM = 4
FONT_PATHS = [r"C:\Windows\Fonts\meiryo.ttc", r"C:\Windows\Fonts\msgothic.ttc", r"C:\Windows\Fonts\YuGothM.ttc"]


def collect(args):
    this_dir = os.environ.get("XEFM_THIS_DIR", os.getcwd())
    names = shlex.split(os.environ.get("XEFM_THIS_SELECTED", "")) or \
        shlex.split(os.environ.get("XEFM_THIS_FOCUSED", ""))
    paths = [n if os.path.isabs(n) else os.path.join(this_dir, n) for n in (args.files or names)]
    return [p for p in paths if os.path.isfile(p) and p.lower().endswith(EXTS)]

def load(path):
    im = Image.open(path)
    try:
        im.seek(0)
    except Exception:
        pass
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im.convert("RGB")


def font(size):
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_pages(paths, paper, landscape, cols, rows, caption, auto_orient):
    pw, ph = PAPERS[paper]
    pages = []
    per = cols * rows
    f = font(int(4.2 * MM)) if caption else None
    cap_h = int(8 * MM) if caption else 0
    for i in range(0, len(paths), per):
        chunk = paths[i:i + per]
        imgs = [load(p) for p in chunk]
        land = landscape
        if auto_orient:
            w, h = imgs[0].size
            land = w > h
        W, H = (ph, pw) if land else (pw, ph)
        W, H = int(W * MM), int(H * MM)
        page = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(page)
        m, g = int(MARGIN_MM * MM), int(GAP_MM * MM)
        cw, ch = (W - 2 * m - g * (cols - 1)) // cols, (H - 2 * m - g * (rows - 1)) // rows
        for n, (p, im) in enumerate(zip(chunk, imgs)):
            r, c = divmod(n, cols)
            x0, y0 = m + c * (cw + g), m + r * (ch + g)
            box_h = ch - cap_h
            s = min(cw / im.width, box_h / im.height)
            nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
            im = im.resize((nw, nh), Image.LANCZOS)
            page.paste(im, (x0 + (cw - nw) // 2, y0 + (box_h - nh) // 2))
            if caption:
                name = os.path.splitext(os.path.basename(p))[0]
                while len(name) > 1 and d.textlength(name, font=f) > cw:
                    name = name[:-2] + "…"
                tw = d.textlength(name, font=f)
                d.text((x0 + (cw - tw) / 2, y0 + box_h + int(1.5 * MM)), name, fill="black", font=f)
        pages.append(page)
    return pages


def unique(path):
    base, ext = os.path.splitext(path)
    n = 1
    while os.path.exists(path):
        n += 1
        path = f"{base}_{n}{ext}"
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="A4", choices=list(PAPERS))
    ap.add_argument("--orient", default="auto", choices=["portrait", "landscape", "auto"])
    ap.add_argument("--cols", type=int, default=1)
    ap.add_argument("--rows", type=int, default=1)
    ap.add_argument("--caption", action="store_true")
    ap.add_argument("--sort", action="store_true", help="名前順に並べる")
    ap.add_argument("--out", default="", help="保存ファイル名 (相対なら先頭画像のフォルダ基準)")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()
    paths = collect(args)
    if not paths:
        print("画像ファイルがありません")
        return 0
    if args.sort:
        paths.sort(key=lambda p: os.path.basename(p).lower())
    pages = build_pages(paths, args.paper, args.orient == "landscape", args.cols, args.rows,
                        args.caption, args.orient == "auto")
    multi = len(paths) > 1
    first = os.path.splitext(os.path.basename(paths[0]))[0]
    name = f"{first}_ほか{len(paths) - 1}件.pdf" if multi else first + ".pdf"
    if args.out:
        name = args.out if args.out.lower().endswith(".pdf") else args.out + ".pdf"
    out = unique(name if os.path.isabs(name) else os.path.join(os.path.dirname(paths[0]), name))
    pages[0].save(out, "PDF", resolution=DPI, save_all=True, append_images=pages[1:], quality=90)
    print(f"{len(pages)} ページ -> {os.path.basename(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())