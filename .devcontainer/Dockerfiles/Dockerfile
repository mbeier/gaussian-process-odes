# FROM nvidia/cuda:12.3.0-devel-ubuntu22.04
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive 
ARG USER_NAME=me
ARG USER_GECOS=me
ARG USER_ID=1000
ARG USER_HOME="/home/$USER_NAME"
ARG PIP_INSTALL="pip install --no-cache" 
ARG PYTHON="python3.8"
### install basics
RUN apt-get update
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    vim \
    git \
    ${PYTHON}-venv \
    cm-super \
    dvipng \
    adduser \
    wget \
    pipx 
# matplotlib latex rendering
RUN pipx ensurepath
RUN ln /bin/${PYTHON} /bin/python
### switch to non root
RUN adduser \
    --home "$USER_HOME" \
    --uid $USER_ID \
    --gecos "$USER_GECOS" \
    --disabled-password \
    "$USER_NAME"
USER ${USER_NAME}
WORKDIR "/workspaces/gaussian-process-odes"

### install pypi libraries
RUN pipx install poetry
# RUN source "${WORKDIR}/.venv/bin/activate"
# ENV PATH="${WORKDIR}/.venv/bin:$PATH"


# ENV GITLAB_TOKEN="gldt-_E_3YehZvnp6Ficj7jkf"
# ENV GITLAB_TOKEN_USER="container"
# ENV DATA_DIR="/workspaces/gaussian-process-odes/data"
# RUN ${PIP_INSTALL} --no-deps git+https://${GITLAB_TOKEN_USER}:${GITLAB_TOKEN}@gitlab.lrz.de/MaxBeier/KKR.git@icml
