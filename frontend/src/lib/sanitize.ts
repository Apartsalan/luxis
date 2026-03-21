import DOMPurify from "dompurify";

/**
 * Sanitize HTML to prevent XSS attacks.
 * Used for rendering email body HTML and other untrusted HTML content.
 *
 * Note: 'style' attribute is intentionally excluded — CSS can be abused
 * for data exfiltration via background-image requests. Email HTML uses
 * class-based styling instead.
 */
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
