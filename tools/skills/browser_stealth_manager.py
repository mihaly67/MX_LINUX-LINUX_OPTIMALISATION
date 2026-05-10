#!/usr/bin/env python3
import asyncio
import sys
import json
import os
from playwright.async_api import async_playwright

def clean_cookies(cookies):
    valid_same_site = ["Strict", "Lax", "None"]
    for cookie in cookies:
        if 'sameSite' in cookie:
            if cookie['sameSite'] is None:
                cookie.pop('sameSite')
            elif cookie['sameSite'] not in valid_same_site:
                if str(cookie['sameSite']).lower() == "no_restriction":
                    cookie['sameSite'] = "None"
                else:
                    cookie.pop('sameSite')
        for key in ['hostOnly', 'session', 'storeId', 'id', 'partitionKey']:
            if key in cookie:
                cookie.pop(key)
    return cookies

async def explore_accessibility():
    url = "https://jules.google.com/session"
    cookie_path = "/home/misi/Jules_mx/cookie.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            locale="hu-HU"
        )

        if os.path.exists(cookie_path):
            with open(cookie_path, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(clean_cookies(cookies))
        else:
            print("❌ Sütifájl nem található! Kilépés.", file=sys.stderr)
            await browser.close()
            return

        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(8.0)

            # Kattintsunk az első session linkre JS-ből, mert onnan nyílik meg a chat mező
            await page.evaluate("""
                () => {
                    const sessionLinks = Array.from(document.querySelectorAll('a.task-container[href^="/session/"]'));
                    if (sessionLinks.length > 0) {
                        sessionLinks[0].click();
                    }
                }
            """)
            await asyncio.sleep(5.0)

            client = await page.context.new_cdp_session(page)
            await client.send('DOM.enable')
            await client.send('Accessibility.enable')
            ax_tree = await client.send('Accessibility.getFullAXTree')

            def extract_nodes(nodes):
                res = []
                for node in nodes:
                    role = node.get('role', {}).get('value', '')
                    name = node.get('name', {}).get('value', '')
                    if role in ['button', 'textbox', 'link'] and name:
                        res.append(f"[{role}] {name}")
                    elif role == 'textbox':
                        res.append(f"[{role}] Névtelen TextBox")
                return res

            nodes = extract_nodes(ax_tree.get('nodes', []))

            print("================ SESSION UI TÉRKÉP ================", file=sys.stderr)
            for item in nodes:
                print(item, file=sys.stderr)
            print("====================================================\n", file=sys.stderr)

        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_accessibility())
