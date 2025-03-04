# jun24_cde_job-market



1- Le fichier qui permet de requeter FranceTravail API est: FranceTravailDataExtractor.py

    1-a Pour tourner le code il faut au prealable creer une "clientID" et une "Key" en s'inscrivant sur France travail et en ajoutant l'api "offresdemploi"
    1-b Enregistrer le "clientID" et le "Key" dans un fichier "clientCredentials.json". 
    1-C clientCreadentials est dans .gitignore 
	
1.2- Le fichier FranceTravailDataExtractor2.py extrait les données de l'API France Travail et les charge dans une base de données.
		Elle fonctionne de la façon suivante :
		a- L'api limitant les resultats à 3150 par requêtes, pour accéder à toutes les offres le script itère d'abord par départements puis pour chaque code ROME à l'interieur du département
		b- le choix des départements se fait via le fichier csv french_departments.csv ainsi l'intégralité des offres d'emploi en ile de france est paramétrée à l'heure actuelle
		c- Les salaires ayants énormément de formats différents, une série d'opérations est réalisée pour formater tous les salaires en mensuel en tenant compte des heures travaillées en temps partiel et du 13e mois
		d- Pour les salaires manquants les champs sont remplis avec dans un premier temps la moyenne des salaires par code rome par niveau d'experience souhaité,
		puis la moyenne des salaires par code rome et enfin la moyenne des salaires.
		e- le script génère un fichier de log d'une taille de 1,5 Go (dans le gitignore)
		f- le script à l'heure actuelle ne fonctione qu'en local, il reste à ajouter des méthodes pour automatiser le lancement du mysql dockerisé et le chargement de la base dans celui ci
		il vous faudra donc un serveur mysql, le script actuel est configuré pour un client mariadb (port 3307) si vous utilisez le client mysql il faudra changer le port en 3306 dans la méthode establish_connection


2-Pour accéder à la session Postman France_Travail.postman_collection.json il faut installer Postman puis Ctrl+O pour importer le fichier


