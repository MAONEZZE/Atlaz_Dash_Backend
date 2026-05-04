from app.utils.normalize_text import normalize_for_compare

FIELD_MAP: dict[str, list[str]] = {
    "nome": ["nome", "cliente", "lead", "contato", "responsável", "responsavel"],
    "cargo": ["cargo", "função", "funcao", "posição", "posicao"],
    "closer": ["closer", "vendedor", "responsável venda", "responsavel venda"],
    "sdr": ["sdr", "pré-vendedor", "pre vendedor", "responsável pré-venda", "responsavel pre venda"],
    "canal": ["canal", "origem", "fonte"],
    "produto": ["produto", "oferta", "mentoria", "serviço", "servico"],
    "status": ["status", "situação", "situacao"],
    "stage": ["stage", "etapa", "fase"],
    "data": ["data", "data da venda", "data fechamento", "vencimento"],
    "valor": ["valor", "receita", "faturamento", "venda", "valor vendido"],
    "bruto": ["bruto", "receita bruta", "valor bruto"],
    "liquido": ["liquido", "líquido", "receita líquida", "receita liquida", "valor liquido"],
    "comissao_sdr": ["comissao sdr", "comissão sdr"],
    "comissao_closer": ["comissao closer", "comissão closer"],
    "reunioes_agendadas": ["reuniões agendadas", "reunioes agendadas"],
    "reunioes_realizadas": ["reuniões realizadas", "reunioes realizadas"],
    "ligacoes_realizadas": ["ligações realizadas", "ligacoes realizadas"],
    "ligacoes_agendadas": ["ligações agendadas", "ligacoes agendadas"],
    "numeros_captados": ["números captados", "numeros captados", "números obtidos", "numeros obtidos"],
    "conexoes_enviadas": ["conexões enviadas", "conexoes enviadas"],
    "conexoes_aceitas": ["conexões aceitas", "conexoes aceitas"],
    "inmails_enviados": ["inmails enviados", "inmails", "inmail"],
    "followups": ["follow-ups", "followups", "follow ups"],
    "indicacoes": ["indicações", "indicacoes"],
    "indicacoes_captadas": ["indicações captadas", "indicacoes captadas"],
    "abordagens": ["abordagens"],
    "meta_mensal": ["meta mensal", "meta_mensal", "meta faturamento", "faturamento meta"],
    "meta_numeros": ["meta números", "meta numeros", "meta_numeros"],
    "meta_leads": ["meta leads", "meta_leads"],
    "meta_ligacoes": ["meta ligações", "meta ligacoes", "meta_ligacoes"],
    "meta_reunioes": ["meta reuniões", "meta reunioes", "meta_reunioes"],
    "meta_indicacoes": ["meta indicações", "meta indicacoes", "meta_indicacoes"],
}

# Person-name aliases — key is normalized compare form, value is canonical display name
NAME_ALIASES: dict[str, str] = {
    "jonny": "Jonathan",
    "johnny": "Jonathan",
    "jon": "Jonathan",
    "jacob": "Jacob",
    "jake": "Jacob",
    "alex": "Alex",
    "alexandre": "Alex",
    "jennifer": "Jennifer",
    "jenny": "Jennifer",
    "tayrone": "Tayrone",
}

_FIELD_MAP_NORMALIZED: dict[str, str] = {
    normalize_for_compare(alias): canonical
    for canonical, aliases in FIELD_MAP.items()
    for alias in aliases
}

_NAME_ALIASES_NORMALIZED: dict[str, str] = {
    normalize_for_compare(k): v for k, v in NAME_ALIASES.items()
}


def resolve_field(label: str) -> str | None:
    """Return canonical field key for a sheet header label, or None if unknown."""
    return _FIELD_MAP_NORMALIZED.get(normalize_for_compare(label))


def resolve_name(name: str) -> str:
    """Return canonical display name. Unknown names returned unchanged (title-cased)."""
    if not name or not name.strip():
        return name
    key = normalize_for_compare(name.strip())
    return _NAME_ALIASES_NORMALIZED.get(key, name.strip().title())
