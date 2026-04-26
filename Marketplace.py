import streamlit as st
from database import get_listings, increment_views, create_transaction, get_conn
import base64

PLATFORMS = ["Todos", "PlayStation 5", "PlayStation 4", "Xbox Series X/S", "Xbox One",
             "Nintendo Switch", "PC", "Game Boy", "Retro", "Outro"]
LISTING_TYPES = ["Todos", "venda", "troca", "venda_troca"]
CONDITIONS = {"novo": "🟢 Novo", "otimo": "🟡 Ótimo", "bom": "🔵 Bom", "regular": "🟠 Regular"}

def show_marketplace():
    st.markdown("<h1 class='page-title'>🛒 Marketplace</h1>", unsafe_allow_html=True)

    # Filters
    with st.container():
        st.markdown("<div class='filter-bar'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
        with c1:
            search = st.text_input("🔍 Buscar", placeholder="Ex: God of War, PS5, Nintendo...")
        with c2:
            platform = st.selectbox("Plataforma", PLATFORMS)
        with c3:
            ltype = st.selectbox("Tipo", ["Todos", "Venda", "Troca"])
        with c4:
            max_price = st.number_input("Preço máx (R$)", min_value=0, value=0, step=50)
        st.markdown("</div>", unsafe_allow_html=True)

    type_map = {"Todos": "Todos", "Venda": "venda", "Troca": "troca"}
    filters = {
        "search": search,
        "platform": platform,
        "listing_type": type_map.get(ltype, "Todos"),
        "max_price": max_price if max_price > 0 else None,
    }

    listings = get_listings(filters)

    if not listings:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-icon'>🎮</div>
            <h3>Nenhum anúncio encontrado</h3>
            <p>Tente outros filtros ou seja o primeiro a anunciar!</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"<p class='results-count'>{len(listings)} anúncio(s) encontrado(s)</p>", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, listing in enumerate(listings):
        with cols[i % 3]:
            show_listing_card(listing)

def show_listing_card(listing):
    ltype_label = {"venda": "💰 Venda", "troca": "🔄 Troca", "venda_troca": "💰🔄 Venda/Troca"}.get(listing["listing_type"], "")
    condition_label = CONDITIONS.get(listing["condition"], listing["condition"])
    price_str = f"R$ {listing['price']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if listing.get("price") else "A combinar"

    img_html = ""
    if listing.get("image_data"):
        img_html = f'<img src="data:image/jpeg;base64,{listing["image_data"]}" class="card-img"/>'
    else:
        img_html = f'<div class="card-img-placeholder">🎮</div>'

    card_html = f"""
    <div class='listing-card'>
        {img_html}
        <div class='card-body'>
            <div class='card-type-badge'>{ltype_label}</div>
            <h4 class='card-title'>{listing['title']}</h4>
            <div class='card-meta'>
                <span class='platform-tag'>{listing['platform']}</span>
                <span class='condition-tag'>{condition_label}</span>
            </div>
            <div class='card-price'>{price_str}</div>
            <div class='card-seller'>👤 {listing['username']} &nbsp; ⭐ {listing['reputation']:.1f}</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    if st.button("Ver detalhes", key=f"detail_{listing['id']}", use_container_width=True):
        increment_views(listing["id"])
        st.session_state["viewing_listing"] = listing
        st.session_state["show_listing_modal"] = True
        show_listing_detail(listing)

def show_listing_detail(listing):
    with st.expander(f"📋 {listing['title']}", expanded=True):
        col1, col2 = st.columns([1, 1.2])
        with col1:
            if listing.get("image_data"):
                img_bytes = base64.b64decode(listing["image_data"])
                st.image(img_bytes, use_container_width=True)
            else:
                st.markdown("<div class='big-placeholder'>🎮</div>", unsafe_allow_html=True)

        with col2:
            ltype_label = {"venda": "💰 Venda", "troca": "🔄 Troca", "venda_troca": "💰🔄 Venda/Troca"}.get(listing["listing_type"], "")
            st.markdown(f"### {listing['title']}")
            st.markdown(f"**Tipo:** {ltype_label}")
            st.markdown(f"**Plataforma:** {listing['platform']}")
            st.markdown(f"**Condição:** {CONDITIONS.get(listing['condition'], listing['condition'])}")
            st.markdown(f"**Categoria:** {listing.get('category', '-')}")
            if listing.get("price"):
                price_str = f"R$ {listing['price']:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                st.markdown(f"**Preço:** 💲 {price_str}")
            if listing.get("description"):
                st.markdown(f"**Descrição:** {listing['description']}")
            st.markdown(f"**Vendedor:** {listing['username']} ⭐ {listing['reputation']:.1f}")
            st.markdown(f"**Visualizações:** 👁 {listing.get('views', 0)}")

            user = st.session_state.get("user")
            if user and user["id"] != listing["user_id"]:
                st.markdown("---")
                if listing["listing_type"] in ("venda", "venda_troca") and listing.get("price"):
                    if st.button("💳 Comprar agora", key=f"buy_{listing['id']}", use_container_width=True):
                        fee, seller_amt = create_transaction({
                            "listing_id": listing["id"],
                            "seller_id": listing["user_id"],
                            "buyer_id": user["id"],
                            "amount": listing["price"],
                            "transaction_type": "venda",
                        })
                        price_str = f"R$ {listing['price']:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                        fee_str = f"R$ {fee:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                        st.success(f"✅ Compra realizada! Valor: {price_str} | Taxa GameSwap (5%): {fee_str}")

                if st.button("💬 Enviar mensagem", key=f"msg_{listing['id']}", use_container_width=True):
                    st.session_state["chat_with"] = listing["user_id"]
                    st.session_state["page"] = "chat"
                    st.rerun()
            elif not user:
                st.info("Faça login para comprar ou entrar em contato.")
