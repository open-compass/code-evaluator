from flask import Flask, request
import os
import subprocess
import shutil
import re
import json
import argparse
from werkzeug.utils import secure_filename
from inspect import signature

app = Flask(__name__)

def upload_file(request):
    if 'file' not in request.files:
        raise FileNotFoundError("File not found")
        
    file = request.files['file']
    
    # 检查文件是否存在
    if file.filename == '':
        raise FileNotFoundError("File not found")
    
    # 保存文件到本地
    ip_address = request.remote_addr
    filepath = os.path.join('uploads', ip_address, secure_filename(file.filename))
    if not os.path.exists(os.path.join('uploads', ip_address)):
        os.makedirs(os.path.join('uploads', ip_address))
    file.save(filepath)
    return filepath


def check_datasets(dataset):
    if 'humanevalx' in dataset:
        if not re.match("^humanevalx/(python|cpp|js|java|rust|go)$", dataset):
            raise ValueError(f"'{dataset}'" + "not follow the struct of `humanevalx/\{LANGUAGE\}`")
    else:
        raise NotImplementedError(f"{dataset} not implemented...")

def make_cmd(request, eval_filepath):

    dataset = request.form.get('dataset', None)
    kwargs = request.form.to_dict()
    ip_address = request.remote_addr

    if dataset and 'humanevalx' in dataset:
        
        # check dataset
        try:
            check_datasets(dataset) 
        except ValueError as e:
            return {'message':f'dataset name ({dataset}) is wrong.', 'exception': e}, 400
        except NotImplementedError as e:
            return {'message':f'Dataset({dataset}) not supported.', 'exception': e}, 400

        dataset, language = dataset.split("/")
        result_dir = f"outputs/{ip_address}-{dataset}-{language}"
        tmp_dir = f"outputs/{ip_address}-{dataset}-{language}-tmp"
        return [
            'scripts/eval_humanevalx.sh', 
            eval_filepath, 
            language, 
            "-n", '8', 
            "-o", result_dir,
            "-t", tmp_dir], result_dir
    elif 'ds1000' in eval_filepath:
        result_dir = f"outputs/{ip_address}-{eval_filepath}"
        from evals.ds1000.evaluation import evaluation
        kwargs = [
            [f'--{k}', f'{kwargs[k]}']
            for k in signature(evaluation).parameters if k in kwargs
        ]
        kwargs = [item for pair in kwargs for item in pair]
        return [
            'python',
            'evals/ds1000/evaluation.py',
            '--pred_file', eval_filepath,
            '--result_dir', result_dir,
            *kwargs,
        ], result_dir

def _eval(single_request):
    try:
        eval_filepath = upload_file(single_request)
    except Exception as e:
        return {'message': 'Error in upload_file', 'exception': e}, 400

    cmd_items, result_dir = make_cmd(single_request, eval_filepath)
    cmd = ' '.join(cmd_items)
    print("RUN CMD : " + cmd)

    result = subprocess.run(cmd_items, text=True)

    if os.path.exists(os.path.dirname(eval_filepath)):
        shutil.rmtree(os.path.dirname(eval_filepath))
    
    if os.path.exists("tmp"):
        shutil.rmtree("tmp")
    result_file = os.path.join(result_dir, "result.json")
    if os.path.exists(result_file):
        result = dict()
        with open(result_file, "r") as f:
            result = json.dumps(f.read())
        if os.path.exists(os.path.dirname(result_file)):
            shutil.rmtree(os.path.dirname(result_file))
        return result, 200
    else:
        if os.path.exists(os.path.dirname(result_file)):
            shutil.rmtree(os.path.dirname(result_file))
        return {'message': "Eval Error with your result file.", 'exception': 'Failed'}, 400


@app.route('/evaluate', methods=['POST'])
def evaluate():
    result = _eval(request)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This is a simple argument parser")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Port number")
    args = parser.parse_args()
    
    if not os.path.exists("uploads"):
        os.mkdir("uploads")
    if not os.path.exists("outputs"):
        os.mkdir("outputs")

    # In this context, we have deactivated multi-threading and use multi-processing  of 2
    # to prevent excessive CPU load. Overloading the CPU can lead to situations where the
    # run-wait time of certain examples, such as 'go', is deemed unacceptable. This could
    #  ultimately result in lower-than-expected evaluation outcomes.
    # CPU负载过高导致部分样例的运行时长超过限制，最后判定为不通过,
    app.run(debug=True, host="0.0.0.0", port=args.port, threaded=False, processes=2)