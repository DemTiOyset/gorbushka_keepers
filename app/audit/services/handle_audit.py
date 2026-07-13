from datetime import date

from fastapi import HTTPException, status

from app.audit.repositories.audit_repo import AuditRepository
from app.audit.schemas.audit_action import (
    AuditActionCreate,
    AuditActionResponse,
    DeleteResponseDTO,
)
from app.audit.schemas.audit_day import (
    AuditDayFullResponse,
    AuditDaySetInitialCashResponse,
)


class AuditHandler:
    def __init__(self, repo: AuditRepository):
        self.repo = repo

    async def get_day(self, target_date: date) -> AuditDayFullResponse:
        cash_from_db = await self.repo.get_cash()

        initial_cash = cash_from_db.initial_cash
        current_cash = cash_from_db.current_cash

        actions_from_db = await self.repo.get_actions_by_day(target_date)
        valid_actions = [
            AuditActionResponse.model_validate(act) for act in actions_from_db
        ]

        cash_by_day = await self.repo.calculate_cash(target_date=target_date)

        return AuditDayFullResponse(
            initial_cash=initial_cash,
            current_cash=current_cash,
            creation_date=target_date,
            actions=valid_actions,
            cash_by_day=cash_by_day,
        )

    async def update_initial_cash(self, new_initial_cash: int):
        cash_from_db = await self.repo.get_cash()
        cash_changes = await self.repo.calculate_cash()

        cash_from_db.initial_cash = new_initial_cash
        cash_from_db.current_cash = new_initial_cash + cash_changes

        await self.repo.session.commit()

        audit = AuditDaySetInitialCashResponse.model_validate(cash_from_db)

        return audit

    async def create_action(self, payload: AuditActionCreate):
        action_from_db = await self.repo.create_action(payload.model_dump())

        cash_from_db = await self.repo.get_cash()

        cash_from_db.current_cash += action_from_db.money

        cash_by_day = await self.repo.calculate_cash(payload.creation_date)

        await self.repo.session.commit()

        action_id, action, actor, money, current_cash = (
            action_from_db.id,
            action_from_db.action,
            action_from_db.actor,
            action_from_db.money,
            cash_from_db.current_cash,
        )

        action = AuditActionResponse(
            id=action_id,
            actor=actor,
            action=action,
            money=money,
            current_cash=current_cash,
            cash_by_day=cash_by_day,
        )

        return action

    async def delete_action(self, action_id: int):
        deleted_action_from_db = await self.repo.delete_action(action_id=action_id)

        if deleted_action_from_db is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Действие не найдено.",
            )

        cash_from_db = await self.repo.get_cash()

        cash_from_db.current_cash -= deleted_action_from_db.money

        cash_by_day = await self.repo.calculate_cash(
            deleted_action_from_db.creation_date
        )

        await self.repo.session.commit()

        deleted_action_response = DeleteResponseDTO(
            current_cash=cash_from_db.current_cash,
            cash_by_day=cash_by_day,
        )

        return deleted_action_response
