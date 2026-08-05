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

    recomendacoes = recomendar_por_conteudo(
        usuario_id,
        filmes,
        usuarios,
        avaliacoes,
    )

    print()
    print(
        f"RECOMENDAÇÕES POR CONTEÚDO PARA "
        f"{usuario['nome']}"
    )
    print("=" * 70)

    for posicao, recomendacao in enumerate(
        recomendacoes,
        start=1,
    ):
        score = recomendacao["score_conteudo"]

        print(
            f"{posicao:2}. "
            f"{recomendacao['titulo']:<35} "
            f"{score:.2f}"
        )

        if recomendacao["motivos"]:
            print(
                "    Correspondências: "
                + "; ".join(recomendacao["motivos"])
            )
        else:
            print(
                "    Correspondências: nenhuma"
            )


if __name__ == "__main__":
    main()