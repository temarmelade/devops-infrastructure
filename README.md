# DevOps Infrastructure Repository

Учебный DevOps-репозиторий: небольшое веб-приложение и вся инфраструктура вокруг него как код —
контейнер, Terraform, Kubernetes, Ansible, мониторинг и CI на GitHub Actions.

## Компоненты

| Компонент | Инструмент | Где лежит |
|-----------|------------|-----------|
| — | Компоненты добавляются через feature-ветки и Pull Request'ы | — |

## Структура репозитория

```
.
├── app/                    # приложение (Python, без зависимостей)
├── tests/                  # unit-тесты
├── docker/
│   └── Dockerfile
├── terraform/
│   ├── main.tf             # образ, сеть и контейнеры через Docker provider
│   ├── variables.tf        # входные переменные с валидацией
│   └── terraform.tfvars.example
├── ansible/
│   ├── playbook.yml        # установка Docker и деплой приложения на сервер
│   └── inventory.ini
├── kubernetes/
│   ├── deployment.yaml
│   └── service.yaml
├── monitoring/
│   ├── prometheus.yml
│   └── alerts.yml
├── docs/
│   └── DEPLOYMENT.md       # подробная инструкция по развёртыванию
├── .github/
│   ├── workflows/ci.yml
│   └── pull_request_template.md
├── .gitignore
├── .dockerignore
├── .yamllint.yml
└── README.md
```

## Быстрый старт

Требования: Git, Docker; для отдельных частей — Terraform ≥ 1.5, kubectl + kind/minikube, Ansible ≥ 2.15.

```bash
git clone https://github.com/temarmelade/devops-infrastructure.git
cd devops-infrastructure
```
