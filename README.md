# Tor Fetch Onions MCP Server

Comprehensive collection of MCP (Model Context Protocol) servers for fetching web content through the Tor network. Includes both JavaScript-enabled and static content fetchers for different use cases.

## Repository Structure

```
tor-fetch-onions-mcp-server/
├── JS/                          # JavaScript-enabled servers (Playwright)
│   ├── playwright_ahmia_mcp_server.py      # Ahmia search & scrape with JS
│   ├── playwright_html_to_md_mcp_server.py  # Dynamic HTML to Markdown
│   └── playwright_README.md                # Playwright-specific documentation
├── non-JS/                      # Static content servers (HTTP requests)
│   ├── tor_mcp_server.py                   # Basic Tor page fetcher
│   ├── html_to_md_converter_mcp_server.py   # Static HTML to Markdown
│   └── ahmia_content_scraper_mcp_server.py # Ahmia content scraper
├── README.md                    # This documentation
├── requirements.txt             # Python dependencies
└── .gitignore                   # Git exclusions
```

## Servers

### JavaScript-Enabled Servers (`JS/` folder)

#### 1. `playwright_ahmia_mcp_server.py` — Ahmia Discovery & Scraping
Advanced MCP server for discovering and scraping onion links through Ahmia search engine with full JavaScript support.

**Tools:**
- **`discover_ahmia_links_js`** — Search Ahmia with JavaScript rendering
- **`scrape_ahmia_top5`** — Discover and scrape top 5 results in parallel
- **`health_check`** — Verify Tor and Playwright connectivity

**Features:**
- Full JavaScript execution for dynamic content
- Parallel scraping with worker threads
- Tor proxy integration with stealth features
- Content extraction with titles and snippets

#### 2. `playwright_html_to_md_mcp_server.py` — Dynamic HTML to Markdown
Converts dynamic HTML content to Markdown using Playwright for JavaScript rendering.

**Tools:**
- **`fetch_and_convert_js`** — Fetch URL with JS and convert to Markdown
- **`health_check`** — Verify system status

**Features:**
- Handles JavaScript-heavy sites and SPAs
- Supports lazy-loaded content
- Content cleaning and conversion
- Tor proxy integration

### Static Content Servers (`non-JS/` folder)

#### 1. `tor_mcp_server.py` — Tor Page Fetcher
Basic server for fetching raw HTML from any URL (including `.onion` sites) through the Tor SOCKS5 proxy.

**Tools:**
- **`fetch_page`** — Fetch a web page through Tor. Returns raw HTML content (capped at 10,000 chars).
- **`health_check`** — Verify Tor connectivity via `check.torproject.org`.

#### 2. `html_to_md_converter_mcp_server.py` — Static HTML to Markdown
Fetches static HTML through Tor and converts it to clean Markdown using `markdownify` and `BeautifulSoup`.

**Tools:**
- **`convert_html_to_md`** — Convert provided HTML string to Markdown.
- **`fetch_and_convert`** — Fetch a URL through Tor and return the content as Markdown.
- **`health_check`** — Verify Tor connectivity and converter functionality.

#### 3. `ahmia_content_scraper_mcp_server.py` — Ahmia Content Scraper
Specialized scraper for extracting content from Ahmia search results without JavaScript.

**Tools:**
- **`scrape_ahmia_content`** — Extract content from Ahmia search results
- **`health_check`** — Verify system connectivity

## Prerequisites

- **Python 3.10+**
- **Tor** running locally with a SOCKS5 proxy on `127.0.0.1:9050` (default Tor Expert Bundle config)

## Installation

```bash
pip install -r requirements.txt
```

## MCP Client Configuration

Add any or all servers to your MCP client configuration (e.g., Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "tor-mcp-server": {
      "command": "python",
      "args": ["c:/servers/non-JS/tor_mcp_server.py"],
      "env": {}
    },
    "html-to-md-converter": {
      "command": "python",
      "args": ["c:/servers/non-JS/html_to_md_converter_mcp_server.py"],
      "env": {}
    },
    "ahmia-content-scraper": {
      "command": "python",
      "args": ["c:/servers/non-JS/ahmia_content_scraper_mcp_server.py"],
      "env": {}
    },
    "playwright-ahmia": {
      "command": "python",
      "args": ["c:/servers/JS/playwright_ahmia_mcp_server.py"],
      "env": {}
    },
    "playwright-html-converter": {
      "command": "python",
      "args": ["c:/servers/JS/playwright_html_to_md_mcp_server.py"],
      "env": {}
    }
  }
}
```

**Server Selection Guide:**
- Use **JS/** servers for dynamic content, JavaScript-heavy sites, or Ahmia search
- Use **non-JS/** servers for static content, basic HTML fetching, or when you need maximum stealth
- **Static servers** are faster and less detectable
- **JavaScript servers** can handle modern web applications and interactive content

## Running Standalone

### Static Content Servers (non-JS/)
```bash
# Basic Tor page fetcher
python non-JS/tor_mcp_server.py

# HTML to Markdown converter
python non-JS/html_to_md_converter_mcp_server.py

# Ahmia content scraper
python non-JS/ahmia_content_scraper_mcp_server.py
```

### JavaScript-Enabled Servers (JS/)
```bash
# Ahmia discovery with JavaScript
python JS/playwright_ahmia_mcp_server.py

# Dynamic HTML to Markdown converter
python JS/playwright_html_to_md_mcp_server.py
```

All servers use stdio transport by default.

## License

MIT
