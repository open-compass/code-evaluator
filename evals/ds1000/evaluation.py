import configparser
import importlib
import os
import pickle
import re
import shutil
import signal
import sys
import tempfile
import threading
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Optional, Union
import json
from postprocess import ds1000_matplotlib_postprocess, ds1000_postprocess
from functools import partial
import fire

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def score_single(raw_pred, pred, refer, dataset_path, debug=None):
    if debug == 'full':
        debug_flag = 7
    elif debug == 'half':
        debug_flag = 3
    elif debug == 'error':
        debug_flag = 1
    elif debug:
        raise ValueError(f'Debug type {debug} is not supported. Use `full`, '
                        '`half`, `error` or None.')
    else:
        debug_flag = 0

    # get current dir because we will enter a temp dir to
    # execute generated code
    cwd = os.getcwd()

    def chdir_return(cwd, return_value):
        os.chdir(cwd)
        return return_value

    # join path for dataset in folder
    problem_path = os.path.join(dataset_path, refer['problem_path'].split('ds1000_data/')[-1])

    # we create a tempdir to execute each generated program
    with tempfile.TemporaryDirectory() as tempdir_name:

        tempdir_name = Path(tempdir_name)
        # copy all files and data dependencies from
        copytree(problem_path, tempdir_name)
        # generated outputs will be put into `result`
        os.mkdir(tempdir_name / 'result')

        program = refer['code_context'].replace('[insert]', pred)
        with open(tempdir_name / 'program.py', 'w', encoding='UTF-8') as f:
            f.write(program)

        # enter into the tempdir to execute
        os.chdir(tempdir_name)

        execution_status = []
        # a question may not have test case but we can still execute and
        # see if there is error
        test_cnt = max(1, int(refer['test_case_cnt']))
        for i in range(1, test_cnt + 1):
            # notice this command, e.g., you may need to
            # replace `python` with `python3`
            cmd_text = f'python program.py --test_case {i}'
            time_limit = 60  # should not change the official time_limit
            cmd = Command(cmd_text, )
            exit_code = cmd.run(timeout=time_limit)  # 0 if there is no error
            if exit_code and debug_flag:
                print(f"#################### Example {refer['problem_path']}")
                if debug_flag >> 2:
                    # Print all extra info
                    print('---------------------Raw Prediction')
                    print(raw_pred)
                    print('---------------------Processed Prediction')
                    print(pred)
                if debug_flag >> 1:
                    print('---------------------Running Code')
                    print(program)
                if debug_flag:
                    print('---------------------Error Massage')
                    print(cmd.stderr)
            execution_status.append(exit_code)

        # return if execution error
        if sum(execution_status) > 0:
            return chdir_return(cwd, False)

        # loading testing code as a module
        test_module = import_source_file(tempdir_name / 'test_code.py',
                                            'test_code')
        pass_flag = True

        if int(refer['test_type']) == 3:
            # stringTest parses the generated code into AST
            # and check AST components
            # if there is static error, stringTest may raise an exception
            pred = pred.split('\n')
            for line in pred:
                if 'print' in line and '#' not in line.split('print'):
                    pred.remove(line)
            pred = '\n'.join(pred)
            try:
                pass_flag = test_module.stringTest(pred)
            except Exception:
                # return False if stringTest error
                return chdir_return(cwd, False)

        test_cnt = max(int(refer['test_case_cnt']), 1)
        for i in range(1, test_cnt + 1):
            try:
                ans = pickle.load(open(f'ans/ans{i}.pkl', 'rb'))
                # loading the generated output might still raise Exception
                # if the generated code is not correct
                result = pickle.load(open(f'result/result_{i}.pkl', 'rb'))
                pass_flag = test_module.test(result, ans) == 1
            except Exception:
                # return False if stringTest error
                return chdir_return(cwd, False)

    return chdir_return(cwd, pass_flag)


def evaluation(pred_file, dataset_path='./ds1000_data/', result_dir= None, debug=None, num_workers=16):
    # load preds and refers
    with open(pred_file, 'r') as f:
        file_content = json.load(f)
        raw_preds = [value['prediction'] for value in file_content.values()]
        refers = [value['gold'] for value in file_content.values()]

    # post proprocessing
    if 'Matplotlib' in pred_file:
        preds = [ds1000_matplotlib_postprocess(pred) for pred in raw_preds]
    else:
        preds = [ds1000_postprocess(pred) for pred in raw_preds]

    score_single_partial = partial(score_single, dataset_path=dataset_path, debug=debug)
    # Each process changes cwd, need to use multi-processing
    with ProcessPoolExecutor(num_workers) as executor:
        passed = sum(
            list(executor.map(score_single_partial, raw_preds, preds, refers)))

    total = len(preds)

    # create dir if not exists
    if result_dir is not None:
        os.makedirs(result_dir, exist_ok=True)
    out_result_file = os.path.join(result_dir, "result.json")
    with open(out_result_file, "w") as f:
        print(pred_file, f'Accuracy: {round(passed / total * 100, 2)}')
        f.write(json.dumps({'accuracy': round(passed / total * 100, 2)}))


class Command(object):
    """This object takes in command and executes it with time out."""

    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):

        def target():
            # Check if in Windows https://stackoverflow.com/questions/1325581/how-do-i-check-if-im-running-on-windows-in-python  # noqa
            if os.name == 'nt':
                self.process = Popen(self.cmd,
                                     shell=True,
                                     stdout=PIPE,
                                     stderr=PIPE)
            else:
                self.process = Popen(self.cmd,
                                     shell=True,
                                     stdout=PIPE,
                                     stderr=PIPE,
                                     preexec_fn=os.setsid)
            stdout, stderr = self.process.communicate()
            self.stdout = stdout.decode()
            self.stderr = stderr.decode()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            # Check if in Windows https://stackoverflow.com/questions/1325581/how-do-i-check-if-im-running-on-windows-in-python  # noqa
            if os.name == 'nt':
                Popen('TASKKILL /F /PID {pid} /T'.format(pid=self.process.pid))
            else:
                os.killpg(self.process.pid, signal.SIGTERM)
            thread.join()
        return self.process.returncode


def import_source_file(fname, modname):
    """Import a Python source file and return the loaded module.

    Args:
        fname: The full path to the source file.  It may container characters
            like `.` or `-`.
        modname: The name for the loaded module.  It may contain `.` and even
            characters that would normally not be allowed (e.g., `-`).
    Return:
        The imported module

    Raises:
        ImportError: If the file cannot be imported (e.g, if it's not a `.py`
            file or if it does not exist).
        Exception: Any exception that is raised while executing the module
            (e.g. :exc:`SyntaxError).
            These are errors made by the author of the module!
    """
    # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    spec = importlib.util.spec_from_file_location(modname, fname)
    if spec is None:
        raise ImportError(
            f"Could not load spec for module '{modname}' at: {fname}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError as e:
        raise ImportError(f'{e.strerror}: {fname}') from e
    return module


def main():
    fire.Fire(evaluation)


if __name__ == "__main__":
    sys.exit(main())
