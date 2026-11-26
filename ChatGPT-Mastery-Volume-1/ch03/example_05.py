import pandas as pd
import numpy as np

# Ingest irregular trade execution stream
ticks_df = pd.read_csv('/mnt/data/irregular_trade_ticks.csv')
ticks_df['timestamp'] = pd.to_datetime(ticks_df['timestamp'], utc=True)
ticks_df.set_index('timestamp', inplace=True)

# Resample to 1-Hour OHLCV (Open, High, Low, Close, Volume) Financial Bars
hourly_bars = ticks_df['price'].resample('1H').ohlc()
hourly_bars['volume'] = ticks_df['volume'].resample('1H').sum().fillna(0)

# Forward-fill closing prices for zero-volume holiday/weekend hours
hourly_bars['close'] = hourly_bars['close'].ffill()
hourly_bars['open'] = hourly_bars['open'].fillna(hourly_bars['close'])
hourly_bars['high'] = hourly_bars['high'].fillna(hourly_bars['close'])
hourly_bars['low'] = hourly_bars['low'].fillna(hourly_bars['close'])

print(f"Standardized {len(ticks_df):,} raw ticks into {len(hourly_bars):,} continuous hourly bars.")
