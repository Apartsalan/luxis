import DOMPurify from "dompurify";

/**
 * Sanitize HTML to prevent XSS attacks.
 * Used for rendering email body HTML and other untrusted HTML content.
 *
 * Note: 'style' attribute is intentionally excluded — CSS can be abused
 * for data exfiltration via background-image requests. Email HTML uses
 * class-based styling instead.
 *
 * SEC-24: IMG src attributes are removed to block tracker pixels.
 * A tags get rel="noopener noreferrer" and target="_blank" enforced.
 */

// Hook to block tracker pixels and harden links — runs after DOMPurify sanitizes attributes
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  // Block tracker pixels: remove src from IMG tags
  if (node.tagName === "IMG") {
    node.removeAttribute("src");
    node.setAttribute("alt", node.getAttribute("alt") || "(afbeelding verwijderd)");
  }

  // Harden links: force safe link attributes
  if (node.tagName === "A") {
    node.setAttribute("rel", "noopener noreferrer");
    node.setAttribute("target", "_blank");
  }
});

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: [
      "p", "br", "b", "i", "u", "strong", "em", "a", "ul", "ol", "li",
      "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "code",
      "table", "thead", "tbody", "tr", "th", "td", "img", "span", "div",
      "hr", "sub", "sup",
    ],
    ALLOWED_ATTR: [
      "href", "src", "alt", "title", "class", "target", "rel",
      "width", "height", "colspan", "rowspan",
    ],
    ALLOW_DATA_ATTR: false,
  });
}

/**
 * Sanitize HTML for outgoing email drafts that the user will send.
 * Less strict than sanitizeHtml because:
 * - The user authored / curated the content (no untrusted source)
 * - Inline `style` is needed to preserve template typography/layout
 * - `data:image` IMG src is needed for embedded logos
 *
 * External http(s) IMG src is still stripped via the global afterSanitizeAttributes
 * hook above — so even outgoing drafts cannot leak via tracker pixels. We only
 * re-allow `data:` URIs by setting them back when present.
 */
export function sanitizeOutgoingHtml(dirty: string): string {
  // Snapshot data: src values before global hook strips them, then restore.
  const dataSrcMap = new Map<string, string>();
  const tmp = document.createElement("div");
  tmp.innerHTML = dirty;
  let counter = 0;
  for (const img of Array.from(tmp.querySelectorAll("img"))) {
    const src = img.getAttribute("src") || "";
    if (src.startsWith("data:")) {
      const token = `__LUXIS_DATA_SRC_${counter++}__`;
      dataSrcMap.set(token, src);
      img.setAttribute("data-luxis-token", token);
    }
  }
  const cleaned = DOMPurify.sanitize(tmp.innerHTML, {
    ALLOWED_TAGS: [
      "p", "br", "b", "i", "u", "strong", "em", "a", "ul", "ol", "li",
      "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "code",
      "table", "thead", "tbody", "tr", "th", "td", "img", "span", "div",
      "hr", "sub", "sup", "html", "head", "body", "meta", "style",
    ],
    ALLOWED_ATTR: [
      "href", "src", "alt", "title", "class", "target", "rel", "style",
      "width", "height", "colspan", "rowspan", "border", "cellpadding",
      "cellspacing", "data-luxis-token",
    ],
    ALLOW_DATA_ATTR: true,
  });
  // Restore data: src on tokenised images
  if (dataSrcMap.size === 0) return cleaned;
  const out = document.createElement("div");
  out.innerHTML = cleaned;
  for (const img of Array.from(out.querySelectorAll("img[data-luxis-token]"))) {
    const token = img.getAttribute("data-luxis-token") || "";
    const src = dataSrcMap.get(token);
    if (src) img.setAttribute("src", src);
    img.removeAttribute("data-luxis-token");
  }
  return out.innerHTML;
}
