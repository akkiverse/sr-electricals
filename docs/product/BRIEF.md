# SR Electricals: Product brief

> Summary of the approved Business Brief. Full brief: https://claude.ai/artifact/LKj2eZSbcyyecVry6MLnnx
> Idea Document: https://claude.ai/artifact/Xy6Z2i1aQS7hbrB232L1vL

**Verdict:** GO (70/100), approved for build on 2026-10-31

## The problem
SR Electrical in Deoghar (owner Sanjay Singh) sells wire, cable, lighting, MCBs and switchgear to dealers, contractors, government contractors and retail buyers, but has almost no presence online. Contractors call around to check brands and stock, and new buyers can't find the shop.

## Who it is for, and who pays
- **Customer:** SR Electrical, Deoghar (owner Sanjay Singh).
- **Users:** electrical and government-work contractors buying in bulk, small dealers restocking, and home owners buying lights, switches and wire.
- **In their words:** "Show me if you have Polycab 2.5 mm wire and Havells MCBs, and let me send my list on WhatsApp for a rate."

## Why this, why now
Contractors in India already buy over WhatsApp. A fast, good-looking site that shows the brands and range and sends a whole list to WhatsApp in one tap fits how they buy, costs nothing to run, and fills a real gap for the shop.

## Competition and our edge
| Alternative | Price | Strength | Gap |
|---|---|---|---|
| Other Deoghar electrical shops (offline) | Free | Relationships, walk-in | Not findable online |
| IndiaMART / TradeIndia listing | Free to paid | Lead flow from search | Cluttered pages, leads shared with competitors |
| WhatsApp Business catalogue | Free | Familiar, direct chat | Not found by search |
| Google Business Profile | Free | Maps visibility, reviews | No real catalogue |
| DIY store builders (Dukaan, Shopify) | Monthly fees | Ready-made carts | Paid, retail-focused, not built for bulk quotes |

**Edge:** one attractive, fast page built for bulk buyers, with a quote list that sends the whole order to WhatsApp in one tap, at no running cost.

## Revenue model
- **For the shop:** more enquiries and orders. Estimate: 5 extra contractor enquiries a month, 2 orders of about ₹15,000 at about 10% margin, roughly ₹3,000 extra profit a month (to validate with the owner).
- **For the studio (later, optional):** reuse as a template for other local shops for a one-time setup fee plus a small yearly care fee. Not part of the MVP.

## Success metrics (first 30 days)
- Visitors (target 300) and taps on WhatsApp or Call (target 30).
- Quote lists sent (target 10) and orders the owner confirms came from the site (target 3).
- Owner or founder updates at least 10 products without help.

## What the real version needs
- A free Neon Postgres database connected to the `sr-electricals` Vercel project by the founder (no cost), so the owner's saves go live. Until then the site runs read-only on the seed catalogue.
- A Studio account for Sanjay Singh with the **owner** role, added by the founder in the hub's `/admin/users`.
- Optional later: a custom domain (yearly fee, founder's decision).

## Risks and compliance flags
1. **Brand logos and product photos** are trademarks and copyrighted: brand names are shown as styled text and products use generic illustrations; official logos only with written permission.
2. **Personal data:** the owner's name, photo and the shop phone are shown publicly with his consent. Enquiries go straight to WhatsApp, so the site stores no customer details.
3. **Stale catalogue:** keep editing simple; review monthly.
4. **Slow WhatsApp replies** would hurt; the owner commits to answering during shop hours.
5. **Prices:** "Price on request" avoids out-of-date prices for copper-linked items.
