# AI Tells — Anti-Slop Catalog

The concrete signatures that make an interface read as AI-generated. Consult this
when refining a design and run the Pre-Flight checklist at the bottom before
shipping. Rules are framework-neutral; Tailwind-style class names appear only as
illustrative examples.

Every rule has an **override**: a tell is only a tell when it fires by default. If
the brief explicitly calls for the pattern, use it with intent.

---

## 1. Copy & content

- **No generic placeholder names.** "John Doe", "Sarah Chan", "Jane Doe" → use
  realistic, locale-appropriate names.
- **No startup-slop brand names.** "Acme", "Nexus", "SmartFlow", "Cloudly" →
  invent contextual names that sound real.
- **No filler verbs.** "Elevate", "Seamless", "Unleash", "Next-Gen",
  "Revolutionize", "Supercharge" → concrete verbs only.
- **No fake-precise numbers.** Invented spec-precision (`92%`, `4.1×`, `5.8 mm`,
  `13.4 lb`, `99.99%`) is banned unless it comes from real data or is explicitly
  labeled as sample/mock. Don't fake engineering precision the brand doesn't claim.
- **No cute-but-broken copy.** Forced metaphors, mock-poetic micro-meta,
  passive-aggressive humility ("two plans but one is honest"), performative-craftsman
  labels ("From the field", "On our desks", "Loose plates"). Re-read every visible
  string; if a phrase doesn't clearly make sense, replace it with a plain functional
  sentence. Boring copy beats cute-wrong copy.
- **One copy register per page.** Don't mix technical mono, editorial prose, and
  marketing punch unless the brand voice explicitly calls for it.

## 2. The em-dash ban

The em-dash (`—`) and separator en-dash (`–`) are the #1 typographic tell in
generated page copy. Banned in **all visible page text**: headlines, eyebrows,
pills, body, quotes, attribution, captions, buttons, alt text. (This governs the
*designed page you output*, not your chat replies.)

Rewrite instead: two sentences with a period, a comma, parentheses, or a colon.
Ranges use a plain hyphen (`2018-2026`, `€40-80k`). Quote attribution uses ` - `
with spaces or a line break. The only permitted dashes on the page are the regular
hyphen and the math minus.

## 3. Typography tells

- **No oversized H1s that just scream.** Control hierarchy with weight and color,
  not raw scale.
- **No mixed-family emphasis.** To emphasize a word in a headline, use italic or
  bold of the *same* font. Injecting a random serif word into a sans headline (or
  vice versa) is amateur.
- **Italic descender clearance.** When an italic display word contains `y g j p q`,
  tight line-height clips the descender. Use `line-height: 1.1` minimum plus a
  little bottom padding on the wrapper.
- (Font selection itself is governed by the main skill's Step 3 — distinctive
  display + refined body, avoid Inter/Roboto/Arial as defaults.)

## 4. Color tells

- **No default AI-purple / blue glow.** No automatic purple button glows, neon
  gradients, or violet-on-white. Use neutral bases (zinc/slate/stone) with one
  high-contrast accent. Override: if the brand asks for purple, execute it with a
  consistent, harmonized palette.
- **One accent, locked across the whole page.** A warm-grey site does not suddenly
  get a blue CTA in section 7. Pick one accent and audit every component.
- **Premium-consumer palette ban.** For cookware / wellness / artisan / luxury /
  DTC-heritage briefs, the default AI reach is warm beige/cream + brass/clay/oxblood
  + espresso near-black. It makes every such brand look identical. Reach for a
  different family instead (cold luxury silver-grey, forest green + amber, black +
  tan, cobalt + cream, terracotta + slate, or monochrome + one saturated pop) unless
  the brand explicitly names those colors.
- **No pure `#000` or `#fff`.** Off-black and off-white preserve depth.
- **Tint shadows to the background hue.** No pure-black drop shadows on light
  backgrounds.

## 5. Layout & composition tells

- **No three equal feature cards.** The generic horizontal trio is banned. Use a
  2-column zigzag, an asymmetric grid, or a scroll/horizontal alternative.
- **No layout-family repetition.** Once a section uses a layout family (3-col cards,
  full-width quote, split text/image), it appears at most once. An 8-section page
  uses at least 4 different families.
- **Zigzag cap.** Max 2 consecutive "image left / text right" then "text left /
  image right" sections. The 3rd in a row is a fail; break it with a full-width,
  stacked, bento, or marquee section.
- **Bento cell count.** A bento grid has exactly as many cells as you have content
  for. No empty tile in the middle or at the end. Vary tile sizes — don't stack six
  identical image+text rows.
- **Bento background diversity.** Not every cell is white-on-white text. At least
  2-3 cells need real visual variation (image, brand-appropriate gradient, pattern,
  tint).
- **No split-header pattern by default.** "Left big headline + right small floating
  explainer paragraph" as a section header is a tell. Stack headline over body
  instead, unless the right column carries a real visual/interactive element.
- **No marquee spam.** At most one horizontal scrolling text/logo marquee per page.

## 6. Decoration tells (the eyebrow family)

- **Eyebrow restraint** (the most-violated rule). An eyebrow is the small
  uppercase wide-tracking label above a section headline (`SELECTED WORK`,
  `THE HARDWARE`). AI puts one above every section, creating a templated rhythm.
  **Max 1 eyebrow per 3 sections** (hero counts as one). Mechanical check: count
  the small-caps micro-labels; if the count exceeds `ceil(sections / 3)`, cut some.
  Usually the headline alone is enough.
- **No section-number eyebrows.** `00 / INDEX`, `001 · Capabilities`,
  `06 · how it works`, `01 / 4` pagination on tiles. If the user can count, they
  don't need the label.
- **No generic step labels.** "Stage 1 / 2 / 3", "Phase 01 / 02 / 03". The step
  content is the label — use the verb ("Install", "Configure", "Ship").
- **Rationed middle-dot (`·`).** Max one per metadata line. Don't use it as the
  universal separator ("foo · bar · baz · qux").
- **No decorative status dots.** A colored dot before every nav item / list row /
  badge is a tell. Allowed only for real semantic state (live server status,
  availability flag), used sparingly.
- **No scroll cues.** "Scroll", "↓ scroll", "Scroll to explore", animated
  mouse-wheel icons. If the user hasn't scrolled, they're on the hero; they know
  scroll exists.
- **No locale / time / weather strips.** "Lisbon 14:23 · 18°C" in a nav/footer,
  atmospheric city-name strips. Allowed only for a genuinely place- or
  timezone-relevant brief. A plain contact address in the footer is fine.
- **No version stamps on marketing pages.** `v1.4.2`, `Build 0048`,
  `last sync 4s ago`. These are devtool fixtures, not landing-page content.
- **No decoration text strip at hero bottom.** `BRAND. MOTION. SPATIAL.`,
  `DESIGN · BUILD · SHIP` mono-caps strips. Allowed only if the strip carries real
  navigable links or real status.
- **No pills/labels overlaid on images**, and **no photo-credit captions as
  decoration** (`Frame XII · 35mm`). Real photo credit for a real photographer is
  fine; invented ones are pretentious.

## 7. Fake-asset tells

- **No `<div>`-based fake screenshots.** Fake task lists, fake terminals, fake
  dashboards built from styled rectangles are the single biggest AI-design tell. To
  show a product: use a real screenshot, a generated image, a real mini component
  preview, or skip the preview.
- **No hand-rolled SVG icons.** Use a real icon library and one family per project
  with a consistent stroke width. Icons from a library are fine; hand-drawn
  decorative SVG illustrations are discouraged as default.
- **Even minimalist sites need real images.** A pure-text page is incomplete work,
  not minimalism. When no image tool is available, use seeded placeholder photos
  (e.g. `picsum.photos/seed/<descriptive-seed>/w/h`) or leave clearly-labeled
  placeholder slots and tell the user what images are needed — don't paper over it
  with a gradient blob.
- **Real logos for social proof.** A "Trusted by" wall uses real SVG logos (e.g.
  Simple Icons) or generated marks for invented brands, not plain text wordmarks.
  Logo wall = logos only; no category label under each logo. It lives *under* the
  hero, never inside it.

## 8. Interactive-state tells

- **No static-success-only UI.** Implement the full cycle: loading (skeletons that
  match the final shape, not generic spinners), empty states, error states.
- **Button contrast.** Every CTA's text must pass WCAG AA against its own
  background. No white-on-white, no transparent button over a busy background
  without a scrim/stroke.
- **No CTA label wrapping** to 2+ lines at desktop. Shorten the label (3 words max)
  or widen the button.
- **No duplicate CTA intent.** "Get in touch" + "Let's talk" + "Start a project" on
  one page = pick one label and use it everywhere.
- **Labels above inputs**, never placeholder-as-label.

## 9. Motion tells (when motion is in scope)

- **Motion must be motivated.** Each animation communicates hierarchy, storytelling,
  feedback, or a state transition. "It looked cool" is not a reason. If you can't
  justify it in one sentence, drop it.
- **Claimed motion = shown motion.** Don't promise a lively page and ship something
  static, and don't half-build motion that breaks (cut-off scroll triggers, jumpy
  enters). If you can't ship working motion, ship a clean static page.
- **Honor `prefers-reduced-motion`.** Anything beyond hover/active states collapses
  to static under reduced motion.
- **Animate only `transform` and `opacity`** (GPU-composited). Never animate
  `top`/`left`/`width`/`height`. Avoid per-frame scroll listeners in state.

---

## Pre-Flight Checklist

Run before declaring a design done. If a box can't be honestly ticked, it's not done.

- [ ] **Design Read** stated (one line: page kind, audience, vibe)?
- [ ] **Zero em-dashes** (`—`/`–`) anywhere in visible page text?
- [ ] **One theme** (light/dark/auto) locked for the whole page — no section flips?
- [ ] **One accent color** used identically across all sections?
- [ ] **One corner-radius system** applied consistently?
- [ ] **Font choice** distinctive, not a default (Inter/Roboto/Arial/system)?
- [ ] **Hero fits the viewport**: headline ≤ 2 lines, short subtext, CTA visible
      without scroll?
- [ ] **Eyebrow count** ≤ `ceil(sections / 3)` (hero counts as one)?
- [ ] **No layout-family repeated**; ≥ 4 families across a long page; zigzag ≤ 2 in
      a row?
- [ ] **Bento** has exactly N cells for N items, with background variety?
- [ ] **CTA** text passes contrast, fits one line, no duplicate-intent CTAs?
- [ ] **Real images** used (no `<div>` fake screenshots, no hand-rolled decorative
      SVG, no pure-text minimalism)?
- [ ] **No decoration tells**: section-number eyebrows, decorative dots, scroll
      cues, locale/time strips, version stamps, hero-bottom text strips?
- [ ] **Copy self-audit** done: no placeholder names, slop brand names, filler
      verbs, fake-precise numbers, or cute-broken phrases?
- [ ] **Interactive states**: loading / empty / error provided; labels above inputs?
- [ ] **Motion** (if any) motivated, actually shown, reduced-motion honored?
- [ ] **Responsive**: high-variance layouts collapse cleanly to single column on
      mobile?
