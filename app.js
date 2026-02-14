const API_BASE = "https://flipkart-deal-tracker.onrender.com";

let idToken = null;
let userEmail = null;

// Called by Google Sign-In
function handleLogin(response) {
  console.log("Google login response:", response);

  idToken = response.credential;

  // Verify token with backend
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
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  const input = document.getElementById("product");
  const product = input.value.trim();

  if (!product) {
    alert("Enter a product name or link!");
    return;
  }

  fetch(`${API_BASE}/favorite?token=${idToken}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product })
  })
    .then(res => res.json())
    .then(data => {
      console.log("Added:", data);
      input.value = "";
      loadFavorites();
    })
    .catch(err => console.error("Add error:", err));
}

// Load favorites
function loadFavorites() {
  if (!idToken) return;

  fetch(`${API_BASE}/favorites?token=${idToken}`)
    .then(res => res.json())
    .then(list => {
      console.log("Favorites:", list);
      renderFavorites(list);
    })
    .catch(err => console.error("Load error:", err));
}

// Render favorites with Remove button
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
        <button class="remove">Remove</button>
      </div>
    `;

    const btn = card.querySelector(".remove");
    btn.onclick = () => removeFavorite(item);

    grid.appendChild(card);
  });
}

// Remove favorite
function removeFavorite(product) {
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  fetch(`${API_BASE}/favorite?token=${idToken}&product=${encodeURIComponent(product)}`, {
    method: "DELETE"
  })
    .then(res => res.json())
    .then(data => {
      console.log("Deleted:", data);
      loadFavorites(); // refresh list
    })
    .catch(err => console.error("Remove error:", err));
}
