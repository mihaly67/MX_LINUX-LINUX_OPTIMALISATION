import os
import subprocess

REPOS = ['Raj1', 'Raj2', 'Raj3', 'Raj4', 'Raj5', 'Raj6', 'Raj7', 'Raj8']
GITHUB_USER = "mihaly67"
TOKEN = os.environ.get("GITHUB_TOKEN")

SEED_DIR = "/home/misi/jules_swarm_seed"
WORK_DIR = "/home/misi/temp_swarm_deploy"

# Configure Git Globally on VPS to avoid identity errors
subprocess.run(["git", "config", "--global", "user.email", "misi@contabo.local"])
subprocess.run(["git", "config", "--global", "user.name", "Jules MX Commander"])

for repo in REPOS:
    repo_path = os.path.join(WORK_DIR, repo)
    print(f"\n--- Felfrissítés: {repo} ---")

    # 2. Seed tartalom másolása újra
    subprocess.run(["rsync", "-av", f"{SEED_DIR}/", f"{repo_path}/"])

    # 3. Git Push
    subprocess.run(["git", "-C", repo_path, "add", "."])

    status = subprocess.run(["git", "-C", repo_path, "status", "--porcelain"], capture_output=True, text=True)
    if status.stdout.strip():
        subprocess.run(["git", "-C", repo_path, "commit", "-m", "chore: Init VPS bridge, MCP tool, and AGENTS_MX protocol"])
        push_res = subprocess.run(["git", "-C", repo_path, "push"])
        if push_res.returncode == 0:
            print(f"✅ {repo} sikeresen frissítve a GitHubon!")
        else:
            print(f"❌ {repo} push sikertelen.")
    else:
        print(f"⏩ {repo} már naprakész, nincs mit commitolni.")
