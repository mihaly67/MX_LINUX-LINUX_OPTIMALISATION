import paramiko
import os

VPS_IP = "5.189.163.88"
VPS_USER = "misi"
KEY_PATH = os.path.join(os.path.dirname(__file__), "secrets", "jules_vps_key")

def run_on_vps(command):
    """
    Biztonságos SSH kódvégrehajtás jelszó nélkül, Ed25519 kulccsal.
    Kikerüli a brute-force érzékelést és a fail2ban tiltásokat.
    """
    if not os.path.exists(KEY_PATH):
        return False, "❌ Hiba: SSH kulcs nem található. Beállítottad a secrets mappában?"

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=VPS_IP, port=22, username=VPS_USER, pkey=key, timeout=10)

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")

        client.close()
        return True, output if output else error

    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        success, out = run_on_vps(cmd)
        print(out)
    else:
        print("💡 Használat: python3 vps_bridge.py <parancs>")
