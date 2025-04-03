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

// This function fetches and updates the general statistics
const makeReq = (url, cb) => {
  console.log(`Fetching from: ${url}`);
  fetch(url)
    .then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP error! Status: ${res.status}`);
      }
      return res.json();
    })
    .then((result) => {
      console.log("Received data: ", result);
      cb(result);
    })
    .catch((error) => {
      console.error("Error fetching data:", error);
      updateErrorMessages(`Error fetching from ${url}: ${error.message}`);
    });
};

const updateCodeDiv = (result, elemId) =>
  (document.getElementById(elemId).innerText = JSON.stringify(result));

const getLocaleDateStr = () => new Date().toLocaleString();

const getStats = () => {
  document.getElementById("last-updated-value").innerText = getLocaleDateStr();

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

const updateErrorMessages = (message) => {
  const id = Date.now();
  console.log("Creation", id);
  msg = document.createElement("div");
  msg.id = `error-${id}`;
  msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`;
  document.getElementById("messages").style.display = "block";
  document.getElementById("messages").prepend(msg);
  setTimeout(() => {
    const elem = document.getElementById(`error-${id}`);
    if (elem) {
      elem.remove();
    }
  }, 7000);
};

const setup = () => {
  getStats();
  setInterval(() => getStats(), 4000); // Update every 4 seconds
};

document.addEventListener("DOMContentLoaded", setup);
