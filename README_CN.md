# Code Evaluator

[English](./README.md)

一个多语言代码评估工具。

**为何创建此仓库。**

1. **环境集成**：在进行代码评估时，需要预先安装各种环境，例如 Java 需要 JDK，JavaScript 需要 Node，在 DS1000 中需要各版本的 numpy 和 torch 等等。这个项目在 Docker 镜像中预装了所有这些环境。

2. **便于评估**：我们可以通过非常简单的步骤通过此仓库启动服务，然后将结果提交给需要的服务。无需进入 Docker 容器并执行脚本，这可能非常繁琐。

## 📖 支持的数据集

### Humanevalx

HumanEval-X 是用于评估代码生成模型的多语言能力的基准测试。它由 820 个高质量人工制作的数据样本（每个样本都有测试案例）组成，包括 **Python**、**C++**、**Java**、**JavaScript** 和 **Go**，可用于各种任务，如代码生成和翻译。

[论文链接](https://arxiv.org/abs/2303.17568)   &nbsp;  [Github 仓库](https://github.com/THUDM/CodeGeeX2)  &nbsp;  [Huggingface](https://huggingface.co/datasets/THUDM/humaneval-x)

## 🛠️ 评估环境

评估所生成的代码需要在多种语言中进行编译和执行。我们依赖的编程语言的版本以及使用的包如下：

| 依赖项    | 版本           |
| ------- | ------------ |
| Python  | 3.8.12       |
| JDK     | 18.0.2.1     |
| Node.js | 16.14.0      |
| js-md5  | 0.7.3        |
| C++     | 11           |
| g++     | 7.5.0        |
| Boost   | 1.71.0       |
| OpenSSL | 3.0.0        |
| go      | 1.18.4       |

## 👨‍🏫 如何使用

### 1. 启动一个服务

确保您已经安装了 docker，然后构建一个镜像并运行一个容器服务。

构建 Docker 镜像：

选择你的数据集: `humanevalx` or `ds1000`

```shell
git clone https://github.com/open-compass/code-evaluator.git
sudo docker build -t code-eval-{your-dataset}:latest -f docker/{your-dataset}/Dockerfile .
```

获取镜像后，使用以下命令创建容器：

```shell
# 输出日志格式
sudo docker run -it -p 5000:5000 code-eval:latest python server.py

# 在后台运行程序
# sudo docker run -itd -p 5000:5000 code-eval:latest python server.py

# 使用不同的端口
# sudo docker run -itd -p 5001:5001 code-eval:latest python server.py --port 5001
```

确保您能够访问服务，检查以下命令(如果在本地主机中运行服务，就跳过这个操作)：

```shell
ping your_service_ip_address
telnet your_service_ip_address your_service_port
```

### 2. 准备提交结果文件

### humanevalx

我们在 [examples](./examples/) 文件夹中给出了不同数据集的样本格式。

以 huamanevalx 为例，其提交结果的格式如下：

```text
{"task_id": "../..", "generation: "..."}
{"task_id": "../..", "generation: "..."}
...
```

### ds1000

Skip this step, use prediction by opencompass directly.

### 3. 提交服务请求

使用 curl 提交你的请求

```shell
curl -X POST -F 'file=@{result_absolute_path}' -F 'dataset={dataset/language}' {your_service_ip_address}:{your_service_port}/evaluate
```

比如在 'localhost:5000' 上评估 'humanevalx/python'：

```shell
curl -X POST -F 'file=@./examples/humanevalx/python.json' -F 'dataset=humanevalx/python' localhost:5000/evaluate
```

你将得到以下结果：

```text
"{\"pass@1\": 37.19512195121951}"% 
```

比如在 'localhost:5000' 上评估 ds1000_Numpy :

```shell
curl -X POST -F 'file=@./internlm-chat-7b-hf-v11/ds1000_Numpy.json' localhost:5000/evaluate
```

你将得到以下结果：

```text
"{\"accuracy\": xx}"%
```


## 🤝 致谢

该项目中的部分代码引用和修改自 [CodeGeeX2](https://github.com/THUDM/CodeGeeX2)。感谢 [THUDM 团队](https://github.com/THUDM)。
