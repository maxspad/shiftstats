'''Module containing helper functions for working with the ShiftAdmin schedule'''

import json
import pandas as pd
from dataclasses import dataclass
import typing as t
import datetime 
import requests


_API_URL = 'https://www.shiftadmin.com/api_getscheduledshifts_json.php'
_API_VALIDATION_KEY = 'UMICH_jrmacyu77w'
_API_GID = 1
_API_STRFTIME = '%Y-%m-%d'

class ScheduleError(ValueError):
    pass


def load_sched_api(start_date : datetime.date, end_date : datetime.date) -> pd.DataFrame:
    # Sanity check the dates
    if end_date < start_date:
        raise ScheduleError('End Date must come after Start Date')

    params = {'validationKey': _API_VALIDATION_KEY, 'gid': _API_GID, 
        'sd': start_date.strftime(_API_STRFTIME), 'ed': end_date.strftime(_API_STRFTIME)}
    r = requests.get(_API_URL, params=params)
    data = r.json()
    df = _json_to_df(data)

    # Clean and add extra columns
    df = _postproc_df(df)

    return df

def add_res_to_sched(sched : pd.DataFrame, res : pd.DataFrame) -> pd.DataFrame:
    return (sched.merge(res[['userID','pgy']], how='left', on='userID')
                 .rename({'pgy' : 'PGY'}, axis=1))

def _postproc_df(df : pd.DataFrame) -> pd.DataFrame:
    df['Start'] = pd.to_datetime(df['shiftStart'])
    df['Start Date'] = df['Start'].dt.date
    df['Start Hour'] = df['Start'].dt.hour
    
    df['End'] = pd.to_datetime(df['shiftEnd'])
    df['End Date'] = df['End'].dt.date
    df['End Hour'] = df['End'].dt.hour

    df['Type'] = df['Start'].dt.hour.map(lambda x: 'Night' if x >= 20 else ('Evening' if x >= 11 else 'Morning'))
    
    df['Resident'] = df['firstName'].str[0] + ' ' + df['lastName']

    df.rename({
        'firstName': 'First Name',
        'lastName': 'Last Name',
        'groupShortName': 'Group',
        'facilityAbbreviation': 'Site',
        'shiftShortName': 'Shift',
        'shiftHours': 'Length'
    }, axis=1, inplace=True)

    df.drop(['employeeID','nPI','facilityExtID','shiftStart','shiftEnd'], inplace=True, axis=1)

    return df[['Resident','Shift','Site',
        'Start','End', 'Type', 'Length',
        'Start Date','Start Hour',
        'End Date', 'End Hour',
        'First Name', 'Last Name', 'userID',
        'facilityID','groupID','Group']]

def _json_to_df(data : dict) -> pd.DataFrame:
    # Check response
    if (data['status'] == 'success') and (len(data['data']['scheduledShifts']) >= 1):
        df = pd.json_normalize(data['data']['scheduledShifts'])
    else:
        raise ScheduleError('Shiftadmin API failure')
    return df

def load_df_json_file(fn : str) -> pd.DataFrame: 
    with open(fn) as data_file:
        data = json.load(data_file)
    return _postproc_df(_json_to_df(data))

def full_df_to_rel(df : pd.DataFrame) -> t.Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    '''Converts a giant long DF into a set of separate tables'''
    # Group
    groups_df = df[['groupID','groupShortName']].drop_duplicates().set_index('groupID').sort_index()
    # Users
    users_df = df[['userID','employeeID','nPI','firstName','lastName']].drop_duplicates().set_index('userID').sort_index()
    # Facilities
    facs_df = df[['facilityID','facilityExtID','facilityAbbreviation']].drop_duplicates().set_index('facilityID').sort_index()
    # Shifts
    shifts_df = df[['shiftID','shiftShortName','facilityID','groupID']]
    shifts_df = shifts_df.drop_duplicates().set_index('shiftShortName').sort_index()
    
    return groups_df, users_df, facs_df, shifts_df

def load_block_dates(fn : str) -> pd.DataFrame:
    bd = pd.read_csv(fn, parse_dates=['Start Date', 'End Date', 'Mid-transition Start Date'])
    bd.rename({'Mid-transition Start Date': 'Mid-Block Transition Date'}, axis=1, inplace=True)
    return bd

def load_residents(fn : str) -> pd.DataFrame:
    res = pd.read_csv(fn).reset_index()
    return res

if __name__ == '__main__':
    start_date = datetime.date.today()
    end_date = datetime.date.today() + datetime.timedelta(days=7)
    # load_df_api(start_date, end_date)

    # load_df_api(start_date, start_date)