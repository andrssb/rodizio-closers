// Frontend da roleta. Conversa com a API (app/main.py) e anima o giro.

const SEGMENTS = 12;
const SEG_DEG = 360 / SEGMENTS;
const SPIN_MS = 4500; // precisa bater com a transição do CSS (.wheel)

const PALETTE = [
  "#2ecc71", "#27ae60", "#3498db", "#2980b9",
  "#9b59b6", "#8e44ad", "#e67e22", "#d35400",
  "#1abc9c", "#16a085", "#f39c12", "#c0392b",
];

const sourceBadge = document.getElementById("source-badge");
const wheel = document.getElementById("wheel");
const spinBtn = document.getElementById("spin-btn");
const closerList = document.getElementById("closer-list");
const resultCard = document.getElementById("result-card");
const skipList = document.getElementById("skip-list");
const winnerEl = document.getElementById("winner");
const queueEl = document.getElementById("queue");

let closers = [];
let currentRotation = 0;
let spinning = false;

// ---------------------------------------------------------------------------
// Carregar closers e desenhar tudo
// ---------------------------------------------------------------------------
async function loadClosers() {
  const res = await fetch("/api/closers");
  closers = await res.json();
  drawWheel();
  drawCloserList();
}

function drawWheel() {
  // fundo da roleta (gatilhos coloridos por segmento; inativo fica cinza)
  const stops = closers.map((c, i) => {
    const color = c.active ? PALETTE[i % PALETTE.length] : "#2a2e3a";
    return `${color} ${i * SEG_DEG}deg ${(i + 1) * SEG_DEG}deg`;
  });
  wheel.style.background = `conic-gradient(${stops.join(", ")})`;

  // nomes posicionados no meio de cada fatia
  wheel.querySelectorAll(".label").forEach((el) => el.remove());
  const radius = wheel.clientWidth / 2 - 58;
  closers.forEach((c, i) => {
    const angle = i * SEG_DEG + SEG_DEG / 2; // centro da fatia, do topo, horário
    const label = document.createElement("div");
    label.className = "label" + (c.active ? "" : " off");
    label.style.transform = `rotate(${angle}deg) translateY(-${radius}px)`;
    const span = document.createElement("span");
    span.textContent = c.name;
    // mantém o texto "em pé" contra a rotação da fatia
    span.style.transform = `translate(-50%, -50%) rotate(${-angle}deg)`;
    label.appendChild(span);
    wheel.appendChild(label);
  });
}

function drawCloserList() {
  closerList.innerHTML = "";
  closers.forEach((c) => {
    const li = document.createElement("li");

    const name = document.createElement("span");
    name.className = "name" + (c.active ? "" : " off");
    name.textContent = c.name;

    const sw = document.createElement("label");
    sw.className = "switch";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = c.active;
    input.disabled = spinning;
    input.addEventListener("change", () => toggleCloser(c.id));
    const slider = document.createElement("span");
    slider.className = "slider";
    sw.append(input, slider);

    li.append(name, sw);
    closerList.appendChild(li);
  });
}

async function toggleCloser(id) {
  await fetch(`/api/closers/${id}/toggle`, { method: "POST" });
  await loadClosers();
}

// ---------------------------------------------------------------------------
// Girar a roleta
// ---------------------------------------------------------------------------
async function spin() {
  if (spinning) return;
  spinning = true;
  spinBtn.disabled = true;
  resultCard.hidden = true;

  const duration = parseInt(document.getElementById("duration").value, 10);
  const when = document.getElementById("when").value;

  const res = await fetch("/api/assign", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ duration_minutes: duration, when }),
  });
  const data = await res.json();

  if (data.chosen) {
    spinToIndex(data.chosen.index);
  } else {
    // ninguém livre: gira algumas voltas "vazias"
    currentRotation += 360 * 4;
    wheel.style.transform = `rotate(${currentRotation}deg)`;
  }

  setTimeout(() => showResult(data), SPIN_MS);
}

function spinToIndex(index) {
  const center = index * SEG_DEG + SEG_DEG / 2;
  const desired = (360 - (center % 360)) % 360; // traz a fatia pro topo
  const base = currentRotation - (currentRotation % 360);
  let next = base + 360 * 5 + desired; // 5 voltas + alvo
  if (next <= currentRotation) next += 360;
  currentRotation = next;
  wheel.style.transform = `rotate(${currentRotation}deg)`;
}

function showResult(data) {
  skipList.innerHTML = "";
  data.skipped.forEach((s, i) => {
    const li = document.createElement("li");
    li.innerHTML = `Pulou <b>${s.name}</b> — ${s.reason}`;
    li.style.animationDelay = `${i * 0.12}s`;
    skipList.appendChild(li);
  });

  if (data.chosen) {
    winnerEl.className = "winner";
    winnerEl.textContent = `Lead vai para: ${data.chosen.name}`;
  } else {
    winnerEl.className = "winner none";
    winnerEl.textContent = "Ninguém disponível nesse horário.";
  }

  queueEl.textContent = data.queue.join(" → ");
  resultCard.hidden = false;

  spinning = false;
  spinBtn.disabled = false;
  drawCloserList(); // reabilita os switches
}

async function loadSource() {
  const res = await fetch("/api/source");
  const { provider } = await res.json();
  if (provider === "google") {
    sourceBadge.textContent = "Agenda: Google Calendar";
    sourceBadge.classList.add("live");
  } else {
    sourceBadge.textContent = "Agenda: simulada (mock)";
  }
}

spinBtn.addEventListener("click", spin);
loadClosers();
loadSource();
