"""Optional: download a public copy of MTSamples into backend/data/mtsamples.csv.
A copy is already bundled; use this only if you deleted it or want a fresh one."""
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/socd06/medical-nlp/master/data/mtsamples.csv"
dest = Path(__file__).resolve().parents[1] / "backend" / "data" / "mtsamples.csv"
dest.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(URL, dest)
print("saved", dest, dest.stat().st_size, "bytes")
