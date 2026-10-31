# CR-0001: First version (MVP)

- **Status:** In review
- **Requested by:** Founder (board notes)
- **Date:** 2026-10-31
- **Release:** (not yet released)
- **Pull request:** https://github.com/akkiverse/sr-electricals/pull/1

## Why
The founder approved the SR Electricals idea (GO, 70/100) for build: an attractive shop website for SR Electrical, Deoghar, that shows the brands, best-selling categories, owner and location, turns visits into WhatsApp quote requests, and gives the owner an admin page to keep brands and items current.

Founder notes included in this build: shop phone 9304359146; opening hours Monday to Saturday, 10:30 AM to 7 PM; the owner consents to his photo being shown and will upload it himself; an admin page lists brands and items so he can add, update and remove them. "Created repo sr-electricals in GitHub, create the project in Vercel, I will add the database with it."

## References
None, beyond the board notes quoted above.

## What changes
Everything is new: home page, catalogue with search and filters, category and brand pages, product pages, browser-only quote list sent on WhatsApp, owner admin behind Studio sign-in, Postgres storage when the founder connects a database (read-only seed catalogue until then).

## Spec impact
| Criterion | Change |
|---|---|
| AC-1.1 to AC-6.4 | Added (all criteria of the approved spec) |

## Architecture impact
New: see [ARCHITECTURE.md](../architecture/ARCHITECTURE.md), [ADR-0002](../adr/0002-stack.md) (stack) and [ADR-0003](../adr/0003-storage.md) (storage).

## Verification
39 of 39 tests pass (34 pytest, 5 node), one or more per acceptance criterion; the Postgres store test passes against a local Postgres 16. Ruff lint and format are clean. A real-browser check at 360, 375 and 1280 px in light and dark found no sideways scrolling or small tap targets, and the full quote flow opened WhatsApp with the expected message. See [TEST-REPORT](../quality/TEST-REPORT.md).

## Notes
- The Vercel project `sr-electricals` exists with the live address `sr-electricals-akkiverse.vercel.app`; nothing goes live until the founder approves the release. Previews are private.
- Founder's hosting note: the app runs in region `sin1` (Singapore) next to the Neon database `sr-electricals-master-db`; the database is connected through `DATABASE_URL` or `POSTGRES_URL`, never in the repo. Until it is linked the site is read-only on the seed catalogue.
- The seed catalogue (38 items) is a typical range for these brands, not the shop's confirmed stock; the owner should review it.
- The admin accepts the hub's default **App admin** role as well as **owner**; the `owner` role is listed in the registry entry at release.
