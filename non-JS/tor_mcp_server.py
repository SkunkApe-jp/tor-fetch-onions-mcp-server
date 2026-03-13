#!/usr/bin/env python3
"""
Tor MCP Server

An MCP server that provides Tor browsing capabilities as a tool.
"""

import requests
import re
import time
import random
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("tor-mcp-server")

# Tor Browser-like user agent
TOR_BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"

# Common HTTP headers that Tor Browser sends
TOR_BROWSER_HEADERS = {
    "User-Agent": TOR_BROWSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "TE": "trailers"
}


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
    try:
        # Find the .onion domain part
        match = re.search(r'https?://([a-z0-9]+\.onion)', url, re.IGNORECASE)
        if not match:
            return False
            
        domain = match.group(1)
        # Basic validation of onion domain
        if len(domain) < 7:  # minimum: a.onion (not realistic but technically possible)
            return False
            
        return True
    except Exception:
        return False


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
def fetch_page(url: str, timeout: int = 30, add_delay: bool = False, 
              min_delay: float = 1.0, max_delay: float = 3.0) -> Dict[str, Any]:
    """
    Fetch a web page through the Tor network.
    
    Args:
        url (str): The URL to fetch through Tor
        timeout (int): Request timeout in seconds (default: 30)
        add_delay (bool): Whether to add a random delay before making the request (default: False)
        min_delay (float): Minimum delay in seconds (default: 1.0)
        max_delay (float): Maximum delay in seconds (default: 3.0)
        
    Returns:
        Dict[str, Any]: Result containing success status, content, and metadata
    """
    # Validate input parameters
    if not url or not isinstance(url, str):
        return {
            "success": False,
            "url": str(url) if url else None,
            "error": "URL must be a non-empty string"
        }
    
    if not isinstance(timeout, int) or timeout <= 0:
        return {
            "success": False,
            "url": url,
            "error": "timeout must be a positive integer"
        }
    
    # Add random delay if requested
    if add_delay:
        random_delay(min_delay, max_delay)
    
    try:
        # For onion URLs, validate them more strictly
        if '.onion' in url:
            # Try to fix common issues with onion URLs
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            if not is_valid_onion_url(url):
                return {
                    "success": False,
                    "url": url,
                    "error": "URL does not appear to be a valid onion service"
                }
        
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
            headers=TOR_BROWSER_HEADERS
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "url": url,
            "status_code": response.status_code,
            "content": response.text[:10000],  # Limit content size
            "content_length": len(response.text)
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "url": url,
            "error": f"Request timed out after {timeout} seconds"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "url": url,
            "error": "Connection error - could not reach the site"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "url": url,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": f"Unexpected error: {str(e)}"
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
        
        # Make a simple request to check if Tor is working with Tor Browser-like headers
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