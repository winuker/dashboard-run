async function loadData() {
  const res = await fetch("dashboard_data.json");
  const data = await res.json();
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

  new Chart(document.getElementById("paceChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Ritmo (min/km)",
        data: activities.map(a => a.pace_min_km),
        borderColor: "#58a6ff",
        tension: 0.3
      }]
    }
  });

  new Chart(document.getElementById("distanceChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Distancia (km)",
        data: activities.map(a => a.distance_km),
        backgroundColor: "#238636"
      }]
    }
  });

  new Chart(document.getElementById("loadChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "ATL",
        data: [summary.ATL],
        borderColor: "#ff7b72"
      },{
        label: "CTL",
        data: [summary.CTL],
        borderColor: "#58a6ff"
      },{
        label: "TSB",
        data: [summary.TSB],
        borderColor: "#f2cc60"
      }]
    }
  });
}

function renderAI(text) {
  document.getElementById("aiText").textContent = text;
}

function renderMap(activities) {
  const map = L.map("map").setView([37.88, -4.77], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18
  }).addTo(map);
}

function predictHalfMarathon(activities) {
  // Basado en tus últimos 30 días
  const lastRuns = activities.slice(-6); // últimas 6 sesiones
  const avgPace = lastRuns.reduce((acc, a) => acc + a.pace_min_km, 0) / lastRuns.length;

  // Fórmula simple: ritmo * 21.097 km
  const predictedMinutes = avgPace * 21.097;

  const hours = Math.floor(predictedMinutes / 60);
  const minutes = Math.round(predictedMinutes % 60);

  return `${hours}h ${minutes}min`;
}

loadData();
