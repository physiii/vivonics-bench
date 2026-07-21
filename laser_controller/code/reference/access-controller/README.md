# Access-controller dashboard reference

This directory preserves the exact browser assets used as the visual and OTA
foundation for the Vivonics laser-controller dashboard. The snapshot was read
from the access-controller working tree on `office` on 2026-07-21 and verified
byte-for-byte against the files served by `http://192.168.1.115/`.

## Provenance

- Source repository: `/home/andy/projects/access-controller` on `office`
- Source repository HEAD: `6146a7bbb51b45ae03bf1d154e957be8e0dfa474`
- Firmware-reported deployed source: `a4f761d6d7791affc679ad33f71db137ead0f461-dirty`
- Reference page: `http://192.168.1.115/`
- Browser verification: desktop and mobile layouts rendered with three tabs,
  eight cards, and no console errors.

| Served asset | SHA-256 |
| --- | --- |
| `deployed-ui/index.html` | `6d2857e1665c10742e119fcdbae2e9c52de1f9d25d71fd6a4676cdb4dce0fd89` |
| `deployed-ui/style.css` | `118e715f14404d9cbb2bccaa5b6bfb37bafdd0005e640593804b8a89242fd2da` |
| `deployed-ui/script.js` | `e39fc0a5446c9d48f7e11e019930229982cdf23d142c17da5e01796dad57ff47` |

The files under `deployed-ui/` are a read-only provenance snapshot. The
laser-controller implementation lives separately under `main/public/` and
intentionally removes access-control users, locks, exits, schedules, Wiegand,
RF, and upstream-server behavior. It retains the proven visual language,
responsive layout, Wi-Fi provisioning flow, diagnostics presentation, and
browser OTA interaction.
