## Library Management System API (Django + DRF)

Production-ready backend API for managing library resources: books, users, and transactions (checkout/return). Built with Django, Django REST Framework, and JWT authentication.

### Features
- Books CRUD with unique ISBN, total/available copy tracking
- Users CRUD with membership fields (admin-only writes)
- Secure authentication: Session/Basic for browsing, JWT for clients
- Borrowing workflow: one active checkout per user/book, atomic stock updates
- Returns workflow with date logging and stock increment
- List available books; search by title/author/ISBN; filter/paginate
- User self profile and borrowing history endpoints

### Tech Stack
- Django 5, Django REST Framework, django-filter
- djangorestframework-simplejwt (JWT)
- SQLite by default (swap to Postgres/MySQL via `DATABASES`)
- Gunicorn + Procfile for deployment

---

## Quickstart

1) Clone and create a virtual environment
```bash
git clone <your-repo-url>
cd Alx_capstone/library_api
python -m venv ../venv
..
\venv\Scripts\activate  # Windows PowerShell
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Apply migrations and create a superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

4) Run the development server
```bash
python manage.py runserver
# http://127.0.0.1:8000/api/
```

5) Admin site
```
http://127.0.0.1:8000/admin/
```

---

## Authentication

The API supports Session/Basic (for browsable API) and JWT for programmatic access.

- Obtain access/refresh tokens:
  - POST `/api/token/` with form or JSON body `{ "username": "<user>", "password": "<pass>" }`
- Refresh an access token:
  - POST `/api/token/refresh/` with `{ "refresh": "<refresh_token>" }`
- Use tokens:
  - Add header: `Authorization: Bearer <access_token>`

Example (curl):
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpass"}'
```

---

## Data Model

- `User` (extends Django `AbstractUser`)
  - `date_of_membership` (date)
  - `is_active_member` (bool)

- `Book`
  - `title`, `author`, `isbn` (unique)
  - `published_date` (optional)
  - `copies_total`, `copies_available` (validation ensures available ≤ total)

- `Transaction`
  - `user`, `book`
  - `checkout_date`, `return_date`
  - DB constraint: only one active checkout per (user, book)

---

## API Endpoints

Base path: `/api/`

### Users
- `GET /users/` (auth) list users (admin sees all; non-admin read-only)
- `GET /users/{id}/` (auth) retrieve user
- `POST /users/` (admin) create user
- `PUT/PATCH/DELETE /users/{id}/` (admin) update/delete user
- `GET /users/me/` (auth) current user profile
- `GET /users/me/transactions/` (auth) current user borrowing history

### Books
- `GET /books/` list books (search/paginate)
  - Search: `?search=<query>` over `title`, `author`, `isbn`
  - Filters: `?copies_available__gt=0` etc.
- `GET /books/{id}/` retrieve book
- `POST /books/` (admin) create book
- `PUT/PATCH /books/{id}/` (admin) update book
- `DELETE /books/{id}/` (admin) delete book
- `GET /books/available/` list only books with `copies_available > 0`

### Transactions (borrowing)
- `GET /transactions/` (auth) list all transactions (read-only viewset)
- `POST /transactions/checkout/` (auth)
  - Body: `{ "book": <book_id> }`
  - Rules: requires available copies; one active checkout per user/book
- `POST /transactions/return/` (auth)
  - Body: `{ "book": <book_id> }`
  - Sets `return_date` and increments availability

Example checkout (curl):
```bash
ACCESS=... # obtain via /api/token/
curl -X POST http://127.0.0.1:8000/api/transactions/checkout/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"book": 1}'
```

---

## Pagination & Filtering

Enabled globally via DRF settings:
- Pagination: `PageNumberPagination` (`PAGE_SIZE=10`)
- Filters: `django-filter` and `SearchFilter`
- Books expose: `search_fields = ["title", "author", "isbn"]`, and `filterset_fields` on `copies_available`.

---

## Configuration

Environment variables (recommended for production):
- `DEBUG=false`
- `SECRET_KEY=<strong secret>`
- `ALLOWED_HOSTS=yourdomain.com`
- `DATABASE_URL` or configure `DATABASES` in settings for Postgres/MySQL

`settings.py` highlights:
- `AUTH_USER_MODEL = 'library_api.core.User'`
- `REST_FRAMEWORK` uses JWT + Session + Basic auth
- `SIMPLE_JWT` token lifetimes configurable

---

## Deployment

### Heroku (outline)
1) Add a `Procfile` (already included):
```
web: gunicorn library_api.wsgi --log-file -
```
2) Add `gunicorn` to `requirements.txt` (already included)
3) Set environment variables (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
4) Use a production database (e.g., Postgres) and run `python manage.py migrate`

### PythonAnywhere (outline)
1) Upload code or connect to your repo
2) Create a virtualenv and `pip install -r requirements.txt`
3) Set WSGI app to `library_api.wsgi`
4) Configure environment variables and run migrations

---

## Development Tips

- Use the browsable API at `/api/` while authenticated (Session auth) for easy testing
- For programmatic tests, prefer JWT with the endpoints above
- Create initial data via admin or fixtures

---

## Troubleshooting

- 401 Unauthorized: ensure you include `Authorization: Bearer <token>` or login to browsable API
- 400 on checkout: book not available or already checked out by you
- Migration/app import issues: ensure `INSTALLED_APPS` uses `library_api.core` and run `python manage.py makemigrations && migrate`

---

## License

MIT (or your chosen license)

##########
