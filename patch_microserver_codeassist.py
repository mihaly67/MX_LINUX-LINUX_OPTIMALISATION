import os

SERVER_FILE = os.path.expanduser("~/Jules_mx/scripts/vps_micro_server.py")

try:
    with open(SERVER_FILE, "r") as f:
        content = f.read()

    new_content = content.replace('"model": "llama3"', '"model": "qwen2.5:1.5b"')

    with open(SERVER_FILE, "w") as f:
        f.write(new_content)
    print("Sikeresen módosítva a micro_server code_assist timeoutja/modelleje!")
except Exception as e:
    print(f"Hiba: {e}")
