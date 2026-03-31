# ComplianShift CLI

![ComplianShift Screenshot](doc/img/screenshot.png)

**ComplianShift** é uma ferramenta de linha de comando (CLI) desenvolvida em Python para realizar diagnósticos de conformidade dos Operadores instalados em um cluster OpenShift. 

A ferramenta valida se as versões e canais dos operadores Red Hat (instalados via OLM - Operator Lifecycle Manager) estão dentro da janela de suporte oficial da Red Hat, classificando-os em:
- **Full Support** (Suporte Completo)
- **Maintenance Support** (Suporte de Manutenção)
- **End of Life / Unsupported** (Fim de Vida / Sem Suporte)

## Principais Funcionalidades

1. **Discovery de Cluster**: Conecta-se automaticamente ao seu cluster OpenShift atual (via `~/.kube/config`) e coleta os *ClusterServiceVersions* (CSVs) da fonte `Red Hat`.
2. **Integração com API Red Hat (v2)**: Consulta a API oficial de Ciclo de Vida de Produtos da Red Hat para obter as datas exatas de suporte de cada versão e a compatibilidade com a versão atual do seu cluster OpenShift.
3. **Planejamento de Upgrade**: Verifica se os operadores instalados suportam as próximas versões do OpenShift, ajudando a planejar atualizações de cluster sem quebrar compatibilidade.
4. **Sistema de Cache**: Implementa um cache local (`data/product-lifecycle.json` e `data/csvs-report.json`) para evitar chamadas excessivas à API da Red Hat e acelerar a execução, com tempo de expiração configurável.
5. **Interface Rica e CLI Moderna**: Construída com as bibliotecas `Typer` e `Rich`, apresenta o progresso em tempo real da consulta de cada operador e consolida os resultados em uma tabela colorida no terminal, destacando visualmente os operadores que precisam de atenção.

## Estrutura do Projeto

O projeto adota uma arquitetura modular para facilitar a manutenção e expansão:

```text
op-check/
├── main.py              # Ponto de entrada da CLI (Typer)
├── mapping.yaml         # Dicionário: Nome Operador -> Nome API Red Hat (Apenas para check-upgrade)
├── requirements.txt     # Dependências do projeto
├── data/                # Dados em JSON do ciclo de vida dos operadores por versão do OCP e cache
├── core/
│   ├── k8s_client.py    # Lógica de interação com Kubernetes/OpenShift
│   ├── upgrade_checker.py # Lógica de verificação de compatibilidade para upgrades do OCP
│   └── scanner.py       # Lógica do Scan de suportabilidade consumindo a API v2
└── ui/
    └── formatter.py     # Lógica de formatação visual (Tabelas e Painéis via Rich)
```

## Pré-requisitos

- **Python 3.10** ou superior.
- Acesso a um cluster OpenShift (usuário logado via `oc login` ou com o `~/.kube/config` devidamente configurado).
- Permissão de leitura em recursos customizados (`customresourcedefinitions`, especificamente `subscriptions.operators.coreos.com`).

Para instruções detalhadas de instalação e uso, consulte o arquivo [USAGE.md](USAGE.md).
