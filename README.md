# PVL Reservoir Monitor

Home Assistant custom integration for current measurements from VD Slapy, published by Povodí Vltavy.

## Features

- Reads current values from the public PVL measurements page every 10 minutes.
- Creates sensors for water level, volume, inflow, outflow, 24-hour precipitation, and air temperature.
- Uses Home Assistant Recorder for history. The integration does not download historical measurements from PVL.
- Includes a Lovelace card with current readings, one-hour and 24-hour water-level charts, and configurable named reference levels.

## Data source and parsing

The integration requests:

<https://www.pvl.cz/portal/nadrze/cz/pc/Mereni.aspx?id=VLSL&oid=2>

The inspected page returns an ASP.NET Web Forms HTML page with its current-values table rendered in the response. No public JSON/XML endpoint was found in the page or its `Mereni.js` script. The integration parses the visible current-values table and does not depend on the page's `__VIEWSTATE` field.

PVL warns that its measurements are provided without guarantee. The page uses decimal commas. Empty fields are exposed as unavailable sensors rather than zero.

## Installation

### Manual integration installation

Copy `custom_components/pvl_reservoir` into the `custom_components` directory under your Home Assistant configuration directory, then restart Home Assistant. Add **PVL Reservoir Monitor** from **Settings → Devices & services → Add integration**.

### Dashboard card

Copy `www/pvl-reservoir-card.js` to the `www` directory under your Home Assistant configuration directory. Add it as a JavaScript module resource at `/local/pvl-reservoir-card.js`.

An integration-type HACS repository installs the integration folder, not the root-level `www` card file. HACS users therefore need to install/register the card separately, or use a future dedicated HACS dashboard repository for the card.

## Lovelace configuration

The card defaults to the entity IDs created by the integration and provides three reference examples from the Slapy page. Change the values or names to define your own reference levels. The water-level entity ID can be overridden if it differs in your Home Assistant entity registry.

```yaml
type: custom:pvl-reservoir-card
entities:
  water_level: sensor.pvl_reservoir_slapy_water_level
references:
  - name: Hladina stálého nadržení
    level: 246.6
  - name: Kóta přelivu
    level: 262.6
  - name: Maximální retenční hladina
    level: 270.6
```

The card selection is stored in the browser's local storage. It is not synchronized between different browsers or devices. The card reads only Home Assistant sensor states and Recorder history; it does not fetch data from PVL.

## Sensors

| Sensor | Home Assistant unit | Notes |
| --- | --- | --- |
| Water level | m | Elevation in PVL's Balt p. v. vertical system |
| Volume | m³ | Converted from PVL's million m³ value |
| Inflow | m³/s | Current inflow |
| Outflow | m³/s | Current outflow |
| Precipitation 24h | mm | Rolling 24-hour value; no forced updates |
| Air temperature | °C | Current value |

Home Assistant Recorder stores state changes according to its configuration. Keep the water-level entity included in Recorder for the card charts. Recorder retention controls how much raw history is available.

## Development

Run parser tests with the Python standard library:

```sh
python3 -m unittest discover -s tests -v
```

The project workspace does not include the Home Assistant Python package. A complete integration setup test must be run in a Home Assistant development environment.

## HACS publication checklist

- Create a public GitHub repository and set its description and topics.
- Replace `OWNER` in `custom_components/pvl_reservoir/manifest.json` with the GitHub account or organization and repository name.
- Decide whether to distribute the card in a separate HACS dashboard repository or document manual installation.
- Run Home Assistant and HACS validation in the target development environment before publishing.
