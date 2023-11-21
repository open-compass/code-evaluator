# 使用 Python 3.7.10 镜像作为基础镜像
FROM python:3.7.10

RUN mkdir -p /workspace/code-evaluator
WORKDIR /workspace/code-evaluator/

RUN wget https://github.com/HKUNLP/DS-1000/raw/main/ds1000_data.zip \
    && unzip ds1000_data.zip

COPY requirements requirements

# 安装 requirements.txt 中指定的任何依赖项
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install -r requirements/ds1000.txt

RUN pip install fire
RUN pip install flask
COPY . .
