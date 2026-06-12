#!/bin/bash
echo "Silex Configuration Utility"
echo ""
if [ ! -f .is_setup ]; then
    echo "We'll ask you a few questions and set the basics up for you!"
    echo "Please read the README file for a complete list of dependencies and how to install them."

    echo "Give us a second to install the Python dependencies."
    pip3 install -r requirements.txt
    if [ $? -eq 2 ]; then
        echo "Error: Something went wrong. We may need root to continue. Please put in your password to continue."
        sudo pip3 install -r requirements.txt
        if [ $? -eq 2 ]; then
            echo "Error: Cannot install Python dependencies. Check your permissions and try again."
            exit
        fi
    fi
    echo "Installed all required packages! Now, just a few questions about you."
    echo ""
    printf "What should your repo be called? "
    read silex_repo_name
    printf "Can you briefly describe what your repo is about? "
    read silex_repo_description
    printf "What domain are you going to host the repo on (don't include https://, just the domain)? "
    read silex_repo_cname
    printf "What is *your* name? "
    read silex_repo_maintainer_name
    printf "What's your email? "
    read silex_repo_maintainer_email
    printf "With Sileo, you can customize your repo's tint color. Can you provide a hex code to do so? "
    read silex_repo_tint
    printf "Would you like Silex to automatically push the repo to a Git server when run? (true/false) "
    read silex_auto_git

    mkdir "Packages"

    printf "{
    \"name\": \"$silex_repo_name\",
    \"description\": \"$silex_repo_description\",
    \"tint\": \"$silex_repo_tint\",
    \"cname\": \"$silex_repo_cname\",
    \"maintainer\": {
        \"name\": \"$silex_repo_maintainer_name\",
        \"email\": \"$silex_repo_maintainer_email\"
    },
    \"automatic_git\": \"$silex_auto_git\"
}" > Styles/settings.json

    echo ""
    echo "Thank you! Now let us generate you some GPG keys. Keep these somewhere safe or you may not be able to edit your repo anymore!"
    echo "   ENTROPY NOTICE: Please do stuff in the meantime like spam some keys or wiggling your mouse. We need entropy!"
    gpg --batch --gen-key util/gpg.batchgen
    echo "Exported key into your GPG keyring. This computer is the only computer that can be used for Silex (under default settings)."

    echo ""
    echo "Remember: for GitHub Pages, you have to go into your repository's settings on github.com and enable GitHub Pages for /docs."
    echo "Silex was successfully configured!"    
    echo ""
    echo "To add packages to your repo, take a look at the pre-bundled file in Packages/ or use the UI to manage/create them from DEBs."
    touch .is_setup
else
    echo "Silex has already been set up. If you are moving machines, please delete .is_setup and ensure the GPG keyring is carried over. Aborting..."
fi