/*
	progress-bar, by Christopher Song

	Special considerations when implementing this library into an HTML document/template:
	 - filename must contain progress as a proportion (ex. 1a_3_fox is module 1 of 3)
	 - filename (var name) fed in dynamically thru HTML template
*/
// var name = "1a_3_fox"
var part = parseInt(name.split('_')[0]) - 1;
var whole = parseInt(name.split('_')[1]);
var percent = part/whole;
var c = document.getElementById("progbar");

// background fill properties
var bgCtx = c.getContext("2d");
bgCtx.fillStyle = "#4dd2ff";
bgCtx.fillRect(0,0,400*percent,100);

// text properties
var txtCtx = c.getContext("2d");
txtCtx.font = "10px Arial";
txtCtx.fillStyle = "#000000";
txtCtx.textAlign = "center";
txtCtx.fillText(parseInt(percent*100) + "% complete", progbar.width/2, progbar.height*.8);