pip install streamlit pandas matplotlib wordcloud openpyxl
streamlit run monitor_enquadramento_midia.py

import re
import string
from collections import Counter
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from wordcloud import WordCloud

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Monitor de Enquadramento Midiático - Alicia (FGV)",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CONSTANTES E LÉXICO DE SENTIMENTO EM PORTUGUÊS
# =============================================================================
POSITIVE_WORDS_PT = {
    "bom", "boa", "ótimo", "ótima", "excelente", "positivo", "positiva", "favorável",
    "avanço", "avanços", "progresso", "sucesso", "crescimento", "recuperação", "melhora",
    "benefício", "benefícios", "vantagem", "vantagens", "oportunidade", "oportunidades",
    "esperança", "confiança", "fortalecimento", "fortalece", "estabilidade", "estável",
    "eficiente", "eficaz", "inovação", "inovações", "desenvolvimento", "desenvolvimentos",
    "sólido", "sólida", "resiliente", "resiliência", "ganho", "ganhos", "alta", "altas",
    "aumento", "aumentos", "superávit", "lucro", "lucros", "expansão", "expansões",
    "aprovação", "aprovações", "apoio", "apoios", "consenso", "harmonia", "celebrar",
    "comemorar", "vitória", "vitórias", "conquista", "conquistas", "melhorar", "crescer",
}

NEGATIVE_WORDS_PT = {
    "mau", "ruim", "péssimo", "negativo", "negativa", "desfavorável", "crise", "crises",
    "queda", "quedas", "recuo", "retração", "recessão", "estagnação", "dificuldade",
    "dificuldades", "problema", "problemas", "preocupação", "preocupações", "ameaça",
    "ameaças", "risco", "riscos", "instabilidade", "instável", "incerteza", "incertezas",
    "tensão", "tensões", "conflito", "conflitos", "escândalo", "escândalos", "corrupção",
    "fracasso", "fracassos", "perda", "perdas", "déficit", "déficits", "divida", "dívidas",
    "inflação", "desemprego", "pobreza", "desigualdade", "violência", "crime", "crimes",
    "acusação", "acusações", "denúncia", "denúncias", "investigação", "investigações",
    "cai", "cair", "diminuir", "reduzir", "retrair", "piorar", "declinar", "desacelerar",
    "austeridade", "dificultar", "obstáculo", "obstáculos", "resistência", "resistências",
}

STOPWORDS_PT = {
    "a", "à", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo", "as", "às",
    "até", "com", "como", "da", "das", "de", "dela", "delas", "dele", "deles", "depois",
    "do", "dos", "e", "ela", "elas", "ele", "eles", "em", "entre", "era", "eram", "essa",
    "essas", "esse", "esses", "esta", "estas", "este", "estes", "eu", "isso", "isto", "já",
    "lhe", "lhes", "mais", "mas", "me", "mesma", "mesmas", "mesmo", "mesmos", "meu", "meus",
    "minha", "minhas", "muito", "muitos", "na", "nas", "no", "nos", "nossa", "nossas",
    "nosso", "nossos", "num", "numa", "nuns", "numas", "o", "os", "ou", "para", "pela",
    "pelas", "pelo", "pelos", "por", "qual", "quando", "que", "quem", "se", "sem", "sua",
    "suas", "também", "te", "teu", "teus", "tu", "tua", "tuas", "um", "uma", "uns", "umas",
    "você", "vocês", "vos", "vosso", "vossos", "sobre", "sob", "ante", "após", "até", "desde",
    "durante", "trás", "contra", "perante", "segundo", "sendo", "sendo", "sido", "ter", "ter",
    "tendo", "ter", "teve", "tinha", "tive", "tiveram", "têm", "temos", "está", "estão", "estou",
    "estamos", "estive", "estiveram", "estava", "estavam", "ser", "sendo", "sido", "é", "são",
    "era", "eram", "foi", "foram", "fui", "fomos", "foram", "haver", "havendo", "havia", "houve",
    "houveram", "há", "não", "sim", "nem", "já", "ainda", "agora", "antes", "depois", "sempre",
    "nunca", "talvez", "apenas", "só", "tão", "tanto", "assim", "desta", "deste", "disso", "disto",
    "daquilo", "daquele", "daquela", "desses", "destas", "destes", "disso", "nisso", "naquilo",
    "nele", "nela", "neles", "nelas", "aqui", "ali", "lá", "onde", "cujo", "cuja", "cujos", "cujas",
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def clean_text(text: str) -> str:
    """Normaliza o texto: minúsculas, remove URLs, menções, pontuação e dígitos."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+|#\w+", "", text)
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list:
    """Tokeniza simplesmente por espaços após limpeza."""
    return [t for t in clean_text(text).split() if t]


def remove_stopwords(tokens: list) -> list:
    """Remove stopwords em português."""
    return [t for t in tokens if t not in STOPWORDS_PT and len(t) > 2]


def extract_terms(text: str, top_n: int = 15) -> list:
    """Retorna os termos mais frequentes (com exceção de stopwords)."""
    tokens = remove_stopwords(tokenize(text))
    counter = Counter(tokens)
    return counter.most_common(top_n)


def analyze_sentiment(text: str) -> dict:
    """
    Análise de sentimento baseada em léxico em português.
    Retorna dicionário com label, score e contadores.
    """
    tokens = tokenize(text)
    positive = sum(1 for t in tokens if t in POSITIVE_WORDS_PT)
    negative = sum(1 for t in tokens if t in NEGATIVE_WORDS_PT)
    total = positive + negative

    if total == 0:
        label = "Neutro"
        score = 0.0
    else:
        score = (positive - negative) / total
        if score > 0.15:
            label = "Positivo"
        elif score < -0.15:
            label = "Negativo"
        else:
            label = "Neutro"

    return {
        "label": label,
        "score": round(score, 3),
        "positive_words": positive,
        "negative_words": negative,
    }


def sentiment_label_class(label: str) -> str:
    """Retorna emoji + label traduzido para exibição."""
    mapping = {
        "Positivo": "🟢 Positivo",
        "Neutro": "🟡 Neutro",
        "Negativo": "🔴 Negativo",
    }
    return mapping.get(label, "⚪ Indefinido")


# =============================================================================
# FUNÇÕES DE VISUALIZAÇÃO
# =============================================================================
def build_wordcloud(text_corpus: str, width: int = 800, height: int = 400) -> plt.Figure:
    """Gera uma nuvem de palavras a partir de um corpus de texto."""
    tokens = remove_stopwords(tokenize(text_corpus))
    if not tokens:
        fig, ax = plt.subplots(figsize=(width / 100, height / 100))
        ax.text(0.5, 0.5, "Sem dados suficientes para nuvem de palavras", ha="center", va="center")
        ax.axis("off")
        return fig

    corpus = " ".join(tokens)
    wordcloud = WordCloud(
        width=width,
        height=height,
        background_color="white",
        colormap="Blues",
        max_words=200,
        stopwords=STOPWORDS_PT,
        prefer_horizontal=0.9,
        min_font_size=10,
    ).generate(corpus)

    fig, ax = plt.subplots(figsize=(width / 100, height / 100))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    return fig


def plot_sentiment_distribution(df: pd.DataFrame) -> plt.Figure:
    """Gera gráfico de barras com a distribuição de sentimentos."""
    counts = df["sentiment_label"].value_counts().reindex(["Positivo", "Neutro", "Negativo"]).fillna(0)
    colors = ["#2ecc71", "#f1c40f", "#e74c3c"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="black")
    ax.set_ylabel("Quantidade de notícias")
    ax.set_title("Distribuição de Sentimento")
    ax.set_ylim(0, max(counts.values.max() * 1.1, 1))
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
        )
    return fig


def plot_sentiment_timeline(df: pd.DataFrame) -> plt.Figure:
    """Gera gráfico de linha temporal do sentimento médio."""
    if "date" not in df.columns or df["date"].isna().all():
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.text(0.5, 0.5, "Data não disponível para linha temporal", ha="center", va="center")
        ax.axis("off")
        return fig

    timeline = df.dropna(subset=["date"]).copy()
    timeline["date_only"] = pd.to_datetime(timeline["date"]).dt.date
    daily = timeline.groupby("date_only").agg(
        avg_score=("sentiment_score", "mean"),
        count=("sentiment_score", "size"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(daily["date_only"], daily["avg_score"], marker="o", color="#3498db", linewidth=2)
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Data")
    ax.set_ylabel("Score médio de sentimento")
    ax.set_title("Evolução do Sentimento ao Longo do Tempo")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


# =============================================================================
# GERAÇÃO DE DADOS DE EXEMPLO
# =============================================================================
def generate_sample_data(n: int = 20) -> pd.DataFrame:
    """Gera um conjunto de notícias fictícias para demonstração."""
    np.random.seed(42)
    templates = [
        ("Mercado financeiro apresenta alta expressiva e investidores comemoram resultados", "Positivo"),
        ("Novo projeto de lei gera preocupação entre economistas e analistas", "Negativo"),
        ("Ministro anuncia medidas para fortalecer a educação e reduzir desigualdades", "Positivo"),
        ("Crise política afeta aprovação de reformas e aumenta tensão no Congresso", "Negativo"),
        ("Estudo aponta avanço na recuperação econômica e crescimento do PIB", "Positivo"),
        ("Empresas relatam dificuldades com alta de custos e queda na demanda", "Negativo"),
        ("Tecnologia inovadora promete transformar o setor produtivo", "Positivo"),
        ("Debates sobre orçamento geram instabilidade e incertezas no mercado", "Negativo"),
        ("Governo investe em infraestrutura e cria oportunidades de desenvolvimento", "Positivo"),
        ("Escândalo de corrupção investigado pela Polícia Federal gera crise", "Negativo"),
    ]

    rows = []
    for i in range(n):
        template, _ = templates[i % len(templates)]
        date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=i * 2)
        rows.append(
            {
                "id": i + 1,
                "date": date,
                "source": np.random.choice(["Portal A", "Jornal B", "Revista C", "Agência D"]),
                "title": f"{template} #{i+1}",
                "content": f"{template}. "
                "Analistas destacam que os próximos meses serão decisivos para entender os impactos. "
                "A sociedade acompanha de perto as novas medidas e seus efeitos no cotidiano.",
                "url": f"https://exemplo.com/noticia/{i+1}",
            }
        )
    return pd.DataFrame(rows)


# =============================================================================
# CARREGAMENTO E PROCESSAMENTO
# =============================================================================
def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica análise de sentimento e extrai termos no DataFrame."""
    df = df.copy()
    df["text_for_analysis"] = df.apply(
        lambda row: f"{row.get('title', '')} {row.get('content', '')}", axis=1
    )

    sentiment_data = df["text_for_analysis"].apply(analyze_sentiment)
    df["sentiment_label"] = sentiment_data.apply(lambda x: x["label"])
    df["sentiment_score"] = sentiment_data.apply(lambda x: x["score"])
    df["positive_words"] = sentiment_data.apply(lambda x: x["positive_words"])
    df["negative_words"] = sentiment_data.apply(lambda x: x["negative_words"])

    df["top_terms"] = df["text_for_analysis"].apply(lambda x: extract_terms(x, top_n=10))
    return df


def load_uploaded_data(file) -> pd.DataFrame:
    """Carrega CSV ou Excel enviado pelo usuário."""
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    raise ValueError("Formato de arquivo não suportado. Envie CSV ou Excel.")


# =============================================================================
# SEÇÕES DO APLICATIVO
# =============================================================================
def render_header():
    st.title("📰 Monitor de Enquadramento Midiático")
    st.markdown("**Alicia (FGV)** – Análise de sentimento, nuvem de palavras e comparador de notícias")
    st.markdown("---")


def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Configurações")
        st.markdown("Carregue um arquivo CSV/Excel com as colunas: `title`, `content`, `date` (opcional) e `source` (opcional).")
        uploaded_file = st.file_uploader("Upload de notícias", type=["csv", "xlsx", "xls"])
        st.markdown("---")
        st.markdown("**Legenda de sentimento:**")
        st.markdown("🟢 Positivo  \n🟡 Neutro  \n🔴 Negativo")
    return uploaded_file


def render_metrics(df: pd.DataFrame):
    total = len(df)
    pos = (df["sentiment_label"] == "Positivo").sum()
    neu = (df["sentiment_label"] == "Neutro").sum()
    neg = (df["sentiment_label"] == "Negativo").sum()
    avg_score = df["sentiment_score"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total de notícias", total)
    col2.metric("Positivas", pos)
    col3.metric("Neutras", neu)
    col4.metric("Negativas", neg)
    col5.metric("Score médio", round(avg_score, 3))
    st.markdown("---")


def render_data_table(df: pd.DataFrame):
    st.subheader("📋 Notícias analisadas")
    display_df = df[["title", "source", "date", "sentiment_label", "sentiment_score"]].copy()
    display_df.columns = ["Título", "Fonte", "Data", "Sentimento", "Score"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_sentiment_analysis(df: pd.DataFrame):
    st.subheader("📊 Análise de Sentimento")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.pyplot(plot_sentiment_distribution(df))
    with col2:
        st.pyplot(plot_sentiment_timeline(df))

    st.markdown("#### Detalhamento por notícia")
    selected = st.selectbox("Selecione uma notícia para ver detalhes", options=df["title"].tolist())
    row = df[df["title"] == selected].iloc[0]
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Sentimento", sentiment_label_class(row["sentiment_label"]))
    col_b.metric("Score", row["sentiment_score"])
    col_c.metric("Fonte", row.get("source", "N/D"))
    st.markdown(f"**Conteúdo:** {row['content']}")
    st.markdown(f"**URL:** {row.get('url', 'N/D')}")



def render_wordcloud(df: pd.DataFrame):
    st.subheader("☁️ Nuvem de Palavras")
    st.markdown("Palavras mais frequentes considerando todo o corpus de notícias.")

    sentiment_filter = st.segmented_control(
        "Filtrar nuvem por sentimento:",
        options=["Todas", "Positivas", "Neutras", "Negativas"],
        default="Todas",
    )

    map_filter = {"Todas": None, "Positivas": "Positivo", "Neutras": "Neutro", "Negativas": "Negativo"}
    selected_label = map_filter.get(sentiment_filter)

    if selected_label:
        corpus_df = df[df["sentiment_label"] == selected_label]
        st.info(f"Nuvem gerada com {len(corpus_df)} notícias {sentiment_filter.lower()}.")
    else:
        corpus_df = df

    if corpus_df.empty:
        st.warning("Não há notícias suficientes para gerar a nuvem com esse filtro.")
        return

    corpus_text = " ".join(corpus_df["text_for_analysis"].fillna(""))
    st.pyplot(build_wordcloud(corpus_text))



def render_news_comparator(df: pd.DataFrame):
    st.subheader("⚖️ Comparador de Notícias")
    st.markdown("Selecione duas notícias para comparar enquadramento, sentimento e termos.")

    titles = df["title"].tolist()
    col1, col2 = st.columns(2)
    with col1:
        title_a = st.selectbox("Notícia A", options=titles, index=0, key="news_a")
    with col2:
        title_b = st.selectbox("Notícia B", options=titles, index=min(1, len(titles) - 1), key="news_b")

    if title_a == title_b:
        st.warning("Selecione duas notícias distintas para comparar.")
        return

    row_a = df[df["title"] == title_a].iloc[0]
    row_b = df[df["title"] == title_b].iloc[0]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 🅰️ {row_a['title']}")
        st.markdown(f"**Fonte:** {row_a.get('source', 'N/D')} | **Data:** {row_a.get('date', 'N/D')}")
        st.metric("Sentimento", sentiment_label_class(row_a["sentiment_label"]))
        st.metric("Score", row_a["sentiment_score"])
        st.markdown(f"**Resumo:** {row_a['content']}")
        st.markdown("**Termos principais:** " + ", ".join([t for t, _ in row_a["top_terms"]]))

    with c2:
        st.markdown(f"### 🅱️ {row_b['title']}")
        st.markdown(f"**Fonte:** {row_b.get('source', 'N/D')} | **Data:** {row_b.get('date', 'N/D')}")
        st.metric("Sentimento", sentiment_label_class(row_b["sentiment_label"]))
        st.metric("Score", row_b["sentiment_score"])
        st.markdown(f"**Resumo:** {row_b['content']}")
        st.markdown("**Termos principais:** " + ", ".join([t for t, _ in row_b["top_terms"]]))

    st.markdown("---")
    st.markdown("#### 🔍 Comparativo de sentimento")
    diff_score = row_a["sentiment_score"] - row_b["sentiment_score"]
    if row_a["sentiment_label"] == row_b["sentiment_label"]:
        st.info(f"Ambas as notícias têm enquadramento **{row_a['sentiment_label'].lower()}** (diferença de score: {abs(diff_score):.3f}).")
    else:
        st.warning(
            f"Enquadramento divergente: notícia A é **{row_a['sentiment_label'].lower()}** "
            f"enquanto a notícia B é **{row_b['sentiment_label'].lower()}**."
        )



def render_export(df: pd.DataFrame):
    st.markdown("---")
    st.subheader("💾 Exportar resultados")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Baixar análise em CSV",
        data=csv,
        file_name=f"analise_sentimento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


# =============================================================================
# APLICATIVO PRINCIPAL
# =============================================================================
def main():
    render_header()
    uploaded_file = render_sidebar()

    if uploaded_file is not None:
        try:
            raw_df = load_uploaded_data(uploaded_file)
            st.success(f"Arquivo carregado: {uploaded_file.name} ({len(raw_df)} registros)")
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
            return
    else:
        raw_df = generate_sample_data(n=20)
        st.info("Usando dados de exemplo. Carregue um arquivo CSV/Excel na barra lateral para análise real.")

    # Garante colunas mínimas
    if "title" not in raw_df.columns and "content" not in raw_df.columns:
        st.error("O arquivo deve conter pelo menos uma das colunas: 'title' ou 'content'.")
        return

    raw_df["title"] = raw_df.get("title", "")
    raw_df["content"] = raw_df.get("content", "")
    raw_df["source"] = raw_df.get("source", "N/D")
    raw_df["date"] = pd.to_datetime(raw_df.get("date", pd.NaT), errors="coerce")

    df = process_dataframe(raw_df)

    render_metrics(df)
    render_sentiment_analysis(df)
    render_wordcloud(df)
    render_news_comparator(df)
    render_data_table(df)
    render_export(df)


if __name__ == "__main__":
    main()
