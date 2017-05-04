import pandas as pd 
import numpy as np

# Years: 1990, 2000, 2005, 2009, 2010, 2015 
YEAR = '1990'

'''
these PUMS data was collected from: 
J:\Projects\Census\AmericanCommunitySurvey\Data\PUMS
'''
##################### input data ####################
INPUT_PATH = 'R:/Angela/equity/income/'
HOUSEHOLD_FILE_NAME = 'ACS Housing Records.csv'
PERSON_FILE_NAME = 'ACS Person Records_ data.csv'
PUMS_FILE_NAME = 'Regional PUMAs.csv'

# hosuehold 
PUMS_PATH_H = INPUT_PATH + YEAR + '/' + HOUSEHOLD_FILE_NAME
print PUMS_PATH_H
PUMS_H = pd.read_csv(PUMS_PATH_H)

# make different years' column names line up
if YEAR == '1990':
    PUMS_H['TEN'] = PUMS_H['TENURE']
    PUMS_H['FINCP'] = PUMS_H['RHHINC']
    PUMS_H['ADJINC'] = 1000000
    PUMS_H['WGTP'] = PUMS_H['HOUSWGT']
    PUMS_H['NP'] = PUMS_H['PERSONS']
    PUMS_H['TYPE'] = PUMS_H['RHHFAMTP']

if YEAR == '2000':
    PUMS_H['TEN'] = PUMS_H['TENURE']
    PUMS_H['FINCP'] = PUMS_H['HINC']
    PUMS_H['ADJINC'] = 1000000
    PUMS_H['WGTP'] = PUMS_H['HWEIGHT']
    PUMS_H['TYPE'] = PUMS_H['UNITTYPE']
    PUMS_H['NP'] = PUMS_H['PERSONS']

if YEAR == '2005':
    PUMS_H['ADJINC'] = PUMS_H['ADJUST']

# get occupied housing records, 'TEN' means tenure
PUMS_H['TEN'] = PUMS_H['TEN'].fillna(0)
PUMS_H = PUMS_H[PUMS_H['TEN'] != 0 ]
my_household = PUMS_H[['SERIALNO', #household id
                       'NP', # number of person in hh
                       'FINCP', # income
                       'ADJINC', # income adjustment factor
                       'WGTP', # hh weight
                       'PUMA', # geo code
                       'TEN', # tenure statues: if tenue is nan/0, it is not a occupied housing
                       'TYPE']] # type of unit: normally-1 is occupied, 2000 data-0 is occupied 

'''
# get PUMA data from person table, if it is not available in housing table
if YEAR == '': 
    PUMS_PATH_P = INPUT_PATH + YEAR + '/' + PERSON_FILE_NAME
    PUMS_P = pd.read_csv(PUMS_PATH_P)
    my_person = PUMS_P[['SERIALNO', 'PINCP', 'ADJINC', 'PUMA']]
'''


# PUMA 
#just for four counties: KING, KITSAP, PIERCE, SHONAMISH
PUMA_PATH = INPUT_PATH + YEAR + '/' + PUMS_FILE_NAME
PUMA = pd.read_csv(PUMA_PATH)
my_puma = PUMA[['PUMA', 'COUNTY']]

# Low income poverty threshold
'''
These poverty threshold was downloaded from U.S. Census web.
They are nation wide thresholds
''' 
poverty_thrdesh = {'2015' : {1: 12082, 
                             2: 15391, 
                             3: 18871, 
                             4: 24257, 
                             5: 28741, 
                             6: 32542, 
                             7: 36998, 
                             8: 41029, 
                             9: 49177}, 
                   '2010' : {1: 11139, 
                             2: 14218,
                             3: 17374,
                             4: 22314,
                             5: 26439,
                             6: 29897, 
                             7: 34009,
                             8: 37934,
                             9: 45220},
                   '2009' : {1: 10956,
                             2: 13991,
                             3: 17098,
                             4: 21954,
                             5: 25991,
                             6: 29405,
                             7: 33372,
                             8: 37252,
                             9: 44366},
                   '2005' : {1: 9973, 
                             2: 12755,
                             3: 15577,
                             4: 19971, 
                             5: 23613,
                             6: 26683,
                             7: 30249,
                             8: 33610,
                             9: 40288},
                   '2004' : {1: 9646,
                             2: 12335, 
                             3: 15066,
                             4: 19307,
                             5: 22830,
                             6: 25787,
                             7: 29233,
                             8: 32641,
                             9: 39062},
                   '2000' : {1: 8794,
                             2: 11239,
                             3: 13738,
                             4: 17603,
                             5: 20819,
                             6: 23528,
                             7: 26753,
                             8: 29701,
                             9: 35060},
                   '1990' : {1: 6652,
                             2: 8509,
                             3: 10419,
                             4: 13359,
                             5: 15792,
                             6: 17839,
                             7: 20241,
                             8: 22582,
                             9: 26848}}

################### computation #################
# step1: adjust the income
    '''
    because the census data were collected during a long period of time
    there is possible that Jan's income is slightly lower then Dec's income
    so we want  to convert all income data into a common date point
    '''

my_household['adjusted_inc'] = my_household['ADJINC']*my_household['FINCP']*0.000001

# step2: estimate the individual number which was represented from PUMS households
'''
PUMS data is sample size data, so we want to apply certain weight to expand to the full size 
'''
my_household['est_indiv'] = my_household['NP']*my_household['WGTP']

# step3: narrow down to four-counties household 
my_household = pd.merge(my_household, my_puma, on='PUMA') 

# step4: create an empty dataframe to hold the low income household
low_income = pd.DataFrame(columns = ['SERIALNO', 'NP', 'FINCP', 'ADJINC', 'WGTP', 'PUMA', 'TYPE', 'COUNTY', 'adjusted_inc', 'est_indiv'])

# step5: narrow down to low-income household 
for hh in np.unique(my_household['SERIALNO']): 
    h = my_household[my_household['SERIALNO'] == hh]
    num_p = h['NP'].iloc[0]
    # We decied: Puget Sound Region's low income definition is 200% of national wide poverty threshold
    if len(h['adjusted_inc']) != 0: 
        # filter out the low income household
        if num_p >0 and num_p < 9:
            pov = poverty_thrdesh[YEAR][num_p]* 2 
            if h['adjusted_inc'].iloc[0] <= pov: 
                print 'yes'
                low_income = pd.concat([low_income, h])
        if num_p >= 9: 
            pov = poverty_thrdesh['2015'][9]* 2
            if h['adjusted_inc'].iloc[0] <= pov: 
                print 'yes'
                low_income = pd.concat([low_income, h])

#################### output #####################
# County ID: 33-King, 35-Kitsap, 53-Pierce, 61-Snohomish
# KING
low_income_king = low_income[low_income['COUNTY'] == 33]
king = np.sum(low_income_king['est_indiv'])

# KITSAP
low_income_kitsap = low_income[low_income['COUNTY'] == 35] 
kitsap = np.sum(low_income_kitsap['est_indiv']) 

# PIERCE
low_income_pierce = low_income[low_income['COUNTY'] == 53] 
pierce = np.sum(low_income_pierce['est_indiv'])  

# SNOHOMISH
low_income_snohomish = low_income[low_income['COUNTY'] == 61] 
snohomish = np.sum(low_income_snohomish['est_indiv'])  

print 'king', king
print 'kitsap', kitsap
print 'pierce', pierce
print 'snohomish', snohomish