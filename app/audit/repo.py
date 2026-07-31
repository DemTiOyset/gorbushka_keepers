from datetime import date
from typing import Protocol, Sequence

from fastapi import Depends
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.audit_action import AuditAction
from app.infrastructure.models.cash import Cash


class AuditRepositoryInterface(Protocol):
    async def get_cash(self) -> "Cash": ...
    async def calculate_cash(self, target_date: date | None = None) -> int: ...
    async def get_actions_by_day(
        self, target_date: date
    ) -> Sequence["AuditAction"]: ...
    async def create_action(self, data: dict) -> "AuditAction": ...
    async def delete_action(self, action_id: int) -> "AuditAction | None": ...
    async def commit(self) -> None: ...


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_cash(self):
        result = await self.session.execute(select(Cash))
        return result.scalar_one()

    async def calculate_cash(self, target_date: date | None = None) -> int:
        stmt = select(func.sum(AuditAction.money))

        if target_date:
            stmt = stmt.where(AuditAction.creation_date == target_date)

        result = await self.session.execute(stmt)

        total_cash = result.scalar() or 0

        return total_cash

    async def get_actions_by_day(self, target_date: date):
        stmt = select(AuditAction).where(AuditAction.creation_date == target_date)
        result = await self.session.execute(stmt)
        audit_actions = result.scalars().all()

        return audit_actions

    async def create_action(self, action_data: dict) -> AuditAction:
        audit_action = AuditAction(**action_data)
        self.session.add(audit_action)

        await self.session.flush()

        return audit_action

    async def update_action(
        self, action_id: int, update_data: dict
    ) -> AuditAction | None:
        stmt = select(AuditAction).where(AuditAction.id == action_id)
        result = await self.session.execute(stmt)
        action = result.scalar_one_or_none()

        if action is None:
            return None

        for key, value in update_data.items():
            setattr(action, key, value)

        await self.session.refresh(action)
        await self.session.flush()

        return action

    async def delete_action(self, action_id: int) -> AuditAction | None:
        stmt = select(AuditAction).where(AuditAction.id == action_id)
        result = await self.session.execute(stmt)
        action = result.scalar_one_or_none()

        if action is None:
            return None

        await self.session.delete(action)
        await self.session.flush()
        return action
