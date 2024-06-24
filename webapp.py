import flask
from flask import render_template, request, url_for, redirect, Flask, session
import json
import sys
import backend.api 
import logging

app = flask.Flask(__name__)

# needed in order to use flask.session, which we use as a sort of global variable to access form data outside of its context
app.secret_key = "supersecretkey1234"

API_OBJECT = backend.api.Disease_API()
VALID_DISEASES = API_OBJECT.get_valid_diseases()
VALID_COUNTIES = API_OBJECT.get_valid_counties()
VALID_SPECIES = API_OBJECT.get_valid_species()

# This line tells the web browser to *not* cache any of the files.
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
@app.route('/home')
def home():
    '''Renders the website's homepage.'''

    return render_template('home.html')

@app.route('/aboutTheData')
def aboutTheData():
    '''Renders the About the Data page.'''

    return render_template('aboutTheData.html')

@app.route('/searchTheData', methods=['GET'])
def searchTheData():
    '''Renders the initial Search the Data page with the available query options,
    or reroutes to the appropriate query page once one is selected.
    '''

    return render_template('searchTheData.html', valid_queries=QUERY_DISPLAY_NAMES_TO_VIEW)

@app.route('/searchTheData/<query>', methods=['GET','POST'])
def searchTheDataForQuery(query):
    '''Renders the search the data page with a parameters form corresponding to the
    given query, or reroutes to the appropriate results page once the form
    has been submitted.
    '''

    if request.method == 'GET':
        return renderTemplateForQuery(query)

    elif request.method == 'POST':
        form_data = request.form
        session['form_data'] = form_data
        return redirect(url_for("searchTheDataWithQueryResults", query=query))

def renderTemplateForQuery(query):
    view_function_for_query = QUERY_DISPLAY_NAMES_TO_VIEW[query]

    if queryTakesNoParameters(query):
        return view_function_for_query()

    template_for_query = f"{view_function_for_query.__name__}.html"
    return render_template(
        template_for_query, 
        valid_diseases=VALID_DISEASES,
        valid_counties=VALID_COUNTIES,
        valid_species=VALID_SPECIES,
        valid_queries=QUERY_DISPLAY_NAMES_TO_VIEW
    )

def queryTakesNoParameters(query):
    '''Returns True if the query takes no parameters, else returns False.'''

    view_function_for_query = QUERY_DISPLAY_NAMES_TO_VIEW[query]
    if view_function_for_query in (getValidCounties, getValidDiseases, getValidSpecies):
        return True
    return False

@app.route("/searchTheData/<query>/results", methods=['GET'])
def searchTheDataWithQueryResults(query):
    '''Renders the Results page for the given query and input parameters.'''

    view_for_query = QUERY_DISPLAY_NAMES_TO_VIEW[query]
    parameter_form_data = session['form_data']
    return view_for_query(parameter_form_data)
   
def getAllDataFromCounty(parameter_form_data):
    county = parameter_form_data.get('county-selection')
    result = API_OBJECT.get_all_data_from_county(county = county)

    return render_template(
        'getAllDataFromCounty.html',
        valid_counties = VALID_COUNTIES,
        county_filter = county,
        result = result
    )

def getCountiesWithDiseaseCases(parameter_form_data):
    disease = parameter_form_data.get('disease-selection')
    result = API_OBJECT.get_counties_with_disease_cases(disease = disease)
    
    return render_template(
        'getCountiesWithDiseaseCases.html',
        valid_disease=VALID_DISEASES,
        disease_filter=disease,
        result = result  
    )

def getCountyWithMostAffectedAnimalsInSingleEvent(parameter_form_data):
    disease = parameter_form_data.get('disease-selection')
    result = API_OBJECT.get_county_with_most_affected_animals_in_single_event(disease=disease)
    for row in result:
        county = row[0]
        numAffected = row[1]
    
    return render_template(
        'getCountyWithMostAffectedAnimalsInSingleEvent.html',
        valid_disease = VALID_DISEASES,
        disease_filter = disease,
        result = result,
        county = county,
        numAffected = numAffected
    )

def getDiseaseWithMostAffectedAnimalsInSingleEvent(parameter_form_data):
    species = parameter_form_data.get('species-selection')
    result = API_OBJECT.get_disease_with_most_affected_animals_in_single_event(species=species)
    for row in result:
        disease = row[0]
        numAffected = row[1]
    
    return render_template(
        'getDiseaseWithMostAffectedAnimalsInSingleEvent.html',
        valid_queries = QUERY_DISPLAY_NAMES_TO_VIEW,
        species_filter = species,
        result = result,
        disease = disease,
        numAffected = numAffected    
    )

def getNumberOfDiseaseCasesForSpecies(parameter_form_data):
    disease = parameter_form_data.get('disease-selection')
    species = parameter_form_data.get('species-selection')
    result = API_OBJECT.get_number_of_disease_cases_for_species(
        disease=disease,
        species=species
    )
    
    return render_template(
        'getNumberOfDiseaseCasesForSpecies.html',
        valid_queries=QUERY_DISPLAY_NAMES_TO_VIEW,
        disease_filter=disease,
        species_filter=species,
        result=result
    )

def getNumberOfDiseaseCasesInCounty(parameter_form_data):
    disease = parameter_form_data.get('disease-selection')
    county = parameter_form_data.get('county-selection')
    result = API_OBJECT.get_number_of_disease_cases_in_county(
        disease=disease,
        county=county
    )

    return render_template(
        'getNumberOfDiseaseCasesInCounty.html',
        valid_queries=QUERY_DISPLAY_NAMES_TO_VIEW,
        disease_filter=disease,
        county_filter=county,
        result=result
    )

def getSpeciesWithMostAffectedAnimalsInSingleEvent(parameter_form_data):
    disease = parameter_form_data.get('disease-selection')
    county = parameter_form_data.get('county-selection')
    result = API_OBJECT.get_species_with_most_affected_animals_in_single_event(
        disease=disease,
        county=county
    )
    
    return render_template(
        'getSpeciesWithMostAffectedAnimalsInSingleEvent.html',
        disease_filter = disease,
        county_filter = county,
        result = result
    )

def getValidCounties():
    result = API_OBJECT.get_valid_counties()
    return render_template(
        'getValidCounties.html',
        result=result
    )

def getValidDiseases():
    result = API_OBJECT.get_valid_diseases()
    return render_template(
        'getValidDiseases.html',
        result=result
    )

def getValidSpecies():
    result = API_OBJECT.get_valid_species()
    return render_template(
        'getValidSpecies.html',
        result=result
    )

QUERY_DISPLAY_NAMES_TO_VIEW = { 
    "See all reports from a county": getAllDataFromCounty,
    "See all counties with cases of a disease": getCountiesWithDiseaseCases,
    "See county with most affected animals in a single event": getCountyWithMostAffectedAnimalsInSingleEvent,
    "See disease with most affected animals in single event": getDiseaseWithMostAffectedAnimalsInSingleEvent,
    "See species with most affected animals in a single event": getSpeciesWithMostAffectedAnimalsInSingleEvent,
    "See number of disease cases for a species": getNumberOfDiseaseCasesForSpecies,
    "See number of disease cases in a county": getNumberOfDiseaseCasesInCounty,
    "See all valid counties": getValidCounties,
    "See all valid diseases": getValidDiseases,
    "See all valid species": getValidSpecies
}

'''
Run the program by typing 'python3 webapp.py perlman.mathcs.carleton.edu [port]'
'''
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: {0} host port'.format(sys.argv[0]), file=sys.stderr)
        exit()

    host = sys.argv[1]
    port = sys.argv[2]
    app.run(host=host, port=port)