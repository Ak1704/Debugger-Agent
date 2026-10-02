FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# --------------------------------------------------
# System dependencies
# --------------------------------------------------

RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    nano \
    dos2unix \
    build-essential \
    ca-certificates \
    bzip2 \
    unzip \
    jq \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Miniconda
# --------------------------------------------------

ENV CONDA_DIR=/opt/conda
ENV PATH=${CONDA_DIR}/bin:$PATH

RUN wget --quiet \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p ${CONDA_DIR} \
    && rm -f /tmp/miniconda.sh \
    && ${CONDA_DIR}/bin/conda clean -afy

RUN conda config --system --set always_yes true \
    && conda config --system --set changeps1 false

# --------------------------------------------------
# BugsInPy++
# --------------------------------------------------

WORKDIR /opt

RUN git clone \
    https://github.com/UNIST-LOFT/BugsInPyPP.git \
    /opt/BugsInPyPP

ENV BUGSINPY_HOME=/opt/BugsInPyPP
ENV PATH=${BUGSINPY_HOME}/framework/bin:${CONDA_DIR}/bin:$PATH

# --------------------------------------------------
# Dataset generator
# --------------------------------------------------

WORKDIR /workspace

COPY dataset_generator /workspace/dataset_generator

RUN chmod +x /workspace/dataset_generator/generator.py

# --------------------------------------------------
# Verify tools
# --------------------------------------------------

RUN python --version
RUN conda --version
RUN bugsinpy-info --help
RUN bugsinpy-checkout --help
RUN bugsinpy-compile --help
RUN bugsinpy-test --help

WORKDIR /workspace

CMD ["bash"]