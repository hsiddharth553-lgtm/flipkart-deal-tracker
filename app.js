let idToken = null;

const API_BASE = "https://flipkart-deal-tracker.onrender.com";

// Called by Google after login
function handleLogin(response) {
  console.log("Google login response:", response);

  idToken = response.credential;

  fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken })
  })
    .then(res => res.json())
    .then(data => {
      console.log("Login API response:", data);
      const ui = document.getElementById("userInfo");
      if (ui && data.email) {
        ui.innerText = "Logged in as: " + data.email;
      }
      loadFavorites();
    })
    .catch(err => console.error("Login error:", err));
}

// Add favorite
function addFavorite() {
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  const input = document.getElementById("product");
  const url = input.value.trim();

  if (!url) {
    alert("Paste a Flipkart product link!");
    return;
  }

  if (!url.includes("flipkart.com")) {
    alert("Please paste a valid Flipkart product link.");
    return;
  }

  fetch(`${API_BASE}/favorite?token=${encodeURIComponent(idToken)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url })
  })
    .then(res => {
      if (!res.ok) throw new Error("Add failed");
      return res.json();
    })
    .then(() => {
      input.value = "";
      loadFavorites();
    })
    .catch(err => console.error("Add favorite error:", err));
}

// Load favorites
function loadFavorites() {
  if (!idToken) return;

  fetch(`${API_BASE}/favorites?token=${encodeURIComponent(idToken)}`)
    .then(res => res.json())
    .then(data => {
      console.log("Favorites:", data);
      renderFavorites(data);
    })
    .catch(err => console.error("Load favorites error:", err));
}

// Remove favorite
function removeFavorite(url) {
  if (!idToken) return;

  fetch(`${API_BASE}/favorite?token=${encodeURIComponent(idToken)}&url=${encodeURIComponent(url)}`, {
    method: "DELETE"
  })
    .then(res => {
      if (!res.ok) throw new Error("Delete failed");
      return res.json();
    })
    .then(() => loadFavorites())
    .catch(err => console.error("Delete error:", err));
}

// Render favorites
function renderFavorites(list) {
  const grid = document.getElementById("favGrid");
  grid.innerHTML = "";

  if (!list || list.length === 0) {
    grid.innerHTML = "<p>No products added yet.</p>";
    return;
  }

  list.forEach(item => {
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
      <img src="${item.image || ""}" />
      <div class="title">${item.title}</div>
      <div class="price">${item.price}</div>
      <a href="${item.url}" target="_blank">View on Flipkart</a>
      <button onclick="removeFavorite(${JSON.stringify(item.url)})">Remove</button>
    `;

    grid.appendChild(card);
  });
}
