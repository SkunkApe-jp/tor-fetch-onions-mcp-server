# Tor Network Scraping Tools

A comprehensive collection of tools for scraping and analyzing content from the Tor network, designed for research and security analysis purposes.

## Overview

This repository contains specialized scraping tools that operate through the Tor network, with support for both static and dynamic content extraction. The tools are designed with stealth features to minimize detection while maintaining functionality.

## Components

### Go Applications

#### Unified Scraper (`unified_scraper.go`)
A high-performance, parallel scraper designed for bulk data collection from onion sites.

**Features:**
- Parallel processing with configurable worker pools (default: 40 workers)
- Full-page screenshot capture
- Link extraction with title mapping
- Advanced stealth timing (Gaussian-distributed delays)
- Tor proxy integration with connection verification
- Structured output organization

**Usage:**
```bash
go run unified_scraper.go -targets targets.yaml -output scraped_data -workers 20
```

**Configuration Options:**
- `-targets`: Path to targets file (YAML format)
- `-output`: Output directory for collected data
- `-workers`: Number of parallel workers
- `-screenshot`: Enable screenshot capture
- `-links`: Extract onion links
- `-titles`: Extract link titles
- `-inter-delay`: Delay between sites (minutes)
- `-intra-delay`: Delay within pages (seconds)

### Python MCP Servers

#### Ahmia Discovery Server (`playwright_ahmia_mcp_server.py`)
MCP server for discovering and scraping onion links through Ahmia search engine.

**Capabilities:**
- JavaScript-enabled search on Ahmia
- Parallel scraping of top 5 results
- Tor proxy integration
- Content extraction with titles and snippets

**Tools:**
- `discover_ahmia_links_js`: Discover onion links using Playwright
- `scrape_ahmia_top5`: Search and scrape top 5 results in parallel
- `health_check`: Verify Tor and Playwright connectivity

#### HTML to Markdown Converter (Playwright) (`playwright_html_to_md_mcp_server.py`)
Converts dynamic HTML content to Markdown using Playwright for JavaScript rendering.

**Features:**
- Full JavaScript execution support
- Handles dynamic and lazy-loaded content
- Tor proxy integration
- Content cleaning and conversion

**Tools:**
- `fetch_and_convert_js`: Fetch URL with JS and convert to Markdown
- `health_check`: Verify system status

#### HTML to Markdown Converter (HTTP) (`html_to_md_converter_mcp_server.py`)
Lightweight converter for static HTML content using simple HTTP requests.

**Features:**
- Fast and efficient for static content
- Lower detection risk
- Simple HTTP-based approach
- Professional HTML parsing

**Tools:**
- `fetch_and_convert`: Fetch and convert static HTML
- `health_check`: Verify system status

## Architecture

### Stealth Features

All tools implement various stealth techniques:
- Tor Browser user agent and headers
- Anti-webdriver detection scripts
- Configurable delays (Gaussian distribution in Go)
- Proxy integration through SOCKS5

### Concurrency Models

- **Go**: Goroutines with channel-based job distribution
- **Python**: ThreadPoolExecutor for parallel processing

### Data Organization

Output is structured by onion address:
```
scraped_data/
├── [onion_address]/
│   ├── images/
│   ├── discovered_links/
│   └── website_identity/
```

## Requirements

### System Requirements
- Tor service running on localhost:9050
- Go 1.19+ (for Go applications)
- Python 3.8+ (for MCP servers)

### Go Dependencies
```bash
go mod tidy
```

### Python Dependencies
```bash
pip install playwright fastmcp requests beautifulsoup4 markdownify
playwright install firefox
```

## Configuration

### Tor Setup
Ensure Tor is running with SOCKS5 proxy enabled:
```bash
# Verify Tor connection
curl --socks5 127.0.0.1:9050 https://check.torproject.org
```

### Targets File Format
YAML format for Go scraper:
```yaml
urls:
  - http://example1.onion
  - http://example2.onion/path
  - https://example3.onion
```

## Usage Examples

### Bulk Scraping with Go
```bash
# Basic usage with default settings
go run unified_scraper.go

# Custom configuration
go run unified_scraper.go \
  -targets custom_targets.yaml \
  -output my_data \
  -workers 10 \
  -inter-delay 5 \
  -screenshot \
  -links
```

### MCP Server Usage
```bash
# Start Ahmia discovery server
python playwright_ahmia_mcp_server.py

# Start HTML converter server
python html_to_md_converter_mcp_server.py
```

## Security Considerations

### Legal and Ethical Use
- These tools are designed for legitimate security research
- Users must comply with applicable laws and regulations
- Respect website terms of service and robots.txt
- Use responsibly and ethically

### Operational Security
- All traffic routed through Tor network
- No direct IP exposure
- Configurable delays to avoid detection
- Professional user agent headers

## Troubleshooting

### Common Issues

**Tor Connection Failed**
- Verify Tor service is running
- Check SOCKS5 proxy configuration
- Ensure firewall allows Tor traffic

**Playwright Installation**
```bash
# Install browsers
playwright install firefox

# Verify installation
python -c "import playwright; print('OK')"
```

**Memory Usage**
- Reduce worker count for large-scale operations
- Monitor system resources during bulk scraping
- Consider batch processing for very large target lists

### Performance Optimization

**Go Scraper**
- Adjust worker count based on system resources
- Tune delay parameters for target responsiveness
- Monitor log files for error patterns

**Python MCP Servers**
- Use non-Playwright version for static content
- Implement request rate limiting
- Consider caching for repeated requests

## Development

### Code Structure
- Modular design with clear separation of concerns
- Consistent error handling patterns
- Comprehensive logging and monitoring
- Professional code documentation

### Contributing
- Follow existing code style and patterns
- Add appropriate tests for new functionality
- Update documentation for API changes
- Ensure Tor compatibility for all network operations

## License

This project is provided for research and educational purposes. Users are responsible for ensuring compliance with applicable laws and regulations.

## Disclaimer

These tools are designed for legitimate security research and analysis purposes. Users must ensure they have appropriate authorization before accessing any systems or networks. The authors are not responsible for misuse of these tools.
