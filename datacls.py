from dataclasses import dataclass


@dataclass
class FilterOption:
    label: str
    value: str


@dataclass
class FilterItem:
    name: str
    label: str
    options: list[FilterOption]
    isMultiSelect: bool | None = None
