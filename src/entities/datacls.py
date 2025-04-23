from dataclasses import dataclass, fields


@dataclass
class GraphFilter:
    def has_at_least_one_filter(self) -> bool:
        """Проверяет, что хотя бы одно поле не пустое"""
        return any(bool(getattr(self, field.name)) for field in fields(self))
