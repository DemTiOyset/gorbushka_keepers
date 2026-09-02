import { useCallback, useEffect, useState } from "react";
import { api, ApiError, OrderResponse, OrdersDayResponse } from "../api";

function todayISO(): string {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

const STATUS_LABELS: Record<string, string> = {
    PLACING: "Оформляется",
    RESERVED: "Зарезервирован",
    UNPAID: "Не оплачен",
    PROCESSING: "В обработке",
    DELIVERY: "Передан в доставку",
    PICKUP: "Ожидает получения",
    DELIVERED: "Получен покупателем",
    CANCELLED: "Отменён",
    PENDING: "Ожидает обработки",
    PARTIALLY_RETURNED: "Частично возвращён",
    RETURNED: "Полностью возвращён",
};

function statusLabel(status: string): string {
    return STATUS_LABELS[status] ?? status;
}

/** CSS-класс бейджа по статусу заказа */
function statusBadgeClass(status: string): string {
    const key = status.toLowerCase();
    const map: Record<string, string> = {
        processing: "status-badge--processing",
        pending: "status-badge--pending",
        delivery: "status-badge--delivery",
        pickup: "status-badge--pickup",
        delivered: "status-badge--delivered",
        cancelled: "status-badge--cancelled",
        returned: "status-badge--returned",
        partially_returned: "status-badge--partially_returned",
        placing: "status-badge--placing",
        reserved: "status-badge--reserved",
        unpaid: "status-badge--unpaid",
    };
    return map[key] ?? "status-badge--unknown";
}

function formatMoney(value: number): string {
    return new Intl.NumberFormat("ru-RU", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
}

export default function Orders() {
    const [date, setDate] = useState<string>(todayISO());
    const [data, setData] = useState<OrdersDayResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadOrders = useCallback(async (target: string) => {
        setLoading(true);
        setError(null);
        try {
            const result = await api.getOrders(target);
            setData(result);
        } catch (err) {
            if (err instanceof ApiError) setError(err.detail);
            else setError("Не удалось загрузить заказы");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadOrders(date);
    }, [date, loadOrders]);

    const orders = data?.orders ?? [];

    const totalPayout = orders.reduce(
        (acc, o) => acc + Number(o.expected_payout),
        0,
    );

    const totalItems = orders.reduce(
        (acc, o) => acc + o.items.reduce((s, i) => s + i.count, 0),
        0,
    );

    return (
        <main className="content">
            <div className="content-head">
                <div>
                    <h2 className="page-title">Заказы с маркетплейса</h2>
                    <p className="page-subtitle">
                        Выберите дату, чтобы увидеть заказы за день
                    </p>
                </div>
                <div className="date-picker-row">
                    <div className="date-picker">
                        <label className="field-label">
                            Дата создания заказа
                        </label>
                        <input
                            className="field-input"
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                        />
                    </div>
                    <button
                        className="btn-ghost btn-ghost--small"
                        onClick={() => setDate(todayISO())}
                        style={{ marginTop: "auto" }}
                    >
                        Сегодня
                    </button>
                </div>
            </div>

            {/* Сводные карточки (или скелетоны при загрузке) */}
            {loading ? (
                <section className="cards-row">
                    <div className="skeleton skeleton-stat" />
                    <div className="skeleton skeleton-stat" />
                    <div className="skeleton skeleton-stat" />
                </section>
            ) : (
                <section className="cards-row">
                    <div className="stat-card">
                        <div className="stat-label">Заказов за день</div>
                        <div className="stat-value">{orders.length}</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">Товаров всего</div>
                        <div className="stat-value">{totalItems}</div>
                    </div>
                    <div className="stat-card stat-card--positive">
                        <div className="stat-label">Ожидаемая выплата</div>
                        <div className="stat-value">
                            {formatMoney(totalPayout)} ₽
                        </div>
                    </div>
                </section>
            )}

            {error && (
                <div className="field-error field-error--block">{error}</div>
            )}

            {/* Скелетоны карточек заказов при загрузке */}
            {loading && (
                <div>
                    <div className="skeleton skeleton-card" />
                    <div className="skeleton skeleton-card" />
                    <div className="skeleton skeleton-card" />
                </div>
            )}

            {/* Список заказов */}
            {!loading && orders.length === 0 ? (
                <section className="actions-section">
                    <div className="empty-state">
                        За {date} заказов не найдено.
                    </div>
                </section>
            ) : (
                orders.map((order) => (
                    <OrderCard key={order.order_id} order={order} />
                ))
            )}
        </main>
    );
}

/** Карточка одного заказа с раскрывающимся списком товаров */
function OrderCard({ order }: { order: OrderResponse }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <section className="order-card">
            <div
                className="order-card__head"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="order-card__left">
                    <h3 className="order-card__title">
                        Заказ #{order.order_id}
                    </h3>
                    <span
                        className={`status-badge ${statusBadgeClass(order.status)}`}
                    >
                        {statusLabel(order.status)}
                    </span>
                </div>
                <div className="order-card__right">
                    <span className="order-card__payout">
                        {formatMoney(Number(order.expected_payout))} ₽
                    </span>
                    <span
                        className={
                            "order-card__expand-icon" +
                            (expanded ? " order-card__expand-icon--open" : "")
                        }
                    >
                        ›
                    </span>
                </div>
            </div>

            {expanded && (
                <div className="table-wrap">
                    <table className="action-table">
                        <thead>
                            <tr>
                                <th>Товар (offer_id)</th>
                                <th>Название</th>
                                <th className="col-money">Кол-во</th>
                                <th className="col-money">Оплата</th>
                                <th className="col-money">Субсидия</th>
                                <th className="col-money">Кешбэк</th>
                                <th className="col-money">НДС</th>
                            </tr>
                        </thead>
                        <tbody>
                            {order.items.map((item) => (
                                <tr key={item.id}>
                                    <td>{item.offer_id}</td>
                                    <td>{item.offer_name}</td>
                                    <td className="col-money">{item.count}</td>
                                    <td className="col-money">
                                        {formatMoney(Number(item.payment))} ₽
                                    </td>
                                    <td className="col-money">
                                        {formatMoney(Number(item.subsidy))} ₽
                                    </td>
                                    <td className="col-money">
                                        {formatMoney(Number(item.cashback))} ₽
                                    </td>
                                    <td className="col-money">
                                        {Number(item.vat) * 100}%
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="order-card__footer">
                Создан: {new Date(order.created_at).toLocaleString("ru-RU")}
                {" · "}
                Кампания: {order.campaign_id}
            </div>
        </section>
    );
}
