---
name: reedly
description: "Use this skill to interact with the user's Feedly RSS feeds via the `reedly` CLI. Trigger whenever the user asks about their feeds, news, articles, unread items, subscriptions, or wants to search/read/summarize RSS content. Also trigger for requests like '뉴스 뭐 있어?', '피드 확인', '읽지 않은 기사', 'what's new in my feeds', 'summarize my unread articles', or mentions specific feed categories like Tech, Comics, News, etc."
---

# Reedly — Feedly RSS Feed Skill

You have access to the user's Feedly account through the `reedly` CLI tool. Use it to browse feeds, read articles, check unread counts, search, and summarize content.

## Prerequisites

If `reedly` is not installed, install it first:

```bash
# Option 1: Homebrew (recommended)
brew tap TeeDDub/tap
brew install reedly

# Option 2: uv
uv tool install git+https://github.com/TeeDDub/reedly.git

# Option 3: pip
pip install git+https://github.com/TeeDDub/reedly.git
```

After installing, the user needs to authenticate with `reedly login` and enter their Feedly Developer Access Token.

## Available Commands

Run these via `bash`:

```bash
# Check unread counts across all feeds and categories
reedly unread

# List all subscriptions
reedly subscriptions list

# List categories
reedly categories list

# Read articles from a stream (feed ID, category ID, or tag ID)
reedly read <stream_id> --count <N> --unread-only --full

# Search for feeds
reedly search feeds "<query>"

# Search for articles
reedly search articles "<query>"

# Get a single article's full content
reedly entries get <entry_id>

# List tags/boards (includes saved/highlighted items)
reedly tags list

# Get feed info
reedly feeds info "<feed_id>"
```

## Stream ID Patterns

The user's stream IDs follow this format — use them when calling `reedly read`:

- Category: `user/e4620900-1bfb-4b2e-a951-c957cf1fc70f/category/<Name>` (e.g., Tech, Comics, News, Movie, Entertainment)
- All articles: `user/e4620900-1bfb-4b2e-a951-c957cf1fc70f/category/global.all`
- Saved for later: `user/e4620900-1bfb-4b2e-a951-c957cf1fc70f/tag/global.saved`
- Individual feed: `feed/https://example.com/rss`

## How to Respond

### Checking unread / what's new
1. Run `reedly unread` to get counts
2. Present a concise summary — highlight categories with the most unread items
3. Ask if they want to dive into a specific category

### Reading articles from a category
1. Run `reedly read "<category_stream_id>" --count <N> --unread-only` (default 10)
2. Present the article list in a clean format: title, source, date
3. Offer to read the full content of any article

### Summarizing articles
When the user asks to "요약" or "summarize":
1. Run `reedly read "<stream_id>" --count <N> --full` to get article content
2. Summarize each article in 2-3 sentences, capturing the key point
3. Group summaries by source if there are many articles

### Showing full article content
When the user asks to "전체 내용 보여줘", "show full content", or "원문 보여줘":
1. Run `reedly read "<stream_id>" --count <N> --full` to get article content
2. Present the original article text as-is — do NOT summarize or translate
3. Format with title, source, date, link, then the full original text
4. The distinction matters: "요약해줘" = summarize, "보여줘/전체 내용" = show original content

### Searching
1. Run `reedly search feeds "<query>"` for feed discovery
2. Run `reedly search articles "<query>"` for article search (searches across all subscriptions by default; use `-s <stream_id>` to limit to a specific stream)
3. Present results clearly with titles and sources

### Reading highlights / saved items
1. Run `reedly read "user/e4620900-1bfb-4b2e-a951-c957cf1fc70f/tag/global.saved" --count <N> --full`
2. Summarize the saved articles

## Guidelines

- Default to `--count 10` unless the user specifies otherwise
- When summarizing articles, focus on the key insight or news value — skip boilerplate
- If the user asks in Korean, respond in Korean. If in English, respond in English.
- When showing article lists, use a clean numbered format rather than dumping raw CLI output
- For "what's new" type requests, start with unread counts, then offer to read specific categories
