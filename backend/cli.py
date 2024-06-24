import api
import inspect

API_OBJECT = api.Disease_API()
NUMBERED_FUNCTIONS = { 
    1: "get_all_data_from_county",
    2: "get_counties_with_disease_cases",
    3: "get_county_with_most_affected_animals_in_single_event",
    4: "get_disease_with_most_affected_animals_in_single_event",
    5: "get_number_of_disease_cases_for_species",
    6: "get_number_of_disease_cases_in_county",
    7: "get_species_with_most_affected_animals_in_single_event",
    8: "get_valid_counties",
    9: "get_valid_diseases",
    10: "get_valid_species",
}
FUNCTION_DESCRIPTIONS = {
    1: "Retrieves every event reported in the given county, along with all associated event information",
    2: "Gets a list of every county with a report of the given disease",
    3: "Searches for the event with the highest number of animals affected, and returns the county(s) where that event happened, along with the number affected",
    4: "Finds the disease that affected the most animals of a given species in one reported event",
    5: "Gets the number of reported cases of a disease in a given species",
    6: "Gets the number of animals affected by a given disease within a given county",
    7: "Searches for the event with the single highest number of animals affected, and returns the species(s) that were affected",
    8: "Prints all of the counties in the database",
    9: "Prints all of the diseases in the database\nNote: disease reports sometimes have similar names, but are kept separate in our queries to be as consistent with the data as possible",
    10: "Prints all of the species in the database",
}

def main():
    user_wants_to_continue = 'y'
    while user_wants_to_continue == 'y':
        func = get_user_function_choice()
        inputs = get_user_inputs_for_function(func)
        run_function_with_inputs(func, inputs)
        user_wants_to_continue = input(
            "\nWould you like to select another function? ('y' to continue, anything else to quit) "
        )

def get_user_function_choice():
    print_functions()
    print(
        "\nPlease type the number of the function you would like to run.\n"
        "Please note, while we provide some sample inputs once you select a function,\n"
        "functions 8, 9, and 10 will allow you to see full lists of possible inputs.\n"
    )

    input_is_valid = False
    user_function_choice = None
    while not input_is_valid:
        try:
            user_function_choice = int(input("\nFunction number: "))
            input_is_valid = True
        except ValueError as e:
            print("Please input the integer corresponding to the desired function")
            continue

        if 1 <= user_function_choice <= 10:
            user_function_choice = NUMBERED_FUNCTIONS[user_function_choice]
            input_is_valid = True
        else:
            input_is_valid = False
            print("Invalid number, please enter a number between 1 and 10")

    return get_function_from_name(user_function_choice)

def get_function_from_name(function_name: str):
    return getattr(api.Disease_API, function_name)

def print_functions():
    """Code snippet from w3docs.com/snippets/python/how-to-list-all-functions-in-a-module.html"""

    helper_method_names = ["get_record_dates_as_datetime", "get_record_with_most_affected"]
    class_objects = dir(api.Disease_API)
    number = 1
    for name in class_objects:
        if (is_method_in_api(name) 
            and "get" in name 
            and name not in helper_method_names):
            print(f"{number}: {name}")
            print(f"{FUNCTION_DESCRIPTIONS[number]}\n")
            number += 1

def is_method_in_api(method_name) -> bool:
    try:
        object_in_api = getattr(api.Disease_API, method_name)
    except AttributeError as e:
        print(f"AttributeError: {e}")
        return False
    return inspect.isfunction(object_in_api)

def get_user_inputs_for_function(func) -> list:
    parameter_names = get_function_parameter_names(func)
    user_inputs = []
    for name in parameter_names:
        if name == 'county':
            user_inputs.append(get_user_input_county())
        elif name == 'disease':
            user_inputs.append(get_user_input_disease())
        elif name == 'species':
            user_inputs.append(get_user_input_species())
    return user_inputs

def get_user_input_county():
    user_input, is_valid_input = "", False
    print("\nSome examples for county format would be 'Rice County, MN' or 'Ramsey County, MN' ")
    while not is_valid_input:
        user_input = input("Please input a valid value for county: ")
        is_valid_input = API_OBJECT.validate_county(user_input)
        if not is_valid_input: print("invalid county")
    return user_input

def get_user_input_disease():
    is_valid_input = False
    print("\nSome examples for disease format would be 'Newcastle Disease' or 'Anemia'")
    while not is_valid_input:
        user_input = input(f"Please input a valid value for disease: ")
        is_valid_input = API_OBJECT.validate_disease(user_input)
        if not is_valid_input: print("invalid disease")
    return user_input

def get_user_input_species():
    is_valid_input = False
    print("\nSome examples for species format would be 'Canada Goose' or 'Big Brown Bat'")
    while not is_valid_input:
        user_input = input(f"Please input a valid value for species: ")
        is_valid_input = API_OBJECT.validate_species(user_input)
        if not is_valid_input: print("invalid species")
    return user_input

def run_function_with_inputs(func, inputs: list):
    results = func(API_OBJECT, *inputs)
    phrase = get_phrase_for_function(func)
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(f"{phrase}")

    if not results:
        print(f"No results found matching parameters {inputs}")    
    elif type(results) == dict:
        for key, value in results.items():
            print(f"{key}: {value} affected")
    elif type(results) == list:
        results.sort()
        for result in results:
            print(f"- {result}")
    elif type(results) == int:
        print(results)  
    else:
        print(f"{type(results)}: {results}")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    
def get_phrase_for_function(func) -> str:
    function_phrases = {
        "get_number_of_disease_cases_in_county":"The number of disease cases in that county is: ",
        "get_counties_with_disease_cases":"The counties with reports of the disease are: ",
        "get_number_of_disease_cases_for_species":"The number of reports of the disease in that species is: ",
        "get_all_data_from_county":"All of the reports in that county are: ",
        "get_species_with_most_affected_animals_in_single_event":"The most affected species in a single report is/are: ",
        "get_county_with_most_affected_animals_in_single_event":"The county with the most affected animals in a single report is/are: ",
        "get_disease_with_most_affected_animals_in_single_event":"The animals in the report with the highest number of affected were affected by the disease(s): ",
        "get_valid_counties":"The list of counties in the database is: ",
        "get_valid_diseases":"The list of diseases in the database is: ",
        "get_valid_species":"The list of species in the database is: "
    }
    function_name = func.__name__
    return function_phrases[function_name]


def get_function_parameter_names(func) -> str:
    signature = inspect.signature(func)
    return [
        param.name for param in signature.parameters.values() 
        if param.name != 'self' 
        and param.name != 'start_date' 
        and param.name != 'end_date'
    ]

if __name__ == "__main__":
    main()