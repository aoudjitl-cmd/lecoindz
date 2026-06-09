const API_URL = "https://rayahdz-production.up.railway.app";

const Auth = {
  getToken: () => localStorage.getItem("cg_token"),
  getUser: () => JSON.parse(localStorage.getItem("cg_user") || "null"),
  setSession: (token, user) => {
    localStorage.setItem("cg_token", token);
    localStorage.setItem("cg_user", JSON.stringify(user));
  },
  logout: () => {
    localStorage.removeItem("cg_token");
    localStorage.removeItem("cg_user");
    window.location.href = "login.html";
  },
  isLoggedIn: () => !!localStorage.getItem("cg_token")
};

async function apiCall(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = Auth.getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(`${API_URL}${endpoint}`, options);

  // Token expiré ou invalide → déconnexion propre
  if (response.status === 401) {
    Auth.logout();
    return;
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Une erreur est survenue");
  }
  return data;
}

const AuthAPI = {
  register: (data) => apiCall("/auth/register", "POST", data),
  login: (data) => apiCall("/auth/login", "POST", data),
};

const TripsAPI = {
  search: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiCall(`/trips/?${query}`);
  },
  getMine: () => apiCall("/trips/mes-trajets"),
  create: (data) => apiCall("/trips/", "POST", data),
  get: (id) => apiCall(`/trips/${id}`),
  delete: (id) => apiCall(`/trips/${id}`, "DELETE"),
};

const ParcelsAPI = {
  search: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiCall(`/parcels/?${query}`);
  },
  create: (data) => apiCall("/parcels/", "POST", data),
  get: (id) => apiCall(`/parcels/${id}`),
  delete: (id) => apiCall(`/parcels/${id}`, "DELETE"),
};

const BookingsAPI = {
  create: (data) => apiCall("/bookings/", "POST", data),
  getMine: () => apiCall("/bookings/mes-reservations"),
  get: (id) => apiCall(`/bookings/${id}`),
  updateStatus: (id, status) => apiCall(`/bookings/${id}/statut`, "PATCH", { status }),
  markPaid: (id) => apiCall(`/bookings/${id}/paid`, "PATCH"),
  delete: (id) => apiCall(`/bookings/${id}`, "DELETE"),
};

const MessagesAPI = {
  send: (bookingId, content) => apiCall(`/messages/${bookingId}`, "POST", { content }),
  getConversation: (bookingId) => apiCall(`/messages/${bookingId}`),
  getUnread: () => apiCall("/messages/non-lus/count"),
};

const DirectAPI = {
  send: (userId, content) => apiCall(`/direct/avec/${userId}`, "POST", { content }),
  getMessages: (userId) => apiCall(`/direct/avec/${userId}`),
  getConversations: () => apiCall("/direct/mes-conversations"),
};

const PaymentsAPI = {
  createIntent: (bookingId) => apiCall("/payments/create-payment-intent", "POST", { booking_id: bookingId }),
  getStatus: (bookingId) => apiCall(`/payments/status/${bookingId}`),
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
  setTimeout(() => container.innerHTML = "", 4000);
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}

function getStatusBadge(status) {
  const map = {
    "PENDING":    ["badge-warning", "En attente"],
    "MATCHED":    ["badge-info",    "Trouve"],
    "ACCEPTED":   ["badge-info",    "Accepte"],
    "IN_TRANSIT": ["badge-warning", "En transit"],
    "DELIVERED":  ["badge-success", "Livre"],
    "CANCELLED":  ["badge-danger",  "Annule"],
    "ACTIVE":     ["badge-success", "Actif"],
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
    // Si l'appel échoue (token expiré, réseau...) → login
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
      <a href="dashboard.html" class="nav-link"><span>👤</span> <span>${user.first_name}</span></a>
      <button class="btn btn-outline btn-sm" onclick="Auth.logout()">Deconnexion</button>
    `;
  } else {
    navAuth.innerHTML = `
      <a href="login.html" class="btn btn-outline btn-sm">Connexion</a>
      <a href="login.html?mode=register" class="btn btn-primary btn-sm">S'inscrire</a>
    `;
  }

  // Badge messages non lus
  if (user) {
    try {
      const data = await DirectAPI.getConversations();
      const unread = data.conversations.reduce((total, conv) => total + (conv.unread || 0), 0);
      const msgLink = document.getElementById("nav-messages");
      if (msgLink && unread > 0) {
        msgLink.innerHTML = `Messages <span style="background:var(--danger); color:white; border-radius:50%; padding:1px 6px; font-size:0.75rem; margin-left:4px;">${unread}</span>`;
      }
    } catch(e) {}
  }
}