#!/usr/bin/env python3
"""Pilot500 build: one source for the WordPress block theme and the static preview.

Writes
  theme/pilot500/patterns/*.php        one block pattern per section (WordPress)
  theme/pilot500/parts/header.html     template parts
  theme/pilot500/parts/footer.html
  theme/pilot500/templates/*.html      front page = all patterns in order
  preview/index.html                   static preview that loads the theme's CSS/JS
  dist/pilot500-preview.html           single self-contained file for sharing
  dist/pilot500-theme.zip              upload in WordPress > Appearance > Themes

Run:  python3 tools/build.py
Edit copy here (or in WordPress after install). The patterns are plain block
markup, so they can also be edited by hand; re-running this script overwrites them.
"""
import base64, json, math, os, re, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = os.path.join(ROOT, 'theme', 'pilot500')
J = lambda d: json.dumps(d, separators=(',', ':'), ensure_ascii=False)


def A(path):
    """Asset URL placeholder, resolved per target (PHP echo or relative path)."""
    return '@@ASSET:%s@@' % path


# ---------------------------------------------------------------- block helpers
def _attrs(d):
    d = {k: v for k, v in d.items() if v not in (None, '', {})}
    return (' ' + J(d)) if d else ''


def group(inner, cls='', tag='div', anchor=None):
    a = {}
    if tag != 'div':
        a['tagName'] = tag
    if anchor:
        a['anchor'] = anchor
    if cls:
        a['className'] = cls
    idattr = f' id="{anchor}"' if anchor else ''
    klass = ('wp-block-group ' + cls).strip()
    return (f'<!-- wp:group{_attrs(a)} -->\n<{tag}{idattr} class="{klass}">'
            + ''.join(inner) + f'</{tag}>\n<!-- /wp:group -->\n')


def heading(text, level=2, cls=''):
    a = {}
    if level != 2:
        a['level'] = level
    if cls:
        a['className'] = cls
    klass = ('wp-block-heading ' + cls).strip()
    return f'<!-- wp:heading{_attrs(a)} -->\n<h{level} class="{klass}">{text}</h{level}>\n<!-- /wp:heading -->\n'


def para(text, cls=''):
    a = {'className': cls} if cls else {}
    c = f' class="{cls}"' if cls else ''
    return f'<!-- wp:paragraph{_attrs(a)} -->\n<p{c}>{text}</p>\n<!-- /wp:paragraph -->\n'


def button(label, href, cls=''):
    a = {'className': cls} if cls else {}
    klass = ('wp-block-button ' + cls).strip()
    return (f'<!-- wp:button{_attrs(a)} -->\n<div class="{klass}"><a class="wp-block-button__link wp-element-button" '
            f'href="{href}">{label}</a></div>\n<!-- /wp:button -->\n')


def buttons(btns, cls=''):
    a = {'className': cls} if cls else {}
    klass = ('wp-block-buttons ' + cls).strip()
    return f'<!-- wp:buttons{_attrs(a)} -->\n<div class="{klass}">' + ''.join(btns) + '</div>\n<!-- /wp:buttons -->\n'


def html(markup):
    return '<!-- wp:html -->\n' + markup.strip() + '\n<!-- /wp:html -->\n'


def section(anchor, cls, inner):
    """Every section: a full-width band with the shared content container inside."""
    return group([group(inner, 'p5-w')], ('p5 p5-band ' + cls).strip(), 'section', anchor)


def head(title, lede=None, extra=''):
    inner = [heading(title, 2, 'p5-h2')]
    if lede:
        inner.append(para(lede, 'p5-lede'))
    if extra:
        inner.append(extra)
    return group(inner, 'p5-head')


def card(svg, title, body, dark=False):
    return group([
        html(f'<div class="p5-thumb" aria-hidden="true"><div class="p5-thumb__plate">{svg}</div></div>'),
        group([heading(title, 3, 'p5-h3'), para(body, 'p5-body')], 'p5-card__body'),
    ], 'p5-card p5-reveal', 'article')


def cta(kicker, title, label, href, extra_cls=''):
    """L6 — CTA banner"""
    return group([
        group([para(kicker, 'p5-kicker'), para(title, 'p5-cta__title')]),
        buttons([button(label, href, ('is-light p5-arrow ' + extra_cls).strip())]),
    ], 'p5-cta p5-reveal')


def ill(body, vb='0 0 200 90'):
    return f'<svg class="p5-ill" viewBox="{vb}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">{body}</svg>'


# ------------------------------------------------------------- illustrations
ILL = {}
# L2 · gain
bars = [(18, 'g', 'dn'), (28, 'g', 'up'), (22, 'g', 'dn'), (46, 'b', 'up'), (30, 'g', 'dn'), (56, 'b', 'up'), (34, 'g', 'dn'), (40, 'g', 'up')]
ILL['reveal'] = ill(''.join(
    f'<rect class="bar {c} {m}" x="{40 + i * 16}" y="{78 - h}" width="9" height="{h}" rx="1.5"/>' for i, (h, c, m) in enumerate(bars))
    + '<rect class="gl" x="34" y="78" width="132" height="1.2"/>')
ILL['align'] = ill(
    '<circle cx="100" cy="45" r="27" fill="none" class="sg" stroke-width="9"/>'
    '<g class="spin"><path d="M100 18a27 27 0 0 1 26.6 22.4" fill="none" class="sb" stroke-width="9"/>'
    '<path d="M73.4 49.6A27 27 0 0 0 88 69.2" fill="none" class="sk" stroke-width="9"/></g>'
    '<rect x="90" y="33" width="20" height="24" rx="3" class="gl"/>'
    '<rect x="94" y="39" width="12" height="2.2" rx="1" class="g"/><rect x="94" y="44" width="12" height="2.2" rx="1" class="g"/><rect x="94" y="49" width="8" height="2.2" rx="1" class="b"/>')
ILL['prioritise'] = ill(
    '<rect class="grow more b" x="72" y="20" width="96" height="6" rx="3"/>'
    '<rect class="grow alt g" x="72" y="34" width="70" height="6" rx="3"/>'
    '<rect class="grow g" x="72" y="48" width="58" height="6" rx="3"/>'
    '<rect class="grow alt g" x="72" y="62" width="78" height="6" rx="3"/>'
    '<g class="drop"><path d="M50 14a8 8 0 0 1 8 8c0 6-8 13-8 13s-8-7-8-13a8 8 0 0 1 8-8z" class="k"/><circle cx="50" cy="22" r="3" fill="#fff"/></g>'
    '<circle class="pulse b" cx="50" cy="40" r="2.2" opacity=".5"/>')
ILL['deliver'] = ill(
    '<rect x="52" y="10" width="96" height="58" rx="4" fill="none" class="sk" stroke-width="2.2"/>'
    '<rect x="58" y="16" width="30" height="3" rx="1.5" class="k"/>'
    '<rect class="bar g" x="62" y="48" width="7" height="12"/><rect class="bar g" x="72" y="42" width="7" height="18"/><rect class="bar g" x="82" y="45" width="7" height="15"/><rect class="bar b up" x="92" y="34" width="7" height="26"/>'
    '<rect class="grow gl" x="108" y="34" width="32" height="3" rx="1.5"/><rect class="grow gl" x="108" y="42" width="26" height="3" rx="1.5"/><rect class="grow gl" x="108" y="50" width="30" height="3" rx="1.5"/>'
    '<rect x="98" y="68" width="4" height="10" class="g"/><rect x="84" y="78" width="32" height="2.5" rx="1.2" class="g"/>')
# L2 · features
ILL['report'] = ill(
    '<rect x="44" y="14" width="66" height="66" rx="4" class="gl"/>'
    '<g class="nudge"><rect x="62" y="8" width="70" height="70" rx="4" fill="#fff" class="sg" stroke-width="1.2" style="fill:#fff"/>'
    '<rect x="70" y="16" width="34" height="3" rx="1.5" class="k"/><rect x="70" y="24" width="50" height="2.2" rx="1" class="gl"/><rect x="70" y="29" width="44" height="2.2" rx="1" class="gl"/>'
    '<rect class="bar g" x="72" y="52" width="7" height="16"/><rect class="bar b up" x="82" y="44" width="7" height="24"/><rect class="bar g" x="92" y="56" width="7" height="12"/><rect class="bar g" x="102" y="50" width="7" height="18"/></g>'
    '<rect class="grow b" x="140" y="30" width="26" height="5" rx="2.5"/><rect class="grow gl" x="140" y="40" width="20" height="5" rx="2.5"/><rect class="grow gl" x="140" y="50" width="24" height="5" rx="2.5"/>')
ILL['visualizer'] = ill(
    '<rect x="56" y="10" width="40" height="13" rx="6.5" class="gl"/><rect x="100" y="10" width="44" height="13" rx="6.5" class="k"/>'
    '<text x="76" y="19" font-size="6" text-anchor="middle" fill="#5A6371" font-family="IBM Plex Sans,Arial">Region A</text>'
    '<text x="122" y="19" font-size="6" text-anchor="middle" fill="#fff" font-family="IBM Plex Sans,Arial">Region B</text>'
    + ''.join(f'<rect class="bar {c} {m}" x="{58 + i * 15}" y="{82 - h}" width="10" height="{h}" rx="1.5"/>' for i, (h, c, m) in enumerate([(30, 'g', 'dn'), (40, 'g', 'up'), (24, 'g', 'up'), (48, 'b', 'up'), (36, 'g', 'dn'), (28, 'g', 'up')])))
ILL['styles'] = ill(
    '<rect x="58" y="8" width="84" height="74" rx="4" fill="none" class="sg" stroke-width="1.2"/>'
    '<path d="M100 8v74M58 45h84" class="sg" stroke-width="1.2"/>'
    '<rect class="fade b" x="101" y="9" width="40" height="35" rx="3" opacity=".15" style="opacity:.14"/>'
    '<g class="g"><circle cx="72" cy="22" r="2.6"/><circle cx="84" cy="34" r="2.6"/><circle cx="70" cy="60" r="2.6"/><circle cx="88" cy="70" r="2.6"/><circle cx="118" cy="64" r="2.6"/><circle cx="130" cy="56" r="2.6"/><circle cx="78" cy="52" r="2.6"/></g>'
    '<g class="nudge"><circle cx="122" cy="28" r="4" class="b"/></g>'
    '<text x="140" y="16" font-size="5" text-anchor="end" fill="#8B94A2" font-family="IBM Plex Sans,Arial" letter-spacing=".5">TARGET</text>')
ILL['chat'] = ill(
    '<rect class="grow k" x="96" y="12" width="64" height="12" rx="6"/>'
    '<g class="spin"><path d="M50 32a10 10 0 0 1 10 10" fill="none" class="sb" stroke-width="3.5"/><path d="M50 52a10 10 0 0 1-10-10" fill="none" class="sk" stroke-width="3.5"/></g>'
    '<rect x="68" y="34" width="92" height="44" rx="5" class="gl" style="opacity:.55"/>'
    '<rect class="grow k" x="76" y="42" width="56" height="3" rx="1.5"/><rect class="grow b" x="76" y="50" width="40" height="3" rx="1.5"/><rect class="grow alt g" x="76" y="58" width="66" height="3" rx="1.5"/>'
    '<rect x="76" y="66" width="76" height="6" rx="3" fill="none" class="sg"/><circle cx="81" cy="69" r="1.6" class="b"/>')
# L2 · trust (dark)
ILL['anon'] = ill(
    '<rect x="50" y="18" width="100" height="54" rx="6" class="gl"/>'
    '<rect x="62" y="28" width="30" height="3" rx="1.5" class="k" style="opacity:.8"/>'
    + ''.join(f'<rect class="fade g" x="{62 + i * 12}" y="38" width="9" height="9" rx="2"/>' for i in range(6))
    + '<rect x="62" y="56" width="76" height="5" rx="2.5" class="g" style="opacity:.4"/><rect class="grow b" x="62" y="56" width="58" height="5" rx="2.5"/>')
ILL['access'] = ill(
    '<rect x="40" y="16" width="56" height="16" rx="8" class="gl"/>'
    + ''.join(f'<circle class="pulse k" cx="{52 + i * 10}" cy="24" r="2.2"/>' for i in range(4))
    + '<path d="M62 50v-5a6 6 0 0 1 12 0v5" fill="none" class="sk" stroke-width="2"/><rect x="58" y="50" width="20" height="16" rx="2.5" class="k"/>'
    '<path d="M136 18v12M120 42v-6h32v6M120 42v6M152 42v6" fill="none" class="sg" stroke-width="1.4"/>'
    '<rect x="130" y="10" width="12" height="9" rx="2" class="g"/><rect x="114" y="34" width="12" height="9" rx="2" class="b"/><rect x="146" y="34" width="12" height="9" rx="2" class="g"/>'
    '<rect x="110" y="54" width="9" height="9" rx="2" class="k"/><rect x="122" y="54" width="9" height="9" rx="2" class="k"/><rect x="142" y="54" width="9" height="9" rx="2" class="g"/><rect x="154" y="54" width="9" height="9" rx="2" class="g"/>')
ILL['only'] = ill(
    '<rect x="36" y="14" width="78" height="62" rx="5" class="gl"/>'
    '<rect x="44" y="22" width="30" height="3" rx="1.5" class="k" style="opacity:.8"/>'
    '<rect class="grow g" x="44" y="34" width="56" height="4" rx="2"/><rect class="grow b" x="44" y="44" width="62" height="4" rx="2"/><rect class="grow alt g" x="44" y="54" width="48" height="4" rx="2"/><rect class="grow g" x="44" y="64" width="40" height="4" rx="2"/>'
    '<rect x="124" y="10" width="2" height="70" class="k" style="opacity:.8"/>'
    '<g class="g" style="opacity:.6"><circle cx="140" cy="20" r="2"/><circle cx="156" cy="32" r="2"/><circle cx="144" cy="46" r="2"/><circle cx="162" cy="56" r="2"/><circle cx="148" cy="70" r="2"/></g>')

PERSON = '<path d="M-5 0A5 4.4 0 0 1 5 0Z"/><circle cx="0" cy="-6.6" r="2.5"/>'
SEND = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M5 9V1M1.5 4.5 5 1l3.5 3.5"/></svg>'
MARK = open(os.path.join(ROOT, 'tools', 'mark.svg')).read().strip() if os.path.exists(os.path.join(ROOT, 'tools', 'mark.svg')) else ''
LOGO = open(os.path.join(ROOT, 'tools', 'logo.svg')).read().strip()

# ------------------------------------------------------------------- content
CLIENTS = [  # name, file, display width, height (from the client file)
    ('Novartis', 'novartis', 133, 23), ('Sanofi', 'sanofi', 110, 28), ('AstraZeneca', 'astrazeneca', 111, 28),
    ('Bristol Myers Squibb', 'bristol-myers-squibb', 150, 21), ('Lilly', 'lilly', 75, 41), ('Merck', 'merck', 59, 44),
    ('Biogen', 'biogen', 98, 32), ('Astellas', 'astellas', 106, 29), ('Daiichi Sankyo', 'daiichi-sankyo', 134, 23),
    ('Servier', 'servier', 125, 25), ('Ipsen', 'ipsen', 103, 30), ('Chiesi', 'chiesi', 115, 27),
    ('UCB', 'ucb', 44, 44), ('Menarini', 'menarini', 44, 44), ('Nestlé Health Science', 'nestle-health-science', 103, 30),
    ('Grünenthal', 'grunenthal', 78, 40), ('Pierre Fabre', 'pierre-fabre', 98, 32), ('Ferrer', 'ferrer', 114, 27),
    ('Ferring', 'ferring', 82, 38), ('LEO Pharma', 'leo-pharma', 57, 44), ('Actelion', 'actelion', 93, 33),
    ('Galderma', 'galderma', 150, 16), ('EGIS', 'egis', 78, 40), ('Biogaran', 'biogaran', 130, 24),
]


def logo_img(c, scale=1.0):
    n, f, w, h = c
    return (f'<img class="p5-logo-img" src="{A("logos/" + f + ".png")}" alt="{n}" '
            f'width="{round(w * scale)}" height="{round(h * scale)}" loading="lazy" decoding="async">')


# L1 — Hero ---------------------------------------------------------------------
STATS = [('27', '+', 'years of data<br>and benchmarks'), ('65', '+', 'countries'),
         ('550', '+', 'senior executives served'), ('60000', '+', 'field participants')]
line_pts = [(0, 140), (40, 134), (80, 137), (120, 126), (160, 118), (200, 104), (240, 92), (280, 74), (320, 56), (360, 36), (400, 14)]
line_d = 'M' + 'L'.join(f'{x} {y}' for x, y in line_pts)


def stat_html():
    items = ''.join(
        f'<div><dt>{l}</dt><dd data-count="{n}" data-suffix="{s}">{int(n):,}{s}</dd></div>' for n, s, l in STATS)
    return f'''
<div class="p5-stats" data-in>
  <div class="p5-stats__grid" aria-hidden="true"></div>
  <svg class="p5-stats__line" viewBox="0 0 400 160" preserveAspectRatio="none" aria-hidden="true">
    <defs><linearGradient id="p5-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#134A83" stop-opacity=".14"/><stop offset="1" stop-color="#134A83" stop-opacity="0"/></linearGradient></defs>
    <path class="ar" d="{line_d}L400 160L0 160Z"/>
    <path class="ln" pathLength="1" vector-effect="non-scaling-stroke" d="{line_d}"/>
  </svg>
  <div class="p5-stats__scan" aria-hidden="true"></div>
  <dl aria-label="Pilot500 in numbers">{items}</dl>
</div>'''


def hero():
    marquee = ''.join(f'<li>{logo_img(c)}</li>' for c in CLIENTS[:12])
    return section('hero', 'is-alt p5-hero', [
        group([
            group([
                heading('Improving<br>Execution<br><span class="p5-accent">Together</span>', 1, 'p5-h1'),
                para('You already track the market, the competition and your numbers, but not your execution. '
                     'In 8 weeks, Pilot500 tracks it and tells you exactly where your management team stands '
                     'and what your affiliate needs to do.', 'p5-lede'),
                buttons([button('Book a demo', '#demo', 'p5-arrow p5-intent-demo'),
                         button('See how it works', '#how', 'is-style-outline')]),
            ], 'p5-hero__text'),
            html(stat_html()),
        ], 'p5-hero__grid'),
        html(f'''
<div class="p5-trust">
  <p class="p5-trust__label">Trusted by leading pharma groups</p>
  <div class="p5-marquee"><div class="p5-marquee__track"><ul aria-label="Clients">{marquee}</ul></div></div>
</div>'''),
    ])


# L2 — Card grid ---------------------------------------------------------------
def gain():
    return section('gain', '', [
        head('From the real picture to the annual plan, in one place.'),
        group([
            card(ILL['reveal'], 'The real picture', 'Every rep, key account manager and MSL gives their own view, so what reaches you is not filtered by management.'),
            card(ILL['align'], 'One set of facts', 'The leadership team and every manager read the same results, each cut for their own role.'),
            card(ILL['prioritise'], 'A clear place to start', 'Every answer comes with recommendations and a ranking of what matters most, so you know where to act first.'),
            card(ILL['deliver'], 'The plan, ready<br>for the room', 'Draft the action plan in minutes, with the team presentation and the leadership summary included, and take it into your meeting.'),
        ], 'p5-cards'),
        buttons([button('What’s inside Pilot500 Intelligence', '#inside', 'p5-arrow')], 'is-center p5-centered'),
    ])


def features():
    return section('features', '', [
        head('Everything your results can tell you, in one place.'),
        group([
            card(ILL['report'], 'Full report', 'The complete results and recommendations, one click away.'),
            card(ILL['visualizer'], 'Visualizer', 'Explore any result by region, business unit or profile.'),
            card(ILL['styles'], 'Styles', 'Selling Styles® and Omnichannel Styles®: where each person sits against the target.'),
            card(ILL['chat'], 'Chat', 'Ask in plain language, or start from ready-made question buttons.'),
        ], 'p5-cards'),
    ])


def trust():
    ring = '''
<div class="p5-ring" data-in>
  <svg viewBox="0 0 56 56" aria-hidden="true"><circle class="bg" cx="28" cy="28" r="24"/><circle class="fg" cx="28" cy="28" r="24" pathLength="1"/></svg>
  <div><b>95%+</b><small>average response</small></div>
</div>'''
    return section('trust', 'is-dark', [
        group([heading('Built so that people answer honestly.', 2, 'p5-h2'), html(ring)], 'p5-head p5-trust-head'),
        group([
            card(ILL['anon'], 'Anonymous by design', 'Answers are collected by an external provider and reported for groups, never for an individual.'),
            card(ILL['access'], 'Access you control', 'Each member of the leadership team receives a private passcode, sent separately, and sees the view built for their role.'),
            card(ILL['only'], 'Your results only', 'The chat answers from your own Pilot500 results and the Pilot500 benchmark, not from the open internet.'),
        ], 'p5-cards is-3'),
    ])


# L3 — Split showcase ----------------------------------------------------------
def chat_html():
    ppl = ''.join(f'<svg viewBox="-6 -10 12 10.5" class="{"on" if i < 3 else ""}">{PERSON}</svg>' for i in range(10))
    answers = [
        ('Do managers read their team accurately?', f'''
<p class="p5-ans__k">The answer</p>
<p class="p5-ans__h">3 in 10 first-line managers read their team accurately.</p>
<div class="p5-ppl" aria-hidden="true">{ppl}</div>
<div class="p5-hb"><span>Accurate</span><div class="p5-hb__t"><i class="b" style="--v:30%"></i></div><b>30%</b></div>
<div class="p5-hb"><span>Not accurate</span><div class="p5-hb__t"><i style="--v:70%"></i></div><b>70%</b></div>
<p class="p5-ans__cap">Manager’s estimate against the team’s real answer · real finding, anonymised</p>
<p class="p5-act"><i></i><b>Key 5 · Leadership &amp; Management.</b> Give each manager their team’s own answers to set against their estimate in the next coaching session.</p>'''),
        ('Where is execution weakest?', '''
<p class="p5-ans__k">The answer</p>
<p class="p5-ans__h">Motivation &amp; Incentives, by a clear margin.</p>
<div class="p5-vb" aria-label="Gap between expectation and score"><div class="on"><i style="--v:92%"></i><span>Motivation</span></div><div><i style="--v:48%"></i><span>Customer</span></div><div><i style="--v:34%"></i><span>Environment</span></div></div>
<p class="p5-ans__cap">Gap between expectation and score · Pilot500 benchmark · illustrative data</p>
<p class="p5-act"><i></i><b>Key 7 · Motivation &amp; Incentives.</b> Review how top performers are recognised before the next incentive cycle.</p>'''),
        ('Which selling style should we grow?', '''
<p class="p5-ans__k">The answer</p>
<p class="p5-ans__h">Only 20% of reps are Professionals, the style that tracks with top performers.</p>
<div class="p5-hb"><span>Professionals</span><div class="p5-hb__t"><i class="b" style="--v:20%"></i></div><b>20%</b></div>
<div class="p5-hb"><span>Presenters</span><div class="p5-hb__t"><i style="--v:15%"></i></div><b>15%</b></div>
<div class="p5-hb"><span>Sellers</span><div class="p5-hb__t"><i style="--v:4%"></i></div><b>4%</b></div>
<div class="p5-hb"><span>Relationals</span><div class="p5-hb__t"><i style="--v:61%"></i></div><b>61%</b></div>
<p class="p5-ans__cap">Selling Styles® of the field team · anonymised example</p>
<p class="p5-act"><i></i><b>Selling Styles®.</b> Coach Relationals toward the sales axis: 76% of reps sit below it.</p>'''),
    ]
    chips = ''.join(f'<button type="button" class="p5-chip" aria-pressed="false">{q}</button>' for q, _ in answers)
    ans = ''.join(f'<div class="p5-ans" aria-live="polite">{a}</div>' for _, a in answers)
    return f'''
<div class="p5-panel p5-chat" data-p5="chat" role="region" aria-label="Pilot500 Intelligence chat, example">
  <div class="p5-panel__bar">
    <div class="p5-chat__id">{MARK}<div><b>Pilot500 Intelligence</b><small>Your results · 2026</small></div></div>
    <span class="p5-status">Ready</span>
  </div>
  <div class="p5-chat__log">
    <div class="p5-msg"><span></span></div>
    <ul class="p5-steps" aria-hidden="true"><li>Reading your results</li><li>Comparing with the benchmark</li><li>Choosing what to act on first</li></ul>
    {ans}
  </div>
  <div class="p5-chips" role="group" aria-label="Ready-made questions">{chips}</div>
  <div class="p5-compose" aria-hidden="true"><span class="p5-compose__t">Ask about your results</span><span class="p5-send">{SEND}</span></div>
</div>'''


def ask():
    return section('inside', 'is-alt', [
        group([
            group([
                heading('Ask your results anything.', 2, 'p5-h2'),
                para('Pilot500 Intelligence answers in plain language, from your own results and the Pilot500 benchmark. '
                     'Every answer shows what the field said, how it compares, and where to act first.', 'p5-lede'),
                buttons([button('See it in a demo', '#demo', 'is-style-outline p5-arrow p5-intent-demo')]),
            ], 'p5-split__text'),
            html(chat_html()),
        ], 'p5-split'),
    ])


KEYS = [
    ('Environment &amp; Competitiveness', 'How the field sees HCPs, the market and the competition.', 'How does the field see our competitors and the market, against us?'),
    ('Operational Marketing', 'How well marketing supports the field, and how field-oriented it is.', 'Is marketing giving the field what it really needs?'),
    ('Organization, Processes &amp; Tools', 'Whether structure, processes and tools help the field or slow it down.', 'Which processes or tools slow the field down?'),
    ('Customer &amp; Omnichannel Engagement', 'How reps engage customers across channels, and how much time they spend with them.', 'How much time do reps really spend with customers, and in which channels?'),
    ('Leadership &amp; Management', 'How managers coach, and how accurately they read their team.', 'How far is each manager’s estimate from their team’s real answer?'),
    ('Training &amp; Development', 'Whether training and field visits build the skills that matter.', 'Do field visits and training build the skills that matter?'),
    ('Motivation &amp; Incentives', 'How fair and motivating the incentive program feels.', 'How motivating does the field find our incentive program?'),
]


def pick(n, label, more, attrs=''):
    return (f'<li class="p5-pick"{attrs}><button type="button" class="p5-pick__btn" aria-expanded="false">'
            f'<span class="p5-pick__n">{n}</span><span>{label}</span></button>'
            f'<div class="p5-pick__more"><div>{more}</div></div></li>')


def ring_svg():
    cx = cy = 200
    R, n, gap = 118, 7, 5.0
    segs, nums, ticks = [], [], []
    for i in range(n):
        a0 = -90 + i * 360 / n + gap / 2
        a1 = -90 + (i + 1) * 360 / n - gap / 2
        p = lambda a, rr=R: (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)))
        x0, y0 = p(a0); x1, y1 = p(a1)
        segs.append(f'<path class="seg" tabindex="0" role="button" aria-label="Key {i + 1}" '
                    f'd="M{x0:.2f} {y0:.2f}A{R} {R} 0 0 1 {x1:.2f} {y1:.2f}"/>')
        mx, my = p((a0 + a1) / 2, R + 34)
        nums.append(f'<text class="num" x="{mx:.1f}" y="{my:.1f}">{i + 1}</text>')
    for k in range(56):
        a = math.radians(k * 360 / 56)
        ticks.append(f'<path class="tick" d="M{cx + 92 * math.cos(a):.1f} {cy + 92 * math.sin(a):.1f}L{cx + 96 * math.cos(a):.1f} {cy + 96 * math.sin(a):.1f}"/>')
    return (f'<svg viewBox="0 0 400 410" aria-hidden="true"><g class="sweep">{"".join(ticks)}</g>{"".join(segs)}{"".join(nums)}'
            f'<text class="sub" x="200" y="152">KEY</text><text class="big" x="200" y="200">05</text>'
            f'<text class="lab" x="200" y="402">Leadership &amp; Management</text></svg>')


def keys():
    items = ''.join(pick(f'{i + 1:02d}', name, f'<p>{d}</p><p class="p5-ask"><b>Ask Pilot500 Intelligence</b>“{q}”</p>',
                         f' data-name="{name}"') for i, (name, d, q) in enumerate(KEYS))
    return section('method', 'is-alt', [
        group([
            group([
                heading('Behind every answer: the 7&nbsp;Management Keys<sup>®</sup>.', 2, 'p5-h2'),
                para('Seven areas that decide how well a field organization executes. Every result, benchmark and '
                     'recommendation is organized around them.', 'p5-lede'),
                html(f'<ul class="p5-picks" id="keys-list" data-p5="picks" data-auto="6500" data-start="4" data-hover>{items}</ul>'),
            ], 'p5-split__text'),
            html(f'<div class="p5-panel is-dark p5-keys" data-p5="keys" data-for="keys-list">{ring_svg()}</div>'),
        ], 'p5-split is-flip'),
    ])


ROLES = [  # name, who, question, sees, view title, view sub, scope, nums, functional?
    ('Global leadership', 'CEO, CCO, COO and group heads', 'What is the reality inside each affiliate?',
     'Sees every country, BU and team in the group, side by side.', 'Global view', 'Every country, side by side', '', '3,9,27', False),
    ('Country leadership', 'General Manager and leadership team', 'Where should my leadership team focus this quarter?',
     'Sees the whole country: every BU and every team.', 'Country view', 'One country, every BU and team', 'g.c0', '1,3,9', False),
    ('BU leadership', 'BU heads and sales directors', 'Which of my teams need coaching first, and on what?',
     'Sees their own BU and the teams in it.', 'BU view', 'One BU and its teams', 'g.c0.b0', '–,1,3', False),
    ('Field line management', 'First-line managers', 'How does my team really see me?',
     'Sees the team they lead, with their own estimate next to the team’s real answers.', 'Team view', 'Their own team, against their estimate', 'g.c0.b0.t0', '–,–,1', False),
    ('Functional and global teams', 'Marketing, omnichannel, HR, training, incentives, sales operations, IT and CRM, global commercial',
     'Is marketing giving the field what it needs?', 'Sees every BU and country through their own function’s keys.',
     'Function view', 'Every country, through one function', '', '3,9,27', True),
]
FUNCTIONS = ['Marketing', 'Omnichannel', 'Sales operations', 'HR', 'Training', 'Incentives', 'IT &amp; CRM', 'Digital', 'Global commercial team']


def org_svg():
    out_e, out_n = [], []

    def node(k, x, y, w, h, label='', sub='', top=False, person=False):
        g = f'<g class="n{" top" if top else ""} on" data-k="{k}"><rect x="{x - w / 2:.2f}" y="{y - h / 2:.2f}" width="{w}" height="{h}" rx="2"/>'
        if person:
            g += f'<g class="p" transform="translate({x:.2f} {y + 6:.2f})">{PERSON}</g>'
        elif sub:
            g += f'<text x="{x:.2f}" y="{y - 3:.2f}">{label}</text><text class="s" x="{x:.2f}" y="{y + 5:.2f}">{sub}</text>'
        else:
            g += f'<text x="{x:.2f}" y="{y:.2f}">{label}</text>'
        out_n.append(g + '</g>')

    def edge(k, x0, y0, x1, y1):
        ym = (y0 + y1) / 2
        out_e.append(f'<path class="e on" data-k="{k}" d="M{x0:.2f} {y0}V{ym}H{x1:.2f}V{y1}"/>')

    node('g', 200, 20, 120, 28, 'Global leadership', 'CEO, CCO, COO and group heads', top=True)
    for c, cxp in enumerate([70, 200, 330]):
        ck = f'g.c{c}'
        edge(ck, 200, 34, cxp, 66)
        node(ck, cxp, 78, 92, 24, f'Country {"ABC"[c]}', 'GM and leadership team')
        for b, off in enumerate([-38, 0, 38]):
            bk = f'{ck}.b{b}'; bx = cxp + off
            edge(bk, cxp, 90, bx, 122)
            node(bk, bx, 131, 32, 18, f'BU{b + 1}')
            for t, toff in enumerate([-11, 0, 11]):
                tk = f'{bk}.t{t}'; tx = bx + toff
                edge(tk, bx, 140, tx, 168)
                node(tk, tx, 180, 9.5, 24, person=True)
    return f'<svg viewBox="0 0 400 196" role="img" aria-label="Org chart: group, three countries, nine business units, twenty-seven teams">{"".join(out_e)}{"".join(out_n)}</svg>'


def roles():
    items = ''.join(pick('', f'{n}<small>{who}</small>', f'<p><b>“{q}”</b>{sees}</p>',
                         f' data-role="{n}" data-view="{v}" data-sub="{s}" data-scope="{sc}" data-nums="{nums}"{" data-fn" if fn else ""}')
                    for n, who, q, sees, v, s, sc, nums, fn in ROLES)
    fns = ''.join(f'<span>{f}</span>' for f in FUNCTIONS)
    panel = f'''
<div class="p5-panel p5-org" data-p5="org" data-for="roles-list">
  <div class="p5-panel__bar"><span class="p5-org__view">Viewing as <b>Global leadership</b></span><span class="p5-org__key"><span>Open to this role</span><span>Not available</span></span></div>
  <div class="p5-org__chart">{org_svg()}</div>
  <div class="p5-org__fns" aria-label="Functions">{fns}</div>
  <div class="p5-org__foot">
    <div><b>Global view</b><small>Every country, side by side</small></div>
    <div class="p5-org__nums"><div><span>3</span><small>countries</small></div><div><span>9</span><small>BUs</small></div><div><span>27</span><small>teams</small></div></div>
  </div>
</div>'''
    return section('roles', 'is-alt', [
        group([
            group([
                heading('A view for every leader, from the Group to the field.', 2, 'p5-h2'),
                html(f'<ul class="p5-picks p5-roles" id="roles-list" data-p5="picks" data-auto="5500">{items}</ul>'),
            ], 'p5-split__text'),
            html(panel),
        ], 'p5-split'),
    ])


FILM_ROWS = [('Marketing', 72, 'Strong'), ('Training', 58, 'OK'), ('Incentives', 26, 'Weak', True),
             ('Management', 34, 'Weak', True), ('Tools', 64, 'OK'), ('Time with customers', 50, 'Mixed')]
FILM_CAPS = ['Set the <em>plan</em>.', 'It loses strength.', 'You can’t see where.', '<em>Pilot500</em> asks the field.',
             'Now you see <em>exactly where</em>.', 'Where to act <em>first</em>.']


def film_html():
    rows = ''.join(
        f'<li class="p5-row{" is-act" if len(r) > 3 else ""}" style="--keep:{r[1]}%"><span>{r[0]}</span>'
        f'<span class="p5-row__t"><i></i></span><span class="p5-row__s"><span class="q">?</span><span class="v">{r[2]}</span></span></li>'
        for r in FILM_ROWS)
    caps = ''.join(f'<p data-s="{i + 1}">{c}</p>' for i, c in enumerate(FILM_CAPS))
    return f'''
<figure class="p5-panel p5-film" data-p5="film" data-step="6" aria-label="Short film: how the plan loses strength between head office and the field, and how Pilot500 shows where">
  <div class="p5-film__top"><span><b>Your plan</b> → <b>Growth</b></span><span>Execution intelligence</span></div>
  <div class="p5-film__cap" aria-hidden="true">{caps}</div>
  <ol class="p5-film__rows">{rows}<li class="p5-film__scan" aria-hidden="true"></li></ol>
  <div class="p5-film__foot"><span class="p5-film__prog" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span>
    <button type="button" class="p5-replay"><svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M10 6a4 4 0 1 1-1.2-2.9M10 1.5V4H7.5"/></svg>Replay</button></div>
  <figcaption class="p5-vh">Set the plan. It loses strength across marketing, training, incentives, management, tools and time with customers, and you can’t see where. Pilot500 asks the field; now you see exactly where, and where to act first.</figcaption>
</figure>'''


def how():
    weeks = [('Week 1', 'The GM speaks to the field', 'A save-the-date, then a message from the General Manager: your input is important to our success.'),
             ('Week 4', 'One shared day', 'The whole team contributes on one shared day. Online inputs are gathered and tracked.'),
             ('Week 8', 'Pilot500 Intelligence opens', 'The executive team gets online access to all results, and a 3-hour workshop at your HQ turns them into priorities, with a shareable PowerPoint for your teams.')]
    items = ''.join(pick(w, t, f'<p>{d}</p>') for w, t, d in weeks)
    return section('how', 'is-alt', [
        group([
            group([
                heading('From kick-off to answers in eight weeks.', 2, 'p5-h2'),
                para('Your plan loses strength somewhere between head office and the customer. Pilot500 asks the whole field team, and shows you where.', 'p5-lede'),
                html(f'<ol class="p5-picks p5-weeks" id="weeks-list" data-p5="picks" data-auto="5000">{items}</ol>'),
            ], 'p5-split__text'),
            html(film_html()),
        ], 'p5-split is-flip'),
        cta('Start here', 'A short call, then your results in eight weeks.', 'Plan your eight weeks', '#demo', 'p5-intent-talk'),
    ])


# L4 — Proof wall --------------------------------------------------------------
QUOTES = [('Pilot500 gives me detailed instruments in my cockpit.', 'CEO', 'Global French company'),
          ('Pilot500 gave us new and unique vision about real strengths and weaknesses of the whole commercial operations.', 'President and CEO', 'Global Swiss pharma group'),
          ('The detail showed weak points in our field force and marketing that head office had underestimated.', 'Country President', 'Global Italian company'),
          ('After only eight weeks, our new GM in Japan had clear ideas for improvement.', 'Head of Operational Excellence EMEA', 'Global Japanese company'),
          ('Used regularly, it shows us whether head-office actions really reach the field.', 'Global Head of Commercial Excellence', 'German company'),
          ('It showed us the low-hanging fruit for quick results, and gave us a roadmap.', 'EVP International', 'Global US biotech company')]


def proof():
    qs = ''.join(f'<figure class="p5-quote"><blockquote>“{q}”</blockquote><figcaption><b>{r}</b> · {c}</figcaption></figure>' for q, r, c in QUOTES)
    dots = ''.join(f'<button type="button" aria-label="Quote {i + 1}"></button>' for i in range(len(QUOTES)))
    arrow = lambda d: f'<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5"><path d="{d}"/></svg>'
    col_a = ''.join(f'<li>{logo_img(c)}</li>' for c in CLIENTS[12:18] + CLIENTS[0:6])
    col_b = ''.join(f'<li>{logo_img(c)}</li>' for c in CLIENTS[18:24] + CLIENTS[6:12])
    return section('customers', '', [
        head('Pharma’s leading groups have already done it.'),
        html(f'''
<div class="p5-proof p5-reveal">
  <div class="p5-quotes" data-p5="quotes" role="region" aria-label="What clients say">
    {qs}
    <div class="p5-quotes__ctl"><div class="p5-dots">{dots}</div>
      <div class="p5-arrows"><button type="button" data-prev aria-label="Previous quote">{arrow("M7.5 2.5 4 6l3.5 3.5")}</button><button type="button" data-next aria-label="Next quote">{arrow("M4.5 2.5 8 6 4.5 9.5")}</button></div></div>
  </div>
  <div class="p5-wall" aria-label="Clients">
    <div class="p5-wall__col"><ul>{col_a}</ul></div>
    <div class="p5-wall__col is-down"><ul>{col_b}</ul></div>
  </div>
</div>'''),
        cta('Join them', 'Put execution intelligence to work, like they did.', 'Get a case study', '#demo', 'p5-intent-case'),
    ])


# L5 — Stat band ---------------------------------------------------------------
def value():
    sizes = [100, 250, 500, 1000, 2000]
    eur = lambda m: '€' + (f'{m:,}' if m >= 1000 else f'{m:g}') + 'M'
    bars = ''.join(
        f'<button type="button" class="p5-cbar" data-m="{m}" style="--h:{max(3, m / 2000 * 82):.1f}%" aria-pressed="false">'
        f'<span class="p5-cbar__c"><i></i><b>{eur(round(m * 0.019, 2))}</b></span><span>{eur(m)}</span></button>' for m in sizes)
    calc = f'''
<div class="p5-panel p5-calc p5-reveal" data-p5="calc">
  <div class="p5-calc__in">
    <label class="p5-kicker" for="p5-rev">On an affiliate with revenue of</label>
    <p class="p5-calc__rev" data-rev>€500M</p>
    <input class="p5-range" id="p5-rev" type="range" min="0" max="4" step="1" value="2">
    <p class="p5-kicker">1.9 points of revenue growth, the gap McKinsey measured, is</p>
    <p class="p5-calc__out" data-out aria-live="polite">€9.5M</p>
    <p class="p5-body" style="color:var(--p5-navy-text)">of revenue.</p>
  </div>
  <div class="p5-calc__in">
    <p class="p5-kicker">The same 1.9 points, at five sizes of affiliate</p>
    <div class="p5-cbars">{bars}</div>
  </div>
  <p class="p5-calc__note">Arithmetic on the gap McKinsey measured between commercial leaders and their peers. It shows the size of a difference, not what any program will deliver, and not a forecast.</p>
</div>'''
    fig = lambda n, body, src: group([para(n, 'p5-fig__n'), para(body, 'p5-body'), para(src, 'p5-note')], 'p5-fig p5-reveal')
    return section('value', '', [
        head('Executives know the execution gap is costly.', 'Improving execution increases sales and profits.'),
        group([
            fig('40%', 'of a strategy’s potential value is lost to breakdowns in execution, according to executives.', 'Harvard Business Review, 2017 · Bain &amp; Company'),
            fig('+1.9 pts', 'higher revenue growth than peers in the same sector, for businesses with superior commercial capabilities.', 'McKinsey, 2018 · 200 clients assessed'),
            fig('+4.7 pts', 'higher earnings growth than the same peers, for the same businesses.', 'McKinsey, 2018 · same assessment'),
        ], 'p5-figs'),
        html(calc),
        cta('Your own numbers', 'See the gap in your own affiliate.', 'Discuss your numbers', '#demo', 'p5-intent-talk'),
    ])


# L7 — Contact -----------------------------------------------------------------
def demo():
    days = ''.join(f'<span>{d}</span>' for d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    chev = lambda d: f'<svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5"><path d="{d}"/></svg>'
    form = f'''
<div class="p5-form" data-p5="demo">
  <form action="#" novalidate>
    <label for="p5-intent">I would like to</label>
    <select class="p5-field" id="p5-intent" name="intent">
      <option value="demo">See Pilot500 Intelligence in a demo</option>
      <option value="case">Receive a case study</option>
      <option value="talk">Talk to the team about my program</option>
    </select>
    <div class="p5-cal" aria-label="Choose a day and time">
      <div>
        <div class="p5-cal__hd"><button type="button" data-cal-prev aria-label="Previous month">{chev("M6.5 2 3.5 5l3 3")}</button><span class="p5-cal__t">November 2026</span><button type="button" data-cal-next aria-label="Next month">{chev("M3.5 2l3 3-3 3")}</button></div>
        <div class="p5-cal__g">{days}</div>
      </div>
      <div class="p5-slots"><small>Pick a day</small><button type="button">09:00</button><button type="button" class="is-on">10:30</button><button type="button">14:00</button><button type="button">15:30</button></div>
    </div>
    <p class="p5-note">Illustration. The live calendar (e.g. Calendly) replaces this block.</p>
    <div class="p5-form__row">
      <div><label for="p5-name">Name</label><input class="p5-field" id="p5-name" name="name" placeholder="Your name" required></div>
      <div><label for="p5-role">Role</label><select class="p5-field" id="p5-role" name="role" required><option value="">Choose your role</option><option>CEO or President</option><option>Chief Operating Officer</option><option>Chief Commercial Officer</option><option>Regional or cluster head</option><option>General Manager or country head</option><option>Global commercial excellence</option><option>Other</option></select></div>
    </div>
    <div class="p5-form__row">
      <div><label for="p5-co">Company</label><input class="p5-field" id="p5-co" name="company" placeholder="Your company" required></div>
      <div><label for="p5-mail">Work email</label><input class="p5-field" id="p5-mail" name="email" type="email" placeholder="name@company.com" required></div>
    </div>
    <div class="wp-block-buttons"><div class="wp-block-button is-light p5-arrow"><a class="wp-block-button__link wp-element-button" href="#demo">Book a demo</a></div></div>
    <p class="p5-sent" role="status">Request received. We’ll be in touch within one working day.</p>
  </form>
</div>'''
    ticks = ''.join(f'<li>{t}</li>' for t in [
        'The chat answering the questions your leadership team asks',
        'The same results as a region head and a first-line manager would see them',
        'How each manager drafts an action plan from their own results',
        'How a program would run for your countries and teams'])
    return section('demo', 'is-dark', [
        group([
            group([
                heading('See what it would show about your organization.', 2, 'p5-h2'),
                para('A private call, on an anonymised example. You will see:', 'p5-lede'),
                html(f'<ul class="p5-ticks">{ticks}</ul>'),
                para('Prefer email? <a href="mailto:contact@pilot500.com">contact@pilot500.com</a>', 'p5-note'),
            ]),
            html(form),
        ], 'p5-contact'),
    ])


# ------------------------------------------------------------ header / footer
NAV = [('Platform', '#inside'), ('Customers', '#customers'), ('Who it is for', '#roles'), ('How it works', '#how')]


def header(static=False):
    brand = html(f'<a class="p5-brand" href="/" aria-label="Pilot500 home">{LOGO}</a>')
    if static:
        nav = html('<nav class="p5-nav wp-block-navigation" aria-label="Main"><ul class="wp-block-navigation__container">' + ''.join(
            f'<li class="wp-block-navigation-item"><a class="wp-block-navigation-item__content" href="{u}"><span class="wp-block-navigation-item__label">{l}</span></a></li>'
            for l, u in NAV) + '</ul></nav>')
    else:
        nav = ('<!-- wp:navigation {"overlayMenu":"never","className":"p5-nav","ariaLabel":"Main"} -->\n'
               + ''.join(f'<!-- wp:navigation-link {{"label":"{l}","url":"{u}","kind":"custom","isTopLevelLink":true}} /-->\n' for l, u in NAV)
               + '<!-- /wp:navigation -->\n')
    right = group([
        buttons([button('Taking the survey?', '#survey')]),
        html('<button type="button" class="p5-menu-btn" aria-label="Menu" aria-expanded="false"><span></span></button>'),
    ], 'p5-hd__right')
    return group([brand, nav, right], 'p5-w p5-hd__in')


def footer():
    cols = [('Platform', ['Pilot500 Intelligence', 'Full report', 'Visualizer']),
            ('Method', ['7 Management Keys®', 'Typologies®', 'GM Playbook®', 'Eight weeks']),
            ('Company', ['About Pilot500', 'Customers', 'Contact', 'Legal'])]
    c = ''.join(f'<div><h4>{t}</h4><ul>' + ''.join(f'<li><a href="#">{x}</a></li>' for x in xs) + '</ul></div>' for t, xs in cols)
    li = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM.22 8h4.56v14H.22V8zm7.5 0h4.37v1.92h.06c.61-1.15 2.1-2.37 4.32-2.37 4.62 0 5.47 3.04 5.47 7v7.45h-4.56v-6.6c0-1.58-.03-3.6-2.2-3.6-2.2 0-2.53 1.71-2.53 3.48v6.72H7.72V8z"/></svg>'
    return html(f'''
<div class="p5-w">
  <div class="p5-ft__grid">
    <div><a class="p5-brand" href="/" aria-label="Pilot500 home" style="color:#fff">{LOGO}</a><p class="p5-ft__tag">Improving Execution Together.</p>
      <a class="p5-ft__social" href="#" aria-label="Pilot500 on LinkedIn">{li}</a></div>
    {c}
  </div>
  <div class="p5-ft__base"><span>© 2026 Pilot500. Pilot500®, 7 Management Keys®, Typologies® and GM Playbook® are Pilot500 marks.</span><span>EN · FR</span></div>
</div>''')


# ------------------------------------------------------------------- patterns
PATTERNS = [  # slug, title, layout, description, builder
    ('hero', 'Hero', 'L1 Hero', 'Headline, intro, two buttons, the stats panel and the client logo strip.', hero),
    ('gain', 'What you gain', 'L2 Card grid', 'Centered heading, four illustrated cards and a button.', gain),
    ('ask', 'Ask your results (chat)', 'L3 Split showcase', 'Text beside the animated Pilot500 Intelligence chat window.', ask),
    ('features', 'Inside Pilot500 Intelligence', 'L2 Card grid', 'Centered heading and four feature cards.', features),
    ('keys', '7 Management Keys', 'L3 Split showcase', 'Interactive list of the seven keys beside the ring.', keys),
    ('customers', 'Customers', 'L4 Proof wall', 'Quote slider beside the moving client logo wall, then a CTA banner.', proof),
    ('roles', 'Who it is for', 'L3 Split showcase', 'Role list beside the org chart that shows what each role sees.', roles),
    ('value', 'What it is worth', 'L5 Stat band', 'Three sourced figures, the revenue calculator and a CTA banner.', value),
    ('how', 'How it works', 'L3 Split showcase', 'Week steps beside the short film, then a CTA banner.', how),
    ('trust', 'Trust and privacy', 'L2 Card grid (dark)', 'Heading, response ring and three cards on navy.', trust),
    ('demo', 'Book a demo', 'L7 Contact', 'Text and the demo request form with calendar.', demo),
]
SINGLE = [('cta-banner', 'CTA banner', 'L6 CTA banner', 'Blue banner with a short line and one button.',
           lambda: group([group([cta('Start here', 'A short call, then your results in eight weeks.', 'Book a demo', '#demo')], 'p5-w')], 'p5 p5-band is-tight', 'section'))]


def php_assets(s):
    return re.sub(r'@@ASSET:([^@]+)@@', lambda m: f"<?php echo esc_url( get_theme_file_uri( 'assets/{m.group(1)}' ) ); ?>", s)


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def build():
    markup = {}
    for slug, title, layout, desc, fn in PATTERNS + SINGLE:
        m = fn()
        markup[slug] = m
        write(os.path.join(THEME, 'patterns', f'{slug}.php'),
              f"<?php\n/**\n * Title: {title}\n * Slug: pilot500/{slug}\n * Categories: pilot500\n"
              f" * Keywords: pilot500, {layout.lower()}\n * Description: {layout}. {desc}\n * Viewport Width: 1440\n */\n?>\n"
              + php_assets(m))
    # full page pattern for new pages
    write(os.path.join(THEME, 'patterns', 'home.php'),
          "<?php\n/**\n * Title: Pilot500 home page\n * Slug: pilot500/home\n * Categories: pilot500\n * Post Types: page\n"
          " * Description: Every section of the home page, in order.\n * Viewport Width: 1440\n */\n?>\n"
          + ''.join(f'<!-- wp:pattern {{"slug":"pilot500/{p[0]}"}} /-->\n' for p in PATTERNS))

    write(os.path.join(THEME, 'parts', 'header.html'), header())
    write(os.path.join(THEME, 'parts', 'footer.html'), footer())
    tp_head = '<!-- wp:template-part {"slug":"header","tagName":"header","className":"p5 p5-hd"} /-->\n'
    tp_foot = '<!-- wp:template-part {"slug":"footer","tagName":"footer","className":"p5 p5-ft"} /-->\n'
    write(os.path.join(THEME, 'templates', 'front-page.html'),
          tp_head + '<!-- wp:group {"tagName":"main","className":"p5-main"} -->\n<main class="wp-block-group p5-main">'
          + ''.join(f'<!-- wp:pattern {{"slug":"pilot500/{p[0]}"}} /-->\n' for p in PATTERNS) + '</main>\n<!-- /wp:group -->\n' + tp_foot)
    page = (tp_head + '<!-- wp:group {"tagName":"main","className":"p5-main"} -->\n<main class="wp-block-group p5-main">'
            '<!-- wp:post-content {"layout":{"type":"default"}} /--></main>\n<!-- /wp:group -->\n' + tp_foot)
    write(os.path.join(THEME, 'templates', 'page.html'), page)
    write(os.path.join(THEME, 'templates', 'index.html'), page)

    # ---------------- static preview (same markup, block comments removed)
    strip = lambda s: re.sub(r'<!-- /?wp:[^>]*-->\n?', '', s)
    body = (f'<header class="wp-block-template-part p5 p5-hd">{strip(header(static=True))}</header>\n<main class="p5-main">'
            + ''.join(strip(markup[p[0]]) for p in PATTERNS)
            + f'</main>\n<footer class="wp-block-template-part p5 p5-ft">{strip(footer())}</footer>')
    fonts = ''.join(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;src:url(@@ASSET:fonts/{f}-{w}.woff2@@) format('woff2')}}\n"
                    for fam, f, ws in [('Bai Jamjuree', 'BaiJamjuree', [300, 400, 500, 600]), ('IBM Plex Sans', 'IBMPlexSans', [400, 500, 600])] for w in ws)
    page_html = lambda css, js: f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pilot500 — Improving Execution Together</title>
<meta name="description" content="Pilot500 tracks your commercial execution in 8 weeks and tells you exactly where your management team stands and what your affiliate needs to do.">
<script>document.documentElement.classList.add('p5-js')</script>
{css}
</head>
<body class="p5">
{body}
{js}
</body>
</html>
'''
    rel = lambda s: re.sub(r'@@ASSET:([^@]+)@@', r'../theme/pilot500/assets/\1', s)
    write(os.path.join(ROOT, 'preview', 'index.html'), rel(page_html(
        f'<style>\n{fonts}</style>\n<link rel="stylesheet" href="@@ASSET:css/site.css@@">',
        '<script src="@@ASSET:js/site.js@@"></script>')))

    # self-contained single file
    def data_uri(m):
        p = os.path.join(THEME, 'assets', m.group(1))
        mime = {'woff2': 'font/woff2', 'png': 'image/png', 'svg': 'image/svg+xml'}[p.rsplit('.', 1)[1]]
        return f'data:{mime};base64,' + base64.b64encode(open(p, 'rb').read()).decode()
    css = open(os.path.join(THEME, 'assets', 'css', 'site.css'), encoding='utf-8').read()
    js = open(os.path.join(THEME, 'assets', 'js', 'site.js'), encoding='utf-8').read()
    single = page_html(f'<style>\n{fonts}\n{css}</style>', f'<script>\n{js}</script>')
    write(os.path.join(ROOT, 'dist', 'pilot500-preview.html'), re.sub(r'@@ASSET:([^@]+)@@', data_uri, single))

    # theme zip
    zp = os.path.join(ROOT, 'dist', 'pilot500-theme.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for d, _, files in os.walk(THEME):
            for f in files:
                full = os.path.join(d, f)
                z.write(full, os.path.join('pilot500', os.path.relpath(full, THEME)))
    print('built', len(PATTERNS) + len(SINGLE) + 1, 'patterns →', os.path.relpath(zp, ROOT))


if __name__ == '__main__':
    build()
