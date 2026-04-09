# Koyejo STAIR Lab — Cluster Setup & Resources

Reference copy of the shared lab onboarding doc for agent visibility.

**Source:** [Google Doc](https://docs.google.com/document/d/1PSTLJdtG3AymDGKPO-bHtzSnDyPmJPpJWXLmnJKzdfU/edit?tab=t.0#heading=h.r4k6tejzm5jy)

---

## Table of Contents

- [Introduction](#introduction)
- [Cluster: Sherlock](#cluster-sherlock)
- [Cluster: SNAP](#cluster-snap)
  - [Brando's Comments](#brandos-comments)
  - [Rylan's Recommended Setup](#rylans-recommended-setup)
  - [Brando's Recommended Setup](#brandos-recommended-setup)
  - [Long Running Jobs on SNAP](#long-running-jobs-on-snap)
  - [The Simplest Way to Use SNAP](#the-simplest-way-to-use-snapinfo-labs-imo)
  - [Secret Q&A Doc](#secret-qa-doc-from-snap)
  - [Large Datasets on SNAP](#large-datasets-on-snap)
- [Installing Anaconda/Miniconda](#installing-anacondaminiconda)
- [IDE Use on Clusters](#ide-use-on-clusters)
- [Lab Website](#lab-website)
- [Sang's Setup](#sangs-setup)
- [Everything Conda](#everything-conda)
- [LLMs Everything](#llms-everything)
- [Everything Tmux](#everything-tmux)

---

## Introduction

Welcome! Hopefully, this tutorial will get you up and running on at least one of Stanford CS's many compute clusters.

### Overview of Stanford Clusters

| Cluster | Used by | Managed by |
|---------|---------|------------|
| **SNAP** | Subset of labs in Stanford CS | Info Lab |
| **Sherlock** | All of Stanford | Stanford |
| **SC** (prev. SAIL Cluster) | — | — |
| **NLP Cluster** | NLP group | — |
| **Yamins' Cluster** | Yamins, Goodman, Ganguli | Yamins |

Onboarding: [Google Doc](https://docs.google.com/document/d/1WmdhdR_-uigbtHHcINz7sTB-vlFasTp8pQ0Y6L4eCm4/edit)

---

## Cluster: Sherlock

Sherlock is a **Slurm cluster**. Slurm manages job queuing, resource sharing, and fair scheduling.

- When you login, you're routed to a **load-balanced login node** — do **not** run code on the login node.
- Use the head node to submit jobs to Slurm.

### Sherlock Setup

1. Email `srcc-support@stanford.edu` with your name and SUNet ID, cc'ing Professor Koyejo.
2. Instructions: https://www.sherlock.stanford.edu/docs/getting-started/
3. Once approved, connect via SSH:
   ```bash
   ssh <sunetid>@login.sherlock.stanford.edu
   ```
4. Details: https://www.sherlock.stanford.edu/docs/getting-started/connecting/

### Sherlock Disk Usage

- **HOME** (`/home/users/<sunetid>`): 15 GB limit
- **GROUP_HOME** (`/home/groups/sanmi`): 1 TB shared
- Recommend: install Anaconda under `$HOME`, put everything else (envs, data) under `$GROUP_HOME`

```bash
echo $HOME        # /home/users/<sunetid>
echo $GROUP_HOME   # /home/groups/sanmi
```

### Sherlock SLURM Jobs

Example SLURM script:

```bash
#!/bin/bash
#SBATCH -n 1                    # one node
#SBATCH --mem=32G               # RAM
#SBATCH --time=01:00:00         # total run time limit (D-HH:MM:SS)
#SBATCH --mail-type=FAIL

# Activate virtual environment
source /home/groups/sanmi/rschaef/KoyejoLab-Rotation/emergence_venv/bin/activate

export PYTHONPATH=.

# Print each command before executing (for reproduction)
set -x

# -u ensures results aren't buffered but immediately written to stdout
python -u notebooks/emergence/gpt3_addition_analyze.py
```

---

## Cluster: SNAP

### Brando's Comments

To gain access to the SNAP cluster, email `action@cs.stanford.edu` and cc Professor Koyejo. Provide your **SUID ID number** (e.g., 05756291) and your **CSID** (e.g., rschaef), **not** your SUNetID.

**Key resources:**
- SNAP wiki: https://ilwiki.stanford.edu/doku.php?id=start
- Introduction to SNAP slides (ask in Slack)
- YouTube showcase: https://youtu.be/XEB79C1yfgE

The SNAP cluster is **not** set up with a standard HPC workload manager (no Slurm, Condor, qsub). Therefore the advice below may seem unusual.

**Critical storage info** — read https://ilwiki.stanford.edu/doku.php?id=hints:storefiles:
- **LFS** (Local File System): fast, per-server, use for data & checkpoints
- **AFS** (Andrew File System): shared across servers, use for code & dotfiles
- **DFS**: slow — avoid unless you have a specific reason

### Rylan's Recommended Setup

**Step 0:** Join the [SNAP Slack](https://join.slack.com/t/snap-group/shared_invite/zt-1lokufgys-g6NOiK3gQi84NjIK_2dUMQ)

**Step 1:** Connect to a SNAP server via SSH

```bash
# Pick a server from https://ilwiki.stanford.edu/doku.php?id=snap-servers:snap-gpu-servers-stats
ssh rschaef@turing1.stanford.edu

# If you get "no matching host key" error:
ssh -oHostKeyAlgorithms=+ssh-rsa rschaef@turing1.stanford.edu
```

**Step 2:** Create your `.bashrc` files

SNAP uses `.bashrc.user` instead of `.bashrc`.

File: `/afs/cs.stanford.edu/u/rschaef/.bashrc.user`
```bash
source /afs/cs.stanford.edu/u/rschaef/.bashrc.lfs
```

File: `/afs/cs.stanford.edu/u/rschaef/.bashrc.lfs`
```bash
# Print current working directory with each prompt
export PS1="\u@\h \w$ "

# Use current machine as home
export LOCAL_MACHINE_PWD=$(python3 -c "import socket;hostname=socket.gethostname().split('.')[0];print('/lfs/'+str(hostname)+'/0/rschaef');")
mkdir -p $LOCAL_MACHINE_PWD
export WANDB_DIR=$LOCAL_MACHINE_PWD
export LFS_HOME=$LOCAL_MACHINE_PWD

cd $LFS_HOME
export TEMP=$LFS_HOME
export AFS_HOME=/afs/cs.stanford.edu/u/rschaef
export DFS_HOME=/dfs/scratch0/rschaef/

# Initialize conda (machine-agnostic version)
# >>> conda initialize >>>
__conda_setup="$("$LOCAL_MACHINE_PWD/miniconda3/bin/conda" 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$LOCAL_MACHINE_PWD/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$LOCAL_MACHINE_PWD/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="$LOCAL_MACHINE_PWD/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
```

**Step 3:** Install Miniconda on `/lfs/` (**not** `/afs/` — AFS has ~1-5 GB limit)

```bash
# Install to /lfs/<machine>/0/<csid>/miniconda3
# If you want conda on multiple machines, install on each machine's LFS
```

See [Installing Anaconda/Miniconda](#installing-anacondaminiconda) below for detailed steps.

### Brando's Recommended Setup

No matter what setup you use, you need to decide:

| Decision | Recommendation |
|----------|---------------|
| Where `$HOME` points to | LFS |
| Where code lives | AFS (shared across servers) |
| Where Python envs live | LFS (DFS is too slow) |
| Where data/logs/checkpoints live | LFS |
| Where `.bashrc` lives | `.bashrc.user` & `.bashrc.lfs` on AFS |
| Other local installs | LFS (speed) |
| How to code | IDE with deployment/sync to server |
| How to run experiments | `main.sh` → krbtmux → tmux |

**Reference configs:**
- `.bashrc.lfs`: https://gist.github.com/brando90/729370f23345b1c46a063ab3ee540a3d
- `.bashrc.user`: https://github.com/brando90/.dotfiles/blob/master/.bashrc.user
- Past `.bashrc.dfs`: https://github.com/brando90/.dotfiles/blob/master/.bashrc.dfs
- Detailed setup repo: https://github.com/brando90/snap-cluster-setup

### Always Put This at the Top of Your Scripts

Prevents CPUs from spinning idly (Rok's request):

```python
import os
n_threads_str = "4"
os.environ["OMP_NUM_THREADS"] = n_threads_str
os.environ["OPENBLAS_NUM_THREADS"] = n_threads_str
os.environ["MKL_NUM_THREADS"] = n_threads_str
os.environ["VECLIB_MAXIMUM_THREADS"] = n_threads_str
os.environ["NUMEXPR_NUM_THREADS"] = n_threads_str
```

### Long Running Jobs on SNAP

```bash
# 1. SSH into your preferred machine
ssh <csid>@<server>.stanford.edu

# 2. Start a Kerberos-aware tmux session
/afs/cs/software/bin/krbtmux

# 3. Prevent SNAP from kicking you off
/afs/cs/software/bin/reauth
# Enter your password when prompted

# 4. Navigate to your code, activate envs, run experiments
```

Reference: https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs

If you use Kerberos for passwordless logins, ensure GSSAPI is enabled in your SSH config.

### The Simplest Way to Use SNAP/Info Labs (imo)

1. **Get an account** — email `action@cs.stanford.edu`, cc Koyejo
2. **Connect** — SSH directly: https://ilwiki.stanford.edu/doku.php?id=hints:remote-access
3. **Set up bash** — use `.bashrc.user` (not `.bashrc`): https://ilwiki.stanford.edu/doku.php?id=hints:enviroment
4. **Storage** — pick 1-2 servers, use LFS for everything: https://ilwiki.stanford.edu/doku.php?id=hints:storefiles#lfs_local_server_storage
5. **Install conda** — see: https://github.com/brando90/ultimate-utils/blob/master/sh_files_repo/download_and_install_conda.sh
6. **Sync code** — PyCharm rsync-on-save, or git, or direct IDE connection
7. **Long-lived jobs** — use `krbtmux` + `reauth`: https://ilwiki.stanford.edu/doku.php?id=hints:long-jobs
8. **GPUs** — check availability: https://ilwiki.stanford.edu/doku.php?id=snap-servers:snap-gpu-servers-stats and SNAP Slack
9. **Done!** Login → sync code → files on local server → set up GPUs → run with krbtmux+reauth

**For help:** use `#cluster-help` or `#general` in SNAP Slack (not DMs). For admin help, contact Rok (https://profiles.stanford.edu/rok-sosic) or email `il-action@cs.stanford.edu`.

### Secret Q&A Doc from SNAP

https://docs.google.com/document/d/1pFBJFki9uJ69q0EcI4vcaB603lA_AXHdwaLMfqIovwE/edit#heading=h.efy1aim4jl4q

### Model Checkpoints on SNAP

(See shared datasets below)

### Large Datasets on SNAP

| Server | Dataset | Path |
|--------|---------|------|
| skampere1 | ImageNet | `/lfs/skampere1/0/rschaef/data/Imagenet2012` |
| skampere1 | LM Eval Harness | `/lfs/skampere1/0/rschaef/data/huggingface` |
| skampere1 | SBU Captions | `/lfs/skampere1/0/rschaef/data/sbucaptions` |
| ampere1 | Anthropic HHH | `/lfs/ampere1/0/rschaef/data/huggingface/Anthropic___json` |
| ampere8 | FineWeb | `/lfs/ampere8/0/dhruvpai/KoyejoLab-EBLM/data/HuggingFaceFW/fineweb` |
| hyperturing2 | FineWeb | `/lfs/hyperturing2/0/rschaef/KoyejoLab-EBLM/data/HuggingFaceFW/fineweb` |

### Data Crawling on SNAP

Four machines available for crawling: `silk04-07` — https://ilwiki.stanford.edu/doku.php?id=other-servers:crawling-servers

These have higher bandwidth than GPU machines. Note: no `/lfs/` on these machines — use `/dfs/scratch0/` instead.

### SSHing onto SNAP and Passwordless Login

> **WARNING:** This has been known to break and cause a "Heisenbug". Use at your own risk.

SNAP uses Kerberos for auth. To log in without typing your password each time:

- **macOS:** open `Ticket Viewer.app` → "+" → log in as `<CSID>@CS.STANFORD.EDU` (UPPERCASE)
- **Linux:** `kinit <CSID>@CS.STANFORD.EDU` (then optionally `aklog` for AFS tokens)

Add to `~/.ssh/config`:

```sshconfig
Host *.stanford.edu
  GSSAPIAuthentication yes
  GSSAPIDelegateCredentials yes
  PreferredAuthentications gssapi-with-mic,publickey,password

# Example host entries
Host skampere1
  HostName skampere1.stanford.edu
  User <your_csid>

# Or multiple hosts on one block
Host skampere1 skampere2
  Hostname %h.stanford.edu
  User <csid>
  GSSAPIAuthentication yes
  GSSAPIDelegateCredentials yes
```

---

## Installing Anaconda/Miniconda

You can run Brando's script: https://github.com/brando90/ultimate-utils/blob/master/sh_files_repo/download_and_install_conda.sh

Or manually:

```bash
# 1. Download
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh

# 2. Install
./Miniconda3-latest-Linux-x86_64.sh
# Read agreement, type "yes"
# Choose location — ON SNAP: put on /lfs/ NOT /afs/
# e.g. /lfs/<machine>/0/<csid>/miniconda3
# When asked "initialize Miniconda?", type "n"

# 3. Update conda
conda update -n base -c defaults conda
conda update conda
conda update --all

# 4. Create an environment
conda create -n myenv python=3.9
conda activate myenv

# 5. Verify pip
which python
pip install --upgrade pip
which pip
```

### Conda init on SNAP

If `conda init` fails (tries to write to `.bashrc` which needs sudo), manually add to `.bashrc.user`:

```bash
# >>> conda initialize >>>
__conda_setup="$('/lfs/<machine>/0/<csid>/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/lfs/<machine>/0/<csid>/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/lfs/<machine>/0/<csid>/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/lfs/<machine>/0/<csid>/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
```

Then `source ~/.bashrc.user`. You should see `(base)` in your prompt.

---

## IDE Use on Clusters

### PyCharm

PyCharm uses "Deployment" for auto-syncing code between machines.

1. On your cluster, create a virtual environment
2. In PyCharm: Add Interpreter → On SSH
3. Specify SSH connection (New for a new cluster)
4. Enter password, 2FA if needed

**Note:** Some clusters (e.g., Sherlock) require 2FA again on rsync. Fix with SSH multiplexing in `~/.ssh/config`:

```sshconfig
Host login.sherlock.stanford.edu
  ControlMaster auto
  ControlPath ~/.ssh/%l%r@%h:%p
```

### VSCode (Linux/macOS)

1. Create/edit `~/.ssh/config`:

```sshconfig
Host whale
  HostName whale.stanford.edu
  User <csid>

Host skampere1
  HostName skampere1.stanford.edu
  User <csid>
  ProxyJump whale
```

2. In VS Code: click bottom-left → Remote-SSH: Connect to Host → select `skampere1`
3. Enter password as prompted

### VSCode (Windows)

Same SSH config as above. In VS Code: bottom-left → Connect to Host → Configure New Host → paste the config → connect.

---

## Lab Website

- Website: https://stair.cs.stanford.edu/
- GitHub: https://github.com/stair-lab/stair
- Access: ping Sang (`sttruong@stanford.edu`)
- Website folder: `/afs/cs/group/koyejolab/stair`
- To publish: email `action@cs.stanford.edu` to join `koyejolab` LDAP group

```bash
# Build locally
bundle exec jekyll build

# Commit to GitHub, then on server:
cd /afs/cs/group/koyejolab/stair
git pull
cp -r _site /afs/cs/group/koyejolab/www
```

- Lab HuggingFace: https://huggingface.co/stair-lab

---

## Sang's Setup

Sang recommends **DFS** (instead of AFS or LFS) since it makes machine hopping painless. Unless you do heavy I/O, performance difference is minimal.

### Everything Conda

```bash
source /dfs/user/sttruong/miniconda3/bin/activate
conda activate eval_llm
export LD_LIBRARY_PATH=/dfs/user/sttruong/miniconda3/envs/eval_llm/lib/python3.10/site-packages/torch/lib:/dfs/user/sttruong/miniconda3/envs/eval_llm/lib:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# Test CUDA
python -c "import torch; print(torch.cuda.is_available()); a=torch.rand(5); a.cuda()"
```

To clone a conda env:
```bash
conda create --name <new_env> --clone train_llm
```

### Conda Alternatives

```bash
python -m pip install virtualenv
python -m virtualenv -p /dfs/user/sttruong/env/python3.10/bin/python3.10 myenv
```

### Conda for Finetuning LLMs

Uses LLaMA Factory to avoid OOM errors. Ping `sttruong@stanford.edu` for help.

```bash
# Step 1: Clone LLaMA Factory
git clone https://github.com/hiyouga/LLaMA-Factory
cd LLaMA-Factory

# Step 2: Create environment
source /dfs/user/sttruong/miniconda3/bin/activate
conda create -n train_llm python=3.10 -y
conda activate train_llm

# Step 3: Install deepspeed and unsloth
pip install deepspeed==0.12.6 flash-attn==2.4.1
pip install -r requirements.txt
pip install "unsloth[cu118_ampere] @ git+https://github.com/unslothai/unsloth.git"

# Step 4: Export paths
export LIBRARY_PATH=/dfs/user/sttruong/miniconda3/envs/test_env/lib/python3.10/site-packages/torch/lib:$LIBRARY_PATH
export LD_LIBRARY_PATH=/dfs/user/sttruong/miniconda3/envs/test_env/lib/python3.10/site-packages/torch/lib:$LD_LIBRARY_PATH
export HF_HOME="/dfs/local/0/sttruong/env/.huggingface"
export TRANSFORMERS_CACHE="/lfs/local/0/sttruong/env/.huggingface"
export HF_DATASETS_CACHE="/lfs/local/0/sttruong/env/.huggingface/datasets"

# Step 5: Configure accelerate
accelerate config
# Choose: this machine, multi-GPU, DeepSpeed yes, ZeRO 2 (or 3 for OOM), etc.

# Step 6: Run finetuning
accelerate launch src/train_bash.py \
    --stage pt \
    --do_train True \
    --model_name_or_path <path_to_model> \
    --use_fast_tokenizer True \
    --finetuning_type freeze \
    --flash_attn True \
    --dataset_dir data \
    --dataset <dataset_name> \
    --preprocessing_num_workers 32 \
    --cutoff_len <model_max_length> \
    --num_train_epochs <num_epochs> \
    --bf16 True \
    --per_device_train_batch_size 2 \
    --gradient_accumulation_steps 64 \
    --learning_rate 1e-4 \
    --lr_scheduler_type cosine \
    --max_grad_norm 1.0 \
    --weight_decay 0.001 \
    --logging_steps 1 \
    --warmup_ratio 0.03 \
    --save_steps 2 \
    --output_dir <output_dir> \
    --save_total_limit 3 \
    --plot_loss True \
    --report_to neptune
```

---

## LLMs Everything

### Software Packages for LLMs

| Framework | Training/FT | Deployment | Multi-GPU | Multimodal | Universal LLM Support |
|-----------|:-----------:|:----------:|:---------:|:----------:|:--------------------:|
| LLaMA Factory | Yes | - | Yes | - | Yes |
| Text Generation Inference | - | Yes | Yes | - | Yes |
| Ollama | - | Yes | Maybe | Yes | Limited |
| LLaVa | Yes | Yes | Yes | Yes | Limited |
| llama.cpp | - | Yes | Maybe | Yes | Limited |
| LLM Foundry | Yes | - | - | - | Limited (MPT, DBRX) |
| llm.c | Yes | - | Maybe | - | Limited (GPT2) |

### Conda for Deploying LLMs

Uses Text Generation Inference (TGI) for serving large LLMs across GPUs.

```bash
# Step 1: Environment
source /dfs/user/sttruong/miniconda3/bin/activate
conda create -n eval_llm python=3.10 -y
conda activate eval_llm

# Step 2: Install Rust, Cargo, OpenSSL
export CARGO_HOME="/dfs/user/sttruong/.cargo"
export RUSTUP_HOME="/dfs/user/sttruong/.rustup"
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# Select modify PATH variable: NO

wget openssl-3.0.13.tar.gz && tar xvf openssl-3.0.13.tar.gz
cd openssl-3.0.13
./config --prefix=/dfs/user/sttruong/miniconda3/envs/openssl --openssldir=/dfs/user/sttruong/miniconda3/envs/openssl
make install -j32

source "/dfs/user/sttruong/.cargo/env"
export PATH=/dfs/user/sttruong/.cargo/bin:/dfs/user/sttruong/miniconda3/envs/openssl/bin:$PATH
export LD_LIBRARY_PATH=/dfs/user/sttruong/miniconda3/envs/eval_llm/lib:/dfs/user/sttruong/miniconda3/envs/openssl/lib64:$LD_LIBRARY_PATH
export OPENSSL_DIR=/dfs/user/sttruong/miniconda3/envs/openssl

# Step 3: Install protoc and TGI
conda install -c "nvidia/label/cuda-11.8.0" cuda-toolkit -y
conda install -c pytorch -c nvidia pytorch==2.1.2 pytorch-cuda=11.8 -y

PROTOC_ZIP=protoc-21.12-linux-x86_64.zip
curl -OL https://github.com/protocolbuffers/protobuf/releases/download/v21.12/$PROTOC_ZIP
unzip -o $PROTOC_ZIP -d /dfs/user/sttruong/miniconda3/envs/eval_llm/ bin/protoc
unzip -o $PROTOC_ZIP -d /dfs/user/sttruong/miniconda3/envs/eval_llm/ 'include/*'
rm -f $PROTOC_ZIP

git clone https://github.com/huggingface/text-generation-inference
cd text-generation-inference
git checkout 0d72af5ab01a5b1dabd5beda953403d63b1886e0
cargo clean
BUILD_EXTENSIONS=True make install

# If C++ version errors (turing/hyperturing):
conda install -c conda-forge gxx=11.4.0 libstdcxx-ng=11.4.0

# Step 4: Compile optimization libraries
export MAX_JOBS=32
cd server
make install-vllm-cuda
make install-awq          # quantization, not for below A100
make install-eetq         # quantization
make install-flash-attention      # for GPU below A100
make install-flash-attention-v2-cuda  # for GPU >= A100

cd flash-attention-v2/csrc
cd ft_attention && python setup.py install && cd ..
cd fused_dense_lib && python setup.py install && cd ..
cd fused_softmax && python setup.py install && cd ..
cd layer_norm && python setup.py install && cd ..
cd rotary && python setup.py install && cd ..
cd xentropy && python setup.py install && cd ..
cd ../../../
pip install mamba_ssm megablocks causal_conv1d

# Step 5: Deploy (only works on ampere1/8, mercury1-4, skampere1, hyperturing)
source /dfs/user/sttruong/miniconda3/bin/activate
conda activate eval_llm
source "/dfs/user/sttruong/.cargo/env"
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
# For llama family: number of GPUs must be a multiple of 4

# Step 6: Launch TGI server
text-generation-launcher \
    --model-id meta-llama/Llama-2-7b-chat-hf \
    --port 8889 \
    --max-input-length 4096 \
    --max-total-tokens 8192 \
    --max-batch-prefill-tokens 4096

# Step 7: Call the server
curl --location 'https://localhost:8889/generate' \
  --header 'Content-Type: application/json' \
  --data '{
    "inputs": "[INST] Question: Who is Albert Einstein?\nAnswer: [/INST] ",
    "parameters": {
      "temperature": 1.0,
      "top_p": 1.0,
      "top_k": 50,
      "repetition_penalty": 1.0,
      "max_new_tokens": 1024
    }
  }'
```

Python client:

```python
import requests, json
url = "https://localhost:8080/generate"
payload = json.dumps({
    "inputs": "[INST] Question: Who is Albert Einstein?\nAnswer: [/INST] ",
    "parameters": {"temperature": 1, "top_p": 1, "top_k": 50, "repetition_penalty": 1, "max_new_tokens": 1024}
})
response = requests.post(url, headers={'Content-Type': 'application/json'}, data=payload)
print(response.text)
```

---

## Install Python (from source)

```bash
cd /dfs/user/sttruong/env
wget https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tar.xz
tar -xvf Python-3.10.11.tar.xz
cd Python-3.10.11/
./configure --prefix=/dfs/user/sttruong/env/python3.10
make install -j 64
# Add to .bashrc.user:
# export PATH=/dfs/user/sttruong/env/python3.10/bin:$PATH
# alias python="python3.10"
```

## Install Jupyter Kernel

```bash
pip install ipykernel
python -m ipykernel install --user --name=mykernel
# Delete: jupyter kernelspec uninstall mykernel
# Start: jupyter-notebook --no-browser --ip 0.0.0.0 --port 10000
```

## Install Torch

Two CUDA families on SNAP:

```bash
# Ampere/Mercury/Hyperturing (CUDA 11.7+) — use PyTorch 2.0.1+
pip install torch==2.0.1

# Turing (CUDA 11.3) — max PyTorch 1.12.1
pip install torch==1.12.1
```

---

## Everything Tmux

```bash
tmux new -s session_name       # create named session
/afs/cs/software/bin/krbtmux   # Kerberos-aware tmux
/afs/cs/software/bin/reauth    # prevent SNAP from kicking you off
jupyter lab --no-browser        # start Jupyter inside tmux

# Detach: Ctrl+B, then D
tmux list-sessions              # list sessions
tmux a -t <session_id>          # reattach
```

## Everything ngrok

```bash
# Install
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
./ngrok config add-authtoken <your_token>

# Get a domain on ngrok dashboard > Domains > New domain

# Start (after starting jupyter or any service)
./ngrok http --domain=<your_domain> <port>
# Access from: https://<your_domain>
```

---

## FAQ

- Cluster Q&A: see [Secret Q&A doc](#secret-qa-doc-from-snap)
- LLM APIs: see lab-internal docs
