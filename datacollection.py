#Check comments with TODO for things that still need to to be implemented

import sqlite3
import json

db_url = "participants.db"
table_name = 'newdev'
data_column_name = 'datastring'
 
con = sqlite3.connect(db_url)
cur = con.cursor()

cur.execute('SELECT datastring FROM newdev')
rows = cur.fetchall()

#currently just choosing the most recent participant's data
mostRecent = len(rows) -1

#participant is a tuple. Its length is 1, and the value is a string
participant = rows[mostRecent]

#turn the string into a python dictionary
participantDict = json.loads(participant[0])
#there are 13 entries in the dictionary: condition, counterbalance, assignmentId, workerId, hitId, currenttrial, bonus, data, questiondata, eventdata, useragent, mode, status

data = participantDict.get("data") 
#the data key has all the trial data
#data is a list, where each entry is its own dictionary

#three lists to collect a single participant's confidence scores, trial accuracy, and reaction times
partConfScores =[]
trialAccuracy = []
reactionTimes = []
botCheckResponse = ""

#each entry is a dictionary. with four keys: uniqueid, current_trial, dateTime, trialdata
for entry in data:
    #trialdata contains the data stored at each step of the study
    trialData = entry.get("trialdata")
    
    phase = trialData.get("phase")
    if phase == "ConfQuestionsResponse": #if its a trial with a confidence score value
        confScore = trialData.get("ConfidenceScore")
        
        #TODO: if confScore is 11 or whatever 11 looks like in data, do something here
        
        if len(confScore) > 1:
            #Trim the confScore if it is 1,5,or 10
            confScore = confScore[0:2] 
            
        confScore = int(confScore) #make it an integer
        partConfScores.append(confScore)
        
    if phase == "TEST": #if its a trial with a stimulus
        #not needed at this time
        #condition = trialData.get("stimulus") 
        #tableDest = trialData.get("destination") 
        
        correct = trialData.get("hit")
        reactionTime = trialData.get("rt")
        
        trialAccuracy.append(correct)
        reactionTimes.append(int(reactionTime))
        
        
    if phase == "BotCheck":
        botCheckResponse = trialData.get("BotCheckResponse")
        
        
        
        
print(partConfScores)
print(trialAccuracy)
print(reactionTimes)
print(botCheckResponse)

        
    

con.close()


# Example using sqlalchemy
# TODO: move to useing sqlalchemy rather than sqlite3

# boilerplace sqlalchemy setup
#engine = create_engine(db_url)
#metadata = MetaData()
#metadata.bind = engine
#table = Table(table_name, metadata, autoload=True)
# make a query and loop through
#s = table.select()
#rows = s.execute()
#
#data = []
##status codes of subjects who completed experiment
#statuses = [3,4,5,7]
## if you have workers you wish to exclude, add them here
#exclude = []
#for row in rows:
#    # only use subjects who completed experiment and aren't excluded
#    if row['status'] in statuses and row['uniqueid'] not in exclude:
#        data.append(row[data_column_name])
#
## Now we have all participant datastrings in a list.
## Let's make it a bit easier to work with:
#
## parse each participant's datastring as json object
## and take the 'data' sub-object
#data = [json.loads(part)['data'] for part in data]
#
## insert uniqueid field into trialdata in case it wasn't added
## in experiment:
#for part in data:
#    for record in part:
#        record['trialdata']['uniqueid'] = record['uniqueid']
#
## flatten nested list so we just have a list of the trialdata recorded
## each time psiturk.recordTrialData(trialdata) was called.
#data = [record['trialdata'] for part in data for record in part]
#
## Put all subjects' trial data into a dataframe object from the
## 'pandas' python library: one option among many for analysis
#data_frame = pd.DataFrame(data)