# Compute 30-day rolling annualized volatility and 14-day EWMA trend
hourly_bars['returns'] = hourly_bars['close'].pct_change()
hourly_bars['rolling_vol_30d'] = hourly_bars['returns'].rolling(window=30 * 24).std() * np.sqrt(365 * 24)
hourly_bars['ewma_fast'] = hourly_bars['close'].ewm(span=24 * 7, adjust=False).mean() # 7-day span
hourly_bars['ewma_slow'] = hourly_bars['close'].ewm(span=24 * 30, adjust=False).mean() # 30-day span
hourly_bars['regime_flag'] = np.where(hourly_bars['ewma_fast'] > hourly_bars['ewma_slow'], 'BULLISH', 'BEARISH')
