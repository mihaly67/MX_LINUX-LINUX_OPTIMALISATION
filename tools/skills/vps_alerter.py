import os
import glob
import json
import time
import subprocess

ALERTS_DIR = os.path.expanduser("~/Jules_mx/alerts")
os.makedirs(ALERTS_DIR, exist_ok=True)

# Ez egy dedikált log fájl, amit a VPS SSD-n gyűjtünk. Ezt később a Google Drive-ra is szinkronizálhatjuk (rclone)
MASTER_LOG = os.path.expanduser("~/Jules_mx/master_alerts.log")

def alerter_loop():
    print("🔔 [VPS ALERTER] Elindult. Figyelem az 'alerts' postaládát a Qwen leleteire...")

    while True:
        alert_files = glob.glob(os.path.join(ALERTS_DIR, "*.json"))

        if alert_files:
            print(f"🔔 {len(alert_files)} új riasztás a postaládában! Feldolgozás...")

            with open(MASTER_LOG, "a", encoding="utf-8") as out_f:
                for file_path in alert_files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as in_f:
                            data = json.load(in_f)

                        # Logolás
                        out_f.write(f"\n[{time.ctime(data['timestamp'])}] ÉRDEKES FÁJL: {data['file']}\n")
                        out_f.write(f"QWEN ELEMZÉS:\n{data['qwen_analysis']}\n")
                        out_f.write("-" * 50 + "\n")

                        # Itt lehetne egy CURL POST egy Discord/Slack/Telegram webhookra,
                        # vagy egy CLI üzenetküldés a chat platformunkra, ha megvan hozzá a hitelesítés!
                        # Példa: subprocess.run(["curl", "-X", "POST", "-d", f"Találtam valamit: {data['file']}", "https://webhook.site/..."])

                        # Töröljük a feldolgozott fájlt
                        os.remove(file_path)

                    except Exception as e:
                        print(f"Hiba a fájl olvasásakor ({file_path}): {e}")

        # 5 percenként nézünk be a postaládába
        time.sleep(300)

if __name__ == "__main__":
    alerter_loop()
