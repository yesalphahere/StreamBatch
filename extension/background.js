/**
 * StreamBatch - Background Service Worker (Manifest V3)
 * Handles context menus, shortcut triggers, and desktop app IPC.
 */

const LOCAL_API_URL = "http://127.0.0.1:9654/add";
const NATIVE_HOST_NAME = "com.streambatch.native_host";

// Setup context menu on installation
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "streambatch-download-link",
    title: "Download with StreamBatch",
    contexts: ["link", "video", "audio"]
  });

  chrome.contextMenus.create({
    id: "streambatch-download-page",
    title: "Download This Media Page with StreamBatch",
    contexts: ["page"]
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  const targetUrl = info.linkUrl || info.srcUrl || info.pageUrl || tab?.url;
  if (targetUrl) {
    sendUrlToStreamBatch(targetUrl, "mp3", "320");
  }
});

// Communication with Desktop App via HTTP loopback or Native Messaging
async function sendUrlToStreamBatch(url, format = "mp3", quality = "320") {
  try {
    // 1. Try Local HTTP Loopback (fastest & most universal)
    const response = await fetch(LOCAL_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, format, quality })
    });

    if (response.ok) {
      showBadge("OK", "#10b981");
      return { success: true };
    }
  } catch (err) {
    // 2. Fallback to Native Messaging Host if HTTP server wasn't reached
    try {
      const nativeResp = await chrome.runtime.sendNativeMessage(NATIVE_HOST_NAME, {
        action: "add_download",
        url: url,
        format: format,
        quality: quality
      });
      showBadge("OK", "#10b981");
      return { success: true, native: true, data: nativeResp };
    } catch (nativeErr) {
      showBadge("ERR", "#ef4444");
      console.warn("Could not connect to StreamBatch desktop:", nativeErr);
      return {
        success: false,
        error: "StreamBatch desktop application is not running or native host is not registered."
      };
    }
  }
}

function showBadge(text, color) {
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color });
  setTimeout(() => {
    chrome.action.setBadgeText({ text: "" });
  }, 3000);
}

// Listen for messages from popup UI
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "send_url") {
    sendUrlToStreamBatch(request.url, request.format, request.quality).then(sendResponse);
    return true; // Keep message channel open for async response
  }
});
