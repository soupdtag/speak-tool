## run test environment
# console logs are not saved, so console outputs are faster

# python virtual environment
#source venv/bin/activate
conda activate speak_tool

# flask environment variables
export FLASK_APP=main.py
export FLASK_ENV=development

# switch mturk config variable from 'production' to 'sandbox'
sed -i "s/env = 'production'/env = 'sandbox'/g" mturk/turk_config.txt

# run
python main.py sandbox
