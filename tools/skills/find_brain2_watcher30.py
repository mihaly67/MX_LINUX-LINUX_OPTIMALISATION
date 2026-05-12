import asyncio
from mcp_bridge_tool import run_mcp_client
import json

async def run():
    print("Checking memory files for recent context about Raj8 and Orchestration...")

    cmd = "cat /home/misi/Jules_mx/Knowledge_Base/agent_memory.jsonl | grep -i 'raj8\\|watcher\\|orchestrator\\|trigger\\|inbox' | tail -n 20"
    result = await run_mcp_client("execute_bash", {"command": cmd})
    if result and isinstance(result, list) and len(result) > 0 and result[0].type == 'text':
        text_output = result[0].text
        try:
            parsed = json.loads(text_output)
            print("Memory grep:\n" + parsed.get("stdout", ""))
        except:
            print(text_output)

if __name__ == "__main__":
    asyncio.run(run())
