#!/usr/bin/env python3
"""
Playwright HTML to Markdown Converter MCP Server

An MCP server that converts HTML content to Markdown format using Playwright
for JavaScript rendering, allowing it to handle dynamic content and JS-heavy sites.
Can fetch through Tor or convert provided HTML content directly.
"""

import asyncio
import markdownify
import time
import random
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# Create the MCP server
mcp = FastMCP("playwright-html-to-md-converter-mcp-server")

# Tor Browser-like user agent
TOR_BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"

# Common HTTP headers that Tor Browser sends (from unified_scraper.go)
TOR_BROWSER_HEADERS = {
    "User-Agent": TOR_BROWSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}


def html_to_markdown(html_content: str) -> str:
    """
    Convert HTML content to Markdown format using markdownify library.
    
    Args:
        html_content (str): HTML content to convert
        
    Returns:
        str: Converted Markdown content
    """
    if not html_content:
        return ""
    
    try:
        markdown_content = markdownify.markdownify(html_content)
        return markdown_content.strip()
    except Exception as e:
        return f"Error converting HTML to Markdown: {str(e)}"


def clean_html_content(html_content: str) -> str:
    """
    Clean HTML content by removing scripts, styles, and comments.
    
    Args:
        html_content (str): HTML content to clean
        
    Returns:
        str: Cleaned HTML content
    """
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Remove comments
        comments = soup.find_all(string=lambda text: isinstance(text, soup.__class__))
        for comment in comments:
            comment.extract()
        
        return str(soup)
    except Exception:
        return html_content


def random_delay(min_delay: float = 1.0, max_delay: float = 3.0):
    """
    Add a random delay to make requests appear more human-like.
    
    Args:
        min_delay (float): Minimum delay in seconds
        max_delay (float): Maximum delay in seconds
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


async def fetch_with_playwright(url: str, timeout: int = 30, max_length: int = 10000,
                               add_delay: bool = False, min_delay: float = 1.0, max_delay: float = 3.0) -> Dict[str, Any]:
    """
    Fetch a web page using Playwright with JavaScript rendering through Tor.
    
    Args:
        url (str): The URL to fetch
        timeout (int): Request timeout in seconds
        max_length (int): Maximum length of output Markdown
        add_delay (bool): Whether to add a random delay before fetching
        min_delay (float): Minimum delay in seconds
        max_delay (float): Maximum delay in seconds
        
    Returns:
        Dict[str, Any]: Result containing success status and converted content
    """
    if add_delay:
        random_delay(min_delay, max_delay)
    
    try:
        async with async_playwright() as p:
            # Launch Firefox with Tor proxy
            browser = await p.firefox.launch(
                headless=True,
                proxy={
                    "server": "socks5://127.0.0.1:9050"
                },
                args=["--proxy-remote-dns"]
            )
            
            # Create context with custom headers
            context = await browser.new_context(
                user_agent=TOR_BROWSER_USER_AGENT,
                extra_http_headers=TOR_BROWSER_HEADERS,
                viewport={"width": 1400, "height": 900},
                ignore_https_errors=True
            )
            
            # Add anti-webdriver detection script
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            page = await context.new_page()
            page.set_default_timeout(timeout * 1000)
            
            # Navigate to the page
            await page.goto(url, wait_until="networkidle")
            
            # Wait for page render and scroll for lazy-loaded content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Simulate human reading delay
            reading_delay = random.uniform(2, 5)
            await page.wait_for_timeout(int(reading_delay * 1000))
            
            # Get the full page HTML after JS execution
            html_content = await page.content()
            
            await context.close()
            await browser.close()
            
            # Clean and convert the HTML
            cleaned_html = clean_html_content(html_content)
            markdown_content = html_to_markdown(cleaned_html)
            
            # Limit content size
            if len(markdown_content) > max_length:
                markdown_content = markdown_content[:max_length] + "\n\n... (content truncated)"
            
            return {
                "success": True,
                "url": url,
                "content": markdown_content,
                "original_length": len(html_content),
                "converted_length": len(markdown_content),
                "source": "playwright_js_enabled"
            }
            
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": f"Playwright fetch failed: {str(e)}",
            "error_type": "playwright_error"
        }


@mcp.tool()
async def fetch_and_convert_js(content: str, timeout: int = 30, max_length: int = 10000,
                        add_delay: bool = False, min_delay: float = 1.0, max_delay: float = 3.0) -> Dict[str, Any]:
    """
    Fetch a URL using Playwright (with JavaScript support) and convert to Markdown.
    
    This tool uses Playwright to fetch pages, enabling it to handle JavaScript-heavy sites
    like Ahmia that require JS rendering. Use this for dynamic content.
    
    Args:
        content (str): URL to fetch (must start with http:// or https://)
        timeout (int): Request timeout in seconds (default: 30)
        max_length (int): Maximum length of output Markdown (default: 10000)
        add_delay (bool): Whether to add a random delay before fetching (default: False)
        min_delay (float): Minimum delay in seconds (default: 1.0)
        max_delay (float): Maximum delay in seconds (default: 3.0)
        
    Returns:
        Dict[str, Any]: Result containing success status, converted content, and metadata
    """
    try:
        if not content or not isinstance(content, str):
            return {
                "success": False,
                "error": "URL must be a non-empty string"
            }
        
        if not content.lower().startswith(('http://', 'https://')):
            return {
                "success": False,
                "error": "Content must be a valid URL (http:// or https://)"
            }
        
        # Use await instead of asyncio.run()
        result = await fetch_with_playwright(content, timeout, max_length, add_delay, min_delay, max_delay)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch with Playwright: {str(e)}",
            "error_type": "execution_error"
        }


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check if Playwright and Tor service are available.
    
    Returns:
        Dict[str, Any]: Health status information
    """
    try:
        # Check if playwright is installed
        import playwright
        
        # Try to run a simple async operation to verify Tor connectivity
        async def check_tor():
            try:
                async with async_playwright() as p:
                    browser = await p.firefox.launch(
                        headless=True,
                        proxy={
                            "server": "socks5://127.0.0.1:9050"
                        }
                    )
                    context = await browser.new_context()
                    page = await context.new_page()
                    page.set_default_timeout(10000)
                    
                    await page.goto("https://check.torproject.org", wait_until="load")
                    
                    await context.close()
                    await browser.close()
                    return True
            except Exception:
                return False
        
        tor_ok = await check_tor()
        
        return {
            "status": "ok" if tor_ok else "warning",
            "playwright_available": True,
            "tor_connectivity": tor_ok
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
