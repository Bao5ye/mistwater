# -*- coding: utf-8 -*-
"""
MISTWATER 主角「陈默」— PS1 精度低多边形模型生成脚本（原创角色）
运行：  "G:\\Blender\\blender.exe" -b -P mistwater_hero.py
输出（与脚本同目录）：
  mistwater_hero.glb        游戏用模型（分段骨架层级，Y 向上，面朝 +Z）
  mistwater_hero.blend      可在 Blender 中继续手工精修
  mistwater_hero_atlas.png  512×512 贴图集（最近邻采样，PS1 风格）
  hero_front/side/back/34/face.png  预览渲染
"""
import math, os, sys
import numpy as np
try:
    import bpy, bmesh
except ImportError:
    bpy = None

OUT = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# ============================================================
# 1. 贴图集（numpy 手绘，512×512，行 0 在上）
# ============================================================
ATL = 512
img = np.zeros((ATL, ATL, 4), np.float32); img[..., 3] = 1
REG = {'face': (0, 0, 128, 128), 'hair': (128, 0, 128, 128), 'jacketF': (256, 0, 128, 128), 'jacketB': (384, 0, 128, 128),
       'sleeve': (0, 128, 128, 128), 'jeans': (128, 128, 128, 128), 'skin': (256, 128, 64, 64), 'boots': (320, 128, 64, 64),
       'belt': (384, 128, 64, 64), 'hand': (448, 128, 64, 64)}

def R(n): x, y, w, h = REG[n]; return img[y:y + h, x:x + w]
def grid(a): h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; return xx / (w - 1), yy / (h - 1)
def put(a, m, col, al=1.0):
    m = (m.astype(np.float32) * al)[..., None]; a[..., :3] = a[..., :3] * (1 - m) + np.array(col, np.float32) * m
def rect(a, u0, v0, u1, v1): u, v = grid(a); return (u >= u0) & (u <= u1) & (v >= v0) & (v <= v1)
def ell(a, cu, cv, ru, rv, soft=0.0):
    u, v = grid(a); d = ((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2
    return np.clip((1 - d) / soft, 0, 1) if soft else (d <= 1)
def noise(a, amt, seed, sx=1, sy=1):
    h, w = a.shape[:2]; r = np.random.default_rng(seed); n = r.random((h // sy + 1, w // sx + 1)) - .5
    n = np.kron(n, np.ones((sy, sx)))[:h, :w]; a[..., :3] += n[..., None] * amt
def vgrad(a, c0, c1):
    u, v = grid(a); a[..., :3] = np.array(c0) * (1 - v[..., None]) + np.array(c1) * v[..., None]
def shade_sides(a, k=.35, w=.2):
    u, v = grid(a); s = np.clip(1 - np.minimum(u, 1 - u) / w, 0, 1) * k; a[..., :3] *= (1 - s[..., None])
def dots(a, n, col, seed, region, al=.5):
    r = np.random.default_rng(seed); h, w = a.shape[:2]
    for _ in range(n):
        x, y = int(r.random() * w), int(r.random() * h)
        if region(x / (w - 1), y / (h - 1)): a[y, x, :3] = a[y, x, :3] * (1 - al) + np.array(col) * al

SKIN0, SKIN1 = (.78, .62, .53), (.64, .49, .41)
HAIR = (.09, .07, .055)

def paint():
    # ---- 脸（头部前半周展开：u 0→1 = 右耳→左耳，v 上→下 = 头顶→下颌）----
    a = R('face'); vgrad(a, SKIN0, SKIN1); shade_sides(a, .2, .16)
    u, v = grid(a)
    hl = .16 + .025 * np.sin(u * 40) + .02 * np.cos(u * 17)
    put(a, v < hl, HAIR)
    put(a, ((u < .085) | (u > .915)) & (v < .47), HAIR)
    put(a, ell(a, .02, .45, .05, .09, .6), (.55, .4, .33), .6); put(a, ell(a, .98, .45, .05, .09, .6), (.55, .4, .33), .6)
    for cu in (.33, .67):
        put(a, ell(a, cu, .4, .13, .055, .8), (.45, .3, .25), .35)                       # 眼窝
        put(a, ell(a, cu, .335, .105, .016), (.14, .1, .08))                            # 眉
        put(a, ell(a, cu, .41, .068, .022), (.86, .82, .76))                            # 眼白
        put(a, ell(a, cu + (.004 if cu < .5 else -.004), .41, .026, .022), (.24, .16, .1)) # 虹膜
        put(a, ell(a, cu + (.004 if cu < .5 else -.004), .41, .011, .011), (.03, .02, .02))
        put(a, rect(a, cu - .07, .385, cu + .07, .392), (.2, .13, .1))                  # 上眼睑
        put(a, rect(a, cu - .06, .432, cu + .06, .437), (.5, .34, .28), .5)
        put(a, ell(a, cu + (.13 if cu < .5 else -.13), .5, .06, .05, .7), (.85, .65, .58), .25)  # 颧骨高光
    put(a, rect(a, .487, .4, .513, .55), (.9, .76, .67), .35)                           # 鼻梁高光
    put(a, rect(a, .455, .42, .48, .56), (.48, .32, .26), .3); put(a, rect(a, .52, .42, .545, .56), (.48, .32, .26), .3)
    put(a, ell(a, .5, .575, .075, .022, .5), (.42, .27, .22), .6)                       # 鼻底
    put(a, ell(a, .46, .575, .014, .008), (.25, .14, .11)); put(a, ell(a, .54, .575, .014, .008), (.25, .14, .11))
    for s in (-1, 1):
        for i in range(14): put(a, ell(a, .5 + s * (.1 + i * .004), .6 + i * .006, .006, .006), (.45, .3, .25), .35)
    put(a, ell(a, .5, .712, .11, .013), (.52, .31, .27))                                 # 上唇
    put(a, rect(a, .4, .722, .6, .728), (.28, .15, .13))                                 # 唇线
    put(a, ell(a, .5, .742, .088, .015), (.66, .44, .38))                                # 下唇
    put(a, ell(a, .5, .87, .17, .05, .6), (.45, .3, .25), .35)                           # 下巴阴影
    dots(a, 650, (.18, .12, .1), 7, lambda x, y: y > .62 and not (.38 < x < .62 and .69 < y < .76) and .1 < x < .9, .45)
    noise(a, .04, 1)
    # ---- 头发 ----
    a = R('hair'); a[..., :3] = HAIR; noise(a, .09, 2, 1, 9); noise(a, .04, 3)
    u, v = grid(a); put(a, (v > .82) & (np.sin(u * 60) > .2), (.5, .38, .32), .5)       # 后颈发际
    # ---- 夹克正面（敞开皮夹克 + 深灰扣领衫）----
    a = R('jacketF'); vgrad(a, (.37, .27, .19), (.25, .18, .13)); noise(a, .05, 4, 1, 3)
    u, v = grid(a); half = .14 - .03 * v
    shirt = np.abs(u - .5) < half; put(a, shirt, (.2, .22, .25))
    put(a, shirt & ((np.arange(a.shape[0])[:, None] % 4) == 0), (.14, .15, .18), .7)
    put(a, (np.abs(u - .5) < .07) & (v < .05), (.72, .56, .47))                         # 领口皮肤
    put(a, rect(a, .485, .04, .515, .3), (.15, .16, .19))                               # 门襟
    for y in (.1, .17, .24): put(a, ell(a, .5, y, .012, .008), (.45, .45, .42))
    for s in (-1, 1):
        e = .5 + s * half
        put(a, np.abs(u - e) < .012, (.48, .36, .26)); put(a, np.abs(u - (e + s * .016)) < .005, (.14, .1, .07))
        lap = (np.abs(u - (e + s * .06)) < .06 * (1 - v / .28)) & (v < .28); put(a, lap, (.3, .21, .15))
        es = .5 + s * .122; put(a, rect(a, min(es + s * .02, es + s * .2), .62, max(es + s * .02, es + s * .2), .635), (.14, .1, .07))  # 下袋口
    put(a, rect(a, .08, .2, .24, .28), (.3, .22, .15)); put(a, rect(a, .08, .2, .24, .21), (.5, .38, .27))  # 胸袋盖
    put(a, v > .9, (.2, .14, .1)); put(a, (v > .895) & (v < .905), (.45, .34, .24))
    put(a, shirt & (v > .76) & (v < .84), (.12, .08, .06)); put(a, shirt & (v >= .84), (.18, .22, .3)); put(a, (np.abs(u - .5) < .03) & (v > .77) & (v < .83), (.55, .48, .32))
    put(a, ell(a, .12, .45, .05, .3, .8), (.55, .42, .31), .25); put(a, ell(a, .88, .45, .05, .3, .8), (.55, .42, .31), .25)
    noise(a, .03, 5)
    # ---- 夹克背面 ----
    a = R('jacketB'); vgrad(a, (.36, .26, .18), (.24, .17, .12)); noise(a, .05, 6, 1, 3)
    u, v = grid(a); put(a, np.abs(v - .26) < .006, (.15, .1, .07)); put(a, np.abs(u - .5) < .004, (.15, .1, .07))
    put(a, v > .9, (.2, .14, .1))
    for i in range(6): put(a, ell(a, .2 + i * .12, .55 + (i % 2) * .1, .08, .006), (.16, .11, .08), .5)
    # ---- 袖子 ----
    a = R('sleeve'); vgrad(a, (.36, .26, .18), (.27, .19, .13)); noise(a, .05, 7, 1, 3)
    u, v = grid(a)
    for i in range(5): put(a, np.abs(v - (.45 + i * .025 + .015 * np.sin(u * 12 + i))) < .004, (.15, .1, .07), .7)
    put(a, v > .9, (.21, .15, .1)); put(a, np.abs(u - .5) < .004, (.16, .11, .08))
    put(a, ell(a, .5, .3, .2, .3, .8), (.55, .42, .31), .2)
    # ---- 牛仔裤 ----
    a = R('jeans'); a[..., :3] = (.18, .22, .3)
    h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; put(a, ((xx + yy) % 4) == 0, (.27, .32, .42), .6)
    u, v = grid(a)
    for c in (.25, .75): put(a, np.abs(u - c) < .006, (.12, .14, .2)); put(a, np.abs(u - c - .012) < .003, (.55, .45, .3), .6)
    put(a, ell(a, .5, .5, .25, .12, .8), (.4, .46, .56), .35); noise(a, .05, 8)
    # ---- 皮肤 / 手 ----
    a = R('skin'); vgrad(a, SKIN0, SKIN1); noise(a, .03, 9)
    a = R('hand'); vgrad(a, SKIN0, SKIN1); u, v = grid(a)
    for c in (.32, .45, .58, .71): put(a, (np.abs(u - c) < .008) & (v > .55), (.5, .36, .3), .6)
    noise(a, .03, 10)
    # ---- 靴子 ----
    a = R('boots'); vgrad(a, (.14, .11, .09), (.07, .06, .05)); u, v = grid(a)
    put(a, v > .84, (.03, .03, .03)); put(a, (np.abs(u - .5) < .12) & (v > .15) & (v < .6) & ((np.arange(64)[:, None] % 6) < 2), (.3, .25, .2))
    put(a, ell(a, .5, .3, .3, .25, .8), (.35, .3, .26), .3); noise(a, .03, 11)
    # ---- 皮带 ----
    a = R('belt'); a[..., :3] = (.12, .08, .06); u, v = grid(a)
    put(a, (np.abs(v - .2) < .02) | (np.abs(v - .8) < .02), (.35, .28, .2), .6); noise(a, .03, 12)
    np.clip(img, 0, 1, out=img)

paint()

# ============================================================
# 2. 几何（游戏坐标：x 右、y 上、z 前；导出时转换为 Blender Z 向上）
#    prof: [y, rx, rz, z偏移]，自下而上；用 Catmull-Rom 插值加密
# ============================================================
def cr(prof, sub=2):
    P = [list(p) + [0] * (4 - len(p)) for p in prof]
    if len(P) < 3 or sub < 2: return P
    out = []
    for k in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(0, k - 1)], P[k], P[k + 1], P[min(len(P) - 1, k + 2)]
        for s in range(sub):
            t = s / sub
            out.append([.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t * t + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t ** 3) for i in range(4)])
    out.append(P[-1]); return out


# ---- 参数化雕刻曲面 ----
def G(x, m, s): return math.exp(-((x - m) / s) ** 2)
def interp(t, pts):
    if t <= pts[0][0]: return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0); k = k * k * (3 - 2 * k); return v0 + (v1 - v0) * k
    return pts[-1][1]
def sellip(a, rx, rz, e):
    s, c = math.sin(a), math.cos(a); k = (abs(s) ** e + abs(c) ** e) ** (-1 / e); return s * k * rx, c * k * rz
HEAD_H = .235
def head_base(a, t):
    rx = interp(t, [(0, .044), (.08, .056), (.2, .064), (.35, .07), (.5, .075), (.62, .077), (.75, .076), (.88, .066), (.96, .043), (1, .003)])
    rz = interp(t, [(0, .05), (.08, .068), (.2, .082), (.35, .09), (.5, .096), (.62, .099), (.75, .098), (.88, .086), (.96, .056), (1, .003)])
    zo = interp(t, [(0, -.012), (.12, .006), (.3, .007), (.6, 0), (.85, -.008), (1, -.012)])
    x, z = sellip(a, rx, rz, 2.25)
    c = math.cos(a)
    if t < .42 and c > 0: x *= 1 - .22 * (1 - t / .42) * c        # 下颌收窄成 V 形
    return x, z + zo, rx, rz
def head_fn(uu, t):
    a = uu * math.tau - math.pi; x, z, rx, rz = head_base(a, t); aa = abs(a); fr = max(math.cos(a), 0)
    d = 0
    d += .024 * G(a, 0, .095) * G(t, .46, .06) + .012 * G(a, 0, .085) * G(t, .56, .07)          # 鼻尖、鼻梁
    d += .006 * G(t, .665, .03) * G(aa, .42, .32)                                                 # 眉弓
    d -= .008 * G(t, .595, .035) * G(aa, .53, .14)                                                # 眼窝
    d += .005 * G(t, .51, .05) * G(aa, .85, .22)                                                  # 颧骨
    d += .0055 * G(t, .3, .025) * G(a, 0, .3) + .005 * G(t, .255, .025) * G(a, 0, .26)            # 上下唇
    d -= .0025 * G(t, .277, .007) * G(a, 0, .3)                                                   # 唇缝
    d += .008 * G(t, .13, .05) * G(a, 0, .3)                                                      # 下巴
    d += .004 * G(t, .22, .05) * G(aa, 1.25, .2)                                                  # 下颌角
    d += .009 * G(t, .55, .16) * G(aa, math.pi, .7)                                               # 后脑
    d -= .004 * G(t, .38, .06) * G(aa, .55, .15) * fr                                             # 法令纹凹
    nx, nz = math.sin(a), math.cos(a)
    return (x + nx * d, t * HEAD_H, z + nz * d)
def hair_fn(uu, k):
    a = uu * math.tau - math.pi; aa = abs(a)
    tb = .8 + .015 * math.cos(a * 14) if aa < .95 else (interp(aa, [(.95, .8), (1.6, .6), (2.3, .34), (math.pi, .3)]))
    t = tb + (1 - tb) * k; x, z, rx, rz = head_base(a, t)
    d = .009 * G(t, .55, .16) * G(aa, math.pi, .7) + .004 + .01 * math.sin(k * math.pi / 2) * (1 if t > .7 else .5)
    if aa < .95: d += .006 * k
    nx, nz = math.sin(a), math.cos(a); return (x + nx * d, t * HEAD_H + .004 * k, z + nz * d)
TORSO = [(-.13, .172, .118, 2.2, 0), (-.02, .154, .103, 2.2, 0), (.1, .157, .106, 2.3, .002), (.22, .171, .116, 2.4, .006), (.32, .181, .116, 2.5, .004),
         (.39, .188, .11, 2.6, 0), (.43, .184, .098, 2.6, -.006), (.46, .158, .086, 2.4, -.01), (.485, .118, .074, 2.2, -.012), (.505, .08, .064, 2.0, -.012), (.52, .058, .057, 2.0, -.01)]
def torso_fn(uu, k):
    a = uu * math.tau - math.pi; f = k * (len(TORSO) - 1); i = min(int(f), len(TORSO) - 2); w = f - i; w = w * w * (3 - 2 * w)
    y, rx, rz, e, zo = [TORSO[i][j] + (TORSO[i + 1][j] - TORSO[i][j]) * w for j in range(5)]
    x, z = sellip(a, rx, rz, e); s, c = math.sin(a), math.cos(a)
    z += .013 * G(y, .27, .07) * max(c, 0) ** 2                                                    # 胸
    z -= .006 * G(y, .34, .06) * max(-c, 0)                                                        # 肩胛
    x += math.copysign(1, s) * .012 * G(y, .425, .04) * G(abs(a), math.pi / 2, .55)               # 三角肌
    y += .012 * G(abs(a), math.pi / 2, .7) * G(y, .47, .03)                                        # 斜方肌隆起
    return (x, y, z + zo)
def S(geo, fn, nu, nv, front, back=None, cap=None): geo.append(('surf', fn, nu, nv, front, back or front, cap or (back or front), back is None))

PARTS = {}   # name -> dict(parent, pivot, geo=[(kind,args)])
def part(name, parent, pivot): PARTS[name] = {'parent': parent, 'pivot': pivot, 'geo': []}; return PARTS[name]['geo']
def L(geo, prof, seg, front, back=None, cap=None, c=(0, 0, 0), sub=2): geo.append(('lathe', cr(prof, sub), seg, front, back or front, cap or (back or front), c, back is None))
def BXg(geo, c, s, reg): geo.append(('box', c, s, reg))

g = part('body', None, (0, 0, 0))
g = part('hips', 'body', (0, .9, 0))
L(g, [[-.13, .13, .1], [-.05, .16, .106], [.06, .162, .108], [.1, .16, .106]], 12, 'jeans')
L(g, [[.062, .162, .108], [.112, .162, .108]], 12, 'belt', sub=1)
BXg(g, (0, .087, .11), (.055, .04, .012), 'belt')
for side, sx in (('L', 1), ('R', -1)):
    g = part('leg' + side, 'body', (sx * .088, .9, 0))
    L(g, [[-.43, .056, .06], [-.38, .062, .068], [-.25, .074, .08], [-.15, .084, .09], [-.03, .094, .1], [.04, .078, .082]], 10, 'jeans')
    g = part('knee' + side, 'leg' + side, (0, -.42, 0))
    L(g, [[-.39, .047, .05], [-.33, .049, .053], [-.24, .055, .064], [-.15, .059, .068], [-.02, .058, .063], [.03, .052, .057]], 10, 'jeans')
    L(g, [[-.48, .053, .136, .045], [-.455, .056, .138, .045], [-.43, .054, .13, .043], [-.4, .048, .1, .03], [-.37, .042, .06, .01], [-.33, .045, .052, 0]], 10, 'boots')
g = part('torso', 'body', (0, .98, 0))
S(g, torso_fn, 24, 22, 'jacketF', 'jacketB')
L(g, [[.47, .095, .082, -.012], [.5, .088, .076, -.012], [.55, .072, .066, -.012]], 16, 'jacketB', sub=1)     # 衣领
L(g, [[.49, .05, .053, .004], [.535, .048, .051, .006], [.575, .045, .049, .01]], 12, 'skin', sub=1)          # 颈
g = part('head', 'torso', (0, .555, 0))
S(g, head_fn, 28, 28, 'face', 'hair', 'hair')
S(g, hair_fn, 28, 8, 'hair', 'hair', 'hair')
for sx in (1, -1):                                                                                             # 耳
    L(g, [[.115, .006, .012, -.006], [.135, .011, .02, -.008], [.16, .012, .022, -.01], [.18, .009, .016, -.012]], 8, 'skin', c=(sx * .074, 0, 0), sub=1)
for side, sx in (('L', 1), ('R', -1)):
    g = part('arm' + side, 'torso', (sx * .182, .4, 0))
    L(g, [[-.29, .046, .049], [-.22, .051, .054], [-.13, .056, .06], [-.04, .061, .065], [.01, .062, .066], [.04, .053, .058], [.062, .033, .037], [.074, .006, .007]], 12, 'sleeve')
    g = part('f' + side, 'arm' + side, (0, -.29, 0))
    L(g, [[-.265, .038, .036], [-.24, .05, .05], [-.21, .042, .041], [-.1, .048, .048], [0, .052, .054], [.03, .045, .047]], 10, 'sleeve')
    g = part('h' + side, 'f' + side, (0, -.265, 0))
    L(g, [[-.17, .01, .014], [-.14, .02, .036], [-.1, .023, .044], [-.06, .024, .046], [0, .022, .036], [.012, .018, .028]], 10, 'hand')
    L(g, [[-.07, .008, .008], [-.035, .011, .011], [0, .012, .012]], 6, 'hand', c=(-sx * .012, -.025, .03), sub=1)

# ============================================================
# 3. 构建 Blender 场景
# ============================================================
def uvmap(reg, u, v):
    x, y, w, h = REG[reg]; u = .02 + u * .96
    return ((x + u * w) / ATL, 1 - (y + (1 - v) * h) / ATL)

def B(p): return (p[0], -p[2], p[1])   # 游戏坐标 → Blender（Z 上，面朝 -Y）

def build_part(name, info, mat):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    for item in info['geo']:
        if item[0] == 'lathe':
            _, prof, seg, front, back, cap, c, wrap = item
            y0, y1 = prof[0][0], prof[-1][0]
            rings = []
            for (y, rx, rz, zo) in prof:
                ring = []
                for i in range(seg):
                    a = i / seg * math.tau + math.pi
                    ring.append(bm.verts.new(B((c[0] + math.sin(a) * rx, c[1] + y, c[2] + zo + math.cos(a) * rz))))
                rings.append(ring)
            for k in range(len(prof) - 1):
                v0, v1 = (prof[k][0] - y0) / (y1 - y0), (prof[k + 1][0] - y0) / (y1 - y0)
                for i in range(seg):
                    j = (i + 1) % seg
                    if wrap: reg, u0, u1 = front, i / seg, (i + 1) / seg
                    elif seg / 4 <= i < seg * 3 / 4: reg, u0, u1 = front, (i - seg / 4) / (seg / 2), (i + 1 - seg / 4) / (seg / 2)
                    else:
                        jj = (i - seg * 3 / 4) % seg; reg, u0, u1 = back, jj / (seg / 2), (jj + 1) / (seg / 2)
                    try: f = bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
                    except ValueError: continue
                    for lp, (uu, vv) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): lp[uvl].uv = uvmap(reg, uu, vv)
                    f.smooth = True
            for k in (0, len(prof) - 1):
                if prof[k][1] > .004:
                    try: f = bm.faces.new(rings[k] if k else list(reversed(rings[k])))
                    except ValueError: continue
                    for lp in f.loops: lp[uvl].uv = uvmap(cap, .5, .5)
        elif item[0] == 'surf':
            _, fn, nu, nv, front, back, cap, wrap = item
            rows = [[bm.verts.new(B(fn(i / nu, k / nv))) for i in range(nu)] for k in range(nv + 1)]
            for k in range(nv):
                for i in range(nu):
                    j = (i + 1) % nu
                    if wrap: reg, u0, u1 = front, i / nu, (i + 1) / nu
                    elif nu / 4 <= i < nu * 3 / 4: reg, u0, u1 = front, (i - nu / 4) / (nu / 2), (i + 1 - nu / 4) / (nu / 2)
                    else:
                        jj = (i - nu * 3 / 4) % nu; reg, u0, u1 = back, jj / (nu / 2), (jj + 1) / (nu / 2)
                    try: f = bm.faces.new((rows[k][i], rows[k][j], rows[k + 1][j], rows[k + 1][i]))
                    except ValueError: continue
                    for lp, (uu, vv) in zip(f.loops, ((u0, k / nv), (u1, k / nv), (u1, (k + 1) / nv), (u0, (k + 1) / nv))): lp[uvl].uv = uvmap(reg, uu, vv)
                    f.smooth = True
            bmesh.ops.remove_doubles(bm, verts=rows[-1], dist=.0015)
        else:
            _, c, s, reg = item
            r = bmesh.ops.create_cube(bm, size=1.0)
            for vt in r['verts']:
                vt.co = B((c[0] + vt.co.x * s[0], c[1] + vt.co.z * s[1], c[2] + vt.co.y * s[2]))
            for f in {f for vt in r['verts'] for f in vt.link_faces}:
                for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uvmap(reg, *uv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    return ob

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    im = bpy.data.images.new('mistwater_hero_atlas', ATL, ATL, alpha=True)
    im.pixels.foreach_set(img[::-1].ravel().astype(np.float32))
    im.filepath_raw = os.path.join(OUT, 'mistwater_hero_atlas.png'); im.file_format = 'PNG'; im.save(); im.pack()
    mat = bpy.data.materials.new('hero_mat')
    try: mat.use_nodes = True
    except Exception: pass
    nt = mat.node_tree; bsdf = nt.nodes.get('Principled BSDF') or nt.nodes.new('ShaderNodeBsdfPrincipled')
    if not bsdf.outputs['BSDF'].links:
        out = nt.nodes.get('Material Output') or nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im; tx.interpolation = 'Closest'
    nt.links.new(tx.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 1.0
    for k in ('Specular IOR Level', 'Specular'):
        if k in bsdf.inputs: bsdf.inputs[k].default_value = 0.0
    objs = {}
    for name, info in PARTS.items():
        ob = build_part(name, info, mat) if info['geo'] else bpy.data.objects.new(name, None)
        if not info['geo']: bpy.context.collection.objects.link(ob)
        objs[name] = ob
    for name, info in PARTS.items():
        ob = objs[name]; par = info['parent']
        if par: ob.parent = objs[par]
        ob.location = B(info['pivot'])
    root = bpy.data.objects.new('mistwater_hero', None); bpy.context.collection.objects.link(root)
    objs['body'].parent = root
    # 自然站姿（仅预览；导出的是零位姿）
    tris = sum(len(o.data.polygons) * 2 for o in objs.values() if o.type == 'MESH')
    print('[MISTWATER] parts=%d  approx tris=%d' % (len(objs), tris))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'mistwater_hero.blend'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'mistwater_hero.glb'), export_format='GLB')
    # ---- 预览渲染（自然站姿）----
    for nm, ry in (('armL', -.1), ('armR', .1)): objs[nm].rotation_euler[1] = ry
    for nm in ('fL', 'fR'): objs[nm].rotation_euler[0] = -.15
    world = bpy.data.worlds.new('w'); world.color = (.32, .32, .33); sc.world = world
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
    sc.render.resolution_x, sc.render.resolution_y = 600, 800
    cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 70; cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
    tgt = bpy.data.objects.new('tgt', None); bpy.context.collection.objects.link(tgt)
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    shots = [('front', 0, 4.2, .95, .92), ('34', 40, 4.2, .95, .92), ('side', 90, 4.2, .95, .92), ('back', 180, 4.2, .95, .92), ('face', 15, .9, 1.68, 1.66)]
    for nm, ang, dist, ch, ty in shots:
        a = math.radians(ang); cam.location = (math.sin(a) * dist, -math.cos(a) * dist, ch); tgt.location = (0, 0, ty)
        sc.render.filepath = os.path.join(OUT, 'hero_%s.png' % nm); bpy.ops.render.render(write_still=True)
    print('[MISTWATER] done ->', OUT)

if bpy is not None and __name__ == '__main__':
    main()
elif bpy is None and __name__ == '__main__':   # 无 Blender 时：仅输出贴图集供检查
    try:
        from PIL import Image
        Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'mistwater_hero_atlas.png'))
        print('atlas only (no bpy)')
    except ImportError:
        print('no bpy / PIL')
