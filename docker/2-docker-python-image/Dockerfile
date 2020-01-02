FROM python:alpine3.8

ADD requirements.txt /
ADD transaction_main.py /
ADD transaction_retry.py /
ADD watch_transactions.py /

# Install any needed packages specified in requirements.txt
RUN apk --update add --no-cache --virtual .build-deps gcc linux-headers musl-dev && \
    pip install --upgrade pip && \
    pip install --trusted-host pypi.python.org -r ./requirements.txt && \
    apk del .build-deps

ENTRYPOINT ["python", "-u"]
