# IntelliReview — AI Code Reviewer

## Project Structure

```
intellireview/
├── main.py                        # FastAPI entry point
├── .env                           # Environment variables (NOT committed — see env_Version2.example)
├── env_Version2.example           # Example environment variables
├── requirements.txt               # Python dependencies
├── test_api.py                    # Manual API test script
├── reviews.db                     # SQLite database (auto-created, not committed)
└── app/
    ├── __init__.py
    ├── database.py                # DB engine, session, ReviewRecord model
    ├── models/
    │   ├── __init__.py
    │   └── code_request.py        # Pydantic request model
    ├── routes/
    │   ├── __init__.py
    │   └── review.py              # /review-code and /reviews endpoints
    ├── services/
    │   ├── __init__.py
    │   └── github_service.py      # GPT-4.1-nano AI review via GitHub Models
    ├── templates/
    │   └── index.html             # Main UI
    └── static/
        └── style.css
```

## Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/Sahil-Jak/IntelliReview-AI.git
cd IntelliReview-AI
```

### 2. Create your `.env` file
```bash
cp env_Version2.example .env
# Then fill in your GITHUB_TOKEN in .env
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
uvicorn main:app --reload
```

### 5. Open in browser
```
http://localhost:8000
```

### 6. Test the API directly
```bash
python test_api.py
```

## API Endpoints

| Method | Path              | Description                              |
|--------|-------------------|------------------------------------------|
| GET    | `/`               | Web UI                                   |
| POST   | `/review-code`    | Analyze code (body: `code`, `language`)  |
| GET    | `/reviews`        | Last 20 stored reviews                   |
| GET    | `/health`         | Health check                             |

## Environment Variables

Copy `env_Version2.example` to `.env` and fill in your values:

| Variable       | Description                        |
|----------------|------------------------------------|
| `GITHUB_TOKEN` | Your GitHub Personal Access Token  |
| `DATABASE_URL` | SQLite DB path (default provided)  |
