# -*- coding: utf-8 -*-
"""
MISTWATER 怪物模型生成脚本（全部为原创设计）
  袋中人 bag   ：佝偻枯瘦、麻袋头（挖空眼洞、缝线嘴）、破布、长爪
  病护   nurse ：病号裙、垂布头罩（布下隐约有脸形）、金属颈托、绷带腿、输液架
  执刑者 boss  ：锈笼头（笼内灯泡）、厚重长大衣、铁链、护肩、巨钩
运行：  "G:\\Blender\\blender.exe" -b -P mistwater_monsters.py   （需与 mistwater_hero.py 同目录）
输出：mistwater_bag.glb / mistwater_nurse.glb / mistwater_boss.glb、mistwater_monsters_atlas.png、各自预览图
"""
import math, os, importlib.util
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
spec = importlib.util.spec_from_file_location('mw_hero', os.path.join(HERE, 'mistwater_hero.py'))
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
R, put, rect, ell, noise, vgrad, grid, dots, G, interp, sellip = H.R, H.put, H.rect, H.ell, H.noise, H.vgrad, H.grid, H.dots, H.G, H.interp, H.sellip
part, L, S, BXg = H.part, H.L, H.S, H.BXg

# ============================================================ 贴图集
H.REG.clear(); H.REG.update({
    'sackF': (0, 0, 128, 128), 'sackB': (128, 0, 128, 128), 'rags': (256, 0, 128, 128), 'ragsF': (384, 0, 128, 128),
    'gown': (0, 128, 128, 128), 'hood': (128, 128, 128, 128), 'hoodB': (256, 128, 128, 128), 'pale': (384, 128, 128, 128),
    'bcoat': (0, 256, 128, 128), 'bcoatB': (128, 256, 128, 128), 'rust': (256, 256, 128, 128),
    'metal': (384, 256, 64, 64), 'sheet': (448, 256, 64, 64), 'bulb': (384, 320, 64, 64), 'chain': (448, 320, 64, 64),
    'leather': (0, 384, 64, 64), 'bandage': (64, 384, 64, 64), 'claw': (128, 384, 64, 64), 'trousers': (192, 384, 128, 128)})
img = H.img; img[...] = 0; img[..., 3] = 1
BLOOD, DRIED = (.36, .03, .02), (.2, .03, .02)

def burlap(a, seed):
    a[..., :3] = (.47, .4, .28); h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    put(a, (xx % 3) == 0, (.36, .3, .2), .6); put(a, (yy % 3) == 0, (.4, .33, .22), .4); noise(a, .08, seed); noise(a, .06, seed + 1, 8, 8)
def drips(a, n, col, seed, top=0.0, al=.85):
    r = np.random.default_rng(seed); h, w = a.shape[:2]
    for _ in range(n):
        x = int(r.random() * w); y0 = int((top + r.random() * .4) * h); ln = int(h * (.1 + r.random() * .4)); wd = 1 + int(r.random() * 2)
        for y in range(y0, min(h, y0 + ln)): a[y, x:x + wd, :3] = a[y, x:x + wd, :3] * (1 - al * (1 - (y - y0) / ln)) + np.array(col) * al * (1 - (y - y0) / ln)
def splats(a, n, col, seed, rmax=.08, al=.8):
    r = np.random.default_rng(seed)
    for _ in range(n): put(a, ell(a, r.random(), r.random(), .01 + r.random() * rmax, .01 + r.random() * rmax, .5), col, al)

def paint():
    # 麻袋正面：挖空眼洞 + 缝线嘴 + 渗血
    a = R('sackF'); burlap(a, 1); u, v = grid(a)
    for cu, cv, ru, rv in ((.34, .42, .075, .055), (.66, .40, .065, .07)):
        put(a, ell(a, cu, cv, ru * 1.6, rv * 1.6, .6), (.2, .14, .09), .6); put(a, ell(a, cu, cv, ru, rv), (.02, .015, .01))
    put(a, np.abs(v - .66 - .015 * np.sin(u * 25)) < .006, (.12, .08, .05))
    for i in range(9):
        x = .3 + i * .05; put(a, (np.abs((u - x) - (v - .66)) < .006) & (np.abs(v - .66) < .03), (.1, .07, .05)); put(a, (np.abs((u - x) + (v - .66)) < .006) & (np.abs(v - .66) < .03), (.1, .07, .05))
    drips(a, 6, DRIED, 2, .4); put(a, ell(a, .5, .72, .14, .07, .5), DRIED, .5); splats(a, 5, BLOOD, 3, .03)
    put(a, ell(a, .15, .2, .1, .08), (.38, .32, .22), .7)   # 补丁
    # 麻袋背面
    a = R('sackB'); burlap(a, 4); u, v = grid(a); put(a, np.abs(u - .5) < .01, (.25, .2, .13)); splats(a, 4, DRIED, 5, .05, .5)
    # 破布（背面/四肢）与正面（撕裂处露出肋骨）
    a = R('rags'); a[..., :3] = (.21, .19, .16); noise(a, .06, 6, 1, 6); noise(a, .05, 7)
    r = np.random.default_rng(8)
    for _ in range(10): put(a, ell(a, r.random(), r.random(), .02 + r.random() * .05, .04 + r.random() * .08), (.08, .07, .06))
    splats(a, 6, DRIED, 9, .06, .7); drips(a, 4, DRIED, 10)
    a = R('ragsF'); a[..., :3] = R('rags')[..., :3]; u, v = grid(a)
    hole = ell(a, .5, .45, .3, .28); put(a, hole, (.5, .47, .42))
    for i in range(6): put(a, hole & (np.abs(v - (.27 + i * .065) - .03 * np.abs(u - .5) * 4) < .012), (.66, .63, .57))
    put(a, hole & (np.abs(u - .5) < .02), (.42, .39, .35)); put(a, ell(a, .5, .45, .32, .3) & ~hole, (.1, .08, .06))
    splats(a, 5, BLOOD, 11, .04); drips(a, 5, DRIED, 12, .5)
    # 灰白皮肤（青紫血管）
    a = R('pale'); vgrad(a, (.6, .58, .53), (.45, .43, .39)); noise(a, .04, 13); u, v = grid(a)
    for i in range(7): put(a, np.abs(u - (.1 + i * .13) - .04 * np.sin(v * 9 + i)) < .006, (.38, .3, .4), .55)
    splats(a, 4, (.35, .25, .3), 14, .08, .35); splats(a, 3, DRIED, 15, .03, .6)
    a = R('claw'); vgrad(a, (.5, .47, .42), (.2, .17, .14)); noise(a, .04, 16)
    # 病号裙
    a = R('gown'); a[..., :3] = (.47, .5, .5); u, v = grid(a)
    put(a, ((np.mgrid[0:128, 0:128][0] % 10) == 0) & ((np.mgrid[0:128, 0:128][1] % 10) == 0), (.36, .4, .42), .7)
    put(a, np.abs(u - .5) < .006, (.33, .36, .36)); put(a, ell(a, .5, .25, .3, .1, .6), (.38, .4, .4), .4)
    splats(a, 10, BLOOD, 17, .06); drips(a, 8, DRIED, 18, .2); noise(a, .05, 19, 1, 4); noise(a, .03, 20)
    # 垂布头罩：正面隐约的脸形血渍
    a = R('hood'); a[..., :3] = (.74, .72, .66); u, v = grid(a)
    for i in range(12): put(a, np.abs(u - i / 11) < .012, (.55, .53, .48), .5)
    put(a, ell(a, .5, .42, .17, .2, .5), (.45, .08, .06), .75); put(a, ell(a, .4, .4, .04, .03), (.25, .03, .02), .8); put(a, ell(a, .6, .4, .04, .03), (.25, .03, .02), .8)
    put(a, ell(a, .5, .56, .07, .02), (.25, .03, .02), .7); drips(a, 9, BLOOD, 21, .45); noise(a, .04, 22)
    a = R('hoodB'); a[..., :3] = (.72, .7, .64); u, v = grid(a)
    for i in range(12): put(a, np.abs(u - i / 11) < .012, (.53, .51, .46), .5)
    splats(a, 3, DRIED, 23, .05, .5); noise(a, .04, 24)
    a = R('bandage'); a[..., :3] = (.7, .67, .6); u, v = grid(a)
    for i in range(9): put(a, np.abs(v - i / 8 - .05 * u) < .02, (.5, .48, .42), .6)
    splats(a, 3, DRIED, 25, .08, .6); noise(a, .04, 26)
    a = R('metal'); vgrad(a, (.55, .56, .58), (.35, .36, .38)); noise(a, .06, 27); splats(a, 4, (.4, .22, .12), 28, .1, .5)
    a = R('sheet'); a[..., :3] = (.66, .64, .58); noise(a, .05, 29); splats(a, 2, DRIED, 30, .1, .5)
    # 执刑者大衣
    a = R('bcoat'); vgrad(a, (.15, .12, .1), (.08, .065, .055)); noise(a, .04, 31, 1, 3); u, v = grid(a)
    for y in (.22, .48, .74): put(a, np.abs(v - y) < .025, (.3, .22, .14)); put(a, rect(a, .45, y - .035, .55, y + .035), (.55, .48, .32))
    put(a, np.abs(u - .5) < .01, (.05, .04, .03)); splats(a, 8, BLOOD, 32, .07); drips(a, 8, DRIED, 33, .1)
    a = R('bcoatB'); vgrad(a, (.14, .11, .09), (.07, .06, .05)); noise(a, .04, 34, 1, 3); u, v = grid(a)
    put(a, np.abs(u - .5) < .006, (.04, .03, .03)); splats(a, 5, DRIED, 35, .06, .7)
    a = R('trousers'); a[..., :3] = (.12, .11, .1); noise(a, .05, 36, 1, 4); splats(a, 5, DRIED, 37, .05, .6)
    a = R('rust'); a[..., :3] = (.33, .19, .11); noise(a, .12, 38, 2, 2); noise(a, .1, 39, 6, 6); splats(a, 12, (.48, .26, .12), 40, .05, .6); splats(a, 10, (.15, .08, .05), 41, .05, .7)
    a = R('bulb'); u, v = grid(a); a[..., :3] = (.95, .8, .5); put(a, ell(a, .5, .5, .35, .35, .8), (1, .97, .85))
    a = R('chain'); a[..., :3] = (.18, .15, .12); u, v = grid(a)
    for i in range(4): put(a, ell(a, .5, .125 + i * .25, .32, .14) & ~ell(a, .5, .125 + i * .25, .18, .07), (.45, .38, .3))
    noise(a, .06, 42)
    a = R('leather'); vgrad(a, (.12, .09, .07), (.05, .04, .03)); noise(a, .04, 43)
    np.clip(img, 0, 1, out=img)

# ============================================================ 几何辅助
def ring_fn(rings, extra=None):
    def fn(uu, k):
        a = uu * math.tau - math.pi; f = k * (len(rings) - 1); i = min(int(f), len(rings) - 2); w = f - i; w = w * w * (3 - 2 * w)
        y, rx, rz, e, zo = [rings[i][j] + (rings[i + 1][j] - rings[i][j]) * w for j in range(5)]
        x, z = sellip(a, rx, rz, e); p = [x, y, z + zo]
        if extra: p = extra(a, k, y, p)
        return tuple(p)
    return fn
def tube(geo, pts, r0, r1, seg, tile, closed=False):
    P = [np.array(p, float) for p in pts]; n = len(P)
    def fn(uu, k):
        f = k * (n - 1); i = min(int(f), n - 2); w = f - i; p = P[i] * (1 - w) + P[i + 1] * w
        t = P[min(i + 1, n - 1)] - P[i]; t /= (np.linalg.norm(t) or 1)
        ref = np.array([0, 0, 1.]) if abs(t[2]) < .9 else np.array([1., 0, 0])
        nn = np.cross(t, ref); nn /= (np.linalg.norm(nn) or 1); bn = np.cross(t, nn)
        a = uu * math.tau; r = r0 + (r1 - r0) * k
        q = p + (nn * math.cos(a) + bn * math.sin(a)) * r; return (q[0], q[1], q[2])
    S(geo, fn, seg, max(2, n - 1) * 2, tile)

# ============================================================ 袋中人
def build_bag():
    H.PARTS.clear()
    part('body', None, (0, 0, 0))
    g = part('hips', 'body', (0, .84, 0)); L(g, [[-.1, .1, .08], [-.03, .12, .09], [.06, .125, .09]], 10, 'rags')
    for side, sx in (('L', 1), ('R', -1)):
        g = part('leg' + side, 'body', (sx * .095, .84, 0)); L(g, [[-.41, .04, .045], [-.3, .045, .05], [-.15, .055, .06], [-.02, .065, .07], [.04, .055, .06]], 8, 'rags')
        g = part('knee' + side, 'leg' + side, (0, -.41, 0))
        L(g, [[-.38, .026, .03], [-.3, .03, .036], [-.15, .038, .046], [-.02, .04, .046], [.03, .036, .042]], 8, 'pale')
        L(g, [[-.45, .034, .1, .05], [-.42, .036, .1, .05], [-.39, .03, .06, .03], [-.36, .027, .035, .01]], 8, 'pale', sub=1)
    g = part('torso', 'body', (0, .86, 0))
    rings = [(-.04, .12, .09, 2.2, 0), (.08, .124, .086, 2.2, 0), (.2, .148, .098, 2.3, -.005), (.32, .168, .108, 2.4, -.015), (.42, .172, .108, 2.4, -.03), (.48, .14, .098, 2.2, -.035), (.52, .08, .07, 2, -.03), (.55, .055, .055, 2, -.02)]
    def hump(a, k, y, p): p[2] -= .035 * G(y, .38, .08) * max(-math.cos(a), 0); p[0] += math.copysign(.015, math.sin(a)) * G(y, .44, .04) * G(abs(a), math.pi / 2, .5); return p
    S(g, ring_fn(rings, hump), 20, 18, 'ragsF', 'rags')
    g = part('head', 'torso', (0, .55, .05))
    def sack(uu, t):
        a = uu * math.tau - math.pi; hgt = .4
        r = interp(t, [(0, .06), (.08, .075), (.12, .062), (.2, .125), (.4, .165), (.6, .17), (.78, .148), (.9, .1), (.97, .05), (1, .003)])
        d = .01 * math.sin(a * 5 + t * 7) * math.sin(t * 9) * (t > .15)
        d -= .016 * G(t, .58, .06) * G(abs(a), .5, .14) * (math.cos(a) > 0)
        d -= .006 * G(t, .34, .02) * G(a, 0, .4)
        rr = r + d; return (math.sin(a) * rr, t * hgt, math.cos(a) * rr * 1.03)
    S(g, sack, 24, 24, 'sackF', 'sackB')
    L(g, [[.39, .02, .02], [.45, .045, .04], [.5, .03, .03], [.52, .003, .003]], 8, 'sackB', sub=1)
    L(g, [[.03, .072, .072], [.06, .074, .074]], 10, 'leather', sub=1)
    for side, sx in (('L', 1), ('R', -1)):
        g = part('arm' + side, 'torso', (sx * .17, .45, 0)); L(g, [[-.38, .03, .034], [-.25, .036, .04], [-.1, .043, .047], [.02, .05, .05], [.05, .03, .03]], 8, 'rags')
        g = part('f' + side, 'arm' + side, (0, -.38, 0))
        L(g, [[-.4, .024, .026], [-.3, .028, .03], [-.12, .032, .034], [0, .034, .036]], 8, 'pale')
        L(g, [[-.12, .008, .014], [-.08, .014, .034], [-.03, .016, .038], [0, .014, .03]], 8, 'pale', c=(0, -.4, 0))
        for z in (-.022, 0, .022): L(g, [[-.27, .002, .002], [-.2, .006, .006], [-.11, .009, .009]], 5, 'claw', c=(0, -.4, z), sub=1)

# ============================================================ 病护
def build_nurse():
    H.PARTS.clear()
    part('body', None, (0, 0, 0))
    for side, sx in (('L', 1), ('R', -1)):
        g = part('leg' + side, 'body', (sx * .075, .84, 0)); L(g, [[-.42, .038, .041], [-.3, .042, .046], [-.15, .05, .055], [0, .058, .064]], 8, 'bandage')
        g = part('knee' + side, 'leg' + side, (0, -.42, 0))
        L(g, [[-.37, .027, .03], [-.28, .032, .036], [-.15, .037, .043], [0, .039, .044]], 8, 'bandage')
        L(g, [[-.42, .036, .095, .04], [-.39, .036, .095, .04], [-.36, .03, .05, .02]], 8, 'sheet', sub=1)
    g = part('skirt', 'body', (0, .86, 0))
    def skirt(uu, k):
        a = uu * math.tau - math.pi; y = -.42 + .54 * k
        rx = interp(k, [(0, .23), (.4, .2), (.78, .165), (1, .152)]); rz = rx * .8
        fold = .013 * math.sin(a * 9) * (1 - k); y += .015 * math.sin(a * 7) * (k < .05)
        return (math.sin(a) * (rx + fold), y, math.cos(a) * (rz + fold))
    S(g, skirt, 24, 10, 'gown')
    g = part('torso', 'body', (0, .96, 0))
    rings = [(-.12, .15, .112, 2.2, 0), (.02, .128, .094, 2.2, 0), (.15, .14, .098, 2.3, .006), (.27, .152, .1, 2.3, .01), (.35, .155, .095, 2.3, 0), (.4, .13, .08, 2.2, -.008), (.44, .08, .06, 2, -.01), (.46, .05, .048, 2, -.008)]
    S(g, ring_fn(rings), 20, 16, 'gown')
    L(g, [[.4, .072, .072], [.47, .075, .075], [.5, .07, .07]], 12, 'metal', sub=1)
    g = part('head', 'torso', (0, .49, 0))
    L(g, [[0, .035, .04], [.06, .06, .075], [.13, .07, .086], [.2, .056, .07], [.23, .003, .003]], 10, 'pale')
    def hood(uu, t):
        a = uu * math.tau - math.pi; y = -.16 + .46 * t
        r = interp(t, [(0, .2), (.25, .16), (.5, .112), (.7, .098), (.88, .07), (1, .003)])
        r += .015 * math.sin(a * 7) * (1 - t) * (t < .6) + .016 * G(t, .55, .12) * G(a, 0, .5)
        return (math.sin(a) * r, y, math.cos(a) * r * 1.05 + .012)
    S(g, hood, 22, 16, 'hood', 'hoodB')
    for side, sx in (('L', 1), ('R', -1)):
        g = part('arm' + side, 'torso', (sx * .155, .37, 0)); L(g, [[-.27, .024, .027], [-.15, .028, .031], [0, .035, .038], [.03, .02, .022]], 8, 'pale')
        g = part('f' + side, 'arm' + side, (0, -.27, 0))
        L(g, [[-.25, .019, .021], [-.12, .023, .025], [0, .027, .029]], 8, 'pale')
        L(g, [[-.13, .005, .008], [-.09, .011, .026], [-.04, .012, .028], [0, .011, .02]], 8, 'pale', c=(0, -.25, 0))
    g = part('pole', 'fR', (0, -.32, 0))
    L(g, [[-1.05, .015, .015], [.6, .015, .015]], 6, 'metal', sub=1)
    BXg(g, (0, .58, 0), (.26, .02, .02), 'metal'); BXg(g, (.1, .5, 0), (.09, .16, .035), 'sheet')
    for i in range(4):
        a = i * math.pi / 2; BXg(g, (math.sin(a) * .13, -1.05, math.cos(a) * .13), (.03 + abs(math.sin(a)) * .2, .03, .03 + abs(math.cos(a)) * .2), 'metal')

# ============================================================ 执刑者
def build_boss():
    H.PARTS.clear()
    part('body', None, (0, 0, 0))
    for side, sx in (('L', 1), ('R', -1)):
        g = part('leg' + side, 'body', (sx * .16, .98, 0)); L(g, [[-.48, .095, .105], [-.3, .11, .12], [-.12, .13, .14], [0, .14, .15], [.05, .12, .13]], 10, 'trousers')
        g = part('knee' + side, 'leg' + side, (0, -.48, 0))
        L(g, [[-.42, .08, .085], [-.25, .09, .1], [-.1, .1, .11], [0, .1, .11]], 10, 'trousers')
        L(g, [[-.52, .1, .18, .05], [-.47, .105, .18, .05], [-.42, .1, .13, .03], [-.36, .095, .1, .01], [-.3, .1, .105]], 10, 'leather')
    g = part('coat', 'body', (0, 1.0, 0))
    def coat(uu, k):
        a = uu * math.tau - math.pi; y = -.72 + .82 * k
        rx = interp(k, [(0, .42), (.4, .36), (.88, .31), (1, .29)]); rz = rx * .8; fold = .022 * math.sin(a * 7) * (1 - k)
        return (math.sin(a) * (rx + fold), y + .02 * math.sin(a * 5) * (k < .05), math.cos(a) * (rz + fold))
    S(g, coat, 26, 10, 'bcoat', 'bcoatB')
    g = part('torso', 'body', (0, 1.04, 0))
    rings = [(-.1, .3, .22, 2.4, 0), (.15, .33, .23, 2.5, .01), (.35, .4, .25, 2.6, .015), (.52, .44, .25, 2.6, 0), (.6, .4, .22, 2.5, -.01), (.66, .28, .18, 2.3, -.02), (.7, .13, .12, 2, -.02)]
    S(g, ring_fn(rings), 24, 18, 'bcoat', 'bcoatB')
    for i, (y0, y1) in enumerate(((.05, .45), (.2, .6), (.35, .12))):
        pts = [(math.sin(t) * .35 * (1.08 if abs(math.cos(t)) > .3 else 1.0), y0 + (y1 - y0) * (t + math.pi) / math.tau, math.cos(t) * .26) for t in np.linspace(-math.pi, math.pi, 20)]
        tube(g, pts, .03, .03, 6, 'chain')
    for sx in (1, -1): L(g, [[.48, .13, .16], [.58, .17, .2], [.66, .12, .15], [.69, .003, .003]], 10, 'rust', c=(sx * .38, 0, 0), sub=1)
    g = part('cage', 'torso', (0, .7, 0))
    for i in range(10):
        a = i / 10 * math.tau; L(g, [[0, .018, .018], [.78, .018, .018]], 5, 'rust', c=(math.cos(a) * .34, 0, math.sin(a) * .34), sub=1)
    for y in (0, .4, .78):
        tube(g, [(math.cos(t) * .34, y, math.sin(t) * .34) for t in np.linspace(0, math.tau, 21)], .025, .025, 5, 'rust')
    L(g, [[.78, .36, .36], [.88, .3, .3], [.97, .18, .18], [1.02, .003, .003]], 14, 'rust', sub=1)
    L(g, [[1.0, .02, .02], [1.12, .02, .02]], 5, 'metal', sub=1); L(g, [[0, .13, .12], [.18, .1, .1], [.24, .003, .003]], 10, 'leather', sub=1)
    L(g, [[.48, .01, .01], [.72, .01, .01]], 4, 'leather', sub=1)
    g = part('bulb', 'cage', (0, .26, 0))
    L(g, [[0, .003, .003], [.03, .06, .06], [.1, .1, .1], [.17, .07, .07], [.2, .03, .03]], 10, 'bulb')
    L(g, [[.2, .032, .032], [.26, .032, .032]], 8, 'metal', sub=1)
    for side, sx in (('L', 1), ('R', -1)):
        g = part('arm' + side, 'torso', (sx * .48, .56, 0)); L(g, [[-.5, .09, .1], [-.3, .1, .11], [-.1, .115, .12], [.05, .13, .13], [.1, .08, .08]], 10, 'bcoat')
        g = part('f' + side, 'arm' + side, (0, -.5, 0))
        L(g, [[-.46, .075, .08], [-.25, .085, .09], [-.05, .1, .1], [0, .1, .1]], 10, 'bcoat')
        L(g, [[-.2, .03, .04], [-.12, .06, .08], [-.04, .065, .085], [0, .06, .07]], 10, 'leather', c=(0, -.46, 0))
    g = part('hook', 'fR', (0, -.62, 0))
    L(g, [[-1.7, .045, .045], [.1, .045, .045]], 8, 'rust', sub=1)
    arc = [(.3 - .3 * math.cos(t), -1.7 - .3 * math.sin(t), 0) for t in np.linspace(0, math.pi * 1.2, 14)]
    tube(g, arc, .06, .015, 8, 'rust')

# ============================================================ 构建与导出
def scene_build(name, builder, preview_h):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    im = bpy.data.images.new('mistwater_monsters_atlas', H.ATL, H.ATL, alpha=True)
    im.pixels.foreach_set(img[::-1].ravel().astype(np.float32)); im.filepath_raw = os.path.join(HERE, 'mistwater_monsters_atlas.png'); im.file_format = 'PNG'; im.save(); im.pack()
    mat = bpy.data.materials.new('monster_mat')
    try: mat.use_nodes = True
    except Exception: pass
    nt = mat.node_tree; bsdf = nt.nodes.get('Principled BSDF') or nt.nodes.new('ShaderNodeBsdfPrincipled')
    if not bsdf.outputs['BSDF'].links:
        out = nt.nodes.get('Material Output') or nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im; tx.interpolation = 'Closest'; nt.links.new(tx.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 1.0
    for k in ('Specular IOR Level', 'Specular'):
        if k in bsdf.inputs: bsdf.inputs[k].default_value = 0.0
    builder()
    objs = {}
    for pn, info in H.PARTS.items():
        if info['geo']: ob = H.build_part(pn, info, mat)
        else: ob = bpy.data.objects.new(pn, None); bpy.context.collection.objects.link(ob)
        objs[pn] = ob
    for pn, info in H.PARTS.items():
        if info['parent']: objs[pn].parent = objs[info['parent']]
        objs[pn].location = H.B(info['pivot'])
    root = bpy.data.objects.new('mistwater_' + name, None); bpy.context.collection.objects.link(root); objs['body'].parent = root
    tris = sum(len(o.data.polygons) * 2 for o in objs.values() if o.type == 'MESH')
    print('[MISTWATER] %s parts=%d approx tris=%d' % (name, len(objs), tris))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'mistwater_%s.blend' % name))
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'mistwater_%s.glb' % name), export_format='GLB')
    world = bpy.data.worlds.new('w'); world.color = (.32, .32, .33); sc.world = world
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
    sc.render.resolution_x, sc.render.resolution_y = 600, 800
    cd = bpy.data.cameras.new('cam'); cd.lens = 70; cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    tgt = bpy.data.objects.new('tgt', None); bpy.context.collection.objects.link(tgt)
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    for nm, ang, dist, ch, ty in (('front', 0, 4.4 * preview_h, .95 * preview_h, .9 * preview_h), ('34', 40, 4.4 * preview_h, .95 * preview_h, .9 * preview_h), ('head', 25, 1.3 * preview_h, 1.6 * preview_h, 1.45 * preview_h)):
        a = math.radians(ang); cam.location = (math.sin(a) * dist, -math.cos(a) * dist, ch); tgt.location = (0, 0, ty)
        sc.render.filepath = os.path.join(HERE, '%s_%s.png' % (name, nm)); bpy.ops.render.render(write_still=True)

paint()
if bpy is not None and __name__ == '__main__':
    scene_build('bag', build_bag, 1.0)
    scene_build('nurse', build_nurse, 1.0)
    scene_build('boss', build_boss, 1.45)
    print('[MISTWATER] monsters done ->', HERE)
elif bpy is None and __name__ == '__main__':
    from PIL import Image
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(os.path.join(HERE, 'mistwater_monsters_atlas.png')); print('atlas only')
