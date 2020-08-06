from sqlalchemy import create_engine, MetaData, Table
import json
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt


'''
 START: BOILER PLATE SET UP
'''
db_url = "sqlite:///participants.db"
table_name = 'datacollectiondev2'
data_column_name = 'datastring'
# boilerplace sqlalchemy setup
engine = create_engine(db_url)
metadata = MetaData()
metadata.bind = engine
table = Table(table_name, metadata, autoload=True)
# make a query and loop through
s = table.select()
rows = s.execute()


data = []

#For use in excluding participants:
    ##status codes of subjects who completed experiment
    #statuses = [3,4,5,7]
    ## if you have workers you wish to exclude, add them here
    #exclude = []
    #for row in rows:
    #    # only use subjects who completed experiment and aren't excluded
    #    if row['status'] in statuses and row['uniqueid'] not in exclude:
    #        data.append(row[data_column_name])
    
#For use when not excluding participants:
for row in rows:
        data.append(row[data_column_name])

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
    #print(part)

    
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
df_trials = df[['uniqueid', 'phase', 'events', 'IV', 'goaltable', 'viewpoint']] 
df_trials = df_trials[df_trials['phase'] == 'TRIAL']
#print("============Stimulus trials==================")
#print(df_trials)

#Just botcheck trials
df_botcheck = df[['uniqueid', 'phase', 'BotCheckResponse']]
df_botcheck = df_botcheck[df_botcheck['phase'] == 'BOTCHECK']
#print("============Botcheck trials==================")
#print(df_botcheck)

#Just post questionnaire data
df_postquestionnaire = df[['uniqueid', 'phase', 'difficultyScore', 'hasRoboticsExperience', 'additionalComments']]
df_postquestionnaire = df_postquestionnaire[df_postquestionnaire['phase'] == 'postquestionnaire']
#print("============Postquestionnaire questions==================")
#print(df_postquestionnaire)


#Get the set of uniqueids (no duplicates)
idSet = set()
for ind in df.index: #how to iterate through rows
    row = df.loc[ind]
    idSet.add(row['uniqueid'])
    
#DEBUG:print(idSet)

'''
 END: TABLE DEFINITIONS
'''

'''
 START: METHOD DECLARATIONS
'''
#Return row that meets the trial criteria for a specific participant
#returns an empty empty dataframe if no such rows exist
def get_trial_row(trial, pid):
    iv = trial[0]
    goal = trial[1]
    view = trial[2]
    #get all the rows that match that trial specification
    all_participants = df_trials[(df_trials['IV'] == iv) & (df_trials['goaltable'] == goal) & (df_trials['viewpoint'] == view)]
    if all_participants.empty:
        return None;
    #find the specified participant
    this_participant = all_participants[all_participants['uniqueid'] == pid]
    if this_participant.empty:
        print("Participant " + pid + " did not complete trial " + str(trial))
        return None
    print("THIS PARTICIPANT", this_participant)
    return this_participant

#Return rows that meets the trial criteria for all participants
#returns an empty empty dataframe if no such rows exist
def get_trial_row_all_participants(trial):
    frames =[]
    
    for ID in idSet:
        frames.append(get_trial_row(trial,ID))
        
    result = pd.concat(frames)
#    print(result)
    return result
    
    

#Given a trial row, returns the list of lists that represents the slider events that took place during that trial
def get_slider_events(trial_row):

    if trial_row.empty:
        print("Participant " + pid + " did not complete trial " + str(trial))
        return None
    
    #get the slider event data, access the list (of lists) it is storing
    slider_events = trial_row['events']
#    print("IN GET_SLIDER_EVENTS", slider_events)
    slider_events = slider_events.array[0]
    return slider_events

#Given a trial (IV, goal, viewpoint), a timestamp, and a uniqueid, return the accuracy at that timestamp 
#If confidence value is greater than 50 and the robot is approaching their table: Accurate (True)
#If confidence value is less than 50 and the robot is not approaching their table: Accurate (True)
#If confidence value is 50, returns None 
#Otherwise, they were inaccurate (False)
def get_accuracy_at_timestamp(trial, pid, time):
    conf_val = get_confidence_at_timestamp(trial, pid, time) #conf_val is how sure they are that the server is approaching their table
    
    if conf_val == None:
        print("The time is out of range or Participant " + pid + " did not complete trial " + str(trial))
        return None
    
    #DEBUG: print(conf_val)
    correct_answer = trial[1] #table 2 is participant's table, any others is a different table
    #DEBUG: print(correct_answer)
    if conf_val == 50:
        return None
    elif (correct_answer == '2' and conf_val > 50):
        return True
    elif (correct_answer != '2' and conf_val < 50):
        return True
    else:
        return False
    
#Given a trial (IV, goal, viewpoint), a timestamp, and a uniqueid, return the confidence at that timestamp 
#Confidence Value = Confidence that the server is approaching the PARTICIPANT's table
#If a time is given that is greater than the final timestamp or less than one, returns None
def get_confidence_at_timestamp(trial_row, time):
    
    slider_events = get_slider_events(trial_row)
    print(slider_events)
    
    last_event_time = slider_events[len(slider_events)-1][0]
    if time > last_event_time:
        print("The time is out of range")
        return None
        #return slider_events[len(slider_events)-1][1] #last_event_value
    elif time < 1:
        print("The time is out of range")
        return None
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
    
    
#Given a trial (IV, goal, viewpoint) and a uniqueid, return the overall accuracy of the trial.
#Will return True is the participant was correct for a longer period of time than they were wrong
#Does not consider timestamps when the participant had 50% confidence
def get_accuracy_overall(trial_row):
    
    slider_events = get_slider_events(trial_row)
    num_events = len(slider_events)
    total_correct_time = 0
    total_incorrect_time = 0
    
    #TODO: UPDATE WITH LENGTH OF VIDEO
    end_of_video = slider_events[num_events-1][0] #ONlY FOR NOW
    
    num_events = len(slider_events)
    #DEBUG: print("num events", num_events)
    
    for i in range(0,num_events-1):
        cur_event_timestamp = slider_events[i][0] #time of current event
        next_event_timestamp = slider_events[i+1][0] #time of next event
        time_until_change = next_event_timestamp - cur_event_timestamp #time between current event and next event
#        print("cur", cur_event_timestamp)
#        print("next", next_event_timestamp)
#        print("dif", time_until_change)
        
        #add the amount of time between current event and next event to either total correct time or total incorrect time, depending on the accuracy at the timestamp
        cur_trial_accuracy = get_accuracy_at_timestamp(trial, pid, cur_event_timestamp)
        if cur_trial_accuracy == None: 
            continue
        elif cur_trial_accuracy: #if true (correct)
            total_correct_time = total_correct_time + time_until_change
        else: #if false (incorrect)
            total_incorrect_time = total_incorrect_time + time_until_change

    #add the time after the final event
    last_event_time = slider_events[num_events-1][0]
    #DEBUG:print("last stamp", last_event_time)
    
    time_until_change = end_of_video - last_event_time
    last_trial_accuracy = get_accuracy_at_timestamp(trial, pid, last_event_time)
    if last_trial_accuracy: #if true (correct)
        total_correct_time = total_correct_time + time_until_change
    elif not last_trial_accuracy: #if false (incorrect)
         total_incorrect_time = total_incorrect_time + time_until_change
    #else, if none, do neither
       

    #DEBUG: print(total_correct_time)
    #DEBUG: print(total_incorrect_time)
    
    if total_correct_time > total_incorrect_time:
        return True
    else:
        return False
    

    
#Given a trial (IV, goal, viewpoint) and a uniqueid, return the overall confidence of the trial 
#Confidence Value = Confidence that the server is approaching MY table
def get_confidence_overall(trial_row):
    print("empty method")
    return None
 


#Given a  trial (IV, goal, viewpoint) and a uniqueid, return the last timestamp when the participant was wrong
def get_last_incorrect_timestamp(trial_row):
    print("empty method")
    return None


#Given a  trial (IV, goal, viewpoint) and a uniqueid, return the last timestamps when the participant changed their mind.
#
def get_reversal_timestamps(trial_row):
    print("empty method")
    return None

#Given an IV (Omn, S, M), return a dictionary of trials and their accuracies
def get_overall_accuracy_across_IV(iv):
    print("empty method")
    return None

#Given an IV (Omn, S, M), return a dictionary of trials and their confidences
def get_overall_confidence_across_IV(iv):
    print("empty method")
    return None

#for plotting time by confidence
def separate_timestamps_and_values(trial_row):
    slider_events = get_slider_events(trial_row)
    timestamps = []
    confValues = []
    for event in slider_events:
        timestamps.append(event[0])
        confValues.append(event[1])
    return((timestamps, confValues)) 

#Given a trial and uniqueid, plot the participants's confidence values over time
def plot_confidence_one_participant(trial_row):
    events = separate_timestamps_and_values(trial_row)
    times = events[0]
    values = events[1]
    
    plt.plot(times, values)
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Confidence Value "My Table"')
    plt.title('Confidence Values for Participant ' + pid + ' During Trial ' + str(trial))
    plt.show()
    
#Given a trial, plot all participants' confidence values over time
def plot_confidence_all_participants(trial):
    frames = get_trial_row_all_participants(trial)
    
    for ind in frames.index:
        row = frames.loc[ind]
        pid = row['uniqueid']
        print("PASSING", row)
        events = separate_timestamps_and_values(row)
        times = events[0]
        values = events[1]
        plt.plot(times, values)
    
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Confidence Value "My Table"')
    plt.title('Confidence Values for All Participants During Trial ' + str(trial))
    plt.show()
        


 
'''
 END: METHOD DECLARATIONS
'''


'''
 START: DATA PROCESSING
'''

#Get the set of uniqueids (no duplicates)
#idSet = set()
#for ind in df.index: #how to iterate through rows
#    row = df.loc[ind]
#    idSet.add(row['uniqueid'])
#
#DEBUG:
##test the get_trial method   
#for ind in df_trials.index:
#    row = df.loc[ind]
#    trial = get_trial(row['IV'], row['goaltable'], row['viewpoint'])
#
practiceTrial = ('Omn', '2', 'side')
practiceID = 'debugR670K8:debugRTWCKD'
practiceTimeStamp = 4000
##
##print(get_trial_rows(('Omn', '2', 'side')))
##print(get_trial_rows(practiceTrial))
#
print(get_confidence_at_timestamp(get_trial_row(practiceTrial, practiceID), practiceTimeStamp))
#print(get_accuracy_overall(get_trial_row(practiceTrial, practiceID)))
##plot_confidence_one_participant(practiceTrial, practiceID)
#
#get_trial_row_all_participants(practiceTrial)
#      
plot_confidence_all_participants(practiceTrial)

'''
 END: DATA PROCESSING
'''


    
