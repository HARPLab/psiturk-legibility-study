from sqlalchemy import create_engine, MetaData, Table
import json
import pandas as pd
import scipy.stats as stats

db_url = "sqlite:///participants.db"
table_name = 'sophisticatedDev'
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
    print(part)

#HERE: Each participant's "data" section is in its own list
    
# flatten nested list so we just have a list of the trialdata recorded
# each time psiturk.recordTrialData(trialdata) was called.
data = [record['trialdata'] for part in data for record in part]

#HERE: A list of the trialdata calls (not by participant)


# Put all subjects' trial data into a dataframe object from the
# 'pandas' python library: one option among many for analysis
data_frame = pd.DataFrame(data)

print(data_frame)