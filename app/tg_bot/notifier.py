import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


async def send_return_notification(
    order_id: int,
    item_id: int,
    offer_name: str,
    offer_id: str,
    count: int,
    return_type: str,
    campaign_id: int | None = None,
    chat_id: str | int | None = None,
) -> bool:
    """
    Отправляет интерактивное уведомление о возврате товара в Telegram.
    Под сообщением формируются инлайн-кнопки:
    - «✅ Возвращен» (товар получен продавцом, все хорошо)
    - «⏳ Оставить» (товар еще не пришел к продавцу)
    """
    token = settings.TG_BOT_TOKEN
    target_chat = chat_id or settings.TG_CHAT_ID

    if not token or not target_chat:
        logger.warning(
            "Telegram bot notification skipped: TG_BOT_TOKEN or TG_CHAT_ID not configured."
        )
        return False

    return_label = "Невыкуп" if return_type == "UNREDEEMED" else "Возврат"

    text = (
        f"🔔 <b>Новое уведомление о возврате!</b>\n\n"
        f"📦 <b>Заказ:</b> #{order_id}\n"
        f"🏷 <b>Тип:</b> {return_label}\n"
        + (f"🏢 <b>Кампания:</b> {campaign_id}\n" if campaign_id else "")
        + f"\n"
        f"🛒 <b>Товар:</b> {offer_name}\n"
        f"🆔 <b>Артикул (SKU):</b> <code>{offer_id}</code>\n"
        f"🔢 <b>Возвращаемое количество:</b> {count} шт.\n\n"
        f"Товар уже поступил к продавцу?"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Возвращен",
                callback_data=f"ret_done:{item_id}",
            ),
            InlineKeyboardButton(
                "⏳ Оставить",
                callback_data=f"ret_keep:{item_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 Все непришедшие возвраты",
                callback_data="list_pending",
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        bot = Bot(token=token)
        async with bot:
            await bot.send_message(
                chat_id=target_chat,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        logger.info(f"Telegram return notification sent for order #{order_id}, item {item_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send telegram notification: {e}")
        return False
