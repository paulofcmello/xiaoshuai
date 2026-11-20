# Xiaoshuai

Mockup de loja de camisas de time, feito para apresentar ao fornecedor. Está no ar em https://xiaoshuai.vercel.app.

São 3.593 camisas, tiradas do catálogo do fornecedor no Yupoo e separadas por liga. Cada camisa tem a própria página, com escolha de tamanho. O carrinho fica salvo no navegador e o pedido é fechado pelo WhatsApp, com a mensagem já escrita. O site tem versão em português e em chinês.

## Arquivos

- `index.html`: página inicial e catálogo por liga
- `camisa.html`: página de uma camisa (`camisa.html?id=<hash>`)
- `carrinho.html`: carrinho, total e botão do WhatsApp
- `style.css`: estilos usados pelas três páginas
- `catalog.json`: dados de cada camisa (`h` hash da foto, `n` time, `l` liga, `t`/`tz` título em PT/ZH, `q`/`qz` detalhes, `s` tamanhos)
- `fotos/all/`: fotos em WebP de 440px, nomeadas pelo hash
- `fotos/*.jpeg`: fotos da primeira tela

## Rodar localmente

```bash
python3 -m http.server 5173
```

Depois é só abrir http://localhost:5173.

## Publicar

```bash
npx vercel deploy --prod --archive=tgz
```

Use `--archive=tgz`. Sem ele, a Vercel envia as 3.593 fotos uma por uma e o plano gratuito estoura o limite de uploads por dia.

## O que ainda é provisório

- Todas as camisas custam R$ 52 (`PRICE` em `camisa.html` e `carrinho.html`, e o texto fixo em `index.html`).
- O número do WhatsApp fica em `carrinho.html` (`WA`).
- A liga e o modelo de cada camisa saíram dos títulos do Yupoo por palavras-chave, então algumas podem estar no lugar errado.
- Prazos de entrega, personalização em 48 h e troca grátis são textos de exemplo.
