const API_URL = "https://lecoindz-production.up.railway.app";

const Auth = {
  getToken: () => localStorage.getItem("lcd_token"),
  getUser: () => JSON.parse(localStorage.getItem("lcd_user") || "null"),
  setSession: (token, user) => {
    localStorage.setItem("lcd_token", token);
    localStorage.setItem("lcd_user", JSON.stringify(user));
  },
  logout: () => {
    localStorage.removeItem("lcd_token");
    localStorage.removeItem("lcd_user");
    window.location.href = "login.html";
  },
  isLoggedIn: () => !!localStorage.getItem("lcd_token")
};

async function apiCall(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = Auth.getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(`${API_URL}${endpoint}`, options);
  if (response.status === 401 && !window.location.pathname.includes("login")) {
    Auth.logout();
    return;
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Une erreur est survenue");
  return data;
}

const AuthAPI = {
  register: (data) => apiCall("/auth/register", "POST", data),
  login: (data) => apiCall("/auth/login", "POST", data),
};

const ProductsAPI = {
  search: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiCall(`/products/?${query}`);
  },
  create: (data) => apiCall("/products/", "POST", data),
  get: (id) => apiCall(`/products/${id}`),
  scrape: (url) => apiCall("/products/scrape", "POST", { url }),
};

const ShoppersAPI = {
  search: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiCall(`/shoppers/?${query}`);
  },
  create: (data) => apiCall("/shoppers/", "POST", data),
  getMine: () => apiCall("/shoppers/mes-disponibilites"),
  delete: (id) => apiCall(`/shoppers/${id}`, "DELETE"),
};

const OrdersAPI = {
  create: (data) => apiCall("/orders/", "POST", data),
  getMine: () => apiCall("/orders/mes-commandes"),
  get: (id) => apiCall(`/orders/${id}`),
  updateStatus: (id, status) => apiCall(`/orders/${id}/statut`, "PATCH", { status }),
};

const DirectAPI = {
  send: (userId, content) => apiCall(`/direct/avec/${userId}`, "POST", { content }),
  getMessages: (userId) => apiCall(`/direct/avec/${userId}`),
  getConversations: () => apiCall("/direct/mes-conversations"),
};

const ReviewsAPI = {
  getForUser: (userId) => apiCall(`/reviews/user/${userId}`),
  create: (data) => apiCall("/reviews/", "POST", data),
};

const SubscriptionsAPI = {
  createCheckout: () => apiCall("/subscriptions/create-checkout", "POST"),
  getStatus: () => apiCall("/subscriptions/status"),
  verify: (sessionId) => apiCall(`/subscriptions/verify/${sessionId}`, "POST"),
  cancel: () => apiCall("/subscriptions/cancel", "DELETE"),
};

function showAlert(message, type = "error", containerId = "alert-container") {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
  const delay = type === "error" ? 8000 : 4000;
  setTimeout(() => { if (container) container.innerHTML = ""; }, delay);
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

function formatPrice(price) {
  if (!price) return "—";
  return parseFloat(price).toFixed(2) + "€";
}

function getStatusBadge(status) {
  const map = {
    "PENDING":     ["badge-warning", "En attente"],
    "ACCEPTED":    ["badge-info",    "Accepte"],
    "IN_PROGRESS": ["badge-warning", "En cours"],
    "DELIVERED":   ["badge-success", "Livre"],
    "CANCELLED":   ["badge-danger",  "Annule"],
    "ACTIVE":      ["badge-success", "Actif"],
  };
  const [cls, label] = map[status] || ["badge-info", status];
  return `<span class="badge ${cls}">${label}</span>`;
}

function requireAuth() {
  if (!Auth.isLoggedIn()) window.location.href = "login.html";
}

async function requireSubscription() {
  if (!Auth.isLoggedIn()) {
    window.location.href = "login.html";
    return;
  }
  try {
    const data = await SubscriptionsAPI.getStatus();
    const status = data.subscription_status;
    const trialEnd = data.trial_end ? new Date(data.trial_end) : null;
    const now = new Date();
    if (status === "ACTIVE") return;
    if (status === "TRIAL" && trialEnd && trialEnd > now) return;
    window.location.href = "subscription.html";
  } catch(e) {
    console.log("Erreur verification abonnement:", e.message);
    window.location.href = "login.html";
  }
}

async function updateNavbar() {
  const user = Auth.getUser();
  const navAuth = document.getElementById("nav-auth");
  if (!navAuth) return;
  if (user) {
    navAuth.innerHTML = `
      <a href="profil.html" class="nav-link"><span>👤</span> <span>${user.first_name}</span></a>
      <button class="btn btn-outline btn-sm" onclick="Auth.logout()">Deconnexion</button>
    `;
  } else {
    navAuth.innerHTML = `
      <a href="login.html" class="btn btn-outline btn-sm">Connexion</a>
      <a href="login.html?mode=register" class="btn btn-primary btn-sm">S'inscrire</a>
    `;
  }
  if (user) {
    try {
      const data = await DirectAPI.getConversations();
      const unread = data.conversations.reduce((t, c) => t + (c.unread || 0), 0);
      const msgLink = document.getElementById("nav-messages");
      if (msgLink && unread > 0) {
        msgLink.innerHTML += ` <span style="background:#e63946; color:white; border-radius:50%; padding:1px 6px; font-size:0.75rem;">${unread}</span>`;
      }
    } catch(e) {}
  }
}