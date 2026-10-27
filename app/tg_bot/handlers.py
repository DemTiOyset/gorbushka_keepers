import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from app.tg_bot.services import (
    get_all_pending_returns,
    get_return_by_id,
    set_return_status,
)

logger = logging.getLogger(__name__)


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура бота с кнопкой для отображения всех непришедших возвратов."""
    keyboard = [
        [KeyboardButton("📦 Непришедшие возвраты")],
        [KeyboardButton("🔄 Обновить список")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение и вывод главной клавиатуры."""
    text = (
        "👋 <b>Добро пожаловать в Дозор · Касса Бот!</b>\n\n"
        "Я отслеживаю возвраты товаров с маркетплейсов и помогаю контролировать "
        "их фактическое поступление к продавцу.\n\n"
        "💡 <b>Возможности:</b>\n"
        "• Мгновенные уведомления о новых возвратах\n"
        "• Кнопка <b>«✅ Возвращен»</b> — товар пришел к продавцу и все хорошо\n"
        "• Кнопка <b>«⏳ Оставить»</b> — товар еще в пути и не поступил\n"
        "• Просмотр всех непришедших возвратов по кнопке ниже."
    )
    if update.message:
        await update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_main_reply_keyboard(),
        )


async def show_pending_returns_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает список всех возвратов, которые ещё не пришли к продавцу.
    Каждый возврат оформлен в виде кликабельной кнопки, открывающей форму действия.
    """
    returns = await get_all_pending_returns()

    if not returns:
        msg = (
            "🎉 <b>Отлично! Все возвращенные товары уже получены.</b>\n\n"
            "Непришедших возвратов в данный момент нет."
        )
        if update.message:
            await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_main_reply_keyboard())
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, parse_mode="HTML")
        return

    text = (
        f"📦 <b>Непришедшие возвраты ({len(returns)} шт.):</b>\n"
        "Нажмите на любой возврат ниже, чтобы открыть форму с подтверждением получения:\n"
    )

    keyboard = []
    for ret in returns:
        ret_type = "Невыкуп" if ret["return_type"] == "UNREDEEMED" else "Возврат"
        btn_text = (
            f"Заказ #{ret['order_id']} · {ret['offer_id']} ({ret['returned_count']} шт., {ret_type})"
        )
        keyboard.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"ret_open:{ret['item_id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton("🔄 Обновить список", callback_data="list_pending")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на инлайн-кнопки."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data

    # 1. Показать список непришедших возвратов
    if data == "list_pending":
        await show_pending_returns_message(update, context)
        return

    # 2. Открыть форму для конкретного возврата
    if data.startswith("ret_open:"):
        item_id = int(data.split(":")[1])
        item = await get_return_by_id(item_id)
        if not item:
            await query.answer("Возврат не найден в базе данных.", show_alert=True)
            return

        ret_type = "Невыкуп" if item["return_type"] == "UNREDEEMED" else "Возврат"
        status_str = "✅ Уже получен" if item["is_returned_finished"] else "⏳ В пути к продавцу"

        card_text = (
            f"📋 <b>Управление возвратом</b>\n\n"
            f"📦 <b>Заказ:</b> #{item['order_id']}\n"
            f"🛒 <b>Товар:</b> {item['offer_name']}\n"
            f"🆔 <b>SKU:</b> <code>{item['offer_id']}</code>\n"
            f"🔢 <b>Количество:</b> {item['returned_count']} шт.\n"
            f"🏷 <b>Тип:</b> {ret_type}\n"
            f"📊 <b>Текущий статус:</b> {status_str}\n\n"
            f"Выберите действие:"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Возвращен", callback_data=f"ret_done:{item_id}"),
                InlineKeyboardButton("⏳ Оставить", callback_data=f"ret_keep:{item_id}"),
            ],
            [
                InlineKeyboardButton("◀️ Назад к списку", callback_data="list_pending"),
            ],
        ]
        await query.answer()
        await query.edit_message_text(
            text=card_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # 3. Нажатие «✅ Возвращен»
    if data.startswith("ret_done:"):
        item_id = int(data.split(":")[1])
        success = await set_return_status(item_id, is_finished=True)
        if success:
            item = await get_return_by_id(item_id)
            order_info = f" Заказ #{item['order_id']}" if item else ""
            sku_info = f" ({item['offer_id']})" if item else ""
            
            await query.answer("✅ Статус обновлен: товар пришел к продавцу, возврат закрыт!", show_alert=True)
            new_text = (
                f"✅ <b>Товар успешно возвращен продавцу!</b>\n\n"
                f"{order_info}{sku_info}\n"
                f"Товар поступил к продавцу и все в порядке. Возврат помечен как закрытый."
            )
            keyboard = [
                [InlineKeyboardButton("📦 Список непришедших возвратов", callback_data="list_pending")]
            ]
            await query.edit_message_text(
                text=new_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await query.answer("Не удалось обновить статус возврата.", show_alert=True)
        return

    # 4. Нажатие «⏳ Оставить»
    if data.startswith("ret_keep:"):
        item_id = int(data.split(":")[1])
        success = await set_return_status(item_id, is_finished=False)
        item = await get_return_by_id(item_id)
        order_info = f" Заказ #{item['order_id']}" if item else ""
        sku_info = f" ({item['offer_id']})" if item else ""

        await query.answer("⏳ Товар оставлен в списке ожидаемых возвратов.", show_alert=False)
        new_text = (
            f"⏳ <b>Возврат оставлен в пути</b>\n\n"
            f"{order_info}{sku_info}\n"
            f"Товар еще не поступил к продавцу и остается в списке непришедших."
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Пометить как возвращен", callback_data=f"ret_done:{item_id}"),
            ],
            [
                InlineKeyboardButton("📦 Список непришедших возвратов", callback_data="list_pending"),
            ],
        ]
        await query.edit_message_text(
            text=new_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
