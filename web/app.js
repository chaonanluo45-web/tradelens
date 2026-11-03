const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const SAMPLE_INQUIRY = `Subject: Inquiry for 50W LED garden light

Dear Supplier,

We are a lighting distributor based in Hamburg, Germany. We need 2,000 pcs 50W IP65 LED garden lights, 3000K, CRI>80, die-cast aluminum. Delivery to Hamburg within 3 weeks. Target price EUR 14.5/pc FOB.

Please send your CE and RoHS certificates, product datasheet and best offer.

Best regards,
Lena Hoffmann
Nordlicht GmbH`;

const CATEGORY_DEFAULT_USD = {
  led_outdoor: 27,
  portable_power: 300,
  smart_home: 17,
  pet: 34,
  tools: 52,
};

const FALLBACK = {
  categories: [
    { key: "led_outdoor", name: "LED 户外庭院灯", short: "户外照明" },
    { key: "portable_power", name: "便携储能电源", short: "便携储能" },
    { key: "smart_home", name: "智能家居传感器", short: "智能家居" },
    { key: "pet", name: "宠物智能用品", short: "宠物智能" },
    { key: "tools", name: "锂电工具", short: "锂电工具" },
  ],
  markets: [
    { key: "DE", name: "德国", currency: "EUR", symbol: "€" },
    { key: "US", name: "美国", currency: "USD", symbol: "$" },
    { key: "AE", name: "阿联酋", currency: "AED", symbol: "AED " },
    { key: "VN", name: "越南", currency: "VND", symbol: "₫" },
    { key: "MX", name: "墨西哥", currency: "MXN", symbol: "MX$" },
  ],
  goals: [
    { key: "trial", name: "试单验证" },
    { key: "distributor", name: "寻找分销商" },
    { key: "brand", name: "品牌出海" },
  ],
};

let OPTIONS = FALLBACK;
let isBusy = false;
let activeReport = null;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[c]));
}

function toast(message, error = false) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.toggle("error", error);
  el.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => el.classList.remove("show"), 2600);
}

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error("服务返回了无法解析的内容");
  }
  if (!res.ok || !data.ok) throw new Error(data.error || "请求失败");
  return data.result;
}

function initSelects() {
  const product = $("#product-select");
  const market = $("#market-select");
  const goal = $("#goal-select");
  product.innerHTML = OPTIONS.categories.map((c) => `<option value="${esc(c.key)}">${esc(c.name)}</option>`).join("");
  market.innerHTML = OPTIONS.markets.map((m) => `<option value="${esc(m.key)}">${esc(m.name)} · ${esc(m.currency)}</option>`).join("");
  goal.innerHTML = OPTIONS.goals.map((g) => `<option value="${esc(g.key)}">${esc(g.name)}</option>`).join("");
  product.value = "led_outdoor";
  market.value = "DE";
  goal.value = "trial";
  syncCurrency(true);
}

function marketOption() {
  return OPTIONS.markets.find((m) => m.key === $("#market-select").value) || OPTIONS.markets[0];
}

function syncCurrency(forcePrice = false) {
  const market = marketOption();
  $("#price-currency").textContent = market.symbol;
  if (forcePrice) {
    const usd = CATEGORY_DEFAULT_USD[$("#product-select").value] || 25;
    const fx = { EUR: 0.92, USD: 1, AED: 3.67, VND: 25400, MXN: 18.2 }[market.currency] || 1;
    let value = usd * fx;
    if (market.currency === "VND") value = Math.round(value / 1000) * 1000;
    else if (market.currency === "MXN") value = Math.round(value);
    else value = Math.round(value * 10) / 10;
    $("#price-input").value = value;
  }
}

function setPipeline(state) {
  $$("#pipeline .pipeline-step").forEach((el) => {
    const step = Number(el.dataset.step);
    el.classList.toggle("done", state === "done" || step < state);
    el.classList.toggle("active", state !== "done" && step === state);
  });
}

async function animatePipeline() {
  for (let step = 1; step <= 5; step += 1) {
    setPipeline(step);
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
}

function setLoading(loading, target = "analysis") {
  const button = target === "analysis" ? $("#analyze-btn") : $("#inquiry-btn");
  button.disabled = loading;
  $(".spinner", button).hidden = !loading;
  $(".btn-label", button).textContent = loading
    ? (target === "analysis" ? "正在分析…" : "正在解析…")
    : (target === "analysis" ? "生成市场简报" : "解析这封询盘");
}

async function runAnalysis({ initial = false } = {}) {
  if (isBusy) return;
  isBusy = true;
  setLoading(true);
  const report = $("#report");
  report.classList.remove("loaded");
  if (!initial) {
    setPipeline(1);
    animatePipeline();
  }
  const payload = {
    category: $("#product-select").value,
    market: $("#market-select").value,
    target_price: Number($("#price-input").value),
    goal: $("#goal-select").value,
  };
  try {
    const started = Date.now();
    const result = await api("/api/analyze", payload);
    if (!initial) {
      const wait = Math.max(0, 850 - (Date.now() - started));
      if (wait) await new Promise((resolve) => setTimeout(resolve, wait));
    }
    setPipeline("done");
    renderReport(result);
    activeReport = result;
    requestAnimationFrame(() => report.classList.add("loaded"));
    if (!initial) toast("市场简报已更新");
  } catch (error) {
    toast(error.message, true);
    setPipeline(1);
  } finally {
    isBusy = false;
    setLoading(false);
  }
}

function renderReport(r) {
  $("#report-title").textContent = `${r.market.name} · ${r.category.name}`;
  $("#report-subtitle").textContent = `面向${r.market.buyer}的${r.input.goal_name}简报 · 目标价 ${formatTarget(r)}`;
  $("#report-time").textContent = `${r.generated_at} 生成`;
  $("#summary").textContent = r.summary;

  const ring = $("#score-ring");
  ring.style.setProperty("--score", r.score);
  $("#score-value").textContent = r.score;
  $("#hero-score").textContent = r.score;
  const badge = $("#score-verdict");
  badge.textContent = r.verdict;
  badge.className = `verdict-badge ${r.level}`;
  $(".hero-stat-foot").innerHTML = `<i></i> ${esc(r.verdict)}`;
  $("#verdict-note").textContent = r.verdict_note;
  $("#verdict-tags").innerHTML = [
    r.market.certs?.[0] || "合规前置",
    r.channels?.[0]?.name || "渠道验证",
    `目标价${r.price_band.position}`,
  ].map((t) => `<span>${esc(t)}</span>`).join("");

  $("#breakdown").innerHTML = r.score_breakdown.map((item) => `
    <div class="break-item">
      <span>${esc(item.label)}</span>
      <div class="break-track"><i style="width:${Number(item.value)}%"></i></div>
      <strong>${esc(item.value)}</strong>
    </div>`).join("");

  $("#metric-grid").innerHTML = r.metrics.map((m) => `
    <div class="metric-card">
      <div class="m-label">${esc(m.label)}</div>
      <strong>${esc(m.value)}</strong>
      <small>${esc(m.hint)}</small>
    </div>`).join("");

  $("#signals").innerHTML = r.signals.map((s) => `
    <div class="signal-card">
      <div class="s-label">${esc(s.label)}</div>
      <strong>${esc(s.value)}</strong>
      <p>${esc(s.detail)}</p>
    </div>`).join("");

  $("#compliance-body").innerHTML = r.compliance.map((row) => `
    <tr><td>${esc(row.item)}</td><td>${esc(row.value)}</td><td>${esc(row.note)}</td></tr>`).join("");

  $("#competitors").innerHTML = r.competitors.map((c) => `
    <div class="competitor"><span>${esc(c.name)}</span><em>${esc(c.price)}</em><p>${esc(c.note)}</p></div>`).join("");

  const band = r.price_band;
  const pct = Math.max(2, Math.min(98, ((band.target - band.low) / (band.high - band.low)) * 100));
  $("#price-marker").style.left = `${pct}%`;
  $("#price-band-label").textContent = `目标价 ${formatTarget(r)}`;
  $("#price-low").textContent = moneyText(band.low, r.market);
  $("#price-high").textContent = moneyText(band.high, r.market);
  $("#price-marker").dataset.position = band.position;

  $("#channels").innerHTML = r.channels.map((c) => `
    <div class="channel-row">
      <div class="channel-top"><strong>${esc(c.name)}</strong><em>${esc(c.fit)}</em></div>
      <div class="channel-bar"><i style="width:${Number(c.fit)}%"></i></div>
    </div>`).join("");

  $("#risks").innerHTML = r.risks.map((risk) => `
    <div class="risk-item ${risk.level === "低" ? "low" : ""}">
      <span class="r-level">${esc(risk.level)}</span>
      <div><strong>${esc(risk.title)}</strong><p>${esc(risk.detail)}</p></div>
    </div>`).join("");

  $("#actions").innerHTML = r.actions.map((a) => `
    <div class="action">
      <span class="a-window">${esc(a.window)}</span>
      <strong>${esc(a.title)}</strong>
      <p>${esc(a.detail)}</p>
    </div>`).join("");

  $("#snapshot").innerHTML = [
    ["目标买家", r.market.buyer],
    ["付款方式", r.market.payment],
    ["物流时效", r.market.logistics],
    ["语言", r.market.language],
    ["HS 编码", r.category.hs],
    ["起订量", r.category.moq],
  ].map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("");

  $("#trace").innerHTML = r.trace.map((t) => `
    <div class="trace-step"><em>${esc(t.step)}</em><div><strong>${esc(t.name)}</strong><p>${esc(t.detail)}</p></div></div>`).join("");

  renderRadar(r.radar);
}

function moneyText(value, market) {
  if (market.currency === "VND") return `${Math.round(value / 1000) * 1000} ₫`;
  if (market.currency === "MXN") return `MX$${Math.round(value).toLocaleString("en-US")}`;
  if (market.currency === "AED") return `AED ${Math.round(value).toLocaleString("en-US")}`;
  if (market.currency === "EUR") return `€${Number(value).toFixed(1)}`;
  return `$${Number(value).toFixed(1)}`;
}

function formatTarget(r) {
  return moneyText(r.input.target_price, r.market);
}

function renderRadar(items) {
  const W = 300, H = 250, cx = 150, cy = 122, R = 82;
  const angles = items.map((_, i) => (-90 + i * 72) * Math.PI / 180);
  const point = (value, i, radius = R) => {
    const r = radius * value / 100;
    return [cx + Math.cos(angles[i]) * r, cy + Math.sin(angles[i]) * r];
  };
  const rings = [25, 50, 75, 100].map((level) => {
    const pts = items.map((_, i) => point(level, i).join(",")).join(" ");
    return `<polygon points="${pts}" fill="none" stroke="#e5ebe1" stroke-width="1"/>`;
  }).join("");
  const axes = items.map((_, i) => {
    const [x, y] = point(100, i);
    return `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#e8ede4" stroke-width="1"/>`;
  }).join("");
  const dataPts = items.map((item, i) => point(item.value, i)).map((p) => p.join(",")).join(" ");
  const dots = items.map((item, i) => {
    const [x, y] = point(item.value, i);
    return `<circle cx="${x}" cy="${y}" r="3" fill="#0f766e" stroke="#fff" stroke-width="1.5"/>`;
  }).join("");
  const labels = items.map((item, i) => {
    const [x, y] = point(122, i);
    const anchor = Math.abs(x - cx) < 8 ? "middle" : (x > cx ? "start" : "end");
    return `<text x="${x}" y="${y + 3}" text-anchor="${anchor}" font-size="9.5" fill="#68766a">${esc(item.label)}</text>
      <text x="${x}" y="${y + 14}" text-anchor="${anchor}" font-size="8" fill="#0f766e" font-family="monospace">${item.value}</text>`;
  }).join("");
  $("#radar").innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="机会雷达：${items.map((i) => `${i.label} ${i.value}`).join("，")}">
      ${rings}${axes}
      <polygon points="${dataPts}" fill="rgba(15,118,110,.16)" stroke="#0f766e" stroke-width="2"/>
      ${dots}${labels}
    </svg>`;
}

function loadSample() {
  $("#inquiry-text").value = SAMPLE_INQUIRY.trim();
  updateCharCount();
}

function updateCharCount() {
  $("#char-count").textContent = `${$("#inquiry-text").value.length} 字符`;
}

async function runInquiry({ initial = false } = {}) {
  const text = $("#inquiry-text").value.trim();
  if (text.length < 20) {
    toast("询盘太短，至少输入 20 个字符", true);
    return;
  }
  setLoading(true, "inquiry");
  try {
    const result = await api("/api/inquiry", { text });
    renderInquiry(result);
    if (!initial) toast("询盘已解析，风险点已标出");
  } catch (error) {
    toast(error.message, true);
  } finally {
    setLoading(false, "inquiry");
  }
}

function renderInquiry(r) {
  $("#inquiry-empty").hidden = true;
  $("#inquiry-result").hidden = false;
  $("#lead-score").textContent = r.lead_score;
  $("#lead-level").textContent = r.lead_level;
  $("#lead-recommended").textContent = r.recommended;

  $("#extracted").innerHTML = r.extracted.map((item) => `
    <div class="extract-item"><span>${esc(item.label)}</span><strong>${esc(item.value)}</strong></div>`).join("");

  $("#benchmark").innerHTML = `
    <svg class="icon"><use href="#i-target"/></svg>
    <span>参考价格带 <strong>${esc(r.benchmark.low)} – ${esc(r.benchmark.high)}</strong>
    ${r.benchmark.target ? `· 客户目标价 <strong>${esc(r.benchmark.target)}</strong>（${esc(r.benchmark.position)}）` : "· 未识别客户目标价"}</span>`;

  $("#flags").innerHTML = r.flags.map((f) => `
    <div class="flag ${esc(f.level)}">
      <i class="flag-dot"></i>
      <div><strong>${esc(f.title)}。</strong><span>${esc(f.detail)}</span></div>
    </div>`).join("");

  $("#reply").textContent = r.reply;
}

async function copyReply() {
  const text = $("#reply").textContent;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    toast("英文回复已复制");
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); toast("英文回复已复制"); }
    catch { toast("复制失败，请手动选择", true); }
    area.remove();
  }
}

function setupNav() {
  const links = $$(".nav-item");
  links.forEach((link) => {
    link.addEventListener("click", () => {
      links.forEach((l) => l.classList.remove("active"));
      link.classList.add("active");
      closeMenu();
    });
  });
  const sections = ["report", "inquiry", "method"].map((id) => document.getElementById(id)).filter(Boolean);
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((l) => l.classList.toggle("active", l.dataset.nav === entry.target.id));
    });
  }, { rootMargin: "-25% 0px -60% 0px", threshold: 0 });
  sections.forEach((section) => observer.observe(section));

  $("#menu-btn").addEventListener("click", (event) => {
    event.stopPropagation();
    const open = !$("#sidebar").classList.contains("open");
    $("#sidebar").classList.toggle("open", open);
    $("#scrim").classList.toggle("show", open);
  });
  $("#scrim").addEventListener("click", closeMenu);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });
}

function closeMenu() {
  $("#sidebar").classList.remove("open");
  $("#scrim").classList.remove("show");
}

function setupEvents() {
  $("#analysis-form").addEventListener("submit", (event) => {
    event.preventDefault();
    runAnalysis();
  });
  ["product-select", "market-select"].forEach((id) => {
    $("#" + id).addEventListener("change", () => syncCurrency(true));
  });
  $("#print-btn").addEventListener("click", () => window.print());
  $("#inquiry-form").addEventListener("submit", (event) => {
    event.preventDefault();
    runInquiry();
  });
  $("#inquiry-text").addEventListener("input", updateCharCount);
  $("#sample-btn").addEventListener("click", () => {
    loadSample();
    runInquiry();
  });
  $("#copy-reply").addEventListener("click", copyReply);
  $("#trace-toggle").addEventListener("click", () => {
    const expanded = $("#trace-toggle").getAttribute("aria-expanded") === "true";
    $("#trace-toggle").setAttribute("aria-expanded", String(!expanded));
    $("#trace").hidden = expanded;
  });
}

async function boot() {
  try {
    const res = await fetch("/api/options");
    const data = await res.json();
    if (data.ok) {
      OPTIONS = {
        categories: data.categories,
        markets: data.markets,
        goals: data.goals,
      };
    }
  } catch {
    $(".status-pill").innerHTML = '<span class="status-dot" style="background:#f59e0b;box-shadow:0 0 0 3px #fef3c7"></span> 演示数据';
  }
  initSelects();
  setupNav();
  setupEvents();
  loadSample();
  await Promise.all([
    runAnalysis({ initial: true }),
    runInquiry({ initial: true }),
  ]);
  document.body.dataset.ready = "true";
}

document.addEventListener("DOMContentLoaded", boot);
