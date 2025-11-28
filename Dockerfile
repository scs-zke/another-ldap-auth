FROM python:3.13.9-alpine3.22 AS builder

RUN apk --update --no-cache add \
        build-base \
        openldap-dev \
        libffi-dev && \
    rm -rf /var/cache/apk/*

COPY src/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade --no-cache-dir pip setuptools && \
    pip install --upgrade --no-cache-dir -r /tmp/requirements.txt

COPY src/ /app

FROM python:3.13.9-alpine3.22

RUN apk --update --no-cache add \
        openldap-dev && \
    rm -rf /var/cache/apk/*

ENV USER=aldap
ENV UID=10001
ENV GROUP=aldap
ENV GID=10001
ENV HOME=/home/$USER
ENV PORT=9000
RUN addgroup -g $GID -S $GROUP && adduser -u $UID -S $USER -G $GROUP

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /app $HOME/

RUN chown -R $USER:$GROUP $HOME

EXPOSE $PORT

USER $UID:$GID
WORKDIR $HOME

CMD ["python3", "-u", "main.py"]