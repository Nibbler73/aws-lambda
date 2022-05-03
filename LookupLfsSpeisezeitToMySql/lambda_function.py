# coding=utf-8
# pip install requests
# pip install beautifulsoup4
# pip install mysql-connector-python
# pip install babel

import json
import os
import requests
from bs4 import BeautifulSoup

import babel.numbers
import decimal
import mysql.connector


def lambda_handler(event, context):
    session = requests.Session()
    session.cookies['opc-cookies_accepted'] = '1'
    session.cookies['opc-mandant_override'] = '4'
    session.cookies['opc-remember_user'] = os.environ["LfsSpeisezeitKartennummer"]

    login_daten = {
    'action' : 'authenticate',
    'username' : os.environ["LfsSpeisezeitKartennummer"],
    'password' : os.environ["LfsSpeisezeitPw"],
    'rememberMe' : '1',
    'mandantOverride' : '4',
    'service' : 'login'
    }

    #
    # SessionTest token holen
    #
    login_form = session.get(url=os.environ["LfsSpeisezeitBaseUrl"]).content
    soup_login_form = BeautifulSoup(login_form, 'html.parser')
    print(soup_login_form) #
    mandantOverride = soup_login_form.select_one('input[name=mandantOverride]').get('value') #.get_text(strip=True)
    print("mandantOverride: " + mandantOverride) #

    # sessiontest Wert aus antwort in unsere Login-Daten schreiben
    login_daten['mandantOverride'] = mandantOverride

    # Login mit Username+PW+SessionTest
    login = session.post(url= os.environ["LfsSpeisezeitBaseUrl"] + '/api/', data=login_daten)

    if "Die eingegeben Benutzerdaten sind nicht korrekt" in login.text:
            return {
                'statusCode': 404,
                'body': json.dumps('Der Benutzername oder das Passwort ist falsch!' + os.environ["LfsSpeisezeitKartennummer"])
            }

    hackintosh = session.get(url=os.environ["LfsSpeisezeitBaseUrl"] + '/menuplan.php?KID=' + os.environ["LfsSpeisezeitKartennummer"]).content
    soup_hackintosh = BeautifulSoup(hackintosh, 'html.parser')
    print(soup_hackintosh) #

    # vierter_absatz = soup_hackintosh.select_one('div[class="article-layout__content article-content"] p:nth-of-type(4)').get_text(strip=True)
    guthaben_alt = soup_hackintosh.select_one('span#saldoOld').get_text(strip=True)
    guthaben_neu = soup_hackintosh.select_one('span#saldoNew').get_text(strip=True)

    guthaben = decimal.Decimal( guthaben_alt.replace(',', '.').replace(' €', '') )

    kommentar = babel.numbers.format_currency(guthaben, "EUR" )

    # print(guthaben)

    # print( kommentar )

    mydb = mysql.connector.connect(
      host=os.environ["MySqlHost"],
      user=os.environ["MySqlUser"],
      password=os.environ["MySqlPw"],
      database=os.environ["MySqlUser"]
    )

    mycursor = mydb.cursor()

    #sql = "INSERT INTO lfs_speisezeit_guthaben (zeitpunkt, kind_id, guthaben, kommentar) VALUES (NOW(), 1, %s, %s)"
    # INSERT if:
    # 1. guthaben has changed
    # 2. last entry is more than 14 days ago
    sql = "INSERT INTO lfs_speisezeit_guthaben (zeitpunkt, kind_id, guthaben, kommentar) SELECT NOW() as zeitpunkt, 1 as kind_id, %s as new_guthaben, %s as kommentar FROM lfs_speisezeit_guthaben WHERE %s IN (SELECT guthaben FROM lfs_speisezeit_guthaben WHERE kind_id=1 AND zeitpunkt = (SELECT max(zeitpunkt) FROM lfs_speisezeit_guthaben WHERE kind_id=1 HAVING MAX(zeitpunkt) > NOW() - INTERVAL 336 HOUR)) HAVING COUNT(*) = 0"
    val = (guthaben, None, guthaben)
    mycursor.execute(sql, val)

    mydb.commit()
    return {
        'statusCode': 200,
        'body': json.dumps('Aktuelles Guthaben: ' + kommentar)
    }

if __name__ == "__main__":
    event = []
    context = []
    lambda_handler(event, context)
