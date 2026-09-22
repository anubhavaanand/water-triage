# Design System: WaterTriage Tactical Telemetry

## 1. Visual Theme & Atmosphere
A raw, Cockpit-Dense (10) interface fusing military terminal aesthetics with high-density data telemetry. The atmosphere is unforgiving, mechanical, and highly engineered — like a declassified biological threat radar. Absolute reliance on monospaced typography, rigid 1px grid compartmentalization, and simulated analog degradation (CRT scanlines). Consumer UI patterns (soft shadows, rounded corners, gradients) are strictly banned.

## 2. Color Palette & Roles
- **Deactivated CRT** (`#0A0A0A`) — Primary background surface. Pure black (`#000000`) is banned.
- **Terminal Grid** (`#1A1A1A`) — Secondary background for panels and input fields.
- **White Phosphor** (`#EAEAEA`) — Primary text, data readouts, and active structural borders.
- **Muted Phosphor** (`#71717A`) — Secondary text, metadata, table headers, inactive borders.
- **Aviation Red** (`#FF2A2A`) — Single accent color. Used EXCLUSIVELY for Critical contamination alerts, priority queue highlights, and strike-throughs. No other accent color is permitted.

## 3. Typography Rules
- **Display & Body:** `JetBrains Mono` (or `Space Mono`) exclusively. This project uses zero proportional fonts. 
- **Scale:** Fixed and small for data (12px - 14px). Generous tracking (0.05em) to simulate mechanical typewriter spacing.
- **Casing:** Exclusively uppercase for all structural headers, navigation, and metadata. 
- **Banned:** `Inter`, any serif fonts, and any proportional sans-serifs.

## 4. Component Stylings
* **Buttons:** Utilitarian rectangles. 0px border-radius. 1px solid border. Hover state inverts colors (Phosphor background, CRT text). No outer glow.
* **Panels/Cards:** 0px border-radius. 1px solid `Muted Phosphor` borders. Extreme data density inside. No drop shadows.
* **Alerts:** Aviation Red text with ASCII framing (e.g., `[ CRITICAL ]`).
* **Loaders:** CSS typing cursors (`_`) blinking, or simulated terminal data streams. No circular spinners.
* **Decorative Syntax:** Use ASCII characters (`///`, `>>>`, `[ ]`) to frame data points structurally.

## 5. Layout Principles
- **Grid Determinism:** Strict CSS Grid architectures. Elements are anchored precisely to grid tracks. 1px gap with contrasting parent/child background colors to generate razor-thin dividing lines.
- **Visible Compartmentalization:** Horizontal rules (`<hr>`) span entire container widths to segregate operational units.
- **Responsive:** Mobile-first collapse below 768px. No horizontal scroll overflow.

## 6. Motion & Interaction
- **CRT Scanlines:** A `repeating-linear-gradient` applied to the background to simulate horizontal electron beam sweeps.
- **Mechanical Noise:** A global, low-opacity SVG static/noise filter applied to the DOM root.
- **Transitions:** Hard cuts or ultra-fast (50ms) linear color inversions. No spring physics, no ease-in-out floating.

## 7. Anti-Patterns (Banned)
- No emojis anywhere.
- No `Inter`, `Roboto`, or generic system fonts.
- No pure black (`#000000`).
- No neon/outer glow shadows.
- No `border-radius` (everything must be sharp 90-degree corners).
- No standard UI dashboards (e.g., 3-column equal white cards).
- No AI copywriting clichés ("Elevate", "Seamless", "Unleash").
- No filler UI text ("Scroll to explore").
