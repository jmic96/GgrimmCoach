import aiohttp

class DamageClient:
    def __init__(self, url="http://localhost:7070/calc"):
        self.url = url

    async def range(self, attacker, defender, move_name: str):
        async with aiohttp.ClientSession() as s:
            async with s.post(self.url, json={
                "attacker": attacker, "defender": defender, "move": move_name
            }, timeout=20) as r:
                data = await r.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("error","calc error"))
                return data["range"], data.get("desc","")
