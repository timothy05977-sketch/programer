#!/usr/bin/env python3
"""Amazon Product Tracker CLI"""
import sys
import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def cli():
    """Amazon Product Tracker — fetch bestsellers and monitor product sales."""


# ── bestsellers ───────────────────────────────────────────────────────────────

@cli.command("bestsellers")
@click.option(
    "--category", "-c", default="all",
    help="Category slug: all, electronics, books, toys, kitchen, clothing, sports, beauty, home",
)
@click.option("--pages", "-p", default=1, show_default=True, help="Number of pages to fetch (each ~50 items).")
@click.option("--top", "-n", default=20, show_default=True, help="Show top N results.")
def cmd_bestsellers(category: str, pages: int, top: int):
    """Fetch and display Amazon Best Sellers for a category."""
    from scraper.bestsellers import fetch_bestsellers, BESTSELLER_CATEGORIES
    from config import BESTSELLER_CATEGORIES as CATS

    if category not in CATS:
        console.print(f"[red]Unknown category '{category}'. Valid: {', '.join(CATS)}[/red]")
        sys.exit(1)

    console.print(f"[cyan]Fetching bestsellers: category=[bold]{category}[/bold], pages={pages}...[/cyan]")
    try:
        items = fetch_bestsellers(category, pages)
    except Exception as exc:
        console.print(f"[red]Failed to fetch bestsellers: {exc}[/red]")
        sys.exit(1)

    items = items[:top]
    if not items:
        console.print("[yellow]No items found. Amazon may have blocked the request.[/yellow]")
        return

    table = Table(title=f"Amazon Best Sellers — {category.title()}", show_lines=True)
    table.add_column("Rank", style="bold cyan", width=5)
    table.add_column("ASIN", style="dim", width=12)
    table.add_column("Title", max_width=50)
    table.add_column("Price", style="green", width=10)
    table.add_column("Rating", width=8)
    table.add_column("Reviews", width=10)

    for item in items:
        table.add_row(
            str(item.rank),
            item.asin or "—",
            item.title,
            item.price,
            item.rating,
            item.review_count,
        )

    console.print(table)


# ── snapshot ──────────────────────────────────────────────────────────────────

@cli.command("snapshot")
@click.argument("asin")
def cmd_snapshot(asin: str):
    """Take a one-off snapshot of a product page."""
    from scraper.product import fetch_product
    from storage.database import init_db, save_snapshot

    init_db()
    console.print(f"[cyan]Fetching product [bold]{asin}[/bold]...[/cyan]")
    try:
        snap = fetch_product(asin)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)

    save_snapshot(snap)

    table = Table(title=f"Product Snapshot — {asin}", show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    for field, value in [
        ("ASIN", snap.asin),
        ("Title", snap.title),
        ("Price", snap.price),
        ("Rating", snap.rating),
        ("Reviews", snap.review_count),
        ("Availability", snap.availability),
        ("Sales Rank", snap.sales_rank),
        ("Fetched At", snap.fetched_at),
    ]:
        table.add_row(field, value)
    console.print(table)


# ── monitor ───────────────────────────────────────────────────────────────────

@cli.command("monitor")
@click.argument("asins", nargs=-1, required=True)
@click.option(
    "--interval", "-i", default=60, show_default=True,
    help="Check interval in minutes.",
)
def cmd_monitor(asins: tuple[str, ...], interval: int):
    """Periodically monitor one or more products (by ASIN) and record snapshots."""
    from monitor import start_monitor
    start_monitor(list(asins), interval)


# ── history ───────────────────────────────────────────────────────────────────

@cli.command("history")
@click.argument("asin")
@click.option("--limit", "-l", default=20, show_default=True, help="Number of recent entries.")
def cmd_history(asin: str, limit: int):
    """Show historical snapshots for a product."""
    from storage.database import get_history

    rows = get_history(asin, limit)
    if not rows:
        console.print(f"[yellow]No history found for ASIN {asin}.[/yellow]")
        return

    table = Table(title=f"History — {asin} (latest {limit})", show_lines=True)
    table.add_column("Time (UTC)", style="dim")
    table.add_column("Price", style="green")
    table.add_column("Rating")
    table.add_column("Reviews")
    table.add_column("Availability")
    table.add_column("Sales Rank", max_width=40)

    for row in rows:
        table.add_row(
            row["fetched_at"],
            row["price"],
            row["rating"],
            row["review_count"],
            row["availability"],
            row["sales_rank"],
        )

    console.print(table)


# ── list-tracked ──────────────────────────────────────────────────────────────

@cli.command("list-tracked")
def cmd_list_tracked():
    """List all ASINs that have been monitored."""
    from storage.database import list_tracked_asins

    asins = list_tracked_asins()
    if not asins:
        console.print("[yellow]No products tracked yet.[/yellow]")
        return

    console.print("[bold]Tracked ASINs:[/bold]")
    for a in asins:
        console.print(f"  • {a}")


if __name__ == "__main__":
    cli()
