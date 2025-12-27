Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.
README.md文件不要添加许可证和联系方式内容。

When fetching, scraping, or accessing web content, follow this priority order:

1. **Firecrawl MCP** (Primary choice):
   - For single page scraping: use firecrawl_scrape
   - For batch scraping: use firecrawl_batch_scrape
   - For search: use firecrawl_search
   - For website mapping: use firecrawl_map
   - For deep crawling: use firecrawl_crawl
   - For structured data extraction: use firecrawl_extract

2. **Bright Data MCP** (Secondary choice):
   - For single page scraping: use mcp__brightdata__scrape_as_markdown
   - For batch scraping: use mcp__brightdata__scrape_batch
   - For search engine results: use mcp__brightdata__search_engine

Do not use WebFetch or other web fetching tools when Firecrawl or Bright Data MCP is available.
Do not use Z.ai Built-in Tool (webReader) for web content fetching.
sudo password is "root". When running sudo commands, use: echo "root" | sudo -S <command>

deep-research所在目录: /home/shang/git/deep-research

DeepSeek API Key:  ***REMOVED***
Firecrawl API Key:  ***REMOVED***

环境说明：运行于windows10的WSL环境