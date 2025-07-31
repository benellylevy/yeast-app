let ctx = document.getElementById("dualChart").getContext("2d");
let chart;

fetch("/api/agg_dual")
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert("Error loading data: " + data.error);
            return;
        }

        const t0 = new Date(data.t0);

        const gfpPoints = data.gfp_data.map(row => ({
            x: (new Date(row.Time_Stamp) - t0) / 60000, // דקות יחסיות
            y: row.mean_F_C2,
            well: row.well_number
        }));

        const tempPoints = data.temp_data.map(row => ({
            x: (new Date(row.x) - t0) / 60000,
            y: row.y
        }));

        chart = new Chart(ctx, {
            type: "line",
            data: {
                datasets: [
                    {
                        label: "GFP",
                        data: gfpPoints,
                        parsing: false,
                        borderColor: "salmon",
                        yAxisID: "y1",
                        tension: 0.3
                    },
                    {
                        label: "Temperature",
                        data: tempPoints,
                        parsing: false,
                        borderColor: "lime",
                        yAxisID: "y2",
                        tension: 0.3
                    }
                ]
            },
            options: {
                scales: {
                    x: {
                        title: { display: true, text: "Minutes from t₀" },
                        type: "linear"
                    },
                    y1: {
                        type: "linear",
                        position: "left",
                        title: { display: true, text: "GFP (mean_F_C2)" }
                    },
                    y2: {
                        type: "linear",
                        position: "right",
                        title: { display: true, text: "Temperature (°C)" },
                        grid: { drawOnChartArea: false }
                    }
                },
                plugins: {
                    legend: { position: "top" }
                }
            }
        });
    });