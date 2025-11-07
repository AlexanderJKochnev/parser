# app/parsers/processor.py
from bs4 import BeautifulSoup
from loguru import logger
from app.storage.postgres import PostgresStorage
from app.storage.mongo import MongoStorage
from app.models.mongo import FileMetadata
import os
import re
from sqlalchemy import func
from app.models.postgres import Rawdata


class Processor:
    def __init__(self, postgres_storage: PostgresStorage, mongo_storage: MongoStorage, settings):
        self.postgres = postgres_storage
        self.mongo = mongo_storage
        self.settings = settings
    
    def extract_codes_from_page(self, html: str) -> list:
        soup = BeautifulSoup(html, 'lxml')
        links = soup.select(self.settings.tags.links_selector)
        codes = []
        for link in links:
            href = link.get('href')
            if href:
                match = re.search(r'/product/(\d+)/', href)
                if match:
                    code = match.group(1)
                    if code not in self.settings.blacklist.codes:
                        codes.append((code, href))
        return codes
    
    def extract_names_from_page(self, html: str, product_code: str) -> list:
        soup = BeautifulSoup(html, 'lxml')
        links = soup.select(self.settings.tags.links_selector)
        names = []
        for link in links:
            href = link.get('href')
            title = link.get_text(strip = True)
            if href and title:
                names.append((title, href, product_code))
        return names
    
    async def extract_and_save_body_html(self, html: str, product_name: str):
        soup = BeautifulSoup(html, 'lxml')
        body = soup.find('body')
        if body:
            body_html = str(body)
            await self.postgres.save_rawdata(product_name, body_html)
    
    async def download_and_save_files(self, html: str, product_name: str):
        soup = BeautifulSoup(html, 'lxml')
        file_links = soup.select(self.settings.tags.file_link_selector)
        
        # ✅ Проверяем количество записей в Rawdata перед скачиванием файлов
        async with self.postgres.session as session:
            rawdata_count = await session.execute(
                    func.count(Rawdata.id).select()
                    )
            count = rawdata_count.scalar()
            if count >= 5:
                logger.info(f"Rawdata limit reached ({count}), skipping file downloads.")
                return
        
        for link in file_links:
            href = link.get('href') or link.get('src')
            if href:
                ext = os.path.splitext(href)[1].lower()
                if ext in self.settings.blacklist.file_extensions:
                    continue
                await self.download_and_store_file(href, product_name)
    
    async def download_and_store_file(self, file_url: str, product_name: str):
        from aiohttp import ClientSession
        timeout = aiohttp.ClientTimeout(total = 30)
        async with ClientSession(timeout = timeout) as session:
            try:
                async with session.get(file_url) as resp:
                    resp.raise_for_status()
                    data = await resp.read()
                    filename = file_url.split('/')[-1]
                    metadata = FileMetadata(
                            original_url = file_url, product_name = product_name, filename = filename,
                            content_type = resp.content_type, size = len(data)
                            )
                    file_id = await self.mongo.save_file(data, metadata)
                    await self.postgres.save_image(product_name, file_id, file_url)
                    logger.info(f"File {filename} saved to MongoDB with ID {file_id}")
            except Exception as e:
                logger.error(f"Failed to download or save file {file_url}: {e}")