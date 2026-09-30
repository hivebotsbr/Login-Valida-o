import streamlit as st
import ast
from datetime import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da página
st.set_page_config(page_title="Lab de Robótica - Cadastro & Submissão", page_icon="🤖", layout="centered")

st.title("🤖 Cadastro & Laboratório de Robótica")
st.markdown("Preencha o formulário abaixo para registrar seu cadastro e enviar seu script `.py`.")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

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

# Formulário único de Cadastro e Submissão
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

# Ação ao clicar no botão
if submit_button:
    # 1. Validação de campos obrigatórios
    if not nome or not email or not pais or not estado or not uploaded_file:
        st.error("⚠️ Preencha todos os campos obrigatórios (*) e anexe o arquivo .py.")
    else:
        # 2. Leitura e validação do código Python
        code_content = uploaded_file.getvalue().decode("utf-8")
        is_safe, msg = validate_code(code_content)
        
        if not is_safe:
            st.error(f"❌ Submissão Rejeitada: {msg}")
        else:
            # 3. Preparação dos dados
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Monta o novo registro
            new_row = pd.DataFrame([{
                "Data_Hora": data_hora,
                "Nome": nome,
                "Email": email,
                "Pais": pais,
                "Estado": estado,
                "Universidade": universidade if universidade else "N/A",
                "Arquivo": uploaded_file.name,
                "Status": "Aprovado"
            }])
            
            try:
                # Busca dados atuais da planilha e adiciona a nova linha
                existing_data = conn.read(worksheet="Submissoes", ttl=0)
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                
                # Salva de volta no Google Sheets
                conn.update(worksheet="Submissoes", data=updated_df)
                
                st.success("✅ Cadastro e script enviados com sucesso!")
                st.info(f"Obrigado, {nome}! Seus dados foram salvos na planilha e o script foi enviado para a fila.")
            except Exception as e:
                st.error(f"Erro ao salvar na planilha do Google Sheets: {e}")