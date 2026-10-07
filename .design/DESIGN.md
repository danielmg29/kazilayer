# KaziLayer Design System

## Visual theme and atmosphere

KaziLayer is calm, decisive, structured and quietly technical. It presents operational complexity without visual drama. The visual system allocates responsibility as follows:

- 70% Swiss Tech Minimalism provides the grid, typography, alignment, hierarchy, flat surfaces, restrained shape language and information density.
- 20% Modular and Bento Systems provides composable blocks, unequal panel emphasis, container-aware 1–3 column layouts and clear grouping through adjacency.
- 10% Blueprint and Flow Graphics provides measurement grids, route lines, state nodes and a mint flow moving through the indigo operational system.

The ratio is a decision framework, not a literal pixel count. Every screen should still feel like one product.

## Colour palette and roles

| Role | Token | Value | Usage |
|---|---|---:|---|
| Primary | Kazi Indigo | `#283C78` | Primary actions, selected navigation, authority and system structure |
| Accent | Flow Mint | `#36D3A0` | Focus, live flow, successful movement and active blueprint nodes |
| Ink | Operational Ink | `#111827` | Primary text and maximum hierarchy |
| Canvas | Cloud Surface | `#F4F7FC` | Page background and quiet operational regions |
| Panel | White | `#FFFFFF` | Main content surfaces in light mode |
| Information | Signal Blue | `#315CCB` | Informational status and active data |
| Success | Service Green | `#176B4D` | Completion and healthy service state |
| Warning | Operational Amber | `#A85A00` | At-risk, pending and paused state |
| Danger | Critical Red | `#A32929` | Breaches, failures and destructive actions |

Each semantic background has a paired foreground. Dark mode changes semantic values rather than requiring separate component classes. Status is never communicated by colour alone; text labels remain visible.

## Typography

- Product headings use Manrope. Display text is 48/52 at weight 600; H1 is 36/42; H2 is 28/34; H3 is 20/26.
- Interface content uses Inter. Body is 14/22 at weight 400; labels are 12/16 at weight 650.
- Technical identifiers, requirement keys, timestamps and design-system annotations use JetBrains Mono at 11/16 and weight 500.
- Headings use compact negative tracking. Body text keeps neutral tracking and readable line height.
- Uppercase is reserved for short technical labels and eyebrows, never paragraphs or primary actions.

## Spacing margins and geometry

- Base spacing unit: 4px.
- Scale: 4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64 and 80px.
- Page margins: 20px narrow, 32px medium and 48px wide.
- Dense authenticated content maximum: 1560px. Reading content uses a smaller measure.
- Component radii: 8px controls, 14px panels and 24px only for large brand surfaces.
- Borders: one-pixel semantic rules provide most grouping. Elevation is reserved for overlays, sheets and menus.
- Layout: twelve-column page logic with 20px nominal gutters. Components respond to their container around 260, 380, 720 and 1100px.

## Component styles

- Buttons are square-to-soft rectangles, never default pills. Primary buttons use indigo; secondary buttons use one-pixel borders; destructive actions use the semantic danger pair.
- Panels are flat or bordered. Raised surfaces are exceptional, not the default card treatment.
- Forms use visible labels, help text and error relationships. Focus uses the mint focus role with a three-pixel outline.
- Status badges always include a label and may add a square dot. Colour reinforces meaning but does not carry it alone.
- Navigation uses a precise left rule and indigo selection block. Technical indexes help scanning on dense desktop navigation.
- Blueprint graphics use thin grids, measured nodes and lines. They must explain flow, dependency or sequence.

## Motion system

Motion is mechanical, restrained and semantic.

- Fast feedback: 120–160ms for press, hover, focus and selection.
- Block transitions: 240–380ms for local reveal, presence and layout change.
- Primary easing: cubic-bezier `.22, 1, .36, 1` for decisive deceleration without bounce.
- Distance: 2px for hover lift and no more than 12px for entry reveal.
- Stagger: sparse and local; never animate every dashboard item on each realtime event.
- High-frequency motion uses transform and opacity only.
- Flow-line animation is allowed where it explains request → dispatch → field work → audit.
- `prefers-reduced-motion` removes stagger and travel, freezes flow paths and keeps every state understandable.

Motion for React is restricted to small client islands. Pages and static blocks remain server components so the motion layer does not pull the complete interface into the client bundle.

## Recipe axes and semantic slots

All shared dynamic components use these recipe axes:

- intent: row, card, detail, stat, media, relation, audit, thread, auth or feedback;
- density: compact, comfortable or spacious;
- tone: neutral, info, success, warning or danger;
- surface: flat, bordered, raised or inset;
- context: list, detail, picker, dashboard or thread.

Content enters through named slots: title, subtitle, badge, media, meta, timestamp, owner and actions. Kernel code must not branch on a model, role, field or action name.

## Responsive and accessibility rules

- Lists explicitly select scroll, collapse or priority behaviour rather than generating a duplicate mobile component.
- Layout blocks respond to container space instead of device names.
- Focus, keyboard order, labels, live announcements, error descriptions and status text are solved in primitives and renderers.
- Reduced motion, increased contrast and browser text scaling must preserve meaning and task completion.
- Loading, empty, error, permission, stale, conflict, offline and retry states are part of each critical block.

## Design system notes for generation

Use semantic tokens and existing recipe axes before adding values. Compose pages from registered blocks. Use the universal `Projection` for repeated records and the field registry for values. Put KaziLayer-specific presentation in declarative configuration. Add a divergent component only for interactions the projection system cannot express cleanly, then document its reason, variants, accessibility behaviour and reduced-motion state.

Do not add raw colours, arbitrary radii, default rounded cards, decorative gradients, glowing surfaces, icon circles or motion without state meaning. Do not copy domain rules into UI components. Contract content supplies meaning; the design system supplies presentation.
