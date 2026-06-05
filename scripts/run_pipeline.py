from backend.ingestion.tiingo_client import ingest_prices
from backend.signals.signals import generate_signals
from backend.events.events import detect_events
from backend.ingestion.news_scraper import fetch_news


def main():
    print("Starting ingestion...")
    ingest_prices()

    print("Generating signals...")
    generate_signals()

    print("Detecting events...")
    detect_events()

    print("Fetching news...")
    fetch_news()

    print("Pipeline completed")


if __name__ == "__main__":
    main()