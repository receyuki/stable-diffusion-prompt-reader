#!/bin/sh
#
# This is the default apptemplate error script
#

echo "Launch error"
if [ -n "$2" ]; then
    echo "An unexpected error has occurred during execution of the main script"
    echo ""
    echo "$2: $3"
    echo ""
fi

echo "Please report this issue to GitHub"
echo ""
echo "ERRORURL: https://github.com/receyuki/stable-diffusion-prompt-reader/issues"
exit


