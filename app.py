import streamlit as st
import sqlite3
import hashlib
import base64
import os
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GameSwap Brasil",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

PLATFORM_FEE = 0.05
DB_PATH = Path(__file__).parent / "gameswap.db"

PLATFORMS = ["PlayStation 5", "PlayStation 4", "Xbox Series X/S", "Xbox One",
             "Nintendo Switch", "PC", "Game Boy", "Retro", "Outro"]
CATEGORIES = ["Jogo", "Console", "Acessório", "Controle", "Headset", "Outro"]
CONDITIONS  = {"novo": "🟢 Novo", "otimo": "🟡 Ótimo", "bom": "🔵 Bom", "regular": "🟠 Regular"}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Nunito:wght@400;600;700&display=swap');
:root {
    --bg:#0d0f14; --surface:#161a24; --surface2:#1e2436; --border:#2a3050;
    --accent:#00e5ff; --accent2:#7c3aed; --green:#00e676; --text:#e8eaf6;
    --text-dim:#8892b0; --gold:#ffd700;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{
    background-color:var(--bg)!important; color:var(--text)!important;
    font-family:'Nunito',sans-serif!important;
}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important;}
.sidebar-logo{display:flex;align-items:center;gap:10px;padding:10px 0;}
.logo-icon{font-size:2rem;}
.logo-text{font-family:'Rajdhani',sans-serif;font-size:1.6rem;font-weight:700;color:var(--accent);letter-spacing:1px;}
.logo-sub{font-size:.75rem;color:var(--text-dim);margin-top:8px;font-weight:600;}
.user-badge{display:flex;align-items:center;gap:12px;padding:12px;background:var(--surface2);border-radius:12px;border:1px solid var(--border);}
.avatar{width:42px;height:42px;background:linear-gradient(135deg,var(--accent2),var(--accent));border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.1rem;color:white;flex-shrink:0;}
.uname{font-weight:700;font-size:.95rem;color:var(--text);}
.urep{font-size:.8rem;color:var(--gold);}
.auth-prompt{color:var(--text-dim);font-size:.85rem;margin-bottom:10px;text-align:center;}
.page-title{font-family:'Rajdhani',sans-serif!important;font-size:2rem!important;font-weight:700!important;color:var(--accent)!important;letter-spacing:1px!important;margin-bottom:1rem!important;}
.listing-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:20px;transition:border-color .2s,transform .2s;}
.listing-card:hover{border-color:var(--accent);transform:translateY(-2px);}
.card-img{width:100%;height:180px;object-fit:cover;}
.card-img-placeholder{width:100%;height:180px;background:var(--surface2);display:flex;align-items:center;justify-content:center;font-size:3.5rem;}
.card-body{padding:14px;}
.card-type-badge{display:inline-block;background:var(--surface2);border:1px solid var(--border);border-radius:20px;font-size:.75rem;padding:2px 10px;margin-bottom:8px;color:var(--accent);}
.card-title{font-family:'Rajdhani',sans-serif;font-size:1.1rem;font-weight:700;color:var(--text);margin:4px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.card-meta{display:flex;gap:6px;margin:6px 0;flex-wrap:wrap;}
.platform-tag,.condition-tag{background:var(--surface2);border-radius:4px;font-size:.72rem;padding:2px 7px;color:var(--text-dim);}
.card-price{font-family:'Rajdhani',sans-serif;font-size:1.35rem;font-weight:700;color:var(--green);margin:6px 0;}
.card-seller{font-size:.78rem;color:var(--text-dim);}
.empty-state{text-align:center;padding:60px 20px;color:var(--text-dim);}
.empty-icon{font-size:4rem;margin-bottom:16px;}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 16px;text-align:center;margin-bottom:12px;}
.stat-val{font-family:'Rajdhani',sans-serif;font-size:1.5rem;font-weight:700;color:var(--accent);}
.stat-label{font-size:.8rem;color:var(--text-dim);margin-top:4px;}
.transaction-row{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:8px;font-size:.88rem;color:var(--text);}
.fee-badge{background:var(--accent2);color:white;border-radius:4px;padding:2px 6px;font-size:.75rem;margin-left:8px;}
.review-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:10px;}
.review-stars{font-size:1.1rem;margin-bottom:4px;}
.review-author{font-size:.8rem;color:var(--text-dim);margin-bottom:6px;}
.chat-window{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;max-height:420px;overflow-y:auto;margin-bottom:12px;}
.msg-row{display:flex;margin-bottom:12px;}
.msg-row.mine{justify-content:flex-end;}
.msg-bubble{max-width:70%;border-radius:12px;padding:10px 14px;}
.msg-bubble.mine{background:linear-gradient(135deg,var(--accent2),#5b21b6);color:white;border-bottom-right-radius:2px;}
.msg-bubble.theirs{background:var(--surface2);border:1px solid var(--border);color:var(--text);border-bottom-left-radius:2px;}
.msg-sender{font-size:.72rem;font-weight:700;margin-bottom:4px;opacity:.8;}
.msg-text{font-size:.9rem;}
.msg-time{font-size:.68rem;opacity:.6;margin-top:4px;text-align:right;}
.top-user-row{display:flex;align-items:center;gap:12px;padding:8px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:6px;}
.rank{font-family:'Rajdhani',sans-serif;font-weight:700;color:var(--gold);width:24px;}
.admin-stat{border-top:3px solid var(--accent);}
.results-count{color:var(--text-dim);font-size:.85rem;margin-bottom:12px;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div{background:var(--surface2)!important;border-color:var(--border)!important;color:var(--text)!important;}
.stButton>button{background:linear-gradient(135deg,var(--accent2),var(--accent))!important;color:white!important;border:none!important;border-radius:8px!important;font-weight:600!important;}
.stTabs [data-baseweb="tab"]{color:var(--text-dim)!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{color:var(--accent)!important;}
div[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:12px!important;}
hr{border-color:var(--border)!important;}
</style>
""", unsafe_allow_html=True)

# ─── DATABASE ─────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, reputation REAL DEFAULT 5.0,
        total_sales INTEGER DEFAULT 0, total_trades INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0, balance REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        title TEXT NOT NULL, description TEXT, category TEXT NOT NULL,
        platform TEXT NOT NULL, condition TEXT NOT NULL, price REAL,
        listing_type TEXT NOT NULL, status TEXT DEFAULT 'active',
        image_data TEXT, views INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, listing_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL, buyer_id INTEGER NOT NULL,
        amount REAL NOT NULL, platform_fee REAL NOT NULL, seller_amount REAL NOT NULL,
        transaction_type TEXT NOT NULL, status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL, listing_id INTEGER, content TEXT NOT NULL,
        read INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT, reviewer_id INTEGER NOT NULL,
        reviewed_id INTEGER NOT NULL, transaction_id INTEGER NOT NULL,
        rating INTEGER NOT NULL, comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    try:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        conn.execute("INSERT OR IGNORE INTO users (username,email,password_hash,is_admin) VALUES ('admin','admin@gameswap.com.br',?,1)", (admin_hash,))
    except Exception:
        pass
    conn.commit()
    conn.close()

def fmt_price(val):
    return f"R$ {val:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def db_get_listings(filters=None):
    conn = get_conn()
    q = "SELECT l.*,u.username,u.reputation FROM listings l JOIN users u ON l.user_id=u.id WHERE l.status='active'"
    params = []
    if filters:
        if filters.get("platform") and filters["platform"] != "Todos":
            q += " AND l.platform=?"; params.append(filters["platform"])
        if filters.get("listing_type") and filters["listing_type"] != "Todos":
            q += " AND l.listing_type=?"; params.append(filters["listing_type"])
        if filters.get("search"):
            q += " AND (l.title LIKE ? OR l.description LIKE ?)"; params += [f"%{filters['search']}%"]*2
        if filters.get("max_price"):
            q += " AND l.price<=?"; params.append(filters["max_price"])
    rows = conn.execute(q + " ORDER BY l.created_at DESC", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_user_listings(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT l.*,u.username FROM listings l JOIN users u ON l.user_id=u.id WHERE l.user_id=? ORDER BY l.created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_create_listing(data):
    conn = get_conn()
    conn.execute("INSERT INTO listings (user_id,title,description,category,platform,condition,price,listing_type,image_data) VALUES (?,?,?,?,?,?,?,?,?)",
        (data["user_id"],data["title"],data["description"],data["category"],data["platform"],data["condition"],data.get("price"),data["listing_type"],data.get("image_data")))
    conn.commit(); conn.close()

def db_delete_listing(listing_id, user_id):
    conn = get_conn()
    conn.execute("UPDATE listings SET status='removed' WHERE id=? AND user_id=?", (listing_id, user_id))
    conn.commit(); conn.close()

def db_buy(listing_id, seller_id, buyer_id, amount):
    fee = amount * PLATFORM_FEE
    conn = get_conn()
    conn.execute("INSERT INTO transactions (listing_id,seller_id,buyer_id,amount,platform_fee,seller_amount,transaction_type,status) VALUES (?,?,?,?,?,?,'venda','completed')",
        (listing_id, seller_id, buyer_id, amount, fee, amount-fee))
    conn.execute("UPDATE listings SET status='sold' WHERE id=?", (listing_id,))
    conn.execute("UPDATE users SET total_sales=total_sales+1 WHERE id=?", (seller_id,))
    conn.commit(); conn.close()
    return fee

def db_get_messages(u1, u2):
    conn = get_conn()
    rows = conn.execute("SELECT m.*,u.username as sender_name FROM messages m JOIN users u ON m.sender_id=u.id WHERE (m.sender_id=? AND m.receiver_id=?) OR (m.sender_id=? AND m.receiver_id=?) ORDER BY m.created_at ASC",
        (u1,u2,u2,u1)).fetchall()
    conn.execute("UPDATE messages SET read=1 WHERE sender_id=? AND receiver_id=?", (u2,u1))
    conn.commit(); conn.close()
    return [dict(r) for r in rows]

def db_send_message(sender, receiver, content):
    conn = get_conn()
    conn.execute("INSERT INTO messages (sender_id,receiver_id,content) VALUES (?,?,?)", (sender,receiver,content))
    conn.commit(); conn.close()

def db_get_conversations(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT DISTINCT CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END as other_id,
        u.username as other_username, MAX(m.created_at) as last_msg,
        SUM(CASE WHEN m.receiver_id=? AND m.read=0 THEN 1 ELSE 0 END) as unread
        FROM messages m JOIN users u ON u.id=CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END
        WHERE m.sender_id=? OR m.receiver_id=? GROUP BY other_id ORDER BY last_msg DESC
    """, (user_id,)*5).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_transactions(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT t.*,u1.username as seller,u2.username as buyer,l.title FROM transactions t JOIN users u1 ON t.seller_id=u1.id JOIN users u2 ON t.buyer_id=u2.id JOIN listings l ON t.listing_id=l.id WHERE t.seller_id=? OR t.buyer_id=? ORDER BY t.created_at DESC", (user_id,user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_reviews(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT r.*,u.username as reviewer_name FROM reviews r JOIN users u ON r.reviewer_id=u.id WHERE r.reviewed_id=? ORDER BY r.created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_create_review(reviewer_id, reviewed_id, rating, comment):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO reviews (reviewer_id,reviewed_id,transaction_id,rating,comment) VALUES (?,?,0,?,?)", (reviewer_id,reviewed_id,rating,comment))
    avg = conn.execute("SELECT AVG(rating) FROM reviews WHERE reviewed_id=?", (reviewed_id,)).fetchone()[0]
    if avg:
        conn.execute("UPDATE users SET reputation=? WHERE id=?", (round(avg,1), reviewed_id))
    conn.commit(); conn.close()

def db_admin_stats():
    conn = get_conn()
    s = {
        "total_users":    conn.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0],
        "active_listings":conn.execute("SELECT COUNT(*) FROM listings WHERE status='active'").fetchone()[0],
        "total_tx":       conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
        "total_revenue":  conn.execute("SELECT COALESCE(SUM(platform_fee),0) FROM transactions").fetchone()[0],
        "total_volume":   conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions").fetchone()[0],
        "recent_tx": [dict(r) for r in conn.execute("SELECT t.*,u1.username as seller,u2.username as buyer,l.title FROM transactions t JOIN users u1 ON t.seller_id=u1.id JOIN users u2 ON t.buyer_id=u2.id JOIN listings l ON t.listing_id=l.id ORDER BY t.created_at DESC LIMIT 8").fetchall()],
        "top_users": [dict(r) for r in conn.execute("SELECT username,total_sales,reputation FROM users WHERE is_admin=0 ORDER BY total_sales DESC LIMIT 5").fetchall()],
    }
    conn.close()
    return s

def db_get_all_users(exclude_id):
    conn = get_conn()
    rows = conn.execute("SELECT id,username FROM users WHERE id!=? AND is_admin=0", (exclude_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_user(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ─── AUTH ─────────────────────────────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def login_user(username, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, hash_pw(password))).fetchone()
    conn.close()
    return dict(row) if row else None

def register_user(username, email, password):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO users (username,email,password_hash) VALUES (?,?,?)", (username,email,hash_pw(password)))
        conn.commit(); conn.close()
        return True, "Cadastro realizado!"
    except sqlite3.IntegrityError as e:
        conn.close()
        return False, "Usuário ou e-mail já cadastrado."

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for k,v in {"user":None,"page":"marketplace","chat_with":None,"active_chat":None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

init_db()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo"><span class="logo-icon">🎮</span><span class="logo-text">GameSwap</span><span class="logo-sub">Brasil</span></div>', unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.user:
        u = st.session_state.user
        st.markdown(f'<div class="user-badge"><div class="avatar">{u["username"][0].upper()}</div><div><div class="uname">{u["username"]}</div><div class="urep">⭐ {u["reputation"]:.1f} reputação</div></div></div>', unsafe_allow_html=True)
        st.markdown("---")
        nav = {"🛒 Marketplace":"marketplace","📦 Meus Anúncios":"my_listings","💬 Mensagens":"chat","👤 Meu Perfil":"profile"}
        if u.get("is_admin"): nav["⚙️ Painel Admin"] = "admin"
        for label, pg in nav.items():
            if st.button(label, key=f"nav_{pg}", use_container_width=True):
                st.session_state.page = pg; st.rerun()
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None; st.session_state.page = "marketplace"; st.rerun()
    else:
        st.markdown('<div class="auth-prompt">Faça login para acessar a plataforma</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            if st.button("Login", use_container_width=True): st.session_state.page="login"; st.rerun()
        with c2:
            if st.button("Cadastrar", use_container_width=True): st.session_state.page="register"; st.rerun()

# ─── PAGES ────────────────────────────────────────────────────────────────────
page = st.session_state.page

# ── LOGIN ──
if page == "login":
    st.markdown("<h1 class='page-title'>🔐 Login</h1>", unsafe_allow_html=True)
    col,_ = st.columns([1.2,1])
    with col:
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar 🎮", use_container_width=True):
                user = login_user(username, password)
                if user:
                    st.session_state.user = user; st.session_state.page = "marketplace"; st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        if st.button("Criar conta grátis →"): st.session_state.page="register"; st.rerun()

# ── REGISTER ──
elif page == "register":
    st.markdown("<h1 class='page-title'>✨ Criar Conta</h1>", unsafe_allow_html=True)
    col,_ = st.columns([1.2,1])
    with col:
        with st.form("reg_form"):
            username = st.text_input("Nome de usuário")
            email    = st.text_input("E-mail")
            pw       = st.text_input("Senha", type="password")
            pw2      = st.text_input("Confirmar senha", type="password")
            if st.form_submit_button("Criar conta 🚀", use_container_width=True):
                if not all([username,email,pw,pw2]): st.error("Preencha todos os campos.")
                elif len(pw)<6: st.error("Mínimo 6 caracteres.")
                elif pw!=pw2: st.error("Senhas não coincidem.")
                else:
                    ok,msg = register_user(username, email, pw)
                    if ok: st.success(msg); st.session_state.page="login"; st.rerun()
                    else: st.error(msg)
        if st.button("Já tenho conta → Login"): st.session_state.page="login"; st.rerun()

# ── MARKETPLACE ──
elif page == "marketplace":
    st.markdown("<h1 class='page-title'>🛒 Marketplace</h1>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns([2,1.5,1.5,1])
    with c1: search = st.text_input("🔍 Buscar", placeholder="Ex: God of War, PS5...")
    with c2: platform = st.selectbox("Plataforma", ["Todos"]+PLATFORMS)
    with c3: ltype = st.selectbox("Tipo", ["Todos","Venda","Troca"])
    with c4: max_price = st.number_input("Preço máx R$", min_value=0, value=0, step=50)

    filters = {"search":search,"platform":platform,"listing_type":{"Todos":"Todos","Venda":"venda","Troca":"troca"}[ltype],"max_price":max_price or None}
    listings = db_get_listings(filters)

    if not listings:
        st.markdown('<div class="empty-state"><div class="empty-icon">🎮</div><h3>Nenhum anúncio encontrado</h3><p>Seja o primeiro a anunciar!</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="results-count">{len(listings)} anúncio(s)</p>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, l in enumerate(listings):
            ltype_lbl = {"venda":"💰 Venda","troca":"🔄 Troca","venda_troca":"💰🔄 Venda/Troca"}.get(l["listing_type"],"")
            price_str = fmt_price(l["price"]) if l.get("price") else "A combinar"
            img_html = f'<img src="data:image/jpeg;base64,{l["image_data"]}" class="card-img"/>' if l.get("image_data") else '<div class="card-img-placeholder">🎮</div>'
            with cols[i%3]:
                st.markdown(f"""
                <div class='listing-card'>
                  {img_html}
                  <div class='card-body'>
                    <div class='card-type-badge'>{ltype_lbl}</div>
                    <h4 class='card-title'>{l['title']}</h4>
                    <div class='card-meta'>
                      <span class='platform-tag'>{l['platform']}</span>
                      <span class='condition-tag'>{CONDITIONS.get(l['condition'],l['condition'])}</span>
                    </div>
                    <div class='card-price'>{price_str}</div>
                    <div class='card-seller'>👤 {l['username']} &nbsp;⭐ {l['reputation']:.1f}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                if st.button("Ver detalhes", key=f"d_{l['id']}", use_container_width=True):
                    conn = get_conn(); conn.execute("UPDATE listings SET views=views+1 WHERE id=?", (l["id"],)); conn.commit(); conn.close()
                    st.session_state[f"show_{l['id']}"] = not st.session_state.get(f"show_{l['id']}", False)
                    st.rerun()

                if st.session_state.get(f"show_{l['id']}"):
                    with st.expander("📋 Detalhes", expanded=True):
                        if l.get("image_data"):
                            st.image(base64.b64decode(l["image_data"]), use_container_width=True)
                        st.markdown(f"**{l['title']}**")
                        st.markdown(f"Plataforma: {l['platform']} | Condição: {CONDITIONS.get(l['condition'],l['condition'])}")
                        if l.get("description"): st.markdown(f"_{l['description']}_")
                        if l.get("price"): st.markdown(f"**Preço:** {fmt_price(l['price'])}")
                        st.markdown(f"Vendedor: {l['username']} ⭐{l['reputation']:.1f} | 👁 {l.get('views',0)} views")

                        user = st.session_state.user
                        if user and user["id"] != l["user_id"]:
                            if l["listing_type"] in ("venda","venda_troca") and l.get("price"):
                                if st.button("💳 Comprar", key=f"buy_{l['id']}"):
                                    fee = db_buy(l["id"], l["user_id"], user["id"], l["price"])
                                    st.success(f"✅ Compra realizada! Taxa GameSwap (5%): {fmt_price(fee)}")
                                    st.rerun()
                            if st.button("💬 Enviar mensagem", key=f"msg_{l['id']}"):
                                st.session_state.chat_with = l["user_id"]
                                st.session_state.page = "chat"; st.rerun()
                        elif not user:
                            st.info("Faça login para comprar ou entrar em contato.")

# ── MEUS ANÚNCIOS ──
elif page == "my_listings":
    if not st.session_state.user:
        st.warning("Faça login para ver seus anúncios.")
    else:
        user = st.session_state.user
        st.markdown("<h1 class='page-title'>📦 Meus Anúncios</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 Meus Anúncios", "➕ Novo Anúncio"])

        with tab1:
            listings = db_get_user_listings(user["id"])
            if not listings:
                st.markdown('<div class="empty-state"><div class="empty-icon">📦</div><h3>Nenhum anúncio ainda</h3></div>', unsafe_allow_html=True)
            for l in listings:
                c1,c2,c3 = st.columns([3,2,1])
                status_lbl = {"active":"🟢 Ativo","sold":"✅ Vendido","removed":"🔴 Removido"}.get(l["status"],l["status"])
                with c1: st.markdown(f"**{l['title']}** — {l['platform']} · {CONDITIONS.get(l['condition'],l['condition'])} · {status_lbl}")
                with c2:
                    price = fmt_price(l["price"]) if l.get("price") else "—"
                    ltype_lbl = {"venda":"💰","troca":"🔄","venda_troca":"💰🔄"}.get(l["listing_type"],"")
                    st.markdown(f"{price} {ltype_lbl} · 👁 {l.get('views',0)}")
                with c3:
                    if l["status"] == "active":
                        if st.button("🗑️", key=f"del_{l['id']}"):
                            db_delete_listing(l["id"], user["id"]); st.rerun()
                st.divider()

        with tab2:
            with st.form("new_listing"):
                c1,c2 = st.columns(2)
                with c1:
                    title     = st.text_input("Título *")
                    platform  = st.selectbox("Plataforma *", PLATFORMS)
                    category  = st.selectbox("Categoria *", CATEGORIES)
                    condition = st.selectbox("Condição *", list(CONDITIONS.keys()), format_func=lambda x: CONDITIONS[x])
                with c2:
                    ltype     = st.selectbox("Tipo *", ["venda","troca","venda_troca"], format_func=lambda x: {"venda":"💰 Venda","troca":"🔄 Troca","venda_troca":"💰🔄 Venda e Troca"}[x])
                    price     = st.number_input("Preço (R$)", min_value=0.0, step=10.0)
                    img_file  = st.file_uploader("Foto", type=["jpg","jpeg","png"])
                description = st.text_area("Descrição")
                if st.form_submit_button("📢 Publicar", use_container_width=True):
                    if not title: st.error("Título obrigatório.")
                    else:
                        img_data = base64.b64encode(img_file.read()).decode() if img_file else None
                        db_create_listing({"user_id":user["id"],"title":title,"description":description,"category":category,"platform":platform,"condition":condition,"price":price or None,"listing_type":ltype,"image_data":img_data})
                        st.success("✅ Anúncio publicado!"); st.rerun()

# ── CHAT ──
elif page == "chat":
    if not st.session_state.user:
        st.warning("Faça login para acessar o chat.")
    else:
        user = st.session_state.user
        st.markdown("<h1 class='page-title'>💬 Mensagens</h1>", unsafe_allow_html=True)

        # Handle redirect from marketplace
        if st.session_state.chat_with:
            st.session_state.active_chat = st.session_state.chat_with
            st.session_state.chat_with = None

        convs = db_get_conversations(user["id"])
        col1,col2 = st.columns([1,2.5])

        with col1:
            st.markdown("#### Conversas")
            if not convs: st.info("Nenhuma conversa.")
            for c in convs:
                badge = f" 🔴{c['unread']}" if c.get("unread",0)>0 else ""
                active = "▶ " if st.session_state.active_chat == c["other_id"] else ""
                if st.button(f"{active}{c['other_username']}{badge}", key=f"cv_{c['other_id']}", use_container_width=True):
                    st.session_state.active_chat = c["other_id"]; st.rerun()

            # New conversation
            st.markdown("---")
            all_users = db_get_all_users(user["id"])
            if all_users:
                target = st.selectbox("Nova conversa", all_users, format_func=lambda u: u["username"])
                if st.button("Iniciar chat", use_container_width=True):
                    st.session_state.active_chat = target["id"]; st.rerun()

        with col2:
            active_id = st.session_state.active_chat
            if not active_id:
                st.markdown('<div class="empty-state"><div class="empty-icon">💬</div><h3>Selecione uma conversa</h3></div>', unsafe_allow_html=True)
            else:
                other = db_get_user(active_id)
                if not other: st.error("Usuário não encontrado.")
                else:
                    st.markdown(f"#### Chat com **{other['username']}** ⭐{other['reputation']:.1f}")
                    msgs = db_get_messages(user["id"], active_id)
                    chat_html = "<div class='chat-window'>"
                    if not msgs: chat_html += "<p style='color:var(--text-dim);text-align:center'>Nenhuma mensagem ainda. Diga olá! 👋</p>"
                    for m in msgs:
                        mine = m["sender_id"] == user["id"]
                        side = "mine" if mine else "theirs"
                        name = "Você" if mine else m["sender_name"]
                        chat_html += f"<div class='msg-row {side}'><div class='msg-bubble {side}'><div class='msg-sender'>{name}</div><div class='msg-text'>{m['content']}</div><div class='msg-time'>{str(m['created_at'])[:16]}</div></div></div>"
                    chat_html += "</div>"
                    st.markdown(chat_html, unsafe_allow_html=True)

                    with st.form("send_msg", clear_on_submit=True):
                        ci,cb = st.columns([4,1])
                        with ci: content = st.text_input("", placeholder="Digite...", label_visibility="collapsed")
                        with cb: sent = st.form_submit_button("Enviar ➤", use_container_width=True)
                        if sent and content.strip():
                            db_send_message(user["id"], active_id, content.strip()); st.rerun()

# ── PERFIL ──
elif page == "profile":
    if not st.session_state.user:
        st.warning("Faça login para ver seu perfil.")
    else:
        user = db_get_user(st.session_state.user["id"])
        st.session_state.user = user
        st.markdown("<h1 class='page-title'>👤 Meu Perfil</h1>", unsafe_allow_html=True)

        txs = db_get_transactions(user["id"])
        revs = db_get_reviews(user["id"])
        volume = sum(t["amount"] for t in txs if t["seller_id"]==user["id"])

        c1,c2,c3,c4 = st.columns(4)
        for col, val, lbl in [(c1,f"⭐ {user['reputation']:.1f}","Reputação"),(c2,f"📦 {user['total_sales']}","Vendas"),(c3,f"💰 {fmt_price(volume)}","Volume"),(c4,f"💬 {len(revs)}","Avaliações")]:
            with col: st.markdown(f'<div class="stat-card"><div class="stat-val">{val}</div><div class="stat-label">{lbl}</div></div>', unsafe_allow_html=True)

        st.divider()
        t1,t2,t3 = st.tabs(["📜 Transações","⭐ Avaliações","✍️ Avaliar"])

        with t1:
            if not txs: st.info("Nenhuma transação.")
            for t in txs:
                role = "Vendedor" if t["seller_id"]==user["id"] else "Comprador"
                st.markdown(f'<div class="transaction-row"><strong>{t["title"]}</strong> · {role} · {fmt_price(t["amount"])}<span class="fee-badge">Taxa: {fmt_price(t["platform_fee"])}</span></div>', unsafe_allow_html=True)

        with t2:
            if not revs: st.info("Nenhuma avaliação recebida.")
            for r in revs:
                stars = "⭐"*r["rating"]+"☆"*(5-r["rating"])
                st.markdown(f'<div class="review-card"><div class="review-stars">{stars}</div><div class="review-author">por <strong>{r["reviewer_name"]}</strong> · {str(r["created_at"])[:10]}</div><div class="review-comment">{r.get("comment") or "—"}</div></div>', unsafe_allow_html=True)

        with t3:
            all_users = db_get_all_users(user["id"])
            if all_users:
                with st.form("review_form"):
                    target = st.selectbox("Usuário", all_users, format_func=lambda u: u["username"])
                    rating = st.slider("Nota", 1, 5, 5)
                    comment = st.text_area("Comentário")
                    if st.form_submit_button("Enviar avaliação ⭐"):
                        db_create_review(user["id"], target["id"], rating, comment)
                        st.success("Avaliação enviada!"); st.rerun()

# ── ADMIN ──
elif page == "admin":
    if not (st.session_state.user and st.session_state.user.get("is_admin")):
        st.error("Acesso negado.")
    else:
        st.markdown("<h1 class='page-title'>⚙️ Painel Admin</h1>", unsafe_allow_html=True)
        s = db_admin_stats()
        c1,c2,c3,c4,c5 = st.columns(5)
        for col,(icon,val,lbl) in zip([c1,c2,c3,c4,c5],[
            ("👥",s["total_users"],"Usuários"),
            ("📦",s["active_listings"],"Anúncios Ativos"),
            ("🔄",s["total_tx"],"Transações"),
            ("💰",fmt_price(s["total_volume"]),"Volume Total"),
            ("🏦",fmt_price(s["total_revenue"]),"Receita (5%)"),
        ]):
            with col: st.markdown(f'<div class="stat-card admin-stat"><div class="stat-val">{icon} {val}</div><div class="stat-label">{lbl}</div></div>', unsafe_allow_html=True)

        st.divider()
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("#### 🏆 Top Vendedores")
            for i,u in enumerate(s["top_users"],1):
                st.markdown(f'<div class="top-user-row"><span class="rank">#{i}</span><span>{u["username"]}</span><span style="color:var(--text-dim);margin-left:auto">{u["total_sales"]} vendas</span><span style="color:var(--gold);margin-left:12px">⭐{u["reputation"]:.1f}</span></div>', unsafe_allow_html=True)
        with col2:
            st.markdown("#### 📊 Últimas Transações")
            for t in s["recent_tx"][:5]:
                st.markdown(f'<div class="transaction-row"><strong>{t["title"][:22]}…</strong><br>{t["seller"]} → {t["buyer"]} · {fmt_price(t["amount"])}<span class="fee-badge">+{fmt_price(t["platform_fee"])}</span></div>', unsafe_allow_html=True)
