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

// Add favorite (expects a Flipkart URL)
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

  fetch(`${API_BASE}/favorite?token=${idToken}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  })
    .then(res => res.json())
    .then(data => {
      console.log("Added:", data);
      input.value = "";
      loadFavorites();
    })
    .catch(err => {
      console.error("Add error:", err);
      alert("Failed to add product");
    });
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

// Render favorites as product cards
function renderFavorites(list) {
  const grid = document.getElementById("favGrid");
  if (!grid) return;

  grid.innerHTML = "";

  if (list.length === 0) {
    grid.innerHTML = "<p>No products added yet.</p>";
    return;
  }

  list.forEach(item => {
    const card = document.createElement("div");
    card.className = "card";

    const oldPriceHtml = item.old_price
      ? `<span class="old-price">${item.old_price}</span>`
      : "";

    card.innerHTML = `
      <div class="product-card">
        <div class="image-wrap">
          ${item.image ? `<img src="${item.image}" alt="Product">` : ""}
        </div>
        <div class="info">
          <div class="title">${item.title}</div>
          <div class="prices">
            <span class="price">${item.price}</span>
            ${oldPriceHtml}
          </div>
          <div class="actions">
            <a href="${item.url}" target="_blank" class="open-btn">Open</a>
            <button class="remove-btn">Remove</button>
          </div>
        </div>
      </div>
    `;

    // Hook remove button
    const removeBtn = card.querySelector(".remove-btn");
    removeBtn.onclick = () => removeFavorite(item.url);

    grid.appendChild(card);
  });
}

// Remove favorite
function removeFavorite(url) {
  if (!idToken) {
    alert("Please sign in first!");
    return;
  }

  fetch(`${API_BASE}/favorite?token=${idToken}&url=${encodeURIComponent(url)}`, {
    method: "DELETE"
  })
    .then(res => res.json())
    .then(data => {
      console.log("Deleted:", data);
      loadFavorites(); // refresh list
    })
    .catch(err => console.error("Remove error:", err));
}
