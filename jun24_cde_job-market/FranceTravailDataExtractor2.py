import requests
import json
import os
import time
import csv
import mysql.connector
import re
from mysql.connector import Error
import sys
from datetime import datetime
import logging
from database import get_db_persistent

HOURS_PER_MONTH = 151.67
WEEKS_PER_MONTH = 4.33

def get_credentials(OUTPUT_DIR: str) -> dict[str, str]:
    """
    Récupère les accréditations à partir d'un fichier JSON.
    """
    with open(os.path.join(OUTPUT_DIR, "clientCredentials.json"), "r") as idFile:
        logging.debug(os.path.join(OUTPUT_DIR, "clientCredentials.json"))
        return json.load(idFile)

def get_access_token(client_id: str, client_secret: str) -> tuple[str, str]:
    """
    Création des accès via les accréditations clients.
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "o2dsoffre api_offresdemploiv2"
    }

    try:
        req=requests.post(url= "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
                headers= headers,params=params)
        req.raise_for_status()
        token_data = req.json()
        return token_data["access_token"], token_data["token_type"]
    except requests.exceptions.HTTPError as errh: 
        logging.exception("HTTP Error") 
        logging.exception(errh.args[0]) 

# def requete_api(token_type:str, token:str):
    # """
    # Requête l'API de France Travail.
    # """
    # headers={
        # "Accept": "application/json",
        # "Authorization": f"{token_type} {token}"
    # }

    # try :
        # query = requests.get(url="https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
                              # headers= headers)
        # query.raise_for_status()
        # return query.json(), query.headers
    # except requests.exceptions.HTTPError as errh:
        # print('HTTP Error:', errh)
        
def years_to_months(years):
    months = years * 12
    return months
    
def days_to_months(days):
    months = days / 30
    return round(months,2)

def get_naf_labels(token_type: str, token: str):
    """
    Requête le référentiel NAF de l'API de France Travail pour récupérer les libellés de chaque code.
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"{token_type} {token}"
    }
    

    
    
    try:
        query = requests.get(
            url="https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/nafs",
            headers=headers,
            timeout=10  # 10 seconds timeout
        )
        
        # Check if the response was successful
        query.raise_for_status()
        
        # Check if the response is JSON
        if query.headers.get('Content-Type') == 'application/json':
            data = query.json()  # Parse the response to JSON
            
            # Now you have the JSON data, which is a list of dictionaries.
            # For example, you can extract the `code` and `libelle` from each item in the list:
            naf_dict = {item['code']: item['libelle'] for item in data}
            return naf_dict
        else:
            logging.error(f"Unexpected response format: {query.headers.get('Content-Type')}")
            return None
    
    except requests.exceptions.HTTPError as errh:
        logging.error(f"HTTP Error: {errh}")
        return None
    except requests.exceptions.Timeout as errt:
        logging.error(f"Timeout Error: {errt}")
        return None
    except requests.exceptions.RequestException as err:
        logging.error(f"Request Error: {err}")
        return None

def get_rome_codes(token_type: str, token: str):
    """
    Requête le référentiel ROME de l'API de France Travail pour récupérer tous les codes.
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"{token_type} {token}"
    }
    

    
    
    try:
        query = requests.get(
            url="https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/metiers",
            headers=headers,
            timeout=10  # 10 seconds timeout
        )
        
        # Check if the response was successful
        query.raise_for_status()
        
        # Check if the response is JSON
        if query.headers.get('Content-Type') == 'application/json':
            data = query.json()  # Parse the response to JSON
            
            # Now you have the JSON data, which is a list of dictionaries.
            # For example, you can extract the `code` and `libelle` from each item in the list:
            rome_codes = [item['code'] for item in data]
            return rome_codes
        else:
            logging.error(f"Unexpected response format: {query.headers.get('Content-Type')}")
            return None
    
    except requests.exceptions.HTTPError as errh:
        logging.error(f"HTTP Error: {errh}")
        return None
    except requests.exceptions.Timeout as errt:
        logging.error(f"Timeout Error: {errt}")
        return None
    except requests.exceptions.RequestException as err:
        logging.error(f"Request Error: {err}")
        return None

    
def convert_to_mysql_datetime(iso_datetime: str) -> str:
    # Remove the 'Z' and convert the string to the MySQL format
    if iso_datetime.endswith('Z'):
        iso_datetime = iso_datetime[:-1]
    
    # Convert to MySQL format (without Z) and handle fractional seconds
    datetime_obj = datetime.fromisoformat(iso_datetime)
    
    # Convert back to string in MySQL-compatible format
    return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    
def insert_job(cursor, connection, job_offer: dict, company_id, contact_id) -> int:
   
    moving = job_offer.get("deplacementCode",1)
    try:
        
        
        def extract_experience_length(experience_label):
            experience_label = job_offer.get("experienceLibelle")
             # Check for months in experience_label
            contract_match = re.search(r"(\d+)\s*Mois$", experience_label)
            # Check for years (with optional "(s)") in experience_label
            contract_match2 = re.search(r"(\d+)\s*(An(?:\(s\)))?", experience_label)
            
            if contract_match:
                experience_length = int(contract_match.group(1))  # Extract the number of months
                return experience_length
    
            # If experience_label is in years(and optional "An(s)" is present)
            elif contract_match2:
                experience_length = int(contract_match2.group(1))  # Extract the number of years
                experience_length = years_to_months(experience_length)  # Convert days to months
                return experience_length
    
            # Default case when no valid work duration is found
            else:
                experience_length = 0
                return experience_length
                
        
            
        # Insert or Update query
        insert_query = """
        INSERT INTO job ( title, description, creation_date, update_date, rome_code, 
                          experience_required, experience_length_months, is_alternance, 
                         is_disabled_friendly, naf_code, qualification_code, candidates_missing, 
                         activity_sector_code, moving_code, experience_detail, insee_code, company_id, contact_id, internal_id)
        VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            creation_date = VALUES(creation_date),
            update_date = VALUES(update_date),
            experience_required = VALUES(experience_required),
            experience_length_months = VALUES(experience_length_months),
            is_alternance = VALUES(is_alternance),
            is_disabled_friendly = VALUES(is_disabled_friendly),
            candidates_missing = VALUES(candidates_missing),
            moving_code = VALUES(moving_code),
            experience_detail = VALUES(experience_detail),
            insee_code = VALUES(insee_code)
        """
        
        # Execute the query
        cursor.execute(insert_query, (
            
            job_offer.get("intitule"),
            job_offer.get("description"),
            convert_to_mysql_datetime(job_offer.get("dateCreation")),
            convert_to_mysql_datetime(job_offer.get("dateActualisation")),
            job_offer.get("romeCode"),
            job_offer.get("experienceExige"),
            extract_experience_length(job_offer.get("experienceLibelle")),
            job_offer.get("alternance"),
            job_offer.get("accessibleTH"),
            job_offer.get("codeNAF"),
            job_offer.get("qualificationCode"),
            job_offer.get("offresManqueCandidats",0),
            job_offer.get("secteurActivite"),
            moving,
            job_offer.get("experienceCommentaire"),
            job_offer.get("lieuTravail", {}).get("commune", "75056"),
            company_id,
            contact_id,
            job_offer.get("id")
            
        ))
        logging.debug(f"Executed query: {cursor._executed}")

        # Retrieve the job_id of the inserted/updated record
        if cursor.lastrowid:
            logging.info(f"Inserted into `job`: {cursor.lastrowid}")
            return cursor.lastrowid
        else:
            cursor.execute("SELECT job_id FROM job WHERE internal_id = %s", 
                           (job_offer.get("id"),))
            logging.debug(f"Executed query: {cursor._executed}")
            result = cursor.fetchone()
            logging.info(f"Duplicate ignored in table `salary`: {result}")
            return result[0] if result else None  
       
        logging.info(f"Job updated with ID: {result}")
        
    except Error as e:
        logging.exception(f"Error inserting/updating job: {e} , {job_offer}")
        return None
    


    
    
def convert_to_float(value: str) -> float:
    """
    Converts a string with comma as decimal separator into a float.
    Example: '1800,00' -> 1800.0
    """
    try:
        # Replace comma with a dot and convert to float
        return float(value.replace(',', '.'))
    except ValueError:
        raise ValueError(f"Unable to convert '{value}' to float.")
        
def add_space_around_numbers(input_str):
    """
    Adds a space:
    1. After numbers (integers and floats) if not already followed by a space or digit.
    2. Before numbers if they are immediately preceded by a letter.
    Does not break floating-point numbers (e.g., 1800.00).
    
    Args:
        input_str (str): The input string to process.
        
    Returns:
        str: The processed string with spaces added around numbers where necessary.
    """
    # Match whole numbers followed by non-space non-digit characters
    pattern_after = r'(\d+)([^\s\d\.])'
    # Match letters immediately followed by numbers, ensuring no space is already present
    pattern_before = r'([a-zA-Z])(\d+(\.\d+)?)'
    
    # Add space after numbers (but not floats)
    result = re.sub(pattern_after, r'\1 \2', input_str)
    # Add space before numbers if needed
    result = re.sub(pattern_before, r'\1 \2', result)
    
    return result



def convert_salary_to_monthly(salary_str, job_offer : dict): 
    """
    Convertit une chaîne de caractères représentant un salaire en un montant mensuel.
    
    Args:
        salary_str (str): Chaîne de caractères représentant le salaire (ex: "Mensuel de 2000.0 Euros sur 12.0 mois").
        
    Returns:
        dict: {'min_salary': float, 'max_salary': float} en Euros par mois.
    """
    # retrieve hours_per_week to calculate monthly salary from an hourly rate
    hpw, work_condition = hours_per_week(job_offer.get("dureeTravailLibelle"))
    if not hpw:
        hpw=35
        
    
    
    # Normalize the input (replace non-breaking space and remove extra spaces)
    salary_str = salary_str.replace('\xa0', ' ').replace(',', '.').replace('€','').strip()
    salary_str = re.sub(r'\s+', ' ', salary_str)  # Ensure consistent spacing
    
    logging.debug(f"Normalized salary string: {repr(salary_str)}")
    
    # Split the string into tokens based on spaces
    tokens = salary_str.split()
    logging.debug(f"Tokens: {tokens}")
    pattern = r'\b\d+(?:\.\d+)?\b'
    match = re.search(pattern, salary_str)
    if not match:
        logging.error(f"Invalid salary format, salary not found: {salary_str}")
        return {'min_salary': 0, 'max_salary': 0}
    
            
    # Check if "de" exists and extract min amount
    if "de" in salary_str or "De" in salary_str :
        salary_str= salary_str.replace("De","de")
        tokens = salary_str.split()
        logging.debug(f"{tokens}")
        min_amount_index = tokens.index("de") + 1 
        min_amount = round(float(tokens[min_amount_index]),1)
        max_amount = min_amount
    
        
    else:
        logging.error(f"Invalid salary format, 'de' not found: {salary_str}")
        return {'min_salary': 0, 'max_salary': 0}
    
    
    # Check for the presence of "à" and extract max_amount if it exists
    if "à" in tokens:
        try:
            max_amount_index = tokens.index("à") + 1
            max_amount = round(float(tokens[max_amount_index]),1)
        except ValueError:
            logging.exception(f"Error extracting max amount after 'à' in: {salary_str}")
            return {'min_salary': 0, 'max_salary': 0}
    
    # Extract the period (months)
    if "sur" in tokens:
        period_index = tokens.index("sur") + 1
        period_in_months = float(tokens[period_index])
        if period_in_months == 0.0:
            period_in_months = 12.0
    else:
        period_in_months = 12.0
        
    
    # Convert amounts to monthly salaries
    if salary_str.startswith("de") or salary_str.startswith("Autre")  or salary_str.startswith("Mensuel") or salary_str.startswith("Annuel") or salary_str.startswith("Horaire"):
        
        if max_amount > 15000:
            min_monthly = min_amount / period_in_months
            max_monthly = max_amount / period_in_months
        elif max_amount < 70:
            min_monthly = min_amount * hpw * WEEKS_PER_MONTH * period_in_months/12
            max_monthly = max_amount * hpw * WEEKS_PER_MONTH * period_in_months/12
        
        else:
            min_monthly = min_amount * period_in_months /12
            max_monthly = max_amount * period_in_months /12
    
    else:
        logging.error(f"Unknown salary type: {salary_str}")
        return {'min_salary': 0, 'max_salary': 0}
    
    
    logging.debug(f"Parsed salary details: Min={min_monthly}, Max={max_monthly}, Period={period_in_months}")
    
    return {
        'min_salary': round(min_monthly, 2),
        'max_salary': round(max_monthly, 2)
    }
def replace_space_between_numbers(input_str):
    """
    Replaces a space between two numbers with a dot (.)
    
    Args:
        input_str (str): The input string to process.
        
    Returns:
        str: The processed string with spaces between numbers replaced by dots.
    """
    # Regular expression to match a digit, followed by a space, followed by another digit
    pattern = r'(\d)\s+(\d)'
    # Replace the space with a dot
    return re.sub(pattern, r'\1\2', input_str)
  
def add_space_before_slash(input_str):
    """
    Adds a space between a number (integer or float) and a '/' if not already present.
    
    Args:
        input_str (str): The input string to process.
        
    Returns:
        str: The processed string with spaces added before '/' where necessary.
    """
    # Regular expression to match a number followed by a '/'
    pattern = r'(\d+(\.\d+)?)/'
    # Replace with the number followed by a space and the '/'
    return re.sub(pattern, r'\1 /', input_str)

  
def insert_salary(cursor, connection, job_id, job_offer: dict):
    """Insert a record into the `salary` table."""
    hpw, work_condition = hours_per_week(job_offer.get("dureeTravailLibelle"))
    if not hpw:
        hpw=35
    
    
    
    def format_salaries(salary_str):
            tokens = salary_str.split()
            try:
                if "à" in salary_str or "-" or " et " in salary_str:
                    if salary_str.startswith("-"):
                        salary_str=salary_str[1:]
                        
                    salary_str = salary_str.replace("-","à").replace("et","à")
                    tokens = salary_str.split()
                    index1= tokens.index("à") -1
                    index2= tokens.index("à") + 1
                    logging.debug(f"{tokens}")
                    min_monthly_salary = float(tokens[index1])
                    max_monthly_salary = float(tokens[index2])
                    if max_monthly_salary < 700:
                        min_monthly_salary *= hpw * WEEKS_PER_MONTH
                        max_monthly_salary *= hpw * WEEKS_PER_MONTH
                        salary_description = salary_str
                    elif max_monthly_salary > 15000:
                        min_monthly_salary /=  12
                        max_monthly_salary /=  12
                        salary_description = salary_str
                    else:
                        min_monthly_salary = min_monthly_salary
                        max_monthly_salary = max_monthly_salary
                        salary_description = salary_str
                    return min_monthly_salary, max_monthly_salary, salary_description
            except Error as e:
                logging.exception(f"conversion error : {salary_str}")
            
    try:
        # Extract salary information from the job_offer
        salary_str = job_offer.get("salaire", {}).get("libelle")
        logging.debug(f"Extracted salary_str from libelle: {salary_str}")
        if not salary_str:
            try:
                salary_str = job_offer.get("salaire", {}).get("commentaire")
                
                if not salary_str:
                    min_monthly_salary = 0
                    max_monthly_salary = 0
                    salary_description = "Invalid salary format (no string)"
                    logging.warning(f"no salary found for job_id {job_id}")
                    
                    
                    
                logging.debug(f"Extracted salary_str from commentaire: {salary_str}")
                salary_str = re.sub(r'\s+', ' ', salary_str)  # Ensure consistent spacing
                salary_str = (
                salary_str.replace("'","")
                .replace("K", "k")
                .replace(" k","k")
                .replace("k","000")
                .replace(",",".")
                .replace(" 000","000")
                .replace("?","")
                .replace("€","")
                .replace("Euros","")
                .replace("E","")
                .replace("euro","")
                .replace("brut","")
                .replace("BRUT","")
                .replace("Brut","")
                .replace("(","")
                .replace(")","")
                )
                salary_str = add_space_around_numbers(salary_str)
                salary_str=replace_space_between_numbers(salary_str)
                logging.debug(f"Cleaned string : {salary_str}")
                pattern = r'\b\d+(?:[.]\d+)?\b' # capture any float or int
                match = re.search(pattern, salary_str)
                pattern2 = r'\d+(\.\d+)?\s+(à|-|et)\s+\d+(\.\d+)?' #capture strings  like "18 à 25", "18,5 - 25,4" "18 et 25",
                                                                                               
                                                                                                 
                                                                                              
                match2 = re.search(pattern2, salary_str)
                if match2:
                    
                        logging.info(f"match 2 reached")
                        logging.debug(f"salary_str : {salary_str}")
                        pattern3= r'\d+\.\d+\.\d+'
                        match3 = re.search(pattern3, salary_str)
                        if match3:
                            def modify_match(match):
                                matched_str = match.group()  # Get the full match
                                # Retain only the first two groups of digits
                                return '.'.join(matched_str.split('.')[:2])

                            # Replace the matched pattern with the modified result
                            salary_str = re.sub(pattern3, modify_match, salary_str)
                        
                        #salary_str=add_space_before_slash(salary_str)
                        salary_str = add_space_around_numbers(salary_str)
                        if "%" in salary_str:
                            min_monthly_salary = 0
                            max_monthly_salary = 0
                            salary_description = salary_str
                        elif "à" in salary_str or "-" in salary_str or " et " in salary_str:
                            logging.debug(f"Match 2, à/-et found")
                            min_monthly_salary, max_monthly_salary, salary_description = format_salaries(salary_str)  
                        else:
                            logging.debug(f"Match 2, exit")
                            min_monthly_salary = 0
                            max_monthly_salary = 0
                            salary_description = salary_str
                            
                            
                elif match:
                    min_monthly_salary = match.group()
                    max_monthly_salary = None
                    if any(keyword in salary_str for keyword in ["%", "CN", "CCN", "CC", "convention", "Convention", "RTT", "Cnn", "13 mois", "Coef", "coef", "grille", "Grille", " 66", "ségur", "Ségur"]) or ( "13 " in salary_str and "mois" in salary_str):
                        logging.warning("Found %/convention/13e mois")
                        min_monthly_salary = 0
                        max_monthly_salary = 0
                        salary_description = salary_str
                    if min_monthly_salary.endswith('.'):
                            logging.info(f"salary ends with '.'")
                            min_monthly_salary = min_monthly_salary[:-1]
                    min_monthly_salary = round(float(min_monthly_salary),1)
                    salary_description = salary_str
                    
                    logging.debug(f"salary found : {min_monthly_salary}")
                          
                    if min_monthly_salary > 9999:
                    
                            min_monthly_salary /= 12
                    elif min_monthly_salary < 70:
                            min_monthly_salary *= hpw * WEEKS_PER_MONTH
                    
                else:
                    logging.warning(f"No salary found")
                    min_monthly_salary = 0
                    max_monthly_salary = 0
                    salary_description = salary_str
            except ValueError:
                logging.error(f"Invalid salary format: {min_monthly_salary}")
                min_monthly_salary = 0
                max_monthly_salary = 0
                salary_description = 'invalid format'
            except Exception as e:
                logging.exception(f"Unexpected error during salary conversion: {e}")
                min_monthly_salary = 0
                max_monthly_salary = 0
                salary_description = 'conversion errror'
                
                
                   
                    
        else:
            # Convert the salary string to monthly min and max values
            salary_str = salary_str.replace("Euros","")
            salary_data = convert_salary_to_monthly(salary_str, job_offer)
            
            if not salary_data:
                min_monthly_salary = 0.0
                max_monthly_salary = 0.0
                salary_description = "Invalid salary format"
                logging.debug(f" salary_data failure")
            else:
                # Extract min and max salary from the converted data
                min_monthly_salary = salary_data.get('min_salary')
                max_monthly_salary = salary_data.get('max_salary')
                salary_description = salary_str
                
        
            
            

        # Insert data into the salary table
        insert_query = """
        INSERT IGNORE INTO salary (job_id, min_monthly_salary, max_monthly_salary, salary_description, max_monthly_predicted)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (job_id, min_monthly_salary, max_monthly_salary, salary_description, max_monthly_salary))
        logging.debug(f"Executed query: {cursor._executed}")
        
        
        # Return the ID of the inserted or existing record
        if cursor.lastrowid:
            logging.info(f"Inserted into `salary`: {cursor.lastrowid}")
            return cursor.lastrowid
        else:
            cursor.execute("SELECT salary_id FROM salary WHERE min_monthly_salary = %s AND max_monthly_salary = %s AND salary_description = %s AND job_id = %s", 
                           (min_monthly_salary, max_monthly_salary, salary_description, job_id))
            logging.debug(f"Executed query: {cursor._executed}")
            result = cursor.fetchone()
            logging.info(f"Duplicate ignored in table `salary`: {result}")
            return result[0] if result else None
            
    except Error as e:
        logging.exception(f"Error inserting into salary: {e}")
        min_monthly_salary = 0.0
        max_monthly_salary = 0.0
        salary_description = "Invalid salary format"
        
def hours_per_week(length_work_label):
            if length_work_label is None or length_work_label == "":
                return None, None
           
                
            elif "\n" in length_work_label and "H" in length_work_label :
                parts = length_work_label.split("\n")
                hpw = parts[0].strip()
                work_condition = parts[1].strip()
                
            elif "temps partiel -" in length_work_label:
                tokens = length_work_label.split()
                index = tokens.index("-") +1
                hpw = tokens[index]
                work_condition= "Temps partiel"
            elif  "\n" not in length_work_label and "H" in length_work_label:
                if "Travail" in length_work_label:
                    parts = length_work_label.split()
                    hpw=parts[0].strip()
                    work_condition= parts[1].strip()
                else:
                    hpw = length_work_label
                    work_condition = None
            elif "temps partiel" in length_work_label:
                hpw = "24"
                work_condition = "Temps partiel"
            elif "H Autre" in length_work_label:
                tokens = length_work_label.split()
                index = tokens.index("Autre") -1
                hpw = tokens[index]
                work_condition= "Autre"
            else: 
                hpw= 0
                work_condition = length_work_label
                
                
            if hpw:
                hpw = hpw.replace("H", ".00").replace(".00",".").replace(".30", ".5").replace(".15",".25").replace(' ','').replace('.Autre','')
                try:
                    hpw = float(hpw)  # Convert to float for duration
                except ValueError:
                # Handle cases where conversion fails (invalid format)
                    logging.exception(f"float conversion failed for work_duration : {hpw} from string {length_work_label}")
                    work_duration = None
                    hpw=0
            
            return hpw, work_condition
            
            
def insert_contract(cursor, connection, job_id, job_offer: dict):
    
    
    
    try:
        
        def insert_contract_type(contract_type):
            try:
                
                insert_query="""
                INSERT IGNORE INTO contract_type (contract_type)
                VALUES (%s)
                """
                cursor.execute(insert_query, (contract_type,))
                logging.debug(f"Executed query: {cursor._executed}")
        
                if cursor.lastrowid:
                    logging.info(f"Inserted into `contract_type`: {cursor.lastrowid}")
                    return cursor.lastrowid
                else:
                    cursor.execute("SELECT contract_type_id FROM contract_type WHERE contract_type = %s", 
                           (contract_type,))
                    logging.debug(f"Executed query: {cursor._executed}")
                    result = cursor.fetchone()
                    logging.info(f"Duplicate ignored in table `contract_type`: {result}")
                    return result[0] if result else None
            except Error as e:
                logging.exception(f"Error inserting into contract_type: {e}")
                return None
        def insert_contract_nature(contract_nature):
            try:
                insert_query="""
                INSERT IGNORE INTO contract_nature (contract_nature)
                VALUES (%s)
                """
                cursor.execute(insert_query, (contract_nature,))
                logging.debug(f"Executed query: {cursor._executed}")
                
        
                if cursor.lastrowid:
                    logging.info(f"Inserted into `contract_type`: {cursor.lastrowid}")
                    return cursor.lastrowid
                else:
                    cursor.execute("SELECT contract_nature_id FROM contract_nature WHERE contract_nature = %s", 
                           (contract_nature,))
                    logging.debug(f"Executed query: {cursor._executed}")
                    result = cursor.fetchone()
                    logging.info(f"Duplicate ignored in table `contract_type`: {result}")
                    return result[0] if result else None 
                    
            except Error as e:
                logging.exception(f"Error inserting into contract_nature: {e}")
                return None    
        
        
        
        
        def extract_contract_label(contract_label):
            
            # Split contract label into label and work duration
            label = contract_label.split("-")[0].strip()
            work_duration = contract_label.split("-")[-1].strip()
    
            # Check for months in work_duration
            contract_match = re.search(r"(\d+)\s*Mois$", work_duration)
            # Check for days (with optional "(s)") in work_duration
            contract_match2 = re.search(r"(\d+)\s*(Jour(?:\(s\)))?", work_duration)
    
            # If work duration is in months
            if contract_match:
                work_duration = int(contract_match.group(1))  # Extract the number of months
                return label, work_duration
    
            # If work duration is in days (and optional "Jour(s)" is present)
            elif contract_match2:
                work_duration = int(contract_match2.group(1))  # Extract the number of days
                work_duration = days_to_months(work_duration)  # Convert days to months
                return label, work_duration
    
            # Default case when no valid work duration is found
            else:
                label = "CDI"
                return label, None
                
        def is_partial(partial_time):
            
                 
            #convert "dureeTravailLibelleConverti" to a boolean
            if partial_time and "Temps partiel" in partial_time :
                return True
            else:
                return False
                
        
        
            
            
        insert_query="""
        INSERT IGNORE INTO job_contract(job_id, contract_type_id,
        contract_nature_id, label, work_duration, hours_per_week, work_condition,
        additional_condition, partial)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s )
        """


    
        
        hpw, work_condition = hours_per_week(job_offer.get("dureeTravailLibelle"))
        partial =  is_partial(job_offer.get("dureeTravailLibelleConverti"))     
        contract_label= job_offer.get("typeContratLibelle")
        label, work_duration = extract_contract_label(contract_label)
        contract_nature_id=insert_contract_nature(job_offer.get("natureContrat"))
        contract_type_id=insert_contract_type(job_offer.get("typeContrat"))
        cursor.execute(insert_query, (job_id, contract_type_id, contract_nature_id, label, work_duration, hpw, work_condition,
        job_offer.get("experienceCommentaire"), partial))
        logging.debug(f"Executed query: {cursor._executed}")
        logging.info(f"Inserted into `job_contract`: {cursor.lastrowid}")
    
    except Error as e:
        logging.exception(f"Error inserting into job_contract: {e}")
        
        
        

        
def insert_benefits(cursor, connection, salary_id, job_offer: dict):
   
    """ insert a record inside the benefits tables"""
    
    complements= job_offer.get("salaire", {})
    try:
        # Extract complements
        complement1 = complements.get("complement1", None)
        complement2 = complements.get("complement2", None)
        
        # Prepare the insert query for insert_benefits
        insert_query = """
        INSERT IGNORE INTO benefits (label)
        VALUES (%s)
        """
        insert_query2= """
        INSERT IGNORE INTO salary_benefits (benefits_id, salary_id)
        VALUES (%s, %s)
        """
        
        
        # Insert complement1 if it exists
        def insert_and_link_benefit(benefit_label, salary_id):
            if benefit_label:
                # Insert the benefit into the `benefits` table
                cursor.execute(insert_query, (benefit_label,))
                logging.debug(f"Executed query: {cursor._executed}")
                 
                # Retrieve the benefit_id of the inserted or existing benefit
                if cursor.lastrowid:
                    benefit_id = cursor.lastrowid
                    logging.info(f"Inserted into `benefits`: {cursor.lastrowid}")
                else:
                    cursor.execute("SELECT benefits_id FROM benefits WHERE label = %s", (benefit_label,))
                    logging.debug(f"Executed query: {cursor._executed}")
                    result = cursor.fetchone()
                    benefit_id = result[0] if result else None
                    logging.info(f"Duplicate ignored in `benefits`: {result}")
                # Link the benefit to the job in the `job_benefit` table
                if benefit_id:
                    cursor.execute(insert_query2, (benefit_id, salary_id))
                    logging.debug(f"Executed query: {cursor._executed}")
                    logging.info(f"Inserted into `salary_benefit`: {cursor.lastrowid}")
                
        
        # Insert and link complement1 if it exists
        insert_and_link_benefit(complement1, salary_id)
        
        # Insert and link complement2 if it exists
        insert_and_link_benefit(complement2, salary_id)
        
        
        
    except Error as e:
        logging.exception(f"Error inserting into benefits: {e}")


        
def insert_salary_benefits(cursor, connection, benefit_id, salary_id):
    
    """
    Insert a record into the `salary_benefits` table.
    If a record with the same salary_id and salary_benefit_id exists, update the existing record.
    """
    try:
        
        insert_query = """
        INSERT IGNORE INTO salary_benefits (salary_benefits_id, salary_id)
        VALUES (%s, %s)
        """
        cursor.execute(insert_query, (benefit_id, salary_id))
        logging.debug(f"Executed query: {cursor._executed}")
        
        logging.info(f"Inserted salary_benefit for salary_id: {salary_id} and benefit_id: {benefit_id}") 
    except Error as e:
        logging.exception(f"Error inserting salary benefit: {e}")

def insert_companies(cursor, connection, job_offer: dict ):
    """Insert a record into the `companies` table."""
    
    try:
        
        insert_query = """
        INSERT IGNORE INTO companies ( name, is_adapted)
        VALUES ( %s, %s)
        """
        cursor.execute(insert_query, (job_offer.get("entreprise", {}).get("nom",'null'), job_offer.get("entreprise", {}).get("entrepriseAdaptee",0))
        )
        logging.debug(f"Executed query: {cursor._executed}")
        if job_offer.get("entreprise", {}).get("nom",'null') == 'null':
            return None
        
        if cursor.lastrowid:
            company_id = cursor.lastrowid
            logging.info(f"Inserted into `companies`: {cursor.lastrowid}")
            return company_id
        else:
                cursor.execute("SELECT company_id FROM companies WHERE name = %s", (job_offer.get("entreprise", {}).get("nom"),))
                logging.debug(f"Executed query: {cursor._executed}")
                result = cursor.fetchone()
                company_id = result[0] if result else None
                logging.info(f"Duplicate ignored in `companies`: {result}")
                return company_id
    except Error as e:
        logging.exception(f"Error inserting into companies: {e}")
        
def insert_contact(cursor, connection, job_offer: dict ):
    """Insert a record into the `contact` table."""
    
    coordonnees1=job_offer.get("contact", {}).get("coordonnees1", "")
    coordonnees2=job_offer.get("contact", {}).get("coordonnees2", "")
    coordonnees3=job_offer.get("contact", {}).get("coordonnees3", "")
    if coordonnees1 == coordonnees2 == coordonnees3:
        coordonnees2 = ''
        coordonnees3 = ''
        address=''
    elif coordonnees1 == coordonnees2:
        coordonnees2 = ''
    elif coordonnees2 == coordonnees3:
        coordonnees3 = ''
    address = " ".join(filter(None, [coordonnees1, coordonnees2, coordonnees3])).strip()
    try:
        
        insert_query = """
        INSERT IGNORE INTO contact (name, email, address)
        VALUES (%s, %s, %s)
        
        """
        if not job_offer.get("contact", {}).get("nom")  and not job_offer.get("contact", {}).get("courriel") and  not address.strip():
            return None
        cursor.execute(insert_query, (job_offer.get("contact", {}).get("nom"), job_offer.get("contact", {}).get("courriel"), address))
        logging.debug(f"Executed query: {cursor._executed}")
        logging.info(f"Inserted into `contact`: {cursor.lastrowid}")
        if cursor.lastrowid:
            contact_id = cursor.lastrowid
            logging.info(f"Inserted into `contact`: {cursor.lastrowid}")
            return contact_id
        else:
                cursor.execute("SELECT contact_id FROM contact WHERE  name = %s AND email = %s AND address = %s", (job_offer.get("contact", {}).get("nom"), job_offer.get("contact", {}).get("courriel"), address ))
                logging.debug(f"Executed query: {cursor._executed}")
                result = cursor.fetchone()
                contact_id = result[0] if result else 0
                logging.info(f"Duplicate ignored in `contact`: {result}")
                return  contact_id
    except Error as e:
        logging.exception(f"Error inserting into contact: {e}")

def insert_competencies(cursor, connection, job_offer: dict):
    """Insert a record into the `competencies` table."""
   
    
    try:
        
        insert_query = """
        INSERT IGNORE INTO competencies (competency_code, label)
        VALUES (%s, %s)

        
        """
        
        
        competencies = job_offer.get("competences", [])
        for competence in competencies:
                cursor.execute(insert_query, (
                competence.get("code"),
                competence.get("libelle")
                
            ))
                logging.debug(f"Executed query: {cursor._executed}")    
        
        
        logging.info(f"Inserted into `competencies`: {cursor.lastrowid}")
        
    except Error as e:
        logging.exception(f"Error inserting into competencies: {e}")
        
def insert_job_competency(cursor, connection, job_id, job_offer: dict):
    """Insert a record into the `job_competencies` table."""
   
    try:
        
        insert_query = """
        INSERT IGNORE INTO job_competency (competency_code, job_id, required)
        VALUES (%s, %s, %s)
        """
        competencies = job_offer.get("competences", [])
        for competence in competencies:
                cursor.execute(insert_query, (
                competence.get("code"),
                job_id,
                competence.get("exigence")))
                logging.debug(f"Executed query: {cursor._executed}")
                 
        
        
        logging.info(f"Inserted into `job_competencies`: {cursor.lastrowid}")
    except Error as e:
        logging.exception(f"Error inserting into job_competencies: {e}")   
def insert_driver_license(cursor, connection, job_offer: dict):
    
    try:
        
       libelle = job_offer.get("permis", [{}])[0].get("libelle")
       if libelle:
            insert_query = """
            INSERT IGNORE INTO driver_license (label)
            VALUES (%s)
            """
            cursor.execute(insert_query, (libelle,))
            logging.debug(f"Executed query: {cursor._executed}")
            
       if cursor.lastrowid:
            logging.info(f"Inserted into `driver_license`: {cursor.lastrowid}")
            return cursor.lastrowid
       else:
            cursor.execute("SELECT driver_license_id FROM driver_license WHERE label = %s", (libelle,))
            logging.debug(f"Executed query: {cursor._executed}")
            result = cursor.fetchone()
            logging.info(f"Duplicate found in `driver_license`: {result}")
            return result[0] if result else None
            
    except Error as e:
        logging.exception(f"Error inserting into driver_license: {e}")
        
def insert_job_driver_license(cursor, connection, job_id, driver_license_id, job_offer: dict ):
    
    try:
        req= job_offer.get("permis", [{}])[0].get("exigence")
        if req:
            insert_query= """
            INSERT IGNORE INTO job_driver_license(job_id, driver_license_id, requirement )
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (job_id, driver_license_id, req))
            logging.debug(f"Executed query: {cursor._executed}")
            logging.info(f"Inserted into `job_driver_license`:driver_licence_id: {driver_license_id} job_id {job_id}")
    except Error as e:
        logging.exception(f"Error inserting into job_driver_license: {e}")
        
def insert_job_node(cursor, connection, job_offer: dict, naf_label: dict):
     """Insert a record into the `job_node` table and its children naf, rome, actuvity sector & qualification."""
     
     def get_naf_libelle(code):
        return naf_label.get(code, None)
     try:
        
       
        
        insert_query_naf= """
        INSERT IGNORE INTO naf (naf_code, label)
        VALUES (%s, %s)
        """
        
        insert_query_rome= """
        INSERT IGNORE INTO rome (rome_code, label)
        VALUES (%s, %s)
        """
        
        insert_query_activity= """
        INSERT IGNORE INTO activity_sector (activity_sector_code, label)
        VALUES (%s, %s)
        """
        
        insert_query_qualification= """
        INSERT IGNORE INTO qualification (qualification_code, label)
        VALUES (%s, %s)
        """
       
        cursor.execute(insert_query_rome, (job_offer.get("romeCode"),job_offer.get("romeLibelle")))
        logging.info(f"Inserted into `rome`: {job_offer.get("romeCode")}")
        logging.debug(f"Executed query: {cursor._executed}")
        cursor.execute(insert_query_naf, (job_offer.get("codeNAF"),get_naf_libelle(job_offer.get("codeNAF"))))
        logging.info(f"Inserted into `naf`: {job_offer.get("codeNAF")}")
        logging.debug(f"Executed query: {cursor._executed}")
        cursor.execute(insert_query_activity, (job_offer.get("secteurActivite"),job_offer.get("secteurActiviteLibelle")))
        logging.info(f"Inserted into `sector_activity`: {job_offer.get("secteurActivite")}")
        logging.debug(f"Executed query: {cursor._executed}")
        cursor.execute(insert_query_qualification, (job_offer.get("qualificationCode"),job_offer.get("qualificationLibelle")))
        logging.info(f"Inserted into `qualification`: {job_offer.get("qualificationCode")}")
        logging.debug(f"Executed query: {cursor._executed}")
        connection.commit()
     except Error as e:
        logging.exception(f"Error inserting into job_node: {e}")
        connection.rollback()
        
def insert_formation(cursor, connection, job_id, job_offer: dict ):
    
    
    
    try:
        formations= job_offer.get("formations", [])
        
            
        def insert_and_link_formations(formation_level, formation_label, job_id, requirement):
            formation_id = None
            nonlocal insert_query, insert_query2
            if formation_label:
                try:
                    # Insert the formation into the `formation` table
                    cursor.execute(insert_query, (formation_level, formation_label))
                    logging.debug(f"Executed query: {cursor._executed}")
                    
                    # Retrieve the formation_id of the inserted or existing formation
                    if cursor.lastrowid:
                        logging.info(f"Inserted into `formation`: {cursor.lastrowid}")
                        formation_id = cursor.lastrowid
                    else:
                        cursor.execute("SELECT formation_id FROM formation WHERE label = %s AND level = %s", (formation_label, formation_level))
                        logging.debug(f"Executed query: {cursor._executed}")
                        result = cursor.fetchone()
                        formation_id = result[0] if result else None
                        logging.info(f"Duplicate found in `formation`: {result}")
                except Error as e:
                    logging.exception(f"Error inserting into formaiton: {e}")
                # Link the formation to the job in the `job_formation` table
                if formation_id:
                    try:
                        cursor.execute(insert_query2, (job_id, formation_id, requirement))
                        logging.debug(f"Executed query: {cursor._executed}")
                        logging.info(f"Inserted into `job_formation`: {cursor.lastrowid}")
                    except Error as e:
                        logging.exception(f"Error inserting into job_formation: {e}")
               
    
        
        insert_query ="""
        INSERT IGNORE INTO formation (level, label)
        VALUES (%s, %s)
        """
        
        insert_query2="""
        INSERT IGNORE INTO job_formation (job_id, formation_id, requirement)
        VALUES (%s, %s, %s)
        """
        for formation in formations:
            insert_and_link_formations(formation.get("niveauLibelle"),
                                    formation.get("domaineLibelle"),
                                    job_id, formation.get("exigence"))
            logging.debug(f"Executed query: {cursor._executed}")
        
        
      
        
    except Error as e:
        logging.exception(f"Error inserting into job_formation: {e}")
        
def insert_professional_qualities(cursor, connection, job_id, job_offer: dict ):
    
    qualities= job_offer.get("qualitesProfessionnelles", [])
    def insert_and_link_qualities( quality_label,quality_desc, job_id):
            if quality_label:
                # Insert the quality into the `professional_quality` table
                cursor.execute(insert_query, (quality_label, quality_desc))
                logging.debug(f"Executed query: {cursor._executed}")
                
                # Retrieve the formation_id of the inserted or existing formation
                if cursor.lastrowid:
                    logging.info(f"Inserted into `professional_quality`: {cursor.lastrowid}")
                    professional_quality_id = cursor.lastrowid
                else:
                    cursor.execute("SELECT professional_quality_id FROM professional_qualities WHERE label = %s AND description = %s", (quality_label, quality_desc))
                    logging.debug(f"Executed query: job_id {job_id}")
                    result = cursor.fetchone()
                    professional_quality_id = result[0] if result else None
                    logging.info(f"Duplicate found`job_formation`: {result}")
                # Link the formation to the job in the `job_professional_qualities` table
                if  professional_quality_id:
                    cursor.execute(insert_query2, (professional_quality_id, job_id))
                    logging.debug(f"Executed query: {cursor._executed}")
                    logging.info(f"Inserted into `job_professional_qualities`: job_id {job_id}, job_professional_quality_id {professional_quality_id}")
                
    try:
        
        insert_query ="""
        INSERT IGNORE INTO professional_qualities(label, description)
        VALUES (%s, %s)
        """
        
        insert_query2="""
        INSERT IGNORE INTO job_professional_qualities(professional_quality_id, job_id)
        VALUES (%s, %s)
        
        """
        for quality in qualities:
            insert_and_link_qualities(quality.get("libelle"),
                                    quality.get("description"),
                                    job_id)
            logging.debug(f"Executed query: {cursor._executed}")
        
        
        
        
    except Error as e:
        logging.exception(f"Error inserting into professional_qualities: {e}")

def insert_languages(cursor, connection, job_id, job_offer: dict):
    
    languages= job_offer.get("langues", [])
    def insert_and_link_languages( label, job_id, requirement):
            if label:
                # Insert the quality into the `languages` table
                cursor.execute(insert_query, (label,))
                logging.debug(f"Executed query: {cursor._executed}")
                
                # Retrieve the language_id of the inserted or existing formation
                if cursor.lastrowid:
                    logging.info(f"Inserted into `language`: {cursor.lastrowid}")
                    language_id = cursor.lastrowid
                else:
                    cursor.execute("SELECT language_id FROM language WHERE label = %s ", (label,))
                    logging.debug(f"Executed query: {cursor._executed}")
                    result = cursor.fetchone()
                    language_id = result[0] if result else None
                    logging.info(f"Duplicate found in `languages`: {result}")
                # Link the language to the job in the `job_languages` table
                if  language_id:
                    cursor.execute(insert_query2, (job_id, language_id, requirement))
                    logging.debug(f"Executed query: {cursor._executed}")
                    logging.info(f"Inserted into `job_language`: {cursor.lastrowid}")
                
    try:
        
        insert_query ="""
        INSERT IGNORE INTO language(label)
        VALUES (%s)
        """
        
        insert_query2="""
        INSERT IGNORE INTO job_language( job_id, language_id, requirement)
        VALUES (%s, %s, %s)
        
        """
        for language in languages:
            insert_and_link_languages(language.get("libelle"),job_id,language.get("exigence"))
        
        
        
        
    except Error as e:
        logging.exception(f"Error inserting into languages: {e}")
    
    
def insert_moving(cursor, connection, job_offer: dict):
    
    try:
      
        insert_query="""
        INSERT IGNORE INTO moving( moving_code, label)
        VALUES (%s, %s)
        
        """
        cursor.execute(insert_query, (job_offer.get("deplacementCode",1),job_offer.get("deplacementLibelle","Jamais")))
        logging.debug(f"Executed query: {cursor._executed}")
        logging.info(f"Inserted into `moving`: {cursor.lastrowid}")
       
        
    except Error as e:
        logging.exception(f"Error inserting into moving: {e}")
        
def insert_cities(cursor, connection, job_offer: dict):
    
    travail=job_offer.get("lieuTravail", {})
    
    def process_location(location_string):
        """
        Processes the location string to extract the city and arrondissement (if present).
        Returns:
        - city: The name of the city.
        """
        # Extract the part after the hyphen
        location_part = location_string.split('-')[-1].strip()

        
            
        return location_part
        
        
        
    
        
    try:

        insert_query="""
        INSERT IGNORE INTO cities( insee_code, name, latitude, longitude)
        VALUES (%s, %s, %s, %s)
        
        """
        city = process_location(travail.get("libelle"))
        
        cursor.execute(insert_query, (travail.get("commune","75056"), city, travail.get("latitude"), 
        travail.get("longitude")))
        logging.debug(f"Executed query: {cursor._executed}")
        
        
        logging.info(f"Inserted into `cities`: {city}")
       
    except Error as e:
         logging.exception(f"Error inserting into cities: {e}")
        
def insert_requirements(cursor, connection):
    
    insert_query="""
    INSERT IGNORE INTO requirements (requirements, label)
    VALUES("E", "Exige"),("S", "Souhaite"),("D", "Debutants acceptes")
    """
    
    cursor.execute(insert_query)
    logging.debug(f"Executed query: {cursor._executed}")
    logging.info(f"Inserted into `requirements`: ")

    
def fetch_all_job_offers(department_code, rome_code, token_type, token):
    all_job_offers = []
    first_index = 0
    last_index = 149
    page_size = 150

    range_param = f"{first_index}-{last_index}"
    headers = {"Accept": "application/json",
        "Authorization": f"{token_type} {token}"}
   
    

    while True:
        # Make the request with the current range
        response = requests.get(f"https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search?codeROME={rome_code}&departement={department_code}&range={range_param}",
        headers=headers)
        timeout=30
        
        if response.status_code in [ 200, 206 ]:
            data = response.json()
            job_offers = data.get("resultats", [])
            if not job_offers:
                break  # Exit the loop if no more job offers are found

            all_job_offers.extend(job_offers)

            first_index += page_size
            last_index += page_size
            range_param = f"{first_index}-{last_index}"

             
            if first_index > 3000:
                 break
        else:
            logging.warning(f"Warning {response.status_code}: {response.text}")
            break
    
    return all_job_offers



def establish_connection():
    
    
    
    logging.basicConfig(
    level=logging.DEBUG,  
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
            logging.FileHandler(log_file_path),  # Log to a file
            logging.StreamHandler()         # Log to the console
    ]
    )
    
   
    
    

    try:
        
        # Use the get_db function as a context manager to get the cursor and connection
        cursor, connection = get_db_persistent()
        if connection.is_connected():
            logging.info("Connected to MySQL database")
            return cursor, connection
    except Error as e:
        logging.exception(f"Error while connecting to MySQL: {e}")
        return None, None
    
def close_connection(cursor, connection):
    """Close the global connection and cursor."""
    
    if cursor:
        cursor.close()  # Close the cursor if it exists
    if connection and connection.is_connected():
        connection.close()
        logging.info("Connection closed")

def load_department_codes(csv_file_path: str) -> list[str]:
    """
    Loads a list of department codes from a CSV file.
    
    :param csv_file_path: Path to the CSV file containing department codes.
    :return: A list of department codes.
    """
    department_codes = []
    
    try:
        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)  # Read the CSV as a dictionary (for better column access)
            
            # Iterate through each row and append the department code to the list
            for row in csv_reader:
                department_codes.append(row['Department_Code'])  
        
        return department_codes
    except FileNotFoundError:
        logging.exception(f"File not found: {csv_file_path}")
        raise
    except KeyError:
        logging.exception("Error: CSV file does not contain 'department_code' column.")
        raise
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        raise
        

def load_data_to_db(cursor, connection, OUTPUT_DIR, csv_file_path):
    """
    Fetches job offers for each department code and inserts them into the database.
    """
    try:
        # Step 1: Fetch credentials and access token
        credentials = get_credentials(OUTPUT_DIR)
        client_id = credentials["clientID"]
        client_secret = credentials["key"]

        token, token_type = get_access_token(client_id, client_secret)
        if token is None:
            logging.error("Failed to get access token")
            return
        

        # Step 2: Read department codes from CSV
        department_codes = load_department_codes(csv_file_path)
        job_count=0
        department_count=0
        logging.info(f"Found {len(department_codes)} department codes to process.")

        naf_labels = get_naf_labels(token_type= token_type, token=token)
        rome_codes=get_rome_codes(token_type= token_type, token=token)

        # Step 3: Iterate over each department code
        for department_code in department_codes:
            department_count+=1
            token, token_type = get_access_token(client_id, client_secret)
            for rome_code in rome_codes:
                job_offers = fetch_all_job_offers(department_code,rome_code, token_type, token)
                
                if not job_offers:
                    logging.warning(f"No job offers found for rome_code {rome_code} in department {department_code}.")
                    
                    continue

                # Insert each job offer into the database
                for job_offer in job_offers:
                    try:
                        # Insert data into the respective tables
                        insert_cities(cursor, connection,job_offer)
                        insert_job_node(cursor, connection,job_offer, naf_labels)
                        contact_id = insert_contact(cursor, connection, job_offer)
                        insert_moving(cursor, connection,job_offer)
                        if not contact_id:
                            logging.warning(f"Failed to insert contact: {job_offer}")
                            contact_id = None
                            
                        company_id = insert_companies(cursor, connection, job_offer)
                        if not company_id:
                            logging.warning(f"Failed to insert company: {job_offer}")
                            company_id = None
                           
                        job_id = insert_job(cursor, connection, job_offer, company_id, contact_id)
                        if not job_id:
                            logging.warning(f"Failed to insert job: {job_offer}")
                            continue
                           
                        insert_contract(cursor, connection, job_id, job_offer)
                        salary_id = insert_salary(cursor, connection, job_id, job_offer)
                        if not salary_id:
                            logging.warning(f"Failed to insert salary: {job_offer}")
                            
                        benefit_id = insert_benefits(cursor, connection, salary_id, job_offer)
                        if not benefit_id:
                            logging.warning(f"Failed to insert benefit: {job_offer}")
                            
                       
                        
                        insert_competencies(cursor, connection, job_offer)
                        insert_job_competency(cursor, connection, job_id, job_offer)
                        
                        driver_license_id = insert_driver_license(cursor, connection, job_offer)
                        if not driver_license_id:
                            logging.warning(f"Failed to insert driver_license: {job_offer}")
                            
                        insert_job_driver_license(cursor, connection, job_id, driver_license_id, job_offer)
                        
                        insert_formation(cursor, connection, job_id, job_offer)
                        insert_professional_qualities(cursor, connection, job_id, job_offer)
                        insert_languages(cursor, connection, job_id, job_offer)
                        
                        job_count+=1
                        
                        
                       
                        connection.commit()
                    
                    except Error as e:
                        logging.exception(f"Error inserting job data for job ID {job_id}: {e}")
                        connection.rollback()
                        continue
                    
    finally:           # Commit all changes after processing all department codes
    
        logging.info(f"Data insertion completed for {department_count}/{len(department_codes)} departments.")
        logging.info(f" {job_count} job offers inserted")
# def Extract_data(OUTPUT_DIR):
    # credentials = get_credentials(OUTPUT_DIR=OUTPUT_DIR)
    # client_id = credentials["clientID"]
    # client_secret = credentials["key"]

    # try : 
        # token, token_type = get_access_token(client_id, client_secret)
        # data, headers = requete_api(token_type= token_type,
                                    # token=token)
        # #print(json.dumps(data, indent=4))
        # #print(headers)
        # file_name=str(time.gmtime().tm_year*10000+time.gmtime().tm_mon*100+time.gmtime().tm_mday)+"_offre_demplois.json"
        # #data["resultats"]
        # print(json.dumps(data["resultats"][0],indent=4))
        # for doc in data["resultats"]:
            # with open(OUTPUT_DIR+"/Elasticsearch/requirements/logstash/data/to_ingest/"+file_name,"+a") as idFile:
                # json.dump(doc,idFile)
                # idFile.write("\n")
                # idFile.close()
    # except Exception as e:
        # print("Erreur :", e) 
        
def fill_missing_salaries(cursor, connection):
    """Fill salaries empty rows with the average salary : 
    phase 1 : avg salary by rome_code by experience, 
    phase 2 : avg salary by rome_code
    phase 3 : avg salary
    phase 4 min_salaries lower than 10 are multiplied by 1000
    """
    
    try:
        cursor.execute("SELECT rome_code from rome")
        rome_codes = cursor.fetchall()
        experience=["D","S","E"]
        for (rome_code,) in rome_codes:
            for exp in experience:
                update_query="""UPDATE salary 
                SET max_monthly_salary = (
                    SELECT round(AVG(a1.max_monthly_salary),2) AS avg_salary 
                        FROM salary a1 JOIN job b1 ON a1.job_id = b1.job_id 
                        WHERE a1.max_monthly_salary IS NOT NULL  
                        AND a1.max_monthly_salary != 0  
                        AND b1.rome_code = %s
                        AND b1.experience_required = %s
                        ), 
                    min_monthly_salary= (
                        SELECT round(AVG(a2.min_monthly_salary),2) AS avg_salary 
                            FROM salary a2 JOIN job b2 ON a2.job_id = b2.job_id 
                                WHERE a2.max_monthly_salary IS NOT NULL  
                                AND a2.max_monthly_salary != 0  
                                AND b2.rome_code = %s
                                AND b2.experience_required = %s
                                ) 
                WHERE (max_monthly_salary = 0 OR max_monthly_salary IS NULL)
                AND (min_monthly_salary = 0 OR min_monthly_salary IS NULL) 
                AND job_id IN ( 
                    SELECT a3.job_id FROM salary a3 JOIN job b3 
                    ON a3.job_id = b3.job_id 
                        WHERE b3.rome_code = %s
                        AND b3.experience_required = %s)"""
               
                cursor.execute(update_query, (rome_code, exp, rome_code, exp, rome_code, exp))
                logging.debug(f"Executed query: {cursor._executed}")
            logging.info(f"empty salaries updated for rome_code {rome_code}")
            connection.commit()
        logging.info(f"update salaries phase 1 complete")
        for (rome_code,) in rome_codes:
            update_query2="""UPDATE salary 
                SET max_monthly_salary = (
                    SELECT round(AVG(a1.max_monthly_salary),2) AS avg_salary 
                        FROM salary a1 JOIN job b1 ON a1.job_id = b1.job_id 
                        WHERE a1.max_monthly_salary IS NOT NULL  
                        AND a1.max_monthly_salary != 0  
                        AND b1.rome_code = %s
                       
                        ), 
                    min_monthly_salary= (
                        SELECT round(AVG(a2.min_monthly_salary),2) AS avg_salary 
                            FROM salary a2 JOIN job b2 ON a2.job_id = b2.job_id 
                                WHERE a2.max_monthly_salary IS NOT NULL  
                                AND a2.max_monthly_salary != 0  
                                AND b2.rome_code = %s
                                
                                ) 
                WHERE (max_monthly_salary = 0 OR max_monthly_salary IS NULL)
                AND (min_monthly_salary = 0 OR min_monthly_salary IS NULL) 
                AND job_id IN ( 
                    SELECT a3.job_id FROM salary a3 JOIN job b3 
                    ON a3.job_id = b3.job_id 
                        WHERE b3.rome_code = %s
                        )"""
            cursor.execute(update_query2, (rome_code, rome_code, rome_code))
            logging.debug(f"Executed query: {cursor._executed}")
        connection.commit()    
        logging.info(f"update salaries phase 2 complete")
        update_query3="""UPDATE salary 
                    SET max_monthly_salary = (
                    SELECT round(AVG(a1.max_monthly_salary),2) AS avg_salary 
                        FROM salary a1 JOIN job b1 ON a1.job_id = b1.job_id 
                        WHERE a1.max_monthly_salary IS NOT NULL  
                        AND a1.max_monthly_salary != 0  
                        
                       
                        ), 
                    min_monthly_salary= (
                        SELECT round(AVG(a2.min_monthly_salary),2) AS avg_salary 
                            FROM salary a2 JOIN job b2 ON a2.job_id = b2.job_id 
                                WHERE a2.max_monthly_salary IS NOT NULL  
                                AND a2.max_monthly_salary != 0  
                                
                                
                                ) 
                WHERE (max_monthly_salary = 0 OR max_monthly_salary IS NULL)
                AND (min_monthly_salary = 0 OR min_monthly_salary IS NULL) 
                AND job_id IN ( 
                    SELECT a3.job_id FROM salary a3 JOIN job b3 
                    ON a3.job_id = b3.job_id 
                        
                        )"""
        cursor.execute(update_query3)
        logging.info(f"update salaries phase 3 complete")
        connection.commit()
        update_query4="""UPDATE salary
                            SET min_monthly_salary = min_monthly_salary *1000 where min_monthly_salary < 10
                            """
        cursor.execute(update_query4)
        logging.debug(f"Executed query: {cursor._executed}")
        logging.info(f"update salaries phase 4 complete")
        connection.commit()
       
        
    except Error as e:
        logging.exception("Error while updating salary for naf_code {naf_code} {e}")
        

if __name__ == "__main__":
    
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_log.txt")
    OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    CSV_FILE_PATH = os.path.join(OUTPUT_DIR, 'french_departments.csv')  # relative path of the csv file
    with open(log_file_path, "w") as log_file:
        # Redirect stdout to the log file
        #original_stdout = sys.stdout
        sys.stdout = log_file
        try:
            cursor, connection = establish_connection()
            insert_requirements(cursor, connection)
            load_data_to_db(cursor, connection,OUTPUT_DIR, CSV_FILE_PATH)
            fill_missing_salaries(cursor, connection)
    
        finally:
            
            logging.info(f"Program completed. Logs are saved in 'output_log.txt'.")
            close_connection(cursor, connection)
            # Restore stdout to its original state
            #sys.stdout = original_stdout

    
    

 