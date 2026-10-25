// Count real visits only on the published site, never in local previews.
(() => {
  const pageCounter = document.getElementById("teaching-visit-count");
  // The teaching catalog counter must not appear in the legacy ?note= reader.
  if (pageCounter && new URLSearchParams(location.search).has("note")) pageCounter.hidden = true;
  const value = document.getElementById("busuanzi_value_site_pv") ||
    (!pageCounter?.hidden && document.getElementById("busuanzi_value_page_pv"));
  const unit = document.getElementById("visit-count-unit");
  if (location.hostname !== "phyytang.github.io" || /[?&]note=/.test(location.search) && document.body.classList.contains("home")) {
    if (value) value.textContent = "—";
    if (unit) unit.hidden = true;
    return;
  }
  if (value) value.textContent = "稍后更新…";
  if (unit) unit.hidden = true;
  const loadCounter = () => {
    let timer;
    let observer;
    const unavailable = () => {
      if (value && !/^[\d,]+$/.test(value.textContent.trim())) {
        value.textContent = "暂不可用";
        if (unit) unit.hidden = true;
      }
    };
    if (value) {
      observer = new MutationObserver(() => {
        const text = value.textContent.trim();
        if (!/^[\d,]+$/.test(text)) return;
        observer.disconnect();
        clearTimeout(timer);
        value.textContent = Number(text.replaceAll(",", "")).toLocaleString("zh-CN");
        if (unit) unit.hidden = false;
      });
      observer.observe(value, {childList: true, characterData: true, subtree: true});
      timer = setTimeout(unavailable, 10000);
    }
    const script = document.createElement("script");
    script.src = "https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
    script.async = true;
    script.onerror = unavailable;
    document.head.append(script);
  };
  // Let readers load the page before contacting the external statistics service.
  setTimeout(loadCounter, 20000);
})();
