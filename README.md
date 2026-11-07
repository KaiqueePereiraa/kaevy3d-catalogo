# Kaevy3D — Catálogo de venda direta

Site estático (GitHub Pages) com os produtos da Kaevy3D para **compra direta com retirada em Serra–ES**.
No ar em: https://kaiqueepereiraa.github.io/kaevy3d-catalogo/

## Como funciona

Tudo é gerado por `build.py` a partir de dois arquivos de dados:

| Arquivo | O que guarda |
|---|---|
| `config.json` | Configuração comercial: Instagram, WhatsApp, local de retirada, modo de compra, pagamentos, avaliações, GA4. |
| `produtos.json` | Fonte única dos produtos e categorias: nome, preço, preço da Shopee, fotos, textos, selos, ordem e destaque. |
| `assets/site.css`, `assets/site.js` | Visual e interações, escritos à mão. O build adiciona `?v=<hash>` para evitar cache antigo. |
| `img/p/<id>/` | Fotos reais de cada produto: `NN-nome.jpg/.webp` com 1200 px e `-600` com 600 px. |

O build gera estes arquivos (não edite à mão):
- `index.html`
- `produto/<id>/index.html`
- `politicas/{retirada,trocas,privacidade}/`
- `404.html`
- `sitemap.xml`
- `robots.txt`

```bash
python3 build.py            # valida e gera o site
python3 build.py --checar   # só valida (campos, imagens, ids duplicados)
python3 -m http.server 8765 # testar em http://localhost:8765
```

## O que foi implementado

- **Home:**
  - hero (no celular: título → subtítulo → botão "Explorar as peças" → foto → informações de retirada)
  - barra de benefícios
  - cards de categoria (atalhos para os filtros)
  - **uma única vitrine** com os 7 produtos e filtros (link direto `?cat=colecionaveis#vitrine`); 2 colunas no celular, até 4 no desktop
  - seção de produção + bloco de confiança "Feito pela Kaevy3D. Escolhido por você."
  - comparação com a Shopee (percentual calculado automaticamente; some se não houver economia válida)
  - como comprar
  - aviso de retirada
  - FAQ
  - CTA final
  - rodapé
- **Página por produto:**
  - galeria com miniaturas, deslize, contador, zoom e vídeo opcional
  - preço direto, economia, 3 características principais
  - opções (só aparecem se houver variação real cadastrada), quantidade, observação opcional recolhida
  - valor total estimado logo acima do botão "Pedir esta peça pelo WhatsApp"
  - disponibilidade, retirada e pagamento ("confirmados durante o atendimento" enquanto não houver dado real)
  - produtos relacionados
  - barra fixa no celular (aparece quando o botão principal sai da tela; não cobre a galeria nem o rodapé)
- **Políticas:** retirada, trocas e devoluções (CDC) e privacidade (LGPD).
- **SEO:**
  - title, description, canonical e Open Graph por página
  - JSON-LD Product e BreadcrumbList, **sem** disponibilidade e **sem** avaliação inventada
  - sitemap e robots
- **Desempenho:** imagens WebP + JPG em dois tamanhos, `lazy` fora da primeira dobra, sem bibliotecas externas além das fontes.
- **Acessibilidade:**
  - um `h1` por página
  - textos alternativos
  - foco visível
  - navegação por teclado no menu e no zoom
  - respeita `prefers-reduced-motion`
- **Testes:**
  - responsivo testado de 320 a 1440 px, sem rolagem horizontal
  - preços conferidos card a card
  - teste de manutenção de preço feito e revertido

## Modo de compra ativo: pedido assistido

- **Sem WhatsApp** (`"whatsapp": ""`):
  - o botão copia um resumo do pedido (produto, quantidade, valor estimado, observação, retirada em Serra–ES) e abre o Instagram @kaevy3d
  - não existe sacola
- **Com WhatsApp** (situação atual): coloque o número real em `config.json`, no formato `55DDDNÚMERO`, só dígitos. O site passa a:
  - abrir o WhatsApp com a mensagem pronta
  - mostrar uma sacola (guardada só no navegador do cliente)
- **Checkout online:** está desativado. Nada é cobrado no site. Veja "Modo 2" abaixo.
- **Analytics (preparado, desligado):** preencha `ga4_id` em `config.json` com o ID real (`G-...`). Com `analytics_exigir_consentimento: true` (padrão), o visitante vê um aviso e o GA4 só é carregado se aceitar.

  | Evento | Quando |
  |---|---|
  | `view_item_list` | vitrine exibida |
  | `select_category` | filtro de categoria |
  | `select_item` | clique em produto |
  | `view_item` | página de produto |
  | `add_to_cart` / `remove_from_cart` | sacola |
  | `contact_click` | clique em WhatsApp ou Instagram |
  | `generate_lead` | início de pedido (mensagem montada) |

  O evento `purchase` **nunca** é disparado: clicar no WhatsApp não é venda. Ele só deve existir com checkout real (Modo 2).

## Manutenção

**Mudar preço:** edite `preco_manual` do produto em `produtos.json` e rode `python3 build.py`. Card, página, resumo, economia e JSON-LD são atualizados juntos. Se mudar o preço da Shopee, atualize `shopee` e `data_comparacao` em `config.json`.

**Adicionar produto:**
1. Crie `img/p/<id>/` com as fotos, nos dois tamanhos, em `.jpg` e `.webp`.
2. Copie um produto existente em `produtos.json` e troque `id`, textos, `categoria`, `preco_manual`, `shopee` (ou `null`), `img` e `galeria`.
3. Rode `python3 build.py --checar`, depois `python3 build.py`.

**Campos do produto que aparecem na vitrine:** `nome`, `diferencial` (frase curta do card), `preco_manual`, `shopee`, primeira foto da `galeria`.

**Galeria:** a ordem de `galeria` é a ordem das fotos. Sugestão: frontal, lateral, detalhe do acabamento, foto mostrando tamanho, foto em uso/decoração. Use só fotos reais. Vídeo opcional: `"video": {"src": "img/p/<id>/video.mp4", "poster": "img/p/<id>/video-poster.jpg", "alt": "..."}` (MP4 H.264 sem áudio, ~540 px de largura, até ~2 MB).

**Opções/variações:** `"variacoes": [{"nome": "Cor", "opcoes": ["Preto", "Branco"]}]`. Só cadastre opções que existem de verdade; com a lista vazia o seletor não aparece.

**Pagamento:** `config.json > pagamentos_confirmados`, ex.: `["Pix", "dinheiro"]`. Vazio = "As condições de pagamento são confirmadas durante o atendimento."

**Disponibilidade:** o padrão é `"a_confirmar"` ("Consulte a disponibilidade"). Não use selos de urgência nem estoque que não sejam reais.

**Ocultar produto:** `"ativo": false`.

**Avaliações:** só depoimentos reais e autorizados em `config.json > avaliacoes`. Com a lista vazia, a seção não aparece.

## Publicar

```bash
python3 build.py
git add -A && git commit -m "atualiza catálogo" && git push
```

O GitHub Pages publica a branch `main` em 1 a 2 minutos. A tag `v1-catalogo-simples` guarda a versão anterior.

## Pendências (dados que só o dono pode fornecer)

- [x] WhatsApp comercial configurado (pedido direto + sacola ativos)
- [ ] Formas de pagamento aceitas (`pagamentos_confirmados`)
- [ ] ID do GA4, se quiser métricas (o aviso de consentimento já está pronto)
- [ ] Avaliações reais de clientes, com autorização
- [ ] Endereço público de retirada (opcional; hoje é combinado na conversa)
- [x] Goku: 3 fotos novas extraídas da filmagem real (estante, lado, costas); Muttley: vídeo real na galeria
- [ ] Mais fotos por produto (lateral, detalhe, em uso) e vídeos curtos; fotos reais da impressora/produção
- [ ] Conferir a regularidade de uso dos personagens licenciados (Goku, Muttley, Harry Potter, Banguela)

## Modo 2 — checkout online (não implementado)

Para vender com pagamento no site é preciso ter:
- um **backend** (ex.: função serverless na Vercel ou Cloudflare) que crie a preferência de pagamento no Mercado Pago, com o **preço vindo do servidor** e nunca do navegador;
- um **webhook** de notificação com verificação de assinatura e **idempotência**, para não confirmar o mesmo pedido duas vezes;
- disparar `purchase` só após o webhook confirmar o pagamento;
- guardar o token de acesso **somente** em variável de ambiente; nunca no repositório nem no JS;
- revisar as políticas de trocas e privacidade para pagamento online.

Até lá, `modo_compra` fica `"assistido"`.
