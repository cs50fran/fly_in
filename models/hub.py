import os
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

class ZoneType(str, Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class Hub(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.normal  # defaults to normal
    color: str | None = None
    max_drones: int = Field(default=1, gt=0)

    @field_validator("name")
    @classmethod
    def validate_hub_name(cls, v: str) -> str:
        if "-" in v or " " in v:
            raise ValueError("Hub name must not contain dashes or spaces")
        return v

    @field_validator("color")
    @classmethod
    def validate_hub_color(cls, v: str) -> str:
        import pygame
        if v:
            if v not in pygame.colordict.THECOLORS and v != "rainbow":
                raise ValueError(f"'{v}' is not a valid pygame color name")
        return v

    def get_cost(self) -> int:
        if self.zone_type == ZoneType.restricted:
            return 2
        return 1
