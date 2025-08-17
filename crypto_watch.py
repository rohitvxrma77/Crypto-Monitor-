from __future__ import annotations
import asyncio, time, argparse
from typing import Dict, List
import aiohttp
from colorama import init, Fore, Style

API = "https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids={ids}"

def parse_symbols(s: str) -> List[str]:
    return [x.strip().lower() for x in s.split(",") if x.strip()]

async def fetch_prices(session: aiohttp.ClientSession, ids: List[str]) -> Dict[str, float]:
    url = API.format(ids=",".join(ids))
    async with session.get(url, timeout=15) as r:
        r.raise_for_status()
        data = await r.json()
        return {k: float(v["usd"]) for k, v in data.items() if "usd" in v}

async def monitor(ids: List[str], interval: int, spike_pct: float):
    init(autoreset=True)
    history: Dict[str, float] = {}
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                prices = await fetch_prices(session, ids)
                ts = time.strftime("%H:%M:%S")
                for sym, price in prices.items():
                    prev = history.get(sym)
                    if prev:
                        change = ((price - prev) / prev) * 100
                        color = Fore.GREEN if change >= 0 else Fore.RED
                        print(f"{ts} {sym.upper():<6} ${price:,.4f}  {color}{change:+.2f}%{Style.RESET_ALL}")
                        if abs(change) >= spike_pct:
                            print(Fore.YELLOW + f"  >> Spike alert: {sym.upper()} moved {change:+.2f}% since last tick")
                    else:
                        print(f"{ts} {sym.upper():<6} ${price:,.4f}")
                    history[sym] = price
            except Exception as e:
                print("Error:", e)
            await asyncio.sleep(interval)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True, help="Comma-separated CoinGecko ids (e.g., btc,eth,sol)")
    p.add_argument("--interval", type=int, default=10, help="Seconds between fetches")
    p.add_argument("--spike", type=float, default=1.0, help="Spike alert threshold in %")
    args = p.parse_args()
    ids = parse_symbols(args.symbols)
    asyncio.run(monitor(ids, args.interval, args.spike))

if __name__ == "__main__":
    main()
