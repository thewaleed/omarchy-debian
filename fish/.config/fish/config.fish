# User binaries (herdr, etc.) - same as the PATH line in ~/.bashrc
fish_add_path -g ~/.local/bin

# nvm's Node (node, npm, and npm -g tools like opencode); bash gets these from nvm.sh
set -l nvm_node_bins ~/.nvm/versions/node/*/bin
test (count $nvm_node_bins) -gt 0; and fish_add_path -g $nvm_node_bins[-1]

if status is-interactive
    # Commands to run in interactive sessions can go here
end

# Merged from fish_variables (universal variables, decoded from SETUVAR)
set -U fish_color_autosuggestion brblack
set -U fish_color_cancel '-'
set -U fish_color_command normal
set -U fish_color_comment red
set -U fish_color_cwd green
set -U fish_color_cwd_root red
set -U fish_color_end green
set -U fish_color_error brred
set -U fish_color_escape brcyan
set -U fish_color_history_current '--bold'
set -U fish_color_host normal
set -U fish_color_host_remote yellow
set -U fish_color_normal normal
set -U fish_color_operator brcyan
set -U fish_color_param cyan
set -U fish_color_quote yellow
set -U fish_color_redirection cyan '--bold'
set -U fish_color_search_match white '--background=brblack'
set -U fish_color_selection white '--bold' '--background=brblack'
set -U fish_color_status red
set -U fish_color_user brgreen
set -U fish_color_valid_path '--underline'
set -U fish_key_bindings fish_default_key_bindings
set -U fish_pager_color_completion normal
set -U fish_pager_color_description yellow '-i'
set -U fish_pager_color_prefix normal '--bold' '--underline'
set -U fish_pager_color_progress brwhite '--background=cyan'
set -U fish_pager_color_selected_background '-'
