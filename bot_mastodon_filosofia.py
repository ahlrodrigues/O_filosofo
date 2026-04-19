import os
import json
import random
import uuid
import requests
from pathlib import Path

MASTODON_TOKEN = os.getenv("MASTODON_TOKEN", "").strip()
MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL", "").strip().rstrip("/")
MASTODON_VISIBILITY = os.getenv("MASTODON_VISIBILITY", "public").strip() or "public"

_raw_state_file = (os.getenv("STATE_FILE") or "").strip()
STATE_FILE = Path(_raw_state_file or "state.json").expanduser()
DEFAULT_QUOTES_FILE = Path("quotes_bilingue.json")
_raw_quotes_file = (os.getenv("QUOTES_FILE") or "").strip()
QUOTES_FILE = Path(_raw_quotes_file or str(DEFAULT_QUOTES_FILE)).expanduser()

BOT_MODE = os.getenv("BOT_MODE", "alternate").strip().lower() or "alternate"
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "y", "on"}
TAG_PT_BR = os.getenv("TAG_PT_BR", "#filosofia").strip() or "#filosofia"
TAG_EN = os.getenv("TAG_EN", "#philosophy").strip() or "#philosophy"


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "used_ids": [],
        "last_language": "en"
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_quotes():
    if not QUOTES_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {QUOTES_FILE}")

    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    if not isinstance(quotes, list) or not quotes:
        raise ValueError("O arquivo de frases está vazio ou inválido.")

    return quotes

def migrate_state_if_needed(state, quotes):
    """
    Migra `used_indexes` (modelo antigo) para `used_ids` (modelo atual).
    Se não for possível mapear, reinicia o histórico.
    """
    if "used_ids" in state:
        if not isinstance(state.get("used_ids"), list):
            state["used_ids"] = []
        if state.get("last_language") == "pt":
            state["last_language"] = "pt_br"
        return state

    used_indexes = state.get("used_indexes")
    if not isinstance(used_indexes, list):
        state["used_ids"] = []
        state.pop("used_indexes", None)
        return state

    mapped_ids = []
    for idx in used_indexes:
        if not isinstance(idx, int):
            continue
        if 0 <= idx < len(quotes):
            quote_id = quotes[idx].get("id")
            if quote_id:
                mapped_ids.append(quote_id)

    state["used_ids"] = list(dict.fromkeys(mapped_ids))
    state.pop("used_indexes", None)
    if state.get("last_language") == "pt":
        state["last_language"] = "pt_br"
    return state


def resolve_language(state):
    if BOT_MODE in {"pt_br", "pt-br", "pt"}:
        return "pt_br"
    if BOT_MODE == "en":
        return "en"
    if BOT_MODE == "alternate":
        last = state.get("last_language", "en")
        if last in {"pt_br", "pt-br", "pt"}:
            return "en"
        return "pt_br"
    if BOT_MODE == "bilingual":
        return "bilingual"
    raise ValueError(f"BOT_MODE inválido: {BOT_MODE!r}")


def pick_quote(quotes, state):
    used_ids = set(state.get("used_ids", []))
    available = [q for q in quotes if q.get("id") and q.get("id") not in used_ids]

    if not available:
        print("🔄 Todas as frases já foram usadas. Reiniciando ciclo.")
        state["used_ids"] = []
        used_ids = set()
        available = [q for q in quotes if q.get("id")] or quotes[:]

    quote = random.choice(available)
    quote_id = quote.get("id")
    if quote_id:
        state.setdefault("used_ids", []).append(quote_id)

    language = resolve_language(state)
    if language in {"pt_br", "en"}:
        state["last_language"] = language

    return quote, language, state


def format_tag(tag: str) -> str:
    tag = (tag or "").strip()
    if not tag:
        return ""
    if not tag.startswith("#"):
        tag = f"#{tag}"
    return tag


def get_language_tag(language: str) -> str:
    if language == "pt_br":
        return TAG_PT_BR
    if language == "en":
        return TAG_EN
    raise ValueError(f"Idioma inválido: {language!r}")


def build_post(quote, language):
    source_url = (quote.get("source_url") or "").strip()

    if language == "bilingual":
        text_pt = quote["quote_pt_br"]
        author_pt = quote["author_pt_br"]
        text_en = quote["quote_en"]
        author_en = quote["author_en"]
        status = f'“{text_pt}”\n— {author_pt}\n\n“{text_en}”\n— {author_en}'
        tags = " ".join(t for t in [format_tag(TAG_PT_BR), format_tag(TAG_EN)] if t)
        if tags:
            status = f"{status}\n\n{tags}"
        if source_url:
            status = f"{status}\n\n{source_url}"
        return status, None

    if language == "pt_br":
        text = quote["quote_pt_br"]
        author = quote["author_pt_br"]
    else:
        text = quote["quote_en"]
        author = quote["author_en"]

    status = f'“{text}”\n\n{author}'
    tag = format_tag(get_language_tag(language))
    if tag:
        status = f"{status}\n\n{tag}"
    if source_url:
        status = f"{status}\n{source_url}"

    return status, language


def to_mastodon_language(language):
    if language is None:
        return None
    if language == "pt_br":
        return "pt-BR"
    return language


def post_to_mastodon(status, language):
    url = f"{MASTODON_BASE_URL}/api/v1/statuses"

    headers = {
        "Authorization": f"Bearer {MASTODON_TOKEN}",
        "Idempotency-Key": str(uuid.uuid4()),
    }

    data = {
        "status": status,
        "visibility": MASTODON_VISIBILITY,
    }

    mastodon_language = to_mastodon_language(language)
    if mastodon_language:
        data["language"] = mastodon_language

    response = requests.post(url, headers=headers, data=data, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Erro ao publicar post: {response.status_code} - {response.text}")

    return response.json()


def validate_env():
    if not MASTODON_TOKEN:
        raise EnvironmentError("MASTODON_TOKEN não configurado.")
    if not MASTODON_BASE_URL:
        raise EnvironmentError("MASTODON_BASE_URL não configurado.")


def main():
    if not DRY_RUN:
        validate_env()
    else:
        if not MASTODON_TOKEN or not MASTODON_BASE_URL:
            print("ℹ️ DRY_RUN=true: MASTODON_TOKEN/MASTODON_BASE_URL não são obrigatórios.")

    print("📚 Carregando estado...")
    state = load_state()

    print("🧠 Carregando frases...")
    quotes = load_quotes()

    state = migrate_state_if_needed(state, quotes)

    print("🎯 Escolhendo frase...")
    quote, language, state = pick_quote(quotes, state)

    status, post_language = build_post(quote, language)

    print("\n📢 Post a ser enviado:\n")
    print(status)

    if DRY_RUN:
        print("\n🧪 DRY_RUN=true: não vai publicar.")
        return

    print("📝 Publicando no Mastodon...")
    post = post_to_mastodon(status, post_language)

    print("💾 Salvando estado...")
    save_state(state)

    print("✅ Post publicado com sucesso.")
    print(f"🔗 ID do post: {post.get('id')}")

if __name__ == "__main__":
    main()
