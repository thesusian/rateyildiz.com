# Check if running from the root directory
if [[ $(basename "$PWD") != "rateyildiz.com" ]]; then
    echo "Error: This script must be run from the 'rateyildiz.com' directory"
    exit 1
fi

# Run Babel commands
pybabel extract -F babel.cfg -o messages.pot .
pybabel init -i translations/messages.pot -d translations -l tr
