# helpers.py
# helper functions
from flask import request
import os


## detect type of question prompt (text, audio, image); pre-process text data
# detects the type of question given by the user-defined question name, through its file extension.
# returns 2 vars:	the correct template to render, in accordance with the file type of the prompt.
# 			the text prompt, as a string. (if not a text prompt, this is a NoneType)
# supported prompt file types: .txt, .wav, .png
# battery: test battery name, as a string
# test: test name, as a string
# question: question name, as a string
# home: home directory of the flask app, as a string
def template_picker(battery, test, question, home):
	path = os.path.join(home,'static','test-files',battery,test)
	template = "recorder_invalid-prompt.html"
	string = ""

	for e in os.listdir(path):
		if question in e:
			if e.endswith(".txt"):
				filename = os.path.join(path,question+'.txt')
				print(filename)
				with open(filename,'r') as content:
					string = content.read()
				template = battery + "/recorder_text-prompt.html"
			elif e.endswith(".wav"):
				if "qual" in e: template = battery + "/recorder_audio-prompt-diag.html"
				else: template = battery + "/recorder_audio-prompt.html"
			elif e.endswith(".png"):
				template = battery + "/recorder_image-prompt.html"
			else:
				template = battery + "/recorder_invalid-prompt.html"

	return template, string


## get all mturk ExternalQuestion arguments
# parses from the URL each argument fed in by mturk. saves each arg in its own variable.
# also saves all args as a string (cgi style), which can be appended to a URL to pass them on during a redirect.
# variable names should be fairly self-explanatory, but for completeness:
# ass_id: mturk var "assignmentId"
# hit_id: mturk var "hitId"
# submit_path: mturk var "turkSubmitTo"
# worker_id: mturk var "workerId"
# arg_string: all mturk vars in a string, readily appendable to the end of a URL
def get_args():
	ass_id = request.args.get('assignmentId')
	hit_id = request.args.get('hitId')
	submit_path = request.args.get('turkSubmitTo')
	worker_id = request.args.get('workerId')

	if submit_path is None:
		if worker_id is None:
			arg_string = ""
	else: 
		arg_string = "?assignmentId=" + ass_id + "&hitId=" + hit_id + "&turkSubmitTo=" + submit_path + "&workerId=" + worker_id

	return ass_id, hit_id, submit_path, worker_id, arg_string


## print a row of two values neatly
# helper function to quickly print argnames and values, pre-formatted for neatness.
def print_row(argName, argVal):
    print("  %-30s %30s" % (argName, argVal))