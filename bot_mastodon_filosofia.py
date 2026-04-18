import os
import json
import random
import requests
from pathlib import Path

# =========================
# Configurações
# =========================

MASTODON_TOKEN = os.getenv("MASTODON_TOKEN")
MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL")

STATE_FILE = Path("state.json")
QUOTES_FILE = Path("quotes_bilingue.json")

# =========================
# Funções de estado
# =========================

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "used_indexes": [],
        "last_language": "en"
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# =========================
# Carregar frases
# =========================

def load_quotes():
    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# =========================
# Escolher frase
# =========================

def pick_quote(quotes, state):
    used = set(state["used_indexes"])
    available = [i for i in range(len(quotes)) if i not in used]

    # Reset se todas usadas
    if not available:
        print("🔄 Resetando lista de frases")
        state["used_indexes"] = []
        available = list(range(len(quotes)))

    index = random.choice(available)
    state["used_indexes"].append(index)

    # Alternar idioma
    state["last_language"] = "pt" if state["last_language"] == "en" else "en"
    language = state["last_language"]

    return quotes[index], language, state

# =========================
# Montar post
# =========================

def build_post(quote, language):
    if language == "pt":
        text = quote["quote_pt"]
        author = quote["author_pt"]
    else:
        text = quote["quote_en"]
        author = quote["author_en"]

    post = f'“{text}”\n\n{author}\n{quote["source_url"]}'

    return post, language

# =========================
# Postar no Mastodon
# =========================

def post_to_mastodon(text, language):
    url = f"{MASTODON_BASE_URL}/api/v1/statuses"

    headers = {
        "Authorization": f"Bearer {MASTODON_TOKEN}"
    }

    data = {
        "status": text,
        "language": language,
        "visibility": "public"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        print("✅ Post publicado com sucesso")
    else:
        print("❌ Erro ao postar:", response.status_code, response.text)

# =========================
# Execução principal
# =========================

def main():
    if not MASTODON_TOKEN or not MASTODON_BASE_URL:
        raise Exception("Variáveis de ambiente não configuradas")

    state = load_state()
    quotes = load_quotes()

    quote, language, state = pick_quote(quotes, state)

    post_text, language = build_post(quote, language)

    print("\n📢 Post a ser enviado:\n")
    print(post_text)

    post_to_mastodon(post_text, language)

    save_state(state)

# =========================

if __name__ == "__main__":
    main()
