import json
from pathlib import Path

from server import collect_updates


ROOT = Path(__file__).resolve().parent
payload = collect_updates()
(ROOT / "updates.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Feed saved: {len(payload.get('codes', []))} codes, {len(payload.get('events', []))} event notices")
