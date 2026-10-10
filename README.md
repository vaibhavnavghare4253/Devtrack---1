# DevTrack

A minimal Django backend for tracking engineering issues. Engineers (reporters) file bugs, assign priorities, and track status — similar to a stripped-down GitHub Issues.

Data is stored in two JSON files (`reporters.json` and `issues.json`) instead of a database. Domain objects are plain Python classes with inheritance, validation, and serialization.

## How to run

```bash
python -m pip install -r requirements.txt
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

No migrations are required. Storage files are created automatically if they are missing.

## Endpoints

### Reporters

| Method | URL | Description |
| --- | --- | --- |
| `POST` | `/api/reporters/` | Create a reporter |
| `GET` | `/api/reporters/` | List all reporters |
| `GET` | `/api/reporters/?id=1` | Get one reporter by ID |

**Create reporter**

```http
POST /api/reporters/
Content-Type: application/json

{
  "id": 1,
  "name": "Asha Patel",
  "email": "asha@example.com",
  "team": "backend"
}
```

Success: `201 Created` with the saved reporter.  
Validation failure: `400 Bad Request` with `{"error": "..."}`.  
Missing ID: `404` with `{"error": "Reporter not found"}`.

### Issues

| Method | URL | Description |
| --- | --- | --- |
| `POST` | `/api/issues/` | Create an issue |
| `GET` | `/api/issues/` | List all issues |
| `GET` | `/api/issues/?id=1` | Get one issue by ID |
| `GET` | `/api/issues/?status=open` | Filter issues by status |

**Create issue**

```http
POST /api/issues/
Content-Type: application/json

{
  "id": 1,
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1
}
```

Success (`201 Created`) includes a `message` from `describe()`. For `critical` priority that looks like:

```json
{
  "id": 1,
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1,
  "created_at": "2026-10-11 01:15:00.123456",
  "message": "[URGENT] Login button not working on mobile — needs immediate attention"
}
```

Empty title returns `400`:

```json
{
  "error": "Title cannot be empty"
}
```

Unknown issue ID returns `404`:

```json
{
  "error": "Issue not found"
}
```

Allowed statuses: `open`, `in_progress`, `resolved`, `closed`.  
Allowed priorities: `low`, `medium`, `high`, `critical`.

Priority subclasses:

- `critical` → `CriticalIssue.describe()`
- `low` → `LowPriorityIssue.describe()`
- `medium` / `high` → base `Issue.describe()`

## Design decision

**JSON files instead of the Django ORM.** The assignment asks for OOP classes (`BaseEntity`, `Reporter`, `Issue`) and file-backed storage, not Django models. Keeping domain objects as plain Python classes made `validate()`, `to_dict()`, and `describe()` easy to test and kept views as a thin layer: parse request → instantiate the right class → validate → persist JSON.

A second practical choice: API views are CSRF-exempt so Postman (and other API clients) can POST JSON without a CSRF cookie. That matches how this API is meant to be tested.

## OOP layout

- `BaseEntity` — abstract `validate()`, shared `to_dict()`
- `Reporter` / `Issue` — inherit from `BaseEntity`
- `CriticalIssue` / `LowPriorityIssue` — override `describe()`

Classes live in `issues/models.py`. Views import them; they are not mixed into view functions.

## Postman tests

Import the collection or create requests pointing at `http://127.0.0.1:8000`. Set header `Content-Type: application/json` on POST requests.

Suggested order:

1. `POST /api/reporters/` with a valid body
2. `POST /api/issues/` with `priority: "critical"` (success)
3. `POST /api/issues/` with `"title": ""` (validation failure)
4. `GET /api/issues/?id=1` (success)
5. `GET /api/issues/?id=999` (not found)

### Screenshots

Save Postman screenshots into `docs/screenshots/` after you run the collection (at least one success and one failure), then link them here:

1. `docs/screenshots/post-issue-success.png` — `POST /api/issues/` with a valid critical issue (`201`)
2. `docs/screenshots/post-issue-failure.png` — `POST /api/issues/` with an empty title (`400`)

A Postman collection is included: `DevTrack.postman_collection.json`. Import it in Postman, start the server, and run the requests in order (create reporter first).
