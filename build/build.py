"""Composes assets/readme.svg — the entire README as one document.

Separate images can't be stacked seamlessly on GitHub: it inserts spacing
between them and strips the CSS that would close it. So every block is drawn
as a group inside a single SVG instead.

Reads build/cache/ (masks, sprite, contribution data) and build/fonts/.
Regenerate those with make_media.sh and fetch_contributions.py.
"""
import base64, json, os, random

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, 'cache')
FONTS = os.path.join(ROOT, 'fonts')
OUT = os.path.join(os.path.dirname(ROOT), 'assets', 'readme.svg')
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()

LOGO = b64(f'{CACHE}/logo.mask.png')
SWORD = b64(f'{CACHE}/sword.mask.png')
SIGIL = b64(f'{CACHE}/sigil.mask.png')
EYES = b64(f'{CACHE}/eyes.sprite.png')
EYES_FRAMES, EYES_H = 25, 268
CONTRIB = json.load(open(f'{CACHE}/contrib.json'))
F_DISPLAY = b64(f'{FONTS}/PirataOne-Regular.woff2')
F_MONO = b64(f'{FONTS}/ShareTechMono-Regular.woff2')

BG = '#000000'
HI = '#FFFFFF'
MID = '#C9C9C9'
DIM = '#6E6E6E'
DEEP = '#3B3B3B'

CORNER = 'round'      # 'round' = rounded panels, 'cut' = chamfered HUD corners
R = 12                # panel corner radius
OUTER_R = 26          # radius of the single frame around the whole page

W = 1200
M = 22                # outer frame margin
IN = 48               # content inset
CW = W - IN * 2
PAD, GAP = 40, 26

DAYS = CONTRIB['days']
WEEKS = [sum(d['count'] for d in DAYS[i:i + 7]) for i in range(0, len(DAYS) - 6, 7)]


# ------------------------------------------------------------------ helpers
def panel(x, y, w, h, c=R, stroke=DEEP, sw=1.1, fill='none', op=1):
    if CORNER == 'round':
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{c}" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')
    d = (f'M{x+c} {y} L{x+w-c} {y} L{x+w} {y+c} L{x+w} {y+h-c} L{x+w-c} {y+h} '
         f'L{x+c} {y+h} L{x} {y+h-c} L{x} {y+c} Z')
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'


def node(x, y, r=3.5, stroke=DIM, sw=1, op=.85):
    return (f'<g stroke="{stroke}" stroke-width="{sw}" opacity="{op}">'
            f'<line x1="{x-r}" y1="{y}" x2="{x+r}" y2="{y}"/>'
            f'<line x1="{x}" y1="{y-r}" x2="{x}" y2="{y+r}"/></g>')


def nodes(x, y, w, h, r=3.5):
    return ''.join(node(px, py, r) for px, py in
                   [(x, y), (x + w, y), (x, y + h), (x + w, y + h)])


FS, LS = 1.38, .55          # display-face compensation


def label(x, y, t, size=11.5, fill=DIM, ls=3, anchor='start', cls=''):
    k = f' class="{cls}"' if cls else ''
    return (f'<text{k} x="{x}" y="{y}" fill="{fill}" font-size="{size*FS:.1f}" '
            f'letter-spacing="{ls*LS:.1f}" text-anchor="{anchor}">{t}</text>')


def table(x, y, w, rows, rh=32, size=13.5, last_rule=True):
    out = ''
    for i, (k, v) in enumerate(rows):
        ry = y + i * rh
        if last_rule or i < len(rows) - 1:
            out += (f'<line x1="{x+14}" y1="{ry+rh}" x2="{x+w-14}" y2="{ry+rh}" '
                    f'stroke="{DEEP}" stroke-width="1"/>')
        out += label(x + 16, ry + rh - 11, k, size, MID, 2)
        out += label(x + w - 16, ry + rh - 11, v, size, HI, 2, 'end')
    return out


def bracket(x, y, w, h, L=16, stroke=DIM, sw=1.1, op=.5):
    return (f'<g stroke="{stroke}" stroke-width="{sw}" fill="none" opacity="{op}">'
            f'<path d="M{x} {y+L} L{x} {y} L{x+L} {y}"/>'
            f'<path d="M{x+w-L} {y} L{x+w} {y} L{x+w} {y+L}"/>'
            f'<path d="M{x} {y+h-L} L{x} {y+h} L{x+L} {y+h}"/>'
            f'<path d="M{x+w-L} {y+h} L{x+w} {y+h} L{x+w} {y+h-L}"/></g>')


SIG_MASKS, _uid = [], [0]


def uid(p):
    _uid[0] += 1
    return f'{p}{_uid[0]}'


def sigil(cx, cy, r, fill=MID, op=.85, cls=''):
    i = uid('sig')
    SIG_MASKS.append(
        f'<mask id="{i}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="9000">'
        f'<use href="#sigsrc" transform="translate({cx-r} {cy-r}) scale({(r*2)/100:.4f})"/></mask>')
    k = f' class="{cls}"' if cls else ''
    return (f'<rect{k} x="{cx-r}" y="{cy-r}" width="{r*2}" height="{r*2}" fill="{fill}" '
            f'mask="url(#{i})" opacity="{op}"/>')


def wave(x, y, w, h, series=None):
    v = series if series is not None else WEEKS
    peak = max(v) or 1
    step = w / max(1, len(v) - 1)
    pts = [(x + i * step, y + h - (n / peak) * h) for i, n in enumerate(v)]
    line = 'M' + ' L'.join(f'{px:.1f},{py:.1f}' for px, py in pts)
    area = line + f' L{pts[-1][0]:.1f},{y+h} L{pts[0][0]:.1f},{y+h} Z'
    grid = ''.join(f'<line x1="{x+i*w/12}" y1="{y}" x2="{x+i*w/12}" y2="{y+h}"/>'
                   for i in range(1, 12))
    grid += ''.join(f'<line x1="{x}" y1="{y+i*h/4}" x2="{x+w}" y2="{y+i*h/4}"/>'
                    for i in range(1, 4))
    dots = ''.join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.6" fill="{HI}" opacity=".5"/>'
                   for px, py in pts[::4])
    return (f'<g stroke="{DEEP}" stroke-width=".8" opacity=".5">{grid}</g>'
            f'<path d="{area}" fill="{HI}" opacity=".07"/>'
            f'<path d="{line}" fill="none" stroke="{HI}" stroke-width="1.5" '
            f'stroke-linejoin="round"/>{dots}')


def heatmap(x, y, cell=11, gap=3):
    op = [.07, .32, .55, .78, 1.0]
    return ''.join(
        f'<rect x="{x+(i//7)*(cell+gap)}" y="{y+(i%7)*(cell+gap)}" width="{cell}" '
        f'height="{cell}" rx="2" fill="{HI}" opacity="{op[d["level"]]}"/>'
        for i, d in enumerate(DAYS))


def pcb(x, y, w, h, seed=9):
    random.seed(seed)
    g = 14
    dots = ''.join(f'<circle cx="{x+i*g}" cy="{y+j*g}" r=".8"/>'
                   for i in range(1, int(w // g)) for j in range(1, int(h // g)))
    traces = ''
    for _ in range(16):
        cx = x + random.randint(1, int(w // g) - 2) * g
        cy = y + random.randint(1, int(h // g) - 2) * g
        d = f'M{cx} {cy}'
        for _ in range(random.randint(2, 4)):
            if random.random() < .5:
                cx += random.choice([-3, -2, 2, 3]) * g
            else:
                cy += random.choice([-2, -1, 1, 2]) * g
            cx = max(x + g, min(x + w - g, cx))
            cy = max(y + g, min(y + h - g, cy))
            d += f' L{cx} {cy}'
        traces += f'<path d="{d}" fill="none" stroke="{MID}" stroke-width="1.2" opacity=".5"/>'
        traces += (f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="none" stroke="{MID}" '
                   f'stroke-width="1" opacity=".6"/>')
    chips = ''
    for _ in range(3):
        cw, chh = random.choice([(52, 38), (66, 30), (40, 46)])
        cx = x + random.randint(1, max(1, int((w - cw) // g))) * g
        cy = y + random.randint(1, max(1, int((h - chh) // g))) * g
        chips += panel(cx, cy, cw, chh, 6, MID, 1.1, BG, .75)
        chips += ''.join(f'<line x1="{cx+6+k*8}" y1="{cy}" x2="{cx+6+k*8}" y2="{cy-5}" '
                         f'stroke="{MID}" stroke-width="1" opacity=".55"/>'
                         for k in range(int((cw - 10) // 8)))
    return f'<g fill="{DIM}" opacity=".45">{dots}</g>{traces}{chips}'


# ------------------------------------------------------------------- blocks
def block_dossier():
    RA, RB = 268, 224
    ra, rb = 46, 46 + RA + 12
    logo_w = 556
    rx, rw = IN + logo_w + 12, CW - logo_w - 12
    thumb = 152
    tx, tw = IN + thumb + 12, CW - thumb - 12
    lw, lh = 440, 219
    lx, ly = IN + (logo_w - lw) / 2, ra + (RA - lh) / 2
    rows = [('ROLE', 'FULLSTACK ENGINEER'), ('PRIMARY', 'TYPESCRIPT'),
            ('SECONDARY', 'C / C++'), ('RUNTIME', 'NODE.JS'),
            ('FRONTEND', 'REACT / NEXT.JS'), ('DATABASES', '06'), ('MODULES', '27')]
    lm, sm, pc = uid('m'), uid('m'), uid('clip')
    body = f'''
  <mask id="{lm}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="9000">
    <image href="data:image/png;base64,{LOGO}" x="{lx}" y="{ly}" width="{lw}" height="{lh}"
           filter="url(#inv)" preserveAspectRatio="xMidYMid meet"/>
    <rect x="0" y="0" width="{W}" height="{ra+RA+40}" fill="url(#dither)"/>
  </mask>
  <mask id="{sm}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="9000">
    <image href="data:image/png;base64,{SWORD}" x="{IN+16}" y="{rb+124}" width="120" height="90"
           preserveAspectRatio="xMidYMid meet"/>
    <rect x="0" y="{rb}" width="{W}" height="240" fill="url(#dither)"/>
  </mask>
  {panel(IN, 0, CW, 34, 8)}
  {label(IN+18, 23, 'JVSJ', 14, HI, 5)}
  <circle class="blink" cx="{IN+CW-26}" cy="18" r="3.4" fill="{HI}"/>

  {panel(IN, ra, logo_w, RA)}
  {bracket(IN+14, ra+14, logo_w-28, RA-28)}
  <g class="g1" filter="url(#glow)">
    <rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{HI}" mask="url(#{lm})"/>
  </g>

  <clipPath id="{pc}"><rect x="{rx}" y="{ra}" width="{rw}" height="{RA}" rx="{R}"/></clipPath>
  <g clip-path="url(#{pc})">
    <image class="eyes" href="data:image/png;base64,{EYES}" x="{rx}" y="{ra}"
           width="{rw}" height="{EYES_H*EYES_FRAMES}" preserveAspectRatio="none"/>
  </g>
  {panel(rx, ra, rw, RA)}

  {panel(IN, rb, thumb, 108)}
  {sigil(IN+thumb/2, rb+54, 40, HI, .9, 'pulse')}
  {panel(IN, rb+116, thumb, 108)}
  <rect class="pulse" x="0" y="{rb}" width="{W}" height="240" fill="{HI}" mask="url(#{sm})"/>
  {bracket(IN+10, rb+126, thumb-20, 88, 10)}

  {panel(tx, rb, tw, RB)}
  {table(tx, rb, tw, rows, 32, 13.5, False)}

  {nodes(IN, ra, CW, RA)}
  {nodes(IN, rb, CW, RB)}'''
    return body, rb + RB


def block_section(num, name):
    H = 50
    body = f'''
  {panel(IN, 0, CW, H, 10)}
  {panel(IN, 0, 60, H, 10, DEEP, 1.1, MID)}
  {label(IN+30, H/2+5, num, 17, BG, 1, 'middle')}
  {sigil(IN+88, H/2, 16, MID, .9)}
  <text class="d" x="{IN+120}" y="{H/2+4}" fill="{HI}" font-size="26"
        letter-spacing="7" filter="url(#glow)">{name}</text>
  <line class="rule" x1="{IN+150+len(name)*23}" y1="{H/2-1}"
        x2="{IN+CW-24}" y2="{H/2-1}" stroke="{DEEP}" stroke-width="1.1"/>'''
    return body, H


def block_stack():
    groups = [('LANGUAGES', ['TYPESCRIPT', 'JAVASCRIPT', 'C / C++', 'HTML', 'CSS']),
              ('FRONTEND', ['REACT', 'NEXT.JS', 'TAILWIND', 'THREE.JS', 'FIGMA']),
              ('BACKEND', ['NODE.JS', 'NESTJS', 'FASTAPI', 'DJANGO', 'PRISMA']),
              ('DATABASES', ['POSTGRES', 'MYSQL', 'MONGODB', 'REDIS', 'SQLITE', 'ELASTIC']),
              ('INFRA', ['DOCKER', 'AWS', 'CLOUDFLARE', 'LINUX', 'GIT', 'VS CODE'])]
    cw, ch, gap, pitch = 166, 52, 11, 96
    cells, idx = '', 1
    for gi, (gname, items) in enumerate(groups):
        gy = 24 + gi * pitch
        cells += label(IN + 16, gy, gname, 11, DIM, 4)
        cells += (f'<line x1="{IN + 16 + len(gname)*9.4 + 34}" y1="{gy-4}" '
                  f'x2="{IN+CW-16}" y2="{gy-4}" stroke="{DEEP}" stroke-width="1"/>')
        cells += label(IN + CW - 16, gy, f'{len(items):02d}', 11, DIM, 2, 'end')
        for ci, name in enumerate(items):
            x, y = IN + 16 + ci * (cw + gap), gy + 12
            cells += panel(x, y, cw, ch, 9)
            cells += label(x + 14, y + 26, name, 16, MID, .9)
            cells += label(x + 14, y + 42, f'{idx:02d}', 10, DIM, 1.5)
            cells += f'<circle class="pulse" cx="{x+cw-15}" cy="{y+16}" r="2.4" fill="{MID}"/>'
            idx += 1
    H = 24 + (len(groups) - 1) * pitch + 12 + ch + 14
    body = f'''
  {cells}'''
    return body, H


def block_telemetry():
    tot_w = 300
    hx, hw = IN + tot_w + 12, CW - tot_w - 12
    cell, cgap = 11, 3
    gx = hx + (hw - 53 * (cell + cgap)) / 2
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    mlab, prev = '', None
    for i in range(0, len(DAYS), 7):
        mo = int(DAYS[i]['date'][5:7])
        if mo != prev:
            prev = mo
            mlab += label(gx + (i // 7) * (cell + cgap), 32, months[mo - 1], 9.5, DIM, 1.5)
    legend = ''.join(f'<rect x="{hx+hw-106+k*15}" y="142" width="{cell}" height="{cell}" '
                     f'rx="2" fill="{HI}" opacity="{o}"/>'
                     for k, o in enumerate([.07, .32, .55, .78, 1.0]))
    stats = [('ACTIVE DAYS', str(CONTRIB['active_days'])),
             ('BEST DAY', str(CONTRIB['best'])),
             ('WEEKS TRACKED', str(len(WEEKS)))]
    H = 302
    body = f'''
  {panel(IN, 0, tot_w, 150)}
  {label(IN+20, 24, 'TOTAL CONTRIBUTIONS', 11, DIM, 3)}
  <text x="{IN+20}" y="68" fill="{HI}" font-size="44" letter-spacing="2"
        filter="url(#glow)">{CONTRIB['total']:,}</text>
  {table(IN, 78, tot_w, stats, 24, 11, False)}

  {panel(hx, 0, hw, 150)}
  {mlab}
  {heatmap(gx, 38, cell, cgap)}
  {label(hx+hw-120, 152, 'LESS', 9.5, DIM, 1.5, 'end')}
  {legend}

  {panel(IN, 162, CW, 140)}
  {label(IN+20, 186, 'COMMITS / WEEK', 11, DIM, 3)}
  {label(IN+CW-20, 186, f'PEAK {max(WEEKS)}', 11, MID, 2, 'end')}
  {wave(IN+20, 196, CW-40, 88)}

  {nodes(IN, 0, CW, 302)}'''
    return body, H


def block_contact():
    mark_w = 200
    cx, cwid = IN + mark_w + 12, CW - mark_w - 12
    chans = [('GITHUB', 'github.com/' + CONTRIB['user']),
             ('EMAIL', '----'), ('LINKEDIN', '----')]
    active = sum(1 for c in chans if c[1] != '----')
    H = 142
    body = f'''
  {panel(IN, 0, CW, 30, 7)}
  {label(IN+16, 20, 'OPEN CHANNELS', 13, HI, 4)}
  {label(IN+CW-16, 20, f'{active} / {len(chans)} ACTIVE', 11, DIM, 2, 'end')}
  {panel(IN, 42, mark_w, 96)}
  {sigil(IN+mark_w/2, 90, 34, HI, .9, 'pulse')}
  {panel(cx, 42, cwid, 96)}
  {table(cx, 42, cwid, chans, 32, 13.5, False)}
  {nodes(IN, 42, CW, 96)}'''
    return body, H


def block_footer():
    H = 108
    return sigil(W / 2, H / 2, 44, MID, .9, 'pulse'), H


# ---------------------------------------------------------------- assemble
LAYOUT = [block_dossier(),
          block_section('01', 'STACK'), block_stack(),
          block_section('02', 'TELEMETRY'), block_telemetry(),
          block_footer()]

parts, y = [], PAD
for body, h in LAYOUT:
    parts.append(f'<g transform="translate(0 {y})">{body}</g>')
    y += h + GAP
H = y - GAP + PAD

CSS = f'''
    @font-face {{ font-family:"JVD"; src:url(data:font/woff2;base64,{F_DISPLAY}) format("woff2"); }}
    @font-face {{ font-family:"JVM"; src:url(data:font/woff2;base64,{F_MONO}) format("woff2"); }}
    text {{ font-family:"JVD","Papyrus",fantasy; }}
    .m {{ font-family:"JVM","Courier New",monospace; }}
    .grain {{ animation:grain .4s steps(1) infinite }}
    @keyframes grain {{ 0%{{opacity:.12}} 33%{{opacity:.18}} 66%{{opacity:.1}} 100%{{opacity:.15}} }}
    .blink {{ animation:blink 1.1s steps(1) infinite }}
    @keyframes blink {{ 0%,50%{{opacity:1}} 51%,100%{{opacity:0}} }}
    .rule {{ stroke-dasharray:5 4; animation:march 3s linear infinite }}
    @keyframes march {{ to {{ stroke-dashoffset:-18 }} }}
    .pulse {{ animation:pulse 3.5s ease-in-out infinite }}
    @keyframes pulse {{ 0%,100%{{opacity:.45}} 50%{{opacity:.95}} }}
    .eyes {{ animation:eyes 2.5s steps({EYES_FRAMES}) infinite }}
    @keyframes eyes {{ to {{ transform:translateY(-{EYES_H*EYES_FRAMES}px) }} }}
    .g1 {{ animation:g1 6s steps(1) infinite }}
    @keyframes g1 {{ 0%,88%{{transform:translate(0,0);opacity:1}}
      89%{{transform:translate(-8px,2px);opacity:.85}} 91%{{transform:translate(5px,-2px)}}
      93%{{transform:translate(-3px,0)}} 95%,100%{{transform:translate(0,0);opacity:1}} }}
'''

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="JVSJ — fullstack engineer">
  <title>JVSJ — fullstack engineer</title>
  <defs>
    <filter id="inv"><feColorMatrix type="matrix"
      values="-1 0 0 0 1 0 -1 0 0 1 0 0 -1 0 1 0 0 0 0 1"/></filter>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" seed="3" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.6" fill="#000" opacity="0.3"/>
      <animateTransform attributeName="patternTransform" type="translate"
                        from="0 0" to="0 4" dur="2.2s" repeatCount="indefinite"/>
    </pattern>
    <pattern id="dither" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#000"/>
    </pattern>
    <clipPath id="page"><rect x="0" y="0" width="{W}" height="{H}" rx="{OUTER_R}"/></clipPath>
    <image id="sigsrc" href="data:image/png;base64,{SIGIL}" x="0" y="0"
           width="100" height="100" preserveAspectRatio="xMidYMid meet"/>
    {''.join(SIG_MASKS)}
  </defs>
  <style>{CSS}</style>

  <g clip-path="url(#page)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    {''.join(parts)}
    <rect width="{W}" height="{H}" filter="url(#grain)" opacity=".15" class="grain"/>
    <rect width="{W}" height="{H}" fill="url(#scan)"/>
  </g>
  <rect x="{M/2}" y="{M/2}" width="{W-M}" height="{H-M}" rx="{OUTER_R-M/2}"
        fill="none" stroke="{DEEP}" stroke-width="1.4"/>
</svg>
'''
open(OUT, 'w').write(svg)
print(f'assets/readme.svg  {W}x{H}  {os.path.getsize(OUT)/1024:.1f} KB')
