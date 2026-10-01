from dataclasses import dataclass, field


@dataclass
class Release:
    id: str
    tag: str
    name: str
    created_at: str
    raw: dict = field(default_factory=dict)

    @property
    def label(self):
        return f"{self.tag} ({self.name})" if self.name else self.tag
