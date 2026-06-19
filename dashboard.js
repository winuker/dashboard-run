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

  function colorATL(value) {
    if (value < 40) return "green";
    if (value < 70) return "orange";
    return "red";
  }

  function colorCTL(value) {
    if (value < 30) return "gray";
    if (value < 60) return "blue";
    return "green";
  }

  function colorTSB(value) {
    if (value > 10) return "green";
    if (value >= 0) return "orange";
    return "red";
  }

  container.innerHTML = `
    <div class="card">
      <h3>KM Totales</h3>
      <p>${summary.km_total} km</p>
    </div>

    <div class="card">
      <h3>Tiempo Total</h3>
      <p>${summary.time_total_min} min</p>
    </div>

    <div class="card">
      <h3>Elevación</h3>
      <p>${summary.elevation_total} m</p>
    </div>

    <div class="card">
      <h3>FC Media</h3>
      <p>${summary.avg_hr_global ?? "-"}</p>
    </div>

    <div class="card">
      <h3>ATL</h3>
      <p style="color:${colorATL(summary.ATL)}; font-weight:bold;">
        ${summary.ATL}
      </p>
      <small class="legend">Fatiga reciente</small>
    </div>

    <div class="card">
      <h3>CTL</h3>
      <p style="color:${colorCTL(summary.CTL)}; font-weight:bold;">
        ${summary.CTL}
      </p>
      <small class="legend">Forma acumulada (base)</small>
    </div>

    <div class="card">
      <h3>TSB</h3>
      <p style="color:${colorTSB(summary.TSB)}; font-weight:bold;">
        ${summary.TSB}
      </p>
      <small class="legend">Frescura actual</small>
    </div>
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
      label: "Ritmo",
      data: activities.map(a => a.pace_min_km),
      borderColor: "#0070f3",
      backgroundColor: "rgba(0,112,243,0.2)",
      tension: 0.3
    }]
  },
  options: {
    plugins: {
      tooltip: {
        callbacks: {
          label: function(context) {
            const raw = context.raw;
            return "Ritmo: " + formatPace(raw);
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: function(value) {
            return formatPace(value);
          }
        }
      }
    }
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
document.getElementById("refreshBtn").addEventListener("click", async () => {
  const bar = document.getElementById("loadingBar");
  bar.classList.remove("hidden");
  bar.style.width = "10%";

  // Llamar a GitHub Actions
  await fetch("https://api.github.com/repos/winuker/dashboard-run/actions/workflows/refresh.yml/dispatches", {
    method: "POST",
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": "Bearer TU_TOKEN_PERSONAL",
      "X-GitHub-Api-Version": "2022-11-28"
    },
    body: JSON.stringify({
      ref: "main"
    })
  });

  // Animación de progreso falsa mientras GitHub Actions trabaja
  let progress = 10;
  const interval = setInterval(() => {
    progress += 5;
    bar.style.width = progress + "%";
    if (progress >= 95) clearInterval(interval);
  }, 500);

  // Esperar 30–60s a que GitHub Actions termine
  setTimeout(() => {
    bar.style.width = "100%";
    setTimeout(() => {
      bar.classList.add("hidden");
      bar.style.width = "0%";
      location.reload();
    }, 800);
  }, 45000);
});

