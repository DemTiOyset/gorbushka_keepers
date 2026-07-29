// API клиент: общается с бэкендом через /api-префикс (Caddy проксирует на FastAPI).
// JWT-токен хранится в localStorage и автоматически добавляется в заголовки.

const API_PREFIX = "/api";

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface AuditAction {
    id: number;
    actor: string;
    action: string;
    money: number;
}

// Ответ POST /audit/action: action + пересчитанные итоги.
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

export class ApiError extends Error {
    status: number;
    detail: string;

    constructor(status: number, detail: string) {
        super(detail);
        this.status = status;
        this.detail = detail;
    }
}

// Имя события, которое рассылается при потере авторизации (401 от бэкенда).
export const AUTH_UNAUTHORIZED_EVENT = "auth:unauthorized";

/** Сбрасывает сессию и оповещает приложение, что пользователь разлогинен.
 * App.tsx слушает событие и переключается на страницу входа. */
function handleUnauthorized() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT));
}

function authHeaders(): HeadersInit {
    const token = localStorage.getItem("access_token");
    return token
        ? {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
          }
        : { "Content-Type": "application/json" };
}

async function parseError(res: Response): Promise<never> {
    let detail = `Ошибка ${res.status}`;
    try {
        const body = await res.json();
        if (body?.detail) {
            detail =
                typeof body.detail === "string"
                    ? body.detail
                    : JSON.stringify(body.detail);
        }
    } catch {
        // не JSON — оставляем дефолт
    }

    // 401 — токен невалиден/просрочен: чистим сессию и кидаем пользователя
    // на страницу входа.
    if (res.status === 401) {
        handleUnauthorized();
    }

    throw new ApiError(res.status, detail);
}

export const api = {
    async login(username: string, password: string): Promise<TokenResponse> {
        const res = await fetch(`${API_PREFIX}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });
        if (!res.ok) await parseError(res);
        return res.json();
    },

    async getDay(date: string): Promise<AuditDay> {
        const res = await fetch(`${API_PREFIX}/audit/${date}`, {
            headers: authHeaders(),
        });
        if (!res.ok) await parseError(res);
        return res.json();
    },

    async setInitialCash(initialCash: number) {
        const res = await fetch(
            `${API_PREFIX}/audit/initial_cash?initial_cash=${encodeURIComponent(initialCash)}`,
            {
                method: "POST",
                headers: authHeaders(),
            },
        );
        if (!res.ok) await parseError(res);
        return res.json();
    },

    async createAction(payload: {
        actor: string;
        action: string;
        money: number;
        creation_date?: string;
    }): Promise<AuditActionCreateResponse> {
        const res = await fetch(`${API_PREFIX}/audit/action`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify(payload),
        });
        if (!res.ok) await parseError(res);
        return res.json();
    },

    async deleteAction(
        auditId: number,
        actionId: number,
    ): Promise<DeleteResponse> {
        const res = await fetch(
            `${API_PREFIX}/audit/action/${auditId}?action_id=${encodeURIComponent(actionId)}`,
            {
                method: "DELETE",
                headers: authHeaders(),
            },
        );
        if (!res.ok) await parseError(res);
        return res.json();
    },
};
