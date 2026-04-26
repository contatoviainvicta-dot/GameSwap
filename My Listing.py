import streamlit as st
from database import get_user_listings, create_listing, delete_listing
import base64

PLATFORMS = ["PlayStation 5", "PlayStation 4", "Xbox Series X/S", "Xbox One",
             "Nintendo Switch", "PC", "Game Boy", "Retro", "Outro"]
CATEGORIES = ["Jogo", "Console", "Acessório", "Controle", "Headset", "Outro"]
CONDITIONS = ["novo", "otimo", "bom", "regular"]
CONDITION_LABELS = {"novo": "🟢 Novo", "otimo": "🟡 Ótimo", "bom": "🔵 Bom", "regular": "🟠 Regular"}

def show_my_listings():
    user = st.session_state.user
    st.markdown("<h1 class='page-title'>📦 Meus Anúncios</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Meus Anúncios", "➕ Novo Anúncio"])

    with tab1:
        listings = get_user_listings(user["id"])
        if not listings:
            st.markdown("""
            <div class='empty-state'>
                <div class='empty-icon'>📦</div>
                <h3>Você ainda não tem anúncios</h3>
                <p>Clique em "Novo Anúncio" para começar a vender!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for listing in listings:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        status_map = {"active": "🟢 Ativo", "sold": "✅ Vendido", "removed": "🔴 Removido"}
                        st.markdown(f"""
                        <div class='my-listing-row'>
                            <strong>{listing['title']}</strong><br>
                            {listing['platform']} · {CONDITION_LABELS.get(listing['condition'], listing['condition'])} · {status_map.get(listing['status'], listing['status'])}
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        price = f"R$ {listing['price']:,.2f}".replace(",","X").replace(".",",").replace("X",".") if listing.get("price") else "—"
                        ltype = {"venda": "💰 Venda", "troca": "🔄 Troca", "venda_troca": "💰🔄"}.get(listing["listing_type"], "")
                        st.markdown(f"**{price}** · {ltype} · 👁 {listing.get('views',0)}")
                    with col3:
                        if listing["status"] == "active":
                            if st.button("🗑️ Remover", key=f"del_{listing['id']}"):
                                delete_listing(listing["id"], user["id"])
                                st.success("Anúncio removido.")
                                st.rerun()
                    st.markdown("<hr style='margin:6px 0;opacity:0.15'>", unsafe_allow_html=True)

    with tab2:
        show_new_listing_form(user)

def show_new_listing_form(user):
    st.markdown("### Criar novo anúncio")
    with st.form("new_listing_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Título do anúncio *", placeholder="Ex: God of War Ragnarök - PS5")
            platform = st.selectbox("Plataforma *", PLATFORMS)
            category = st.selectbox("Categoria *", CATEGORIES)
            condition = st.selectbox("Condição *", CONDITIONS, format_func=lambda x: CONDITION_LABELS[x])
        with col2:
            listing_type = st.selectbox("Tipo de anúncio *", ["venda", "troca", "venda_troca"],
                                        format_func=lambda x: {"venda":"💰 Venda","troca":"🔄 Troca","venda_troca":"💰🔄 Venda e Troca"}[x])
            price = st.number_input("Preço (R$)", min_value=0.0, step=10.0, value=0.0)
            uploaded_img = st.file_uploader("Foto do produto", type=["jpg","jpeg","png"])

        description = st.text_area("Descrição", placeholder="Descreva o produto, inclua detalhes como: acompanha caixa, manual, estado dos botões...", height=100)
        submitted = st.form_submit_button("📢 Publicar anúncio", use_container_width=True)

        if submitted:
            if not title:
                st.error("O título é obrigatório.")
            else:
                image_data = None
                if uploaded_img:
                    image_data = base64.b64encode(uploaded_img.read()).decode()
                create_listing({
                    "user_id": user["id"],
                    "title": title,
                    "description": description,
                    "category": category,
                    "platform": platform,
                    "condition": condition,
                    "price": price if price > 0 else None,
                    "listing_type": listing_type,
                    "image_data": image_data,
                })
                st.success("✅ Anúncio publicado com sucesso!")
                st.rerun()
