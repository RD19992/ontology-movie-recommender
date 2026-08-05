from pathlib import Path

from rdflib import Graph, RDF, RDFS, OWL, URIRef


# Caminho da ontologia relativo ao projeto
ONTOLOGY_PATH = (
    Path(__file__).resolve().parents[1]
    / "ontology"
    / "film_recommender_ontology.ttl"
)


def local_name(uri):
    """
    Retorna somente o nome final de uma URI.

    Exemplos:
    http://exemplo.org#Filme -> Filme
    http://exemplo.org/Filme -> Filme
    """
    text = str(uri)

    if "#" in text:
        return text.rsplit("#", 1)[1]

    return text.rsplit("/", 1)[-1]


def carregar_ontologia():
    """Carrega o arquivo Turtle em um grafo RDF."""
    graph = Graph()
    graph.parse(ONTOLOGY_PATH, format="turtle")
    return graph


def encontrar_classe(graph, nome_classe):
    """Localiza uma classe OWL pelo nome local."""
    for classe in graph.subjects(RDF.type, OWL.Class):
        if local_name(classe) == nome_classe:
            return classe

    raise ValueError(f"Classe '{nome_classe}' não encontrada.")


def subclasses_de(graph, classe):
    """
    Retorna a classe informada e todas as suas subclasses.
    Isso é importante porque FilmeDocumentario também é Filme.
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
    """Lista indivíduos de uma classe, incluindo suas subclasses."""
    classe = encontrar_classe(graph, nome_classe)
    classes_validas = subclasses_de(graph, classe)

    individuos = set()

    for classe_valida in classes_validas:
        individuos.update(
            graph.subjects(RDF.type, classe_valida)
        )

    return sorted(individuos, key=lambda x: local_name(x))


def main():
    print(f"Carregando ontologia:")
    print(ONTOLOGY_PATH)
    print()

    graph = carregar_ontologia()

    print(f"Total de triplas RDF: {len(graph)}")
    print()

    filmes = listar_individuos(graph, "Filme")
    usuarios = listar_individuos(graph, "Usuario")

    print(f"Filmes encontrados: {len(filmes)}")

    for filme in filmes:
        print(f"  - {local_name(filme)}")

    print()

    print(f"Usuários encontrados: {len(usuarios)}")

    for usuario in usuarios:
        print(f"  - {local_name(usuario)}")


if __name__ == "__main__":
    main()