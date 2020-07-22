from sqlalchemy import create_engine, MetaData, Table
import json
import pandas as pd
import scipy.stats as stats


'''
 START: BOILER PLATE SET UP
'''
db_url = "sqlite:///participants.db"
table_name = 'datacollectiondev'
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

'''
 END: TABLE DEFINITIONS
'''

'''
 START: METHOD DECLARATIONS
'''
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
def get_confidence_at_timestamp(trial, pid, time):
    this_participant = get_trial_row(trial, pid)
    
    if this_participant.empty:
        print("Participant " + pid + " did not complete trial " + str(trial))
        return None
    
    #get the slider event data, access the list (of lists) it is storing
    slider_events = this_participant['events']
    slider_events = slider_events.array[0]
    
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
    
    
#Given a trial (IV, goal, viewpoint) and a uniqueid, return the overall accuracy of the trial 
def get_accuracy_overall(trial, pid):
    print("empty method")

#Given a trial (IV, goal, viewpoint) and a uniqueid, return the overall confidence of the trial 
#Confidence Value = Confidence that the server is approaching MY table
def get_confidence_overall(trial, pid):
    print("empty method")
    

# Return a tuple representing which video this trial presented
# Independent variable: Omn, S,or M 
# Goal Table: 1 = Same Side Before, 2 = Viewpoint, 3 = Same Side After, 4 = Across, 5 = Perpendicular
# Viewpoint: forward, backward, or side
def get_trial(iv, goal, view):
    return (iv, goal, view)

#Return all rows that meet the trial criteria for a specific participant
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
        return None;
    return this_participant
 
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
practiceTrial = ('Omn', '3', 'side')
practiceID = 'debug2J5A7H:debugQAOCVR'
practiceTimeStamp = 4000
##
##print(get_trial_rows(('Omn', '2', 'side')))
##print(get_trial_rows(practiceTrial))
#
#print(get_confidence_at_timestamp(practiceTrial, practiceID, practiceTimeStamp))
print(get_accuracy_at_timestamp(practiceTrial, practiceID, practiceTimeStamp))

'''
 END: DATA PROCESSING
'''


    
