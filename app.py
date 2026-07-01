# 1. Instala a nova ferramenta de extração de notícias
pip install streamlit pandas matplotlib wordcloud nltk newspaper3k

# 2. Roda o novo aplicativo
streamlit run monitor_enquadramento.py

import streamlit as st
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import nltk
from newspaper import Article

# Baixar recursos do NLTK (silencioso)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

from nltk.corpus import stopwords

# Configuração da página
st.set_page_config(page_title="Monitor de Enquadramento Midiático - Alicia (FGV)", layout="wide")

# Título e descrição acadêmica
st.title("Monitor de Enquadramento Midiático")
st.markdown("### Alicia - Projeto de Pesquisa | FGV")
st.markdown("""
Esta ferramenta auxilia na análise de enquadramento midiático, extraindo automaticamente 
o conteúdo de reportagens a partir de suas URLs. A análise léxica identifica a polaridade 
sentimental (positiva/negativa) e gera uma nuvem de palavras para visualização dos termos 
mais frequentes. O comparador permite contrastar o enquadramento de veículos diferentes.
""")

# Lista de palavras-chave para análise de sentimento (simplificada e acadêmica)
PALAVRAS_POSITIVAS = {
    'avanço', 'progresso', 'sucesso', 'vitória', 'conquista', 'melhoria', 'crescimento',
    'positivo', 'benefício', 'esperança', 'otimismo', 'eficiência', 'inovação', 'recuperação',
    'estabilidade', 'prosperidade', 'consenso', 'acordo', 'tranquilidade', 'favorável'
}

PALAVRAS_NEGATIVAS = {
    'crise', 'conflito', 'fracasso', 'perda', 'ataque', 'crítica', 'problema', 'negativo',
    'medo', 'pessimismo', 'instabilidade', 'corrupção', 'escândalo', 'controvérsia', 'queda',
    'recessão', 'desordem', 'violência', 'ameaça', 'prejuízo'
}

# Stopwords em português
STOPWORDS_PT = set(stopwords.words('portuguese'))
STOPWORDS_PT.update(['segundo', 'após', 'sobre', 'diz', 'disse', 'afirma', 'afirmou', 'ainda', 'também'])

def extrair_artigo(url):
    """Extrai título e texto de uma URL usando newspaper3k."""
    try:
        artigo = Article(url, language='pt')
        artigo.download()
        artigo.parse()
        return artigo.title, artigo.text
    except Exception as e:
        st.error(f"Erro ao extrair o artigo: {e}")
        return None, None

def preprocessar_texto(texto):
    """Remove pontuação, números e normaliza para minúsculas."""
    texto = re.sub(r'[^\w\s]', '', texto.lower())
    texto = re.sub(r'\d+', '', texto)
    return texto

def analisar_sentimento(texto):
    """Análise léxica simplificada de polaridade sentencial."""
    palavras = texto.split()
    pos_count = sum(1 for p in palavras if p in PALAVRAS_POSITIVAS)
    neg_count = sum(1 for p in palavras if p in PALAVRAS_NEGATIVAS)
    total = pos_count + neg_count
    
    if total == 0:
        polaridade = 0.0
        classificacao = "Neutro"
    else:
        polaridade = (pos_count - neg_count) / total
        if polaridade > 0.15:
            classificacao = "Positivo"
        elif polaridade < -0.15:
            classificacao = "Negativo"
        else:
            classificacao = "Neutro"
    
    return {
        'positivo': pos_count,
        'negativo': neg_count,
        'polaridade': polaridade,
        'classificacao': classificacao
    }

def gerar_nuvem_palavras(texto, titulo):
    """Gera e exibe uma nuvem de palavras."""
    palavras_filtradas = [p for p in texto.split() if p not in STOPWORDS_PT and len(p) > 3]
    texto_filtrado = ' '.join(palavras_filtradas)
    
    if not texto_filtrado.strip():
        st.warning("Texto insuficiente para gerar a nuvem de palavras.")
        return
    
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis',
        max_words=100
    ).generate(texto_filtrado)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.set_title(titulo, fontsize=14, fontweight='bold')
    ax.axis('off')
    st.pyplot(fig)
    plt.close()

def obter_frequencia_termos(texto, top_n=15):
    """Retorna os termos mais frequentes."""
    palavras_filtradas = [p for p in texto.split() if p not in STOPWORDS_PT and len(p) > 3]
    return Counter(palavras_filtradas).most_common(top_n)

# Menu lateral
st.sidebar.title("Navegação")
aba = st.sidebar.radio("Selecione a funcionalidade:", ["Análise Individual", "Comparador de Veículos"])

# =====================
# Análise Individual
# =====================
if aba == "Análise Individual":
    st.header("Análise de Enquadramento Individual")
    
    url = st.text_input("Insira a URL da reportagem:", placeholder="https://www.exemplo.com/reportagem...")
    
    if st.button("Analisar Reportagem", key="btn_individual"):
        if url:
            with st.spinner("Extraindo conteúdo da URL..."):
                titulo, texto = extrair_artigo(url)
            
            if texto:
                texto_proc = preprocessar_texto(texto)
                resultado = analisar_sentimento(texto_proc)
                
                st.subheader(titulo)
                st.markdown(f"**Fonte:** {url}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Classificação", resultado['classificacao'])
                with col2:
                    st.metric("Menções Positivas", resultado['positivo'])
                with col3:
                    st.metric("Menções Negativas", resultado['negativo'])
                
                st.markdown("---")
                st.markdown("### Nuvem de Palavras")
                gerar_nuvem_palavras(texto_proc, "Termos mais frequentes na reportagem")
                
                st.markdown("### Termos mais frequentes")
                freq = obter_frequencia_termos(texto_proc)
                if freq:
                    df_freq = st.dataframe(
                        [{"Termo": t, "Frequência": f} for t, f in freq],
                        use_container_width=True
                    )
            else:
                st.error("Não foi possível extrair o conteúdo. Verifique a URL informada.")
        else:
            st.warning("Por favor, insira uma URL válida.")

# =====================
# Comparador de Veículos
# =====================
elif aba == "Comparador de Veículos":
    st.header("Comparador de Enquadramento entre Veículos")
    st.markdown("Insira duas URLs de reportagens sobre o mesmo fato de veículos diferentes para comparar os enquadramentos.")
    
    col_url1, col_url2 = st.columns(2)
    
    with col_url1:
        url1 = st.text_input("URL - Veículo A", placeholder="https://www.veiculoA.com/reportagem...")
    with col_url2:
        url2 = st.text_input("URL - Veículo B", placeholder="https://www.veiculoB.com/reportagem...")
    
    if st.button("Comparar Enquadramentos", key="btn_comparador"):
        if url1 and url2:
            with st.spinner("Extraindo conteúdo dos veículos..."):
                titulo1, texto1 = extrair_artigo(url1)
                titulo2, texto2 = extrair_artigo(url2)
            
            if texto1 and texto2:
                texto1_proc = preprocessar_texto(texto1)
                texto2_proc = preprocessar_texto(texto2)
                
                res1 = analisar_sentimento(texto1_proc)
                res2 = analisar_sentimento(texto2_proc)
                
                st.markdown("---")
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.subheader("Veículo A")
                    st.markdown(f"**Título:** {titulo1}")
                    st.markdown(f"**Fonte:** {url1}")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Classificação", res1['classificacao'])
                    m2.metric("Positivas", res1['positivo'])
                    m3.metric("Negativas", res1['negativo'])
                    
                    gerar_nuvem_palavras(texto1_proc, "Nuvem - Veículo A")
                    
                    st.markdown("**Termos frequentes:**")
                    freq1 = obter_frequencia_termos(texto1_proc, top_n=10)
                    st.dataframe([{"Termo": t, "Frequência": f} for t, f in freq1], use_container_width=True)
                
                with col_b:
                    st.subheader("Veículo B")
                    st.markdown(f"**Título:** {titulo2}")
                    st.markdown(f"**Fonte:** {url2}")
                    
                    m4, m5, m6 = st.columns(3)
                    m4.metric("Classificação", res2['classificacao'])
                    m5.metric("Positivas", res2['positivo'])
                    m6.metric("Negativas", res2['negativo'])
                    
                    gerar_nuvem_palavras(texto2_proc, "Nuvem - Veículo B")
                    
                    st.markdown("**Termos frequentes:**")
                    freq2 = obter_frequencia_termos(texto2_proc, top_n=10)
                    st.dataframe([{"Termo": t, "Frequência": f} for t, f in freq2], use_container_width=True)
                
                st.markdown("---")
                st.subheader("Síntese Comparativa")
                
                comp_col1, comp_col2, comp_col3 = st.columns(3)
                with comp_col1:
                    delta_pos = res1['positivo'] - res2['positivo']
                    st.metric("Diferença de Menções Positivas (A - B)", delta_pos)
                with comp_col2:
                    delta_neg = res1['negativo'] - res2['negativo']
                    st.metric("Diferença de Menções Negativas (A - B)", delta_neg)
                with comp_col3:
                    delta_pol = res1['polaridade'] - res2['polaridade']
                    st.metric("Diferença de Polaridade (A - B)", f"{delta_pol:.2f}")
                
                st.markdown("""
                **Interpretação acadêmica:** A diferença de polaridade entre os veículos pode indicar 
ênfases distintas na cobertura do mesmo fato, revelando possíveis vieses editoriais ou escolhas 
de enquadramento narrativo.
                """)
            else:
                st.error("Não foi possível extrair o conteúdo de uma ou ambas as URLs. Verifique os links informados.")
        else:
            st.warning("Por favor, insira ambas as URLs para realizar a comparação.")

# Rodapé
st.markdown("---")
st.markdown("*Monitor de Enquadramento Midiático | Alicia (FGV) - Ferramenta de apoio à pesquisa acadêmica*")
