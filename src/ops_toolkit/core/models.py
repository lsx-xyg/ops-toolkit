from dataclasses import dataclass, field
from typing import Any


@dataclass
class Resource:
    id: str
    label: str
    created_at: Any = 0
    raw: dict = field(default_factory=dict)
