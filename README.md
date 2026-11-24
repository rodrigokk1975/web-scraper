# Web Scraper com Relatório CSV

Aplicação CLI em **Python** para demonstração de **coleta, limpeza, organização de dados e geração de relatórios em CSV** usando `requests` e `BeautifulSoup`, direcionada ao sandbox educacional [`books.toscrape.com`](https://books.toscrape.com/).

## Destaques Técnicos

- **Scraping Ético e Responsável:** validação prévia de `robots.txt` (RFC 9309), respeito a `Crawl-delay`, `User-Agent` descritivo, retries com backoff exponencial e *rate limiting* configurável.
- **Pipeline Modular:** separação clara entre cliente HTTP (`client.py` / `robots.py`), parser HTML (`parser.py`), coleta paginada (`scraper.py`), limpeza/normalização (`cleaner.py`), exportação (`exporter.py`) e relatório analítico (`reporter.py`).
- **Saída Leve em CSV:** gera tanto o dataset limpo (`books_clean.csv`) quanto um relatório de métricas agregadas (`books_summary.csv`), ambos em `UTF-8` com BOM (`utf-8-sig`) para abertura direta no Excel.
- **Testes Offline Determinísticos:** suíte `pytest` usando fixtures HTML locais e mocks, sem depender de acesso à internet.

> **Nota sobre APIs oficiais e termos de uso:** Em projetos reais, sempre verifique os Termos de Uso do site e **dê preferência a uma API oficial** quando ela existir. Este projeto utiliza `books.toscrape.com`, um site criado especificamente para fins educacionais de web scraping.

---

## Instalação

```powershell
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependências e o pacote em modo editável
pip install -r requirements.txt
pip install -e . --no-build-isolation --no-deps
```

---

## Uso (CLI)

```powershell
# Coleta padrão (5 páginas = 100 livros) salvando em output/
python -m web_scraper

# Coletar 2 páginas ordenando pelo menor preço com logs detalhados
python -m web_scraper --max-pages 2 --sort price_asc --output-dir output --verbose

# Coletar todo o catálogo (50 páginas) com delay de 1s entre requisições
python -m web_scraper --max-pages 0 --delay 1.0
```

### Opções Disponíveis

| Flag | Padrão | Descrição |
|---|---|---|
| `--base-url` | `https://books.toscrape.com/` | URL inicial do catálogo |
| `--max-pages` | `5` | Máximo de páginas (`0` = todas) |
| `--delay` | `0.5` | Intervalo mínimo (segundos) entre requisições |
| `--output-dir` | `output` | Diretório onde os CSVs serão salvos |
| `--sort` | `rating_desc` | Ordenação: `rating_desc`, `price_asc`, `price_desc`, `title_asc` |
| `--verbose` | `False` | Ativa logs em nível `DEBUG` |

---

## Arquivos Gerados

### 1. `output/books_clean.csv`
Dataset limpo, deduplicado e ordenado:

| Coluna | Descrição | Exemplo |
|---|---|---|
| `title` | Título normalizado | `A Light in the Attic` |
| `price_gbp` | Preço numérico em GBP | `51.77` |
| `rating` | Avaliação inteira (`1` a `5`) | `3` |
| `in_stock` | Disponibilidade booleana | `True` |
| `url` | URL absoluta do livro | `https://books.toscrape.com/catalogue/...` |
| `scraped_at` | Timestamp UTC ISO 8601 | `2026-11-24T14:30:00Z` |

### 2. `output/books_summary.csv`
Relatório consolidado com total de livros, estoque, preço médio, mediano, mínimo, máximo e distribuição por estrelas (1 a 5).

---

## Testes Automatizados

```powershell
python -m pytest -v
```
