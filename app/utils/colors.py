DEFAULT_CHANNEL_COLORS: dict[str, tuple[str, str]] = {
    "linkedin": ("#0077B5", "#005885"),
    "instagram": ("#E1306C", "#B02356"),
    "indicacao": ("#F59E0B", "#D97706"),
    "whatsapp": ("#25D366", "#1DA850"),
    "outros": ("#6B7280", "#4B5563"),
}

DEFAULT_COLOR = "#6B7280"
DEFAULT_COLOR_ACC = "#4B5563"


def channel_color(channel_key: str) -> str:
    return DEFAULT_CHANNEL_COLORS.get(channel_key, (DEFAULT_COLOR, DEFAULT_COLOR_ACC))[0]


def channel_color_acc(channel_key: str) -> str:
    return DEFAULT_CHANNEL_COLORS.get(channel_key, (DEFAULT_COLOR, DEFAULT_COLOR_ACC))[1]
