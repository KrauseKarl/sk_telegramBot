FROM python:3.12-slim


WORKDIR /app
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get -y install python3-dev musl-dev build-essential libpq-dev postgresql gcc postgresql-client  nano net-tools
RUN rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TZ=Asia/Yekaterinburg
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["python", "main.py", "localhost", "8000"]