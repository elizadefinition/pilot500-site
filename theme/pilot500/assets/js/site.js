/* Pilot500 — site interactions (no dependencies)
   Each module starts from a data-p5="name" hook, so any pattern can be
   placed anywhere on any page. Loops only run while their panel is on
   screen, and nothing auto-plays when the visitor prefers reduced motion. */
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.add('p5-js');
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* Run fn(isVisible) whenever el enters or leaves the viewport */
  function watch(el, fn, threshold) {
    if (!('IntersectionObserver' in window)) { fn(true); return; }
    new IntersectionObserver(function (es) { es.forEach(function (e) { fn(e.isIntersecting); }); },
      { threshold: threshold || 0.25 }).observe(el);
  }
  function once(el, fn, threshold) {
    var done = false;
    watch(el, function (v) { if (v && !done) { done = true; fn(); } }, threshold);
  }

  /* Header ---------------------------------------------------------------- */
  var hd = $('.p5-hd');
  if (hd) {
    var onScroll = function () { hd.classList.toggle('is-stuck', window.scrollY > 8); };
    onScroll(); window.addEventListener('scroll', onScroll, { passive: true });
    var mb = $('.p5-menu-btn', hd);
    if (mb) mb.addEventListener('click', function () {
      var open = hd.classList.toggle('is-open'); mb.setAttribute('aria-expanded', open);
    });
    $$('.p5-nav a', hd).forEach(function (a) { a.addEventListener('click', function () { hd.classList.remove('is-open'); }); });
  }

  /* Scroll motion --------------------------------------------------------- *
   * Added at runtime only, so the WordPress block markup never changes.      */
  // 1. Section headings rise word by word (text nodes only; links, <br>, <sup> and spans are kept)
  function splitWords(el) {
    var i = 0;
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var parts = n.textContent.split(/(\s+)/), frag = document.createDocumentFragment();
          parts.forEach(function (t) {
            if (!t) return;
            if (/^\s+$/.test(t)) { frag.appendChild(document.createTextNode(t)); return; }
            var w = document.createElement('span'), wi = document.createElement('span');
            w.className = 'p5-w8'; wi.className = 'p5-w8i'; wi.style.setProperty('--i', i++);
            wi.textContent = t; w.appendChild(wi); frag.appendChild(w);
          });
          n.parentNode.replaceChild(frag, n);
        } else if (n.nodeType === 1 && n.tagName !== 'BR') walk(n);
      });
    })(el);
    el.classList.add('p5-words');
    return i;
  }
  if (!RM) {
    $$('.p5-h1,.p5-band .p5-h2').forEach(function (h) {
      var n = splitWords(h);
      // what follows the heading in its column waits for the words
      var col = h.parentNode, d = Math.min(n, 10) * 0.045 + 0.15;
      $$(':scope > .p5-lede, :scope > .wp-block-buttons, :scope > .p5-picks, :scope > .p5-ring, :scope > .p5-ticks, :scope > .p5-note', col).forEach(function (el, k) {
        el.classList.add('p5-reveal'); el.style.setProperty('--d', (d + k * 0.08).toFixed(2) + 's');
      });
    });
    // 2. Side panels unmask as they arrive
    $$('.p5-split > .p5-panel, .p5-stats, .p5-contact > .p5-form, .p5-trust').forEach(function (el) { el.classList.add('p5-rise'); });
  }
  $$('.p5-words,.p5-rise').forEach(function (el) { once(el, function () { el.classList.add('is-in'); }, 0.15); });

  // 3. Big figures count up when they come into view ("40%", "+1.9 pts")
  $$('.p5-fig__n').forEach(function (el) {
    var m = el.textContent.match(/^([^\d]*)([\d.,]+)(.*)$/); if (!m || RM) return;
    var end = parseFloat(m[2].replace(/,/g, '')), dec = (m[2].split('.')[1] || '').length;
    var show = function (v) { el.textContent = m[1] + v.toFixed(dec) + m[3]; };
    show(0);
    once(el, function () {
      var t0 = performance.now();
      (function tick(t) { var p = Math.min(1, (t - t0) / 1400); show(end * (1 - Math.pow(1 - p, 4))); if (p < 1) requestAnimationFrame(tick); })(t0);
    }, 0.6);
  });

  // 4. Light parallax: a few pixels on the hero stats and the side panels, desktop only
  var px = RM ? [] : $$('.p5-stats, .p5-split > .p5-panel');
  // 5. Scroll progress line in the header + current section in the nav
  var navLinks = $$('.p5-nav a[href^="#"]'), targets = navLinks.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var ticking = false;
  function onScrollFrame() {
    ticking = false;
    var vh = window.innerHeight, max = document.documentElement.scrollHeight - vh;
    root.style.setProperty('--p5-scroll', max > 0 ? (window.scrollY / max).toFixed(4) : 0);
    if (window.innerWidth > 1040) px.forEach(function (el) {
      var r = el.getBoundingClientRect(); if (r.bottom < -100 || r.top > vh + 100) return;
      var y = ((r.top + r.height / 2) - vh / 2) * -0.04;
      el.style.translate = '0 ' + Math.max(-14, Math.min(14, y)).toFixed(1) + 'px';
    }); else px.forEach(function (el) { el.style.translate = ''; });
    var cur = -1;
    targets.forEach(function (t, k) { if (t && t.getBoundingClientRect().top < vh * 0.4) cur = k; });
    navLinks.forEach(function (a, k) { a.parentNode.classList.toggle('is-current', k === cur); });
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScrollFrame); } }, { passive: true });
  window.addEventListener('resize', onScrollFrame);
  onScrollFrame();

  /* Reveal + "in view" flags -------------------------------------------- */
  $$('.p5-reveal,[data-in]').forEach(function (el) {
    once(el, function () { el.classList.add('is-in'); setTimeout(function () { el.classList.add('is-done'); }, 1600); }, 0.2);
  });

  /* Count-up numbers ------------------------------------------------------ */
  $$('[data-count]').forEach(function (el) {
    var end = parseFloat(el.getAttribute('data-count')), suf = el.getAttribute('data-suffix') || '';
    var fmt = function (n) { return Math.round(n).toLocaleString('en-GB') + suf; };
    if (RM) { el.textContent = fmt(end); return; }
    el.textContent = fmt(0);
    once(el, function () {
      var t0 = performance.now(), dur = 1600;
      (function tick(t) {
        var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 4);
        el.textContent = fmt(end * e);
        if (p < 1) requestAnimationFrame(tick);
      })(t0);
    }, 0.5);
  });

  /* Marquee + logo wall: duplicate the list for a seamless loop ----------- */
  $$('.p5-marquee__track,.p5-wall__col').forEach(function (track) {
    var ul = $('ul', track); if (!ul) return;
    var c = ul.cloneNode(true); c.setAttribute('aria-hidden', 'true');
    $$('img', c).forEach(function (i) { i.alt = ''; });
    track.appendChild(c);
  });

  /* Picks: accordion list with optional auto-advance ---------------------- *
   * <ul data-p5="picks" data-auto="6000"> <li class="p5-pick">…            */
  function Picks(list) {
    var items = $$('.p5-pick', list), cur = -1, auto = +list.getAttribute('data-auto') || 0;
    var vis = false, hover = false, user = false, t0 = 0, raf = 0, self = this;
    this.list = list; this.items = items; this.listeners = [];
    function set(i, byUser) {
      if (byUser) user = true;
      if (i === cur) return;
      cur = i;
      items.forEach(function (li, k) {
        var on = k === i; li.classList.toggle('is-on', on);
        var b = $('.p5-pick__btn', li); if (b) b.setAttribute('aria-expanded', on);
        li.style.setProperty('--p', (user || !auto || RM) ? 1 : 0);
      });
      t0 = performance.now();
      self.listeners.forEach(function (f) { f(i, items[i]); });
    }
    this.set = set;
    this.on = function (f) { this.listeners.push(f); if (cur > -1) f(cur, items[cur]); };
    items.forEach(function (li, k) {
      var b = $('.p5-pick__btn', li); if (b) b.addEventListener('click', function () { set(k, true); });
    });
    // data-hover: select on hover (mouse only; touch and keyboard still tap/focus to select).
    // Uses mousemove with a short intent delay so the accordion opening and closing
    // under a still pointer never triggers another change.
    if (list.hasAttribute('data-hover')) {
      var ht = 0;
      items.forEach(function (li, k) {
        li.addEventListener('mousemove', function (e) {
          if (e.pointerType === 'touch' || k === cur) return;
          clearTimeout(ht); ht = setTimeout(function () { set(k, true); }, 90);
        });
        li.addEventListener('mouseleave', function () { clearTimeout(ht); });
        var b = $('.p5-pick__btn', li);
        if (b) {
          b.addEventListener('mousedown', function (e) { e.preventDefault(); });
          b.addEventListener('focus', function () { set(k, true); });
        }
      });
    }
    list.addEventListener('mouseenter', function () { hover = true; });
    list.addEventListener('mouseleave', function () { hover = false; t0 = performance.now() - (parseFloat(items[cur].style.getPropertyValue('--p')) || 0) * auto; });
    var start = +list.getAttribute('data-start') || 0;
    set(start);
    if (auto && !RM) {
      watch(list.closest('section') || list, function (v) { vis = v; if (v) { t0 = performance.now(); loop(); } });
      function loop() {
        cancelAnimationFrame(raf);
        if (!vis || user) return;
        raf = requestAnimationFrame(function (t) {
          if (hover) { t0 = t - (parseFloat(items[cur].style.getPropertyValue('--p')) || 0) * auto; loop(); return; }
          var p = (t - t0) / auto;
          if (p >= 1) { set((cur + 1) % items.length); }
          else items[cur].style.setProperty('--p', p.toFixed(4));
          loop();
        });
      }
    }
  }
  var picks = {};
  $$('[data-p5="picks"]').forEach(function (l) { picks[l.id] = new Picks(l); });

  /* 7 Management Keys ring ----------------------------------------------- */
  $$('[data-p5="keys"]').forEach(function (ring) {
    var p = picks[ring.getAttribute('data-for')]; if (!p) return;
    var segs = $$('.seg', ring), nums = $$('.num', ring), big = $('.big', ring), lab = $('.lab', ring);
    var bars = $$('.p5-kbar', ring), score = $('[data-score]', ring), gap = $('[data-gap]', ring), bench = +ring.getAttribute('data-bench') || 0;
    once(ring, function () { ring.classList.add('is-in'); }, 0.3);
    p.on(function (i, li) {
      if (bars[i]) {
        var v = +bars[i].getAttribute('data-s'), d = v - bench;
        bars.forEach(function (b, k) { b.classList.toggle('is-on', k === i); });
        score.textContent = v;
        gap.textContent = 'Key ' + ('0' + (i + 1)).slice(-2) + ' · ' + (d === 0 ? 'level with' : Math.abs(d) + ' pts ' + (d < 0 ? 'below' : 'above')) + ' benchmark';
        gap.classList.toggle('is-low', d < 0);
      }
      segs.forEach(function (s, k) { s.classList.toggle('is-on', k === i); });
      nums.forEach(function (s, k) { s.classList.toggle('is-on', k === i); });
      big.textContent = ('0' + (i + 1)).slice(-2);
      lab.textContent = li.getAttribute('data-name');
    });
    segs.forEach(function (s, k) {
      s.addEventListener('click', function () { p.set(k, true); });
      s.addEventListener('mouseenter', function () { p.set(k, true); });
      if (bars[k]) { bars[k].addEventListener('mouseenter', function () { p.set(k, true); }); bars[k].addEventListener('click', function () { p.set(k, true); }); }
      s.addEventListener('mousedown', function (e) { e.preventDefault(); });
      s.addEventListener('focus', function () { p.set(k, true); });
      s.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); p.set(k, true); } });
    });
  });

  /* Roles org chart ------------------------------------------------------- */
  $$('[data-p5="org"]').forEach(function (org) {
    var p = picks[org.getAttribute('data-for')]; if (!p) return;
    var nodes = $$('.n', org), edges = $$('.e', org);
    var view = $('.p5-org__view b', org), title = $('.p5-org__foot b', org), sub = $('.p5-org__foot small', org);
    var nums = $$('.p5-org__nums span', org), fns = $$('.p5-org__fns span', org), fi = 0, ft = 0;
    p.on(function (i, li) {
      var scope = li.getAttribute('data-scope');               // node id prefix, '' = everything
      var inScope = function (k) { return scope === '' || k.indexOf(scope) === 0; };
      nodes.forEach(function (n) { n.classList.toggle('on', inScope(n.getAttribute('data-k'))); });
      edges.forEach(function (e) { var k = e.getAttribute('data-k'); e.classList.toggle('on', inScope(k) && k !== scope); });
      view.textContent = li.getAttribute('data-role');
      title.textContent = li.getAttribute('data-view');
      sub.textContent = li.getAttribute('data-sub');
      li.getAttribute('data-nums').split(',').forEach(function (v, k) {
        nums[k].textContent = v; nums[k].parentNode.classList.toggle('dim', v === '–');
      });
      var fn = li.hasAttribute('data-fn'); org.classList.toggle('is-fn', fn);
      clearInterval(ft);
      if (fn && !RM) { ft = setInterval(function () { fns.forEach(function (s, k) { s.classList.toggle('on', k === fi); }); fi = (fi + 1) % fns.length; }, 900); }
      else fns.forEach(function (s) { s.classList.remove('on'); });
    });
  });

  /* Chat window ----------------------------------------------------------- */
  $$('[data-p5="chat"]').forEach(function (chat) {
    var chips = $$('.p5-chip', chat), answers = $$('.p5-ans', chat), steps = $$('.p5-steps li', chat);
    var msg = $('.p5-msg', chat), msgT = $('.p5-msg span', chat), comp = $('.p5-compose__t', chat);
    var timers = [], cur = -1, vis = false, user = false, ph = comp.textContent;
    function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
    function clear() { timers.forEach(clearTimeout); timers = []; }
    function show(i, instant) {
      clear(); cur = i;
      var q = chips[i].textContent;
      chips.forEach(function (c, k) { c.classList.toggle('is-on', k === i); c.setAttribute('aria-pressed', k === i); });
      answers.forEach(function (a) { a.classList.remove('is-on'); });
      steps.forEach(function (s) { s.classList.remove('is-on', 'is-done'); });
      msg.classList.remove('is-on');
      if (instant || RM) {
        msgT.textContent = q; msg.classList.add('is-on'); answers[i].classList.add('is-on'); comp.textContent = ph; comp.classList.remove('has-text');
        return next();
      }
      // 1. type the question into the composer
      chat.classList.add('is-typing'); comp.classList.add('has-text'); comp.textContent = '';
      var n = 0;
      (function type() {
        comp.textContent = q.slice(0, ++n);
        if (n < q.length) later(type, 26); else later(send, 380);
      })();
      // 2. send, think in three beats, answer
      function send() {
        chat.classList.remove('is-typing'); comp.classList.remove('has-text'); comp.textContent = ph;
        msgT.textContent = q; msg.classList.add('is-on'); chat.classList.add('is-busy');
        steps.forEach(function (s, k) {
          later(function () { s.classList.add('is-on'); }, 250 + k * 520);
          later(function () { s.classList.add('is-done'); }, 700 + k * 520);
        });
        later(function () {
          steps.forEach(function (s) { s.classList.remove('is-on'); });
          answers[i].classList.add('is-on'); chat.classList.remove('is-busy'); next();
        }, 250 + steps.length * 520 + 300);
      }
    }
    function next() { if (!user && !RM) later(function () { if (vis) show((cur + 1) % chips.length); else cur = cur; }, 7500); }
    chips.forEach(function (c, k) { c.addEventListener('click', function () { user = true; show(k); }); });
    show(0, true);
    watch(chat, function (v) {
      var was = vis; vis = v;
      if (v && !was && !user && !RM) { clear(); later(function () { show((cur + 1) % chips.length); }, 2500); }
      if (!v) clear();
    }, 0.4);
  });

  /* Testimonials ---------------------------------------------------------- */
  $$('[data-p5="quotes"]').forEach(function (box) {
    var qs = $$('.p5-quote', box), dots = $$('.p5-dots button', box), cur = 0, t0 = 0, raf = 0, vis = false, hold = false, DUR = 6500;
    function set(i) {
      cur = (i + qs.length) % qs.length; t0 = performance.now();
      qs.forEach(function (q, k) { q.classList.toggle('is-on', k === cur); q.setAttribute('aria-hidden', k !== cur); });
      dots.forEach(function (d, k) { d.classList.toggle('is-on', k === cur); d.style.setProperty('--p', RM ? 1 : 0); d.setAttribute('aria-current', k === cur); });
    }
    dots.forEach(function (d, k) { d.addEventListener('click', function () { set(k); }); });
    var prev = $('[data-prev]', box), nxt = $('[data-next]', box);
    if (prev) prev.addEventListener('click', function () { set(cur - 1); });
    if (nxt) nxt.addEventListener('click', function () { set(cur + 1); });
    box.addEventListener('mouseenter', function () { hold = true; });
    box.addEventListener('mouseleave', function () { hold = false; t0 = performance.now(); });
    set(0);
    if (RM) return;
    watch(box, function (v) { vis = v; if (v) { t0 = performance.now(); loop(); } });
    function loop() {
      cancelAnimationFrame(raf); if (!vis) return;
      raf = requestAnimationFrame(function (t) {
        if (hold) t0 = t - parseFloat(dots[cur].style.getPropertyValue('--p') || 0) * DUR;
        var p = (t - t0) / DUR;
        if (p >= 1) set(cur + 1); else dots[cur].style.setProperty('--p', p.toFixed(4));
        loop();
      });
    }
  });

  /* Value calculator ------------------------------------------------------ */
  $$('[data-p5="calc"]').forEach(function (calc) {
    var range = $('input[type=range]', calc), bars = $$('.p5-cbar', calc);
    var sizes = bars.map(function (b) { return +b.getAttribute('data-m'); });
    var rev = $('[data-rev]', calc), out = $('[data-out]', calc), shown = 0, raf = 0;
    var eur = function (m) { return '€' + (m >= 1000 ? m.toLocaleString('en-GB') : (Math.round(m * 100) / 100).toString()) + 'M'; };
    function set(i) {
      range.value = i; range.style.setProperty('--v', (i / (sizes.length - 1) * 100) + '%');
      range.setAttribute('aria-valuetext', eur(sizes[i]));
      bars.forEach(function (b, k) { b.classList.toggle('is-on', k === i); b.setAttribute('aria-pressed', k === i); });
      rev.textContent = eur(sizes[i]);
      var target = sizes[i] * 0.019, from = shown, t0 = performance.now();
      cancelAnimationFrame(raf);
      if (RM) { shown = target; out.textContent = eur(target); return; }
      (function tick(t) {
        var p = Math.min(1, (t - t0) / 500), e = 1 - Math.pow(1 - p, 3);
        shown = from + (target - from) * e;
        out.textContent = eur(p < 1 ? Math.round(shown * 10) / 10 : target);
        if (p < 1) raf = requestAnimationFrame(tick);
      })(t0);
    }
    range.addEventListener('input', function () { set(+range.value); });
    bars.forEach(function (b, k) { b.addEventListener('click', function () { set(k); }); });
    set(+range.value);
  });

  /* The short film (how it works) ----------------------------------------- *
   * 1 set the plan · 2 it loses strength · 3 you can't see where ·
   * 4 Pilot500 asks the field · 5 now you see exactly where · 6 act first   */
  $$('[data-p5="film"]').forEach(function (film) {
    var caps = $$('.p5-film__cap p', film), rows = $$('.p5-row', film), prog = $$('.p5-film__prog i', film);
    var timers = [], vis = false, playing = false;
    var STEPS = [1800, 2400, 2200, 3200, 2400, 5200];
    function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
    function step(s) {
      film.setAttribute('data-step', s);
      caps.forEach(function (c) { c.classList.toggle('is-on', +c.getAttribute('data-s') === s); });
      prog.forEach(function (p, k) { p.classList.toggle('on', k < s); });
      if (s === 4) rows.forEach(function (r, k) { later(function () { r.classList.add('is-ans'); }, 300 + k * 360); });
    }
    function reset() {
      timers.forEach(clearTimeout); timers = [];
      rows.forEach(function (r) { r.classList.remove('is-ans'); });
      film.setAttribute('data-step', 0);
      caps.forEach(function (c) { c.classList.remove('is-on'); });
    }
    function finalFrame() { reset(); rows.forEach(function (r) { r.classList.add('is-ans'); }); step(6); film.setAttribute('data-step', 6); }
    function play() {
      reset(); playing = true;
      var t = 120;
      STEPS.forEach(function (d, k) { later(function () { step(k + 1); }, t); t += d; });
      later(function () { playing = false; if (vis) play(); }, t + 600);
    }
    var rp = $('.p5-replay', film);
    if (rp) rp.addEventListener('click', function () { RM ? finalFrame() : play(); });
    if (RM) { finalFrame(); return; }
    reset();
    watch(film, function (v) { vis = v; if (v && !playing) play(); if (!v) { reset(); playing = false; } }, 0.45);
  });

  /* Demo form: calendar, slots, intent ----------------------------------- */
  $$('[data-p5="demo"]').forEach(function (form) {
    var grid = $('.p5-cal__g', form), title = $('.p5-cal__t', form), slotDay = $('.p5-slots small', form);
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var view = new Date(today.getFullYear(), today.getMonth(), 1), picked = null;
    var M = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    var D = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    function firstOpen(d) { d = new Date(d); do { d.setDate(d.getDate() + 1); } while (d.getDay() === 0 || d.getDay() === 6); return d; }
    picked = firstOpen(today);
    function render() {
      title.textContent = M[view.getMonth()] + ' ' + view.getFullYear();
      $$('button', grid).forEach(function (b) { b.remove(); });
      $$('i', grid).forEach(function (b) { b.remove(); });
      var lead = (view.getDay() + 6) % 7, days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
      for (var k = 0; k < lead; k++) grid.appendChild(document.createElement('i'));
      for (var d = 1; d <= days; d++) {
        var dt = new Date(view.getFullYear(), view.getMonth(), d), b = document.createElement('button');
        b.type = 'button'; b.textContent = d;
        b.disabled = dt <= today || dt.getDay() === 0 || dt.getDay() === 6;
        if (picked && +dt === +picked) b.classList.add('is-on');
        (function (dt) { b.addEventListener('click', function () { picked = dt; render(); }); })(dt);
        grid.appendChild(b);
      }
      if (picked) slotDay.textContent = D[picked.getDay()] + ' ' + picked.getDate() + ' ' + M[picked.getMonth()].slice(0, 3);
    }
    $('[data-cal-prev]', form).addEventListener('click', function () {
      var p = new Date(view.getFullYear(), view.getMonth() - 1, 1);
      if (p >= new Date(today.getFullYear(), today.getMonth(), 1)) { view = p; render(); }
    });
    $('[data-cal-next]', form).addEventListener('click', function () { view = new Date(view.getFullYear(), view.getMonth() + 1, 1); render(); });
    $$('.p5-slots button', form).forEach(function (b, k, all) {
      b.addEventListener('click', function () { all.forEach(function (x) { x.classList.toggle('is-on', x === b); x.setAttribute('aria-pressed', x === b); }); });
    });
    render();
    var intent = $('[name=intent]', form), btn = $('.wp-block-button__link', form);
    var labels = { demo: 'Book a demo', case: 'Send me a case study', talk: 'Ask the team to call me' };
    if (intent) intent.addEventListener('change', function () { btn.textContent = labels[intent.value] || labels.demo; });
    // buttons elsewhere on the page can preselect the intent: add the class
    // p5-intent-case or p5-intent-talk to a Button block that links to #demo
    $$('.p5-intent-case a,.p5-intent-talk a,.p5-intent-demo a').forEach(function (a) {
      a.addEventListener('click', function () {
        var m = a.closest('[class*="p5-intent-"]').className.match(/p5-intent-(\w+)/);
        if (m && intent) { intent.value = m[1]; intent.dispatchEvent(new Event('change')); }
      });
    });
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var f = $('form', form);
      if (f && !f.reportValidity()) return;
      form.classList.add('is-sent');           // replace with your form plugin / Calendly embed
    });
  });
})();
