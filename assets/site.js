/* Kaevy3D — interações. Sem dependências. Dados vêm de <script type="application/json"> gerados pelo build.py */
(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const lerJSON = id => { try { return JSON.parse($("#" + id)?.textContent || "null"); } catch { return null; } };
  const CFG = lerJSON("cfg") || {};
  const CAT = lerJSON("catalogo") || [];
  const porId = Object.fromEntries(CAT.map(p => [p.id, p]));
  const brl = v => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const reduzir = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ===== analytics =====
     Só existe se config.json tiver um ga4_id real. O gtag só é carregado depois que o visitante aceita
     (analytics_exigir_consentimento=true, padrão). Eventos: view_item_list, view_item, select_category,
     select_item, add_to_cart, remove_from_cart, contact_click (WhatsApp/Instagram), generate_lead (início de pedido).
     NUNCA dispara "purchase": clicar no WhatsApp não é venda. "purchase" só com checkout real confirmado. */
  const CONS = "kaevy3d-consent";
  const lerCons = () => { try { return localStorage.getItem(CONS); } catch { return null; } };
  const fila = [];
  let gaPronto = false;
  const carregarGA = () => {
    if (gaPronto || !/^G-[A-Z0-9]+$/i.test(CFG.ga4 || "")) return;
    gaPronto = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date()); gtag("config", CFG.ga4);
    const sc = document.createElement("script"); sc.async = true;
    sc.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(CFG.ga4);
    document.head.appendChild(sc);
    fila.splice(0).forEach(([n, pr]) => gtag("event", n, pr));
  };
  const track = (nome, params = {}) => {
    if (!CFG.ga4 || nome === "purchase") return;
    try { if (gaPronto) window.gtag("event", nome, params); else if (fila.length < 30) fila.push([nome, params]); } catch {}
  };
  if (CFG.ga4) {
    const c = lerCons();
    if (!CFG.consentimento || c === "sim") carregarGA();
    else if (c !== "nao") {
      const b = document.createElement("div"); b.className = "consent"; b.setAttribute("role", "dialog"); b.setAttribute("aria-label", "Privacidade");
      b.innerHTML = '<p>Usamos o Google Analytics para entender, de forma estatística, como o site é usado. Você aceita? <a href="' + CFG.privacidade + '">Saiba mais</a></p><div class="bts"><button type="button" class="btn btn-sec" data-c="nao">Recusar</button><button type="button" class="btn btn-pri" data-c="sim">Aceitar</button></div>';
      b.addEventListener("click", e => { const v = e.target.closest("[data-c]")?.dataset.c; if (!v) return;
        try { localStorage.setItem(CONS, v); } catch {} b.remove(); if (v === "sim") carregarGA(); else fila.length = 0; });
      document.body.appendChild(b);
    }
  }
  const itemGA = (p, qtd = 1) => ({ item_id: p.id, item_name: p.nome, item_category: p.categoria, price: p.preco, quantity: qtd });

  /* imagens que falharem não quebram o card */
  window.addEventListener("error", e => {
    const img = e.target;
    if (img && img.tagName === "IMG" && !img.dataset.falhou) {
      img.dataset.falhou = "1";
      const caixa = img.closest("picture") || img;
      const aviso = document.createElement("span");
      aviso.className = "img-erro"; aviso.textContent = "Imagem indisponível";
      aviso.style.cssText = "position:absolute;inset:0";
      (caixa.parentElement || caixa).style.position ||= "relative";
      caixa.style.visibility = "hidden";
      caixa.parentElement?.appendChild(aviso);
    }
  }, true);

  /* cabeçalho: encolhe ao rolar + menu do celular */
  const cab = $(".cab");
  const aoRolar = () => cab && cab.classList.toggle("rolou", scrollY > 8);
  addEventListener("scroll", aoRolar, { passive: true }); aoRolar();
  const menuBtn = $(".menu-btn"), nav = $(".cab nav");
  const fecharMenu = () => { nav?.classList.remove("aberto"); menuBtn?.setAttribute("aria-expanded", "false"); };
  menuBtn?.addEventListener("click", () => {
    const abrir = !nav.classList.contains("aberto");
    nav.classList.toggle("aberto", abrir); menuBtn.setAttribute("aria-expanded", String(abrir));
  });
  nav?.addEventListener("click", e => { if (e.target.closest("a")) fecharMenu(); });
  addEventListener("keydown", e => { if (e.key === "Escape") { fecharMenu(); fecharSacola(); } });

  /* contatos e seleção de produto */
  document.addEventListener("click", e => {
    const c = e.target.closest("[data-contato]");
    if (c) track("contact_click", { canal: c.dataset.contato, local: c.dataset.local || "" });
    const s = e.target.closest("[data-select]");
    if (s && porId[s.dataset.select]) track("select_item", { items: [itemGA(porId[s.dataset.select])] });
  });

  /* vitrine: filtros por categoria (home) */
  const vitrine = $("#vitrine");
  const chips = $$("[data-filtro]");
  const cardsV = $$("#vitrine .card");
  const aplicarFiltro = (cat, rolar, imediato) => {
    if (!vitrine) return;
    let n = 0;
    cardsV.forEach(c => { const ok = cat === "todos" || c.dataset.cat === cat; c.hidden = !ok; n += ok; });
    chips.forEach(ch => ch.setAttribute("aria-pressed", String(ch.dataset.filtro === cat)));
    const vazio = $("#vitrine-vazio"); if (vazio) vazio.hidden = n > 0;
    const st = $("#vitrine-status"); if (st) st.textContent = `${n} ${n === 1 ? "peça" : "peças"} exibida${n === 1 ? "" : "s"}`;
    if (rolar) vitrine.scrollIntoView({ behavior: reduzir || imediato ? "instant" : "smooth", block: "start" });
    if (cat !== "todos") track("select_category", { categoria: cat });
  };
  chips.forEach(ch => ch.addEventListener("click", () => {
    aplicarFiltro(ch.dataset.filtro, false);
    history.replaceState(null, "", ch.dataset.filtro === "todos" ? location.pathname + "#vitrine" : `?cat=${ch.dataset.filtro}#vitrine`);
  }));
  $$("[data-ir-cat]").forEach(a => a.addEventListener("click", e => {
    if (!vitrine) return; // em outras páginas o link leva à home com ?cat=
    e.preventDefault();
    const cat = a.dataset.irCat; aplicarFiltro(cat, true);
    history.replaceState(null, "", cat === "todos" ? location.pathname + "#vitrine" : `?cat=${cat}#vitrine`);
  }));
  if (vitrine) {
    const cat = new URLSearchParams(location.search).get("cat");
    if (cat && chips.some(c => c.dataset.filtro === cat)) {
      aplicarFiltro(cat, location.hash === "#vitrine", true);
      if (location.hash === "#vitrine") {   // link vindo de outra página: garante a posição depois de carregar tudo
        history.scrollRestoration = "manual";
        addEventListener("load", () => vitrine.scrollIntoView({ behavior: "instant", block: "start" }), { once: true });
      }
    }
    track("view_item_list", { item_list_name: "vitrine", items: CAT.map(p => itemGA(p)) });
  }

  /* ===== página de produto ===== */
  const PROD = lerJSON("produto");
  if (PROD) {
    const p = porId[PROD.id];
    track("view_item", { currency: "BRL", value: p.preco, items: [itemGA(p)] });

    /* galeria */
    const trilho = $(".gal .trilho"), slides = $$(".gal .slide"), minis = $$(".gal .miniaturas button"), pontos = $$(".gal .pontos i");
    const contador = $(".gal .contador b");
    const fotos = slides.filter(s => s.dataset.full);          // o zoom navega só pelas fotos (o vídeo fica fora)
    let atual = 0;
    const marcar = i => {
      atual = i;
      minis.forEach((m, k) => m.setAttribute("aria-current", String(k === i)));
      pontos.forEach((d, k) => d.classList.toggle("on", k === i));
      if (contador) contador.textContent = i + 1;
      slides.forEach((s, k) => { const v = $("video", s); if (v && k !== i && !v.paused) v.pause(); });
    };
    const irPara = i => { trilho?.scrollTo({ left: slides[i].offsetLeft - trilho.offsetLeft, behavior: reduzir ? "instant" : "smooth" }); marcar(i); };
    minis.forEach((m, i) => m.addEventListener("click", () => irPara(i)));
    trilho?.addEventListener("scroll", () => {
      const i = Math.round(trilho.scrollLeft / trilho.clientWidth);
      if (i !== atual && slides[i]) marcar(i);
    }, { passive: true });

    /* zoom */
    const dlg = $("dialog.zoom");
    if (dlg) {
      const zImg = $("img", dlg), zSrc = $("source", dlg), zCont = $(".cont", dlg);
      let zi = 0;
      const mostrar = i => {
        zi = (i + fotos.length) % fotos.length; const s = fotos[zi];
        zSrc.srcset = s.dataset.full + ".webp"; zImg.src = s.dataset.full + ".jpg"; zImg.alt = s.dataset.alt;
        zCont.textContent = (zi + 1) + " de " + fotos.length;
      };
      fotos.forEach((s, i) => $("button", s)?.addEventListener("click", () => { mostrar(i); dlg.showModal(); }));
      $(".ant", dlg)?.addEventListener("click", () => mostrar(zi - 1));
      $(".prox", dlg)?.addEventListener("click", () => mostrar(zi + 1));
      $(".fechar", dlg)?.addEventListener("click", () => dlg.close());
      dlg.addEventListener("close", () => irPara(slides.indexOf(fotos[zi])));
      dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
      dlg.addEventListener("keydown", e => { if (e.key === "ArrowLeft") mostrar(zi - 1); if (e.key === "ArrowRight") mostrar(zi + 1); });
      if (fotos.length < 2) $$(".ant,.prox", dlg).forEach(b => b.hidden = true);
    }

    /* quantidade, total e resumo */
    const qIn = $("#qtd"), obs = $("#obs"), opc = $("#opcao");
    const qtd = () => Math.min(20, Math.max(1, parseInt(qIn?.value, 10) || 1));
    const montarResumo = () => {
      const q = qtd(), op = opc ? opc.value : "padrão, como nas fotos";
      const linhas = [
        "Olá! Quero fazer um pedido na Kaevy3D.", "",
        `Produto: ${p.nome}`, `Cor/opção: ${op}`, `Quantidade: ${q}`, `Valor estimado: ${brl(p.preco * q)}`,
      ];
      if (obs && obs.value.trim()) linhas.push(`Observação: ${obs.value.trim()}`);
      linhas.push("", `Vi no site e gostaria de confirmar a disponibilidade e combinar a retirada em ${CFG.local}.`);
      return linhas.join("\n");
    };
    const atualizar = () => {
      if (qIn) qIn.value = qtd();
      const tot = brl(p.preco * qtd());
      $$("[data-total]").forEach(el => el.textContent = tot);
      const pre = $("#resumo-texto"); if (pre) pre.textContent = montarResumo();
      if (CFG.whatsapp) $$("[data-pedir-whats]").forEach(a => a.href = `https://wa.me/${CFG.whatsapp}?text=${encodeURIComponent(montarResumo())}`);
    };
    $$("[data-qtd]").forEach(b => b.addEventListener("click", () => { qIn.value = qtd() + Number(b.dataset.qtd); atualizar(); }));
    qIn?.addEventListener("input", atualizar); qIn?.addEventListener("change", atualizar);
    obs?.addEventListener("input", atualizar); opc?.addEventListener("change", atualizar);
    atualizar();

    /* pedido assistido */
    const status = $("#pedido-status");
    const avisar = (txt, erro) => { if (status) { status.textContent = txt; status.classList.toggle("erro", !!erro); } };
    const copiar = async txt => {
      try { await navigator.clipboard.writeText(txt); return true; } catch {
        const t = document.createElement("textarea"); t.value = txt; t.setAttribute("readonly", ""); t.style.cssText = "position:fixed;opacity:0";
        document.body.appendChild(t); t.select(); let ok = false; try { ok = document.execCommand("copy"); } catch {} t.remove(); return ok;
      }
    };
    $$("[data-pedir-insta]").forEach(a => a.addEventListener("click", async () => {
      const ok = await copiar(montarResumo());
      avisar(ok ? `Resumo copiado. Cole na conversa com @${CFG.instagram} para confirmar o pedido.` : "Não consegui copiar. Abra o resumo abaixo e copie manualmente.", !ok);
      track("generate_lead", { canal: "instagram", currency: "BRL", value: p.preco * qtd(), items: [itemGA(p, qtd())] });
    }));
    $$("[data-copiar]").forEach(b => b.addEventListener("click", async () => {
      b.classList.add("carregando");
      const ok = await copiar(montarResumo()); b.classList.remove("carregando");
      avisar(ok ? "Resumo copiado." : "Não consegui copiar. Selecione o texto do resumo e copie.", !ok);
    }));
    $$("[data-pedir-whats]").forEach(a => a.addEventListener("click", () =>
      track("generate_lead", { canal: "whatsapp", currency: "BRL", value: p.preco * qtd(), items: [itemGA(p, qtd())] })));
    $$("[data-add-sacola]").forEach(b => b.addEventListener("click", () => {
      addSacola(p.id, qtd(), obs?.value.trim() || "", opc ? opc.value : "");
      avisar("Adicionado à sacola."); abrirSacola();
    }));

    /* barra fixa contextual (celular) */
    const barra = $(".barra-compra"), alvo = $("#pedido-cta");
    if (barra && alvo) {
      document.body.classList.add("tem-barra");
      const rodape = $(".rod");
      const gal = $(".gal");
      const conferir = () => {
        const r = alvo.getBoundingClientRect(), h = innerHeight;
        const ctaFora = r.bottom < 0 || r.top > h;                                  // botão principal fora da área visível
        const g = gal?.getBoundingClientRect();
        const cobreGaleria = g && g.bottom > h - 90 && g.top < h;                   // não cobre pontos/controles da galeria
        const noRodape = rodape && rodape.getBoundingClientRect().top < h - 40;      // não cobre o rodapé
        const sacolaAberta = document.querySelector(".sacola.aberta");
        const vis = ctaFora && !cobreGaleria && !noRodape && !sacolaAberta;
        barra.classList.toggle("vis", vis); barra.setAttribute("aria-hidden", String(!vis));
      };
      addEventListener("scroll", conferir, { passive: true }); addEventListener("resize", conferir); conferir();
    }
  }

  /* ===== sacola (só existe no HTML quando há WhatsApp configurado) ===== */
  const CHAVE = "kaevy3d-sacola";
  const sacolaEl = $(".sacola"), veu = $(".veu");
  const ler = () => { try { return (JSON.parse(localStorage.getItem(CHAVE)) || []).filter(i => porId[i.id]); } catch { return []; } };
  const gravar = l => { try { localStorage.setItem(CHAVE, JSON.stringify(l)); } catch {} };
  function addSacola(id, qtd, obs, opcao) {
    const l = ler(); const ex = l.find(i => i.id === id && (i.opcao || "") === (opcao || ""));
    if (ex) { ex.qtd = Math.min(20, ex.qtd + qtd); if (obs) ex.obs = obs; } else l.push({ id, qtd, obs, opcao });
    gravar(l); renderSacola(); track("add_to_cart", { currency: "BRL", value: porId[id].preco * qtd, items: [itemGA(porId[id], qtd)] });
  }
  function abrirSacola() { if (!sacolaEl) return; sacolaEl.classList.add("aberta"); veu.hidden = false; sacolaEl.querySelector("button")?.focus(); }
  function fecharSacola() { if (!sacolaEl) return; sacolaEl.classList.remove("aberta"); if (veu) veu.hidden = true; }
  function mensagemSacola(l) {
    const linhas = ["Olá! Quero fazer um pedido na Kaevy3D.", ""];
    let tot = 0;
    l.forEach(i => { const p = porId[i.id]; const sub = p.preco * i.qtd; tot += sub;
      linhas.push(`• ${p.nome}${i.opcao ? ` (${i.opcao})` : ""} — ${i.qtd} × ${brl(p.preco)} = ${brl(sub)}${i.obs ? `\n  Obs.: ${i.obs}` : ""}`); });
    linhas.push("", `Total estimado: ${brl(tot)}`, "", `Vi no site e gostaria de confirmar a disponibilidade e combinar a retirada em ${CFG.local} (sem entrega).`);
    return { texto: linhas.join("\n"), tot };
  }
  function renderSacola() {
    const l = ler(); const n = l.reduce((a, i) => a + i.qtd, 0);
    $$(".sacola-btn .n").forEach(el => el.textContent = n || "");
    if (!sacolaEl) return;
    const box = $(".itens", sacolaEl);
    box.innerHTML = l.length ? "" : '<p class="mudo">Sua sacola está vazia.</p>';
    l.forEach((i, k) => {
      const p = porId[i.id]; const d = document.createElement("div"); d.className = "item";
      d.innerHTML = `<img src="${p.thumb}.jpg" alt="" width="64" height="64"><div><b>${p.nome}</b><br><span class="mudo">${brl(p.preco)}${i.opcao ? " · " + i.opcao : ""}</span>
        <div class="qtd" style="margin-top:6px"><button type="button" aria-label="Diminuir">−</button><input aria-label="Quantidade" type="number" min="1" max="20" value="${i.qtd}"><button type="button" aria-label="Aumentar">+</button></div></div>
        <button type="button" class="btn btn-sec" style="min-height:40px;padding:0 10px" aria-label="Remover ${p.nome}">Remover</button>`;
      const [menos, mais] = $$(".qtd button", d), inp = $("input", d);
      const set = v => { const ll = ler(); ll[k].qtd = Math.min(20, Math.max(1, v)); gravar(ll); renderSacola(); };
      menos.onclick = () => set(i.qtd - 1); mais.onclick = () => set(i.qtd + 1); inp.onchange = () => set(parseInt(inp.value, 10) || 1);
      d.lastElementChild.onclick = () => { const ll = ler(); ll.splice(k, 1); gravar(ll); renderSacola(); track("remove_from_cart", { items: [itemGA(p, i.qtd)] }); };
      box.appendChild(d);
    });
    const { texto, tot } = mensagemSacola(l);
    $("[data-sacola-total]", sacolaEl).textContent = brl(tot);
    const fin = $("[data-sacola-enviar]", sacolaEl);
    fin.setAttribute("aria-disabled", String(!l.length));
    fin.href = l.length ? `https://wa.me/${CFG.whatsapp}?text=${encodeURIComponent(texto)}` : "#";
    fin.onclick = e => { if (!l.length) { e.preventDefault(); return; } track("generate_lead", { canal: "whatsapp", currency: "BRL", value: tot, items: l.map(i => itemGA(porId[i.id], i.qtd)) }); };
  }
  if (sacolaEl && CFG.whatsapp) {
    $$(".sacola-btn").forEach(b => b.addEventListener("click", abrirSacola));
    $(".fechar-sacola", sacolaEl)?.addEventListener("click", fecharSacola);
    veu?.addEventListener("click", fecharSacola);
    renderSacola();
  }
})();
