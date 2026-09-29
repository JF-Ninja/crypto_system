from sqlalchemy import select, update


class MainRepository:

    def __init__(self, db, model):
        self.db = db
        self.model = model

    async def save_changes(self):
        await self.db.commit()

    async def rollback_changes(self):
        await self.db.rollback()

    async def add(self, info):
        obj = self.model(**info)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, filter_by: dict, values):
        query = update(self.model).filter_by(**filter_by).values(**values)
        result = await self.db.execute(query)
        return result.rowcount

    async def find_all(self, **filter_by: None):
        query = select(self.model).filter_by(**filter_by)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def find_one_or_none(self, **filter_by):
        query = select(self.model).filter_by(**filter_by)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()