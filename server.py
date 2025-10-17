import json, asyncio, os
from aiohttp import web
import websockets
from websockets.server import WebSocketServerProtocol

from core.legality import Legality
from core.ps_state import BattleState
from core.set_inference import SetInference
from core.damage_client import DamageClient
from core.llm_client import LLMClient
from core.strategy import StrategyEngine
from core.format_router import format_dir
from core.validator import validate_packs

HTTP_HOST, HTTP_PORT = "localhost", 6060
WS_HOST, WS_PORT = "localhost", 6061

# select format by env var or default to monotype
FORMAT = os.getenv("GGRIMM_FORMAT","monotype").lower()

def load_ctx(fmt: str):
    fdir = format_dir("packs", fmt)
    validate_packs(fdir)
    leg = Legality(fdir)
    sets = SetInference(fdir)
    return fdir, leg, sets

FORMAT_DIR, LEG, SETS = load_ctx(FORMAT)
DMG = DamageClient("http://localhost:7070/calc")
LLM = LLMClient(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"))

STATE = BattleState()
MY_TEAM = {}   # {name: {moves,item,ability,ivs,evs,types,tera_type}}
overlay_clients:set[WebSocketServerProtocol]=set()

def _resolve_types(species: str, given_types):
    if given_types: return given_types
    types_db = json.load(open(f"{FORMAT_DIR}/species_types.json","r",encoding="utf-8"))
    t = types_db.get(species)
    if not t:
        raise ValueError(f"Types missing for {species}; include 'Type:' in team or ensure species_types.json has it.")
    return t

async def ws_handler(ws: WebSocketServerProtocol):
    overlay_clients.add(ws)
    try: await ws.wait_closed()
    finally: overlay_clients.discard(ws)

async def broadcast(title, text):
    packet = json.dumps({"title": title, "analysis": text}, ensure_ascii=False)
    if overlay_clients:
        await asyncio.gather(*(c.send(packet) for c in list(overlay_clients)))

async def post_team(req: web.Request):
    global MY_TEAM
    txt = (await req.text()).strip()
    if not txt: return web.json_response({"ok":False,"error":"empty team"}, status=400)

    team = {}
    blocks = [b.strip() for b in txt.split("\n\n") if b.strip()]
    for b in blocks:
        lines=[l.rstrip() for l in b.splitlines() if l.strip()]
        name_line=lines[0]
        name = name_line.split("@")[0].strip()
        item = name_line.split("@")[1].strip() if "@" in name_line else ""
        ability=""; moves=[]; evs={}; ivs={}; tera=None; types=[]
        for l in lines[1:]:
            L=l.lower()
            if L.startswith("ability:"): ability=l.split(":",1)[1].strip()
            elif L.startswith("tera type:"): tera=l.split(":",1)[1].strip()
            elif L.startswith("evs:"): pass
            elif L.startswith("ivs:"): pass
            elif L.startswith("type:"): types=[t.strip() for t in l.split(":",1)[1].split("/")]
            elif l.startswith("- "): moves.append(l[2:].strip())
        types = _resolve_types(name, types)  # REQUIRED
        team[name]={"moves":moves[:4],"item":item,"ability":ability,"tera_type":tera,"evs":evs,"ivs":ivs,"types":types}

    MY_TEAM = team
    return web.json_response({"ok":True,"mons":list(MY_TEAM.keys())})

def _find_info_for(name: str):
    return next((v for k,v in MY_TEAM.items() if name and (name.lower() in k.lower() or k.lower() in name.lower())), None)

async def post_log(req: web.Request):
    txt = (await req.text()).strip()
    if not txt: return web.json_response({"ok":False,"error":"empty"}, status=400)
    STATE.ingest_log(txt)

    my_name = STATE.active["us"] or "(unknown)"
    opp_name= STATE.active["opp"] or "(unknown)"
    my_info = _find_info_for(my_name)
    opp_info= _find_info_for(opp_name)

    # Ensure opp types exist
    types_db = json.load(open(f"{FORMAT_DIR}/species_types.json","r",encoding="utf-8"))
    opp_types = opp_info.get("types", []) if opp_info else types_db.get(opp_name, [])
    if not opp_types:
        opp_types = types_db.get(opp_name, [])
    opp_view = {
        "name": opp_name, "level": 100, "item": (opp_info or {}).get("item",""),
        "ability": (opp_info or {}).get("ability",""), "nature": "Hardy",
        "evs": (opp_info or {}).get("evs", {}), "ivs": (opp_info or {}).get("ivs", {}),
        "types": opp_types, "teraType": (opp_info or {}).get("tera_type")
    }

    engine = StrategyEngine(LEG, SETS, DMG, LLM, LEG.explain_format())
    engine.set_opp_view(opp_view)
    advice = await engine.advise(STATE, MY_TEAM, my_name, opp_name)

    title = ("Lead" if STATE.turn==0 else f"Turn {STATE.turn}")
    await broadcast(title, advice)
    return web.json_response({"ok":True,"turn":STATE.turn,"advice":advice})

async def get_state(_):
    return web.json_response({
        "turn": STATE.turn,
        "active": STATE.active,
        "revealed": {k:list(v) for k,v in STATE.revealed.items()},
        "format": FORMAT
    })

async def panel_handler(_):
    html = open("panel.html","r",encoding="utf-8").read()
    return web.Response(text=html, content_type="text/html")

async def main():
    app = web.Application()
    app.router.add_post("/team", post_team)
    app.router.add_post("/log",  post_log)
    app.router.add_get ("/state", get_state)
    app.router.add_get ("/panel", panel_handler)

    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, HTTP_HOST, HTTP_PORT); await site.start()
    print(f"Open panel:   http://{HTTP_HOST}:{HTTP_PORT}/panel")
    print(f"POST /team:   http://{HTTP_HOST}:{HTTP_PORT}/team")
    print(f"POST /log:    http://{HTTP_HOST}:{HTTP_PORT}/log")
    print(f"GET  /state:  http://{HTTP_HOST}:{HTTP_PORT}/state")
    print(f"Format: {FORMAT} (override with GGRIMM_FORMAT env var)")

    ws_srv = websockets.serve(ws_handler, WS_HOST, WS_PORT, ping_interval=30, ping_timeout=60)
    async with ws_srv: await asyncio.Future()

if __name__=="__main__":
    asyncio.run(main())
