#!/bin/bash
set -x
TEST_RESULTDIR=${TEST_RESULTDIR:="/data/test-results"}
EXEDIR=${EXEDIR:="/workspace/onnxruntime/onnxruntime/python/tools/transformers"}
PYTHONPATH=${PYTHONPATH:="/workspace/migraphx/build/lib"}
export PYTHONPATH
testdir=${TEST_RESULTDIR}/onnxruntime-`date '+%Y-%m-%d-%H-%M'`
mkdir $testdir
pushd /workspace/migraphx/src
git log > $testdir/commit.txt
popd
cd ${EXEDIR}
touch ${testdir}/summary.csv

# clear the cached optimized models
rm ./onnx_models/*gpu*

while read model bs
do
    echo "\n ***** " ${model} "migraphx engine\n"
    python benchmark.py -g -m  ${model} --sequence_length 32 384 --batch_sizes 1 ${bs} --engine=migraphx -p fp16 --disable_gelu --disable_layer_norm --disable_attention --disable_skip_layer_norm --disable_embed_layer_norm --disable_bias_skip_layer_norm --disable_bias_gelu --result_csv $testdir/dashboard-eng.csv --detail_csv $testdir/dashboard-detail.csv

    rm ./onnx_models/*gpu*
    echo "\n ***** " ${model} "rocm\n"
    python benchmark.py -g -m  ${model} --sequence_length 32 384 --batch_sizes 1 ${bs} --provider=rocm -p fp16 --result_csv $testdir/dashboard-rocm.csv --detail_csv $testdir/dashboard-detail.csv

    rm ./onnx_models/*gpu*
    echo "\n ***** " ${model} "migrpahx ex provider\n"
    python benchmark.py -g -m  ${model} --sequence_length 32 384 --batch_sizes 1 ${bs} --provider=migraphx -p fp16 --result_csv $testdir/dashboard-ep.csv --disable_gelu --disable_layer_norm --disable_attention --disable_skip_layer_norm --disable_embed_layer_norm --disable_bias_skip_layer_norm --disable_bias_gelu --detail_csv $testdir/dashboard-detail.csv
done <<BMARK_LIST
distilgpt2 8
bert-base-uncased 32
openai-gpt 8
gpt2 8
roberta-large 8
distilroberta-base 32
deepset/roberta-base-squad2 32
bert-base-cased 32
bert-large-uncased 16
roberta-base 16
deepset/roberta-base-squad2 32
camembert-base 32
albert-base-v1 32
albert-base-v2 32
xlm-roberta-base 16
microsoft/layoutlm-base-uncased 32
BMARK_LIST