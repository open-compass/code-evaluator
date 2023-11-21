import re


def ds1000_postprocess(text: str) -> str:
    match = re.search('<code>(.*?)</code>', text, re.DOTALL)
    if match:
        text = match.group(1)

    match = re.search('(.*?)</code>', text, re.DOTALL)
    if match:
        text = match.group(1)

    match = re.search('```python(.*?)```', text, re.DOTALL)
    if match:
        text = match.group(1)

    match = re.search('```(.*?)```', text, re.DOTALL)
    if match:
        text = match.group(1)

    match = re.search('BEGIN SOLUTION(.*?)END SOLUTION', text, re.DOTALL)
    if match:
        text = match.group(1)

    return text


def ds1000_matplotlib_postprocess(text: str) -> str:
    text = ds1000_postprocess(text)
    code_lines = text.split('\n')
    postprocessed_lines = []
    for line in code_lines:
        skip_line_flag = False
        # Matplotlib removes function calls that will clear the
        # global figure object
        # Removing these functions helps running execution-based evaluation
        for phrase in ['plt.show()', 'plt.clf()', 'plt.close()', 'savefig']:
            if phrase in line:
                skip_line_flag = True
                break

        if skip_line_flag:
            continue
        else:
            postprocessed_lines.append(line)
    text = '\n'.join(postprocessed_lines)
    return text
