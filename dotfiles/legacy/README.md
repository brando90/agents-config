# Brando's dotfiles

## Install

TODO

- check pedro's code: https://github.com/pcattori/dotfiles

##

To edit hammerspoon file do it through their interface


## Emacs & Proof General

see: https://superuser.com/questions/771442/configuring-proof-general-for-coq-in-emacs/1658596#1658596
Also, see my: https://github.com/brando90/coq4brando

general comments:

- note if you copy `(require 'package)` multiple times it causes errors becuase it is not an indepodent op
- it seems that you do not need to set the coqtop path explicitly if you use PG - PG finds it on its own
  - I think it's because I installed it with opam but I am not 100%

## Path Variables

My original mac had this path variable:
```
(base) brandomiranda~ ❯ echo $PATH
/Library/Frameworks/Python.framework/Versions/3.8/bin:/Users/brandomiranda/miniconda3/bin:/Users/brandomiranda/.pyenv/shims:/Users/brandomiranda/.pyenv/bin:/Users/brandomiranda/anaconda3/bin:/Users/brandomiranda/.opam/4.07.0/bin:/Users/brandomiranda/.gem/ruby/2.6.0/bin:/usr/local/opt/ruby/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/brandomiranda/opt/anaconda3/bin:/Users/brandomiranda/opt/anaconda3/condabin:/Users/brandomiranda/bin#:/Users/brandomiranda/bin/Maude-2.7.1-osx
```
to reset PATH variable see: https://superuser.com/questions/121870/how-do-i-reset-the-path-variable-on-mac-os-x

To reset PATH do:
```
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH

# add custom, local installations to PATH
PATH=/usr/local/bin:/usr/local/sbin:"$PATH"

# add MacPorts to PATH
PATH=/opt/local/bin:/opt/local/sbin:"$PATH"
```


## PyCharm settings

private repo: https://github.com/brando90/pycharm-settings-brando-internships
