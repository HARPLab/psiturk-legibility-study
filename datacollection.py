#Version Using sqlite3

import sqlite3
import json
import sqlalchemy
import pandas as pd
import scipy.stats as stats

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
allConfResponses = True
trialAccuracy = []
reactionTimes = []
botCheckResponse = ""
botCheckPass = True

#each entry is a dictionary. with four keys: uniqueid, current_trial, dateTime, trialdata
for entry in data:
    #trialdata contains the data stored at each step of the study
    trialData = entry.get("trialdata")
    
    phase = trialData.get("phase")
    if phase == "ConfQuestionsResponse": #if its a trial with a confidence score value
        confScore = trialData.get("ConfidenceScore")
                
        if len(confScore) > 1:
            #Trim the confScore if it is 1,5,or 10
            confScore = confScore[0:2] 
                    
        if confScore == "": #if the participant did not make a selection, there will be a blank 
            partConfScores.append("")
            allConfResponses = False
        else:
            confScore = int(confScore) #make it an integer
            partConfScores.append(confScore)
        
    if phase == "TEST": #if its a trial with a stimulus
        #not needed at this time
        #stimulusname = trialData.get("stimulus") 
        #tableDest = trialData.get("destination") 
        #condition = trialData.get("condition)
        
        correct = trialData.get("hit")
        reactionTime = trialData.get("rt")
        
        trialAccuracy.append(correct)
        reactionTimes.append(int(reactionTime))
        
        
    if phase == "BotCheck":
        botCheckResponse = trialData.get("BotCheckResponse")
        if len(botCheckResponse) != 2: #response too short or too long
            botCheckPass = False
        else:
            letter = botCheckResponse[0:1]
            digit = botCheckResponse[1:2]
            if digit not in "0123456789": #second value not a digit
                botCheckPass = False
            if letter not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz": #first value not a letter
                botCheckPass = False
        
        
        
        
        
        
print("Confidence Scores:", partConfScores)
print("Answered all confidence questions?", allConfResponses)
print("Trial Accuracies:", trialAccuracy)
print("RTs:", reactionTimes)
print("Bot check response:", botCheckResponse)
print("Passed bot check?", botCheckPass)

        
    

con.close()


# TODO: Data Analysis. 
    #Look here: https://www.geeksforgeeks.org/create-a-pandas-dataframe-from-lists/
    #and here: https://reneshbedre.github.io/blog/anova.html


