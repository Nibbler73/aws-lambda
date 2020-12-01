import json
import os
import requests
from bs4 import BeautifulSoup

import babel.numbers
import decimal
import mysql.connector


def lambda_handler(event, context):
    session = requests.Session()

    login_daten = {
    'f_kartennr' : os.environ["LfsSpeisezeitKartennummer"],
    'f_pw' : os.environ["LfsSpeisezeitPw"],
    'sessiontest' : ''
    }

    #
    # SessionTest token holen
    #
    login_form = session.get(url=os.environ["LfsSpeisezeitBaseUrl"] + '/index.php').content
    soup_login_form = BeautifulSoup(login_form, 'html.parser')
    sessiontest = soup_login_form.select_one('input[name=sessiontest]').get('value') #.get_text(strip=True)
    # print("Sessiontest: " + sessiontest)

    # sessiontest Wert aus antwort in unsere Login-Daten schreiben
    login_daten['sessiontest'] = sessiontest

    # Login mit Username+PW+SessionTest
    login = session.post(url= 'https://www.opc-asp.de/speisezeit/index.php?LogIn=true', data=login_daten)

    if "Die eingegeben Benutzerdaten sind nicht korrekt" in login.text:
            return {
                'statusCode': 404,
                'body': json.dumps('Der Benutzername oder das Passwort ist falsch!' + os.environ["LfsSpeisezeitKartennummer"])
            }

    hackintosh = session.get(url=os.environ["LfsSpeisezeitBaseUrl"] + '/menuplan.php?KID=' + os.environ["LfsSpeisezeitKartennummer"] + '&OWN=2').content
    soup_hackintosh = BeautifulSoup(hackintosh, 'html.parser')
    # print(soup_hackintosh)

    # vierter_absatz = soup_hackintosh.select_one('div[class="article-layout__content article-content"] p:nth-of-type(4)').get_text(strip=True)
    guthaben_alt = soup_hackintosh.select_one('span#saldoOld').get_text(strip=True)
    guthaben_neu = soup_hackintosh.select_one('span#saldoNew').get_text(strip=True)

    guthaben = decimal.Decimal( guthaben_alt.replace(',', '.') )

    kommentar = babel.numbers.format_currency(guthaben, "EUR" )

    mydb = mysql.connector.connect(
      host=os.environ["MySqlHost"],
      user=os.environ["MySqlUser"],
      password=os.environ["MySqlPw"],
      database=os.environ["MySqlUser"]
    )

    mycursor = mydb.cursor()

    sql = "INSERT INTO lfs_speisezeit_guthaben (zeitpunkt, guthaben, kommentar) VALUES (NOW(), %s, %s)"
    val = (guthaben, None)
    mycursor.execute(sql, val)

    mydb.commit()
    return {
        'statusCode': 200,
        'body': json.dumps('Aktuelles Guthaben: ' + kommentar)
    }

