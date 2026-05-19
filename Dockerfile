FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace/src

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        latexmk \
        lmodern \
        octave \
        octave-io \
        octave-statistics \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-latex-recommended \
        texlive-pictures \
        texlive-science \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

COPY . /workspace
RUN pip install -e .

EXPOSE 8888 8080

CMD ["bash"]
