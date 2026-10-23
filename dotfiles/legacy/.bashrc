# source ~/.bash_profile

BLACK='\e[0;30m'
RED='\e[0;31m'
GREEN='\e[0;32m'
BROWN='\e[0;33m'
BLUE='\e[0;34m'
PURPLE='\e[0;35m'
CYAN='\e[0;36m'
LIGHT_GREY='\e[0;37m'
DARK_GREY='\e[1;30m'
LIGHT_RED='\e[1;31m'
LIGHT_GREEN='\e[1;32m'
YELLOW='\e[1;33m'
LIGHT_BLUE='\e[1;34m'
LIGHT_PURPLE='\e[1;35m'
LIGHT_CYAN='\e[1;36m'
WHITE='\e[1;37m'

BACK_DEFAULT_COLOR='\e[m'

export PS1="\[$LIGHT_GREY\]\u\[$LIGHT_PURPLE\]\w\[$LIGHT_GREY\] \$ \[$LIGHT_CYAN\]"

#http://linux-sxs.org/housekeeping/lscolors.html
LS_COLORS='di=1:fi=96:*.m=31:*.py=32:*.txt=36:*.out=35'
export LS_COLORS

#export PATH="$PATH:$HOME/bin"\

export DOCKER_ID_USER='brandojazz'

#export MIZFILES="/usr/local/share/mizar"

#alias tcoq="/Users/brandomiranda/home_simulation_research/gamepad/tcoq/bin/coqc"


conda activate automl

pip install wandb --upgrade
