# Healer Hero — Registro técnico para agentes

- Site (GitHub Pages): https://johnathangomesdev.github.io/healer-hero/
- Repo: https://github.com/johnathangomesdev/healer-hero (remote `origin`, branch `main`; Pages publica a raiz da `main` a cada push)
- O GitLab antigo (johndev-group/healer-hero) foi abandonado e o remote dele removido — não use.
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

## 3b. Painel de balanceamento → jogo

- `balanceamento.html` (simulador). O rascunho fica em `localStorage['hh_balance_params_v1']`; o botão **Salvar no jogo** copia para `localStorage['hh_balance_game_v1']`; **Voltar o jogo ao padrão** apaga essa chave.
- O jogo (`index.html`, que é o que o Pages serve) lê `hh_balance_game_v1` no bloco `const BAL = (() => {...})()`, logo após `STAGES_DB`. Ele sobrescreve `ITEMS_DB`, `ENEMIES_DB`, `STAGES_DB` (escala/ondas), `MERCENARIES_DB`, `TIER_MULT`, `COMBINE_COST`, `COMBINE_UP_CHANCE`, `REFINE_BASE` e expõe escalares (`BAL.critChance`, `BAL.hpBase`, `BAL.expGrowth`, custos/força/recarga das skills, `BAL.dropChance`, `BAL.tabCosts`, stats da família...).
- Ao adicionar um número balanceável novo: ponha o padrão em `BAL`, leia-o no bloco e use `BAL.x` no código, nunca o literal.
- Só vale no mesmo navegador + mesma origem (localStorage). Não entra no código para outros jogadores. Drops fixos de chefe e "unlock" dos mercs ainda são fixos no código.

## 3c. Modo Robô (menu DEV)

- Botão `#dev-robot`; código em `ROBOT`/`robotTick` (seção 12b' do `index.html`), chamado no `loop` só com `DEV.on && ROBOT.on` (respeita a velocidade do DEV). Pula guias do tutorial (`guideFinish`).
- Replica o jogador "certo" do `simulate()` do balanceamento: distribui pontos pela proporção `strategy.alloc`, guarda DPE até a classe definitiva e depois compra o nível de skill mais barato liberado, equipa o melhor item por `strategy.weights`, contrata/troca o mercenário mais forte (`replaceRatio`, `saveForMerc`), combina 3 piores do mesmo tier, compra aba/descarta o pior com bolsa cheia, refina pelo melhor ganho/ouro, coleta todos os drops, escolhe a vocação `strategy.stance`, avança na vitória e na derrota volta ao início do ato (`farmOnLoss`).
- Estratégia lida de `hh_balance_game_v1` (ou o rascunho `hh_balance_params_v1`) ao ligar o robô. Se mudar a lógica do simulador, mude aqui também.
- Teste headless: trocar `setTimeout` por fila manual e chamar `updateSimulation(0.05)` + `robotTick(0.05)` em laço (20 min de jogo → chega ao Ato 5 sem derrotas com os valores padrão).

## 3d. Regras de drop, tutorial e classes (2026-11-18)

- Tier do drop aleatório: `rollDropTier(dropTierCap(entity))`. Comum até Raro, alfas (boss:true) até Mítico, Lendário só do Necromante; peso de cada tier = `BAL.tierDecay^k` (padrão 0.3). Drops fixos de alfa são limitados com `capTier` (a Armadura da Alvorada cai Mítica do Lobo Alfa). O drop guarda `d.tier`.
- Tutorial usa `TUTORIAL_WOLF` (Lobo Faminto, mais fraco, rig ZOMBIE_WOLF) em 1-2/1-3.
- Peitorais travados por classe: MONK_ROBE→MONK, KNIGHT_PLATE e GOLDEN_ARMOR→TANK, ELVEN_TUNIC→ARCHER; sem peitoral = roupa de aldeão. SAINT_ROBE→SAINT (2026-11-20). EXO_ROBE→EXORCIST.
- Ritmo: meta de ≥30 min jogando perfeito. Medido com o Modo Robô no jogo real (headless): Monge ~41, Exorcista ~44, Santo ~53 min. O simulador do painel NÃO bate com o jogo real (erra por classe); valide mudanças de ritmo com o robô, não só com o simulador.
- Escalas das fases e ouro dos monstros ficam iguais em `index.html` (STAGES_DB/ENEMIES_DB) e `balanceamento.html` (DEFAULTS); mude os dois juntos.

## 3e. Estrutura atual (2026-11-18, fim do dia)

- 5 fases por ato (X-1..X-5), chefe na X-5; tutorial: irmã em 1-2, pai cai e Monge em 1-5 (câmera lenta `SLOWMO` no golpe final, depois a escolha de vocação). Indicador `dot-sub-1..5`.
- Vida/mortes continuam entre fases do ato; `startStage` só cura/revive em X-1 ou após derrota (`freshStart`). O simulador faz o mesmo (`hpFrac`, `freshNext`).
- `BAL_VERSION` (jogo) = `DEFAULTS.version` (painel); balanceamento salvo com outra versão é ignorado.
- Itens de duas mãos (`twoHanded`): Cajado do Santo, Orbe do Exorcista, Bandagens, Cajado do Necromante. `fixTwoHanded`, `autoEquipClassWeapon`. Cajado/orbe só aparecem no sprite se equipados.
- Equipamento inicial: Roupa/Botas de Pano (todos), Espada Velha + Broquel de Madeira (pai), Arco de Caça (filha), Cajado (herói) + Orbe na bolsa.
- Visual: `hpBarY(ent)` por tipo de monstro, `BEAR_SIZE` 1.31, coroa + anel vermelho nos `isBoss`, rastro de golpe por `trailRecord`/`drawWeaponTrails` (ponta da espada e punho do Monge).
- Robô tem vigia anti-travamento (4 s parado → `startStage`).
- Ritmo após 5 fases (robô, escala Atos 2-5 ×0.8): Monge ~29, Santo ~38, Exorcista ~77 min. Pendente: equilibrar Exorcista e garantir ≥30 min no Monge.

## 3f. Fragmentos (2026-11-19)

- `state.frags = {COMMON..DIVINE}` (salvo no save; `frags()` cria se faltar). Craft tem 3 modos: Combinar, Refinar e **Quebrar/Trocar** (um menu só, duas colunas). Quebrar: o jogador escolhe vários itens da bolsa (`craft.salvage` é lista de uid), qualquer item, sem restrição; `salvageItem` destrói e dá `BAL.fragYield + BAL.fragPerPlus × plus` fragmentos do tier. Trocar: `tradeFrags`, `BAL.fragTrade` (padrão 3) de um tier → 1 do seguinte. Barra `#craft-frags` mostra o saldo.
- Refinar custa ouro + `refineFragCost(inst)` = `fragRefine × (1 + ⌊plus/2⌋)` fragmentos do tier do item; falha perde os dois.
- Robô e simulador: só quebram item que ninguém do time usa (`itemUselessForTeam`, depois da vocação), no início de cada gestão de itens; bolsa cheia → quebra o pior em vez de descartar; faltando fragmento para refinar → só troca fragmentos de tiers abaixo. Para o jogador não há selo nem restrição (o uso depende do mercenário que ele vai comprar). Painel: campos na aba Itens.
- Efeito no simulador (Santo, padrões, troca 3:1): 63 → ~136 min, refinos 116 → ~46, combinações ~35.

## 3g. Economia, dificuldades e ranking (2026-11-19)

- Ouro dos monstros × `BAL.goldMult` (0.7). Ao vencer o chefe X-5 (fora do tutorial): prêmio `BAL.actBonus` (0.3) × ouro ganho no ato (`state.chapterEarned.gold`, zera no X-1). Custos: `COMBINE_COST` e `REFINE_BASE` +50%, `SALVAGE_COST` por tier (quebrar custa ouro), `fragYield` 5, `fragPerPlus` 2. `BAL_VERSION` = 7.
- Dificuldades: `state.cycle` (0 Normal, 1 Difícil, 2 Insano, 3 Infernal, 4+ Infernal II, III…), `DIFFS` / `diffOf(c)` / `curDiff()`. Multiplica stats dos monstros (`stat`), ouro/DPE/EXP, chance de drop, raridade (`decay` × `BAL.tierDecay`) e tiers extras (`cap`, também nos drops fixos dos alfas via `upTier`). Aplicado em `spawnEnemy`, `dropTierCap`, `rollDropTier`.
- 5-5 tem `next: 'NEXT_CYCLE'`: `startStage('NEXT_CYCLE')` sobe o ciclo e vai para `C1-1`. `C1-1..C1-5` = Ato 1 de ciclo (sem eventos, `ZOMBIE_WOLF` no lugar do lobo do tutorial, escala 3.2→3.8, `start: 'C1-1'`). Use sempre `actStartId(cfg)` em vez de `${act}-1`. Ato exibido = `displayAct(cfg)` = ciclo×5 + ato (`toRoman` genérico). HUD mostra `#lbl-diff`; o mapa tem seletor das dificuldades já liberadas (`state.maxCycle`).
- Save guarda `cycle`, `maxCycle`, `playTime` (tempo real), `cheated` (Modo DEV ligado), `rankedUpTo`.
- Ranking local (`hh_ranking_v1`, nome em `hh_player_name`): 1ª vitória sobre o Necromante em cada dificuldade por save grava `{name, cycle, act, time, level, stance, dev}`; ordena por dificuldade desc e tempo asc. `#modal-ranking` fica fora do `#hud-root` (abre no menu principal e na vitória do 5-5) com CSS próprio. **Não é online**: precisa de um backend (Supabase/Firebase etc.) para ser compartilhado.
- Simulador: `general.goldMult`, `general.actBonus`, `items.salvageCost`; não simula os ciclos. Santo, padrões: ~87 min.

## 3h. Arte de classes e skills (2026-11-19)

- Logos das classes: `icons/class-{saint,exorcist,monk}.png` via `CLASS_LOGO`/`classIconHtml` (escolha de vocação + nó inicial da árvore).
- Ícones das skills: `icons/skill-{saint,exorcist,monk}-{1,2,3}.png` (1 passiva, 2 ativa, 3 ultimate; 128×128, cantos arredondados transparentes) via `SKILL_IMG_KEY`/`skillIconHtml`, usados na barra de skills, na árvore e nos cards do Time. `SKILL_ICONS` (SVG) é só reserva.
- Card de mercenário no Time mostra a ultimate real (`MERC_ULT`).
- Ícones de dificuldade: `icons/diff-{normal,dificil,insano,infernal}.png` via `DIFF_ICONS`/`diffIconSrc(ciclo)`. No HUD, `#img-diff` fica dentro da barra de waves, à esquerda do número do ato (margem negativa para não aumentar a barra), sempre visível; Infernal II+ mostra numeral em `#lbl-diff-n`. Também no seletor de dificuldade do mapa.
- Clicar no ícone (`#lbl-diff`, com stopPropagation para não abrir o mapa) abre `#diff-picker` (`renderDiffPicker`): lista as dificuldades liberadas (0..`maxCycle`) e vai para o início do MESMO ato na escolhida (Ato I: `C1-1`, ou `2-1` no Normal pós-tutorial). Fecha ao clicar fora.
- Mira dos monstros (2026-11-20): `e.lockTarget` = herói mais próximo que entrou no alcance (`e.range`); fica travado enquanto vivo e no alcance. Não usa mais o "mais à frente"/formação.

- Ícones dos menus: `icons/menu-{team,quests,tree,bag,tavern,craft}.png` (gavetas 0-5) e `menu-{autoskill,repeat,autoadvance,settings}.png` (barra superior), aplicados em `applyCartoonIcons` por `putImg` (classe `.img-btn`, sem fundo/borda; `.img-toggle` desligado fica cinza; gaveta aberta = brilho + escala).

- Roupa do Santo (2026-11-20): peças `st_*` numa linha `Object.assign(RIG_SRC, {...})` logo depois da `RIG_SRC` (também base64 — **não ler**). `HUMAN_SKINS.saint` (capuz = cabeça inteira com `noHair`, manto, mangas, antebraços, coxa+bota como o monge, `staff: [img, pivô, y da cruz]`). Itens `SAINT_HOOD` (HEAD), `SAINT_ROBE` (CHEST), `SAINT_BOOTS` (FEET), classe SAINT, no pool de drop; `SAINT_STAFF` agora desenha a arte `st_staff` (brilho na cruz ao conjurar). Recorte feito tirando fundo + anel branco da folha do usuário e escalando cada peça para o tamanho da equivalente do monge.

- `WOODEN_ROSARY` agora se chama **Capuz do Noviço** (id mantido por causa dos saves): capuz do Santo com `NOVICE_TINT` (`ITEM_SKIN.cowlTint`).
- **Capuz em 2 camadas** (`HUMAN_SKINS.x.cowl = {back, front, pv}`, `ITEM_SKIN.cowl`): `back` (abertura pintada de sombra) é desenhado antes da cabeça base, `front` (abertura transparente) depois do rosto — a cabeça/rosto do personagem aparece pelo recorte; sem cabelo. Peças `st_hoodB/st_hoodF` (substituíram `st_hood`) e `ex_hoodB/ex_hoodF`. Gerados pelo script `hollow` (flood fill da pele a partir do centro do rosto).
- **Set do Exorcista aprendiz** (2026-11-20): peças `ex_*` numa segunda linha `Object.assign(RIG_SRC, {...})` (base64 — **não ler**), `HUMAN_SKINS.exorcist` (pivôs copiados do Santo, `book`). Itens COMMON, classe EXORCIST, no pool de drop: `EXO_HOOD` Capuz do Aprendiz, `EXO_ROBE` Manto do Aprendiz, `EXO_BOOTS` Botas do Aprendiz, `EXO_GRIMOIRE` Grimório Gasto (2 mãos, desenhado na mão com brilho roxo ao conjurar; `ITEM_SKIN.book`). Stats um pouco acima da roupa de aldeão.
- **Exorcista não usa mais orbe**: `EXORCIST_ORB` (id mantido pelos saves) agora é o **Livro do Exorcista**, desenhado com a arte `ex_book` (`ITEM_SKIN.EXORCIST_ORB = {book}`); o código do orbe foi removido.
- **Set do Monge iniciante** (2026-11-20): peças `mi_*` numa terceira linha `Object.assign(RIG_SRC, {...})` (base64 — **não ler**), `HUMAN_SKINS.monkInit` (pivôs do monge; `neck` = colar desenhado no pescoço entre tronco e cabeça). Itens COMMON, classe MONK, no pool: `MONK_INIT_BEADS` Colar de Contas (HEAD: cabeça careca tatuada + colar), `MONK_INIT_TUNIC` Túnica do Iniciante, `MONK_INIT_SANDALS` Sandálias do Iniciante, `MONK_INIT_WRAPS` Faixas do Iniciante (2 mãos, troca os antebraços).
- **Set do Guerreiro intermediário (couro)** (2026-11-20): peças `wl_*` numa quarta linha `Object.assign(RIG_SRC, {...})` (base64 — **não ler**), `HUMAN_SKINS.leather` (elmo como `cowl` com `s` = escala e `hair: true` = franja aparece; luvas como `hand`; calça + botas com coxa). Itens COMMON (TANK; elmo/armadura/botas/escudo também PALADIN), no pool: `LEATHER_HELM` Elmo de Couro, `LEATHER_ARMOR` Armadura de Couro, `LEATHER_BOOTS` Botas de Couro, `STEEL_SHORTSWORD` Espada de Aço, `ROUND_SHIELD` Escudo Redondo. Stats ~metade do Vanguarda.
- **Set do Paladino avançado** (2026-11-20): peças `pa_*` numa quinta linha `Object.assign(RIG_SRC, {...})` (base64 — **não ler**), `HUMAN_SKINS.paladin` (elmo alado `cowl` com franja; armadura com capa; manoplas; grevas; malho no slot `sword`). Itens classe PALADIN no pool: `PALADIN_HELM` Elmo Alado (COMMON), `PALADIN_ARMOR` Armadura do Paladino (UNCOMMON), `PALADIN_GREAVES` Grevas (COMMON), `PALADIN_SHIELD` Escudo da Cruz (UNCOMMON). `PALADIN_MACE` virou **Malho do Paladino** e usa a arte `pa_hammer` (o caso especial `drawMaceShape` na mão foi removido; a função ficou sem uso).
- **Set do Arqueiro intermediário (patrulheiro)** (2026-11-20): peças `ar_*` numa sexta linha `Object.assign(RIG_SRC, {...})` (base64 — **não ler**), `HUMAN_SKINS.ranger` (corpo da irmã; capuz `cowl` com franja; luvas; arco `ar_bow` espelhado/girado para ficar como o `s_bow` e **sem corda** — a corda é desenhada por código entre `top`/`bot`). Itens COMMON, classe ARCHER, no pool: `RANGER_HOOD` Capuz do Patrulheiro, `RANGER_VEST` Gibão do Patrulheiro, `RANGER_BOOTS` Botas do Patrulheiro, `RANGER_BOW` Arco Recurvo, `RANGER_QUIVER` Aljava de Couro (entre o Arco de Caça e o set élfico).
- **Dano físico x mágico** (2026-11-20): `receiveDamage(raw, attacker, isHoly)` — `isHoly` agora significa **dano mágico**: reduzido por `getRes() * BAL.resMit`; físico por `getDef() * BAL.defMit` (antes o mágico ignorava tudo). `getRes()` = `baseRes` (stats.res, ou metade da def base) + `BAL.resFromDefPt` (0.5) × pontos de Defesa + `equipRes` (bônus `res` dos itens, opcional; `instBonuses` e `bonusTip` mostram). `dmgTypeOf(ent)`: heróis = MAG, mercenário = `MERCENARIES_DB.dmgType` (padrão PHYS), monstro = `ENEMIES_DB.dmgType`. Monstros têm `res` (slimes/ursos baixos, Necromante def 12 / res 18 e ataque MAG). Número de dano roxo = mágico. Painel de Atributos mostra tipo de dano + RES; taverna mostra RES e o tipo. `stat4` do BAL preserva `res`. Robô: `weights.*.res`, papel/alloc `MAGE`. Ritmo (robô, Normal): Santo ~29, Exorcista ~24, Monge ~42 min (antes 36/23/32; variação alta entre execuções). Simulador não modela res.
- **Mercenário Mago** (`MERCENARIES_DB.MAGE`, rig `MAGE`, `dmgType: 'MAG'`, `ranged`, `range: 220`): projétil `fireBolt`/`drawBoltShot` (em `arrowShots` com `bolt: true`), ultimate `MERC_ULT.MAGE` Explosão Arcana (mágico em todos). `mercIsRanged`/`mercRange` substituem `rig === 'ARCHER'` na criação. Sprite `mg_*` (sétima linha `Object.assign(RIG_SRC…)` — **não ler**), `HUMAN_SKINS.mage` (chapéu `hood`, cajado `mstaff` na mão de trás, tomo `tome` na da frente via `heldTome`). Itens classe MAGE: `MAGE_HAT`, `MAGE_ROBE`, `MAGE_BOOTS`, `MAGE_STAFF`, `MAGE_TOME` (pool). O robô não contrata o Mago (força menor que a Arqueira em `robotMercPower`).
- **Set do Santo iniciante (noviço)** (2026-11-20): peças `sb_*` numa oitava linha `Object.assign(RIG_SRC…)` (**não ler**), `HUMAN_SKINS.saintBase`. O **Capuz do Noviço** (`WOODEN_ROSARY`) agora usa o capuz de linho `sb_hoodB/F` (sem tinta; `NOVICE_TINT` ficou sem uso). Itens classe SAINT no pool: `NOVICE_HABIT` Hábito do Noviço, `NOVICE_BOOTS` Botas do Noviço, `WOODEN_STAFF` Cajado de Madeira (2 mãos). Cajados do Santo agora vêm de `ITEM_SKIN.staff` (`SAINT_STAFF → saint`, `WOODEN_STAFF → saintBase`; desenho em `isSaint && SK.staff`).
- Recorte de interiores escuros (elmos/capuz) em `scratchpad\hollow_dark*.ps1`: flood fill do escuro que fica a > N px de pixels claros, depois limpeza manual do arco da abertura.
- Pendentes (imagens chegaram no meio de um turno e não foram salvas como arquivo): nova arte do guerreiro Vanguarda (prata/dourado, pluma vermelha — substitui o atual), Paladino intermediário (couro + malho), Mago intermediário e Mago avançado.
- Dica: imagem colada enquanto o agente trabalha não vira arquivo em `images\`; peça para reenviar numa mensagem nova ou salvar em disco.
- Irmã infectada: `addExp` ignora quem não é `faction: 'ALLY'`; a transformação zera `levelUpAura/healAura/buff`; o loop dos monstros também decai essas auras (antes ficava com o efeito de level-up para sempre).

## 3i. Nível dos itens (2026-11-20)

- Instância ganhou `lvl` (`{uid,id,tier,plus,lvl}`; saves antigos sem `lvl` = 1). `itemLvl(inst)`, `levelOkFor(slot, inst)` (nível do personagem ≥ lvl). Trava em `equipItem`, `autoEquipClassWeapon` e `robotEquipAll`.
- Força: `ilvlPower(lvl) = BAL.ilvlMult^⌊lvl/10⌋` (padrão 1.3) multiplica `instBonuses`.
- Nível do drop: `zoneItemLevel()` lê `ACT_ITEM_LVL[ciclo][ato]` = média de nível do herói do robô em cada ato, arredondada de 10 em 10 (Normal 1/1/10/10/10, Difícil 20×5, Insano 20/30/30/30/30, Infernal 40 estimado; além disso +10 por ciclo). Re-medir com o robô se mudar EXP/dificuldade.
- Craft (combinar) mantém o `lvl` do item sorteado. Bolsa mostra o nível no canto (vermelho se não alcança) e no tooltip (`itemTipTitle`). DEV: seletor de nível ao adicionar item.
- EXP: a partir do nível `BAL.expSoftLvl` (20) a curva usa `BAL.expGrowthHigh` (1.10) em vez de `expGrowth` (1.40). Robô: Normal ~36 min, Difícil termina ~nv 29 (~120 min total), Insano chega a ~39.
- O simulador `balanceamento.html` ainda NÃO modela nível de item nem a curva suave de EXP.

## 3j. Editor de sprites (2026-11-20)

- Cada ocorrência da mesma imagem num personagem tem chave própria: `foreR` (1ª), `foreR#2` (2ª)... (`sprKey`/`SPR_OCC`, zerado em `sprLayered`). Sem ajuste próprio, a 2ª segue a 1ª (`sprAdjOf`); ao editar, `seAdj(true)` copia o ajuste para cada ocorrência e elas ficam independentes.
- Ajuste de peça aceita `fx`/`fy` (inverter H/V em volta do pivô) e `hide` (deletada: não desenha no jogo; no editor aparece a 18% para poder restaurar).

- **Edições por personagem** (escopo): `sprScopeOf(ent, stance)` → `HEALER.SAINT|EXORCIST|MONK`, `FATHER`, `SISTER`, `VANGUARD_WARRIOR`, `PALADIN`, `ELVEN_ARCHER`, `MAGE` ou o rig do monstro. `sprLayered` define `SPR_SCOPE`; ajustes ficam em `parts['ESCOPO|peça']` / `joints['ESCOPO|articulação']` (posição, rotação, escala, inverter, deletar, camada e articulações). Sem ajuste próprio, cai no ajuste comum antigo (sem escopo). No editor: `SE.scope`, `seEff`/`seOwn`/`seAdj`; `ent.sprScope` força o escopo. Personagem novo: acrescente o caso em `sprScopeOf` e, no editor, `scope` no `SE_CHARS` se o rótulo não bastar.

- **Alcance corpo a corpo** (2026-11-20): o aliado melee para a `min(38 + 8×slot, alcance do monstro − 8)` do monstro (antes a distância passava do alcance do lobo/urso: o monstro andava, o aliado recuava = empurrão infinito). Monstro ataca o primeiro aliado que entra no alcance (`lockTarget`) e não passa do aliado mais à frente (`x >= frente + 8`); aliados só recuam com golpe de alfa/chefe (`allyKb`). Antes, vários lobos empurravam o mercenário até o herói. Ranged (Necromante) continua livre.

## 3k. Aldeão base do PSD (2026-11-21) — PADRÃO VISUAL

- Fonte: `assets/Personagem Base Montado.psd` (camadas: cabeça, cabelo, torso, ombro/braço/mão D e E, coxa/pé D e E; "Camada 0" é só referência). Peças `v_*` numa linha `Object.assign(RIG_SRC…)` própria (base64 — **não ler**); `HUMAN_SKINS.base` usa coxa + pé articulados no joelho e `wrist` (novo campo opcional: ponto do pulso no antebraço, padrão `[0, 64]`).
- Escala: 0.92 px do PSD = 1 px da arte (imagens guardadas em meia resolução, como as outras). Os pivôs/articulações foram calculados medindo o rig no navegador para a pose parada (Santo, sem item) ficar idêntica à montagem do PSD. Olhos/boca foram apagados da arte (o rosto é desenhado por código, alinhado aos olhos do PSD).
- Mapeamento: braço R do jogo = camadas "D" (lado esquerdo da tela); perna R do jogo = camadas "E" (a da esquerda, por cima).
- Ajustes de articulação `*base.*` antigos (feitos para a arte velha) foram removidos de `SPR_ADJ_FILE`.
- **Toda roupa nova deve seguir este corpo** (tamanho, proporção, posição). Para refazer: scripts `prep.py` → `fit.py` → `build.py` → `apply.py` (scratchpad da sessão; refazer igual se o PSD mudar).

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

- (2026-11-21) Grupos do PSD já encaixados: `guerreiro` → skin `knight` (peças `vg_*`, item novo `KNIGHT_HELM`), `monge` → skin `monkInit` (peças `mo_*`; itens MONK_INIT_*; cabeça própria careca, `noHair`). Script: `outfit.py <grupo> <prefixo>` usa as matrizes medidas do aldeão (fit.json) e apaga olhos/boca da cabeça.

- (2026-11-21) **Limpeza de sprites**: só ficam as roupas do PSD do aldeão — Vanguarda (`knight`, `vg_*`), Monge iniciante (`monkInit`, `mo_*`), Arqueiro (`ranger`, `aq_*`, grupo `arqueiro`; itens RANGER_*; capuz com cabelo próprio `hair`) + aldeão base e a Filha. Roupas de Santo, Exorcista, Monge avançado, couro, Paladino, Mago e Élfica foram removidas (os itens continuam, sem visual; ícone genérico). Paladino usa o visual do Vanguarda com o malho (`pa_hammer`). Mercenária élfica = sprite da Filha. Imagens sem uso foram apagadas de RIG_SRC (4,9 MB → 2,6 MB). Ferramenta `tools/cortar_pecas.py` corta folhas do GPT.

- (2026-11-22) **Drops procedurais** (sem drops fixos; só o manto da Irmã continua): `DROP_DEF`/`rollProceduralDrop`/`mobLevel` no index.html, aba **Drops** no balanceamento (`P.drops`; o jogo lê via `BAL.drops`). Comum: só equipamento (cabeça/peito/pés); alfa/chefe: `bossChance`, `weaponPct` arma; peças com chance igual, `exclude` = itens iniciais; armas do mesmo tipo de dano do monstro × `typeBias` (MAG = Santo/Exorcista/Mago); raridade em % por monstro (+`D.cap` tiers nas dificuldades); nível = `zoneItemLevel()` + `lvl` do monstro. Simulador usa as mesmas regras.
