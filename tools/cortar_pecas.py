"""Corta as peças de uma folha "Paper Slice" (gerada no GPT) do mesmo jeito que o recorte manual:
mantém o contorno preto + o interior de cada peça e apaga o resto (fundo, anel branco, textos, molduras).

Uso:
  python tools/cortar_pecas.py "assets/Folha.png"
  python tools/cortar_pecas.py "assets/Folha.png" --nomes "cabelo,cabeca,capuz,ombro D,braco D,mao D,torso,ombro E,braco E,mao E,coxa D,coxa E,pe D,pe E"

Saída: pasta "<folha>_pecas/" ao lado da imagem, com
  - um PNG transparente por peça (peca_01.png... ou o nome dado em --nomes, na ordem de leitura:
    de cima para baixo, da esquerda para a direita; o personagem montado da direita vira "preview.png")
  - _indice.png: a folha com o número de cada peça desenhado (para conferir a ordem)
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


def cortar(caminho, nomes=None, min_area=1500):
    im = Image.open(caminho).convert('RGBA')
    a = np.array(im).astype(np.int32)
    rgb = a[..., :3]
    H, W = rgb.shape[:2]
    # cor do fundo = mediana da borda da imagem
    borda = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(borda, axis=0)
    lum = rgb.mean(-1)
    sat = rgb.max(-1) - rgb.min(-1)
    perto_fundo = np.abs(rgb - bg).sum(-1) < 45
    branco = (rgb.min(-1) > 175) & (sat < 45)          # anel branco, textos e molduras
    removivel = perto_fundo | branco | (a[..., 3] < 20)
    # tudo que é removível e está ligado à borda da imagem = fora das peças
    lab, n = ndimage.label(removivel)
    toca = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fora = np.isin(lab, list(toca))
    # meio-tom entre o anel branco e o contorno preto (antisserrilhado): sai também
    for _ in range(2):
        viz = ndimage.binary_dilation(fora) & ~fora & (lum > 110) & (sat < 60)
        fora |= viz
    dentro = ~fora
    dentro = ndimage.binary_opening(dentro, iterations=1)
    lab, n = ndimage.label(dentro)
    objs = ndimage.find_objects(lab)
    pecas = []
    for i, sl in enumerate(objs, start=1):
        if sl is None: continue
        m = lab[sl] == i
        area = int(m.sum())
        if area < min_area: continue
        # sombra projetada (escura e sem cor, sem nada claro dentro): não é peça
        colorido = ((sat[sl] > 40) | (lum[sl] > 90))[m].mean()
        if colorido < 0.15: continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        pecas.append({'id': i, 'box': (x0, y0, x1, y1), 'area': area})
    if not pecas:
        print('nenhuma peça encontrada'); return
    # personagem montado: a maior peça (fica à direita)
    prev = max(pecas, key=lambda p: p['area'])
    soltas = [p for p in pecas if p is not prev]
    # ordem de leitura: linhas (centro vertical próximo) e depois esquerda -> direita
    soltas.sort(key=lambda p: (p['box'][1] + p['box'][3]) / 2)
    linhas, atual = [], []
    for p in soltas:
        cy = (p['box'][1] + p['box'][3]) / 2
        if atual and cy - np.mean([(q['box'][1] + q['box'][3]) / 2 for q in atual]) > 90:
            linhas.append(atual); atual = []
        atual.append(p)
    if atual: linhas.append(atual)
    ordem = [p for ln in linhas for p in sorted(ln, key=lambda p: p['box'][0])]
    pasta = os.path.splitext(caminho)[0] + '_pecas'
    os.makedirs(pasta, exist_ok=True)
    if nomes and len(nomes) != len(ordem):
        print(f'aviso: {len(nomes)} nomes para {len(ordem)} peças — usando números')
        nomes = None
    alpha = (dentro * 255).astype(np.uint8)
    saida = []
    for k, p in enumerate(ordem + [prev]):
        x0, y0, x1, y1 = p['box']
        m = (lab[y0:y1, x0:x1] == p['id'])
        pedaco = a[y0:y1, x0:x1].copy().astype(np.uint8)
        pedaco[..., 3] = np.where(m, alpha[y0:y1, x0:x1], 0)
        nome = 'preview' if p is prev else (nomes[k] if nomes else f'peca_{k + 1:02d}')
        Image.fromarray(pedaco).save(os.path.join(pasta, nome + '.png'))
        saida.append((nome, p['box']))
    # índice para conferir
    ind = im.convert('RGB').copy(); d = ImageDraw.Draw(ind)
    try: fonte = ImageFont.truetype('arialbd.ttf', 34)
    except Exception: fonte = ImageFont.load_default()
    for nome, (x0, y0, x1, y1) in saida:
        d.rectangle([x0, y0, x1, y1], outline=(255, 60, 60), width=3)
        rot = nome.replace('peca_', '')
        d.text((x0 + 4, y0 + 2), rot, fill=(255, 230, 0), font=fonte, stroke_width=3, stroke_fill=(0, 0, 0))
    ind.save(os.path.join(pasta, '_indice.png'))
    print(f'{len(saida)} peças salvas em: {pasta}')
    for nome, box in saida: print(f'  {nome}: {box}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('folha')
    ap.add_argument('--nomes', help='nomes separados por vírgula, na ordem de leitura')
    ap.add_argument('--min-area', type=int, default=1500)
    arg = ap.parse_args()
    cortar(arg.folha, [s.strip() for s in arg.nomes.split(',')] if arg.nomes else None, arg.min_area)
