const API_BASE = "https://flipkart-deal-tracker.onrender.com";

let idToken = null;
let userEmail = null;

// Called by Google when user logs in
function handleLogin(response) {
  idToken = response.credential;

  // Send token to backend to verify
  fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken })
  })
    .then(res => res.json())
    .then(data => {
      userEmail = data.email;
      document.getElementById("userInfo").innerText = "Logged in as: " + userEmail;
      loadFavorites();
    })
    .catch(err => {
      console.error("Login error:", err);
      alert("Login failed");
    });
}

// Add favorite
function addFavorite() {
  const product = document.getElementById("product").value.trim();
  if (!product) {
    alert("Enter product name or URL");
    return;
  }
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  fetch(`${API_BASE}/favorite?token=${idToken}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product: product })
  })
    .then(res => res.json())
    .then(() => {
      document.getElementById("product").value = "";
      loadFavorites();
    })
    .catch(err => console.error("Add favorite error:", err));
}

// Load favorites
function loadFavorites() {
  if (!idToken) return;

  fetch(`${API_BASE}/favorites?token=${idToken}`)
    .then(res => res.json())
    .then(items => {
      const grid = document.getElementById("favGrid");
      grid.innerHTML = "";

      items.forEach(item => {
        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
          <div class="title">${item}</div>
          <div class="actions">
            <button class="remove" onclick="removeFavorite('${item.replace(/'/g, "\\'")}')">Remove</button>
          </div>
        `;

        grid.appendChild(card);
      });
    })
    .catch(err => console.error("Load favorites error:", err));
}

// Remove favorite ✅
function removeFavorite(product) {
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  fetch(`${API_BASE}/favorite?token=${idToken}&product=${encodeURIComponent(product)}`, {
    method: "DELETE"
  })
    .then(res => res.json())
    .then(() => {
      loadFavorites(); // refresh list
    })
    .catch(err => console.error("Remove favorite error:", err));
}
