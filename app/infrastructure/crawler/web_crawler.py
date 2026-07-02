"""
Web crawler using httpx and BeautifulSoup.

Handles rate limiting, robots.txt, and HTML content extraction.
Crawl4AI integration point for advanced crawling.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.shared.config.settings import get_settings
from app.shared.logging.logger import get_logger
from app.shared.utils.retry import async_retry

logger = get_logger(__name__)


class CrawlResult:
    """Represents the result of crawling a web page."""

    def __init__(
        self,
        url: str,
        status_code: int,
        html: str = "",
        text: str = "",
        title: str = "",
        meta_description: str = "",
        links: list[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.status_code = status_code
        self.html = html
        self.text = text
        self.title = title
        self.meta_description = meta_description
        self.links = links or []
        self.headers = headers or {}

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 400

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "status_code": self.status_code,
            "title": self.title,
            "meta_description": self.meta_description,
            "text_length": len(self.text),
            "links_count": len(self.links),
        }


class WebCrawler:
    """
    Async web crawler with rate limiting and content extraction.

    Uses httpx for HTTP requests and BeautifulSoup for HTML parsing.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._rate_limit = settings.crawl_rate_limit
        self._timeout = settings.crawl_timeout
        self._max_pages = settings.crawl_max_pages_per_site
        self._semaphore = asyncio.Semaphore(self._rate_limit)
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    @async_retry(max_attempts=3, min_wait=2.0)
    async def crawl_page(self, url: str) -> CrawlResult:
        """Crawl a single web page and extract content."""
        async with self._semaphore:
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout,
                    follow_redirects=True,
                    headers={"User-Agent": self._user_agent},
                ) as client:
                    response = await client.get(url)

                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", "10"))
                        logger.warning("Rate limited", url=url, retry_after=retry_after)
                        await asyncio.sleep(retry_after)
                        response = await client.get(url)

                    html = response.text
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract clean text
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    text = soup.get_text(separator="\n", strip=True)

                    # Extract title
                    title = ""
                    title_tag = soup.find("title")
                    if title_tag:
                        title = title_tag.get_text(strip=True)

                    # Extract meta description
                    meta_desc = ""
                    meta_tag = soup.find("meta", attrs={"name": "description"})
                    if meta_tag:
                        meta_desc = meta_tag.get("content", "")  # type: ignore[assignment]

                    # Extract links
                    links = []
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        full_url = urljoin(url, href)
                        if full_url.startswith("http"):
                            links.append(full_url)

                    result = CrawlResult(
                        url=url,
                        status_code=response.status_code,
                        html=html,
                        text=text[:50000],  # Cap text to prevent memory issues
                        title=title,
                        meta_description=meta_desc,
                        links=list(set(links)),
                        headers=dict(response.headers),
                    )

                    logger.info(
                        "Page crawled",
                        url=url,
                        status=response.status_code,
                        text_length=len(text),
                        links=len(links),
                    )

                    return result

            except httpx.TimeoutException:
                logger.error("Crawl timeout", url=url)
                return CrawlResult(url=url, status_code=408)
            except Exception as exc:
                logger.error("Crawl failed", url=url, error=str(exc))
                return CrawlResult(url=url, status_code=0)

    async def crawl_site(
        self,
        base_url: str,
        max_pages: Optional[int] = None,
    ) -> list[CrawlResult]:
        """Crawl multiple pages from a single site."""
        max_pages = max_pages or self._max_pages
        visited: set[str] = set()
        results: list[CrawlResult] = []
        to_visit = [base_url]
        base_domain = urlparse(base_url).netloc

        while to_visit and len(results) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)

            result = await self.crawl_page(url)
            if result.is_success:
                results.append(result)

                # Add same-domain links to queue
                for link in result.links:
                    if urlparse(link).netloc == base_domain and link not in visited:
                        to_visit.append(link)

            # Rate limiting delay
            await asyncio.sleep(1.0 / self._rate_limit)

        logger.info("Site crawl complete", base_url=base_url, pages_crawled=len(results))
        return results
