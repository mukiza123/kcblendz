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

