from sqlalchemy.ext.asyncio import AsyncSession

from src.core.application.transactions import SessionManagerProtocol


class TransactionSessionManager(SessionManagerProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        if not self.session.in_transaction():
            await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()


class SessionManager(SessionManagerProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
