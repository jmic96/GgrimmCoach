import re
TURN_RE   = re.compile(r"\|turn\|(\d+)")
MOVE_RE   = re.compile(r"\|move\|p([12])a: ([^|]+)\|([^|]+)\|")
SWITCH_RE = re.compile(r"\|switch\|p([12])a: ([^|]+)\|")

class BattleState:
    def __init__(self):
        self.turn = 0
        self.active = {"us": None, "opp": None}
        self.revealed = {"us": set(), "opp": set()}

    def ingest_log(self, text: str):
        m = TURN_RE.findall(text)
        if m: self.turn = int(m[-1])
        for side, mon in SWITCH_RE.findall(text):
            self.active["us" if side=="1" else "opp"] = mon
        for side, mon, mv in MOVE_RE.findall(text):
            self.revealed["us" if side=="1" else "opp"].add(mv)
