# Bot de Filosofia para Mastodon

Bot em Python para publicar citações filosóficas no Mastodon, alternando automaticamente entre português e inglês.

## O que ele faz

- publica uma frase por execução
- alterna PT/EN automaticamente no modo `alternate`
- evita repetir frases até esgotar o arquivo
- pode marcar o idioma do post com o campo `language`
- usa `Idempotency-Key` para ajudar a evitar duplicatas acidentais
- mantém histórico local em `state.json`
- opcionalmente gera um card (imagem) e anexa no post

## Estrutura esperada do JSON

O arquivo `quotes_bilingue.json` deve conter itens assim:

```json
{
  "id": "q001",
  "author_pt": "Marco Aurélio",
  "author_en": "Marcus Aurelius",
  "quote_pt": "Você tem poder sobre sua mente, não sobre os acontecimentos externos.",
  "quote_en": "You have power over your mind, not outside events.",
  "source_url": "https://www.gutenberg.org/ebooks/2680",
  "theme": "self-control",
  "verified": true
}
```

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Depois, edite o `.env`.

## Como obter o token do Mastodon

Você precisa registrar um app no seu servidor Mastodon e autorizar um usuário com escopo `write:statuses`.

Resumo do fluxo:

1. Registrar um app em `POST /api/v1/apps`
2. Autorizar o usuário em `/oauth/authorize`
3. Trocar o código por token em `/oauth/token`
4. Guardar o access token como `MASTODON_TOKEN`

## Execução

No primeiro teste, mantenha `DRY_RUN=true`:

```bash
set -a
source .env
set +a
python bot_mastodon_filosofia.py
```

Quando o preview estiver bom, troque para `DRY_RUN=false`.

## Modos

- `BOT_MODE=alternate` alterna PT e EN a cada execução
- `BOT_MODE=pt` força português
- `BOT_MODE=en` força inglês
- `BOT_MODE=bilingual` publica os dois idiomas no mesmo post

## Configurações úteis

- `POST_WITH_MEDIA=true|false` anexa um card gerado ao post
- `QUOTES_FILE=...` permite trocar o arquivo de frases
- `MASTODON_VISIBILITY=public|unlisted|private|direct`

## Agendamento

### Cron diário

Exemplo para publicar todos os dias às 9h:

```cron
0 9 * * * cd /caminho/do/bot && /caminho/do/bot/.venv/bin/python bot_mastodon_filosofia.py >> bot.log 2>&1
```

### GitHub Actions

Também funciona bem em GitHub Actions, desde que você guarde o token nos secrets do repositório.

## Observações

- No `schedule` do GitHub Actions, o cron é em UTC.
- O escopo recomendado é o mínimo necessário: `write:statuses`.
- Links ainda aparecem como URLs no texto. O Mastodon não transforma palavras arbitrárias em link clicável dentro do conteúdo do post.
