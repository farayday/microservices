// Dashboard Configuration
const CONFIG = {
  baseUrl: "http://localhost:8110", // Change this to match your local service port

  endpoints: {
    analyzerStats: "/traffic/stats",
    trafficConditions: "/traffic/conditions",
    trafficIncidents: "/traffic/incidents",
  },

  // Update every 3 seconds
  refreshInterval: 3000,
};

// DOM Elements
const elements = {
  timestamp: document.getElementById("timestamp"),
  analyzerStats: document.getElementById("analyzer-stats"),
  randomEvent1: document.getElementById("random-event-1"),
  randomEvent2: document.getElementById("random-event-2"),
};

// Fetch data from API
async function fetchData(endpoint) {
  try {
    const response = await fetch(`${CONFIG.baseUrl}${endpoint}`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error fetching data from ${endpoint}:`, error);
    return { error: error.message };
  }
}

// Format timestamp
function formatTimestamp() {
  const now = new Date();
  return now.toLocaleString();
}

// Update timestamp
function updateTimestamp() {
  elements.timestamp.textContent = formatTimestamp();
}

// Create a simple table from object
function createTable(data) {
  if (!data || typeof data !== "object") {
    return "<p>No data available</p>";
  }

  let tableHtml = "<table>";
  tableHtml += "<tr><th>Property</th><th>Value</th></tr>";

  for (const [key, value] of Object.entries(data)) {
    if (typeof value !== "object") {
      tableHtml += `<tr><td>${key}</td><td>${value}</td></tr>`;
    }
  }

  tableHtml += "</table>";
  return tableHtml;
}

// Display JSON in a readable format
function displayJson(data) {
  if (!data) return "<p>No data available</p>";

  if (data.error) {
    return `<p>Error: ${data.error}</p>`;
  }

  return `<div class="json-display">${JSON.stringify(data, null, 2)}</div>`;
}

// Update Analyzer Stats
async function updateAnalyzerStats() {
  const data = await fetchData(CONFIG.endpoints.analyzerStats);

  if (data.error) {
    elements.analyzerStats.innerHTML = `<p>Error: ${data.error}</p>`;
    return;
  }

  elements.analyzerStats.innerHTML = createTable(data);
}

// Update random event
async function updateRandomEvent(endpoint, element, paramName = "index") {
  // Generate a random index between 0 and 5
  const randomIndex = Math.floor(Math.random() * 5);

  const data = await fetchData(`${endpoint}?${paramName}=${randomIndex}`);

  if (data.error) {
    element.innerHTML = `<p>Error: ${data.error}</p>`;
    return;
  }

  element.innerHTML = displayJson(data);
}

// Update all dashboard data
async function updateDashboard() {
  updateAnalyzerStats();
  updateRandomEvent(CONFIG.endpoints.trafficConditions, elements.randomEvent1);
  updateRandomEvent(CONFIG.endpoints.trafficIncidents, elements.randomEvent2);

  // Update the last updated timestamp
  updateTimestamp();
}

// Initialize dashboard
function initDashboard() {
  // Initial update
  updateDashboard();

  // Set interval for updates
  setInterval(updateDashboard, CONFIG.refreshInterval);
}

// Start when page loads
document.addEventListener("DOMContentLoaded", initDashboard);
