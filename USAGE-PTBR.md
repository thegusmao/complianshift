# Guia de Uso: ComplianShift CLI

Este guia explica como instalar, configurar e executar o **ComplianShift CLI** no seu ambiente.

## 1. Instalação

O ComplianShift pode ser executado de duas formas: diretamente a partir do código-fonte (requer Python) ou como um binário compilado e autossuficiente (sem necessidade de Python). Escolha a opção que melhor se adapta ao seu ambiente.

### Opção A — Executar a partir do código-fonte (requer Python)

Certifique-se de ter o Python 3.10+ instalado. Em seguida, instale as dependências listadas no arquivo `requirements.txt`:

```bash
# Opcional: Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

### Opção B — Executar o binário compilado (sem Python)

Baixe ou compile o binário `complianshift` (veja [DEVELOPMENT.md](DEVELOPMENT.md)) e, opcionalmente, instale-o no sistema:

```bash
# Torne o binário executável (se necessário)
chmod +x ./complianshift

# Opcional: instale no PATH para poder chamá-lo de qualquer lugar
sudo cp ./complianshift /usr/local/bin/complianshift
```

## 2. Configuração do Mapeamento (`mapping.yaml`)

A API da Red Hat utiliza nomes comerciais (ex: "Red Hat OpenShift Data Foundation"), enquanto o OpenShift utiliza nomes técnicos nos pacotes (ex: `ocs-operator`, `mcg-operator`). 

O arquivo `mapping.yaml` na raiz do projeto é responsável por essa tradução durante o scan. O projeto já vem com dezenas de operadores mapeados, mas você pode adicionar novos conforme a necessidade do seu cluster:

```yaml
# Exemplo de conteúdo do mapping.yaml
amq-streams: "Streams for Apache Kafka"
3scale-operator: "Red Hat 3scale API Management"
rhbk-operator: "Red Hat build of Keycloak"
odf-operator: "Red Hat OpenShift Data Foundation"
cluster-observability-operator: "Red Hat OpenShift Observability"
```
*Dica: Se um operador retornar como "Desconhecido" durante a execução, você precisará encontrar o nome oficial do produto na API da Red Hat e adicioná-lo a este arquivo.*

## 3. Autenticação no Cluster

A ferramenta utiliza o contexto atual do seu Kubernetes/OpenShift. Certifique-se de estar logado no cluster alvo:

```bash
oc login --token=SEU_TOKEN --server=URL_DO_CLUSTER
# ou garanta que a variável KUBECONFIG aponta para um arquivo válido
```

## 4. Execução

A CLI foi construída utilizando a biblioteca `Typer`. Os comandos são idênticos tanto ao executar a partir do código-fonte quanto ao usar o binário compilado — basta substituir `python main.py` por `complianshift` (ou `./complianshift` caso o binário não esteja no seu `PATH`).

### Executando a partir do código-fonte

```bash
python main.py
```

### Executando o binário compilado

```bash
# Se o binário estiver no PATH
complianshift

# Se estiver executando a partir do diretório dist/
./complianshift
```

### Flags disponíveis

Você pode rodar com flags adicionais para controlar o cache e o nível de detalhes:

```bash
# Força a ignorar o cache e baixar tudo de novo
complianshift --force

# Altera o tempo de validade do cache (padrão é 30 min)
complianshift --cache-minutes 60

# Exibe logs detalhados do que está acontecendo por baixo dos panos
complianshift --debug

# Exporta a tabela de compliance em HTML
complianshift -o html

# Exporta em Markdown para um diretório específico
complianshift -o md -p ./reports

# Combina com outras flags
complianshift --force -o html -p /tmp/reports
```

Você também pode visualizar a ajuda integrada da ferramenta executando:

```bash
complianshift --help
```

### O que esperar da execução:
1. Um *spinner* indicará que a ferramenta está consultando a API da Red Hat e o cluster.
2. A ferramenta exibirá o progresso individual de cada operador.
3. Ao final, uma tabela consolidada será exibida.
4. Se houver operadores fora da janela de suporte (EOL), um painel de alerta vermelho será exibido ao final, recomendando o upgrade.
5. Se `--output` for especificado, um arquivo de relatório (`compliance-report-YYYY-MM-DD.html` ou `.md`) será gerado no diretório indicado por `--path` (padrão: diretório atual).

## 5. Gerenciamento de Cache

Para otimizar as consultas e evitar bloqueios na API, o ComplianShift armazena os dados em cache local na pasta `data/`.
Os arquivos gerados são:
- `data/product-lifecycle.json` (Dados da API v2 da Red Hat)
- `data/csvs-report.json` (CSVs cacheados do cluster)

O cache é válido por 30 minutos por padrão. Você pode forçar a atualização usando a flag `--force` no comando scan, ou simplesmente deletando os arquivos da pasta `data/`.
