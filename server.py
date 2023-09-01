from flask import Flask, request, g
import os
import subprocess
import shutil
import re
import json
import argparse
from werkzeug.utils import secure_filename

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

def make_cmd(eval_filepath, dataset, ip_address, with_prompt):
    if 'humanevalx' in dataset:
        dataset, language = dataset.split("/")
        result_dir = f"outputs/{ip_address}-{dataset}-{language}"
        tmp_dir = f"outputs/{ip_address}-{dataset}-{language}-tmp"
        return [
            'scripts/eval_humanevalx.sh', 
            eval_filepath, 
            language, 
            "-n", '8', 
            "-p", f"{with_prompt}", 
            "-o", result_dir,
            "-t", tmp_dir], result_dir

def _eval(single_request):
    try:
        eval_filepath = upload_file(single_request)
    except Exception as e:
        return {'message': 'Error in upload_file', 'exception': e}, 400
    
    dataset = single_request.form.get('dataset')
    ip_address = single_request.remote_addr
    if 'With-Prompt' in single_request.headers:
        with_prompt = single_request.headers['With-Prompt']
    else:
        with_prompt = True
    try:
        check_datasets(dataset) 
    except ValueError as e:
        return {'message':f'dataset name ({dataset}) is wrong.', 'exception': e}, 400
    except NotImplementedError as e:
        return {'message':f'Dataset({dataset}) not supported.', 'exception': e}, 400

    cmd_items, result_dir = make_cmd(eval_filepath, dataset, ip_address, with_prompt)
    print("RUN CMD : " + " ".join(cmd_items))

    result = subprocess.run(cmd_items, capture_output=True, text=True)

    if os.path.exists(os.path.dirname(eval_filepath)):
        shutil.rmtree(os.path.dirname(eval_filepath))
    
    if os.path.exists("tmp"):
        shutil.rmtree("tmp")
    resilt_file = os.path.join(result_dir, "result.json")
    if 'Evaluation finished.' in result.stdout and os.path.exists(resilt_file):
        result = dict()
        with open(resilt_file, "r") as f:
            result = json.dumps(f.read())
        if os.path.exists(os.path.dirname(resilt_file)):
            shutil.rmtree(os.path.dirname(resilt_file))
        return result, 200
    else:
        if os.path.exists(os.path.dirname(resilt_file)):
            shutil.rmtree(os.path.dirname(resilt_file))
        return {'message': "Eval Error with your result file.", 'stderr': result.stderr}, 400


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