#!/usr/bin/env python3
import os
import json
import subprocess

MAIN_FILE = os.getenv("MAIN_FILE", "quotes_bilingue.json")
NEW_FILE = os.getenv("NEW_FILE", "quotes_new.json")
GH_TOKEN = os.getenv("GH_TOKEN", "").strip()
COMMIT_MSG = os.getenv("COMMIT_MSG", "Adds new verified quotes")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro: {result.stderr}")
        return False
    return True


def main():
    print(f"📚 Carregando {MAIN_FILE}...")
    main_data = load_json(MAIN_FILE)
    main_count = len(main_data)
    
    print(f"📚 Carregando {NEW_FILE}...")
    new_data = load_json(NEW_FILE)
    
    verified = [q for q in new_data if q.get("verified", False)]
    print(f"✅ Verificadas: {len(verified)}")
    
    if not verified:
        print("❌ Nenhuma quote verificada!")
        return
    
    merged = main_data + verified
    print(f"📝 Total mesclado: {len(merged)}")
    
    save_json(MAIN_FILE, merged)
    print(f"💾 Salvo em {MAIN_FILE}")
    
    print("📝 Commitando...")
    run("git add quotes_bilingue.json quotes_new.json")
    run(f'git config user.name "Bot"')
    run(f'git config user.email "bot@.local"')
    run(f'git commit -m "{COMMIT_MSG}"')
    
    if GH_TOKEN:
        print("📤 Pushando...")
        run(f"git push https://{GH_TOKEN}@github.com/ahlrodrigues/O_filosofo.git")
        print("✅ Concluído!")
    else:
        print("⚠️ GH_TOKEN não definido. Execute manualmente:")
        print("   git push")


if __name__ == "__main__":
    main()