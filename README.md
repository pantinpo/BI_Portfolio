# E-commerce Sales Dashboard

End-to-end BI project: extract sales data with SQL, clean it with Python, and visualize it in Looker Studio.

**Live dashboard:** [link](#) <!-- add your Looker Studio link -->

![Dashboard screenshot](images/dashboard.png) <!-- add a screenshot -->

## Pipeline

```
ecommerce.db  →  extract_sales.sql  →  sales_raw.csv  →  clean_data.py  →  sales_clean.csv  →  Looker Studio
```

| Step | File | Tool |
|---|---|---|
| Extract | `extract_sales.sql` | SQL (SQLite) |
| Clean | `clean_data.py` | Python (pandas) |
| Visualize | Looker Studio | Connected to `sales_clean.csv` |

## Data

The data is synthetic, generated for this project. It models a US online retailer from January 2024 to September 2026: about 45,000 orders, 69,000 order lines, and 24,000 customers across five product categories.

The source database has six tables: `customers`, `orders`, `order_items`, `products`, `promotions`, and `returns`. It includes the kinds of problems real source systems produce:

| Issue | Cause | Fix |
|---|---|---|
| Three date formats | Website, app, and marketplace each store dates differently | Parse each known format |
| `Web` / `App` channel codes | Legacy values from before a system migration | Map to current names |
| `DELIVERED`, `Canceled`, `CA` | Marketplace feed and app use different conventions | Unify casing, aliases, expand state codes |
| `$19.99` and `10%` stored as text | Formatted values from feeds and manual entry | Strip symbols, convert to numbers |
| Duplicate rows | A data load that ran twice | Drop duplicates |
| Missing net sales and profit | Finance backfill not yet run | Recalculate from other columns |
| Missing city | Incomplete shipping data | Fill from the customer's other orders |
| Test orders | Left behind by QA | Remove |

The SQL extract is intentionally unfiltered. All cleaning happens in Python so the rules are in one place and validated before the data reaches the dashboard.

## Running it

```bash
sqlite3 -header -csv data/source/ecommerce.db < extract_sales.sql > data/raw/sales_raw.csv
pip install -r requirements.txt
python clean_data.py
```

## Key insights

<!-- add 3-5 findings from your dashboard -->

## Project structure

```
├── data/
│   ├── source/ecommerce.db
│   ├── raw/sales_raw.csv
│   └── processed/sales_clean.csv
├── extract_sales.sql
├── clean_data.py
└── requirements.txt
```
