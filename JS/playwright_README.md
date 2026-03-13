## MCP Server Updates & Playwright Integration

### Recent Changes

#### 1. Unified HTTP Headers
Updated HTTP headers across all MCP servers to use a leaner, more consistent set (inspired by `unified_scraper.go`):
```python
TOR_BROWSER_HEADERS = {
    "User-Agent": TOR_BROWSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}
```

**Updated servers:**
- `html_to_md_converter_mcp_server.py`
- `ahmia_content_scraper_mcp_server.py`

#### 2. New Playwright-Based MCP Servers
Created two new servers with **JavaScript rendering support** for handling dynamic content:

##### **`playwright_html_to_md_mcp_server.py`**
Fetches URLs with Playwright (Firefox + Tor) and converts to Markdown.
- ✅ Handles JavaScript-heavy sites
- ✅ Routes through Tor
- ✅ Anti-webdriver detection
- ✅ Single tool: `fetch_and_convert_js(url)`

**Installation:**
```powershell
pip install playwright
python -m playwright install firefox
```

##### **`playwright_ahmia_mcp_server.py`**
Searches Ahmia with JavaScript rendering, scrapes top 5 results in parallel using 5 worker threads.
- ✅ Playwright discovery (JS rendering for Ahmia search)
- ✅ 5 parallel worker threads for concurrent scraping
- ✅ ThreadPoolExecutor for efficient resource use
- ✅ Tools:
  - `discover_ahmia_links_js(query)` - Get links from Ahmia
  - `scrape_ahmia_top5(query)` - Discover + scrape top 5 in parallel (main tool)
  - `health_check()` - Verify Playwright & Tor

#### 3. HTML to Markdown Consolidation
Merged `convert_html_to_md` and `fetch_and_convert` tools into single `convert_to_markdown` tool in:
- `html_to_md_converter_mcp_server.py`

The unified tool auto-detects whether input is a URL or raw HTML and handles both.

#### 4. Problem: Ahmia Requires JavaScript
**Issue:** Original Ahmia scraper couldn't search because Ahmia requires JS rendering
- Simple HTTP requests only get the landing page
- JavaScript not executed = no search results

**Solution:** Use Playwright servers for JS-heavy sites

### Architecture Summary

| Server | Purpose | JavaScript | Parallel |
|--------|---------|------------|----------|
| `ahmia_content_scraper_mcp_server.py` | Simple HTTP scraping | ❌ | ❌ |
| `html_to_md_converter_mcp_server.py` | HTTP → Markdown | ❌ | ❌ |
| `tor_mcp_server.py` | Generic Tor fetching | ❌ | ❌ |
| `playwright_html_to_md_mcp_server.py` | Playwright → Markdown | ✅ | ❌ |
| `playwright_ahmia_mcp_server.py` | Ahmia search (JS) + parallel scraping | ✅ | ✅ (5 workers) |

### When to Use Each

**Use simple HTTP servers when:**
- Site doesn't require JavaScript
- Speed is critical
- Lightweight operation
- No need for rendering

**Use Playwright servers when:**
- Site requires JavaScript to function (like Ahmia's search)
- Need to handle dynamic content
- Screenshot/link extraction after JS execution
- Can tolerate slower execution

### User Agent Maintenance

**Current user agent:**
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0
```

**To update all servers:**
```powershell
python update_user_agents.py
```

**To verify:**
```powershell
python tests/test_user_agent_update.py
```

**Note:** Playwright servers must have Playwright installed:
```powershell
pip install playwright && playwright install firefox
```

Summary: User Agent Maintenance Solution
Browser user agents change with each update, which means we need to keep them current to appear truly human-like. Here's what I've done to address this issue:
1. Updated All User Agents
I've updated all MCP servers with the current Tor Browser user agent you provided:
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0
2. Created Maintenance Tools
I've developed several tools to make user agent maintenance easier:
Automated Update Script: update_user_agents.py - Updates all MCP servers with a single command
Verification Script: test_user_agent_update.py - Verifies all user agents are current
Maintenance Guide: USER_AGENT_MAINTENANCE.md - Documentation on how to maintain user agents
3. Key Features of the Solution
Single Command Updates: Run python update_user_agents.py to update all servers
Automatic Verification: Scripts verify all user agents match the current version
Error Handling: The update script reports which files were successfully updated
Documentation: Clear guide on maintenance procedures
4. How to Maintain User Agents Going Forward
When Tor Browser Updates:
Get the new user agent string
Update the get_latest_tor_browser_ua() function in update_user_agents.py
Run python update_user_agents.py
Regular Verification:
Run python tests/test_user_agent_update.py to verify all user agents are current
Documentation:
Keep USER_AGENT_MAINTENANCE.md updated with current information
This approach significantly reduces the maintenance overhead you mentioned. Instead of manually updating each file, you can now update all user agents across all MCP servers with a single command!
