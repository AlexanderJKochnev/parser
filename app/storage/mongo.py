# app/storage/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.models.mongo import FileMetadata
import io


class MongoStorage:
    def __init__(self, client: AsyncIOMotorClient, db_name: str, bucket_name: str):
        self.client = client
        self.db = client[db_name]
        self.fs = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket_name)

    async def save_file(self, data: bytes, metadata: FileMetadata) -> str:
        file_id = await self.fs.upload_from_stream(
            filename=metadata.filename or metadata.original_url.split('/')[-1],
            source=io.BytesIO(data),
            metadata=metadata.model_dump()
        )
        return str(file_id)

    async def get_file(self, file_id: str):
        try:
            grid_out = await self.fs.open_download_stream(file_id)
            return await grid_out.read()
        except Exception:
            return None
