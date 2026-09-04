import subprocess
import urllib.parse
import os
import requests
from bs4 import BeautifulSoup
import re

class DaeguLibSearcher:
    def __init__(self):
        self.base_url = "http://library.daegu.go.kr"
        self.search_path = "/dgulib/intro/search/indexAll.do"

    def search_books(self, query, max_results=15):
        """
        Search books in Daegu Integrated Public Libraries.
        Returns holding libraries, call numbers, and loan availability.
        """
        results = []
        if not query:
            return results

        try:
            encoded_query = urllib.parse.quote(query)
            target_url = f"{self.base_url}{self.search_path}?menu_idx=7&title={encoded_query}&booktype=BOOKANDNONBOOK"
            
            curl_bin = 'curl.exe' if os.name == 'nt' else 'curl'
            cmd = [curl_bin, '-k', '-s', '-L', '--max-time', '10', target_url]
            html_content = ""
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if res.returncode == 0 and res.stdout:
                    html_content = res.stdout
            except Exception:
                pass

            if not html_content:
                # Fallback to requests if curl is unavailable
                try:
                    r = requests.get(target_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
                    if r.status_code == 200:
                        html_content = r.text
                except Exception:
                    pass

            if not html_content:
                return results

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # The search results in dgulib are in .bif or .book-list
            items = soup.select('.bif, .book-list > li, table.board-list tbody tr')
            if not items:
                items = soup.select('.resultList > li, tr')

            for item in items[:max_results]:
                title_elem = item.select_one('a[href*="detail.do"], .tit a, .title a, a.tit')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                # Clean up title formatting
                title = re.sub(r'\[.*?\]', '', title).strip()
                if not title:
                    title = title_elem.text.strip()

                link = title_elem.get('href', '')
                if link and not link.startswith('http'):
                    link = f"{self.base_url}/dgulib/intro/search/{link}"

                full_text = item.get_text(separator=' ', strip=True)
                
                # Extract Library name
                lib_name = "대구 공공도서관"
                if "소장도서관" in full_text:
                    parts = full_text.split("소장도서관")
                    if len(parts) > 1:
                        lib_part = parts[1].split("/")[0].replace(":", "").strip()
                        if lib_part:
                            lib_name = lib_part

                # Extract Call number / location
                call_no = ""
                if "위치" in full_text:
                    loc_parts = full_text.split("위치")
                    if len(loc_parts) > 1:
                        call_no = loc_parts[1].split("|")[0].replace(":", "").strip()

                # Loan status
                status = "대출가능"
                if "대출중" in full_text:
                    status = "대출중"
                elif "예약" in full_text:
                    status = "예약중"
                elif "열람" in full_text:
                    status = "관내열람"

                results.append({
                    "title": title,
                    "info": full_text[:120],
                    "library_name": lib_name,
                    "call_number": call_no,
                    "status": status,
                    "link": link,
                    "source": "대구통합도서관"
                })

        except Exception as e:
            print(f"[DaeguLibSearcher] Search error: {e}")

        return results
