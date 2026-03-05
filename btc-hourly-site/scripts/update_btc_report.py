#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf

TZ = ZoneInfo("Asia/Taipei")


def fmt(v, d=2):
    if v is None:
        return None
    return round(float(v), d)


def build_report():
    now = datetime.now(tz=TZ)
    ticker = yf.Ticker("BTC-USD")

    daily = ticker.history(period="180d", interval="1d", auto_adjust=False)
    closes = daily["Close"].dropna() if (not daily.empty and "Close" in daily) else []

    latest = closes.iloc[-1] if len(closes) else None
    prev = closes.iloc[-2] if len(closes) >= 2 else None

    change = (latest - prev) if (latest is not None and prev is not None) else None
    change_pct = ((change / prev) * 100) if (change is not None and prev not in (None, 0)) else None

    performance = []
    if len(closes) >= 2:
        tail = closes.tail(30)
        last_val = None
        for idx, val in tail.items():
            if last_val is None:
                last_val = val
                continue
            delta = val - last_val
            pct = (delta / last_val) * 100 if last_val else None
            ts = idx.tz_convert(TZ) if getattr(idx, "tzinfo", None) else idx.tz_localize(TZ)
            performance.append(
                {
                    "date": ts.strftime("%Y-%m-%d"),
                    "price": fmt(val, 2),
                    "change": fmt(delta, 2),
                    "changePercent": fmt(pct, 3),
                }
            )
            last_val = val

    trend = []
    if len(closes):
        for idx, val in closes.tail(90).items():
            ts = idx.tz_convert(TZ) if getattr(idx, "tzinfo", None) else idx.tz_localize(TZ)
            trend.append(
                {
                    "time": ts.strftime("%m-%d"),
                    "close": fmt(val, 2),
                }
            )

    return {
        "updatedAt": now.isoformat(),
        "timezone": "Asia/Taipei",
        "asset": "BTC-USD",
        "latest": {
            "price": fmt(latest, 2),
            "change": fmt(change, 2),
            "changePercent": fmt(change_pct, 3),
        },
        "source": {
            "name": "Yahoo Finance",
            "provider": "yfinance",
            "url": "https://finance.yahoo.com/",
            "interval": "1d",
        },
        "trendDaily": trend,
        "performanceDaily": performance,
    }


def main():
    report = build_report()

    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = data_dir / "latest.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Updated {out_file}")


if __name__ == "__main__":
    main()
