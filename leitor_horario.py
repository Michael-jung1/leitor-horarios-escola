import streamlit as st
import pandas as pd
import re
from pypdf import PdfReader

def extrair_texto_pdf(arquivo_pdf):
    """Lê o arquivo PDF e converte as páginas em texto."""
    leitor = PdfReader(arquivo_pdf)
    texto_completo = ""
    for pagina in leitor.pages:
        texto_extraido = pagina.extract_text()
        if texto_extraido:
            texto_completo += texto_extraido + "\n"
    return texto_completo

def extrair_grade_turma(texto_pdf, turma):
    """Busca o bloco de texto específico de uma turma e estrutura os horários."""
    padrao_inicio = f"Turma: {turma}"
    inicio_idx = texto_pdf.find(padrao_inicio)
    
    if inicio_idx == -1:
        return None
        
    texto_isolado = texto_pdf[inicio_idx:]
    proxima_turma_idx = texto_isolado.find("Turma:", 10)
    
    if proxima_turma_idx != -1:
        texto_isolado = texto_isolado[:proxima_turma_idx]

    horarios = ["13:00", "13:45", "14:30", "15:30", "16:15", "17:00"]
    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    
    grade = {dia: [] for dia in dias_semana}
    grade["Horário"] = horarios
    
    for horario in horarios:
        # Busca o horário e tenta capturar as matérias na mesma linha
        padrao_linha = f"{horario}(.*)"
        match = re.search(padrao_linha, texto_isolado)
        
        if match:
            # Limpa a linha e separa as palavras
            linha_suja = match.group(1).replace('|', ' ')
            # Remove palavras muito curtas ou lixo de formatação
            materias = [m.strip() for m in linha_suja.split() if len(m.strip()) > 1]
            
            for i in range(5):
                if i < len(materias):
                    grade[dias_semana[i]].append(materias[i])
                else:
                    grade[dias_semana[i]].append("Verificar PDF")
        else:
            for dia in dias_semana:
                grade[dia].append("Verificar PDF")

    df = pd.DataFrame(grade)
    df = df[["Horário", "Segunda", "Terça", "Quarta", "Quinta", "Sexta"]]
    return df

# --- Interface Streamlit ---
st.set_page_config(page_title="Leitor de Horário Escolar", layout="centered")

st.title("📚 Extrator de Horários")
st.write("Faça o upload do seu PDF de horários para filtrar a grade da sua sala.")

# Novo componente: Upload de Arquivo
arquivo_enviado = st.file_uploader("Arraste e solte o seu PDF aqui", type=["pdf"])

turma_selecionada = st.selectbox("Qual é a sua turma?", ["104", "105", "106", "107", "108", "109", "206", "207", "208", "209", "305", "306"])

if st.button("Extrair Meu Horário"):
    if arquivo_enviado is not None:
        with st.spinner('Lendo o arquivo PDF...'):
            # Transforma o PDF em texto
            texto_extraido = extrair_texto_pdf(arquivo_enviado)
            
            # Processa o texto
            df_horario = extrair_grade_turma(texto_extraido, turma_selecionada)
            
            if df_horario is not None:
                st.success(f"Horário da Turma {turma_selecionada} encontrado!")
                st.dataframe(df_horario, use_container_width=True)
                
                st.download_button(
                    label="Baixar em JSON para o App",
                    data=df_horario.to_json(orient="records"),
                    file_name=f"horario_turma_{turma_selecionada}.json",
                    mime="application/json"
                )
            else:
                st.error("Turma não encontrada no PDF. Verifique se o arquivo está correto.")
    else:
        st.warning("Por favor, envie um arquivo PDF primeiro.")