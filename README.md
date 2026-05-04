# Scraper Arquidiocese de Campo Grande

Extrator automatizado de paróquias e horários de missas do site oficial da [Arquidiocese de Campo Grande](https://arquidiocesedecampogrande.org.br).

## Sobre

Este script faz web scraping da seção [Nossas Paróquias](https://arquidiocesedecampogrande.org.br/nossas-paroquias/) e extrai, para cada uma das 54 paróquias da Arquidiocese:

- Nome
- Forania (Centro, Leste, Norte, Oeste, Rural, Sudoeste, Sul)
- Endereço completo
- Telefone e e-mail de contato
- Ano de criação
- **Tabela completa de celebrações** (missas e demais cultos), com tipo, dia da semana, horário e observações

Os dados são salvos em dois formatos: JSON estruturado (para uso em código) e CSV (para abrir no Excel/Numbers).

## Estrutura do site

Cada paróquia tem uma página individual em `arquidiocesedecampogrande.org.br/paroquias/<slug>/` contendo uma tabela HTML padronizada com as colunas `Tipo | Dia da Semana | Horário | Observações`. O scraper percorre todas elas.

## Requisitos

- Python 3.9 ou superior
- Bibliotecas: `requests`, `beautifulsoup4`, `lxml`

## Instalação

Clone ou baixe o projeto e instale as dependências:

```bash
pip3 install requests beautifulsoup4 lxml
```

Se aparecer o erro `externally-managed-environment` (comum no macOS recente):

```bash
# Opção 1 — ambiente virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 lxml

# Opção 2 — instalar forçando
pip3 install requests beautifulsoup4 lxml --break-system-packages
```

## Como usar

```bash
python3 scraper_arqcgr.py
```

O script imprime o progresso no terminal:

```
==> Lendo lista de paroquias: https://arquidiocesedecampogrande.org.br/nossas-paroquias/
    54 paroquias encontradas.
[1/54] CATEDRAL NOSSA SENHORA DA ABADIA E SANTO ANTÔNIO DE PÁDUA
    10 celebracoes extraidas
[2/54] PARÓQUIA NOSSA SENHORA DA ABADIA (SANTUÁRIO)
    8 celebracoes extraidas
...
==> JSON salvo em: paroquias_arqcgr.json
==> CSV salvo em: paroquias_arqcgr.csv
==> Concluido! 54 paroquias, ~400 celebracoes no total.
```

Tempo total: aproximadamente **1 min 30 s** (54 paróquias × 1,5 s de delay + tempo de rede).

## Arquivos gerados

### `paroquias_arqcgr.json`

Lista de objetos JSON, um por paróquia:

```json
[
  {
    "nome": "CATEDRAL NOSSA SENHORA DA ABADIA E SANTO ANTÔNIO DE PÁDUA",
    "url": "https://arquidiocesedecampogrande.org.br/paroquias/catedral-.../",
    "forania": "Centro",
    "ano_criacao": "07 de abril de 1912",
    "endereco": "Travessa Lídia Baís, 29 - Centro - CEP 79003-120 - Campo Grande/MS",
    "telefone": "(67) 3321-9886",
    "email": "catedral.santoantonio@hotmail.com",
    "celebracoes": [
      { "tipo": "Missa", "dia": "Domingo", "horario": "08:00", "observacoes": "" },
      { "tipo": "Missa", "dia": "Domingo", "horario": "09:30", "observacoes": "" },
      { "tipo": "Missa", "dia": "Sábado", "horario": "18:00", "observacoes": "" }
    ]
  }
]
```

### `paroquias_arqcgr.csv`

Uma linha por celebração, com encoding UTF-8 com BOM e delimitador `;` — abre direto no Excel e no Numbers. Colunas:

| Paróquia | Forania | Endereço | Telefone | E-mail | Tipo | Dia da Semana | Horário | Observações | URL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Configurações

No topo do `scraper_arqcgr.py`:

```python
DELAY_BETWEEN_REQUESTS = 1.5  # segundos entre requisições
```

Por padrão o script aguarda 1,5 s entre requisições para não sobrecarregar o servidor da Arquidiocese. Reduza com cuidado se quiser mais velocidade.

## Tratamento de erros

- **Retentativas automáticas:** se uma requisição falhar, o script tenta de novo até 3 vezes com backoff exponencial (2s, 4s, 6s).
- **Tolerância a falhas:** se uma paróquia específica falhar mesmo após retentativas, o script registra o erro no JSON daquela paróquia e continua para as próximas — o processamento das demais não é interrompido.

## Estrutura do projeto

```
lista igreja/
├── scraper_arqcgr.py       # script principal
├── paroquias_arqcgr.json   # gerado após execução
├── paroquias_arqcgr.csv    # gerado após execução
└── README.md
```

## Casos de uso

- Mapeamento de paróquias e horários de missa de Campo Grande e região
- Base de dados para aplicativos católicos locais
- Análise de cobertura geográfica e distribuição de celebrações por forania
- Material de pesquisa para projetos pastorais e acadêmicos

## Observações importantes

- Os dados pertencem à Arquidiocese de Campo Grande. Use de forma respeitosa, sem sobrecarregar o servidor.
- A estrutura HTML do site pode mudar a qualquer momento — se isso acontecer, o parser pode precisar de ajustes nos seletores das funções `extrair_celebracoes` e `extrair_info_paroquia`.
- Os horários extraídos refletem o que está publicado no site no momento da execução. Sempre confirme com a paróquia antes de divulgar.

## Licença

Uso livre para fins não comerciais. Os dados originais pertencem à Arquidiocese de Campo Grande.

## Autor

George Emmanuel — Campo Grande, MS
