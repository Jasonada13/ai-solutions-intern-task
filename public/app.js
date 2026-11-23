const $ = (id) => document.getElementById(id);
let requests = [];
let selectedRequest = null;
let busy = false;

async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "The request failed. Please try again.");
  return body;
}

function message(text, error = false) {
  $("message").textContent = text;
  $("message").dataset.error = String(error);
}

function setBusy(value) {
  busy = value;
  $("review-fields").disabled = value;
  document.querySelectorAll(".request-button").forEach((button) => { button.disabled = value; });
}

function renderList() {
  $("request-list").replaceChildren();
  for (const request of requests) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "request-button";
    button.disabled = busy;
    button.setAttribute("aria-current", String(request.id === selectedRequest?.id));
    const title = document.createElement("span");
    title.textContent = request.title;
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = `${request.id} · ${request.review.status}`;
    button.append(title, meta);
    button.addEventListener("click", () => selectRequest(request.id));
    item.append(button);
    $("request-list").append(item);
  }
}

async function refreshList() {
  ({ requests } = await api("/api/requests"));
  renderList();
}

function renderDetail(request) {
  selectedRequest = request;
  $("detail").hidden = false;
  $("request-id").textContent = request.id;
  $("request-title").textContent = request.title;
  $("description").textContent = request.description;
  $("review-status").textContent = request.review.status === "reviewed"
    ? `Reviewed · ${request.review.priority}` : "Unreviewed";
  $("priority").value = request.review.status === "reviewed" ? request.review.priority : "";
  $("note").value = request.review.status === "reviewed" ? request.review.note : "";
  $("suggestion-panel").hidden = true;
  $("suggestion-output").textContent = "";
}

async function selectRequest(id) {
  setBusy(true);
  try {
    const { request } = await api(`/api/requests/${id}`);
    renderDetail(request);
    renderList();
    message("Review this request manually or get a suggestion.");
  } catch (error) {
    message(error.message, true);
  } finally {
    setBusy(false);
  }
}

$("suggest").addEventListener("click", async () => {
  if (!selectedRequest || busy) return;
  setBusy(true);
  message("Getting a suggestion…");
  try {
    const { suggestion } = await api(`/api/requests/${selectedRequest.id}/suggestion`, { method: "POST" });
    $("suggestion-output").textContent = JSON.stringify(suggestion, null, 2);
    $("suggestion-panel").hidden = false;
    // TODO: Prefill the draft priority and note from a validated suggestion. Do not save it.
    message("Raw provider response received. The draft is unchanged in this starter.");
  } catch (error) {
    message(error.message, true);
  } finally {
    setBusy(false);
  }
});

$("review-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedRequest || busy) return;
  const input = { priority: $("priority").value, note: $("note").value };
  setBusy(true);
  message("Saving your review…");
  try {
    const { request } = await api(`/api/requests/${selectedRequest.id}/review`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input),
    });
    // TODO: Show the saved request in the detail view and refresh the list's review status.
    void request;
    message("Save response received.");
  } catch (error) {
    message(error.message, true);
  } finally {
    setBusy(false);
  }
});

async function start() {
  try {
    await refreshList();
    if (requests[0]) await selectRequest(requests[0].id);
  } catch (error) {
    message(error.message, true);
  }
}
start();
