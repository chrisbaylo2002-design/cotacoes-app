# Gerador de Cotações — Excel & PDF

App em Streamlit que recebe o texto bruto de uma cotação (hotel, passeio, transfer etc.),
interpreta os dados por regras (sem IA, sem API, 100% grátis) e gera automaticamente um
**Excel** (planilha de dados) e um **PDF** de apresentação (com logo e cor personalizados).

## Como rodar localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Rode o app:
   ```bash
   streamlit run app.py
   ```

3. O navegador abrirá em `http://localhost:8501`.

## Como usar

1. Cole o texto da cotação recebida (do fornecedor, por e-mail, WhatsApp etc.) na caixa de texto.
2. Clique em **"Processar texto"** — o parser extrai fornecedor, datas, categorias e valores.
3. **Revise e edite** a tabela gerada (você pode corrigir qualquer campo, adicionar ou remover linhas
   manualmente — isso cobre os casos em que o texto foge do padrão esperado).
4. Ajuste o **logo** e a **cor** na barra lateral, se quiser personalizar o PDF.
5. Clique em **"Baixar Excel"** ou **"Baixar PDF"**.

## Formato de texto reconhecido pelo parser

O parser (`utils/parser.py`) foi feito pro padrão de cotação de hotel, por exemplo:

```
Hotel: Windsor Plaza Brasília
Até 18 apartamentos singles
1º - 20/09 a 26/09/2026 - Confirmação sujeita a disponibilidade

20/09/2026 - Diária
Superior Executivo/Superior Plus single: R$ 830,00 + taxas
Superior Executivo/Superior Plus duplo: R$ 954,00 + taxas
Superior Executivo/Superior Plus triplo: R$ 1.193,00 + taxas

21,22 e 23/09/2026 - Diária
Superior Executivo/Superior Plus single: R$ 1.166,00 + taxas
...
```

Regras usadas:
- Linha `Hotel:` / `Serviço:` / `Passeio:` / `Fornecedor:` → nome do fornecedor.
- Linha contendo a palavra "Diária" + uma data → marca o início de um novo grupo de datas
  (todas as linhas de preço seguintes usam essa data, até aparecer outra linha de "Diária").
- Linha no formato `Categoria: R$ valor + observação` → vira um item da cotação. A ocupação
  (single/duplo/triplo) é detectada automaticamente pelo texto da categoria.
- Qualquer outra linha com data (ex: período de validade) → observação geral.

Se o texto do fornecedor fugir muito desse padrão, alguns itens podem não ser identificados
automaticamente — nesse caso, é só adicionar/corrigir manualmente na tabela editável antes de
gerar os arquivos.

## Rodando com Docker

Se você tem o Docker instalado, não precisa instalar Python nem dependências.

**Opção A — Docker Compose (mais simples):**
```bash
docker compose up --build
```
Acesse em `http://localhost:8501`. Pra rodar em segundo plano: `docker compose up --build -d`.
Pra parar: `docker compose down`.

**Opção B — Docker puro:**
```bash
docker build -t cotacoes-app .
docker run -p 8501:8501 cotacoes-app
```

### Disponibilizar para outras pessoas acessarem

Rodar o container no seu computador só deixa o app acessível localmente. Pra outras
pessoas acessarem de fora, você precisa subir esse mesmo container em algum servidor
com IP público. Algumas opções comuns, do mais simples ao mais robusto:

- **Railway ou Render** — conecta o repositório (ou sobe a imagem Docker) e eles cuidam
  do servidor e do domínio pra você. Bom pra começar rápido, tem plano gratuito limitado.
- **Fly.io** — parecido, com CLI própria (`fly launch` detecta o Dockerfile automaticamente).
- **VPS próprio** (DigitalOcean, Hetzner, AWS EC2 etc.) — você instala Docker no servidor,
  copia o projeto, roda `docker compose up -d` e aponta um domínio pra ele. Mais controle,
  mais trabalho de manutenção.

Em qualquer uma dessas opções, o `Dockerfile` e o `docker-compose.yml` já incluídos no
projeto são o que a plataforma vai usar pra construir e rodar o app — não precisa mudar
nada no código.

## Estrutura do projeto

```
cotacoes_app/
├── app.py                  # interface Streamlit
├── requirements.txt
└── utils/
    ├── parser.py           # extrai dados do texto por regras (regex)
    ├── excel_gen.py        # gera o .xlsx
    └── pdf_gen.py           # gera o .pdf de apresentação
```

## Próximos passos sugeridos

- Deploy gratuito no [Streamlit Community Cloud](https://streamlit.io/cloud) — basta subir
  este projeto num repositório do GitHub e conectar (não precisa configurar nenhuma chave de API).
- Adicionar upload de logo fixo (salvo em `assets/`) em vez de precisar subir toda vez.
- Ajustar as regras do `parser.py` conforme aparecerem novos padrões de texto de outros fornecedores.
