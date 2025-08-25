import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import pandas as pd
import re
import json


class NoticeCrawlerAgent:
    BASE_URL = "https://library.sogang.ac.kr"
    NOTICE_URL = "https://library.sogang.ac.kr/bbs/list/1"
    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SogangNoticeBot/1.0)"}

    def __init__(self, output_dir: str = "database"):
        self.output_file = Path(output_dir) / "notices.json"
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    # === 크롤링 메서드 ===
    def fetch_notices(self) -> pd.DataFrame:
        """공지사항 목록 크롤링"""
        all_data = []
        page = 1
        stop_crawling = False

        while not stop_crawling:
            url = f"{self.NOTICE_URL}?pn={page}"
            resp = requests.get(url, headers=self.HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            rows = soup.select("table tbody tr")
            if not rows:
                break

            for tr in rows:
                cols = tr.find_all("td")
                if len(cols) < 5:
                    continue

                no = cols[0].get_text(strip=True)
                title_cell = cols[1]
                a = title_cell.find("a")
                title = a.get_text(strip=True) if a else title_cell.get_text(strip=True)
                href = urljoin(self.BASE_URL, a["href"]) if a and a.has_attr("href") else self.NOTICE_URL
                author = cols[2].get_text(strip=True)
                date = cols[3].get_text(strip=True)
                views = cols[4].get_text(strip=True)

                # 2024 또는 2025만 가져오기
                if not (date.startswith("2024") or date.startswith("2025")):
                    stop_crawling = True
                    break

                all_data.append({
                    "No.": no,
                    "제목": title,
                    "작성자": author,
                    "작성일": date,
                    "조회수": views,
                    "링크": href
                })

            page += 1

        return pd.DataFrame(all_data)

    def fetch_notice_detail(self, url: str) -> dict:
        """공지사항 상세 페이지 크롤링"""
        r = requests.get(url, headers=self.HEADERS, timeout=10)
        r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")

        content =   s.select_one(".boardContent") or \
                    s.select_one(".board-view .board-txt") or \
                    s.select_one(".bbs_view .view_con") or \
                    s.select_one(".contents") or \
                    s.select_one("article") or \
                    s.select_one("#content")

        body_parts = []
        if content:
            for img in content.find_all("img"):
                img_url = urljoin(self.BASE_URL, img.get("src"))
                body_parts.append(f"![이미지]({img_url})")

            text_only = self.clean_notice_content(content)
            if text_only:
                body_parts.append(text_only)

        body_text = "\n".join(body_parts)

        # 첨부파일
        atts = []
        for a in s.select('a[href]'):
            href = a["href"]
            if any(k in href.lower() for k in ["download", "attach", "file", "files"]):
                atts.append({"name": a.get_text(strip=True), "url": urljoin(self.BASE_URL, href)})

        seen = set()
        attachments = []
        for x in atts:
            if x["url"] not in seen:
                seen.add(x["url"])
                attachments.append(x)

        title = (s.select_one("h3, h2, .title, .board-tit") or content)
        title_text = title.get_text(strip=True) if title else ""

        return {
            "url": url,
            "title": title_text,
            "body": body_text,
            "attachments": attachments,
        }

    def clean_notice_content(self, content):
        """본문 텍스트 정리"""
        for br in content.find_all("br"):
            br.replace_with("\n")
        text = content.get_text()
        clean_text = re.sub(r'\n{3,}', '\n\n', text)
        return clean_text.strip()

    # === JSON 저장 ===
    def create_notices_json(self):
        """공지사항 목록 + 상세 내용을 JSON으로 저장"""
        print("📢 공지사항 목록 가져오는 중...")
        notice_df = self.fetch_notices()

        if notice_df.empty:
            print("가져올 공지사항이 없습니다.")
            return

        all_notices = []
        for _, row in notice_df.iterrows():
            url = row["링크"]
            try:
                print(f"➡️ 상세 내용 가져오는 중: {url}")
                notice_detail = self.fetch_notice_detail(url)

                notice_data = {
                    "source": url,
                    "title": row["제목"],
                    "author": row["작성자"],
                    "date": row["작성일"],
                    "content": notice_detail["body"]
                }
                all_notices.append(notice_data)

            except Exception as e:
                print(f"❌ 상세 내용 가져오기 실패: {url}, 오류: {e}")
                continue

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(all_notices, f, ensure_ascii=False, indent=4)
        print(f"✅ 공지사항 데이터가 '{self.output_file}'에 저장되었습니다.")

    # === 에이전트 실행 ===
    def run(self):
        """Agent 실행"""
        self.create_notices_json()
        return f"✅ 공지사항 데이터가 {self.output_file} 에 저장 완료되었습니다."


if __name__ == "__main__":
    agent = NoticeCrawlerAgent()
    agent.run()
