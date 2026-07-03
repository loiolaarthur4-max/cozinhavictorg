import streamlit as st
from datetime import datetime, date
import sqlite3
import time

# Configuração da página do site
st.set_page_config(page_title="Controle de Validade - Cozinha", page_icon="🍳", layout="wide")

# Título principal do Site
st.title("🍳 Sistema de Controle da Cozinha")
st.write("Sistema permanente ativo. Aguardando comandos do cozinheiro **Victor**.")

# --- CONEXÃO COM BANCO DE DADOS (SQLITE) ---
conn = sqlite3.connect("cozinha_permanente.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    local TEXT,
    validade TEXT
)
""")
conn.commit()

def carregar_produtos():
    cursor.execute("SELECT nome, local, validade FROM produtos")
    linhas = cursor.fetchall()
    lista_produtos = []
    for linha in lines:
        lista_produtos.append({
            "nome": linha[0],
            "local": linha[1],
            "validade": datetime.strptime(linha[2], "%Y-%m-%d").date()
        })
    return lista_produtos

if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos()

# Inicializa as variáveis da memória para o sistema de "Desfazer"
if "backup_produtos" not in st.session_state:
    st.session_state.backup_produtos = None
if "tempo_limpeza" not in st.session_state:
    st.session_state.tempo_limpeza = 0

# COLUNA 1: Formulário para o Victor digitar os produtos
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📥 Cadastrar Novo Produto")
    
    nome = st.text_input("Nome do Alimento / Bebida:", placeholder="Ex: Queijo, Leite, Carne...")
    
    local = st.selectbox("Onde este produto será guardado?", [
        "Geladeira Principal (1)", 
        "Freezer Branco", 
        "Freezer Red Bull", 
        "Freezer Grande"
    ])
    
    data_val = st.date_input("Data de Validade do Produto:", min_value=date.today())
    
    if st.button("Adicionar ao Estoque"):
        if nome:
            nome_limpo = nome.strip()
            data_texto = data_val.strftime("%Y-%m-%d")
            
            cursor.execute("INSERT INTO produtos (nome, local, validade) VALUES (?, ?, ?)", (nome_limpo, local, data_texto))
            conn.commit()
            
            st.session_state.produtos = carregar_produtos()
            # Se cadastrar algo novo, cancela a chance de desfazer a limpeza antiga
            st.session_state.backup_produtos = None 
            st.success("🟢 {0} adicionado e salvo permanentemente!".format(nome_limpo))
            st.rerun()
        else:
            st.error("⚠️ Por favor, digite o nome do produto antes de adicionar.")

# COLUNA 2: O painel de Alarmes Automáticos
with col2:
    st.header("🚨 Alarmes e Estoque Atual")
    
    # LÓGICA DO BOTÃO DESFAZER (Aparece se o backup existir e não passou de 10 segundos)
    if st.session_state.backup_produtos is not None:
        tempo_passado = time.time() - st.session_state.tempo_limpeza
        tempo_restante = int(10 - tempo_passado)
        
        if tempo_restante > 0:
            st.warning("⚠️ Todo o estoque foi apagado!")
            # Se clicar no botão, ele recupera os dados salvos no backup de volta para o banco SQLite
            if st.button("🔄 DESFAZER AÇÃO ({0}s)".format(tempo_restante)):
                for item in st.session_state.backup_produtos:
                    cursor.execute(
                        "INSERT INTO produtos (nome, local, validade) VALUES (?, ?, ?)", 
                        (item["nome"], item["local"], item["validade"].strftime("%Y-%m-%d"))
                    )
                conn.commit()
                st.session_state.produtos = carregar_produtos()
                st.session_state.backup_produtos = None # Limpa o backup
                st.success("✅ Estoque recuperado com sucesso!")
                st.rerun()
            
            # Força o site a atualizar a cada 1 segundo para mostrar o cronômetro rodando
            time.sleep(1)
            st.rerun()
        else:
            # Passou dos 10 segundos, o backup é destruído para sempre
            st.session_state.backup_produtos = None
            st.rerun()

    # Se não tiver nada cadastrado (e não estiver na janela de tempo de desfazer)
    if len(st.session_state.produtos) == 0 and st.session_state.backup_produtos is None:
        st.info("O estoque está completamente vazio. Victor pode começar a enviar os produtos!")
    
    elif len(st.session_state.produtos) > 0:
        # Botão de Limpar Estoque
        if st.button("🗑️ Limpar Todo o Estoque"):
            # Salva uma cópia na memória RAM antes de deletar tudo do banco
            st.session_state.backup_produtos = st.session_state.produtos.copy()
            st.session_state.tempo_limpeza = time.time() # Guarda a hora exata do clique
            
            # Deleta do banco de dados definitivo
            cursor.execute("DELETE FROM produtos")
            conn.commit()
            st.session_state.produtos = []
            st.rerun()
            
        st.write("---")
        
        for item in st.session_state.produtos:
            hoje = date.today()
            dias_restantes = (item["validade"] - hoje).days
            
            if dias_restantes < 0:
                status_texto = "❌ VENCIDO HÁ {0} DIAS!".format(abs(dias_restantes))
                cor_alarme = "#ef4444"
                cor_fundo = "#fee2e2"
            elif dias_restantes <= 3:
                status_texto = "🚨 CRÍTICO! Vence em {0} dias.".format(dias_restantes)
                cor_alarme = "#dc2626"
                cor_fundo = "#fee2e2"
            elif dias_restantes <= 7:
                status_texto = "⚠️ ATENÇÃO! Vence em {0} dias.".format(dias_restantes)
                cor_alarme = "#d97706"
                cor_fundo = "#fef3c7"
            else:
                status_texto = "✅ Seguro ({0} dias restantes)".format(dias_restantes)
                cor_alarme = "#16a34a"
                cor_fundo = "#dcfce7"
            
            html_card = (
                '<div style="padding: 12px; border-radius: 8px; border-left: 6px solid ' + cor_alarme + '; '
                'background-color: ' + cor_fundo + '; margin-bottom: 12px; color: #1e293b; font-family: sans-serif;">'
                '<span style="font-size: 12pt; font-weight: bold;">' + str(item['nome']) + '</span> <br>'
                '<span style="font-size: 10pt;">📍 Local: <b>' + str(item['local']) + '</b> | Validade: ' + item['validade'].strftime('%d/%m/%Y') + '</span><br>'
                '<span style="font-size: 10.5pt; font-weight: bold; color: ' + cor_alarme + ';">' + status_texto + '</span>'
                '</div>'
            )
            st.html(html_card)
