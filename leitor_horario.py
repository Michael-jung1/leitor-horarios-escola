import streamlit as st
import pandas as pd
import pdfplumber

SIGLAS = {
    'BIO': 'Biologia', 'ED.F': 'Ed. Física', 'ED.F.': 'Ed. Física',
    'PORT': 'Português', 'ART': 'Artes', 'MAT': 'Matemática',
    'GEO': 'Geografia', 'SOC': 'Sociologia', 'HIST': 'História',
    'FIL': 'Filosofia', 'ING': 'Inglês', 'FIS': 'Física',
    'QUI': 'Química', 'ESP': 'Espanhol', 'BIOLOGIA': 'Biologia'
}

def extrair_horario_inteligente(arquivo_pdf, turma_alvo):
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    resultado = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto or f"Turma: {turma_alvo}" not in texto:
                continue
            
            tabelas = page.extract_tables()
            for tabela in tabelas:
                # Verifica se é o cabeçalho correto
                if not tabela or not tabela[0] or "Hor" not in str(tabela[0][0]):
                    continue
                    
                for linha in tabela[1:]:
                    texto_horario = str(linha[0]) if linha[0] else ""
                    horarios = [h.strip() for h in texto_horario.split("\n") if ":" in h]
                    
                    for index_horario, h in enumerate(horarios):
                        linha_formatada = {"Horário": h}
                        
                        for i, dia in enumerate(dias):
                            col = i + 1
                            celula = str(linha[col]) if col < len(linha) and linha[col] else ""
                            
                            # Limpa os espaços em branco extras dentro da célula
                            linhas_celula = [x.strip() for x in celula.split("\n") if x.strip()]
                            
                            # Lógica à prova de falhas: Matéria fica na linha PAR, Professor na linha ÍMPAR
                            idx_materia = index_horario * 2
                            idx_prof = idx_materia + 1
                            
                            # Tenta pegar a matéria e o professor; se falhar, usa um padrão
                            materia_crua = linhas_celula[idx_materia] if idx_materia < len(linhas_celula) else "Livre"
                            prof_cru = linhas_celula[idx_prof] if idx_prof < len(linhas_celula) else "Não Informado"
                            
                            sigla = materia_crua.split(" ")[0].upper()
                            
                            if sigla and sigla != "LIVRE":
                                materia_nome = SIGLAS.get(sigla, materia_crua.title())
                                # Força a união com a barra "|" para o React conseguir separar depois
                                linha_formatada[dia] = f"{materia_nome} | {prof_cru.title()}"
                            else:
                                linha_formatada[dia] = "Livre"
                        
                        resultado.append(linha_formatada)
                
                if resultado:
                    return pd.DataFrame(resultado)
    return None

st.set_page_config(page_title="Leitor de Horário Escolar", layout="centered")

# Lembre-se de colocar o link do seu site principal aqui!
st.link_button("⬅️ Voltar para o App Principal", "https://app-organizacao-escolar.vercel.app/")

st.title("📚 Extrator de Horários Automático")
st.write("Arraste seu PDF gerado pelo Urania. O sistema mapeará as matérias e os professores automaticamente.")

arquivo_enviado = st.file_uploader("Arraste e solte o seu PDF aqui", type=["pdf"])
turma_selecionada = st.selectbox("Selecione sua Turma:", [
    "104", "105", "106", "107", "108", "109", "206", "207", "208", "209", "305", "306"
])

if st.button("Extrair Meu Horário"):
    if arquivo_enviado is not None:
        with st.spinner('Analisando as grades do PDF...'):
            df_horario = extrair_horario_inteligente(arquivo_enviado, turma_selecionada)
            
            if df_horario is not None and not df_horario.empty:
                st.success(f"🎉 Horário da Turma {turma_selecionada} mapeado!")
                st.dataframe(df_horario, use_container_width=True)
                
                st.download_button(
                    label="Baixar em JSON para o App",
                    data=df_horario.to_json(orient="records"),
                    file_name=f"horario_turma_{turma_selecionada}.json",
                    mime="application/json"
                )
            else:
                st.error("Turma não encontrada ou PDF com formato inválido.")
    else:
        st.warning("Envie o arquivo PDF primeiro!")
