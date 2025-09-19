FROM httpd:2.4-bookworm

ENV TZ=Europe/Moscow

RUN apt-get update && apt-get install -y openssh-server tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && mkdir /var/run/sshd \
    && rm -rf /var/lib/apt/lists/*

COPY www/index.html /usr/local/apache2/htdocs/index.html

ARG TARGET_USER=webtester

RUN bash -c "useradd -m -s /bin/bash $TARGET_USER \
    && mkdir -p /home/$TARGET_USER/.ssh \
    && chown -R $TARGET_USER:$TARGET_USER /home/$TARGET_USER/.ssh"

# Настройка SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Читаем пароль из секрета и применяем
RUN --mount=type=secret,id=target_password \
    PASS=$(cat /run/secrets/target_password) \
    && echo "${TARGET_USER}:${PASS}" | chpasswd

RUN chown -R root:$TARGET_USER /usr/local/apache2/logs \
    && chmod -R 750 /usr/local/apache2/logs \
    && chmod -R 1777 /tmp

# Настройка ServerName
RUN echo "ServerName localhost:80" >> /usr/local/apache2/conf/httpd.conf

EXPOSE 22 80

CMD echo "Index доступен по http://localhost:80/index.html" && /usr/sbin/sshd -D -e & httpd-foreground
