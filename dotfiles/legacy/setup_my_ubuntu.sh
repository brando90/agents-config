# TODO: get bashrc

# install python
sudo apt-get update
sudo apt-get install wget

wget https://repo.anaconda.com/archive/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda

# source /Users/my_username/opt/anaconda3/bin/activate
source ~/miniconda/bin/activate
# conda init zsh
conda init
conda update -n base -c defaults conda
conda install conda-build

conda create -n iit_synthesis python=3.9
conda activate iit_synthesis
#conda remove --name metalearning2 --all

# TODO: install docker? maybe

# others?
