// Хранилище сессии: JWT в localStorage + имя пользователя в памяти.

const TOKEN_KEY = "access_token";
const USER_KEY = "username";

export const session = {
  save(token: string, username: string) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, username);
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  getUsername(): string | null {
    return localStorage.getItem(USER_KEY);
  },

  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem(TOKEN_KEY);
  },
};
