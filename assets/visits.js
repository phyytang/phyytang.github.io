// Page-view counters, backed by 不蒜子 (busuanzi.ibruce.info).
//
// Markup: <span data-visit-counter="site|page" data-visit-offset="0" data-visit-floor="0">
//           …<span class="visit-value">…</span>…</span>
//   site   — page views of the whole site (all pages that load this script)
//   page   — page views of this URL only
//   offset — added to the live number (views recorded before a page moved to this URL)
//   floor  — the number is never shown below this (last known total before an outage)
//
// The view is recorded 1 second after the page opens; the request is asynchronous and
// never blocks reading. If the service is slow or down, the counter keeps showing the
// last known total instead of an error, and updates whenever an answer arrives.
(() => {
  const counters = [...document.querySelectorAll("[data-visit-counter]")];
  const legacyReader = new URLSearchParams(location.search).has("note");
  const published = location.hostname === "phyytang.github.io";
  const DELAY = 1000;     // count a view after the page has been open for 1 s
  const TIMEOUT = 15000;  // then wait this long for an answer before dimming the number

  const storageKey = (counter) => `visits:${counter.dataset.visitCounter}:${counter.dataset.visitCounter === "site" ? "" : location.pathname}`;
  const remembered = (counter) => {
    try { return Number(localStorage.getItem(storageKey(counter))) || 0; } catch { return 0; }
  };
  const remember = (counter, total) => {
    try { localStorage.setItem(storageKey(counter), String(total)); } catch { /* private mode */ }
  };

  const show = (counter, total) => {
    const value = counter.querySelector(".visit-value");
    if (value) value.textContent = total > 0 ? total.toLocaleString("zh-CN") : "—";
  };
  const markStale = (counter) => {
    counter.classList.add("visit-stale");
    counter.title = "统计服务暂时没有响应，显示的是最近一次记录的数字";
  };

  for (const counter of counters) {
    // Page counters belong to their own page, not to the legacy ?note= reader.
    if (legacyReader && counter.dataset.visitCounter === "page") { counter.hidden = true; continue; }
    counter.dataset.visitTitle = counter.title;
    const floor = Number(counter.dataset.visitFloor) || 0;
    const known = Math.max(floor, remembered(counter));
    show(counter, known);
  }
  // Local previews never count. Every published page counts toward the site total,
  // including pages that show no counter themselves.
  if (!published) return;

  const callback = `visitsCallback_${Math.floor(Math.random() * 1e12)}`;
  const script = document.createElement("script");
  let answered = false;
  const giveUp = () => {
    if (answered) return;
    for (const counter of counters) if (!counter.hidden) markStale(counter);
  };
  window[callback] = (data) => {
    answered = true;
    for (const counter of counters) {
      if (counter.hidden) continue;
      const raw = Number(data?.[`${counter.dataset.visitCounter}_pv`]);
      if (!Number.isFinite(raw) || raw <= 0) continue;
      const offset = Number(counter.dataset.visitOffset) || 0;
      const floor = Number(counter.dataset.visitFloor) || 0;
      const total = Math.max(raw + offset, floor, remembered(counter));
      remember(counter, total);
      show(counter, total);
      counter.classList.remove("visit-stale");
      counter.title = counter.dataset.visitTitle;
    }
    script.remove();
    delete window[callback];
  };
  script.src = `https://busuanzi.ibruce.info/busuanzi?jsonpCallback=${callback}`;
  // 不蒜子 identifies the page from the Referer header, so send the full URL.
  script.referrerPolicy = "no-referrer-when-downgrade";
  script.async = true;
  script.onerror = giveUp;
  setTimeout(() => {
    document.head.append(script);
    setTimeout(giveUp, TIMEOUT);
  }, DELAY);
})();
