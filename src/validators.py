def validar_nota(nota):
    """
    Valida nota de filme na escala de 1 a 5.
    """
    if not isinstance(nota, (int, float)):
        raise ValueError("A nota deve ser numérica.")

    if nota < 1 or nota > 5:
        raise ValueError("A nota deve estar entre 1 e 5.")

    return True


def validar_usuario_existe(usuario_id, usuarios):
    """
    Verifica se o usuário existe na base.
    """
    ids = {usuario["id"] for usuario in usuarios}

    if usuario_id not in ids:
        raise ValueError(
            f"Usuário '{usuario_id}' não encontrado."
        )

    return True


def validar_filme_existe(filme_id, filmes):
    """
    Verifica se o filme existe na base.
    """
    ids = {filme["id"] for filme in filmes}

    if filme_id not in ids:
        raise ValueError(
            f"Filme '{filme_id}' não encontrado."
        )

    return True

def validar_nome_usuario(nome):
    """
    Nome deve conter pelo menos 2 caracteres úteis.
    """
    if not isinstance(nome, str):
        raise ValueError("O nome do usuário deve ser texto.")

    if len(nome.strip()) < 2:
        raise ValueError("Informe um nome de usuário válido.")

    return True


def validar_idade_usuario(idade):
    """
    Idade deve ser inteira e positiva.
    """
    if not isinstance(idade, int):
        raise ValueError("A idade deve ser um número inteiro.")

    if idade <= 0 or idade > 120:
        raise ValueError("Informe uma idade válida.")

    return True


def validar_contato_usuario(
    email="",
    whatsapp="",
    outro_contato="",
):
    """
    O usuário deve possuir pelo menos um canal de contato.
    """
    contatos = [
        str(email).strip(),
        str(whatsapp).strip(),
        str(outro_contato).strip(),
    ]

    if not any(contatos):
        raise ValueError(
            "Informe pelo menos um canal de contato: "
            "e-mail, WhatsApp ou outro contato."
        )

    return True


def validar_preferencias_usuario(preferencias):
    """
    Exige pelo menos uma preferência para que um novo usuário
    possa receber recomendações por conteúdo imediatamente.
    """
    if not any(preferencias.values()):
        raise ValueError(
            "Selecione pelo menos uma preferência."
        )

    return True

def validar_titulo_filme(titulo):
    """Título original é obrigatório."""
    if not isinstance(titulo, str):
        raise ValueError("O título deve ser texto.")

    if len(titulo.strip()) < 1:
        raise ValueError("Informe o título original do filme.")

    return True


def validar_ano_filme(ano):
    """Validação operacional simples do ano."""
    if not isinstance(ano, int):
        raise ValueError("O ano deve ser um número inteiro.")

    if ano < 1888 or ano > 2100:
        raise ValueError("Informe um ano de produção válido.")

    return True


def validar_relacoes_filme(
    generos,
    diretores,
    atores,
):
    """
    Regras principais da ontologia/aplicação.

    - Todo filme tem pelo menos um gênero.
    - Todo filme tem pelo menos um diretor.
    - Documentário tem exatamente um diretor e nenhum ator.
    - Filme não documentário tem pelo menos um ator.
    """
    if not generos:
        raise ValueError(
            "Selecione pelo menos um gênero."
        )

    if not diretores:
        raise ValueError(
            "Selecione pelo menos um diretor."
        )

    documentario = "Documentario" in generos

    if documentario:
        if len(diretores) != 1:
            raise ValueError(
                "Documentário deve ter exatamente um diretor."
            )

        if atores:
            raise ValueError(
                "Documentário não deve possuir ator "
                "nesta modelagem."
            )

    else:
        if not atores:
            raise ValueError(
                "Filme não documentário deve possuir "
                "pelo menos um ator."
            )

    return True