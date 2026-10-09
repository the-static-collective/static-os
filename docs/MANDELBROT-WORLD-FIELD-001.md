# MANDELBROT-WORLD-FIELD-001 — The 11×11 Infinite Tuning Instrument

> An address is a choice of attention. It is neither a permission nor a piece of evidence about content.

**Owner:** STATIC OS experiment, standalone from \`main\` bootstrap and not a claimed ISO/installed operating system. **Neighboring sources:** STATIC OS ELEVEN-HEAP-001 (original 11-position nested radix-11 dial math at \`integration/instrument-host-001\`), Static Live RADIO WORLD 001 (#35), GHoT RADIO HOUSE 004 (#106), reLATTE owner-source crossing and receipts.

## What is working

The project contains a runnable browser application that draws actual **Mandelbrot parameter-plane escape-time mathematics**. It uses the recurrence z→z²+c, z initially zero, with a bounded iteration budget. The colorful escaped pixels are a numerical approximation, **not a proof that any remaining pixel belongs to the set**.

The world is navigable by:

- **Up/down:** tune vertical attention using 11 distinct positions.
- **Left/right:** adjust granularity/zoom using 11 positions.
- **Drag:** vertical motion changes tuning, horizontal motion changes granularity, with both effects independently quantized.
- **Wheel/trackpad:** vertical delta tunes, horizontal delta adjusts granularity; Shift+wheel adjusts granularity on vertical-only hardware.
- **Arrow keys:** same four motions when not in a slider; Enter/Backspace on the focused fractal enters/rises a nested world.
- **Enter nested world:** store the current pair of dial positions and open a fresh 06/11, 06/11 child. **Rise:** restore the exact parent pair. **Root:** drop to founding world.
- **Copy world address:** copies a URL hash whose address string has complete nesting. Browser back/forward and pasting the URL reconstruct the exact state, without signing, grants, cookies or cloud storage.
- **Exact witness inspector:** displays numerator/denominator base-eleven rational intervals for tuning and granularity, using \`BigInt\`; a depth-75 path does not collapse even when the float display would.

### Exact address example

~~~text
MWF1/t08g03/t04g11/t06g06
~~~

The first pair sets the parent world, the second its next nested child; the final pair represents the current live dial settings. ELEVEN-HEAP-001 encodes positions internally with digits 0–10. This app displays 1–11, so the original digit is \`position - 1\`. The stored path and current live dial are strictly checked, with a 96-level address budget. That is finite software storage, not an assertion that mathematics stops at level 96.

The tuning intervals and granularity intervals are separate, exact radix-11 nested cells, stored as integer strings. This reuses the **grammar** of ELEVEN-HEAP, not its complete original sensitivity/response policy implementation. The visual projection uses an explicit, independently typed approximate floating viewport. A nested granularity dial affects viewport zoom gain; the tuning dial steers the imaginary component. These screen controls are a *composed application mapping*, not a physical Mandelbrot property or a radio frequency measurement.

### The precision limit is a feature

The exact address can grow far deeper than the finite renderer. The floating-point preview is capped at depth 12 and refused if its scale is too small. The app displays **DISPLAY LIMIT**, preserves the full address and still lets the user rise or bookmark it. No false arbitrary-precision pixels are shown; no promise of endless real-time rendering on an ordinary computer.

## Run immediately

Node.js 22+, zero third-party dependencies:

~~~sh
npm test
npm start
~~~

Open **http://127.0.0.1:8790/** on the computer running the server. The local server is read-only and loopback-only. No HTTPS site, GitHub Pages hosting, mobile app-store submission or physical STATIC OS installation is claimed. Compatible browsers can optionally install the first-party PWA shell; its service worker only caches UI assets, never audio or external sites. Use the exact URL for a resumable bookmark.

## Static Live's two world doors

The app contains a **typed, explicitly curated, owner-held** Radio World adapter:
- Kinship Radio, Minnesota — official entry point \`https://kinshipradio.org/main/\`.
- Rock Impact Makers, Nigeria — official entry point \`https://rockimpactmakersglobal.org/\`.

Both are **direct external links opened only on explicit user click**. No actual stations are geometrically discovered, streamed, monitored or merged. A mathematical point in the fractal is **not** evidence that a radio program or organization occupies that point. There is no direct-play URL, license, audio capture, podcast distribution, donation or worker-compute API in this interface. Selecting a world only creates a local navigation choice; opening an official site proves neither playback nor consent.

Future \`RADIO WORLD 002\` may install separately authorized *listen-only* source adapters after each original broadcaster approves exact stream/embedded player terms, copyright and revocation. Future GHoT work may execute independently authorized compute jobs, but the fractal field does not initiate them. A reLATTE crossing remains an external owner admission event, not a side effect of turning a dial.

## Extension architecture

| Layer | Owns | Does not claim |
|---|---|---|
| STATIC OS / World Field | Typed dial/navigation grammar, exact nested address and renderer | Installed/booted image or external-world authority |
| Static Live | Source-owned recording, podcast/multimedia production and prospective listen-only adapters | Unlimited external music redistribution |
| GHoT | Replaceable, bounded operator-voluntary compute on independent physical machines | Media rights, ministry governance, infinite processing power |
| reLATTE | Portable authenticated crossing syntax, receiving-party admission, receipts | Automatic owner grants from a cursor movement |
| CANNON | Traceable experiments and explicit selection | Exclusive canon on main branch |

### Next 002 proofs

1. Publish a testable standalone web build on an owner-selected HTTPS host, without changing either organization's present radio site or app.
2. Instrument a real OBS local status/health connector and deliberately ensure active media streams preempt GHoT jobs (not part of this UI's authority).
3. Add source-curated station/program bookmarks with accountable origin metadata, without inferring editorial connection from geometric closeness.
4. Explore high-precision Mandelbrot rendering beyond the current finite limit (e.g. higher-precision arithmetic and adaptive tile scheduling), still respecting resource/energy budgets.
5. After source owner consent, add safe one-active-source radio listening with stop-on-switch and provider fallback.

**NAVIGATION ≠ SELECTION ≠ CROSSING ≠ PLAYBACK. EXACT ADDRESS ≠ EXACT PIXELS. GEOMETRIC NEIGHBOR ≠ VERIFIED RELATION. UI CONTROL ≠ LOCAL PERMISSION.**
