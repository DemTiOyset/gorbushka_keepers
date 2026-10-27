// API и локальное хранилище данных приложения «Дозор · Касса»
// Поддерживает журнал кассы, расчёт остатков, заказы и возвраты с маркетплейса.

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface AuditAction {
    id: number;
    actor: string;
    action: string;
    money: number;
    creation_date?: string;
    created_at?: string;
}

export interface AuditActionCreateResponse extends AuditAction {
    current_cash: number;
    cash_by_day: number;
}

export interface AuditDay {
    initial_cash: number;
    current_cash: number;
    creation_date: string;
    actions: AuditAction[];
    cash_by_day: number | null;
}

export interface DeleteResponse {
    status: string;
    message: string;
    cash_by_day: number;
    current_cash: number;
}

// --- Заказы ---

export interface OrderItemResponse {
    id: number;
    order_id: number;
    offer_id: string;
    offer_name: string;
    count: number;
    returned_count: number | null;
    is_returned_finished: boolean;
    return_type: string | null;
    payment: number;
    subsidy: number;
    cashback: number;
    vat: number;
}

export interface OrderResponse {
    order_id: number;
    campaign_id: number;
    created_at: string;
    status: string;
    expected_payout: number;
    payout: number | null;
    is_cancelled: boolean;
    has_returned: boolean;
    items: OrderItemResponse[];
}

export interface OrdersDayResponse {
    orders: OrderResponse[];
}

export interface CancellationsAndReturnsResponse {
    cancellations: OrderResponse[];
    returns: OrderItemResponse[];
}

export class ApiError extends Error {
    status: number;
    detail: string;

    constructor(status: number, detail: string) {
        super(detail);
        this.status = status;
        this.detail = detail;
    }
}

export const AUTH_UNAUTHORIZED_EVENT = "auth:unauthorized";

function getTodayISO(): string {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

const STORAGE_KEYS = {
    INITIAL_CASH: "dozor_initial_cash",
    ACTIONS: "dozor_audit_actions",
    ORDERS: "dozor_orders",
};

// Начальные демонстрационные данные (согласно seed.py и бизнес-логике магазина)
function getInitialSeedData() {
    const today = getTodayISO();
    const nowISO = new Date().toISOString();

    const initialCash = 50000;

    const initialActions: AuditAction[] = [
        {
            id: 1,
            actor: "Осман",
            action: "Выручка с витрины (наличные)",
            money: 18500,
            creation_date: today,
            created_at: nowISO,
        },
        {
            id: 2,
            actor: "Тимур",
            action: "Взял в долг у поставщика",
            money: -5000,
            creation_date: today,
            created_at: nowISO,
        },
        {
            id: 3,
            actor: "Осман",
            action: "Продажа аксессуаров и чехлов",
            money: 7200,
            creation_date: today,
            created_at: nowISO,
        },
        {
            id: 4,
            actor: "Тимур",
            action: "Оплата курьерской доставки",
            money: -2400,
            creation_date: today,
            created_at: nowISO,
        },
    ];

    const initialOrders: OrderResponse[] = [
        {
            order_id: 777001,
            campaign_id: 100500,
            created_at: `${today}T09:15:00.000Z`,
            status: "PROCESSING",
            expected_payout: 3500.0,
            payout: null,
            is_cancelled: false,
            has_returned: false,
            items: [
                {
                    id: 101,
                    order_id: 777001,
                    offer_id: "SKU-777001-A",
                    offer_name: "Защитное стекло Ceramic Pro (iPhone 15)",
                    count: 2,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 2000.0,
                    subsidy: 100.0,
                    cashback: 50.0,
                    vat: 0.2,
                },
                {
                    id: 102,
                    order_id: 777001,
                    offer_id: "SKU-777001-B",
                    offer_name: "Чехол силиконовый MagSafe Clear",
                    count: 1,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 1500.0,
                    subsidy: 0.0,
                    cashback: 0.0,
                    vat: 0.2,
                },
            ],
        },
        {
            order_id: 777002,
            campaign_id: 100500,
            created_at: `${today}T10:40:00.000Z`,
            status: "DELIVERED",
            expected_payout: 4200.0,
            payout: 4200.0,
            is_cancelled: false,
            has_returned: false,
            items: [
                {
                    id: 103,
                    order_id: 777002,
                    offer_id: "SKU-777002-A",
                    offer_name: "Кабель Type-C to Lightning 1m braided",
                    count: 2,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 2200.0,
                    subsidy: 100.0,
                    cashback: 100.0,
                    vat: 0.2,
                },
                {
                    id: 104,
                    order_id: 777002,
                    offer_id: "SKU-777002-B",
                    offer_name: "Сетевое З/У 35W Dual USB-C Port",
                    count: 1,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 2000.0,
                    subsidy: 0.0,
                    cashback: 0.0,
                    vat: 0.2,
                },
            ],
        },
        {
            order_id: 777003,
            campaign_id: 100500,
            created_at: `${today}T11:20:00.000Z`,
            status: "CANCELLED",
            expected_payout: 3500.0,
            payout: 0,
            is_cancelled: true,
            has_returned: false,
            items: [
                {
                    id: 105,
                    order_id: 777003,
                    offer_id: "SKU-777003-A",
                    offer_name: "Беспроводной PowerBank 10000 mAh",
                    count: 2,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 2000.0,
                    subsidy: 100.0,
                    cashback: 50.0,
                    vat: 0.2,
                },
                {
                    id: 106,
                    order_id: 777003,
                    offer_id: "SKU-777003-B",
                    offer_name: "Держатель в авто с MagSafe",
                    count: 1,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 1500.0,
                    subsidy: 0.0,
                    cashback: 0.0,
                    vat: 0.2,
                },
            ],
        },
        {
            order_id: 777004,
            campaign_id: 100501,
            created_at: `${today}T12:05:00.000Z`,
            status: "PARTIALLY_RETURNED",
            expected_payout: 2500.0,
            payout: null,
            is_cancelled: false,
            has_returned: true,
            items: [
                {
                    id: 107,
                    order_id: 777004,
                    offer_id: "SKU-777004-A",
                    offer_name: "Ремешок силиконовый для Apple Watch 45mm",
                    count: 2,
                    returned_count: 1,
                    is_returned_finished: true,
                    return_type: "RETURN",
                    payment: 1000.0,
                    subsidy: 50.0,
                    cashback: 20.0,
                    vat: 0.2,
                },
                {
                    id: 108,
                    order_id: 777004,
                    offer_id: "SKU-777004-B",
                    offer_name: "Защитный бампер для Apple Watch",
                    count: 1,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 1500.0,
                    subsidy: 0.0,
                    cashback: 0.0,
                    vat: 0.2,
                },
            ],
        },
        {
            order_id: 777005,
            campaign_id: 100501,
            created_at: `${today}T14:30:00.000Z`,
            status: "DELIVERED",
            expected_payout: 3100.0,
            payout: null,
            is_cancelled: false,
            has_returned: true,
            items: [
                {
                    id: 109,
                    order_id: 777005,
                    offer_id: "SKU-777005-A",
                    offer_name: "Кабель AUX аудио Jack 3.5mm",
                    count: 1,
                    returned_count: null,
                    is_returned_finished: false,
                    return_type: null,
                    payment: 1100.0,
                    subsidy: 0.0,
                    cashback: 0.0,
                    vat: 0.2,
                },
                {
                    id: 110,
                    order_id: 777005,
                    offer_id: "SKU-777005-B",
                    offer_name: "Адаптер Bluetooth 5.3 для автомагнитолы",
                    count: 1,
                    returned_count: 1,
                    is_returned_finished: true,
                    return_type: "UNREDEEMED",
                    payment: 2000.0,
                    subsidy: 0.0,
                    cashback: 0.0,
                    vat: 0.2,
                },
            ],
        },
    ];

    return { initialCash, initialActions, initialOrders };
}

function loadInitialCash(): number {
    const raw = localStorage.getItem(STORAGE_KEYS.INITIAL_CASH);
    if (raw === null) {
        const { initialCash } = getInitialSeedData();
        localStorage.setItem(STORAGE_KEYS.INITIAL_CASH, String(initialCash));
        return initialCash;
    }
    return parseInt(raw, 10) || 0;
}

function saveInitialCash(val: number) {
    localStorage.setItem(STORAGE_KEYS.INITIAL_CASH, String(val));
}

function loadActions(): AuditAction[] {
    const raw = localStorage.getItem(STORAGE_KEYS.ACTIONS);
    if (raw === null) {
        const { initialActions } = getInitialSeedData();
        localStorage.setItem(STORAGE_KEYS.ACTIONS, JSON.stringify(initialActions));
        return initialActions;
    }
    try {
        return JSON.parse(raw);
    } catch {
        return [];
    }
}

function saveActions(actions: AuditAction[]) {
    localStorage.setItem(STORAGE_KEYS.ACTIONS, JSON.stringify(actions));
}

function loadOrders(): OrderResponse[] {
    const raw = localStorage.getItem(STORAGE_KEYS.ORDERS);
    if (raw === null) {
        const { initialOrders } = getInitialSeedData();
        localStorage.setItem(STORAGE_KEYS.ORDERS, JSON.stringify(initialOrders));
        return initialOrders;
    }
    try {
        return JSON.parse(raw);
    } catch {
        return [];
    }
}

export const api = {
    async login(username: string, password: string): Promise<TokenResponse> {
        // Имитация валидации
        await new Promise((r) => setTimeout(r, 150));
        const trimmed = username.trim();
        if (!trimmed) {
            throw new ApiError(400, "Укажите имя пользователя");
        }
        if (!password) {
            throw new ApiError(400, "Укажите пароль");
        }

        const fakeToken = `dozor_token_${trimmed}_${Date.now()}`;
        return {
            access_token: fakeToken,
            token_type: "bearer",
        };
    },

    async getDay(date: string): Promise<AuditDay> {
        await new Promise((r) => setTimeout(r, 60));
        const initialCash = loadInitialCash();
        const allActions = loadActions();

        // Текущая сумма = изначальная + сумма всех действий в истории
        const totalDelta = allActions.reduce((sum, a) => sum + (Number(a.money) || 0), 0);
        const currentCash = initialCash + totalDelta;

        // Действия за указанную дату
        const dayActions = allActions.filter((a) => a.creation_date === date);
        const cashByDay = dayActions.reduce((sum, a) => sum + (Number(a.money) || 0), 0);

        return {
            initial_cash: initialCash,
            current_cash: currentCash,
            creation_date: date,
            actions: dayActions,
            cash_by_day: cashByDay,
        };
    },

    async setInitialCash(newInitial: number) {
        await new Promise((r) => setTimeout(r, 80));
        saveInitialCash(newInitial);
        const allActions = loadActions();
        const totalDelta = allActions.reduce((sum, a) => sum + (Number(a.money) || 0), 0);
        return {
            initial_cash: newInitial,
            current_cash: newInitial + totalDelta,
        };
    },

    async createAction(payload: {
        actor: string;
        action: string;
        money: number;
        creation_date?: string;
    }): Promise<AuditActionCreateResponse> {
        await new Promise((r) => setTimeout(r, 80));
        const date = payload.creation_date || getTodayISO();
        const allActions = loadActions();

        const newId = allActions.length > 0 ? Math.max(...allActions.map((a) => a.id)) + 1 : 1;
        const newRecord: AuditAction = {
            id: newId,
            actor: payload.actor,
            action: payload.action,
            money: payload.money,
            creation_date: date,
            created_at: new Date().toISOString(),
        };

        const updated = [...allActions, newRecord];
        saveActions(updated);

        const initialCash = loadInitialCash();
        const totalDelta = updated.reduce((sum, a) => sum + (Number(a.money) || 0), 0);
        const currentCash = initialCash + totalDelta;

        const dayActions = updated.filter((a) => a.creation_date === date);
        const cashByDay = dayActions.reduce((sum, a) => sum + (Number(a.money) || 0), 0);

        return {
            ...newRecord,
            current_cash: currentCash,
            cash_by_day: cashByDay,
        };
    },

    async deleteAction(auditId: number, actionId: number): Promise<DeleteResponse> {
        await new Promise((r) => setTimeout(r, 80));
        const allActions = loadActions();
        const target = allActions.find((a) => a.id === actionId);
        if (!target) {
            throw new ApiError(404, "Действие не найдено");
        }

        const date = target.creation_date || getTodayISO();
        const filtered = allActions.filter((a) => a.id !== actionId);
        saveActions(filtered);

        const initialCash = loadInitialCash();
        const totalDelta = filtered.reduce((sum, a) => sum + (Number(a.money) || 0), 0);
        const currentCash = initialCash + totalDelta;

        const dayActions = filtered.filter((a) => a.creation_date === date);
        const cashByDay = dayActions.reduce((sum, a) => sum + (Number(a.money) || 0), 0);

        return {
            status: "ok",
            message: "Действие успешно удалено",
            cash_by_day: cashByDay,
            current_cash: currentCash,
        };
    },

    async getOrders(day: string): Promise<OrdersDayResponse> {
        await new Promise((r) => setTimeout(r, 70));
        const allOrders = loadOrders();
        // Фильтруем по дате (YYYY-MM-DD в начале ISO-строки created_at)
        const dayOrders = allOrders.filter((o) => o.created_at.startsWith(day));
        return {
            orders: dayOrders,
        };
    },

    async getReturns(): Promise<CancellationsAndReturnsResponse> {
        await new Promise((r) => setTimeout(r, 70));
        const allOrders = loadOrders();

        const cancellations = allOrders.filter((o) => o.is_cancelled);
        const returns: OrderItemResponse[] = [];

        for (const order of allOrders) {
            for (const item of order.items) {
                if ((item.returned_count ?? 0) > 0) {
                    returns.push(item);
                }
            }
        }

        return {
            cancellations,
            returns,
        };
    },
};
