#!/bin/bash
DOCKER=${DOCKER:="ort:cuda-20210621"}

docker run -e TZ=America/Chicago --gpus all --network=host -v /home/mev:/home/mev ${DOCKER} env EXPROVIDER=cuda /home/mev/source/rocm-migraphx/scripts/run_ort_mev.sh
