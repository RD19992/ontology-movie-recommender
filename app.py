import streamlit as st

from src.ontology_service import (
    carregar_ontologia,
    obter_filmes,
    obter_usuarios,
    obter_avaliacoes,
    registrar_avaliacao,
    registrar_usuario,
    listar_opcoes_preferencia,
    registrar_filme,
    listar_opcoes_filme,
)

from src.recommender import (
    recomendar_por_conteudo,
    recomendar_colaborativo,
    recomendar_hibrido,
)


# ---------------------------------------------------------
# Configuração
# ---------------------------------------------------------

st.set_page_config(
    page_title="Ontology Movie Recommender",
    page_icon="🎬",
    layout="wide",
)


# ---------------------------------------------------------
# Carregamento dos dados
# ---------------------------------------------------------

graph = carregar_ontologia()

filmes = obter_filmes(graph)
usuarios = obter_usuarios(graph)
avaliacoes = obter_avaliacoes(graph)

usuarios_por_id = {
    usuario["id"]: usuario
    for usuario in usuarios
}

filmes_por_id = {
    filme["id"]: filme
    for filme in filmes
}

opcoes_preferencia = listar_opcoes_preferencia(
    graph
)

opcoes_filme = listar_opcoes_filme(
    graph
)

def filtrar_catalogo(
    filmes,
    texto="",
    generos=None,
    diretores=None,
    atores=None,
    paises=None,
    idiomas=None,
):
    """
    Filtra o catálogo usando os metadados extraídos
    da ontologia.
    """

    generos = generos or []
    diretores = diretores or []
    atores = atores or []
    paises = paises or []
    idiomas = idiomas or []

    texto = texto.strip().lower()

    resultados = []

    for filme in filmes:

        titulos = [
            filme["id"],
            filme["titulo_original"] or "",
            filme["titulo_portugues"] or "",
        ]

        if texto:
            if not any(
                texto in str(titulo).lower()
                for titulo in titulos
            ):
                continue

        if generos and not (
            set(generos) & set(filme["generos"])
        ):
            continue

        if diretores and not (
            set(diretores) & set(filme["diretores"])
        ):
            continue

        if atores and not (
            set(atores) & set(filme["atores"])
        ):
            continue

        if paises and not (
            set(paises) & set(filme["paises"])
        ):
            continue

        if idiomas and not (
            set(idiomas) & set(filme["idiomas"])
        ):
            continue

        resultados.append(filme)

    return sorted(
        resultados,
        key=lambda filme: (
            filme["titulo_portugues"]
            or filme["titulo_original"]
            or filme["id"]
        ),
    )

# ---------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------

st.title("🎬 Ontology Movie Recommender")

st.caption(
    "Sistema híbrido de recomendação baseado em "
    "ontologia OWL/RDF e filtragem colaborativa."
)

if "mensagem" in st.session_state:
    st.success(
        st.session_state.pop("mensagem")
    )


# ---------------------------------------------------------
# Seleção do usuário
# ---------------------------------------------------------

st.sidebar.header("Usuário")

usuario_id = st.sidebar.selectbox(
    "Selecione o usuário",
    options=list(usuarios_por_id.keys()),
    format_func=lambda uid: usuarios_por_id[uid]["nome"],
)

usuario = usuarios_por_id[usuario_id]


# ---------------------------------------------------------
# Método
# ---------------------------------------------------------

st.sidebar.header("Método de recomendação")

metodo = st.sidebar.radio(
    "Modelo",
    options=[
        "Híbrido",
        "Conteúdo",
        "Colaborativo",
    ],
)

top_n = st.sidebar.slider(
    "Número de recomendações",
    min_value=1,
    max_value=10,
    value=5,
)


# ---------------------------------------------------------
# Perfil
# ---------------------------------------------------------

st.subheader(f"Perfil de {usuario['nome']}")

preferencias = usuario["preferencias"]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Gêneros",
    ", ".join(preferencias["generos"]) or "—",
)

col2.metric(
    "Diretores",
    ", ".join(preferencias["diretores"]) or "—",
)

col3.metric(
    "Atores",
    ", ".join(preferencias["atores"]) or "—",
)

col4.metric(
    "Nacionalidades",
    ", ".join(preferencias["nacionalidades"]) or "—",
)

col5.metric(
    "Idiomas",
    ", ".join(preferencias["idiomas"]) or "—",
)


# ---------------------------------------------------------
# Recomendação
# ---------------------------------------------------------

st.divider()
st.header(f"Recomendações — {metodo}")


if metodo == "Conteúdo":

    recomendacoes = recomendar_por_conteudo(
        usuario_id,
        filmes,
        usuarios,
        avaliacoes,
    )

    recomendacoes = [
        item
        for item in recomendacoes
        if item["score_conteudo"] > 0
    ]

    if not recomendacoes:
        st.info(
            "Não há filmes não avaliados com afinidade "
            "de conteúdo para este usuário."
        )

    for posicao, item in enumerate(
        recomendacoes[:top_n],
        start=1,
    ):
        st.subheader(
            f"{posicao}. {item['titulo']}"
        )

        st.write(
            f"**Score:** "
            f"{item['score_conteudo']:.2f}"
        )

        if item["motivos"]:
            st.write(
                "**Correspondências:** "
                + "; ".join(item["motivos"])
            )
        else:
            st.write(
                "Nenhuma correspondência explícita."
            )


elif metodo == "Colaborativo":

    recomendacoes, similares = (
        recomendar_colaborativo(
            usuario_id,
            filmes,
            usuarios,
            avaliacoes,
        )
    )

    if not recomendacoes:
        st.info(
            "Não há evidência colaborativa suficiente "
            "para este usuário."
        )

    for posicao, item in enumerate(
        recomendacoes[:top_n],
        start=1,
    ):
        st.subheader(
            f"{posicao}. {item['titulo']}"
        )

        st.write(
            f"**Score colaborativo:** "
            f"{item['score_colaborativo']:.2f}"
        )

        with st.expander(
            "Ver usuários que influenciaram"
        ):
            for vizinho in item["vizinhos"]:
                st.write(
                    f"{vizinho['nome']} — "
                    f"similaridade "
                    f"{vizinho['similaridade']:.2f}, "
                    f"nota {vizinho['nota']:.0f}"
                )


else:

    recomendacoes, similares = (
        recomendar_hibrido(
            usuario_id,
            filmes,
            usuarios,
            avaliacoes,
        )
    )

    recomendacoes = [
        item
        for item in recomendacoes
        if item["score_final"] > 0
    ]

    if not recomendacoes:
        st.info(
            "Não há recomendações com evidência "
            "suficiente para este usuário."
        )

    for posicao, item in enumerate(
        recomendacoes[:top_n],
        start=1,
    ):
        st.subheader(
            f"{posicao}. {item['titulo']}"
        )

        col_score, col_content, col_collab = (
            st.columns(3)
        )

        col_score.metric(
            "Score final",
            f"{item['score_final']:.2f}",
        )

        col_content.metric(
            "Conteúdo",
            f"{item['score_conteudo']:.2f}",
        )

        if item["score_colaborativo"] is None:
            collab_texto = "—"
        else:
            collab_texto = (
                f"{item['score_colaborativo']:.2f}"
            )

        col_collab.metric(
            "Colaborativo",
            collab_texto,
        )

        st.caption(
            f"Origem: {item['origem']}"
        )

        if item["motivos_conteudo"]:
            st.write(
                "**Afinidades semânticas:** "
                + "; ".join(
                    item["motivos_conteudo"]
                )
            )


# ---------------------------------------------------------
# Nova avaliação
# ---------------------------------------------------------

st.divider()
st.header("Avaliar um filme")


ja_avaliados = {
    avaliacao["filme"]
    for avaliacao in avaliacoes
    if avaliacao["usuario"] == usuario_id
}

filmes_nao_avaliados = [
    filme
    for filme in filmes
    if filme["id"] not in ja_avaliados
]


if filmes_nao_avaliados:

    ids_disponiveis = [
        filme["id"]
        for filme in filmes_nao_avaliados
    ]

    with st.form("nova_avaliacao"):

        filme_id = st.selectbox(
            "Filme",
            options=ids_disponiveis,
            format_func=lambda fid: (
                filmes_por_id[fid]["titulo_portugues"]
                or filmes_por_id[fid]["titulo_original"]
                or fid
            ),
        )

        nota = st.slider(
            "Nota",
            min_value=1,
            max_value=5,
            value=3,
        )

        enviar = st.form_submit_button(
            "Salvar avaliação"
        )

        if enviar:
            try:
                resultado = registrar_avaliacao(
                    usuario_id=usuario_id,
                    filme_id=filme_id,
                    nota=nota,
                )

                titulo = (
                    filmes_por_id[filme_id][
                        "titulo_portugues"
                    ]
                    or filme_id
                )

                st.session_state["mensagem"] = (
                    f"Avaliação registrada: "
                    f"{titulo} — {nota}/5."
                )

                st.rerun()

            except ValueError as erro:
                st.error(str(erro))

else:
    st.info(
        "Este usuário já avaliou todos os filmes "
        "do catálogo."
    )

# ---------------------------------------------------------
# Cadastro de usuário
# ---------------------------------------------------------

st.divider()
st.header("Cadastrar novo usuário")

with st.expander(
    "Novo usuário",
    expanded=False,
):

    with st.form("cadastro_usuario"):

        nome_novo = st.text_input(
            "Nome"
        )

        idade_nova = st.number_input(
            "Idade",
            min_value=1,
            max_value=120,
            value=25,
            step=1,
        )

        st.subheader("Contato")

        email_novo = st.text_input(
            "E-mail"
        )

        whatsapp_novo = st.text_input(
            "WhatsApp"
        )

        outro_contato_novo = st.text_input(
            "Outro contato"
        )

        st.subheader("Preferências")

        generos_novos = st.multiselect(
            "Gêneros",
            options=opcoes_preferencia["generos"],
        )

        diretores_novos = st.multiselect(
            "Diretores",
            options=opcoes_preferencia["diretores"],
        )

        atores_novos = st.multiselect(
            "Atores",
            options=opcoes_preferencia["atores"],
        )

        nacionalidades_novas = st.multiselect(
            "Nacionalidades",
            options=opcoes_preferencia[
                "nacionalidades"
            ],
        )

        idiomas_novos = st.multiselect(
            "Idiomas",
            options=opcoes_preferencia["idiomas"],
        )

        cadastrar = st.form_submit_button(
            "Cadastrar usuário"
        )

        if cadastrar:

            try:

                resultado = registrar_usuario(
                    nome=nome_novo,
                    idade=int(idade_nova),
                    email=email_novo,
                    whatsapp=whatsapp_novo,
                    outro_contato=outro_contato_novo,
                    generos=generos_novos,
                    diretores=diretores_novos,
                    atores=atores_novos,
                    nacionalidades=nacionalidades_novas,
                    idiomas=idiomas_novos,
                )

                st.session_state["mensagem"] = (
                    f"Usuário "
                    f"{resultado['nome']} "
                    f"cadastrado com sucesso."
                )

                st.rerun()

            except ValueError as erro:
                st.error(str(erro))

# ---------------------------------------------------------
# Cadastro de filme
# ---------------------------------------------------------

st.divider()
st.header("Cadastrar novo filme")

with st.expander(
    "Novo filme",
    expanded=False,
):

    with st.form("cadastro_filme"):

        titulo_original_novo = st.text_input(
            "Título original"
        )

        titulo_portugues_novo = st.text_input(
            "Título em português (opcional)"
        )

        col_ano1, col_ano2 = st.columns(2)

        ano_producao_novo = col_ano1.number_input(
            "Ano de produção",
            min_value=1888,
            max_value=2100,
            value=2025,
            step=1,
        )

        ano_lancamento_novo = col_ano2.number_input(
            "Ano de lançamento",
            min_value=1888,
            max_value=2100,
            value=2025,
            step=1,
        )

        generos_novo_filme = st.multiselect(
            "Gêneros",
            options=opcoes_filme["generos"],
        )

        diretores_novo_filme = st.multiselect(
            "Diretores",
            options=opcoes_filme["diretores"],
        )

        atores_novo_filme = st.multiselect(
            "Atores",
            options=opcoes_filme["atores"],
        )

        roteiristas_novo_filme = st.multiselect(
            "Roteiristas",
            options=opcoes_filme["roteiristas"],
        )

        paises_novo_filme = st.multiselect(
            "Países",
            options=opcoes_filme["paises"],
        )

        idiomas_novo_filme = st.multiselect(
            "Idiomas",
            options=opcoes_filme["idiomas"],
        )

        cadastrar_filme = (
            st.form_submit_button(
                "Cadastrar filme"
            )
        )

        if cadastrar_filme:

            try:

                resultado = registrar_filme(
                    titulo_original=(
                        titulo_original_novo
                    ),
                    titulo_portugues=(
                        titulo_portugues_novo
                    ),
                    ano_producao=int(
                        ano_producao_novo
                    ),
                    ano_lancamento=int(
                        ano_lancamento_novo
                    ),
                    generos=generos_novo_filme,
                    diretores=diretores_novo_filme,
                    atores=atores_novo_filme,
                    roteiristas=(
                        roteiristas_novo_filme
                    ),
                    paises=paises_novo_filme,
                    idiomas=idiomas_novo_filme,
                )

                st.session_state[
                    "mensagem"
                ] = (
                    f"Filme "
                    f"{resultado['titulo']} "
                    f"cadastrado com sucesso."
                )

                st.rerun()

            except ValueError as erro:
                st.error(str(erro))

# ---------------------------------------------------------
# Exploração do catálogo
# ---------------------------------------------------------

st.divider()
st.header("Explorar catálogo")

st.write(
    "Consulte os filmes utilizando propriedades "
    "semânticas da ontologia."
)

texto_busca = st.text_input(
    "Buscar por título",
    key="busca_catalogo",
)

col_filtro1, col_filtro2 = st.columns(2)

with col_filtro1:

    filtro_generos = st.multiselect(
        "Filtrar por gênero",
        options=opcoes_filme["generos"],
        key="filtro_generos",
    )

    filtro_diretores = st.multiselect(
        "Filtrar por diretor",
        options=opcoes_filme["diretores"],
        key="filtro_diretores",
    )

    filtro_atores = st.multiselect(
        "Filtrar por ator",
        options=opcoes_filme["atores"],
        key="filtro_atores",
    )

with col_filtro2:

    filtro_paises = st.multiselect(
        "Filtrar por nacionalidade",
        options=opcoes_filme["paises"],
        key="filtro_paises",
    )

    filtro_idiomas = st.multiselect(
        "Filtrar por idioma",
        options=opcoes_filme["idiomas"],
        key="filtro_idiomas",
    )


resultados_catalogo = filtrar_catalogo(
    filmes=filmes,
    texto=texto_busca,
    generos=filtro_generos,
    diretores=filtro_diretores,
    atores=filtro_atores,
    paises=filtro_paises,
    idiomas=filtro_idiomas,
)


st.subheader(
    f"Resultados: {len(resultados_catalogo)}"
)


if resultados_catalogo:

    linhas_catalogo = []

    for filme in resultados_catalogo:

        linhas_catalogo.append(
            {
                "Título": (
                    filme["titulo_portugues"]
                    or filme["titulo_original"]
                    or filme["id"]
                ),
                "Ano": filme["ano_producao"],
                "Gênero": ", ".join(
                    filme["generos"]
                ),
                "Diretor": ", ".join(
                    filme["diretores"]
                ),
                "Ator": ", ".join(
                    filme["atores"]
                ),
                "País": ", ".join(
                    filme["paises"]
                ),
                "Idioma": ", ".join(
                    filme["idiomas"]
                ),
            }
        )

    st.dataframe(
        linhas_catalogo,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info(
        "Nenhum filme corresponde aos filtros selecionados."
    )