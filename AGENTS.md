# Healer Hero — Registro técnico para agentes

- Site (GitHub Pages): https://johnathangomesdev.github.io/healer-hero/
- Repo: https://github.com/johnathangomesdev/healer-hero (remote `github`, branch `main`; Pages publica a raiz da `main` a cada push)
- O GitLab antigo (remote `origin`, johndev-group/healer-hero) foi abandonado — não use.
- Arquivo principal: `healer_hero_procedural_idle_rpg_prototype.html` (≈7000 linhas, HTML + CSS + JS em um único arquivo, sem build).
- Idioma da UI e do usuário: português (BR).

> ⚠️ **Nunca leia as linhas `RIG_SRC` (~linha 2490) e `MON_SRC`**: são strings base64 enormes com os sprites recortados. Use Grep com offset/limit e pule essas linhas.

---

## 1. Arquitetura geral

| Sistema | Onde / nomes | Como funciona |
|---|---|---|
| Sprites (rig "paper slice") | `RIG_SRC`, `MON_SRC`, `rigPart`, `monPart`, `sprDraw` | Peças de sprite em base64 desenhadas em Canvas 2D, montadas por articulações. |
| Ajustes de sprite | `SPR_ADJ`, linha `SPR_ADJ_FILE` | Por peça `{x,y,r,s,z}` (posição, rotação, escala, camada) e por articulação `{x,y}`. `JT()` aplica offsets de articulação. `SPR_REC` registra o que foi desenhado (hit-test do editor). `SPR_Q` + `sprLayered` fazem desenho adiado ordenado por `z`. |
| HUD responsivo | `#hud-root`, `HUD_S`, `CAM`, `VIEW`, `clientToWorld`, `hiRes` | Equivalente HTML ao Godot 640×360 / canvas_items / expand. HUD escalado por `HUD_S`; mundo com transform uniforme + expand; canvases pequenos (ícones/previews) renderizados em resolução real via `hiRes`. |
| Cenário | `scnBuild`, `scnDraw`, `SCN_TW=960`, `SCENE_PAL` | Camadas parallax pré-renderizadas (lua de sangue, floresta em chamas). Tutorial usa só o primeiro cenário, sem transição de céu. |
| Itens | `state.inv`, `equippedSlots`, `instView`, `instBonuses`, `eqIdsOf`, `itemIdOf`, `TIER_MULT` | Cada item é instância `{uid,id,tier,plus}`. Slots guardam `uid`. Bônus = base × `TIER_MULT` × (1 + 12% por nível de refino). **`state.ownedItems` não existe mais.** |
| Visual por item | `composeHumanSkin`, `ITEM_SKIN` | Sprite do herói só muda quando o item correspondente está equipado. |
| Time / formação | `state.formation` (padrão `[2,1,0]`), `slotHomeX(s)`, `POS_X=[90,150,215]`, `firstFreeTeamSlot`, `ent.mercKey` | Mercenário contratado vai para o primeiro slot livre; não pode ser contratado 2×; ordem dos cards no menu Time = formação (arrastar). |
| Som | `PSFX` (antes de `class SoundFX`), `SoundFX._custom`, mapa de gap | Ver seção 3. |

## 2. Funcionalidades implementadas (por ordem)

1. **Modo DEV** — menu no canto inferior esquerdo: Editar status, Adicionar itens, Dinheiro ∞, DPE ∞, Adicionar monstro, Adicionar herói, Acelerar, Desacelerar.
2. **Editor de sprites** (botão "Editar Sprites" no menu inicial) — move/rotaciona peças, move articulações, altera camada (z-order) de heróis e monstros. Botão **Salvar** grava direto no próprio HTML via File System Access API, reescrevendo a linha `SPR_ADJ_FILE` (não há mais import/export JSON).
3. **HUD responsivo** (ver tabela).
4. **Polimento visual** — ícones nítidos, rastro de golpe, poeira de passos, correção das pernas na caminhada/corrida, take-hit dos monstros, flecha real, efeito de cura (estilo level-up, menor, verde, com cruzes), drops como imagem das peças.
5. **Inventário** — imagens dos itens, arrastar para equipar/desequipar (item equipado sai do inventário), ícones cartunizados, sangue com cor por monstro, correção do avanço automático.
6. **Cenário** baseado na referência do usuário.
7. **Menus padronizados** (mesma fonte e escala).
8. **Resets e abas** — resetar atributos e resetar talentos (custo em gold dobra a cada uso); até 4 abas de inventário compradas.
9. **Tiers**: Comum (branco), Incomum (verde), Raro (azul), Mítico (roxo), Lendário (dourado), Divino (dourado com brilhos brancos).
10. **Mercenários** já vêm com equipamento Comum (ex.: arqueira = arco, botas, flechas, capuz; guerreiro = espada, armadura, broquel, botas). Removida a opção de posição na Taverna.
11. **Craft** — combinar 3 itens do mesmo tier → item aleatório, com pequena chance de subir de tier (custo cresce com o tier); **Refinar** — gold + chance de sucesso, +12% stats por nível.
12. **Destruir item** — arrastar para fora da janela → diálogo de confirmação.
13. **Sons diferenciados** — ver seção 3.

## 3. Áudio (procedural, Web Audio)

- Todos os sons são gerados em código; **nenhum arquivo de áudio é carregado pelo jogo.**
- `PSFX` = sintetizador por amostra (`SR=44100`), renderiza `AudioBuffer`s com cache:
  - `tone(b,o)` (envelope em blocos de 32 amostras; opções `f,f1,glide,amp,tau|env,att,ph,vib,trem`)
  - `noise(b,o)` com `filt: [['lp'|'hp'|'bp', f0, f1, q]]` via `biquadRun`; `buzz`, `normalize`.
  - Receitas: `R.heal`, `R.magic`, `R.bow(draw=0.40)`, `R.arrowHit`, `R.sword`, `R.punch`. Uso: `PSFX.get(ctx, nome, ...args)`.
- As receitas são **cópias procedurais** de referências do usuário (`Downloads\sfx`: bow, heal, magic, punch, sword .mp3), feitas medindo espectrograma, envelope e parciais. Ex.: heal = 8 plins (8419.5, 5017.2, 3746.8, 3337.6, 2820.8, 3165.4×2, 3337.6 Hz) em 0–0.321 s, tau 0.085.
- Mapeamento em `SoundFX._custom` (tabela `P`: `[receita, args, ganho, playbackRate]`, variação ±4%):
  - `SWORD`/`SWORD_CRIT` → sword · `BOW_DRAW` → bow(0.12) (puxada encurtada para caber na animação) · `ARROW_HIT` → ao acertar a flecha · `MAGIC` → Santo/Exorcista (gap 0.6 s, som tem ~2.9 s) · `HEAL` · `PUNCH`/`PUNCH_CRIT` → Monge em postura MONK (`atkIsPunch` em `receiveDamage`).
  - `BOW_RELEASE` é no-op. `WOLF_HOWL` (grave, 190→360→215 Hz, 3 vozes, lowpass 1000), urso e slime continuam com síntese antiga, sem referência.
- `unlock()` pré-renderiza os buffers PSFX em jobs escalonados no primeiro gesto (~0.5 s total).
- WAVs exportados para escuta: `Desktop\healer_hero_sfx\` e `Desktop\healer_hero_sfx\copias_procedurais\` (+ `comparacao_espectrogramas.png`).

## 4. Como testar

- Teste headless com Edge: `msedge --headless --dump-dom` / `--screenshot` com `--user-data-dir` separado.
- **Timers não disparam** em headless (e `--virtual-time-budget` trava) → scripts de teste rodam síncronos.
- Regressão esperada: `ready=true`, `gold=999999 items=5 enemies=4`, e todos os 12 tipos de som tocando sem erro.
- Para achar erros de sintaxe, use `onerror` no script inline (um SyntaxError aparece como "sfx is not defined").

## 5. Armadilhas conhecidas

- Não inserir classes (`ui-btn`) por regex dentro de `${...}` em templates.
- Ao fazer splice de texto via PowerShell, conferir quebras de linha (já quebrou o `if (type === 'WOLF_HOWL')`).
- Novos sprites de roupa/itens: usar o **monge com roupa de aldeão** como referência de proporção; braço padrão = manga + antebraço + mão padrão.
- O editor de sprites só salva em navegadores com File System Access API (Edge/Chrome). Live Server: `liveServer.settings.CustomBrowser` = `microsoftedge`.

## 6. Pendências / ideias

- Ajuste fino de timbre depende do ouvido do usuário (arco um pouco brilhante, soco um pouco grave).
- Magia longa (~2.9 s): pode ser encurtada.
- Uivo, urso e slime aguardam referências.
