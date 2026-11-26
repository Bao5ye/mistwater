# 构建：把 assets/ 中的 Blender 模型与贴图内嵌进单文件 index.html
import base64, os
B = os.path.dirname(os.path.abspath(__file__)); A_ = os.path.join(B, '..', 'assets')
s = open(os.path.join(B, 'src.html'), encoding='utf8').read()
uri = lambda p: 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
A = 'const HERO_MODEL=' + open(os.path.join(A_, 'hero.json')).read() + ';\nconst HERO_ATLAS="' + uri(os.path.join(A_, 'hero_atlas.png')) + '";\n'
for k in ('bag', 'nurse', 'boss'): A += f'const {k.upper()}_MODEL=' + open(os.path.join(A_, k + '.json')).read() + ';\n'
A += 'const MON_ATLAS="' + uri(os.path.join(A_, 'mon_atlas.png')) + '";\n'
open(os.path.join(B, '..', 'index.html'), 'w', encoding='utf8').write(s.replace('/*@@ASSETS@@*/', A)); print('built index.html')
