FROM python:3.10
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && pip3 install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
