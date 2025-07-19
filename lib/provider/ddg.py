import asyncio
import time
import base64
import json
import hashlib
import subprocess
import re
import os
import traceback
import filetype

from typing import Optional, List, Mapping, Union, Tuple
from PIL import Image
from io import BytesIO

import requests

CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))

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
        self.task_alive = None

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

        async def alive(delay: float): 
            while True: 
                try: 
                    resp = await self.__make_request(
                        "GET", 
                        self.main_url + "/duckchat/v1/status",
                        headers=headers, 
                    )
                    x_vqd_hash_1 = resp.headers.get("x-vqd-hash-1")
                    if not await self.make_xvqd_hash(x_vqd_hash_1): 
                        continue

                    self.x_vqd_hash_1 = x_vqd_hash_1
                    self.x_fe_version = await self.get_xfe_version()
                except requests.RequestException as e: 
                    print(f"[Alive Request Exception]: {e}")
                    pass
                except asyncio.CancelledError: 
                    break
                except Exception as e: 
                    print(f"[Alive Normal Exception]: {e}")
                    pass

                await asyncio.sleep(delay)
            
        loop = asyncio.get_event_loop()
        self.task_alive = loop.create_task(alive(5))

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
    
    async def make_xvqd_hash(self, xvqd_hash: str = "", source: str = "web") -> str: 
        try: 
            if source == "cmd": 
                result = subprocess.run(
                    ["node", CURRENT_FILE_DIR + "/utils/xvqd_hash.js", xvqd_hash or self.x_vqd_hash_1],
                    capture_output=True,
                    text=True
                )
                if result.stderr.strip(): 
                    print("[XVQD_ERROR_HASH] {result.stderr.strip()}")

                return result.stdout.strip()
            else: 
                headers = {
                    "content-type": "application/x-www-form-urlencoded"
                }
                params = {
                    "hash": xvqd_hash or self.x_vqd_hash_1
                }
                resp = await self.__make_request("GET", "https://gethash-api.vercel.app/get-hash", params=params, headers=headers)
                return resp.json().get("hash")
        except: 
            return ""

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
    
    async def extract_image(self, prompt_image: str) -> tuple[str, str]:
        def convert_to_webp(img_bytes: bytes) -> str:
            image = Image.open(BytesIO(img_bytes)).convert("RGB")
            buffer = BytesIO()
            image.save(buffer, format="WEBP")
            webp_bytes = buffer.getvalue()
            base64_webp = base64.b64encode(webp_bytes).decode("utf-8")
            return f"data:image/webp;base64,{base64_webp}"

        if prompt_image.startswith("data:"):
            # Contoh: data:image/png;base64,AAA...
            header, base64_data = prompt_image.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]

            # Jika sudah WebP, langsung return
            if mime_type == "image/webp":
                return mime_type, prompt_image

            # Jika bukan WebP, convert
            try:
                img_bytes = base64.b64decode(base64_data)
            except Exception as e:
                raise ValueError(f"Gagal decode base64 dari data URI: {e}")

            photo_uri = convert_to_webp(img_bytes)
            return "image/webp", photo_uri

        # Jika bukan data URI, anggap URL
        resp = await self.__make_request("GET", prompt_image)

        img_bytes = resp.content
        kind = filetype.guess(img_bytes)
        if kind is None or not kind.mime.startswith("image/"):
            raise ValueError("File bukan gambar yang valid.")

        photo_uri = convert_to_webp(img_bytes)
        return "image/webp", photo_uri
                
    async def chat_wrapper(
        self, 
        prompt: Union[str, Tuple[str, str]] = "Halo apakabar?",
        model: str = Model.GPT_O4_MINI,
        history: Optional[List[Mapping[str, str]]] = None,
    ) -> str: 
        headers = {
            "content-type": "application/json",
            "x-fe-version": self.x_fe_version,
            "x-vqd-hash-1": await self.make_xvqd_hash(),
            "x-fe-signals": self.make_fe_signals()
        }

        role = "user"
        prompt_text, prompt_image = None, None

        if history is None: 
            history = []
        
        if isinstance(prompt, tuple): 
            prompt_text, prompt_image = prompt
            mime_type, photo_uri = await self.extract_image(prompt_image)

            history.append({ "role": role, "content": [ { "type": "text", "text": prompt_text }, { "type": "image", "mimeType": mime_type, "image": photo_uri } ] })
        else: 
            prompt_text = prompt
            history.append({ "role": role, "content": prompt_text })

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

        x_vqd_hash_1 = resp.headers.get("x-vqd-hash-1")
        if await self.make_xvqd_hash(x_vqd_hash_1): 
            self.x_vqd_hash_1 = x_vqd_hash_1

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
        
        history[-1]["content"] = prompt_text

        role = "assistant"
        history.append({ "role": role, "content": resp_text })

        return resp_text

    async def chat(
        self, 
        prompt: Union[str, Tuple[str, str]] = "Halo apakabar?",
        model: str = Model.GPT_O4_MINI,
        history: Optional[List[Mapping[str, str]]] = [],
    ) -> str: 
        resp = ""
        if isinstance(prompt, tuple): 
            prompt_text, prompt_image = prompt

            if model != Model.GPT_4_DOT_0_MINI: 
                init_prompt = "Ekstrak isi dalam gambar ini secara menyeluruh"
                resp = await self.chat_wrapper(prompt=(init_prompt, prompt_image), model=Model.GPT_4_DOT_0_MINI)

                prompt_text = f"Deskripsi: {resp}\n\nPrompt: {prompt_text}"
                resp = await self.chat_wrapper(prompt=prompt_text, model=model, history=history)
            else: 
                resp = await self.chat_wrapper(prompt=(prompt_text, prompt_image), model=model, history=history)
        else: 
            resp = await self.chat_wrapper(prompt=prompt, model=model, history=history)
        
        return resp

    async def destroy(self): 
        self.task_alive.cancel()
        try:
            await self.task_alive
        except asyncio.CancelledError:
            pass  # Task dibatalkan dengan sukses

async def main(): 
    client = await DuckDuckGo.build()
    # history = []
    model = Model.GPT_4_DOT_0_MINI
    # prompt = ( "ini gambar apa?", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHqQAhr87cf9o3nfPj42O4loQ1oz8FBJIfJkYckRg2gjzwwu4BT3lqa4NVTDQpzIn7LFRhLPl9LJFL6qp_9i_f-A" )
    # prompt = ("ini gambar apa?", "data:image/webp;base64,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")
    # resp = await client.chat(prompt, model=model, history=history)
    # model = Model.GPT_O4_MINI
    # prompt = "Saya tadi nanya apa ke kamu? terus kamu jawab apa?"
    # resp = await client.chat(prompt, model=model, history=history)
    # print(resp)

    i = 0

    print(asyncio.all_tasks())
    while i < 25: 
        resp = await client.chat("hi apakabar, jam berapa sekarang dijakarta?",model=model)
        print(resp)
        await asyncio.sleep(1)
        i += 1
    await client.destroy()
    print(asyncio.all_tasks())

if __name__ == "__main__": 
    asyncio.run(main())
