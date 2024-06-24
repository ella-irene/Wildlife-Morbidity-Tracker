import unittest
from datetime import datetime

from api import *

class APITester(unittest.TestCase):

    def setUp(self):
        self.api = Disease_API()

    def test_convert_record_dates_to_datetime(self):
        record = {
            'Event ID':202687,
            'Event Type':"Mortality/Morbidity",
            'Public':True,
            'Number Affected':37,
            'Event Start Date':'10/4/2022',
            'Event End Date':'11/17/2022',
            'Countries':'United States',
            'States (or equivalent)':'Minnesota',
            'Counties (or equivalent)':'"Aitkin County, MN"',
            'Species':'Canada Goose; Trumpeter Swan',
            'Event Diagnosis':'Highly Pathogenic Avian Influenza (AI virus H5N1); Undetermined'
        }
        start_date, end_date = self.api.convert_record_dates_to_datetime(record)
        self.assertEqual(datetime(2022, 10, 4), start_date)
        self.assertEqual(datetime(2022, 11, 17), end_date)

    def test_convert_record_dates_to_datetime_empty_enddate(self):
        record = {
            'Event ID':202687,
            'Event Type':"Mortality/Morbidity",
            'Public':True,
            'Number Affected':37,
            'Event Start Date':'10/4/2022',
            'Event End Date':'',
            'Countries':'United States',
            'States (or equivalent)':'Minnesota',
            'Counties (or equivalent)':'"Aitkin County, MN"',
            'Species':'Canada Goose; Trumpeter Swan',
            'Event Diagnosis':'Highly Pathogenic Avian Influenza (AI virus H5N1); Undetermined'
        }
        start_date, end_date = self.api.convert_record_dates_to_datetime(record)
        self.assertEqual(datetime(2022, 10, 4), end_date)
    
    def test_get_number_of_disease_cases_in_county_valid_county_and_disease(self):
        county = "Rice County, MN"
        disease = "Chytridiomycosis (Batrachochytrium dendrobatidis) suspect"
        result = self.api.get_number_of_disease_cases_in_county(disease, county)
        self.assertEqual(result, 27)
    
    def test_get_number_of_disease_cases_in_county_invalid_county_and_disease(self):
        county = "Fake County, MN"
        disease = "Fake Disease"
        result = self.api.get_number_of_disease_cases_in_county(disease, county)
        self.assertIsNone(result)

    def test_get_counties_with_disease_cases_valid_disease(self):
        # The union of the correct counties and the result counties should
        # be equal to the set of correct counties.
        disease = "Chytridiomycosis (Batrachochytrium dendrobatidis) suspect"
        correct_counties = {"Rice County, MN", "Winona County, MN"}
        result_counties = self.api.get_counties_with_disease_cases(disease)
        self.assertEqual(correct_counties, correct_counties.union(result_counties))

    def test_get_counties_with_disease_cases_invalid_disease(self):
        disease = "Fake disease"
        result_counties = self.api.get_counties_with_disease_cases(disease)
        self.assertIsNone(result_counties)

    def test_get_number_of_disease_cases_for_species(self):
        disease = "Chytridiomycosis (Batrachochytrium dendrobatidis) suspect"
        species = "Pickerel Frog"
        number_of_affected = self.api.get_number_of_disease_cases_for_species(disease, species)
        self.assertEqual(number_of_affected, 6)
    
    def test_get_number_of_disease_cases_for_invalid_species(self):
        disease = "Chytridiomycosis (Batrachochytrium dendrobatidis) suspect"
        species = "Pickle "
        number_of_affected = self.api.get_number_of_disease_cases_for_species(disease, species)
        self.assertIsNone(number_of_affected)

    def test_get_all_data_from_county(self):
        county = "Rice County, MN"
        records_from_county = self.api.get_all_data_from_county(county)
        number_of_records = len(records_from_county)
        self.assertEqual(number_of_records, 5)

    def test_get_all_data_from_invalid_county(self):
        county = "Fake County, MN"
        records_from_county = self.api.get_all_data_from_county(county)
        self.assertIsNone(records_from_county)

    def test_get_species_with_most_affected_animals_in_single_event(self):
        disease = "Toxicosis (lead) suspect"
        county = "Scott County, MN"
        correct_species = {'Trumpeter Swan':8}
        species = self.api.get_species_with_most_affected_animals_in_single_event(disease, county)
        self.assertEqual(correct_species, species)

    def test_get_species_with_most_affected_animals_in_single_event_invalid(self):
        disease = "Fake disease"
        county = "Scott County, MN"
        species = self.api.get_species_with_most_affected_animals_in_single_event(disease, county)
        self.assertIsNone(species)

    def test_get_county_with_most_affected_animals_in_single_event(self):
        disease = "Toxicosis (lead) suspect"
        correct_county = {'Lac Qui Parle County, MN':110}
        county = self.api.get_county_with_most_affected_animals_in_single_event(disease)
        self.assertEqual(correct_county, county)

    def test_get_county_with_most_affected_animals_in_single_event_invalid(self):
        disease = "Fake disease"
        county = self.api.get_county_with_most_affected_animals_in_single_event(disease)
        self.assertIsNone(county)

    def test_get_disease_with_most_affected_animals_in_single_event(self):
        species = "Big Brown Bat"
        correct_disease_pair = {"Emaciation (not otherwise specified)":70}
        disease_pair = self.api.get_disease_with_most_affected_animals_in_single_event(species)
        self.assertEqual(correct_disease_pair, disease_pair)

    def test_get_disease_with_most_affected_animals_in_single_event_invalid(self):
        species = "Fake species"
        disease_pair = self.api.get_disease_with_most_affected_animals_in_single_event(species)
        self.assertIsNone(disease_pair)

if __name__ == '__main__':
    unittest.main()
