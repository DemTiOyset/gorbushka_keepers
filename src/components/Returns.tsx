import { useCallback, useEffect, useState } from "react";
import {
    api,
    ApiError,
    CancellationsAndReturnsResponse,
    OrderItemResponse,
    OrderResponse,
} from "../api";

function formatMoney(value: number): string {
    return new Intl.NumberFormat("ru-RU", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
}

/** «Невыкуп» для UNREDEEMED, «Возврат» для всего остального. */
function returnTypeLabel(item: OrderItemResponse): string {
    return item.return_type === "UNREDEEMED" ? "Невыкуп" : "Возврат";
}

export default function Returns() {
    const [data, setData] = useState<CancellationsAndReturnsResponse | null>(
        null,
    );
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await api.getReturns();
            setData(result);
        } catch (err) {
            if (err instanceof ApiError) setError(err.detail);
            else setError("Не удалось загрузить возвраты и отмены");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const cancellations = data?.cancellations ?? [];
    const returns = data?.returns ?? [];

    return (
        <main className="content">
            <div className="content-head">
                <div>
                    <h2 className="page-title">Возвраты и отмены</h2>
                    <p className="page-subtitle">
                        Отменённые заказы и возвращённые товары
                    </p>
                </div>
            </div>

            {error && (
                <div className="field-error field-error--block">{error}</div>
            )}

            {loading && (
                <div>
                    <div className="skeleton skeleton-card" />
                    <div className="skeleton skeleton-card" />
                    <div className="skeleton skeleton-card" />
                </div>
            )}

            {!loading && (
                <>
                    {/* Отменённые заказы */}
                    <section className="actions-section">
                        <div className="section-head">
                            <h3 className="section-title">
                                Отменённые заказы ({cancellations.length})
                            </h3>
                        </div>
                        {cancellations.length === 0 ? (
                            <div className="empty-state">
                                Отменённых заказов нет.
                            </div>
                        ) : (
                            cancellations.map((order) => (
                                <CancellationCard
                                    key={order.order_id}
                                    order={order}
                                />
                            ))
                        )}
                    </section>

                    {/* Возвраты и невыкупы */}
                    <section className="actions-section" style={{ marginTop: 24 }}>
                        <div className="section-head">
                            <h3 className="section-title">
                                Возвраты и невыкупы ({returns.length})
                            </h3>
                        </div>
                        {returns.length === 0 ? (
                            <div className="empty-state">
                                Возвращённых товаров нет.
                            </div>
                        ) : (
                            returns.map((item) => (
                                <ReturnItemCard key={item.id} item={item} />
                            ))
                        )}
                    </section>
                </>
            )}
        </main>
    );
}

/** Карточка отменённого заказа (вся красная). */
function CancellationCard({ order }: { order: OrderResponse }) {
    return (
        <section className="order-card order-card--cancelled">
            <div className="order-card__head">
                <div className="order-card__left">
                    <h3 className="order-card__title">
                        Заказ #{order.order_id}
                    </h3>
                    <span className="status-badge status-badge--cancelled">
                        Отменён
                    </span>
                </div>
                <div className="order-card__right">
                    <span className="order-card__payout">
                        {formatMoney(Number(order.expected_payout))} ₽
                    </span>
                </div>
            </div>
            <div className="order-card__footer">
                Кампания: {order.campaign_id} · Создан:{" "}
                {new Date(order.created_at).toLocaleString("ru-RU")}
            </div>
        </section>
    );
}

/** Карточка возвращённого/невыкупленного товара с контекстом заказа. */
function ReturnItemCard({ item }: { item: OrderItemResponse }) {
    return (
        <section className="order-card">
            <div className="order-card__head">
                <div className="order-card__left">
                    <h3 className="order-card__title">
                        Заказ #{item.order_id} · {item.offer_id}
                    </h3>
                    <span className="muted-text">{item.offer_name}</span>
                </div>
                <div className="order-card__right">
                    <span className="status-badge status-badge--returned">
                        {returnTypeLabel(item)}
                    </span>
                </div>
            </div>
            <div className="order-card__footer">
                Возвращено: {item.returned_count ?? 0} шт.
            </div>
        </section>
    );
}
