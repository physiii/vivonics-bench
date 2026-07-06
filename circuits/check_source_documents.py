#!/usr/bin/env python3
"""Check that cited bench laser-controller source documents are present.

This gate deliberately separates hard evidence from unresolved sourcing risks:

* required primary URLs and required local artifacts fail the run if missing;
* secondary/distributor URLs and known source conflicts are reported as warnings.

It does not prove that the cited documents are the latest revision or that every
package drawing has been visually reviewed. It makes missing evidence visible in
the same review wrapper that checks the generated schematic and PCB.
Required online sources may rate-limit scripted probes; HTTP 429 is reported as
a warning because the quote/upload flow remains the authoritative live check.
"""
from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
TIMEOUT_S = 12
READ_BYTES = 4096
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


@dataclass(frozen=True)
class OnlineEvidence:
    label: str
    url: str
    required: bool
    expect_pdf: bool = False
    note: str = ""


@dataclass(frozen=True)
class LocalEvidence:
    label: str
    path: str
    min_bytes: int
    note: str = ""


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    detail: str


REQUIRED_ONLINE = [
    OnlineEvidence(
        "JLCPCB PCB capabilities",
        "https://jlcpcb.com/capabilities/pcb-capabilities",
        True,
    ),
    OnlineEvidence(
        "Espressif ESP32-S3-WROOM-1/WROOM-1U datasheet",
        "https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "Espressif ESP32-S3 series datasheet",
        "https://documentation.espressif.com/esp32-s3_datasheet_en.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "Espressif ESP32-S3 hardware design guidelines",
        "https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "Silicon Labs CP2102N datasheet",
        "https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "JLC/LCSC Mini-B C53207143 assembly source",
        "https://jlcpcb.com/partdetail/BXCONN-MINI_USB5P/C53207143",
        True,
    ),
    OnlineEvidence(
        "Espressif ESP-IDF ESP32-S3 ADC guide",
        "https://docs.espressif.com/projects/esp-idf/en/v4.4/esp32s3/api-reference/peripherals/adc.html",
        True,
    ),
    OnlineEvidence(
        "TI OPA380 datasheet",
        "https://www.ti.com/lit/ds/symlink/opa380.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "TI TLV9001 datasheet",
        "https://www.ti.com/lit/ds/symlink/tlv9001.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "Diodes AP2112 datasheet",
        "https://www.diodes.com/assets/Datasheets/AP2112.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "Diodes AP63200/AP63201/AP63203/AP63205 datasheet",
        "https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "ams OSRAM SFH 2201 A01 datasheet",
        "https://look.ams-osram.com/m/151c0967b1d4864e/original/SFH-2201-A01.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "Bourns 3224 datasheet",
        "https://www.bourns.com/pdfs/3224.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "US-Lasers D6505I 650nm 5mW source page",
        "http://www.us-lasers.com/d650nm5m.htm",
        True,
    ),
    OnlineEvidence(
        "US-Lasers D7805I 780nm 5mW source page",
        "http://www.us-lasers.com/n780nm5m.htm",
        True,
    ),
    OnlineEvidence(
        "ams OSRAM PLT5 520EB_P datasheet",
        "https://look.ams-osram.com/m/650bf4d7f1f7e736/original/PLT5-520EB_P.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "ams OSRAM PLT5 450GB datasheet",
        "https://look.ams-osram.com/m/29170f7edbc7cb46/original/PLT5-450GB.pdf",
        True,
        expect_pdf=True,
    ),
    OnlineEvidence(
        "Samsung CL05B104KO5NNN 100nF MLCC page",
        "https://product.samsungsem.com/mlcc/CL05B104KO5NNN.do",
        True,
    ),
    OnlineEvidence(
        "Samsung CL05A105KA5NQN 1uF MLCC page",
        "https://product.samsungsem.com/mlcc/CL05A105KA5NQN.do",
        True,
    ),
    OnlineEvidence(
        "Samsung CL21A106KAYNNN 10uF MLCC page",
        "https://product.samsungsem.com/mlcc/CL21A106KAYNNN.do",
        True,
    ),
    OnlineEvidence(
        "Yageo CC0603JRNPO9BN100 specsheet",
        "https://yageogroup.com/download/specsheet/CC0603JRNPO9BN100",
        True,
    ),
]


WARNING_ONLINE = [
    OnlineEvidence(
        "Alpha & Omega AO3400A datasheet",
        "https://www.aosmd.com/res/data_sheets/AO3400A.pdf",
        False,
        expect_pdf=True,
        note=(
            "Primary source reachable from this shell; manual release-time latest-revision "
            "verification remains required."
        ),
    ),
    OnlineEvidence(
        "JLCPCB via-design article",
        "https://jlcpcb.com/blog/pcb-via-design-best-practices",
        False,
        note="Advisory article only; JLCPCB quote capability page wins.",
    ),
    OnlineEvidence(
        "Vishay SS12-SS16 family datasheet",
        "https://www.vishay.com/doc/?88746=",
        False,
        note="Family reference only; current C2480 order identity is captured in the 2026-07-04 signoff.",
    ),
    OnlineEvidence(
        "LCSC C2480 SS14 order page",
        "https://www.lcsc.com/product-detail/Schottky-Barrier-Diodes-SBD_MDD-Microdiode-Electronics-SS14_C2480.html",
        False,
        note="Distributor/order source matching the 2026-07-04 C2480 MDD SS14 signoff.",
    ),
    OnlineEvidence(
        "JLCPCB C408410 MWSA0503S-4R7MT inductor page",
        "https://jlcpcb.com/partdetail/Sunlord-MWSA0503S4R7MT/C408410",
        False,
        note="Distributor/order source for the AP63205 4.7uH inductor; final AVL should retain a manufacturer datasheet copy.",
    ),
    OnlineEvidence(
        "JLCPCB C98364 WPN4020H100MT inductor page",
        "https://jlcpcb.com/partdetail/Sunlord-WPN4020H100MT/C98364",
        False,
        note="Distributor/order source for the AP63200 10uH inductor; final AVL should retain a manufacturer datasheet copy.",
    ),
    OnlineEvidence(
        "Wuerth Mini/Micro USB family page",
        "https://www.we-online.com/en/components/products/INPUT_OUTPUT_WR_USB_MINI_MICRO",
        False,
        note="Family/product page for the KiCad footprint naming lineage; active JLC assembly metadata is C53207143.",
    ),
    OnlineEvidence(
        "Farnell mirror of Wuerth 65100516121 drawing",
        "https://www.farnell.com/datasheets/1442461.pdf",
        False,
        expect_pdf=True,
        note="Distributor mirror only; the official Wuerth drawing URL is the required source.",
    ),
    OnlineEvidence(
        "LCSC C2907002 FRC0603F1001TS 1k resistor page",
        "https://www.lcsc.com/product-detail/C2907002.html",
        False,
        note="Distributor/order source for active 1k 0603 passive rating evidence.",
    ),
    OnlineEvidence(
        "JLCPCB C22984 30k resistor page",
        "https://jlcpcb.com/partdetail/0603WAF3002T5E/C22984",
        False,
        note="Distributor/order source for passive rating evidence.",
    ),
    OnlineEvidence(
        "LCSC C844918 CRCW060310K0FKEA 10k resistor page",
        "https://www.lcsc.com/product-detail/C844918.html",
        False,
        note="Distributor/order source for active 10k 0603 passive rating evidence.",
    ),
    OnlineEvidence(
        "JLCPCB C103446 RTT032400FTP 240 ohm resistor page",
        "https://jlcpcb.com/partdetail/RALEC-RTT032400FTP/C103446",
        False,
        note="Distributor/order source for active 240 ohm monitor-PD sense resistor evidence.",
    ),
    OnlineEvidence(
        "JLCPCB C22908 0603WAF2491T5E 2.49k resistor page",
        "https://jlcpcb.com/partdetail/UniroyalElec-0603WAF2491T5E/C22908",
        False,
        note="Distributor/order source for active 2.49k monitor-PD bias resistor evidence.",
    ),
    OnlineEvidence(
        "JLCPCB C242011 100CE22FS+P electrolytic page",
        "https://jlcpcb.com/partdetail/240857-100CE22FSP/C242011",
        False,
        note="Distributor/order source for active 22uF 100V VIN_24V bulk electrolytic evidence.",
    ),
    OnlineEvidence(
        "LRC L8050QLT1G transistor datasheet",
        "https://www.lrc.cn/Upload/PDF/Product/GPBJ/L8050QLT1G.pdf",
        False,
        expect_pdf=True,
        note="Manufacturer datasheet for the Q5 NPN SOT-23 auto-reset transistor.",
    ),
    OnlineEvidence(
        "LCSC C39282 L8550HQLT1G transistor page",
        "https://www.lcsc.com/product-detail/C39282.html",
        False,
        note="Distributor/order source for the Q6 PNP SOT-23 auto-reset transistor; final AVL should retain a manufacturer datasheet copy.",
    ),
    OnlineEvidence(
        "LCSC C127509 K2-1102SP-C4SC-04 switch page",
        "https://www.lcsc.com/product-detail/C127509.html",
        False,
        note="Distributor/order source for the SW1-SW3 tactile reset/program/factory buttons.",
    ),
    OnlineEvidence(
        "LCSC C192300 2x4 SMT pin header page",
        "https://www.lcsc.com/product-detail/C192300.html",
        False,
        note="Distributor/order source for J7; page identifies BOOMELE 2.54-2*4P as SMD, 2 rows, 8 pins, surface-mount vertical.",
    ),
    OnlineEvidence(
        "JLCPCB C5123624 10 ohm 2512 sense resistor page",
        "https://jlcpcb.com/partdetail/Milliohm-HoCR2512_2W_10R_1/C5123624",
        False,
        note="Distributor/order source for passive rating evidence.",
    ),
]


REQUIRED_LOCAL = [
    LocalEvidence(
        "access-controller ESP32-S3 source schematic",
        "~/projects/access-controller/circuits/controller/microcontroller.kicad_sch",
        10_000,
    ),
    LocalEvidence("local OPA380 datasheet copy", "docs/datasheets/opa380.pdf", 100_000),
    LocalEvidence("KiCad ESP32-S3-WROOM-1 footprint", "/usr/share/kicad/footprints/RF_Module.pretty/ESP32-S3-WROOM-1.kicad_mod", 1_000),
    LocalEvidence("KiCad SFH2201 footprint", "/usr/share/kicad/footprints/OptoDevice.pretty/Osram_SFH2201.kicad_mod", 1_000),
    LocalEvidence("KiCad TO18 laser diode footprint", "/usr/share/kicad/footprints/OptoDevice.pretty/LaserDiode_TO18-D5.6-3.kicad_mod", 1_000),
    LocalEvidence("KiCad TO56 laser diode footprint", "/usr/share/kicad/footprints/OptoDevice.pretty/LaserDiode_TO56-3.kicad_mod", 1_000),
    LocalEvidence("KiCad OPA380 SOIC-8 footprint", "/usr/share/kicad/footprints/Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod", 1_000),
    LocalEvidence("KiCad INA4180 TSSOP-14 footprint", "/usr/share/kicad/footprints/Package_SO.pretty/TSSOP-14_4.4x5mm_P0.65mm.kicad_mod", 1_000),
    LocalEvidence("KiCad SOT-23 footprint", "/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod", 1_000),
    LocalEvidence("KiCad SOT-23-5 footprint", "/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod", 1_000),
    LocalEvidence("KiCad SOT-23-6 footprint", "/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod", 1_000),
    LocalEvidence("KiCad TSOT-23-6 footprint", "/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/TSOT-23-6.kicad_mod", 1_000),
    LocalEvidence("KiCad AD7606 LQFP-64 footprint", "/usr/share/kicad/footprints/Package_QFP.pretty/LQFP-64_10x10mm_P0.5mm.kicad_mod", 1_000),
    LocalEvidence("KiCad D_SMA footprint", "/usr/share/kicad/footprints/Diode_SMD.pretty/D_SMA.kicad_mod", 1_000),
    LocalEvidence("KiCad Wuerth Mini-B footprint", "/usr/share/kicad/footprints/Connector_USB.pretty/USB_Mini-B_Wuerth_65100516121_Horizontal.kicad_mod", 1_000),
    LocalEvidence("KiCad Bourns 3224W footprint", "/usr/share/kicad/footprints/Potentiometer_SMD.pretty/Potentiometer_Bourns_3224W_Vertical.kicad_mod", 1_000),
    LocalEvidence("SS14 and Bourns order/orientation signoff", "circuits/review/signoff/2026-07-04-ss14-bourns-order-source-signoff.md", 2_000),
    LocalEvidence("direct laser MPN/footprint signoff", "circuits/review/signoff/2026-07-04-direct-laser-mpn-footprint-signoff.md", 2_000),
    LocalEvidence("return-path layout signoff", "circuits/review/signoff/2026-07-04-return-path-layout-signoff.md", 2_000),
    LocalEvidence("KiCad 2512 hand-solder footprint", "/usr/share/kicad/footprints/Resistor_SMD.pretty/R_2512_6332Metric_Pad1.40x3.35mm_HandSolder.kicad_mod", 1_000),
    LocalEvidence("KiCad 0603 hand-solder footprint", "/usr/share/kicad/footprints/Resistor_SMD.pretty/R_0603_1608Metric_Pad0.98x0.95mm_HandSolder.kicad_mod", 1_000),
    LocalEvidence("KiCad 0402 hand-solder footprint", "/usr/share/kicad/footprints/Capacitor_SMD.pretty/C_0402_1005Metric_Pad0.74x0.62mm_HandSolder.kicad_mod", 1_000),
    LocalEvidence("KiCad 0603 capacitor hand-solder footprint", "/usr/share/kicad/footprints/Capacitor_SMD.pretty/C_0603_1608Metric_Pad1.08x0.95mm_HandSolder.kicad_mod", 1_000),
    LocalEvidence("Open_Automation 4.7uH inductor footprint", "circuits/lib/Open_Automation.pretty/L_5.4x5.3_H3.kicad_mod", 1_000),
    LocalEvidence("Open_Automation 10uH inductor footprint", "circuits/lib/Open_Automation.pretty/L_4x4.kicad_mod", 1_000),
    LocalEvidence("canonical proof laser parts list", "../docs/program/PROOF_LASER_PARTS_2026-06-24.md", 5_000),
    LocalEvidence("laser harness pin-code compatibility note", "docs/part-notes/laser-harness-pin-code-compatibility.md", 1_000),
]


def request(url: str, method: str) -> urllib.request.Request:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if method == "GET":
        headers["Range"] = f"bytes=0-{READ_BYTES - 1}"
    return urllib.request.Request(url, method=method, headers=headers)


def fetch_url(url: str, *, expect_pdf: bool) -> ProbeResult:
    head_detail = ""
    try:
        with urllib.request.urlopen(request(url, "HEAD"), timeout=TIMEOUT_S) as response:
            status = response.getcode()
            content_type = response.headers.get("content-type", "")
            length = response.headers.get("content-length", "unknown")
            head_detail = f"HEAD HTTP {status}, type={content_type or 'unknown'}, length={length}"
            if 200 <= status < 400 and not expect_pdf:
                return ProbeResult(True, head_detail)
            if 200 <= status < 400 and expect_pdf and "pdf" in content_type.lower():
                return ProbeResult(True, head_detail)
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, ssl.SSLError, TimeoutError) as exc:
        head_detail = f"HEAD failed: {exc}"

    try:
        with urllib.request.urlopen(request(url, "GET"), timeout=TIMEOUT_S) as response:
            status = response.getcode()
            content_type = response.headers.get("content-type", "")
            data = response.read(READ_BYTES)
            detail = f"GET HTTP {status}, type={content_type or 'unknown'}, first_bytes={len(data)}"
            if not (200 <= status < 400):
                return ProbeResult(False, f"{detail}; {head_detail}")
            if not data:
                return ProbeResult(False, f"{detail}; empty response; {head_detail}")
            if expect_pdf and not data.startswith(b"%PDF"):
                return ProbeResult(False, f"{detail}; expected PDF header; {head_detail}")
            return ProbeResult(True, detail)
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, ssl.SSLError, TimeoutError) as exc:
        return ProbeResult(False, f"GET failed: {exc}; {head_detail}")


def rate_limited(detail: str) -> bool:
    return "HTTP Error 429" in detail


def local_path(path_text: str) -> Path:
    expanded = Path(path_text).expanduser()
    if expanded.is_absolute():
        return expanded
    return REPO_DIR / expanded


def check_local(evidence: LocalEvidence) -> ProbeResult:
    path = local_path(evidence.path)
    if not path.exists():
        return ProbeResult(False, f"missing: {path}")
    if not path.is_file():
        return ProbeResult(False, f"not a file: {path}")
    size = path.stat().st_size
    if size < evidence.min_bytes:
        return ProbeResult(False, f"{path} is {size} bytes, expected at least {evidence.min_bytes}")
    return ProbeResult(True, f"{path} ({size} bytes)")


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    required_online_ok = 0
    required_online_rate_limited = 0
    required_local_ok = 0
    warning_checked = 0

    for evidence in REQUIRED_ONLINE:
        if not evidence.required:
            failures.append(f"{evidence.label}: required source is misclassified as optional")
            continue
        result = fetch_url(evidence.url, expect_pdf=evidence.expect_pdf)
        if result.ok:
            required_online_ok += 1
        elif rate_limited(result.detail):
            required_online_rate_limited += 1
            warnings.append(
                f"{evidence.label}: rate-limited scripted probe; quote/upload review still required "
                f"[{result.detail}]"
            )
        else:
            failures.append(f"{evidence.label}: {evidence.url} -> {result.detail}")

    for evidence in REQUIRED_LOCAL:
        result = check_local(evidence)
        if result.ok:
            required_local_ok += 1
        else:
            failures.append(f"{evidence.label}: {evidence.path} -> {result.detail}")

    for evidence in WARNING_ONLINE:
        if evidence.required:
            failures.append(f"{evidence.label}: required source is misclassified as warning-only")
            continue
        result = fetch_url(evidence.url, expect_pdf=evidence.expect_pdf)
        warning_checked += 1
        state = "reachable" if result.ok else "not reachable"
        warnings.append(f"{evidence.label}: {state}; {evidence.note} [{result.detail}]")

    for warning in warnings:
        print(f"WARN {warning}")

    if failures:
        print(f"FAIL source-document evidence: {len(failures)} required source checks failed")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(
        "PASS source-document evidence: "
        f"{required_online_ok} required online sources, "
        f"{required_online_rate_limited} rate-limited required online source(s), "
        f"{required_local_ok} required local artifacts, "
        f"and {warning_checked} secondary/open-risk sources reviewed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
