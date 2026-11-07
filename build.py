#!/usr/bin/env python3
"""Gerador do site Kaevy3D (GitHub Pages, subdiretório /kaevy3d-catalogo/).

Lê SÓ arquivos do repositório:
  config.json    -> configuração comercial (Instagram, WhatsApp, retirada, modo de compra, GA4...)
  produtos.json  -> fonte única dos produtos (preço, textos, galeria, categoria)
  assets/        -> site.css e site.js (escritos à mão, não são gerados)

Gera: index.html, produto/<id>/index.html, politicas/*/index.html, 404.html, sitemap.xml, robots.txt

Uso:  python3 build.py            (valida os dados e regenera tudo)
      python3 build.py --checar   (só valida, não escreve)
"""
import hashlib
import html
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CFG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
DADOS = json.loads((RAIZ / "produtos.json").read_text(encoding="utf-8"))
CATS = DADOS["categorias"]
HOJE = date.today().strftime("%d/%m/%Y")
BASE_URL = CFG["base_url"].rstrip("/") + "/"
LOCAL = CFG["local_retirada"]
IG = f"https://www.instagram.com/{CFG['instagram']}/"
WHATS = "".join(ch for ch in CFG.get("whatsapp", "") if ch.isdigit())
esc = html.escape
VER = {n: hashlib.md5((RAIZ / "assets" / n).read_bytes()).hexdigest()[:8] for n in ("site.css", "site.js")}


# ---------------------------------------------------------------- dados e validação
def preco_de(p):
    if p.get("preco_manual"):
        return round(float(p["preco_manual"]), 2)
    # integração opcional e local com o banco de custos do squad (não usada na vitrine pública)
    try:
        sq = Path(DADOS.get("catalogo_squad", ""))
        sys.path.insert(0, str(sq / "tools"))
        import margin_dashboard as m  # noqa
        c = json.loads((sq / "pipeline/data/produtos-catalogo.json").read_text(encoding="utf-8"))["produtos"][p["id"]]
        return m.preco_site("Facebook", m.unit_cost({"gramas": c["gramas"], "horas": c["horas"]}))
    except Exception as e:
        raise SystemExit(f"ERRO: {p['id']} sem preco_manual e o banco do squad não está disponível ({e}).")


erros = []
OBRIG = ["id", "nome", "titulo", "categoria", "galeria", "headline", "descricao", "caracteristicas", "seo_description"]
PRODS = []
for p in sorted(DADOS["produtos"], key=lambda x: x.get("ordem", 99)):
    if not p.get("ativo", True):
        continue
    for k in OBRIG:
        if not p.get(k):
            erros.append(f"{p.get('id', '?')}: campo obrigatório vazio: {k}")
    if p.get("categoria") not in CATS:
        erros.append(f"{p['id']}: categoria inexistente {p.get('categoria')}")
    for g in p.get("galeria", []):
        for suf in (".jpg", ".webp", "-600.jpg", "-600.webp"):
            if not (RAIZ / (g["src"] + suf)).exists():
                erros.append(f"{p['id']}: imagem não encontrada {g['src']}{suf}")
    p = dict(p)
    p["preco"] = preco_de(p)
    sh = p.get("shopee")
    p["eco"] = round((sh - p["preco"]) / sh * 100) if (CFG.get("comparacao_shopee") and sh and sh > p["preco"]) else 0
    p["eco_rs"] = round(sh - p["preco"], 2) if p["eco"] else 0
    PRODS.append(p)
if len({p["id"] for p in PRODS}) != len(PRODS):
    erros.append("ids duplicados")
if erros:
    raise SystemExit("Dados inválidos:\n  " + "\n  ".join(erros))
POR_ID = {p["id"]: p for p in PRODS}
MAX_ECO = max((p["eco"] for p in PRODS), default=0)
if "--checar" in sys.argv:
    print(f"OK: {len(PRODS)} produtos válidos.")
    sys.exit(0)


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- peças de HTML
ICON = {
    "foto": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="18" height="14" rx="3"/><circle cx="12" cy="13" r="3.5"/><path d="M8 6l1.5-2h5L16 6"/></svg>',
    "camadas": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/></svg>',
    "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    "info": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
    "sacola": '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 7h12l-1 13H7L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    "lupa": '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5M11 8v6M8 11h6"/></svg>',
}


def pic(pre, base, alt, sizes, w=1200, h=1200, eager=False):
    """<picture> com WebP + JPG em 600 e 1200 px. `base` = caminho sem extensão."""
    b = pre + base
    carga = 'fetchpriority="high" decoding="async"' if eager else 'loading="lazy" decoding="async"'
    return (f'<picture><source type="image/webp" srcset="{b}-600.webp 600w, {b}.webp 1200w" sizes="{sizes}">'
            f'<img src="{b}-600.jpg" srcset="{b}-600.jpg 600w, {b}.jpg 1200w" sizes="{sizes}" alt="{esc(alt)}" width="{w}" height="{h}" {carga}>'
            f'</picture>')


def dados_json(pre):
    cfg = {"instagram": CFG["instagram"], "whatsapp": WHATS, "local": LOCAL, "ga4": CFG.get("ga4_id", "")}
    cat = [{"id": p["id"], "nome": p["nome"], "preco": p["preco"], "categoria": p["categoria"],
            "thumb": pre + p["galeria"][0]["src"] + "-600"} for p in PRODS]
    j = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/json" id="cfg">{j(cfg)}</script>\n<script type="application/json" id="catalogo">{j(cat)}</script>'


def head(pre, titulo, desc, url, og_img, ld=None):
    ga = ""
    if CFG.get("ga4_id"):
        g = esc(CFG["ga4_id"])
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>'
              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{g}');</script>")
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    v = HOJE.replace("/", "")
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#101827">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Kaevy3D">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="{pre}img/favicon.png">
<link rel="apple-touch-icon" href="{pre}img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&family=Unbounded:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/site.css?v={VER['site.css']}">
{lds}{ga}
</head>'''


def link_cat(pre, cat, eh_home):
    return f'href="#vitrine" data-ir-cat="{cat}"' if eh_home else f'href="{pre}?cat={cat}#vitrine"'


def cabecalho(pre, eh_home=False):
    navs = "".join(f'<li><a {link_cat(pre, k, eh_home)}>{esc(v["nome"])}</a></li>' for k, v in CATS.items())
    como = "#como-comprar" if eh_home else f"{pre}#como-comprar"
    sacola = (f'<button class="sacola-btn" type="button" aria-label="Abrir sacola">{ICON["sacola"]}<span class="n"></span></button>'
              if WHATS else "")
    contato = (f'<a class="btn btn-pri contato" href="https://wa.me/{WHATS}" target="_blank" rel="noopener" data-contato="whatsapp" data-local="cabecalho">WhatsApp</a>'
               if WHATS else f'<a class="btn btn-sec contato" href="{IG}" target="_blank" rel="noopener" data-contato="instagram" data-local="cabecalho">@{esc(CFG["instagram"])}</a>')
    return f'''<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="cab">
  <div class="wrap in">
    <a class="logo" href="{pre or './'}" aria-label="Kaevy3D, página inicial"><img src="{pre}img/logo.png" alt="Kaevy3D" width="900" height="268"></a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu-principal" aria-label="Abrir menu">{ICON["menu"]}</button>
    <nav id="menu-principal" aria-label="Principal"><ul>{navs}<li><a href="{como}">Como funciona</a></li></ul></nav>
    <div class="acoes-cab">{sacola}{contato}</div>
  </div>
</header>'''


def rodape(pre, eh_home=False):
    navs = "".join(f'<li><a {link_cat(pre, k, eh_home)}>{esc(v["nome"])}</a></li>' for k, v in CATS.items())
    todos = 'href="#vitrine" data-ir-cat="todos"' if eh_home else f'href="{pre}#vitrine"'
    whats = f'<li><a href="https://wa.me/{WHATS}" target="_blank" rel="noopener" data-contato="whatsapp" data-local="rodape">WhatsApp</a></li>' if WHATS else ""
    pag = ", ".join(CFG.get("pagamentos_confirmados") or [])
    pag_li = f'<li>Pagamento: {esc(pag)}</li>' if pag else ""
    return f'''<footer class="rod">
  <div class="wrap">
    <div class="grid">
      <div><a class="marca-rod" href="{pre or './'}" aria-label="Kaevy3D, página inicial"><img src="{pre}img/logo.png" alt="Kaevy3D" width="900" height="268" loading="lazy"></a>
        <p>Peças criativas em 3D para colecionar, decorar e presentear.</p></div>
      <div><h3>Navegação</h3><ul><li><a {todos}>Todos os produtos</a></li>{navs}<li><a href="{pre or './'}#como-comprar">Como comprar</a></li></ul></div>
      <div><h3>Atendimento</h3><ul><li><a href="{IG}" target="_blank" rel="noopener" data-contato="instagram" data-local="rodape">Instagram @{esc(CFG["instagram"])}</a></li>{whats}<li>{esc(LOCAL)} · somente retirada</li>{pag_li}</ul></div>
      <div><h3>Informações</h3><ul><li><a href="{pre}politicas/retirada/">Política de retirada</a></li><li><a href="{pre}politicas/trocas/">Trocas e devoluções</a></li><li><a href="{pre}politicas/privacidade/">Privacidade</a></li></ul></div>
    </div>
    <div class="legal">
      <span>Peças decorativas produzidas por impressão 3D em PLA. Pequenas linhas de camada e variações de acabamento são características possíveis desse processo. Não são brinquedos.</span>
      <span>Produtos independentes, sem vínculo com os detentores das marcas e personagens representados.</span>
      <span>© {date.today().year} Kaevy3D · {esc(LOCAL)}</span>
    </div>
  </div>
</footer>'''


def sacola_html():
    if not WHATS:
        return ""
    return f'''<div class="veu" hidden></div>
<aside class="sacola" aria-label="Sacola" aria-live="polite">
  <header><b style="font-size:18px">Sua sacola</b><button type="button" class="btn btn-sec fechar-sacola" style="min-height:40px">Fechar</button></header>
  <div class="itens"></div>
  <footer><div class="total" style="margin:0;border:0;padding:0"><span>Total estimado</span><b data-sacola-total>R$ 0,00</b></div>
    <p class="mudo" style="margin:0;font-size:14px">Retirada em {esc(LOCAL)}, sem entrega. Disponibilidade e pagamento confirmados na conversa.</p>
    <a class="btn btn-pri btn-bloco" data-sacola-enviar data-contato="whatsapp" href="#" target="_blank" rel="noopener">Enviar pedido pelo WhatsApp</a></footer>
</aside>'''


def pagina(pre, titulo, desc, url, og, corpo, eh_home=False, ld=None, extra_json=""):
    v = HOJE.replace("/", "")
    return f'''{head(pre, titulo, desc, url, og, ld)}
<body>
{cabecalho(pre, eh_home)}
<main id="conteudo">
{corpo}
</main>
{rodape(pre, eh_home)}
{sacola_html()}
{dados_json(pre)}
{extra_json}
<script src="{pre}assets/site.js?v={VER['site.js']}" defer></script>
</body>
</html>
'''


def card(p, pre):
    g = p["galeria"][0]
    url = f"{pre}produto/{p['id']}/"
    sel_eco = f'<span class="selo">Economize {p["eco"]}%</span>' if p["eco"] else ""
    sel_extra = "".join(f'<span class="selo neutro">{esc(s)}</span>' for s in p.get("selos", [])[:1])
    de = f'<span class="de">Shopee <s>{brl(p["shopee"])}</s></span>' if p["eco"] else ""
    return f'''<article class="card" data-cat="{p["categoria"]}">
  <a class="ft" href="{url}" data-select="{p["id"]}" tabindex="-1" aria-hidden="true">{pic(pre, g["src"], g["alt"], "(min-width:1100px) 280px, (min-width:760px) 30vw, 48vw")}{sel_eco}{sel_extra}</a>
  <div class="cp">
    <span class="cat-n">{esc(CATS[p["categoria"]]["nome"])}</span>
    <h3><a href="{url}" data-select="{p["id"]}">{esc(p["nome"])}</a></h3>
    <p class="fr">{esc(p.get("resumo") or p["headline"])}</p>
    <div class="preco"><span class="v">{brl(p["preco"])}</span>{de}</div>
    <a class="btn btn-sec" href="{url}" data-select="{p["id"]}" aria-label="Ver detalhes de {esc(p["nome"])}">Ver detalhes</a>
  </div>
</article>'''


# ---------------------------------------------------------------- home
def home():
    pre = ""
    goku = POR_ID.get("goku-ssj4", PRODS[0])
    hero_img = goku["galeria"][0]
    arg = (f'<p class="arg">Compre direto de quem produz e <b>economize até {MAX_ECO}%</b> em comparação com os preços da nossa loja na Shopee.</p>'
           if MAX_ECO else "")
    benef = [("foto", "Fotos reais", "Veja as peças que produzimos."),
             ("camadas", "Produção própria", "Peças impressas e finalizadas pela Kaevy3D."),
             ("tag", "Preço direto", "Economize em comparação com a nossa loja na Shopee." if MAX_ECO else "Compre direto de quem produz."),
             ("pin", f"Retirada em {LOCAL}", "Combine a retirada após a confirmação do pedido.")]
    benef_html = "".join(f'<li>{ICON[i]}<div><b>{esc(t)}</b><span>{esc(s)}</span></div></li>' for i, t, s in benef)
    cats_html = "".join(f'''<a class="cat-card" {link_cat(pre, k, True)}>{pic(pre, c["imagem"], "", "(min-width:760px) 33vw, 100vw")}
      <div class="c"><small>{esc(c["nome"])}</small><h3>{esc(c["titulo"])}</h3><p>{esc(c["texto"])}</p><span class="ir">{esc(c["botao"])}</span></div></a>'''
                        for k, c in CATS.items())
    dest = [p for p in PRODS if p.get("destaque")][:4]
    dest_html = "".join(card(p, pre) for p in dest)
    cont = {k: sum(p["categoria"] == k for p in PRODS) for k in CATS}
    chips = f'<button class="chip" type="button" data-filtro="todos" aria-pressed="true">Todos<span>{len(PRODS)}</span></button>' + "".join(
        f'<button class="chip" type="button" data-filtro="{k}" aria-pressed="false">{esc(v["nome"])}<span>{cont[k]}</span></button>' for k, v in CATS.items() if cont[k])
    vit_html = "".join(card(p, pre) for p in PRODS)

    cmp_html = ""
    if goku["eco"]:
        cmp_html = f'''<section class="sec" aria-labelledby="t-compara" style="background:var(--branco)">
  <div class="wrap compara">
    <div class="sec-cab" style="margin:0">
      <span class="olho">Compra direta</span>
      <h2 id="t-compara">A mesma peça. Um preço melhor na compra direta.</h2>
      <p>Você pode encontrar nossas peças na Shopee, mas aqui consulta diretamente a Kaevy3D e aproveita os preços cadastrados para retirada local.</p>
    </div>
    <div>
      <div class="cmp-box">
        <img src="{goku["galeria"][0]["src"]}-600.jpg" alt="{esc(goku["nome"])}" width="425" height="600" loading="lazy">
        <div class="cmp-linhas">
          <b style="font-size:16px">{esc(goku["titulo"])}</b>
          <div class="cmp-l shopee"><span>Na nossa loja da Shopee</span><b><s>{brl(goku["shopee"])}</s></b></div>
          <div class="cmp-l direto"><span>Direto na Kaevy3D</span><b>{brl(goku["preco"])}</b></div>
          <span class="cmp-eco">Economia de {brl(goku["eco_rs"])}</span>
        </div>
      </div>
      <p class="nota">Preços comparados em {esc(CFG["data_comparacao"])}, sujeitos a atualização. A comparação usa o preço da nossa própria loja na Shopee. A compra direta possui condições próprias e retirada combinada em {esc(LOCAL)}, sem entrega.</p>
    </div>
  </div>
</section>'''

    aval = CFG.get("avaliacoes") or []
    aval_html = ""
    if aval:
        itens = "".join(f'<blockquote><p>“{esc(a["texto"])}”</p><footer>— {esc(a["nome"])}</footer></blockquote>' for a in aval)
        aval_html = f'<section class="sec" aria-labelledby="t-aval"><div class="wrap"><div class="sec-cab"><h2 id="t-aval">Quem comprou, mostra.</h2></div><div class="aval">{itens}</div></div></section>'

    online = CFG.get("modo_compra") == "online" and CFG.get("checkout_online_url")
    if online:
        passos = [("Escolha suas peças.", "Explore os produtos e veja os detalhes antes de decidir."),
                  ("Finalize o pagamento.", "Pagamento pelo provedor oficial."),
                  ("Aguarde a confirmação.", "Confirmamos disponibilidade ou prazo de produção."),
                  (f"Combine a retirada em {LOCAL}.", "Combine o dia e horário de retirada.")]
    else:
        canal = "WhatsApp" if WHATS else f"Instagram @{CFG['instagram']}"
        passos = [("Escolha sua peça.", "Explore os produtos e veja os detalhes antes de decidir."),
                  ("Solicite seu pedido.", f"Escolha a quantidade e envie o resumo pelo {canal}."),
                  ("Confirme os detalhes.", "Nossa equipe confirma disponibilidade, prazo e pagamento."),
                  (f"Retire em {LOCAL}.", "Combine o dia e horário de retirada.")]
    passos_html = "".join(f"<li><b>{esc(t)}</b><p>{esc(s)}</p></li>" for t, s in passos)

    pag = CFG.get("pagamentos_confirmados") or []
    resp_pag = (f"Aceitamos: {', '.join(pag)}. As condições são confirmadas durante o atendimento, antes da finalização do pedido."
                if pag else "As condições de pagamento são confirmadas durante o atendimento, antes da finalização do pedido.")
    end = CFG.get("endereco_retirada_publico")
    resp_ret = (f"A retirada é feita em {end}. Dia e horário são combinados após o alinhamento do pedido." if end else
                f"A retirada é combinada em {LOCAL}. As informações do local, dia e horário são confirmadas após o alinhamento do pedido.")
    faq = [("Vocês fazem entrega?", f"No momento, trabalhamos somente com retirada combinada em {LOCAL}. Não realizamos entregas."),
           ("Os produtos são feitos de qual material?", "As peças são produzidas em impressão 3D utilizando PLA. Esse processo pode deixar linhas de camada discretamente visíveis, além de pequenas variações de acabamento e cor."),
           ("As peças são brinquedos?", "Não. Os produtos do catálogo são destinados a uso decorativo e colecionável. Não devem ser apresentados como brinquedos, especialmente para crianças pequenas."),
           ("Posso escolher a cor?", "Alguns produtos podem ter opções de cor. Consulte as alternativas disponíveis na página de cada peça ou confirme com a Kaevy3D antes de fazer o pedido."),
           ("Como sei se o produto está disponível?", "A disponibilidade pode variar conforme a peça. Antes da confirmação do pedido, informamos se ela está pronta ou qual é o prazo previsto de produção."),
           ("Por que o preço aqui é diferente da Shopee?", "Aqui você consulta a compra diretamente com a Kaevy3D, em condições específicas de retirada local. Os valores podem ser diferentes dos oferecidos no marketplace."),
           ("Como funciona o pagamento?", resp_pag),
           ("Posso encomendar um produto que não está disponível?", "Consulte a Kaevy3D para verificar se a peça pode ser produzida e qual seria o prazo."),
           ("Onde faço a retirada?", resp_ret)]
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)

    final_img = POR_ID.get("muttley-15cm", PRODS[0])["galeria"][0]
    prod_fotos = [("harry-potter-croche", 4, "Detalhes de perto", "Texturas, formatos e acabamentos que você pode conhecer antes de comprar."),
                  ("presepio-minimalista", 5, "Tamanho de verdade", "Fotos com a peça na mão para você ter noção da escala."),
                  ("muttley-15cm", 1, "Pronta para ganhar um novo lugar", "A peça finalizada, do jeito que você vai receber.")]
    prod_html = "".join(f'<figure>{pic(pre, POR_ID[i]["galeria"][n]["src"], POR_ID[i]["galeria"][n]["alt"], "(min-width:760px) 33vw, 100vw")}<figcaption><b>{esc(t)}</b><span>{esc(s)}</span></figcaption></figure>'
                        for i, n, t, s in prod_fotos if i in POR_ID and len(POR_ID[i]["galeria"]) > n)

    corpo = f'''<section class="hero escuro" aria-labelledby="t-hero">
  <div class="wrap">
    <div class="texto">
      <div class="t1">
        <span class="olho surge">Colecionáveis, decoração e presentes criativos</span>
        <h1 id="t-hero" class="surge d1">Sua paixão merece um <mark>lugar de destaque</mark>.</h1>
        <p class="sub surge d2">Do personagem que marcou sua infância ao presente que surpreende: descubra peças feitas em 3D para colecionar, decorar e dar de presente.</p>
      </div>
      <div class="t2">
        {arg}
        <div class="cta-linha"><a class="btn btn-pri" href="#vitrine" data-ir-cat="todos">Explorar as peças</a></div>
        <p class="apoio">Produção própria • Fotos reais • Retirada combinada em {esc(LOCAL)}</p>
      </div>
    </div>
    <figure class="hero-foto surge d2">
      {pic(pre, hero_img["src"], hero_img["alt"], "(min-width:900px) 520px, 90vw", 850, 1200, eager=True)}
      <figcaption><a href="produto/{goku["id"]}/" style="color:inherit;text-decoration:none" data-select="{goku["id"]}">{esc(goku["nome"])} · <b>{brl(goku["preco"])}</b></a></figcaption>
    </figure>
  </div>
</section>

<section class="benef" aria-label="Benefícios"><div class="wrap"><ul>{benef_html}</ul></div></section>

<section class="sec" aria-labelledby="t-cats">
  <div class="wrap">
    <div class="sec-cab"><h2 id="t-cats">Encontre algo que combine com você.</h2><p>Seja para sua coleção, sua casa ou para presentear alguém, existe uma peça esperando pelo lugar certo.</p></div>
    <div class="cats">{cats_html}</div>
  </div>
</section>

<section class="sec" style="padding-top:0" aria-labelledby="t-dest">
  <div class="wrap">
    <div class="sec-cab"><h2 id="t-dest">Peças que merecem sua atenção.</h2><p>Alguns dos nossos colecionáveis, objetos criativos e detalhes para deixar seu espaço com mais personalidade.</p></div>
    <div class="grade">{dest_html}</div>
    <div class="ver-todas"><a class="btn btn-sec" href="#vitrine" data-ir-cat="todos">Ver todas as peças</a></div>
  </div>
</section>

<section class="sec" id="vitrine" aria-labelledby="t-vit" style="background:#EFEAE1">
  <div class="wrap">
    <div class="sec-cab"><h2 id="t-vit">Todas as peças</h2><p>Filtre por categoria e abra cada peça para ver fotos, medidas e como pedir.</p></div>
    <div class="filtros" role="group" aria-label="Filtrar por categoria">{chips}</div>
    <p id="vitrine-status" class="sr" aria-live="polite"></p>
    <div class="grade">{vit_html}</div>
    <p id="vitrine-vazio" class="vazio" hidden>Nenhuma peça nesta categoria no momento. <a href="#vitrine" data-ir-cat="todos">Ver todas</a></p>
  </div>
</section>

<section class="sec escuro" aria-labelledby="t-prod">
  <div class="wrap">
    <div class="sec-cab"><span class="olho">Fotos reais</span><h2 id="t-prod">Da nossa impressora para o seu cantinho favorito.</h2>
      <p>Por trás de cada peça existe um processo de produção em 3D. Da impressão ao acabamento, buscamos transformar cada modelo em um objeto que você tenha prazer em colocar na sua coleção, usar na decoração ou escolher como presente.</p></div>
    <div class="prod-grade">{prod_html}</div>
  </div>
</section>

{cmp_html}
{aval_html}

<section class="sec" id="como-comprar" aria-labelledby="t-como">
  <div class="wrap">
    <div class="sec-cab"><h2 id="t-como">Gostou de uma peça? É simples.</h2></div>
    <ol class="passos">{passos_html}</ol>
    <div class="retirada-aviso">{ICON["pin"]}<span><b>Somente retirada em {esc(LOCAL)}.</b> Não fazemos entrega. Local, dia e horário são combinados depois da confirmação do pedido. <a href="politicas/retirada/">Ver política de retirada</a></span></div>
  </div>
</section>

<section class="sec" style="padding-top:0" aria-labelledby="t-faq">
  <div class="wrap">
    <div class="sec-cab"><h2 id="t-faq">Perguntas frequentes</h2></div>
    <div class="faq">{faq_html}</div>
  </div>
</section>

<section class="sec escuro final" aria-labelledby="t-final">
  <div class="wrap">
    <div>
      <h2 id="t-final">O próximo destaque da sua estante pode estar aqui.</h2>
      <p>Encontre uma peça que combina com seu universo, escolha seus favoritos e descubra os detalhes antes de comprar.</p>
      <a class="btn btn-pri" href="#vitrine" data-ir-cat="todos">Explorar todas as peças</a>
      <small>Compra direta com retirada combinada em {esc(LOCAL)}.</small>
    </div>
    {pic(pre, final_img["src"], final_img["alt"], "(min-width:900px) 45vw, 100vw")}
  </div>
</section>'''
    ld = [{"@context": "https://schema.org", "@type": "Organization", "name": "Kaevy3D", "url": BASE_URL,
           "logo": BASE_URL + "img/logo.png", "sameAs": [IG]},
          {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": f"{BASE_URL}produto/{p['id']}/", "name": p["nome"]} for i, p in enumerate(PRODS)]}]
    return pagina(pre, "Kaevy3D | Colecionáveis, Decoração e Presentes em 3D",
                  f"Descubra colecionáveis, peças de decoração e presentes criativos produzidos em 3D. Compre direto da Kaevy3D e combine a retirada em {LOCAL}.",
                  BASE_URL, BASE_URL + "img/og.jpg", corpo, eh_home=True, ld=ld)


# ---------------------------------------------------------------- produto
DISP = {"pronta": "Pronta entrega.", "encomenda": "Produção sob encomenda.", "indisponivel": "Indisponível no momento.",
        "a_confirmar": "Consulte a disponibilidade antes de concluir o pedido."}


def produto(p):
    pre = "../../"
    url = f"{BASE_URL}produto/{p['id']}/"
    gal = p["galeria"]
    retrato = lambda g: "goku-ssj4" in g["src"]
    slides = "".join(f'''<figure class="slide{' retrato' if retrato(g) else ''}" data-full="{pre}{g["src"]}" data-alt="{esc(g["alt"])}">
        <button type="button" aria-label="Ampliar foto {i + 1} de {len(gal)}">{pic(pre, g["src"], g["alt"], "(min-width:900px) 52vw, 100vw", 850 if retrato(g) else 1200, 1200, eager=(i == 0))}</button>
        <span class="lupa">{ICON["lupa"]}</span></figure>''' for i, g in enumerate(gal))
    minis = "".join(f'<button type="button" aria-label="Ver foto {i + 1}" aria-current="{"true" if i == 0 else "false"}"><img src="{pre}{g["src"]}-600.jpg" alt="" width="72" height="72" loading="lazy"></button>' for i, g in enumerate(gal)) if len(gal) > 1 else ""
    pontos = "".join(f'<i class="{"on" if i == 0 else ""}"></i>' for i in range(len(gal))) if len(gal) > 1 else ""
    eco = (f'<p class="eco-linha">Na nossa loja da Shopee: <s>{brl(p["shopee"])}</s> · <b>economize {brl(p["eco_rs"])} ({p["eco"]}%)</b></p>' if p["eco"] else "")
    opcoes = ""
    for v in p.get("variacoes") or []:
        ops = "".join(f'<option>{esc(o)}</option>' for o in v.get("opcoes", []))
        if ops:
            opcoes += f'<div class="obs"><label for="opcao">{esc(v.get("nome", "Opção"))}</label><select id="opcao" class="btn btn-sec" style="width:100%">{ops}</select></div>'
    disp_k = p.get("disponibilidade", "a_confirmar")
    indisp = disp_k == "indisponivel"
    if WHATS:
        dis_a = ' aria-disabled="true"' if indisp else ""
        dis_b = " disabled" if indisp else ""
        cta = (f'<a id="pedido-cta" class="btn btn-pri btn-bloco" data-pedir-whats data-contato="whatsapp" data-local="produto" href="https://wa.me/{WHATS}" target="_blank" rel="noopener"{dis_a}>Pedir pelo WhatsApp</a>'
               f'<button class="btn btn-sec btn-bloco" type="button" data-add-sacola{dis_b}>Adicionar à sacola</button>')
        barra_btn = f'<a class="btn btn-pri" data-pedir-whats data-contato="whatsapp" data-local="barra" href="https://wa.me/{WHATS}" target="_blank" rel="noopener">Consultar disponibilidade</a>'
        ajuda = "A mensagem já vai com o produto, a quantidade e o valor. A equipe confirma disponibilidade, prazo e pagamento."
    else:
        cta = (f'<a id="pedido-cta" class="btn btn-pri btn-bloco" data-pedir-insta data-contato="instagram" data-local="produto" href="{IG}" target="_blank" rel="noopener">Copiar resumo e consultar no Instagram</a>'
               f'<button class="btn btn-sec btn-bloco" type="button" data-copiar>Só copiar o resumo</button>')
        barra_btn = f'<a class="btn btn-pri" data-pedir-insta data-contato="instagram" data-local="barra" href="{IG}" target="_blank" rel="noopener">Consultar disponibilidade</a>'
        ajuda = f"Copie o resumo do produto e envie para @{CFG['instagram']} para confirmar o pedido. Nada é cobrado aqui."
    feats = "".join(f"<li>{esc(c)}</li>" for c in p["caracteristicas"])
    rel = [q for q in PRODS if q["id"] != p["id"] and q["categoria"] == p["categoria"]]
    rel += [q for q in PRODS if q["id"] != p["id"] and q not in rel]
    rel_html = "".join(card(q, pre) for q in rel[:3])
    prazo = (" Prazo: " + esc(p["prazo"])) if p.get("prazo") else ""
    corpo = f'''<div class="wrap">
  <nav class="migalha" aria-label="Você está em"><a href="{pre}">Início</a> › <a href="{pre}?cat={p["categoria"]}#vitrine">{esc(CATS[p["categoria"]]["nome"])}</a> › <span aria-current="page">{esc(p["nome"])}</span></nav>
  <div class="pp">
    <div class="gal" aria-label="Fotos do produto">
      <div class="trilho">{slides}</div>
      <div class="miniaturas">{minis}</div>
      <div class="pontos" aria-hidden="true">{pontos}</div>
    </div>
    <div class="info">
      <span class="cat-n">{esc(CATS[p["categoria"]]["nome"])}</span>
      <h1>{esc(p["titulo"])}</h1>
      <p class="headline">{esc(p["headline"])}</p>
      <div class="preco" aria-label="Preço {brl(p['preco'])}"><span class="v">{brl(p["preco"])}</span></div>
      {eco}
      <div class="caixa">
        {opcoes}
        <div class="linha-qtd"><label for="qtd">Quantidade</label>
          <div class="qtd"><button type="button" data-qtd="-1" aria-label="Diminuir quantidade">−</button><input id="qtd" type="number" inputmode="numeric" min="1" max="20" value="1"><button type="button" data-qtd="1" aria-label="Aumentar quantidade">+</button></div></div>
        <div class="total"><span>Valor estimado</span><b data-total aria-live="polite">{brl(p["preco"])}</b></div>
        <div class="obs"><label for="obs">Observação (opcional)</label><textarea id="obs" maxlength="300" placeholder="Ex.: é para presente, prefiro retirar à noite..."></textarea></div>
        <p class="disp">{ICON["info"]}<span>{esc(DISP.get(disp_k, DISP["a_confirmar"]))}{prazo}</span></p>
        <div class="pedido">{cta}
          <p class="ajuda">{esc(ajuda)}</p>
          <p class="status" id="pedido-status" role="status" aria-live="polite"></p>
          <details class="resumo"><summary>Ver o resumo do pedido</summary><pre class="resumo-pre" id="resumo-texto"></pre></details>
        </div>
        <div class="retirada-mini">{ICON["pin"]}<span><b>Somente retirada em {esc(LOCAL)}.</b> Não fazemos entrega. <a href="{pre}politicas/retirada/">Como funciona</a></span></div>
      </div>
      <div class="desc">
        <h2>Sobre a peça</h2>
        <p>{esc(p["descricao"])}</p>
        <h2>Características</h2>
        <ul>{feats}</ul>
        <p class="aviso-pla">Peça decorativa produzida por impressão 3D em PLA: linhas de camada discretas e pequenas variações de acabamento e cor podem aparecer. Não é brinquedo.</p>
      </div>
    </div>
  </div>
</div>
<section class="relac" aria-labelledby="t-rel"><div class="wrap"><div class="sec-cab"><h2 id="t-rel">Você também pode gostar</h2></div><div class="grade">{rel_html}</div></div></section>
<dialog class="zoom" aria-label="Foto ampliada">
  <picture><source type="image/webp"><img alt=""></picture>
  <div class="ctl"><button type="button" class="ant" aria-label="Foto anterior">‹ Anterior</button><span class="cont"></span><button type="button" class="prox" aria-label="Próxima foto">Próxima ›</button><button type="button" class="fechar">Fechar</button></div>
</dialog>
<div class="barra-compra"><span><span class="mudo" style="display:block;font-size:12px">{esc(p["nome"])}</span><span class="v" data-total>{brl(p["preco"])}</span></span>{barra_btn}</div>'''
    img_abs = BASE_URL + gal[0]["src"] + ".jpg"
    ld = [{"@context": "https://schema.org", "@type": "Product", "name": p["nome"], "description": p["descricao"],
           "image": [BASE_URL + g["src"] + ".jpg" for g in gal], "sku": p["id"], "brand": {"@type": "Brand", "name": "Kaevy3D"},
           "material": "PLA", "category": CATS[p["categoria"]]["nome"],
           "offers": {"@type": "Offer", "price": f'{p["preco"]:.2f}', "priceCurrency": "BRL", "url": url,
                      "itemCondition": "https://schema.org/NewCondition", "seller": {"@type": "Organization", "name": "Kaevy3D"}}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Início", "item": BASE_URL},
              {"@type": "ListItem", "position": 2, "name": CATS[p["categoria"]]["nome"], "item": f"{BASE_URL}?cat={p['categoria']}"},
              {"@type": "ListItem", "position": 3, "name": p["nome"], "item": url}]}]
    extra = f'<script type="application/json" id="produto">{json.dumps({"id": p["id"]})}</script>'
    return pagina(pre, f"{p['titulo']} | {brl(p['preco'])} | Kaevy3D", p["seo_description"], url, img_abs, corpo, ld=ld, extra_json=extra)


# ---------------------------------------------------------------- políticas
def politica(slug, titulo, desc, secoes):
    pre = "../../"
    blocos = "".join(f"<h2>{esc(h)}</h2>" + "".join(f"<p>{t}</p>" for t in ps) for h, ps in secoes)
    corpo = f'''<div class="wrap"><article class="doc">
  <nav class="migalha" aria-label="Você está em"><a href="{pre}">Início</a> › <span aria-current="page">{esc(titulo)}</span></nav>
  <h1>{esc(titulo)}</h1>
  {blocos}
  <p class="atualizado">Última revisão desta página: {HOJE}.</p>
</article></div>'''
    return pagina(pre, f"{titulo} | Kaevy3D", desc, f"{BASE_URL}politicas/{slug}/", BASE_URL + "img/og.jpg", corpo)


IGL = f'<a href="{IG}" target="_blank" rel="noopener">@{esc(CFG["instagram"])}</a>'
ANALISE = (" Usamos o Google Analytics 4 para contar visitas e cliques de forma estatística." if CFG.get("ga4_id")
           else " No momento, não usamos ferramentas de análise de tráfego nem cookies de rastreamento.")
POLITICAS = {
    "retirada": ("Política de retirada", f"Como funciona a retirada dos pedidos da Kaevy3D em {LOCAL}.", [
        ("Somente retirada", [f"Trabalhamos apenas com retirada combinada em {esc(LOCAL)}. No momento não fazemos entregas nem envios nas compras diretas."]),
        ("Como combinar", [f"Depois que você envia o pedido pelo nosso canal de atendimento ({IGL}), confirmamos a disponibilidade da peça, o prazo (se ela precisar ser produzida), a forma de pagamento e o local, dia e horário da retirada."]),
        ("Na retirada", ["Confira a peça no momento da retirada. Se notar qualquer problema, avise na hora para resolvermos."]),
    ]),
    "trocas": ("Trocas e devoluções", "Direitos de troca e devolução nas compras diretas da Kaevy3D.", [
        ("Seus direitos", ["Esta política segue o Código de Defesa do Consumidor (Lei 8.078/1990) e não limita nenhum direito previsto em lei."]),
        ("Produto com defeito", [f"Se a peça apresentar defeito, fale com a gente pelo {IGL}. Para produtos duráveis, o prazo legal para reclamar de vícios aparentes é de 90 dias a partir da retirada (art. 26 do CDC). Analisamos o caso e fazemos o reparo, a troca por outra peça igual ou a devolução do valor, conforme a lei."]),
        ("Arrependimento", [f"Quando o pedido é feito à distância (por mensagem, fora de um estabelecimento comercial), você pode desistir da compra em até 7 dias a contar da retirada, com devolução integral do valor pago (art. 49 do CDC). A peça deve ser devolvida em {esc(LOCAL)}, em local e horário combinados."]),
        ("Características do processo", ["Linhas de camada discretas e pequenas variações de cor são características da impressão 3D e estão descritas em cada produto. Isso não afasta seu direito de reclamar de qualquer defeito real."]),
    ]),
    "privacidade": ("Privacidade", "Como a Kaevy3D trata dados neste site.", [
        ("O que este site coleta", ["Este site não tem cadastro, formulários de envio nem cobrança. Não pedimos seus dados aqui." + ANALISE]),
        ("Dados no seu navegador", ["A quantidade, a observação e, quando ativa, a sacola ficam salvas apenas no seu próprio navegador e não são enviadas para nós. Você pode apagá-las limpando os dados do site."]),
        ("Ao falar com a gente", [f"Quando você clica para falar no Instagram ou no WhatsApp, a conversa acontece nesses serviços, que têm políticas próprias. Usamos os dados da conversa só para atender seu pedido, conforme a Lei Geral de Proteção de Dados (Lei 13.709/2018). Para pedir informações ou exclusão, fale com {IGL}."]),
        ("Hospedagem", ["O site é hospedado no GitHub Pages, que pode registrar dados técnicos de acesso (como o endereço IP) por motivos de segurança, conforme a política do GitHub."]),
    ]),
}


def pagina_404():
    bp = CFG["base_path"]
    corpo = f'''<div class="wrap"><div class="doc" style="text-align:center;margin:0 auto">
  <h1>Página não encontrada</h1><p>O endereço pode ter mudado. Veja todas as peças na vitrine.</p>
  <p><a class="btn btn-pri" href="{bp}#vitrine">Ver as peças</a></p></div></div>'''
    return pagina(bp, "Página não encontrada | Kaevy3D", "Página não encontrada.", BASE_URL, BASE_URL + "img/og.jpg", corpo).replace(
        "<head>", '<head>\n<meta name="robots" content="noindex">', 1)


# ---------------------------------------------------------------- escrever
def escrever(rel, txt):
    f = RAIZ / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(txt, encoding="utf-8")


escrever("index.html", home())
for p in PRODS:
    escrever(f"produto/{p['id']}/index.html", produto(p))
for slug, (t, d, s) in POLITICAS.items():
    escrever(f"politicas/{slug}/index.html", politica(slug, t, d, s))
escrever("404.html", pagina_404())
urls = [BASE_URL] + [f"{BASE_URL}produto/{p['id']}/" for p in PRODS] + [f"{BASE_URL}politicas/{s}/" for s in POLITICAS]
escrever("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
         + "".join(f"  <url><loc>{u}</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n" for u in urls) + "</urlset>\n")
escrever("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")

modo = "WhatsApp + sacola" if WHATS else "Instagram (copiar resumo)"
print(f"Gerado: index, {len(PRODS)} produtos, {len(POLITICAS)} políticas, 404, sitemap, robots · pedido assistido via {modo}")
for p in PRODS:
    print(f"  {p['id']:22s} {brl(p['preco']):>10s}  Shopee {brl(p['shopee']):>10s}  economia {p['eco']}%")
