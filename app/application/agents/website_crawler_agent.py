"""
Agent 5: Website Crawler.

Given a website URL, crawls the public pages and extracts relevant content
for further analysis.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.crawler.web_crawler import WebCrawler


class WebsiteCrawlerInput(BaseModel):
    website_url: str
    max_pages: int = 10


class PageContent(BaseModel):
    url: str
    title: str
    text: str


class WebsiteCrawlerOutput(BaseModel):
    pages: list[PageContent]
    success_count: int
    failed_count: int


class WebsiteCrawlerAgent(BaseAgent[WebsiteCrawlerInput, WebsiteCrawlerOutput]):
    def __init__(self) -> None:
        super().__init__("WebsiteCrawlerAgent")
        self.crawler = WebCrawler()

    async def execute(self, input_data: WebsiteCrawlerInput) -> WebsiteCrawlerOutput:
        results = await self.crawler.crawl_site(
            base_url=input_data.website_url,
            max_pages=input_data.max_pages
        )
        
        pages = []
        success = 0
        failed = 0
        
        for r in results:
            if r.is_success:
                pages.append(PageContent(
                    url=r.url,
                    title=r.title,
                    text=r.text
                ))
                success += 1
            else:
                failed += 1
                
        if not pages:
            raise ValueError(f"Failed to extract any content from {input_data.website_url}")
            
        return WebsiteCrawlerOutput(
            pages=pages,
            success_count=success,
            failed_count=failed
        )
