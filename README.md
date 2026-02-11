# Minerva Tabela FIPE App

Aplicacao Streamlit para consulta da Tabela FIPE com fluxo em cascata, usando somente a API oficial:

- Base URL: `https://fipe.parallelum.com.br/api/v2`
- Header obrigatorio: `X-Subscription-Token`
- Token via variavel de ambiente: `FIPE_TOKEN`

## Requisitos

- Python 3.11+
- Token valido da API FIPE

## Configuracao

No PowerShell:

```powershell
$env:FIPE_TOKEN="seu_token_aqui"
```

Instalacao:

```powershell
pip install -e .[dev]
```

## Executar aplicacao

```powershell
streamlit run src/ui/consulta_page.py
```

## Executar testes

```powershell
pytest -q --cov=src --cov-report=term-missing --cov-fail-under=80
```

Todos os testes sao offline e usam mocks (sem chamadas reais para internet).

## Executar qualidade de codigo

```powershell
ruff check .
black --check .
```

## Arquitetura

Estrutura principal:

```text
src/
  ui/
    consulta_page.py
  services/
    fipe_service.py
  providers/
    base.py
    api_provider.py
  domain/
    models.py
  utils/
    formatting.py
tests/
  test_formatting.py
  test_api_provider.py
  test_fipe_service.py
```

Responsabilidades:

- `src/providers/base.py`: contrato `FipeProvider`.
- `src/providers/api_provider.py`: cliente HTTP para endpoints da API oficial, token obrigatorio, timeout e erros customizados.
- `src/services/fipe_service.py`: orquestracao e normalizacao de dados para uso da UI.
- `src/ui/consulta_page.py`: fluxo Streamlit em cascata com `session_state`, cache e debug.
- `src/utils/formatting.py`: formatacao BRL e normalizacao de mes de referencia.

## Endpoints implementados

- `GET /references`
- `GET /{vehicleType}/brands?reference=X`
- `GET /{vehicleType}/brands/{brandId}/models?reference=X`
- `GET /{vehicleType}/brands/{brandId}/models/{modelId}/years?reference=X`
- `GET /{vehicleType}/brands/{brandId}/models/{modelId}/years/{yearId}?reference=X`

## Checklist

- Sem Kaggle
- Sem scraping
- Somente API oficial
- Token obrigatorio (`FIPE_TOKEN`)
- Testes offline com mocks
- Cobertura minima configurada para `>= 80%`
- `ruff` + `black` + CI no GitHub Actions
