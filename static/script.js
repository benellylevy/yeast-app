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

            gfpChart.data.datasets = Object.entries(grouped).map(([well, points]) => ({
                label: `Well ${well}`,
                data: points,
                borderWidth: 1,
                tension: 0.3,
                borderColor: well == 1 ? 'salmon' : 'gray',
                hidden: well != 1
            }));

            gfpChart.update();
        });
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