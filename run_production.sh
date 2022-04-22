## run test environment
# console logs are not saved, so console outputs are faster

# python virtual environment
#source venv/bin/activate

# flask environment variables
export FLASK_APP=main.py
export FLASK_ENV=development

# switch mturk config variable from 'sandbox' to 'production'
sed -i "s/env = 'sandbox'/env = 'production'/g" mturk/turk_config.txt

# run
python main.py production
