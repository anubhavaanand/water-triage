# Design System: WaterTriage Sketch Prototype

## 1. Visual Theme & Atmosphere
A hand-drawn, wireframe sketch aesthetic — like a field engineer's notebook on graph paper. The interface feels provisional, tactical, and human: dashed borders, hatched fills, dog-eared corners, and a single marker-blue accent. It's not a dashboard; it's a working sketch for a dashboard.

## 2. Color Palette & Roles

### Light Mode (Paper)
- **Paper** (`#f4f0e8`) — Warm off-white graph paper base
- **Ink** (`#1a1a1a`) — Primary text, structural lines
- **Ink-Muted** (`#555555`) — Secondary text, metadata, grid lines
- **Grid-Line** (`#d0c8b8`) — Subtle graph paper lines
- **Grid-Major** (`#b8b0a0`) — Major grid intervals (every 5th line)
- **Accent** (`#2b6cb0`) — Single marker blue for CTAs, links, highlights
- **Accent-Soft** (`#d6e9f8`) — Accent backgrounds, hover states
- **Red** (`#c0392b`) — Critical alerts, overrides
- **Red-Soft** (`#fadbd8`) — Critical backgrounds
- **Amber** (`#d4a017`) — Medium risk, warnings
- **Amber-Soft** (`#fef9e7`) — Warning backgrounds
- **Green** (`#27ae60`) — Low risk, safe
- **Green-Soft** (`#d5f5e3`) — Safe backgrounds
- **White** (`#ffffff`) — Card backgrounds, overlays
- **Shadow** (`rgba(0,0,0,0.08)`) — Subtle depth

### Dark Mode (Blueprint)
- **Paper** (`#1a1a2e`) — Deep navy-blueprint base
- **Ink** (`#e8e8e8`) — Primary text (near-white)
- **Ink-Muted** (`#999999`) — Secondary text
- **Grid-Line** (`#2a2a4a`) — Graph paper lines
- **Grid-Major** (`#3a3a5a`) — Major grid intervals
- **Accent** (`#5dade2`) — Marker blue (lighter for dark mode)
- **Accent-Soft** (`#2c3e5e`) — Accent backgrounds
- **Red** (`#e74c3c`) — Critical alerts
- **Red-Soft** (`#4a1a1a`) — Critical backgrounds
- **Amber** (`#f39c12`) — Medium risk
- **Amber-Soft** (`#4a3a1a`) — Warning backgrounds
- **Green** (`#58d68d`) — Low risk
- **Green-Soft** (`#1a3a2a`) — Safe backgrounds
- **White** (`#252545`) — Card backgrounds
- **Shadow** (`rgba(0,0,0,0.3)`) — Depth

## 3. Typography Rules
- **Display & Headings:** `"Segoe Print"`, `"Comic Sans MS"`, `"Chalkboard SE"`, cursive — handwritten feel
- **Body & UI:** `"Segoe Print"`, `"Comic Sans MS"`, `"Chalkboard SE"`, cursive — same family for cohesion
- **Monospace/Data:** `"Courier New"`, `"Courier"`, monospace — for tabular numbers, codes
- **Scale:** Clamp-based fluid scaling: `clamp(1.5rem, 3vw, 2.5rem)` for h1, `clamp(1.1rem, 2vw, 1.5rem)` for h2, `1rem` base
- **Weight:** Normal (400) for sketch feel; Bold (700) only for emphasis
- **Casing:** Sentence case throughout — no ALL CAPS (unlike tactical)
- **Sketch Font Stack:** `font-family: var(--font-sketch)`

## 4. Component Stylings

### Buttons
- **Primary:** `Accent` background, `White` text, `2px solid Ink` border, `var(--radius-md)` (8px), sketch shadow
- **Secondary:** `White` background, `Ink` text, `2px dashed Ink` border, `var(--radius-md)`
- **Ghost:** `transparent` background, `Accent` text, `2px dashed Accent` border, `var(--radius-md)`
- **Critical:** `Red` background, `White` text, `2px solid Ink` border
- **Hover:** `transform: translateY(-1px) rotate(-0.5deg)` — sketch "lift"
- **Focus:** `2px solid Accent` outline, `2px` offset

### Panels / Cards
- **Base:** `White` background, `2px solid Ink` border, `var(--radius-lg)` (12px)
- **Dog-eared corner:** `::before` triangle fold at top-right (`16px` accent color)
- **Hatchet fill:** `repeating-linear-gradient(-45deg, Grid-Line, Grid-Line 2px, transparent 2px, transparent 8px)` for disabled/empty states
- **Dashed border variant:** `2px dashed Ink` for provisional sections
- **No drop shadows** — only the dog-ear and border give depth

### Tables
- **Header:** `Ink-Muted` text, `2px solid Ink` bottom border
- **Rows:** `2px dashed Grid-Line` horizontal separators
- **Hover:** `Accent-Soft` background, slight `rotate(0.1deg)` on row
- **Critical row:** `Red-Soft` background, `Red` text, `2px solid Red` left border
- **Sticky header** on scroll

### Inputs
- `White` background, `2px solid Ink` border, `var(--radius-sm)` (4px)
- Focus: `2px solid Accent` border, `Accent-Soft` background tint
- Placeholder: `Ink-Muted` in sketch font

### Badges / Pills
- `var(--radius-pill)` (9999px), `2px solid` border, sketch font, `0.85em` size
- **Critical:** `Red` border/text, `Red-Soft` bg
- **High:** `Amber` border/text, `Amber-Soft` bg
- **Medium:** `Accent` border/text, `Accent-Soft` bg
- **Low:** `Green` border/text, `Green-Soft` bg

## 5. Layout Principles
- **Graph Paper Canvas:** `repeating-linear-gradient` grid on `body` (16px minor, 80px major)
- **Container:** `max-width: 1400px`, centered, `padding: var(--space-xl)` (24px)
- **Section Rhythm:** `var(--space-2xl)` (32px) between major sections
- **Grid System:** CSS Grid with `repeat(auto-fit, minmax(280px, 1fr))` for card grids
- **Asymmetric Allowed:** Sketch feel permits imperfect alignment — `rotate(-0.3deg)` on cards
- **Breakpoints:** 920px (tablet), 480px (mobile), 1300px (wide side-notes)

## 6. Motion & Interaction
- **Transitions:** `200ms ease` for color, `300ms cubic-bezier(0.25, 0.46, 0.45, 0.94)` for transform
- **Sketch Wobble:** `transform: rotate(-0.5deg)` on hover — subtle human imperfection
- **Staggered Entrance:** `animation: fadeInUp 0.4s ease forwards` with `--delay` per element
- **Reduced Motion:** `@media (prefers-reduced-motion)` disables all transforms/animations
- **No Spring Physics** — only ease/cubic-bezier

## 7. Anti-Patterns (Banned)
- No pure black (`#000000`) or pure white (`#ffffff`) as primary surfaces
- No `Inter`, `Roboto`, `JetBrains Mono` as display/UI fonts (only for data tables)
- No neon/glow shadows, no Material elevation, no glassmorphism
- No perfect alignment — embrace the sketch wobble
- No AI copy clichés ("Elevate", "Seamless", "Unleash")
- No filler text — every label must be domain-specific
- No rounded pills on structural elements — only on badges/tags
- No emoji as functional icons — use ASCII or sketch icons

## 8. Data Visualization Style
- **Bars:** Hatched fills (`repeating-linear-gradient`), not solid
- **Lines:** Dashed strokes, `stroke-linecap: round`
- **Donuts:** Stroke-only, hatched segments, center label in sketch font
- **Axes:** `2px dashed Ink-Muted`, labels in sketch font `0.85em`
- **Tooltips:** Sketch card style with dog-ear, handwritten text

## 9. Accessibility
- **Contrast:** 4.5:1 minimum (WCAG AA) in both light/dark modes
- **Focus:** Visible `2px solid Accent` outline on all interactive elements
- **Keyboard:** Full tab navigation, arrow keys for tabs, `Enter`/`Space` for buttons
- **Screen Readers:** Semantic HTML, `aria-labels` on icon-only buttons, `role="status"` on health pill
- **Reduced Motion:** All animations/transforms disabled via media query

## 10. Token Reference (CSS Custom Properties)
```css
:root {
  /* Light mode (default) */
  --paper: #f4f0e8;
  --ink: #1a1a1a;
  --ink-muted: #555555;
  --grid-line: #d0c8b8;
  --grid-major: #b8b0a0;
  --accent: #2b6cb0;
  --accent-soft: #d6e9f8;
  --red: #c0392b;
  --red-soft: #fadbd8;
  --amber: #d4a017;
  --amber-soft: #fef9e7;
  --green: #27ae60;
  --green-soft: #d5f5e3;
  --white: #ffffff;
  --shadow: rgba(0,0,0,0.08);

  --font-sketch: "Segoe Print", "Comic Sans MS", "Chalkboard SE", cursive;
  --font-mono: "Courier New", "Courier", monospace;

  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 24px;
  --space-2xl: 32px;
  --space-3xl: 48px;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-pill: 9999px;

  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-spring: 300ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@media (prefers-color-scheme: dark) {
  :root {
    --paper: #1a1a2e;
    --ink: #e8e8e8;
    --ink-muted: #999999;
    --grid-line: #2a2a4a;
    --grid-major: #3a3a5a;
    --accent: #5dade2;
    --accent-soft: #2c3e5e;
    --red: #e74c3c;
    --red-soft: #4a1a1a;
    --amber: #f39c12;
    --amber-soft: #4a3a1a;
    --green: #58d68d;
    --green-soft: #1a3a2a;
    --white: #252545;
    --shadow: rgba(0,0,0,0.3);
  }
}

[data-theme="dark"] { /* manual override via JS */
  --paper: #1a1a2e;
  --ink: #e8e8e8;
  --ink-muted: #999999;
  --grid-line: #2a2a4a;
  --grid-major: #3a3a5a;
  --accent: #5dade2;
  --accent-soft: #2c3e5e;
  --red: #e74c3c;
  --red-soft: #4a1a1a;
  --amber: #f39c12;
  --amber-soft: #4a3a1a;
  --green: #58d68d;
  --green-soft: #1a3a2a;
  --white: #252545;
  --shadow: rgba(0,0,0,0.3);
}
```