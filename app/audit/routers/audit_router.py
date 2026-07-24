"""
Данный модуль - журнал действий. В нем пользователи указывают изначальное количество денег в кассе
Затем добавляют различные операции (Например: взял в долг у кого то и сумму) сумма имеет знак -, если деньги ушли из кассы и + если прибавились.
На странице должны отображаться: действия за указанный день, изначальная сумма в кассе, текущая сумма в кассе и изменения за день (то есть +5000 или -53214).
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

import app.audit.schemas.audit_action as AuditActionSchemas
from app.audit.repositories.audit_repo import AuditRepository
from app.audit.repositories.dependencies import get_repo_obj
from app.audit.schemas.audit_action import AuditActionResponse, DeleteResponseDTO
from app.audit.schemas.audit_day import AuditDayFullResponse
from app.audit.schemas.audit_exc import ActionNotFoundError
from app.audit.services.handle_audit import AuditHandler

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{date}", response_model=AuditDayFullResponse)
async def get(
    date: date, repo: AuditRepository = Depends(get_repo_obj)
) -> AuditDayFullResponse:
    """
    Данный роут берет из базы данных изначальную сумму в кассе,
    которая по умолчанию 0 и текущую сумму, которая рассчитывается из изначальной суммы
    и действий, которые совершаются с деньгами в кассе, а так же берет все действия за указанный день
    и возвращает их.
    Пусть будет возможность выбора даты.
    """
    handler = AuditHandler(repo=repo)
    return await handler.get_day(date)


@router.post("/initial_cash")
async def set_initial_cash(
    initial_cash: int = Query(..., description="Новая изначальная сумма в кассе"),
    repo: AuditRepository = Depends(get_repo_obj),
):
    """
    Данный роут нужен для изменения изначальной суммы в кассе.
    Пусть при нажатии на изначальную сумму она становится интерактивной и появляются кнопочки Отменить и Сохранить.
    """
    handler = AuditHandler(repo=repo)
    return await handler.update_initial_cash(initial_cash)


@router.post("/action", response_model=AuditActionResponse)
async def create_action(
    payload: AuditActionSchemas.AuditActionCreate,
    repo: AuditRepository = Depends(get_repo_obj),
) -> AuditActionResponse:
    """
    Данный роут создает новое действие в кассе на сегодняшний день.
    Пусть справа будет кнопочка "добавить действие", при нажатии на которую появляется окошко для создания действия с кнопочками Сохранить или Отменить
    """
    handler = AuditHandler(repo=repo)
    return await handler.create_action(payload)


@router.delete("/action/{audit_id}", response_model=DeleteResponseDTO)
async def delete_action(
    action_id: int = Query(..., description="ID удаляемого действия"),
    repo: AuditRepository = Depends(get_repo_obj),
):
    """Данный роут удаляет
    Пусть при нажатии на действие справа сверху была кнопочка корзины, при нажатии на которое всплывало бы уведомление: вы точно хотите удалить и если нажать да, то действие удалялось бы, если нет, то сброс."""
    try:
        handler = AuditHandler(repo=repo)
        return await handler.delete_action(action_id)
    except ActionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Действие не найдено.",
        )
