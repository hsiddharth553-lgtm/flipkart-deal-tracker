const API = "http://127.0.0.1:8000"; // backend
let googleToken = null;

function handleLogin(response) {
  googleToken = response.credential;

  fetch(API + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: googleToken })
  })
    .then(r => r.json())
    .then(data => {
      document.getElementById("userInfo").innerText = "Logged in as: " + data.email;
      loadFavorites();
    })
    .catch(err => {
      console.error(err);
      alert("Login failed. Check backend.");
    });
}

function addFavorite() {
  const product = document.getElementById("product").value;

  if (!googleToken) {
    alert("Please login first!");
    return;
  }

  fetch(API + "/favorite?token=" + googleToken, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product: product })
  })
    .then(() => {
      document.getElementById("product").value = "";
      loadFavorites();
    });
}

function loadFavorites() {
  if (!googleToken) return;

  fetch(API + "/favorites?token=" + googleToken)
    .then(r => r.json())
    .then(list => {
      const ul = document.getElementById("favList");
      ul.innerHTML = "";
      list.forEach(p => {
        const li = document.createElement("li");
        li.innerText = p;
        ul.appendChild(li);
      });
    });
}
