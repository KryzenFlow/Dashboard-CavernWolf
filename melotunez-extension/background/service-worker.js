/**
 * MeloTunez MV3 service worker — open side panel on action click.
 * AI and music calls run from the side panel / options UI, not here yet.
 */

chrome.runtime.onInstalled.addListener(() => {
  if (chrome.sidePanel?.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {
      /* older Chromium builds */
    });
  }
});

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab?.id || !chrome.sidePanel?.open) return;
  try {
    await chrome.sidePanel.open({ tabId: tab.id });
  } catch {
    /* side panel may already be open */
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === 'ping') {
    sendResponse({ ok: true, service: 'melotunez-extension' });
    return true;
  }
  return false;
});
