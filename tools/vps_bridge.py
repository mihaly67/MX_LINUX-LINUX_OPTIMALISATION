import paramiko
import os
import sys

VPS_IP = "5.189.163.88"
VPS_USER = "misi"
VPS_PWD = "USER_PROVIDED_PASSWORD"  # Biztonsági okokból (Git commit) nem tartalmazza a nyílt jelszót. Futtatáskor dinamikusan adjuk át.

def run_on_vps(command, password=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Prioritás: futásidőben megadott jelszó, egyébként környezeti változó
        pwd = password or os.environ.get("VPS_PWD")
        if not pwd:
            return False, "❌ Hiba: Nincs megadva VPS jelszó (VPS_PWD környezeti változó üres)."

        client.connect(hostname=VPS_IP, port=22, username=VPS_USER, password=pwd, timeout=10)

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")

        client.close()
        return True, output if output else error

    except Exception as e:
        return False, str(e)

def upload_to_vps(local_path, remote_path, password=None):
    """SFTP feltöltés a VPS Második Agyára (tehermentesítés)."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        pwd = password or os.environ.get("VPS_PWD")
        if not pwd:
            return False, "❌ Hiba: Nincs megadva VPS jelszó."

        client.connect(hostname=VPS_IP, port=22, username=VPS_USER, password=pwd, timeout=10)
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        client.close()
        return True, f"✅ Sikeres feltöltés: {local_path} -> {remote_path}"
    except Exception as e:
        return False, f"❌ Hiba a feltöltésnél: {e}"

if __name__ == "__main__":
    pwd = os.environ.get("VPS_PWD")
    if not pwd:
        print("❌ Hiba: Kérlek állítsd be a VPS_PWD környezeti változót a futtatás előtt! (pl: export VPS_PWD='...')")
        sys.exit(1)

    if len(sys.argv) > 2 and sys.argv[1] == "--upload":
        success, out = upload_to_vps(sys.argv[2], sys.argv[3], password=pwd)
        print(out)
    elif len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        success, out = run_on_vps(cmd, password=pwd)
        print(out)
    else:
        print("💡 Használat: \n Parancs futtatása: python3 tools/vps_bridge.py <parancs>\n Fájl feltöltése: python3 tools/vps_bridge.py --upload <helyi_fájl> <távoli_fájl>")
