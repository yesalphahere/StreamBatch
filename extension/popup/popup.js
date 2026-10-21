document.addEventListener("DOMContentLoaded", async () => {
  const pageUrlInput = document.getElementById("page-url");
  const formatSelect = document.getElementById("format-select");
  const qualitySelect = document.getElementById("quality-select");
  const sendBtn = document.getElementById("send-btn");
  const statusIndicator = document.getElementById("status-indicator");
  const feedbackMsg = document.getElementById("feedback-msg");

  // Get active tab URL
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      pageUrlInput.value = tab.url;
    }
  } catch (e) {
    pageUrlInput.value = "";
  }

  // Check if desktop StreamBatch loopback is responsive
  async function checkDesktopStatus() {
    try {
      const resp = await fetch("http://127.0.0.1:9654/status");
      if (resp.ok) {
        statusIndicator.textContent = "Connected";
        statusIndicator.className = "status-badge online";
        sendBtn.disabled = false;
        return true;
      }
    } catch (e) {
      statusIndicator.textContent = "App Offline";
      statusIndicator.className = "status-badge offline";
      return false;
    }
  }

  await checkDesktopStatus();

  sendBtn.addEventListener("click", async () => {
    const url = pageUrlInput.value.trim();
    if (!url) {
      feedbackMsg.textContent = "No valid URL on current tab.";
      feedbackMsg.className = "msg error";
      return;
    }

    sendBtn.disabled = true;
    feedbackMsg.textContent = "Sending to StreamBatch...";
    feedbackMsg.className = "msg";

    chrome.runtime.sendMessage(
      {
        action: "send_url",
        url: url,
        format: formatSelect.value,
        quality: qualitySelect.value
      },
      (response) => {
        sendBtn.disabled = false;
        if (response && response.success) {
          feedbackMsg.textContent = "Sent to StreamBatch successfully!";
          feedbackMsg.className = "msg success";
          setTimeout(() => window.close(), 1500);
        } else {
          feedbackMsg.textContent = (response && response.error) || "Could not connect to desktop app.";
          feedbackMsg.className = "msg error";
        }
      }
    );
  });
});
