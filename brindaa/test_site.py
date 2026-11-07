import os
import sys
import time
import json
import socket
import asyncio
import threading
import subprocess
import urllib.request
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer
import websockets

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_http_server(port):
    server = HTTPServer(('127.0.0.1', port), SimpleHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

async def run_cdp_tests():
    http_port = find_free_port()
    start_http_server(http_port)
    print(f"HTTP Server started at http://127.0.0.1:{http_port}")
    
    cdp_port = find_free_port()
    url = f"http://127.0.0.1:{http_port}/brinda-birthday-surprise.html"
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = os.path.abspath("chrome_temp_profile")
    
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
    
    print(f"Launching Chrome headless on CDP port {cdp_port}...")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for CDP to be ready
    ws_url = None
    for _ in range(20):
        time.sleep(0.5)
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json/list")
            pages = json.loads(req.read().decode())
            target_pages = [p for p in pages if p.get("type") == "page"]
            if target_pages:
                ws_url = target_pages[0]["webSocketDebuggerUrl"]
                print("Found target page:", target_pages[0].get("url"))
                break
        except Exception as e:
            pass
            
    assert ws_url, "Could not obtain WebSocket debugger URL"
    print("Connecting to:", ws_url)
    
    try:
        async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
            msg_id = 0
            async def send_cmd(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method}
                if params:
                    payload["params"] = params
                await ws.send(json.dumps(payload))
                while True:
                    resp = await ws.recv()
                    data = json.loads(resp)
                    if data.get("id") == msg_id:
                        return data.get("result", {})
            
            await send_cmd("Runtime.enable")
            await send_cmd("Page.enable")
            await send_cmd("Log.enable")
            await send_cmd("Page.reload")
            await asyncio.sleep(1.5)
            
            async def send_cmd(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method}
                if params:
                    payload["params"] = params
                await ws.send(json.dumps(payload))
                while True:
                    resp = await ws.recv()
                    data = json.loads(resp)
                    if data.get("method") == "Runtime.exceptionThrown":
                        print("\n>>> BROWSER EXCEPTION:", data.get("params"))
                    if data.get("method") == "Log.entryAdded":
                        print("\n>>> BROWSER LOG:", data.get("params"))
                    if data.get("id") == msg_id:
                        return data.get("result", {})

            # Wait for DOM ready
            await asyncio.sleep(2.0)
            
            async def eval_js(expression):
                res = await send_cmd("Runtime.evaluate", {"expression": expression, "returnByValue": True})
                if "exceptionDetails" in res:
                    print("JS EXCEPTION:", res["exceptionDetails"])
                val = res.get("result", {}).get("value")
                return val
            
            # 1. Page Title
            title = await eval_js("document.title")
            print("PAGE TITLE:", title)
            assert "Brinda" in title, f"Title was '{title}'"
            
            # 2. Photos loaded from config
            photos_count = await eval_js("window.photosList ? window.photosList.length : (typeof window.BRINDA_PHOTO_STORE !== 'undefined' ? window.BRINDA_PHOTO_STORE.getAll().length : 0)")
            print("PHOTOS COUNT IN STORE:", photos_count)
            assert photos_count == 3, f"Expected 3 photos, got {photos_count}"
            
            # 3. Check Screens Count
            screens_count = await eval_js("document.querySelectorAll('.screen').length")
            print("TOTAL SCREENS IN DOM:", screens_count)
            assert screens_count == 10, f"Expected 10 screens, got {screens_count}"
            
            # 4. Check Welcome screen active
            welcome_active = await eval_js("document.getElementById('screen-welcome').classList.contains('active')")
            print("Welcome screen initially active:", welcome_active)
            assert welcome_active, "Welcome screen should be active initially"
            
            # 5. Tap Gift Box -> Reveal screen
            print("\n--- Testing Gift Box Interaction ---")
            await eval_js("document.getElementById('gift').click()")
            await asyncio.sleep(1.0)
            reveal_active = await eval_js("document.getElementById('screen-reveal').classList.contains('active')")
            print("Reveal screen active:", reveal_active)
            assert reveal_active, "Reveal screen should be active after opening gift"

            # 6. Test Hero Photo Click & Lightbox
            print("\n--- Testing Hero Photo & Lightbox ---")
            await eval_js("document.getElementById('hero-photo').click()")
            await asyncio.sleep(0.5)
            lightbox_active = await eval_js("document.getElementById('photo-lightbox').classList.contains('active')")
            print("Lightbox active:", lightbox_active)
            assert lightbox_active, "Lightbox should open when hero photo is clicked"
            
            lightbox_title = await eval_js("document.getElementById('lightbox-title').textContent")
            lightbox_counter = await eval_js("document.getElementById('lightbox-counter').textContent")
            print("Lightbox Title:", lightbox_title, "| Counter:", lightbox_counter)
            assert "Queen" in lightbox_title or "Brinda" in lightbox_title
            assert "1 / 3" in lightbox_counter
            
            # Next photo in lightbox
            await eval_js("document.getElementById('lightbox-next').click()")
            lightbox_counter_2 = await eval_js("document.getElementById('lightbox-counter').textContent")
            print("Lightbox Next Counter:", lightbox_counter_2)
            assert "2 / 3" in lightbox_counter_2
            
            # Close lightbox
            await eval_js("document.getElementById('lightbox-close').click()")
            lightbox_closed = await eval_js("!document.getElementById('photo-lightbox').classList.contains('active')")
            print("Lightbox closed successfully:", lightbox_closed)
            assert lightbox_closed

            # 7. Test Countdown Screen
            print("\n--- Testing Countdown Screen ---")
            await eval_js("showScreen('countdown')")
            cd_days = await eval_js("document.getElementById('cd-days').textContent")
            print("Countdown days remaining:", cd_days)
            assert cd_days != "--", "Countdown days should be calculated"

            # 8. Test Polaroids Screen
            print("\n--- Testing Polaroids Screen ---")
            await eval_js("showScreen('photos')")
            polaroids_count = await eval_js("document.querySelectorAll('#carousel .polaroid').length")
            print("Polaroid cards in carousel:", polaroids_count)
            assert polaroids_count == 3
            
            # Click polaroid #3 (index 2)
            await eval_js("document.querySelectorAll('#carousel .polaroid')[2].click()")
            await asyncio.sleep(0.3)
            lb_counter_3 = await eval_js("document.getElementById('lightbox-counter').textContent")
            print("Opened polaroid 3 in lightbox, counter:", lb_counter_3)
            assert "3 / 3" in lb_counter_3
            await eval_js("document.getElementById('lightbox-close').click()")

            # 9. Test Timeline Screen
            print("\n--- Testing Timeline Screen ---")
            await eval_js("showScreen('timeline')")
            timeline_items = await eval_js("document.querySelectorAll('.timeline-item').length")
            print("Timeline chapters:", timeline_items)
            assert timeline_items == 3

            # 10. Test Letter Screen
            print("\n--- Testing Letter Screen ---")
            await eval_js("showScreen('letter')")
            letter_text = await eval_js("document.querySelector('.letter-text').textContent")
            letter_sign = await eval_js("document.querySelector('.letter-sign').textContent")
            print("Letter sign:", letter_sign)
            assert "Dhanush" in letter_sign

            # 11. Test Flip Cards (5 Reasons)
            print("\n--- Testing Flip Cards ---")
            await eval_js("showScreen('reasons')")
            cards = await eval_js("document.querySelectorAll('[data-flip]').length")
            print("Flip cards count:", cards)
            assert cards == 5
            for i in range(5):
                await eval_js(f"document.querySelectorAll('[data-flip]')[{i}].click()")
            all_flipped = await eval_js("Array.from(document.querySelectorAll('[data-flip]')).every(c => c.classList.contains('flipped'))")
            print("All 5 cards flipped:", all_flipped)
            assert all_flipped

            # 12. Test Secret Surprise Vault
            print("\n--- Testing Secret Surprise Vault ---")
            await eval_js("showScreen('surprise')")
            vault_display_before = await eval_js("window.getComputedStyle(document.getElementById('surprise-unlocked')).display")
            assert vault_display_before == "none"
            await eval_js("document.getElementById('vault-btn').click()")
            await asyncio.sleep(0.4)
            vault_display_after = await eval_js("window.getComputedStyle(document.getElementById('surprise-unlocked')).display")
            print("Secret vault unlocked display:", vault_display_after)
            assert vault_display_after == "block"

            # 13. Test Cake & Wish Candle
            print("\n--- Testing Cake & Candle ---")
            await eval_js("showScreen('wish')")
            flame_out_before = await eval_js("document.getElementById('flame').classList.contains('out')")
            assert not flame_out_before
            await eval_js("document.getElementById('cake').click()")
            await asyncio.sleep(0.5)
            flame_out_after = await eval_js("document.getElementById('flame').classList.contains('out')")
            wish_msg = await eval_js("document.getElementById('wish-msg').textContent")
            next_btn_display = await eval_js("document.getElementById('btn-after-wish').style.display")
            print("Flame extinguished:", flame_out_after)
            print("Wish message text:", wish_msg)
            print("Next button display:", next_btn_display)
            assert flame_out_after
            assert "Wish granted" in wish_msg
            assert next_btn_display == "inline-flex"

            # 14. Test Final Screen & Mini-polaroids
            print("\n--- Testing Final Screen ---")
            await eval_js("showScreen('final')")
            mini_count = await eval_js("document.querySelectorAll('.final-mini-polaroid').length")
            print("Final mini-polaroids count:", mini_count)
            assert mini_count == 3

            # 15. Test Audio Control
            print("\n--- Testing Audio Controls Toggle ---")
            state_before = await eval_js("window.musicBox.isPlaying")
            await eval_js("document.getElementById('music-btn').click()")
            state_after = await eval_js("window.musicBox.isPlaying")
            print(f"Music toggled: before={state_before}, after={state_after}")
            assert state_before != state_after, "Music button should toggle state"

            # 16. Test Mobile Viewports (320px, 375px, 390px, 430px, 768px, 1024px, 1440px)
            print("\n--- Testing Responsive Viewports (Zero Horizontal Overflow) ---")
            test_widths = [320, 375, 390, 430, 768, 1024, 1440]
            screen_names = ['welcome', 'reveal', 'countdown', 'photos', 'timeline', 'letter', 'reasons', 'surprise', 'wish', 'final']
            for w in test_widths:
                await send_cmd("Emulation.setDeviceMetricsOverride", {
                    "width": w,
                    "height": 780,
                    "deviceScaleFactor": 1,
                    "mobile": w < 768
                })
                for s in screen_names:
                    await eval_js(f"showScreen('{s}')")
                    has_overflow = await eval_js("document.documentElement.scrollWidth > window.innerWidth || document.body.scrollWidth > window.innerWidth")
                    assert not has_overflow, f"Horizontal overflow on '{s}' at {w}px!"
                print(f"  ✓ {w}px breakpoint: 100% clean, no horizontal overflow on any of the 10 screens!")

            print("\n🎉 ================================================= 🎉")
            print("  CONGRATULATIONS: ALL 16 TESTS PASSED FLAWLESSLY!   ")
            print("🎉 ================================================= 🎉\n")
            
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()
        try:
            import shutil
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(run_cdp_tests())
