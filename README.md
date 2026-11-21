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
- `--preco-retro 99`: preço das retrô, em reais (padrão: o mesmo da versão torcedor)
- `--personalizacao 20`: preço de nome e número por peça, em reais. Sem ela, o site mostra "valor a combinar" e o pedido avisa que o preço ainda vai ser confirmado
- `--patch 7`: preço de cada patch, em reais. A página da camisa pergunta "Tem patch?" (não, ou de 1 a 4) e pede para o cliente mandar a foto do patch no WhatsApp. Sem ela, a pergunta não aparece
- `--frete 5,4,3`: frete em dólar com 1, 2, 3… camisas; com mais camisas que a lista, é grátis (padrão 5,4,3)
- `--cotacao 5.8`: reais por dólar, para converter o frete. Para passar o frete já em reais, use `--cotacao 1` (ex.: `--frete 56,49,42,35,28,21,14 --cotacao 1`)
- `--logo jin.webp`: imagem no lugar do nome escrito no topo e no rodapé. Fica guardada na pasta da loja, então nas próximas vezes não precisa repetir
- `--banner banner.webp`: imagem larga (proporção 3:1) no lugar do título do topo da home. Também fica guardada na pasta da loja
- `--sem-classico`: tira a home antiga e o botão "Visual clássico". Também fica guardado na pasta da loja
- `--slug outro-nome`: nome da pasta e do projeto na Vercel (padrão: o nome da loja sem acentos)
- `--sem-publicar`: só monta a pasta, sem publicar

Um catálogo de ~3.600 camisas leva alguns minutos, quase todo o tempo baixando fotos. Se cair no meio, é só rodar de novo: as fotos que já baixaram são puladas.

## Precisa ter

- Python 3 (só biblioteca padrão)
- `cwebp`: `brew install webp`
- Node (para o `npx vercel`) e login na Vercel: `npx vercel login`

## Como está organizado

- `gerar.py`: junta tudo, do Yupoo até o link publicado
- `gerador/yupoo.py`: lê os álbuns do Yupoo e baixa as fotos em WebP de 440px
- `gerador/classificar.py`: tira time, liga, modelo, temporada e tamanhos do título de cada álbum
- `modelo/`: as páginas, com marcadores como `{{NOME}}` e `{{WA}}`. A home tem dois visuais: `index.html` (o novo) e `classico.html`. Um botão no menu troca entre eles, e o navegador do visitante guarda a escolha
- `sites/<loja>/`: cada loja gerada, fora do git por causa das fotos

Para mudar o visual de todas as lojas, edite `modelo/` e gere de novo. Como as fotos já estão baixadas, a segunda vez é rápida.

## Limites

- Liga e modelo saem de palavras-chave nos títulos. Títulos estranhos ou times que o classificador não conhece vão para "Outros".
- Só três preços: torcedor, jogador e retrô (a versão jogador sai do título do álbum). Kit infantil, agasalho, personalização, patch e tamanhos grandes não têm preço próprio.
- Os textos de entrega e personalização em 48 h são iguais em todas as lojas e não foram combinados com nenhum revendedor.
- O plano grátis da Vercel tem limites de uso. Se muitas lojas forem para o ar, talvez seja preciso um plano pago ou outra hospedagem.
