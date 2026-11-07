#!/usr/bin/env python3
"""Gera o index.html do catálogo kaevy3d (tema escuro).

Preço de venda direta: "preco_manual" em produtos.json (definido pelo Kaique). Sem ele,
calcula pelo banco do squad (calculadora Onyon 3D, venda direta = lucro igual ao custo).

Uso:  python3 build.py        (depois: git add -A && git commit -m "preços" && git push)
"""
import html
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

AQUI = Path(__file__).resolve().parent
D = json.loads((AQUI / "produtos.json").read_text(encoding="utf-8"))
SQUAD = Path(D["catalogo_squad"])
sys.path.insert(0, str(SQUAD / "tools"))
import margin_dashboard as m  # noqa: E402

CAT = json.loads((SQUAD / "pipeline/data/produtos-catalogo.json").read_text(encoding="utf-8"))["produtos"]


def preco_direto(p):
    if p.get("preco_manual"):
        return float(p["preco_manual"])
    c = CAT[p["id"]]
    custo = m.unit_cost({"gramas": c["gramas"], "horas": c["horas"], "cores": 1, "unidades_por_placa": 1})
    return m.preco_site("Facebook", custo)


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


esc = html.escape
IG = f"https://www.instagram.com/{D['instagram']}/"
LOCAL = D["local"]


def link_pedido(nome, preco):
    if D.get("whatsapp"):
        msg = f"Oi! Vi no catálogo e quero o {nome} ({brl(preco)}) para retirar em {LOCAL}. Ainda tem?"
        return f"https://wa.me/{D['whatsapp']}?text={quote(msg)}"
    return IG


CANAL = "WhatsApp" if D.get("whatsapp") else "Instagram"
LINK_CANAL = f"https://wa.me/{D['whatsapp']}" if D.get("whatsapp") else IG

itens = []
for p in D["produtos"]:
    pd = preco_direto(p)
    eco = round((1 - pd / p["shopee"]) * 100) if p.get("shopee") else 0
    itens.append({**p, "preco": pd, "eco": eco})
max_eco = max(i["eco"] for i in itens)
cont = {k: sum(1 for i in itens if i["categoria"] == k) for k in D["categorias"]}


def partes(v):
    r, c = brl(v).replace("R$ ", "").split(",")
    return r, c


chips = [f'<button class="chip is-on" data-f="todos" aria-pressed="true">Todos <span>{len(itens)}</span></button>']
chips += [f'<button class="chip" data-f="{k}" aria-pressed="false">{esc(v)} <span>{cont[k]}</span></button>'
          for k, v in D["categorias"].items() if cont[k]]

cards = []
for n, i in enumerate(itens):
    reais, cents = partes(i["preco"])
    ancora = f'<p class="ancora">Na Shopee <s>{brl(i["shopee"])}</s></p>' if i.get("shopee") else ""
    selo = f'<span class="eco">−{i["eco"]}%</span>' if i["eco"] > 0 else ""
    cards.append(f'''      <article class="card" data-cat="{i["categoria"]}" style="--i:{n}">
        <figure class="foto">
          <img src="img/{i["img"]}" alt="{esc(i["nome"])}, foto real da peça" loading="{'eager' if n < 2 else 'lazy'}" width="900" height="900">
          <figcaption class="cat">{esc(D["categorias"][i["categoria"]])}</figcaption>
          {selo}
        </figure>
        <div class="corpo">
          <h3>{esc(i["nome"])}</h3>
          <p class="det">{esc(i["detalhe"])}</p>
          <div class="preco" aria-label="Preço {brl(i['preco'])}"><small>R$</small><b>{reais}</b><sup>,{cents}</sup></div>
          {ancora}
          <a class="pedir" href="{link_pedido(i["nome"], i["preco"])}" target="_blank" rel="noopener">Quero esse</a>
        </div>
      </article>''')

# colagem flutuante no topo: 4 peças com etiqueta de preço
colagem_ids = ["goku-ssj4", "muttley-15cm", "harry-potter-croche", "banguela-chaveiro"]
por_id = {i["id"]: i for i in itens}
colagem = "\n".join(
    f'''      <figure class="flut f{k}"><img src="img/{por_id[pid]["img"]}" alt="" width="900" height="900"><span>{brl(por_id[pid]["preco"])}</span></figure>'''
    for k, pid in enumerate(colagem_ids) if pid in por_id)

fita = " ".join(f'<span>{esc(i["nome"])} <b>{brl(i["preco"])}</b></span><i>✦</i>' for i in itens)
hoje = date.today().strftime("%d/%m/%Y")

PAGE = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>kaevy3d · Catálogo de peças impressas em 3D</title>
<meta name="description" content="Colecionáveis, decoração e presentes impressos em 3D. Preço direto, só retirada em {esc(LOCAL)}.">
<meta name="theme-color" content="#0a1226">
<meta property="og:type" content="website">
<meta property="og:title" content="kaevy3d · Catálogo 3D com preço direto">
<meta property="og:description" content="Peças impressas em 3D com fotos reais. Preço direto, retirada em {esc(LOCAL)}.">
<meta property="og:image" content="img/og.jpg">
<link rel="icon" type="image/png" href="img/favicon.png">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700;900&family=Onest:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{
  --noite:#0a1226; --noite-2:#101c38; --painel:#15233f; --painel-2:#1c2d50; --borda:#26385e;
  --texto:#f3f0ea; --mudo:#a5b0c8; --laranja:#ff6a13; --laranja-2:#ff8a3d; --azul:#3b82f6;
  --r:22px;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth;background:var(--noite)}}
body{{margin:0;color:var(--texto);font:16px/1.55 "Onest",ui-sans-serif,sans-serif;background:var(--noite);-webkit-font-smoothing:antialiased;overflow-x:hidden}}
img{{max-width:100%;display:block}}
a{{color:inherit}}
.wrap{{max-width:1160px;margin:0 auto;padding:0 18px}}

/* topo fixo */
.topo{{position:sticky;top:0;z-index:40;background:rgba(10,18,38,.78);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.07)}}
.topo .wrap{{display:flex;align-items:center;justify-content:space-between;gap:12px;height:66px}}
.marca{{display:flex;align-items:center;background:#fffdf9;border-radius:14px;padding:6px 12px;box-shadow:0 0 0 3px rgba(255,106,19,.25)}}
.marca img{{height:30px;width:auto}}
.btn-topo{{font:700 13px/1 "Onest";text-decoration:none;color:#fff;background:rgba(255,255,255,.08);border:1.5px solid rgba(255,255,255,.22);padding:10px 14px;border-radius:999px;white-space:nowrap;transition:.2s}}
.btn-topo:hover{{background:var(--laranja);border-color:var(--laranja)}}

/* palco do topo */
.palco{{position:relative;overflow:hidden;isolation:isolate;padding:40px 0 30px}}
.palco::before{{content:"";position:absolute;inset:-30%;z-index:-3;
  background:
    radial-gradient(38% 34% at 18% 22%,rgba(255,106,19,.55),transparent 70%),
    radial-gradient(34% 38% at 85% 30%,rgba(59,130,246,.45),transparent 70%),
    radial-gradient(40% 40% at 60% 95%,rgba(255,138,61,.35),transparent 70%);
  filter:blur(30px);animation:deriva 16s ease-in-out infinite alternate}}
@keyframes deriva{{0%{{transform:translate(0,0) rotate(0)}}50%{{transform:translate(4%,-3%) rotate(8deg)}}100%{{transform:translate(-4%,3%) rotate(-6deg)}}}}
.palco::after{{content:"";position:absolute;inset:0;z-index:-2;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent 0 11px,rgba(255,255,255,.05) 11px 12px);
  mask-image:linear-gradient(180deg,#000 30%,transparent);-webkit-mask-image:linear-gradient(180deg,#000 30%,transparent);
  animation:camadas 6s linear infinite}}
@keyframes camadas{{to{{background-position:0 -120px}}}}
.fios{{position:absolute;inset:0;z-index:-1;width:100%;height:100%;pointer-events:none;opacity:.9}}
.fios path{{fill:none;stroke-linecap:round;stroke-dasharray:14 22;animation:corre 9s linear infinite}}
.fios .a{{stroke:var(--laranja);stroke-width:3;filter:drop-shadow(0 0 6px rgba(255,106,19,.9))}}
.fios .b{{stroke:#ffb37f;stroke-width:1.5;opacity:.6;animation-duration:13s;animation-direction:reverse}}
.fios .c{{stroke:#7fb0ff;stroke-width:1.5;opacity:.45;animation-duration:17s}}
@keyframes corre{{to{{stroke-dashoffset:-720}}}}

.palco .wrap{{display:grid;gap:30px;align-items:center}}
.pill{{display:inline-flex;align-items:center;gap:8px;font:700 12px/1 "Onest";letter-spacing:.06em;color:#fff;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);padding:9px 12px;border-radius:999px}}
.pill i{{width:8px;height:8px;border-radius:50%;background:#3ddc84;box-shadow:0 0 0 0 rgba(61,220,132,.7);animation:pulso 1.8s infinite}}
@keyframes pulso{{70%{{box-shadow:0 0 0 9px rgba(61,220,132,0)}}100%{{box-shadow:0 0 0 0 rgba(61,220,132,0)}}}}
h1{{font:900 clamp(34px,8.6vw,72px)/1 "Unbounded",sans-serif;letter-spacing:-.035em;margin:16px 0 14px}}
h1 .pula{{display:inline-block;color:var(--laranja);animation:pula 2.6s cubic-bezier(.3,1.6,.5,1) infinite;transform-origin:bottom}}
@keyframes pula{{0%,70%,100%{{transform:translateY(0) rotate(0)}}78%{{transform:translateY(-10px) rotate(-3deg)}}86%{{transform:translateY(0) rotate(2deg)}}}}
h1 .risco{{position:relative;white-space:nowrap}}
h1 .risco svg{{position:absolute;left:-2%;bottom:-.18em;width:104%;height:.36em}}
h1 .risco path{{fill:none;stroke:var(--laranja);stroke-width:7;stroke-linecap:round;stroke-dasharray:420;stroke-dashoffset:420;animation:traco 1.1s .6s ease-out forwards}}
@keyframes traco{{to{{stroke-dashoffset:0}}}}
.sub{{font-size:clamp(16px,2.2vw,19px);color:#d6dbe7;max-width:44ch;margin:0 0 22px}}
.sub b{{color:#fff}}
.acoes{{display:flex;flex-wrap:wrap;gap:10px}}
.cta{{display:inline-flex;align-items:center;gap:8px;text-decoration:none;font:700 15px/1 "Onest";padding:15px 20px;border-radius:16px;transition:.2s}}
.cta.forte{{background:var(--laranja);color:#fff;box-shadow:0 14px 30px -12px rgba(255,106,19,.9)}}
.cta.forte:hover{{transform:translateY(-2px);background:var(--laranja-2)}}
.cta.leve{{background:rgba(255,255,255,.08);color:#fff;border:1.5px solid rgba(255,255,255,.2)}}

/* colagem flutuante */
.colagem{{position:relative;height:340px;max-width:460px;width:100%;justify-self:center}}
.flut{{position:absolute;margin:0;width:46%;aspect-ratio:1/1;border-radius:20px;overflow:visible;
  background:#fff;padding:7px;box-shadow:0 26px 50px -18px rgba(0,0,0,.75);animation:flutua 6s ease-in-out infinite}}
.flut img{{width:100%;height:100%;object-fit:cover;border-radius:14px}}
.flut span{{position:absolute;right:-8px;bottom:-12px;font:900 13px/1 "Unbounded";background:var(--laranja);color:#fff;padding:9px 10px;border-radius:12px;transform:rotate(-4deg);box-shadow:0 10px 20px -8px rgba(255,106,19,.9)}}
.f0 span{{right:auto;bottom:auto;left:-8px;top:-12px;transform:rotate(4deg)}}
.f0{{left:2%;top:4%;--r0:-8deg;animation-delay:0s;z-index:2}}
.f1{{right:2%;top:0;--r0:7deg;animation-delay:-1.5s;z-index:3}}
.f2{{left:10%;bottom:0;--r0:5deg;animation-delay:-3s;z-index:4}}
.f3{{right:8%;bottom:6%;--r0:-6deg;animation-delay:-4.5s;width:38%;z-index:5}}
@keyframes flutua{{0%,100%{{transform:translateY(0) rotate(var(--r0))}}50%{{transform:translateY(-14px) rotate(calc(var(--r0) * -.6))}}}}
@media (min-width:880px){{
  .palco{{padding:70px 0 54px}}
  .palco .wrap{{grid-template-columns:1.15fr 1fr}}
  .colagem{{height:460px;max-width:none}}
  .marca img{{height:36px}}
}}

/* fita de preços */
.fita{{background:var(--laranja);color:#fff;transform:rotate(-1.6deg);margin:10px -10px 0;overflow:hidden;box-shadow:0 18px 40px -20px rgba(255,106,19,.8)}}
.fita div{{display:flex;gap:22px;width:max-content;padding:12px 0;animation:rola 32s linear infinite;font:700 14px/1 "Unbounded";white-space:nowrap;text-transform:uppercase;letter-spacing:.02em}}
.fita b{{color:#0a1226}}
.fita i{{font-style:normal;opacity:.7}}
@keyframes rola{{to{{transform:translateX(-50%)}}}}

/* selos */
.confia{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:40px 0 0;padding:0;list-style:none}}
.confia li{{display:flex;gap:10px;align-items:center;background:var(--painel);border:1px solid var(--borda);border-radius:16px;padding:13px;font-size:13.5px;line-height:1.25;font-weight:500}}
.confia svg{{flex:none;width:26px;height:26px;color:var(--laranja)}}
.confia li.destaque{{grid-column:1/-1;background:linear-gradient(90deg,rgba(255,106,19,.22),rgba(255,106,19,.06));border-color:rgba(255,106,19,.55)}}
.confia li.destaque b{{color:var(--laranja-2)}}
@media (max-width:879px){{.confia{{grid-template-columns:repeat(3,1fr);gap:8px}} .confia li:not(.destaque){{flex-direction:column;text-align:center;gap:8px;padding:12px 8px;font-size:12px}} .confia li.destaque{{font-size:13.5px}}}}
@media (min-width:880px){{.confia{{grid-template-columns:repeat(3,1fr) 1.4fr}} .confia li.destaque{{grid-column:auto}} .confia li{{font-size:14.5px;padding:15px 16px}}}}

/* filtros */
.barra{{display:flex;align-items:end;justify-content:space-between;gap:14px;flex-wrap:wrap;margin:42px 0 16px}}
h2{{font:700 clamp(22px,4vw,30px)/1.1 "Unbounded";letter-spacing:-.02em;margin:0}}
.chips{{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;margin:0 -18px;padding:2px 18px 6px}}
.chips::-webkit-scrollbar{{display:none}}
.chip{{flex:none;font:600 14px/1 "Onest";color:var(--texto);background:var(--painel);border:1.5px solid var(--borda);border-radius:999px;padding:11px 14px;cursor:pointer;transition:.18s}}
.chip span{{font-weight:700;color:var(--mudo);margin-left:4px}}
.chip:hover{{border-color:var(--laranja)}}
.chip.is-on{{background:var(--laranja);border-color:var(--laranja);color:#fff}}
.chip.is-on span{{color:#0a1226}}
@media (min-width:880px){{.chips{{margin:0;padding:0}}}}

/* grade */
.grade{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
@media (min-width:700px){{.grade{{grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}}}
@media (min-width:1040px){{.grade{{grid-template-columns:repeat(4,minmax(0,1fr))}}}}
.card{{position:relative;background:linear-gradient(180deg,var(--painel-2),var(--painel));border:1px solid var(--borda);border-radius:var(--r);overflow:hidden;display:flex;flex-direction:column;
  animation:sobe .6s calc(var(--i)*70ms + .2s) cubic-bezier(.2,.7,.2,1) backwards;transition:transform .25s,box-shadow .25s,border-color .25s}}
@keyframes sobe{{from{{opacity:0;transform:translateY(16px)}}}}
.card:hover{{transform:translateY(-5px) rotate(-.4deg);border-color:rgba(255,106,19,.6);box-shadow:0 26px 60px -24px rgba(255,106,19,.55)}}
.card[hidden]{{display:none}}
.foto{{position:relative;margin:0;aspect-ratio:1/1;overflow:hidden;background:#0d172e}}
.foto img{{width:100%;height:100%;object-fit:cover;transition:transform .5s}}
.card:hover .foto img{{transform:scale(1.05)}}
.cat{{display:none;position:absolute;left:10px;top:10px;font:700 10.5px/1 "Onest";letter-spacing:.06em;text-transform:uppercase;background:rgba(10,18,38,.8);color:#fff;padding:7px 9px;border-radius:999px}}
.eco{{position:absolute;right:10px;top:10px;font:900 13px/1 "Unbounded";background:var(--laranja);color:#fff;padding:8px 9px;border-radius:12px;box-shadow:0 8px 18px -8px rgba(255,106,19,.9)}}
.corpo{{padding:13px 13px 14px;display:flex;flex-direction:column;flex:1}}
h3{{font:700 15px/1.2 "Unbounded";letter-spacing:-.01em;margin:0 0 5px}}
.det{{margin:0 0 10px;color:var(--mudo);font-size:12.5px;line-height:1.35;flex:1}}
.preco{{display:flex;align-items:flex-start;line-height:1;color:#fff}}
.preco small{{font:700 13px/1 "Onest";margin:6px 3px 0 0;color:var(--laranja-2)}}
.preco b{{font:900 30px/1 "Unbounded";letter-spacing:-.04em}}
.preco sup{{font:800 14px/1 "Unbounded";margin-top:3px}}
.ancora{{margin:6px 0 12px;font-size:11.5px;color:var(--mudo)}}
.ancora s{{text-decoration-color:var(--laranja);text-decoration-thickness:2px}}
.pedir{{display:block;text-align:center;text-decoration:none;font:700 13.5px/1 "Onest";background:var(--laranja);color:#fff;padding:13px 10px;border-radius:14px;transition:.18s}}
.pedir:hover{{background:var(--laranja-2)}}
.pedir:focus-visible,.chip:focus-visible,.btn-topo:focus-visible,.cta:focus-visible{{outline:3px solid #fff;outline-offset:3px}}
@media (min-width:700px){{.cat{{display:block}} .corpo{{padding:16px}} h3{{font-size:17px}} .det{{font-size:13.5px}} .preco b{{font-size:36px}}}}

/* como comprar */
.passos{{margin:60px 0 0;background:linear-gradient(135deg,#ff6a13,#ff8a3d);color:#fff;border-radius:28px;padding:30px 22px;position:relative;overflow:hidden}}
.passos::after{{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent 0 11px,rgba(255,255,255,.09) 11px 12px);pointer-events:none}}
.passos h2{{color:#fff;position:relative;z-index:1}}
.passos ol{{position:relative;z-index:1;list-style:none;margin:22px 0 0;padding:0;display:grid;gap:16px;counter-reset:p}}
.passos li{{counter-increment:p;display:flex;gap:14px;align-items:flex-start}}
.passos li::before{{content:counter(p);flex:none;width:38px;height:38px;border-radius:12px;background:#0a1226;font:900 17px/38px "Unbounded";text-align:center}}
.passos b{{display:block;font:700 16px/1.25 "Unbounded";margin-bottom:3px}}
.passos p{{margin:0;font-size:14.5px;color:#fff6ee}}
.passos .cta{{position:relative;z-index:1;margin-top:24px;background:#0a1226;color:#fff}}
@media (min-width:880px){{.passos{{padding:44px}} .passos ol{{grid-template-columns:repeat(3,1fr);gap:26px}}}}

/* rodapé */
footer{{margin:48px 0 0;padding:28px 0 112px;border-top:1px solid var(--borda);color:var(--mudo);font-size:13px}}
footer .wrap{{display:grid;gap:18px}}
footer img{{width:76px;height:76px}}
footer p{{margin:0;max-width:72ch}}
@media (min-width:880px){{footer{{padding-bottom:40px}} footer .wrap{{grid-template-columns:auto 1fr;align-items:center}}}}

/* barra fixa no celular */
.fixa{{position:fixed;left:12px;right:12px;bottom:max(12px,env(safe-area-inset-bottom));z-index:50;display:flex;align-items:center;justify-content:space-between;gap:10px;background:rgba(21,35,63,.94);backdrop-filter:blur(10px);border:1px solid var(--borda);color:#fff;border-radius:18px;padding:10px 10px 10px 16px;box-shadow:0 18px 40px -16px rgba(0,0,0,.8)}}
.fixa span{{font-size:13px;line-height:1.25}}
.fixa span b{{color:var(--laranja-2)}}
.fixa a{{flex:none;text-decoration:none;font:700 13.5px/1 "Onest";background:var(--laranja);color:#fff;padding:12px 14px;border-radius:12px}}
@media (min-width:880px){{.fixa{{display:none}}}}

@media (prefers-reduced-motion:reduce){{
  *,*::before,*::after{{animation:none!important;transition:none!important}}
  h1 .risco path{{stroke-dashoffset:0}}
}}
</style>
</head>
<body>
<header class="topo">
  <div class="wrap">
    <a class="marca" href="#" aria-label="kaevy3d, início"><img src="img/logo.png" alt="kaevy3d" width="900" height="268"></a>
    <a class="btn-topo" href="{LINK_CANAL}" target="_blank" rel="noopener">Chamar no {CANAL}</a>
  </div>
</header>

<main>
<section class="palco">
  <svg class="fios" viewBox="0 0 1200 700" preserveAspectRatio="none" aria-hidden="true">
    <path class="a" d="M-50 520 C 200 420, 380 640, 640 520 S 1000 380, 1260 470"/>
    <path class="b" d="M-50 180 C 240 260, 420 80, 700 170 S 1050 300, 1260 140"/>
    <path class="c" d="M-50 640 C 260 560, 520 700, 760 610 S 1080 560, 1260 660"/>
  </svg>
  <div class="wrap">
    <div>
      <span class="pill"><i></i>Retirada em {esc(LOCAL)}</span>
      <h1>Personagens que saem da <span class="pula">impressora</span> direto pra sua <span class="risco">estante<svg viewBox="0 0 200 20" preserveAspectRatio="none" aria-hidden="true"><path d="M3 14 C 50 4, 110 18, 197 6"/></svg></span>.</h1>
      <p class="sub">Colecionáveis, peças de fé e presentes impressos em 3D por nós. Comprando direto você foge da taxa de marketplace: <b>até {max_eco}% mais barato</b> que na nossa loja da Shopee.</p>
      <div class="acoes">
        <a class="cta forte" href="#pecas">Ver as peças ↓</a>
        <a class="cta leve" href="{LINK_CANAL}" target="_blank" rel="noopener">Chamar no {CANAL}</a>
      </div>
    </div>
    <div class="colagem" aria-hidden="true">
{colagem}
    </div>
  </div>
  <div class="fita" aria-hidden="true"><div>{fita} {fita}</div></div>
</section>

<div class="wrap">
  <ul class="confia">
    <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="18" height="14" rx="3"/><circle cx="12" cy="13" r="3.5"/><path d="M8 6l1.5-2h5L16 6"/></svg>Fotos reais das peças</li>
    <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16M6 16h12M8 12h8M10 8h4"/><path d="M12 4v4"/></svg>Impresso e acabado por nós</li>
    <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12V7l-8-4-8 4v5c0 5 3.5 8 8 9 4.5-1 8-4 8-9z"/><path d="M9 12l2 2 4-4"/></svg>Mesma peça da nossa loja na Shopee</li>
    <li class="destaque"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg><span><b>Só retirada em {esc(LOCAL)}.</b> Não fazemos entrega: o preço direto não tem frete embutido.</span></li>
  </ul>

  <div class="barra" id="pecas">
    <h2>As peças</h2>
    <div class="chips" role="toolbar" aria-label="Filtrar por categoria">
      {"".join(chips)}
    </div>
  </div>

  <div class="grade">
{chr(10).join(cards)}
  </div>

  <section class="passos" aria-labelledby="como">
    <h2 id="como">Como comprar</h2>
    <ol>
      <li><div><b>Escolha a peça</b><p>Tudo aqui é foto real do que sai da nossa impressora.</p></div></li>
      <li><div><b>Chame a gente</b><p>Mande o nome da peça no {CANAL} @{esc(D['instagram'])}. Confirmamos se tem pronta ou o prazo para imprimir.</p></div></li>
      <li><div><b>Retire em {esc(LOCAL)}</b><p>Combinamos dia e horário para você retirar. Não fazemos entrega.</p></div></li>
    </ol>
    <a class="cta" href="{LINK_CANAL}" target="_blank" rel="noopener">Chamar no {CANAL}</a>
  </section>
</div>
</main>

<footer>
  <div class="wrap">
    <img src="img/selo.png" alt="" width="76" height="76" loading="lazy">
    <div>
      <p>Preços de venda direta, somente para retirada em {esc(LOCAL)} (não entregamos) · atualizados em {hoje}. A comparação usa o preço da nossa própria loja na Shopee na mesma data.</p>
      <p style="margin-top:8px">Peças impressas em 3D (PLA): as linhas de camada aparecem levemente e pode haver pequenas variações de cor. São peças decorativas e colecionáveis, não brinquedos. Produtos independentes, sem vínculo com os detentores das marcas e personagens.</p>
    </div>
  </div>
</footer>

<div class="fixa">
  <span>Retirada em {esc(LOCAL)} · <b>até {max_eco}% menos</b></span>
  <a href="{LINK_CANAL}" target="_blank" rel="noopener">{CANAL}</a>
</div>

<script>
const chips=[...document.querySelectorAll('.chip')], cards=[...document.querySelectorAll('.card')];
chips.forEach(c=>c.addEventListener('click',()=>{{
  chips.forEach(x=>{{x.classList.toggle('is-on',x===c);x.setAttribute('aria-pressed',x===c)}});
  const f=c.dataset.f; cards.forEach(k=>k.hidden=!(f==='todos'||k.dataset.cat===f));
}}));
</script>
</body>
</html>
'''
(AQUI / "index.html").write_text(PAGE, encoding="utf-8")
for i in itens:
    print(f"{i['nome']:24s} {brl(i['preco']):>10s} | Shopee {brl(i['shopee']):>10s} | −{i['eco']}%")
print("index.html gerado.")
