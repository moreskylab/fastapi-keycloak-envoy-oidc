/**
 * Keycloak Authentication Module (OWASP A07: Auth Failures).
 *
 * Security controls:
 * - PKCE S256 (Proof Key for Code Exchange) prevents authorization code interception
 * - Tokens stored in memory only — never localStorage or cookies
 * - Short-lived access tokens (5 min), silent token refresh
 * - Token expiry checked before every API call
 */

import Keycloak from "keycloak-js";

// Keycloak configuration from environment or defaults
const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "oidc-demo",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "frontend-spa",
};

// Keycloak instance — tokens held in memory only (OWASP A07)
const keycloak = new Keycloak(keycloakConfig);

/**
 * Initialize Keycloak with silent check-sso and PKCE S256.
 * Returns true if the user is already authenticated.
 */
export async function initAuth(): Promise<boolean> {
  try {
    const authenticated = await keycloak.init({
      onLoad: "check-sso",
      pkceMethod: "S256", // OWASP A02: PKCE prevents code interception
      checkLoginIframe: false, // Avoid third-party cookie issues
      silentCheckSsoRedirectUri:
        window.location.origin + "/silent-check-sso.html",
    });

    if (authenticated) {
      // Set up automatic token refresh
      setupTokenRefresh();
    }

    return authenticated;
  } catch (error) {
    console.error("Keycloak init failed:", error);
    return false;
  }
}

/**
 * Redirect to Keycloak login page.
 */
export function login(): void {
  keycloak.login();
}

/**
 * Logout and redirect to home.
 */
export function logout(): void {
  keycloak.logout({ redirectUri: window.location.origin });
}

/**
 * Get the current access token, refreshing if needed.
 * Returns null if not authenticated.
 */
export async function getToken(): Promise<string | null> {
  if (!keycloak.authenticated) {
    return null;
  }

  try {
    // Refresh token if it expires within 30 seconds
    await keycloak.updateToken(30);
    return keycloak.token ?? null;
  } catch {
    console.warn("Token refresh failed — redirecting to login");
    keycloak.login();
    return null;
  }
}

/**
 * Get the authenticated user's profile from the token.
 */
export function getUserProfile(): {
  name: string;
  email: string;
  roles: string[];
} | null {
  if (!keycloak.authenticated || !keycloak.tokenParsed) {
    return null;
  }

  const parsed = keycloak.tokenParsed as Record<string, unknown>;
  const realmAccess = parsed.realm_access as
    | { roles?: string[] }
    | undefined;

  return {
    name:
      (parsed.name as string) ||
      (parsed.preferred_username as string) ||
      "Unknown",
    email: (parsed.email as string) || "",
    roles: realmAccess?.roles || [],
  };
}

/**
 * Check if user is authenticated.
 */
export function isAuthenticated(): boolean {
  return keycloak.authenticated ?? false;
}

/**
 * Set up automatic silent token refresh.
 * Refreshes the access token 60 seconds before expiry.
 */
function setupTokenRefresh(): void {
  keycloak.onTokenExpired = () => {
    keycloak
      .updateToken(70)
      .then((refreshed: boolean) => {
        if (refreshed) {
          console.debug("Token refreshed silently");
        }
      })
      .catch(() => {
        console.warn("Token refresh failed — session expired");
        keycloak.login();
      });
  };
}
