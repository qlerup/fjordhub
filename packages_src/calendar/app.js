(function () {
  "use strict";

  var KEY = "fjordhub.calendar.v2";
  var MONTHS = ["januar", "februar", "marts", "april", "maj", "juni", "juli", "august", "september", "oktober", "november", "december"];
  var WEEKDAYS = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"];
  var ICAL_PALETTE = ["#06b6d4", "#f97316", "#84cc16", "#ec4899", "#eab308", "#38bdf8", "#a3e635"];
  var USER_COLOR = "#8b5cf6";
  var MAX_CHIPS = 3;
  var MAX_ICAL_EVENTS = 2000;

  // ── Storage ────────────────────────────────────────────────────────────────
  function load() {
    try {
      var raw = JSON.parse(localStorage.getItem(KEY));
      if (raw && typeof raw === "object") {
        return {
          holidays: raw.holidays && typeof raw.holidays === "object" ? raw.holidays : { dk: true },
          icals: Array.isArray(raw.icals) ? raw.icals : [],
          events: raw.events && typeof raw.events === "object" ? raw.events : {}
        };
      }
    } catch (err) { /* korrupt data → frisk start */ }
    return { holidays: { dk: true }, icals: [], events: {} };
  }

  var data = load();

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (err) { /* kvote opbrugt */ }
  }

  // ── Dato-hjælpere ──────────────────────────────────────────────────────────
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  function keyOf(y, m, d) { return y + "-" + pad(m + 1) + "-" + pad(d); }
  function keyOfDate(dt) { return keyOf(dt.getFullYear(), dt.getMonth(), dt.getDate()); }
  function addDays(dt, n) { var c = new Date(dt); c.setDate(c.getDate() + n); return c; }

  function easter(y) {
    var a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4,
        f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30,
        i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7,
        m = Math.floor((a + 11 * h + 22 * l) / 451),
        month = Math.floor((h + l - 7 * m + 114) / 31), day = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(y, month - 1, day);
  }

  function nthWeekday(y, m, weekday, n) {
    var first = new Date(y, m, 1);
    var offset = (weekday - first.getDay() + 7) % 7;
    return new Date(y, m, 1 + offset + (n - 1) * 7);
  }

  function lastWeekday(y, m, weekday) {
    var last = new Date(y, m + 1, 0);
    var offset = (last.getDay() - weekday + 7) % 7;
    return new Date(y, m, last.getDate() - offset);
  }

  function weekdayBetween(y, m, dFrom, dTo, weekday) {
    for (var d = dFrom; d <= dTo; d++) {
      var dt = new Date(y, m, d);
      if (dt.getDay() === weekday) return dt;
    }
    return new Date(y, m, dFrom);
  }

  function isoWeek(dt) {
    var t = new Date(Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate()));
    var day = (t.getUTCDay() + 6) % 7;
    t.setUTCDate(t.getUTCDate() - day + 3);
    var firstThu = new Date(Date.UTC(t.getUTCFullYear(), 0, 4));
    var fday = (firstThu.getUTCDay() + 6) % 7;
    firstThu.setUTCDate(firstThu.getUTCDate() - fday + 3);
    return 1 + Math.round((t - firstThu) / (7 * 864e5));
  }

  // ── Helligdags-kalendere ───────────────────────────────────────────────────
  var HOLIDAY_SETS = [
    { id: "dk", name: "Danmark", flag: "🇩🇰", color: "#ef4444", build: function (y) {
      var E = easter(y);
      var list = [
        [new Date(y, 0, 1), "Nytårsdag"],
        [addDays(E, -3), "Skærtorsdag"], [addDays(E, -2), "Langfredag"],
        [E, "Påskedag"], [addDays(E, 1), "2. påskedag"],
        [addDays(E, 39), "Kristi himmelfartsdag"],
        [addDays(E, 49), "Pinsedag"], [addDays(E, 50), "2. pinsedag"],
        [new Date(y, 5, 5), "Grundlovsdag"],
        [new Date(y, 11, 24), "Juleaftensdag"], [new Date(y, 11, 25), "Juledag"],
        [new Date(y, 11, 26), "2. juledag"], [new Date(y, 11, 31), "Nytårsaftensdag"]
      ];
      if (y < 2024) list.push([addDays(E, 26), "Store bededag"]);
      return list;
    } },
    { id: "se", name: "Sverige", flag: "🇸🇪", color: "#fbbf24", build: function (y) {
      var E = easter(y);
      return [
        [new Date(y, 0, 1), "Nyårsdagen"], [new Date(y, 0, 6), "Trettondedag jul"],
        [addDays(E, -2), "Långfredagen"], [E, "Påskdagen"], [addDays(E, 1), "Annandag påsk"],
        [new Date(y, 4, 1), "Första maj"], [addDays(E, 39), "Kristi himmelsfärds dag"],
        [addDays(E, 49), "Pingstdagen"], [new Date(y, 5, 6), "Nationaldagen"],
        [weekdayBetween(y, 5, 20, 26, 6), "Midsommardagen"],
        [weekdayBetween(y, 9, 31, 31, 6) > new Date(y, 9, 31) ? weekdayBetween(y, 10, 1, 6, 6) : weekdayBetween(y, 9, 31, 31, 6), "Alla helgons dag"],
        [new Date(y, 11, 24), "Julafton"], [new Date(y, 11, 25), "Juldagen"],
        [new Date(y, 11, 26), "Annandag jul"], [new Date(y, 11, 31), "Nyårsafton"]
      ];
    } },
    { id: "no", name: "Norge", flag: "🇳🇴", color: "#60a5fa", build: function (y) {
      var E = easter(y);
      return [
        [new Date(y, 0, 1), "Nyttårsdag"],
        [addDays(E, -3), "Skjærtorsdag"], [addDays(E, -2), "Langfredag"],
        [E, "1. påskedag"], [addDays(E, 1), "2. påskedag"],
        [new Date(y, 4, 1), "Arbeidernes dag"], [new Date(y, 4, 17), "Grunnlovsdag"],
        [addDays(E, 39), "Kristi himmelfartsdag"],
        [addDays(E, 49), "1. pinsedag"], [addDays(E, 50), "2. pinsedag"],
        [new Date(y, 11, 25), "1. juledag"], [new Date(y, 11, 26), "2. juledag"]
      ];
    } },
    { id: "de", name: "Tyskland", flag: "🇩🇪", color: "#f59e0b", build: function (y) {
      var E = easter(y);
      return [
        [new Date(y, 0, 1), "Neujahr"], [addDays(E, -2), "Karfreitag"],
        [addDays(E, 1), "Ostermontag"], [new Date(y, 4, 1), "Tag der Arbeit"],
        [addDays(E, 39), "Christi Himmelfahrt"], [addDays(E, 50), "Pfingstmontag"],
        [new Date(y, 9, 3), "Tag der Deutschen Einheit"],
        [new Date(y, 11, 25), "1. Weihnachtstag"], [new Date(y, 11, 26), "2. Weihnachtstag"]
      ];
    } },
    { id: "uk", name: "Storbritannien", flag: "🇬🇧", color: "#818cf8", build: function (y) {
      var E = easter(y);
      return [
        [new Date(y, 0, 1), "New Year's Day"], [addDays(E, -2), "Good Friday"],
        [addDays(E, 1), "Easter Monday"], [nthWeekday(y, 4, 1, 1), "Early May Bank Holiday"],
        [lastWeekday(y, 4, 1), "Spring Bank Holiday"], [lastWeekday(y, 7, 1), "Summer Bank Holiday"],
        [new Date(y, 11, 25), "Christmas Day"], [new Date(y, 11, 26), "Boxing Day"]
      ];
    } },
    { id: "us", name: "USA", flag: "🇺🇸", color: "#f472b6", build: function (y) {
      return [
        [new Date(y, 0, 1), "New Year's Day"], [nthWeekday(y, 0, 1, 3), "Martin Luther King Jr. Day"],
        [nthWeekday(y, 1, 1, 3), "Presidents' Day"], [lastWeekday(y, 4, 1), "Memorial Day"],
        [new Date(y, 5, 19), "Juneteenth"], [new Date(y, 6, 4), "Independence Day"],
        [nthWeekday(y, 8, 1, 1), "Labor Day"], [new Date(y, 10, 11), "Veterans Day"],
        [nthWeekday(y, 10, 4, 4), "Thanksgiving"], [new Date(y, 11, 25), "Christmas Day"]
      ];
    } }
  ];

  // ── iCalendar-parsing ──────────────────────────────────────────────────────
  function parseIcsDate(value) {
    var m = String(value).match(/(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?/);
    if (!m) return null;
    return { y: +m[1], m: +m[2] - 1, d: +m[3], time: m[4] ? m[4] + ":" + m[5] : "", hasTime: !!m[4] };
  }

  function unescapeIcs(s) {
    return String(s).replace(/\\n/gi, " · ").replace(/\\,/g, ",").replace(/\\;/g, ";").replace(/\\\\/g, "\\").trim();
  }

  function parseICS(text) {
    var lines = String(text).replace(/\r\n/g, "\n").replace(/\r/g, "\n").replace(/\n[ \t]/g, "").split("\n");
    var calName = "";
    var events = [];
    var yearly = [];
    var cur = null;

    function commit(ev) {
      if (!ev.start || !ev.title) return;
      var s = ev.start;
      if (ev.rrule && /FREQ=YEARLY/.test(ev.rrule)) {
        yearly.push({ m: s.m, d: s.d, title: ev.title });
        return;
      }
      var span = 1;
      if (ev.end) {
        var startDt = new Date(s.y, s.m, s.d);
        var endDt = new Date(ev.end.y, ev.end.m, ev.end.d);
        var diff = Math.round((endDt - startDt) / 864e5);
        span = ev.end.hasTime ? diff + 1 : diff; // DTEND uden tid er eksklusiv
        span = Math.max(1, Math.min(60, span));
      }
      events.push({ key: keyOf(s.y, s.m, s.d), title: ev.title, time: s.time, span: span });
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (line === "BEGIN:VEVENT") { cur = {}; continue; }
      if (line === "END:VEVENT") { if (cur) commit(cur); cur = null; continue; }
      var idx = line.indexOf(":");
      if (idx < 0) continue;
      var prop = line.slice(0, idx).split(";")[0].toUpperCase();
      var value = line.slice(idx + 1);
      if (!cur) {
        if (prop === "X-WR-CALNAME") calName = value.trim();
        continue;
      }
      if (prop === "DTSTART") cur.start = parseIcsDate(value);
      else if (prop === "DTEND") cur.end = parseIcsDate(value);
      else if (prop === "SUMMARY") cur.title = unescapeIcs(value);
      else if (prop === "RRULE") cur.rrule = value.toUpperCase();
    }
    return { name: calName, events: events.slice(0, MAX_ICAL_EVENTS), yearly: yearly };
  }

  // ── DOM ────────────────────────────────────────────────────────────────────
  function $(id) { return document.getElementById(id); }
  var elTitle = $("calTitle"), elSub = $("calSub"), elGrid = $("calGrid"),
      elWeekdays = $("calWeekdays"), elLegend = $("calLegend");
  if (!elGrid) return;

  var today = new Date();
  var view = { y: today.getFullYear(), m: today.getMonth() };
  var selectedDay = null;

  WEEKDAYS.forEach(function (name, i) {
    if (i === 0) {
      var uge = document.createElement("span");
      uge.textContent = "Uge";
      elWeekdays.appendChild(uge);
    }
    var s = document.createElement("span");
    s.textContent = name;
    elWeekdays.appendChild(s);
  });

  // ── Måneds-indeks: dato-nøgle → [{title, color, kind, time, source, ...}] ──
  function buildIndex(cells) {
    var index = {};
    var years = {};
    cells.forEach(function (dt) { years[dt.getFullYear()] = true; });
    var keys = {};
    cells.forEach(function (dt) { keys[keyOfDate(dt)] = true; });

    function add(key, item) {
      if (!keys[key]) return;
      (index[key] = index[key] || []).push(item);
    }

    Object.keys(data.events).forEach(function (key) {
      data.events[key].forEach(function (ev) {
        add(key, { title: ev.title, time: ev.time || "", color: USER_COLOR, kind: "user", source: "Egen aftale", id: ev.id });
      });
    });

    HOLIDAY_SETS.forEach(function (set) {
      if (!data.holidays[set.id]) return;
      Object.keys(years).forEach(function (yStr) {
        set.build(+yStr).forEach(function (pair) {
          add(keyOfDate(pair[0]), { title: pair[1], time: "", color: set.color, kind: "holiday", source: set.name });
        });
      });
    });

    data.icals.forEach(function (cal) {
      if (cal.enabled === false) return;
      (cal.events || []).forEach(function (ev) {
        var parts = ev.key.split("-");
        var start = new Date(+parts[0], +parts[1] - 1, +parts[2]);
        for (var i = 0; i < (ev.span || 1); i++) {
          add(keyOfDate(addDays(start, i)), { title: ev.title, time: i === 0 ? (ev.time || "") : "", color: cal.color, kind: "ical", source: cal.name });
        }
      });
      (cal.yearly || []).forEach(function (rule) {
        Object.keys(years).forEach(function (yStr) {
          add(keyOf(+yStr, rule.m, rule.d), { title: rule.title, time: "", color: cal.color, kind: "ical", source: cal.name });
        });
      });
    });

    Object.keys(index).forEach(function (key) {
      index[key].sort(function (a, b) {
        var order = { holiday: 0, ical: 1, user: 2 };
        if (order[a.kind] !== order[b.kind]) return order[a.kind] - order[b.kind];
        return (a.time || "99:99") < (b.time || "99:99") ? -1 : 1;
      });
    });
    return index;
  }

  // ── Rendering ──────────────────────────────────────────────────────────────
  function render(direction) {
    var first = new Date(view.y, view.m, 1);
    var startOffset = (first.getDay() + 6) % 7;
    var cells = [];
    for (var i = 0; i < 42; i++) cells.push(addDays(first, i - startOffset));

    var index = buildIndex(cells);
    var todayKey = keyOfDate(new Date());

    elTitle.textContent = MONTHS[view.m] + " " + view.y;

    var userCount = 0, holidayCount = 0;
    cells.forEach(function (dt) {
      if (dt.getMonth() !== view.m) return;
      (index[keyOfDate(dt)] || []).forEach(function (item) {
        if (item.kind === "user") userCount++;
        if (item.kind === "holiday") holidayCount++;
      });
    });
    var subParts = [];
    subParts.push(userCount === 1 ? "1 aftale" : userCount + " aftaler");
    if (holidayCount) subParts.push(holidayCount === 1 ? "1 helligdag" : holidayCount + " helligdage");
    elSub.textContent = subParts.join(" · ") + " i denne måned";

    elGrid.innerHTML = "";
    for (var row = 0; row < 6; row++) {
      var weekCell = document.createElement("div");
      weekCell.className = "cal-week";
      weekCell.textContent = isoWeek(cells[row * 7]);
      elGrid.appendChild(weekCell);

      for (var col = 0; col < 7; col++) {
        var dt = cells[row * 7 + col];
        var key = keyOfDate(dt);
        var items = index[key] || [];

        var cell = document.createElement("div");
        cell.className = "cal-day";
        cell.dataset.date = key;
        if (dt.getMonth() !== view.m) cell.classList.add("is-out");
        if (key === todayKey) cell.classList.add("is-today");
        if (col === 6) cell.classList.add("is-sun");
        if (items.some(function (it) { return it.kind === "holiday"; })) cell.classList.add("is-holiday");

        var num = document.createElement("span");
        num.className = "cal-day-num";
        num.textContent = dt.getDate();
        cell.appendChild(num);

        if (items.length) {
          var chips = document.createElement("div");
          chips.className = "cal-chips";
          items.slice(0, MAX_CHIPS).forEach(function (item) {
            var chip = document.createElement("div");
            chip.className = "cal-chip";
            chip.style.setProperty("--chip", item.color);
            var label = document.createElement("span");
            label.textContent = (item.time ? item.time + " " : "") + item.title;
            chip.title = item.title + " (" + item.source + ")";
            chip.appendChild(label);
            chips.appendChild(chip);
          });
          if (items.length > MAX_CHIPS) {
            var more = document.createElement("span");
            more.className = "cal-more";
            more.textContent = "+" + (items.length - MAX_CHIPS) + " mere";
            chips.appendChild(more);
          }
          cell.appendChild(chips);
        }
        elGrid.appendChild(cell);
      }
    }

    if (direction) {
      elGrid.classList.remove("cal-anim-next", "cal-anim-prev");
      void elGrid.offsetWidth;
      elGrid.classList.add(direction > 0 ? "cal-anim-next" : "cal-anim-prev");
    }

    renderLegend();
  }

  function renderLegend() {
    elLegend.innerHTML = "";
    var entries = [];
    HOLIDAY_SETS.forEach(function (set) {
      if (data.holidays[set.id]) entries.push({ name: set.flag + " " + set.name, color: set.color });
    });
    data.icals.forEach(function (cal) {
      if (cal.enabled !== false) entries.push({ name: cal.name, color: cal.color });
    });
    elLegend.hidden = entries.length === 0;
    entries.forEach(function (entry) {
      var span = document.createElement("span");
      var dot = document.createElement("i");
      dot.style.background = entry.color;
      span.appendChild(dot);
      span.appendChild(document.createTextNode(entry.name));
      elLegend.appendChild(span);
    });
  }

  // ── Navigation ─────────────────────────────────────────────────────────────
  function shiftMonth(delta) {
    var dt = new Date(view.y, view.m + delta, 1);
    view.y = dt.getFullYear();
    view.m = dt.getMonth();
    render(delta);
  }

  $("calPrev").addEventListener("click", function () { shiftMonth(-1); });
  $("calNext").addEventListener("click", function () { shiftMonth(1); });
  $("calToday").addEventListener("click", function () {
    var now = new Date();
    var delta = (now.getFullYear() * 12 + now.getMonth()) - (view.y * 12 + view.m);
    view.y = now.getFullYear();
    view.m = now.getMonth();
    render(delta === 0 ? 0 : (delta > 0 ? 1 : -1));
  });

  document.addEventListener("keydown", function (e) {
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable)) return;
    if (!$("calDayOverlay").hidden || !$("calSettingsOverlay").hidden) {
      if (e.key === "Escape") { closeDay(); closeSettings(); }
      return;
    }
    if (e.key === "ArrowLeft") shiftMonth(-1);
    if (e.key === "ArrowRight") shiftMonth(1);
  });

  // ── Dag-modal ──────────────────────────────────────────────────────────────
  var dayOverlay = $("calDayOverlay"), dayTitle = $("calDayTitle"), dayList = $("calDayList"),
      dayForm = $("calDayForm"), dayInput = $("calDayInput"), dayTime = $("calDayTime");

  elGrid.addEventListener("click", function (e) {
    var cell = e.target.closest(".cal-day");
    if (cell) openDay(cell.dataset.date);
  });

  function openDay(key) {
    selectedDay = key;
    var parts = key.split("-");
    var dt = new Date(+parts[0], +parts[1] - 1, +parts[2]);
    var dayNames = ["Søndag", "Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag"];
    dayTitle.textContent = dayNames[dt.getDay()] + " " + dt.getDate() + ". " + MONTHS[dt.getMonth()] + " " + dt.getFullYear();
    renderDayList();
    dayOverlay.hidden = false;
    dayInput.value = "";
    dayTime.value = "";
    dayInput.focus();
  }

  function renderDayList() {
    var parts = selectedDay.split("-");
    var dt = new Date(+parts[0], +parts[1] - 1, +parts[2]);
    var index = buildIndex([dt]);
    var items = index[selectedDay] || [];
    dayList.innerHTML = "";
    if (!items.length) {
      var empty = document.createElement("li");
      empty.className = "cal-day-empty";
      empty.textContent = "Ingen aftaler denne dag.";
      dayList.appendChild(empty);
      return;
    }
    items.forEach(function (item) {
      var li = document.createElement("li");
      li.className = "cal-day-item";
      var dot = document.createElement("i");
      dot.style.background = item.color;
      li.appendChild(dot);
      var text = document.createElement("span");
      text.className = "cal-item-text";
      text.textContent = item.title;
      li.appendChild(text);
      var meta = document.createElement("span");
      meta.className = "cal-item-meta";
      meta.textContent = item.time ? item.time : item.source;
      li.appendChild(meta);
      if (item.kind === "user") {
        var del = document.createElement("button");
        del.type = "button";
        del.className = "cal-item-del";
        del.textContent = "×";
        del.setAttribute("aria-label", "Slet aftale");
        del.addEventListener("click", function () {
          data.events[selectedDay] = (data.events[selectedDay] || []).filter(function (ev) { return ev.id !== item.id; });
          if (!data.events[selectedDay].length) delete data.events[selectedDay];
          save();
          renderDayList();
          render(0);
        });
        li.appendChild(del);
      }
      dayList.appendChild(li);
    });
  }

  dayForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var title = dayInput.value.trim();
    if (!title || !selectedDay) return;
    (data.events[selectedDay] = data.events[selectedDay] || []).push({
      id: Date.now() + "-" + Math.random().toString(36).slice(2, 7),
      title: title,
      time: dayTime.value || ""
    });
    save();
    dayInput.value = "";
    dayTime.value = "";
    renderDayList();
    render(0);
    dayInput.focus();
  });

  function closeDay() { dayOverlay.hidden = true; selectedDay = null; }
  $("calDayClose").addEventListener("click", closeDay);
  dayOverlay.addEventListener("click", function (e) { if (e.target === dayOverlay) closeDay(); });

  // ── Indstillinger ──────────────────────────────────────────────────────────
  var settingsOverlay = $("calSettingsOverlay"), holidayList = $("calHolidayList"),
      icalList = $("calIcalList"), importMsg = $("calImportMsg"),
      drop = $("calDrop"), fileInput = $("calFile");

  $("calSettings").addEventListener("click", function () {
    renderSettings();
    importMsg.hidden = true;
    settingsOverlay.hidden = false;
  });

  function closeSettings() { settingsOverlay.hidden = true; }
  $("calSettingsClose").addEventListener("click", closeSettings);
  settingsOverlay.addEventListener("click", function (e) { if (e.target === settingsOverlay) closeSettings(); });

  function makeSwitch(checked, onToggle) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "cal-switch";
    btn.setAttribute("role", "switch");
    btn.setAttribute("aria-checked", checked ? "true" : "false");
    btn.addEventListener("click", function () {
      var next = btn.getAttribute("aria-checked") !== "true";
      btn.setAttribute("aria-checked", next ? "true" : "false");
      onToggle(next);
    });
    return btn;
  }

  function renderSettings() {
    holidayList.innerHTML = "";
    HOLIDAY_SETS.forEach(function (set) {
      var row = document.createElement("div");
      row.className = "cal-set-row";
      var flag = document.createElement("span");
      flag.className = "cal-set-flag";
      flag.textContent = set.flag;
      row.appendChild(flag);
      var name = document.createElement("span");
      name.className = "cal-set-name";
      name.textContent = set.name;
      row.appendChild(name);
      var dot = document.createElement("i");
      dot.style.background = set.color;
      row.appendChild(dot);
      row.appendChild(makeSwitch(!!data.holidays[set.id], function (on) {
        data.holidays[set.id] = on;
        save();
        render(0);
      }));
      holidayList.appendChild(row);
    });

    icalList.innerHTML = "";
    if (!data.icals.length) {
      var none = document.createElement("p");
      none.className = "cal-hint";
      none.textContent = "Ingen kalendere importeret endnu.";
      icalList.appendChild(none);
    }
    data.icals.forEach(function (cal) {
      var row = document.createElement("div");
      row.className = "cal-set-row";
      var dot = document.createElement("i");
      dot.style.background = cal.color;
      row.appendChild(dot);
      var name = document.createElement("span");
      name.className = "cal-set-name";
      name.textContent = cal.name;
      row.appendChild(name);
      var count = document.createElement("span");
      count.className = "cal-set-count";
      var total = (cal.events || []).length + (cal.yearly || []).length;
      count.textContent = total === 1 ? "1 begivenhed" : total + " begivenheder";
      row.appendChild(count);
      row.appendChild(makeSwitch(cal.enabled !== false, function (on) {
        cal.enabled = on;
        save();
        render(0);
      }));
      var del = document.createElement("button");
      del.type = "button";
      del.className = "cal-set-del";
      del.textContent = "×";
      del.setAttribute("aria-label", "Fjern " + cal.name);
      del.addEventListener("click", function () {
        data.icals = data.icals.filter(function (c) { return c.id !== cal.id; });
        save();
        renderSettings();
        render(0);
      });
      row.appendChild(del);
      icalList.appendChild(row);
    });
  }

  // ── Import ─────────────────────────────────────────────────────────────────
  function showImportMsg(text, ok) {
    importMsg.textContent = text;
    importMsg.className = "cal-import-msg " + (ok ? "is-ok" : "is-err");
    importMsg.hidden = false;
  }

  function importFile(file) {
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      var parsed = parseICS(reader.result);
      if (!parsed.events.length && !parsed.yearly.length) {
        showImportMsg("Ingen begivenheder fundet i filen. Er det en gyldig .ics-fil?", false);
        return;
      }
      var name = parsed.name || file.name.replace(/\.ics$/i, "");
      data.icals.push({
        id: Date.now() + "-" + Math.random().toString(36).slice(2, 7),
        name: name,
        color: ICAL_PALETTE[data.icals.length % ICAL_PALETTE.length],
        enabled: true,
        events: parsed.events,
        yearly: parsed.yearly
      });
      save();
      renderSettings();
      render(0);
      var total = parsed.events.length + parsed.yearly.length;
      showImportMsg("„" + name + "“ importeret med " + total + " begivenheder.", true);
    };
    reader.onerror = function () { showImportMsg("Filen kunne ikke læses.", false); };
    reader.readAsText(file);
  }

  fileInput.addEventListener("change", function () {
    importFile(fileInput.files[0]);
    fileInput.value = "";
  });

  ["dragenter", "dragover"].forEach(function (type) {
    drop.addEventListener(type, function (e) { e.preventDefault(); drop.classList.add("is-over"); });
  });
  ["dragleave", "drop"].forEach(function (type) {
    drop.addEventListener(type, function (e) { e.preventDefault(); drop.classList.remove("is-over"); });
  });
  drop.addEventListener("drop", function (e) {
    if (e.dataTransfer && e.dataTransfer.files.length) importFile(e.dataTransfer.files[0]);
  });

  render(0);
})();
