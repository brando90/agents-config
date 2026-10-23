# - install python
# install brew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
#  install wget to get miniconda
brew install wget

# get miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda

# source /Users/my_username/opt/anaconda3/bin/activate
source ~/miniconda/bin/activate
conda init zsh
# conda init
conda update -n base -c defaults conda
conda install conda-build

conda create -n iit_synthesis python=3.9
conda activate iit_synthesis
#conda remove --name metalearning2 --all

# TODO: get zshrc from my github

# TODO: get opam

# TODO just link to get coq

# install docker
brew install --cask docker
