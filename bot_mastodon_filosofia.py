import json
import os
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_FILE = Path(os.getenv('QUOTES_FILE', 'quotes_bilingue.json'))
STATE_FILE = Path(os.getenv('STATE_FILE', 'state.json'))
MASTODON_BASE_URL = os.getenv('MASTODON_BASE_URL', '').rstrip('/')
MASTODON_TOKEN = os.getenv('MASTODON_TOKEN', '')
DEFAULT_VISIBILITY = os.getenv('MASTODON_VISIBILITY', 'public')
DEFAULT_TAGS = os.getenv('MASTODON_TAGS', '#filosofia #philosophy').strip()
MODE = os.getenv('BOT_MODE', 'alternate')  # alternate | pt | en | bilingual
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
TIMEOUT = int(os.getenv('HTTP_TIMEOUT', '30'))


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, payload):
    with path.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def ensure_state() -> dict:
    if STATE_FILE.exists():
        return load_json(STATE_FILE)
    state = {
        'last_language': None,
        'posted_ids': [],
        'history': []
    }
    save_json(STATE_FILE, state)
    return state


def normalize_quotes(raw_quotes):
    quotes = []
    for i, q in enumerate(raw_quotes, start=1):
        if not q.get('verified', False):
            continue
        q = dict(q)
        q.setdefault('id', f'q{i:03d}')
        quotes.append(q)
    if not quotes:
        raise ValueError('Nenhuma citação válida encontrada no arquivo JSON.')
    return quotes


def choose_language(state: dict) -> str:
    if MODE in {'pt', 'en', 'bilingual'}:
        return MODE
    return 'en' if state.get('last_language') == 'pt' else 'pt'


def choose_quote(quotes: list, state: dict) -> dict:
    posted_ids = set(state.get('posted_ids', []))
    available = [q for q in quotes if q['id'] not in posted_ids]

    if not available:
        state['posted_ids'] = []
        available = quotes[:]

    return random.choice(available)


def build_post_text(quote: dict, language: str) -> str:
    author = quote['author']
    source_url = quote.get('source_url', '').strip()

    if language == 'pt':
        text = f'“{quote["quote_pt"]}”\n\n{author}'
    elif language == 'en':
        text = f'“{quote["quote_en"]}”\n\n{author}'
    else:
        text = (
            f'PT\n“{quote["quote_pt"]}”\n\n'
            f'EN\n“{quote["quote_en"]}”\n\n'
            f'{author}'
        )

    if source_url:
        text += f'\n{source_url}'

    if DEFAULT_TAGS:
        text += f'\n\n{DEFAULT_TAGS}'

    return text


def post_to_mastodon(status_text: str, language: str) -> dict:
    if not MASTODON_BASE_URL or not MASTODON_TOKEN:
        raise EnvironmentError('Defina MASTODON_BASE_URL e MASTODON_TOKEN no ambiente.')

    headers = {
        'Authorization': f'Bearer {MASTODON_TOKEN}',
        'Idempotency-Key': str(uuid.uuid4()),
    }
    data = {
        'status': status_text,
        'visibility': DEFAULT_VISIBILITY,
    }
    if language in {'pt', 'en'}:
        data['language'] = language

    response = requests.post(
        f'{MASTODON_BASE_URL}/api/v1/statuses',
        headers=headers,
        data=data,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f'Arquivo de citações não encontrado: {DATA_FILE}')

    raw_quotes = load_json(DATA_FILE)
    quotes = normalize_quotes(raw_quotes)
    state = ensure_state()

    language = choose_language(state)
    quote = choose_quote(quotes, state)
    status_text = build_post_text(quote, language)

    print('--- PREVIEW ---')
    print(status_text)
    print('---------------')

    if DRY_RUN:
        print('DRY_RUN=true, nada foi publicado.')
        return

    result = post_to_mastodon(status_text, language)

    state['last_language'] = language if language in {'pt', 'en'} else state.get('last_language')
    state['posted_ids'] = list(dict.fromkeys(state.get('posted_ids', []) + [quote['id']]))
    state['history'].append({
        'id': quote['id'],
        'author': quote['author'],
        'language': language,
        'posted_at_utc': datetime.now(timezone.utc).isoformat(),
        'mastodon_status_id': result.get('id'),
        'url': result.get('url'),
    })
    save_json(STATE_FILE, state)

    print('Publicado com sucesso!')
    print(result.get('url', 'Sem URL retornada pela API.'))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        sys.exit(1)
