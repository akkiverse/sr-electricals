# CR-0001: First version (MVP)

- **Status:** In progress
- **Requested by:** Founder (board notes)
- **Date:** 2026-10-31
- **Release:** (not yet released)
- **Pull request:** (opened at the end of the build)

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
To be filled when the build is tested.

## Notes
The Vercel project is created with production deploys off until the founder approves the release.
