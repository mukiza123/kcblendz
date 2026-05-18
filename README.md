# KCBlendz — Premium Smoothie and Wellness E-Commerce Platform

*Nourishing lives, inspiring wellness.*

A production-ready, full-stack e-commerce website built for **KCBlendz**, a student-led wellness brand founded inside the **African Leadership College of Higher Education**, operating from Kitchen 2 of the Kongo residence in Pamplemousses, Mauritius. KCBlendz sells fresh-blended smoothies, juices, wellness shots, sorbets, fruit salads, popsicles, probiotics, dried fruits, fruit powders, party packs and kiddies packs across three regions — Mauritius, Nigeria, and Global (shelf-stable products shipped via DHL).

This repository delivers a complete, demo-ready website covering every part of the buyer's journey and every back-office workflow an owner needs.

## Table of contents

1. [What's inside](#whats-inside)
2. [Quick start](#quick-start)
3. [Default admin credentials](#default-admin-credentials)
4. [Sandbox payment test cards](#sandbox-payment-test-cards)
5. [Running the tests](#running-the-tests)
6. [Project structure](#project-structure)
7. [Feature tour](#feature-tour)
8. [Brand system](#brand-system)
9. [Tech stack and architecture](#tech-stack-and-architecture)
10. [Security model](#security-model)
11. [Deployment](#deployment)
12. [Going live with real payments](#going-live-with-real-payments)

## What's inside

- A public storefront with three regions and full currency switching
- A custom smoothie builder with a live video preview of ingredients being prepared
- A complete cart, secure card-entry payment flow, and bank-transfer fallback
- Product reviews with verified-buyer badges
- Favorites / wishlist for logged-in customers
- A Wellness Hub blog with five long-form, original articles
- Customer dashboards (orders, reorder, saved blends, addresses, favorites, profile)
- A full administrator panel (products, orders, customers, reports, blog CMS, builder config, profile, messages, notifications)
- A 53-test unit-test suite covering business logic, security and seed integrity
- A complete sprint board plan and a 125-commit GitHub history plan in the `docs/` folder

## Quick start

```bash
# 1. Unpack and enter the project
unzip kcblendz.zip && cd kcblendz

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

Open <http://127.0.0.1:5000>. The database is created on first import (so gunicorn, Railway and other WSGI hosts all boot cleanly without a separate migration step). Seed data is inserted only if the database is empty.

On first boot the seed creates:

- 1 admin user
- 12 product categories
- 57 real products from the KCBlendz catalog
- 37 builder options (cup sizes, fruits, bases, sweeteners, add-ons, boosters)
- 5 long-form Wellness Hub articles
- 54 sample customer reviews so the UI is never empty

You will be redirected to the region picker — choose **Mauritius**, **Nigeria**, or **Global** to begin shopping.

## Default admin credentials

```
URL:       http://127.0.0.1:5000/admin
Email:     admin@kcblendz.com
Password:  KCBlendz@2026
```

## Sandbox payment test cards

These cards are only revealed on the live payment page to admin users; ordinary customers never see them. Use them to test the secure-card-entry flow without touching real money.

| Brand        | Number                 | Expiry       | CVV         |
| ------------ | ---------------------- | ------------ | ----------- |
| Visa         | `4242 4242 4242 4242`  | any future   | any 3-digit |
| Mastercard   | `5555 5555 5555 4444`  | any future   | any 3-digit |
| Amex         | `3782 822463 10005`    | any future   | `1234`      |

All numbers are real Luhn-valid test PANs that the live brand-detection JavaScript recognises as you type.

## Running the tests

The project ships with a 53-test unit-test suite (100% passing) covering business logic, route security, role separation, payment validation, custom-blend imagery, and seed data integrity.

```bash
# All tests, verbose
python -m unittest tests.py -v

# A specific suite
python -m unittest tests.CardValidationTests -v
python -m unittest tests.AuthTests -v
python -m unittest tests.AuthorizationTests -v
```

Test coverage summary:

| Suite                    | What it verifies                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| `CardValidationTests`    | Luhn checksum, brand detection, expiry/CVV/format validation                                            |
| `PublicRouteTests`       | Every public page returns 200; guest redirects work; sitemap and robots render                          |
| `AuthTests`              | Signup with one password, signup with matching/mismatched confirm, duplicate-email rejection, 2026 admin password works |
| `AuthorizationTests`     | Guests blocked from account and admin; customers blocked from admin; admin can reach every admin page  |
| `FavoritesAndReviewsTests` | Favorite toggle adds and removes; requires login; 404 on missing product; reviews submit and render    |
| `CustomBlendImageTests`  | Real-image mapper picks the dominant fruit; falls back safely                                          |
| `RegionHelperTests`      | Price-field mapping, currency mapping, formatted money output                                          |
| `CartTests`              | Add product, render cart, handle empty state                                                            |
| `SandboxVisibilityTests` | Admin sees sandbox test cards on the payment page; guests and customers do not                          |
| `SeedDataTests`          | Admin user, products, blog posts, reviews and builder options all seed correctly; every product has a real http image URL |

## Project structure

```
kcblendz/
├── app.py                  # Monolithic Flask app — routes, schema, seed data, business logic
├── tests.py                # 53 unit tests
├── requirements.txt        # Flask + Werkzeug
├── kcblendz.db             # SQLite, created on first import
├── README.md
├── docs/
│   ├── TRELLO_BOARD.md     # Sprint board template (lists, cards, subtasks)
│   └── GITHUB_COMMITS.md   # 125 commit messages across 5 team members
├── static/
│   ├── img/
│   │   ├── logo.png                 # The round glassy KCBlendz logo
│   │   ├── kcblendz-video.mp4       # The brand video on hero, region picker, builder preview
│   │   ├── kcblendz-catalog.jpeg    # Printed menu used as the pricing source
│   │   ├── kcblendz-product.png
│   │   ├── kcblendz-products.png
│   │   └── custom-cup.svg
│   ├── uploads/                     # Admin uploads + customer payment proofs
│   ├── css/  &  js/                 # Reserved for future custom assets
└── templates/
    ├── base.html                    # Brand palette, performance hints, WhatsApp button, flash UI
    ├── partials/
    │   ├── nav.html                 # Role-aware navigation (admin vs customer)
    │   └── footer.html              # Newsletter, address, payment badges
    ├── public/                      # All customer-facing pages
    │   ├── store_select.html        # Region picker with video background
    │   ├── home.html                # Hero with KCBlendz video
    │   ├── shop.html                # Filterable product grid
    │   ├── _product_card.html       # Shared product card with onerror fallback
    │   ├── product.html             # Detail + reviews + favorites + related
    │   ├── builder.html             # Custom smoothie builder with live video preview
    │   ├── cart.html, checkout.html
    │   ├── payment.html             # Real card-entry flow with live brand detection
    │   ├── order_thanks.html
    │   ├── wellness.html, wellness_post.html  # Long-form blog with markdown rendering
    │   ├── about.html, contact.html, faq.html
    │   └── privacy.html, terms.html, refund.html, shipping.html
    ├── auth/                        # login.html, register.html, forgot.html
    ├── account/                     # dashboard, orders, favorites, saved_smoothies, addresses, profile, notifications
    └── admin/                       # dashboard, products, orders, users, categories, blogs, builder_config, reports, profile, messages, notifications
```

