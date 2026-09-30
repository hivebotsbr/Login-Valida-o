import streamlit as st
import ast
import os
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Lab de Robótica - Cadastro & Submissão", page_icon="🤖", layout="centered")

# Credenciais de Acesso do Administrador
ADM_USER = "hivebr"
ADM_PASS = "Olivia123"

# Inicializa o estado de autenticação
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# Arquivos e pastas locais
CSV_FILE = "submissoes.csv"
UPLOADS_DIR = "codigos_recebidos"

# Garante que a pasta de uploads existe
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Garante que o arquivo CSV existe com os cabeçalhos corretos
if not os.path.exists(CSV_FILE):
    df_init = pd.DataFrame(columns=[
        "Data_Hora", "Nome", "Email", "Pais", "Estado", "Universidade", "Arquivo", "Status"
    ])
    df_init.to_csv(CSV_FILE, index=False, encoding="utf-8")

# Módulos proibidos por segurança
FORBIDDEN_MODULES = {'os', 'subprocess', 'sys', 'socket', 'requests', 'urllib', 'shutil', 'ctypes'}

def validate_code(code_string):
    """Valida a sintaxe e procura por importações perigosas."""
    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return False, f"Erro de sintaxe no arquivo Python: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in FORBIDDEN_MODULES:
                    return False, f"Módulo proibido detectado: '{alias.name}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in FORBIDDEN_MODULES:
                return False, f"Módulo proibido detectado: 'from {node.module}'"

    return True, "Código aprovado nas checagens de segurança!"

# --- INTERFACE PRINCIPAL DO ALUNO ---
st.title("🤖 Cadastro & Laboratório de Robótica")
st.markdown("Preencha o formulário para se cadastrar e enviar seu script `.py` para o laboratório.")

with st.form("form_submissao", clear_on_submit=True):
    st.subheader("👤 Dados Cadastrais")
    nome = st.text_input("Nome Completo *")
    email = st.text_input("E-mail *")
    
    col1, col2 = st.columns(2)
    with col1:
        pais = st.text_input("País *", value="Brasil")
    with col2:
        estado = st.text_input("Estado *", value="MG")
        
    universidade = st.text_input("Universidade / Instituição (Opcional)")

    st.subheader("💻 Envio do Script Python")
    uploaded_file = st.file_uploader("Selecione seu script (.py) *", type=["py"])

    submit_button = st.form_submit_button("🚀 Finalizar Cadastro e Enviar")

# --- PROCESSAMENTO DO ALUNO ---
if submit_button:
    if not nome or not email or not pais or not estado or not uploaded_file:
        st.error("⚠️ Preencha todos os campos obrigatórios (*) e anexe o arquivo .py.")
    else:
        code_content = uploaded_file.getvalue().decode("utf-8")
        is_safe, msg = validate_code(code_content)
        
        if not is_safe:
            st.error(f"❌ Submissão Rejeitada: {msg}")
        else:
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Nomeia o arquivo recebido com a data/hora para evitar sobreposição
            safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
            filepath = os.path.join(UPLOADS_DIR, safe_filename)
            
            # 1. Salva o arquivo .py localmente
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code_content)
                
            # 2. Adiciona a linha ao arquivo CSV
            new_row = pd.DataFrame([{
                "Data_Hora": data_hora,
                "Nome": nome,
                "Email": email,
                "Pais": pais,
                "Estado": estado,
                "Universidade": universidade if universidade else "N/A",
                "Arquivo": safe_filename,
                "Status": "Aprovado"
            }])
            
            new_row.to_csv(CSV_FILE, mode='a', header=False, index=False, encoding="utf-8")
            
            st.success("✅ Cadastro e código enviados com sucesso!")
            st.info(f"Obrigado, {nome}! Seus dados foram salvos e o script foi enviado para a fila do laboratório.")

# --- ÁREA DO ADMINISTRADOR PROTEGIDA POR LOGIN ---
st.markdown("---")
with st.expander("🔒 Painel do Administrador"):
    if not st.session_state.admin_logged_in:
        st.subheader("Login de Administrador")
        user_input = st.text_input("Usuário", key="login_user")
        pass_input = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Acessar Painel"):
            if user_input == ADM_USER and pass_input == ADM_PASS:
                st.session_state.admin_logged_in = True
                st.success("Login efetuado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    else:
        # Cabeçalho do Painel Autenticado com Botão de Logout
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.subheader("📊 Registros Recebidos")
        with col_logout:
            if st.button("🚪 Sair"):
                st.session_state.admin_logged_in = False
                st.rerun()

        # Exibição e Download do CSV
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            st.dataframe(df, use_container_width=True)
            
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 Baixar CSV para Google Sheets",
                data=csv_bytes,
                file_name="submissoes_lab_robotica.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhuma submissão registrada até o momento.")
