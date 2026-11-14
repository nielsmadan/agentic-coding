# On an interactive SSH login (the phone), offer the running tmux sessions.
# Esc in the picker leaves a plain shell; TMX_NO_AUTO=1 turns it off.
if [[ -o interactive && -n $SSH_CONNECTION && -z $TMUX && -z $TMX_NO_AUTO && -t 0 && -t 1 ]]; then
  tmx --auto
fi
