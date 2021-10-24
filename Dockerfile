FROM python:3.9.7-slim-buster

ENV \
  # build:
  BUILD_ONLY_PACKAGES='curl' \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    gcc \
    g++ \
    make \
    python3-dev \
    tar \
    wget \
    cmake \
    gfortran \
    ${BUILD_ONLY_PACKAGES} \
  # Poetry
  && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python - \
  && poetry --version \
  # Clean up
  && apt-get remove -y $BUILD_ONLY_PACKAGES \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install ECCodes
RUN wget https://confluence.ecmwf.int/download/attachments/45757960/eccodes-2.23.0-Source.tar.gz
RUN tar -xvzf eccodes-2.23.0-Source.tar.gz
RUN cmake ./eccodes-2.23.0-Source -DCMAKE_INSTALL_PREFIX=/usr/lib/eccodes
RUN make
RUN ctest
RUN make install

WORKDIR /app

COPY ./poetry.lock ./pyproject.toml ./run.py /app/
COPY ./windvisdata /app/windvisdata//

RUN poetry version \
  && poetry install \
  && poetry run pip install -U pip \
  && rm -rf "${POETRY_CACHE_DIR}"
