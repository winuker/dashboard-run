function formatPace(pace) {
  const minutes = Math.floor(pace);
  const seconds = Math.round((pace - minutes) * 60);
  const padded = seconds.toString().padStart(2, "0");
  return `${minutes}:${padded} / km`;
}

async function loadData() {
  const res = await fetch("dashboard_data.json");
  const data = await res.json();

  // Predicción Media Maratón
  const prediction = predictHalfMarathon(data.activities);
  document.getElementById("predictionText").textContent = prediction;

  renderMetrics(data.summary);
  renderCharts(data.activities, data.summary);
  renderAI(data.plan);
  renderMap(data.activities);
}

function renderMetrics(summary) {
  const container = document.getElementById("metrics");

  container.innerHTML = `
    <div class="card"><h3>KM Totales</h3><p>${summary.km_total} km</p></div>
    <div class="card"><h3>Tiempo Total</h3><p>${summary.time_total_min} min</p></div>
    <div class="card"><h3>Elevación</h3><p>${summary.elevation_total} m</p></div>
    <div class="card"><h3>FC Media</h3><p>${summary.avg_hr_global ?? "-"}</p></div>
    <div class="card"><h3>ATL</h3><p>${summary.ATL}</p></div>
    <div class="card"><h3>CTL</h3><p>${summary.CTL}</p></div>
    <div class="card"><h3>TSB</h3><p>${summary.TSB}</p></div>
  `;
}

function renderCharts(activities, summary) {
  const labels = activities.map(a => a.date);

  // Ritmo
  new Chart(document.getElementById("paceChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Ritmo (min/km)",
        data: activities.map(a => a.pace_min_km),
        borderColor: "#0070f3",
        backgroundColor: "rgba(0,112,243,0.2)",
        tension: 0.3
      }]
    }
  });

  // Distancia
  new Chart(document.getElementById("distanceChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Distancia (km)",
        data: activities.map(a => a.distance_km),
        backgroundColor: "#00b341"
      }]
    }
  });

  // ATL / CTL / TSB
  new Chart(document.getElementById("loadChart"), {
    type: "line",
    data: {
      labels: ["Hoy"],
      datasets: [
        { label: "ATL", data: [summary.ATL], borderColor: "#ff4d4d", borderWidth: 2 },
        { label: "CTL", data: [summary.CTL], borderColor: "#0070f3", borderWidth: 2 },
        { label: "TSB", data: [summary.TSB], borderColor: "#f2a900", borderWidth: 2 }
      ]
    }
  });
}

function renderAI(text) {
  document.getElementById("aiText").textContent = text;
}

function renderMap() {
  const map = L.map("map").setView([37.88, -4.77], 12); // Córdoba

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18
  }).addTo(map);
}

// Predicción Media Maratón
function predictHalfMarathon(activities) {
  const lastRuns = activities.slice(-6);
  const avgPace = lastRuns.reduce((acc, a) => acc + a.pace_min_km, 0) / lastRuns.length;

  const predictedMinutes = avgPace * 21.097;
  const hours = Math.floor(predictedMinutes / 60);
  const minutes = Math.round(predictedMinutes % 60);

  return `${hours}h ${minutes}min`;
}

loadData();

