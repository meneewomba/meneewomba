import requests
import json
import os
import time

#### Save credentials 
""" OUTPUT_DIR="C:/Users/medsa/Desktop/projet_DE"

credentials={
    "clientID":"$$$ to be filled",
    "key":"$$$$ to be filled"
} """

def saveCredentials(OUTPUT_DIR: str, credentials: dict[str,str]) -> None:
    """
    Enrgistre les accrédiations clients dans un ficher JSON.

    :param OUTPUT_DIR: Répertoire où sera engistré le fichier.
    :param credentials: Dictionnaire contenant les données clientID et key
    """
    with open(os.path.join(OUTPUT_DIR,"clientCredentials.json"),"w") as idFile:
        json.dump(credentials,idFile)
        idFile.close()  

# saveCredentials(OUTPUT_DIR,credentials)

#### 0.get credentials

def get_credentials(OUTPUT_DIR: str) -> dict[str,str]:
    """
    Récupère les accréditations à partir d'un fichier JSON.

    :param OUTPUT_DIR: Répertoire dans lequel se trouve le fichier JSON avec les accrédiations.
    :return: Dictionnaire contenant les accrédiations (clientID et key)
    """

    with open(os.path.join(OUTPUT_DIR,"clientCredentials.json"),"r") as idFile:
        return json.load(idFile)

def get_access_token(client_id: str, client_secret: str) -> tuple[str,str]:
    """
    Création des accès via les accréditations clients.
    
    :return: Tuple contenant le token et token_type."""

    headers={"Content-Type":"application/x-www-form-urlencoded"}
    params={
        "grant_type":"client_credentials",
        "client_id":client_id,
        "client_secret":client_secret,
        "scope":"o2dsoffre api_offresdemploiv2"
    }

    #### 1.generate token

    try:
        req=requests.post(url= "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
                headers= headers,params=params)
        req.raise_for_status()
        token_data = req.json()
        return token_data["access_token"], token_data["token_type"]
    except requests.exceptions.HTTPError as errh: 
        print("HTTP Error") 
        print(errh.args[0]) 

def requete_api(token_type:str, token:str):
    """
    Requête l'API de France Travail.
    """
    headers={
        "Accept": "application/json",
        "Authorization": f"{token_type} {token}"
    }

    try :
        query = requests.get(url="https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
                              headers= headers)
        query.raise_for_status()
        return query.json(), query.headers
    except requests.exceptions.HTTPError as errh:
        print('HTTP Error:', errh)

def Extract_data(OUTPUT_DIR):
    credentials = get_credentials(OUTPUT_DIR=OUTPUT_DIR)
    client_id = credentials["clientID"]
    client_secret = credentials["key"]

    try : 
        token, token_type = get_access_token(client_id, client_secret)
        data, headers = requete_api(token_type= token_type,
                                    token=token)
        #print(json.dumps(data, indent=4))
        #print(headers)
        file_name=str(time.gmtime().tm_year*10000+time.gmtime().tm_mon*100+time.gmtime().tm_mday)+"_offre_demplois.json"
        #data["resultats"]
        print(json.dumps(data["resultats"][0],indent=4))
        for doc in data["resultats"]:
            with open(OUTPUT_DIR+"/Elasticsearch/requirements/logstash/data/to_ingest/"+file_name,"+a") as idFile:
                json.dump(doc,idFile)
                idFile.write("\n")
                idFile.close()
    except Exception as e:
        print("Erreur :", e)

if __name__ == "__main__":
    OUTPUT_DIR = 'C:/Users/medsa/Desktop/projet_DE'
    Extract_data(OUTPUT_DIR)