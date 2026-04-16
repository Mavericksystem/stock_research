from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

def create_dirs(dirs):
    for d in dirs:
        path = BASE_DIR / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Directory created: {path}")

def create_files(files):
    for f in files:
        path = BASE_DIR / f
        path.parent.mkdir(parents=True, exist_ok=True)   # ensure parent exists
        if not path.exists():
            path.touch()
            print(f"File created: {path}")
        else:
            print(f"File already exists: {path}")

def main():
    dirs = [
        "src/config",
        "src/db",
        "src/api",
        "src/ingestion",
        "src/processing",
        "src/context",
        "src/rag",
        "src/services",
        "src/utils",
        "scripts",
        "tests"
    ]
    files = [
        "README.md",
        "requirements.txt",
        ".env",
        ".gitignore",

        "src/config/settings.py",
        "src/db/connection.py",
        "src/db/models.py",
        "src/db/queries.py",

        "src/ingestion/yfinance_client.py",
        "src/ingestion/news_scraper.py",

        "src/processing/indicators.py",
        "src/processing/signals.py",

        "src/context/engine.py",
        
        "src/rag/retriever.py",
        "src/rag/generator.py",

        "src/services/stock_service.py",
        "src/services/analysis_service.py",

        "src/api/main.py",
        "src/api/routes/stock.py",
        "src/api/routes/analysis.py",
        "src/api/routes/ask.py",

        "src/utils/helpers.py",

        "src/scripts/fetch_prices.py",
        "tests/test_yfinance.py",
    ]

    create_dirs(dirs)
    create_files(files)

if __name__ == "__main__":    
    main()