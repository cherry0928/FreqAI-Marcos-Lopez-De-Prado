FROM python:3.10.11-slim-bullseye as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PATH=/home/ftuser/.local/bin:$PATH
ENV FT_APP_ENV="docker"

# Prepare environment
RUN mkdir /freqtrade \
  && apt-get update \
  && apt-get -y install sudo libatlas3-base curl sqlite3 libhdf5-serial-dev libgomp1 wget\
  && apt-get clean \
  && useradd -u 1000 -G sudo -U -m -s /bin/bash ftuser \
  && chown ftuser:ftuser /freqtrade \
  # Allow sudoers
  && echo "ftuser ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

WORKDIR /freqtrade

# Install dependencies
FROM base as python-deps
RUN  apt-get update \
  && apt-get -y install build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc \
  && apt-get clean \
  && pip install --upgrade pip==23.0.1 wheel==0.38.4

# Install TA-lib
COPY build_helpers/* /tmp/
COPY * /freqtrade/
RUN cd /tmp && /tmp/install_ta-lib.sh && rm -r /tmp/*ta-lib*
ENV LD_LIBRARY_PATH /usr/local/lib

# Install dependencies
COPY --chown=ftuser:ftuser requirements.txt requirements-hyperopt.txt /freqtrade/
USER ftuser
RUN  pip install --user --no-cache-dir numpy \
  && pip install --user --no-cache-dir -r requirements-hyperopt.txt

# Copy dependencies to runtime-image
FROM base as runtime-image
COPY --from=python-deps /usr/local/lib /usr/local/lib
ENV LD_LIBRARY_PATH /usr/local/lib

COPY --from=python-deps --chown=ftuser:ftuser /home/ftuser/.local /home/ftuser/.local

USER ftuser
# Install and execute
COPY --chown=ftuser:ftuser . /freqtrade/

RUN pip install -e . --user --no-cache-dir --no-build-isolation \
  && mkdir /freqtrade/user_data/ \
  && freqtrade install-ui \
  && wget https://raw.githubusercontent.com/cherry0928/FreqAI-Marcos-Lopez-De-Prado/litmus-ai/user_data/config.json \
  # && wget https://raw.githubusercontent.com/cherry0928/FreqAI-Marcos-Lopez-De-Prado/litmus-ai/user_data/strategies/Zeus.py \
  # && wget https://raw.githubusercontent.com/cherry0928/FreqAI-Marcos-Lopez-De-Prado/litmus-ai/user_data/strategies/Zeus.json \
  && mv config.json /freqtrade/user_data/config.json 
  # && mv Zeus.py /freqtrade/user_data/strategies/Zeus.py \
  # && mv Zeus.json /freqtrade/user_data/strategies/Zeus.json

ENTRYPOINT ["freqtrade"]
# Default to trade mode
# CMD [ "trade", "-s", "Zeus", "--freqaimodel", "LightGBMRegressor" ]
CMD ["trade"]
