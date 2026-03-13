#!/usr/bin/env python3
"""
Playwright Ahmia Scraper MCP Server

An MCP server that discovers onion links from Ahmia using Playwright (JavaScript support)
and scrapes the top 5 results in parallel using worker threads.
"""

import asyncio
import requests
import re
import html
import time
import random
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Create the MCP server
mcp = FastMCP("playwright-ahmia-mcp-server")

# Ahmia search URL
AHMIA_URL = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q="

# Tor Browser-like user agent
TOR_BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"

# Common HTTP headers (from unified_scraper.go)
TOR_BROWSER_HEADERS = {
    "User-Agent": TOR_BROWSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}


def extract_title(html_content: str) -> str:
    """Extract title from HTML content."""
    if not html_content:
        return ""
    
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        title = html.unescape(title)
        return title
    return ""


def extract_text_content(html_content: str, max_chars: int) -> str:
    """Extract and clean text content from HTML."""
    if not html_content or max_chars <= 0:
        return ""
    
    try:
        clean_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        clean_html = re.sub(r'<!--.*?-->', '', clean_html, flags=re.DOTALL)
        text_content = re.sub(r'<[^>]+>', ' ', clean_html)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        return text_content[:max_chars]
    except Exception:
        return ""


def extract_onion_links(html_content: str) -> List[str]:
    """Extract onion links from HTML content."""
    onion_pattern = r'https?://[a-z0-9]+\.onion(?:/[^\s"<>\)]*)?'
    links = re.findall(onion_pattern, html_content, re.IGNORECASE)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links


def random_delay(min_delay: float = 1.0, max_delay: float = 3.0):
    """Add a random delay to appear more human-like."""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


async def fetch_ahmia_with_playwright(query: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch Ahmia search results using Playwright with JavaScript rendering through Tor.
    
    Args:
        query (str): Search query
        timeout (int): Request timeout in seconds
        
    Returns:
        Dict[str, Any]: Result with discovered links
    """
    try:
        search_url = AHMIA_URL + query
        
        async with async_playwright() as p:
            # Launch Firefox with Tor proxy
            browser = await p.firefox.launch(
                headless=True,
                proxy={
                    "server": "socks5://127.0.0.1:9050"
                },
                args=["--proxy-remote-dns"]
            )
            
            # Create context with custom headers and user agent
            context = await browser.new_context(
                user_agent=TOR_BROWSER_USER_AGENT,
                extra_http_headers=TOR_BROWSER_HEADERS,
                viewport={"width": 1400, "height": 900},
                ignore_https_errors=True
            )
            
            # Add anti-webdriver detection
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            page = await context.new_page()
            page.set_default_timeout(timeout * 1000)
            
            # Navigate to Ahmia search
            await page.goto(search_url, wait_until="networkidle")
            
            # Wait for search results to render
            time.sleep(2)
            
            # Get the rendered HTML
            html_content = await page.content()
            
            await context.close()
            await browser.close()
            
            # Extract links from the rendered HTML
            links = extract_onion_links(html_content)
            
            # Skip first 4 if they're Ahmia's own links (like search filters)
            if len(links) > 4:
                links = links[4:]
            
            return {
                "success": True,
                "query": query,
                "links_found": len(links),
                "links": links
            }
            
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": f"Playwright Ahmia fetch failed: {str(e)}"
        }


def scrape_single_url(url: str, max_chars: int = 300, timeout: int = 30) -> Dict[str, Any]:
    """
    Scrape a single onion URL using simple HTTP (worker function).
    
    Args:
        url (str): Onion URL to scrape
        max_chars (int): Max chars to extract
        timeout (int): Request timeout
        
    Returns:
        Dict[str, Any]: Scraped content
    """
    try:
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        
        response = requests.get(
            url,
            proxies=proxies,
            timeout=timeout,
            allow_redirects=True,
            headers=TOR_BROWSER_HEADERS
        )
        response.raise_for_status()
        
        title = extract_title(response.text)
        snippet = extract_text_content(response.text, max_chars)
        
        return {
            "url": url,
            "title": title,
            "snippet": snippet,
            "success": True
        }
        
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "error": f"Request timed out after {timeout} seconds",
            "success": False
        }
    except requests.exceptions.ConnectionError:
        return {
            "url": url,
            "error": "Connection error - could not reach the site",
            "success": False
        }
    except requests.exceptions.RequestException as e:
        return {
            "url": url,
            "error": f"Request failed: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "url": url,
            "error": f"Unexpected error: {str(e)}",
            "success": False
        }


def scrape_urls_parallel(urls: List[str], max_workers: int = 5, max_chars: int = 300, 
                        timeout: int = 30, add_delay: bool = True, 
                        min_delay: float = 1.0, max_delay: float = 3.0) -> List[Dict[str, Any]]:
    """
    Scrape multiple URLs in parallel using worker threads.
    
    Args:
        urls (List[str]): URLs to scrape
        max_workers (int): Number of parallel workers
        max_chars (int): Max chars to extract from each page
        timeout (int): Request timeout
        add_delay (bool): Add random delays
        min_delay (float): Min delay
        max_delay (float): Max delay
        
    Returns:
        List[Dict[str, Any]]: Results from all workers
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for i, url in enumerate(urls):
            # Add delay between submitting jobs
            if add_delay and i > 0:
                random_delay(min_delay, max_delay)
            
            future = executor.submit(scrape_single_url, url, max_chars, timeout)
            futures[future] = url
        
        # Collect results as they complete
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    return results


@mcp.tool()
async def discover_ahmia_links_js(query: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Discover onion links from Ahmia using Playwright with JavaScript rendering.
    
    This tool uses Playwright to fetch and render Ahmia search results, handling
    the site's JavaScript requirements. Returns discovered .onion links.
    
    Args:
        query (str): Search query term
        timeout (int): Request timeout in seconds (default: 30)
        
    Returns:
        Dict[str, Any]: Results containing discovered onion links
    """
    try:
        if not query or not isinstance(query, str):
            return {
                "success": False,
                "error": "Query must be a non-empty string"
            }
        
        # Use await instead of asyncio.run()
        result = await fetch_ahmia_with_playwright(query, timeout)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": f"Discovery failed: {str(e)}"
        }


@mcp.tool()
async def scrape_ahmia_top5(query: str, max_chars: int = 300, timeout: int = 30, 
                     max_workers: int = 5, add_delay: bool = True,
                     min_delay: float = 1.0, max_delay: float = 3.0) -> Dict[str, Any]:
    """
    Search Ahmia for links and scrape the top 5 results in parallel using worker threads.
    
    This is the main tool: it discovers links from Ahmia (with JS rendering),
    takes the top 5, and scrapes them concurrently using 5 separate workers.
    
    Args:
        query (str): Search query term
        max_chars (int): Max characters to extract from each page (default: 300)
        timeout (int): Request timeout in seconds (default: 30)
        max_workers (int): Number of parallel worker threads (default: 5)
        add_delay (bool): Add random delays between requests (default: True)
        min_delay (float): Minimum delay in seconds (default: 1.0)
        max_delay (float): Maximum delay in seconds (default: 3.0)
        
    Returns:
        Dict[str, Any]: Combined discovery and scraping results
    """
    try:
        # First, discover links from Ahmia using Playwright (with JS support)
        discovery_result = await fetch_ahmia_with_playwright(query, timeout)
        
        if not discovery_result["success"]:
            return discovery_result
        
        # Get top 5 links
        links = discovery_result["links"][:5]
        
        if not links:
            return {
                "success": True,
                "query": query,
                "message": "No onion links found",
                "links_found": 0,
                "results": []
            }
        
        # Scrape the top 5 in parallel using worker threads
        scrape_results = scrape_urls_parallel(
            links, 
            max_workers=max_workers,
            max_chars=max_chars,
            timeout=timeout,
            add_delay=add_delay,
            min_delay=min_delay,
            max_delay=max_delay
        )
        
        # Count successful scrapes
        successful = len([r for r in scrape_results if r.get("success", False)])
        
        return {
            "success": True,
            "query": query,
            "links_discovered": discovery_result["links_found"],
            "links_to_scrape": len(links),
            "links_scraped_successfully": successful,
            "discovery": discovery_result,
            "scraping": scrape_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": f"Ahmia scrape failed: {str(e)}"
        }


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check if Playwright, Tor, and all dependencies are available.
    
    Returns:
        Dict[str, Any]: Health status information
    """
    try:
        import playwright
        
        async def check_playwright_tor():
            try:
                async with async_playwright() as p:
                    browser = await p.firefox.launch(
                        headless=True,
                        proxy={"server": "socks5://127.0.0.1:9050"}
                    )
                    context = await browser.new_context()
                    page = await context.new_page()
                    page.set_default_timeout(10000)
                    
                    await page.goto("https://check.torproject.org", wait_until="load")
                    
                    await context.close()
                    await browser.close()
                    return True
            except Exception as e:
                return False
        
        tor_ok = await check_playwright_tor()
        
        return {
            "status": "ok" if tor_ok else "warning",
            "playwright_available": True,
            "tor_connectivity": tor_ok,
            "workers_available": True
        }
        
    except ImportError:
        return {
            "status": "error",
            "playwright_available": False,
            "error": "Playwright not installed. Run: pip install playwright && playwright install firefox"
        }
    except Exception as e:
        return {
            "status": "error",
            "playwright_available": True,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run()
