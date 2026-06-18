import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re

st.set_page_config(
    page_title="Monitor de Enquadramento Midiático",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TipoEnquadramento(Enum):
    POSITIVO = "positivo"
    NEUTRO = "neutro"
    NEGATIVO = "negativo"
    CRISIS = "crisis"
    OPORTUNIDADE = "oportunidade"

class VeiculoTipo(Enum):
    ONLINE = "online"
    IMPRESSO = "impresso"
    TV = "tv"
    RADIO = "radio"
    REDES_SOCIAIS = "redes_sociais"
    PODCAST = "podcast"

@dataclass
class Veiculo:
    nome: str
    tipo: VeiculoTipo
    alcance_estimado: int
    credibilidade: float
    url: Optional[str] = None

@dataclass
class Materia:
    id: str
    titulo: str
    veiculo: str
    data_publicacao: datetime
    url: Optional[str]
    resumo: str
    citacoes_diretas: List[str]
    enquadramento_principal: TipoEnquadramento
    enquadramentos_secundarios: List[TipoEnquadramento]
    temas: List[str]
    autor: Optional[str]
    alcance_estimado: int
    engajamento: int
    verificado: bool

@dataclass
class ReputacaoSnapshot:
    data: datetime
    score_positivo: float
    score_negativo: float
    score_crisis: float
    score_oportunidade: float
    volume_total: int

class DicionarioEnquadramento:
    def __init__(self):
        self.palavras_positivas = [
            "excelente", "ótimo", "inovação", "crescimento", "expansão", "sucesso",
            "lucro", "avanço", "conquista", "premiação", "reconhecimento", "qualidade",
            "líder", "referência", "sustentabilidade", "inclusão", "diversidade", "parceria",
            "benefício", "vantagem", "melhoria", "superação", "eficiência", "destaque"
        ]
        self.palavras_negativas = [
            "crise", "problema", "queda", "prejuízo", "demissão", "escândalo", "falha",
            "fraude", "corrupção", "polêmica", "controvérsia", "crítica", "reclamação",
            "suspeita", "investigação", "sancionado", "condenado", "devassa", "preocupação"
        ]
        self.palavras_crisis = [
            "tragédia", "acidente", "morte", "fatalidade", "vítima", "emergência",
            "desastre", "catástrofe", "colapso", "pânico", "alerta", "evacuação",
            "risco iminente", "ameaça", "ataque", "violência", "caso grave", "urgência"
        ]
        self.palavras_oportunidade = [
            "oportunidade", "potencial", "mercado em alta", "tendência", "disrupção",
            "novo nicho", "lançamento", "investimento", "aquisição", "fusão", "ipo",
            "expansão internacional", "digitalização", "transformação", "edge", "vantagem competitiva"
        ]
    
    def detectar(self, texto: str) -> Dict[TipoEnquadramento, float]:
        texto_lower = texto.lower()
        scores = {
            TipoEnquadramento.POSITIVO: 0.0,
            TipoEnquadramento.NEGATIVO: 0.0,
            TipoEnquadramento.CRISIS: 0.0,
            TipoEnquadramento.OPORTUNIDADE: 0.0
        }
        
        for palavra in self.palavras_positivas:
            scores[TipoEnquadramento.POSITIVO] += len(re.findall(r'\b' + re.escape(palavra) + r'\b', texto_lower))
        for palavra in self.palavras_negativas:
            scores[TipoEnquadramento.NEGATIVO] += len(re.findall(r'\b' + re.escape(palavra) + r'\b', texto_lower))
        for palavra in self.palavras_crisis:
            scores[TipoEnquadramento.CRISIS] += len(re.findall(r'\b' + re.escape(palavra) + r'\b', texto_lower))
        for palavra in self.palavras_oportunidade:
            scores[TipoEnquadramento.OPORTUNIDADE] += len(re.findall(r'\b' + re.escape(palavra) + r'\b', texto_lower))
        
        total = sum(scores.values())
        if total > 0:
            for key in scores:
                scores[key] /= total
        
        return scores

class MonitorEnquadramento:
    def __init__(self, nome_cliente: str = "Cliente"):
        self.nome_cliente = nome_cliente
        self.veiculos: List[Veiculo] = []
        self.materias: List[Materia] = []
        self.dicionario = DicionarioEnquadramento()
        self.historico_reputacao: List[ReputacaoSnapshot] = []
    
    def adicionar_veiculo(self, veiculo: Veiculo) -> None:
        self.veiculos.append(veiculo)
    
    def remover_veiculo(self, nome: str) -> bool:
        for i, v in enumerate(self.veiculos):
            if v.nome == nome:
                del self.veiculos[i]
                return True
        return False
    
    def adicionar_materia(self, materia: Materia) -> None:
        self.materias.append(materia)
    
    def analisar_enquadramento(self, texto: str) -> Tuple[TipoEnquadramento, Dict[TipoEnquadramento, float]]:
        scores = self.dicionario.detectar(texto)
        principal = max(scores, key=scores.get)
        if scores[principal] == 0:
            principal = TipoEnquadramento.NEUTRO
        return principal, scores
    
    def classificar_materia(self, materia: Materia) -> Dict[str, any]:
        texto_completo = f"{materia.titulo} {materia.resumo} {' '.join(materia.citacoes_diretas)}"
        principal, scores = self.analisar_enquadramento(texto_completo)
        
        secundarios = []
        for tipo, score in scores.items():
            if tipo != principal and score > 0.15:
                secundarios.append(tipo)
        
        materia.enquadramento_principal = principal
        materia.enquadramentos_secundarios = secundarios
        
        return {
            "materia": materia,
            "scores": scores,
            "confianca": scores[principal]
        }
    
    def classificar_todas(self) -> List[Dict[str, any]]:
        resultados = []
        for materia in self.materias:
            resultados.append(self.classificar_materia(materia))
        return resultados
    
    def calcular_reputacao(self, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None) -> ReputacaoSnapshot:
        materias_filtradas = self.materias
        if data_inicio and data_fim:
            materias_filtradas = [m for m in self.materias if data_inicio <= m.data_publicacao <= data_fim]
        
        total = len(materias_filtradas) if materias_filtradas else 1
        
        positivo = sum(1 for m in materias_filtradas if m.enquadramento_principal == TipoEnquadramento.POSITIVO)
        negativo = sum(1 for m in materias_filtradas if m.enquadramento_principal == TipoEnquadramento.NEGATIVO)
        crisis = sum(1 for m in materias_filtradas if m.enquadramento_principal == TipoEnquadramento.CRISIS)
        oportunidade = sum(1 for m in materias_filtradas if m.enquadramento_principal == TipoEnquadramento.OPORTUNIDADE)
        
        return ReputacaoSnapshot(
            data=datetime.now(),
            score_positivo=round(positivo / total * 100, 2),
            score_negativo=round(negativo / total * 100, 2),
            score_crisis=round(crisis / total * 100, 2),
            score_oportunidade=round(oportunidade / total * 100, 2),
            volume_total=len(materias_filtradas)
        )
    
    def materias_por_enquadramento(self, tipo: TipoEnquadramento) -> List[Materia]:
        return [m for m in self.materias if m.enquadramento_principal == tipo]
    
    def tendencia_temporal(self, dias: int = 30) -> pd.DataFrame:
        hoje = datetime.now()
        inicio = hoje - timedelta(days=dias)
        
        dados = []
        for d in range(dias + 1):
            dia = inicio + timedelta(days=d)
            materias_dia = [m for m in self.materias if m.data_publicacao.date() == dia.date()]
            
            positivo = sum(1 for m in materias_dia if m.enquadramento_principal == TipoEnquadramento.POSITIVO)
            negativo = sum(1 for m in materias_dia if m.enquadramento_principal == TipoEnquadramento.NEGATIVO)
            neutro = sum(1 for m in materias_dia if m.enquadramento_principal == TipoEnquadramento.NEUTRO)
            crisis = sum(1 for m in materias_dia if m.enquadramento_principal == TipoEnquadramento.CRISIS)
            oportunidade = sum(1 for m in materias_dia if m.enquadramento_principal == TipoEnquadramento.OPORTUNIDADE)
            
            dados.append({
                "data": dia.strftime("%d/%m/%Y"),
                "Positivo": positivo,
                "Negativo": negativo,
                "Neutro": neutro,
                "Crisis": crisis,
                "Oportunidade": oportunidade,
                "Total": len(materias_dia)
            })
        
        return pd.DataFrame(dados)
    
    def exportar_json(self, caminho: str) -> None:
        dados = {
            "nome_cliente": self.nome_cliente,
            "veiculos": [asdict(v) for v in self.veiculos],
            "materias": [self._materia_para_dict(m) for m in self.materias]
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2, default=str)
    
    def _materia_para_dict(self, materia: Materia) -> dict:
        return {
            "id": materia.id,
            "titulo": materia.titulo,
            "veiculo": materia.veiculo,
            "data_publicacao": materia.data_publicacao.isoformat(),
            "url": materia.url,
            "resumo": materia.resumo,
            "citacoes_diretas": materia.citacoes_diretas,
            "enquadramento_principal": materia.enquadramento_principal.value,
            "enquadramentos_secundarios": [e.value for e in materia.enquadramentos_secundarios],
            "temas": materia.temas,
            "autor": materia.autor,
            "alcance_estimado": materia.alcance_estimado,
            "engajamento": materia.engajamento,
            "verificado": materia.verificado
        }

DADOS_DEMO = {
    "veiculos": [
        Veiculo("Folha de S.Paulo", VeiculoTipo.IMPRESSO, 800000, 0.88, "https://www1.folha.uol.com.br"),
        Veiculo("Estadão", VeiculoTipo.IMPRESSO, 650000, 0.86, "https://www.estadao.com.br"),
        Veiculo("Globo", VeiculoTipo.TV, 12000000, 0.82, "https://www.globo.com"),
        Veiculo("Record", VeiculoTipo.TV, 9000000, 0.78, "https://www.recordtv.com.br"),
        Veiculo("G1", VeiculoTipo.ONLINE, 15000000, 0.84, "https://g1.globo.com"),
        Veiculo("UOL", VeiculoTipo.ONLINE, 12000000, 0.80, "https://www.uol.com.br"),
        Veiculo("Twitter/X", VeiculoTipo.REDES_SOCIAIS, 50000000, 0.45, "https://twitter.com"),
        Veiculo("LinkedIn", VeiculoTipo.REDES_SOCIAIS, 15000000, 0.60, "https://www.linkedin.com"),
        Veiculo("Spotify Podcasts", VeiculoTipo.PODCAST, 8000000, 0.55, "https://open.spotify.com"),
        Veiculo("Rádio Bandeirantes", VeiculoTipo.RADIO, 2500000, 0.72, "https://www.bandnewsfm.com.br")
    ],
    "materias": [
        {
            "titulo": "Empresa anuncia expansão internacional e cria 500 novos empregos",
            "veiculo": "Folha de S.Paulo",
            "dias_atras": 2,
            "resumo": "A empresa apresentou resultados excelentes no último trimestre e anunciou a conquista de novos mercados na Europa, destacando a inovação dos seus produtos e o compromisso com a sustentabilidade.",
            "citacoes": ["Este é um marco histórico para a companhia", "A expansão reflete nossa liderança no setor"],
            "temas": ["expansão", "empregos", "sustentabilidade"],
            "alcance": 450000,
            "engajamento": 12000
        },
        {
            "titulo": "Produto inovador da empresa é reconhecido com prêmio internacional de qualidade",
            "veiculo": "G1",
            "dias_atras": 5,
            "resumo": "Referência em inovação, a empresa conquistou uma premiação importante no exterior, reconhecendo a melhoria contínua e a eficiência de sua nova linha de produtos.",
            "citacoes": ["O prêmio consolida nossa posição entre os líderes globais"],
            "temas": ["inovação", "premiação", "qualidade"],
            "alcance": 890000,
            "engajamento": 34000
        },
        {
            "titulo": "Empresa enfrenta investigação por suposta fraude em contratos públicos",
            "veiculo": "Estadão",
            "dias_atras": 1,
            "resumo": "Uma polêmica investigação aponta suspeita de corrupção e irregularidades em contratos. A empresa foi duramente criticada e enfrenta risco de sanções e queda de credibilidade.",
            "citacoes": ["Estamos preocupados com as alegações", "A empresa colaborará com as autoridades"],
            "temas": ["investigação", "fraude", "contratos"],
            "alcance": 720000,
            "engajamento": 56000
        },
        {
            "titulo": "Acidente grave em unidade industrial deixa vítimas e gera alerta de emergência",
            "veiculo": "Globo",
            "dias_atras": 0,
            "resumo": "Uma tragédia na fábrica da empresa resultou em vítimas fatais e colapso parcial da estrutura. Autoridades decretaram estado de emergência e evacuaram a área.",
            "citacoes": ["É uma catástrofe para a comunidade", "As equipes de resgate estão em campo"],
            "temas": ["acidente", "segurança", "emergência"],
            "alcance": 15000000,
            "engajamento": 180000
        },
        {
            "titulo": "Mercado em alta: empresa identifica oportunidade em novo nicho de digitalização",
            "veiculo": "LinkedIn",
            "dias_atras": 3,
            "resumo": "Análise de tendências aponta potencial de crescimento para a empresa em um novo nicho de digitalização e transformação dos serviços, com vantagem competitiva em relação aos concorrentes.",
            "citacoes": ["A digitalização abre um campo de oportunidades", "Estamos prontos para liderar essa tendência"],
            "temas": ["digitalização", "tendências", "mercado"],
            "alcance": 320000,
            "engajamento": 8900
        },
        {
            "titulo": "Resultados trimestrais da empresa superam expectativas e impulsionam ações",
            "veiculo": "UOL",
            "dias_atras": 7,
            "resumo": "A empresa divulgou lucro acima do esperado, com crescimento de receita e eficiência operacional. Especialistas destacam a superação das metas e o avanço das estratégias.",
            "citacoes": ["Os números refletem a força do modelo de negócio", "Investidores reagiram positivamente"],
            "temas": ["resultados", "lucro", "ações"],
            "alcance": 610000,
            "engajamento": 21000
        },
        {
            "titulo": "Reclamações de consumidores sobre atendimento crescem nas redes sociais",
            "veiculo": "Twitter/X",
            "dias_atras": 4,
            "resumo": "Usuários relatam problemas no atendimento e falha no suporte ao cliente, gerando críticas e preocupação com a perda de qualidade nos serviços prestados.",
            "citacoes": ["Estou insatisfeito com o atendimento", "A empresa precisa melhorar o suporte"],
            "temas": ["atendimento", "reclamação", "redes sociais"],
            "alcance": 1200000,
            "engajamento": 95000
        },
        {
            "titulo": "Empresa firma parceria estratégica para impulsionar inclusão e diversidade",
            "veiculo": "Rádio Bandeirantes",
            "dias_atras": 6,
            "resumo": "A iniciativa promove a inclusão de grupos sub-representados e fortalece a diversidade nas equipes, reconhecida como um benefício para a cultura organizacional e a inovação.",
            "citacoes": ["A diversidade é um pilar da nossa estratégia", "A parceria ampliará nosso impacto social"],
            "temas": ["inclusão", "diversidade", "parceria"],
            "alcance": 180000,
            "engajamento": 4500
        },
        {
            "titulo": "Podcast discute oportunidades de fusão e aquisição no setor",
            "veiculo": "Spotify Podcasts",
            "dias_atras": 8,
            "resumo": "Especialistas comentam a disrupção no mercado e o potencial de aquisições estratégicas, apontando a empresa como candidata a liderar movimentos de consolidação.",
            "citacoes": ["Uma aquisição pode acelerar a transformação", "A empresa está bem posicionada para movimentos estratégicos"],
            "temas": ["fusão", "aquisição", "podcast"],
            "alcance": 250000,
            "engajamento": 7800
        },
        {
            "titulo": "Empresa anuncia nova sede corporativa em região estratégica",
            "veiculo": "Record",
            "dias_atras": 9,
            "resumo": "A construção da nova sede representa investimento e expansão das operações, trazendo benefícios para a economia local e melhoria da infraestrutura corporativa.",
            "citacoes": ["A nova sede reflete nosso crescimento sustentável", "Investimos na excelência operacional"],
            "temas": ["expansão", "infraestrutura", "investimento"],
            "alcance": 540000,
            "engajamento": 15000
        }
    ]
}

def gerar_id_materia(titulo: str, veiculo: str, data: datetime) -> str:
    hash_str = f"{titulo}{veiculo}{data.isoformat()}"
    return hashlib.md5(hash_str.encode("utf-8")).hexdigest()[:12]

def inicializar_monitor() -> MonitorEnquadramento:
    if "monitor" not in st.session_state:
        st.session_state.monitor = criar_monitor_demo()
    return st.session_state.monitor

def criar_monitor_demo() -> MonitorEnquadramento:
    monitor = MonitorEnquadramento("Cliente Demo")
    
    for veiculo in DADOS_DEMO["veiculos"]:
        monitor.adicionar_veiculo(veiculo)
    
    for item in DADOS_DEMO["materias"]:
        data = datetime.now() - timedelta(days=item["dias_atras"])
        materia = Materia(
            id=gerar_id_materia(item["titulo"], item["veiculo"], data),
            titulo=item["titulo"],
            veiculo=item["veiculo"],
            data_publicacao=data,
            url=None,
            resumo=item["resumo"],
            citacoes_diretas=item["citacoes"],
            enquadramento_principal=TipoEnquadramento.NEUTRO,
            enquadramentos_secundarios=[],
            temas=item["temas"],
            autor=None,
            alcance_estimado=item["alcance"],
            engajamento=item["engajamento"],
            verificado=False
        )
        monitor.adicionar_materia(materia)
    
    monitor.classificar_todas()
    return monitor

def obter_cor_enquadramento(tipo: TipoEnquadramento) -> str:
    cores = {
        TipoEnquadramento.POSITIVO: "#2ecc71",
        TipoEnquadramento.NEUTRO: "#95a5a6",
        TipoEnquadramento.NEGATIVO: "#e74c3c",
        TipoEnquadramento.CRISIS: "#8e44ad",
        TipoEnquadramento.OPORTUNIDADE: "#3498db"
    }
    return cores.get(tipo, "#95a5a6")

def obter_label_enquadramento(tipo: TipoEnquadramento) -> str:
    labels = {
        TipoEnquadramento.POSITIVO: "Positivo",
        TipoEnquadramento.NEUTRO: "Neutro",
        TipoEnquadramento.NEGATIVO: "Negativo",
        TipoEnquadramento.CRISIS: "Crisis",
        TipoEnquadramento.OPORTUNIDADE: "Oportunidade"
    }
    return labels.get(tipo, tipo.value)

def render_sidebar(monitor: MonitorEnquadramento):
    with st.sidebar:
        st.title("📊 Monitor de Enquadramento")
        st.markdown(f"**Cliente:** {monitor.nome_cliente}")
        st.markdown("---")
        
        menu = st.radio(
            "Navegação",
            ["Dashboard", "Matérias", "Veículos", "Análise de Texto", "Configurações"]
        )
        
        st.markdown("---")
        st.markdown("**Filtros Rápidos**")
        
        filtro_tipo = st.multiselect(
            "Tipos de Enquadramento",
            options=[t for t in TipoEnquadramento],
            format_func=lambda x: obter_label_enquadramento(x),
            default=[]
        )
        
        filtro_dias = st.slider("Últimos dias", 1, 90, 30)
        
        st.session_state.filtro_tipo = filtro_tipo
        st.session_state.filtro_dias = filtro_dias
        st.session_state.menu = menu

def render_dashboard(monitor: MonitorEnquadramento):
    st.title("Dashboard de Enquadramento Midiático")
    
    dias = st.session_state.get("filtro_dias", 30)
    data_inicio = datetime.now() - timedelta(days=dias)
    data_fim = datetime.now()
    
    materias_filtradas = [
        m for m in monitor.materias
        if data_inicio <= m.data_publicacao <= data_fim
    ]
    
    snapshot = monitor.calcular_reputacao(data_inicio, data_fim)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Positivo", f"{snapshot.score_positivo}%", f"{snapshot.score_positivo - 0:.1f}%")
    with col2:
        st.metric("Negativo", f"{snapshot.score_negativo}%", f"{snapshot.score_negativo - 0:.1f}%", delta_color="inverse")
    with col3:
        st.metric("Crisis", f"{snapshot.score_crisis}%", delta_color="inverse")
    with col4:
        st.metric("Oportunidade", f"{snapshot.score_oportunidade}%")
    with col5:
        st.metric("Volume Total", snapshot.volume_total)
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Distribuição de Enquadramento")
        
        contagem = {}
        for m in materias_filtradas:
            contagem[m.enquadramento_principal] = contagem.get(m.enquadramento_principal, 0) + 1
        
        df_pie = pd.DataFrame([
            {"Enquadramento": obter_label_enquadramento(t), "Quantidade": q, "Tipo": t}
            for t, q in contagem.items()
        ])
        
        if not df_pie.empty:
            fig_pie = px.pie(
                df_pie,
                values="Quantidade",
                names="Enquadramento",
                color="Tipo",
                color_discrete_map={
                    TipoEnquadramento.POSITIVO: obter_cor_enquadramento(TipoEnquadramento.POSITIVO),
                    TipoEnquadramento.NEGATIVO: obter_cor_enquadramento(TipoEnquadramento.NEGATIVO),
                    TipoEnquadramento.NEUTRO: obter_cor_enquadramento(TipoEnquadramento.NEUTRO),
                    TipoEnquadramento.CRISIS: obter_cor_enquadramento(TipoEnquadramento.CRISIS),
                    TipoEnquadramento.OPORTUNIDADE: obter_cor_enquadramento(TipoEnquadramento.OPORTUNIDADE)
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nenhuma matéria no período selecionado.")
    
    with col_chart2:
        st.subheader("Tendência Temporal")
        df_tendencia = monitor.tendencia_temporal(dias)
        
        fig_line = go.Figure()
        for coluna, cor, nome in [
            ("Positivo", obter_cor_enquadramento(TipoEnquadramento.POSITIVO), "Positivo"),
            ("Negativo", obter_cor_enquadramento(TipoEnquadramento.NEGATIVO), "Negativo"),
            ("Crisis", obter_cor_enquadramento(TipoEnquadramento.CRISIS), "Crisis"),
            ("Oportunidade", obter_cor_enquadramento(TipoEnquadramento.OPORTUNIDADE), "Oportunidade"),
            ("Neutro", obter_cor_enquadramento(TipoEnquadramento.NEUTRO), "Neutro")
        ]:
            fig_line.add_trace(go.Scatter(
                x=df_tendencia["data"],
                y=df_tendencia[coluna],
                mode="lines+markers",
                name=nome,
                line=dict(color=cor)
            ))
        
        fig_line.update_layout(
            xaxis_title="Data",
            yaxis_title="Quantidade de Matérias",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Últimas Matérias Relevantes")
    
    materias_ordenadas = sorted(materias_filtradas, key=lambda m: m.data_publicacao, reverse=True)
    
    for materia in materias_ordenadas[:5]:
        with st.expander(f"{materia.titulo} - {obter_label_enquadramento(materia.enquadramento_principal)}"):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**Veículo:** {materia.veiculo}")
                st.markdown(f"**Data:** {materia.data_publicacao.strftime('%d/%m/%Y')}")
                st.markdown(f"**Resumo:** {materia.resumo}")
                if materia.citacoes_diretas:
                    st.markdown("**Citações:**")
                    for citacao in materia.citacoes_diretas:
                        st.markdown(f"> {citacao}")
            with col_b:
                st.markdown(f"**Alcance:** {materia.alcance_estimado:,}")
                st.markdown(f"**Engajamento:** {materia.engajamento:,}")
                st.markdown(f"**Temas:** {', '.join(materia.temas)}")
                st.markdown(f"**Verificado:** {'Sim' if materia.verificado else 'Não'}")

def render_materias(monitor: MonitorEnquadramento):
    st.title("Gerenciamento de Matérias")
    
    dias = st.session_state.get("filtro_dias", 30)
    filtro_tipos = st.session_state.get("filtro_tipo", [])
    
    data_inicio = datetime.now() - timedelta(days=dias)
    data_fim = datetime.now()
    
    materias_filtradas = [
        m for m in monitor.materias
        if data_inicio <= m.data_publicacao <= data_fim
        and (not filtro_tipos or m.enquadramento_principal in filtro_tipos)
    ]
    
    st.subheader(f"Total: {len(materias_filtradas)} matérias")
    
    if not materias_filtradas:
        st.info("Nenhuma matéria encontrada com os filtros atuais.")
        return
    
    dados_tabela = []
    for m in materias_filtradas:
        dados_tabela.append({
            "Data": m.data_publicacao.strftime("%d/%m/%Y"),
            "Veículo": m.veiculo,
            "Título": m.titulo,
            "Enquadramento": obter_label_enquadramento(m.enquadramento_principal),
            "Alcance": m.alcance_estimado,
            "Engajamento": m.engajamento,
            "Verificado": "Sim" if m.verificado else "Não"
        })
    
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Adicionar Nova Matéria")
    
    with st.form("nova_materia"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título")
            veiculo = st.selectbox("Veículo", options=[v.nome for v in monitor.veiculos])
            data = st.date_input("Data de Publicação", value=datetime.now())
        with col2:
            resumo = st.text_area("Resumo")
            citacoes = st.text_area("Citações Diretas (uma por linha)")
            temas = st.text_input("Temas (separados por vírgula)")
        
        alcance = st.number_input("Alcance Estimado", min_value=0, value=1000, step=1000)
        engajamento = st.number_input("Engajamento", min_value=0, value=100, step=100)
        verificado = st.checkbox("Verificado", value=False)
        
        submitted = st.form_submit_button("Adicionar Matéria")
        
        if submitted:
            if not titulo or not resumo:
                st.error("Título e resumo são obrigatórios.")
            else:
                data_completa = datetime.combine(data, datetime.min.time())
                citacoes_lista = [c.strip() for c in citacoes.split("\n") if c.strip()]
                temas_lista = [t.strip() for t in temas.split(",") if t.strip()]
                
                nova = Materia(
                    id=gerar_id_materia(titulo, veiculo, data_completa),
                    titulo=titulo,
                    veiculo=veiculo,
                    data_publicacao=data_completa,
                    url=None,
                    resumo=resumo,
                    citacoes_diretas=citacoes_lista,
                    enquadramento_principal=TipoEnquadramento.NEUTRO,
                    enquadramentos_secundarios=[],
                    temas=temas_lista,
                    autor=None,
                    alcance_estimado=alcance,
                    engajamento=engajamento,
                    verificado=verificado
                )
                
                monitor.adicionar_materia(nova)
                monitor.classificar_materia(nova)
                st.success("Matéria adicionada e classificada com sucesso!")
                st.rerun()

def render_veiculos(monitor: MonitorEnquadramento):
    st.title("Cadastro de Veículos")
    
    dados_veiculos = []
    for v in monitor.veiculos:
        dados_veiculos.append({
            "Nome": v.nome,
            "Tipo": v.tipo.value,
            "Alcance Estimado": v.alcance_estimado,
            "Credibilidade": f"{v.credibilidade * 100:.0f}%",
            "URL": v.url or "-"
        })
    
    st.dataframe(pd.DataFrame(dados_veiculos), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Adicionar Novo Veículo")
    
    with st.form("novo_veiculo"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Veículo")
            tipo = st.selectbox("Tipo", options=[t for t in VeiculoTipo])
        with col2:
            alcance = st.number_input("Alcance Estimado", min_value=0, value=10000, step=1000)
            credibilidade = st.slider("Credibilidade", 0.0, 1.0, 0.7, 0.05)
        
        url = st.text_input("URL (opcional)")
        
        submitted = st.form_submit_button("Adicionar Veículo")
        
        if submitted:
            if not nome:
                st.error("Nome do veículo é obrigatório.")
            else:
                novo = Veiculo(nome, tipo, alcance, credibilidade, url if url else None)
                monitor.adicionar_veiculo(novo)
                st.success("Veículo adicionado com sucesso!")
                st.rerun()
    
    st.markdown("---")
    st.subheader("Remover Veículo")
    
    veiculo_remover = st.selectbox("Selecione o veículo para remover", options=[v.nome for v in monitor.veiculos])
    if st.button("Remover"):
        if monitor.remover_veiculo(veiculo_remover):
            st.success(f"Veículo '{veiculo_remover}' removido.")
            st.rerun()
        else:
            st.error("Não foi possível remover o veículo.")

def render_analise_texto(monitor: MonitorEnquadramento):
    st.title("Análise de Texto")
    
    texto = st.text_area("Cole aqui o texto da matéria, release ou notícia para análise de enquadramento", height=200)
    
    if st.button("Analisar"):
        if not texto.strip():
            st.warning("Insira um texto para análise.")
        else:
            principal, scores = monitor.analisar_enquadramento(texto)
            
            st.markdown(f"### Enquadramento Principal: {obter_label_enquadramento(principal)}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Scores por Categoria:**")
                for tipo, score in scores.items():
                    st.markdown(f"- {obter_label_enquadramento(tipo)}: {score * 100:.1f}%")
            with col2:
                df_scores = pd.DataFrame([
                    {"Categoria": obter_label_enquadramento(t), "Score": s}
                    for t, s in scores.items()
                ])
                fig = px.bar(
                    df_scores,
                    x="Categoria",
                    y="Score",
                    color="Categoria",
                    color_discrete_map={
                        obter_label_enquadramento(TipoEnquadramento.POSITIVO): obter_cor_enquadramento(TipoEnquadramento.POSITIVO),
                        obter_label_enquadramento(TipoEnquadramento.NEGATIVO): obter_cor_enquadramento(TipoEnquadramento.NEGATIVO),
                        obter_label_enquadramento(TipoEnquadramento.CRISIS): obter_cor_enquadramento(TipoEnquadramento.CRISIS),
                        obter_label_enquadramento(TipoEnquadramento.OPORTUNIDADE): obter_cor_enquadramento(TipoEnquadramento.OPORTUNIDADE),
                        obter_label_enquadramento(TipoEnquadramento.NEUTRO): obter_cor_enquadramento(TipoEnquadramento.NEUTRO)
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

def render_configuracoes(monitor: MonitorEnquadramento):
    st.title("Configurações")
    
    st.subheader("Identidade do Cliente")
    novo_nome = st.text_input("Nome do Cliente", value=monitor.nome_cliente)
    if st.button("Atualizar Nome"):
        monitor.nome_cliente = novo_nome
        st.success("Nome atualizado.")
    
    st.markdown("---")
    st.subheader("Exportar Dados")
    
    if st.button("Exportar para JSON"):
        caminho = f"monitor_{monitor.nome_cliente.lower().replace(' ', '_')}.json"
        monitor.exportar_json(caminho)
        st.success(f"Dados exportados para {caminho}")
        
        with open(caminho, "rb") as f:
            st.download_button(
                label="Download JSON",
                data=f,
                file_name=caminho,
                mime="application/json"
            )
    
    st.markdown("---")
    st.subheader("Resetar Dados")
    
    if st.button("Restaurar Dados de Demonstração", type="primary"):
        st.session_state.monitor = criar_monitor_demo()
        st.success("Dados de demonstração restaurados.")
        st.rerun()

def main():
    monitor = inicializar_monitor()
    render_sidebar(monitor)
    
    menu = st.session_state.get("menu", "Dashboard")
    
    if menu == "Dashboard":
        render_dashboard(monitor)
    elif menu == "Matérias":
        render_materias(monitor)
    elif menu == "Veículos":
        render_veiculos(monitor)
    elif menu == "Análise de Texto":
        render_analise_texto(monitor)
    elif menu == "Configurações":
        render_configuracoes(monitor)

if __name__ == "__main__":
    main()
