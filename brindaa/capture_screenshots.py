import os
import time
import json
import base64
import socket
import asyncio
import threading
import subprocess
import urllib.request
from http.server import SimpleHTTPRequestHandler, HTTPServer
import websockets

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

async def capture():
    http_port = find_free_port()
    server = HTTPServer(('127.0.0.1', http_port), SimpleHTTPRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    
    cdp_port = find_free_port()
    url = f"http://127.0.0.1:{http_port}/brinda-birthday-surprise.html"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = os.path.abspath("chrome_temp_profile_shot")
    
    cmd = [
        chrome_path,
        "--headless=new",
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        url
    ]
    proc = subprocess.Popen(cmd)
    
    for _ in range(20):
        time.sleep(0.4)
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json/list")
            pages = json.loads(req.read().decode())
            target_pages = [p for p in pages if p.get("type") == "page"]
            if target_pages:
                ws_url = target_pages[0]["webSocketDebuggerUrl"]
                break
        except:
            pass
            
    try:
        async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
            msg_id = 0
            async def send_cmd(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method}
                if params: payload["params"] = params
                await ws.send(json.dumps(payload))
                while True:
                    resp = await ws.recv()
                    data = json.loads(resp)
                    if data.get("id") == msg_id: return data.get("result", {})

            await send_cmd("Runtime.enable")
            await send_cmd("Page.enable")
            await asyncio.sleep(1.0)
            
            # Mobile 375x812 (iPhone size)
            await send_cmd("Emulation.setDeviceMetricsOverride", {
                "width": 375, "height": 812, "deviceScaleFactor": 2, "mobile": True
            })
            
            # 1. Reveal Screen
            await send_cmd("Runtime.evaluate", {"expression": "showScreen('reveal')"})
            await asyncio.sleep(0.8)
            shot = await send_cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 85})
            with open("preview_reveal_mobile.jpeg", "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print("Saved preview_reveal_mobile.jpeg")
            
            # 2. Polaroids Screen
            await send_cmd("Runtime.evaluate", {"expression": "showScreen('photos')"})
            await asyncio.sleep(0.8)
            shot = await send_cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 85})
            with open("preview_polaroids_mobile.jpeg", "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print("Saved preview_polaroids_mobile.jpeg")
            
            # 3. Timeline Screen
            await send_cmd("Runtime.evaluate", {"expression": "showScreen('timeline')"})
            await asyncio.sleep(0.8)
            shot = await send_cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 85})
            with open("preview_timeline_mobile.jpeg", "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print("Saved preview_timeline_mobile.jpeg")

            # 4. Letter Screen
            await send_cmd("Runtime.evaluate", {"expression": "showScreen('letter')"})
            await asyncio.sleep(0.8)
            shot = await send_cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 85})
            with open("preview_letter_mobile.jpeg", "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print("Saved preview_letter_mobile.jpeg")

            # 5. Secret Surprise Screen
            await send_cmd("Runtime.evaluate", {"expression": "showScreen('surprise')"})
            await send_cmd("Runtime.evaluate", {"expression": "document.getElementById('vault-btn').click()"})
            await asyncio.sleep(0.8)
            shot = await send_cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 85})
            with open("preview_surprise_mobile.jpeg", "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print("Saved preview_surprise_mobile.jpeg")

            # 6. Wish Screen
            await send_cmd("Runtime.evaluate", {"expression": "showScreen('wish')"})
            await asyncio.sleep(0.8)
            shot = await send_cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 85})
            with open("preview_wish_mobile.jpeg", "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            print("Saved preview_wish_mobile.jpeg")
            
    finally:
        proc.terminate()
        try:
            import shutil
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except: pass

if __name__ == "__main__":
    asyncio.run(capture())
