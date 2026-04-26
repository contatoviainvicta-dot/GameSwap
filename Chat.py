import streamlit as st
from database import get_conversations, get_messages, send_message, get_conn

def show_chat():
    user = st.session_state.user
    st.markdown("<h1 class='page-title'>💬 Mensagens</h1>", unsafe_allow_html=True)

    conversations = get_conversations(user["id"])

    col1, col2 = st.columns([1, 2.5])

    with col1:
        st.markdown("#### Conversas")
        if not conversations:
            st.info("Nenhuma conversa ainda.")
        
        # Check if redirected from marketplace
        if st.session_state.get("chat_with"):
            target_id = st.session_state["chat_with"]
            conn = get_conn()
            target_user = conn.execute("SELECT * FROM users WHERE id=?", (target_id,)).fetchone()
            conn.close()
            if target_user:
                target_user = dict(target_user)
                # Add to conversations if not there
                if not any(c["other_id"] == target_id for c in conversations):
                    conversations.insert(0, {"other_id": target_id, "other_username": target_user["username"], "unread": 0})
                if "active_chat" not in st.session_state or st.session_state.active_chat != target_id:
                    st.session_state.active_chat = target_id
                    st.session_state.chat_with = None

        for conv in conversations:
            unread_badge = f" 🔴{conv['unread']}" if conv.get("unread", 0) > 0 else ""
            active = st.session_state.get("active_chat") == conv["other_id"]
            btn_label = f"{'▶ ' if active else ''}{conv['other_username']}{unread_badge}"
            if st.button(btn_label, key=f"conv_{conv['other_id']}", use_container_width=True):
                st.session_state.active_chat = conv["other_id"]
                st.rerun()

    with col2:
        active_id = st.session_state.get("active_chat")
        if not active_id:
            st.markdown("""
            <div class='empty-state'>
                <div class='empty-icon'>💬</div>
                <h3>Selecione uma conversa</h3>
                <p>Ou inicie uma conversa pelo marketplace</p>
            </div>
            """, unsafe_allow_html=True)
            return

        conn = get_conn()
        other_user = conn.execute("SELECT * FROM users WHERE id=?", (active_id,)).fetchone()
        conn.close()
        if not other_user:
            st.error("Usuário não encontrado.")
            return
        other_user = dict(other_user)

        st.markdown(f"#### Conversa com **{other_user['username']}** ⭐ {other_user['reputation']:.1f}")

        messages = get_messages(user["id"], active_id)

        chat_html = "<div class='chat-window'>"
        for msg in messages:
            is_mine = msg["sender_id"] == user["id"]
            side = "mine" if is_mine else "theirs"
            name = "Você" if is_mine else msg["sender_name"]
            chat_html += f"""
            <div class='msg-row {side}'>
                <div class='msg-bubble {side}'>
                    <div class='msg-sender'>{name}</div>
                    <div class='msg-text'>{msg['content']}</div>
                    <div class='msg-time'>{str(msg['created_at'])[:16]}</div>
                </div>
            </div>
            """
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        with st.form("send_msg_form", clear_on_submit=True):
            col_input, col_btn = st.columns([4, 1])
            with col_input:
                content = st.text_input("", placeholder="Digite sua mensagem...", label_visibility="collapsed")
            with col_btn:
                sent = st.form_submit_button("Enviar ➤", use_container_width=True)
            if sent and content.strip():
                send_message(user["id"], active_id, content.strip())
                st.rerun()
