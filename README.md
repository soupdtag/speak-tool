#### Note: the README for this repository is uploaded to my personal GitHub for documentation purposes, but the code is not yet available for public use. As soon as it is, I will upload it to this repo - stay tuned!

# Speak: a toolkit to collect speech recordings from Amazon Mechanical Turk workers
Created by Christopher Song ([e-mail](csong23@mit.edu); GitHub: [MIT](https://github.mit.edu/csong23), [personal](https://github.com/soupdtag/)). Please contact before use.


*README last updated 22 Aug 2019.* This README is split into the following five sections:
 - Overview
 - Setup/Configuration
 - Instructions for use
 - Methods
 - References


## Overview
This toolkit allows requesters to collect speech recordings from workers on Amazon Mechanical Turk (AMT), by posting tasks to AMT using the boto3 ExternalQuestion data structure. Each webpage prompts a worker with a stimulus (image, text, sound, etc.) and uses an embedded audio recorder to collect the worker's speech recordings. Importantly, the collected data is validated before storage.

This toolkit consists of two distinct tools:
 - [A Flask web application](main.py), which hosts the website through which workers record their answers to tasks
 - [A suite of AMT scripts](mturk/), which allows a requester to deploy/review/delete HITs that direct workers to the Flask web application


These tools are used together in order to accomplish the following tasks:
1. **Upload** (Flask app): deploy the task prompts + audio recorder on a website (with a unique link for each task)
2. **Deploy** (AMT scripts): embed each task link in an ExternalQuestion, and launch HITs for each ExternalQuestion
3. **Collect** (Flask app): save worker recordings to a location on the web server, in an organized manner
4. **Transcribe** (Flask app): save transcripts of worker recordings, using a speech transcription API of your choice (default: Google SpeechRecognition API)
5. **Validate** (Flask app): ensure that the data collected is useful, and that workers are completing tasks properly
6. **Document** (Flask app, AMT scripts): log the metadata for each task, including AMT worker info, prompt info, and data locations
7. **Review** (AMT scripts): review HITs, automatically approve those which are unlikely to be fraudulent, log those which require further investigation, and reject them as needed

Each of these steps is described in detail further below in the README.


## Setup/Configuration
1. Clone this repository.
2. Ensure that you have the AWS `credentials` file linked to your AMT account. It should be an extensionless file (path: `~/.aws/credentials`) with the following format:
```
[USERNAME_IN_BRACKETS]
aws_access_key_id = ACCESS_KEY_ID_HERE
aws_secret_access_key = SECRET_ACCESS_KEY_HERE
```
3. Install a python (or conda) virtual environment in the repo home directory, and activate it.
4. Install all of the packages outlined in `requirements.txt` in your virtual environment.
5. Obtain an SSL certificate for your machine. (Amazon does not allow ExternalQuestion HITs to direct workers to non-HTTPS enabled websites.)
   - MIT CSAIL affiliates can [request an SSL cert from TIG](https://tig.csail.mit.edu/web-services/server-certificates/).
6. Generate a text file containing file paths to each prompt file (image, audio, text, etc.) to be displayed in HITs, separated by a linebreak. For example (example file located in `./static/test-files/`):
     ```
     dave_task/d/dining_room/gsun_2cfa50e4b8eab1d67a53bb20aaa28021.jpg
     dave_task/a/abbey/gsun_20086d50e070ae7560403aa409461895.jpg
     dave_task/b/bookstore/gsun_f7efe349c296fd257139aca0de4e22e4.jpg
     ...
     dave_task/w/waiting_room/gsun_70b37b552d889c97fce43787c53bab9d.jpg
     dave_task/w/waiting_room/gsun_a2ff10af03c0e2e41987bc83aadd1400.jpg
     ```
   - *It is strongly suggested that you use a symbolic link to your dataset folder inside the repo home directory, in order to make file paths as short as possible. This is important during data collection, for eliminating unnecessary nested folders. (Files are saved in a folder structure adapted from these file paths.)*
7. Edit the template files in `templates/` with the text you'd like to display to workers. Sample templates are available for image, audio, and text tasks in `templates/test_battery`.
8. Edit the configuration files (`app_config.txt` and `mturk/turk_config.txt`) according to your project (account info, file locations, etc.)
9. (optional) For extracting geolocation data from IP addresses during user/participant logging, download [GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data?lang=en). Place the `GeoLite2-City.mmdb` file in `./scripts/geolite2` before use.
10. Edit the `run_sandbox.sh` and `run_production.sh` files, following the instructions commented inside. (You need to configure the scripts in order to activate your virtual environment properly.)


## Instructions for use
### Deploying HITs
1. Configure the app using the steps outlined in Setup/Configuration.
2. Run `./run_production.sh` (or `./run_sandbox.sh` for a test environment), to turn on the Flask server and load your prompts onto it. Testing Flask functionality can be as simple as follows:
   - Navigating to https://0.0.0.0:5000/ (replace 0.0.0.0 with your domain name URL) should print a list of lists, each sub-list containing all the filenames of prompts to be delivered in a single HIT.
   - Navigating to https://0.0.0.0:5000/turk/YOUR_TASK_NAME_HERE/1?assignmentId=None&hitId=None&turkSubmitTo=None&workerId=None should direct you to what the first task should look like (not deployed on AMT yet; for testing purposes only.) The URL variables are necessary for AMT.
3. In another terminal window, navigate to `mturk/`, activate the virtual environment, and run `python 1_deploy-hit.py`. This deploys HITs with links to individual tasks on the Flask server. You will get a link to the HITs in the console once this is successful.
4. You have now successfully deployed HITs. The Flask console will output visitor activity, so you can watch as workers (or you) complete tasks. (Tasks deployed on the sandbox will not be visible to workers.)

### Reviewing HITs
 - Run `python 2_list-hits.py` to list all HITs, including information for each HIT such as:
   - HIT id
   - group id
   - type id
   - status (Assignable, Reviewable, Unassignable, etc.)
   - active until date/time
   - number of assignments pending
   - URL to HIT
 - Run `python 3_list-submissions.py` to list all submissions to HITs, showing all information collected during each HIT submission.
 - Run `python 4_autoreview-hits.py` to auto-approve all submissions that passed the criteria for `probably_not_fraud` final data validation test.
   - HIT submission metadata is dumped into JSON files and appended to a running CSV file, both of which are located in the directory specified in `turk_config.txt`. Metadata is sorted into `accepted` and `failed_auto_accept` folders, based on whether they passed `probably_not_fraud`.
 - Run `python 5_manual-accept-hit.py` to manually go through each submission and accept/reject. Recommended to use for all submissions that failed automatic approval by `4_autoreview-hits.py`.
 
 ### Expiring/deleting HITs
 - Run `python 6_expire-hits.py` to expire all HITs (i.e. set HIT lifetime to 0).
 - Run `python 7_delete-hits.py` to delete all expired HITs.


## Methods
### Data collection
Speak's primary purpose is to collect audio recordings from workers, but it also collects additional data, in order to keep a running log of all activities carried out on Speak. Below is a list of all data that is collected for a single HIT submission:
 - `hit_id`: HIT id of HIT submitted
 - `worker_id`: worker ID of AMT worker that completed HIT
 - `datetime_completed`: date/time HIT was completed
 - `elapsed_time`: how long it took (in seconds) for worker to complete HIT
 - `probably_not_fraud`: Whether worker passed final test for fraudulent activity
 - `worker_ip`: IP address of worker
 - `worker_country`, `worker_region`, `worker_city`: worker location info (approximated from IP)
 - `test_idx`: index of sub-list of prompts presented to worker
 - `test_passed`: whether worker passed the test
 - `questions_passed`: all pass/fail results for individual questions within the test
 - Question-specific info:
   - `question_X_img`: question prompt file location
   - `question_X_rec`: worker recording file location
   - `question_X_transcript_loc`: worker recording transcript file location
   - `question_X_transcript`: worker recording transcript, as a string

### Data validation
Speak includes a series of tests that validate whether a worker actually recorded and submitted usable data, in order to remove unusable data and prevent loss of resources due to technical difficulties and/or fraudulent activity. Tests are done at the question- and HIT-level.
 - Question-level:
   - `val1`: transcribes the recorded audio file into a text file; writes "!INAUDIBLE" if no words are detected. (Uses Google SpeechRecognition API, but can be easily modified to use a different speech recognition system)
   - `val1a`: checks whether the number of words transcribed exceeds a certain threshold, defined by the task requester.
   - `val1b`: checks whether the length of the audio recording (in seconds) exceeds a certain threshold, defined by the requester.
   - `val2` (disabled by default): compares the user recording transcript to a ground-truth transcript (provided by the requester), calculates the word-error rate (WER), and checks whether the WER is under a certain threshold, defined by the requester. 
 - HIT-level:
   - `probably_not_fraud`: checks whether the amount of time (in seconds) the worker spent on the task exceeds a certain threshold, defined by the task requester.
  
### Security considerations
- The Flask web application is HTTPS-enabled, and requires SSL certificates to run.
- Submit requests to AMT are handled in the backend, since worker data is sent to AMT using cgi-style variables in a URL. When a worker presses "Submit", a request is sent to the Flask server, which then sends the official submit request to AMT.


## References
 - Matt Diamond's [Recorder.js](https://github.com/mattdiamond/Recorderjs): used (with no modifications) to access the microphone and record audio in-browser
 - Chris Wilson's [Simple volume meter](https://github.com/cwilso/volume-meter): used (with some modifications) for the in-browser volume meter shown to workers during recording
 - [Tuka Alhanai](https://github.com/talhanai/)'s turker-task (link no longer available): used for the foundation of all scripts in `mturk/`
 - Patricia Saylor's [Spoke](https://dspace.mit.edu/bitstream/handle/1721.1/100636/933232677-MIT.pdf): a similar tool designed to work with the old AMT API; used for inspiration
 
