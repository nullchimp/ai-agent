export interface LoginResponse {
    user_id: string;
    user_token: string;
    email?: string;
    name?: string;
    message: string;
}

export interface UserSession {
    session_id: string;
    title: string;
    last_activity: string;
    conversation_count: number;
    is_active: boolean;
}

export class AuthManager {
    private apiBaseUrl = 'http://localhost:5555/api';
    private userTokenKey = 'user_token';
    private userIdKey = 'user_id';

    public async login(userToken: string): Promise<LoginResponse> {
        const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_token: userToken })
        });

        if (!response.ok) {
            throw new Error(`Login failed: ${response.status}`);
        }

        const data: LoginResponse = await response.json();
        this.storeUserToken(data.user_token);
        this.storeUserId(data.user_id);
        return data;
    }

    public async getUserSessions(): Promise<UserSession[]> {
        const userToken = this.getUserToken();
        if (!userToken) {
            throw new Error('No user token found');
        }

        const response = await fetch(`${this.apiBaseUrl}/auth/sessions`, {
            method: 'GET',
            headers: {
                'X-User-Token': userToken
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to load sessions: ${response.status}`);
        }

        const data = await response.json();
        return data.sessions;
    }

    public storeUserToken(token: string): void {
        localStorage.setItem(this.userTokenKey, token);
    }

    public getUserToken(): string | null {
        return localStorage.getItem(this.userTokenKey);
    }

    public storeUserId(userId: string): void {
        localStorage.setItem(this.userIdKey, userId);
    }

    public getUserId(): string | null {
        return localStorage.getItem(this.userIdKey);
    }

    public clearAuth(): void {
        localStorage.removeItem(this.userTokenKey);
        localStorage.removeItem(this.userIdKey);
    }

    public isAuthenticated(): boolean {
        return this.getUserToken() !== null;
    }

    public logout(): void {
        this.clearAuth();
        window.location.reload();
    }
}
