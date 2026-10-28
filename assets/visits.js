// Public CounterAPI V2 counters. Never put an API token in this public website.
(() => {
  if (window.siteVisitsStarted) return;
  window.siteVisitsStarted = true;
  const counters = [...document.querySelectorAll("[data-visit-counter]")];
  const legacyReader = new URLSearchParams(location.search).has("note");
  const pathname = location.pathname.replace(/\/index\.html$/, "/");
  const DELAY = 1000;
  const TIMEOUT = 10000;
  const configURL = new URL("counterapi.json", document.currentScript.src);
  const identities = new Map();

  const storedKey = (counter) => `visits:counterapi:${identities.get(counter)}:${counter.dataset.visitCounter}:${counter.dataset.visitCounter === "site" ? "" : pathname}`;
  const remembered = (counter) => {
    try { return Number(localStorage.getItem(storedKey(counter))) || 0; } catch { return 0; }
  };
  const status = (counter, state) => {
    counter.dataset.visitState = state;
    counter.classList[state === "ready" ? "remove" : "add"]("visit-stale");
    let label = counter.querySelector(".visit-status");
    if (!label) {
      label = document.createElement("small");
      label.className = "visit-status";
      counter.append(label);
    }
    label.textContent = state === "ready" ? "" : "（历史记录）";
    counter.title = state === "ready" ? counter.dataset.visitTitle : "尚未取得新统计，显示的是保留的历史记录";
  };
  const show = (counter, total) => {
    const value = counter.querySelector(".visit-value");
    if (value) value.textContent = total > 0 ? total.toLocaleString("zh-CN") : "—";
  };
  for (const counter of counters) {
    if (legacyReader && counter.dataset.visitCounter === "page") { counter.hidden = true; continue; }
    counter.dataset.visitTitle = counter.title;
    show(counter, Number(counter.dataset.visitFloor) || 0);
    status(counter, "pending");
  }
  // Preview pages never send visits. Redirecting old home links must not count twice.
  if (location.hostname !== "phyytang.github.io" || (legacyReader && document.body.classList.contains("home"))) return;

  const fetchJSON = async (url) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT);
    try {
      const response = await fetch(url, {cache: "no-store", credentials: "omit", signal: controller.signal});
      if (!response.ok) throw new Error(`CounterAPI HTTP ${response.status}`);
      return await response.json();
    } finally { clearTimeout(timer); }
  };
  const number = (value) => {
    if (typeof value !== "number" && !(typeof value === "string" && /^\d+$/.test(value))) return NaN;
    const result = Number(value);
    return Number.isSafeInteger(result) && result >= 0 ? result : NaN;
  };
  const countValue = (payload) => {
    if (payload?.code !== undefined && String(payload.code) !== "200") throw new Error("CounterAPI rejected request");
    const data = payload?.data ?? payload;
    let result;
    if (data && Object.hasOwn(data, "up_count")) {
      const up = number(data.up_count), down = number(data.down_count ?? 0);
      result = up - down;
    } else { result = number(data?.count ?? data?.value); }
    if (!Number.isSafeInteger(result) || result < 0) throw new Error("CounterAPI returned no valid count");
    return result;
  };
  const identity = (definition) => {
    const {workspace, name} = definition ?? {};
    if (typeof workspace !== "string" || !workspace.trim() || typeof name !== "string" || !name.trim()) {
      throw new Error("CounterAPI workspace or counter name is missing");
    }
    return `${encodeURIComponent(workspace.trim())}/${encodeURIComponent(name.trim())}`;
  };
  const increment = async (id) => {
    const url = new URL(`https://api.counterapi.dev/v2/${id}/up`);
    // GET /up changes state: bypass shared caches and never automatically retry it.
    url.searchParams.set("_", window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`);
    return countValue(await fetchJSON(url));
  };
  const update = (counter, raw) => {
    const total = Math.max(raw + (Number(counter.dataset.visitOffset) || 0), Number(counter.dataset.visitFloor) || 0, remembered(counter));
    show(counter, total);
    try { localStorage.setItem(storedKey(counter), String(total)); } catch { /* Storage is optional. */ }
    status(counter, "ready");
  };
  const run = async () => {
    const visible = counters.filter((counter) => !counter.hidden);
    try {
      const config = await fetchJSON(configURL);
      const jobs = new Map();
      const add = (definition, targets) => {
        try {
          const id = identity(definition);
          for (const counter of targets) {
            identities.set(counter, id);
            show(counter, Math.max(Number(counter.dataset.visitFloor) || 0, remembered(counter)));
          }
          if (!jobs.has(id)) jobs.set(id, {id, targets: []});
          jobs.get(id).targets.push(...targets);
        } catch { for (const counter of targets) status(counter, "stale"); }
      };
      add(config.site, visible.filter((counter) => counter.dataset.visitCounter === "site"));
      const pages = visible.filter((counter) => counter.dataset.visitCounter === "page");
      if (!legacyReader && config.pages?.[pathname]) add(config.pages[pathname], pages);
      else for (const counter of pages) status(counter, "stale");
      await Promise.allSettled([...jobs.values()].map(async ({id, targets}) => {
        try { const raw = await increment(id); for (const counter of targets) update(counter, raw); }
        catch { for (const counter of targets) status(counter, "stale"); }
      }));
    } catch { for (const counter of visible) status(counter, "stale"); }
  };
  setTimeout(run, DELAY);
})();
