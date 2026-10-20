from __future__ import annotations

import html
import os
import re
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring


ROOT = Path(__file__).resolve().parent
BASE_URL = os.environ["SITE_BASE_URL"].strip().rstrip("/")

DESCRIPTIONS = {
    "index.html": "Seby Official: ghid neoficial Drakensang Online în română, cu clase, echipamente, rune, pietre, evenimente și coduri promoționale.",
    "personaje.html": "Descoperă cele patru clase din Drakensang Online: Ranger, Dragonknight, Spellweaver și Steam Mechanicus, cu ghiduri pentru fiecare.",
    "ranger.html": "Ghid în română pentru Ranger în Drakensang Online: abilități, stil de joc, echipamente și idei de construcție.",
    "dragonknight.html": "Ghid în română pentru Dragonknight în Drakensang Online: abilități, stil de joc, echipamente și idei de construcție.",
    "spellweaver.html": "Ghid în română pentru Spellweaver în Drakensang Online: abilități, stil de joc, echipamente și idei de construcție.",
    "steam-mechanicus.html": "Ghid în română pentru Steam Mechanicus în Drakensang Online: abilități, stil de joc și idei de echipamente.",
    "echipamente.html": "Ghid de echipamente Drakensang Online: arme, armuri, mantale, bijuterii și sugestii pentru personajul tău.",
    "arme.html": "Ghid de arme Drakensang Online cu explicații despre tipuri, statistici și alegeri pentru clasele de personaje.",
    "armuri.html": "Ghid de armuri Drakensang Online: echipamente de apărare, statistici și idei pentru personajul tău.",
    "mantale.html": "Ghid de mantale Drakensang Online cu explicații și sugestii de echipare pentru aventurile din Dracania.",
    "bijuterii.html": "Ghid Drakensang Online pentru inele, amulete, centuri și bijuterii speciale, cu statistici și explicații.",
    "pietre.html": "Ghid de pietre prețioase Drakensang Online: tipuri, efecte și sfaturi pentru alegerea pietrelor potrivite.",
    "rune.html": "Ghid de rune Drakensang Online în română: efectele runelor și cum îți pot îmbunătăți personajul.",
    "harti.html": "Hărți și ghiduri Drakensang Online pentru explorarea zonelor, portalurilor și lumii Dracania.",
    "misiuni.html": "Ghid de misiuni Drakensang Online cu explicații pentru obiective și progresul aventurii.",
    "bossi.html": "Ghid pentru bossi Drakensang Online: pregătire, luptă și recomandări pentru înfruntarea șefilor.",
    "evenimente.html": "Calendar Drakensang Online cu evenimente, date de început și de sfârșit și anunțuri recente.",
    "coduri.html": "Coduri bonus Drakensang Online, recompensele oferite și datele de expirare verificate.",
    "noutati.html": "Cele mai recente noutăți Drakensang Online, rezumate în română și afișate pe Seby Official.",
    "grup-pvp.html": "Ghid de grup și PvP în Drakensang Online: joc în echipă, roluri și lupte între jucători.",
    "clasament.html": "Informații despre clasamentele comunității și activitățile PvP din Drakensang Online.",
}


def absolute_url(filename: str) -> str:
    return BASE_URL + ("/" if filename == "index.html" else f"/{filename}")


def prepare_page(path: Path) -> None:
    source = path.read_text(encoding="utf-8-sig")
    description = DESCRIPTIONS.get(path.name)
    if not description:
        return
    title_match = re.search(r"<title>(.*?)</title>", source, re.I | re.S)
    title = html.unescape(title_match.group(1).strip()) if title_match else "Seby Official"
    canonical = absolute_url(path.name)
    head_match = re.search(r"<head\b[^>]*>(.*?)</head>", source, re.I | re.S)
    if not head_match:
        return
    head = head_match.group(1)
    head = re.sub(r"\s*<meta\s+name=['\"]description['\"][^>]*>", "", head, flags=re.I)
    head = re.sub(r"\s*<link\s+rel=['\"]canonical['\"][^>]*>", "", head, flags=re.I)
    head = re.sub(r"\s*<meta\s+property=['\"]og:(?:title|description|type|url)['\"][^>]*>", "", head, flags=re.I)
    tags = (
        f'\n  <meta name="description" content="{html.escape(description, quote=True)}">'
        f'\n  <link rel="canonical" href="{html.escape(canonical, quote=True)}">'
        f'\n  <meta property="og:title" content="{html.escape(title, quote=True)}">'
        f'\n  <meta property="og:description" content="{html.escape(description, quote=True)}">'
        '\n  <meta property="og:type" content="website">'
        f'\n  <meta property="og:url" content="{html.escape(canonical, quote=True)}">'
    )
    source = source[:head_match.start(1)] + head + tags + source[head_match.end(1):]
    path.write_text(source, encoding="utf-8")


pages = sorted(path for path in ROOT.glob("*.html") if path.name in DESCRIPTIONS)
for page in pages:
    prepare_page(page)

urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
for page in pages:
    url = SubElement(urlset, "url")
    SubElement(url, "loc").text = absolute_url(page.name)
(ROOT / "sitemap.xml").write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(urlset, encoding="utf-8"))
(ROOT / "robots.txt").write_text(
    f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n",
    encoding="utf-8",
)
