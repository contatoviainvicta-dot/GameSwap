import streamlit as st
from database import get_admin_stats

def show_admin_panel():
    st.markdown("<h1 class='page-title'>⚙️ Painel Administrativo</h1>", unsafe_allow_html=True)

    stats = get_admin_stats()

    # KPI cards
    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        ("👥", stats["total_users"], "Usuários"),
        ("📦", stats["active_listings"], "Anúncios Ativos"),
        ("🔄", stats["total_transactions"], "Transações"),
        (f"💰", f"R$ {stats['total_volume']:,.0f}".replace(",","."), "Volume Total"),
        ("🏦", f"R$ {stats['total_revenue']:,.2f}".replace(",","X").replace(".",",").replace("X","."), "Receita (5%)"),
    ]
    for col, (icon, val, label) in zip([c1, c2, c3, c4, c5], cards):
        with col:
            st.markdown(f"""
            <div class='stat-card admin-stat'>
                <div class='stat-icon'>{icon}</div>
                <div class='stat-val'>{val}</div>
                <div class='stat-label'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏆 Top Vendedores")
        if stats["top_users"]:
            for i, u in enumerate(stats["top_users"], 1):
                st.markdown(f"""
                <div class='top-user-row'>
                    <span class='rank'>#{i}</span>
                    <span class='uname'>{u['username']}</span>
                    <span class='usales'>{u['total_sales']} vendas</span>
                    <span class='urep'>⭐ {u['reputation']:.1f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma venda ainda.")

    with col2:
        st.markdown("#### 📊 Últimas Transações")
        if stats["recent_transactions"]:
            for t in stats["recent_transactions"][:5]:
                amount_str = f"R$ {t['amount']:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                fee_str = f"R$ {t['platform_fee']:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                st.markdown(f"""
                <div class='transaction-row'>
                    <strong>{t['title'][:25]}...</strong><br>
                    {t['seller']} → {t['buyer']} · {amount_str}
                    <span class='fee-badge'>+{fee_str}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma transação ainda.")
