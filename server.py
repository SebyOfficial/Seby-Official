from __future__ import annotations

import json
import re
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
NEWS_URL = "https://www.drakensang.com/en/news"
FORUM_URL = "https://board-en.drakensang.com/forums/event-announcements.120/"
BONUS_CODES_URL = "https://board-en.drakensang.com/threads/bonusove-kody.88869/page-4"
USER_AGENT = "SebyOfficialFanSite/1.0 (official public news reader)"
CACHE_SECONDS = 60
cache_lock = threading.Lock()
cache_data = None
cache_time = 0.0


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            self.current = {"href": href, "text": []}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.current["text"] = " ".join(" ".join(self.current["text"]).split())
            self.links.append(self.current)
            self.current = None


class TextParser(HTMLParser):
    BLOCKS = {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "section"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
        if not self.skip and tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1
        if not self.skip and tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(request, timeout=14) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read(2_500_000).decode(charset, errors="replace")


def page_text(markup: str) -> str:
    parser = TextParser()
    parser.feed(markup)
    return parser.text()


def date_from_validity(value: str):
    cleaned = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", value, flags=re.I)
    candidates = re.findall(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b|\b[A-Za-z]+\s+\d{1,2},?\s+\d{4}\b", cleaned)
    formats = ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y")
    for candidate in candidates:
        for fmt in formats:
            try:
                return datetime.strptime(candidate.replace(",", ""), fmt).date()
            except ValueError:
                pass
    return None


def extract_codes(title: str, text: str):
    results = []
    pattern = re.compile(r"\b(?:BONUS\s+)?CODES?\s*[:(]\s*([A-Z0-9][A-Z0-9_-]{2,}(?:\s*(?:&|,|and)\s*[A-Z0-9][A-Z0-9_-]{2,})*)", re.I)
    # Only take codes from the article title. The official news page repeats
    # other stories in its sidebar, which otherwise pollutes article results.
    for match in pattern.finditer(title):
        for code in re.split(r"\s*(?:&|,|and)\s*", match.group(1), flags=re.I):
            code = code.strip().rstrip(")").upper()
            if code and code not in results:
                results.append(code)
    validity = ""
    for line in text.splitlines():
        if re.search(r"\bvalid\s+(?:till|until|through)\b", line, re.I):
            validity = line[:220]
            break
    expiry = date_from_validity(validity)
    return [{"code": code, "validity": validity, "expired": bool(expiry and expiry < date.today())} for code in results]


def article_links(markup: str):
    parser = LinkParser()
    parser.feed(markup)
    found = []
    seen = set()
    for item in parser.links:
        href = urljoin(NEWS_URL, item["href"])
        title = item["text"].strip()
        if "/en/news/" not in urlparse(href).path or not title or href in seen:
            continue
        seen.add(href)
        found.append({"title": title, "url": href})
    return found[:18]


def read_article(item):
    try:
        text = page_text(fetch(item["url"]))
    except Exception:
        text = ""
    title = item["title"]
    date_match = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b", text)
    duration = ""
    for line in text.splitlines():
        if re.search(r"event duration\s*:", line, re.I):
            duration = line[:240]
            break
    item.update({"date": date_match.group(0) if date_match else "", "codes": extract_codes(title, text), "duration": duration, "summary": " ".join(text.split())[:260]})
    return item


def read_forum_schedule():
    try:
        markup = fetch(FORUM_URL)
        parser = LinkParser()
        parser.feed(markup)
        links = parser.links
        monthly = None
        for link in links:
            label = link["text"]
            if re.search(r"events? coming in [A-Za-z]+", label, re.I) and "/threads/" in link["href"]:
                monthly = {"title": label, "url": urljoin(FORUM_URL, link["href"])}
                break
        if not monthly:
            return {"title": "", "url": FORUM_URL, "items": []}
        text = page_text(fetch(monthly["url"]))
        schedule = []
        previous = ""
        today = date.today()
        for line in text.splitlines():
            if re.search(r"\b\d{1,2}[./-]\d{1,2}\b.*\b\d{1,2}:\d{2}\b", line):
                event_name = previous.strip(" •*⚜️") or "Eveniment Drakensang Online"
                # Keep only items that have not finished yet; the current year is the calendar's year.
                dates = re.findall(r"(\d{1,2})[./-](\d{1,2})", line)
                if dates:
                    try:
                        end_day, end_month = map(int, dates[-1])
                        end_date = date(today.year, end_month, end_day)
                        if end_date >= today:
                            schedule.append({"title": event_name, "duration": line[:200], "url": monthly["url"]})
                    except ValueError:
                        schedule.append({"title": event_name, "duration": line[:200], "url": monthly["url"]})
                previous = ""
            elif line and not re.search(r"events? coming|all times|times may change|disclaimer|heroes of dracania|your drakensang", line, re.I):
                previous = line
        return {"title": monthly["title"], "url": monthly["url"], "items": schedule[:35]}
    except Exception:
        return {"title": "", "url": FORUM_URL, "items": []}


def read_moderator_codes():
    """Read the current code details posted by the DSO moderator."""
    rewards = {
        "99IPS": "Recompensă: 99 fragmente de trecere infernală.",
        "COINS50": "Recompensă: 50 de monede ale comunității.",
        "DRAGONBONES": "Recompensă: 50 de oase de dragon.",
        "6KEYS": "Recompensă: 6 chei de amforă.",
        "LUCKY3PEARLS": "Recompensă: 3 perle blestemate împuternicite.",
        "DRAGANNEWJEWEL": "Recompensă: 2 perle blestemate împuternicite.",
        "2PEARLS": "Recompensă: 2 perle blestemate împuternicite.",
    }
    try:
        text = page_text(fetch(BONUS_CODES_URL))
    except Exception:
        return []
    expiry_match = re.search(r"12[./]11[./]2026", text)
    if not expiry_match:
        return []
    return [
        {
            "code": code,
            "title": "Cod bonus Drakensang Online",
            "validity": f"{reward} · valabil până la 12.11.2026.",
            "expired": date.today() > date(2026, 11, 12),
            "url": BONUS_CODES_URL,
        }
        for code, reward in rewards.items()
        if re.search(rf"\b{re.escape(code)}\b", text)
    ]


def collect_updates():
    errors = []
    try:
        items = article_links(fetch(NEWS_URL))
    except Exception as exc:
        items = []
        errors.append("Nu am putut citi site-ul oficial de știri: " + type(exc).__name__)
    articles = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(read_article, item) for item in items[:12]]
        for future in as_completed(futures):
            try:
                articles.append(future.result())
            except Exception:
                pass
    order = {item["url"]: index for index, item in enumerate(items)}
    articles.sort(key=lambda item: order.get(item["url"], 999))
    codes = read_moderator_codes()
    for article in articles:
        for code in article.get("codes", []):
            if not any(existing["code"] == code["code"] for existing in codes):
                codes.append({**code, "title": article["title"], "url": article["url"]})
    events = [article for article in articles if article.get("duration") or re.search(r"event|festival|season pass", article["title"], re.I)]
    return {"checkedAt": datetime.now().astimezone().isoformat(timespec="minutes"), "codes": codes, "events": events[:12], "schedule": read_forum_schedule(), "news": articles[:12], "errors": errors, "sources": {"news": NEWS_URL, "forum": FORUM_URL, "codes": BONUS_CODES_URL}}


def updates(force=False):
    global cache_data, cache_time
    with cache_lock:
        if not force and cache_data and time.time() - cache_time < CACHE_SECONDS:
            return cache_data
    value = collect_updates()
    with cache_lock:
        cache_data, cache_time = value, time.time()
    return value


class SiteHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/updates"):
            force = "refresh=1" in self.path
            payload = json.dumps(updates(force), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()


if __name__ == "__main__":
    handler = partial(SiteHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 8765), handler)
    print("Seby Official rulează la http://127.0.0.1:8765")
    print("Lasă această fereastră deschisă cât timp folosești site-ul. Oprește cu Ctrl+C.")
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer oprit.")
        server.server_close()
