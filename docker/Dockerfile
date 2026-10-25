# Build from the repository root:
#   docker build -f docker/Dockerfile -t devops-app:local .
FROM python:3.12-slim

LABEL org.opencontainers.image.title="devops-app" \
      org.opencontainers.image.description="Demo service for the DevOps infrastructure repository"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=8080

WORKDIR /srv

# Run as an unprivileged user
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home app

COPY app/ ./app/

# Numeric UID so Kubernetes can verify runAsNonRoot
USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2).status == 200 else 1)"

CMD ["python", "-m", "app.main"]
