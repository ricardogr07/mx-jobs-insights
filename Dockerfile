FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos "" appuser

COPY pyproject.toml README.md LICENSE mkdocs.yml tox.toml ./
COPY src ./src
COPY docs ./docs
COPY scripts ./scripts
COPY configs ./configs

RUN python -m pip install --upgrade pip \
    && python -m pip install .[cloud,docs]

USER appuser

ENTRYPOINT ["python", "-m", "mexico_linkedin_jobs_portfolio.interfaces.cli.main", "pipeline"]
