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
