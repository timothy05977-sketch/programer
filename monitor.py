"""Background scheduler: periodically snapshots a list of ASINs."""
from __future__ import annotations
import time
import schedule
from rich.console import Console
from scraper.product import fetch_product
from storage.database import init_db, save_snapshot

console = Console()


def _job(asin: str) -> None:
    try:
        snap = fetch_product(asin)
        save_snapshot(snap)
        console.print(
            f"[green][{snap.fetched_at}][/green] {asin} | "
            f"Price: [bold]{snap.price}[/bold] | "
            f"Rating: {snap.rating} | "
            f"Reviews: {snap.review_count} | "
            f"Rank: {snap.sales_rank[:80] if snap.sales_rank != 'N/A' else 'N/A'}"
        )
    except Exception as exc:
        console.print(f"[red]Error fetching {asin}: {exc}[/red]")


def start_monitor(asins: list[str], interval_minutes: int) -> None:
    """Schedule periodic snapshots for each ASIN and block until interrupted."""
    init_db()
    console.print(
        f"[cyan]Monitoring {len(asins)} product(s) every {interval_minutes} min. "
        "Press Ctrl-C to stop.[/cyan]\n"
    )

    # Run immediately on start, then on schedule
    for asin in asins:
        _job(asin)
        schedule.every(interval_minutes).minutes.do(_job, asin=asin)

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor stopped.[/yellow]")
