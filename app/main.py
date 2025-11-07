# app/main.py
import asyncio
from loguru import logger
from app.config import Settings
from app.models.postgres import init_db, Rawdata
from app.storage.postgres import PostgresStorage
from app.storage.mongo import MongoStorage
from app.parsers.fetcher import Fetcher
from app.parsers.processor import Processor
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import func


async def main_loop(settings: Settings, gui: 'ParserGUI' = None):
    # Инициализация БД
    async_session = await init_db(settings)
    
    # Подключение к MongoDB
    mongo_client = AsyncIOMotorClient(settings.database.mongodb.url)
    mongo_storage = MongoStorage(
            client = mongo_client, db_name = settings.database.mongodb.database,
            bucket_name = settings.database.mongodb.collection
            )
    
    codes_processed = 0
    names_processed = 0
    files_downloaded = 0
    errors = 0
    
    async with async_session() as session:
        postgres_storage = PostgresStorage(session)
        
        async with Fetcher(settings) as fetcher:
            processor = Processor(postgres_storage, mongo_storage, settings)
            
            # Шаг 1: Получить все ссылки с кодами (если еще не сохранены)
            html = await fetcher.fetch(settings.site.base_url)
            if html:
                codes = processor.extract_codes_from_page(html)
                for code, url in codes:
                    await postgres_storage.save_code(code, url)
                logger.info(f"Saved {len(codes)} codes to DB")
            
            # Шаг 2: Обработать все незавершенные коды
            pending_codes = await postgres_storage.get_pending_codes()
            for code_obj in pending_codes:
                if not gui or not gui.is_running:
                    logger.info("Parser stopped by user.")
                    return
                try:
                    code_url = code_obj.url
                    if not code_url.startswith('http'):
                        code_url = settings.site.base_url.rstrip('/') + code_url
                    html = await fetcher.fetch(code_url)
                    if html:
                        names = processor.extract_names_from_page(html, code_obj.code)
                        for name, url, code in names:
                            await postgres_storage.save_name(code, name, url)
                        await postgres_storage.update_code_status(code_obj.id, 'done')
                        codes_processed += 1
                        if gui:
                            gui.update_stats(codes = codes_processed, errors = errors)
                except Exception as e:
                    logger.error(f"Error processing code {code_obj.code}: {e}")
                    await postgres_storage.update_code_status(code_obj.id, 'error')
                    errors += 1
                    if gui:
                        gui.update_stats(errors = errors)
            
            # Шаг 3: Обработать все незавершенные имена
            pending_names = await postgres_storage.get_pending_names()
            for name_obj in pending_names:
                if not gui or not gui.is_running:
                    logger.info("Parser stopped by user.")
                    return
                try:
                    name_url = name_obj.url
                    if not name_url.startswith('http'):
                        name_url = settings.site.base_url.rstrip('/') + name_url
                    html = await fetcher.fetch(name_url)
                    if html:
                        await processor.extract_and_save_body_html(html, name_obj.name)
                        await processor.download_and_save_files(html, name_obj.name)
                        await postgres_storage.update_name_status(name_obj.id, 'done')
                        names_processed += 1
                        files_downloaded += 1
                        if gui:
                            gui.update_stats(names = names_processed, files = files_downloaded, errors = errors)
                        
                        # ✅ Проверяем количество записей в Rawdata
                        rawdata_count = await session.execute(
                                func.count(Rawdata.id).select()
                                )
                        count = rawdata_count.scalar()
                        if count >= 5:
                            logger.info(f"Test limit reached: {count} rawdata entries. Stopping.")
                            if gui:
                                gui.stop_parser()  # Останавливаем GUI
                            return
                
                except Exception as e:
                    logger.error(f"Error processing name {name_obj.name}: {e}")
                    await postgres_storage.update_name_status(name_obj.id, 'error')
                    errors += 1
                    if gui:
                        gui.update_stats(errors = errors)
    
    logger.info("Parsing completed successfully.")