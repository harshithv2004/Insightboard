# InsightBoard 📊
**SQL-Based Business Reporting & Analytics Dashboard**

> Portfolio project demonstrating relational database design, advanced SQL, Flask web development, Chart.js visualizations, input validation, automated tests, and Git workflow.

---

## 🖥️ Screenshots

> _Run the app and add screenshots here after seeding data._

---

## 🚀 Features

| Feature | Description |
|---|---|
| Executive Dashboard | 4 KPI cards, monthly revenue line chart, regional bar chart, category donut, top products |
| Sales Report | Filterable by date/region/category/status, sortable columns, pagination, CSV export |
| Product Analytics | Top products bar chart, revenue by category donut, full comparison table |
| Customer Analytics | High-value customers, repeat buyer report, month-over-month growth (CTE + LAG) |
| CSV Export | Respects all active filters; same data definition as on-screen report |
| Input Validation | Date format, date ordering, region/category/status whitelist checks |
| Error Handling | No stack traces exposed; database errors logged server-side |
| Automated Tests | 30+ pytest tests covering queries, routes, and validation |

---

## 🗂️ Architecture

```
Browser (HTML/CSS/JS/Chart.js)
        │  fetch()
        ▼
Flask Application (routes.py)
        │  calls
        ▼
Services Layer (services.py)   ← validation, CSV generation
        │  calls
        ▼
SQL Reporting Layer (queries.py) ← parameterized queries
        │
        ▼
MySQL Database (insightboard)
        └── Customers, Products, Orders, OrderItems
```

**Design rule:** All business metrics are calculated from SQL queries. No hard-coded numbers.

---

## 🗄️ Database Schema (ER Summary)

```
Customers ──< Orders ──< OrderItems >── Products
   PK: customer_id    PK: order_id   PK: order_item_id    PK: product_id
                      FK: customer_id  FK: order_id
                                       FK: product_id
```

### Tables

| Table | Key Columns |
|---|---|
| `Customers` | customer_id PK, customer_name, email UNIQUE, region, signup_date |
| `Products` | product_id PK, product_name, category, unit_price ≥ 0 |
| `Orders` | order_id PK, customer_id FK, order_date, region, status ENUM |
| `OrderItems` | order_item_id PK, order_id FK, product_id FK, quantity > 0, unit_price ≥ 0 |

Indexes on `Orders(order_date)`, `Orders(region)`, `Orders(status)`, `Orders(customer_id)`, `OrderItems(product_id)`.

---

## 💡 SQL Concepts Demonstrated

| Concept | Where Used |
|---|---|
| Multi-table JOINs | All reports join 2–4 tables |
| Aggregations (SUM, COUNT, AVG) | KPIs, all chart queries |
| GROUP BY + ORDER BY | Monthly revenue, top products, regional |
| HAVING | Repeat customers (order_count > 1) |
| COALESCE / NULLIF | KPI query (safe division, null revenue) |
| CTE (WITH clause) | Month-over-month growth query |
| Window function (LAG) | Previous-month revenue in MoM growth |
| Parameterized queries | All queries use %s placeholders |
| CHECK constraints | quantity > 0, unit_price ≥ 0 |
| Foreign keys | All inter-table relationships |
| Indexes | Frequently-filtered columns |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Application logic |
| Flask 3.x | Web server + routing |
| MySQL 8+ | Relational database |
| mysql-connector-python | DB connectivity |
| python-dotenv | Environment variable management |
| HTML5 / CSS3 | Page structure + dark glassmorphism design |
| JavaScript (ES2022) | Dynamic fetch, Chart.js integration |
| Chart.js 4.x | Line, bar, horizontal bar, donut charts |
| pytest | Automated tests |
| Git / GitHub | Version control |

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.11+
- MySQL 8.0+ (running locally)
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/insightboard.git
cd insightboard
```

### 2. Create and activate virtual environment
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
copy .env.example .env
# Edit .env and set your MySQL password
```

`.env` contents:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=insightboard
DB_USER=root
DB_PASSWORD=your_password_here
SECRET_KEY=change-me-in-production
```

### 5. Create the MySQL schema
```bash
mysql -u root -p < sql/schema.sql
```

Or open `sql/schema.sql` in MySQL Workbench and execute.

### 6. Seed synthetic data
```bash
python sql/seed_data.py
```
Inserts 400 customers, 40 products, 1,500 orders, ~3,000 order items.

### 7. Run the application
```bash
python run.py
```

Open **http://localhost:5000** in your browser.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests do **not** require a live database (all DB calls are mocked).

### Test coverage summary

| Module | What is tested |
|---|---|
| `test_queries.py` | SQL contains correct WHERE/HAVING clauses, params include filter values, AOV zero-division safety, MoM uses CTE + LAG |
| `test_routes.py` | All pages return 200, API returns valid JSON structure, invalid filters → 400, CSV content-type and attachment headers |
| `test_validation.py` | Date format, date ordering, region/category/status whitelists, empty inputs, combined filters |

---

## 📁 Project Structure

```
insightboard/
├── app/
│   ├── __init__.py      Flask app factory
│   ├── db.py            Database connection (context manager)
│   ├── queries.py       All 7 parameterized SQL report functions
│   ├── routes.py        Flask blueprint (pages + API endpoints)
│   └── services.py      Validation, CSV generation, data aggregation
├── sql/
│   ├── schema.sql        DDL — CREATE TABLE + indexes
│   ├── seed_data.py      Synthetic data generator
│   └── reports.sql       Reference SQL queries (for MySQL Workbench)
├── static/
│   ├── css/style.css     Dark glassmorphism design system
│   └── js/
│       ├── dashboard.js  KPIs + 4 Chart.js charts
│       └── reports.js    Sales table, products charts, customers tables
├── templates/
│   ├── base.html         Sidebar layout
│   ├── dashboard.html    Executive dashboard
│   ├── sales.html        Sales report with pagination
│   ├── products.html     Product analytics
│   ├── customers.html    Customer analytics + MoM growth
│   └── errors/
│       ├── 404.html
│       └── 500.html
├── tests/
│   ├── conftest.py        pytest fixtures
│   ├── test_queries.py    SQL logic tests
│   ├── test_routes.py     Route + API tests
│   └── test_validation.py Input validation tests
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

---

## 📊 Metric Definitions

| Metric | Definition |
|---|---|
| Revenue | SUM(quantity × unit_price) for `status = 'Completed'` orders only |
| Total Orders | COUNT(DISTINCT order_id) for completed orders |
| Average Order Value | Revenue ÷ Total Orders (0 if no orders) |
| Unique Customers | COUNT(DISTINCT customer_id) with completed orders |
| Units Sold | SUM(quantity) for completed orders |
| Monthly Revenue | Revenue grouped by `DATE_FORMAT(order_date, '%Y-%m')` |

> The same definition is applied consistently to dashboard cards, report pages, and CSV exports.

---

## 🔒 Security

- All SQL queries use `%s` parameterized placeholders — no string concatenation with user input.
- Filter values are validated against a whitelist before reaching the query layer.
- Error responses never expose stack traces, credentials, or internal paths.
- `.env` is excluded from Git via `.gitignore`.

---

## ⚡ Performance

- Indexes on `Orders(order_date, region, status, customer_id)` and `OrderItems(product_id)`.
- Paginated sales report avoids full table scans on large datasets.
- Use `EXPLAIN` in MySQL Workbench to inspect query plans if performance degrades.

---

## ⚠️ Known Limitations

- Authentication/authorization not implemented (extend post-completion).
- No real-time refresh; data is fetched on page load and filter submission.
- Single-server deployment only (no load balancing or connection pooling).
- Synthetic data may not represent all real-world edge cases.
- Does not demonstrate Oracle, PL/SQL, Business Objects, or Tableau.

---

## 📅 Timeline

| Week | Work |
|---|---|
| 1 | Schema, seed data, 6 SQL reports validated in MySQL Workbench |
| 2 | Flask routes, JSON APIs, templates, charts, filters |
| 3 | Tests, CSV export, README, screenshots, GitHub release |

---

## 🎯 Resume Bullet Points (after completion)

- Designed a relational MySQL database for customers, orders, products, and order items using primary and foreign keys.
- Developed SQL reports using multi-table joins, aggregations, CTEs, and window functions to analyze revenue, regional performance, and product sales.
- Built a Flask web application with interactive KPI dashboards, date filters, data visualizations using Chart.js, and CSV report exports.
- Implemented input validation, database error handling, and 30+ automated pytest tests to verify report accuracy and data integrity.

---

## 📜 License

MIT — use freely for portfolio and learning purposes.
