# Use the GNOME keyring SSH agent (gcr-ssh-agent.socket)
if test -S $XDG_RUNTIME_DIR/gcr/ssh
    set -gx SSH_AUTH_SOCK $XDG_RUNTIME_DIR/gcr/ssh
end
