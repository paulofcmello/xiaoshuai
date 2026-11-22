# Gerador de lojas de camisas

Monta e publica a loja de um revendedor de camisas de time a partir de três dados: nome da loja, WhatsApp e link do Yupoo. O primeiro site feito com ele está em https://xiaoshuai.vercel.app.

Cada loja gerada tem:

- o catálogo inteiro do Yupoo, separado por liga (Brasileirão, Premier League, seleções, retrô…)
- títulos em português com time, modelo e temporada ("Camisa 2 Cruzeiro 26/27 · Jogador")
- uma página para cada camisa, com escolha de tamanho
- carrinho com total e botão que abre o WhatsApp do revendedor com o pedido já escrito
- versão em chinês, que o próprio visitante liga

## Gerar uma loja

```bash
python3 gerar.py --nome "Xiaoshuai" --whatsapp "+86 195 2122 8559" --yupoo "https://x.yupoo.com/photos/1022669895/albums"
```

Para juntar vários Yupoos numa loja só, passe os links um depois do outro: `--yupoo LINK1 LINK2 LINK3`.

No fim ele mostra o link da loja no ar. Opções:

- `--preco 60` e `--preco-jogador 90`: preço da versão torcedor e da versão jogador, em reais (padrão 58 e 87)
- `--preco-nba 150`: preço das camisas da NBA, em reais (padrão: as regras de torcedor, jogador e retrô)
- `--preco-treino 70`: preço de camiseta e short das roupas de treino (Nike, Adidas, On…), em reais. Jaqueta, moletom e calça ficam no preço padrão
- `--preco-infantil 80`: preço do conjunto infantil, em reais (vale também para retrô e manga longa infantil; NBA fica no preço da NBA)
- `--preco-manga-longa 85` e `--preco-manga-longa-jogador 110`: preço da manga longa (torcedor e jogador), em reais. Retrô de manga longa usa o preço da manga longa jogador
- `sites/<loja>/_manga-longa.txt`: álbuns que são manga longa mas não dizem isso no título, um código por linha (o código está no fim do link da foto, ex.: `5c0236b081`; pode pôr `# comentário` depois). Eles passam a valer como manga longa no preço e na etiqueta
- `--preco-retro 99`: preço das retrô, em reais (padrão: o mesmo da versão torcedor)
- `--personalizacao 20`: preço de nome e número por peça, em reais. Sem ela, o site mostra "valor a combinar" e o pedido avisa que o preço ainda vai ser confirmado
- `--patch 7`: preço de cada patch, em reais. A página da camisa pergunta "Tem patch?" (não, ou de 1 a 4) e pede para o cliente mandar a foto do patch no WhatsApp. Sem ela, a pergunta não aparece
- `--frete 5,4,3`: frete em dólar com 1, 2, 3… camisas; com mais camisas que a lista, é grátis (padrão 5,4,3)
- `--cotacao 5.8`: reais por dólar, para converter o frete. Para passar o frete já em reais, use `--cotacao 1` (ex.: `--frete 56,49,42,35,28,21,14 --cotacao 1`)
- `--logo jin.webp`: imagem no lugar do nome escrito no topo e no rodapé. Fica guardada na pasta da loja, então nas próximas vezes não precisa repetir
- `--banner banner.webp`: imagem larga (proporção 3:1) no topo da home. Também fica guardada na pasta da loja e substitui um banner anterior
- `--sem-classico`: tira a home antiga e o botão "Visual clássico". Também fica guardado na pasta da loja
- `--sem-preco`: esconde todos os preços (cartões, página da camisa, carrinho, mensagem e página do pedido). O frete só aparece quando é grátis, sem valor. Os preços continuam guardados nos dados; `--com-preco` volta a mostrar. Fica guardado na pasta da loja
- `--amostra 10`: loja de demonstração rápida: lê a 1ª página de cada categoria do Yupoo e fica com só 10 camisas por liga (uma por time primeiro). Sem home clássica. Escreve `sites/<loja>/banner-prompt.txt`
- `--gerar-banner`: se a loja ainda não tem banner, gera o cenário pelo Codex CLI (usa o login do ChatGPT; precisa de `codex` instalado) e coloca por cima as cinco camisas de `gerador/camisas.png`. Leva de 1 a 3 minutos
- cor da marca: sai sozinha do `--banner` (ou do `--logo`, se ainda não tem banner) e troca o vermelho do modelo em todas as páginas
- `--cloudflare`: publica no Cloudflare Pages (`npx wrangler login` antes) em vez da Vercel
- `--slug outro-nome`: nome da pasta e do projeto na hospedagem (padrão: o nome da loja sem acentos)
- `--sem-publicar`: só monta a pasta, sem publicar

Um catálogo de ~3.600 camisas leva alguns minutos, quase todo o tempo baixando fotos. Se cair no meio, é só rodar de novo: as fotos que já baixaram são puladas.

## Banner e cor da marca

Para montar uma amostra sem publicar, passe o logo e use `--amostra 10 --sem-publicar`. O gerador salva `banner-prompt.txt` na pasta da loja. Você pode usar esse texto para criar um banner e passá-lo com `--banner caminho/para/banner.webp` na próxima execução. Para deixar o Codex CLI gerar o cenário e adicionar as cinco camisas fixas, use `--gerar-banner` na primeira execução. Se já houver um banner na pasta, essa opção o reaproveita; use `--banner` para trocar a imagem.

A cor do site é extraída do banner quando ele existe, ou do logo quando não existe. Gere a loja novamente após trocar qualquer uma dessas imagens para atualizar o CSS. Para usar camisas diferentes no banner automático, substitua `gerador/camisas.png` antes de gerar um novo banner.

## Precisa ter

- Python 3 e Pillow: `python3 -m pip install Pillow`
- `cwebp`: `brew install webp`
- Node e login na hospedagem escolhida: `npx vercel login` ou `npx wrangler login`

## Como está organizado

- `gerar.py`: junta tudo, do Yupoo até o link publicado
- `gerador/yupoo.py`: lê os álbuns do Yupoo e baixa as fotos em WebP de 440px
- `gerador/classificar.py`: tira time, liga, modelo, temporada e tamanhos do título de cada álbum
- `modelo/`: as páginas, com marcadores como `{{NOME}}` e `{{WA}}`. A home tem dois visuais: `index.html` (o novo) e `classico.html`. Um botão no menu troca entre eles, e o navegador do visitante guarda a escolha
- `sites/<loja>/`: cada loja gerada, fora do git por causa das fotos
- `sites/<loja>/dados/`: o catálogo dividido em arquivos pequenos para o celular não baixar tudo: `home.json` (12 camisas por liga), `l-<liga>.json` (a página de cada liga mostra 48 por vez), `i-<xx>.json` (camisas pelo começo do código, para a página da camisa, o carrinho e o pedido) e `busca.json` (só abre quando alguém usa a lupa)

Para mudar o visual de todas as lojas, edite `modelo/` e gere de novo. Como as fotos já estão baixadas, a segunda vez é rápida.

## Limites

- Liga e modelo saem de palavras-chave nos títulos. Títulos estranhos ou times que o classificador não conhece vão para "Outros".
- Os preços especiais dependem de palavras-chave no título do álbum ou das opções passadas. Tamanhos grandes não têm preço próprio.
- Os textos de entrega e personalização em 48 h são iguais em todas as lojas e não foram combinados com nenhum revendedor.
- Os planos grátis de hospedagem têm limites de uso. Confira os limites da Vercel ou do Cloudflare Pages antes de publicar muitas lojas.
