from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_muito_forte_aqui_123456_mude_em_producao!'  

# ====================== CONFIGURAÇÃO DO BANCO ======================

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    # Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            telefone TEXT
        )
    ''')

    # Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            preco REAL
        )
    ''')

    # Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            total REAL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Usuários padrão
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', ?, 'Adiministrador')",
                   (generate_password_hash('123456'),))

    cursor.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (2, 'vendedor', ?, 'Vendedor')",
                   (generate_password_hash('123456'),))

    # Produtos padrão
    cursor.execute("INSERT OR IGNORE INTO produtos (id, nome, preco) VALUES (1, 'Camiseta', 49.90)")
    cursor.execute("INSERT OR IGNORE INTO produtos (id, nome, preco) VALUES (2, 'Tênis', 199.90)")
    cursor.execute("INSERT OR IGNORE INTO produtos (id, nome, preco) VALUES (3, 'Boné', 29.90)")

    conn.commit()
    conn.close()
# ====================== ROTAS ======================
@app.route('/produtos')
def produtos():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    conn.close()
    return render_template('produtos.html', produtos=produtos)

@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']

        cursor.execute("INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
                       (nome, email, telefone))
        conn.commit()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    conn.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        cliente_id = request.form['cliente']
        produto_id = request.form['produto']
        quantidade = int(request.form['quantidade'])

        cursor.execute("SELECT preco FROM produtos WHERE id=?", (produto_id,))
        preco = cursor.fetchone()[0]

        total = preco * quantidade

        cursor.execute('''
            INSERT INTO vendas (cliente_id, produto_id, quantidade, total)
            VALUES (?, ?, ?, ?)
        ''', (cliente_id, produto_id, quantidade, total))

        conn.commit()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    cursor.execute("SELECT * FROM vendas")
    vendas = cursor.fetchall()

    conn.close()

    return render_template('vendas.html', clientes=clientes, produtos=produtos, vendas=vendas)

@app.route('/relatorios')
def relatorios():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(total) FROM vendas")
    total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM vendas")
    qtd = cursor.fetchone()[0]

    conn.close()

    return render_template('relatorios.html', total=total, qtd=qtd)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Preencha todos os campos!', 'error')
            return render_template('index.html')
        
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
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
            return render_template('index.html')
    
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Faça login para acessar o sistema.', 'error')
        return redirect(url_for('index'))
    
    role_name = 'Administrador' if session.get('role') == 'adm' else 'Vendedor'
    return render_template('dashboard.html', username=session['username'], role=role_name)


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('index'))


# ====================== EXECUÇÃO ======================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
