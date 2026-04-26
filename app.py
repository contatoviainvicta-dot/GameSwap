import streamlit as st
from database import init_db
from auth import show_login, show_register, logout
from marketplace import show_marketplace
from my_listings import show_my_listings
from chat import show_chat
from admin import show_admin_panel
from profile import show_profile

st.set_page_config(
    page_title="GameSwap Brasil",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_db()

# Session state defaults
for key, val in {
    "user": None,
    "page": "marketplace",
    "chat_with": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


def sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <span class="logo-icon">🎮</span>
            <span class="logo-text">GameSwap</span>
            <span class="logo-sub">Brasil</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if st.session_state.user:
            user = st.session_state.user
            st.markdown(f"""
            <div class="user-badge">
                <div class="avatar">{user['username'][0].upper()}</div>
                <div class="user-info">
                    <div class="uname">{user['username']}</div>
                    <div class="urep">⭐ {user['reputation']:.1f} reputação</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")

            pages = {
                "🛒 Marketplace": "marketplace",
                "📦 Meus Anúncios": "my_listings",
                "💬 Mensagens": "chat",
                "👤 Meu Perfil": "profile",
            }
            if user.get("is_admin"):
                pages["⚙️ Painel Admin"] = "admin"

            for label, page in pages.items():
                active = "nav-active" if st.session_state.page == page else ""
                if st.button(label, key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Sair", use_container_width=True):
                logout()
                st.rerun()
        else:
            st.markdown("<div class='auth-prompt'>Faça login para acessar a plataforma</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Login", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun()
            with col2:
                if st.button("Cadastrar", use_container_width=True):
                    st.session_state.page = "register"
                    st.rerun()


def main():
    sidebar()

    page = st.session_state.page

    if page == "login":
        show_login()
    elif page == "register":
        show_register()
    elif page == "marketplace":
        show_marketplace()
    elif page == "my_listings":
        if not st.session_state.user:
            st.warning("Faça login para ver seus anúncios.")
        else:
            show_my_listings()
    elif page == "chat":
        if not st.session_state.user:
            st.warning("Faça login para acessar o chat.")
        else:
            show_chat()
    elif page == "profile":
        if not st.session_state.user:
            st.warning("Faça login para ver seu perfil.")
        else:
            show_profile()
    elif page == "admin":
        if st.session_state.user and st.session_state.user.get("is_admin"):
            show_admin_panel()
        else:
            st.error("Acesso negado.")


if __name__ == "__main__":
    main()
