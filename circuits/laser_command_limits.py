"""Per-channel laser PWM command-limiter parts and current math."""
from __future__ import annotations

from dataclasses import dataclass


PWM_FULL_SCALE_V = 3.3
PWM_TOP_OHMS = 10_000.0
PWM_TOP_TOLERANCE = 0.01
PWM_PULLDOWN_TOLERANCE = 0.01
SENSE_OHMS = 10.0


@dataclass(frozen=True)
class LaserCommandLimiter:
    color: str
    sheet: str
    value: str
    resistance_ohms: float
    mpn: str
    lcsc: str
    source_note: str

    @property
    def command_voltage_v(self) -> float:
        return command_voltage_v(self.resistance_ohms)

    @property
    def command_current_a(self) -> float:
        return command_current_a(self.resistance_ohms)

    @property
    def worst_case_current_a(self) -> float:
        return command_current_a(
            self.resistance_ohms * (1.0 + PWM_PULLDOWN_TOLERANCE),
            top_ohms=PWM_TOP_OHMS * (1.0 - PWM_TOP_TOLERANCE),
        )


def command_voltage_v(pulldown_ohms: float, *, top_ohms: float = PWM_TOP_OHMS) -> float:
    return PWM_FULL_SCALE_V * pulldown_ohms / (top_ohms + pulldown_ohms)


def command_current_a(pulldown_ohms: float, *, top_ohms: float = PWM_TOP_OHMS) -> float:
    return command_voltage_v(pulldown_ohms, top_ohms=top_ohms) / SENSE_OHMS


LASER_COMMAND_LIMITERS = (
    LaserCommandLimiter(
        color="IR",
        sheet="LASER_IR",
        value="1.3k LIMIT",
        resistance_ohms=1_300.0,
        mpn="0603WAF1301T5E",
        lcsc="C22767",
        source_note="UNI-ROYAL 0603 1% 100mW 1.3k, JLC/LCSC C22767",
    ),
    LaserCommandLimiter(
        color="RED",
        sheet="LASER_RED",
        value="750R LIMIT",
        resistance_ohms=750.0,
        mpn="0603WAF7500T5E",
        lcsc="C23241",
        source_note="UNI-ROYAL 0603 1% 100mW 750R, JLC/LCSC C23241",
    ),
    LaserCommandLimiter(
        color="GREEN",
        sheet="LASER_GREEN",
        value="3k LIMIT",
        resistance_ohms=3_000.0,
        mpn="0603WAF3001T5E",
        lcsc="C4211",
        source_note="UNI-ROYAL 0603 1% 100mW 3k, JLC/LCSC C4211",
    ),
    LaserCommandLimiter(
        color="BLUE",
        sheet="LASER_BLUE",
        value="4.7k LIMIT",
        resistance_ohms=4_700.0,
        mpn="0603WAF4701T5E",
        lcsc="C23162",
        source_note="UNI-ROYAL 0603 1% 100mW 4.7k, JLC/LCSC C23162",
    ),
)

LIMITER_BY_COLOR = {limiter.color: limiter for limiter in LASER_COMMAND_LIMITERS}
LIMITER_BY_SHEET = {limiter.sheet: limiter for limiter in LASER_COMMAND_LIMITERS}


def limiter_for_color(color: str) -> LaserCommandLimiter:
    try:
        return LIMITER_BY_COLOR[color]
    except KeyError as exc:
        raise KeyError(f"unknown laser command-limiter color {color!r}") from exc


def limiter_for_sheet(sheet: str) -> LaserCommandLimiter:
    normalized = sheet.strip("/")
    try:
        return LIMITER_BY_SHEET[normalized]
    except KeyError as exc:
        raise KeyError(f"unknown laser command-limiter sheet {sheet!r}") from exc


def all_channel_command_limit_current_a() -> float:
    return sum(limiter.command_current_a for limiter in LASER_COMMAND_LIMITERS)


def all_channel_worst_case_command_limit_current_a() -> float:
    return sum(limiter.worst_case_current_a for limiter in LASER_COMMAND_LIMITERS)
