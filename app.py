# app.py
# flask app

# flask libraries
from flask import Flask, request, render_template, redirect, abort, url_for, session
from flask_sslify import SSLify
# python/third-party libraries
from collections import OrderedDict
import os, requests, numpy, urllib, time, argparse, geoip2.database#, librosa
# helpers
import scripts


	
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# setup
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
env = 'production' # 'production' vs. 'sandbox'

with open("app_config.txt", "r+") as config:
	for line in config: exec(line)

localtime = time.asctime(time.localtime(time.time()))
print("\n\n----- NEW SESSION %s, ENVIRONMENT: %s ---------------------------" % (localtime, env))

app = Flask(__name__)
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
app_dir = os.path.abspath(os.path.dirname(__file__))					# global directory var to make code more readable
app.secret_key = 'SooperDooperSecret'							# secret key used for session cookies
iplocator = geoip2.database.Reader(app_dir+'/scripts/geolite2/GeoLite2-City.mmdb')	# ip address location lookup
#sslify = SSLify(app)									# force SSL (to comply with MTurk)

files_list = []

with open(input_files, "r") as f:
	for line in f:
		files_list.append(line.strip("\n"))

# structure: a list of lists
# each sublist contains 4 strings, each a path to a photo to be presented to the user
files_sublists = [files_list[i*n:(i + 1)*n] for i in range((len(files_list)+n-1)//n)]
#print(files_sublists)

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# test
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/')
def hello_world():
	return str(files_sublists)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# STEP 0: initialize test
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/<proctor_name>/<battery_name>/<test_idx>')
def init_test(proctor_name, battery_name, test_idx):
	if proctor_name != 'turk': flask.abort(404)					# for this particular task, only turk allowed
	ass_id, hit_id, submit_path, worker_id, arg_string = scripts.get_args()
	session.clear()									# clear all cookies from other hits, in case multiple hits accomplished in one sitting
	session[ass_id + "_" + test_idx + "_starttime"] = time.time()			# start task timer

	# redirect worker to first question within HIT, multiple_attempts_true = 0 (false)
	return redirect('/' + proctor_name + '/' + battery_name + '/record-voice/' + test_idx + '/0/0' + arg_string)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# STEP 1: record user input
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/<proctor_name>/<battery_name>/record-voice/<test_idx>/<question_idx>/<multiple_attempts_true>')
def record(proctor_name, battery_name, test_idx, question_idx, multiple_attempts_true):
	ass_id, hit_id, submit_path, worker_id, arg_string = scripts.get_args()
	if (multiple_attempts_true == '1'): print('\n  ---- worker recording (failed the first time) -----')
	else: print('\n  ---- worker recording for',battery_name,'(new) -----')
	scripts.print_row('assignmentId:', ass_id)
	scripts.print_row('workerId:', worker_id)
	scripts.print_row('test:', test_idx)
	scripts.print_row('question:', question_idx)

	is_not_preview = (ass_id != None)

	with open(files_sublists[int(test_idx)-1][int(question_idx)], 'r') as fp:
		captionText = fp.read().rstrip()
	
	if (not is_not_preview) or (ass_id + "_" + test_idx + "_starttime" in session):
			return render_template(record_template,
				error=multiple_attempts_true,
				proctor=proctor_name,
				battery=battery_name,
				test=test_idx,
				question=question_idx,
				questionIdx1Based=str(int(question_idx)+1),
				numQuestions=n,
				captionText=captionText,
				assignmentId=ass_id,
				hitId=hit_id,
				turkSubmitTo=submit_path,
				workerId=worker_id,
			is_not_preview=is_not_preview)
	else:
		return render_template('base/cookie_error.html',
			assignmentId=ass_id,
			hitId=hit_id,
			workerId=worker_id,
			turkSubmitTo=submit_path,
			retrySubmitUrl="/{}/{}/{}".format(proctor_name, battery_name, test_idx))


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# STEP 2: upload user input
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/<proctor_name>/<battery_name>/upload-voice/<test_idx>/<question_idx>', methods=['GET', 'POST'])
def upload(proctor_name, battery_name, test_idx, question_idx):
	ass_id, hit_id, submit_path, worker_id, arg_string = scripts.get_args()
	filename = os.path.join(save_location,env,files_sublists[int(test_idx)-1][int(question_idx)].strip(".txt"),worker_id+"_"+ass_id+".wav")
	print('  workerId:', worker_id, 'recorded. uploading to file ' + filename +'...')
	os.makedirs(os.path.dirname(filename), exist_ok=True)
	print('  request.files:',request.files)
	audio_data = request.files['audio_data']
	print('  saving to',filename,'...')
	audio_data.save(filename)			# save original file
	#y, sr = librosa.load(filename, sr=16000)	# downsample to 16kHz
	#os.remove(filename)				# remove original
	#os.rename(filename, filename.rstrip('.wav') + '_original.wav')
	#sf.write(filename, y, sr)	
	print('  workerId:', worker_id, '...upload complete.')

	return ('', 202)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# STEP 3: validate user input
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/<proctor_name>/<battery_name>/validate-voice/<test_idx>/<question_idx>', methods=['GET', 'POST'])
def validate(proctor_name, battery_name, test_idx, question_idx):
	ass_id, hit_id, submit_path, worker_id, arg_string = scripts.get_args()
	print('\n  workerId:', worker_id, 'validating...')

	# validation 1: transcribe worker-uploaded audio file
	filename = os.path.join(save_location,env,files_sublists[int(test_idx)-1][int(question_idx)].strip(".txt"),worker_id+"_"+ass_id+".wav")
	try:
		transcript = scripts.val1(filename)
	except FileNotFoundError:
		return redirect('/' + proctor_name + '/' + battery_name + '/record-voice/' + test_idx + '/' + question_idx + '/1' + arg_string)
	print('    transcript: ' + transcript)

	with open(files_sublists[int(test_idx)-1][int(question_idx)], 'r') as fp:
		gtruth_str = fp.read().rstrip()

	# validation 1a: count number of words transcribed; accept/reject based on # words threshold
	# validation 1b: measure length of audio file; accept/reject based on length threshold
	# output True iff pass val1a and val1b
	# save in user's specific accept_hit gradesheet
	test_numwords = scripts.val1a(transcript, 4)
	test_soundlength = scripts.val1b(filename, 1)
	test_wer = scripts.val2(gtruth_str, transcript)
	print('    val1a (numwords): ' + str(test_numwords))
	print('    val1b (soundlength): ' + str(test_soundlength))
	print('    val2 (WER): ' + str(test_wer))
	#session[ass_id + "_" + test_idx + "_" + question_idx] = test_numwords & test_soundlength# & (test_wer < 0.2)
	session[ass_id + "_" + test_idx + "_" + question_idx] = test_soundlength & bool(test_wer <= 0.5)
	print("    worker passes this task:",session[ass_id + "_" + test_idx + "_" + question_idx])

	if (session[ass_id + "_" + test_idx + "_" + question_idx] != True):
		return redirect('/' + proctor_name + '/' + battery_name + '/record-voice/' + test_idx + '/' + question_idx + '/1' + arg_string)
	else:	
		print('  workerId:', worker_id, 'redirecting...')
		return redirect('/' + proctor_name + '/' + battery_name + '/thanks/' + test_idx + '/' + question_idx + arg_string)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# STEP 4: data collection complete (if applicable, tell mturk that worker is done)
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/<proctor_name>/<battery_name>/thanks/<test_idx>/<question_idx>', methods=['GET', 'POST'])
def complete(proctor_name, battery_name, test_idx, question_idx):
	ass_id, hit_id, submit_path, worker_id, arg_string = scripts.get_args()
	print('\n    workerId:', worker_id, '  successfully redirected. checking if worker completed all questions...')

	filename = os.path.join(save_location,env,files_sublists[int(test_idx)-1][int(question_idx)].strip(".txt"),worker_id+"_"+ass_id+".wav")
	filedir = os.path.dirname(filename)

	# check if user is at last question
	if int(question_idx) != (n-1):
		print('    workerId:', worker_id, 'not yet done. redirecting to next question...')
		next_q = str(int(question_idx) + 1)
		return redirect('/' + proctor_name + '/' + battery_name + '/record-voice/' + test_idx + '/' + next_q + '/0' + arg_string)
	print('    workerId:', worker_id, 'done with all tasks for test', test_idx + '.')

	# calculate how many tasks worker passed; record in CSV file whether worker passed grading criteria (i.e. whether to accept/reject HIT)
	if (proctor_name == 'turk'):
		num_passes = 0
		try:
			for i in range(0,n):
				print('    test',str(i),'passed:', session[ass_id + "_" + test_idx + "_" + str(i)])
				if session[ass_id + "_" + test_idx + "_" + str(i)] == True: num_passes += 1
		except:
			num_passes = 0
		print("    num passes:", num_passes)
		accept_hit = True if (num_passes / n >= accept_criteria) else False
		session[ass_id + "_" + test_idx + "_" + 'overall'] = accept_hit
		print('    workerId:', worker_id + ',', 'assignmentId:', ass_id + ',', '# tests passed:',num_passes,"/",n)
		print('      accept hit:', str(accept_hit) + ',', 'saved.')

	# final thanks + instructions for worker
	print('    workerId:', worker_id, 'done with all questions for test', test_idx,'of',battery_name + '.')
	
	if (proctor_name == 'turk'):
		print('  ---- task complete -------------')
		###
		submit_link = 'https://www.mturk.com/mturk/externalSubmit' if (env == 'production') else 'https://workersandbox.mturk.com/mturk/externalSubmit'

		localtime = time.asctime(time.localtime(time.time()))
		worker_ip = request.environ['REMOTE_ADDR']
		try:
			ip_loc = iplocator.city(worker_ip)
			worker_country = "%s (%s)" % (ip_loc.country.name, ip_loc.country.iso_code)
			worker_region = "%s (%s)" % (ip_loc.subdivisions.most_specific.name, ip_loc.subdivisions.most_specific.iso_code)
			worker_city = ip_loc.city.name
		except:
			worker_country = "N/A"
			worker_region = "N/A"
			worker_city = "N/A"

		elapsed_time = time.time() - session.get(ass_id + "_" + test_idx + "_starttime", 0)
		probably_not_fraud = True if (elapsed_time > 15) else False

		payload = {	'hitId':hit_id, 'assignmentId':ass_id, 'workerId':worker_id, 'turkSubmitTo':submit_link, 'environment':env,
				'datetime_completed':localtime, 'elapsed_time':elapsed_time, 'probably_not_fraud':str(probably_not_fraud),
				'worker_ip':worker_ip, 'worker_country':worker_country, 'worker_region':worker_region, 'worker_city':worker_city,
				'test_idx':test_idx, 'test_passed':session[ass_id + "_" + test_idx + "_" + 'overall'], 'questions_passed':''	}

		for i in range(0,n):
			filename = os.path.join(save_location,env,files_sublists[int(test_idx)-1][i].strip(".txt"),worker_id+"_"+ass_id+"_transcript.txt")
			payload['question_'+str(i)+'_img'] = str(files_sublists[int(test_idx)-1][i])
			payload['question_'+str(i)+'_rec'] = os.path.join(app_dir,'user-content',proctor_name,files_sublists[int(test_idx)-1][i].strip(".txt"),worker_id+"_"+ass_id+".wav")
			payload['question_'+str(i)+'_transcript_loc'] = os.path.join(app_dir,'user-content',proctor_name,files_sublists[int(test_idx)-1][i].strip(".txt"),worker_id+"_"+ass_id+"_transcript.txt")
			with open(filename,'r') as f:
				payload['question_'+str(i)+'_transcript'] = f.read()
			payload['questions_passed'] = payload['questions_passed'] + " " + str(session[ass_id + "_" + test_idx + "_" + str(i)])
		print('final payload:',payload)
		###

		return render_template(thanks_template,
					turkSubmitTo=submit_link,
					payload=payload)
	else:
		return render_template('base/thanks_no-turk.html', nextTask='/'+proctor_name)


# --------------------------------------------------------------------------------------
# STEP 5: submit to mturk
# --------------------------------------------------------------------------------------
@app.route('/<proctor_name>/<battery_name>/submit/<test_idx>', methods=['GET', 'POST'])
def submit(proctor_name, battery_name, test_idx):
	ass_id, hit_id, submit_path, worker_id, arg_string = scripts.get_args()

	print("\nass_id:",ass_id)
	print("hit_id:",hit_id)
	print("submit_path:",submit_path)
	print("worker_id:",worker_id)

	# production vs sandbox environment
	submit_link = 'https://www.mturk.com/mturk/externalSubmit' if (env == 'production') else 'https://workersandbox.mturk.com/mturk/externalSubmit'

	localtime = time.asctime(time.localtime(time.time()))
	worker_ip = request.environ['REMOTE_ADDR']
	try:
		ip_loc = iplocator.city(worker_ip)
		worker_country = "%s (%s)" % (ip_loc.country.name, ip_loc.country.iso_code)
		worker_region = "%s (%s)" % (ip_loc.subdivisions.most_specific.name, ip_loc.subdivisions.most_specific.iso_code)
		worker_city = ip_loc.city.name
	except:
		worker_country = "N/A"
		worker_region = "N/A"
		worker_city = "N/A"

	elapsed_time = time.time() - session.get(ass_id + "_" + test_idx + "_starttime", 0)
	probably_not_fraud = True if (elapsed_time > 15) else False

	payload = {	'hit_id':hit_id, 'assignmentId':ass_id, 'worker_id':worker_id, 'environment':env,
			'datetime_completed':localtime, 'elapsed_time':elapsed_time, 'probably_not_fraud':str(probably_not_fraud),
			'worker_ip':worker_ip, 'worker_country':worker_country, 'worker_region':worker_region, 'worker_city':worker_city,
			'test_idx':test_idx, 'test_passed':session[ass_id + "_" + test_idx + "_" + 'overall'], 'questions_passed':''	}

	for i in range(0,n):
		filename = os.path.join(save_location,env,files_sublists[int(test_idx)-1][i].strip(".txt"),worker_id+"_"+ass_id+"_transcript.txt")
		payload['question_'+str(i)+'_img'] = str(files_sublists[int(test_idx)-1][i])
		payload['question_'+str(i)+'_rec'] = os.path.join(app_dir,'user-content',proctor_name,files_sublists[int(test_idx)-1][i].strip(".txt"),worker_id+"_"+ass_id+".wav")
		payload['question_'+str(i)+'_transcript_loc'] = os.path.join(app_dir,'user-content',proctor_name,files_sublists[int(test_idx)-1][i].strip(".txt"),worker_id+"_"+ass_id+"_transcript.txt")
		with open(filename,'r') as f:
			payload['question_'+str(i)+'_transcript'] = f.read()
		payload['questions_passed'] = payload['questions_passed'] + " " + str(session[ass_id + "_" + test_idx + "_" + str(i)])
	print('final payload:',payload)

	payload = {'assignmentId': ass_id}

	session.clear()
	print('session cleared. ready to submit.')
	print('  ---- task complete -------------')

	turk_submit_final = submit_link + '?' + urllib.parse.urlencode(payload)
	print(turk_submit_final)
	return redirect(turk_submit_final)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	# path to ssl certs goes here
	app.run(host='0.0.0.0', port=5000, ssl_context=(cer, key))








