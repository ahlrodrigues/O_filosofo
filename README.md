# Bot de Filosofia para Mastodon

Bot em Python para publicar citações filosóficas no Mastodon, alternando automaticamente entre português e inglês.

## O que ele faz

- publica uma frase por execução
- alterna PT-BR/EN automaticamente no modo `alternate`
- evita repetir frases até esgotar o arquivo
- pode marcar o idioma do post com o campo `language`
- usa `Idempotency-Key` para ajudar a evitar duplicatas acidentais
- mantém histórico local em um arquivo de estado (padrão: `state.json`)

## Estrutura esperada do JSON

O arquivo `quotes_bilingue.json` deve conter itens assim:

```json
{
  "id": "q001",
  "author_pt_br": "Marco Aurélio",
  "author_en": "Marcus Aurelius",
  "quote_pt_br": "Você tem poder sobre sua mente, não sobre os acontecimentos externos.",
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
- `BOT_MODE=pt_br` força português (pt-BR)
- `BOT_MODE=en` força inglês
- `BOT_MODE=bilingual` publica os dois idiomas no mesmo post

## Configurações úteis

- `QUOTES_FILE=...` permite trocar o arquivo de frases
- `STATE_FILE=...` permite separar estados por “linha editorial” (ex.: `state.json` e `state_humor.json`)
- `MASTODON_VISIBILITY=public|unlisted|private|direct`
- `TAG_PT_BR=#filosofia` e `TAG_EN=#philosophy` adicionam hashtags por idioma

## Agendamento

### Cron diário

Exemplo para publicar todos os dias às 9h:

```cron
0 9 * * * cd /caminho/do/bot && /caminho/do/bot/.venv/bin/python bot_mastodon_filosofia.py >> bot.log 2>&1
```

### GitHub Actions

Também funciona bem em GitHub Actions, desde que você guarde o token nos secrets do repositório.

Este repositório vem configurado para 2 execuções por dia (cron em UTC):

- `0 11 * * *` (08:00 em America/Sao_Paulo) publica as citações de `quotes_bilingue.json` (estado em `state.json`)
- `0 17 * * *` (14:00 em America/Sao_Paulo) publica as frases de humor de `quotes_humor_bilingue.json` (estado em `state_humor.json`)

## Adicionar novas quotes

### Fluxo atual ⚠️ PENDENTE

> Problema: erro "NetworkError" ao buscar quotes_bilingue.json do GitHub via browser.

### Fluxo alternativo (funcionando)

1. Gerar novas quotes: `python fetch_quotes.py`
2. Revisar traduções em `review_quotes.html`
3. Marcar como verificadas
4. Merge + Push automático

### Passos detalhados

1. Executar `python fetch_quotes.py` para gerar `quotes_new.json`
2. Abrir `review_quotes.html` no navegador
3. Carregar `quotes_new.json` e inserir GitHub Token
4. Revisar/corrigir traduções
5. Marcar como verificadas
6. Clicar "Revisar + Push" para mesclar e fazer push

## Observações

- No `schedule` do GitHub Actions, o cron é em UTC.
- O escopo recomendado é o mínimo necessário: `write:statuses`.
- Links ainda aparecem como URLs no texto. O Mastodon não transforma palavras arbitrárias em link clicável dentro do conteúdo do post.
