import os

# Aladin OpenAPI TTBKey (Can be overridden by environment variable or UI)
DEFAULT_ALADIN_TTBKEY = os.environ.get("ALADIN_TTBKEY", "ttblaptop1747001") # placeholder or user key

# Target store names in Daegu
ALADIN_DAEGU_STORES = ["대구동성로점", "대구상인점"]
KYOBO_DAEGU_STORES = ["대구점", "칠곡센터", "영남대점"]

# Request Headers
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}
