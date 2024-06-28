# this is the settings for db module. 

DEBUG = True

VALIDATION_ADDRESS = "https://finance.yahoo.com/quote/"
    
DATABASES = {
    
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "ai1",
        "USER": "aiapp",
        "PASSWORD": "+ibAIV5aqU5S85Rr4lcjb0mF3oItClYKEeN9pjKqcEE=",
        "HOST": "localhost",
        "PORT": "5432",

    }

ASSETDATA_TABLE_NAME = "aiinvest_assetdata"
ASSETLIST_TABLE_NAME = "aiinvest_assetlist"