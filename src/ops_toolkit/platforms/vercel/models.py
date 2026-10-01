from dataclasses import dataclass, field


@dataclass
class Deployment:
    id: str
    url: str
    created_at: float
    raw: dict = field(default_factory=dict)
