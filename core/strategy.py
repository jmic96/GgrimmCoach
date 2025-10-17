from typing import List, Dict

COACH_SYSTEM = """You are a top-tier competitive coach for SV Gen 9 formats (OU/Ubers/UU/RU/NU/PU/LC/Monotype).
Return 1–3 short sentences, plain English, no lists or JSON. Be decisive and legal (respect clauses/bans).
Only mention moves that are actually available to the user's active Pokémon.
"""

def ensure_types(name: str, info: Dict) -> List[str]:
    t = info.get("types", [])
    if not t: raise ValueError(f"Missing types for {name}")
    return t

class StrategyEngine:
    def __init__(self, legality, set_infer, damage_client, llm_client, rules_text: str):
        self.legality = legality
        self.sets = set_infer
        self.dmg = damage_client
        self.llm = llm_client
        self.rules_text = rules_text
        self._opp_view = None

    def set_opp_view(self, opp_view_dict):
        self._opp_view = opp_view_dict

    async def _ev_for_move(self, my_view, opp_view, my_move: str, opp_moves: List[str]) -> float:
        try:
            rng, _ = await self.dmg.range(my_view, opp_view, my_move)
            my_dmg = sum(rng)/2.0
        except: my_dmg = 30.0
        best = 0.0
        for om in opp_moves[:4]:
            try:
                rng2, _ = await self.dmg.range(opp_view, my_view, om)
                opp_dmg = sum(rng2)/2.0
                if opp_dmg > best: best = opp_dmg
            except: pass
        return my_dmg - best

    async def advise(self, state, my_team, my_active_name: str, opp_name: str):
        my_info = next((v for k,v in my_team.items() if my_active_name and (my_active_name.lower() in k.lower() or k.lower() in my_active_name.lower())), None)
        if not my_info: return "Active set unknown—pivot safely."
        my_types = ensure_types(my_active_name, my_info)
        my_moves = my_info.get("moves", [])
        if not my_moves: return "No moves recorded—pivot or scout safely."
        if my_info.get("item") and not self.legality.team_item_ok(my_info["item"]):
            return "Your item looks banned in this format; switch or play conservatively until fixed."

        opp_sets = self.sets.top_sets(opp_name, k=5)
        opp_moves_union = []
        for s in opp_sets:
            for m in s.get("moves", []):
                if m not in opp_moves_union:
                    opp_moves_union.append(m)
        if not opp_moves_union:
            opp_moves_union = ["Earthquake","Knock Off","Stone Edge","U-turn"]  # fallback

        my_view = {
            "name": my_active_name, "level": 100,
            "item": my_info.get("item",""), "ability": my_info.get("ability",""), "nature": "Hardy",
            "evs": my_info.get("evs", {}), "ivs": my_info.get("ivs", {}),
            "types": my_types, "teraType": my_info.get("tera_type")
        }
        opp_view = self._opp_view

        # Depth-2 EV (our move vs best opp reply from union)
        evs = []
        for mv in my_moves:
            ev = await self._ev_for_move(my_view, opp_view, mv, opp_moves_union)
            evs.append((ev, mv))
        evs.sort(reverse=True)
        best_ev, best_move = evs[0]

        user_prompt = f"""Turn {state.turn}. You: {my_active_name} [{", ".join(my_types)}] with moves {", ".join(my_moves)}.
Opponent: {opp_name} [{", ".join(opp_view["types"])}].
Top candidate: {best_move} (EV {best_ev:.1f}). Format: {self.rules_text}. Give concise advice now."""
        text = await self.llm.coach(COACH_SYSTEM, user_prompt)
        return self.legality.sanitize(text)
