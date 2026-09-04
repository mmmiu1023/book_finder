import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import re
from config import DEFAULT_HEADERS, KYOBO_DAEGU_STORES

class KyoboSearcher:
    def __init__(self):
        self.search_url = "https://search.kyobobook.co.kr/search"

    def search_books(self, query, max_results=10):
        """Search books on Kyobo Book Centre."""
        books = []
        try:
            params = {
                "keyword": query,
                "gbCode": "TOT",
                "target": "total"
            }
            res = requests.get(self.search_url, params=params, headers=DEFAULT_HEADERS, timeout=8)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                items = soup.select(".prod_item")
                for item in items[:max_results]:
                    title_elem = item.select_one(".prod_info .prod_name, a.prod_info")
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    link = title_elem.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://product.kyobobook.co.kr{link}"

                    # cmdtid / barcode
                    cmdtid = ""
                    if "detail/" in link:
                        cmdtid = link.split("detail/")[1].split("?")[0].split("/")[0]

                    # author & publisher
                    author_elem = item.select_one(".prod_author")
                    author = author_elem.text.strip() if author_elem else ""

                    # price
                    price_elem = item.select_one(".price .val")
                    price = price_elem.text.strip() if price_elem else ""

                    # image
                    img_elem = item.select_one(".prod_thumb_img img")
                    cover = img_elem.get("src", "") if img_elem else ""

                    # check Daegu stores directly if present in text
                    books.append({
                        "title": title,
                        "author": author,
                        "price": price,
                        "cmdtid": cmdtid,
                        "link": link,
                        "cover": cover,
                        "source": "교보문고"
                    })
        except Exception as e:
            print(f"[KyoboSearcher] Search error: {e}")

        return books

    def get_store_stock(self, cmdtid_or_isbn):
        """
        Check offline store stock for Kyobo branches in Daegu.
        """
        stores = []
        if not cmdtid_or_isbn:
            return stores

        try:
            # Check detail/pickup endpoint
            url = f"https://product.kyobobook.co.kr/api/gw/pdt/store-stock/list?saleCmdtid={cmdtid_or_isbn}"
            res = requests.get(url, headers=DEFAULT_HEADERS, timeout=6)
            if res.status_code == 200:
                try:
                    data = res.json()
                    stock_list = data.get("data", {}).get("storeStockList", [])
                    for s in stock_list:
                        store_name = s.get("storeName", "")
                        count = s.get("stockCount", 0)
                        is_daegu = any(d in store_name for d in ["대구", "칠곡", "영남"])
                        stores.append({
                            "store_name": store_name,
                            "count": count,
                            "is_daegu": is_daegu
                        })
                    if stores:
                        return stores
                except Exception:
                    pass
        except Exception as e:
            print(f"[KyoboSearcher] Stock check error: {e}")

        # Default Daegu branch representation
        return stores
