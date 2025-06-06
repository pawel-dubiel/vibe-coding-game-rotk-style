from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List


@dataclass
class Location:
    """A point on the campaign map."""
    name: str
    pos: Tuple[int, int]


@dataclass
class Army:
    """An army travelling on the map."""
    name: str
    location: str
    player_id: int
    move_remaining: int = 0
    target: Optional[str] = None


class CampaignMap:
    """Simple campaign map tracking armies and locations."""

    def __init__(self) -> None:
        self.locations: Dict[str, Location] = {}
        self.armies: Dict[str, Army] = {}

    def add_location(self, name: str, x: int, y: int) -> None:
        self.locations[name] = Location(name, (x, y))

    def add_army(self, name: str, location: str, player_id: int) -> None:
        if location not in self.locations:
            raise ValueError(f"Unknown location: {location}")
        self.armies[name] = Army(name=name, location=location, player_id=player_id)

    def distance(self, origin: str, destination: str) -> int:
        p1 = self.locations[origin].pos
        p2 = self.locations[destination].pos
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def move_army(self, army_name: str, destination: str) -> None:
        if destination not in self.locations:
            raise ValueError(f"Unknown destination: {destination}")
        army = self.armies[army_name]
        if destination == army.location:
            return
        travel_time = self.distance(army.location, destination)
        army.move_remaining = travel_time
        army.target = destination

    def advance_turn(self) -> None:
        """Advance all armies by one turn."""
        for army in self.armies.values():
            if army.move_remaining > 0:
                army.move_remaining -= 1
                if army.move_remaining == 0 and army.target:
                    army.location = army.target
                    army.target = None

    def armies_at_location(self, location: str) -> List[Army]:
        return [a for a in self.armies.values() if a.location == location]

    def check_for_battle(self) -> Optional[str]:
        """Return location name if opposing armies occupy the same spot."""
        for name in self.locations:
            armies = self.armies_at_location(name)
            players = {a.player_id for a in armies}
            if len(players) > 1:
                return name
        return None


def create_poland_campaign() -> CampaignMap:
    """Create a minimal Poland map with one neighbour for testing."""
    cmap = CampaignMap()
    cmap.add_location("Gniezno", 3, 3)
    cmap.add_location("Neighbor Country", 8, 3)
    cmap.add_army("Polish Army", "Gniezno", player_id=1)
    cmap.add_army("Enemy Army", "Neighbor Country", player_id=2)
    return cmap
