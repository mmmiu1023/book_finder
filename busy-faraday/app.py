import streamlit as st
import concurrent.futures
import random
from searchers import (
    AladinSearcher,
    KyoboSearcher,
    DaeguLibSearcher,
    YULibSearcher,
    AIRecommender
)

# Page configuration
st.set_page_config(
    page_title="Book Finder - 대구/영남대 도서관 & 서점 통합 검색",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS styling (clean & mobile-friendly)
st.markdown("""
<style>
    /* Hide sidebar completely for a clean, full-width view */
    [data-testid="stSidebar"] {
        display: none;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
        line-height: 1.5;
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
</style>
""", unsafe_allow_html=True)

# Rich pool of popular books for dynamic refresh
POPULAR_BOOK_POOL = [
    "소년이 온다", "불편한 편의점", "클린 코드", "세이노의 가르침",
    "돈의 속성", "자존감 수업", "괴물의 심연", "혼자 공부하는 파이썬",
    "역행자", "물고기는 존재하지 않는다", "모순", "원씽",
    "마흔에 읽는 쇼펜하우어", "도둑맞은 집중력", "데미안", "사피엔스",
    "작별하지 않는다", "초역 니체의 말", "인간 실격", "트렌드 코리아"
]

# Initialize Session State
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "dynamic_suggestions" not in st.session_state:
    st.session_state.dynamic_suggestions = random.sample(POPULAR_BOOK_POOL, 4)
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Initialize Searcher instances
aladin_searcher = AladinSearcher()
kyobo_searcher = KyoboSearcher()
daegu_searcher = DaeguLibSearcher()
yu_searcher = YULibSearcher()
ai_recommender = AIRecommender()

# Main Header
st.markdown('<div class="main-title">📚 Book Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">대구지역 도서관 · 영남대 도서관 · 교보문고 · 알라딘 온/오프라인 중고매장 실시간 재고 확인</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 통합 도서 검색", "🤖 AI 도서 추천", "ℹ️ 서비스 기능 안내"])

# ==========================================
# Tab 1: Integrated Search
# ==========================================
with tab1:
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "도서명 또는 저자명 입력",
            value=st.session_state.search_query,
            placeholder="도서명 또는 저자명을 입력하세요 (예: 소년이 온다, 클린 코드)",
            label_visibility="collapsed"
        )
    with col_btn:
        search_clicked = st.button("통합 검색 🚀", use_container_width=True, type="primary")

    # Dynamic Recommendation Keywords with Refresh
    col_tag, col_refresh = st.columns([6, 1])
    with col_tag:
        st.markdown("<small style='color:#6B7280;'>🔥 추천 검색어: </small>", unsafe_allow_html=True)
    with col_refresh:
        if st.button("새로고침 🔄", key="refresh_suggestions", help="추천 검색어를 새로 섞습니다"):
            st.session_state.dynamic_suggestions = random.sample(POPULAR_BOOK_POOL, 4)
            st.rerun()

    q_cols = st.columns(4)
    for i, sq in enumerate(st.session_state.dynamic_suggestions):
        if q_cols[i].button(sq, key=f"quick_{i}_{sq}", use_container_width=True):
            st.session_state.search_query = sq
            st.rerun()

    active_query = query if query else st.session_state.search_query

    if search_clicked or (active_query and st.session_state.get("auto_search", False)):
        st.session_state.auto_search = False
        st.markdown(f"### 🔎 **'{active_query}'** 통합 검색 결과")

        with st.spinner("대구지역 도서관, 영남대, 교보문고, 알라딘 재고를 실시간 조회 중입니다..."):
            # Parallel execution for all 5 sources
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_daegu = executor.submit(daegu_searcher.search_books, active_query)
                future_yu = executor.submit(yu_searcher.search_books, active_query)
                future_kyobo = executor.submit(kyobo_searcher.search_books, active_query)
                future_aladin = executor.submit(aladin_searcher.search_books, active_query)

                daegu_results = future_daegu.result()
                yu_results = future_yu.result()
                kyobo_results = future_kyobo.result()
                aladin_results = future_aladin.result()

            # Check Aladin used stock for top book
            aladin_used_stocks = []
            target_isbn = aladin_results[0].get("isbn13", "") if aladin_results else ""
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

        # Result display sections in 2 columns
        col_lib, col_store = st.columns([1.1, 1])

        # Left Column: Libraries
        with col_lib:
            st.markdown("#### 🏛️ 무료 대출 (도서관)")
            lib_sub1, lib_sub2 = st.tabs(["대구통합도서관", "영남대학교 중앙도서관"])
            
            with lib_sub1:
                if daegu_results:
                    for item in daegu_results:
                        clean_title = item.get('title', '').replace('\n', ' ').strip()
                        clean_status = item.get('status', '확인필요')
                        status_badge = "status-badge-green" if "대출가능" in clean_status else "status-badge-red"
                        with st.container(border=True):
                            c_top1, c_top2 = st.columns([4, 1])
                            c_top1.markdown(f"**{clean_title}**")
                            c_top2.markdown(f"<span class='{status_badge}'>{clean_status}</span>", unsafe_allow_html=True)
                            st.caption(f"📍 소장처: **{item.get('library_name', '')}**")
                            if item.get('info'):
                                st.caption(item['info'])
                            st.markdown(f"[상세정보 & 대출 예약 바로가기 ↗]({item.get('link', '#')})")
                else:
                    st.info("대구 공공도서관에서 검색된 도서가 없습니다.")

            with lib_sub2:
                if yu_results:
                    for item in yu_results:
                        clean_title = item.get('title', '').replace('\n', ' ').strip()
                        clean_status = item.get('status', '대출가능')
                        status_badge = "status-badge-green" if "대출가능" in clean_status else "status-badge-red"
                        with st.container(border=True):
                            c_top1, c_top2 = st.columns([4, 1])
                            c_top1.markdown(f"**{clean_title}**")
                            c_top2.markdown(f"<span class='{status_badge}'>{clean_status}</span>", unsafe_allow_html=True)
                            st.caption(f"📍 위치: **{item.get('location', '')}** | 🏷️ 청구기호: {item.get('call_number') or '자료실 확인'}")
                            st.markdown(f"[영남대 소장자료 상세 보기 ↗]({item.get('link', '#')})")
                else:
                    st.info("영남대학교 도서관에서 검색된 도서가 없습니다.")

        # Right Column: Bookstores
        with col_store:
            st.markdown("#### 🛒 구매 (새책 & 중고매장)")
            store_sub1, store_sub2, store_sub3 = st.tabs(["알라딘 중고(대구)", "교보문고", "알라딘 온라인"])

            with store_sub1:
                st.caption("대구 동성로점 / 상인점 등 오프라인 중고 매장 재고")
                if aladin_used_stocks:
                    for s in aladin_used_stocks:
                        badge = "status-badge-blue" if s.get("is_daegu") else "status-badge-green"
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1])
                            c1.markdown(f"🏪 **{s['store_name']}**")
                            c2.markdown(f"<span class='{badge}'>보유 {s['count']}권</span>", unsafe_allow_html=True)
                            st.markdown(f"[알라딘 중고매장 재고 상세 ↗]({s['link']})")
                else:
                    st.info("현재 알라딘 대구 중고 매장에 입고된 재고가 없거나 조회 중입니다.")

            with store_sub2:
                if kyobo_results:
                    for item in kyobo_results:
                        clean_title = item.get('title', '').replace('\n', ' ').strip()
                        clean_author = item.get('author', '').replace('\n', ' ').strip()
                        clean_price = item.get('price', '').replace('\n', ' ').strip()
                        with st.container(border=True):
                            c_img, c_body = st.columns([1, 4])
                            if item.get('cover'):
                                c_img.image(item['cover'], width=65)
                            with c_body:
                                st.markdown(f"**{clean_title}**")
                                if clean_author:
                                    st.caption(clean_author)
                                if clean_price:
                                    st.markdown(f"<span style='color:#DC2626; font-weight:bold; font-size:0.95rem;'>{clean_price}</span>", unsafe_allow_html=True)
                                st.markdown(f"[교보문고 대구점/칠곡점 재고확인 & 구매 ↗]({item.get('link', '#')})")
                else:
                    st.info("교보문고에서 검색된 도서가 없습니다.")

            with store_sub3:
                if aladin_results:
                    for item in aladin_results:
                        clean_title = item.get('title', '').replace('\n', ' ').strip()
                        clean_author = item.get('author', '').replace('\n', ' ').strip()
                        price_sales = item.get('priceSales', 0)
                        with st.container(border=True):
                            c_img, c_body = st.columns([1, 4])
                            if item.get('cover'):
                                c_img.image(item['cover'], width=65)
                            with c_body:
                                st.markdown(f"**{clean_title}**")
                                if clean_author:
                                    st.caption(clean_author)
                                if price_sales:
                                    st.markdown(f"<span style='color:#059669; font-weight:bold; font-size:0.95rem;'>판매가: {price_sales:,}원</span>", unsafe_allow_html=True)
                                st.markdown(f"[알라딘 상세 & 구매하기 ↗]({item.get('link', '#')})")
                else:
                    st.info("알라딘에서 검색된 도서가 없습니다.")


# ==========================================
# Tab 2: AI Book Recommendation (Conversational)
# ==========================================
with tab2:
    st.markdown("### 🤖 AI 도서 추천")
    st.markdown("나에게 필요한 책이나 궁금한 분야를 사람에게 질문하듯 편하게 물어보세요.")

    # Conversational Welcome message if no chat yet
    if not st.session_state.chat_messages:
        st.info("💡 **질문 예시:**\n- *\"사이코 패스의 심리를 알고 싶은데 어떤 책이 좋을까?\"*\n- *\"채권 투자 관련해서 읽을만한 책 알려줘\"*\n- *\"비전공자가 읽기 좋은 파이썬 데이터 분석 입문서 알려줘\"*")

    # Display historical chat messages
    for msg_idx, msg in enumerate(st.session_state.chat_messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "books" in msg and msg["books"]:
                for b_idx, book in enumerate(msg["books"]):
                    with st.container(border=True):
                        st.markdown(f"#### {b_idx+1}. {book['title']}")
                        st.caption(f"**저자:** {book.get('author', '저자 정보')} | **분야:** {book.get('genre', '추천도서')}")
                        st.write(f"💡 **추천 이유:** {book.get('reason', '')}")
                        
                        if st.button(f"🔍 '{book['title']}' 대구/영남대 재고 바로 확인", key=f"chat_search_{msg_idx}_{b_idx}"):
                            st.session_state.search_query = book['title']
                            st.session_state.auto_search = True
                            st.rerun()

    # Chat Input Box
    user_prompt = st.chat_input("궁금한 심리, 기분, 공부하고 싶은 주제를 자유롭게 질문하세요...")

    if user_prompt:
        # Append User Message
        st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
        
        # Generate AI Recommendation
        with st.spinner("AI가 질문을 분석하고 알맞은 도서를 찾고 있습니다..."):
            recs = ai_recommender.recommend_books(user_prompt)
            reply_text = f"**'{user_prompt}'**에 대해 깊이 있는 통찰을 주는 추천 도서 {len(recs)}권을 엄선했습니다:"
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": reply_text,
                "books": recs
            })
        st.rerun()


# ==========================================
# Tab 3: Feature Guide (Clean & Focused)
# ==========================================
with tab3:
    st.markdown("""
    ### ℹ️ Book Finder 기능 소개

    **Book Finder**는 책을 대출하거나 구매할 때 여러 사이트를 일일이 들어가 확인하는 번거로움을 해결해 주는 원스톱 통합 검색 서비스입니다.

    ---

    #### 🏛️ 1. 대구광역시 통합도서관 실시간 연동
    - 대구 시내 **47개 공공도서관**(시립, 구·군립 도서관)의 소장 여부와 대출 가능 상태를 실시간으로 확인합니다.
    - 검색 결과에서 각 도서관의 상세 정보 및 대출 예약 페이지로 바로 이동할 수 있습니다.

    #### 🎓 2. 영남대학교 중앙도서관 실시간 연동
    - 영남대학교 중앙도서관 및 분관의 **소장 위치, 청구기호, 실시간 대출 상태**를 제공합니다.

    #### 🏪 3. 알라딘 대구 오프라인 중고매장 재고 연동
    - 알라딘 **대구 동성로점, 대구 상인점**에 입고된 중고 도서의 실시간 보유 권수를 파악합니다.

    #### 📖 4. 교보문고 실시간 재고 & 가격 조회
    - 교보문고 온라인 판매 가격 및 대구 지역 오프라인 매장(**대구점, 칠곡점**) 재고를 조회합니다.

    #### 📦 5. 알라딘 온라인 새책 정보
    - 알라딘 온라인 서점의 새책 판매 가격 및 상세 서지 정보를 실시간으로 확인합니다.

    #### 🤖 6. AI 맞춤 도서 추천 & 즉시 재고 연동
    - *"사이코패스의 심리를 알고 싶어"*, *"채권 관련 책 읽고 싶어"* 등 평소 대화하듯 질문하면 딱 맞는 실제 책을 추천해주고, 버튼 한 번으로 5개 도서관/서점의 실시간 재고를 바로 확인합니다.
    """)
