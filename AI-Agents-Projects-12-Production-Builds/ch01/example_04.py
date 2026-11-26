from __future__ import annotations

import re
from html.parser import HTMLParser


class CleanTextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript", "svg"}
    BLOCK_TAGS = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "li", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in self.SKIP_TAGS:
            self._skip_depth += 1
        elif self._skip_depth == 0 and t in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif self._skip_depth == 0 and t in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self._chunks.append(stripped + " ")

    def get_clean_text(self) -> str:
        joined = "".join(self._chunks)
        joined = re.sub(r"[ \t]+", " ", joined)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        return joined.strip()


def extract_clean_html(html_payload: str) -> tuple[str, float]:
    parser = CleanTextExtractor()
    parser.feed(html_payload)
    parser.close()
    cleaned = parser.get_clean_text()
    reduction = 1.0 - (len(cleaned) / max(1, len(html_payload)))
    return cleaned, reduction


if __name__ == "__main__":
    sample_html = """
    <html><head><style>.nav{color:red}</style><script>track();</script></head>
    <body>
      <nav>Home | Pricing | Login | Cookie Policy</nav>
      <article>
        <h1>SEC Form 10-K Cloud Infrastructure Disclosure</h1>
        <p>In fiscal year 2025, sovereign enclave workloads accounted for 38.4% of compute spend.</p>
        <p>Zero-trust attestation reduced lateral-movement audit findings by 71%.</p>
      </article>
      <footer>Copyright 2026 Acme Corp. All rights reserved.</footer>
    </body></html>
    """
    text, ratio = extract_clean_html(sample_html)
    print(f"Extracted chars={len(text)} boilerplate_reduction={ratio:.1%}")
    print(text)
