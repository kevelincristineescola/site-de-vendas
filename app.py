from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)

# ====================== CONFIGURAÇÃO DE SEGURANÇA (IMPORTANTE PARA SERVIDOR) ======================
# Sempre use variável de ambiente no servidor!
app.secret_key = os.environ.get('SECRET_KEY') 

# Se não encontrar SECRET_KEY no ambiente, força um erro (melhor que usar chave fraca)
if not app.secret_key:
    raise RuntimeError("ERRO: Defina a variável de ambiente SECRET_KEY antes de rodar o servidor!")

# ====================== CONFIGURAÇÃO DO BANCO ======================
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('adm', 'user'))
            )
        ''')

        # Tabela de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        ''')

        # Tabela de vendas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sale_date TEXT,
                total REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Tabela de itens da venda
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # Usuários padrão (senha: 123456)
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('admin', generate_password_hash('123456'), 'adm'))
       
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('vendedor', generate_password_hash('123456'), 'user'))

        # Produtos de exemplo
        produtos_exemplo = [
            ('Notebook Dell', 3499.90, 10),
            ('Mouse Logitech', 89.90, 50),
            ('Teclado Mecânico', 299.90, 30),
            ('Monitor 24"', 899.90, 15)
        ]
        cursor.executemany("INSERT OR IGNORE INTO products (name, price, stock) VALUES (?, ?, ?)", produtos_exemplo)

        conn.commit()
        conn.close()
        print("✅ Banco de dados criado com usuários e produtos padrão!")


# ====================== DECORADOR DE LOGIN ======================
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap


# ====================== ROTAS ======================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('vendas'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            flash(f'Login realizado com sucesso! Bem-vindo, {user[1]}', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos!', 'error')

    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('index'))


# ====================== SISTEMA DE VENDAS ======================

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') != 'adm':
        flash('Acesso negado! Apenas administradores.', 'error')
        return redirect(url_for('vendas'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products")
    products = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', products=products)


@app.route('/vendas')
@login_required
def vendas():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products WHERE stock > 0")
    products = cursor.fetchall()
    conn.close()
    
    return render_template('vendas.html', products=products)


@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    if session.get('role') != 'adm':
        flash('Acesso negado!', 'error')
        return redirect(url_for('vendas'))

    name = request.form['name'].strip()
    price = float(request.form['price'])
    stock = int(request.form['stock'])

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
    conn.commit()
    conn.close()

    flash('Produto cadastrado com sucesso!', 'success')
    return redirect(url_for('dashboard'))


# Carrinho usando session
@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = int(request.form['product_id'])
    quantity = int(request.form.get('quantity', 1))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product or product[3] < quantity:
        flash('Estoque insuficiente ou produto não encontrado!', 'error')
        return redirect(url_for('vendas'))

    if 'cart' not in session:
        session['cart'] = []

    # Verifica se já existe no carrinho
    for item in session['cart']:
        if item['id'] == product_id:
            item['quantity'] += quantity
            flash(f'{product[1]} atualizado no carrinho!', 'success')
            return redirect(url_for('vendas'))

    session['cart'].append({
        'id': product[0],
        'name': product[1],
        'price': float(product[2]),
        'quantity': quantity
    })

    flash(f'{product[1]} adicionado ao carrinho!', 'success')
    return redirect(url_for('vendas'))


@app.route('/cart')
@login_required
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart=cart_items, total=total)


@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
    flash('Item removido do carrinho.', 'info')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = session.get('cart', [])
    if not cart:
        flash('Seu carrinho está vazio!', 'error')
        return redirect(url_for('vendas'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    total = sum(item['price'] * item['quantity'] for item in cart)

    # Registra a venda
    cursor.execute("""
        INSERT INTO sales (user_id, sale_date, total) 
        VALUES (?, ?, ?)
    """, (session['user_id'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total))
    
    sale_id = cursor.lastrowid

    # Registra itens e atualiza estoque
    for item in cart:
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, quantity, price) 
            VALUES (?, ?, ?, ?)
        """, (sale_id, item['id'], item['quantity'], item['price']))
        
        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", 
                       (item['quantity'], item['id']))

    conn.commit()
    conn.close()

    session.pop('cart', None)   # Limpa o carrinho após a venda
    flash(f'Venda finalizada com sucesso! Total: R$ {total:.2f}', 'success')
    return redirect(url_for('vendas'))


# ====================== EXECUÇÃO PARA SERVIDOR ======================
if __name__ == '__main__':
    init_db()
    
    print("🚀 Iniciando aplicação Flask no servidor...")
    print("Acesse pela URL fornecida pelo seu servidor (ex: http://seu-ip:5000)")
    
    # Configuração segura para servidor
    app.run(
        host='0.0.0.0',      # Permite acesso de fora (importante no servidor)
        port=int(os.environ.get('PORT', 5000)),  # Usa PORT se disponível (muitas plataformas usam)
        debug=False           # Nunca deixe debug=True em servidor!
    )
