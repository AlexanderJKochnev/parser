# app/storage/postgres.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.postgres import Code, Name, Rawdata, Image
from typing import List


class PostgresStorage:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_code(self, code: str, url: str):
        stmt = select(Code).where(Code.code == code)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            new_code = Code(code=code, url=url)
            self.session.add(new_code)
            await self.session.commit()

    async def get_pending_codes(self) -> List[Code]:
        stmt = select(Code).where(Code.status == 'pending')
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_code_status(self, code_id: int, status: str):
        stmt = update(Code).where(Code.id == code_id).values(status=status)
        await self.session.execute(stmt)
        await self.session.commit()

    async def save_name(self, product_code: str, name: str, url: str):
        stmt = select(Name).where(Name.name == name)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            new_name = Name(product_code=product_code, name=name, url=url)
            self.session.add(new_name)
            await self.session.commit()

    async def get_pending_names(self) -> List[Name]:
        stmt = select(Name).where(Name.status == 'pending')
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_name_status(self, name_id: int, status: str):
        stmt = update(Name).where(Name.id == name_id).values(status=status)
        await self.session.execute(stmt)
        await self.session.commit()

    async def save_rawdata(self, product_name: str, body_html: str):
        stmt = select(Rawdata).where(Rawdata.product_name == product_name)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            new_rawdata = Rawdata(product_name=product_name, body_html=body_html)
            self.session.add(new_rawdata)
            await self.session.commit()

    async def save_image(self, product_name: str, file_id: str, file_url: str):
        new_image = Image(product_name=product_name, file_id=file_id, file_url=file_url)
        self.session.add(new_image)
        await self.session.commit()
