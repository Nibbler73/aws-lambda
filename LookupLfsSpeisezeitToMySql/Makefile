zip: clean package
        cd package && zip -r9 ../function.zip .
        zip -g function.zip *.py

deploy:
        aws lambda update-function-code --function-name LookupLfsSpeisezeitToMySql --zip-file fileb://function.zip

package:
        mkdir -p ./package
        pip3 install --target ./package --system requests beautifulsoup4 mysql-connector-python babel

clean:
        rm -f function.zip
