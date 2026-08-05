from ontology_service import (
    carregar_ontologia,
    obter_filmes,
    obter_usuarios,
    obter_avaliacoes,
)


# Pesos da recomendação baseada em conteúdo.
# A soma é 1.0.
PESOS_CONTEUDO = {
    "generos": 0.30,
    "diretores": 0.25,
    "atores": 0.20,
    "nacionalidades": 0.15,
    "idiomas": 0.10,
}

# Parâmetros da filtragem colaborativa
MIN_FILMES_COMUNS = 2
LIMIAR_SIMILARIDADE = 0.40
FILMES_PARA_CONFIANCA_MAXIMA = 3

# Parâmetros para modelo híbrido
PESO_HIBRIDO_CONTEUDO = 0.60
PESO_HIBRIDO_COLABORATIVO = 0.40

def encontrar_usuario(usuarios, usuario_id):
    """
    Localiza um usuário pelo ID da ontologia.
    """
    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            return usuario

    raise ValueError(f"Usuário '{usuario_id}' não encontrado.")


def filmes_avaliados_por(avaliacoes, usuario_id):
    """
    Retorna o conjunto de IDs dos filmes já avaliados pelo usuário.
    """
    return {
        avaliacao["filme"]
        for avaliacao in avaliacoes
        if avaliacao["usuario"] == usuario_id
    }


def calcular_score_conteudo(usuario, filme):
    """
    Calcula a compatibilidade entre as preferências explícitas
    do usuário e os metadados semânticos do filme.

    O score final varia de 0 a 1.

    Se o usuário não possuir determinada preferência,
    o peso correspondente é retirado do denominador.
    """

    preferencias = usuario["preferencias"]

    correspondencias = {
        "generos": set(preferencias["generos"])
        & set(filme["generos"]),

        "diretores": set(preferencias["diretores"])
        & set(filme["diretores"]),

        "atores": set(preferencias["atores"])
        & set(filme["atores"]),

        "nacionalidades": set(preferencias["nacionalidades"])
        & set(filme["paises"]),

        "idiomas": set(preferencias["idiomas"])
        & set(filme["idiomas"]),
    }

    peso_ativo = 0.0
    pontos = 0.0
    motivos = []

    for categoria, peso in PESOS_CONTEUDO.items():

        # Só considera o peso se o usuário declarou
        # alguma preferência nessa categoria.
        if preferencias[categoria]:
            peso_ativo += peso

            if correspondencias[categoria]:
                pontos += peso

                valores = ", ".join(
                    sorted(correspondencias[categoria])
                )

                motivos.append(
                    f"{categoria}: {valores}"
                )

    if peso_ativo == 0:
        return 0.0, []

    score = pontos / peso_ativo

    return score, motivos


def recomendar_por_conteudo(
    usuario_id,
    filmes,
    usuarios,
    avaliacoes,
):
    """
    Gera ranking de filmes ainda não avaliados pelo usuário.
    """

    usuario = encontrar_usuario(
        usuarios,
        usuario_id,
    )

    ja_avaliados = filmes_avaliados_por(
        avaliacoes,
        usuario_id,
    )

    recomendacoes = []

    for filme in filmes:

        # Não recomendamos aquilo que o usuário
        # já avaliou.
        if filme["id"] in ja_avaliados:
            continue

        score, motivos = calcular_score_conteudo(
            usuario,
            filme,
        )

        recomendacoes.append(
            {
                "filme": filme["id"],
                "titulo": (
                    filme["titulo_portugues"]
                    or filme["titulo_original"]
                    or filme["id"]
                ),
                "score_conteudo": score,
                "motivos": motivos,
            }
        )

    recomendacoes.sort(
        key=lambda item: (
            item["score_conteudo"],
            item["titulo"],
        ),
        reverse=True,
    )

    return recomendacoes

# ---------------------------------------------------------
# Filtragem colaborativa
# ---------------------------------------------------------

def construir_matriz_avaliacoes(avaliacoes):
    """
    Constrói uma estrutura:

    {
        "UsuarioAna": {
            "CentralDoBrasil": 5,
            "AOrigem": 2,
            ...
        },
        ...
    }
    """
    matriz = {}

    for avaliacao in avaliacoes:
        usuario = avaliacao["usuario"]
        filme = avaliacao["filme"]
        nota = avaliacao["nota"]

        if usuario is None or filme is None or nota is None:
            continue

        if usuario not in matriz:
            matriz[usuario] = {}

        matriz[usuario][filme] = float(nota)

    return matriz


def calcular_similaridade_usuarios(
    usuario_a,
    usuario_b,
    matriz,
):
    """
    Calcula similaridade entre dois usuários usando apenas
    os filmes avaliados por ambos.

    A similaridade considera:
    1. diferença média entre as notas;
    2. quantidade de filmes em comum.

    Retorna:
        similaridade entre 0 e 1
        quantidade de filmes em comum
    """

    notas_a = matriz.get(usuario_a, {})
    notas_b = matriz.get(usuario_b, {})

    filmes_comuns = set(notas_a) & set(notas_b)

    quantidade_comuns = len(filmes_comuns)

    if quantidade_comuns < MIN_FILMES_COMUNS:
        return 0.0, quantidade_comuns

    diferencas = [
        abs(notas_a[filme] - notas_b[filme])
        for filme in filmes_comuns
    ]

    diferenca_media = sum(diferencas) / quantidade_comuns

    # Como as notas vão de 1 a 5,
    # a diferença máxima possível é 4.
    similaridade_base = 1 - (diferenca_media / 4)

    # Evita dar confiança excessiva a uma comparação
    # feita sobre poucos filmes.
    confianca = min(
        quantidade_comuns / FILMES_PARA_CONFIANCA_MAXIMA,
        1.0,
    )

    similaridade = similaridade_base * confianca

    return similaridade, quantidade_comuns


def encontrar_usuarios_similares(
    usuario_id,
    usuarios,
    matriz,
):
    """
    Retorna usuários suficientemente semelhantes
    ao usuário selecionado.
    """
    similares = []

    for usuario in usuarios:
        outro_id = usuario["id"]

        if outro_id == usuario_id:
            continue

        similaridade, filmes_comuns = (
            calcular_similaridade_usuarios(
                usuario_id,
                outro_id,
                matriz,
            )
        )

        if similaridade >= LIMIAR_SIMILARIDADE:
            similares.append(
                {
                    "usuario": outro_id,
                    "nome": usuario["nome"],
                    "similaridade": similaridade,
                    "filmes_comuns": filmes_comuns,
                }
            )

    similares.sort(
        key=lambda item: -item["similaridade"]
    )

    return similares


def recomendar_colaborativo(
    usuario_id,
    filmes,
    usuarios,
    avaliacoes,
):
    """
    Recomenda filmes com base nas avaliações de usuários
    semelhantes.

    Filmes já avaliados pelo usuário são excluídos.
    """

    matriz = construir_matriz_avaliacoes(avaliacoes)

    ja_avaliados = filmes_avaliados_por(
        avaliacoes,
        usuario_id,
    )

    similares = encontrar_usuarios_similares(
        usuario_id,
        usuarios,
        matriz,
    )

    filmes_por_id = {
        filme["id"]: filme
        for filme in filmes
    }

    candidatos = {}

    for vizinho in similares:
        vizinho_id = vizinho["usuario"]
        similaridade = vizinho["similaridade"]

        notas_vizinho = matriz.get(vizinho_id, {})

        for filme_id, nota in notas_vizinho.items():

            if filme_id in ja_avaliados:
                continue

            if filme_id not in filmes_por_id:
                continue

            if filme_id not in candidatos:
                candidatos[filme_id] = {
                    "soma_ponderada": 0.0,
                    "soma_similaridades": 0.0,
                    "vizinhos": [],
                }

            # Normalizamos nota de 1-5 para 0-1.
            nota_normalizada = nota / 5.0

            candidatos[filme_id]["soma_ponderada"] += (
                similaridade * nota_normalizada
            )

            candidatos[filme_id]["soma_similaridades"] += (
                similaridade
            )

            candidatos[filme_id]["vizinhos"].append(
                {
                    "usuario": vizinho_id,
                    "nome": vizinho["nome"],
                    "similaridade": similaridade,
                    "nota": nota,
                }
            )

    recomendacoes = []

    for filme_id, dados in candidatos.items():

        if dados["soma_similaridades"] == 0:
            continue

        score = (
            dados["soma_ponderada"]
            / dados["soma_similaridades"]
        )

        filme = filmes_por_id[filme_id]

        recomendacoes.append(
            {
                "filme": filme_id,
                "titulo": (
                    filme["titulo_portugues"]
                    or filme["titulo_original"]
                    or filme_id
                ),
                "score_colaborativo": score,
                "vizinhos": dados["vizinhos"],
            }
        )

    recomendacoes.sort(
        key=lambda item: (
            -item["score_colaborativo"],
            item["titulo"],
        )
    )

    return recomendacoes, similares

# ---------------------------------------------------------
# Recomendação híbrida
# ---------------------------------------------------------

def recomendar_hibrido(
    usuario_id,
    filmes,
    usuarios,
    avaliacoes,
):
    """
    Combina recomendação baseada em conteúdo e
    filtragem colaborativa.

    Quando há evidência dos dois métodos:
        60% conteúdo + 40% colaborativo.

    Quando não existe evidência colaborativa para um filme,
    utiliza somente o score de conteúdo.
    """

    recomendacoes_conteudo = recomendar_por_conteudo(
        usuario_id,
        filmes,
        usuarios,
        avaliacoes,
    )

    recomendacoes_collab, similares = recomendar_colaborativo(
        usuario_id,
        filmes,
        usuarios,
        avaliacoes,
    )

    # Facilita consultar o score colaborativo por filme.
    collab_por_filme = {
        item["filme"]: item
        for item in recomendacoes_collab
    }

    recomendacoes = []

    for item_conteudo in recomendacoes_conteudo:
        filme_id = item_conteudo["filme"]
        score_conteudo = item_conteudo["score_conteudo"]

        item_collab = collab_por_filme.get(filme_id)

        if item_collab is not None:
            score_collab = item_collab["score_colaborativo"]

            score_final = (
                PESO_HIBRIDO_CONTEUDO * score_conteudo
                + PESO_HIBRIDO_COLABORATIVO * score_collab
            )

            origem = "conteúdo + colaborativo"
            vizinhos = item_collab["vizinhos"]

        else:
            # Não penaliza um filme apenas porque ainda
            # não existe informação colaborativa suficiente.
            score_collab = None
            score_final = score_conteudo
            origem = "somente conteúdo"
            vizinhos = []

        recomendacoes.append(
            {
                "filme": filme_id,
                "titulo": item_conteudo["titulo"],
                "score_conteudo": score_conteudo,
                "score_colaborativo": score_collab,
                "score_final": score_final,
                "origem": origem,
                "motivos_conteudo": item_conteudo["motivos"],
                "vizinhos": vizinhos,
            }
        )

    recomendacoes.sort(
        key=lambda item: (
            -item["score_final"],
            item["titulo"],
        )
    )

    return recomendacoes, similares

def main():
    graph = carregar_ontologia()

    filmes = obter_filmes(graph)
    usuarios = obter_usuarios(graph)
    avaliacoes = obter_avaliacoes(graph)

    usuario_id = "UsuarioAna"

    usuario = encontrar_usuario(
        usuarios,
        usuario_id,
    )

    # -----------------------------------------------------
    # Conteúdo
    # -----------------------------------------------------

    recomendacoes_conteudo = recomendar_por_conteudo(
        usuario_id,
        filmes,
        usuarios,
        avaliacoes,
    )

    print()
    print(f"CONTEÚDO - {usuario['nome']}")
    print("=" * 70)

    for posicao, item in enumerate(
        recomendacoes_conteudo[:5],
        start=1,
    ):
        print(
            f"{posicao:2}. "
            f"{item['titulo']:<35} "
            f"{item['score_conteudo']:.2f}"
        )

    # -----------------------------------------------------
    # Colaborativo
    # -----------------------------------------------------

    recomendacoes_collab, similares = recomendar_colaborativo(
        usuario_id,
        filmes,
        usuarios,
        avaliacoes,
    )

    print()
    print(f"COLABORATIVO - {usuario['nome']}")
    print("=" * 70)

    for posicao, item in enumerate(
        recomendacoes_collab[:5],
        start=1,
    ):
        print(
            f"{posicao:2}. "
            f"{item['titulo']:<35} "
            f"{item['score_colaborativo']:.2f}"
        )

    # -----------------------------------------------------
    # Híbrido
    # -----------------------------------------------------

    recomendacoes_hibridas, _ = recomendar_hibrido(
        usuario_id,
        filmes,
        usuarios,
        avaliacoes,
    )

    print()
    print(f"HÍBRIDO - {usuario['nome']}")
    print("=" * 70)

    for posicao, item in enumerate(
        recomendacoes_hibridas[:5],
        start=1,
    ):
        collab = item["score_colaborativo"]

        if collab is None:
            collab_texto = "-"
        else:
            collab_texto = f"{collab:.2f}"

        print(
            f"{posicao:2}. "
            f"{item['titulo']:<30} "
            f"final={item['score_final']:.2f} "
            f"conteúdo={item['score_conteudo']:.2f} "
            f"collab={collab_texto}"
        )

        print(
            f"    Origem: {item['origem']}"
        )


if __name__ == "__main__":
    main()