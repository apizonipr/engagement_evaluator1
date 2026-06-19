import streamlit as st
from PIL import Image
import base64
from io import BytesIO
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

st.set_page_config(
    page_title="Monitor de Enquadramento Midiático",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
    .main {
        background-color: #f8f9fa;
    }
    .sidebar .sidebar-content {
        background-color: #e9ecef;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #2980b9;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .news-box {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .highlight-positive {
        background-color: #d4edda;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .highlight-negative {
        background-color: #f8d7da;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .highlight-neutral {
        background-color: #fff3cd;
        padding: 2px 6px;
        border-radius: 4px;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    stopwords_pt = set(stopwords.words('portuguese'))
except:
    stopwords_pt = set()

PAGINAS = [
    "Dashboard",
    "Análise de Notícia",
    "Comparador de Notícias",
    "Nuvem de Palavras",
    "Análise de Sentimento",
    "Entidades e Temas",
    "Exportar Relatório",
    "Sobre"
]

def inicializar_estado():
    if 'noticias' not in st.session_state:
        st.session_state.noticias = []
    if 'comparacoes' not in st.session_state:
        st.session_state.comparacoes = []
    if 'relatorio' not in st.session_state:
        st.session_state.relatorio = None

inicializar_estado()

def limpar_texto(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\d+', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def extrair_palavras(texto, min_len=3):
    texto_limpo = limpar_texto(texto)
    tokens = word_tokenize(texto_limpo, language='portuguese') if texto_limpo else []
    palavras = [p for p in tokens if p not in stopwords_pt and len(p) >= min_len]
    return palavras

def contar_palavras(texto, n=15):
    palavras = extrair_palavras(texto)
    return Counter(palavras).most_common(n)

def analisar_sentimento(texto):
    if not texto:
        return {"polaridade": 0.0, "subjetividade": 0.0, "classificacao": "Neutro"}
    blob = TextBlob(texto)
    polaridade = blob.sentiment.polarity
    subjetividade = blob.sentiment.subjectivity
    if polaridade > 0.1:
        classificacao = "Positivo"
    elif polaridade < -0.1:
        classificacao = "Negativo"
    else:
        classificacao = "Neutro"
    return {
        "polaridade": polaridade,
        "subjetividade": subjetividade,
        "classificacao": classificacao
    }

def detectar_entidades(texto):
    tokens = word_tokenize(texto, language='portuguese') if texto else []
    tags = nltk.pos_tag(tokens) if tokens else []
    entidades = {
        "pessoas": [],
        "organizacoes": [],
        "locais": [],
        "termos": []
    }
    for palavra, tag in tags:
        if tag == 'NNP':
            entidades["pessoas"].append(palavra)
        elif tag == 'NNPS':
            entidades["organizacoes"].append(palavra)
    palavras = extrair_palavras(texto)
    entidades["termos"] = list(set(palavras))[:20]
    return entidades

def gerar_wordcloud(texto, largura=800, altura=400, fundo='white', colormap='viridis'):
    if not texto:
        return None
    palavras = extrair_palavras(texto)
    texto_freq = ' '.join(palavras)
    if not texto_freq:
        return None
    wc = WordCloud(
        width=largura,
        height=altura,
        background_color=fundo,
        colormap=colormap,
        max_words=100,
        stopwords=stopwords_pt
    ).generate(texto_freq)
    return wc

def imagem_para_base64(imagem_pil):
    buffer = BytesIO()
    imagem_pil.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def comparar_noticias(titulo_a, texto_a, titulo_b, texto_b):
    palavras_a = set(extrair_palavras(texto_a))
    palavras_b = set(extrair_palavras(texto_b))
    palavras_titulo_a = set(extrair_palavras(titulo_a))
    palavras_titulo_b = set(extrair_palavras(titulo_b))
    intersecao_texto = palavras_a & palavras_b
    intersecao_titulo = palavras_titulo_a & palavras_titulo_b
    uniao_texto = palavras_a | palavras_b
    similaridade_texto = len(intersecao_texto) / max(len(uniao_texto), 1)
    uniao_titulo = palavras_titulo_a | palavras_titulo_b
    similaridade_titulo = len(intersecao_titulo) / max(len(uniao_titulo), 1)
    sent_a = analisar_sentimento(texto_a)
    sent_b = analisar_sentimento(texto_b)
    diferenca_sentimento = abs(sent_a["polaridade"] - sent_b["polaridade"])
    termos_comuns = sorted(list(intersecao_texto))[:20]
    termos_exclusivos_a = sorted(list(palavras_a - palavras_b))[:20]
    termos_exclusivos_b = sorted(list(palavras_b - palavras_a))[:20]
    return {
        "similaridade_texto": round(similaridade_texto * 100, 2),
        "similaridade_titulo": round(similaridade_titulo * 100, 2),
        "intersecao_texto": intersecao_texto,
        "intersecao_titulo": intersecao_titulo,
        "sentimento_a": sent_a,
        "sentimento_b": sent_b,
        "diferenca_sentimento": round(diferenca_sentimento, 3),
        "termos_comuns": termos_comuns,
        "termos_exclusivos_a": termos_exclusivos_a,
        "termos_exclusivos_b": termos_exclusivos_b
    }

def dashboard():
    st.title("📊 Dashboard - Monitor de Enquadramento Midiático")
    st.markdown("Visão geral das análises realizadas no sistema.")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Notícias Analisadas", len(st.session_state.noticias))
    with col2:
        st.metric("Comparações Realizadas", len(st.session_state.comparacoes))
    with col3:
        st.metric("Relatórios Gerados", 1 if st.session_state.relatorio else 0)
    with col4:
        st.metric("Páginas Disponíveis", len(PAGINAS) - 1)
    st.divider()
    if st.session_state.noticias:
        st.subheader("Últimas Notícias Analisadas")
        for noticia in st.session_state.noticias[-5:]:
            with st.container():
                st.markdown(f"**{noticia['manchete']}**")
                st.caption(f"Fonte: {noticia['url']}")
    else:
        st.info("Nenhuma notícia analisada ainda. Utilize a página 'Análise de Notícia' para começar.")

def analise_noticia():
    st.title("🔍 Análise de Notícia")
    st.markdown("Insira os dados de uma notícia para análise completa de enquadramento.")
    with st.form("form_analise"):
        url = st.text_input("URL da notícia", placeholder="https://exemplo.com/noticia")
        manchete = st.text_input("Manchete", placeholder="Digite a manchete da notícia")
        texto = st.text_area("Texto completo", placeholder="Cole o texto completo da notícia aqui", height=250)
        submitted = st.form_submit_button("Analisar Notícia")
    if submitted:
        if not texto.strip():
            st.warning("Por favor, insira o texto da notícia para realizar a análise.")
            return
        noticia = {
            "url": url,
            "manchete": manchete,
            "texto": texto
        }
        st.session_state.noticias.append(noticia)
        st.success("Notícia adicionada para análise!")
        st.divider()
        st.subheader("Resultados da Análise")
        palavras = contar_palavras(texto, 20)
        sentimento = analisar_sentimento(texto)
        entidades = detectar_entidades(texto)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Classificação de Sentimento", sentimento["classificacao"])
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Polaridade", f"{sentimento['polaridade']:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Subjetividade", f"{sentimento['subjetividade']:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        st.subheader("Principais Termos")
        if palavras:
            df = pd.DataFrame(palavras, columns=["Termo", "Frequência"])
            st.bar_chart(df.set_index("Termo"))
        else:
            st.info("Não foram encontrados termos suficientes para análise.")
        st.subheader("Entidades Detectadas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Pessoas:")
            st.write(entidades["pessoas"] if entidades["pessoas"] else ["Nenhuma detectada"])
        with col2:
            st.write("Organizações:")
            st.write(entidades["organizacoes"] if entidades["organizacoes"] else ["Nenhuma detectada"])
        with col3:
            st.write("Termos Relevantes:")
            st.write(entidades["termos"] if entidades["termos"] else ["Nenhum detectado"])

def comparador_noticias():
    st.title("⚖️ Comparador de Notícias")
    st.markdown("Compare duas notícias para identificar similaridades, diferenças e enquadramentos distintos.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<<div class='news-box'>", unsafe_allow_html=True)
        st.subheader("Notícia A")
        url_a = st.text_input("URL da Notícia A", value="", placeholder="Insira a URL aqui...", key="url_a")
        manchete_a = st.text_input("Manchete A", value="", placeholder="Escreva a manchete aqui...", key="manchete_a")
        texto_a = st.text_area("Texto A", value="", placeholder="Cole o texto completo aqui...", height=250, key="texto_a")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("<<div class='news-box'>", unsafe_allow_html=True)
        st.subheader("Notícia B")
        url_b = st.text_input("URL da Notícia B", value="", placeholder="Insira a URL aqui...", key="url_b")
        manchete_b = st.text_input("Manchete B", value="", placeholder="Escreva a manchete aqui...", key="manchete_b")
        texto_b = st.text_area("Texto B", value="", placeholder="Cole o texto completo aqui...", height=250, key="texto_b")
        st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Comparar Notícias", key="comparar_noticias"):
        campos_vazios = []
        if not url_a.strip():
            campos_vazios.append("URL da Notícia A")
        if not manchete_a.strip():
            campos_vazios.append("Manchete A")
        if not texto_a.strip():
            campos_vazios.append("Texto A")
        if not url_b.strip():
            campos_vazios.append("URL da Notícia B")
        if not manchete_b.strip():
            campos_vazios.append("Manchete B")
        if not texto_b.strip():
            campos_vazios.append("Texto B")
        if campos_vazios:
            st.warning(f"Preencha todos os campos antes de comparar. Campos vazios: {', '.join(campos_vazios)}")
            return
        resultado = comparar_noticias(manchete_a, texto_a, manchete_b, texto_b)
        st.session_state.comparacoes.append({
            "manchete_a": manchete_a,
            "manchete_b": manchete_b,
            "resultado": resultado
        })
        st.success("Comparação realizada com sucesso!")
        st.divider()
        st.subheader("Resultado da Comparação")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Similaridade de Texto", f"{resultado['similaridade_texto']}%")
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Similaridade de Título", f"{resultado['similaridade_titulo']}%")
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Diferença de Sentimento", f"{resultado['diferenca_sentimento']}")
            st.markdown("</div>", unsafe_allow_html=True)
        st.subheader("Sentimentos")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Notícia A:**")
            st.write(f"Classificação: {resultado['sentimento_a']['classificacao']}")
            st.write(f"Polaridade: {resultado['sentimento_a']['polaridade']:.2f}")
        with col2:
            st.markdown("**Notícia B:**")
            st.write(f"Classificação: {resultado['sentimento_b']['classificacao']}")
            st.write(f"Polaridade: {resultado['sentimento_b']['polaridade']:.2f}")
        st.subheader("Termos em Comum")
        st.write(resultado["termos_comuns"] if resultado["termos_comuns"] else ["Nenhum termo em comum encontrado"])
        st.subheader("Termos Exclusivos da Notícia A")
        st.write(resultado["termos_exclusivos_a"] if resultado["termos_exclusivos_a"] else ["Nenhum termo exclusivo encontrado"])
        st.subheader("Termos Exclusivos da Notícia B")
        st.write(resultado["termos_exclusivos_b"] if resultado["termos_exclusivos_b"] else ["Nenhum termo exclusivo encontrado"])

def nuvem_palavras():
    st.title("☁️ Nuvem de Palavras")
    st.markdown("Gere uma nuvem de palavras a partir de um texto ou notícia analisada.")
    texto = ""
    if st.session_state.noticias:
        opcoes = ["Inserir texto manualmente"] + [n["manchete"] for n in st.session_state.noticias]
        escolha = st.selectbox("Selecione uma notícia ou insira texto manualmente", opcoes)
        if escolha != "Inserir texto manualmente":
            for noticia in st.session_state.noticias:
                if noticia["manchete"] == escolha:
                    texto = noticia["texto"]
                    break
    if not texto:
        texto = st.text_area("Texto para nuvem de palavras", placeholder="Cole o texto aqui", height=250)
    col1, col2, col3 = st.columns(3)
    with col1:
        largura = st.slider("Largura", 400, 1600, 800)
    with col2:
        altura = st.slider("Altura", 200, 800, 400)
    with col3:
        colormap = st.selectbox("Paleta de cores", ["viridis", "plasma", "magma", "cividis", "inferno", "Spectral", "coolwarm", "RdYlGn"])
    if st.button("Gerar Nuvem de Palavras"):
        if not texto.strip():
            st.warning("Por favor, insira um texto para gerar a nuvem de palavras.")
            return
        wc = gerar_wordcloud(texto, largura, altura, colormap=colormap)
        if wc:
            fig, ax = plt.subplots(figsize=(largura/100, altura/100))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        else:
            st.warning("Não foi possível gerar a nuvem. O texto pode não conter palavras suficientes.")

def analise_sentimento_pagina():
    st.title("😊 Análise de Sentimento")
    st.markdown("Analise o sentimento de textos ou notícias de forma detalhada.")
    texto = ""
    if st.session_state.noticias:
        opcoes = ["Inserir texto manualmente"] + [n["manchete"] for n in st.session_state.noticias]
        escolha = st.selectbox("Selecione uma notícia ou insira texto manualmente", opcoes)
        if escolha != "Inserir texto manualmente":
            for noticia in st.session_state.noticias:
                if noticia["manchete"] == escolha:
                    texto = noticia["texto"]
                    break
    if not texto:
        texto = st.text_area("Texto para análise de sentimento", placeholder="Cole o texto aqui", height=250)
    if st.button("Analisar Sentimento"):
        if not texto.strip():
            st.warning("Por favor, insira um texto para análise.")
            return
        sentimento = analisar_sentimento(texto)
        frases = sent_tokenize(texto, language='portuguese') if texto else []
        st.subheader("Resultado Geral")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Classificação", sentimento["classificacao"])
        with col2:
            st.metric("Polaridade", f"{sentimento['polaridade']:.2f}")
        with col3:
            st.metric("Subjetividade", f"{sentimento['subjetividade']:.2f}")
        st.subheader("Análise por Sentença")
        for frase in frases:
            if frase.strip():
                sent_frase = analisar_sentimento(frase)
                classe = sent_frase["classificacao"]
                if classe == "Positivo":
                    st.markdown(f"<<span class='highlight-positive'>{frase}</span> — {classe}", unsafe_allow_html=True)
                elif classe == "Negativo":
                    st.markdown(f"<<span class='highlight-negative'>{frase}</span> — {classe}", unsafe_allow_html=True)
                else:
                    st.markdown(f"<<span class='highlight-neutral'>{frase}</span> — {classe}", unsafe_allow_html=True)

def entidades_temas():
    st.title("🏷️ Entidades e Temas")
    st.markdown("Identifique pessoas, organizações, locais e temas principais nos textos.")
    texto = ""
    if st.session_state.noticias:
        opcoes = ["Inserir texto manualmente"] + [n["manchete"] for n in st.session_state.noticias]
        escolha = st.selectbox("Selecione uma notícia ou insira texto manualmente", opcoes)
        if escolha != "Inserir texto manualmente":
            for noticia in st.session_state.noticias:
                if noticia["manchete"] == escolha:
                    texto = noticia["texto"]
                    break
    if not texto:
        texto = st.text_area("Texto para extração de entidades", placeholder="Cole o texto aqui", height=250)
    if st.button("Extrair Entidades e Temas"):
        if not texto.strip():
            st.warning("Por favor, insira um texto para extração.")
            return
        entidades = detectar_entidades(texto)
        palavras = contar_palavras(texto, 20)
        st.subheader("Entidades")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Pessoas")
            st.write(entidades["pessoas"] if entidades["pessoas"] else ["Nenhuma detectada"])
        with col2:
            st.write("Organizações")
            st.write(entidades["organizacoes"] if entidades["organizacoes"] else ["Nenhuma detectada"])
        with col3:
            st.write("Locais / Termos")
            st.write(entidades["termos"] if entidades["termos"] else ["Nenhum detectado"])
        st.subheader("Temas Principais")
        if palavras:
            df = pd.DataFrame(palavras, columns=["Termo", "Frequência"])
            st.bar_chart(df.set_index("Termo"))
        else:
            st.info("Não foram encontrados termos suficientes.")

def exportar_relatorio():
    st.title("📄 Exportar Relatório")
    st.markdown("Gere um relatório consolidado com todas as análises realizadas.")
    if not st.session_state.noticias and not st.session_state.comparacoes:
        st.info("Não há dados suficientes para gerar um relatório. Realize análises ou comparações primeiro.")
        return
    if st.button("Gerar Relatório HTML"):
        relatorio = []
        relatorio.append("<<html><head><meta charset='utf-8'><title>Relatório</title></head><body>")
        relatorio.append("<<h1>Relatório de Monitoramento de Enquadramento Midiático</h1>")
        relatorio.append(f"<<p>Total de notícias analisadas: {len(st.session_state.noticias)}</p>")
        relatorio.append(f"<<p>Total de comparações: {len(st.session_state.comparacoes)}</p>")
        relatorio.append("<<hr>")
        if st.session_state.noticias:
            relatorio.append("<<h2>Notícias Analisadas</h2>")
            for i, noticia in enumerate(st.session_state.noticias, 1):
                sentimento = analisar_sentimento(noticia["texto"])
                relatorio.append(f"<<h3>{i}. {noticia['manchete']}</h3>")
                relatorio.append(f"<<p><strong>URL:</strong> {noticia['url']}</p>")
                relatorio.append(f"<<p><strong>Sentimento:</strong> {sentimento['classificacao']} (polaridade {sentimento['polaridade']:.2f})</p>")
                relatorio.append(f"<<p>{noticia['texto'][:500]}...</p>")
        if st.session_state.comparacoes:
            relatorio.append("<<h2>Comparações Realizadas</h2>")
            for i, comp in enumerate(st.session_state.comparacoes, 1):
                r = comp["resultado"]
                relatorio.append(f"<<h3>{i}. {comp['manchete_a']} vs {comp['manchete_b']}</h3>")
                relatorio.append(f"<<p>Similaridade de texto: {r['similaridade_texto']}%</p>")
                relatorio.append(f"<<p>Similaridade de título: {r['similaridade_titulo']}%</p>")
                relatorio.append(f"<<p>Diferença de sentimento: {r['diferenca_sentimento']}</p>")
        relatorio.append("</body></html>")
        html_completo = "\n".join(relatorio)
        st.session_state.relatorio = html_completo
        st.download_button(
            label="Baixar Relatório HTML",
            data=html_completo,
            file_name="relatorio_enquadramento.html",
            mime="text/html"
        )
        st.success("Relatório gerado com sucesso!")

def sobre():
    st.title("ℹ️ Sobre")
    st.markdown("""
    **Monitor de Enquadramento Midiático**

    Ferramenta desenvolvida para auxiliar pesquisadores, jornalistas e cidadãos a identificarem padrões de enquadramento, sentimento e similaridade em notícias.

    Funcionalidades:
    - Análise individual de notícias
    - Comparação entre duas notícias
    - Geração de nuvem de palavras
    - Análise de sentimento por texto e sentença
    - Extração de entidades e temas
    - Exportação de relatórios em HTML

    Desenvolvido com Python, Streamlit, NLTK, TextBlob e WordCloud.
    """)

def main():
    st.sidebar.title("📰 Menu")
    pagina = st.sidebar.radio("Navegação", PAGINAS)
    if pagina == "Dashboard":
        dashboard()
    elif pagina == "Análise de Notícia":
        analise_noticia()
    elif pagina == "Comparador de Notícias":
        comparador_noticias()
    elif pagina == "Nuvem de Palavras":
        nuvem_palavras()
    elif pagina == "Análise de Sentimento":
        analise_sentimento_pagina()
    elif pagina == "Entidades e Temas":
        entidades_temas()
    elif pagina == "Exportar Relatório":
        exportar_relatorio()
    elif pagina == "Sobre":
        sobre()

if __name__ == "__main__":
    main()para fins educacionais e de pesquisa em comunicação política.')'
