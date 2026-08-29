from dataclasses import dataclass

MODULE_ICONS: dict[str, str] = {
    "tasks": "📋",
    "finances": "💰",
    "food": "🍱",
    "dates": "🌹",
}


@dataclass(frozen=True)
class SystemRef:
    module: str
    detail: str

    @classmethod
    def parse(cls, entity_str: str) -> "SystemRef":
        parts = entity_str.split(":", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"Invalid system_ref_entity: {entity_str!r}")
        return cls(module=parts[0], detail=parts[1])

    def __str__(self) -> str:
        return f"{self.module}:{self.detail}"


def module_icon(system_ref: SystemRef | None) -> str:
    if system_ref is None:
        return ""
    return MODULE_ICONS.get(system_ref.module, "")
