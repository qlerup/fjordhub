(function () {
  "use strict";

  var KEY = "fjordhub.whiteboard.v2";
  var PEN_COLORS = ["#e8eaf0", "#60a5fa", "#34d399", "#fbbf24", "#f87171", "#f472b6"];
  var PEN_SIZES = [{ w: 3, dot: 4 }, { w: 6, dot: 7 }, { w: 12, dot: 11 }];
  var NOTE_COLORS = ["#fde68a", "#fbcfe8", "#bfdbfe", "#bbf7d0"];
  var MIN_SCALE = 0.05, MAX_SCALE = 8;

  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
  function clamp(n, lo, hi) { return Math.min(hi, Math.max(lo, n)); }

  // ── Tilstand ───────────────────────────────────────────────────────────────
  function newBoard(name) {
    return { id: uid(), name: name, strokes: [], notes: [], view: { tx: 0, ty: 0, s: 1 } };
  }

  function normalizeBoard(b) {
    return {
      id: b.id || uid(),
      name: typeof b.name === "string" && b.name ? b.name : "Board",
      strokes: Array.isArray(b.strokes) ? b.strokes : [],
      notes: Array.isArray(b.notes) ? b.notes : [],
      view: b.view && typeof b.view.s === "number" ? b.view : { tx: 0, ty: 0, s: 1 }
    };
  }

  function load() {
    try {
      var raw = JSON.parse(localStorage.getItem(KEY));
      if (raw && Array.isArray(raw.boards) && raw.boards.length) {
        var boards = raw.boards.map(normalizeBoard);
        var active = boards.some(function (b) { return b.id === raw.active; }) ? raw.active : boards[0].id;
        return { active: active, boards: boards };
      }
    } catch (err) { /* korrupt data → frisk start */ }
    var first = newBoard("Mit board");
    return { active: first.id, boards: [first] };
  }

  var state = load();
  function board() {
    for (var i = 0; i < state.boards.length; i++) if (state.boards[i].id === state.active) return state.boards[i];
    return state.boards[0];
  }

  // ── DOM ────────────────────────────────────────────────────────────────────
  function $(id) { return document.getElementById(id); }
  var stage = $("wbStage"), canvas = $("wbCanvas"), notesEl = $("wbNotes"),
      boardsEl = $("wbBoards"), savedEl = $("wbSaved");
  if (!stage) return;
  var ctx = canvas.getContext("2d");

  var dpr = window.devicePixelRatio || 1;
  var stageRect = { left: 0, top: 0 };
  var stageW = 0, stageH = 0;

  var tool = "pen";
  var penColor = PEN_COLORS[1];
  var penSize = PEN_SIZES[1].w;
  var spaceHeld = false, stageHover = false;
  var zTop = 10;

  // ── Gem ────────────────────────────────────────────────────────────────────
  var flashTimer = null, saveTimer = null;
  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
      savedEl.classList.add("is-flash");
      clearTimeout(flashTimer);
      flashTimer = setTimeout(function () { savedEl.classList.remove("is-flash"); }, 900);
      refreshActiveMeta();
    } catch (err) {
      savedEl.textContent = "Kunne ikke gemme – lager fuldt";
    }
  }
  function saveSoon() { clearTimeout(saveTimer); saveTimer = setTimeout(save, 500); }

  // ── Viewport ───────────────────────────────────────────────────────────────
  function toWorld(px, py) {
    var bv = board().view;
    return { x: (px - bv.tx) / bv.s, y: (py - bv.ty) / bv.s };
  }

  function withTransform(fn) {
    var bv = board().view;
    ctx.setTransform(dpr * bv.s, 0, 0, dpr * bv.s, dpr * bv.tx, dpr * bv.ty);
    fn();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  function applyView() {
    var bv = board().view;
    notesEl.style.transform = "translate(" + bv.tx + "px, " + bv.ty + "px) scale(" + bv.s + ")";
    var sp = 28 * bv.s;
    while (sp < 16) sp *= 2;
    while (sp > 64) sp /= 2;
    stage.style.backgroundImage = "radial-gradient(circle, rgba(232,234,240,.08) 1px, transparent 1.4px)";
    stage.style.backgroundSize = sp + "px " + sp + "px";
    stage.style.backgroundPosition = bv.tx + "px " + bv.ty + "px";
    $("wbZoomReset").textContent = Math.round(bv.s * 100) + "%";
    redraw();
  }

  function zoomAt(px, py, factor) {
    var bv = board().view;
    var ns = clamp(bv.s * factor, MIN_SCALE, MAX_SCALE);
    if (ns === bv.s) return;
    var wx = (px - bv.tx) / bv.s, wy = (py - bv.ty) / bv.s;
    bv.s = ns;
    bv.tx = px - wx * ns;
    bv.ty = py - wy * ns;
    applyView();
    saveSoon();
  }

  // ── Tegning ────────────────────────────────────────────────────────────────
  function setStrokeStyle(stroke) {
    ctx.globalCompositeOperation = stroke.erase ? "destination-out" : "source-over";
    ctx.strokeStyle = stroke.color;
    ctx.fillStyle = stroke.color;
    ctx.lineWidth = stroke.size;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
  }

  function paintStroke(stroke) {
    setStrokeStyle(stroke);
    var p = stroke.pts;
    if (p.length === 1) {
      ctx.beginPath();
      ctx.arc(p[0][0], p[0][1], stroke.size / 2, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.moveTo(p[0][0], p[0][1]);
      for (var i = 1; i < p.length - 1; i++) {
        ctx.quadraticCurveTo(p[i][0], p[i][1], (p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2);
      }
      ctx.lineTo(p[p.length - 1][0], p[p.length - 1][1]);
      ctx.stroke();
    }
    ctx.globalCompositeOperation = "source-over";
  }

  function redraw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    var bv = board().view;
    var wx0 = -bv.tx / bv.s, wy0 = -bv.ty / bv.s;
    var wx1 = (stageW - bv.tx) / bv.s, wy1 = (stageH - bv.ty) / bv.s;
    withTransform(function () {
      board().strokes.forEach(function (stroke) {
        var bb = stroke.bb;
        if (bb && (bb[2] < wx0 || bb[0] > wx1 || bb[3] < wy0 || bb[1] > wy1)) return;
        paintStroke(stroke);
      });
    });
  }

  function resize() {
    var r = stage.getBoundingClientRect();
    stageRect = r;
    stageW = r.width;
    stageH = r.height;
    dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.height * dpr);
    redraw();
  }
  new ResizeObserver(resize).observe(stage);

  // ── Pointer-håndtering (tegn / pan / pinch) ────────────────────────────────
  var pointers = new Map();
  var mode = null;
  var cur = null, drawPrev = null, drawMid = null;
  var panPrev = null, pinchPrev = null;

  function sx(e) { return e.clientX - stageRect.left; }
  function sy(e) { return e.clientY - stageRect.top; }

  function abortStroke() {
    if (cur) { cur = null; drawMid = null; redraw(); }
  }

  function eraserWidth() { return penSize * 3.5; }

  stage.addEventListener("pointerdown", function (e) {
    if (e.target.closest(".wb-note")) return;
    stageRect = stage.getBoundingClientRect();
    stage.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: sx(e), y: sy(e) });

    if (pointers.size === 2) {
      abortStroke();
      mode = "pinch";
      pinchPrev = null;
      stage.classList.remove("is-panning");
      return;
    }
    if (pointers.size > 2) return;
    if (e.button !== 0 && e.button !== 1) return;

    if (tool === "hand" || spaceHeld || e.button === 1) {
      e.preventDefault();
      mode = "pan";
      panPrev = { x: sx(e), y: sy(e) };
      stage.classList.add("is-panning");
      return;
    }

    mode = "draw";
    var w = toWorld(sx(e), sy(e));
    cur = {
      color: penColor,
      size: tool === "eraser" ? eraserWidth() : penSize,
      erase: tool === "eraser",
      pts: [[Math.round(w.x * 100) / 100, Math.round(w.y * 100) / 100]],
      bb: [w.x, w.y, w.x, w.y]
    };
    drawPrev = w;
    drawMid = null;
    withTransform(function () { paintStroke(cur); });
  });

  stage.addEventListener("pointermove", function (e) {
    if (!pointers.has(e.pointerId)) return;
    var p = { x: sx(e), y: sy(e) };
    pointers.set(e.pointerId, p);

    if (mode === "pinch") {
      if (pointers.size < 2) return;
      var pts = [];
      pointers.forEach(function (v) { pts.push(v); });
      var d = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) || 1;
      var mx = (pts[0].x + pts[1].x) / 2, my = (pts[0].y + pts[1].y) / 2;
      if (pinchPrev) {
        var bv = board().view;
        var ns = clamp(bv.s * (d / pinchPrev.d), MIN_SCALE, MAX_SCALE);
        var wx = (pinchPrev.mx - bv.tx) / bv.s, wy = (pinchPrev.my - bv.ty) / bv.s;
        bv.s = ns;
        bv.tx = mx - wx * ns;
        bv.ty = my - wy * ns;
        applyView();
      }
      pinchPrev = { d: d, mx: mx, my: my };
      return;
    }

    if (mode === "pan" && panPrev) {
      var bv2 = board().view;
      bv2.tx += p.x - panPrev.x;
      bv2.ty += p.y - panPrev.y;
      panPrev = p;
      applyView();
      return;
    }

    if (mode === "draw" && cur) {
      var w = toWorld(p.x, p.y);
      var bv3 = board().view;
      if (Math.hypot(w.x - drawPrev.x, w.y - drawPrev.y) < 1.4 / bv3.s) return;
      var mid = { x: (drawPrev.x + w.x) / 2, y: (drawPrev.y + w.y) / 2 };
      withTransform(function () {
        setStrokeStyle(cur);
        ctx.beginPath();
        if (!drawMid) {
          ctx.moveTo(cur.pts[0][0], cur.pts[0][1]);
          ctx.lineTo(mid.x, mid.y);
        } else {
          ctx.moveTo(drawMid.x, drawMid.y);
          ctx.quadraticCurveTo(drawPrev.x, drawPrev.y, mid.x, mid.y);
        }
        ctx.stroke();
        ctx.globalCompositeOperation = "source-over";
      });
      drawMid = mid;
      cur.pts.push([Math.round(w.x * 100) / 100, Math.round(w.y * 100) / 100]);
      cur.bb[0] = Math.min(cur.bb[0], w.x);
      cur.bb[1] = Math.min(cur.bb[1], w.y);
      cur.bb[2] = Math.max(cur.bb[2], w.x);
      cur.bb[3] = Math.max(cur.bb[3], w.y);
      drawPrev = w;
    }
  });

  function endPointer(e, cancelled) {
    if (!pointers.has(e.pointerId)) return;
    pointers.delete(e.pointerId);

    if (mode === "pinch") {
      if (pointers.size < 2) { mode = null; pinchPrev = null; saveSoon(); }
      return;
    }
    if (mode === "pan") {
      mode = null;
      panPrev = null;
      stage.classList.remove("is-panning");
      saveSoon();
      return;
    }
    if (mode === "draw") {
      mode = null;
      if (!cur) return;
      if (cancelled) { abortStroke(); return; }
      if (drawMid) {
        var last = cur.pts[cur.pts.length - 1];
        withTransform(function () {
          setStrokeStyle(cur);
          ctx.beginPath();
          ctx.moveTo(drawMid.x, drawMid.y);
          ctx.lineTo(last[0], last[1]);
          ctx.stroke();
          ctx.globalCompositeOperation = "source-over";
        });
      }
      var pad = cur.size / 2 + 1;
      cur.bb = [cur.bb[0] - pad, cur.bb[1] - pad, cur.bb[2] + pad, cur.bb[3] + pad];
      board().strokes.push(cur);
      cur = null;
      drawMid = null;
      save();
    }
  }

  stage.addEventListener("pointerup", function (e) { endPointer(e, false); });
  stage.addEventListener("pointercancel", function (e) { endPointer(e, true); });

  stage.addEventListener("wheel", function (e) {
    e.preventDefault();
    stageRect = stage.getBoundingClientRect();
    zoomAt(sx(e), sy(e), Math.exp(-e.deltaY * 0.0012));
  }, { passive: false });

  stage.addEventListener("pointerenter", function () { stageHover = true; });
  stage.addEventListener("pointerleave", function () { stageHover = false; });

  // ── Værktøjer ──────────────────────────────────────────────────────────────
  function setTool(next) {
    tool = next;
    $("wbTools").querySelectorAll(".wb-tool").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.dataset.tool === next);
    });
    stage.classList.toggle("is-hand", next === "hand");
  }

  $("wbTools").addEventListener("click", function (e) {
    var btn = e.target.closest("[data-tool]");
    if (btn) setTool(btn.dataset.tool);
  });

  var colorsEl = $("wbColors");
  PEN_COLORS.forEach(function (color) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "wb-swatch" + (color === penColor ? " is-active" : "");
    b.style.setProperty("--sw", color);
    b.setAttribute("aria-label", "Farve " + color);
    b.addEventListener("click", function () {
      penColor = color;
      colorsEl.querySelectorAll(".wb-swatch").forEach(function (s) { s.classList.toggle("is-active", s === b); });
      if (tool !== "pen") setTool("pen");
    });
    colorsEl.appendChild(b);
  });

  var sizesEl = $("wbSizes");
  PEN_SIZES.forEach(function (size, i) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "wb-size" + (size.w === penSize ? " is-active" : "");
    b.setAttribute("aria-label", "Stregtykkelse " + size.w);
    var dot = document.createElement("i");
    dot.style.width = size.dot + "px";
    dot.style.height = size.dot + "px";
    b.appendChild(dot);
    b.addEventListener("click", function () {
      penSize = size.w;
      sizesEl.querySelectorAll(".wb-size").forEach(function (s) { s.classList.toggle("is-active", s === b); });
    });
    sizesEl.appendChild(b);
  });

  var noteColorsEl = $("wbNoteColors");
  NOTE_COLORS.forEach(function (color) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "wb-note-swatch";
    b.style.setProperty("--sw", color);
    b.setAttribute("aria-label", "Ny note");
    b.addEventListener("click", function () { addNote(color); });
    noteColorsEl.appendChild(b);
  });

  $("wbZoomIn").addEventListener("click", function () { zoomAt(stageW / 2, stageH / 2, 1.25); });
  $("wbZoomOut").addEventListener("click", function () { zoomAt(stageW / 2, stageH / 2, 0.8); });
  $("wbZoomReset").addEventListener("click", function () {
    zoomAt(stageW / 2, stageH / 2, 1 / board().view.s);
  });

  $("wbUndo").addEventListener("click", undo);
  function undo() {
    if (board().strokes.length) {
      board().strokes.pop();
      redraw();
      save();
    }
  }

  var clearBtn = $("wbClear"), clearTimer = null;
  clearBtn.addEventListener("click", function () {
    if (!clearBtn.classList.contains("is-arm")) {
      clearBtn.classList.add("is-arm");
      clearBtn.title = "Sikker? Klik igen for at rydde";
      clearTimer = setTimeout(function () {
        clearBtn.classList.remove("is-arm");
        clearBtn.title = "Ryd board";
      }, 2500);
      return;
    }
    clearTimeout(clearTimer);
    clearBtn.classList.remove("is-arm");
    clearBtn.title = "Ryd board";
    board().strokes = [];
    board().notes = [];
    redraw();
    renderNotes();
    save();
  });

  document.addEventListener("keydown", function (e) {
    var editing = e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable);
    if (e.code === "Space" && !editing) {
      if (stageHover) e.preventDefault();
      if (!spaceHeld) { spaceHeld = true; stage.classList.add("is-hand"); }
      return;
    }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !editing) {
      e.preventDefault();
      undo();
    }
  });

  document.addEventListener("keyup", function (e) {
    if (e.code === "Space") {
      spaceHeld = false;
      if (tool !== "hand") stage.classList.remove("is-hand");
    }
  });

  // ── Sticky notes ───────────────────────────────────────────────────────────
  var openPalette = null;

  function closePalette() {
    if (openPalette) {
      openPalette.classList.remove("is-open");
      openPalette = null;
    }
  }

  document.addEventListener("pointerdown", function (e) {
    if (openPalette && !e.target.closest(".wb-note-palette, .wb-note-grip")) closePalette();
  });

  function bringFront(n, el) {
    el.style.zIndex = ++zTop;
    var list = board().notes;
    var idx = list.indexOf(n);
    if (idx > -1 && idx !== list.length - 1) {
      list.splice(idx, 1);
      list.push(n);
      saveSoon();
    }
  }

  function noteEl(n) {
    var el = document.createElement("div");
    el.className = "wb-note";
    el.style.left = n.x + "px";
    el.style.top = n.y + "px";
    el.style.width = n.w + "px";
    el.style.height = n.h + "px";
    el.style.background = n.color;
    el.style.transform = "rotate(" + (n.tilt || 0) + "deg)";
    el.style.zIndex = ++zTop;

    var bar = document.createElement("div");
    bar.className = "wb-note-bar";
    var grip = document.createElement("button");
    grip.type = "button";
    grip.className = "wb-note-grip";
    grip.setAttribute("aria-label", "Skift farve");
    grip.title = "Skift farve";
    for (var i = 0; i < 3; i++) grip.appendChild(document.createElement("i"));
    bar.appendChild(grip);

    var palette = document.createElement("div");
    palette.className = "wb-note-palette";
    NOTE_COLORS.forEach(function (color) {
      var swatch = document.createElement("button");
      swatch.type = "button";
      swatch.className = "wb-note-palette-swatch";
      swatch.style.setProperty("--sw", color);
      swatch.setAttribute("aria-label", "Farve");
      swatch.addEventListener("click", function (e) {
        e.stopPropagation();
        n.color = color;
        el.style.background = color;
        palette.querySelectorAll(".wb-note-palette-swatch").forEach(function (s) {
          s.classList.toggle("is-active", s === swatch);
        });
        closePalette();
        save();
      });
      palette.appendChild(swatch);
    });

    grip.addEventListener("click", function (e) {
      e.stopPropagation();
      if (openPalette === palette) { closePalette(); return; }
      closePalette();
      palette.querySelectorAll(".wb-note-palette-swatch").forEach(function (s) {
        s.classList.toggle("is-active", s.style.getPropertyValue("--sw").trim() === n.color);
      });
      palette.classList.add("is-open");
      openPalette = palette;
    });
    var del = document.createElement("button");
    del.type = "button";
    del.className = "wb-note-del";
    del.textContent = "×";
    del.setAttribute("aria-label", "Slet note");
    bar.appendChild(del);
    el.appendChild(bar);
    el.appendChild(palette);

    var text = document.createElement("div");
    text.className = "wb-note-text";
    text.contentEditable = "true";
    text.spellcheck = false;
    text.textContent = n.text || "";
    el.appendChild(text);

    var handle = document.createElement("div");
    handle.className = "wb-note-resize";
    el.appendChild(handle);

    el.addEventListener("pointerdown", function () { bringFront(n, el); });

    del.addEventListener("click", function () {
      board().notes = board().notes.filter(function (x) { return x.id !== n.id; });
      el.remove();
      save();
    });

    text.addEventListener("input", function () {
      n.text = text.innerText;
      saveSoon();
    });

    bar.addEventListener("pointerdown", function (e) {
      if (e.target.closest(".wb-note-del, .wb-note-grip, .wb-note-palette")) return;
      e.preventDefault();
      e.stopPropagation();
      bar.setPointerCapture(e.pointerId);
      el.classList.add("is-lifted");
      var start = { x: e.clientX, y: e.clientY, nx: n.x, ny: n.y };
      function mv(ev) {
        var s = board().view.s;
        n.x = start.nx + (ev.clientX - start.x) / s;
        n.y = start.ny + (ev.clientY - start.y) / s;
        el.style.left = n.x + "px";
        el.style.top = n.y + "px";
      }
      function up() {
        bar.removeEventListener("pointermove", mv);
        bar.removeEventListener("pointerup", up);
        bar.removeEventListener("pointercancel", up);
        el.classList.remove("is-lifted");
        save();
      }
      bar.addEventListener("pointermove", mv);
      bar.addEventListener("pointerup", up);
      bar.addEventListener("pointercancel", up);
    });

    handle.addEventListener("pointerdown", function (e) {
      e.preventDefault();
      e.stopPropagation();
      handle.setPointerCapture(e.pointerId);
      var start = { x: e.clientX, y: e.clientY, nw: n.w, nh: n.h };
      function mv(ev) {
        var s = board().view.s;
        n.w = Math.max(140, start.nw + (ev.clientX - start.x) / s);
        n.h = Math.max(110, start.nh + (ev.clientY - start.y) / s);
        el.style.width = n.w + "px";
        el.style.height = n.h + "px";
      }
      function up() {
        handle.removeEventListener("pointermove", mv);
        handle.removeEventListener("pointerup", up);
        handle.removeEventListener("pointercancel", up);
        save();
      }
      handle.addEventListener("pointermove", mv);
      handle.addEventListener("pointerup", up);
      handle.addEventListener("pointercancel", up);
    });

    return el;
  }

  function renderNotes() {
    notesEl.innerHTML = "";
    board().notes.forEach(function (n) { notesEl.appendChild(noteEl(n)); });
  }

  function addNote(color) {
    var c = toWorld(stageW / 2, stageH / 2);
    var n = {
      id: uid(),
      x: c.x - 110 + (Math.random() * 80 - 40),
      y: c.y - 90 + (Math.random() * 60 - 30),
      w: 220,
      h: 180,
      color: color,
      text: "",
      tilt: Math.round((Math.random() * 3 - 1.5) * 10) / 10
    };
    board().notes.push(n);
    var el = noteEl(n);
    notesEl.appendChild(el);
    save();
    el.querySelector(".wb-note-text").focus();
  }

  // ── Boards (sidebar-liste) ────────────────────────────────────────────────
  var PENCIL_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>';

  function boardMeta(b) {
    var notes = b.notes.length === 1 ? "1 note" : b.notes.length + " noter";
    var strokes = b.strokes.length === 1 ? "1 streg" : b.strokes.length + " streger";
    return notes + " · " + strokes;
  }

  function refreshActiveMeta() {
    var meta = boardsEl.querySelector(".wb-board.is-active .wb-board-meta");
    if (meta) meta.textContent = boardMeta(board());
  }

  function switchBoard(id) {
    if (id === state.active) return;
    state.active = id;
    renderBoards();
    renderNotes();
    applyView();
    save();
  }

  function startRename(b, nameSpan) {
    var input = document.createElement("input");
    input.type = "text";
    input.className = "wb-tab-rename";
    input.value = b.name;
    input.maxLength = 40;
    nameSpan.replaceWith(input);
    input.focus();
    input.select();
    var done = false;
    function commit(cancel) {
      if (done) return;
      done = true;
      if (!cancel) {
        var value = input.value.trim();
        if (value) b.name = value;
        save();
      }
      renderBoards();
    }
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") commit(false);
      if (e.key === "Escape") commit(true);
      e.stopPropagation();
    });
    input.addEventListener("blur", function () { commit(false); });
  }

  function renderBoards() {
    boardsEl.innerHTML = "";
    state.boards.forEach(function (b) {
      var row = document.createElement("div");
      row.className = "wb-board" + (b.id === state.active ? " is-active" : "");
      row.setAttribute("role", "button");
      row.tabIndex = 0;

      var name = document.createElement("span");
      name.className = "wb-board-name";
      name.textContent = b.name;
      row.appendChild(name);

      var meta = document.createElement("span");
      meta.className = "wb-board-meta";
      meta.textContent = boardMeta(b);
      row.appendChild(meta);

      var actions = document.createElement("span");
      actions.className = "wb-board-actions";

      var ren = document.createElement("button");
      ren.type = "button";
      ren.className = "wb-tab-action";
      ren.setAttribute("aria-label", "Omdøb board");
      ren.title = "Omdøb";
      ren.innerHTML = PENCIL_SVG;
      ren.addEventListener("click", function (e) {
        e.stopPropagation();
        if (b.id !== state.active) switchBoard(b.id);
        startRename(b, row.querySelector(".wb-board-name") || name);
      });
      actions.appendChild(ren);

      if (state.boards.length > 1) {
        var del = document.createElement("button");
        del.type = "button";
        del.className = "wb-tab-action";
        del.setAttribute("aria-label", "Slet board");
        del.title = "Slet board";
        del.textContent = "×";
        var armTimer = null;
        del.addEventListener("click", function (e) {
          e.stopPropagation();
          if (!del.classList.contains("is-arm")) {
            del.classList.add("is-arm");
            del.textContent = "Slet?";
            armTimer = setTimeout(function () {
              del.classList.remove("is-arm");
              del.textContent = "×";
            }, 2500);
            return;
          }
          clearTimeout(armTimer);
          state.boards = state.boards.filter(function (x) { return x.id !== b.id; });
          if (state.active === b.id) state.active = state.boards[0].id;
          renderBoards();
          renderNotes();
          applyView();
          save();
        });
        actions.appendChild(del);
      }
      row.appendChild(actions);

      row.addEventListener("click", function (e) {
        if (e.target.closest(".wb-tab-action, .wb-tab-rename")) return;
        switchBoard(b.id);
      });
      row.addEventListener("dblclick", function (e) {
        if (e.target.closest(".wb-tab-action, .wb-tab-rename")) return;
        if (b.id === state.active) startRename(b, row.querySelector(".wb-board-name") || name);
      });
      row.addEventListener("keydown", function (e) {
        if ((e.key === "Enter" || e.key === " ") && e.target === row) {
          e.preventDefault();
          switchBoard(b.id);
        }
      });
      boardsEl.appendChild(row);
    });
  }

  $("wbAddBoard").addEventListener("click", function () {
    var b = newBoard("Board " + (state.boards.length + 1));
    state.boards.push(b);
    state.active = b.id;
    renderBoards();
    renderNotes();
    applyView();
    save();
  });

  // ── Start ──────────────────────────────────────────────────────────────────
  resize();
  renderBoards();
  renderNotes();
  applyView();
})();
