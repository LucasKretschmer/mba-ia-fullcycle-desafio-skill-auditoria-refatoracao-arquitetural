import re

from src.config.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO,
)
from src.utils.errors import ValidationError

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _texto(valor):
    return isinstance(valor, str) and valor.strip() != ""


def exigir_json(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def validar_produto(dados):
    exigir_json(dados)
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao") or ""
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not _numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _inteiro(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def converter_preco(valor, parametro):
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"Parâmetro {parametro} inválido")


def validar_usuario(dados):
    exigir_json(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not (_texto(nome) and _texto(email) and _texto(senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    email = email.strip()
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    return {"nome": nome.strip(), "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not (_texto(email) and _texto(senha)):
        raise ValidationError("Email e senha são obrigatórios")
    return email.strip(), senha


def validar_pedido(dados):
    exigir_json(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens") or []

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _inteiro(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list) or not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens_validos = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item de pedido inválido")
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if not _inteiro(produto_id) or not _inteiro(quantidade) or quantidade <= 0:
            raise ValidationError("Item de pedido inválido: informe produto_id e quantidade positiva")
        itens_validos.append({"produto_id": produto_id, "quantidade": quantidade})
    return usuario_id, itens_validos


def validar_status(dados):
    status = dados.get("status", "") if isinstance(dados, dict) else ""
    if status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    return status
