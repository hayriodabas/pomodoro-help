#!/usr/bin/env python3
"""Builds the Pomodoro help and privacy pages from content/*.json.

    python3 build.py

Writes index.html, help.html and privacy.html at the root (English, with the
list of languages) and <locale>/help.html, <locale>/privacy.html for every
content file. The store and the app link to the two root pages; each page
links to the same page in every other language.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://hayriodabas.github.io/pomodoro-help/"
ORDER = ["en", "de", "fr", "es", "it", "pt", "nl", "ja", "ko", "zh", "ru", "tr"]

CSS = """
:root {
  color-scheme: light dark;
  --desk: #F5F0E6; --sheet: #FFFCF6; --well: #EBE4D6; --ink: #231F1B; --soft: #6A6257;
  --rule: #D9D0C0; --tomato: #BE3320; --rest: #146C6B;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --desk: #161412; --sheet: #211E1A; --well: #2B2722; --ink: #F1EBDF; --soft: #A79F92;
    --rule: #3A342D; --tomato: #E2604A; --rest: #58B3AF;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--desk); color: var(--ink);
  font: 17px/1.6 ui-rounded, -apple-system, "SF Pro Rounded", "Hiragino Maru Gothic ProN", system-ui, sans-serif; }
a { color: var(--tomato); text-underline-offset: 2px; }
.wrap { max-width: 720px; margin: 0 auto; padding: 28px 16px 64px; }
.top { display: flex; gap: 18px; align-items: center; }
.top svg { width: 92px; height: 92px; flex: none; }
.top h1 { margin: 0; font-size: 30px; line-height: 1.15; letter-spacing: -0.01em; }
.lede { color: var(--soft); margin: 14px 0 18px; }
.tabs { display: flex; gap: 8px; margin: 0 0 22px; }
.tabs a { text-decoration: none; padding: 7px 16px; border-radius: 999px; border: 1.5px solid var(--rule);
  color: var(--ink); font-weight: 600; font-size: 15px; }
.tabs a[aria-current] { background: var(--tomato); border-color: var(--tomato); color: #fff; }
.suggest { display: none; margin: 0 0 18px; padding: 10px 14px; border-radius: 12px; background: var(--well); }
.suggest.on { display: block; }
.sheet { background: var(--sheet); border: 1px solid var(--rule); border-radius: 18px; padding: 6px 20px 14px;
  margin: 0 0 16px; }
.sheet h2 { font-size: 19px; margin: 14px 0 6px; display: flex; align-items: center; gap: 10px; }
.sheet h2::before { content: ""; width: 14px; height: 14px; border-radius: 4px; border: 2px solid var(--tomato); flex: none; }
.sheet p { margin: 0; padding: 9px 0; border-top: 1px solid var(--rule); }
.sheet h2 + p { border-top: 0; }
details { border-top: 1px solid var(--rule); padding: 10px 0; }
.sheet h2 + details { border-top: 0; }
summary { cursor: pointer; font-weight: 600; }
details p { border: 0; padding: 6px 0 0; color: var(--ink); }
.updated { color: var(--soft); font-size: 14px; margin: -8px 0 18px; }
.langs { margin-top: 28px; font-size: 15px; color: var(--soft); }
.langs ul { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-wrap: wrap; gap: 6px 14px; }
.langs a[aria-current] { color: var(--ink); font-weight: 700; text-decoration: none; }
footer { margin-top: 26px; color: var(--soft); font-size: 14px; }
@media (max-width: 420px) { .top svg { width: 72px; height: 72px; } .top h1 { font-size: 25px; } }
"""


def dial_svg() -> str:
    """The app's kitchen-timer face, wound to 25 minutes."""
    import math
    ticks = []
    for m in range(60):
        a = math.radians(m * 6 - 90)
        inner = 41 if m % 5 else 38
        ticks.append(f'<line x1="{50 + inner * math.cos(a):.2f}" y1="{50 + inner * math.sin(a):.2f}" '
                     f'x2="{50 + 45 * math.cos(a):.2f}" y2="{50 + 45 * math.sin(a):.2f}" '
                     f'stroke="var(--ink)" stroke-width="{1.6 if m % 5 == 0 else 0.7}" stroke-linecap="round"/>')
    end = math.radians(25 * 6 - 90)
    x, y = 50 + 32 * math.cos(end), 50 + 32 * math.sin(end)
    wedge = f'<path d="M50 50 L50 18 A32 32 0 0 1 {x:.2f} {y:.2f} Z" fill="var(--tomato)"/>'
    hx, hy = 50 + 32 * math.cos(end), 50 + 32 * math.sin(end)
    return ('<svg viewBox="0 0 100 100" aria-hidden="true">'
            '<circle cx="50" cy="50" r="48" fill="var(--sheet)" stroke="var(--rule)" stroke-width="1.5"/>'
            + "".join(ticks) +
            '<circle cx="50" cy="50" r="32" fill="var(--well)"/>' + wedge +
            f'<circle cx="{hx:.2f}" cy="{hy:.2f}" r="4" fill="var(--sheet)" stroke="var(--tomato)" stroke-width="2"/>'
            '<circle cx="50" cy="50" r="14" fill="var(--sheet)"/></svg>')


def load() -> tuple[dict, list[dict]]:
    ui = json.loads((ROOT / "content" / "ui.json").read_text(encoding="utf-8"))
    langs = []
    for key in ORDER:
        path = ROOT / "content" / f"{key}.json"
        if path.is_file():
            d = json.loads(path.read_text(encoding="utf-8"))
            d["key"] = key
            langs.append(d)
    return ui, langs


def contact(d: dict, ui: dict) -> str:
    mail = ui["contact_email"]
    link = f'<a href="mailto:{html.escape(mail)}">{html.escape(mail)}</a>'
    return d["contact"]["p"].replace("{email}", link)


def page(d: dict, ui: dict, langs: list[dict], kind: str, root: bool) -> str:
    body = d[kind]
    prefix = "" if root else "../"
    here = f"{kind}.html" if root else f"{d['locale']}/{kind}.html"
    parts = [f'<div class="top">{dial_svg()}<h1>{body["title"]}</h1></div>']
    if kind == "privacy":
        parts.append(f'<p class="updated">{body["updated"]}</p>')
    parts.append(f'<p class="lede">{body["lede"]}</p>')
    help_href = "help.html"
    priv_href = "privacy.html"
    on = ' aria-current="page"'
    help_cur = on if kind == "help" else ""
    priv_cur = on if kind == "privacy" else ""
    parts.append('<nav class="tabs">'
                 f'<a href="{help_href}"{help_cur}>{d["nav"]["help"]}</a>'
                 f'<a href="{priv_href}"{priv_cur}>{d["nav"]["privacy"]}</a>'
                 '</nav>')
    if root:
        parts.append('<p class="suggest" id="suggest"></p>')
    for s in body["sections"]:
        parts.append('<section class="sheet"><h2>' + s["h"] + "</h2>" + "".join(f"<p>{p}</p>" for p in s["p"]) + "</section>")
    if kind == "help":
        items = "".join(f"<details><summary>{q['q']}</summary><p>{q['a']}</p></details>" for q in body["faq"])
        parts.append(f'<section class="sheet"><h2>{body["faq_h"]}</h2>{items}</section>')
    parts.append(f'<section class="sheet"><h2>{d["contact"]["h"]}</h2><p>{contact(d, ui)}</p></section>')
    links = []
    for other in langs:
        href = f"{prefix}{other['locale']}/{kind}.html"
        cur = ' aria-current="page"' if (other is d and not root) else ""
        links.append(f'<li><a href="{href}" hreflang="{other["html_lang"]}" lang="{other["html_lang"]}"{cur}>{other["label"]}</a></li>')
    parts.append(f'<nav class="langs" aria-label="{d["nav"]["languages"]}">{d["nav"]["languages"]}<ul>{"".join(links)}</ul></nav>')
    parts.append(f'<footer>{d["app"]} · <a href="{prefix}index.html">hayriodabas.github.io/pomodoro-help</a></footer>')
    alternates = "".join(f'<link rel="alternate" hreflang="{o["html_lang"]}" href="{BASE}{o["locale"]}/{kind}.html">' for o in langs)
    script = ""
    if root:
        table = {o["html_lang"]: [f"{o['locale']}/{kind}.html", o["suggest"]] for o in langs if o["key"] != "en"}
        script = ("<script>(function(){var t=" + json.dumps(table, ensure_ascii=False) +
                  ";var l=(navigator.languages||[navigator.language||'']);for(var i=0;i<l.length;i++){"
                  "var c=(l[i]||'').toLowerCase(),k=c.indexOf('zh')===0?'zh-Hans':c.indexOf('pt')===0?'pt-BR':c.split('-')[0];"
                  "if(k==='en')return;if(t[k]){var e=document.getElementById('suggest');var a=document.createElement('a');"
                  "a.href=t[k][0];a.textContent=t[k][1];e.appendChild(a);e.className='suggest on';return;}}})();</script>")
    title = f"{body['title']}"
    return ("<!doctype html>\n"
            f'<html lang="{d["html_lang"]}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(title)}</title>"
            f'<link rel="canonical" href="{BASE}{here}">{alternates}'
            f'<link rel="icon" href="{prefix}assets/icon.png">'
            f"<style>{CSS}</style></head><body><main class=\"wrap\">"
            + "".join(parts) + f"</main>{script}</body></html>\n")


def index(ui: dict, langs: list[dict]) -> str:
    en = langs[0]
    rows = "".join(
        f'<p><b lang="{o["html_lang"]}">{o["label"]}</b> · <a href="{o["locale"]}/help.html">{o["nav"]["help"]}</a> · '
        f'<a href="{o["locale"]}/privacy.html">{o["nav"]["privacy"]}</a></p>' for o in langs)
    return ("<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Pomodoro</title><link rel="canonical" href="{BASE}"><link rel="icon" href="assets/icon.png">'
            f"<style>{CSS}</style></head><body><main class=\"wrap\">"
            f'<div class="top">{dial_svg()}<h1>Pomodoro</h1></div>'
            f'<p class="lede">{en["help"]["lede"]}</p>'
            '<nav class="tabs"><a href="help.html">Help</a><a href="privacy.html">Privacy</a></nav>'
            f'<section class="sheet"><h2>{en["nav"]["languages"]}</h2>{rows}</section>'
            "</main></body></html>\n")


def main() -> None:
    ui, langs = load()
    assert langs and langs[0]["key"] == "en"
    count = 0
    for d in langs:
        folder = ROOT / d["locale"]
        folder.mkdir(exist_ok=True)
        for kind in ("help", "privacy"):
            (folder / f"{kind}.html").write_text(page(d, ui, langs, kind, root=False), encoding="utf-8")
            count += 1
    for kind in ("help", "privacy"):
        (ROOT / f"{kind}.html").write_text(page(langs[0], ui, langs, kind, root=True), encoding="utf-8")
        count += 1
    (ROOT / "index.html").write_text(index(ui, langs), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"{count + 1} pages, {len(langs)} languages")


if __name__ == "__main__":
    main()
