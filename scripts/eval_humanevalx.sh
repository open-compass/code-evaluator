#!/bin/bash

support_languages=("python" "js" "go" "cpp" "java" "rust")

EVAL_INPUT_PATH=$1        # evaluation file, 
LANGUAGE=$2               # langugae
TIMEOUT=15
DATA_PATH="./datasets/humanevalx/humanevalx_$LANGUAGE.jsonl.gz"

NUM_WORKERS=8
OUTPUT_DIR=outputs/humanevalx-${LANGUAGE} 
TMP_DIR=tmp

OPTIND=3
while getopts "n:o:t:p:l:" OPT; 
do
  case $OPT in
    n) 
      NUM_WORKERS="$OPTARG"
      ;;
    o) 
      OUTPUT_DIR="$OPTARG"
      ;;
    t) 
      TMP_DIR="$OPTARG"
      ;;
    p) 
      WITH_PROMPT=$OPTARG
      ;;
    \?) 
      echo "Invalid option -$OPTARG" >&2
      exit 1
    ;;
    :)
      echo "Invalid Option: -$OPTARG requires an argument" 1>&2
      exit 1
      ;;
  esac
done

# 标记是否找到字符串 
found=false

for str in "${support_languages[@]}"; do
    if [ "$str" == "$LANGUAGE" ]; then
        found=true
        break
    fi
done

# 如果没有找到字符串，打印错误消息并退出
if [ "$found" = false ]; then
    echo "We don't support '$LANGUAGE' Language, only supoorts ${support_languages[*]}."
    exit 1
fi

if [ ! -f "$EVAL_INPUT_PATH" ]; then
    echo "Error: File ($EVAL_INPUT_PATH) does not exist."
    exit 1
fi

if [ ! -f "$DATA_PATH" ]; then
    echo "Error: File ($DATA_PATH) does not exist."
    exit 1
fi

echo "Evaluating $LANGUAGE Start ......"

if [ $LANGUAGE = rust ]; then
    TIMEOUT=300
    echo "Setting timeout to $TIMEOUT for Rust"
fi

CMD="python ./evals/humanevalx/evaluation.py \
    --input_path $EVAL_INPUT_PATH \
    --output_path $OUTPUT_DIR \
    --language_type $LANGUAGE \
    --dataset_type humanevalx \
    --generation_mode completion \
    --n_workers $NUM_WORKERS \
    --tmp_dir $TMP_DIR  \
    --problem_file $DATA_PATH \
    --with_prompt $WITH_PROMPT \
    --timeout $TIMEOUT"

echo "Running CMD: " $CMD

eval $CMD

echo "Evaluating $LANGUAGE End ......"

if [ -f $TMP_DIR ]; then
    rm -R $TMP_DIR
fi

echo "Evaluation finished."

exit 0
