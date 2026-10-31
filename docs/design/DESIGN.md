# SR Electricals: Design

## Subject and audience
A trusted neighbourhood electrical supplier in Deoghar. Visitors are contractors on a phone at a building site in bright daylight (fast, big tap targets, high contrast) and families browsing lights in the evening (calm dark theme). The owner edits on his phone between customers.

## The main screen's one job
Home: in five seconds, show who the shop is, the brands it stocks, and how to reach it (Call, WhatsApp, Browse). The catalogue's one job: find an item and add it to the quote list.

## Palette
| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | #FFFFFF | #0B1530 | Page background (deep navy at night) |
| `--surface` | #F2F5FC | #101D3F | Alternate sections, footer |
| `--ink` | #0F172A | #E8EDF8 | Text |
| `--muted` | #475569 | #A7B4CF | Secondary text (AA on bg and surface) |
| `--brand` | #1D4ED8 | #3B6CF0 | Primary buttons, electric blue |
| `--spark` | #F59E0B | #FBBF24 | Amber spark: logo bolt, badges, focus ring, dark-mode accent text |
| `--wa` | #15803D | #15803D | WhatsApp buttons (white text, AA) |

## Typography
Barlow (400, 600) for text and Barlow Semi Condensed (600, 700) for headings, self-hosted from `public/static/fonts` (OFL). Sturdy, slightly technical and condensed, like the type on cable drums and switchgear labels, and very readable on small screens.

## Layout
Mobile first, one column, sticky header (logo, Products, Quote list with count, theme toggle) and a sticky bottom bar with Call and WhatsApp on phones. Two-column grids for categories and products on phones, up to five or six columns on desktop. Each home section has one clear action. The admin is a single column with large buttons.

## The memorable element
**Wire colours.** The hero is three cables (blue, red, black) drawn in on load with an amber spark; each brand chip carries a coloured stripe in the house-wire insulation colours (red, black, yellow, blue, green); category pictures are simple self-made illustrations of a cable coil, lamp, street light, MCB board and switch plate. Tapping **Send on WhatsApp** flicks the lightning bolt.

## States
- **Empty catalogue search:** "No products match" with Clear filters and Ask us on WhatsApp.
- **Empty quote list:** "Your quote list is empty" with Browse the catalogue; Send is disabled.
- **Not found:** "Page not found" with Home, All products and Call us.
- **Server error:** "Couldn't load this page, please try again in a moment, or call us."
- **Owner photo missing:** initials in a soft circle.
- **Admin without database:** amber banner "Saving needs the shop database. Ask the founder to connect it."; saves refused with the same message.
- **Invalid quantity:** inline "Enter a whole number from 1 to 9999."
- **Motion:** one entrance moment (cables drawing in) and button feedback; all of it off with `prefers-reduced-motion`.
