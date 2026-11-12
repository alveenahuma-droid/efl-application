// Login, registration and logout. Loaded on every page by base.html.
async function sendJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  return { ok: response.ok, data: data };
}

async function submitAuth(url, body, errorId) {
  showMessage(errorId, "");
  try {
    const reply = await sendJson(url, body);
    if (!reply.ok) {
      showMessage(errorId, reply.data.error);
      return;
    }
    window.location.href = "/converter";
  } catch (problem) {
    showMessage(errorId, "Could not reach the server. Try again shortly.");
  }
}

const loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", function (event) {
    event.preventDefault();
    submitAuth("/api/login", {
      email: document.getElementById("email").value,
      password: document.getElementById("password").value,
    }, "login-error");
  });
}

const registerForm = document.getElementById("register-form");
if (registerForm) {
  registerForm.addEventListener("submit", function (event) {
    event.preventDefault();
    submitAuth("/api/register", {
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      password: document.getElementById("password").value,
    }, "register-error");
  });
}

const logoutLink = document.getElementById("logout-link");
if (logoutLink) {
  logoutLink.addEventListener("click", async function (event) {
    event.preventDefault();
    await sendJson("/api/logout", {});
    window.location.href = "/login";
  });
}
