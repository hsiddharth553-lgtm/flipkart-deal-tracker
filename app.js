let idToken = null;

const API_BASE = "https://flipkart-deal-tracker.onrender.com";

// Called by Google after login
function handleLogin(response) {
  idToken = response.credential;

  fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken })
  })
    .then(res => res.json())
    .then(data => {
      const ui = document.getElementById("userInfo");
      if (ui && data.email) {
        ui.innerText = "Logged in as: " + data.email;
      }
      loadFavorites();
    })
    .catch(err => console.error("Login error:", err));
}

// Add favorite (expects Flipkart URL)
function addFavorite() {
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  const input = document.getElementById("product");
  const url = input.value.trim();
  if (!url) return;

  fetch(`${API_BASE}/favorite?token=${idToken}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
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
    .then(data => renderFavorites(data))
    .catch(err => console.error("Load favorites error:", err));
}

// Remove favorite
function removeFavorite(url) {
  if (!idToken) return;

  fetch(`${API_BASE}/favorite?token=${idToken}&url=${encodeURIComponent(url)}`, {
    method: "DELETE"
  })
    .then(() => loadFavorites())
    .catch(err => console.error("Delete error:", err));
}

// Render favorites as cards
function renderFavorites(list) {
  const grid = document.getElementById("favGrid");
  if (!grid) return;

  grid.innerHTML = "";

  list.forEach(item => {
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
      <img src="${item.image}" alt="" style="max-width:150px;">
      <h3>${item.title}</h3>
      <p><b>Price:</b> ${item.price}</p>
      <p style="text-decoration: line-through; color: gray;">${item.mrp || ""}</p>
      <div class="actions">
        <a href="${item.url}" target="_blank">Open on Flipkart</a>
        <button onclick="removeFavorite('${item.url.replace(/'/g, "\\'")}')">Remove</button>
      </div>
    `;

    grid.appendChild(card);
  });
}
