import zlib, struct, sys

def read_png(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n', 'not a png'
    pos, idat, pal = 8, b'', None
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos+4])[0]
        typ = d[pos+4:pos+8]
        data = d[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w, h, depth, ctype, comp, filt, inter = struct.unpack('>IIBBBBB', data)
            assert depth == 8 and inter == 0, (depth, inter)
        elif typ == b'PLTE':
            pal = data
        elif typ == b'IDAT':
            idat += data
        elif typ == b'IEND':
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = w * ch
    out = bytearray(stride * h)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if f == 1:
            for i in range(ch, stride): line[i] = (line[i] + line[i-ch]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                b = prev[i]
                c = prev[i-ch] if i >= ch else 0
                pa, pb, pc = abs(b-c), abs(a-c), abs(a+b-2*c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y*stride:(y+1)*stride] = line
        prev = line
    return w, h, ch, ctype, pal, bytes(out)

def to_1bit(w, h, ch, ctype, pal, px, thr=140):
    rowbytes = (w + 7) // 8
    bits = bytearray(rowbytes * h)
    for y in range(h):
        base = y * w * ch
        rb = y * rowbytes
        for x in range(w):
            i = base + x * ch
            if ctype == 3:
                idx = px[i] * 3
                r, g, b = pal[idx], pal[idx+1], pal[idx+2]
                a = 255
            elif ctype in (0, 4):
                r = g = b = px[i]
                a = px[i+1] if ctype == 4 else 255
            else:
                r, g, b = px[i], px[i+1], px[i+2]
                a = px[i+3] if ctype == 6 else 255
            lum = (r*299 + g*587 + b*114) // 1000
            if a < 128:
                lum = 255                      # transparent -> paper
            if lum >= thr:                     # paper -> bit 1 (white)
                bits[rb + (x >> 3)] |= (0x80 >> (x & 7))
    return rowbytes, bytes(bits)

def write_png(path, w, h, rowbytes, bits):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += bits[y*rowbytes:(y+1)*rowbytes]
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 1, 0, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)

src, dst, thr = sys.argv[1], sys.argv[2], int(sys.argv[3])
w, h, ch, ctype, pal, px = read_png(src)
rowbytes, bits = to_1bit(w, h, ch, ctype, pal, px, thr)
write_png(dst, w, h, rowbytes, bits)
import os
print(f'{w}x{h} ctype={ctype} -> {dst} {os.path.getsize(dst)} bytes')
