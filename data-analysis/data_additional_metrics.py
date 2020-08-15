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
import pingouin as pg
import copy
import seaborn as sns
import numpy as np

'''
CONSTANTS and FLAGS
'''
ACCURACY_OPTION = 1
UNSURE_WINDOW = 5 #the amount of values around 50 that counts as people being unsure. 0 = participants are only unsure if confidence value is 50
REVERSALS_WINDOW = 5 #the amount of values around 50 that don't count as the participant changing their mind. 0 = participants change their mind every time the confidence value passes 50
RETURN_LIST_OF_AVERAGES = False #if you want the list of all the trials' averages (or total list of reversals) rather than the overall averages
UNSUPPORTED_BROWSER_ERROR = False #for the pilot study, some people used unsupported browsers. If that's the case, this will trigger and adapt the rest of it

FILENAME_OUTPUTS = "outputs/"
FILENAME_PLOTS = FILENAME_OUTPUTS + "plots/"
FILENAME_ANOVAS = FILENAME_OUTPUTS + "anovas/"
FILENAME_PREFIX = ""

VALUE_MIDDLE = 50
VALUE_MAX = 100
VALUE_MIN = 0
VALUE_THRES_ACCURATE = 75

FLAG_EXPORT = False
FLAG_LOCAL_VERSION = True

perspectives = ['0','1']
pathing_methods = ['Omn', 'M', 'SA', 'SB']
goals = [0, 1, 2, 3]
goal_names = ["BEFORE", "ME", "PAST", "ACROSS"]

COL_PATHING = 'Pathing Method'
COL_CHAIR = 'Perspective'
COL_GOAL = 'Goal Table'
COL_MATCHING = 'Match Condition'

# Types of analysis
A_PCT_UNSURE = 'pct_unsure'
A_PCT_CORRECT = 'pct_correct'
A_PCT_INCORRECT = 'pct_incorrect'

A_REVERSALS = 'reversals'

A_ENV_CUTOFF = 'envelope_cutoff'
A_ENV_ACC = 'envelope_accuracy'
A_ENV_CERT = 'envelope_certainty'


A_TT_CUTOFF = 'tt_cutoff'
A_TT_ACC = 'tt_accuracy'
A_TT_CERT = 'tt_certainty'

A_FLIPPED = 'is-flipped'

P_GLITCHES = 'glitches'
P_POST_EVENTS = 'post-events'
P_LOOKUP = 'lookup-packet'

OUTPUT_GRAPH_BOXPLOT = True
OUTPUT_GRAPH_STRIPPLOT = True
OUTPUT_GRAPH_BLENDED = True
OUTPUT_CALC_ANOVA = True

STATUS_GLITCH_UNSUPPORTED_BROWSER = "unsupported browser"
STATUS_GLITCH_NO_EVENTS = "no events found"
STATUS_GLITCH_EVENT_PAST_VIDEO_END = "past video end"
STATUS_NORMAL = "glitch-free"

LABELS_PATHING = {}
LABELS_PATHING['Omn'] = "Omniscient"
LABELS_PATHING['M'] = "Multi"
LABELS_PATHING['SA'] = "Single:A\n (for back-to-robot)"
LABELS_PATHING['SB'] = "Single:B\n (for facing-robot)"
# Static math
unsure_top = VALUE_MIDDLE + UNSURE_WINDOW
unsure_bottom = VALUE_MIDDLE - UNSURE_WINDOW

perspectives_file = ['PA','PB']
pathings_file = ['Omn', 'SA', 'SB', 'Multi']

# OUTPUT helper for finding video lengths
# video_lengths ={}
# for goal in goals:
#     for pathing in pathing_methods:
#         for perspective in perspectives:
#             # print(pathing + "_" + str(int(goal)) + "_" + perspective + ".mp4")
#             key = (pathing, goal, perspective)
#             print("video_lengths.append(" + str(key) + ", v)")



'''
 START: BOILER PLATE SET UP
'''
import dbkeys
db_url = dbkeys.db_url
table_name = dbkeys.table_name
data_column_name = dbkeys.data_column_name

if not FLAG_LOCAL_VERSION:
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
else:
    df = pd.read_json('pilot-all-frames.json')
    print("Pandas data imported from JSON")

video_lengths = {}
video_lengths[('Omn', 0, 0)] = 11.233333
video_lengths[('Omn', 0, 1)] = 8.63333
video_lengths[('SA', 0, 0)] = 10.8333
video_lengths[('SA', 0, 1)] = 10.400000

video_lengths[('SB', 0, 0)] = 11.666667
video_lengths[('SB', 0, 1)] = 9.7000
video_lengths[('M', 0, 0)] = 11.1333
video_lengths[('M', 0, 1)] = 9.600

video_lengths[('Omn', 1, 0)] = 11.76666
video_lengths[('Omn', 1, 1)] = 11.700000
video_lengths[('SA', 1, 0)] = 11.7333
video_lengths[('SA', 1, 1)] = 11.233333

video_lengths[('SB', 1, 0)] = 11.866667
video_lengths[('SB', 1, 1)] = 11.400000
video_lengths[('M', 1, 0)] = 11.66666
video_lengths[('M', 1, 1)] = 11.800000

video_lengths[('Omn', 2, 0)] = 12.93333
video_lengths[('Omn', 2, 1)] = 12.4333
video_lengths[('SA', 2, 0)] = 13.1000
video_lengths[('SA', 2, 1)] = 13.466667

video_lengths[('SB', 2, 0)] = 13.1666
video_lengths[('SB', 2, 1)] = 13.800
video_lengths[('M', 2, 0)] = 13.1000
video_lengths[('M', 2, 1)] = 12.600

video_lengths[('Omn', 3, 0)] = 10.96666
video_lengths[('Omn', 3, 1)] = 11.166667
video_lengths[('SA', 3, 0)] = 12.20000
video_lengths[('SA', 3, 1)] = 12.7000

video_lengths[('SB', 3, 0)] = 11.46666
video_lengths[('SB', 3, 1)] = 11.46666
video_lengths[('M', 3, 0)] = 11.33333
video_lengths[('M', 3, 1)] = 11.133333

'''
 END: BOILER PLATE SET UP
'''

'''
 START: TABLE DEFINITIONS
'''
print("All trials pre-work")
print(df.shape)

#Just stimulus trials
df_trials = df[['uniqueid', 'condition', 'videoduraction', 'phase', 'events', 'IV', 'goaltable', 'viewpoint']] 
df_trials = df_trials[df_trials['phase'] == 'TRIAL']
#print("============Stimulus trials==================")
print("Trials")
print(df_trials.shape)

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


FIRST_TIMESTAMP = 0
DEFAULT_START = 50

'''
Given a dataframe/trial_row, return the list (of lists) that represents the slider events from that trial
'''
def get_slider_events(trial_row, lp):
    ERROR_EVENTS = [[0,DEFAULT_START]]
    pathing = trial_row['IV']
    goal = trial_row['goaltable']
    perspective = trial_row['condition']

    key = (pathing, goal, perspective)
    final_timestamp = int(video_lengths[key] * 1000) + 1
    # print(final_timestamp)

    if trial_row.empty:
        print("Participant " + pid + " did not complete a trial")
        return None
    #get the slider event data, access the list (of lists) it is storing
    slider_events = trial_row['events']
    status = STATUS_NORMAL
    # print(len(slider_events))
    clean_events = [[0, DEFAULT_START]]

    #Cleans glitchy data. We should enforce the browsers we want, and see if these still occur
    if len(slider_events) != 0:
        #Take care of some glitched data, where an erroneous first event is recorded 
        firstEvent = slider_events[0]
        firstValue = firstEvent[1]

        if firstValue < 45 or firstValue > 55:
            slider_events = slider_events[1:]
#            print("fixed glitched data: First event glitch")
        
        #Take care of some glitched data, where events are recorded after the end of the video. Remove those events
        i = 0
        glitch = False
        
        vidlength = final_timestamp #round(trial_row['videoduraction'] * 1000)
        for event in slider_events:
            time = event[0]
            if time == None: #believe this is another odd case of someone using a non-supported browser, but not sure 
                UNSUPPORTED_BROWSER_ERROR = True
                status = STATUS_GLITCH_UNSUPPORTED_BROWSER
                return status, ERROR_EVENTS
                #print("None timestamp") 
            if time > vidlength: #found an event that took place after the video ended
#                print("fixed glitched data: Last event glitch")
                glitch = True
                # THIS IS NO LONGER A GLITCH, HANDLED
                # status = STATUS_GLITCH_EVENT_PAST_VIDEO_END
                # print("~~~")
                # print(str(time) +" is longer than "+ str(vidlength))
                # print(slider_events)
                # return clean_events, status
                clean_events.append([final_timestamp, clean_events[-1][1]])
                # print(clean_events)
                break
            i = i+1
            clean_events.append(event)

        
        # print("Final event is ")
        if (len(slider_events) > 0):
            final_val = slider_events[-1][1]
            # print(slider_events[-1])
        else:
            # print("No events " + status)
            final_val = -1
        # slider_events.append([final_timestamp, final_val])

        if glitch:
            # slider_events = slider_events[0:i] #slice off any of that data
            # status = STATUS_GLITCH
            # slider_events = ERROR_EVENTS
            return status, ERROR_EVENTS
    else:
        status = STATUS_GLITCH_NO_EVENTS


    # print(type(slider_events))
    # print(status)
    return status, clean_events

def slider_test():
    events = [[100, 50],[110, 44],[120, 50],[130, 56],[135, 75],[150, 100]]
    # print("Events")
    # print(events)
    df = pd.DataFrame(columns = ['events'])
    df.loc[0] = [events]

    post_events = get_slider_events(df)
    # print("Post events")
    # print(post_events)
    # print(post_events.shape)
    # print("Slider test OK")

def get_polarity(value):
    unsure_top = VALUE_MIDDLE + UNSURE_WINDOW
    unsure_bottom = VALUE_MIDDLE - UNSURE_WINDOW

    if unsure_bottom <= value <= unsure_top:
        return 0
    elif value > unsure_top:
        return 1
    elif value < unsure_bottom:
        return -1
    print("Error in polarity of " + str(value))
    return None


# print(slider_test())

def new_frame_view(events, video_length):
    #Note: this method does not provide any smoothing
    # Events guaranteed to be in order
    # format of [(time, value), (time2, value2)...]

    shifts = {}
    shifts[FIRST_TIMESTAMP] = DEFAULT_START
    for event in events:
        shifts[event[0]] = event[1]

    time = []
    values = []

    current_value = -1
    frame_view = []
    for i in range(video_length):
        if i in shifts:
            current_value = shifts[i]
        
        frame_view.append((i, current_value))
        
        time.append(i)
        values.append(current_value)

    frame_data = {'time': time, 'value': values}
  
    df_time = pd.DataFrame(frame_data, columns=['time','value'])
    
    # Verified that frame_view is correct from output graphs ;-)
    # return frame_view
    return df_time

def get_stat_percents(events, df, lp):

    df_unsure = (df[df['value'].between(unsure_bottom, unsure_top)])
    df_correct = (df[df['value'] > unsure_top])
    df_incorrect = (df[df['value'] < unsure_bottom])

    num_unsure = len(df_unsure)
    num_correct = len(df_correct)
    num_incorrect = len(df[df['value'].between(VALUE_MIN - 1, unsure_bottom)])
    total = len(df)

    if num_correct is np.nan:
        num_correct = 0
    if num_incorrect is np.nan:
        num_incorrect = 0
    if num_unsure is np.nan:
        num_unsure = 0
    if total is np.nan:
        total = 1

    # print("Percent stats")
    # print(num_correct, num_incorrect, num_unsure, total)

    # print(num_correct + num_unsure + num_incorrect)
    # print(total)

    pct_correct = num_correct / total
    pct_incorrect = num_incorrect / total
    pct_unsure = num_unsure / total
    pct_total = pct_correct + pct_incorrect + pct_unsure

    # print(pct_correct, pct_incorrect, pct_unsure, pct_total)

    return pct_correct, pct_incorrect, pct_unsure

def get_stat_envelope(events, frame_view, lookup_packet):
    envelope_accuracy, envelope_cutoff = 0, 0
    units = 1000.0
    df = frame_view

    # tag rows based on the threshold
    df['tag'] = df['value'] > VALUE_THRES_ACCURATE
    # first row is a True preceded by a False
    fst = df.index[df['tag'] & ~ df['tag'].shift(1).fillna(False)]
    # last row is a True followed by a False
    lst = df.index[df['tag'] & ~ df['tag'].shift(-1).fillna(False)]
    # filter those which are adequately apart
    pr = [(i, j) for i, j in zip(fst, lst) if j > i + 4]
    
    # This is now a series of contiguous regions
    if len(pr) > 0:
        # print(pr)
        region = pr[-1]
        envelope_cutoff = (region[1] - region[0]) / units
    else:
        envelope_cutoff = 0
        # print("Never right acc cutoff?")
        # print(lookup_packet)
        # print(events)
        # print(lp)

    # tag rows based on the threshold
    df['acc'] = df['value'] > VALUE_MIDDLE
    # first row is a True preceded by a False
    fst = df.index[df['acc'] & ~ df['acc'].shift(1).fillna(False)]
    # last row is a True followed by a False
    lst = df.index[df['acc'] & ~ df['acc'].shift(-1).fillna(False)]
    # filter those which are adequately apart
    pa = [(i, j) for i, j in zip(fst, lst) if j > i + 4]
    # This is now a series of contiguous regions
    if len(pa) > 0:
        region = pa[-1]
        envelope_accuracy = (region[1] - region[0]) / units

    else:
        envelope_accuracy = 0
        # print("Never right acc env?")
        # print(lookup_packet)
        # print(events)
        # print("~~~")


    # tag rows based on the threshold
    df['cert'] = df['value'] > unsure_top
    # first row is a True preceded by a False
    fst = df.index[df['cert'] & ~ df['cert'].shift(1).fillna(False)]
    # last row is a True followed by a False
    lst = df.index[df['cert'] & ~ df['cert'].shift(-1).fillna(False)]
    # filter those which are adequately apart
    pc = [(i, j) for i, j in zip(fst, lst) if j > i + 4]
    # This is now a series of contiguous regions
    if len(pc) > 0:
        region = pc[-1]
        envelope_certainty = (region[1] - region[0]) / units
    else:
        envelope_certainty = 0

    # print(envelope_accuracy, envelope_certainty, envelope_cutoff)

    if envelope_accuracy == 0:
        # print("Never accurate")
        # print(lookup_packet)
        pass
    return envelope_accuracy, envelope_certainty, envelope_cutoff

def get_stat_tt(events, frame_view, lookup_packet):
    last_frame = frame_view["time"].max()

    tt_accuracy, tt_cutoff, tt_certainty = last_frame, last_frame, last_frame 
    units = 1000.0
    df = frame_view

    # tag rows based on the threshold
    df['tag'] = df['value'] > VALUE_THRES_ACCURATE
    # first row is a True preceded by a False
    fst = df.index[df['tag'] & ~ df['tag'].shift(1).fillna(False)]
    # last row is a True followed by a False
    lst = df.index[df['tag'] & ~ df['tag'].shift(-1).fillna(False)]
    # filter those which are adequately apart
    pr = [(i, j) for i, j in zip(fst, lst) if j > i + 4]
    
    # This is now a series of contiguous regions
    if len(pr) > 0:
        region = pr[-1]
        tt_cutoff = (region[0]) / units
    # else:
        # tt_cutoff = frame_view[-1][0]
        # print(lp)

    # tag rows based on the threshold
    df['acc'] = df['value'] >= VALUE_MIDDLE
    # first row is a True preceded by a False
    fst = df.index[df['acc'] & ~ df['acc'].shift(1).fillna(False)]
    # last row is a True followed by a False
    lst = df.index[df['acc'] & ~ df['acc'].shift(-1).fillna(False)]
    # filter those which are adequately apart
    pa = [(i, j) for i, j in zip(fst, lst) if j > i + 4]
    # This is now a series of contiguous regions
    if len(pa) > 0:
        region = pa[-1]
        tt_accuracy = (region[0]) / units
    # else:
    #     tt_accuracy = 0
        # print("Never right acc env?")
        # print(lookup_packet)


    # tag rows based on the threshold
    df['cert'] = df['value'] > unsure_top
    # first row is a True preceded by a False
    fst = df.index[df['cert'] & ~ df['cert'].shift(1).fillna(False)]
    # last row is a True followed by a False
    lst = df.index[df['cert'] & ~ df['cert'].shift(-1).fillna(False)]
    # filter those which are adequately apart
    pc = [(i, j) for i, j in zip(fst, lst) if j > i + 4]
    # This is now a series of contiguous regions
    if len(pc) > 0:
        region = pc[-1]
        tt_certainty = (region[0]) / units
    # else:
    #     tt_certainty = 0


    return tt_accuracy, tt_certainty, tt_cutoff

def get_stat_reversals(events, frame_view, lp):
    reversals = 0
    status = 0

    for time, value in events:
        polarity = get_polarity(value)
        if polarity is not 0:
            if polarity is not status:
                reversals += 1
                status = polarity

    # if reversals > 0:
    #     print("success " + str(reversals))
    return reversals

NOT_FLIPPED = 1
INDECISIVE = 0
FLIPPED = -1

def get_stat_is_flipped(events, frame_view, lp):
    status = 0

    for time, value in events:
        polarity = get_polarity(value)
        if polarity is not 0:
            if polarity is not status:
                status = polarity
    
    if status > 0:
        return NOT_FLIPPED
    elif status == 0:
        return INDECISIVE
    else:
        return FLIPPED



def get_stat_total_confidence(events, frame_view, lp):
    acc = 0

    return acc

def get_stat_total_accuracy(events, frame_view, lp):
    # df['acc'] = df['value'] >= VALUE_MIDDLE
    acc = 0
    return acc

def get_perspective_label(row):
    perspective = row['condition']
    labels = ["A: back-to-robot", "B: facing-robot"]
    return labels[int(perspective)]

def get_pm_label(row):
    perspective = row['IV']
    labels = LABELS_PATHING
    return labels[perspective]

def get_mismatch_label(row):
    label = "NA"
    perspective = row['condition']
    p_labels = ["A", "B"]
    perspective = p_labels[int(perspective)]

    iv = row['IV']

    if perspective is "A" and iv is "SA":
        label = "AA"
    elif perspective is "A" and iv is "SB":
        label = "AB"
    elif perspective is "B" and iv is "SA":
        label = "BA"
    elif perspective is "B" and iv is "SB":
        label = "BB"
    else:
        label = iv

    return label

# Create a unique human-readable string to identify this specific entry
def get_lookup_packet(trial_row):
    goaltable = trial_row['goaltable']
    iv = trial_row['IV']
    viewpoint = trial_row['viewpoint']
    person_id = trial_row['uniqueid']
    lookup_packet = (person_id, iv, viewpoint, goaltable)
    return str(lookup_packet)

# Given a row, return a dictionary of new analysis columns for understanding
def analyze_participant(trial_row):

    lookup_packet = get_lookup_packet(trial_row)
    lp = lookup_packet

    status, events = get_slider_events(trial_row, lookup_packet)
    times = []
    values = []

    # lookup_packet = (person_id, iv, viewpoint, goaltable, status)
    # lp = str(lookup_packet)

    # print("Analysis for person id: " + str(person_id))

    video_length = int(round(trial_row['videoduraction'] * 1000)) #round to the nearest millisecond
    frame_view = new_frame_view(events, video_length)

    pct_correct, pct_incorrect, pct_unsure = get_stat_percents(events, frame_view, lp)
    envelope_accuracy, envelope_certainty, envelope_cutoff = get_stat_envelope(events, frame_view, lp)
    tt_accuracy, tt_certainty, tt_cutoff = get_stat_tt(events, frame_view, lp)
    reversals = get_stat_reversals(events, frame_view, lp)
    total_confidence = get_stat_total_confidence(events, frame_view, lp)
    total_accuracy = get_stat_total_accuracy(events, frame_view, lp)

    is_flipped = get_stat_is_flipped(events, frame_view, lp)


    analyses = {}
    # Notes if there's a glitch in any of the processing
    analyses[P_GLITCHES] = status
    analyses[P_LOOKUP] = lp
    analyses[P_POST_EVENTS] = json.dumps(events)

    analyses['total_confidence'] = total_confidence
    analyses['total_accuracy'] = total_accuracy

    analyses[A_REVERSALS] = reversals

    analyses[A_ENV_CUTOFF] = envelope_cutoff
    analyses[A_ENV_ACC] = envelope_accuracy
    analyses[A_ENV_CERT] = envelope_certainty

    analyses[A_TT_CUTOFF] = tt_cutoff
    analyses[A_TT_ACC] = tt_accuracy
    analyses[A_TT_CERT] = tt_certainty

    analyses[A_PCT_UNSURE] = pct_unsure
    analyses[A_PCT_CORRECT] = pct_correct
    analyses[A_PCT_INCORRECT] = pct_incorrect

    analyses[A_FLIPPED] = is_flipped

    # analyses['avg_accuracy'] = get_overall_confidence(events, video_length)
    # analyses['avg_accuracy'] = get_overall_confidence(events, video_length)
    # analyses['avg_accuracy'] = get_overall_confidence(events, video_length)
    

    return analyses, frame_view

def clean_flipped_data(df):
    df_clean = df[df[A_FLIPPED] != FLIPPED]
    df_flipped = df[df[A_FLIPPED] == FLIPPED]
    df_indecisive = df[df[A_FLIPPED] == INDECISIVE]


    pct = (1.0 * len(df_flipped) / len(df))

    print("Removed " + str(len(df_flipped)) + "flipped entries out of " + str(len(df)) + " -> " + str(pct) + "%")
    pct = (1.0 * len(df_indecisive) / len(df))
    print("Retained " + str(len(df_indecisive)) + " indecisive entries out of " + str(len(df)) + " -> " + str(pct) + "%")

    # TODO add filtering summary
    print("Clean entries: " + str(len(df_clean)) + "")

    return df_clean


def clean_glitchy_data_and_report(df):
    df_glitches = df[df[P_GLITCHES] != STATUS_NORMAL]
    df_no_glitches = df[df[P_GLITCHES] == STATUS_NORMAL]
    pct = (1.0 * len(df_glitches) / len(df))

    print("Removed " + str(len(df_glitches)) + " glitchy entries out of " + str(len(df)) + " -> " + str(pct) + "%")
    error_types = [STATUS_GLITCH_NO_EVENTS, STATUS_GLITCH_UNSUPPORTED_BROWSER, STATUS_GLITCH_EVENT_PAST_VIDEO_END]
    for et in error_types:
        df_et = df[df[P_GLITCHES] == et]
        pct_et = (len(df_et) / len(df_glitches))
        print("Found " + str(len(df_et)) + " entries with error type " + et + ", " + str(pct_et) + "% of all glitches")


    # TODO add filtering summary
    print("Clean entries: " + str(len(df_no_glitches)) + "")

    return df_no_glitches


def analyze_all_participants(df):
    print(df.shape)
    for i, row in df.iterrows():
        analyses, frame_view = analyze_participant(row)

        # Add pretty labels for making graphs later
        df.at[i,COL_PATHING] = get_pm_label(row)
        df.at[i,COL_CHAIR] = get_perspective_label(row)

        # Add pretty and easy sorting mechanism for mismatches
        df.at[i,COL_MATCHING] = get_perspective_label(row)

        # print(df.columns)
        for key in analyses.keys():
            # print(key)
            # print(analyses[key])
            df.at[i,key] = analyses[key]

    analysis_categories = analyses.keys()
    # remove glitched entries and report
    
    df = clean_glitchy_data_and_report(df)

    df = clean_flipped_data(df)    

    print("Time to make some graphs")
    print(df.columns)
    print(df.shape)
    return df

#   
#Given a trial and uniqueid, plot the participants's confidence values over time
def plot_confidence_one_participant(trial_row):
    status, events = get_slider_events(trial_row)
    times = []
    values = []

    for event in events:
        times.append(event[0])
        values.append(event[1])   
 
    plt.plot(times, values)
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Average Raw Slider Value')
    plt.title('Confidence Values for Participant ' + trial_row['uniqueid'] + ' During Trial ' + str(trial_row['goaltable']) + ', ' + str(trial_row['IV']))
    plt.savefig(FILENAME_PLOTS + "conf_one.png")


def plot_analysis_one_participant(trial_row, lp, fn):
    # print(trial_row.columns)
    glitch = trial_row.get(P_GLITCHES)

    # print(trial_row[P_POST_EVENTS])
    events = trial_row.get(P_POST_EVENTS)
    events = json.loads(events)
    times = []
    values = []

    for event in events:
        times.append(event[0])
        values.append(event[1])   
 
    uniqueid = trial_row['uniqueid']
    goaltable = trial_row['goaltable']
    iv = trial_row['IV']

    plt.figure()
    plt.plot(times, values)
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Average Raw Slider Value')
    plt.title('Confidence Values for Participant ' + str(uniqueid) + ' \nDuring Trial ' + str(goaltable) + ', ' + str(iv) +  " \nstatus=" + glitch)
    plt.savefig(fn)
    plt.close()
    

def plot_confidence_one_participant_full(trial_row):
    status, events = get_slider_events(trial_row)
    video_length = int(round(trial_row['videoduraction'] * 1000)) #round to the nearest millisecond
    frame_view = new_frame_view(events, video_length)
 

    # plt.plot(times, values)
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Average Raw Slider Value')
    plt.title('Raw Slider Values for Participant ' + trial_row['uniqueid'] + ' During Trial ' + str(trial_row['goaltable']) + ', ' + str(trial_row['IV']))
    plt.savefig("testPlots2.png", bbox_inches='tight')


def is_unique(s):
    a = s.to_numpy() # s.values (pandas<0.24)
    return (a[0] == a).all()

def make_anova(df, analysis_label, fn, title):
    SIGNIFICANCE_CUTOFF = .4
    if OUTPUT_CALC_ANOVA:
        anova_text = title + "\n"
        # print("ANOVA FOR ")
        # print(analysis_label)
        # print(df[analysis_label])

        subject_id = 'uniqueid'

        df_col = df[analysis_label]
        val_min = df_col.get(df_col.idxmin())
        val_max = df_col.get(df_col.idxmax())
        homogenous_data = (val_min == val_max)

        if not homogenous_data:
            aov = pg.mixed_anova(dv=analysis_label, between=COL_CHAIR, within=COL_PATHING, subject=subject_id, data=df)
            aov.round(3)

            anova_text = anova_text + str(aov)

            p_vals = aov['p-unc']
            p_chair = p_vals[0]
            p_path_method = p_vals[1]

            if p_chair < SIGNIFICANCE_CUTOFF:
                print("Chair position is significant for " + analysis_label + ": " + str(p_chair))
                print(title)
            if p_path_method < SIGNIFICANCE_CUTOFF:
                print("Pathing method is significant for " + analysis_label + ": " + str(p_path_method))
                print(title)

            anova_text = anova_text + "\n"
            # Verify that subjects is legit
            # print(df[subject_id])

            # posthocs = pg.pairwise_ttests(dv=analysis_label, within=COL_PATHING, between=COL_CHAIR,
            #                           subject=subject_id, data=df)
            # anova_text = anova_text + pg.print_table(posthocs)

        else:
            print("! Issue creating ANOVA for " + analysis_label)
            print("Verify that there are at least a few non-identical values recorded")
            anova_text = anova_text + "Column homogenous with value " + str(val_min)


        f = open(FILENAME_ANOVAS + fn + "anova.txt", "w")
        f.write(anova_text)
        f.close()

def make_boxplot(df, analysis, fn, title):
    if OUTPUT_GRAPH_BOXPLOT:
        graph_type = "boxplot"
        plt.figure()
        # plt.tight_layout()
        # title = al_title[analysis] + "\n" + al_y_range
        bx = sns.boxplot(data=df, x=COL_PATHING, y=analysis, hue=COL_CHAIR, order=cat_order)
        # print("San check on data")
        # print(df[analysis])
        # print(df[analysis].columns)

        bx.set(xlabel='Pathing Method')
        ylims = al_y_range[analysis]
        bx.set(ylim=ylims)
        bx.set(title=title, ylabel=al_y_units[analysis])
        figure = bx.get_figure()    
        figure.savefig(FILENAME_PLOTS + fn + graph_type + '.png', bbox_inches='tight')
        plt.close()

def make_stripplot(df, analysis, fn, title):
    if OUTPUT_GRAPH_STRIPPLOT:
            graph_type = "stripplot"
            plt.figure()
            # plt.tight_layout()
            bplot=sns.stripplot(y=analysis, x=COL_PATHING, 
                           data=df_goal, 
                           jitter=True, 
                           marker='o', 
                           alpha=0.8,
                           hue=COL_CHAIR, order=cat_order)
            bplot.set(xlabel='Pathing Method')
            bplot.set(ylim=al_y_range[analysis])
            bplot.set(title=al_title[analysis], ylabel=al_y_units[analysis])
            figure = bplot.get_figure()    
            figure.savefig(FILENAME_PLOTS + fn + graph_type + '.png', bbox_inches='tight')
            plt.close()

'''
 END: METHOD DECLARATIONS
'''

# row = df_analyzed.loc[0]
# plot_confidence_one_participant(row)
# plot_confidence_one_participant_full(row)

al_title = {}
al_y_units = {}
al_y_range = {}

al_title[A_PCT_UNSURE] = "Proportion of Time Spent Unsure (+/- " + str(UNSURE_WINDOW) + ")"
al_title[A_PCT_CORRECT] = "Proportion of Time Spent Correct"
al_title[A_PCT_INCORRECT] = "Proportion of Time Spent Incorrect"
al_title[A_REVERSALS] = "Reversals (Flipped Certainty beyond +/- " + str(UNSURE_WINDOW) + "% from neutral)"
al_title[A_ENV_CUTOFF] = "Envelope (in seconds) of Certainty Beyond Cutoff"
al_title[A_ENV_ACC] = "Envelope (in seconds) of Staying Accurate"
al_title[A_ENV_CERT] = "Envelope (in seconds) of Staying Certain Beyond +/- " + str(UNSURE_WINDOW) + "%)"

al_title[A_TT_CUTOFF] = "Time to Correct Certainty Beyond Cutoff"
al_title[A_TT_ACC] = "Time to final correct Accuracy"
al_title[A_TT_CERT] = "Time to Staying More Certain Than +/- " + str(UNSURE_WINDOW) + "% from neutral)"


al_y_units[A_PCT_UNSURE] = "Proportion of Time Spent Unsure"
al_y_units[A_PCT_CORRECT] = "Proportion of Time Spent Correct"
al_y_units[A_PCT_INCORRECT] = "Proportion of Time Spent Incorrect"
al_y_units[A_REVERSALS] = "# of Reversals"
al_y_units[A_ENV_CUTOFF] = "Period of Time Correct Beyond Cutoff"
al_y_units[A_ENV_ACC] = "Period of Time with Accurate Guess"
al_y_units[A_ENV_CERT] = "Envelope (in seconds) of Staying Certain Beyond +/- " + str(UNSURE_WINDOW) + "%)"

al_y_units[A_TT_CUTOFF] = "Time (in seconds)"
al_y_units[A_TT_ACC] = "Time (in seconds)"
al_y_units[A_TT_CERT] = "Time (in seconds)"


max_video = round(df_trials["videoduraction"].max())
print("Max Video Length")
print(max_video)

UNSURE_WINDOW = 5
FILENAME_PREFIX += str(UNSURE_WINDOW) + "window-"


# CONDUCT ANALYSIS ON DATA
# analysis_categories = al_title.keys()
analysis_categories = [A_ENV_ACC, A_ENV_CERT, A_ENV_CUTOFF]

df_analyzed = copy.copy(df_trials)
df_analyzed = analyze_all_participants(df_analyzed)

# Calculate graph bounds AFTER analysis
al_y_range[A_PCT_UNSURE] =      (0, 1.0)
al_y_range[A_PCT_CORRECT] =     (0, 1.0)
al_y_range[A_PCT_INCORRECT] =   (0, 1.0)
al_y_range[A_REVERSALS] =  (0, df_analyzed[A_REVERSALS].max())
al_y_range[A_ENV_CUTOFF] = (0, max_video)
al_y_range[A_ENV_ACC] = (0, max_video)
al_y_range[A_ENV_CERT] = (0, max_video)

al_y_range[A_TT_CUTOFF] =   (0, max_video)
al_y_range[A_TT_ACC] =      (0, max_video)
al_y_range[A_TT_CERT] =     (0, max_video)


# GENERATE GRAPHS FOR DATA
goal = 3
goals = [3]
goal_title = goal_names[goal]
categories = pathing_methods
# perspective = don't care

# Colors aligned with blue and yellow of the table images
PATH_COLORS = [(0,255,255), (255,64,64), (0,201,87)]
PATH_COLORS = ["amber", "windows blue"]

custom_palette = sns.xkcd_palette(PATH_COLORS) #sns.color_palette("Paired", 2)
sns.set_palette(custom_palette)

# Set a consistent ordering for the groupings of analysis
cat_order = [LABELS_PATHING['Omn'], LABELS_PATHING['SB'], LABELS_PATHING['SA'], LABELS_PATHING['M']]

# For each stimuli, group the data and inspect individually
# (this should help distill what's going on)
for goal in goals:
    goal_title = goal_names[goal]
    df_goal = df_analyzed[df_analyzed['goaltable'] == goal]
    # print(df_goal.shape)

    for analysis in analysis_categories:
        # print(df_goal[analysis])

        # print(df_goal)

        title = al_title[analysis]
        title += "\nfor the goal " + goal_title
        fn = FILENAME_PREFIX + goal_title + "-" + analysis + "-"
        make_boxplot(df_goal, analysis, fn, title)
        make_stripplot(df_goal, analysis, fn, title)
        make_anova(df_goal, analysis, fn, title)
        

        # TODO: ANOVAs, highlight if something interesting

    print("DONE with " + goal_title)


print("Inspecting troublemakers")
# Inspect troublemakers
# Ex ('debugRg8DP:debugDKHYC', 'M', 'B', 2.0)
t1 = "('debugRg8DP:debugDKHYC', 'M', 'B', 2.0)"
t2 = "('debugRg8DP:debugDKHYC', 'M', 'B', 3.0)"
t3 = "('debugYuhM3:debugdoGQl', 'M', 'B', 1.0)"
t4 = "('debugYuhM3:debugdoGQl', 'SA', 'B', 0.0)"
t5 = "('debugYuhM3:debugdoGQl', 'SA', 'B', 0.0)"
# This one is never accurate
troublemakers = [t5]

for t in troublemakers:
    df_trouble = df_analyzed[df_analyzed[P_LOOKUP] == t]
    # print(type(df_trouble))
    df_trouble = df_trouble.iloc[0]

    print(df_trouble.shape)
    # Should only be one
    t_id = t
    t_id = t_id.replace("(", "")
    t_id = t_id.replace(")", "")
    t_id = t_id.replace("\'", "")
    t_id = t_id.replace(", ", "-")
    print(t_id)

    fn = FILENAME_PLOTS + "trouble-" + t_id + ".png"
    plot_analysis_one_participant(df_trouble, t, fn)
    # Add dirty data marker, too

print("FINISHED")





