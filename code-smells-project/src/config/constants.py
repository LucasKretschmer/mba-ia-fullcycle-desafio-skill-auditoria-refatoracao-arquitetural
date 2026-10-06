VERSAO_API = "1.0.0"

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO = (STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)

TIPO_CLIENTE = "cliente"
TIPO_ADMIN = "admin"

FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
