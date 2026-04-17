from pydantic import BaseModel, Field


class Connection(BaseModel):
    zone1: str  # name already verified in the Hub class
    zone2: str
    max_link_capacity: int = Field(default=1, gt=0)

    def has_hub(self, hub_name: str) -> bool:
        return hub_name in (self.zone1, self.zone2)
