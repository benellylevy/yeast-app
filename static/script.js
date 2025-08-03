// פונקציה לעדכון טבלת feedback_log
const highlightWell = 1;
const experimentPhase = window.experimentPhase || "feedback";

function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-GB');
    const dateString = now.toLocaleDateString('en-GB');
    document.getElementById("retro-clock").innerText = `🕰️ ${dateString} | ${timeString}`;
  }
  setInterval(updateClock, 1000);
  window.onload = () => {
    updateClock();
    updateScriptLights();
    updateDynamicTable();
    fetch("/get_paths")
     .then(res => res.json())
     .then(data => {
         document.getElementById("aggDisplay").innerText = data.agg_path || "—";
         document.getElementById("mqttDisplay").innerText = data.mqtt_path || "—";
         document.getElementById("currentGraphPath").innerText = data.csv_for_fig || "—";
  })   ;
  };
  
function updateFeedbackTable() {
    fetch('/api/feedback_log')
        .then(res => res.json())
        .then(data => {
            const tableBody = document.querySelector('#feedbackTable tbody');
            tableBody.innerHTML = '';
            data.forEach((row, index) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${index + 1}</td><td>${row.val}</td><td>${row.Temp_sent}</td>`;
                tableBody.appendChild(tr);
            });
        });
}
let gfpCtx = document.getElementById('gfpChart').getContext('2d');
let gfpChart = new Chart(gfpCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: []
    },
    options: {
        animation: false,
        parsing: false,
        normalized: true,
        scales: {
            x: { type: 'time', time: { unit: 'minute' }, title: { display: true, text: 'Time' }},
            y: { title: { display: true, text: 'mean_F_C2' } }
        }
    }
});
function parseWellNumbers(input) {
    let wells = [];
    input.split(',').forEach(part => {
        if (part.includes('-')) {
            const [start, end] = part.split('-').map(Number);
            for (let i = start; i <= end; i++) wells.push(i);
        } else {
            wells.push(Number(part));
        }
    });
    return wells;
}

function submitPaths(event) {
    event.preventDefault();
    const agg = document.getElementById('aggPath').value;
    const mqtt = document.getElementById('mqttPath').value;
    const wellsRaw = document.getElementById('wells').value;
    const wells = parseWellNumbers(wellsRaw);

    fetch('/set_paths', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            agg_path: agg,
            mqtt_path: mqtt,
            well_numbers: wells
        })
    }).then(res => res.json())
      .then(data => {
          document.getElementById('pathStatus').innerText = '✅ Paths set successfully';
          // הדלקת נורות סטטוס ליד AGG ו־MQTT
          document.getElementById("status-aggPath").classList.add("status-on");
          document.getElementById("status-mqttPath").classList.add("status-on");
          // עדכון תצוגת נתיבים
          document.getElementById("currentAnalysePath").innerText = data.csv_directory || 'N/A';
          document.getElementById("currentGraphPath").innerText = data.csv_for_fig || 'N/A';
      })
      .catch(err => {
          document.getElementById('pathStatus').innerText = '❌ Failed to set paths';
      });
}
setInterval(updateGFPChart, 1800000); // כל 30 דקות
function updateGFPChart() {
    fetch('/api/agg_recent')
        .then(res => res.json())
        .then(data => {
            const grouped = {};
            data.forEach(row => {
                const well = row.well_number;
                if (!grouped[well]) grouped[well] = [];
                grouped[well].push({ x: row.Time_Stamp, y: row.mean_F_C2 });
            });

            gfpChart.data.datasets = Object.entries(grouped).map(([well, points], idx) => {
                const w = Number(well);
                let color = 'gray';
                if (experimentPhase === 'acclimation') {
                    const hue = (idx * 35) % 360;
                    color = `hsl(${hue}, 70%, 55%)`;
                } else if (experimentPhase === 'feedback' && w === highlightWell) {
                    color = 'salmon';
                }
                return {
                    label: `Well ${well}`,
                    data: points,
                    borderWidth: 1,
                    tension: 0.3,
                    borderColor: color,
                    hidden: false
                };
            });

            gfpChart.update();
        });
}

function refreshDualChart(experimentPhase, wellNumbers, dataPoints) {
    // יצירת פלטת צבעים מבוססת HSL עבור כל באר
    const baseHue = 200; // כחול
    const saturation = 70;
    const lightness = 50;
    const colors = wellNumbers.map((well, idx) => {
        if (experimentPhase === 'acclimation') {
            return `hsl(${(baseHue + idx * 40) % 360}, ${saturation}%, ${lightness}%)`;
        } else if (experimentPhase === 'feedback') {
            return well === highlightWell ? 'salmon' : 'gray';
        }
        return 'gray';
    });

    const datasets = wellNumbers.map((well, idx) => ({
        label: `Well ${well}`,
        data: dataPoints[well] || [],
        backgroundColor: colors[idx],
        borderWidth: 1
    }));

    const dualChartCtx = document.getElementById('dualChart').getContext('2d');
    if (window.dualChartInstance) {
        window.dualChartInstance.data.datasets = datasets;
        window.dualChartInstance.update();
    } else {
        window.dualChartInstance = new Chart(dualChartCtx, {
            type: 'bar',
            data: {
                labels: [], // יש למלא את התוויות לפי הצורך
                datasets: datasets
            },
            options: {
                animation: false,
                scales: {
                    x: { title: { display: true, text: 'Wells' } },
                    y: { title: { display: true, text: 'Value' } }
                }
            }
        });
    }
}

updateGFPChart();  // תוכל לרענן גם באינטרוול אם תרצה
let ctx = document.getElementById('tempChart').getContext('2d');
let tempChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Temperature (°C)',
            data: [],
            borderColor: 'lime',
            borderWidth: 2
        }]
    },
    options: {
        animation: false,
        scales: {
            x: { title: { display: true, text: 'Time' }},
            y: { title: { display: true, text: '°C' }, min: 25, max: 45 }
        }
    }
});

function fetchTemperature() {
    fetch('/api/temperature_from_path')
        .then(res => res.json())
        .then(data => {
            if (!data.error) {
                tempChart.data.labels.push(data.time);
                tempChart.data.datasets[0].data.push(data.temperature);
                if (tempChart.data.labels.length > 20) {
                    tempChart.data.labels.shift();
                    tempChart.data.datasets[0].data.shift();
                }
                tempChart.update();
            }
        });
}

setInterval(fetchTemperature, 1000);

// רענון טבלת פידבק כל 10 דקות
setInterval(updateFeedbackTable, 600000);