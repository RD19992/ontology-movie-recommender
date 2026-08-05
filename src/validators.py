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