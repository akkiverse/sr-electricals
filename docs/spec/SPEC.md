# SR Electricals: Specification

**Status:** Approved 2026-10-31 · **Source:** https://claude.ai/artifact/L9FWLLgDX3p2yND9P4CAfc
This file is the source of truth for what the product does. Every change to it is made through a change request (see [../changes/](../changes/)).

## Overview
SR Electricals is a fast, attractive, mobile-first shop website for SR Electrical, Deoghar: brands, best-selling categories, a searchable product catalogue, the owner and the shop's location. Visitors add items to a quote list and send it to the shop on WhatsApp. The owner keeps the site current from an admin page.

**MVP goal:** get the first 10 quote requests from the site within 30 days, with no payments and no customer data stored.

## Users
- **Ravi, electrical contractor (primary):** on a phone at a site, needs to check brand and size and send a list for a bulk rate.
- **Meena, home owner (retail):** wants a nice light or switch set and the shop's location and hours.
- **Sanjay Singh, shop owner (admin):** signs in on his phone between customers, uploads his own photo and product pictures, and adds or removes brands and items so the main page stays current without a developer.

## User stories and acceptance criteria

### US-1: Landing page
As a visitor, I want a landing page showing who the shop is, the brands it deals in and its best-selling categories, so that I trust it and know what it sells.
- **AC-1.1** Given the home page, when it loads, then it shows the shop name, a one-line tagline, and Call and WhatsApp buttons using the configured shop phone (seed 9304359146, linked as `tel:+919304359146` and `https://wa.me/919304359146`). *(added CR-0001)*
- **AC-1.2** Given the configured brands (seed: Polycab, KEI, HPL, Benlo, Anchor, Havells), when the home page loads, then each brand appears in a "Brands we deal in" section, and each links to the catalogue filtered by that brand. *(added CR-0001)*
- **AC-1.3** Given the categories flagged best-selling (seed: Wires and cables, Indoor lighting, Outdoor lighting, MCBs and distribution boards, Switches and switchgear), when the home page loads, then each shows as a card with name, image and link to its category page. *(added CR-0001)*
- **AC-1.4** Given the home page, when it loads, then a "Who we serve" section lists Dealers, Contractors, Government contractors and Retail customers. *(added CR-0001)*

### US-2: Browse, search and filter
As a contractor, I want to browse, search and filter products by category and brand, so that I can quickly check whether the shop has what I need.
- **AC-2.1** Given the catalogue page, when no filter is set, then all active products are listed with name, brand, category, image and a "Price on request" label unless the product has a price. *(added CR-0001)*
- **AC-2.2** Given the catalogue, when I filter by a category and/or brand, then only matching products are shown and the filters appear in the URL query (shareable link). *(added CR-0001)*
- **AC-2.3** Given the catalogue, when I search for a term (for example "2.5 mm" or "polycab"), then only products whose name, brand, category or specs contain the term (case-insensitive) are shown. *(added CR-0001)*
- **AC-2.4** Given a filter or search with no matches, when the page renders, then it shows "No products match" with a link to clear filters and a WhatsApp "Ask us" button. *(added CR-0001)*
- **AC-2.5** Given a product, when I open its detail page, then it shows name, brand, category, specs (sizes, ratings), a "Bulk available" tag when set, and an "Add to quote" control with a quantity field. *(added CR-0001)*

### US-3: Quote list on WhatsApp
As a buyer, I want to collect several items with quantities in a quote list and send it on WhatsApp in one tap, so that I get a rate without calling.
- **AC-3.1** Given a product, when I add it with quantity N, then the quote list count increases and the list shows the item with quantity N; adding it again increases its quantity. *(added CR-0001)*
- **AC-3.2** Given the quote list, when I change a quantity or remove an item, then the list updates; quantities must be whole numbers from 1 to 9999, and invalid values show an inline error. *(added CR-0001)*
- **AC-3.3** Given a quote list with items and an optional name and "I am a" choice (Dealer, Contractor, Government contractor, Retail), when I press "Send on WhatsApp", then the browser opens a `https://wa.me/<number>?text=` link whose decoded text lists each item as "<name> (<brand>) x <qty>" plus the name and buyer type. *(added CR-0001)*
- **AC-3.4** Given the quote list, when I reload the page, then it is still there (kept in the browser only); the server stores no quote or customer data. *(added CR-0001)*
- **AC-3.5** Given an empty quote list, when I open it, then it says the list is empty and links to the catalogue; the send button is disabled. *(added CR-0001)*

### US-4: Owner, address, map and hours
As a visitor, I want to see the owner and the shop's address, map and hours, so that I can trust and visit the shop.
- **AC-4.1** Given the About section, when it loads, then it shows the owner name "Sanjay Singh", the owner photo if one is set (otherwise a neutral placeholder with initials), and the short shop story. *(added CR-0001)*
- **AC-4.2** Given the Visit us section, when it loads, then it shows the full address (SR Electrical, Tiwary Chowk, Deoghar College Road, Deoghar, Jharkhand 814112, India), the opening hours (seed: Monday to Saturday, 10:30 AM to 7 PM), an embedded map, and a Get directions link to Google Maps for that address; the LocalBusiness data carries the same hours. *(added CR-0001)*
- **AC-4.3** Given any page, when it loads, then the footer shows the address, phone and WhatsApp links, and the page contains LocalBusiness structured data (JSON-LD) with name, address and phone. *(added CR-0001)*

### US-5: Owner admin
As the shop owner, I want an admin page that lists every brand, category and product shown on the main page and lets me add, edit and remove them and upload my own photo, so that I keep the site current without a developer.
- **AC-5.1** Given the admin area `/admin`, when a visitor without a sign-in for this app with the owner or admin role opens it, then they are redirected to Studio sign-in (studio-auth kit; roles in `registry/sr-electricals.json`: owner, admin); a signed-in owner or admin sees the admin dashboard. *(added CR-0001)*
- **AC-5.2** Given the admin product form, when I submit a product with name, brand, category and optional specs, price, bulk flag, best-selling flag and image, then it is saved through the catalogue store and appears in the catalogue; missing required fields show inline errors. *(added CR-0001)*
- **AC-5.3** Given the admin, when I edit or deactivate a product, then the change shows in the catalogue (deactivated products are hidden from visitors). *(added CR-0001)*
- **AC-5.4** Given the admin, when I upload an owner photo or product image (JPEG, PNG or WebP, at most 2 MB), then it is stored through the image store and shown on the site; other types or larger files are refused with a clear message. *(added CR-0001)*
- **AC-5.5** Given the admin, when I edit shop settings (tagline, phone, WhatsApp number, hours, story, brands list, best-selling categories), then the public pages use the new values. *(added CR-0001)*
- **AC-5.6** Given the shop database is connected (`DATABASE_URL` set), when the owner saves any change in the admin, then it is stored in Postgres and the next load of the public pages shows it (no redeploy); uploaded images are resized to WebP at most 1600 px wide and stored in the database. Given no database is connected, saves are refused with the message: "Saving needs the shop database. Ask the founder to connect it." Tests run against the in-memory store. *(added CR-0001)*
- **AC-5.7** Given the admin, when I open Brands, Categories or Products, then each shows a list of every item currently on the site (name, picture, shown or hidden) with Edit and Remove buttons and an Add button; Remove asks for confirmation, and after confirming the item no longer appears on any public page. *(added CR-0001)*
- **AC-5.8** Given the admin, when I add, remove or reorder a brand or mark a category or product as best-selling, then the home page "Brands we deal in" and "Best-selling" sections show exactly the new list in the new order. *(added CR-0001)*

### US-6: Fast, clear, good-looking
As any visitor, I want the site to be fast, clear and good-looking on my phone, in light or dark mode, so that it feels like a trustworthy modern shop.
- **AC-6.1** Given a 360 px wide screen, when any public page renders, then nothing scrolls sideways and all buttons are at least 44 px tall. *(added CR-0001)*
- **AC-6.2** Given the system theme is dark, when a page loads, then the dark theme is used; a toggle switches themes and the choice is remembered. *(added CR-0001)*
- **AC-6.3** Given any public page, when checked with an automated accessibility check, then there are no critical issues (labels on inputs, alt text on images, contrast AA, visible focus). *(added CR-0001)*
- **AC-6.4** Given each public page, when it renders, then it has a unique title and meta description including "Deoghar" (for example "Polycab, Havells and more electrical supplies in Deoghar | SR Electrical"). *(added CR-0001)*

## Screens and flows
- **Home (`/`):** hero (shop name, tagline, Call, WhatsApp, "Browse products"), Brands we deal in, Best-selling categories, Who we serve, About the owner, Visit us (address, hours, map), footer.
- **Catalogue (`/products`):** search box, category and brand filter chips, product grid. Empty: "No products match". Error: "Couldn't load products, please try again" with Call button.
- **Category (`/category/<slug>`) and Brand (`/brand/<slug>`):** catalogue pre-filtered with a heading.
- **Product (`/products/<slug>`):** image, details, specs table, quantity, Add to quote, "Ask on WhatsApp about this item". Not found: friendly 404 with links home.
- **Quote list (`/quote`):** items, quantities, name, buyer type, Send on WhatsApp, Clear. Empty state as AC-3.5.
- **Admin (`/admin`, owner or admin only):** dashboard (counts), Brands, Categories and Products lists, each with Add, Edit and Remove (with confirmation) and shown or hidden status; product form with image upload; Shop settings (tagline, phone, hours, story); Owner photo upload; Export catalogue (JSON backup). Phone-friendly: one column, large buttons. No database: a clear banner and saves refused (AC-5.6).

## Look and feel
- **Personality:** bright, dependable, quick.
- **Feels right for:** a contractor on a phone at a building site in daylight, and a family browsing lights at home in the evening.
- **Colour mood:** confident electric blue with a warm amber "spark" accent on white; deep navy in dark mode. Main brand colour **#1D4ED8**, accent **#F59E0B**.
- **Typography:** crisp, sturdy sans with bold, slightly condensed headings.
- **Cues from:** clean product grids of modern Indian brand sites, generous whitespace in the hero, simple local-business sites with a strong map and Call block.
- **Stand apart from:** IndiaMART-style pages crowded with ads, banners and tiny text. One clear action per section.
- **Avoid:** official brand logos without permission, stock photos with watermarks, emoji, flashing banners, autoplay video.
- **Delight moment:** tapping "Send on WhatsApp" opens a neatly formatted order message, with a small lightning-bolt animation on the button.

## Data model
- **Settings:** shop_name, tagline, owner_name, owner_photo, story, address, map_query, phone, whatsapp, hours, serves[], brands order, best-selling categories.
- **Brand:** slug, name, logo (optional, only with permission), order, active.
- **Category:** slug, name, image, description, best_selling (bool), order, active.
- **Product:** id, slug, name, brand_slug, category_slug, specs {key: value}, price_inr (optional), unit (for example "per 90 m coil"), bulk_available (bool), best_selling (bool), image, active (bool), updated_at.
- **Quote item (browser only):** product slug, name, brand, qty.
- **Where it lives:** Postgres (one `store` table of JSON documents plus an `images` table of WebP bytes) when `DATABASE_URL` is set, seeded on first start from `app/data/catalogue.json`. Without a database the site shows the seed data read-only. No customer data on the server.

## Non-functional requirements
Works from 360 px to 1440 px; light and dark; first load under 2 s on 4G (images lazy-loaded, small SVG/WebP); labels, alt text, AA contrast, keyboard use and visible focus; clear plain-English errors; no personal phone or email on the page except the shop's business contact the owner approved.

## Out of scope
Online payment and checkout, delivery booking, customer accounts or order history, live stock or price feeds, GST invoices, reviews, Hindi translation, chat bots, AI features, custom domain, separate file storage service.

## Open questions
1. Connect a free Neon Postgres database to the sr-electricals Vercel project (founder action, no cost) so the owner's saves go live; until then the site runs read-only on seed data.
2. Permission to show brand logos, or names only (default: names only).
3. Real product and shop photos, or generic images the owner replaces later (default: generic illustrations).
4. Show prices on any retail items, or "Price on request" for all (default).
5. Confirm 9304359146 is the shop number to publish (it will be public). The founder's notes give it as the shop phone.
6. Who gets the owner role: Sanjay Singh needs a Studio account, added by the founder in `/admin/users`.
