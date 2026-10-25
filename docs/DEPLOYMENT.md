# Руководство по развёртыванию

Документ описывает, как развернуть `devops-app` четырьмя способами, как обновить версию
и как откатиться. Все команды выполняются из корня репозитория.

## 0. Подготовка

| Инструмент | Версия | Зачем |
|------------|--------|-------|
| Docker | 24+ | сборка и запуск образа |
| Terraform | 1.5+ | способ 2 |
| kubectl + kind или minikube | 1.28+ | способ 3 |
| Ansible | 2.15+ | способ 4 |

Сборка образа (нужна для способов 1 и 3):

```bash
docker build -f docker/Dockerfile -t devops-app:1.0.0 .
```

Проверка работоспособности в любом способе:

```bash
curl -f http://localhost:8080/health   # {"status": "ok"}
```

## 1. Docker (локально)

```bash
docker run -d --name devops-app --restart unless-stopped \
  -p 8080:8080 -e APP_ENV=dev -e APP_VERSION=1.0.0 devops-app:1.0.0
docker ps --filter name=devops-app      # STATUS должен стать (healthy)
```

Остановка: `docker rm -f devops-app`.

## 2. Terraform (Docker provider)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
terraform output app_urls
```

- Количество контейнеров задаёт `replicas`, порты публикуются начиная с `app_port`.
- State хранится локально (`terraform.tfstate`, в `.gitignore`). Для команды стоит вынести
  state в удалённый backend (S3 / Terraform Cloud) с блокировкой.
- Удаление: `terraform destroy`.

## 3. Kubernetes

```bash
kind create cluster --name devops
kind load docker-image devops-app:1.0.0 --name devops
kubectl apply -f kubernetes/
kubectl rollout status deployment/devops-app --timeout=120s
kubectl get pods -l app.kubernetes.io/name=devops-app
kubectl port-forward svc/devops-app 8080:80
```

Для minikube вместо `kind load` выполните `minikube image load devops-app:1.0.0`.
Service типа NodePort также доступен на порту `30080` узла.

## 4. Ansible (удалённый сервер Ubuntu/Debian)

1. Впишите адрес и пользователя в `ansible/inventory.ini`.
2. Проверьте доступ: `ansible -i ansible/inventory.ini app_servers -m ping`.
3. Запустите:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

Playbook идемпотентен: повторный запуск без изменений в коде ничего не перезапускает.

## 5. Мониторинг

```bash
docker network create monitoring
docker run -d --name app --network monitoring devops-app:1.0.0
docker run -d --name prometheus --network monitoring -p 9090:9090 \
  -v "$PWD/monitoring:/etc/prometheus" prom/prometheus:v2.53.0
```

Откройте http://localhost:9090 → Status → Targets: цель `devops-app` должна быть `UP`.
В Kubernetes поды обнаруживаются автоматически по аннотации `prometheus.io/scrape: "true"`.

## Обновление версии

1. Измените код через feature-ветку и Pull Request; дождитесь зелёного CI.
2. Соберите образ с новым тегом: `docker build -f docker/Dockerfile -t devops-app:1.1.0 .`
3. Разверните:
   - Terraform: `terraform apply -var image_tag=1.1.0`
   - Kubernetes: `kubectl set image deployment/devops-app app=devops-app:1.1.0` (RollingUpdate без простоя)
   - Ansible: поменяйте `app_version` и запустите playbook.

## Откат

- Kubernetes: `kubectl rollout undo deployment/devops-app`
- Terraform: `terraform apply -var image_tag=<предыдущий тег>`
- Docker: `docker rm -f devops-app` и запуск предыдущего тега.

## Типичные проблемы

| Симптом | Причина и решение |
|---------|-------------------|
| `ErrImageNeverPull` / `ImagePullBackOff` | образ не загружен в кластер: `kind load docker-image ...` |
| Pod в `CrashLoopBackOff` | `kubectl logs deploy/devops-app`; проверьте, что порт 8080 свободен в контейнере |
| Terraform: `Cannot connect to the Docker daemon` | запустите Docker или задайте переменную `docker_host` |
| Target в Prometheus `DOWN` | контейнеры должны быть в одной сети `monitoring`, имя контейнера — `app` |
