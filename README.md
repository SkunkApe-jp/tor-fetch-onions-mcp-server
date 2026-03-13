# Tor Fetch Onions MCP Server

Two MCP (Model Context Protocol) servers for fetching web content through the Tor network.

## Servers

### 1. `tor_mcp_server.py` — Tor Page Fetcher
Fetches raw HTML from any URL (including `.onion` sites) through the Tor SOCKS5 proxy.

**Tools:**
- **`fetch_page`** — Fetch a web page through Tor. Returns raw HTML content (capped at 10,000 chars).
- **`health_check`** — Verify Tor connectivity via `check.torproject.org`.

### 2. `html_to_md_converter_mcp_server.py` — Tor Fetch & Convert
Fetches HTML through Tor and converts it to clean Markdown using `markdownify` and `BeautifulSoup`.

**Tools:**
- **`convert_html_to_md`** — Convert provided HTML string to Markdown.
- **`fetch_and_convert`** — Fetch a URL through Tor and return the content as Markdown.
- **`health_check`** — Verify Tor connectivity and converter functionality.

## Prerequisites

- **Python 3.10+**
- **Tor** running locally with a SOCKS5 proxy on `127.0.0.1:9050` (default Tor Expert Bundle config)

## Installation

```bash
pip install -r requirements.txt
```

## MCP Client Configuration

Add one or both servers to your MCP client config (e.g. Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "tor-mcp-server": {
      "command": "python",
      "args": ["path/to/tor_mcp_server.py"]
    },
    "html-to-md-converter-mcp-server": {
      "command": "python",
      "args": ["path/to/html_to_md_converter_mcp_server.py"]
    }
  }
}
```

## Running Standalone

```bash
python tor_mcp_server.py
python html_to_md_converter_mcp_server.py
```

Both servers use stdio transport by default.

## License

MIT
