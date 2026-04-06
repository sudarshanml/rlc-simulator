/* global Chart */
(function () {
  const canvas = document.getElementById("sch");
  const ctx = canvas.getContext("2d");
  const statusEl = document.getElementById("status");
  const propsEl = document.getElementById("props");
  const waveCanvas = document.getElementById("wave");

  let chart = null;

  const state = {
    junctions: [
      { id: "j1", x: 140, y: 180, net: "in" },
      { id: "j2", x: 420, y: 180, net: "out" },
      { id: "j3", x: 140, y: 360, net: "0" },
    ],
    branches: [
      { id: "b1", kind: "R", name: "R1", jA: "j1", jB: "j2", value: 1000 },
      { id: "b2", kind: "C", name: "C1", jA: "j2", jB: "j3", value: 1e-6 },
      {
        id: "b3",
        kind: "V",
        name: "V1",
        jA: "j1",
        jB: "j3",
        source: { kind: "STEP", params: [0, 1, 0] },
      },
    ],
    mode: "select",
    selected: null,
    pendingJunction: null,
    drag: null,
    nextJ: 4,
    nextB: 4,
  };

  function setStatus(msg, isErr) {
    statusEl.textContent = msg || "";
    statusEl.classList.toggle("err", !!isErr);
  }

  function junctionById(id) {
    return state.junctions.find((j) => j.id === id);
  }

  function branchById(id) {
    return state.branches.find((b) => b.id === id);
  }

  function nextElementName(letter) {
    let maxN = 0;
    const re = new RegExp("^" + letter + "(\\d+)$", "i");
    for (const b of state.branches) {
      const m = b.name.match(re);
      if (m) maxN = Math.max(maxN, parseInt(m[1], 10));
    }
    return letter + (maxN + 1);
  }

  function parseProbeList() {
    const raw = document.getElementById("probes").value;
    return raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function sourceFromForm() {
    const kind = document.getElementById("srcKind").value;
    if (kind === "DC") {
      const v = parseFloat(document.getElementById("srcDC").value);
      return { kind: "DC", params: [v] };
    }
    if (kind === "STEP") {
      const parts = document
        .getElementById("srcSTEP")
        .value.split(/[,\s]+/)
        .filter(Boolean)
        .map(parseFloat);
      return { kind: "STEP", params: parts };
    }
    const parts = document
      .getElementById("srcPWL")
      .value.split(/[,\s]+/)
      .filter(Boolean)
      .map(parseFloat);
    return { kind: "PWL", params: parts };
  }

  function passiveFromForm() {
    return parseFloat(document.getElementById("passiveVal").value);
  }

  function buildSchematic() {
    return {
      junctions: state.junctions.map((j) => ({
        id: j.id,
        net: j.net,
        x: j.x,
        y: j.y,
      })),
      branches: state.branches.map((b) => {
        const o = {
          id: b.id,
          kind: b.kind,
          name: b.name,
          jA: b.jA,
          jB: b.jB,
        };
        if ("value" in b) o.value = b.value;
        if ("source" in b) o.source = { ...b.source, params: [...b.source.params] };
        return o;
      }),
      probes: parseProbeList(),
    };
  }

  function dist(px, py, qx, qy) {
    const dx = px - qx;
    const dy = py - qy;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function distToSegment(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len2 = dx * dx + dy * dy;
    if (len2 < 1e-12) return dist(px, py, x1, y1);
    let t = ((px - x1) * dx + (py - y1) * dy) / len2;
    t = Math.max(0, Math.min(1, t));
    const nx = x1 + t * dx;
    const ny = y1 + t * dy;
    return dist(px, py, nx, ny);
  }

  function hitJunction(x, y) {
    for (let i = state.junctions.length - 1; i >= 0; i--) {
      const j = state.junctions[i];
      if (dist(x, y, j.x, j.y) <= 14) return j;
    }
    return null;
  }

  function hitBranch(x, y) {
    let best = null;
    let bestD = 10;
    for (const b of state.branches) {
      const a = junctionById(b.jA);
      const c = junctionById(b.jB);
      if (!a || !c) continue;
      const d = distToSegment(x, y, a.x, a.y, c.x, c.y);
      if (d < bestD) {
        bestD = d;
        best = b;
      }
    }
    return best;
  }

  function draw() {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#121820";
    ctx.fillRect(0, 0, w, h);

    ctx.strokeStyle = "#2d3a4f";
    ctx.lineWidth = 1;
    for (let gx = 0; gx < w; gx += 40) {
      ctx.beginPath();
      ctx.moveTo(gx, 0);
      ctx.lineTo(gx, h);
      ctx.stroke();
    }
    for (let gy = 0; gy < h; gy += 40) {
      ctx.beginPath();
      ctx.moveTo(0, gy);
      ctx.lineTo(w, gy);
      ctx.stroke();
    }

    for (const b of state.branches) {
      const a = junctionById(b.jA);
      const c = junctionById(b.jB);
      if (!a || !c) continue;
      const sel =
        state.selected &&
        state.selected.type === "branch" &&
        state.selected.id === b.id;
      ctx.strokeStyle = sel ? "#5b9cf5" : "#8b9cb3";
      ctx.lineWidth = sel ? 3 : 2;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(c.x, c.y);
      ctx.stroke();

      const mx = (a.x + c.x) / 2;
      const my = (a.y + c.y) / 2;
      let label = b.name;
      if (b.kind === "R" || b.kind === "C" || b.kind === "L") {
        label += " " + formatVal(b.value, b.kind);
      }
      ctx.font = "12px system-ui";
      const tw = ctx.measureText(label).width;
      ctx.fillStyle = "#1a2332";
      ctx.fillRect(mx - tw / 2 - 4, my - 18, tw + 8, 18);
      ctx.fillStyle = sel ? "#cde2ff" : "#e8eef5";
      ctx.fillText(label, mx - tw / 2, my - 6);
    }

    for (const j of state.junctions) {
      const sel =
        state.selected &&
        state.selected.type === "junction" &&
        state.selected.id === j.id;
      const gnd = j.net === "0" || j.net.toLowerCase() === "gnd";
      if (gnd) {
        ctx.strokeStyle = sel ? "#5b9cf5" : "#c9d4e5";
        ctx.lineWidth = 2;
        const t = 10;
        ctx.beginPath();
        ctx.moveTo(j.x - t, j.y);
        ctx.lineTo(j.x + t, j.y);
        ctx.moveTo(j.x - t * 0.65, j.y + 5);
        ctx.lineTo(j.x + t * 0.65, j.y + 5);
        ctx.moveTo(j.x - t * 0.35, j.y + 10);
        ctx.lineTo(j.x + t * 0.35, j.y + 10);
        ctx.stroke();
        ctx.fillStyle = "#8b9cb3";
        ctx.font = "11px system-ui";
        ctx.fillText(j.net, j.x + 12, j.y + 4);
      } else {
        ctx.beginPath();
        ctx.arc(j.x, j.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = sel ? "#5b9cf5" : "#2d3a4f";
        ctx.fill();
        ctx.strokeStyle = sel ? "#cde2ff" : "#8b9cb3";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = "#e8eef5";
        ctx.font = "11px system-ui";
        ctx.fillText(j.net, j.x + 12, j.y + 4);
      }
    }

    if (state.pendingJunction) {
      const pj = junctionById(state.pendingJunction);
      if (pj) {
        ctx.strokeStyle = "#5b9cf5";
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 2;
        ctx.strokeRect(pj.x - 16, pj.y - 16, 32, 32);
        ctx.setLineDash([]);
      }
    }
  }

  function formatVal(v, kind) {
    if (kind === "C" || kind === "L") {
      if (Math.abs(v) < 1e-2 || Math.abs(v) >= 1e6)
        return v.toExponential(2);
    }
    if (Math.abs(v) >= 1e6 || (Math.abs(v) < 0.01 && v !== 0))
      return v.toExponential(2);
    return String(v);
  }

  function renderProps() {
    const sel = state.selected;
    if (!sel) {
      propsEl.innerHTML = "Click a node or branch.";
      return;
    }
    if (sel.type === "junction") {
      const j = junctionById(sel.id);
      if (!j) {
        propsEl.innerHTML = "";
        return;
      }
      propsEl.innerHTML = `
        <div><strong>Node</strong> ${escapeHtml(j.id)}</div>
        <label class="field">Net name
          <input type="text" data-prop="jnet" value="${escapeHtml(j.net)}" />
        </label>`;
      propsEl.querySelector("[data-prop=jnet]").addEventListener("input", (e) => {
        j.net = e.target.value.trim() || "n";
        draw();
      });
      return;
    }
    const b = branchById(sel.id);
    if (!b) {
      propsEl.innerHTML = "";
      return;
    }
    if (b.kind === "R" || b.kind === "C" || b.kind === "L") {
      propsEl.innerHTML = `
        <div><strong>${escapeHtml(b.kind)}</strong> ${escapeHtml(b.name)}</div>
        <label class="field">Value
          <input type="text" data-prop="bval" value="${escapeHtml(String(b.value))}" />
        </label>`;
      propsEl.querySelector("[data-prop=bval]").addEventListener("input", (e) => {
        const v = parseFloat(e.target.value);
        if (!Number.isNaN(v)) {
          b.value = v;
          draw();
        }
      });
      return;
    }
    const src = b.source;
    const pstr = src.params.join(", ");
    propsEl.innerHTML = `
      <div><strong>${escapeHtml(b.kind)}</strong> ${escapeHtml(b.name)}</div>
      <label class="field">Source kind
        <select data-prop="skind">
          <option value="DC" ${src.kind === "DC" ? "selected" : ""}>DC</option>
          <option value="STEP" ${src.kind === "STEP" ? "selected" : ""}>STEP</option>
          <option value="PWL" ${src.kind === "PWL" ? "selected" : ""}>PWL</option>
        </select>
      </label>
      <label class="field">Params (comma-separated)
        <input type="text" data-prop="sparams" value="${escapeHtml(pstr)}" />
      </label>`;
    const kindSel = propsEl.querySelector("[data-prop=skind]");
    const parInp = propsEl.querySelector("[data-prop=sparams]");
    function pushSource() {
      const kind = kindSel.value;
      const params = parInp.value
        .split(/[,\s]+/)
        .filter(Boolean)
        .map(parseFloat);
      b.source = { kind, params };
      draw();
    }
    kindSel.addEventListener("change", pushSource);
    parInp.addEventListener("input", pushSource);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function setMode(mode) {
    state.mode = mode;
    state.pendingJunction = null;
    document.querySelectorAll(".tool[data-mode]").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-mode") === mode);
    });
    draw();
  }

  document.querySelectorAll(".tool[data-mode]").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.getAttribute("data-mode")));
  });

  document.querySelector(".tool[data-action=delete]").addEventListener("click", () => {
    deleteSelection();
  });

  function deleteSelection() {
    const sel = state.selected;
    if (!sel) return;
    if (sel.type === "branch") {
      state.branches = state.branches.filter((b) => b.id !== sel.id);
    } else {
      const jid = sel.id;
      state.branches = state.branches.filter(
        (b) => b.jA !== jid && b.jB !== jid
      );
      state.junctions = state.junctions.filter((j) => j.id !== jid);
    }
    state.selected = null;
    state.pendingJunction = null;
    renderProps();
    draw();
  }

  function addJunction(x, y) {
    const id = "j" + state.nextJ++;
    const n = "n" + (state.junctions.length + 1);
    state.junctions.push({ id, x, y, net: n });
    state.selected = { type: "junction", id };
    renderProps();
    draw();
  }

  function tryCompleteBranch(jB) {
    const mode = state.mode;
    if (!state.pendingJunction || state.pendingJunction === jB) return;
    const jA = state.pendingJunction;
    const letter =
      mode === "R"
        ? "R"
        : mode === "C"
          ? "C"
          : mode === "L"
            ? "L"
            : mode === "V"
              ? "V"
              : mode === "I"
                ? "I"
                : "";
    if (!letter) return;
    const name = nextElementName(letter);
    const id = "b" + state.nextB++;
    if (letter === "V" || letter === "I") {
      state.branches.push({
       id,
        kind: letter,
        name,
        jA,
        jB,
        source: sourceFromForm(),
      });
    } else {
      state.branches.push({
        id,
        kind: letter,
        name,
        jA,
        jB,
        value: passiveFromForm(),
      });
    }
    state.pendingJunction = null;
    state.selected = { type: "branch", id };
    renderProps();
    draw();
  }

  function canvasPos(ev) {
    const r = canvas.getBoundingClientRect();
    const scaleX = canvas.width / r.width;
    const scaleY = canvas.height / r.height;
    return {
      x: (ev.clientX - r.left) * scaleX,
      y: (ev.clientY - r.top) * scaleY,
    };
  }

  canvas.addEventListener("mousedown", (ev) => {
    const { x, y } = canvasPos(ev);
    const jHit = hitJunction(x, y);

    if (state.mode === "junction") {
      if (!jHit) addJunction(x, y);
      return;
    }

    if (state.mode === "gnd" && jHit) {
      jHit.net = "0";
      state.selected = { type: "junction", id: jHit.id };
      renderProps();
      draw();
      return;
    }

    if (
      state.mode === "R" ||
      state.mode === "C" ||
      state.mode === "L" ||
      state.mode === "V" ||
      state.mode === "I"
    ) {
      if (jHit) {
        if (!state.pendingJunction) {
          state.pendingJunction = jHit.id;
        } else {
          tryCompleteBranch(jHit.id);
        }
      }
      return;
    }

    // select
    if (jHit) {
      state.drag = { id: jHit.id, startX: x, startY: y, jx: jHit.x, jy: jHit.y };
      state.selected = { type: "junction", id: jHit.id };
      state.pendingJunction = null;
      renderProps();
      draw();
      return;
    }
    const bHit = hitBranch(x, y);
    if (bHit) {
      state.selected = { type: "branch", id: bHit.id };
      state.pendingJunction = null;
      renderProps();
      draw();
      return;
    }
    state.selected = null;
    state.pendingJunction = null;
    renderProps();
    draw();
  });

  window.addEventListener("mousemove", (ev) => {
    if (!state.drag) return;
    const { x, y } = canvasPos(ev);
    const j = junctionById(state.drag.id);
    if (!j) return;
    j.x = state.drag.jx + (x - state.drag.startX);
    j.y = state.drag.jy + (y - state.drag.startY);
    draw();
  });

  window.addEventListener("mouseup", () => {
    state.drag = null;
  });

  window.addEventListener("keydown", (ev) => {
    if (ev.key === "Delete" || ev.key === "Backspace") {
      if (document.activeElement && document.activeElement.tagName === "INPUT")
        return;
      ev.preventDefault();
      deleteSelection();
    }
  });

  document.getElementById("runBtn").addEventListener("click", async () => {
    setStatus("Running…");
    const tstop = parseFloat(document.getElementById("tstop").value);
    const dt = parseFloat(document.getElementById("dt").value);
    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          schematic: buildSchematic(),
          tstop,
          dt,
        }),
      });
      const data = await res.json();
      if (!data.ok) {
        setStatus(data.error || "Simulation failed", true);
        return;
      }
      setStatus(`Completed ${data.times.length} time points.`);
      renderChart(data.times, data.probes);
    } catch (e) {
      setStatus(String(e), true);
    }
  });

  document.getElementById("netlistBtn").addEventListener("click", async () => {
    setStatus("Exporting…");
    try {
      const res = await fetch("/api/netlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ schematic: buildSchematic() }),
      });
      const data = await res.json();
      if (!data.ok) {
        setStatus(data.error || "Export failed", true);
        return;
      }
      setStatus("Netlist:\n" + data.netlist);
    } catch (e) {
      setStatus(String(e), true);
    }
  });

  function renderChart(times, probes) {
    const labels = times;
    const keys = Object.keys(probes || {});
    if (!keys.length) {
      setStatus("No probe data returned.", true);
      return;
    }
    const palette = [
      "#5b9cf5",
      "#e85d6a",
      "#5bd4a6",
      "#e8b55a",
      "#c78bfc",
      "#7ad0e8",
    ];
    const datasets = keys.map((k, i) => ({
      label: k,
      data: probes[k],
      borderColor: palette[i % palette.length],
      backgroundColor: "transparent",
      tension: 0.1,
      pointRadius: 0,
      borderWidth: 2,
    }));
    if (chart) chart.destroy();
    chart = new Chart(waveCanvas, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { color: "#e8eef5" } },
        },
        scales: {
          x: {
            title: { display: true, text: "time (s)", color: "#8b9cb3" },
            ticks: { color: "#8b9cb3", maxTicksLimit: 8 },
            grid: { color: "rgba(45,58,79,0.5)" },
          },
          y: {
            title: { display: true, text: "voltage (V)", color: "#8b9cb3" },
            ticks: { color: "#8b9cb3" },
            grid: { color: "rgba(45,58,79,0.5)" },
          },
        },
      },
    });
  }

  draw();
  renderProps();
})();
