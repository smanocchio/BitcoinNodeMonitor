# GeoIP Updater

The `geoipupdate` service downloads MaxMind GeoLite2 Country and ASN databases. Provide `GEOIP_ACCOUNT_ID` and `GEOIP_LICENSE_KEY` in `.env` (free account available at https://www.maxmind.com/).

Downloaded databases are stored in the `geoip-data` volume and mounted into the collector container at `/usr/share/GeoIP`.

If credentials are blank, the service remains idle and the collector falls back to IP-only metrics.
