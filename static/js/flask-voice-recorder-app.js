/*
	recorder_app, by Christopher Song

	other necessary libraries:
	 - Recorder.js (Michael Diamond)
	 - volume-meter (Chris Wilson)
	
	Special considerations when implementing this library into an HTML document/template:
	 - declare vars "upload_link" and "next_link" in HTML template
	 - record button id = "recBtn"
*/

// browser engine-dependent vars
URL = window.URL || window.webkitURL;
var AudioContext = window.AudioContext || window.webkitAudioContext;
navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia;

// user mic input vars
var audioContext;	// audioContext object
var gumStream;		// getUserMedia() stream
var rec;		// Recorder.js object
var input;		// MediaStreamAudioSourceNode

// volume meter vars
var meter = null;
var canvasContext = null;
var meter_width=250;
var meter_height=50;
var rafID = null;

// meter colors
var notRec_notClip = "#ffa64d" 
var notRec_Clip = "#ff4d4d"
var Rec_notClip = "#4dd2ff"
var Rec_Clip = "#ff4d4d"


// --------------------------------------------------------------------------------------
// volume meter
// --------------------------------------------------------------------------------------

// on page load: initialize volume meter
window.onload = function() {
	// get user's permission to access microphone
	console.log("  initializing getUserMedia()...");
	navigator.mediaDevices.getUserMedia({ audio: true, video: false })
	.then(function(stream) {
		console.log("  getUserMedia() stream created.");

		// create an audio context after getUserMedia is called
		audioContext = new AudioContext();
		console.log("  audioContext created.");

		// save stream; configure audioContext
		gumStream = stream;
		input = audioContext.createMediaStreamSource(stream);
		console.log("  stream saved.");

		// start volume meter
		canvasContext = document.getElementById("meter").getContext("2d");
		meter = createAudioMeter(audioContext);
		input.connect(meter);
		console.log("  volume meter initialized.");
		drawLoop();
	}).catch(function(e) {
			console.log("  error: getUserMedia() failed");
			console.log(e);
			//alert("Error: failed to initialize recorder stream. Please refresh the page and ensure that this website has access to your microphone.");
		});
}


// volume meter refresh: draw the bar in the volume meter (loop)
function drawLoop(time) {
	// clear background
	canvasContext.clearRect(0,0,meter_width,meter_height);

	// fill color, based on whether user is recording + whether user is clipping
	if ((typeof rec == 'object') && rec.recording) {
		// user is recording
		if (meter.checkClipping())
			canvasContext.fillStyle = Rec_Clip;
		else
			canvasContext.fillStyle = Rec_notClip;
	} else {
		// user is not recording
		if (meter.checkClipping())
			canvasContext.fillStyle = notRec_Clip;
		else
			canvasContext.fillStyle = notRec_notClip;
	}

	// draw a bar based on the current volume
	canvasContext.fillRect(0, 0, meter.volume*meter_width, meter_height);

	// set up the next visual callback
	rafID = window.requestAnimationFrame(drawLoop);
}


// --------------------------------------------------------------------------------------
// start/stop/submit recording
// --------------------------------------------------------------------------------------

// record button element + click event listener
var recBtn = document.getElementById("recBtn");
recBtn.addEventListener("click", recStartStop);


// on record button click: determine button functionality, based on whether already recording or not
function recStartStop() {
	console.log("rec button clicked");

	if ((typeof rec == 'object') && rec.recording) {
		// if already recording, stop recording and submit
		recStopSubmit();
	} else {
		// if not already recording, start recording
		recStart();
	}
}


// initialize Recorder.js object + start recording
function recStart() {
	console.log("starting recording...");

	// create recorder object; configure to record mono sound (1 channel)
	rec = new Recorder(input,{numChannels:1});

	// start the recording process
	rec.record();
	console.log("started recording");

	// record button is now a stop button
	recBtn.className = 'button stopButton';
	recBtn.innerHTML = 'Stop';
	status_msg.innerHTML = 'Now recording. Press the "Stop" button below to stop recording.';
	document.getElementById("example").className = "hidden";
}


// stop recording
function recStopSubmit() {
	console.log("stopping recording...");

	// record button tells user it is now submitting the recording
	recBtn.disabled = true;
	recBtn.className = 'button disabledButton';
	recBtn.innerHTML = 'Submitting...';

	// stop volume meter
	meter.shutdown();

	// stop recording + getUserMedia() stream (mic access)
	rec.stop();
	gumStream.getAudioTracks()[0].stop();

	console.log("stopped recording.");

	// create wav blob; pass blob to recSubmit() function
	rec.exportWAV(recSubmit);
}


// submit recording + redirect user to another website (create download link code included as well)
function recSubmit(blob) {
	console.log("submitting recording...");
	status_msg.innerHTML = 'Now submitting your recording.';

	var url = URL.createObjectURL(blob);

	// .wav file name (without extension)
	var filename = new Date().toISOString();

	// create download link
	/*
	var link = document.createElement('a');
	link.href = url;
	link.download = filename+".wav";
	link.innerHTML = "Save to disk";
	*/

	// assemble form data to be submitted to URL upload_link
	// (upload_link var declared in recorder template)
	var fd = new FormData();
	fd.append("audio_data", blob, filename);

	// send POST request to URL upload_link (async), then redirect user to next link
	postRequestAsync(upload_link, next_link, fd).then(next => redirectUser(next));
}
 
async function postRequestAsync(upload, next, file) {
	let response = await fetch(upload, {method: "POST", body: file});
	console.log("recording submitted.");
	return next;
}

// redirect user to URL next_link
// (next_link var declared in recorder template)
function redirectUser(nextLink) {
	console.log("redirecting user...");
	window.location.replace(nextLink);
}