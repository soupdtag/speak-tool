# validation.py
# validation functions
import os, csv
from jiwer import wer
import speech_recognition as sr
import soundfile as sf



## validation 1 - google speech api transcription
# 1. transcribes a given file audio_file, using Google Speech Recognition API
# 2. saves the transcript in a .txt file in the same directory
# 3. returns the transcript as a string
# audio_file: path of the audio file to be transcribed (including extension), as a string
# transc: the resultant transcript, as a string
def val1(audio_file):
	r = sr.Recognizer()
	transc = "!INAUDIBLE"

	with sr.AudioFile(audio_file) as source:
    		audio = r.record(source)

	with open(os.path.splitext(audio_file)[0] + '_transcript.txt', 'w') as output:
		try:
			transc = r.recognize_google(audio)
			output.write(transc)
		except sr.UnknownValueError:
			# Google Speech Recognition API could not understand audio
			transc = "!INAUDIBLE"
			output.write(transc)
		except sr.RequestError as e:
			# Could not request results from Google Speech Recognition API
			transc = "!REQUEST_ERROR_{0}".format(e)
			output.write(transc)

	return(transc)


## validation 1a - transcript word threshold check
# given the transcript as a string, find whether the number of words in transcript is greater than the threshold
# threshold: # of words, as an int
# outputs boolean value; True if passes threshold check, False otherwise
def val1a(transcript, threshold):
	return len(transcript.split()) > threshold


## validation 1b - audio file length threshold check
# given the audiofile path as a string, find whether the length of the recording is greater than the threshold
# threshold: # of seconds, as an int
# outputs boolean value; True if passes threshold check, False otherwise
def val1b(file_path, threshold):
	f = sf.SoundFile(file_path)
	length = len(f) / f.samplerate
	return length > threshold


## validation 2 - comparison w/ transcript
# 1. finds the ground-truth transcript associated with the question.
# 2. calculates the WER (word error rate) for the subject-generated transcript, based on the ground truth.
# 3. saves the WER in a text file in the subject's folder (within the folder for the battery and test), located in user-content.
#	(user-content/proctor/battery/subject/test/question_wer.txt)
# 4. returns the WER as a float
# transcript: the user-generated transcript, as a string
# question: the name of the question the user was given, as a string
def val2(gtruth_str, transcript_str):#, question, test, battery, proctor, subject):
#	save_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","user-content")),proctor,battery,subject,test,question+"_wer.txt")
        word_error_rate = wer(gtruth_str, transcript_str)
        char_error_rate = wer(' '.join(list(gtruth_str)), ' '.join(list(transcript_str)))
        if 'mmm mmm mmm mm mm mmm' in gtruth_str:
                return 0.0
        if len(gtruth_str.split(' ')) > 20:
                return 0.0
        error_rate = min(word_error_rate, char_error_rate)
        return error_rate
#	with open(save_path, 'w+') as f:
#		f.write(str(error_rate))
