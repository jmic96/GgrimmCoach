import os, json, zipfile, io, requests, re
from tqdm import tqdm

# Sources (Showdown main repo provides structured data):
PS_ZIP = "https://github.com/smogon/pokemon-showdown/archive/refs/heads/master.zip"

# Output formats we support
FORMATS = {
    "monotype": {
        "name":"SV Monotype",
        "banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],
        "banned_items":["Booster Energy"],
        "clauses":["Sleep Clause Mod","Evasion Clause","OHKO Clause","Endless Battle Clause","Species Clause"]
    },
    "ou":     {"name":"SV OU","banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],"banned_items":[],"clauses":["Sleep Clause Mod","Species Clause","Evasion Clause","OHKO Clause","Endless Battle Clause"]},
    "ubers":  {"name":"SV Ubers","banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],"banned_items":[],"clauses":["Sleep Clause Mod","Species Clause","Evasion Clause","OHKO Clause","Endless Battle Clause"]},
    "uu":     {"name":"SV UU","banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],"banned_items":[],"clauses":["Sleep Clause Mod","Species Clause","Evasion Clause","OHKO Clause","Endless Battle Clause"]},
    "ru":     {"name":"SV RU","banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],"banned_items":[],"clauses":["Sleep Clause Mod","Species Clause","Evasion Clause","OHKO Clause","Endless Battle Clause"]},
    "nu":     {"name":"SV NU","banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],"banned_items":[],"clauses":["Sleep Clause Mod","Species Clause","Evasion Clause","OHKO Clause","Endless Battle Clause"]},
    "pu":     {"name":"SV PU","banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],"banned_items":[],"clauses":["Sleep Clause Mod","Species Clause","Evasion Clause","OHKO Clause","Endless Battle Clause"]},
    "lc":     {"name":"SV LC","banned_mechanics":["ZMove","Mega","Dynamax","OHKO"],"banned_items":[],"clauses":["Sleep Clause Mod","Species Clause","Evasion Clause","OHKO Clause","Endless Battle Clause"]}
}

OUT = os.path.join(os.path.dirname(__file__), "..", "packs")

def ensure_dir(p): os.makedirs(p, exist_ok=True)

print("Downloading Pokémon Showdown data…")
r = requests.get(PS_ZIP, timeout=60); r.raise_for_status()
zf = zipfile.ZipFile(io.BytesIO(r.content))
files = zf.namelist()

def read_json(path):
    with zf.open(path) as f:
        return json.load(io.TextIOWrapper(f, encoding="utf-8"))

# key SV data paths (showdown repo layout)
base = [p for p in files if p.endswith("data/") and "pokemon-showdown-master/" in p][0]
moves_path     = base + "data/moves.json"
abilities_path = base + "data/abilities.json"
items_path     = base + "data/items.json"
species_path   = base + "data/pokedex.json"
learnsets_path = base + "data/learnsets.json"
types_path     = base + "data/types.json"

moves = read_json(moves_path)
abilities = read_json(abilities_path)
items = read_json(items_path)
species = read_json(species_path)
learnsets = read_json(learnsets_path)
types = read_json(types_path)

# Normalize into friendly “name → …” mappings
def to_name_map(d):
    out={}
    for k,v in d.items():
        name = v.get("name") or k
        out[name] = v
    return out

moves_map = to_name_map(moves)
abilities_map = to_name_map(abilities)
items_map = to_name_map(items)

# Species types (name → [Type1, Type2?])
species_types={}
for k, v in species.items():
    name = v.get("name") or k
    t = v.get("types") or []
    species_types[name] = t

# Learnsets (name → [move names]) for SV species
learnsets_sv={}
for k, v in learnsets.items():
    name = v.get("name") or k
    ls = []
    for mv, info in (v.get("learnset") or {}).items():
        # Showdown uses ids (lowercase no spaces); moves.json contains name fields
        # reverse lookup by matching id on moves dict key
        for mk, mval in moves.items():
            if mk == mv:
                ls.append(mval.get("name") or mk)
                break
    if ls:
        learnsets_sv[name] = sorted(set(ls))

# Write packs per format
for fmt_key, meta in FORMATS.items():
    outdir = os.path.join(OUT, fmt_key)
    ensure_dir(outdir)
    json.dump({"name":meta["name"],"banned_mechanics":meta["banned_mechanics"],"banned_items":meta["banned_items"],"clauses":meta["clauses"]}, open(os.path.join(outdir,"format.json"),"w",encoding="utf-8"), indent=2)
    json.dump({k:{"bp":v.get("basePower",0),"type":v.get("type","Normal"),"category":v.get("category","Status")} for k,v in moves_map.items()}, open(os.path.join(outdir,"moves.json"),"w",encoding="utf-8"), indent=2)
    json.dump({k:True for k in abilities_map.keys()}, open(os.path.join(outdir,"abilities.json"),"w",encoding="utf-8"), indent=2)
    json.dump({k:True for k in items_map.keys()}, open(os.path.join(outdir,"items.json"),"w",encoding="utf-8"), indent=2)
    json.dump(species_types, open(os.path.join(outdir,"species_types.json"),"w",encoding="utf-8"), indent=2)
    json.dump(learnsets_sv, open(os.path.join(outdir,"learnsets_sv.json"),"w",encoding="utf-8"), indent=2)

print("Base packs built. Next: run tools/build_usage.py to create usage_sets.json for each format.")
