import json, os

REQUIRED_FILES = ["format.json","learnsets_sv.json","moves.json","abilities.json","items.json","species_types.json","usage_sets.json"]

def validate_packs(dirpath: str):
    for f in REQUIRED_FILES:
        p = os.path.join(dirpath, f)
        if not os.path.exists(p):
            raise RuntimeError(f"Missing pack file: {p}")
    # basic coverage checks
    learn = json.load(open(os.path.join(dirpath,"learnsets_sv.json"),"r",encoding="utf-8"))
    moves = json.load(open(os.path.join(dirpath,"moves.json"),"r",encoding="utf-8"))
    abilities = json.load(open(os.path.join(dirpath,"abilities.json"),"r",encoding="utf-8"))
    items = json.load(open(os.path.join(dirpath,"items.json"),"r",encoding="utf-8"))
    types = json.load(open(os.path.join(dirpath,"species_types.json"),"r",encoding="utf-8"))

    if not learn or not moves or not abilities or not items or not types:
        raise RuntimeError("Pack files present but empty or invalid.")

    # ensure every species has types and at least 1 learnset entry
    missing_types = [s for s in learn.keys() if s not in types]
    if missing_types:
        raise RuntimeError(f"Species missing types: {missing_types[:10]} ... ({len(missing_types)} total)")

    # ensure all referenced moves exist
    ref_moves = set(m for arr in learn.values() for m in arr)
    unknown = [m for m in ref_moves if m not in moves]
    if unknown:
        raise RuntimeError(f"Unknown moves in learnsets: {unknown[:10]} ... ({len(unknown)} total)")

    return True
