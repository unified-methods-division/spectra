# Brand Guidelines — Feedback Intelligence

## Personality

Beauty is utility. This is not a dashboard. Not a dev tool. It's an intelligent surface where user voices are readable, browsable, and actionable. The AI layer feels like helpful annotations on real content, not the main event.

The aesthetic is atmospheric — film grain texture, ambient glows, frosted glass surfaces, glowing status indicators. Every page should feel like it has depth, not flatness.

## Visual Language

### Atmosphere

- **Film grain**: SVG noise overlay on `body::after` at 2.5% (light) / 3.5% (dark) — adds tactility
- **Ambient glows**: Blurred indigo/violet orbs behind key content areas
- **Frosted glass panels**: `bg-card/80 backdrop-blur-xl` with `border-foreground/8` for content surfaces that float over imagery
- **Mastheads**: Full-bleed imagery (Unsplash) with gradient fade, content card overlapping at bottom for depth
- **No flat cards or boxed layouts** — use dividers, rows, and floating panels instead

### Depth Hierarchy

1. Background (deepest) — `bg-background` with grain
2. Masthead imagery — bleeds edge-to-edge, gradient fades to background
3. Glass panels — `bg-card/80 backdrop-blur-xl`, overlaps imagery
4. Content rows — separated by subtle dividers, not borders
5. Status indicators — glowing dots that radiate light
6. Tooltips — `bg-popover` with `border-foreground/12`, no arrow, backdrop blur

## Color System

All colors defined as CSS custom properties using oklch in `src/index.css`.

### Primary — Indigo (hue 270)

Used sparingly: active nav indicators, status glows, primary buttons. Should appear 3-5 times on screen.

- Light: `oklch(0.50 0.18 270)`
- Dark: `oklch(0.70 0.19 270)`

### Neutrals — Blue-violet undertone

Not pure gray. Background at hue 265, low chroma. Dark mode goes deep (`oklch 0.115`) not black.

- Foreground: three tiers — `foreground` (high contrast), `muted-foreground` (secondary at 0.70 lightness for AA contrast), `muted-foreground/70` (tertiary)
- Never use `muted-foreground/50` or lower in dark mode — fails contrast

### Semantic Status Colors

| Token          | Purpose              | Representation                                    |
|----------------|----------------------|---------------------------------------------------|
| `--success`    | Completed, imported  | Glowing green dot + green text                    |
| `--warning`    | Needs attention      | Amber dot + amber text                            |
| `--info`       | In progress          | Pulsing blue dot with glow animation + blue text  |
| `--destructive`| Errors, failed       | Glowing red dot + red text                        |

Status indicators use colored dots (1.5px) with `box-shadow` glows, not badges. Active states pulse via `glow-pulse` keyframe animation. This is more expressive and less generic than badge variants.

### Sentiment Colors (Explorer page)

Sentiment appears as colored text on the word itself — not badge backgrounds. Calmer, screenshots better.

## Typography

**Font:** Geist Variable (body) + Geist Mono (tabular data, item counts).

| Role               | Size  | Weight    | Treatment                           |
|--------------------|-------|-----------|-------------------------------------|
| Page headers       | 30px  | Normal    | `tracking-tight`                    |
| Source names       | 14px  | Medium    | `text-foreground`                   |
| Item counts        | 10px  | Mono      | Sharp-edged `bg-foreground/8` badge |
| Metadata           | 11px  | Regular   | `text-muted-foreground/70`, tracked |
| Status labels      | 12px  | Regular   | Colored per status                  |

### Copy Conventions

- Source type copy lives in `SOURCE_TYPE_COPY` structure in `lib/utils.ts` — each type has `label`, `emptyStatus`, and `emptyTimestamp`
- Use contextual language per source type: "No file uploaded" not "No data yet", "Awaiting events" not "Awaiting upload"
- Unsupported features: show "Soon" label in selectors, "coming soon" in tooltips
- Relative timestamps: compact format — "5m ago", "2h ago", "3d ago"

## Layout

### Sidebar (220px)

- No border, no distinct background — sits on the same surface as the page
- Logo: "FEEDBACK" as tiny tracked uppercase (category), "Intelligence" as 15px medium (name)
- Nav items: `+` prefix in monospace (primary-colored when active, muted when not)
- Active state: bold text + lit `+` — no pills, no bars, no background
- The sidebar should feel like a document margin, not a toolbar

### Page Structure

- **Masthead**: full-bleed image with gradient fade to background
- **Content panel**: `max-w-2xl`, frosted glass card overlapping masthead by `-mt-24`
- **Heading + actions**: centered above the card, between masthead and panel
- **Content rows**: `divide-y divide-border`, hover reveals left accent bar (2px indigo)

### Source Rows

- Left accent bar on hover (primary color, 2px, fades in 150ms)
- Name + monospace item count badge on first line
- Type label + contextual timestamp on second line (11px, tracked, low opacity)
- Status dot + label right-aligned
- Action icon per source type (upload, webhook, RSS, API) — visible always if no data, hover-reveal if has data
- Upload panel indented with `pl-4`, file drop zone with dashed `border-foreground/10`

## Motion (via `motion/react`)

| Element               | Animation                    | Easing              | Duration |
|-----------------------|------------------------------|---------------------|----------|
| Source rows           | Staggered slide-in from left | ease-out-quint      | 250ms, 60ms stagger |
| Create form           | Scale 0.97 + opacity         | ease-out-quint      | 150ms |
| Layout reflow         | `layout` prop on siblings    | ease-out-quint      | 200ms |
| Upload panel          | Height + opacity             | ease-out-quad       | 200ms |
| Upload step changes   | Crossfade                    | ease-out-quint      | 150ms |
| Status badge change   | Crossfade                    | linear              | 150ms |
| Success dot           | Spring scale-in              | spring, bounce 0.3  | 300ms |
| Progress bars         | Motion-driven left sweep     | easeInOut           | 1.2s loop |
| Button loading        | Text slide-up swap + spinner | ease-out-quint      | 150ms |
| Error page            | Fade + slide up              | ease-out-quint      | 400ms |

### Animation Rules

- Never animate `height: "auto"` to `height: 0` — it snaps. Use `scale(0.97)` + opacity for enter/exit, `LayoutGroup` + `layout` for siblings.
- `AnimatePresence mode="wait"` for state swaps (button text, status labels)
- Loading states: delayed fade-in (300ms) so fast connections never see them
- Respect `prefers-reduced-motion`

## Buttons

- `cursor-pointer` always, `cursor-not-allowed` when disabled
- Active press: `translate-y-px` (built into base styles)
- Loading state: text slides up, spinner + new label slides in from below
- Match input heights in forms — use `size="default"` (h-9) next to inputs

## Tooltips

- Frosted glass: `bg-popover` + `border-foreground/12` + `backdrop-blur-xl`
- No arrow — clean floating panel
- `shadow-lg` for lift
- Animate in with zoom + fade (95% → 100%, 0 → 1 opacity)

## Error Pages

- Same masthead image (desaturated with `saturate-50`)
- Frosted glass card centered below
- Large monospace error code (404/500) in `text-primary/40`
- Headline + description + back link

## Extending

1. **New colors**: define `--token` in `:root` and `.dark` in `index.css`, bridge via `--color-token: var(--token)` in `@theme inline`
2. **New pages**: add masthead + frosted glass card pattern, add route in `routes.tsx`, add nav item in `App.tsx`
3. **New source types**: add entry to `SOURCE_TYPE_COPY` in `lib/utils.ts` and `SOURCE_ACTION_ICONS` in `sources-table.tsx`
4. **Chart colors**: `--chart-1` through `--chart-5` — indigo-to-violet graduated ramp
