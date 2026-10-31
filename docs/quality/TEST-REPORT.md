# SR Electricals: Test report

**Run:** 2026-10-31 · **Commit:** branch `cr/0001-mvp` (after 4266450) · **Result:** 39 of 39 tests passing (34 pytest + 5 node), plus the Postgres store test passing against a local Postgres 16 · **Build:** Ruff lint and format clean; `npm run build` OK

How to run: `uv run ruff check . && uv run ruff format --check . && uv run pytest` and `npm test`. The Postgres test runs when `TEST_DATABASE_URL` points at a throwaway database (never the shop's).

## Traceability: acceptance criteria to tests

| Criterion | Test | Result |
|---|---|---|
| AC-1.1 | `tests/test_us1_landing.py::test_ac_1_1_hero_with_call_and_whatsapp` | Pass |
| AC-1.2 | `tests/test_us1_landing.py::test_ac_1_2_brands_section_links_to_filtered_catalogue` | Pass |
| AC-1.3 | `tests/test_us1_landing.py::test_ac_1_3_best_selling_category_cards` | Pass |
| AC-1.4 | `tests/test_us1_landing.py::test_ac_1_4_who_we_serve` | Pass |
| AC-2.1 | `tests/test_us2_catalogue.py::test_ac_2_1_all_active_products_with_price_on_request` | Pass |
| AC-2.2 | `tests/test_us2_catalogue.py::test_ac_2_2_filter_by_category_and_brand_in_url` | Pass |
| AC-2.3 | `tests/test_us2_catalogue.py::test_ac_2_3_search_case_insensitive_over_name_brand_category_specs` | Pass |
| AC-2.4 | `tests/test_us2_catalogue.py::test_ac_2_4_no_matches_empty_state` | Pass |
| AC-2.5 | `tests/test_us2_catalogue.py::test_ac_2_5_product_detail` | Pass |
| AC-3.1 | `tests/js/quote-core.test.js` "AC-3.1", `tests/test_us3_quote.py::test_ac_3_1_add_buttons_carry_item_details` | Pass |
| AC-3.2 | `tests/js/quote-core.test.js` "AC-3.2", `tests/test_us3_quote.py::test_ac_3_2_quantity_limits` | Pass |
| AC-3.3 | `tests/js/quote-core.test.js` "AC-3.3", `tests/test_us3_quote.py::test_ac_3_3_whatsapp_message` | Pass |
| AC-3.4 | `tests/js/quote-core.test.js` "AC-3.4", `tests/test_us3_quote.py::test_ac_3_4_server_stores_no_quote_data` | Pass |
| AC-3.5 | `tests/js/quote-core.test.js` "AC-3.5", `tests/test_us3_quote.py::test_ac_3_5_empty_list_state` | Pass |
| AC-4.1 | `tests/test_us4_visit.py::test_ac_4_1_owner_with_photo_or_initials` | Pass |
| AC-4.2 | `tests/test_us4_visit.py::test_ac_4_2_visit_us_address_hours_map_directions` | Pass |
| AC-4.3 | `tests/test_us4_visit.py::test_ac_4_3_footer_and_local_business_on_every_page` | Pass |
| AC-5.1 | `tests/test_us5_admin.py::test_ac_5_1_admin_needs_owner_or_admin_signin`, `::test_ac_5_1_previews_open_admin` | Pass |
| AC-5.2 | `tests/test_us5_admin.py::test_ac_5_2_add_product_and_inline_errors` | Pass |
| AC-5.3 | `tests/test_us5_admin.py::test_ac_5_3_edit_and_deactivate` | Pass |
| AC-5.4 | `tests/test_us5_admin.py::test_ac_5_4_uploads_checked_and_shown` | Pass |
| AC-5.5 | `tests/test_us5_admin.py::test_ac_5_5_settings_change_public_pages` | Pass |
| AC-5.6 | `tests/test_us5_admin.py::test_ac_5_6_saves_need_the_database`, `::test_ac_5_6_store_choice_and_webp_resize`, `tests/test_postgres_store.py::test_ac_5_6_postgres_store_saves_and_seeds` (local Postgres) | Pass |
| AC-5.7 | `tests/test_us5_admin.py::test_ac_5_7_lists_with_edit_remove_and_confirmation` | Pass |
| AC-5.8 | `tests/test_us5_admin.py::test_ac_5_8_brand_order_and_best_selling_on_home` | Pass |
| AC-6.1 | `tests/test_us6_quality.py::test_ac_6_1_phone_width_no_sideways_scroll_and_44px_targets` and the 360 px browser check below | Pass |
| AC-6.2 | `tests/test_us6_quality.py::test_ac_6_2_dark_theme_follows_system_and_toggle_is_remembered` and the browser check below | Pass |
| AC-6.3 | `tests/test_us6_quality.py::test_ac_6_3_automated_accessibility_check` (labels, alt text, names, AA contrast of every token pair, focus ring) | Pass |
| AC-6.4 | `tests/test_us6_quality.py::test_ac_6_4_unique_titles_and_descriptions_with_deoghar` | Pass |

Also: `test_search_ignores_hidden_brand_products`, `test_admin_export_backup`, `test_saved_data_from_this_version_loads` (compatibility of saved data).

## Design checklist
- [x] Colours as CSS custom properties; designed dark theme via `prefers-color-scheme` plus a remembered toggle
- [x] 360 px to 1440 px without sideways scrolling; tap targets at least 44 px
- [x] Semantic HTML, labelled fields, visible focus (amber ring), AA contrast, reduced motion respected
- [x] Plain-English copy; seed catalogue shown as "Price on request" with a note that stock and rates change
- [x] Designed empty, error and not-found states; read-only banner without a database
- [x] Favicon, title, meta description, Open Graph, theme-color on every page
- [x] Inline SVG icons, no emoji; self-made SVG pictures, no brand logos
- [x] One entrance moment (cables drawing in) and button feedback (Add, Send zap)
- [x] Footer link "Part of Idea Studio by AkkiVerse"
- [x] No test counts or build details shown to visitors

## Visual check
`scripts/visual_check.py` with Playwright Chromium against the app running on a local Postgres 16 (`DATABASE_URL` set, admin opened as on a preview):
- Screenshots of home, catalogue, empty search, product, quote list and four admin screens at 375 px and 1280 px, light and dark. Fixes made after looking: two-column product and category grids on phones, dark-mode accent text (amber) for brand labels and links, search box padding.
- 360 px: every page `scrollWidth = 360`, no button or link under 44 px tall.
- Quote flow in the browser: quantity 0 shows "Enter a whole number from 1 to 9999."; two items survive a reload (badge 2); Send on WhatsApp opens `https://wa.me/919304359146?text=` with "Polycab FR PVC house wire 2.5 sq mm (Polycab) x 20 … Name: Ravi … I am a: Contractor".
- Theme toggle: switching to dark is remembered after reload.

## Releases
Not released yet.
