---
name: theme-factory
description: Apply professional visual themes to artifacts (presentations, documents, reports, HTML pages, landing pages). Use when user asks to "style this", "apply a theme", "make this look better", "beautify", or requests specific aesthetics like minimalist, modern, luxury, etc. Includes 10 preset themes and custom theme generation.
license: Apache-2.0
---

# Theme Factory

A curated collection of professional font and color themes with carefully selected color palettes and font pairings. Once a theme is chosen, it can be applied to any artifact.

Each theme includes:
- A cohesive color palette with hex codes
- Complementary font pairings for headers and body text
- A distinct visual identity suitable for different contexts and audiences

## Usage

```
/theme-factory                        # Show all themes and let user choose
/theme-factory midnight-galaxy        # Apply a specific theme directly
/theme-factory create a luxury theme  # Generate a custom theme
```

## Instructions

### Step 1: Understand Context

Determine:
- What artifact is being styled (slides, document, HTML page, report, etc.)
- Target audience and purpose
- Any branding constraints or preferences
- Whether user wants a preset theme or a custom one

If `$ARGUMENTS` specifies a theme name, skip to Step 3.
If `$ARGUMENTS` describes an aesthetic, skip to Step 4 (custom theme).

### Step 2: Present Theme Options

1. Display `theme-showcase.pdf` so the user can visually browse all themes. Do not modify this file.
2. List the available themes:

| # | Theme | Description |
|---|-------|-------------|
| 1 | Ocean Depths | Professional and calming maritime theme |
| 2 | Sunset Boulevard | Warm and vibrant sunset colors |
| 3 | Forest Canopy | Natural and grounded earth tones |
| 4 | Modern Minimalist | Clean and contemporary grayscale |
| 5 | Golden Hour | Rich and warm autumnal palette |
| 6 | Arctic Frost | Cool and crisp winter-inspired theme |
| 7 | Desert Rose | Soft and sophisticated dusty tones |
| 8 | Tech Innovation | Bold and modern tech aesthetic |
| 9 | Botanical Garden | Fresh and organic garden colors |
| 10 | Midnight Galaxy | Dramatic and cosmic deep tones |

3. **Wait for explicit user selection before proceeding.** Do not auto-select a theme.

### Step 3: Apply Theme

1. Read the selected theme file from `themes/{theme-name}.md`
2. Apply colors and fonts consistently throughout the artifact:
   - Background colors
   - Text colors (headings, body, accents)
   - Font families for headers and body
3. Ensure proper contrast and readability
4. Maintain the theme's visual identity across all pages/slides

### Step 4: Custom Theme (when no preset fits)

1. Discuss aesthetic direction with the user
2. Generate a new theme specification following the same structure as files in `themes/`
3. Give it a descriptive name reflecting the font/color combination
4. Present the specification for review before applying
5. Once approved, apply as in Step 3

## Examples

### Applying a preset theme to a slide deck
User: "Apply a professional theme to this presentation"

1. Show `theme-showcase.pdf` for visual browsing
2. User selects "Ocean Depths"
3. Read `themes/ocean-depths.md` for color palette and fonts
4. Apply navy backgrounds, teal accents, seafoam highlights, and DejaVu Sans throughout

### Creating a custom theme
User: "I need a warm, organic theme for a coffee shop website"

1. Generate custom theme with earth tones, warm browns, cream backgrounds
2. Present specification for approval
3. Apply approved theme to the HTML artifact

### Beautifying an existing document
User: "Make this report look more modern"

1. Suggest Tech Innovation or Modern Minimalist themes
2. User picks Modern Minimalist
3. Apply charcoal, slate gray, and clean white palette with DejaVu Sans

## Troubleshooting

### Theme showcase PDF not displaying
**Cause:** PDF viewer not available or file path issue
**Solution:** Fall back to text descriptions of each theme with color swatches (hex codes) and font specifications. User can still select by name.

### Theme doesn't match user's vision
**Cause:** Ambiguous aesthetic direction
**Solution:** Present 2-3 theme variations. Ask user which direction resonates, then refine.

### Theme breaks artifact structure
**Cause:** Overly aggressive styling replacing functional elements
**Solution:** Apply theme to visual elements only (colors, fonts, spacing). Preserve original layout, component hierarchy, and functionality.

## Notes

- Always wait for user theme selection — do not auto-select
- Theme files are specifications, not rigid templates — interpret creatively for each artifact type
- For HTML artifacts, consider using CSS variables for easy theme switching
- Preserve the artifact's original content and structure when applying themes
- Ensure color contrast meets accessibility standards (4.5:1 for body text, 3:1 for headings)
