import pytest
import os
from validate_maps import validate_map

ERROR_MAPS_DIR = os.path.join(os.path.dirname(__file__), "../maps/error")


def get_error_maps() -> list[str]:
    return [
        os.path.join(ERROR_MAPS_DIR, f)
        for f in os.listdir(ERROR_MAPS_DIR)
        if f.endswith(".txt")
    ]


@pytest.mark.parametrize("map_path", get_error_maps())
def test_error_maps_raise(map_path: str) -> None:
    with pytest.raises((ValueError, Exception)):
        validate_map(map_path)
