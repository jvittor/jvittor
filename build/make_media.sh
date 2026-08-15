#!/usr/bin/env bash
# Turns build/source/ artwork into the masks and sprite that build.py embeds.
# Only needed when the source art changes — the results are committed in cache/.
#
#   ./build/make_media.sh
#
# Requires: ffmpeg, and macOS `sips` (swap for any resizer elsewhere).
set -euo pipefail
cd "$(dirname "$0")"

SRC=source
CACHE=cache
PREP="python3 prepare_images.py"
mkdir -p "$CACHE"

# --- logo -------------------------------------------------------------------
# Flat two-colour blackletter mark: 1-bit keeps it crisp and ~40x smaller.
sips -Z 820 "$SRC/logo.png" --out "$CACHE/.logo.tmp.png" >/dev/null
$PREP "$CACHE/.logo.tmp.png" "$CACHE/logo.mask.png" 140

# --- sword ------------------------------------------------------------------
# White-on-transparent: the alpha channel *is* the mask.
sips -c 420 560 "$SRC/sword.png" --out "$CACHE/.sword.tmp.png" >/dev/null
sips -Z 460 "$CACHE/.sword.tmp.png" >/dev/null
python3 - "$CACHE/.sword.tmp.png" "$CACHE/sword.mask.png" <<'PY'
import sys, zlib, struct
exec(open('prepare_images.py').read().split('src, dst, thr')[0])
w, h, ch, ctype, pal, px = read_png(sys.argv[1])
raw = bytearray()
for y in range(h):
    raw.append(0)
    for x in range(w):
        i = (y * w + x) * ch
        raw.append(px[i + 3] if ch == 4 else 255)
def chunk(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
open(sys.argv[2], 'wb').write(
    b'\x89PNG\r\n\x1a\n'
    + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
    + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))
PY

# --- sigil ------------------------------------------------------------------
# Shown as small as 32px, so it needs an antialiased ramp, NOT 1-bit:
# thresholding shatters the thin prongs and the inner ring at that size.
sips -Z 192 "$SRC/sigil.png" --out "$CACHE/.sigil.tmp.png" >/dev/null
python3 - "$CACHE/.sigil.tmp.png" "$CACHE/sigil.mask.png" <<'PY'
import sys, zlib, struct
exec(open('prepare_images.py').read().split('src, dst, thr')[0])
w, h, ch, ctype, pal, px = read_png(sys.argv[1])
LO, HI = 30.0, 120.0                      # measured: ink ~0-63, ground ~96-127
raw = bytearray()
for y in range(h):
    raw.append(0)
    for x in range(w):
        i = (y * w + x) * ch
        lum = (px[i] * 299 + px[i + 1] * 587 + px[i + 2] * 114) // 1000 if ch >= 3 else px[i]
        v = int(max(0.0, min(1.0, (HI - lum) / (HI - LO))) * 255)
        raw.append(0 if v < 24 else 255 if v > 231 else v)
def chunk(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
open(sys.argv[2], 'wb').write(
    b'\x89PNG\r\n\x1a\n'
    + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
    + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))
PY

# --- eyes -------------------------------------------------------------------
# An animated GIF does NOT play inside an SVG, and the README is a single SVG.
# So the loop ships as a vertical sprite sheet driven by CSS steps() instead.
# CROP frames the eye itself (measured at x 170-580, y 350-640 of 720x900);
# using the full width left dead space on both sides.
CROP="crop=520:260:130:340"
EYE_W=536; EYE_H=268; FRAMES=25          # keep FRAMES/EYE_H in sync with build.py

ffmpeg -v error -i "$SRC/eyes.mp4" \
  -vf "select='not(mod(n\,11))',$CROP,scale=$EYE_W:$EYE_H:flags=neighbor,format=gray,tile=1x$FRAMES" \
  -frames:v 1 -y "$CACHE/.eyes.tmp.png"
$PREP "$CACHE/.eyes.tmp.png" "$CACHE/eyes.sprite.png" 128

# Standalone looping GIF, forced to the page's exact two colours.
ffmpeg -v error -i "$SRC/eyes.mp4" \
  -vf "$CROP,fps=15,scale=$EYE_W:$EYE_H:flags=neighbor,format=monob,split[a][b];[a]palettegen=max_colors=2:reserve_transparent=0[p];[b][p]paletteuse=dither=none" \
  -loop 0 -y ../assets/eyes.gif

rm -f "$CACHE"/.*.tmp.png
echo "cache rebuilt:"
ls -la "$CACHE"
