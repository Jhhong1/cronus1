FROM python:3.6.11-alpine3.12

ARG USER=cronus
ENV HOME /$USER

WORKDIR $HOME

COPY . $HOME

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && apk --no-cache --update add sudo vim curl sshpass procps net-tools nginx bash chromium-chromedriver chromium firefox-esr ttf-dejavu mariadb-connector-c-dev zlib-dev jpeg-dev openjpeg-dev \
    && apk add fontconfig mkfontscale wqy-zenhei --update-cache --repository http://mirrors.aliyun.com/alpine/edge/testing --allow-untrusted \
    && apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk --no-cache --update add --virtual .build-deps openssl-dev gcc libffi-dev libc-dev linux-headers musl-dev \
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-linux64.tar.gz \
    && tar -zxvf geckodriver-v0.27.0-linux64.tar.gz -C /usr/local/bin/ \
    && rm -f geckodriver-v0.27.0-linux64.tar.gz \
    && python -m pip install --upgrade pip --timeout 100 \
    && pip install -r $HOME/requirements.txt --timeout 200 \
    && mkdir -p /cronus/logs/ \
    && adduser -D $USER \
    && echo "$USER ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$USER \
    && chmod 0440 /etc/sudoers.d/$USER \
    && chown -R $USER:$USER $HOME \
    && apk del .build-deps \
    && apk del tzdata \
    && rm -rf /var/cache/apk/*

USER $USER

EXPOSE 8081
CMD ["/bin/bash", "run_django.sh"]