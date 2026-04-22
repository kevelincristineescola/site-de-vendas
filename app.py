from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_muito_forte_aqui_123456_mude_em_producao!'  

# ====================== CONFIGURAÇÃO DO BANCO ======================

def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('adm', 'user'))
            )
        ''')
        
        # Usuários padrão (senha: 123456)
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('admin', generate_password_hash('123456'), 'adm'))
        
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('vendedor', generate_password_hash('123456'), 'user'))
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados criado com usuários padrão!")

# ====================== ROTAS ======================

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