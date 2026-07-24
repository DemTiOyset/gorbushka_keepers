import { useEffect, useState } from "react";
import { AUTH_UNAUTHORIZED_EVENT } from "./api";
import { session } from "./auth";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";

export default function App() {
    const [authed, setAuthed] = useState<boolean>(() =>
        session.isAuthenticated(),
    );

    // Слушаем событие от api.ts при получении 401 от бэкенда — токен
    // невалиден или просрочен, чистим сессию и отправляем на логин.
    useEffect(() => {
        function onUnauthorized() {
            session.clear();
            setAuthed(false);
        }
        window.addEventListener(AUTH_UNAUTHORIZED_EVENT, onUnauthorized);
        return () =>
            window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, onUnauthorized);
    }, []);

    // Реактивная проверка окна localStorage в другой вкладке (например, ручной
    // выход в соседней вкладке). Необязательно, но дёшево и приятно.
    useEffect(() => {
        function onStorage(e: StorageEvent) {
            if (e.key === "access_token" && !e.newValue) {
                setAuthed(false);
            }
        }
        window.addEventListener("storage", onStorage);
        return () => window.removeEventListener("storage", onStorage);
    }, []);

    function handleLoginSuccess() {
        setAuthed(true);
    }

    function handleLogout() {
        session.clear();
        setAuthed(false);
    }

    // Гард: неавторизованный пользователь видит только страницу входа.
    if (!authed) {
        return <Login onSuccess={handleLoginSuccess} />;
    }

    return <Dashboard onLogout={handleLogout} />;
}
