// KidSafe AI - Content Script
// Extracts page metadata and text for classification and monitors active time restrictions

(() => {
  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "EXTRACT_PAGE_METADATA") {
      const pageData = extractPageContext();
      sendResponse({ success: true, data: pageData });
    }
  });

  /**
   * Sanitizes and extracts visible text content and metadata from the document
   * (Used by the AI Classifier in Phase 3)
   */
  function extractPageContext() {
    const title = document.title || "";
    let metaDescription = "";

    const descEl = document.querySelector('meta[name="description"]') || 
                   document.querySelector('meta[property="og:description"]');
    if (descEl) {
      metaDescription = descEl.getAttribute("content") || "";
    }

    // Extract high-value semantic text from headings, paragraphs, and main content
    const elements = document.querySelectorAll("h1, h2, h3, p, article, main");
    let textChunks = [];
    for (const el of elements) {
      const txt = el.innerText ? el.innerText.trim() : "";
      if (txt.length > 20) {
        textChunks.push(txt);
      }
      if (textChunks.length >= 10) break; // Keep payload minimal
    }

    return {
      url: window.location.href,
      title: title.slice(0, 150),
      metaDescription: metaDescription.slice(0, 300),
      bodySample: textChunks.join(" \n ").slice(0, 1200)
    };
  }
})();
