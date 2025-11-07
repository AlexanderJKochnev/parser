# app/parsers/fetcher.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


class Fetcher:
    def __init__(self, settings):
        self.settings = settings
        self.session = None

    async def __aenter__(self):
        headers = {'User-Agent': self.settings.site.user_agent}
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch(self, url: str) -> str:
        await asyncio.sleep(self.settings.site.delay_between_requests)
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_links(self, html: str, selector: str) -> list:
        if not html:
            return []
        soup = BeautifulSoup(html, 'lxml')
        links = soup.select(selector)
        return [link.get('href') for link in links if link.get('href')]
