import json, re

ILLEGAL_TEXT = re.compile(r"(Z\-?Move|Dynamax|Gigantamax|Mega|OHKO|Fissure|Sheer Cold|Horn Drill|Guillotine)", re.I)

class Legality:
    def __init__(self, format_dir: str):
        # format_dir contains: format.json, learnsets_sv.json, moves.json, abilities.json, items.json, species_types.json, usage_sets.json
        self.format = json.load(open(f"{format_dir}/format.json","r",encoding="utf-8"))
        self.learn  = json.load(open(f"{format_dir}/learnsets_sv.json","r",encoding="utf-8"))
        self.moves  = json.load(open(f"{format_dir}/moves.json","r",encoding="utf-8"))
        self.items  = json.load(open(f"{format_dir}/items.json","r",encoding="utf-8"))
        self.abilities = json.load(open(f"{format_dir}/abilities.json","r",encoding="utf-8"))
        self.species_types = json.load(open(f"{format_dir}/species_types.json","r",encoding="utf-8"))
        self.banned_items = set(self.format.get("banned_items", []))
        self.banned_mech  = set(m.lower() for m in self.format.get("banned_mechanics", []))
        self.clauses      = self.format.get("clauses", [])

    def pokemon_has_move(self, species: str, move: str) -> bool:
        return move in self.learn.get(species, [])

    def team_item_ok(self, item: str) -> bool:
        return (not item) or (item in self.items and item not in self.banned_items)

    def sanitize(self, s: str) -> str:
        if ILLEGAL_TEXT.search(s or ""):
            return "Play safe & legal for SV. Illegal mechanic mentioned."
        return (s or "").replace("\n", " ").strip()[:300]

    def explain_format(self) -> str:
        return f"{self.format['name']}: bans={sorted(self.banned_mech)} items={sorted(self.banned_items)} clauses={self.clauses}"
