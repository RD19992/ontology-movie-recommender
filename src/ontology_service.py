from pathlib import Path

from rdflib import (
    Graph,
    RDF,
    RDFS,
    OWL,
    URIRef,
    Literal,
    XSD,
)

from src.validators import (
    validar_nota,
    validar_usuario_existe,
    validar_filme_existe,
)

# ---------------------------------------------------------
# Configuração
# ---------------------------------------------------------

ONTOLOGY_PATH = (
    Path(__file__).resolve().parents[1]
    / "ontology"
    / "film_recommender_ontology.ttl"
)

APP_DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "ontology"
    / "app_data.ttl"
)

# ---------------------------------------------------------
# Funções básicas
# ---------------------------------------------------------

def local_name(uri):
    """
    Retorna apenas o nome local de uma URI.

    Exemplos:
    http://exemplo.org#Filme -> Filme
    http://exemplo.org/Filme -> Filme
    """
    text = str(uri)

    if "#" in text:
        return text.rsplit("#", 1)[1]

    return text.rsplit("/", 1)[-1]


def carregar_ontologia():
    """
    Carrega a ontologia principal e, se existir,
    os dados persistidos pela aplicação.
    """
    graph = Graph()

    graph.parse(
        ONTOLOGY_PATH,
        format="turtle",
    )

    if APP_DATA_PATH.exists():
        graph.parse(
            APP_DATA_PATH,
            format="turtle",
        )

    return graph


def encontrar_entidade(graph, nome):
    """
    Localiza qualquer URI da ontologia pelo nome local.
    Serve para classes e propriedades.
    """
    candidatos = set()

    for sujeito, predicado, objeto in graph:
        if isinstance(sujeito, URIRef):
            candidatos.add(sujeito)

        if isinstance(predicado, URIRef):
            candidatos.add(predicado)

        if isinstance(objeto, URIRef):
            candidatos.add(objeto)

    for entidade in candidatos:
        if local_name(entidade) == nome:
            return entidade

    raise ValueError(f"Entidade '{nome}' não encontrada.")


def encontrar_classe(graph, nome_classe):
    """Localiza uma classe OWL pelo nome local."""
    for classe in graph.subjects(RDF.type, OWL.Class):
        if local_name(classe) == nome_classe:
            return classe

    raise ValueError(f"Classe '{nome_classe}' não encontrada.")


def subclasses_de(graph, classe):
    """
    Retorna a classe informada e todas as subclasses nomeadas.

    Exemplo:
    FilmeDocumentario também será considerado Filme.
    """
    classes = {classe}

    houve_alteracao = True

    while houve_alteracao:
        houve_alteracao = False

        for subclasse, _, superclasse in graph.triples(
            (None, RDFS.subClassOf, None)
        ):
            if (
                isinstance(subclasse, URIRef)
                and isinstance(superclasse, URIRef)
                and superclasse in classes
                and subclasse not in classes
            ):
                classes.add(subclasse)
                houve_alteracao = True

    return classes


def listar_individuos(graph, nome_classe):
    """Lista indivíduos de uma classe, incluindo subclasses."""
    classe = encontrar_classe(graph, nome_classe)
    classes_validas = subclasses_de(graph, classe)

    individuos = set()

    for classe_valida in classes_validas:
        individuos.update(
            graph.subjects(RDF.type, classe_valida)
        )

    return sorted(individuos, key=local_name)


# ---------------------------------------------------------
# Leitura de propriedades
# ---------------------------------------------------------

def objetos(graph, individuo, nome_propriedade):
    """
    Retorna os indivíduos ligados por uma object property.
    """
    propriedade = encontrar_entidade(graph, nome_propriedade)

    return sorted(
        {
            local_name(objeto)
            for objeto in graph.objects(individuo, propriedade)
            if isinstance(objeto, URIRef)
        }
    )


def literais(graph, individuo, nome_propriedade):
    """
    Retorna todos os valores literais de uma data property.
    """
    propriedade = encontrar_entidade(graph, nome_propriedade)

    return [
        valor.toPython()
        for valor in graph.objects(individuo, propriedade)
    ]


def primeiro_literal(graph, individuo, nome_propriedade):
    """
    Retorna o primeiro valor de uma data property ou None.
    """
    valores = literais(graph, individuo, nome_propriedade)

    return valores[0] if valores else None


# ---------------------------------------------------------
# Filmes
# ---------------------------------------------------------

def obter_filmes(graph):
    """
    Converte os indivíduos Filme em registros Python.
    """
    filmes = []

    for filme in listar_individuos(graph, "Filme"):
        filmes.append(
            {
                "id": local_name(filme),
                "titulo_original": primeiro_literal(
                    graph, filme, "tituloOriginal"
                ),
                "titulo_portugues": primeiro_literal(
                    graph, filme, "tituloPortugues"
                ),
                "ano_producao": primeiro_literal(
                    graph, filme, "anoProducao"
                ),
                "generos": objetos(
                    graph, filme, "pertenceAoGenero"
                ),
                "diretores": objetos(
                    graph, filme, "temDiretor"
                ),
                "atores": objetos(
                    graph, filme, "temAtor"
                ),
                "roteiristas": objetos(
                    graph, filme, "temRoteirista"
                ),
                "paises": objetos(
                    graph, filme, "temNacionalidadeFilme"
                ),
                "idiomas": objetos(
                    graph, filme, "temIdiomaFilme"
                ),
            }
        )

    return filmes


# ---------------------------------------------------------
# Usuários
# ---------------------------------------------------------

def obter_usuarios(graph):
    """
    Converte os indivíduos Usuario em registros Python.
    """
    usuarios = []

    for usuario in listar_individuos(graph, "Usuario"):
        usuarios.append(
            {
                "id": local_name(usuario),
                "nome": primeiro_literal(
                    graph, usuario, "nomeUsuario"
                ),
                "idade": primeiro_literal(
                    graph, usuario, "idadeUsuario"
                ),
                "preferencias": {
                    "generos": objetos(
                        graph, usuario, "prefereGenero"
                    ),
                    "diretores": objetos(
                        graph, usuario, "prefereDiretor"
                    ),
                    "atores": objetos(
                        graph, usuario, "prefereAtor"
                    ),
                    "nacionalidades": objetos(
                        graph, usuario, "prefereNacionalidade"
                    ),
                    "idiomas": objetos(
                        graph, usuario, "prefereIdioma"
                    ),
                },
            }
        )

    return usuarios


# ---------------------------------------------------------
# Avaliações
# ---------------------------------------------------------

def obter_avaliacoes(graph):
    """
    Converte os indivíduos Avaliacao em registros Python.
    """
    avaliacoes = []

    for avaliacao in listar_individuos(graph, "Avaliacao"):
        usuarios = objetos(
            graph, avaliacao, "avaliacaoFeitaPor"
        )

        filmes = objetos(
            graph, avaliacao, "avaliaFilme"
        )

        nota = primeiro_literal(
            graph, avaliacao, "notaEstrelas"
        )

        avaliacoes.append(
            {
                "id": local_name(avaliacao),
                "usuario": usuarios[0] if usuarios else None,
                "filme": filmes[0] if filmes else None,
                "nota": nota,
            }
        )

    return avaliacoes

# ---------------------------------------------------------
# Escrita e persistência
# ---------------------------------------------------------

def uri_novo_individuo(graph, classe_uri, nome_individuo):
    """
    Cria uma URI para um novo indivíduo usando
    o mesmo namespace da ontologia.
    """
    classe_texto = str(classe_uri)
    nome_classe = local_name(classe_uri)

    namespace = classe_texto[:-len(nome_classe)]

    return URIRef(namespace + nome_individuo)


def encontrar_avaliacao(
    graph,
    usuario_uri,
    filme_uri,
):
    """
    Procura uma avaliação já existente do mesmo
    usuário para o mesmo filme.
    """
    prop_usuario = encontrar_entidade(
        graph,
        "avaliacaoFeitaPor",
    )

    prop_filme = encontrar_entidade(
        graph,
        "avaliaFilme",
    )

    for avaliacao in graph.subjects(
        prop_usuario,
        usuario_uri,
    ):
        if (
            avaliacao,
            prop_filme,
            filme_uri,
        ) in graph:
            return avaliacao

    return None


def registrar_avaliacao(
    usuario_id,
    filme_id,
    nota,
):
    """
    Registra uma nova avaliação em RDF.

    Se o usuário já avaliou o filme,
    atualiza a nota existente.

    Os novos dados são persistidos em app_data.ttl.
    """

    graph = carregar_ontologia()

    filmes = obter_filmes(graph)
    usuarios = obter_usuarios(graph)

    validar_nota(nota)
    validar_usuario_existe(
        usuario_id,
        usuarios,
    )
    validar_filme_existe(
        filme_id,
        filmes,
    )

    usuario_uri = encontrar_entidade(
        graph,
        usuario_id,
    )

    filme_uri = encontrar_entidade(
        graph,
        filme_id,
    )

    classe_avaliacao = encontrar_classe(
        graph,
        "Avaliacao",
    )

    prop_usuario = encontrar_entidade(
        graph,
        "avaliacaoFeitaPor",
    )

    prop_filme = encontrar_entidade(
        graph,
        "avaliaFilme",
    )

    prop_nota = encontrar_entidade(
        graph,
        "notaEstrelas",
    )

    avaliacao_uri = encontrar_avaliacao(
        graph,
        usuario_uri,
        filme_uri,
    )

    nova_avaliacao = avaliacao_uri is None

    if nova_avaliacao:
        nome_avaliacao = (
            f"Avaliacao_{usuario_id}_{filme_id}"
        )

        avaliacao_uri = uri_novo_individuo(
            graph,
            classe_avaliacao,
            nome_avaliacao,
        )

    # Grafo separado contendo somente dados
    # criados/modificados pela aplicação.
    data_graph = Graph()

    if APP_DATA_PATH.exists():
        data_graph.parse(
            APP_DATA_PATH,
            format="turtle",
        )

    if nova_avaliacao:
        data_graph.add(
            (
                avaliacao_uri,
                RDF.type,
                OWL.NamedIndividual,
            )
        )

        data_graph.add(
            (
                avaliacao_uri,
                RDF.type,
                classe_avaliacao,
            )
        )

        data_graph.add(
            (
                avaliacao_uri,
                prop_usuario,
                usuario_uri,
            )
        )

        data_graph.add(
            (
                avaliacao_uri,
                prop_filme,
                filme_uri,
            )
        )

    # Remove uma possível nota anterior que esteja
    # no arquivo da aplicação.
    data_graph.remove(
        (
            avaliacao_uri,
            prop_nota,
            None,
        )
    )

    data_graph.add(
        (
            avaliacao_uri,
            prop_nota,
            Literal(
                int(nota),
                datatype=XSD.integer,
            ),
        )
    )

    data_graph.serialize(
        destination=APP_DATA_PATH,
        format="turtle",
    )

    return {
        "avaliacao": local_name(avaliacao_uri),
        "usuario": usuario_id,
        "filme": filme_id,
        "nota": int(nota),
        "nova": nova_avaliacao,
    }


# ---------------------------------------------------------
# Teste manual
# ---------------------------------------------------------

def main():
    print("Carregando ontologia:")
    print(ONTOLOGY_PATH)
    print()

    graph = carregar_ontologia()

    filmes = obter_filmes(graph)
    usuarios = obter_usuarios(graph)
    avaliacoes = obter_avaliacoes(graph)

    print(f"Total de triplas RDF: {len(graph)}")
    print(f"Filmes estruturados: {len(filmes)}")
    print(f"Usuários estruturados: {len(usuarios)}")
    print(f"Avaliações estruturadas: {len(avaliacoes)}")
    print()

    print("EXEMPLO DE FILME")
    print("-" * 60)
    print(filmes[0])
    print()

    print("EXEMPLO DE USUÁRIO")
    print("-" * 60)
    print(usuarios[0])
    print()

    print("PRIMEIRAS 5 AVALIAÇÕES")
    print("-" * 60)

    for avaliacao in avaliacoes[:5]:
        print(avaliacao)


if __name__ == "__main__":
    main()