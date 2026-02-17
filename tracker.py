from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TrackingError(Exception):
    """Raised when tracking information cannot be fetched or parsed."""


@dataclass
class TrackingResult:
    awb: str
    status: str | None
    details: str
    history: list[str]
    source_url: str


class BlueDartTracker:
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    STATUS_PATTERNS = [
        re.compile(r"Current\s*Status\s*[:\-]\s*([^<\n\r]+)", re.IGNORECASE),
        re.compile(r"Shipment\s*Status\s*[:\-]\s*([^<\n\r]+)", re.IGNORECASE),
        re.compile(r"Status\s*[:\-]\s*([^<\n\r]+)", re.IGNORECASE),
    ]

    DETAIL_PATTERNS = [
        re.compile(r"Expected\s*Delivery\s*Date\s*[:\-]\s*([^<\n\r]+)", re.IGNORECASE),
        re.compile(r"Delivered\s*On\s*[:\-]\s*([^<\n\r]+)", re.IGNORECASE),
        re.compile(r"Last\s*Scanned\s*At\s*[:\-]\s*([^<\n\r]+)", re.IGNORECASE),
    ]

    NO_RECORD_PATTERNS = [
        re.compile(r"no\s+records?\s+found", re.IGNORECASE),
        re.compile(r"invalid\s+awb", re.IGNORECASE),
        re.compile(r"unable\s+to\s+find", re.IGNORECASE),
    ]

    def get_direct_tracking_url(self, awb: str) -> str:
        return f"https://www.bluedart.com/web/guest/trackdartresult?trackFor=0&trackNo={awb}"

    def _build_candidate_urls(self, awb: str) -> list[str]:
        query = urlencode({"trackFor": "0", "trackNo": awb})
        return [
            self.get_direct_tracking_url(awb),
            f"https://www.bluedart.com/tracking?tracking_no={awb}",
            f"https://www.bluedart.com/web/guest/trackdartresultthirdparty?{query}",
        ]

    def _fetch_html(self, url: str, timeout: int = 20) -> str:
        req = Request(url, headers={"User-Agent": self.USER_AGENT})
        with urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def parse_tracking_html(self, html: str, awb: str, source_url: str) -> TrackingResult:
        text = self._html_to_text(html)

        if any(pattern.search(text) for pattern in self.NO_RECORD_PATTERNS):
            raise TrackingError(
                "Is AWB ke liye Blue Dart par record nahi mila. AWB dubara check karein."
            )

        status = self._first_match(text, self.STATUS_PATTERNS)
        details = self._first_match(text, self.DETAIL_PATTERNS) or "Detail not clearly available"
        history = self._extract_history_lines(text)

        if not status and not history:
            raise TrackingError(
                "Blue Dart se readable status nahi mil paya (site bot-protection ya format change ho sakta hai)."
            )

        return TrackingResult(
            awb=awb,
            status=status,
            details=details,
            history=history,
            source_url=source_url,
        )

    def track_awb(self, awb: str) -> dict:
        cleaned_awb = awb.strip().upper()
        if not re.fullmatch(r"[A-Z0-9\-]{6,25}", cleaned_awb):
            raise TrackingError("Please valid AWB number daaliye (6-25 alphanumeric characters).")

        last_error = None
        for candidate_url in self._build_candidate_urls(cleaned_awb):
            try:
                html = self._fetch_html(candidate_url)
                result = self.parse_tracking_html(html, cleaned_awb, candidate_url)
                return {
                    "awb": result.awb,
                    "status": result.status or "Status found but unclear",
                    "details": result.details,
                    "history": result.history,
                    "source_url": result.source_url,
                    "tracking_url": self.get_direct_tracking_url(cleaned_awb),
                }
            except (URLError, HTTPError, TimeoutError, TrackingError) as exc:
                last_error = exc
                continue

        raise TrackingError(
            f"Live tracking fetch nahi ho paaya. Error: {last_error}. "
            "Aap direct tracking link use karke verify kar sakte hain."
        )

    @staticmethod
    def _first_match(text: str, patterns: list[re.Pattern]) -> str | None:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return " ".join(match.group(1).split())
        return None

    @staticmethod
    def _extract_history_lines(text: str) -> list[str]:
        lines = []
        for line in text.splitlines():
            compact = " ".join(line.split())
            if len(compact) < 8:
                continue
            if re.search(r"\d{1,2}[-/ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", compact, re.IGNORECASE):
                lines.append(compact)
            elif re.search(r"\d{2}[/-]\d{2}[/-]\d{4}", compact):
                lines.append(compact)
        deduped = []
        seen = set()
        for line in lines:
            if line not in seen:
                seen.add(line)
                deduped.append(line)
        return deduped[:8]

    @staticmethod
    def _html_to_text(html: str) -> str:
        without_script = re.sub(r"<script.*?>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
        without_style = re.sub(r"<style.*?>.*?</style>", " ", without_script, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<[^>]+>", "\n", without_style)
        text = unescape(text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text
