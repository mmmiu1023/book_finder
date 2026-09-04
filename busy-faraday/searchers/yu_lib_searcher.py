import requests
from bs4 import BeautifulSoup
import urllib.parse
import urllib3
from config import DEFAULT_HEADERS
urllib3.disable_warnings()

class YULibSearcher:
    def __init__(self):
        self.base_url = "https://libs.yu.ac.kr"
        self.search_url = f"{self.base_url}/search/tot/result"

    def search_books(self, query, max_results=10):
        """
        Search books in Yeungnam University Library.
        Returns book titles, location (중앙도서관/과학도서관 등), call numbers, and loan availability.
        """
        results = []
        if not query:
            return results

        try:
            params = {
                "st": "KWRD",
                "si": "TOTAL",
                "q": query
            }
            res = requests.get(self.search_url, params=params, headers=DEFAULT_HEADERS, verify=False, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Each result is an item
                items = soup.select(".briefDetail, dl.briefDetail, li.items, div.briefContent")
                if not items:
                    items = soup.select("ul.searchResult > li, div.searchResultItem")

                for item in items[:max_results]:
                    title_elem = item.select_one(".title a, a.searchTitle, h4.title, .searchTitle")
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link = title_elem.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"{self.base_url}{link}"

                    # Author / Publisher / Year info
                    info_elem = item.select_one(".author, .info, .briefEtc, dd.author")
                    info_text = info_elem.text.strip() if info_elem else ""

                    # Holding / Call number / Status
                    status_elem = item.select_one(".status, .holding, span.state, .itemState, .holdInfo")
                    status_text = status_elem.text.strip() if status_elem else ""

                    location = "영남대 중앙도서관"
                    call_no = ""
                    status = "대출가능"

                    if status_text:
                        status = status_text
                        if "[" in status_text and "]" in status_text:
                            call_no = status_text.split("[")[1].split("]")[0]
                            location = status_text.split("[")[0].strip()

                    # Fallback keyword matching
                    if not status_text:
                        full_text = item.text
                        if "대출가능" in full_text:
                            status = "대출가능"
                        elif "대출중" in full_text:
                            status = "대출중"
                        elif "예약중" in full_text:
                            status = "예약중"

                    results.append({
                        "title": title,
                        "info": info_text,
                        "location": location or "영남대학교 중앙도서관",
                        "call_number": call_no,
                        "status": status,
                        "link": link,
                        "source": "영남대학교 도서관"
                    })

        except Exception as e:
            print(f"[YULibSearcher] Search error: {e}")

        return results
