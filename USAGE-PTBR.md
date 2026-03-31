# Guia de Uso: ComplianShift CLI

Este guia explica como instalar, configurar e executar o **ComplianShift CLI** no seu ambiente.

## 1. Instalação

Primeiro, certifique-se de ter o Python 3.10+ instalado. Em seguida, instale as dependências listadas no arquivo `requirements.txt`:

```bash
# Opcional: Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

## 2. Configuração do Mapeamento (`mapping.yaml`)

A API da Red Hat utiliza nomes comerciais (ex: "Red Hat OpenShift Data Foundation"), enquanto o OpenShift utiliza nomes técnicos nos pacotes (ex: `ocs-operator`, `mcg-operator`). 

O arquivo `mapping.yaml` na raiz do projeto é responsável por essa tradução. O projeto já vem com dezenas de operadores mapeados, mas você pode adicionar novos conforme a necessidade do seu cluster:

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

A CLI foi construída utilizando a biblioteca `Typer` e possui múltiplos comandos. Se você rodar apenas `python main.py`, o comando `scan` será executado por padrão.

### Scan de Suportabilidade (Padrão)
Baixa os dados consolidados da API v2 e verifica a compatibilidade dos operadores (CSVs) com a versão atual do OpenShift, além da data limite de suporte:

```bash
python main.py scan
# ou simplesmente:
python main.py
```

Você pode rodar com flags adicionais para controlar o cache e o nível de detalhes:
```bash
# Força a ignorar o cache e baixar tudo de novo
python main.py scan --force

# Altera o tempo de validade do cache (padrão é 30 min)
python main.py scan --cache-minutes 60

# Exibe logs detalhados do que está acontecendo por baixo dos panos
python main.py scan --debug
```

### Planejamento de Upgrade do OpenShift
Para verificar se os operadores atuais suportam as próximas versões do OpenShift e se precisam de mudança de canal:

```bash
python main.py check-upgrade
```

Você também pode visualizar a ajuda integrada da ferramenta executando:
```bash
python main.py --help
```

### O que esperar da execução:
1. Um *spinner* indicará que a ferramenta está consultando a API da Red Hat e o cluster.
2. A ferramenta exibirá o progresso individual de cada operador.
3. Ao final, uma tabela consolidada será exibida.
4. Se houver operadores fora da janela de suporte (EOL), um painel de alerta vermelho será exibido ao final, recomendando o upgrade.

## 5. Gerenciamento de Cache

Para otimizar as consultas e evitar bloqueios na API, o ComplianShift armazena os dados em cache local na pasta `data/`.
Os arquivos gerados são:
- `data/product-lifecycle.json` (Dados da API v2 da Red Hat)
- `data/csvs-report.json` (CSVs cacheados do cluster)

O cache é válido por 30 minutos por padrão. Você pode forçar a atualização usando a flag `--force` no comando scan, ou simplesmente deletando os arquivos da pasta `data/`.
