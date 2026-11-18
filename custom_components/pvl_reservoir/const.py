"""Constants for the PVL Reservoir Monitor integration."""

from datetime import timedelta

DOMAIN = "pvl_reservoir"
RESERVOIR_ID = "VLSL"
RESERVOIR_NAME = "VD Slapy"
RIVER_NAME = "Vltava"
PVL_MEASUREMENTS_URL = "https://www.pvl.cz/portal/nadrze/cz/pc/Mereni.aspx?id=VLSL&oid=2"
UPDATE_INTERVAL = timedelta(minutes=10)
REQUEST_TIMEOUT_SECONDS = 20
PLATFORMS = ("sensor",)
