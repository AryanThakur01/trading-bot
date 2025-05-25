import os
import json
import hashlib


class CacheManager:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _generate_cache_key(self, symbol, startDate, interval, limit=None, max_candles=None):
        key = f"{symbol}_{startDate}_{interval}_{limit}_{max_candles}"
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def load(self, symbol, startDate, interval, limit=None, max_candles=None):
        path = self._generate_cache_key(symbol, startDate, interval, limit, max_candles)
        if os.path.exists(path):
            with open(path, 'r') as f:
                print(f"[CacheManager] Loaded from cache: {path}")
                return json.load(f)
        return None

    def save(self, data, symbol, startDate, interval, limit=None, max_candles=None):
        path = self._generate_cache_key(symbol, startDate, interval, limit, max_candles)
        with open(path, 'w') as f:
            json.dump(data, f)
        print(f"[CacheManager] Saved to cache: {path}")

    def clear_cache(self):
        for file in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, file))
        print("[CacheManager] Cache cleared.")
