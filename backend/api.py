import csv
import os
from datetime import datetime
from typing import Optional, List, Dict
from collections import defaultdict
import re
import psycopg2

import sys
sys.path.append('backend/')
import psqlConfig as config


# The first and last days there were datapoints in the DB
DATA_START_DATE = datetime(1991, 10, 17)
DATA_END_DATE = datetime(2023, 1, 1)

# The indices of data fields within a given DB row
EVENT_ID_INDEX = 0
NUMBER_AFFECTED_INDEX = 1
EVENT_START_DATE_INDEX = 2
EVENT_END_DATE_INDEX = 3
COUNTIES_INDEX = 4
SPECIES_INDEX = 5
DIAGNOSIS_INDEX = 6

class Disease_API:

    def __init__(self) -> None:
        """Creates an API object that is connected to the WHISPersData DB
        using the credentials within psqlConfig.py:
        
            user - username, which is also the name of the database
            password - the password for this database on perlman
        
        Note: exits if a connection cannot be established.

        Returns: 
            None  
        """

        try:
            dbconnection = psycopg2.connect(
                database=config.database,
                user=config.user, 
                password=config.password, 
                host="localhost"
            )
        except Exception as e:
            print("Connection error: ", e)
            exit()
        self.dbconnection = dbconnection
    
    def is_valid_timerange(self, start_date=DATA_START_DATE, end_date=DATA_END_DATE) -> bool:
        """Checks if entered date range is a valid date range
        within the data.

        Args:
            start_date (datetime): The start date of the time range, defaults to data's start
            end_date (datetime): The end date of the time range, defaults to data's end
            
        Returns: 
            True or False
        """

        if (start_date <= end_date and
            self.date_is_within_timerange(start_date) and
            self.date_is_within_timerange(end_date)):
            return True
        return False
    
    def convert_record_dates_to_datetime(self, record) -> datetime:
        """Converts the given record's start and end date strings
        to datetime objects, and returns the pair.

        Returns:
            (start_date, end_date) tuple, both as datetime objects
        """
        
        record_start_date = datetime.strptime(record["Event Start Date"], '%m/%d/%Y')

        # Some events have no end date. We treat those as single-day events.
        if record["Event End Date"] == "":
            record_end_date = record_start_date
        else:
            record_end_date = datetime.strptime(record["Event End Date"], '%m/%d/%Y')
        return (record_start_date, record_end_date)

    def date_is_within_timerange(
            self, date: datetime, start_of_timerange=DATA_START_DATE, end_of_timerange=DATA_END_DATE
        ) -> bool:
        """Checks if the given date is within the start date and end date, 
        inclusive. By default, start and end dates are those of the dataset.

        Args:
            date (datetime): The date to check
            start_of_timerange (datetime): Start of range - data start date by default
            end_of_timerange (datetime): End of range - data end date by default

        Returns:
            True or False
        """

        return start_of_timerange <= date <= end_of_timerange

    def get_number_of_disease_cases_in_county(
            self, disease: str, county: str, start_date=DATA_START_DATE, end_date=DATA_END_DATE
        ) -> int:
        """Gets the number of reports of the given disease within the
        county during the time range.

        Args:
            disease (str): The disease diagnosis to filter by
            county (str): The county in MN to search for reports in
            start_date (datetime): The start of the time range, defaults to data's start
            end_date (datetime): The end of the time range, defaults to data's end

        Returns:
            int: the number of disease reports
        """

        try:
            self.validate_user_inputs(
                disease=disease, 
                county=county, 
                start_date=start_date, 
                end_date=end_date
            )
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT * FROM events "
                "WHERE diagnoses LIKE %s "
                "AND counties LIKE %s " 
                "AND event_start_date >= %s::date " 
                "AND event_end_date <= %s::date "
            )
            cursor.execute(query, (
                '%' + disease + '%', 
                '%' + county + '%', 
                start_date, 
                end_date, 
            ))
            results = cursor.fetchall()
            return self.sum_number_affected(results)
        except ValueError as ve:
            print ("Some inputs were invalid: ", ve)
            return None
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None
    
    def sum_number_affected(self, results: List[tuple]) -> int:
        """Sums the number of affected from each result in the given results

        Args:
            results (List[tuple]): The data results returned from executing a query with a DB cursor
        """

        number_affected = 0
        for result in results:
            number_affected += int(result[NUMBER_AFFECTED_INDEX])
        return number_affected

    def get_counties_with_disease_cases(
            self, disease: str, start_date=DATA_START_DATE, end_date=DATA_END_DATE
        ) -> List[str]:
        """Gets a list of all counties in MN that have reports of the disease
        within the time range.

        Args:
            disease (str): The disease diagnosis to filter by
            start_date (datetime): The start of the time range, defaults to data's start
            end_date (datetime): The end of the time range, defaults to data's end

        Returns:
            List[str]: a list of county names
        """

        try:
            self.validate_user_inputs(
                disease=disease, 
                start_date=start_date, 
                end_date=end_date
            )
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT counties FROM events "
                "WHERE diagnoses LIKE %s "
                "AND event_start_date >= %s::date " 
                "AND event_end_date <= %s::date "
            )
            cursor.execute(query, (
                '%' + disease + '%', 
                start_date, 
                end_date, 
            ))
            results = cursor.fetchall()
            return self.convert_tuples_to_strings(results)
        except ValueError as ve:
            print ("Some inputs were invalid: ", ve)
            return None
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None
    
    def convert_tuples_to_strings(self, tuples: List[tuple]) -> List[str]:
        """Create a new list by converting each tuple in the list to a string"""

        results = []
        for tup in tuples:
            for string_of_one_or_more_counties in tup:
                results.extend(self.split_and_clean_result_string(string_of_one_or_more_counties))
        return self.remove_duplicates_from_list(results)

    def split_and_clean_result_string(self, string_with_one_or_more_elements: str) -> List[str]:
        """Splits and cleans the given string, placing them in a list
        
        Example input: 'Winona County, MN; Rice County, MN'
                output: ['Winona County, MN', 'Rice County, MN']
        """

        split_string = string_with_one_or_more_elements.split(';')
        cleaned_and_split_results = [county.strip() for county in split_string]
        return cleaned_and_split_results

    def remove_duplicates_from_list(self, list_with_duplicates: list) -> list:
        """Removes duplicates from the given list"""

        results = set(list_with_duplicates)
        return list(results)

    def get_number_of_disease_cases_for_species(
            self, disease: str, species: str, start_date=DATA_START_DATE, end_date=DATA_END_DATE
        ) -> int:
        """Gets the number of reported cases of the disease in the
        species during the time range.

        Args:
            disease (str): The disease diagnosis to filter by
            species (str): The species of animal to filter by
            start_date (datetime): The start of the time range, defaults to data's start
            end_date (datetime): The end of the time range, defaults to data's end

        Returns:
            int: the number of reports
        """

        try:
            self.validate_user_inputs(
                disease=disease, 
                species=species, 
                start_date=start_date, 
                end_date=end_date
            )
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT * FROM events "
                "WHERE diagnoses LIKE %s "
                "AND species LIKE %s "
                "AND event_start_date >= %s::date " 
                "AND event_end_date <= %s::date "
            )
            cursor.execute(query, (
                '%' + disease + '%', 
                '%' + species + '%', 
                start_date, 
                end_date, 
            ))
            results = cursor.fetchall()
            return self.sum_number_affected(results)
        except ValueError as ve:
            print ("Some inputs were invalid: ", ve)
            return None
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None
        
    def get_all_data_from_county( 
            self, county: str, start_date=DATA_START_DATE, end_date=DATA_END_DATE
        ) -> List[tuple]:
        """Gets all of the reports recorded in a given county within
        the time range.

        Args:
            county (str): The county in MN to search for reports in
            start_date (datetime): The start of the time range, defaults to data's start
            end_date (datetime): The end of the time range, defaults to data's end

        Returns:
            List[tuple]: a list of rows from the database
        """

        try:
            self.validate_user_inputs(
                county=county, 
                start_date=start_date, 
                end_date=end_date
            )
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT * FROM events "
                "WHERE counties LIKE %s "
                "AND event_start_date >= %s::date " 
                "AND event_end_date <= %s::date "
            )
            cursor.execute(query, (
                '%' + county + '%',  
                start_date, 
                end_date, 
            ))
            results = cursor.fetchall()
            return results
        except ValueError as ve:
            print ("Some inputs were invalid: ", ve)
            return None
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None
   
    def get_species_with_most_affected_animals_in_single_event(
            self, disease: str,  county: str, start_date=DATA_START_DATE, end_date=DATA_END_DATE
        ) -> Optional[str]:
        """Searches for the event with the highest number of animals affected,
        and returns the species(s) that were affected.

        Args:
            disease (str): The disease diagnosis to filter by
            county (str): The county in MN to search for reports in
            start_date (datetime): The start of the time range, defaults to data's start
            end_date (datetime): The end of the time range, defaults to data's end

        Returns:
            str: the name of the species as a string, or None if no records match
        """

        try:
            self.validate_user_inputs(
                disease=disease, 
                county=county, 
                start_date=start_date, 
                end_date=end_date
            )
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT species, number_affected FROM events "
                "WHERE diagnoses LIKE %s "
                "AND counties LIKE %s "                
                "AND event_start_date >= %s::date " 
                "AND event_end_date <= %s::date "
                "ORDER BY number_affected DESC "
                "LIMIT 1"
            )
            cursor.execute(query, (
                '%' + disease + '%', 
                '%' + county + '%', 
                start_date, 
                end_date, 
            ))
            results = cursor.fetchall()
            return results
        except ValueError as ve:
            print ("Some inputs were invalid: ", ve)
            return None
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None

    def get_county_with_most_affected_animals_in_single_event(
            self, disease: str, start_date=DATA_START_DATE, end_date=DATA_END_DATE
        ) -> tuple:
        """Searches for the event with the highest number of animals affected,
        and returns the county(s) where that event happened, along with the number affected.

        Args:
            disease (str): The disease diagnosis to filter by
            start_date (datetime): The start of the time range, defaults to data's start
            end_date (datetime): The end of the time range, defaults to data's end

        Returns:
            tuple: A [county, number affected] tuple
        """

        try:
            self.validate_user_inputs(
                disease=disease, 
                start_date=start_date, 
                end_date=end_date
            )
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT counties, number_affected FROM events "
                "WHERE diagnoses LIKE %s "               
                "AND event_start_date >= %s::date " 
                "AND event_end_date <= %s::date "
                "ORDER BY number_affected DESC "
                "LIMIT 1"
            )
            cursor.execute(query, (
                '%' + disease + '%', 
                start_date, 
                end_date, 
            ))
            results = cursor.fetchall()
            return results
        except ValueError as ve:
            print ("Some inputs were invalid: ", ve)
            return None
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None

    def get_disease_with_most_affected_animals_in_single_event(
            self, species: str, start_date=DATA_START_DATE, end_date=DATA_END_DATE
        ) -> tuple:
        """Searches for the event with the most number of reported disease cases
        for the given species, and returns the afflicting disease(s) and number affected.

        Args:
            species (str): The wildlife species to filter by
            start_date (datetime): The start of the time range, defaults to data's start
            end_date (datetime): The end of the time range, defaults to data's end

        Returns:
            tuple: A [(disease(s)), number affected] tuple
        """

        try:
            self.validate_user_inputs(
                species=species, 
                start_date=start_date, 
                end_date=end_date
            )
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT diagnoses, number_affected FROM events "
                "WHERE species LIKE %s "               
                "AND event_start_date >= %s::date " 
                "AND event_end_date <= %s::date "
                "ORDER BY number_affected DESC "
                "LIMIT 1"
            )
            cursor.execute(query, (
                '%' + species + '%', 
                start_date, 
                end_date, 
            ))
            results = cursor.fetchall()
            return results

        except ValueError as ve:
            print ("Some inputs were invalid: ", ve)
            return None
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None
        
    def get_record_with_most_affected(self) -> tuple: 
        """Gets the record that has the highest number of affected animals.

        Returns:
            tuple: The event with the most number of affected animals
        """

        try:
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT * FROM events "
                "ORDER BY number_affected DESC "
                "LIMIT 1"
            )
            cursor.execute(query)
            results = cursor.fetchall()
            return results
    
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None

    def validate_user_inputs(
        self, county=None, disease=None, species=None, start_date=None, end_date=None
    ):

        """Checks whether the given inputs are valid within the database. If not, raises
        ValueErrors for the invalid inputs."""

        if county:
            if not self.validate_county(county):
                raise ValueError(f"'{county}' is an invalid county.")          
        if disease:
            if not self.validate_disease(disease):
                raise ValueError(f"'{disease}' is an invalid disease.")          
        if species:
            if not self.validate_species(species):
                raise ValueError(f"'{species}' is an invalid species.")  
        if start_date:
            if not self.is_valid_timerange(start_date, DATA_END_DATE):
                start_date = datetime.strftime(start_date, "%m/%d/%Y")
                raise ValueError(f"{start_date} is an invalid start date.")
        if end_date:
            if not self.is_valid_timerange(DATA_START_DATE, end_date):
                end_date = datetime.strftime(end_date, "%m/%d/%Y")
                raise ValueError(f"{end_date} is an invalid end date.")             

    def validate_county(self, county: str) -> bool:
        """Checks whether the given county is a valid county in the database."""

        valid_counties = self.get_valid_counties()
        return county in valid_counties

    def validate_disease(self, disease: str) -> bool:
        """Checks whether the given disease is a valid county in the database."""

        valid_diseases = self.get_valid_diseases()
        return disease in valid_diseases

    def validate_species(self, species: str) -> bool:
        """Checks whether the given species is a valid county in the database."""

        valid_species = self.get_valid_species()
        return species in valid_species

    def get_valid_diseases(self) -> List[str]:
        """Creates a sorted list of strings with all of the diseases in this dataset

        Returns:
            List[str]: A list of all of the disease options
        """

        try:
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT diagnoses FROM events "
            )
            cursor.execute(query)
            results = cursor.fetchall()
            diseases = self.convert_tuples_to_strings(results)
            diseases.sort()
            return diseases
    
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None

    def get_valid_counties(self) -> List[str]:
        """Creates a sorted list of strings with all of the counties in this dataset

        Returns:
            List[str]: A list of all of the county options
        """

        try:
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT counties FROM events "
            )
            cursor.execute(query)
            results = cursor.fetchall()
            counties = self.convert_tuples_to_strings(results)
            counties.sort()
            return counties
    
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None
    
    def get_valid_species(self) -> List[str]:
        """Creates a sorted list of strings with all of the species in this dataset

        Returns:
            List[str]: A list of all of the species options
        """

        try:
            cursor = self.dbconnection.cursor()
            query = (
                "SELECT species FROM events "
            )
            cursor.execute(query)
            results = cursor.fetchall()
            species = self.convert_tuples_to_strings(results)
            species.sort()
            return species
        
        except Exception as e:
            print ("Something went wrong when executing the query: ", e)
            return None