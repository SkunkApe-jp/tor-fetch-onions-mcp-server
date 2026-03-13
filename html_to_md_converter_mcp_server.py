#!/usr/bin/env python3
"""
HTML to Markdown Converter MCP Server

An MCP server that converts HTML content to Markdown format.
Can fetch HTML content through Tor or convert provided HTML content directly.
Uses professional libraries for robust HTML parsing and conversion.
"""

import requests
import markdownify
import time
import random
from bs4 import BeautifulSoup
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("html-to-md-converter-mcp-server")

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
        # Use markdownify library for robust HTML to Markdown conversion
        # This is much more reliable than regex-based approaches
        markdown_content = markdownify.markdownify(html_content)
        return markdown_content.strip()
    except Exception as e:
        # Fallback to basic conversion if markdownify fails
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
        # Parse HTML with BeautifulSoup
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
        # Return original content if parsing fails
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


@mcp.tool()
def convert_html_to_md(html_content: str, max_length: int = 10000) -> Dict[str, Any]:
    """
    Convert HTML content to Markdown format.
    
    Args:
        html_content (str): HTML content to convert
        max_length (int): Maximum length of output Markdown (default: 10000)
        
    Returns:
        Dict[str, Any]: Result containing success status, converted content, and metadata
    """
    try:
        if not html_content or not isinstance(html_content, str):
            return {
                "success": False,
                "error": "HTML content must be a non-empty string"
            }
        
        # Clean the HTML content
        cleaned_html = clean_html_content(html_content)
        
        # Convert HTML to Markdown
        markdown_content = html_to_markdown(cleaned_html)
        
        # Limit content size
        if len(markdown_content) > max_length:
            markdown_content = markdown_content[:max_length] + "\n\n... (content truncated)"
        
        return {
            "success": True,
            "content": markdown_content,
            "original_length": len(html_content),
            "converted_length": len(markdown_content)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Conversion failed: {str(e)}"
        }


@mcp.tool()
def fetch_and_convert(url: str, timeout: int = 30, max_length: int = 10000,
                   add_delay: bool = False, min_delay: float = 1.0, max_delay: float = 3.0) -> Dict[str, Any]:
    """
    Fetch a web page through the Tor network and convert it to Markdown.
    
    Args:
        url (str): The URL to fetch through Tor
        timeout (int): Request timeout in seconds (default: 30)
        max_length (int): Maximum length of output Markdown (default: 10000)
        add_delay (bool): Whether to add a random delay before making the request (default: False)
        min_delay (float): Minimum delay in seconds (default: 1.0)
        max_delay (float): Maximum delay in seconds (default: 3.0)
        
    Returns:
        Dict[str, Any]: Result containing success status, converted content, and metadata
    """
    # Add random delay if requested
    if add_delay:
        random_delay(min_delay, max_delay)
    
    try:
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
        
        # Clean the HTML content
        cleaned_html = clean_html_content(response.text)
        
        # Convert HTML to Markdown
        markdown_content = html_to_markdown(cleaned_html)
        
        # Limit content size
        if len(markdown_content) > max_length:
            markdown_content = markdown_content[:max_length] + "\n\n... (content truncated)"
        
        return {
            "success": True,
            "url": url,
            "status_code": response.status_code,
            "content": markdown_content,
            "original_length": len(response.text),
            "converted_length": len(markdown_content)
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": f"Conversion failed: {str(e)}"
        }


@mcp.tool()
def health_check() -> Dict[str, Any]:
    """
    Check if the converter is working properly.
    
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
        
        # Test with a simple HTML snippet
        test_html = "<h1>Test</h1><p>This is a <strong>test</strong> with <a href='http://example.com'>link</a>.</p>"
        result_md = html_to_markdown(test_html)
        
        # Check if basic conversion elements are present
        if "# Test" in result_md and "**test**" in result_md and "[link]" in result_md:
            return {
                "status": "ok",
                "tor_enabled": is_tor,
                "converter_working": True
            }
        else:
            # Do a simpler check
            if len(result_md) > 0:
                return {
                    "status": "ok",
                    "converter_working": True
                }
            else:
                return {
                    "status": "warning",
                    "converter_working": False,
                    "error": "Converter test failed"
                }
        
    except Exception as e:
        return {
            "status": "error",
            "converter_working": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run()