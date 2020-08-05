from sqlalchemy import create_engine, MetaData, Table
import json
import pandas as pd
import scipy.stats as stats
import matplotlib
matplotlib.use('tkagg')
import matplotlib.pyplot as plt
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as ols
from pingouin import pairwise_tukey

'''
CONSTANTS and FLAGS
'''
ACCURACY_OPTION = 1
UNSURE_WINDOW = 5 #the amount of values around 50 that counts as people being unsure. 0 = participants are only unsure if confidence value is 50
REVERSALS_WINDOW = 5 #the amount of values around 50 that don't count as the participant changing their mind. 0 = participants change their mind every time the confidence value passes 50
RETURN_LIST_OF_AVERAGES = False #if you want the list of all the trials' averages (or total list of reversals) rather than the overall averages
UNSUPPORTED_BROWSER_ERROR = False #for the pilot study, some people used unsupported browsers. If that's the case, this will trigger and adapt the rest of it
'''
 START: BOILER PLATE SET UP
'''
import dbkeys
db_url = dbkeys.db_url
table_name = dbkeys.table_name
data_column_name = dbkeys.data_column_name


# boilerplace sqlalchemy setup
engine = create_engine(db_url)
metadata = MetaData()
metadata.bind = engine
table = Table(table_name, metadata, autoload=True)
# make a query and loop through
s = table.select()
rows = s.execute()


data = []

#status codes of subjects who completed experiment
statuses = [3,4,5,7]
# if you have workers you wish to exclude, add them here
exclude = []
for row in rows:
    # only use subjects who completed experiment and aren't excluded
    if row['status'] in statuses and row['uniqueid'] not in exclude:
        data.append(row[data_column_name])
    
#For use when not excluding participants:
#for row in rows:
#        data.append(row[data_column_name])
#        #ids.append((row['assignmentID'], condition))
        

# Now we have all participant datastrings in a list.
# Let's make it a bit easier to work with:

# parse each participant's datastring as json object
# and take the 'data' sub-object
data = [json.loads(part)['data'] for part in data]

# insert uniqueid field into trialdata in case it wasn't added
# in experiment:
for part in data:
    for record in part:
        record['trialdata']['uniqueid'] = record['uniqueid']
    

    
# flatten nested list so we just have a list of the trialdata recorded
# each time psiturk.recordTrialData(trialdata) was called.
data = [record['trialdata'] for part in data for record in part]

# Put all subjects' trial data into a dataframe object from the
# 'pandas' python library: one option among many for analysis
df = pd.DataFrame(data)
'''
 END: BOILER PLATE SET UP
'''

'''
 START: TABLE DEFINITIONS
'''

#Just stimulus trials
df_trials = df[['uniqueid', 'condition', 'videoduraction', 'phase', 'events', 'IV', 'goaltable', 'viewpoint']] 
df_trials = df_trials[df_trials['phase'] == 'TRIAL']
#print("============Stimulus trials==================")
#print(df_trials)

#Just botcheck trials
df_botcheck = df[['uniqueid', 'phase', 'BotCheckResponse']]
df_botcheck = df_botcheck[df_botcheck['phase'] == 'BOTCHECK']
#print("============Botcheck trials==================")
#print(df_botcheck)

#Just post questionnaire data
df_postquestionnaire = df[['uniqueid', 'phase', 'name','experienceScore', 'gender', 'selfDescribedGender','age','difficultyScore','hardToUnderstand','easierToUnderstand','surprised','expectations','differences','otherComments']]
df_postquestionnaire = df_postquestionnaire[df_postquestionnaire['phase'] == 'POSTQUESTIONAIRE']
#print("============Postquestionnaire questions==================")
#print(df_postquestionnaire)


#Get the set of uniqueids (no duplicates)
idSet = set()
for ind in df.index: #how to iterate through rows
    row = df.loc[ind]
    idSet.add(row['uniqueid'])
    
print("Number of participants: " + str(len(idSet)))
print("participants: "+ str(idSet))

#ageList = []
#for ind in df_postquestionnaire.index: #how to iterate through rows
#    row = df_postquestionnaire.loc[ind]
#    ageList.append(row['age'])

#print("Ages: ")
#for item in ageList:
#    print(item)

#genderList = []
#for ind in df_postquestionnaire.index: #how to iterate through rows
#    row = df_postquestionnaire.loc[ind]
#    genderList.append(row['gender'])

#print("Genders: ")
#for item in genderList:
#    print(item)

'''
 END: TABLE DEFINITIONS
'''


'''
 START: METHOD DECLARATIONS
'''
#Perspectives: "0" or "1". Perspective/Condition 0 is Perspective A  and has their back to the door. Perspective/Condition 1 is Perspective B and is facing the door.
#Pathing Methods: "Omn", "M", "SA", "SB". Omniscient, Multiple, Single (for perspective A), Single (for perspective B)
#Goals: "1", "2", "3", "4". 1 = Front/Before table. 2 = Viewpoint table. 3 = across table. 4 = perpendicular table

'''
Given a perspective and pathing method, returns a list of data frames.
Each data frame represents a trial that used that pathing method from a participant in that perspective condition.
'''
def get_dfs(perspective, pathing_method):
    #only get the dataframes that match this perspective and pathing method
    frames =[]
    for ind in df_trials.index:
        row = df_trials.loc[ind]
        pid = row['uniqueid']
        pathMethod = row['IV']
        condition = row['condition']
    
        if ((int(condition) == int(perspective)) and (pathing_method == pathMethod)):
            frames.append(row)
    return frames

'''
Given a perspective and pathing method, returns the average confidence value from all trials that used that perspective and pathing method

If the goal of the trial is the participant's table, a 90 confidence value means that the participant, on average, reported that they were 90% sure the server was approaching their table. 
If the goal of the trial is not the participant's table, a 90 confidence value means that the participant, on average, reported that they were 90% sure the server was approaching a different table. 

In other words, whatever the goal was, a 100 confidence score represents that they were 100% confidence and their guess was correct. 
'''
def get_avg_confidence_overall(perspective, pathing_method):
    frames = get_dfs(perspective, pathing_method)
    
    #get the average from each frame and add it to averages
    conf_averages = []
    for frame in frames:
        conf_averages.append(get_avg_confidence_trial(frame))
        
    if RETURN_LIST_OF_AVERAGES:
        #return the list of averages rather than an overall average
        return conf_averages
        
    #DEBUG: print(conf_averages)
    sum_averages = 0
    num_trials = len(conf_averages)
    #DEBUG: print(num_trials)
    for value in conf_averages:
        sum_averages = sum_averages + value
        
    overall_average = sum_averages/num_trials
    #DEBUG: print("Overall Average: ", overall_average)
        
    #Take the average of averages. Return that
    return overall_average

'''
Given a perspective and pathing method, returns the average accuracy value from all trials that used that perspective and pathing method

Average accuracy value means the average amount of time the participants were correct during each trial. 
Accuracy value can be calculated as 
    Option 1: (total time correct) / (time correct + time incorrect)
    Option 2: (total time correct + 0.5 * total time unsure) / total time
Which option is being used is determined by the flag ACCURACY_OPTION
'''
def get_avg_accuracy_overall(perspective, pathing_method):
    frames = get_dfs(perspective, pathing_method)
    
    #get the average from each frame and add it to averages
    acc_averages = []
    for frame in frames:
        trial_avg = get_avg_accuracy_trial(frame)
        if trial_avg == None: #Unsupported_browser_error
            continue #Do not include that trial 
        acc_averages.append(get_avg_accuracy_trial(frame))
        
    if RETURN_LIST_OF_AVERAGES:
        #return the list of averages rather than an overall average
        return acc_averages
    
    #Take the average of averages. Return that
    sum_averages = 0
    num_trials = len(acc_averages)
    #DEBUG: print(num_trials)
    for value in acc_averages:
        sum_averages = sum_averages + value
        
    overall_average = sum_averages/num_trials
    #DEBUG: print("Overall Average: ", overall_average)
    
    return overall_average

'''
Given a perspective and pathing method, returns the average number of reversals that happened during all trials that used that perspective and pathing method

Also can collect the times the reversals happens, but does not do anything with them as of now
'''
def get_average_num_reversals_overall(perspective, pathing_method):
    frames = get_dfs(perspective, pathing_method)
    
    #get the average from each frame and add it to averages
    total_reversals = 0
    num_frames = len(frames)
    
    list_of_reversals = []
#    print("Number of frames: ", num_frames)
    for frame in frames:
        reversals_and_times = get_reversals_trial(frame)
        #print(reversals_and_times)
        reversals = reversals_and_times[0]
        times = reversals_and_times[1]
        if reversals == None: #UNSUPPORTED_BROWSER_ERROR
            continue
        list_of_reversals.append(reversals)
        #not using times right now
        #total_reversals = total_reversals + get_reversals_trial(frame)
        total_reversals = total_reversals + reversals
        
    if RETURN_LIST_OF_AVERAGES:
        return list_of_reversals
        
    #Take the average of total reversals. Return that
    avg_reversals = total_reversals/num_frames
    #DEBUG: print("total reversals: ", total_reversals)
    #DEBUG: print("average: ", avg_reversals)
    
    return avg_reversals

'''
Given a dataframe representing a trial row, return the average confidence value reported.

See get_avg_confidence_overall method for description of confidence value
'''
def get_avg_confidence_trial(trial_row):
    #DEBUG: print("==========new avg confidence trial method call ==========")
    
    #the confidence values are in terms of what the participant thinks about the server approaching their table. So if the goal is not their table, the confidence values need to be subtracted from 100. Since, a 0% conf score means that the participant was 100% confident that they were approaching a different table
    goal = trial_row['goaltable']
    goalIsOtherTable = False
    if int(goal) != 2: #if the server was approaching the participant's table 
        goalIsOtherTable = True
        #DEBUG: print("goal is other table")
    
    slider_events = get_slider_events(trial_row)
    num_events = len(slider_events)
    if num_events == 0: #never moved the slider; confidence stayed at 50 the whole time
        return 50
    
    if UNSUPPORTED_BROWSER_ERROR: #issue in pilot study where slider events got recorded at time None
        return None

    video_length = round(trial_row['videoduraction'] * 1000) #round to the nearest millisecond
    
    lengths_values = get_lengths_and_values(slider_events, video_length)
    lengths = lengths_values[0]
    values = lengths_values[1]
    
    #DEBUG: print("Values: ", values)
    if goalIsOtherTable:
        #DEBUG: print("swapping values")
        for i in range(0,num_events):
            values[i] = 100 - values[i]
    #DEBUG: print("Possibly updated values: ", values)
    
    #DEBUG: print("Lenghts: ", lengths)
    #DEBUG: print("Values: ", values)
    
    weighted_sum = 0 #numerator of the average. Will be divided by the length of the video
    for j in range(0, num_events):
        value_scaledby_length = values[j] * lengths[j]
        weighted_sum = weighted_sum + value_scaledby_length
    
    #DEBUG: print("numerator: ", weighted_sum)
    
    weighted_average = weighted_sum / video_length
    
    #DEBUG: print("average: ", weighted_average)
    
    return weighted_average


'''
Given a dataframe representing a trial row, return the average accuracy value.

Average accuracy value means the average amount of time the participants were correct during each trial. 
Accuracy value can be calculated as 
    Option 1: (total time correct + 0.5 * total time unsure) / total time
    Option 2: (total time correct) / (time correct + time incorrect)
Which option is being used is determined by the flag ACCURACY_OPTION
'''
def get_avg_accuracy_trial(trial_row):
#    print("==========new avg accuracy trial method call ==========")
        
    goal = trial_row['goaltable']
    goalIsOtherTable = False
    if int(goal) != 2: #if the server was approaching the participant's table 
        goalIsOtherTable = True
        
    slider_events = get_slider_events(trial_row)
    num_events = len(slider_events)
            
    video_length = round(trial_row['videoduraction'] * 1000) #round to the nearest millisecond
    
    if num_events == 0:
        if ACCURACY_OPTION == 1: #The entire time is spent unsure, so return 0.5
            return 0.5
        else: #ACCURACY_OPTION == 2. No time spent correct or incorrect. Return 0
            return 0

    if UNSUPPORTED_BROWSER_ERROR: #issue in pilot study where slider events got recorded at time None
        return None

    lengths_values = get_lengths_and_values(slider_events, video_length)
    lengths = lengths_values[0]
    values = lengths_values[1]
    
    #the confidence values are in terms of what the participant thinks about the server approaching their table. So if the goal is not their table, the confidence values need to be subtracted from 100. Since, a 0% conf score means that the participant was 100% confident that they were approaching a different table
    if goalIsOtherTable:
        #DEBUG: print("swapping values")
        for i in range(0,num_events):
            values[i] = 100 - values[i]
            
                  
    #once the values are adjusted so that 100% confidence value means that they were 100% confident about the correct thing, a confidence value above 50 means they were correct
    #calculate the average accuracy due to the accuracy option
    weighted_average = None
    if ACCURACY_OPTION == 1: #accuracy avg: (total time correct + 0.5 * total time unsure) / total time
        acc_values = []
        for j in range(0, num_events):
            if values[j] > (50 + UNSURE_WINDOW): #correct
                acc_values.append(1)
            elif values[j] < (50 - UNSURE_WINDOW): #incorrect
                acc_values.append(0)
            else: #unsure
                acc_values.append(0.5)
        
        #DEBUG: print(acc_values)
        
        #scale each accuracy by the length of time of the event
        weighted_sum = 0 #numerator of the average. Will be divided by the length of the video
        for k in range(0, num_events):
            value_scaledby_length = acc_values[k] * lengths[k]
            weighted_sum = weighted_sum + value_scaledby_length
    
        #DEBUG: print("numerator: ", weighted_sum)
        weighted_average = weighted_sum / video_length
    else:   #accuracy avg: (total time correct) / (time correct + time incorrect)
        time_correct = 0
        time_incorrect = 0
        for j in range(0, num_events):
            if values[j] > (50 + UNSURE_WINDOW): #correct
                time_correct = time_correct + lengths[j]
            elif values[j] < (50 - UNSURE_WINDOW): #incorrect
                time_incorrect = time_incorrect + lengths[j]
            else: #unsure
                continue
        
        if time_correct + time_incorrect == 0:
            return 0
        weighted_average = time_correct / (time_correct + time_incorrect)
        
#    print("weighted average using accuracy option " + str(ACCURACY_OPTION) + ": " + str(weighted_average))
    return(weighted_average)
    

'''
Given a dataframe representinga trial_row, returns a tuple that contains the number of reversals the participant made and a list of the timestamps at which the participant makes a reversal
'''    
def get_reversals_trial(trial_row):
    #DEBUG: print("==========new reversals trial method call ==========")
    
    #Since we only care about when it crossed the threshold of 50, we don't care whether the goal was their table or a different table. The two slider sides will be called above_half and below_half instead then
    above_half = 50 + REVERSALS_WINDOW
    below_half = 50 - REVERSALS_WINDOW
    
    slider_events = get_slider_events(trial_row)
    num_events = len(slider_events)
    
    if num_events == 0: #no slider events means no reversals!
        return (0, [])
    
    if UNSUPPORTED_BROWSER_ERROR: #issue in pilot study where slider events got recorded at time None
        return (None, None)

    time_of_reversals = []
    num_reversals = 0
    
    prev_guess = None
    
    for i in range(0,num_events):
        event = slider_events[i]
        value = event[1]
        time = event[0]
        #DEBUG: print("event", event)
        #DEBUG: print("prev_guess: ", prev_guess)
        if prev_guess == None: #no guess yet
            #DEBUG: print("unsure")
            if value >= above_half: #if the new event is an above_half guess
                prev_guess = 'above_half'
            elif value <= below_half:  #if the new event is an below_half guess
                prev_guess = 'below_half'
            else: #the participant is still unsure
                continue
        elif ((value >= above_half) and (prev_guess == 'below_half')): #the new event is an above_half guess and the last event was a below_half guess
            #DEBUG print("reversal because value is above half and previous guess was below half")
            num_reversals = num_reversals + 1
            time_of_reversals.append(time)
            prev_guess = 'above_half'
        elif ((value <= below_half) and (prev_guess == 'above_half')): #the new event is an below_half guess and the last event was a above_half guess
            #DEGUG: print("reversal because value is below half and previous guess was above half")
            num_reversals = num_reversals + 1
            time_of_reversals.append(time)
            prev_guess = 'below_half'
        else:
            continue
    
    #DEBUG: print("num reversals", num_reversals)
    #DEBUG: print("time of reversals", time_of_reversals)
    return (num_reversals, time_of_reversals)
    
    
'''
Given a list of events, create two lists, one of event lengths and one of event values
Event length is the length of time (in milliseconds) from the time the event occurs to the time the next event occurs
'''
def get_lengths_and_values(slider_events, video_length):
    numEvents = len(slider_events)
    
    lengths = []
    values = []
 
    if numEvents == 0:
       # print("no events")
        return (lengths, values)
   
   # print("All: ", slider_events)
    
    #create two list, one of lengths and one of values
    #"length" = how long it was until the next events
    for i in range(0,numEvents - 1):
        event = slider_events[i]
       # print("Event: ", event)
       # print("Next: ", slider_events[i+1])
        next_event = slider_events[i+1]
        timestamp = event[0]
        next_timestamp = next_event[0]
        if timestamp == None: #believe this is another odd case of someone using a non-supported browser, but not sure 
            UNSUPPORTED_BROWSER_ERROR = True
            #print("None timestamp")
            timestamp = 0
        if next_timestamp == None:
            UNSUPPORTED_BROWSER_ERROR = True
            #print("None next_timestamp")
            next_timestamp = 0
        event_length = next_timestamp - timestamp
        lengths.append(event_length)
        
        value = event[1]
        values.append(value)


	    
    #deal with the last event
    #print("NumEvents: ", numEvents)
    last_event = slider_events[numEvents - 1]
    if last_event[0] == None: #unsupported browser issue (probably)
        length_of_last_event = 0
    else:
        length_of_last_event = video_length - last_event[0]
    lengths.append(length_of_last_event)
    last_event_value = last_event[1]
    values.append(last_event_value)
    
    return((lengths, values))
    
    
'''
Given a dataframe/trial_row, return the list (of lists) that represents the slider events from that trial
'''
def get_slider_events(trial_row):
    if trial_row.empty:
        print("Participant " + pid + " did not complete a trial")
        return None
    #get the slider event data, access the list (of lists) it is storing
    slider_events = trial_row['events']
    #if len(slider_events) == 0:
        #print("Participant " + trial_row['uniqueid'] + " reported no events in a trial")
    return slider_events

    

#Confidence Value = Confidence that the server is approaching the PARTICIPANT's table
#Just the raw confidence value
#If a time is given that is greater than the final timestamp or less than one, returns None
def get_raw_confidence_at_timestamp(trial_row, time):
    
    slider_events = get_slider_events(trial_row)
#    print("Slider events we are looking at: " + str(slider_events))
   
 #   print("the time we're looking for is: " + str(time))    

    last_event_time = slider_events[len(slider_events)-1][0]
    first_event_time = slider_events[0][0]
    if time > last_event_time:
        #print("The time is out of range")
        return slider_events[len(slider_events)-1][1]
        #return slider_events[len(slider_events)-1][1] #last_event_value
    elif time < first_event_time:
        #print("The time is out of range")
        return 50 #no move yet, so return 50
        #return slider_events[0][1] #first_event_value
    
    #Find the most recently recorded confidence value to the time provided.
    i = 0
    for event in slider_events:
        timestamp = event[0] #both are ints
        value = event[1]
        if timestamp == time: #found the exact timestamp, report the value
            return value
        elif timestamp > time: #found a greater timestamp, report the previous value
            return slider_events[i-1][1]
        else: #otherwise, continue
            i = i+1
            continue 


#Confidence Value = Confidence that the server is approaching the PARTICIPANT's table
#Just the raw confidence value
#If a time is given that is greater than the final timestamp or less than one, returns None
def average_raw_confidence_trial(perspective, pathing_method, viewpoint, goaltable):
    
    dfs = get_dfs(perspective, pathing_method)
    
    filter_dfs = []
    
    for frame in dfs:
        if (goaltable == frame['goaltable'] and viewpoint == frame['viewpoint']):
            filter_dfs.append(frame)
    
    vidLength = 1000* filter_dfs[0]['videoduraction'] #round to the closest milliseconds
    vidLength = round(vidLength)
    vidLength = int(vidLength)
 
    timestamps = []
    for i in range(0,vidLength,50): #average every 50 milliseconds
        timestamps.append(i)
    timestamps.append(vidLength - 1)
#    print("timestamps", timestamps)

    timestamps = timestamps[1:]
    avg_values = []

    for time in timestamps:
  #      print("*************NEW TIME STAMP: " + str(time) + " ****************")
        values_at_time = []
        for f_frame in filter_dfs:
             temp = get_raw_confidence_at_timestamp(f_frame, time)
 #            print("Temp is "+ str(temp))
             if temp != None:
                 values_at_time.append(temp)
   #     print("values_at_time: ", values_at_time)
        avg_at_time = sum(values_at_time)/len(values_at_time)
    #    print("avg at time: ", avg_at_time)
        avg_values.append(avg_at_time)

    print("avg values: ", avg_values)
    return((timestamps, avg_values))



#Given a trial and uniqueid, plot the participants's confidence values over time
def plot_confidence_all_participants(goaltable, pathing_method, perspective):
    events = average_raw_confidence_trial(perspective, pathing_method, goaltable)
    times = []
    values = []

    for event in events:
        times.append(event[0])
        values.append(event[1])   
 
    plt.plot(times, values)
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Confidence Value "My Table"')
    plt.title('Average Confidence Value Across Participants for Goal Table ' + goaltable + ', Pathing Method' + pathing_method + ', and perspective ' + perspective)
    plt.savefig('plot.pdf')
    plt.show()
            
#   
#Given a trial and uniqueid, plot the participants's confidence values over time
def plot_confidence_one_participant(trial_row):
    events = get_slider_events(trial_row)
    times = []
    values = []

    for event in events:
        times.append(event[0])
        values.append(event[1])   
 
    plt.plot(times, values)
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Confidence Value "My Table"')
    plt.title('Confidence Values for Participant ' + trial_row['uniqueid'] + ' During Trial ' + trial_row['goaltable'] + ', ' + trial_row['IV'])
    plt.savefig('plot.pdf')
    plt.show()
    
'''
 END: METHOD DECLARATIONS
'''

'''
START: graph generation
'''

#dfs = get_dfs("0", "Omn")
#print(dfs[0])
#
#plot_confidence_one_participant(dfs[0])

average_raw_confidence_trial('0', 'M', 'A', '1')
