# DevOps Infrastructure Repository

[![CI](https://github.com/temarmelade/devops-infrastructure/actions/workflows/ci.yml/badge.svg)](https://github.com/temarmelade/devops-infrastructure/actions/workflows/ci.yml)

Учебный DevOps-репозиторий: небольшое веб-приложение и вся инфраструктура вокруг него как код —
контейнер, Terraform, Kubernetes, Ansible, мониторинг и CI на GitHub Actions.

## Компоненты

| Компонент | Инструмент | Где лежит |
|-----------|------------|-----------|
| Приложение | Python 3.12 (stdlib), эндпоинты `/`, `/health`, `/metrics` | `app/`, `tests/` |
| Контейнер | Docker, non-root, HEALTHCHECK | `docker/Dockerfile` |
| CI | GitHub Actions: 7 проверок на каждый PR | `.github/workflows/ci.yml` |

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

### Docker

```bash
docker build -f docker/Dockerfile -t devops-app:1.0.0 .
docker run -d --name devops-app -p 8080:8080 devops-app:1.0.0
curl http://localhost:8080/health      # {"status": "ok"}
curl http://localhost:8080/metrics     # метрики Prometheus
```

Тесты приложения: `python -m unittest discover -s tests -t . -v`

## CI/CD

Workflow `.github/workflows/ci.yml` запускается на каждый Pull Request и push в `main`:

| Job | Что проверяет |
|-----|---------------|
| Lint YAML | `yamllint --strict` по всему репозиторию |
| Unit tests | тесты приложения |
| Docker build and smoke test | сборка образа, запуск контейнера, проверка `/health` |
| Terraform validate | `terraform fmt -check`, `init`, `validate` |
| Validate Kubernetes manifests | `kubeconform -strict` |
| Ansible syntax check | `ansible-playbook --syntax-check` |
| Validate Prometheus config | `promtool check config` (вместе с правилами алертов) |
