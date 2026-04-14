import os
from enum import Enum

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame  # type: ignore :is not installed
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ZoneType(str, Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class Hub(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str  #ok
    x: int  #ok
    y: int  #ok
    zone_type: ZoneType = ZoneType.normal  #defaults to normal
    color: str| None = None  #ok
    max_drones: int = Field(default=1, gt=0)
    is_start: bool = False  #ok
    is_end: bool = False  #ok

    @field_validator("name")
    @classmethod
    def validate_hub_name(cls, v: str) -> str:
        if "-" in v or " " in v:
            raise ValueError("Hub name must not contain dashes or spaces")
        return v

    @field_validator("color")
    @classmethod  # There is no self to call, so we use a classmethod
    def validate_hub_color(cls, v: str) -> str:
        if v:
            try:
                pygame.Color(v)
            except ValueError:
                raise ValueError(f"'{v}' is not a valid pygame color name")
        return v

    def get_cost(self) -> int:
        if self.zone_type == ZoneType.restricted:
            return 2
        return 1

