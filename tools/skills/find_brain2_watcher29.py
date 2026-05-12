import asyncio
from mcp_bridge_tool import run_mcp_client
import json

async def run():
    print("Checking Jules_mx/tools/skills/vps_tour_guide.py for insights...")

    cmd = "cat /home/misi/Jules_mx/tools/skills/vps_tour_guide.py | grep -i 'raj8\\|inbox\\|push\\|github'"
    result = await run_mcp_client("execute_bash", {"command": cmd})
    if result and isinstance(result, list) and len(result) > 0 and result[0].type == 'text':
        text_output = result[0].text
        try:
            parsed = json.loads(text_output)
            print("Content:\n" + parsed.get("stdout", ""))
        except:
            print(text_output)

if __name__ == "__main__":
    asyncio.run(run())
