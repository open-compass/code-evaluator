# Code Evaluator

[中文](./README_CN.md)

A multi-language code evaluation tool.

**Why create this repo.**

1. **Environment integration**: When evaluating code, various environments need to be pre-installed, such as JDK for Java, Node for JavaScript, various versions of numpy and torch in DS1000, etc. This project pre-installs all these environments in a Docker image.

2. **Easy to evaluate**: We can start the service through this repo with very simple steps, and then submit the results to the desired service. There's no need to go into the Docker container and execute the script, which can be quite cumbersome.

## 📄 Table of Contents

- [Support Datasets](#-support-datasets-)
- [Evaluation Environments](#-evaluation-environments-)
- [How to use](#-how-to-use-)
- [Acknowledgement](#-acknowledgement-)

## 📖 Support Datasets&Language

### Humanevalx

HumanEval-X is a benchmark for evaluating the multilingual ability of code generative models. It consists of 820 high-quality human-crafted data samples (each with test cases) in **Python**, **C++**, **Java**, **JavaScript**, and **Go**, and can be used for various tasks, such as code generation and translation.

[paper link](https://arxiv.org/abs/2303.17568)   &nbsp;  [Github repo](https://github.com/THUDM/CodeGeeX2)  &nbsp;  [Huggingface](https://huggingface.co/datasets/THUDM/humaneval-x)

## 🛠️ Evaluation Environments

The generated code for evaluation requires compilation and execution in multiple languages. The versions of the programming languages we depend on, as well as the packages used are as follows:

| Dependencies | Version |
| ------- | -------- |
| Python  | 3.8.12   |
| JDK     | 18.0.2.1 |
| Node.js | 16.14.0  |
| js-md5  | 0.7.3    |
| C++     | 11       |
| g++     | 7.5.0    |
| Boost   | 1.71.0   |
| OpenSSL | 3.0.0    |
| go      | 1.18.4   |

## 👨‍🏫 How to use

### 1. Launch a service

Make sure you have install docker, and then build a image and run a service of container.

build Docker Image:

Choose your dataset: `humanevalx` or `ds1000`

```shell
git clone https://github.com/open-compass/code-evaluator.git
sudo docker build -t code-eval-{your-dataset}:latest -f docker/{your-dataset}/Dockerfile .
```

After getting the image, use the following command to create the container:

```shell
# Output Log Format
sudo docker run -it -p 5000:5000 code-eval:latest python server.py

# Running programs in the background
# sudo docker run -itd -p 5000:5000 code-eval:latest python server.py

# use differnet port
# sudo docker run -itd -p 5001:5001 code-eval:latest python server.py --port 5001
```

Make sure you can reach the service by checking the fllowing commands(If you run service in the loaclhost, just skip this.):

```shell
ping your_service_ip_address
telnet your_service_ip_address your_service_port
```

### 2. Prepare submit result files


### humanevalx
We give sample formats for different datasets in the [examples](./examples/) folder.

Let's take huamanevalx as an example，which submits results in the following format：

```text
{"task_id": "../..", "generation: "..."}
{"task_id": "../..", "generation: "..."}
...
```

### ds1000

Skip this step, use prediction by opencompass directly.

### 3. Submit service request

Use curl to submit your request

```shell
curl -X POST -F 'file=@{result_absolute_path}' -F 'dataset={dataset/language}' {your_service_ip_address}:{your_service_port}/evaluate
```

such as evaluate 'humanevalx/python' in 'localhost:5000':

```shell
curl -X POST -F 'file=@./examples/humanevalx/python.json' -F 'dataset=humanevalx/python' localhost:5000/evaluate
```

You will get the fllowing result：

```text
"{\"pass@1\": 37.19512195121951}"% 
```

such as evaluate 'ds1000_Numpy' in 'localhost:5000':

```shell
curl -X POST -F 'file=@./internlm-chat-7b-hf-v11/ds1000_Numpy.json' localhost:5000/evaluate
```

You will get the fllowing result：

```text
"{\"accuracy\": xx}"%
```

## 🤝 Acknowledgements

Some code in this project is cited and modified from [CodeGeeX2](https://github.com/THUDM/CodeGeeX2). Thanks for [THUDM Team](https://github.com/THUDM).
