#!/usr/bin/env python3
"""Конвертер изображений: jfif/webp/jpg/jpeg -> png + правка ссылок в .md.

Ищет в publication/murder/*.md все ссылки вида ../../...X.(jfif|webp|jpe?g)
(т.е. не-PNG), где X — реальный файл. Для каждого:
  - если рядом уже есть X.png -> просто обновляет ссылку;
  - иначе конвертирует X.(ext) -> X.png (ImageMagick `convert`, затем `ffmpeg`),
    оставляя исходник, затем обновляет ссылку.
В .md на maps/*.png ссылок на jfif/webp/jpg нет — трогать maps/ не нужно.
"""
import os, re, subprocess, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR = os.path.join(ROOT, "publication", "murder")
# любая ссылка в .md, оканчивающаяся .jfif/.webp/.jpg/.jpeg (через ../)
IMG_RE = re.compile(r"(\.\./+[\w/.\-]+\.(?:jfif|webp|jpe?g))", re.I)

def resolve(md_path, rel):
    return os.path.normpath(os.path.join(os.path.dirname(md_path), rel))

def to_png(src, dst):
    if os.path.exists(dst):
        return "already"
    for args in (
        ["convert", "-quiet", src, dst],
        ["ffmpeg", "-y", "-i", src, dst],
    ):
        try:
            r = subprocess.run(args, capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(dst):
                return args[0]
        except FileNotFoundError:
            continue
    return "FAILED"

def main():
    plan = {}  # dst_png -> dict
    for md in sorted(glob.glob(os.path.join(MD_DIR, "*.md"))):
        lines = open(md, encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            for m in IMG_RE.finditer(line):
                rel = m.group(1)
                src = resolve(md, rel)
                png = resolve(md, rel.rsplit(".", 1)[0] + ".png")
                rec = plan.get(png)
                if rec is None:
                    rec = plan[png] = {"src": src, "status": None, "count": 0, "mds": set()}
                rec["count"] += 1
                rec["mds"].add(os.path.basename(md))
        # замена ссылок в этом файле
        out = []
        for line in lines:
            def repl(m):
                rel = m.group(1)
                png = resolve(md, rel.rsplit(".", 1)[0] + ".png")
                newlink = rel.rsplit(".", 1)[0] + ".png"
                return newlink
            out.append(IMG_RE.sub(repl, line))
        open(md, "w", encoding="utf-8").write("\n".join(out))

    # конвертация (один раз на файл)
    for png, rec in plan.items():
        if os.path.exists(png):
            rec["status"] = "already"
        else:
            rec["status"] = to_png(rec["src"], png)

    for png, rec in sorted(plan.items()):
        print(f"{rec['status'] or '?':14s} {rec['count']}x  {png}")
        print(f"                ссылки: {', '.join(sorted(rec['mds']))}")

if __name__ == "__main__":
    main()
