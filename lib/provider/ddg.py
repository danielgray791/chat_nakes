import asyncio
import time
import base64
import json
import hashlib
import subprocess
import re

from typing import Optional, List, Mapping

import requests

class Model: 
    GPT_4_DOT_0_MINI = "gpt-4o-mini"
    LLAMA_4_SCOUT = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
    CLAUDE_3_DOT_5_HAIKU = "claude-3-5-haiku-latest"
    GPT_O4_MINI = "o4-mini"
    MISTRAL_SMALL = "mistralai/Mistral-Small-24B-Instruct-2501"

class DuckDuckGo: 
    def __init__(self): 
        self.main_url = "https://duckduckgo.com"
        self.cookies = { "dcm": "3", "dcs": "1" }
        self.headers = { 
            "referer": self.main_url + "/",
            "origin": self.main_url,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        self.x_vqd_hash_1 = ""
        self.x_fe_version = ""

    @classmethod
    async def build(cls) -> "DuckDuckGo": 
        instance = cls()
        await instance.__keep_alive()
        return instance

    async def __make_request(
        self, 
        method: str ="GET", 
        *args, 
        **kwargs
    ) -> requests.Response: 
        resp = None

        headers = self.headers.copy()
        headers.update(kwargs.get("headers", {}))
        kwargs["headers"] = headers

        cookies = self.cookies.copy()
        cookies.update(kwargs.get("cookies", {}))
        kwargs["cookies"] = cookies

        if method == "GET": 
            resp = await asyncio.to_thread(requests.get, *args, **kwargs)
            resp.raise_for_status()
        elif method == "POST": 
            resp = await asyncio.to_thread(requests.post, *args, **kwargs)
            resp.raise_for_status()

        return resp 

    async def __keep_alive(self) -> bool:  
        headers = {
            "x-vqd-accept": "1",
        }

        async def alive(): 
            while True: 
                try: 
                    resp = await self.__make_request(
                        "GET", 
                        self.main_url + "/duckchat/v1/status",
                        headers=headers, 
                    )

                    self.x_vqd_hash_1 = resp.headers.get("x-vqd-hash-1", self.x_vqd_hash_1)
                    self.x_fe_version = await self.get_xfe_version()
                except requests.RequestException as e: 
                    pass
                except Exception as e: 
                    pass

                await asyncio.sleep(60)
            
        loop = asyncio.get_event_loop()
        loop.create_task(alive())

        while not self.x_vqd_hash_1 and not self.x_fe_version: 
            await asyncio.sleep(0.25)

        return True

    def make_fe_signals(self) -> str: 
        payload = json.dumps({
            "start": int(time.time()),
            "events": [],
            "end": 93195
        })
        return base64.b64encode(payload.encode()).decode()
    
    async def make_xvqd_hash(self, source: str = "web") -> str: 
        if source == "cmd": 
            result = subprocess.run(
                ["node", "utils/xvqd_hash.js", self.x_vqd_hash_1],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        else: 
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
            }

            params = {
                "hash": self.x_vqd_hash_1
            }
            resp = await self.__make_request("GET", "https://gethash-api.vercel.app/get-hash", params=params)
            return resp.json().get("hash")

    async def get_xfe_version(self) -> str: 
        params = {
            "q": "DuckDuckGo+AI+Chat",
            "ia": "chat",
            "duckai": 1
        }

        resp = await self.__make_request("GET", self.main_url, params=params)
        xfe_match = re.search(r"__DDG_BE_VERSION__=\"(.+?)\",__DDG_FE_CHAT_HASH__=\"(.+?)\"", resp.text)
        
        if xfe_match: 
            be_version, fe_chat_hash = xfe_match.groups()
            return f"{be_version}-{fe_chat_hash}"
                
    
    async def chat(
        self, 
        prompt: str = "Halo apakabar?",
        model: str = Model.GPT_O4_MINI,
        history: Optional[List[Mapping[str, str]]] = [],
    ) -> str: 
        headers = {
            "content-type": "application/json",
            "x-fe-version": self.x_fe_version,
            "x-vqd-hash-1": await self.make_xvqd_hash(),
            "x-fe-signals": self.make_fe_signals()
        }

        role = "user"
        content = prompt
        
        history.append({ "role": role, "content": content })

        json_data = {
            'model': model,
            'metadata': {
                'toolChoice': {
                    'NewsSearch': False,
                    'VideosSearch': False,
                    'LocalSearch': False,
                    'WeatherForecast': False,
                },
            },
            'messages': history,
            'canUseTools': True,
            'canUseApproxLocation': True,
        }

        resp = await self.__make_request("POST", self.main_url + "/duckchat/v1/chat", headers=headers, json=json_data)
        resp.encoding = "utf-8"

        resp_text = ""
        for chunk in resp.text.splitlines(): 
            chunk = chunk.strip()[6:]

            if not chunk: 
                continue

            if chunk == "[DONE]": 
                break

            c_json = json.loads(chunk)
            c_action = c_json.get("action")
            c_msg = c_json.get("message") or ""

            if c_action != "success": 
                raise Exception(f"[CHAT] Exception: {c_action} ")
            
            resp_text += c_msg

        return resp_text

async def main(): 
    client = await DuckDuckGo.build()
    resp = await client.chat("apakah game24 bisa dibikin aturan game judi?")
    print(resp)

if __name__ == "__main__": 
    asyncio.run(main())
