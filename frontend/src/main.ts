/**
 * UI orchestration — wires auth controls and API test buttons.
 */

import { initAuth, login, logout, getUserProfile, isAuthenticated } from "./auth";
import { apiGet } from "./api";

// ── DOM Elements ──
const btnLogin = document.getElementById("btn-login") as HTMLButtonElement;
const btnLogout = document.getElementById("btn-logout") as HTMLButtonElement;
const userInfo = document.getElementById("user-info") as HTMLDivElement;
const apiSection = document.getElementById("api-section") as HTMLElement;
const apiResponse = document.getElementById("api-response") as HTMLPreElement;
const btnPublic = document.getElementById("btn-public") as HTMLButtonElement;
const btnMe = document.getElementById("btn-me") as HTMLButtonElement;
const btnRbac = document.getElementById("btn-rbac") as HTMLButtonElement;

/**
 * Update the UI based on authentication state.
 */
function updateUI(): void {
  if (isAuthenticated()) {
    const profile = getUserProfile();
    btnLogin.style.display = "none";
    btnLogout.style.display = "inline-block";
    apiSection.style.display = "block";
    userInfo.style.display = "block";
    userInfo.innerHTML = profile
      ? `<strong>${profile.name}</strong> (${profile.email})<br/>
         Roles: <code>${profile.roles.join(", ") || "none"}</code>`
      : "Authenticated";
  } else {
    btnLogin.style.display = "inline-block";
    btnLogout.style.display = "none";
    apiSection.style.display = "none";
    userInfo.style.display = "none";
  }
}

/**
 * Call an API endpoint and display the result.
 */
async function callApi(path: string): Promise<void> {
  apiResponse.textContent = "Loading...";
  apiResponse.className = "";
  try {
    const data = await apiGet(path);
    apiResponse.textContent = JSON.stringify(data, null, 2);
    apiResponse.className = "success";
  } catch (error: unknown) {
    const axiosError = error as { response?: { status: number; data: unknown } };
    if (axiosError.response) {
      apiResponse.textContent = `HTTP ${axiosError.response.status}\n${JSON.stringify(axiosError.response.data, null, 2)}`;
      apiResponse.className = axiosError.response.status === 403 ? "forbidden" : "error";
    } else {
      apiResponse.textContent = `Network error: ${String(error)}`;
      apiResponse.className = "error";
    }
  }
}

// ── Event Listeners ──
btnLogin.addEventListener("click", () => login());
btnLogout.addEventListener("click", () => logout());
btnPublic.addEventListener("click", () => callApi("/api/public"));
btnMe.addEventListener("click", () => callApi("/api/secure/me"));
btnRbac.addEventListener("click", () => callApi("/api/secure/rbac-check"));

// ── Initialize ──
initAuth().then(() => updateUI());
