import streamlit as st
import pandas as pd
import plotly.express as px
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional

st.set_page_config(page_title="Monitor de Enquadramento Midiático", layout="wide")


class TipoEnquadramento(Enum):
    CONFRONTO_DIRETO = "confronto_direto"
    NARRATIVA_GOVERNO = "narrativa_governo"
    NARRATIVA_OPOSICAO = "narrativa_oposicao"
    ANALISE_FATO = "analise_fato"
    AUSENCIA = "ausencia"


class Veiculo(Enum):
    G1 = "G1"
    FOLHA = "Folha de S.Paulo"
    ESTADAO = "Estadão"
    GLOBO = "Globo"
    RECORD = "Record"
    BAND = "Band"
    CNN = "CNN Brasil"
    JOVEM_PAN = "Jovem Pan"
    BR247 = "Brasil 247"
    REVISTA_F = "Revista Fórum"


class TipoMateria(Enum):
    NOTICIA = "noticia"
    ARTIGO = "artigo"
    EDITORIAL = "editorial"
    COLUNA = "coluna"
    VIDEO = "video"


class Situacao(Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"


@dataclass
class Coleta:
    id: int
    titulo: str
    veiculo: Veiculo
    tipo_materia: TipoMateria
    data_publicacao: datetime
    url: str
    coletor: str
    data_coleta: datetime = field(default_factory=datetime.now)
    situacao: Situacao = Situacao.PENDENTE


@dataclass
class Analise:
    coleta_id: int
    analista: str
    enquadramento: TipoEnquadramento
    justificativa: str
    pessoas: List[str] = field(default_factory=list)
    organizacoes: List[str] = field(default_factory=list)
    data_analise: datetime = field(default_factory=datetime.now)
    revisada: bool = False


class MonitorEnquadramento:
    def __init__(self):
        self.coletas: List[Coleta] = []
        self.analises: List[Analise] = []
        self.prox_id = 1

    def obter_label_enquadramento(self, tipo: TipoEnquadramento) -> str:
        labels = {
            TipoEnquadramento.CONFRONTO_DIRETO: "Confronto Direto",
            TipoEnquadramento.NARRATIVA_GOVERNO: "Narrativa Governo",
            TipoEnquadramento.NARRATIVA_OPOSICAO: "Narrativa Oposição",
            TipoEnquadramento.ANALISE_FATO: "Análise de Fato",
            TipoEnquadramento.AUSENCIA: "Ausência de Enquadramento",
        }
        return labels.get(tipo, tipo.value)

    def obter_label_tipo_materia(self, tipo: TipoMateria) -> str:
        labels = {
            TipoMateria.NOTICIA: "Notícia",
            TipoMateria.ARTIGO: "Artigo",
            TipoMateria.EDITORIAL: "Editorial",
            TipoMateria.COLUNA: "Coluna",
            TipoMateria.VIDEO: "Vídeo",
        }
        return labels.get(tipo, tipo.value)

    def obter_label_situacao(self, situacao: Situacao) -> str:
        labels = {
            Situacao.PENDENTE: "Pendente",
            Situacao.APROVADO: "Aprovado",
            Situacao.REPROVADO: "Reprovado",
        }
        return labels.get(situacao, situacao.value)

    def adicionar_coleta(self, titulo: str, veiculo: Veiculo, tipo_materia: TipoMateria, url: str, coletor: str) -> Coleta:
        coleta = Coleta(
            id=self.prox_id,
            titulo=titulo,
            veiculo=veiculo,
            tipo_materia=tipo_materia,
            data_publicacao=datetime.now(),
            url=url,
            coletor=coletor,
        )
        self.coletas.append(coleta)
        self.prox_id += 1
        return coleta

    def adicionar_analise(self, coleta_id: int, analista: str, enquadramento: TipoEnquadramento, justificativa: str, pessoas: List[str], organizacoes: List[str]) -> Analise:
        analise = Analise(
            coleta_id=coleta_id,
            analista=analista,
            enquadramento=enquadramento,
            justificativa=justificativa,
            pessoas=pessoas,
            organizacoes=organizacoes,
        )
        self.analises.append(analise)
        return analise

    def obter_analises_por_coleta(self, coleta_id: int) -> List[Analise]:
        return [a for a in self.analises if a.coleta_id == coleta_id]

    def obter_resumo(self) -> Dict:
        total_coletas = len(self.coletas)
        total_analises = len(self.analises)
        pendentes = len([c for c in self.coletas if c.situacao == Situacao.PENDENTE])
        aprovados = len([c for c in self.coletas if c.situacao == Situacao.APROVADO])
        reprovados = len([c for c in self.coletas if c.situacao == Situacao.REPROVADO])
        return {
            "total_coletas": total_coletas,
            "total_analises": total_analises,
            "pendentes": pendentes,
            "aprovados": aprovados,
            "reprovados": reprovados,
        }

    def obter_distribuicao_enquadramento(self) -> pd.DataFrame:
        if not self.analises:
            return pd.DataFrame(columns=["enquadramento", "quantidade"])
        dados = {}
        for analise in self.analises:
            label = self.obter_label_enquadramento(analise.enquadramento)
            dados[label] = dados.get(label, 0) + 1
        df = pd.DataFrame(list(dados.items()), columns=["enquadramento", "quantidade"])
        return df


@st.cache_resource
def get_monitor() -> MonitorEnquadramento:
    return MonitorEnquadramento()


def inicializar_dados(monitor: MonitorEnquadramento):
    if not monitor.coletas:
        monitor.adicionar_coleta(
            titulo="Governo anuncia novo pacote de medidas econômicas",
            veiculo=Veiculo.G1,
            tipo_materia=TipoMateria.NOTICIA,
            url="https://g1.globo.com/economia",
            coletor="sistema",
        )
        monitor.adicionar_coleta(
            titulo="Oposição critica gestão federal em debate na Câmara",
            veiculo=Veiculo.FOLHA,
            tipo_materia=TipoMateria.NOTICIA,
            url="https://folha.uol.com.br/poder",
            coletor="sistema",
        )
        monitor.adicionar_coleta(
            titulo="Análise: os números por trás da polêmica orçamentária",
            veiculo=Veiculo.ESTADAO,
            tipo_materia=TipoMateria.COLUNA,
            url="https://estadao.com.br/economia",
            coletor="sistema",
        )
        monitor.adicionar_coleta(
            titulo="Presidente e governador trocam acusações em evento",
            veiculo=Veiculo.GLOBO,
            tipo_materia=TipoMateria.VIDEO,
            url="https://globo.com/jornal",
            coletor="sistema",
        )

        for coleta in monitor.coletas:
            if coleta.id == 1:
                monitor.adicionar_analise(
                    coleta_id=coleta.id,
                    analista="sistema",
                    enquadramento=TipoEnquadramento.NARRATIVA_GOVERNO,
                    justificativa="Matéria reproduz discurso oficial sem contraposição.",
                    pessoas=["ministro da economia"],
                    organizacoes=["governo federal"],
                )
            elif coleta.id == 2:
                monitor.adicionar_analise(
                    coleta_id=coleta.id,
                    analista="sistema",
                    enquadramento=TipoEnquadramento.NARRATIVA_OPOSICAO,
                    justificativa="Foco exclusivo nas críticas da oposição.",
                    pessoas=["líder da oposição"],
                    organizacoes=["partido de oposição"],
                )
            elif coleta.id == 3:
                monitor.adicionar_analise(
                    coleta_id=coleta.id,
                    analista="sistema",
                    enquadramento=TipoEnquadramento.ANALISE_FATO,
                    justificativa="Apresenta dados e contexto sobre o tema.",
                    pessoas=["economista"],
                    organizacoes=["instituto de pesquisa"],
                )
            elif coleta.id == 4:
                monitor.adicionar_analise(
                    coleta_id=coleta.id,
                    analista="sistema",
                    enquadramento=TipoEnquadramento.CONFRONTO_DIRETO,
                    justificativa="Registro direto de embate entre autoridades.",
                    pessoas=["presidente", "governador"],
                    organizacoes=["governo federal", "governo estadual"],
                )

        for coleta in monitor.coletas:
            coleta.situacao = Situacao.APROVADO


def render_sidebar(monitor: MonitorEnquadramento):
    with st.sidebar:
        st.title("Monitor")
        st.markdown("---")
        menu = st.radio("Navegação", ["Dashboard", "Coletas", "Análises", "Nova Coleta", "Nova Análise"])
        st.markdown("---")
        resumo = monitor.obter_resumo()
        st.metric("Coletas", resumo["total_coletas"])
        st.metric("Análises", resumo["total_analises"])
        st.markdown("---")
        st.caption("Monitor de Enquadramento Midiático v1.0")
    return menu


def render_dashboard(monitor: MonitorEnquadramento):
    st.title("Dashboard")
    st.markdown("---")

    resumo = monitor.obter_resumo()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Coletas", resumo["total_coletas"])
    col2.metric("Total Análises", resumo["total_analises"])
    col3.metric("Pendentes", resumo["pendentes"])
    col4.metric("Aprovados", resumo["aprovados"])
    col5.metric("Reprovados", resumo["reprovados"])

    st.markdown("---")

    df_pie = monitor.obter_distribuicao_enquadramento()

    cores = {
        "Confronto Direto": "#FF6B6B",
        "Narrativa Governo": "#4ECDC4",
        "Narrativa Oposição": "#45B7D1",
        "Análise de Fato": "#96CEB4",
        "Ausência de Enquadramento": "#D3D3D3",
    }

    col_grafico, col_tabela = st.columns([2, 1])

    with col_grafico:
        if not df_pie.empty:
            fig = px.pie(
                df_pie,
                values="quantidade",
                names="enquadramento",
                title="Distribuição de Enquadramento",
                color="enquadramento",
                color_discrete_map=cores,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma análise disponível para exibir o gráfico.")

    with col_tabela:
        st.subheader("Resumo por Enquadramento")
        st.dataframe(df_pie, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Últimas Análises")
    if monitor.analises:
        analises_recentes = sorted(monitor.analises, key=lambda x: x.data_analise, reverse=True)[:10]
        dados = []
        for analise in analises_recentes:
            coleta = next((c for c in monitor.coletas if c.id == analise.coleta_id), None)
            if coleta:
                dados.append({
                    "Data": analise.data_analise.strftime("%d/%m/%Y %H:%M"),
                    "Veículo": coleta.veiculo.value,
                    "Título": coleta.titulo,
                    "Enquadramento": monitor.obter_label_enquadramento(analise.enquadramento),
                    "Analista": analise.analista,
                })
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma análise registrada.")


def render_coletas(monitor: MonitorEnquadramento):
    st.title("Coletas")
    st.markdown("---")

    if not monitor.coletas:
        st.info("Nenhuma coleta registrada.")
        return

    dados = []
    for coleta in monitor.coletas:
        dados.append({
            "ID": coleta.id,
            "Título": coleta.titulo,
            "Veículo": coleta.veiculo.value,
            "Tipo": monitor.obter_label_tipo_materia(coleta.tipo_materia),
            "Publicação": coleta.data_publicacao.strftime("%d/%m/%Y %H:%M"),
            "Coletor": coleta.coletor,
            "Situação": monitor.obter_label_situacao(coleta.situacao),
        })
    df = pd.DataFrame(dados)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_analises(monitor: MonitorEnquadramento):
    st.title("Análises")
    st.markdown("---")

    if not monitor.analises:
        st.info("Nenhuma análise registrada.")
        return

    dados = []
    for analise in monitor.analises:
        coleta = next((c for c in monitor.coletas if c.id == analise.coleta_id), None)
        if coleta:
            dados.append({
                "ID": analise.coleta_id,
                "Título": coleta.titulo,
                "Veículo": coleta.veiculo.value,
                "Enquadramento": monitor.obter_label_enquadramento(analise.enquadramento),
                "Analista": analise.analista,
                "Data Análise": analise.data_analise.strftime("%d/%m/%Y %H:%M"),
                "Revisada": "Sim" if analise.revisada else "Não",
            })
    df = pd.DataFrame(dados)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_nova_coleta(monitor: MonitorEnquadramento):
    st.title("Nova Coleta")
    st.markdown("---")

    with st.form("form_coleta"):
        titulo = st.text_input("Título")
        veiculo = st.selectbox("Veículo", [v for v in Veiculo])
        tipo_materia = st.selectbox("Tipo de Matéria", [t for t in TipoMateria])
        url = st.text_input("URL")
        coletor = st.text_input("Coletor", value="usuário")
        submit = st.form_submit_button("Salvar Coleta")

    if submit:
        if not titulo or not url or not coletor:
            st.error("Preencha todos os campos obrigatórios.")
        else:
            coleta = monitor.adicionar_coleta(titulo, veiculo, tipo_materia, url, coletor)
            st.success(f"Coleta {coleta.id} registrada com sucesso.")


def render_nova_analise(monitor: MonitorEnquadramento):
    st.title("Nova Análise")
    st.markdown("---")

    if not monitor.coletas:
        st.info("Nenhuma coleta disponível para análise.")
        return

    opcoes_coleta = {f"{c.id} - {c.titulo} ({c.veiculo.value})": c.id for c in monitor.coletas}

    with st.form("form_analise"):
        coleta_label = st.selectbox("Coleta", list(opcoes_coleta.keys()))
        coleta_id = opcoes_coleta[coleta_label]
        analista = st.text_input("Analista", value="usuário")
        enquadramento = st.selectbox("Enquadramento", [e for e in TipoEnquadramento])
        justificativa = st.text_area("Justificativa")
        pessoas = st.text_input("Pessoas mencionadas (separadas por vírgula)")
        organizacoes = st.text_input("Organizações mencionadas (separadas por vírgula)")
        submit = st.form_submit_button("Salvar Análise")

    if submit:
        if not analista or not justificativa:
            st.error("Preencha todos os campos obrigatórios.")
        else:
            lista_pessoas = [p.strip() for p in pessoas.split(",") if p.strip()]
            lista_org = [o.strip() for o in organizacoes.split(",") if o.strip()]
            analise = monitor.adicionar_analise(coleta_id, analista, enquadramento, justificativa, lista_pessoas, lista_org)
            coleta = next((c for c in monitor.coletas if c.id == coleta_id), None)
            if coleta:
                coleta.situacao = Situacao.APROVADO
            st.success(f"Análise da coleta {analise.coleta_id} registrada com sucesso.")


def main():
    monitor = get_monitor()
    inicializar_dados(monitor)
    menu = render_sidebar(monitor)

    if menu == "Dashboard":
        render_dashboard(monitor)
    elif menu == "Coletas":
        render_coletas(monitor)
    elif menu == "Análises":
        render_analises(monitor)
    elif menu == "Nova Coleta":
        render_nova_coleta(monitor)
    elif menu == "Nova Análise":
        render_nova_analise(monitor)


if __name__ == "__main__":
    main()
