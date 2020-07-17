/*
 * Requires:
 *     psiturk.js
 *     utils.js
 */

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);

var mycondition = condition;  // these two variables are passed by the psiturk server process
var mycounterbalance = counterbalance;  // they tell you which condition you have been assigned to
// they are not used in the stroop code but may be useful to you

// All pages to be loaded
var pages = [
	//"instructions/instruct-ready.html",
    "instructions/instruct-1.html",
    "instructions/practice.html",
	"stage.html",
	"postquestionnaire.html",
    "questions.html"
];

psiTurk.preloadPages(pages);

var instructionPages = [ // add as a list as many pages as you like
	"instructions/instruct-1.html",
    "instructions/practice.html",
   // "instructions/instruct-ready.html"
];


/********************
* HTML manipulation
*
* All HTML files in the templates directory are requested 
* from the server when the PsiTurk object is created above. We
* need code to get those pages from the PsiTurk object and 
* insert them into the document.
*
********************/

/********************
* Legibility Task       *
********************/
var LegibilityExperiment = function() {

    //reaction time is tracked by setting start time once the stimulus has been loaded into the page with show_stimulus() and setting end time once a key response has been registered. rt is calculated by subtracting the start and end time. 
	var stimStartTime, // time word is presented
	    listening = false;
    
    var sliderEvents =[]; //to collect the (moveTime, myTableConfValue) events for each stimulus

	// Altering the Stimuli
	var stims = [
            //[Stimulus name, correct answer, trial type, video location, condition]
			["Other Viewpoint 1", "other", "show_video", "otherRobotV1.mp4", "baseline"],
            ["Other Viewpoint 2", "other", "show_video", "otherRobotV2.mp4", "baseline"],
			["Mine Viewpoint 1", "mine", "show_video", "mineRobotV1.mp4", "baseline"],
            ["Mine Viewpoint 2", "mine", "show_video", "mineRobotV2.mp4", "baseline"],
            //["Mine Viewpoint 1 Human", "mine", "show_video", "CorrectTable.mp4"],
            //["Other Viewpoint 1 Human", "mine", "show_video", "IncorrectTable.mp4"],
            ["Bot Check Trial", "neither", "bot_check", "n/a", "n/a"]
		];


	stims = _.shuffle(stims); //returns a randomized array

	var next = function() {
        //console.log("next called");
		if (stims.length===0) {
            //console.log("finishing because no more stims");
			finish();
		}
		else {
			stim = stims.shift();
            if(stim[2] == "show_video"){
                    document.getElementById("container-exp").style.display = "block";
//                    document.getElementById("container-question").style.display = "none";
                    document.getElementById("container-bot-check").style.display = "none";

                
                    //present stimulus
                    show_stimulus(stim[3]);
                    stimStartTime = new Date().getTime();
                    listening = true;
                
                    var video = document.getElementById("vid");
                
                    //Control Slider values
                    var slider = document.getElementById("confSlider");
                    d3.select("#sliderValueMyTable").html(slider.value+ "%");
                    d3.select("#sliderValueOtherTable").html(slider.value+ "%");

                    slider.onmousedown = function(){
                        console.log("Mouse down");
                        vid.play();
                    }
                    
                    slider.onmouseup = function(){
                        console.log("Mouse up");
                        vid.pause();
                    }
                    
                     //Update the current slider value (each time you drag the slider handle)
                    slider.oninput = function() {
                      d3.select("#sliderValueMyTable").html(100-slider.value + "%");
                      d3.select("#sliderValueOtherTable").html(slider.value + "%");

                      var eventTime = new Date().getTime() - stimStartTime; //time into the trial the event occurs
                      var newEvent = [eventTime, 100-slider.value]; //(moveTime, myTableConfValue)
                      sliderEvents.push(newEvent);
                    }
                    
                    
                    
                
            }
            else{ //check for bot
                document.getElementById("container-exp").style.display = "none";
//                document.getElementById("container-question").style.display = "none";
                document.getElementById("container-bot-check").style.display = "block";
                
                document.getElementById("botcontinue").addEventListener('click', continueClick);
        
                function continueClick(){
                    var botCheckQuestion = document.getElementById("botcheck");
                    var botCheckResponse = botCheckQuestion.value;
                    //console.log(botCheckResponse);
          
                    //Record the scores for this trial
                    psiTurk.recordTrialData({'phase':'BOTCHECK', 'BotCheckResponse':botCheckQuestion.value});
                    psiTurk.saveData();
                            //Do not respond to more clicks
                    document.getElementById("botcontinue").removeEventListener('click', continueClick);
                    //go to next stimulus
                    next();
                }
            }
           
		}
	};
	
	var response_handler = function(e) {
		if (!listening) return;

		var keyCode = e.keyCode,
			response;

		switch (keyCode) {
			case 37:
				// "left arrow" means my table
				response="mine";
				break;
			case 39:
				// "right arrow" means other table
				response="other";
				break;
			case 32:
				// "Space"
				response="skip";
				break;
			default:
				response = "";
				break;
		}
		if (response.length>0) {
            var rt = new Date().getTime() - stimStartTime;
			listening = false;
			var hit = response == stim[1];

			psiTurk.recordTrialData({'phase':"TRIAL",
                                     //'stimulus':stim[0],
                                     //'destination':stim[1],
                                     //'relation':stim[2],
                                     //'response':response,
                                     //'hit':hit,
                                     //'rt':rt,
                                     //'condition':stim[4],
                                     'events':sliderEvents
                                    }
                                   );            
           // go_to_questionnare();
            
            d3.select("#sourceComp").remove();
            
            //reset the slider's starter value to 50
            var slider = document.getElementById("confSlider");
            slider.value = 50;
            
            //reset sliderEvents to be empty
            sliderEvents = [];
            
            next();			
		}
	};

	var finish = function() {
	    $("body").unbind("keydown", response_handler); // Unbind keys
	    currentview = new Questionnaire();
	};
	
	var show_stimulus = function(videoPath) {
        console.log("showing stim: " + videoPath);
		d3.select("#vid").append("source").attr("id", "sourceComp").attr("src", "../static/videos/" + videoPath + "")
	};

    
    
//	var remove_word = function() {
//		d3.select("#sourceComp").remove();
//	};
    
//    var go_to_questionnare = function(){
//        
//        //console.log("Questionnare called");
//        
//        record_responses = function() {
//            //console.log("recording responses");
//            //Get confidence score
//            var selectConfidence = document.getElementById("confidence");
//            var confidenceScore = selectConfidence.options[selectConfidence.selectedIndex];
//            
//          
//            //Record the scores for this trial
//            psiTurk.recordTrialData({'phase':'ConfQuestionsResponse', 'ConfidenceScore':confidenceScore.text});
//            
//        //    psiTurk.recordTrialData({'phase':'ConfQuestions', 'status':'submited'});
//
//	   };
//        
//        document.getElementById("container-question").style.display = "block";
//        document.getElementById("container-exp").style.display = "none";
//        document.getElementById("container-bot-check").style.display = "none";
//        
//       // psiTurk.recordTrialData({'phase':'ConfQuestions', 'status':'begin'});
//        
//        d3.select("#sourceComp").remove();
//        
//        //Make the button respond to a click
//        document.getElementById("cont").addEventListener('click', continueClick);
//        
//        function continueClick(){
//            console.log("button pressed");
//            record_responses();
//            document.getElementById("confExpQuestions").reset();
//            psiTurk.saveData();
//            //Do not respond to more clicks
//            document.getElementById("cont").removeEventListener('click', continueClick);
//            //go to next stimulus
//            next();
//        }
//    }

	
	// Load the stage.html snippet into the body of the page
	psiTurk.showPage('stage.html');

	// Register the response handler that is defined above to handle any
	// key down events.
	$("body").focus().keydown(response_handler); 

	// Start the test
	next();
};



/****************
* POST Questionnaire *
****************/

var Questionnaire = function() {

	var error_message = "<h1>Oops!</h1><p>Something went wrong submitting your HIT. This might happen if you lose your internet connection. Press the button to resubmit.</p><button id='resubmit'>Resubmit</button>";

	record_responses = function() {

        //Difficulty Score
        var selectDifficulty = document.getElementById("difficulty");
        var difficultyScore = selectDifficulty.options[selectDifficulty.selectedIndex];
        
        //Robotics Experience
        var selectExperience = document.getElementById("experience");
        var roboticsExperience = selectExperience.options[selectExperience.selectedIndex]; 
        
        //Free Response
        var freeResponseQuestion = document.getElementById("postcomments");
        var freeResponse = freeResponseQuestion.value;
        
        psiTurk.recordTrialData({'phase':'postquestionnaire', 'difficultyScore':difficultyScore.text, 'hasRoboticsExperience':roboticsExperience.text,
        'additionalComments':freeResponse});
        
		psiTurk.recordTrialData({'phase':'postquestionnaire', 'status':'submit'});

//		$('textarea').each( function(i, val) {
//			psiTurk.recordUnstructuredData(this.id, this.value);
//		});
//		$('select').each( function(i, val) {
//			psiTurk.recordUnstructuredData(this.id, this.value);		
//		});

	};

	prompt_resubmit = function() {
		document.body.innerHTML = error_message;
		$("#resubmit").click(resubmit);
	};

	resubmit = function() {
		document.body.innerHTML = "<h1>Trying to resubmit...</h1>";
		reprompt = setTimeout(prompt_resubmit, 10000);
		
		psiTurk.saveData({
			success: function() {
			    clearInterval(reprompt); 
                psiTurk.computeBonus('compute_bonus', function(){
                	psiTurk.completeHIT(); // when finished saving compute bonus, the quit
                }); 


			}, 
			error: prompt_resubmit
		});
	};

	// Load the questionnaire snippet 
	psiTurk.showPage('postquestionnaire.html');
	psiTurk.recordTrialData({'phase':'postquestionnaire', 'status':'begin'});
	
	$("#next").click(function () {
	    record_responses();
	    psiTurk.saveData({
            success: function(){
                psiTurk.computeBonus('compute_bonus', function() { 
                	psiTurk.completeHIT(); // when finished saving compute bonus, the quit
                }); 
            }, 
            error: prompt_resubmit});
	});
    
	
};

// Task object to keep track of the current phase
var currentview;

/*******************
 * Run Task
 ******************/
$(window).load( function(){
    psiTurk.doInstructions(
    	instructionPages, // a list of pages you want to display in sequence
    	function() { 
            currentview = new LegibilityExperiment(); } // what you want to do when you are done with instructions
    );
});
