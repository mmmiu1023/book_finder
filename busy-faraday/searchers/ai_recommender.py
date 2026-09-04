import os
import json

class AIRecommender:
    def __init__(self, api_key=None, provider="gemini"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.provider = provider

    def recommend_books(self, user_query):
        """
        Takes user query/mood/interests and returns a list of recommended book titles,
        authors, and reasons for recommendation.
        """
        # If API key is available, attempt LLM call
        if self.api_key:
            try:
                # Try google-genai / google-generativeai
                if self.provider == "gemini" or "AIza" in self.api_key:
                    import google.generativeai as genai
                    genai.configure(api_key=self.api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
당신은 최고의 도서 큐레이터 및 사서 AI입니다.
사용자의 요청에 맞는 도서 3~5권을 엄선하여 추천해 주세요.
사용자 요청: "{user_query}"

응답은 반드시 아래 JSON 형식만을 반환해야 합니다 (마크다운 코드블록 제외하고 순수 JSON 또는 ```json ... ``` 형식):
[
  {{
    "title": "도서 정확한 제목",
    "author": "저자명",
    "genre": "장르/분야",
    "reason": "이 책을 추천하는 구체적이고 따뜻한 이유 (2~3문장)"
  }}
]
"""
                    response = model.generate_content(prompt)
                    text = response.text.strip()
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()
                    return json.loads(text)
            except Exception as e:
                print(f"[AIRecommender] LLM generation error: {e}")

        # Fallback intelligent rule-based / keyword-based recommendations
        fallback_recommendations = self._fallback_recommend(user_query)
        return fallback_recommendations

    def _fallback_recommend(self, query):
        """Rule-based recommendations if no API key is provided."""
        q = query.lower()
        if any(w in q for w in ["힐링", "위로", "지칠", "마음", "휴식", "에세이"]):
            return [
                {
                    "title": "불편한 편의점",
                    "author": "김호연",
                    "genre": "소설/힐링",
                    "reason": "골목길 작은 편의점을 무대로 따뜻한 온기와 일상의 위로를 전하는 베스트셀러 소설입니다."
                },
                {
                    "title": "어서 오세요, 휴남동 서점입니다",
                    "author": "황보름",
                    "genre": "소설/힐링",
                    "reason": "지친 일상을 잠시 멈추고 자신만의 속도를 찾아가는 사람들의 따뜻한 이야기입니다."
                },
                {
                    "title": "보이지 않는 곳에서 애쓰고 있는 너에게",
                    "author": "최대호",
                    "genre": "에세이",
                    "reason": "남들은 모르는 나의 노력과 지친 마음을 다독여주는 다정한 문장들로 채워져 있습니다."
                }
            ]
        elif any(w in q for w in ["파이썬", "코딩", "개발", "프로그래밍", "컴퓨터", "ai", "인공지능"]):
            return [
                {
                    "title": "혼자 공부하는 파이썬",
                    "author": "윤인성",
                    "genre": "컴퓨터/IT",
                    "reason": "입문자도 쉽게 따라 할 수 있도록 그림과 친절한 설명으로 구성된 파이썬 바이블입니다."
                },
                {
                    "title": "Do it! 점프 투 파이썬",
                    "author": "박응용",
                    "genre": "컴퓨터/IT",
                    "reason": "수많은 개발자들의 첫걸음이 되어준 파이썬 기초의 정석 교재입니다."
                },
                {
                    "title": "클린 코드 Clean Code",
                    "author": "로버트 C. 마틴",
                    "genre": "컴퓨터/IT",
                    "reason": "읽기 쉽고 유지보수하기 좋은 훌륭한 소프트웨어를 작성하는 핵심 원칙을 제시합니다."
                }
            ]
        elif any(w in q for w in ["소설", "문학", "한강", "이야기", "추리"]):
            return [
                {
                    "title": "소년이 온다",
                    "author": "한강",
                    "genre": "한국소설",
                    "reason": "노벨문학상 수상 작가 한강의 대표작으로 깊은 울림과 역사적 아픔을 시적인 문체로 다룹니다."
                },
                {
                    "title": "작별하지 않는다",
                    "author": "한강",
                    "genre": "한국소설",
                    "reason": "지극한 사랑과 기억의 연대를 눈부신 문장으로 펼쳐낸 감동적인 대작입니다."
                },
                {
                    "title": "구의 증명",
                    "author": "최진영",
                    "genre": "한국소설",
                    "reason": "사랑과 상실, 존재의 의미를 파격적이면서도 애절하게 그려낸 스테디셀러 소설입니다."
                }
            ]
        else:
            return [
                {
                    "title": "소년이 온다",
                    "author": "한강",
                    "genre": "한국문학",
                    "reason": "인간의 존엄성과 사랑을 깊이 있게 응시한 필독 문학 작품입니다."
                },
                {
                    "title": "불편한 편의점",
                    "author": "김호연",
                    "genre": "한국소설",
                    "reason": "남녀노소 누구나 편안하고 재미있게 몰입해서 읽을 수 있는 힐링 스토리입니다."
                },
                {
                    "title": "세이노의 가르침",
                    "author": "세이노",
                    "genre": "자기계발",
                    "reason": "현실적이고 직설적인 조언으로 삶의 태도와 경제적 자유를 일깨워주는 책입니다."
                }
            ]
