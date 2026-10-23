;; Open .v files with Proof General's Coq mode
;;(load "~/.emacs.d/lisp/PG/generic/proof-site")

;; points to the path where I git cloned evil and somehow makes it work
(add-to-list 'load-path "~/evil")
(require 'evil)
(evil-mode 1)

;; see cs598 instructions for this: https://dependenttyp.es/classes/artifacts/4-foundations.html or https://agda.readthedocs.io/en/latest/getting-started/installation.html#running-the-agda-mode-program
(load-file (let ((coding-system-for-read 'utf-8))
                (shell-command-to-string "agda-mode locate")))
