from pathlib import Path

from rdflib import Graph, RDF, RDFS, OWL, URIRef


# ---------------------------------------------------------
# Configuração
# ---------------------------------------------------------

ONTOLOGY_PATH = (
    Path(__file__).resolve().parents[1]
    / "ontology"
    / "film_recommender_ontology.ttl"
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
    """Carrega a ontologia Turtle em um grafo RDF."""
    graph = Graph()
    graph.parse(ONTOLOGY_PATH, format="turtle")
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