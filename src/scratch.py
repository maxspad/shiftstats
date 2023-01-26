import json
import pandas as pd
from dataclasses import dataclass

# @dataclass
# class Group:
#     groupID: int
#     groupShortName: str

# @dataclass
# class User:
#     userID: int
#     employeeID: str
#     nPI: str
#     firstName: str 
#     lastName: str

# @dataclass 

def load_df_json(fn : str) -> pd.DataFrame: 
    with open(fn) as data_file:
        data = json.load(data_file)
    df = pd.json_normalize(data['data']['scheduledShifts'])
    df['shiftStart'] = pd.to_datetime(df['shiftStart'])
    df['shiftEnd'] = pd.to_datetime(df['shiftEnd'])
    return df

def full_df_to_rel(df : pd.DataFrame):
    '''Converts a giant long DF into a set of separate tables'''
    # Group
    groups_df = df[['groupID','groupShortName']].drop_duplicates().set_index('groupID').sort_index()
    # Users
    users_df = df[['userID','employeeID','nPI','firstName','lastName']].drop_duplicates().set_index('userID').sort_index()
    # Facilities
    facs_df = df[['facilityID','facilityExtID','facilityAbbreviation']].drop_duplicates().set_index('facilityID').sort_index()
    # Shifts
    shifts_df = df[['shiftID','shiftShortName','facilityID','groupID']]
    # shifts_df['shiftStartTime'] = shifts_df['shiftStart'].dt.time
    # shifts_df['shiftEndTime'] = shifts_df['shiftEnd'].dt.time
    # shifts_df.drop(['shiftStart','shiftEnd'], axis=1, inplace=True)
    shifts_df = shifts_df.drop_duplicates().set_index('shiftShortName').sort_index()
    return groups_df, users_df, facs_df, shifts_df


df = load_df_json('../data/api_getscheduledshifts_json.json')
cols = df.columns
# for c in cols:
#     print(f'{c}: {len(df[c].unique())} unique values ({df[c].dtype})')
# print(df.shape)

groups, users, facs, shifts = full_df_to_rel(df)
