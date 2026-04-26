import streamlit as st
from database import get_user_transactions, get_user_reviews, get_conn

def show_profile():
    user = st.session_state.user
    st.markdown("<h1 class='page-title'>👤 Meu Perfil</h1>", unsafe_allow_html=True)

    # Refresh user data
    conn = get_conn()
    fresh = conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
    conn.close()
    if fresh:
        fresh = dict(fresh)
        st.session_state.user = fresh
        user = fresh

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-val'>⭐ {user['reputation']:.1f}</div>
            <div class='stat-label'>Reputação</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-val'>📦 {user['total_sales']}</div>
            <div class='stat-label'>Vendas</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        transactions = get_user_transactions(user["id"])
        volume = sum(t["amount"] for t in transactions if t["seller_id"] == user["id"])
        vol_str = f"R$ {volume:,.0f}".replace(",",".")
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-val'>💰 {vol_str}</div>
            <div class='stat-label'>Volume vendido</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        reviews = get_user_reviews(user["id"])
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-val'>💬 {len(reviews)}</div>
            <div class='stat-label'>Avaliações</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2 = st.tabs(["📜 Histórico de Transações", "⭐ Avaliações Recebidas"])

    with tab1:
        if not transactions:
            st.info("Nenhuma transação ainda.")
        for t in transactions:
            is_seller = t["seller_id"] == user["id"]
            role = "Vendedor" if is_seller else "Comprador"
            amount_str = f"R$ {t['amount']:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            fee_str = f"R$ {t['platform_fee']:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            st.markdown(f"""
            <div class='transaction-row'>
                <strong>{t['title']}</strong> · {role} · {amount_str}
                <span class='fee-badge'>Taxa: {fee_str}</span>
                <span class='tx-date'>{str(t['created_at'])[:10]}</span>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        if not reviews:
            st.info("Nenhuma avaliação recebida ainda.")
        for r in reviews:
            stars = "⭐" * r["rating"] + "☆" * (5 - r["rating"])
            st.markdown(f"""
            <div class='review-card'>
                <div class='review-stars'>{stars}</div>
                <div class='review-author'>por <strong>{r['reviewer_name']}</strong> · {str(r['created_at'])[:10]}</div>
                <div class='review-comment'>{r.get('comment') or '—'}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ✍️ Avaliar um usuário")
    with st.form("review_form"):
        conn = get_conn()
        users = conn.execute("SELECT id, username FROM users WHERE id != ? AND is_admin=0", (user["id"],)).fetchall()
        conn.close()
        users = [dict(u) for u in users]
        if users:
            target = st.selectbox("Usuário", users, format_func=lambda u: u["username"])
            rating = st.slider("Nota", 1, 5, 5)
            comment = st.text_area("Comentário (opcional)")
            if st.form_submit_button("Enviar avaliação ⭐"):
                from database import create_review
                create_review(user["id"], target["id"], 0, rating, comment)
                st.success("Avaliação enviada!")
                st.rerun()
        else:
            st.info("Nenhum usuário para avaliar.")
