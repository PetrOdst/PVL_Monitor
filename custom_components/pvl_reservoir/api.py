"""Parse current measurements from the PVL HTML page."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
import re
import unicodedata
from zoneinfo import ZoneInfo

_PRAGUE_TZ = ZoneInfo("Europe/Prague")
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_TIMESTAMP_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}")


class PVLPageError(ValueError):
    """Raised when the expected current-measurement table is missing or invalid."""


@dataclass(frozen=True, slots=True)
class PVLMeasurements:
    """Current measurements published for Slapy Reservoir."""

    measured_at: datetime
    water_level_m: float | None
    volume_million_m3: float | None
    inflow_m3_s: float | None
    outflow_m3_s: float | None
    precipitation_24h_mm: float | None
    air_temperature_c: float | None


class _CurrentTableParser(HTMLParser):
    """Collect cell text from the page's current-values table."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.timestamp_text: list[str] = []
        self._table_depth = 0
        self._in_target_table = False
        self._in_cell = False
        self._cell_parts: list[str] = []
        self._row: list[str] | None = None
        self._in_timestamp = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("id") == "AktualniHodnotyDV":
            self._in_target_table = True
            self._table_depth = 1
            return
        if tag == "span" and attributes.get("id") == "casMereniLbl":
            self._in_timestamp = True
        if not self._in_target_table:
            return
        if tag == "table":
            self._table_depth += 1
        elif tag == "tr" and self._table_depth == 1:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None and self._table_depth == 1:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "span":
            self._in_timestamp = False
        if not self._in_target_table:
            return
        if tag in {"td", "th"} and self._in_cell:
            assert self._row is not None
            self._row.append(" ".join("".join(self._cell_parts).split()))
            self._in_cell = False
        elif tag == "tr" and self._row is not None and self._table_depth == 1:
            self.rows.append(self._row)
            self._row = None
        elif tag == "table":
            self._table_depth -= 1
            if self._table_depth == 0:
                self._in_target_table = False

    def handle_data(self, data: str) -> None:
        if self._in_timestamp:
            self.timestamp_text.append(data)
        if self._in_cell:
            self._cell_parts.append(data)


def _normalize_label(value: str) -> str:
    """Normalize Czech labels for matching without depending on their accents."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _parse_number(value: str, label: str) -> float | None:
    """Parse a Czech decimal value, preserving empty values as unavailable."""
    stripped = "".join(value.replace("\xa0", " ").split())
    if not stripped or stripped in {"-", "—", "–"}:
        return None
    if "," in stripped:
        stripped = stripped.replace(".", "").replace(",", ".")
    if not _NUMBER_RE.fullmatch(stripped):
        raise PVLPageError(f"Invalid numeric value for {label}: {value!r}")
    try:
        return float(stripped)
    except ValueError as err:
        raise PVLPageError(f"Invalid numeric value for {label}: {value!r}") from err


def parse_current_measurements(page: str) -> PVLMeasurements:
    """Parse the current-values table without relying on ASP.NET ViewState."""
    parser = _CurrentTableParser()
    parser.feed(page)
    if not parser.rows:
        raise PVLPageError("Current-values table was not found")

    timestamp_value = " ".join(parser.timestamp_text)
    timestamp_match = _TIMESTAMP_RE.search(timestamp_value)
    if timestamp_match is None:
        raise PVLPageError("Current measurement timestamp was not found")
    try:
        measured_at = datetime.strptime(timestamp_match.group(), "%d.%m.%Y %H:%M").replace(tzinfo=_PRAGUE_TZ)
    except ValueError as err:
        raise PVLPageError("Current measurement timestamp is invalid") from err

    field_prefixes = {
        "water_level_m": "hladina vody v nadrzi",
        "volume_million_m3": "objem",
        "inflow_m3_s": "pritok",
        "outflow_m3_s": "odtok",
        "precipitation_24h_mm": "srazky (24h)",
        "air_temperature_c": "teplota vzduchu",
    }
    values: dict[str, float | None] = {}
    for row in parser.rows:
        if len(row) < 2:
            continue
        normalized_label = _normalize_label(row[0])
        for key, prefix in field_prefixes.items():
            if normalized_label.startswith(prefix):
                values[key] = _parse_number(row[1], key)
                break

    missing_fields = set(field_prefixes) - values.keys()
    if missing_fields:
        raise PVLPageError(f"Current-values fields were not found: {', '.join(sorted(missing_fields))}")
    return PVLMeasurements(measured_at=measured_at, **values)
