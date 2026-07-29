import { useState } from "react";
import { api, ApiError } from "../api";
import { session } from "../auth";

interface Props {
    onSuccess: () => void;
}

export default function Login({ onSuccess }: Props) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const { access_token } = await api.login(username, password);
            session.save(access_token, username);
            onSuccess();
        } catch (err) {
            if (err instanceof ApiError) setError(err.detail);
            else setError("Не удалось подключиться к серверу");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="auth-wrap">
            <form className="auth-card" onSubmit={handleSubmit}>
                <div className="auth-brand">Дозор</div>
                <h1 className="auth-title">Вход в личный кабинет</h1>
                <p className="auth-subtitle">
                    Учёт кассы · введите свои данные для входа
                </p>

                <label className="field-label">Имя пользователя</label>
                <input
                    className="field-input"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="например, osman"
                    autoFocus
                    required
                />

                <label className="field-label">Пароль</label>
                <input
                    className="field-input"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                />

                {error && <div className="field-error">{error}</div>}

                <button
                    className="btn-primary"
                    type="submit"
                    disabled={loading}
                >
                    {loading ? "Входим..." : "Войти"}
                </button>
            </form>
        </div>
    );
}
