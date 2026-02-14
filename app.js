let idToken = null;

const API_BASE = "https://flipkart-deal-tracker.onrender.com";

// Called by Google after login
function handleLogin(response) {
  console.log("Google login response:", response);

  idToken = response.credential;

  fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      id_token: idToken
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log("Login API response:", data);

    // ✅ FIX: Update UI properly
    const ui = document.getElementById("userInfo");
    if (ui) {
      if (data.email) {
        ui.innerText = "Logged in as: " + data.email;
      } else {
        ui.innerText = "Logged in";
      }
    }

    loadFavorites();
  })
  .catch(err => {
    console.error("Login error:", err);
  });
}

// Add favorite
function addFavorite() {
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  const input = document.getElementById("product");
  const product = input.value.trim();
  if (!product) return;

  fetch(`${API_BASE}/favorite?token=${idToken}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ product })
  })
  .then(res => res.json())
  .then(() => {
    input.value = "";
    loadFavorites();
  })
  .catch(err => console.error("Add favorite error:", err));
}

// Load favorites
function loadFavorites() {
  if (!idToken) return;

  fetch(`${API_BASE}/favorites?token=${idToken}`)
    .then(res => res.json())
    .then(data => {
      console.log("Favorites:", data);
      renderFavorites(data);
    })
    .catch(err => console.error("Load favorites error:", err));
}

// Render favorites
function renderFavorites(list) {
  const grid = document.getElementById("favGrid");
  if (!grid) return;

  grid.innerHTML = "";

  list.forEach(item => {
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
      <div class="title">${item}</div>
      <div class="actions">
        <button class="remove" onclick="alert('Remove coming soon 😄')">Remove</button>
      </div>
    `;

    grid.appendChild(card);
  });
}
