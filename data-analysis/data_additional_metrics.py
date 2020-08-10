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

FILENAME_PLOTS = "plots/"

VALUE_MIDDLE = 50
VALUE_MAX = 100
VALUE_MIN = 0
VALUE_THRES_ACCURATE = 75

FLAG_EXPORT = False
FLAG_LOCAL_VERSION = True

perspectives = ['0','1']
pathing_methods = ['Omn', 'M', 'SA', 'SB']
goals = [0, 1, 2, 3]
goal_names = ["BEFORE", "ME", "ACROSS", "PAST"]

COL_PATHING = 'Pathing Method'
COL_CHAIR = 'Perspective'
COL_GOAL = 'Goal Table'
COL_MATCHING = 'Match Condition'

# Static math
unsure_top = VALUE_MIDDLE + UNSURE_WINDOW
unsure_bottom = VALUE_MIDDLE - UNSURE_WINDOW

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

df_analyzed = copy.copy(df_trials)


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
def get_slider_events(trial_row):
    if trial_row.empty:
        print("Participant " + pid + " did not complete a trial")
        return None
    #get the slider event data, access the list (of lists) it is storing
    slider_events = trial_row['events']
    
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
        vidlength = round(trial_row['videoduraction'] * 1000)
        for event in slider_events:
            time = event[0]
            if time == None: #believe this is another odd case of someone using a non-supported browser, but not sure 
                UNSUPPORTED_BROWSER_ERROR = True
                return []
                #print("None timestamp") 
            if time > vidlength: #found an event that took place after the video ended
#                print("fixed glitched data: Last event glitch")
                # glitch = True
                break
            i = i+1
        if glitch:
            # slider_events = slider_events[0:i] #slice off any of that data
            slider_events = [(0,DEFAULT_START)]
    return slider_events

def slider_test():
    events = [[100, 50],[110, 44],[120, 50],[130, 56],[135, 75],[150, 100]]
    # print("Events")
    # print(events)
    df = pd.DataFrame(columns = ['events'])
    df.loc[0] = [events]

    post_events = get_slider_events(df)
    # print("Post events")
    # print(post_events)
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

def get_stat_percents(events, df):

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

def get_stat_envelope(events, df):
    envelope_accuracy, envelope_cutoff = 0, 0
    units = 1000.0

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
        envelope_cutoff = (region[1] - region[0]) / units
    else:
        envelope_cutoff = 0

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


    return envelope_accuracy, envelope_certainty, envelope_cutoff

def get_stat_reversals(events, frame_view):
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

def get_stat_total_confidence(events, frame_view):
    acc = 0

    return acc

def get_stat_total_accuracy(events, frame_view):
    acc = 0

    return acc

def get_perspective_label(row):
    perspective = row['condition']
    labels = ["A", "B"]
    return labels[int(perspective)]

def get_pm_label(row):
    perspective = row['IV']
    labels = {}
    labels['Omn'] = "Omniscient"
    labels['M'] = "Multi"
    labels['SA'] = "Single:A"
    labels['SB'] = "Single:B"
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

# Given a row, return a dictionary of new analysis columns for understanding
def analyze_participant(trial_row):
    events = get_slider_events(trial_row)
    times = []
    values = []

    goaltable = trial_row['goaltable']
    iv = trial_row['IV']
    viewpoint = trial_row['viewpoint']

    video_length = int(round(trial_row['videoduraction'] * 1000)) #round to the nearest millisecond
    frame_view = new_frame_view(events, video_length)

    pct_correct, pct_incorrect, pct_unsure = get_stat_percents(events, frame_view)
    envelope_accuracy, envelope_certainty, envelope_cutoff = get_stat_envelope(events, frame_view)
    reversals = get_stat_reversals(events, frame_view)
    total_confidence = get_stat_total_confidence(events, frame_view)
    total_accuracy = get_stat_total_accuracy(events, frame_view)

    analyses = {}
    analyses['total_confidence'] = total_confidence
    analyses['total_accuracy'] = total_accuracy
    analyses['reversals'] = reversals

    analyses['envelope_cutoff'] = envelope_cutoff
    analyses['envelope_accuracy'] = envelope_accuracy
    analyses['envelope_certainty'] = envelope_certainty

    analyses['pct_unsure'] = pct_unsure
    analyses['pct_correct'] = pct_correct
    analyses['pct_incorrect'] = pct_incorrect

    # analyses['avg_accuracy'] = get_overall_confidence(events, video_length)
    # analyses['avg_accuracy'] = get_overall_confidence(events, video_length)
    # analyses['avg_accuracy'] = get_overall_confidence(events, video_length)
    

    return analyses, frame_view

def analyze_all_participants(df):
    for i, row in df.iterrows():
        analyses, frame_view = analyze_participant(row)

        # Add pretty labels for making graphs later
        df.at[i,COL_PATHING] = get_pm_label(row)
        df.at[i,COL_CHAIR] = get_perspective_label(row)

        # Add pretty and easy sorting mechanism for mismatches
        df.at[i,COL_MATCHING] = get_perspective_label(row)

        for key in analyses.keys():
            df.at[i,key] = analyses[key]

    analysis_categories = analyses.keys()
    print("Time to make some graphs")
    return df

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
    plt.ylabel('Average Raw Slider Value')
    plt.title('Confidence Values for Participant ' + trial_row['uniqueid'] + ' During Trial ' + str(trial_row['goaltable']) + ', ' + str(trial_row['IV']))
    plt.savefig("testPlots.png")
    

def plot_confidence_one_participant_full(trial_row):
    events = get_slider_events(trial_row)
    video_length = int(round(trial_row['videoduraction'] * 1000)) #round to the nearest millisecond
    frame_view = new_frame_view(events, video_length)
 

    # plt.plot(times, values)
    plt.xlabel('Timestamp (milliseconds)')
    plt.ylabel('Average Raw Slider Value')
    plt.title('Confidence Values for Participant ' + trial_row['uniqueid'] + ' During Trial ' + str(trial_row['goaltable']) + ', ' + str(trial_row['IV']))
    plt.savefig("testPlots2.png")
'''
 END: METHOD DECLARATIONS
'''

# row = df_analyzed.loc[0]
# plot_confidence_one_participant(row)
# plot_confidence_one_participant_full(row)

# A_PCT_UNSURE = 'pct_unsure'
# A_PCT_CORRECT = 'pct_correct'
# A_PCT_INCORRECT = 'pct_incorrect'
# A_REVERSALS = 'reversals'

# analysis_categories = ['total_confidence', 'total_accuracy', 'reversals', 'envelope_cutoff', 'envelope_accuracy', 'pct_unsure', 'pct_correct', 'pct_incorrect']
analysis_categories = ['pct_unsure', 'pct_correct', 'pct_incorrect', 'reversals', 'envelope_cutoff', 'envelope_accuracy','envelope_certainty']

pretty_al = {}
pretty_al['pct_unsure'] = "Percent of Time Spent Unsure (+/- " + str(UNSURE_WINDOW) + ")"
pretty_al['pct_correct'] = "Percent of Time Spent Correct"
pretty_al['pct_incorrect'] = "Percent of Time Spent Incorrect"
pretty_al['reversals'] = "Reversals (Flipped Certainty beyond +/- " + str(UNSURE_WINDOW) + "%)"
pretty_al['envelope_cutoff'] = "Envelope (in seconds) of Certainty Beyond Cutoff"
pretty_al['envelope_accuracy'] = "Envelope (in seconds) of Staying Accurate"
pretty_al['envelope_certainty'] = "Envelope (in seconds) of Staying Certain Beyond +/- " + str(UNSURE_WINDOW) + "%)"

# analysis_categories = ['reversals']

UNSURE_WINDOW = 5
FILENAME_PLOTS += str(UNSURE_WINDOW) + "window-"
df_analyzed = analyze_all_participants(df_analyzed)
goal = 2
goal_title = goal_names[goal]
categories = pathing_methods
# perspective = don't care

custom_palette = sns.color_palette("Paired", 2)
sns.set_palette(custom_palette)
# sns.set_palette("colorblind")

cat_order = ["Omniscient", "Single:A", "Single:B", "Multi"]

# print(analysis_categories)
for goal in goals:
    goal_title = goal_names[goal]
    df_goal = df_analyzed[df_analyzed['goaltable'] == goal]

    for analysis in analysis_categories:
        # print(df_across)

        graph_type = "boxplot"
        plt.figure()
        bx = sns.boxplot(data=df_goal, x=COL_PATHING, y=analysis, hue=COL_CHAIR, order=cat_order)
        bx.set(xlabel='Pathing Method', ylabel=pretty_al[analysis])
        figure = bx.get_figure()    
        figure.savefig(FILENAME_PLOTS + graph_type + "-" + goal_title + "-"+ analysis + '.png')
        plt.close()

        # graph_type = "stripplot"
        # plt.figure()
        # bplot=sns.stripplot(y=analysis, x=COL_PATHING, 
        #                data=df_goal, 
        #                jitter=True, 
        #                marker='o', 
        #                alpha=0.5,
        #                hue=COL_CHAIR, order=cat_order)
        # bplot.set(xlabel='Pathing Method', ylabel=pretty_al[analysis])
        # figure = bplot.get_figure()    
        # figure.savefig(FILENAME_PLOTS + graph_type + "-" + goal_title + "-"+ analysis + '.png')
        # plt.close()

        # # Do some ANOVA checks
        # formula = ""
        # model = ols(formula, data=df_goal).fit()
        # sm.stats.anova_lm(model, typ=2)


        # print(accuracy_df)
        # fvalue_acc, pvalue_acc = stats.f_oneway(accuracy_df['Omn'], accuracy_df['M'], accuracy_df['SA'], accuracy_df['SB'])
        # print("fvalue,pvalue: " + str(fvalue_acc) + ',' +str(pvalue_acc))

        # #get ANOVA table 
        # accuracy_df_melt = pd.melt(accuracy_df.reset_index(), id_vars = ['index'], value_vars=['Omn', 'M', 'SA', 'SB'])
        # accuracy_df_melt.columns = ['index', 'treatments', 'value']
        # # Ordinary Least Squares (OLS) model
        # model_acc = ols.ols('value ~ C(treatments)', data=accuracy_df_melt).fit()
        # anova_table_acc = sm.stats.anova_lm(model_acc,typ=2)
        # print(anova_table_acc)




    print("DONE with " + goal_title)
print("FINISHED")





