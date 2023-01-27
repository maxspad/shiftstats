import json
import pandas as pd
from dataclasses import dataclass
import typing as t
import datetime 
import requests

class ScheduleExplorerError(ValueError):
    pass

class ScheduleExplorer:

    _API_URL = 'https://www.shiftadmin.com/api_getscheduledshifts_json.php'
    _API_VALIDATION_KEY = 'UMICH_jrmacyu77w'
    _API_GID = 1
    _API_STRFTIME = '%Y-%m-%d'

    def __init__(self, start_date : datetime.date, end_date : datetime.date,
        res : pd.DataFrame, exclude_nonem=True):

        self.start_date = start_date
        self.end_date = end_date

        # Sanity check the dates
        if end_date < start_date:
            raise ScheduleExplorerError('End Date must come after Start Date')

        # Call the ShiftAdmin API to get the shifts for the selected dates
        self.shifts = self._postproc_df(self._load_df_api())

        # Add pgy column to shifts
        self.shifts = self.shifts.merge(res[['userID','pgy']], 'left', on='userID')

        if exclude_nonem:
            self.shifts = self.shifts.dropna(subset=['pgy'])

        self.person_hours = self.shifts['shiftHours'].sum()
        self.n_shifts = len(self.shifts)
        self.n_residents = len(self.shifts['userID'].unique())
        
    def _load_df_api(self) -> pd.DataFrame:
        params = {'validationKey': self._API_VALIDATION_KEY, 'gid': self._API_GID, 
            'sd': self.start_date.strftime(self._API_STRFTIME), 'ed': self.end_date.strftime(self._API_STRFTIME)}
        r = requests.get(self._API_URL, params=params)
        data = r.json()

        # sanity check response
        if (data['status'] == 'success') and (len(data['data']['scheduledShifts']) >= 1):
            df = pd.json_normalize(data['data']['scheduledShifts'])
        else:
            raise ShiftAdminException('Shiftadmin API failure')

        return df

    def _postproc_df(self, df : pd.DataFrame) -> pd.DataFrame:
        df['shiftStart'] = pd.to_datetime(df['shiftStart'])
        df['shiftStartDay'] = df['shiftStart'].dt.date
        df['shiftType'] = df['shiftStart'].dt.hour.map(lambda x: 'Night' if x >= 20 else ('Evening' if x >= 11 else 'Morning'))
        
        df['shiftEnd'] = pd.to_datetime(df['shiftEnd'])
        df['shiftEndDay'] = df['shiftEnd'].dt.date
        
        df['Resident'] = df['firstName'].str[0] + '. ' + df['lastName']

        return df

    def shift_totals_by(self, gb : t.Collection[str], query : t.Union[str, None] = None):
        if query is not None:
            s = self.shifts.query(query)
        else:
            s = self.shifts
        return (s.groupby(gb)['id']
                 .count()
                 .reset_index()
                 .rename({'id': 'Count'}, axis=1))



def _json_to_df(data : dict) -> pd.DataFrame:
    df = pd.json_normalize(data['data']['scheduledShifts'])
    df['shiftStart'] = pd.to_datetime(df['shiftStart'])
    df['shiftStartDay'] = df['shiftStart'].dt.date
    df['shiftType'] = df['shiftStart'].dt.hour.map(lambda x: 'Night' if x >= 20 else ('Evening' if x >= 11 else 'Morning'))
    # df['isMorning'] = df['shiftStart'].dt.hour < 12
    # df['isEvening'] = (df['shiftStart'].dt.hour >= 12) & ~(df['isNight'])
    # df['shiftStartTime'] = df['shiftStart'].dt.time
    df['shiftEnd'] = pd.to_datetime(df['shiftEnd'])
    df['shiftEndDay'] = df['shiftEnd'].dt.date

    df['Resident'] = df['firstName'].str[0] + '. ' + df['lastName']
    # df['shiftEndTime'] = df['shiftEnd'].dt.time
    return df

def load_df_json_file(fn : str) -> pd.DataFrame: 
    with open(fn) as data_file:
        data = json.load(data_file)
    return _json_to_df(data)

class ShiftAdminException(Exception):
    pass

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