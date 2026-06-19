import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from collections import Counter
import re
import urllib.parse

st.set_page_config(
    page_title="Monitor de Enquadramento Midiático",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

DICIONARIO_ENQUADRAMENTO = {
    "Econômico": [
        "economia", "mercado", "financeiro", "investimento", "bolsa", "empresas",
        "negócios", "lucro", "receita", "despesa", "inflação", "juros", "crescimento"
    ],
    "Político": [
        "governo", "política", "congresso", "senado", "câmara", "deputado", "senador",
        "ministro", "presidente", "eleição", "voto", "partido", "oposição", "aliança"
    ],
    "Social": [
        "sociedade", "população", "comunidade", "pessoas", "família", "trabalhadores",
        "saúde", "educação", "moradia", "desigualdade", "pobreza", "direitos"
    ],
    "Segurança": [
        "crime", "violência", "polícia", "segurança", "investigação", "prisão",
        "traficante", "roubo", "homicídio", "ordem pública", "forças armadas"
    ],
    "Ambiental": [
        "meio ambiente", "clima", "sustentabilidade", "amazônia", "desmatamento",
        "energia", "poluição", "recursos naturais", "biodiversidade", "aquecimento"
    ],
    "Judicial": [
        "justiça", "tribunal", "supremo", "stf", "processo", "julgamento", "direito",
        "constituição", "acusado", "testemunha", "advogado", "magistrado"
    ],
    "Internacional": [
        "exterior", "internacional", "relações exteriores", "diplomacia", "país",
        "estrangeiro", "global", "nações unidas", "ue", "oit", "fronteira"
    ]
}

EXEMPLOS_NOTICIAS = [
    {
        "id": 1,
        "data": datetime.now() - timedelta(days=1),
        "fonte":"" ,
        "manchete": "Governo anuncia cortes de gastos e aumento de investimentos em infraestrutura",
        "texto": "O governo federal anunciou nesta terça-feira um pacote de medidas econômicas que inclui corte de gastos e aumento de investimentos em infraestrutura. A iniciativa visa estimular o crescimento econômico e reduzir a inflação.",
        "url": "https://agenciabrasil.ebc.com.br/economia/noticia/2024-01/governo-anuncia-cortes-de-gastos",
        "tendencia": "Neutro"
    },
    {
        "id": 2,
        "data": datetime.now() - timedelta(days=3),
        "fonte": "Folha de S.Paulo",
        "manchete": "Congresso aprova projeto que amplia benefícios sociais em ano eleitoral",
        "texto": "O Congresso Nacional aprovou nesta quarta-feira um projeto de lei que amplia benefícios sociais. A oposição criticou a medida, afirmando que ela tem caráter eleitoreiro e pode afetar as contas públicas.",
        "url": "https://www1.folha.uol.com.br/poder/2024/01/congresso-aprova-beneficios-sociais.shtml",
        "tendencia": "Neutro"
    },
    {
        "id": 3,
        "data": datetime.now() - timedelta(days=6),
        "fonte": "GloboNews",
        "manchete": "Aumento da violência urbana preocupa moradores de grandes centros",
        "texto": "Dados recentes indicam crescimento da violência urbana em grandes centros. Especialistas apontam desigualdade social e falta de investimento em segurança pública como principais causas.",
        "url": "https://g1.globo.com/globonews/jornal-das-dez/violencia-urbana.html",
        "tendencia": "Negativo"
    },
    {
        "id": 4,
        "data": datetime.now() - timedelta(days=8),
        "fonte": "Valor Econômico",
        "manchete": "Mercado financeiro reage positivamente a sinais de estabilidade política",
        "texto": "O mercado financeiro reagiu de forma positiva nesta quinta-feira a sinais de estabilidade política. O Ibovespa subiu e o dólar recuou, refletindo o otimismo dos investidores.",
        "url": "https://valor.globo.com/financas/noticia/2024/01/mercado-reage-positivamente.ghtml",
        "tendencia": "Positivo"
    },
    {
        "id": 5,
        "data": datetime.now() - timedelta(days=12),
        "fonte": "O Globo",
        "manchete": "Desmatamento na Amazônia cai pelo terceiro mês consecutivo, mostram dados",
        "texto": "Dados oficiais mostram queda no desmatamento na Amazônia pelo terceiro mês consecutivo. Ambientalistas celebram a redução, mas alertam para a necessidade de políticas de longo prazo.",
        "url": "https://oglobo.globo.com/meio-ambiente/desmatamento-amazonia-cai.html",
        "tendencia": "Positivo"
    },
    {
        "id": 6,
        "data": datetime.now() - timedelta(days=25),
        "fonte": "Estadão",
        "manchete": "STF retoma julgamento sobre tributação de grandes fortunas",
        "texto": "O Supremo Tribunal Federal retomou nesta terça-feira o julgamento sobre a tributação de grandes fortunas. A decisão pode impactar a arrecadação e a distribuição de renda no país.",
        "url": "https://www.estadao.com.br/politica/stf-tributacao-grandes-fortunas.html",
        "tendencia": "Neutro"
    }
]


def calcular_enquadramento(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", " ", texto)
    tokens = texto.split()

    scores = {}
    for enquadramento, palavras in DICIONARIO_ENQUADRAMENTO.items():
        score = 0
        for palavra in palavras:
            if " " in palavra:
                score += texto.count(palavra)
            else:
                score += tokens.count(palavra)
        scores[enquadramento] = score

    total = sum(scores.values())
    if total == 0:
        scores["Neutro / Indeterminado"] = 1
        total = 1

    percentuais = {k: round(v / total * 100, 2) for k, v in scores.items()}
    principal = max(percentuais, key=percentuais.get)

    return percentuais, principal


def detectar_tendencia(texto):
    texto = texto.lower()
    positivas = ["crescimento", "aumento", "queda", "redução", "positivo", "sucesso", "avanço",
                 "melhora", "benefício", "ganho", "superávit", "recuperação", "estabilidade"]
    negativas = ["crise", "queda", "aumento", "violência", "preocupação", "problema", "escândalo",
                 "corrupção", "risco", "ameaça", "colapso", "recessão", "desigualdade", "desmatamento"]

    pos = sum(1 for p in positivas if p in texto)
    neg = sum(1 for n in negativas if n in texto)

    if pos > neg:
        return "Positivo"
    elif neg > pos:
        return "Negativo"
    return "Neutro"


@st.cache_data(ttl=3600)
def carregar_base_noticias():
    df = pd.DataFrame(EXEMPLOS_NOTICIAS)
    df["data"] = pd.to_datetime(df["data"]).dt.date
    return df


def extrair_enquadramentos_df(df):
    resultados = []
    for _, row in df.iterrows():
        percentuais, principal = calcular_enquadramento(row["texto"])
        resultados.append({
            "id": row["id"],
            "data": row["data"],
            "fonte": row["fonte"],
            "manchete": row["manchete"],
            "url": row["url"],
            "enquadramento_principal": principal,
            "tendencia": row["tendencia"],
            **{f"pct_{k}": v for k, v in percentuais.items()}
        })
    return pd.DataFrame(resultados)


def formatar_scorecard(percentuais, principal):
    linhas = []
    for k, v in sorted(percentuais.items(), key=lambda x: x[1], reverse=True):
        destaque = "➤ " if k == principal else "   "
        linhas.append(f"{destaque}{k}: {v}%")
    return "\n".join(linhas)


st.sidebar.title("📰 Monitor de Enquadramento Midiático")
st.sidebar.markdown("Análise comparativa de enquadramentos na imprensa brasileira.")

pagina = st.sidebar.radio("Navegação", ["Painel Principal", "Comparador de Notícias", "Notícias por Período"])

base_df = carregar_base_noticias()
analise_df = extrair_enquadramentos_df(base_df)

if pagina == "Painel Principal":
    st.title("Monitor de Enquadramento Midiático")
    st.markdown("**Metodologia inspirada em estudos de comunicação política e análise de mídia (FGV style).**")

    st.header("1. Fundamentação Teórica: O Que É Enquadramento Midiático?")
    st.markdown("""
    O **enquadramento midiático** (*media framing*) refere-se ao processo pelo qual a mídia seleciona,
    destaca e organiza informações de modo a construir uma determinada interpretação sobre um evento,
    problema ou ator social. Em vez de descrever a realidade de forma neutra, o enquadramento
    orienta a atenção do público para aspectos específicos, atribuindo causalidade, moralidade e
    responsabilidade.

    A teoria dos enquadramentos (*Framing Theory*) foi desenvolvida originalmente por Erving Goffman
    (1974) e posteriormente aplicada à comunicação e à ciência política por pesquisadores como
    Robert Entman (1993). De acordo com Entman, enquadrar uma notícia significa “selecionar alguns
    aspectos de uma percepção realidade percebida e torná-los mais salientes em uma mensagem de
    comunicação, de forma a promover uma definição particular do problema, interpretação causal,
    avaliação moral e/ou recomendação de tratamento”.

    No contexto brasileiro, o estudo de enquadramentos é fundamental para compreender como temas
    como economia, segurança pública, meio ambiente e política institucional são apresentados ao
    público. A análise de enquadramento permite identificar padrões de cobertura, tendências
    ideológicas, hierarquias de importância e possíveis vieses nos relatos jornalísticos.

    **Como este monitor funciona:**
    - Identifica a presença de palavras-chave associadas a sete enquadramentos clássicos.
    - Calcula a distribuição percentual de cada enquadramento no texto.
    - Determina o enquadramento dominante e a tendência do tom da notícia.
    - Oferece visualização comparativa entre múltiplas fontes e períodos.
    """)

    st.header("2. Distribuição Geral de Enquadramentos na Base")
    col1, col2 = st.columns(2)

    with col1:
        contagem = analise_df["enquadramento_principal"].value_counts().reset_index()
        contagem.columns = ["Enquadramento", "Quantidade"]
        fig = px.bar(
            contagem,
            x="Enquadramento",
            y="Quantidade",
            color="Enquadramento",
            title="Enquadramentos Principais na Base",
            text="Quantidade",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        tendencia = analise_df["tendencia"].value_counts().reset_index()
        tendencia.columns = ["Tendência", "Quantidade"]
        fig2 = px.pie(
            tendencia,
            values="Quantidade",
            names="Tendência",
            title="Distribuição de Tendência das Notícias",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.header("3. Evolução Temporal dos Enquadramentos")
    evolucao = analise_df.groupby(["data", "enquadramento_principal"]).size().reset_index(name="quantidade")
    fig3 = px.line(
        evolucao,
        x="data",
        y="quantidade",
        color="enquadramento_principal",
        markers=True,
        title="Evolução dos Enquadramentos ao Longo do Tempo",
        labels={"data": "Data", "quantidade": "Quantidade", "enquadramento_principal": "Enquadramento"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig3.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig3, use_container_width=True)

    st.header("4. Tabela Resumida de Notícias Analisadas")
    st.dataframe(
        analise_df[["data", "fonte", "manchete", "enquadramento_principal", "tendencia"]].sort_values("data", ascending=False),
        use_container_width=True,
        hide_index=True
    )

elif pagina == "Comparador de Notícias":
    st.title("Comparador de Enquadramentos entre Duas Notícias")
    st.markdown("Insira as URLs e os textos/manchetes de duas notícias para comparar seus enquadramentos.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Notícia A")
        url_a = st.text_input("URL da Notícia A", value="https://exemplo.com/noticia-a", key="url_a")
        manchete_a = st.text_input("Manchete A", value="Governo anuncia medidas econômicas para conter inflação", key="manchete_a")
        texto_a = st.text_area("Texto A", value="""O governo anunciou novas medidas econômicas para conter a inflação e estimular o crescimento do mercado. Empresários e investidores reagiram de forma positiva às medidas, que incluem corte de juros e redução de impostos para setores estratégicos.""", key="texto_a", height=200)

    with col2:
        st.subheader("Notícia B")
        url_b = st.text_input("URL da Notícia B", value="https://exemplo.com/noticia-b", key="url_b")
        manchete_b = st.text_input("Manchete B", value="Especialistas questionam impacto social das medidas econômicas do governo", key="manchete_b")
        texto_b = st.text_area("Texto B", value="""Especialistas em políticas sociais questionam o impacto das medidas econômicas anunciadas pelo governo. Segundo analistas, a redução de impostos pode beneficiar grandes empresas enquanto trabalhadores e famílias de baixa renda terão pouco ganho real.""", key="texto_b", height=200)

    if st.button("Comparar Enquadramentos", type="primary"):
        texto_completo_a = f"{manchete_a} {texto_a}"
        texto_completo_b = f"{manchete_b} {texto_b}"

        percentuais_a, principal_a = calcular_enquadramento(texto_completo_a)
        percentuais_b, principal_b = calcular_enquadramento(texto_completo_b)
        tendencia_a = detectar_tendencia(texto_completo_a)
        tendencia_b = detectar_tendencia(texto_completo_b)

        st.divider()

        col_res_a, col_res_b = st.columns(2)

        with col_res_a:
            st.markdown("### Notícia A")
            st.markdown(f"**URL:** [{url_a}]({url_a})")
            st.markdown(f"**Manchete:** {manchete_a}")
            st.markdown(f"**Enquadramento dominante:** `{principal_a}`")
            st.markdown(f"**Tendência:** `{tendencia_a}`")
            st.markdown("**Distribuição de scores:**")
            st.text(formatar_scorecard(percentuais_a, principal_a))

        with col_res_b:
            st.markdown("### Notícia B")
            st.markdown(f"**URL:** [{url_b}]({url_b})")
            st.markdown(f"**Manchete:** {manchete_b}")
            st.markdown(f"**Enquadramento dominante:** `{principal_b}`")
            st.markdown(f"**Tendência:** `{tendencia_b}`")
            st.markdown("**Distribuição de scores:**")
            st.text(formatar_scorecard(percentuais_b, principal_b))

        st.markdown("### Comparação Visual Lado a Lado")

        categorias = list(DICIONARIO_ENQUADRAMENTO.keys())
        valores_a = [percentuais_a.get(c, 0) for c in categorias]
        valores_b = [percentuais_b.get(c, 0) for c in categorias]

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            x=categorias,
            y=valores_a,
            name="Notícia A",
            marker_color="#1f77b4"
        ))
        fig_comp.add_trace(go.Bar(
            x=categorias,
            y=valores_b,
            name="Notícia B",
            marker_color="#ff7f0e"
        ))
        fig_comp.update_layout(
            barmode="group",
            title="Comparação de Enquadramentos (%)",
            xaxis_title="Enquadramento",
            yaxis_title="Percentual",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("### Análise Comparativa")
        st.markdown(f"""
        - A **Notícia A** ({url_a}) é predominantemente enquadrada como **`{principal_a}`**, com tendência **`{tendencia_a}`**.
        - A **Notícia B** ({url_b}) é predominantemente enquadrada como **`{principal_b}`**, com tendência **`{tendencia_b}`**.
        - Diferença de enquadramento principal: **{'Mesmo enquadramento' if principal_a == principal_b else 'Enquadramentos distintos'}**.
        """)

elif pagina == "Notícias por Período":
    st.title("Notícias Filtradas por Período")
    st.markdown("Visualize notícias e seus enquadramentos filtradas por semana, mês ou todo o período disponível.")

    abas = st.tabs(["Semana", "Mês", "Geral"])
    hoje = datetime.now().date()

    with abas[0]:
        inicio_semana = hoje - timedelta(days=7)
        df_semana = analise_df[analise_df["data"] >= inicio_semana]
        st.markdown(f"**Período:** {inicio_semana} a {hoje}")
        st.markdown(f"**Total de notícias:** {len(df_semana)}")

        if not df_semana.empty:
            contagem_semana = df_semana["enquadramento_principal"].value_counts().reset_index()
            contagem_semana.columns = ["Enquadramento", "Quantidade"]
            fig_s = px.bar(
                contagem_semana,
                x="Enquadramento",
                y="Quantidade",
                color="Enquadramento",
                title="Enquadramentos Principais na Semana",
                text="Quantidade",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_s.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig_s, use_container_width=True)
            st.dataframe(df_semana[["data", "fonte", "manchete", "enquadramento_principal", "tendencia"]].sort_values("data", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma notícia disponível para a semana selecionada.")

    with abas[1]:
        inicio_mes = hoje - timedelta(days=30)
        df_mes = analise_df[analise_df["data"] >= inicio_mes]
        st.markdown(f"**Período:** {inicio_mes} a {hoje}")
        st.markdown(f"**Total de notícias:** {len(df_mes)}")

        if not df_mes.empty:
            contagem_mes = df_mes["enquadramento_principal"].value_counts().reset_index()
            contagem_mes.columns = ["Enquadramento", "Quantidade"]
            fig_m = px.bar(
                contagem_mes,
                x="Enquadramento",
                y="Quantidade",
                color="Enquadramento",
                title="Enquadramentos Principais no Mês",
                text="Quantidade",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_m.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig_m, use_container_width=True)
            st.dataframe(df_mes[["data", "fonte", "manchete", "enquadramento_principal", "tendencia"]].sort_values("data", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma notícia disponível para o mês selecionado.")

    with abas[2]:
        st.markdown("**Período:** Todo o período disponível")
        st.markdown(f"**Total de notícias:** {len(analise_df)}")

        contagem_geral = analise_df["enquadramento_principal"].value_counts().reset_index()
        contagem_geral.columns = ["Enquadramento", "Quantidade"]
        fig_g = px.bar(
            contagem_geral,
            x="Enquadramento",
            y="Quantidade",
            color="Enquadramento",
            title="Enquadramentos Principais no Período Geral",
            text="Quantidade",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_g.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_g, use_container_width=True)

        st.dataframe(analise_df[["data", "fonte", "manchete", "enquadramento_principal", "tendencia"]].sort_values("data", ascending=False), use_container_width=True, hide_index=True)

st.sidebar.markdown("---")
st.sidebar.markdown("Desenvolvido para fins educacionais e de pesquisa em comunicação política.")
