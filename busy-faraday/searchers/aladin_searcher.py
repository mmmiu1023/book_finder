import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
from config import DEFAULT_ALADIN_TTBKEY, DEFAULT_HEADERS

class AladinSearcher:
    def __init__(self, ttbkey=None):
        self.ttbkey = ttbkey or DEFAULT_ALADIN_TTBKEY
        self.search_url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
        self.lookup_url = "http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx"

    def search_books(self, query, max_results=10):
        """Search books via Aladin Open API or fallback web search."""
        books = []
        # Try API first if ttbkey looks real
        if self.ttbkey and not self.ttbkey.startswith("sample") and not self.ttbkey.startswith("ttblaptop"):
            try:
                params = {
                    "ttbkey": self.ttbkey,
                    "Query": query,
                    "QueryType": "Title",
                    "MaxResults": max_results,
                    "start": 1,
                    "SearchTarget": "Book",
                    "output": "js",
                    "Version": "20131101"
                }
                res = requests.get(self.search_url, params=params, headers=DEFAULT_HEADERS, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    if "item" in data:
                        for item in data["item"]:
                            books.append({
                                "title": item.get("title", ""),
                                "author": item.get("author", ""),
                                "publisher": item.get("publisher", ""),
                                "pubDate": item.get("pubDate", ""),
                                "isbn13": item.get("isbn13", item.get("isbn", "")),
                                "priceStandard": item.get("priceStandard", 0),
                                "priceSales": item.get("priceSales", 0),
                                "cover": item.get("cover", ""),
                                "link": item.get("link", ""),
                                "description": item.get("description", ""),
                                "source": "알라딘 (API)"
                            })
                        if books:
                            return books
            except Exception as e:
                print(f"[AladinSearcher] API search error: {e}")

        # Web Crawling Fallback
        try:
            url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchWord={urllib.parse.quote(query)}"
            res = requests.get(url, headers=DEFAULT_HEADERS, timeout=8)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                boxes = soup.select(".ss_book_box")
                for box in boxes[:max_results]:
                    # Title
                    title_elem = box.select_one("a.bo3, a.bo_title, b")
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    link = title_elem.get("href", "")
                    if not link and title_elem.find_parent("a"):
                        link = title_elem.find_parent("a").get("href", "")

                    # Cover
                    img_elem = box.select_one("img.front_cover, img.cover")
                    cover = img_elem.get("src", "") if img_elem else ""

                    # Info (Author, publisher, date)
                    info_elem = box.select_one(".ss_book_list ul li:nth-child(2)") or box.select_one(".ss_book_list ul li:nth-child(3)")
                    info_text = info_elem.text.strip() if info_elem else ""

                    # ItemId / ISBN
                    isbn = ""
                    if link and "ItemId=" in link:
                        isbn = link.split("ItemId=")[1].split("&")[0]

                    # Price
                    price_sales = 0
                    price_elem = box.select_one(".ss_p2")
                    if price_elem:
                        digits = "".join([c for c in price_elem.text if c.isdigit()])
                        if digits:
                            price_sales = int(digits)

                    books.append({
                        "title": title,
                        "author": info_text,
                        "publisher": "",
                        "pubDate": "",
                        "isbn13": isbn,
                        "priceStandard": price_sales,
                        "priceSales": price_sales,
                        "cover": cover,
                        "link": link,
                        "description": "",
                        "source": "알라딘"
                    })
        except Exception as e:
            print(f"[AladinSearcher] Web search fallback error: {e}")

        return books

    def get_used_store_stock(self, isbn, title=""):
        """
        Check used store stock in Daegu branches (Dongseongro, Sangin).
        """
        store_stocks = []
        
        # Method 1: API lookup
        if self.ttbkey and not self.ttbkey.startswith("sample") and not self.ttbkey.startswith("ttblaptop") and isbn:
            try:
                params = {
                    "ttbkey": self.ttbkey,
                    "itemIdType": "ISBN13",
                    "ItemId": isbn,
                    "output": "js",
                    "Version": "20131101",
                    "OptResult": "usedStoreList"
                }
                res = requests.get(self.lookup_url, params=params, headers=DEFAULT_HEADERS, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    if "item" in data and len(data["item"]) > 0:
                        item = data["item"][0]
                        sub_info = item.get("subInfo", {})
                        used_store_list = sub_info.get("usedStoreList", [])
                        for store in used_store_list:
                            name = store.get("name", "")
                            is_daegu = any(d in name for d in ["대구", "동성로", "상인"])
                            store_stocks.append({
                                "store_name": name,
                                "count": store.get("count", 1),
                                "link": store.get("link", ""),
                                "is_daegu": is_daegu
                            })
                        if store_stocks:
                            return store_stocks
            except Exception as e:
                print(f"[AladinSearcher] Used store API error: {e}")

        # Method 2: Fallback Crawling off.aladin.co.kr
        search_kw = isbn if isbn else title
        if search_kw:
            try:
                url = f"https://off.aladin.co.kr/usedstore/wsearchresult.aspx?SearchWord={urllib.parse.quote(search_kw)}"
                res = requests.get(url, headers=DEFAULT_HEADERS, timeout=8)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    boxes = soup.select(".ss_book_box")
                    for box in boxes:
                        store_name = ""
                        store_badge = box.select_one(".used_store_name, .usedshop_off_btn, a[href*='off.aladin.co.kr/usedstore']")
                        if store_badge:
                            store_name = store_badge.text.strip()
                        if not store_name:
                            store_links = box.select("a[href*='usedstore/shop']")
                            if store_links:
                                store_name = ", ".join([sl.text.strip() for sl in store_links])

                        if store_name:
                            is_daegu = any(d in store_name for d in ["대구", "동성로", "상인"])
                            store_stocks.append({
                                "store_name": store_name,
                                "count": 1,
                                "link": url,
                                "is_daegu": is_daegu
                            })
            except Exception as e:
                print(f"[AladinSearcher] Used store crawl error: {e}")

        return store_stocks
