import difflib
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box
from src.utils import BANK_ALIASES, resolve_bank_alias, get_bank_type

console = Console()

class BankSelector:
    def __init__(self, banks_list):
        self.banks = sorted(set(b.strip().upper() for b in banks_list))
        self.categories = {}
        for b in self.banks:
            cat = get_bank_type(b)
            self.categories.setdefault(cat, []).append(b)

    def fuzzy_match(self, text):
        text = text.strip().upper()
        text = resolve_bank_alias(text).upper()
        if text in self.banks:
            return [("exact", text)]
        text_lower = text.lower()
        substr_matches = [b for b in self.banks if text_lower in b.lower()]
        if substr_matches:
            return [("partial", b) for b in substr_matches[:10]]
        close = difflib.get_close_matches(text, self.banks, n=5, cutoff=0.4)
        if close:
            return [("fuzzy", b) for b in close]
        return []

    def paginated_browse(self, banks_subset=None, title="Banks", page_size=15):
        items = banks_subset or self.banks
        total_pages = max(1, (len(items) + page_size - 1) // page_size)
        page = 0
        while True:
            start = page * page_size
            end = start + page_size
            page_items = items[start:end]
            table = Table(title=f"{title} — Page {page+1}/{total_pages}", box=box.ROUNDED)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Bank Name", style="white")
            table.add_column("Type", style="yellow", width=10)
            for i, bank in enumerate(page_items, start + 1):
                table.add_row(str(i), bank, get_bank_type(bank))
            console.print(table)
            console.print("[dim]n. next page | p. prev page | #. select | c. category filter | q. quit[/dim]")
            cmd = Prompt.ask("[yellow]Choice[/yellow]", default="q").strip().lower()
            if cmd == "n" and page < total_pages - 1:
                page += 1
            elif cmd == "p" and page > 0:
                page -= 1
            elif cmd == "c":
                cat_filter = Prompt.ask("[yellow]Category[/yellow]", default="all",
                                        choices=["all", "PSU", "PVT", "FOREIGN", "SFB", "PAYMENTS"])
                if cat_filter == "all":
                    items = self.banks
                else:
                    items = self.categories.get(cat_filter, [])
                total_pages = max(1, (len(items) + page_size - 1) // page_size)
                page = 0
            elif cmd == "q":
                return None
            else:
                try:
                    idx = int(cmd) - 1
                    if 0 <= idx < len(items):
                        return items[idx]
                    console.print("[red]Invalid number[/red]")
                except ValueError:
                    console.print("[red]Invalid input[/red]")

    def select(self, prompt_text="Select bank", allow_all=False, multi=False, show_browse_hint=True):
        hint = " (? to browse)" if show_browse_hint else ""
        all_suffix = " (or type 'all' for all banks)" if allow_all else ""
        while True:
            raw = Prompt.ask(f"[yellow]{prompt_text}{hint}{all_suffix}[/yellow]")
            if not raw.strip():
                if allow_all:
                    return None
                continue
            if raw.strip().lower() == "all" and allow_all:
                return None
            if raw.strip() == "?":
                selected = self.paginated_browse(title=prompt_text)
                if selected:
                    return selected if not multi else [selected]
                continue
            matches = self.fuzzy_match(raw)
            if not matches:
                console.print(f"[red]No bank found matching '{raw}'[/red]")
                console.print("[yellow]Press ? to browse all banks[/yellow]")
                continue
            if len(matches) == 1:
                bank = matches[0][1]
                console.print(f"[green]→ Selected: {bank}[/green]")
                return bank if not multi else [bank]
            if len(matches) <= 10:
                console.print("[yellow]Multiple matches:[/yellow]")
                for i, (match_type, bank) in enumerate(matches[:10], 1):
                    console.print(f"  {i}. {bank} [{match_type}]")
                choice = Prompt.ask("[yellow]Select number[/yellow]", default="1")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(matches):
                        bank = matches[idx][1]
                        console.print(f"[green]→ Selected: {bank}[/green]")
                        return bank if not multi else [bank]
                except:
                    pass
            console.print("[yellow]Too many matches. Press ? to browse or refine your search.[/yellow]")

    def select_multiple(self, prompt_text="Select banks", max_count=5):
        selected = []
        remaining = list(self.banks)
        while len(selected) < max_count:
            console.print(f"[cyan]Selected so far: {', '.join(selected) if selected else 'none'}[/cyan]")
            console.print(f"[dim]Select bank {len(selected)+1} of up to {max_count} (or 'done' to finish)[/dim]")
            bank = self.select(prompt_text, show_browse_hint=True)
            if bank is None:
                break
            if bank in selected:
                console.print(f"[yellow]Already selected: {bank}[/yellow]")
                continue
            selected.append(bank)
            remaining.remove(bank)
            add_more = Prompt.ask("[yellow]Add another?[/yellow]", choices=["y", "n"], default="y")
            if add_more == "n":
                break
        if not selected:
            console.print("[red]No banks selected[/red]")
            return None
        console.print(f"[green]Selected: {', '.join(selected)}[/green]")
        return selected

    def quick_select_compare(self):
        groups = {
            "1": ("Top 5 PSU Banks", ["STATE BANK OF INDIA", "BANK OF BARODA", "PUNJAB NATIONAL BANK",
                                       "BANK OF INDIA", "CANARA BANK"]),
            "2": ("Top 5 Private Banks", ["HDFC BANK LTD", "ICICI BANK LTD", "AXIS BANK LTD",
                                          "KOTAK MAHINDRA BANK LTD", "YES BANK LTD"]),
            "3": ("Top 5 by Volume (RBI Data)", []),
            "4": ("Custom Selection", []),
        }
        console.print("[cyan]Quick-select groups:[/cyan]")
        console.print("  1. Top 5 PSU Banks")
        console.print("  2. Top 5 Private Banks")
        console.print("  3. Top 5 by Transaction Volume")
        console.print("  4. Custom Selection (pick one by one)")
        console.print("  5. Cancel")
        choice = Prompt.ask("[yellow]Choose[/yellow]", choices=["1", "2", "3", "4", "5"])
        if choice == "1":
            return groups["1"][1]
        elif choice == "2":
            return groups["2"][1]
        elif choice == "3":
            from src.data_analysis import DataAnalysis
            da = DataAnalysis()
            top = list(da.top_banks("Total_Txn_Vol", 5).keys())
            if top:
                return top
            return groups["1"][1]
        elif choice == "4":
            return self.select_multiple()
        return None
