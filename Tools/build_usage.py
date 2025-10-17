import os, re, json, requests
from tqdm import tqdm

# Smogon monthly usage stats text files are public; you can configure the month here.
# Example endpoint pattern (adjust month/paths as needed):
# https://www.smogon.com/stats/2025-09/moveset/monotype-1825.txt
MONTH = os.environ.get("GGRIMM_USAGE_MONTH","2025-09")
FORMATS = {
    "monotype":"monotype-1825",
    "ou":"ou-1825","ubers":"ubers-1825","uu":"uu-1825","ru":"ru-1825","nu":"nu-1825","pu":"pu-1825","lc":"lc-0"
}
OUT = os.path.join(os.path.dirname(__file__), "..", "packs")

def fetch_moveset(fmt_key, ladder_tag):
    url = f"https://www.smogon.com/stats/{MONTH}/moveset/{ladder_tag}.txt"
    r = requests.get(url, timeout=60); r.raise_for_status()
    return r.text

def parse_block(block: str):
    # very rough parser: extract Moves lines with percentages (top 4)
    lines = block.splitlines()
    name = lines[0].strip().strip("|").strip()
    moves = []
    capture = False
    for ln in lines:
        if ln.strip().startswith("| Moves"):
            capture = True; continue
        if capture:
            if ln.strip().startswith("|"):
                # |    Move Name | 45.6% |
                parts = [p.strip() for p in ln.split("|") if p.strip()]
                if len(parts)>=2 and parts[0] and re.search(r"%", ln):
                    mv = parts[0]
                    pct = re.findall(r"([\d\.]+)%", ln)
                    p = float(pct[0]) if pct else 0.0
                    moves.append((mv,p))
            else:
                break
    moves.sort(key=lambda x: -x[1])
    top_moves = [m for m,_ in moves[:8]]  # we’ll keep 8 and later choose 4 in engine
    weight = 1.0
    return name, {"weight": weight, "moves": top_moves}

def parse_all(text: str):
    entries = {}
    blocks = text.split("\n +----------------------------------------+ \n")
    for b in blocks:
        b = b.strip()
        if not b: continue
        try:
            name, data = parse_block(b)
            entries.setdefault(name, [])
            entries[name].append(data)
        except:
            continue
    return entries

for fmt_key, ladder in FORMATS.items():
    try:
        txt = fetch_moveset(fmt_key, ladder)
        parsed = parse_all(txt)
        outdir = os.path.join(OUT, fmt_key)
        json.dump(parsed, open(os.path.join(outdir,"usage_sets.json"),"w",encoding="utf-8"), indent=2)
        print(f"Wrote {fmt_key}/usage_sets.json with {len(parsed)} species.")
    except Exception as e:
        print(f"[warn] {fmt_key}: {e} (you can rerun later)")
