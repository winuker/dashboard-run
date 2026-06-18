async function loadData() {
    const response = await fetch("dashboard_data.json");
    const data = await response.json();

    renderAnalysis(data.plan);
    renderCharts(data.activities);
    renderMap(data.activities);
    renderHistory(data.history || []);
}

function renderAnalysis(planText) {
    document.getElementById("analysis").innerText = planText;
}

function renderCharts(activities) {
    const dates = activities.map(a => a.start_date_local.split("T")[0]);
    const distances = activities.map(a => a.distance / 1000);
    const pace = activities.map(a => (a.moving_time / 60) / (a.distance / 1000));

    new Chart(document.getElementById("paceChart"), {
        type: "line",
        data: {
            labels: dates,
            datasets: [{
                label: "Ritmo (min/km)",
                data: pace,
                borderColor: "#00e676"
            }]
        }
    });

    new Chart(document.getElementById("distanceChart"), {
        type: "bar",
        data: {
            labels: dates,
            datasets: [{
                label: "Distancia (km)",
                data: distances,
                backgroundColor: "#2979ff"
            }]
        }
    });
}

function renderMap(activities) {
    const map = L.map("mapid").setView([37.88, -4.77], 12);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

    activities.forEach(a => {
        if (!a.map || !a.map.summary_polyline) return;

        const coords = decodePolyline(a.map.summary_polyline);
        L.polyline(coords, { color: "#ff1744" }).addTo(map);
    });
}

function decodePolyline(str) {
    let index = 0, lat = 0, lng = 0, coords = [];

    while (index < str.length) {
        let b, shift = 0, result = 0;

        do {
            b = str.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);

        let dlat = (result & 1) ? ~(result >> 1) : (result >> 1);
        lat += dlat;

        shift = 0;
        result = 0;

        do {
            b = str.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);

        let dlng = (result & 1) ? ~(result >> 1) : (result >> 1);
        lng += dlng;

        coords.push([lat / 1e5, lng / 1e5]);
    }

    return coords;
}

loadData();
