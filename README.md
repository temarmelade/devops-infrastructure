# DevOps Infrastructure Repository

[![CI](https://github.com/temarmelade/devops-infrastructure/actions/workflows/ci.yml/badge.svg)](https://github.com/temarmelade/devops-infrastructure/actions/workflows/ci.yml)

Учебный DevOps-репозиторий: небольшое веб-приложение и вся инфраструктура вокруг него как код —
контейнер, Terraform, Kubernetes, Ansible, мониторинг и CI на GitHub Actions.

## Компоненты

| Компонент | Инструмент | Где лежит |
|-----------|------------|-----------|
| Приложение | Python 3.12 (stdlib), эндпоинты `/`, `/health`, `/metrics` | `app/`, `tests/` |
| Контейнер | Docker, non-root, HEALTHCHECK | `docker/Dockerfile` |
| Инфраструктура как код | Terraform + провайдер `kreuzwerker/docker` | `terraform/` |
| Оркестрация | Kubernetes: Deployment (2 реплики, probes, limits) + Service | `kubernetes/` |
| Конфигурация серверов | Ansible playbook | `ansible/` |
| Мониторинг | Prometheus: scrape-конфиг и алерты | `monitoring/` |
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

### Terraform

Terraform собирает образ из `docker/Dockerfile` и запускает контейнеры в отдельной сети.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # при необходимости поправьте значения
terraform init
terraform plan
terraform apply
terraform output app_urls
terraform destroy                              # удалить всё
```

Основные переменные: `environment` (dev/staging/prod), `image_tag`, `app_port`, `replicas` (1–5).

### Kubernetes

```bash
kind create cluster --name devops                 # или minikube start
docker build -f docker/Dockerfile -t devops-app:1.0.0 .
kind load docker-image devops-app:1.0.0 --name devops
kubectl apply -f kubernetes/
kubectl rollout status deployment/devops-app
kubectl port-forward svc/devops-app 8080:80
```

Deployment: 2 реплики, RollingUpdate без простоя, readiness/liveness probes на `/health`,
requests/limits, запуск от non-root с read-only файловой системой.

### Ansible

```bash
# впишите адрес сервера в ansible/inventory.ini
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

Playbook ставит Docker, забирает код из этого репозитория, собирает образ, запускает контейнер
и ждёт, пока `/health` ответит 200.

### Мониторинг

```bash
docker network create monitoring
docker run -d --name app --network monitoring devops-app:1.0.0
docker run -d --name prometheus --network monitoring -p 9090:9090 \
  -v "$PWD/monitoring:/etc/prometheus" prom/prometheus:v2.53.0
```

Prometheus доступен на http://localhost:9090. Алерты: `AppDown` (приложение недоступно > 1 мин)
и `AppHigh404Rate`.

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

## Развёртывание

Пошаговая инструкция для всех способов (Docker, Terraform, Kubernetes, Ansible), обновление
и откат — в [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Git workflow

- `main` — стабильная ветка, защищена: изменения только через Pull Request, все 7 проверок CI должны пройти.
- Работа ведётся в feature-ветках: `feature/ci-pipeline`, `feature/docker-app`, `feature/terraform-infra`,
  `feature/kubernetes-manifests`, `feature/ansible-monitoring`.
- Коммиты в стиле [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `ci:`, `test:`, `chore:`.
- PR оформляются по шаблону `.github/pull_request_template.md`: описание, список изменений, как проверено.
- Пример разрешённого конфликта: ветки Terraform и Kubernetes одновременно меняли README;
  конфликт разрешён в коммите `merge: resolve README conflict ...` в `feature/kubernetes-manifests`.
