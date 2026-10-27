import { useState } from "react";
import { api, ApiError } from "../api";
import { session } from "../auth";

interface Props {
    onSuccess: () => void;
}

export default function Login({ onSuccess }: Props) {
    const [username, setUsername] = useState("test_user");
    const [password, setPassword] = useState("1234");
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
                    placeholder="например, test_user или osman"
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

                <div className="demo-credentials">
                    <div><strong>Тестовый аккаунт:</strong> <code>test_user</code> / <code>1234</code></div>
                    <div>Также доступен: <code>osman</code>, <code>timur</code></div>
                    <div className="demo-credentials-actions">
                        <button
                            type="button"
                            className="link-button"
                            onClick={() => {
                                setUsername("test_user");
                                setPassword("1234");
                            }}
                        >
                            Заполнить demo данные
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}
