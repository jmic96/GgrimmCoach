import json
from collections import defaultdict

class SetInference:
    def __init__(self, format_dir: str):
        self.usage = json.load(open(f"{format_dir}/usage_sets.json","r",encoding="utf-8"))

    def top_sets(self, species: str, k=5):
        return self.usage.get(species, [])[:k]

    def move_probs(self, species: str):
        dist = defaultdict(float)
        for entry in self.usage.get(species, []):
            w = float(entry.get("weight", 0))
            for mv in entry.get("moves", []):
                dist[mv] += w
        total = sum(dist.values()) or 1.0
        return {m: v/total for m,v in dist.items()}
