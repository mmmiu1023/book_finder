import streamlit as st
import concurrent.futures
import time
from searchers import (
    AladinSearcher,
    KyoboSearcher,
    DaeguLibSearcher,
    YULibSearcher,
    AIRecommender
)

# Page configuration
st.set_page_config(
    page_title="AI Book Finder - 대구/영남대 도서관 & 서점 통합 검색",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .status-badge-green {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-red {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-blue {
        background-color: #E1EFFE;
        color: #1E429F;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .book-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.1s ease;
    }
    .book-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.title("⚙️ 설정 & 옵션")

ttb_key = st.sidebar.text_input(
    "알라딘 TTB Key (선택)",
    value="",
    help="알라딘 OpenAPI 키가 없어도 웹 크롤링 방식으로 검색이 가능합니다."
)

gemini_key = st.sidebar.text_input(
    "Gemini API Key (선택)",
    value="",
    type="password",
    help="AI 추천 기능에 개인 API 키를 사용할 수 있습니다. (미입력 시 기본 추천 동작)"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📍 검색 대상 채널")
show_daegu = st.sidebar.checkbox("대구 통합 공공도서관", value=True)
show_yu = st.sidebar.checkbox("영남대학교 중앙도서관", value=True)
show_aladin_used = st.sidebar.checkbox("알라딘 중고매장 (대구)", value=True)
show_kyobo = st.sidebar.checkbox("교보문고 (온/오프라인)", value=True)
show_aladin_new = st.sidebar.checkbox("알라딘 (새책)", value=True)

# Initialize Searcher instances
aladin_searcher = AladinSearcher(ttbkey=ttb_key if ttb_key.strip() else None)
kyobo_searcher = KyoboSearcher()
daegu_searcher = DaeguLibSearcher()
yu_searcher = YULibSearcher()
ai_recommender = AIRecommender(api_key=gemini_key if gemini_key.strip() else None)

# Session state initialization
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Main Header
st.markdown('<div class="main-title">📚 AI Book Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">대구지역 도서관, 영남대 도서관, 교보문고, 알라딘 온·오프라인 중고매장까지 <b>한 번에 검색하고 실시간 소장/재고 확인</b></div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 통합 도서 검색", "🤖 AI 도서 추천 & 큐레이션", "📖 서비스 안내"])

# Tab 1: Integrated Search
with tab1:
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "도서명 또는 저자명 입력",
            value=st.session_state.search_query,
            placeholder="예: 소년이 온다, 클린 코드, 불편한 편의점, 파이썬",
            label_visibility="collapsed"
        )
    with col_btn:
        search_clicked = st.button("통합 검색 🚀", use_container_width=True, type="primary")

    # Quick search suggestions
    st.markdown("<small style='color:#6B7280;'>🔥 추천 검색어: </small>", unsafe_allow_html=True)
    q_cols = st.columns(4)
    sample_queries = ["소년이 온다", "불편한 편의점", "클린 코드", "세이노의 가르침"]
    for i, sq in enumerate(sample_queries):
        if q_cols[i].button(sq, key=f"quick_{i}", use_container_width=True):
            st.session_state.search_query = sq
            st.rerun()

    active_query = query if query else st.session_state.search_query

    if search_clicked or (active_query and st.session_state.get("auto_search", False)):
        st.session_state.auto_search = False
        st.markdown(f"### 🔎 **'{active_query}'** 통합 검색 결과")

        with st.spinner("대구지역 도서관, 영남대, 교보문고, 알라딘 재고를 실시간 조회 중입니다..."):
            # Parallel execution for speed
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_daegu = executor.submit(daegu_searcher.search_books, active_query) if show_daegu else None
                future_yu = executor.submit(yu_searcher.search_books, active_query) if show_yu else None
                future_kyobo = executor.submit(kyobo_searcher.search_books, active_query) if show_kyobo else None
                future_aladin = executor.submit(aladin_searcher.search_books, active_query) if (show_aladin_new or show_aladin_used) else None

                daegu_results = future_daegu.result() if future_daegu else []
                yu_results = future_yu.result() if future_yu else []
                kyobo_results = future_kyobo.result() if future_kyobo else []
                aladin_results = future_aladin.result() if future_aladin else []

            # Check for Aladin Used stock for top book
            aladin_used_stocks = []
            target_isbn = ""
            if aladin_results:
                target_isbn = aladin_results[0].get("isbn13", "")
            aladin_used_stocks = aladin_searcher.get_used_store_stock(target_isbn, active_query)

        # Overview metric cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(label="🏛️ 대구 공공도서관", value=f"{len(daegu_results)}건 발견")
        with m2:
            st.metric(label="🎓 영남대 중앙도서관", value=f"{len(yu_results)}건 발견")
        with m3:
            daegu_used_count = sum(1 for s in aladin_used_stocks if s.get("is_daegu", False))
            st.metric(label="🏪 알라딘 대구 중고매장", value=f"{daegu_used_count}개 매장 보유" if daegu_used_count else "재고 확인필요")
        with m4:
            st.metric(label="📖 교보문고 / 알라딘 새책", value=f"{len(kyobo_results) + len(aladin_results)}건 검색됨")

        st.markdown("---")

        # Result display sections in columns
        col_lib, col_store = st.columns([1.1, 1])

        # Left Column: Libraries (대구 공공도서관 & 영남대 도서관)
        with col_lib:
            st.markdown("#### 🏛️ 무료 대출 (도서관)")
            
            # Sub-tab for Libraries
            lib_sub1, lib_sub2 = st.tabs(["대구통합도서관", "영남대학교 중앙도서관"])
            
            with lib_sub1:
                if daegu_results:
                    for item in daegu_results:
                        status_class = "status-badge-green" if "대출가능" in item['status'] else "status-badge-red"
                        st.markdown(f"""
                        <div class="book-card">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <b style="font-size:1.05rem; color:#1F2937;">{item['title']}</b>
                                <span class="{status_class}">{item['status']}</span>
                            </div>
                            <p style="margin: 6px 0; color:#4B5563; font-size:0.9rem;">📍 소장처: <b>{item['library_name']}</b></p>
                            <p style="margin: 2px 0; color:#6B7280; font-size:0.85rem;">{item['info']}</p>
                            <div style="margin-top:8px;">
                                <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#2563EB; font-size:0.85rem; font-weight:600;">상세정보 & 대출 예약 바로가기 ↗</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("대구 공공도서관에서 검색된 도서가 없습니다.")

            with lib_sub2:
                if yu_results:
                    for item in yu_results:
                        status_class = "status-badge-green" if "대출가능" in item['status'] else "status-badge-red"
                        st.markdown(f"""
                        <div class="book-card">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <b style="font-size:1.05rem; color:#1F2937;">{item['title']}</b>
                                <span class="{status_class}">{item['status']}</span>
                            </div>
                            <p style="margin: 6px 0; color:#4B5563; font-size:0.9rem;">📍 위치: <b>{item['location']}</b></p>
                            <p style="margin: 2px 0; color:#6B7280; font-size:0.85rem;">🏷️ 청구기호: {item.get('call_number') or '자료실 확인'}</p>
                            <div style="margin-top:8px;">
                                <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#2563EB; font-size:0.85rem; font-weight:600;">영남대 소장자료 상세 보기 ↗</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("영남대학교 도서관에서 검색된 도서가 없습니다.")

        # Right Column: Bookstores (교보문고, 알라딘 중고 & 새책)
        with col_store:
            st.markdown("#### 🛒 구매 (새책 & 중고매장)")
            
            store_sub1, store_sub2, store_sub3 = st.tabs(["알라딘 중고(대구)", "교보문고", "알라딘 온라인"])

            with store_sub1:
                st.caption("대구 동성로점 / 상인점 등 오프라인 중고 매장 재고")
                if aladin_used_stocks:
                    for s in aladin_used_stocks:
                        badge = "status-badge-blue" if s.get("is_daegu") else "status-badge-green"
                        st.markdown(f"""
                        <div class="book-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-weight:600; font-size:1rem;">🏪 {s['store_name']}</span>
                                <span class="{badge}">보유 {s['count']}권</span>
                            </div>
                            <div style="margin-top:8px;">
                                <a href="{s['link']}" target="_blank" style="text-decoration:none; color:#2563EB; font-size:0.85rem; font-weight:600;">알라딘 중고매장 재고 상세 ↗</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(f"현재 알라딘 대구 중고 매장에 입고된 재고가 없거나 조회 중입니다. (온라인 알라딘 탭을 확인하세요)")

            with store_sub2:
                if kyobo_results:
                    for item in kyobo_results:
                        st.markdown(f"""
                        <div class="book-card">
                            <div style="display:flex; gap:12px;">
                                {"<img src='" + item['cover'] + "' style='width:50px; height:70px; object-fit:cover; border-radius:4px;'/>" if item.get('cover') else ""}
                                <div style="flex:1;">
                                    <b style="font-size:1rem; color:#1F2937;">{item['title']}</b>
                                    <p style="margin:2px 0; color:#4B5563; font-size:0.85rem;">{item['author']}</p>
                                    <p style="margin:2px 0; color:#DC2626; font-weight:600; font-size:0.9rem;">{item['price']}</p>
                                    <div style="margin-top:6px;">
                                        <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#2563EB; font-size:0.85rem; font-weight:600;">교보문고 대구점/칠곡점 재고확인 & 구매 ↗</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("교보문고에서 검색된 도서가 없습니다.")

            with store_sub3:
                if aladin_results:
                    for item in aladin_results:
                        st.markdown(f"""
                        <div class="book-card">
                            <div style="display:flex; gap:12px;">
                                {"<img src='" + item['cover'] + "' style='width:50px; height:70px; object-fit:cover; border-radius:4px;'/>" if item.get('cover') else ""}
                                <div style="flex:1;">
                                    <b style="font-size:1rem; color:#1F2937;">{item['title']}</b>
                                    <p style="margin:2px 0; color:#4B5563; font-size:0.85rem;">{item['author']}</p>
                                    <p style="margin:2px 0; color:#059669; font-weight:600; font-size:0.9rem;">판매가: {item['priceSales']:,}원</p>
                                    <div style="margin-top:6px;">
                                        <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#2563EB; font-size:0.85rem; font-weight:600;">알라딘 상세 & 구매하기 ↗</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("알라딘에서 검색된 도서가 없습니다.")


# Tab 2: AI Book Recommendation
with tab2:
    st.markdown("### 🤖 AI 맞춤 도서 추천 & 큐레이션")
    st.markdown("원하는 기분, 상황, 학습 목표를 자유롭게 말씀해 주시면 AI가 최적의 책을 추천해 드립니다.")

    ai_col_input, ai_col_btn = st.columns([5, 1])
    with ai_col_input:
        user_prompt = st.text_input(
            "상황이나 읽고 싶은 분야를 입력하세요",
            placeholder="예: 요즘 인간관계 때문에 지치는데 위로가 되는 소설이나 에세이 추천해줘",
            label_visibility="collapsed"
        )
    with ai_col_btn:
        recommend_btn = st.button("AI 추천받기 ✨", type="primary", use_container_width=True)

    # Preset prompts
    st.markdown("<small style='color:#6B7280;'>💡 추천 요청 예시: </small>", unsafe_allow_html=True)
    p_cols = st.columns(3)
    presets = [
        "힐링과 위로가 필요한 날 읽을 따뜻한 에세이",
        "비전공자를 위한 파이썬/AI 기초 입문서",
        "몰입감 넘치는 한국 스릴러/미스터리 소설"
    ]
    for i, p in enumerate(presets):
        if p_cols[i].button(p, key=f"preset_{i}", use_container_width=True):
            user_prompt = p
            recommend_btn = True

    if recommend_btn and user_prompt:
        with st.spinner("AI 큐레이터가 최적의 책을 선별하고 있습니다..."):
            recs = ai_recommender.recommend_books(user_prompt)

        st.markdown(f"#### 📖 **'{user_prompt}'**에 대한 AI 추천 도서")
        
        for idx, book in enumerate(recs):
            with st.container():
                st.markdown(f"""
                <div class="book-card" style="border-left: 4px solid #3B82F6;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; color:#1E3A8A;">{idx+1}. {book['title']}</h4>
                        <span class="status-badge-blue">{book.get('genre', '추천도서')}</span>
                    </div>
                    <p style="margin:4px 0 8px 0; color:#4B5563;"><b>저자:</b> {book['author']}</p>
                    <p style="margin:4px 0; color:#374151; font-size:0.95rem; line-height:1.5;">💡 <b>추천 이유:</b> {book['reason']}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🔍 '{book['title']}' 대구/영남대 재고 바로 검색하기", key=f"search_rec_{idx}"):
                    st.session_state.search_query = book['title']
                    st.session_state.auto_search = True
                    st.rerun()


# Tab 3: About
with tab3:
    st.markdown("""
    ### ℹ️ AI Book Finder 서비스 소개

    **AI Book Finder**는 책을 읽고 싶을 때 매번 여러 도서관과 서점 사이트를 각각 들어가서 재고를 확인해야 하는 번거로움을 해결하기 위해 제작되었습니다.

    #### 🎯 연동 시스템 및 지원 채널
    1. **대구통합도서관**: 대구광역시 내 시립, 구·군립 공공도서관(47개관)의 실시간 소장 및 대출 가능 여부
    2. **영남대학교 중앙도서관**: 중앙도서관 및 분관의 소장 위치, 청구기호, 대출 상태
    3. **알라딘 중고매장 (대구)**: 대구 동성로점, 대구 상인점의 오프라인 중고 보유 재고
    4. **교보문고**: 온/오프라인(대구점, 칠곡점) 재고 및 판매 가격
    5. **알라딘 온라인**: 새책 판매가 및 도서 상세 서지 정보

    #### 💡 사용 팁
    - **알라딘 TTB Key**: 사이드바에 알라딘 TTB Key를 입력하시면 더 정밀한 상품 정보 및 중고 재고 API를 활용할 수 있습니다. (미입력 시에도 크롤링 엔진으로 동작합니다)
    - **AI 맞춤 추천**: 읽고 싶은 주제나 현재 고민을 편하게 입력하시면 AI가 책을 골라주고, 클릭 한 번으로 대구 지역 도서관/서점 재고를 즉시 찾아드립니다.
    """)
