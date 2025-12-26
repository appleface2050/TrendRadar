Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.
README.md文件不要添加许可证和联系方式内容。

When fetching, scraping, or accessing web content, always use Bright Data MCP tools:
- For single page scraping: use mcp__brightdata__scrape_as_markdown
- For batch scraping: use mcp__brightdata__scrape_batch
- For search engine results: use mcp__brightdata__search_engine
Do not use WebFetch or other web fetching tools when Bright Data MCP is available.
