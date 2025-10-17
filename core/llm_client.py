import os, json, aiohttp

class LLMClient:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.key = os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise RuntimeError("OPENAI_API_KEY not set")

    async def coach(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type":"application/json"}
        body = {"model": self.model, "messages":[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],"temperature":0.2}
        async with aiohttp.ClientSession() as s:
            async with s.post(url, headers=headers, data=json.dumps(body), timeout=25) as r:
                j = await r.json()
                return j["choices"][0]["message"]["content"].strip()
