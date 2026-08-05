import pytest

from src.ontology_service import (
    carregar_ontologia,
    obter_filmes,
    obter_usuarios,
    obter_avaliacoes,
    gerar_id_usuario,
    gerar_id_filme,
)

from src.recommender import (
    calcular_score_conteudo,
    calcular_similaridade_usuarios,
)

from src.validators import (
    validar_nota,
    validar_contato_usuario,
    validar_relacoes_filme,
)


# =========================================================
# Ontologia / RDF
# =========================================================

def test_ontologia_carrega():
    graph = carregar_ontologia()

    assert len(graph) > 0


def test_quantidades_minimas_da_base():
    """
    Usamos >= porque app_data.ttl pode conter novos
    usuários, filmes e avaliações cadastrados pela aplicação.
    """
    graph = carregar_ontologia()

    filmes = obter_filmes(graph)
    usuarios = obter_usuarios(graph)
    avaliacoes = obter_avaliacoes(graph)

    assert len(filmes) >= 15
    assert len(usuarios) >= 9
    assert len(avaliacoes) >= 30


def test_entidades_conhecidas_estao_presentes():
    graph = carregar_ontologia()

    filmes = obter_filmes(graph)
    usuarios = obter_usuarios(graph)

    ids_filmes = {
        filme["id"]
        for filme in filmes
    }

    ids_usuarios = {
        usuario["id"]
        for usuario in usuarios
    }

    assert "AOrigem" in ids_filmes
    assert "CentralDoBrasil" in ids_filmes
    assert "UsuarioAna" in ids_usuarios


def test_metadados_de_a_origem():
    graph = carregar_ontologia()

    filmes = obter_filmes(graph)

    a_origem = next(
        filme
        for filme in filmes
        if filme["id"] == "AOrigem"
    )

    assert a_origem["titulo_original"] == "Inception"
    assert "ChristopherNolan" in a_origem["diretores"]
    assert "LeonardoDiCaprio" in a_origem["atores"]
    assert "FiccaoCientifica" in a_origem["generos"]
    assert "Ingles" in a_origem["idiomas"]


# =========================================================
# Geração de IDs
# =========================================================

def test_geracao_id_usuario_remove_acentos():
    resultado = gerar_id_usuario(
        "João da Silva"
    )

    assert resultado == "UsuarioJoaoDaSilva"


def test_geracao_id_filme_inclui_ano():
    resultado = gerar_id_filme(
        "O Auto da Compadecida",
        2000,
    )

    assert resultado == "OAutoDaCompadecida2000"


# =========================================================
# Validações
# =========================================================

def test_nota_valida():
    assert validar_nota(5) is True


def test_nota_maior_que_cinco_falha():
    with pytest.raises(
        ValueError,
        match="entre 1 e 5",
    ):
        validar_nota(6)


def test_usuario_sem_contato_falha():
    with pytest.raises(ValueError):
        validar_contato_usuario(
            email="",
            whatsapp="",
            outro_contato="",
        )


def test_documentario_com_ator_falha():
    with pytest.raises(
        ValueError,
        match="Documentário",
    ):
        validar_relacoes_filme(
            generos=["Documentario"],
            diretores=["PetraCosta"],
            atores=["FernandaTorres"],
        )


def test_documentario_com_um_diretor_sem_ator_e_valido():
    assert validar_relacoes_filme(
        generos=["Documentario"],
        diretores=["PetraCosta"],
        atores=[],
    ) is True


def test_filme_comum_sem_ator_falha():
    with pytest.raises(ValueError):
        validar_relacoes_filme(
            generos=["Drama"],
            diretores=["WalterSalles"],
            atores=[],
        )


# =========================================================
# Recomendação baseada em conteúdo
# =========================================================

def test_score_conteudo_match_parcial():
    usuario = {
        "preferencias": {
            "generos": ["Drama"],
            "diretores": ["WalterSalles"],
            "atores": ["FernandaTorres"],
            "nacionalidades": ["Brasil"],
            "idiomas": ["Portugues"],
        }
    }

    filme = {
        "generos": ["Drama"],
        "diretores": ["WalterSalles"],
        "atores": [],
        "paises": [],
        "idiomas": [],
    }

    score, motivos = calcular_score_conteudo(
        usuario,
        filme,
    )

    # 0.30 gênero + 0.25 diretor
    assert score == pytest.approx(0.55)

    assert any(
        "Drama" in motivo
        for motivo in motivos
    )

    assert any(
        "WalterSalles" in motivo
        for motivo in motivos
    )


def test_score_conteudo_renormaliza_preferencias_ausentes():
    """
    Se o usuário não declarou preferência de ator,
    esse peso não deve penalizá-lo.
    """

    usuario = {
        "preferencias": {
            "generos": ["Drama"],
            "diretores": ["WalterSalles"],
            "atores": [],
            "nacionalidades": ["Brasil"],
            "idiomas": ["Portugues"],
        }
    }

    filme = {
        "generos": ["Drama"],
        "diretores": ["WalterSalles"],
        "atores": [],
        "paises": ["Brasil"],
        "idiomas": ["Portugues"],
    }

    score, _ = calcular_score_conteudo(
        usuario,
        filme,
    )

    assert score == pytest.approx(1.0)


# =========================================================
# Filtragem colaborativa
# =========================================================

def test_similaridade_perfeita_com_tres_filmes():
    matriz = {
        "UsuarioA": {
            "Filme1": 5,
            "Filme2": 4,
            "Filme3": 3,
        },
        "UsuarioB": {
            "Filme1": 5,
            "Filme2": 4,
            "Filme3": 3,
        },
    }

    similaridade, comuns = (
        calcular_similaridade_usuarios(
            "UsuarioA",
            "UsuarioB",
            matriz,
        )
    )

    assert comuns == 3
    assert similaridade == pytest.approx(1.0)


def test_similaridade_com_apenas_um_filme_e_insuficiente():
    matriz = {
        "UsuarioA": {
            "Filme1": 5,
            "Filme2": 4,
        },
        "UsuarioB": {
            "Filme1": 5,
            "Filme3": 4,
        },
    }

    similaridade, comuns = (
        calcular_similaridade_usuarios(
            "UsuarioA",
            "UsuarioB",
            matriz,
        )
    )

    assert comuns == 1
    assert similaridade == pytest.approx(0.0)