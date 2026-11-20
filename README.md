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

No fim ele mostra o link da loja no ar. Opções:

- `--preco 60`: preço único em reais (padrão 52)
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
- `modelo/`: as páginas, com marcadores como `{{NOME}}`, `{{WA}}` e `{{PRECO}}`
- `sites/<loja>/`: cada loja gerada, fora do git por causa das fotos

Para mudar o visual de todas as lojas, edite `modelo/` e gere de novo. Como as fotos já estão baixadas, a segunda vez é rápida.

## Limites

- Liga e modelo saem de palavras-chave nos títulos. Títulos estranhos ou times que o classificador não conhece vão para "Outros".
- Todas as camisas têm o mesmo preço.
- Os textos de entrega, personalização em 48 h e troca grátis são iguais em todas as lojas e não foram combinados com nenhum revendedor.
- O plano grátis da Vercel tem limites de uso. Se muitas lojas forem para o ar, talvez seja preciso um plano pago ou outra hospedagem.
