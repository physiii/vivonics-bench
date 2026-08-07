from projector import Projector, ProjectorConfig


class FakeController:
    def __init__(self) -> None:
        self.calls: list[dict[str, int]] = []

    def set_levels(self, **levels: int) -> dict:
        self.calls.append(levels)
        return {"ok": True}

    def off(self) -> dict:
        self.calls.append({"red": 0, "green": 0, "infrared": 0, "blue": 0})
        return {"ok": True}


def test_controller_projector_maps_named_channels_without_opening_gpio() -> None:
    controller = FakeController()
    projector = Projector(ProjectorConfig(light_driver="controller"), controller)  # type: ignore[arg-type]

    projector.open()
    projector.show_color(10, 20, 40, infrared_level=30)
    projector.close()

    assert projector.driver_name == "none"
    assert controller.calls == [
        {"red": 0, "green": 0, "infrared": 0, "blue": 0},
        {"red": 10, "green": 20, "infrared": 30, "blue": 40},
        {"red": 0, "green": 0, "infrared": 0, "blue": 0},
    ]
