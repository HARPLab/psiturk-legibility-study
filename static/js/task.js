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
    "instructions/instruct-2.html",
    "instructions/instruct-3.html",
    "instructions/slider-practice.html",
    "instructions/instruct-4.html",
    //"instructions/practice.html",
	"stage.html",
	"postquestionnaire.html",
    "questions.html"
];

psiTurk.preloadPages(pages);

var instructionPages = [ // add as a list as many pages as you like
	"instructions/instruct-1.html",
    "instructions/instruct-2.html",
    "instructions/instruct-3.html",
    "instructions/slider-practice.html",
    "instructions/instruct-4.html",
   // "instructions/practice.html",
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
//	var stimStartTime, // time word is presented
//	    stimPauseTime,
//        stimPlayTime,
//        listening = false;
    
    var sliderEvents =[]; //to collect the (moveTime, myTableConfValue) events for each stimulus

	// Altering the Stimuli
	var stims = [
            //TODO: Remove stimulus name and correct answer, update rest of code
            //TODO: add IV, goal table, and viewpoint to the trial recorded data
        
            //[Stimulus name, trial type, video location, independent variable (Omn, S,or M), goal table (1 = Before Table, 2 = Pespective Table, 3 = Across, 4 = Perpendicular), viewpoint (A or B)]
			["Other Viewpoint 1", "show_video", "otherRobotV1.mp4", "M", "3", "A"],
            ["Other Viewpoint 2", "show_video", "otherRobotV2.mp4", "SA", "3", "A"],
			["Mine Viewpoint 1", "show_video", "mineRobotV1.mp4", "SB", "2", "A"],
            ["Mine Viewpoint 2", "show_video", "mineRobotV2.mp4", "Omn", "2", "A"],
            //["Mine Viewpoint 1 Human", "mine", "show_video", "CorrectTable.mp4"],
            //["Other Viewpoint 1 Human", "mine", "show_video", "IncorrectTable.mp4"],
            ["Bot Check Trial", "bot_check", "n/a", "n/a"]
		];
    
    if mycondition == '0':
        console.log("Condition is 0! yay")
    else:
        console.log("Condition is 1! yay")


	stims = _.shuffle(stims); //returns a randomized array

	var next = function() {
        //DEBUG: console.log("next called");
		if (stims.length===0) {
            //DEBUG: console.log("finishing because no more stims");
			finish();
		}
		else {
			stim = stims.shift();
            var stimStartTime, // time word is presented
	            stimPauseTime,
                stimPlayTime;
            
            if(stim[1] == "show_video"){
                document.getElementById("container-exp").style.display = "block";
                document.getElementById("container-instructions").style.display = "none";
                document.getElementById("container-bot-check").style.display = "none";
                document.getElementById("container-slider-info").style.display = "block";


                //present stimulus
                show_stimulus(stim[2]);
//                stimStartTime = new Date().getTime();
//                listening = true;

                var video = document.getElementById("vid");

                video.onended = function(){
                    //DEBUG: console.log("The video has ended");
                    trialEnded(stim);
                }

                //Control Slider values
                var slider = document.getElementById("confSlider");
                
                //ensure the slider's value has been reset
                //DEBUG:console.log("in next! slider value is: " + slider.value);
                slider.value = 50;
                
                d3.select("#sliderValueMyTable").html(100-slider.value+ "%");
                d3.select("#sliderValueOtherTable").html(slider.value+ "%");
                
                
                

                slider.onmousedown = function(){
                    //DEBUG: console.log("Mouse down");
                    
                    if (typeof stimStartTime == 'undefined'){
                        stimStartTime = new Date().getTime(); //First time video starts
                        //DEBUG: console.log("video start time: " + stimStartTime.toString());
                    }
                    else {
                        //console.log("start after a pause");
                        stimPlayTime = new Date().getTime(); //Time play begins again
                        var pauseTime = stimPlayTime - stimPauseTime; //calculate length of pause
                       //DEBUG: console.log("length of pause " + pauseTime.toString());
                        stimStartTime = stimStartTime + pauseTime; //update start time to compensate for the pause
                    }
                    
                    document.getElementById("container-slider-info").style.display = "none";
                    video.play();
                }

                slider.onmouseup = function(){
                    //DEBUG: console.log("Pause");
                    stimPauseTime = new Date().getTime();
                    d3.select("#container-slider-info").html("The video has not finished playing. Please hold the slider to advance video and indicate confidence.");
                    document.getElementById("container-slider-info").style.display = "block";
                    video.pause();
                }

                 //Update the current slider value (each time you drag the slider handle)
                slider.oninput = function() {
                  d3.select("#sliderValueMyTable").html(100-slider.value + "%");
                  d3.select("#sliderValueOtherTable").html(slider.value + "%");

                  var eventTime = new Date().getTime() - stimStartTime; //time into the trial the event occurs
                  var newEvent = [eventTime, 100-slider.value]; //(moveTime, myTableConfValue)
                  //DEBUG: console.log("newEvent logged: " + newEvent.toString());
                  sliderEvents.push(newEvent);
                }




            }
            else{ //check for bot
                document.getElementById("container-exp").style.display = "none";
                document.getElementById("container-instructions").style.display = "none";
                document.getElementById("container-bot-check").style.display = "block";
                document.getElementById("container-slider-info").style.display = "none";
                
                document.getElementById("botcontinue").addEventListener('click', continueClick);
        
                function continueClick(){
                    var botCheckQuestion = document.getElementById("botcheck");
                    var botCheckResponse = botCheckQuestion.value;
                    //DEBUG: console.log(botCheckResponse);
          
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
	
	var finish = function() {
//	    $("body").unbind("keydown", response_handler); // Unbind keys
	    currentview = new Questionnaire();
	};
	
	var show_stimulus = function(videoPath) {
        //DEBUG: console.log("showing stim: " + videoPath);
        d3.select("#video-container").append("video").attr("id", "vid").attr("width","620").attr("height", "540");
		d3.select("#vid").append("source").attr("id", "sourceComp").attr("src", "../static/videos/" + videoPath + "")
	};

    
var trialEnded = function(stimulus) {
    //DEBUG: console.log("trial ended");
    document.getElementById("container-exp").style.display = "none";
    document.getElementById("container-instructions").style.display = "block";
    document.getElementById("container-bot-check").style.display = "none";
    document.getElementById("container-slider-info").style.display = "none";
    
    var video = document.getElementById("vid");
    trial_duration = video.duration;
    
    psiTurk.recordTrialData({'phase':"TRIAL",
                             'IV': stimulus[3],
                             'goaltable': stimulus[4],
                             'viewpoint': stimulus[5],
                             'events':sliderEvents,
                             'condition':mycondition,
                             'videoduraction':trial_duration
                            }
                           );            

    d3.select("#sourceComp").remove();
    d3.select("#vid").remove();

    //reset the slider's starter value to 50
    var slider = document.getElementById("confSlider");
    //DEBUG: console.log("slider's value is:" + slider.value +"; it will now be reset:");
    slider.value = 50;
    //DEBUG: console.log("slider's value is now:" + slider.value);

    //reset sliderEvents to be empty
    sliderEvents = [];
    
    //reset the message about holding the slider
    d3.select("#container-slider-info").html("Hold the slider to play the video and indicate confidence.");

    //Make the button respond to a click
    document.getElementById("cont").addEventListener('click', continueClick);

    function continueClick(){
        //DEBUG: console.log("continue button pressed");
        psiTurk.saveData();
        //Do not respond to more clicks
        document.getElementById("cont").removeEventListener('click', continueClick);
        //go to next stimulus
        next();
    }
    
    //next();			
    
}

    
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
//	$("body").focus().keydown(response_handler); 

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
        
        //Expectation Score
        var selectExpectation = document.getElementById("expectations");
        var expectationScore = selectExpectation.options[selectExpectation.selectedIndex];
        
        //Did anything make it hard to understand?
        var hardToUnderstand = document.getElementById("hardtounderstand");
        var hardToUnderstandResponse = hardToUnderstand.value;
        
        //Any changes that could have made it easier to understand?
        var easierToUnderstand = document.getElementById("easiertounderstand");
        var easierToUnderstandResponse = easierToUnderstand.value;
        
        //Other comments?
        var otherComments = document.getElementById("othercomments");
        var freeResponse = otherComments.value;
        
        //Experience
        var selectExperience = document.getElementById("experience");
        var experienceScore = selectExperience.options[selectExperience.selectedIndex];
        
        //Gender
        var selectGender = document.getElementById("gender");
        var gender = selectGender.options[selectGender.selectedIndex];
        
        //Self describe gender
        var selfDescribeGender = document.getElementById("selfdescribegender");
        var selfGender = selfDescribeGender.value;
        
        //Age
        var describeAge = document.getElementById("age");
        var age = describeAge.value;
        
        //Country
        var describeCountry = document.getElementById("country");
        var country = describeCountry.value;
        
        
        psiTurk.recordTrialData({'phase':'POSTQUESTIONAIRE',
                                 'difficultyScore':difficultyScore.text, 
                                 'expectationScore':expectationScore.text, 
                                 'hardToUnderstand':hardToUnderstandResponse,
                                 'easierToUnderstand':easierToUnderstandResponse,
                                 'otherComments':freeResponse,
                                 'experienceScore':experienceScore.text, 
                                 'gender':gender.text,
                                 'selfDescribedGender':selfGender,
                                 'age':age,
                                 'country':country
                                });
        
//		psiTurk.recordTrialData({'phase':'postquestionnaire', 'status':'submit'});

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
//	psiTurk.recordTrialData({'phase':'postquestionnaire', 'status':'begin'});
	
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
