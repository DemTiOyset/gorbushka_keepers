import { useCallback, useEffect, useState } from "react";
import { api, ApiError, AuditAction, AuditDay } from "../api";
import { session } from "../auth";

interface Props {
    onLogout: () => void;
}

function todayISO(): string {
    // Локальная дата в формате YYYY-MM-DD.
    // toISOString() здесь не подходит — он возвращает UTC и для таймзон с
    // положительным смещением даёт «завтра» поздно вечером.
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

function isToday(dateISO: string): boolean {
    return dateISO === todayISO();
}

function formatMoney(value: number): string {
    return new Intl.NumberFormat("ru-RU").format(value);
}

export default function Dashboard({ onLogout }: Props) {
    const [date, setDate] = useState<string>(todayISO());
    const [day, setDay] = useState<AuditDay | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Редактирование изначальной суммы
    const [editingInitial, setEditingInitial] = useState(false);
    const [initialDraft, setInitialDraft] = useState("0");
    const [savingInitial, setSavingInitial] = useState(false);

    // Создание действия
    const [showCreate, setShowCreate] = useState(false);
    const [newActor, setNewActor] = useState("");
    const [newAction, setNewAction] = useState("");
    const [newMoney, setNewMoney] = useState("");
    const [creating, setCreating] = useState(false);

    // Удаление действия
    const [pendingDelete, setPendingDelete] = useState<AuditAction | null>(
        null,
    );
    const [deleting, setDeleting] = useState(false);

    const username = session.getUsername();

    const loadDay = useCallback(async (target: string) => {
        setLoading(true);
        setError(null);
        try {
            const data = await api.getDay(target);
            setDay(data);
        } catch (err) {
            if (err instanceof ApiError) setError(err.detail);
            else setError("Не удалось загрузить данные за день");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadDay(date);
    }, [date, loadDay]);

    function startEditInitial() {
        setInitialDraft(String(day?.initial_cash ?? 0));
        setEditingInitial(true);
    }

    async function saveInitial() {
        const parsed = parseInt(initialDraft, 10);
        if (Number.isNaN(parsed)) {
            setError("Введите корректное число для изначальной суммы");
            return;
        }
        setSavingInitial(true);
        setError(null);
        try {
            await api.setInitialCash(parsed);
            setEditingInitial(false);
            await loadDay(date);
        } catch (err) {
            if (err instanceof ApiError) setError(err.detail);
            else setError("Не удалось сохранить изначальную сумму");
        } finally {
            setSavingInitial(false);
        }
    }

    async function handleCreateAction(e: React.FormEvent) {
        e.preventDefault();
        const money = parseInt(newMoney, 10);
        if (Number.isNaN(money)) {
            setError("Введите корректную сумму (может быть отрицательной)");
            return;
        }
        setCreating(true);
        setError(null);
        try {
            await api.createAction({
                actor: newActor.trim(),
                action: newAction.trim(),
                money,
            });
            setNewActor("");
            setNewAction("");
            setNewMoney("");
            setShowCreate(false);
            await loadDay(date);
        } catch (err) {
            if (err instanceof ApiError) setError(err.detail);
            else setError("Не удалось создать действие");
        } finally {
            setCreating(false);
        }
    }

    async function confirmDelete() {
        if (!pendingDelete) return;
        setDeleting(true);
        setError(null);
        try {
            // Бэкенд требует audit_id в пути и action_id в query.
            // Из схемы action.id — это идентификатор действия.
            await api.deleteAction(pendingDelete.id, pendingDelete.id);
            setPendingDelete(null);
            await loadDay(date);
        } catch (err) {
            if (err instanceof ApiError) setError(err.detail);
            else setError("Не удалось удалить действие");
        } finally {
            setDeleting(false);
        }
    }

    const totalDelta = day?.actions?.reduce((acc, a) => acc + a.money, 0) ?? 0;
    const deltaPositive = totalDelta >= 0;

    // Добавлять и удалять действия можно только за сегодняшний день.
    // Прошлые и будущие дни доступны только для просмотра.
    const canModify = isToday(date);

    return (
        <div className="dashboard">
            <header className="topbar">
                <div className="topbar-brand">
                    <span className="brand-mark">₽</span>
                    <span className="brand-text">Горбушка · Касса</span>
                </div>
                <div className="topbar-user">
                    <span className="user-greeting">{username}</span>
                    <button className="btn-ghost" onClick={onLogout}>
                        Выйти
                    </button>
                </div>
            </header>

            <main className="content">
                <div className="content-head">
                    <div>
                        <h2 className="page-title">Журнал кассы</h2>
                        <p className="page-subtitle">
                            Выберите дату, чтобы увидеть действия и остаток
                            средств за день
                        </p>
                    </div>
                    <div className="date-picker">
                        <label className="field-label">
                            Дата операционного дня
                        </label>
                        <input
                            className="field-input"
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                        />
                    </div>
                </div>

                {/* Сводные карточки */}
                <section className="cards-row">
                    {/* Изначальная сумма — интерактивная */}
                    <div className="stat-card stat-card--accent">
                        <div className="stat-label">Изначальная сумма</div>
                        {!editingInitial ? (
                            <button
                                className="stat-value-btn"
                                onClick={startEditInitial}
                            >
                                <span className="stat-value">
                                    {formatMoney(day?.initial_cash ?? 0)} ₽
                                </span>
                                <span className="stat-hint">
                                    нажмите, чтобы изменить
                                </span>
                            </button>
                        ) : (
                            <div className="inline-edit">
                                <input
                                    className="field-input field-input--small"
                                    type="number"
                                    value={initialDraft}
                                    onChange={(e) =>
                                        setInitialDraft(e.target.value)
                                    }
                                    disabled={savingInitial}
                                    autoFocus
                                />
                                <div className="inline-edit-actions">
                                    <button
                                        className="btn-primary btn-primary--small"
                                        onClick={saveInitial}
                                        disabled={savingInitial}
                                    >
                                        {savingInitial ? "..." : "Сохранить"}
                                    </button>
                                    <button
                                        className="btn-ghost btn-ghost--small"
                                        onClick={() => setEditingInitial(false)}
                                        disabled={savingInitial}
                                    >
                                        Отменить
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="stat-card">
                        <div className="stat-label">Текущая сумма в кассе</div>
                        <div className="stat-value">
                            {formatMoney(day?.current_cash ?? 0)} ₽
                        </div>
                        <div className="stat-hint stat-hint--muted">
                            общий остаток
                        </div>
                    </div>

                    <div
                        className={`stat-card ${deltaPositive ? "stat-card--positive" : "stat-card--negative"}`}
                    >
                        <div className="stat-label">Изменения за день</div>
                        <div className="stat-value">
                            {deltaPositive ? "+" : ""}
                            {formatMoney(totalDelta)} ₽
                        </div>
                        <div className="stat-hint stat-hint--muted">
                            {day?.actions?.length ?? 0} действ.
                        </div>
                    </div>
                </section>

                {error && (
                    <div className="field-error field-error--block">
                        {error}
                    </div>
                )}
                {loading && <div className="muted-text">Загрузка...</div>}

                {/* Таблица действий */}
                <section className="actions-section">
                    <div className="section-head">
                        <div>
                            <h3 className="section-title">
                                Действия за {date}
                            </h3>
                            {!canModify && (
                                <span className="day-mode-hint">
                                    Просмотр · изменения доступны только за
                                    сегодняшний день
                                </span>
                            )}
                        </div>
                        {canModify && (
                            <button
                                className="btn-primary"
                                onClick={() => setShowCreate(true)}
                            >
                                + Добавить действие
                            </button>
                        )}
                    </div>

                    {!loading && (day?.actions?.length ?? 0) === 0 ? (
                        <div className="empty-state">
                            {canModify ? (
                                <>
                                    За этот день действий не зафиксировано.
                                    <br />
                                    Нажмите «Добавить действие», чтобы внести
                                    первую запись.
                                </>
                            ) : (
                                <>За этот день действий не зафиксировано.</>
                            )}
                        </div>
                    ) : (
                        <div className="table-wrap">
                            <table className="action-table">
                                <thead>
                                    <tr>
                                        <th className="col-id">№</th>
                                        <th className="col-actor">Кто</th>
                                        <th>Действие</th>
                                        <th className="col-money">Сумма</th>
                                        <th className="col-cash">
                                            Итог за день
                                        </th>
                                        {canModify && (
                                            <th className="col-actions"></th>
                                        )}
                                    </tr>
                                </thead>
                                <tbody>
                                    {day?.actions?.map((a) => (
                                        <tr key={a.id}>
                                            <td className="col-id">{a.id}</td>
                                            <td className="col-actor">
                                                {a.actor}
                                            </td>
                                            <td>{a.action}</td>
                                            <td
                                                className={`col-money ${a.money >= 0 ? "money-positive" : "money-negative"}`}
                                            >
                                                {a.money >= 0 ? "+" : ""}
                                                {formatMoney(a.money)} ₽
                                            </td>
                                            <td className="col-cash">
                                                {formatMoney(a.cash_by_day)} ₽
                                            </td>
                                            {canModify && (
                                                <td className="col-actions">
                                                    <button
                                                        className="btn-icon"
                                                        title="Удалить"
                                                        onClick={() =>
                                                            setPendingDelete(a)
                                                        }
                                                    >
                                                        ✕
                                                    </button>
                                                </td>
                                            )}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            </main>

            {/* Модалка создания действия */}
            {showCreate && (
                <div
                    className="modal-overlay"
                    onClick={() => !creating && setShowCreate(false)}
                >
                    <div
                        className="modal-card"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-head">
                            <h3 className="modal-title">Новое действие</h3>
                            <button
                                className="btn-icon"
                                onClick={() =>
                                    !creating && setShowCreate(false)
                                }
                                disabled={creating}
                            >
                                ✕
                            </button>
                        </div>
                        <form
                            className="modal-body"
                            onSubmit={handleCreateAction}
                        >
                            <label className="field-label">
                                Кто совершил действие
                            </label>
                            <input
                                className="field-input"
                                type="text"
                                value={newActor}
                                onChange={(e) => setNewActor(e.target.value)}
                                placeholder="например, Тимур"
                                autoFocus
                                required
                            />

                            <label className="field-label">
                                Описание действия
                            </label>
                            <input
                                className="field-input"
                                type="text"
                                value={newAction}
                                onChange={(e) => setNewAction(e.target.value)}
                                placeholder="например, взял в долг у поставщика"
                                required
                            />

                            <label className="field-label">
                                Сумма (со знаком минус, если деньги ушли)
                            </label>
                            <input
                                className="field-input"
                                type="number"
                                value={newMoney}
                                onChange={(e) => setNewMoney(e.target.value)}
                                placeholder="например, -5000 или 10000"
                                required
                            />

                            <div className="modal-actions">
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => setShowCreate(false)}
                                    disabled={creating}
                                >
                                    Отменить
                                </button>
                                <button
                                    type="submit"
                                    className="btn-primary"
                                    disabled={creating}
                                >
                                    {creating ? "Сохраняем..." : "Сохранить"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Модалка подтверждения удаления */}
            {pendingDelete && (
                <div
                    className="modal-overlay"
                    onClick={() => !deleting && setPendingDelete(null)}
                >
                    <div
                        className="modal-card modal-card--small"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="modal-title">Удалить действие?</h3>
                        <p className="modal-text">
                            Действие «{pendingDelete.action}» (
                            {formatMoney(pendingDelete.money)} ₽) будет удалено
                            без возможности восстановления.
                        </p>
                        <div className="modal-actions">
                            <button
                                className="btn-ghost"
                                onClick={() => setPendingDelete(null)}
                                disabled={deleting}
                            >
                                Нет, сброс
                            </button>
                            <button
                                className="btn-danger"
                                onClick={confirmDelete}
                                disabled={deleting}
                            >
                                {deleting ? "Удаляем..." : "Да, удалить"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
