(function () {
  "use strict";

  const NUMERIC_FIELDS = new Set([
    "driver_age", "years_licensed", "vehicle_age", "annual_mileage",
    "accidents_last_5yrs", "claims_last_5yrs", "vehicle_value",
    "property_age", "square_footage", "roof_age",
    "fire_station_distance_km", "property_value",
  ]);
  const BOOLEAN_FIELDS = new Set(["urban_area", "security_system", "flood_zone"]);

  function collectPayload(form) {
    const payload = {};
    for (const el of form.elements) {
      if (!el.name) continue;
      if (BOOLEAN_FIELDS.has(el.name)) {
        payload[el.name] = el.checked;
      } else if (NUMERIC_FIELDS.has(el.name)) {
        payload[el.name] = Number(el.value);
      }
    }
    return payload;
  }

  function describeError(detail) {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => {
          const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
          const label = field && field !== "body" ? `${field}: ` : "";
          return `${label}${d.msg}`;
        })
        .join(" · ");
    }
    return "Something went wrong validating that input.";
  }

  function tierClass(tier) {
    return { low: "tier-low", medium: "tier-medium", high: "tier-high" }[tier] || "tier-low";
  }

  function gaugeColor(tier) {
    return (
      { low: "var(--forest)", medium: "var(--ochre)", high: "var(--brick)" }[tier] ||
      "var(--forest)"
    );
  }

  function wireDossier(domain) {
    const form = document.getElementById(`${domain}-form`);
    if (!form) return;
    const resultEl = form.querySelector("[data-result]");
    const errorEl = form.querySelector("[data-error]");
    const stampEl = form.querySelector("[data-tier-stamp]");
    const scoreEl = form.querySelector("[data-score]");
    const gaugeFillEl = form.querySelector("[data-gauge-fill]");
    const premiumEl = form.querySelector("[data-premium]");
    const submitBtn = form.querySelector(".btn-submit");
    const btnLabel = submitBtn.querySelector(".btn-label");
    const btnLoading = submitBtn.querySelector(".btn-loading");

    form.addEventListener("submit", async (evt) => {
      evt.preventDefault();
      errorEl.hidden = true;
      resultEl.hidden = true;
      stampEl.classList.remove("stamp-in", "tier-low", "tier-medium", "tier-high");

      submitBtn.disabled = true;
      btnLabel.hidden = true;
      btnLoading.hidden = false;

      try {
        const resp = await fetch(`/risk/${domain}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(collectPayload(form)),
        });
        const data = await resp.json();

        if (!resp.ok) {
          errorEl.textContent = describeError(data.detail);
          errorEl.hidden = false;
          return;
        }

        scoreEl.textContent = data.risk_score.toFixed(1);
        gaugeFillEl.style.width = `${data.risk_score}%`;
        gaugeFillEl.style.background = gaugeColor(data.risk_tier);
        premiumEl.textContent = `${data.premium_multiplier.toFixed(2)}×`;
        stampEl.textContent = data.risk_tier.toUpperCase();
        stampEl.classList.add(tierClass(data.risk_tier));

        resultEl.hidden = false;
        // restart the stamp animation
        void stampEl.offsetWidth;
        stampEl.classList.add("stamp-in");
      } catch (err) {
        errorEl.textContent = "Couldn't reach the risk service. Is it still running?";
        errorEl.hidden = false;
      } finally {
        submitBtn.disabled = false;
        btnLabel.hidden = false;
        btnLoading.hidden = true;
      }
    });
  }

  async function pingHealth() {
    const dot = document.querySelector("[data-status-dot]");
    const text = document.querySelector("[data-status-text]");
    try {
      const resp = await fetch("/health");
      if (resp.ok) {
        dot.classList.add("ok");
        text.textContent = "System status: operational";
        return;
      }
      throw new Error("bad status");
    } catch {
      dot.classList.add("down");
      text.textContent = "System status: unreachable";
    }
  }

  wireDossier("car");
  wireDossier("home");
  pingHealth();
})();
