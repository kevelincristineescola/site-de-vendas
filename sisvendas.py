import sqlite3
from datetime import datetime

# Conexão com o banco de dados
conn = sqlite3.connect('sisvendas.db')
cursor = conn.cursor()

# Criar tabelas
def criar_tabelas():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            endereco TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            cliente_id INTEGER,
            total REAL NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL,
            FOREIGN KEY (venda_id) REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    conn.commit()
    print("✅ Banco de dados e tabelas criados com sucesso!")

# ==================== FUNÇÕES DE CLIENTES ====================
def cadastrar_cliente():
    nome = input("Nome do cliente: ")
    telefone = input("Telefone: ")
    endereco = input("Endereço: ")
    cursor.execute("INSERT INTO clientes (nome, telefone, endereco) VALUES (?, ?, ?)", 
                   (nome, telefone, endereco))
    conn.commit()
    print("✅ Cliente cadastrado!")

def listar_clientes():
    cursor.execute("SELECT * FROM clientes")
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | Nome: {row[1]} | Tel: {row[2]} | End: {row[3]}")

# ==================== FUNÇÕES DE PRODUTOS ====================
def cadastrar_produto():
    nome = input("Nome do produto: ")
    preco = float(input("Preço: R$ "))
    estoque = int(input("Estoque inicial: "))
    cursor.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)", 
                   (nome, preco, estoque))
    conn.commit()
    print("✅ Produto cadastrado!")

def listar_produtos():
    cursor.execute("SELECT * FROM produtos")
    for row in cursor.fetchall():
        print(f"ID: {row[0]} | {row[1]} | R$ {row[2]:.2f} | Estoque: {row[3]}")

def atualizar_estoque(produto_id, quantidade_vendida):
    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", 
                   (quantidade_vendida, produto_id))
    conn.commit()

# ==================== FUNÇÕES DE VENDAS ====================
def registrar_venda():
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    listar_clientes()
    cliente_id = int(input("\nID do cliente (0 para cliente não cadastrado): ") or 0)
    
    itens = []
    total = 0.0
    
    while True:
        listar_produtos()
        prod_id = int(input("\nID do produto (0 para finalizar): "))
        if prod_id == 0:
            break
            
        cursor.execute("SELECT nome, preco, estoque FROM produtos WHERE id = ?", (prod_id,))
        produto = cursor.fetchone()
        if not produto:
            print("Produto não encontrado!")
            continue
            
        if produto[2] <= 0:
            print("Estoque insuficiente!")
            continue
            
        qtd = int(input(f"Quantidade (máx {produto[2]}): "))
        if qtd > produto[2]:
            print("Quantidade maior que o estoque!")
            continue
            
        subtotal = qtd * produto[1]
        itens.append((prod_id, qtd, produto[1], subtotal))
        total += subtotal
        atualizar_estoque(prod_id, qtd)
        
        print(f"Adicionado: {qtd}x {produto[0]} = R$ {subtotal:.2f}")
    
    if not itens:
        print("Venda cancelada (nenhum item).")
        return
    
    # Registrar venda
    cursor.execute("INSERT INTO vendas (data, cliente_id, total) VALUES (?, ?, ?)", 
                   (data, cliente_id if cliente_id > 0 else None, total))
    venda_id = cursor.lastrowid
    
    # Registrar itens da venda
    for item in itens:
        cursor.execute("INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)", 
                       (venda_id, item[0], item[1], item[2]))
    
    conn.commit()
    print(f"\n✅ Venda registrada com sucesso! Total: R$ {total:.2f} | ID da venda: {venda_id}")

def listar_vendas():
    cursor.execute("""
        SELECT v.id, v.data, c.nome, v.total 
        FROM vendas v 
        LEFT JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.id DESC
    """)
    for row in cursor.fetchall():
        cliente = row[2] if row[2] else "Cliente avulso"
        print(f"ID: {row[0]} | Data: {row[1]} | Cliente: {cliente} | Total: R$ {row[3]:.2f}")

# Menu principal
def menu():
    criar_tabelas()
    while True:
        print("\n" + "="*40)
        print("          SISVENDAS - MENU")
        print("="*40)
        print("1. Cadastrar Cliente")
        print("2. Listar Clientes")
        print("3. Cadastrar Produto")
        print("4. Listar Produtos")
        print("5. Registrar Venda")
        print("6. Listar Vendas")
        print("0. Sair")
        print("="*40)
        
        op = input("Escolha uma opção: ")
        
        if op == "1":
            cadastrar_cliente()
        elif op == "2":
            listar_clientes()
        elif op == "3":
            cadastrar_produto()
        elif op == "4":
            listar_produtos()
        elif op == "5":
            registrar_venda()
        elif op == "6":
            listar_vendas()
        elif op == "0":
            print("Saindo do sistema... Até logo!")
            conn.close()
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    menu()