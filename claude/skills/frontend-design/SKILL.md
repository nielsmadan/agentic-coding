---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use when the user asks to build web components, pages, artifacts, posters, or applications (websites, landing pages, dashboards, React components, HTML/CSS layouts) or when styling/beautifying any web UI.
argument-hint: <component or page description>
---

# Frontend Design

Build distinctive, production-grade frontend interfaces that avoid generic AI aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

## Instructions

### Step 1: Understand Requirements

Extract from the user's request:
- **What to build**: Component, page, full application, or beautification of existing UI
- **Framework**: HTML/CSS/JS, React, Vue, etc. — infer from the project if not stated
- **Purpose**: What problem does this interface solve? Who uses it?
- **Constraints**: Accessibility, performance, branding, or technical requirements

If beautifying existing code, read it first to understand the current structure and framework.

### Step 2: Choose an Aesthetic Direction

Commit to a BOLD direction before writing any code. Pick a tone — not a safe middle ground:

Brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, or something entirely original.

For each direction, answer:
- What makes this UNFORGETTABLE? What's the one thing someone will remember?
- Does the complexity of the implementation match the aesthetic vision? (Maximalist needs elaborate code; minimalist needs precision and restraint.)

**CRITICAL**: Bold maximalism and refined minimalism both work — the key is intentionality, not intensity.

### Step 3: Design the Visual System

Apply these guidelines to build a cohesive design system:

- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt for distinctive, characterful choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive palette. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (`animation-delay`) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Use gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays as appropriate.

### Step 4: Implement

Write production-grade, functional code following the visual system:
- Use CSS variables for color, spacing, and typography consistency
- Load fonts from Google Fonts or CDN with `font-display: swap` and appropriate fallbacks
- Prioritize CSS-only animations for HTML; use Motion library for React when available
- Ensure the interface is responsive and functional, not just decorative

### Step 5: Refine

Review against the anti-patterns list. The design MUST NOT have:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Verify every design choice is intentional for this specific context. No two designs should look the same — vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

## Examples

### Example 1: Landing page
User says: "Build a landing page for a coffee roaster"
Actions:
1. Choose warm editorial aesthetic with organic/natural tone
2. Pick a serif display font (e.g., Playfair Display) paired with a clean sans-serif body
3. Earth-tone palette with a burnt orange accent, CSS variables for consistency
4. Full-bleed hero image, parallax scroll, staggered text reveals on load
Result: Single HTML file with embedded CSS, Google Fonts link, scroll-triggered animations

### Example 2: Dashboard component
User says: "Create a React analytics dashboard"
Actions:
1. Choose industrial/utilitarian aesthetic with dark theme
2. Monospace display font (e.g., JetBrains Mono), dense data layout
3. Crisp grid, high-contrast data visualization colors, subtle hover states
4. Motion library for panel transitions, minimal decoration
Result: React component with CSS modules, recharts integration, motion transitions

### Example 3: Beautify existing UI
User says: "Make this form look better" (with existing code in conversation)
Actions:
1. Read existing code to understand current structure and framework
2. Identify current aesthetic direction, elevate rather than replace
3. Improve typography (better font pairing, refined sizing/spacing)
4. Add micro-interactions (focus states, validation feedback, submit animation)
5. Keep existing framework and component structure intact
Result: Edited files with improved visual design, no structural changes

## Troubleshooting

### Design feels generic despite following guidelines
**Solution:** Be more extreme in your aesthetic commitment. Pick a bolder font pairing, push the color contrast further, or add an unexpected layout element. Generic results come from playing it safe — commit fully to a direction.

### Google Fonts CDN not loading
**Solution:** Add fallback `font-family` values in every declaration. Use `font-display: swap` to prevent invisible text during load. If offline, use system fonts that match the aesthetic intent (e.g., Georgia for serif, Menlo for monospace).

### Animations cause layout shift or jank
**Solution:** Only animate `transform` and `opacity` (GPU-composited properties). Use `will-change` sparingly on elements that will animate. Test with browser DevTools Performance tab to verify 60fps.

## Notes

- Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist designs need restraint, precision, and careful attention to spacing, typography, and subtle details.
- Claude is capable of extraordinary creative work. Don't hold back — show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
