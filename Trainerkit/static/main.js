// static/charts.js

// Hàm render chart (tái sử dụng cho nhiều loại chart)
function renderChart(containerId, type, title, data, dark = false) {
  Highcharts.chart(containerId, {
    chart: {
      type: type,
      backgroundColor: dark ? "#1e1e1e" : "#fff"
    },
    title: {
      text: title,
      style: { color: dark ? "#eee" : "#111" }
    },
    xAxis: {
      categories: data.categories,
      labels: { style: { color: dark ? "#eee" : "#111" } }
    },
    yAxis: {
      title: { text: "Số lượng", style: { color: dark ? "#eee" : "#111" } },
      labels: { style: { color: dark ? "#eee" : "#111" } }
    },
    legend: {
      itemStyle: { color: dark ? "#eee" : "#111" }
    },
    tooltip: {
      shared: true,
      crosshairs: true,
      backgroundColor: dark ? "#333" : "#fff",
      style: { color: dark ? "#eee" : "#111" }
    },
    plotOptions: {
      series: {
        dataLabels: { enabled: true, color: dark ? "#eee" : "#111" }
      }
    },
    series: [
      { name: "Goals", data: data.goals },
      { name: "Assists", data: data.assists }
    ]
  });
}

// Hàm gọi API và render cả 2 chart
async function renderCharts(dark = false) {
  const res = await fetch("/api/chart");
  const data = await res.json();

  renderChart("container1", "line", "Line Chart - Goals & Assists", data, dark);
  renderChart("container2", "column", "Column Chart - Goals & Assists", data, dark);
}

// Export để HTML gọi được
window.renderCharts = renderCharts;

// Render mặc định (light)
renderCharts(false);

