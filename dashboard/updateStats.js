const PROCESSING_STATS_API_URL =
  "http://microservices-app.westus2.cloudapp.azure.com:8100/stats";
const ANALYZER_API_URL = {
  stats:
    "http://microservices-app.westus2.cloudapp.azure.com:8110/traffic/stats",
  conditions:
    "http://microservices-app.westus2.cloudapp.azure.com:8110/traffic/conditions?index=latest",
  incident:
    "http://microservices-app.westus2.cloudapp.azure.com:8110/traffic/incidents?index=latest",
};

// Simple fetch function
const makeReq = (url, cb) => {
  console.log(`Fetching from: ${url}`);
  fetch(url)
    .then((res) => res.json())
    .then((result) => {
      console.log(`Got data from ${url}`);
      cb(result);
    })
    .catch((error) => {
      console.error(`Error fetching from ${url}: ${error}`);
      document.getElementById("messages").style.display = "block";
      const msg = document.createElement("div");
      msg.innerHTML = `<p>Error: ${error.message}</p>`;
      document.getElementById("messages").appendChild(msg);
    });
};

// Update element with data
const updateCodeDiv = (result, elemId) => {
  const element = document.getElementById(elemId);
  if (element) {
    element.textContent = JSON.stringify(result, null, 2);
  } else {
    console.error(`Element ${elemId} not found`);
  }
};

// Get current time
const getLocaleDateStr = () => new Date().toLocaleString();

// Main function to get stats
const getStats = () => {
  const timeElement = document.getElementById("last-updated-value");
  if (timeElement) {
    timeElement.textContent = getLocaleDateStr();
  }

  makeReq(PROCESSING_STATS_API_URL, (result) =>
    updateCodeDiv(result, "processing-stats")
  );

  makeReq(ANALYZER_API_URL.stats, (result) =>
    updateCodeDiv(result, "analyzer-stats")
  );

  makeReq(ANALYZER_API_URL.conditions, (result) =>
    updateCodeDiv(result, "event-conditions")
  );

  makeReq(ANALYZER_API_URL.incident, (result) =>
    updateCodeDiv(result, "event-incident")
  );
};

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  console.log("Dashboard starting");
  getStats();
  setInterval(getStats, 4000);
});
