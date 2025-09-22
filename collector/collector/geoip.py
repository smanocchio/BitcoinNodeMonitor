"""GeoIP lookup helper."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, cast

GeoIPReader: type[Any] | None

try:  # pragma: no cover
    import geoip2.database as _geoip_database  # type: ignore[import-not-found, import-untyped]
except ImportError:  # pragma: no cover
    GeoIPReader = None
else:  # pragma: no cover
    GeoIPReader = cast(type[Any], _geoip_database.Reader)


class GeoIPResolver:
    def __init__(self, db_dir: str = "/usr/share/GeoIP") -> None:
        self.city_reader: Optional[Any] = None
        self.asn_reader: Optional[Any] = None
        city_path = Path(db_dir) / "GeoLite2-City.mmdb"
        asn_path = Path(db_dir) / "GeoLite2-ASN.mmdb"
        if GeoIPReader is not None and city_path.exists():
            self.city_reader = GeoIPReader(str(city_path))
        if GeoIPReader is not None and asn_path.exists():
            self.asn_reader = GeoIPReader(str(asn_path))

    def close(self) -> None:
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()

    def lookup(self, ip: str) -> dict[str, Optional[str]]:
        result: dict[str, Optional[str]] = {"country": None, "asn": None}
        if self.city_reader:
            try:
                city = self.city_reader.city(ip)
                result["country"] = city.country.iso_code
            except Exception:
                result["country"] = None
        if self.asn_reader:
            try:
                asn = self.asn_reader.asn(ip)
                number = asn.autonomous_system_number
                org = asn.autonomous_system_organization
                result["asn"] = f"AS{number} {org}"
            except Exception:
                result["asn"] = None
        return result
