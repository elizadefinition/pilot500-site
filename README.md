# Pilot500 site

Refined build of the Pilot500 home page as a **WordPress block theme**. Every section is a block pattern, and all sections sit on **seven shared layouts**, so the page reads as one system instead of nine one-off modules.

- **Brand blue:** `#134A83`. It replaces the client's green everywhere.
- **Fonts:** Bai Jamjuree for headings and IBM Plex Sans for body text. Both are self-hosted.
- **No dependencies:** one CSS file and one small vanilla JS file.

## Quick look

- `dist/pilot500-preview.html` is a single self-contained file. Open it in any browser.
- `preview/index.html` is the same page, loading the theme's real CSS and JS.

## Install on WordPress (6.5+)

1. Go to **Appearance → Themes → Add New → Upload** and choose `dist/pilot500-theme.zip`. Then activate it.
2. The front page template already contains every section in order.
3. To build other pages, open **Patterns → Pilot500** in the editor. You can insert any section, or the full **Pilot500 home page** pattern.

Copy, headings and buttons are normal editable blocks. The interactive visuals are **Custom HTML** blocks inside each pattern. Their content is plain HTML that you can edit in place.

## The 7 shared layouts

| Layout | Used by | What it is |
|---|---|---|
| L1 Hero | Hero | Headline and buttons beside the stats panel, then the client logo strip |
| L2 Card grid | What you gain · Inside Pilot500 Intelligence · Trust (dark) | Centered heading above 3–4 illustrated cards |
| L3 Split showcase | Ask (chat) · 7 Keys · Who it is for · How it works | Text column beside an interactive panel. Add `is-flip` to swap sides |
| L4 Proof wall | Customers | Quote slider beside a moving logo wall |
| L5 Stat band | What it is worth | Three sourced figures above the revenue calculator |
| L6 CTA banner | After Customers, Value and How it works | Blue banner with one line and one button |
| L7 Contact | Book a demo | Text beside the request form and calendar |

## Animation rules

- Every animated visual sits inside a `.p5-panel` or `.p5-thumb`. These containers clip their own content (`overflow:hidden; contain:paint`), so nothing can draw outside its canvas. The client's original had several visuals escaping their bounds.
- Loops (chat, film, keys, roles, quotes) only run while the panel is on screen. They pause on hover and stop auto-advancing once the visitor clicks.
- With `prefers-reduced-motion`, there is no autoplay. Each visual shows its finished state.
- The hero film has moved from the hero to **How it works**. It now plays as a contained six-step story beside the week steps, and has a Replay button.

## Scroll animations

These are all added by `site.js` when the page loads. The block markup stays the same, so editors never see extra wrappers.

- **Headings:** section headings rise word by word as they enter the viewport. The intro text, buttons and lists below each heading follow just after.
- **Side panels:** the hero stats, chat, keys ring, org chart and film unmask as they arrive.
- **Big figures:** 40%, +1.9 pts and +4.7 pts count up.
- **Parallax:** on desktop only, the stats panel and side panels drift slightly as you scroll, by no more than 14px.
- **Header:** a blue progress line shows how far down the page you are, and the nav underlines the section you are in.
- **Reduced motion:** all of this is switched off for visitors who prefer reduced motion.

## Editing the source

`tools/build.py` generates the patterns, template parts, templates, preview and zip from one place:

```
python3 tools/build.py
```

Styles are in `theme/pilot500/assets/css/site.css`, which is organised by layout. Behaviour is in `theme/pilot500/assets/js/site.js`, where each module hooks onto a `data-p5="…"` attribute.

## Before launch

- **7 Keys profile chart:** the scores (and the benchmark of 63) in the keys panel are illustrative. Set them in `KEY_SCORES` and `KEY_BENCH` in `tools/build.py`, or edit the pattern directly.
- **"Ask your results anything."** is new placeholder copy, written to replace "Subheading in here". It needs client approval.
- The form is a front-end demo only. To make it work, connect a form plugin (Gravity Forms, WPForms or Contact Form 7) or a Calendly embed in the **Book a demo** pattern.
- **Testimonials:** two are verbatim and four are paraphrased (per the client's own note). They need approved wording.
- **Findings:** the chat findings and the film ratings are illustrative. They need client sign-off for public use.
