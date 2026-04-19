import os
import json
import random
import uuid
import requests
from pathlib import Path
from gerar_imagem import gerar_card

MASTODON_TOKEN = os.getenv("MASTODON_TOKEN", "").strip()
MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL", "").strip().rstrip("/")
MASTODON_VISIBILITY = os.getenv("MASTODON_VISIBILITY", "public").strip() or "public"

STATE_FILE = Path("state.json")
DEFAULT_QUOTES_FILE = Path("quotes_bilingue.json")
QUOTES_FILE = Path(os.getenv("QUOTES_FILE", str(DEFAULT_QUOTES_FILE))).expanduser()
CARD_FILE = Path(os.getenv("CARD_FILE", "card.png")).expanduser()

BOT_MODE = os.getenv("BOT_MODE", "alternate").strip().lower() or "alternate"
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "y", "on"}
POST_WITH_MEDIA = os.getenv("POST_WITH_MEDIA", "true").strip().lower() in {"1", "true", "yes", "y", "on"}


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
    return state


def resolve_language(state):
    if BOT_MODE == "pt":
        return "pt"
    if BOT_MODE == "en":
        return "en"
    if BOT_MODE == "alternate":
        last = state.get("last_language", "en")
        return "pt" if last == "en" else "en"
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
    if language in {"pt", "en"}:
        state["last_language"] = language

    return quote, language, state


def build_post(quote, language):
    source_url = (quote.get("source_url") or "").strip()

    if language == "bilingual":
        text_pt = quote["quote_pt"]
        author_pt = quote["author_pt"]
        text_en = quote["quote_en"]
        author_en = quote["author_en"]
        status = f'“{text_pt}”\n— {author_pt}\n\n“{text_en}”\n— {author_en}'
        if source_url:
            status = f"{status}\n\n{source_url}"
        alt_text = f'Card com a citação em PT/EN — {author_pt} / {author_en}'
        return status, None, alt_text, text_pt, author_pt

    if language == "pt":
        text = quote["quote_pt"]
        author = quote["author_pt"]
    else:
        text = quote["quote_en"]
        author = quote["author_en"]

    status = f'“{text}”\n\n{author}'
    if source_url:
        status = f"{status}\n{source_url}"

    alt_text = f'Card com a citação: "{text}" — {author}'
    return status, language, alt_text, text, author


def upload_media(card_path, alt_text):
    url = f"{MASTODON_BASE_URL}/api/v2/media"

    headers = {
        "Authorization": f"Bearer {MASTODON_TOKEN}"
    }

    with open(card_path, "rb") as f:
        response = requests.post(
            url,
            headers=headers,
            files={"file": (card_path.name, f, "image/png")},
            data={"description": alt_text},
            timeout=60,
        )

    if response.status_code not in (200, 202):
        raise RuntimeError(f"Erro ao enviar mídia: {response.status_code} - {response.text}")

    data = response.json()
    media_id = data.get("id")
    if not media_id:
        raise RuntimeError("A resposta do upload não trouxe media id.")

    return media_id


def post_to_mastodon(status, language, media_id=None):
    url = f"{MASTODON_BASE_URL}/api/v1/statuses"

    headers = {
        "Authorization": f"Bearer {MASTODON_TOKEN}",
        "Idempotency-Key": str(uuid.uuid4()),
    }

    data = {
        "status": status,
        "visibility": MASTODON_VISIBILITY,
    }

    if language:
        data["language"] = language

    if media_id:
        data["media_ids[]"] = [media_id]

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

    status, post_language, alt_text, card_text, card_author = build_post(quote, language)

    print("\n📢 Post a ser enviado:\n")
    print(status)

    if DRY_RUN:
        print("\n🧪 DRY_RUN=true: não vai enviar mídia nem publicar.")
        if POST_WITH_MEDIA:
            print(f"🖼️ Gerando card: {CARD_FILE}")
            gerar_card(card_text, card_author, output=str(CARD_FILE))
        return

    media_id = None
    if POST_WITH_MEDIA:
        print(f"🖼️ Gerando card: {CARD_FILE}")
        gerar_card(card_text, card_author, output=str(CARD_FILE))

        print("📤 Enviando imagem...")
        media_id = upload_media(CARD_FILE, alt_text)

    print("📝 Publicando no Mastodon...")
    post = post_to_mastodon(status, post_language, media_id=media_id)

    print("💾 Salvando estado...")
    save_state(state)

    print("✅ Post publicado com sucesso.")
    print(f"🔗 ID do post: {post.get('id')}")

if __name__ == "__main__":
    main()
