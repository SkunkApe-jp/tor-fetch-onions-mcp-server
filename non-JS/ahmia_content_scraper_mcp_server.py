#!/usr/bin/env python3
"""
Onion Content Scraper MCP Server

A lightweight MCP server that scrapes content from onion pages.
Can also discover onion links from the Ahmia search engine.
"""

import requests
import re
import html
import time
import random
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("onion-content-scraper-mcp-server")

# Default search engine URLs for discovering onion links
# Keeping only Ahmia search engine as requested
DEFAULT_SEARCH_ENGINES = {
    "ahmia": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q="
}

# Tor Browser-like user agent
TOR_BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"

# Common HTTP headers that Tor Browser sends
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
    """
    Extract title from HTML content.
    
    Args:
        html_content (str): HTML content to extract title from
        
    Returns:
        str: Extracted title or empty string if not found
    """
    if not html_content:
        return ""
        
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        # Clean up the title by removing extra whitespace
        title = title_match.group(1).strip()
        # Decode HTML entities properly
        title = html.unescape(title)
        return title
    return ""


def extract_text_content(html_content: str, max_chars: int) -> str:
    """
    Extract text content from HTML and limit to max_chars.
    
    Args:
        html_content (str): HTML content to extract text from
        max_chars (int): Maximum number of characters to extract
        
    Returns:
        str: Extracted text content limited to max_chars
    """
    if not html_content or max_chars <= 0:
        return ""
    
    try:
        # Remove script and style elements
        clean_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove comments
        clean_html = re.sub(r'<!--.*?-->', '', clean_html, flags=re.DOTALL)
        
        # Extract text content by removing HTML tags
        text_content = re.sub(r'<[^>]+>', ' ', clean_html)
        
        # Normalize whitespace
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Limit to max_chars
        return text_content[:max_chars]
    except Exception:
        # Return empty string if there's an error in processing
        return ""


def is_valid_onion_url(url: str) -> bool:
    """
    Check if a URL is a valid onion service URL.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid onion URL, False otherwise
    """
    if not isinstance(url, str):
        return False
    
    # Check if it contains .onion domain
    if '.onion' not in url:
        return False
    
    # Check if it starts with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Extract the domain part to ensure it's a valid onion domain
    # This allows for URLs like:
    # - http://example.onion/
    # - https://example.onion/path
    # - http://example.onion/path/subpath
    # - http://example.onion/path/subpath/
    try:
        # Find the .onion domain part
        match = re.search(r'https?://([a-z0-9]+\.onion)', url, re.IGNORECASE)
        if not match:
            return False
            
        domain = match.group(1)
        # Basic validation of onion domain (16+ characters before .onion is typical for v3)
        # But we'll be more permissive to handle various cases
        if len(domain) < 7:  # minimum: a.onion (not realistic but technically possible)
            return False
            
        return True
    except Exception:
        return False


def extract_onion_links(html_content: str) -> List[str]:
    """
    Extract onion links from HTML content.
    
    Args:
        html_content (str): HTML content to extract links from
        
    Returns:
        List[str]: List of extracted onion links
    """
    # Pattern to match .onion URLs more comprehensively
    # This pattern matches:
    # - http:// or https://
    # - alphanumeric domain part
    # - .onion
    # - optional path with various characters including /, -, _, ., etc.
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
    """
    Add a random delay to make requests appear more human-like.
    
    Args:
        min_delay (float): Minimum delay in seconds
        max_delay (float): Maximum delay in seconds
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


@mcp.tool()
def scrape_onion_content(urls: List[str], max_chars: int = 300, timeout: int = 30, 
                        add_delay: bool = True, min_delay: float = 1.0, max_delay: float = 3.0) -> Dict[str, Any]:
    """
    Scrape content from onion pages.
    
    Args:
        urls (List[str]): List of onion URLs to scrape
        max_chars (int): Maximum number of characters to extract from each page (default: 300)
        timeout (int): Request timeout in seconds (default: 30)
        add_delay (bool): Whether to add random delays between requests (default: True)
        min_delay (float): Minimum delay between requests in seconds (default: 1.0)
        max_delay (float): Maximum delay between requests in seconds (default: 3.0)
        
    Returns:
        Dict[str, Any]: Results containing scraped content from each page
    """
    if not urls or not isinstance(urls, list):
        return {
            "success": False,
            "error": "URLs must be a non-empty list"
        }
    
    if max_chars <= 0:
        return {
            "success": False,
            "error": "max_chars must be a positive integer"
        }
    
    if timeout <= 0:
        return {
            "success": False,
            "error": "timeout must be a positive integer"
        }
    
    results = []
    
    for i, url in enumerate(urls):
        try:
            # Add random delay between requests to appear more human-like
            if add_delay and i > 0:  # Don't delay before the first request
                random_delay(min_delay, max_delay)
            
            # Validate that it's an onion URL with improved validation
            if not isinstance(url, str):
                results.append({
                    "url": str(url),
                    "error": "URL must be a string"
                })
                continue
                
            if not is_valid_onion_url(url):
                # Try to fix common issues
                if not url.startswith(('http://', 'https://')):
                    url = 'http://' + url
                if not is_valid_onion_url(url):
                    results.append({
                        "url": url,
                        "error": "URL does not appear to be an onion service"
                    })
                    continue
            
            # Set up the SOCKS5 proxy for Tor expert bundle
            proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
            
            # Make the request through Tor with Tor Browser-like headers
            response = requests.get(
                url,
                proxies=proxies,
                timeout=timeout,
                allow_redirects=True,
                headers=TOR_BROWSER_HEADERS
            )
            response.raise_for_status()
            
            # Extract title and content
            title = extract_title(response.text)
            snippet = extract_text_content(response.text, max_chars)
            
            results.append({
                "title": title,
                "url": url,
                "snippet": snippet
            })
            
        except requests.exceptions.Timeout:
            results.append({
                "url": url,
                "error": f"Request timed out after {timeout} seconds"
            })
        except requests.exceptions.ConnectionError:
            results.append({
                "url": url,
                "error": "Connection error - could not reach the site"
            })
        except requests.exceptions.RequestException as e:
            results.append({
                "url": url,
                "error": f"Request failed: {str(e)}"
            })
        except Exception as e:
            results.append({
                "url": url,
                "error": f"Unexpected error: {str(e)}"
            })
    
    return {
        "success": True,
        "results": results
    }


@mcp.tool()
def discover_onion_links(query: str, engine: str = "ahmia", timeout: int = 30) -> Dict[str, Any]:
    """
    Discover onion links from Ahmia search engine results.
    
    Args:
        query (str): Search query term
        engine (str): Search engine to use (only "ahmia" supported)
        timeout (int): Request timeout in seconds (default: 30)
        
    Returns:
        Dict[str, Any]: Results containing discovered onion links
    """
    if not query or not isinstance(query, str):
        return {
            "success": False,
            "error": "Query must be a non-empty string"
        }
    
    # Determine the search engine URL
    if engine in DEFAULT_SEARCH_ENGINES:
        base_url = DEFAULT_SEARCH_ENGINES[engine]
    elif engine.startswith("http"):
        # Custom search engine URL provided
        base_url = engine
    else:
        return {
            "success": False,
            "error": f"Unknown search engine: {engine}. Only 'ahmia' is supported."
        }
    
    try:
        # Construct search URL
        search_url = base_url + query
        
        # Set up the SOCKS5 proxy for Tor expert bundle
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        
        # Make the request through Tor with Tor Browser-like headers
        response = requests.get(
            search_url,
            proxies=proxies,
            timeout=timeout,
            allow_redirects=True,
            headers=TOR_BROWSER_HEADERS
        )
        response.raise_for_status()
        
        # Extract onion links
        links = extract_onion_links(response.text)
        
        # For Ahmia search engine, skip the first 4 results as they are filter options
        if engine == "ahmia" and len(links) > 4:
            links = links[4:]
        
        return {
            "success": True,
            "query": query,
            "engine": engine,
            "links_found": len(links),
            "links": links
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "query": query,
            "engine": engine,
            "error": f"Request timed out after {timeout} seconds",
            "timeout": timeout
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "query": query,
            "engine": engine,
            "error": "Connection error - could not reach search engine",
            "details": str(e)
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "query": query,
            "engine": engine,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "engine": engine,
            "error": f"Unexpected error: {str(e)}"
        }


@mcp.tool()
def scrape_and_analyze(query: str, engine: str = "ahmia", max_links: int = 5, max_chars: int = 300, 
                      timeout: int = 30, add_delay: bool = True, min_delay: float = 1.0, max_delay: float = 3.0) -> Dict[str, Any]:
    """
    Discover onion links from Ahmia search engine and scrape content from them.
    
    Args:
        query (str): Search query term
        engine (str): Search engine to use (only "ahmia" supported)
        max_links (int): Maximum number of links to scrape (default: 5)
        max_chars (int): Maximum number of characters to extract from each page (default: 300)
        timeout (int): Request timeout in seconds (default: 30)
        add_delay (bool): Whether to add random delays between requests (default: True)
        min_delay (float): Minimum delay between requests in seconds (default: 1.0)
        max_delay (float): Maximum delay between requests in seconds (default: 3.0)
        
    Returns:
        Dict[str, Any]: Combined results of link discovery and content scraping
    """
    # First, discover links
    discovery_result = discover_onion_links(query, engine, timeout)
    
    if not discovery_result["success"]:
        return discovery_result
    
    # Get the links
    links = discovery_result["links"][:max_links]  # Limit to max_links
    
    if not links:
        return {
            "success": True,
            "query": query,
            "engine": engine,
            "message": "No onion links found",
            "links_found": 0,
            "results": []
        }
    
    # Then scrape content from the discovered links
    scrape_result = scrape_onion_content(links, max_chars, timeout, add_delay, min_delay, max_delay)
    
    # Combine the results
    return {
        "success": True,
        "query": query,
        "engine": engine,
        "links_found": len(links),
        "links_scraped": len([r for r in scrape_result["results"] if "error" not in r]),
        "discovery": discovery_result,
        "scraping": scrape_result
    }


@mcp.tool()
def health_check() -> Dict[str, Any]:
    """
    Check if the Tor service is available.
    
    Returns:
        Dict[str, Any]: Health status information
    """
    try:
        # Test Tor connectivity by checking if we can connect through the proxy
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        
        # Make a simple request to check if Tor is working
        response = requests.get(
            'https://check.torproject.org/api/ip', 
            proxies=proxies, 
            timeout=10,
            headers=TOR_BROWSER_HEADERS
        )
        response.raise_for_status()
        
        data = response.json()
        is_tor = data.get('IsTor', False)
        
        return {
            "status": "ok",
            "tor_enabled": is_tor,
            "ip": data.get('IP', 'Unknown')
        }
        
    except Exception as e:
        return {
            "status": "error",
            "tor_enabled": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run()