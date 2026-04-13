from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_muito_forte_aqui_123456'  # Mude isso em produção!

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
        
        # Usuários padrão (senha: 123456)
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('admin', generate_password_hash('123456'), 'adm'))
        
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('vendedor', generate_password_hash('123456'), 'user'))
        
        conn.commit()
        conn.close()
        print("Banco de dados criado com usuários padrão!")

# ====================== ROTAS ======================

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'adm':
            return "Bem-vindo, Administrador! <a href='/logout'>Sair</a>"
        else:
            return "Bem-vindo, Usuário! <a href='/logout'>Sair</a>"
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
            
            if user[3] == 'adm':
                return redirect(url_for('index'))  # ou para dashboard admin
            else:
                return redirect(url_for('index'))  # ou para dashboard user
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('index'))


# ====================== EXECUÇÃO ======================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)