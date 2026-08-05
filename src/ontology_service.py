from pathlib import Path

import re
import unicodedata

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
    validar_nome_usuario,
    validar_idade_usuario,
    validar_contato_usuario,
    validar_preferencias_usuario,
    validar_titulo_filme,
    validar_ano_filme,
    validar_relacoes_filme,
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

def gerar_id_usuario(nome):
    """
    Converte um nome humano em ID RDF simples.

    Exemplo:
        João da Silva -> UsuarioJoaoDaSilva
    """

    texto = unicodedata.normalize(
        "NFKD",
        nome.strip(),
    ).encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    partes = re.findall(
        r"[A-Za-z0-9]+",
        texto,
    )

    if not partes:
        raise ValueError(
            "Não foi possível gerar um identificador para o usuário."
        )

    identificador = "".join(
        parte[:1].upper() + parte[1:]
        for parte in partes
    )

    return "Usuario" + identificador

def gerar_id_filme(titulo, ano):
    """
    Gera um identificador RDF simples e previsível.

    Exemplo:
        O Auto da Compadecida, 2000
        -> OAutoDaCompadecida2000
    """

    texto = unicodedata.normalize(
        "NFKD",
        titulo.strip(),
    ).encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    partes = re.findall(
        r"[A-Za-z0-9]+",
        texto,
    )

    if not partes:
        raise ValueError(
            "Não foi possível gerar um identificador "
            "para o filme."
        )

    identificador = "".join(
        parte[:1].upper() + parte[1:]
        for parte in partes
    )

    return f"{identificador}{ano}"

def listar_opcoes_filme(graph):
    """
    Retorna indivíduos existentes que podem ser usados
    nas relações de um novo filme.
    """

    return {
        "generos": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Genero",
            )
        ],
        "diretores": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Diretor",
            )
        ],
        "atores": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Ator",
            )
        ],
        "roteiristas": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Roteirista",
            )
        ],
        "paises": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Pais",
            )
        ],
        "idiomas": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Idioma",
            )
        ],
    }

def listar_opcoes_preferencia(graph):
    """
    Retorna os indivíduos que podem ser escolhidos
    como preferências no cadastro de usuário.
    """

    return {
        "generos": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Genero",
            )
        ],
        "diretores": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Diretor",
            )
        ],
        "atores": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Ator",
            )
        ],
        "nacionalidades": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Pais",
            )
        ],
        "idiomas": [
            local_name(item)
            for item in listar_individuos(
                graph,
                "Idioma",
            )
        ],
    }

def registrar_usuario(
    nome,
    idade,
    email="",
    whatsapp="",
    outro_contato="",
    generos=None,
    diretores=None,
    atores=None,
    nacionalidades=None,
    idiomas=None,
):
    """
    Cria um novo indivíduo Usuario e persiste seus
    dados e preferências em app_data.ttl.
    """

    generos = generos or []
    diretores = diretores or []
    atores = atores or []
    nacionalidades = nacionalidades or []
    idiomas = idiomas or []

    preferencias = {
        "generos": generos,
        "diretores": diretores,
        "atores": atores,
        "nacionalidades": nacionalidades,
        "idiomas": idiomas,
    }

    validar_nome_usuario(nome)
    validar_idade_usuario(idade)

    validar_contato_usuario(
        email=email,
        whatsapp=whatsapp,
        outro_contato=outro_contato,
    )

    validar_preferencias_usuario(preferencias)

    graph = carregar_ontologia()

    usuario_id = gerar_id_usuario(nome)

    usuarios_existentes = {
        usuario["id"]
        for usuario in obter_usuarios(graph)
    }

    if usuario_id in usuarios_existentes:
        raise ValueError(
            f"O usuário '{nome}' já existe."
        )

    classe_usuario = encontrar_classe(
        graph,
        "Usuario",
    )

    usuario_uri = uri_novo_individuo(
        graph,
        classe_usuario,
        usuario_id,
    )

    data_graph = Graph()

    if APP_DATA_PATH.exists():
        data_graph.parse(
            APP_DATA_PATH,
            format="turtle",
        )

    # -----------------------------------------------------
    # Tipo
    # -----------------------------------------------------

    data_graph.add(
        (
            usuario_uri,
            RDF.type,
            OWL.NamedIndividual,
        )
    )

    data_graph.add(
        (
            usuario_uri,
            RDF.type,
            classe_usuario,
        )
    )

    # -----------------------------------------------------
    # Data properties
    # -----------------------------------------------------

    prop_nome = encontrar_entidade(
        graph,
        "nomeUsuario",
    )

    prop_idade = encontrar_entidade(
        graph,
        "idadeUsuario",
    )

    data_graph.add(
        (
            usuario_uri,
            prop_nome,
            Literal(
                nome.strip(),
                datatype=XSD.string,
            ),
        )
    )

    data_graph.add(
        (
            usuario_uri,
            prop_idade,
            Literal(
                idade,
                datatype=XSD.integer,
            ),
        )
    )

    contatos = {
        "emailUsuario": email,
        "whatsappUsuario": whatsapp,
        "outroContatoUsuario": outro_contato,
    }

    for propriedade_nome, valor in contatos.items():

        valor = str(valor).strip()

        if not valor:
            continue

        propriedade = encontrar_entidade(
            graph,
            propriedade_nome,
        )

        data_graph.add(
            (
                usuario_uri,
                propriedade,
                Literal(
                    valor,
                    datatype=XSD.string,
                ),
            )
        )

    # -----------------------------------------------------
    # Preferências
    # -----------------------------------------------------

    propriedades_preferencia = {
        "generos": "prefereGenero",
        "diretores": "prefereDiretor",
        "atores": "prefereAtor",
        "nacionalidades": "prefereNacionalidade",
        "idiomas": "prefereIdioma",
    }

    for categoria, valores in preferencias.items():

        propriedade = encontrar_entidade(
            graph,
            propriedades_preferencia[categoria],
        )

        for valor_id in valores:

            valor_uri = encontrar_entidade(
                graph,
                valor_id,
            )

            data_graph.add(
                (
                    usuario_uri,
                    propriedade,
                    valor_uri,
                )
            )

    data_graph.serialize(
        destination=APP_DATA_PATH,
        format="turtle",
    )

    return {
        "id": usuario_id,
        "nome": nome.strip(),
        "idade": idade,
        "preferencias": preferencias,
    }


def registrar_filme(
    titulo_original,
    ano_producao,
    generos,
    diretores,
    atores,
    titulo_portugues="",
    ano_lancamento=None,
    roteiristas=None,
    paises=None,
    idiomas=None,
):
    """
    Cria um novo indivíduo Filme ou FilmeDocumentario
    e persiste suas propriedades em app_data.ttl.
    """

    roteiristas = roteiristas or []
    paises = paises or []
    idiomas = idiomas or []

    titulo_original = titulo_original.strip()
    titulo_portugues = titulo_portugues.strip()

    validar_titulo_filme(
        titulo_original
    )

    validar_ano_filme(
        ano_producao
    )

    validar_relacoes_filme(
        generos=generos,
        diretores=diretores,
        atores=atores,
    )

    graph = carregar_ontologia()

    filme_id = gerar_id_filme(
        titulo_original,
        ano_producao,
    )

    filmes_existentes = {
        filme["id"]
        for filme in obter_filmes(graph)
    }

    if filme_id in filmes_existentes:
        raise ValueError(
            "Este filme já está cadastrado."
        )

    documentario = (
        "Documentario" in generos
    )

    if documentario:
        classe_filme = encontrar_classe(
            graph,
            "FilmeDocumentario",
        )
    else:
        classe_filme = encontrar_classe(
            graph,
            "Filme",
        )

    filme_uri = uri_novo_individuo(
        graph,
        classe_filme,
        filme_id,
    )

    data_graph = Graph()

    if APP_DATA_PATH.exists():
        data_graph.parse(
            APP_DATA_PATH,
            format="turtle",
        )

    # -----------------------------------------------------
    # Tipos
    # -----------------------------------------------------

    data_graph.add(
        (
            filme_uri,
            RDF.type,
            OWL.NamedIndividual,
        )
    )

    data_graph.add(
        (
            filme_uri,
            RDF.type,
            classe_filme,
        )
    )

    # -----------------------------------------------------
    # Data properties
    # -----------------------------------------------------

    propriedades_literais = {
        "tituloOriginal": (
            titulo_original,
            XSD.string,
        ),
        "anoProducao": (
            ano_producao,
            XSD.integer,
        ),
    }

    if titulo_portugues:
        propriedades_literais[
            "tituloPortugues"
        ] = (
            titulo_portugues,
            XSD.string,
        )

    if ano_lancamento is not None:
        propriedades_literais[
            "anoLancamento"
        ] = (
            int(ano_lancamento),
            XSD.integer,
        )

    for nome_prop, (
        valor,
        datatype,
    ) in propriedades_literais.items():

        propriedade = encontrar_entidade(
            graph,
            nome_prop,
        )

        data_graph.add(
            (
                filme_uri,
                propriedade,
                Literal(
                    valor,
                    datatype=datatype,
                ),
            )
        )

    # -----------------------------------------------------
    # Object properties
    # -----------------------------------------------------

    relacoes = {
        "pertenceAoGenero": generos,
        "temDiretor": diretores,
        "temAtor": atores,
        "temRoteirista": roteiristas,
        "temNacionalidadeFilme": paises,
        "temIdiomaFilme": idiomas,
    }

    for nome_prop, valores in relacoes.items():

        propriedade = encontrar_entidade(
            graph,
            nome_prop,
        )

        for valor_id in valores:

            valor_uri = encontrar_entidade(
                graph,
                valor_id,
            )

            data_graph.add(
                (
                    filme_uri,
                    propriedade,
                    valor_uri,
                )
            )

    data_graph.serialize(
        destination=APP_DATA_PATH,
        format="turtle",
    )

    return {
        "id": filme_id,
        "titulo": titulo_original,
        "ano": ano_producao,
        "documentario": documentario,
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