"""GeoIP lookup helper."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from geoip2.database import Reader


class GeoIPResolver:
    def __init__(self, db_dir: str = "/usr/share/GeoIP") -> None:
        self.city_reader: Optional[Reader] = None
        self.asn_reader: Optional[Reader] = None
        city_path = Path(db_dir) / "GeoLite2-City.mmdb"
        asn_path = Path(db_dir) / "GeoLite2-ASN.mmdb"
        if city_path.exists():
            self.city_reader = Reader(str(city_path))
        if asn_path.exists():
            self.asn_reader = Reader(str(asn_path))

    @property
    def is_configured(self) -> bool:
        """Return ``True`` when at least one GeoIP database is available."""

        return self.city_reader is not None or self.asn_reader is not None

    def close(self) -> None:
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()

    def lookup(self, ip: str) -> dict[str, Optional[str | float]]:
        result: dict[str, Optional[str | float]] = {
            "country": None,
            "asn": None,
            "latitude": None,
            "longitude": None,
        }
        if self.city_reader:
            try:
                city = self.city_reader.city(ip)
                result["country"] = city.country.iso_code
                result["latitude"] = city.location.latitude
                result["longitude"] = city.location.longitude
            except Exception:  # noqa: BLE001
                result["country"] = None
                result["latitude"] = None
                result["longitude"] = None
        if self.asn_reader:
            try:
                asn = self.asn_reader.asn(ip)
                number = asn.autonomous_system_number
                org = asn.autonomous_system_organization
                result["asn"] = f"AS{number} {org}" if number and org else None
            except Exception:  # noqa: BLE001
                result["asn"] = None
        return result
