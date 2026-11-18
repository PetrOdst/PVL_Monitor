const DEFAULT_ENTITIES = {
  water_level: "sensor.pvl_reservoir_slapy_water_level",
  volume: "sensor.pvl_reservoir_slapy_volume",
  inflow: "sensor.pvl_reservoir_slapy_inflow",
  outflow: "sensor.pvl_reservoir_slapy_outflow",
  precipitation_24h: "sensor.pvl_reservoir_slapy_precipitation_24h",
  air_temperature: "sensor.pvl_reservoir_slapy_air_temperature",
};

const DEFAULT_REFERENCES = [
  { name: "Hladina stálého nadržení", level: 246.6 },
  { name: "Kóta přelivu", level: 262.6 },
  { name: "Maximální retenční hladina", level: 270.6 },
];

const VALUE_LABELS = [
  ["water_level", "Hladina", "m n. m."],
  ["volume", "Objem", "mil. m³"],
  ["inflow", "Přítok", "m³/s"],
  ["outflow", "Odtok", "m³/s"],
  ["precipitation_24h", "Srážky za 24 hodin", "mm"],
  ["air_temperature", "Teplota vzduchu", "°C"],
];

class PVLReservoirCard extends HTMLElement {
  setConfig(config) {
    if (!config || (config.references !== undefined && !Array.isArray(config.references))) {
      throw new Error("The references option must be a list of name and level pairs.");
    }
    const references = config.references || DEFAULT_REFERENCES;
    if (references.some((reference) => (
      !reference || typeof reference.name !== "string" || reference.level === null
      || reference.level === undefined || String(reference.level).trim() === ""
      || !Number.isFinite(Number(reference.level))
    ))) {
      throw new Error("Each reference needs a name and a numeric level in meters.");
    }
    this._config = { ...config, entities: { ...DEFAULT_ENTITIES, ...config.entities }, references };
    this._period = "day";
    this._lastWaterState = undefined;
    this._historyRequestId = 0;
    this._build();
  }

  set hass(hass) {
    this._hass = hass;
    this._updateValues();
  }

  get hass() { return this._hass; }
  getCardSize() { return 6; }

  static getStubConfig() {
    return { type: "custom:pvl-reservoir-card", entities: DEFAULT_ENTITIES, references: DEFAULT_REFERENCES };
  }

  _build() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { padding: 16px; }
        h2, h3 { margin: 0 0 12px; }
        .values { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
        .value { padding: 10px; border-radius: 10px; background: var(--secondary-background-color); }
        .label { color: var(--secondary-text-color); font-size: 0.85em; }
        .number { margin-top: 4px; font-size: 1.25em; font-weight: 600; }
        .reference { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin: 16px 0; }
        .reference select, .periods button { color: var(--primary-text-color); background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 6px; padding: 7px 10px; }
        .difference { font-weight: 600; }
        .chart-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
        .periods { display: flex; gap: 6px; }
        .periods button[aria-pressed="true"] { color: var(--text-primary-color); background: var(--primary-color); }
        .chart { width: 100%; min-height: 150px; }
        .chart svg { display: block; width: 100%; height: 170px; overflow: visible; }
        .grid { stroke: var(--divider-color); stroke-width: 1; }
        .line { fill: none; stroke: var(--primary-color); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
        .point { fill: var(--primary-color); }
        .empty, .updated { color: var(--secondary-text-color); font-size: 0.9em; }
        .updated { margin-top: 8px; }
        @media (max-width: 420px) { .values { grid-template-columns: 1fr; } .chart-heading { align-items: flex-start; flex-direction: column; } }
      </style>
      <ha-card>
        <h2>Vodní nádrž Slapy</h2>
        <div class="values"></div>
        <div class="reference"><label for="reference-select">Referenční hladina</label><select id="reference-select"></select><span class="difference" id="difference">—</span></div>
        <div class="chart-heading"><h3>Vývoj hladiny</h3><div class="periods" aria-label="Období grafu">
          <button type="button" data-period="hour" aria-pressed="false">1 hodina</button>
          <button type="button" data-period="day" aria-pressed="true">24 hodin</button>
        </div></div>
        <div class="chart" id="chart"><p class="empty">Načítám historii…</p></div>
        <div class="updated" id="updated"></div>
      </ha-card>`;

    this._renderValues();
    this._populateReferences();
    this.shadowRoot.querySelector("#reference-select").addEventListener("change", (event) => {
      this._saveReference(event.target.value);
      this._updateDifference();
    });
    this.shadowRoot.querySelectorAll(".periods button").forEach((button) => {
      button.addEventListener("click", () => {
        this._period = button.dataset.period;
        this.shadowRoot.querySelectorAll(".periods button").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
        this._loadHistory();
      });
    });
    this._updateValues();
  }

  _renderValues() {
    const values = this.shadowRoot.querySelector(".values");
    values.replaceChildren();
    VALUE_LABELS.forEach(([key, label, unit]) => {
      const item = document.createElement("div"); item.className = "value";
      const title = document.createElement("div"); title.className = "label"; title.textContent = label;
      const number = document.createElement("div"); number.className = "number"; number.dataset.value = key; number.textContent = `— ${unit}`;
      item.append(title, number); values.append(item);
    });
  }

  _populateReferences() {
    const select = this.shadowRoot.querySelector("#reference-select");
    select.replaceChildren();
    this._config.references.forEach((reference, index) => {
      if (!reference || typeof reference.name !== "string" || !Number.isFinite(Number(reference.level))) return;
      const option = document.createElement("option"); option.value = String(index);
      option.textContent = `${reference.name} (${this._format(Number(reference.level), 2)} m)`; select.append(option);
    });
    const saved = this._loadSavedReference();
    if ([...select.options].some((option) => option.value === saved)) select.value = saved;
    select.disabled = select.options.length === 0;
  }

  _storageKey() { return `pvl-reservoir-reference:${this._config.reference_key || this._config.entities.water_level}`; }
  _loadSavedReference() { try { return window.localStorage.getItem(this._storageKey()) || "0"; } catch (_error) { return "0"; } }
  _saveReference(value) { try { window.localStorage.setItem(this._storageKey(), value); } catch (_error) { /* Keep the selection for this page if storage is unavailable. */ } }

  _state(key) { return this._hass?.states?.[this._config.entities[key]]; }

  _numericState(key) {
    const state = this._state(key)?.state;
    if (state === undefined || state === "unknown" || state === "unavailable") return null;
    const value = Number(state);
    return Number.isFinite(value) ? value : null;
  }

  _unit(key) { return this._state(key)?.attributes?.unit_of_measurement || VALUE_LABELS.find(([item]) => item === key)?.[2] || ""; }

  _waterLevelMeters(value, unit = this._unit("water_level")) {
    if (unit === "ft" || unit === "feet") return value * 0.3048;
    if (unit === "cm") return value / 100;
    if (unit === "mm") return value / 1000;
    if (unit === "km") return value * 1000;
    return value;
  }

  _volumeMillionsOfCubicMeters(value, unit = this._unit("volume")) {
    const factors = { "m³": 1, m3: 1, "ft³": 0.028316846592, ft3: 0.028316846592, L: 0.001, gal: 0.003785411784, "UK gal": 0.00454609 };
    const factor = factors[unit];
    return factor === undefined ? null : value * factor / 1_000_000;
  }

  _format(value, digits = 2) { return new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: digits, minimumFractionDigits: 0 }).format(value); }

  _updateValues() {
    if (!this._config || !this.shadowRoot) return;
    const precision = { water_level: 2, volume: 2, inflow: 2, outflow: 2, precipitation_24h: 1, air_temperature: 1 };
    const units = Object.fromEntries(VALUE_LABELS.map(([key, _label, unit]) => [key, unit]));
    VALUE_LABELS.forEach(([key]) => {
      const value = this._numericState(key); const target = this.shadowRoot.querySelector(`[data-value="${key}"]`);
      if (value === null) target.textContent = `— ${units[key]}`;
      else if (key === "water_level") target.textContent = `${this._format(this._waterLevelMeters(value), precision[key])} m n. m.`;
      else if (key === "volume") {
        const volume = this._volumeMillionsOfCubicMeters(value);
        target.textContent = volume === null ? `${this._format(value, precision[key])} ${this._unit(key)}` : `${this._format(volume, precision[key])} mil. m³`;
      } else target.textContent = `${this._format(value, precision[key])} ${this._unit(key)}`;
    });
    const measuredAt = this._state("water_level")?.attributes?.measurement_time;
    this.shadowRoot.querySelector("#updated").textContent = measuredAt
      ? `Čas měření PVL: ${new Intl.DateTimeFormat("cs-CZ", { dateStyle: "short", timeStyle: "short" }).format(new Date(measuredAt))}` : "";
    this._updateDifference();
    const waterState = this._state("water_level")?.last_updated;
    if (waterState && waterState !== this._lastWaterState) { this._lastWaterState = waterState; this._loadHistory(); }
  }

  _updateDifference() {
    const target = this.shadowRoot?.querySelector("#difference");
    const rawLevel = this._numericState("water_level");
    const level = rawLevel === null ? null : this._waterLevelMeters(rawLevel);
    const select = this.shadowRoot?.querySelector("#reference-select");
    const reference = this._config.references[Number(select?.value)];
    if (!target || level === null || !reference || !Number.isFinite(Number(reference.level))) { if (target) target.textContent = "—"; return; }
    const difference = level - Number(reference.level);
    const sign = difference > 0 ? "+" : difference < 0 ? "−" : "";
    target.textContent = `${sign}${this._format(Math.abs(difference), 2)} m`;
  }

  async _loadHistory() {
    const chart = this.shadowRoot?.querySelector("#chart");
    const entityId = this._config?.entities?.water_level;
    if (!chart || !this._hass || !entityId) return;
    const requestId = ++this._historyRequestId;
    chart.innerHTML = '<p class="empty">Načítám historii…</p>';
    const end = new Date();
    const start = new Date(end.getTime() - (this._period === "hour" ? 3600000 : 86400000));
    const query = new URLSearchParams({ filter_entity_id: entityId, end_time: end.toISOString(), no_attributes: "1", significant_changes_only: "0" });
    const path = `history/period/${encodeURIComponent(start.toISOString())}?${query}`;
    try {
      const result = await this._hass.callApi("GET", path);
      if (requestId !== this._historyRequestId) return;
      const entries = Array.isArray(result?.[0]) ? result.flat() : result;
      const points = (Array.isArray(entries) ? entries : []).map((entry) => ({
        time: new Date(entry.last_updated || entry.last_changed).getTime(),
        value: this._waterLevelMeters(Number(entry.state)),
      })).filter((point) => Number.isFinite(point.time) && Number.isFinite(point.value));
      this._drawChart(points);
    } catch (_error) {
      if (requestId !== this._historyRequestId) return;
      chart.innerHTML = '<p class="empty">Historii se nepodařilo načíst.</p>';
    }
  }

  _drawChart(points) {
    const chart = this.shadowRoot.querySelector("#chart");
    if (points.length === 0) { chart.innerHTML = '<p class="empty">Pro toto období zatím nejsou v Recorderu žádné hodnoty.</p>'; return; }
    const width = 600, height = 170, padX = 12, padY = 14;
    const values = points.map((point) => point.value);
    let min = Math.min(...values), max = Math.max(...values);
    if (min === max) { min -= 0.05; max += 0.05; }
    const firstTime = points[0].time, lastTime = points[points.length - 1].time;
    const duration = Math.max(1, lastTime - firstTime);
    const coords = points.map((point) => [padX + ((point.time - firstTime) / duration) * (width - padX * 2), height - padY - ((point.value - min) / (max - min)) * (height - padY * 2)]);
    const line = coords.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
    const last = coords[coords.length - 1];
    const timeFormat = new Intl.DateTimeFormat("cs-CZ", { hour: "2-digit", minute: "2-digit" });
    const startLabel = timeFormat.format(new Date(firstTime)), endLabel = timeFormat.format(new Date(lastTime));
    chart.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Vývoj hladiny nádrže Slapy"><line class="grid" x1="${padX}" y1="${height / 2}" x2="${width - padX}" y2="${height / 2}"></line><polyline class="line" points="${line}"></polyline><circle class="point" cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="4"></circle></svg><div class="chart-heading"><span class="empty">${startLabel}</span><span class="empty">${endLabel}</span></div><div class="empty">${this._format(min, 2)}–${this._format(max, 2)} m n. m. · ${points.length} záznamů</div>`;
  }
}

if (!customElements.get("pvl-reservoir-card")) customElements.define("pvl-reservoir-card", PVLReservoirCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "pvl-reservoir-card", name: "PVL Reservoir Monitor", description: "Current measurements and Home Assistant history for Slapy Reservoir.", preview: true });
