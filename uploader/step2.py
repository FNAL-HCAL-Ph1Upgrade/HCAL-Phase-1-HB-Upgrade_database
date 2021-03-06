"""
#   step2.py:
#       This script accepts a properly formatted .json file and uploads it
#       to the database. The json file should contain results from Step 2
#       of Test Stand 1.
"""

__author__  = "Andrew Baas"
__credits__ = ["Shaun Hogan", "Mason Dorseth", "John Lawrence",
                "Jordan Potarf", "Joe Pastika", "Andrew Baas"]

__version__     = "2.0"
__maintainer__  = "Caleb Smith"
__email__       = "caleb_smith2@baylor.edu"
__status__      = "Live"

import sys
import os
import json
import django
from shutil import copyfile
from card_stats import set_card_status

sys.path.insert(0, '/home/django/testing_database_hb/card_db')
django.setup()

from django.utils import timezone
from qie_cards.models import Test, Tester, Attempt, Location, QieCard
from card_db.settings import MEDIA_ROOT



def getUID(raw):
    """ Parses the raw UID into a pretty-print format """
    noHex = raw[2:18]
    return noHex

def loadCard(cardData, qie):
    """ Loads in QIE card information """
    qie.uid                 = getUID(cardData["Unique_ID"])
    qie.bridge_major_ver    = cardData["FirmwareMaj"]
    qie.bridge_minor_ver    = cardData["FirmwareMin"]
    qie.bridge_other_ver    = cardData["FirmwareOth"]
    qie.igloo_top_major_ver     = cardData["IglooMajVerT"]
    qie.igloo_top_minor_ver     = cardData["IglooMinVerT"]
    qie.igloo_bot_major_ver     = cardData["IglooMajVerB"]
    qie.igloo_bot_minor_ver     = cardData["IglooMinVerB"]
    return qie
    
def moveJsonFile(qie, fileName):
    """ Moves the json for this upload to permanent storage """
    url = os.path.join("uploads/qieCards/", qie.barcode)
    path = os.path.join(MEDIA_ROOT, url)
    if not os.path.exists(path):
        exit("Database does not contain this card's log folder")
    extension = 1
    while os.path.isfile(os.path.join(path, str(extension) + os.path.basename(fileName))):
        extension += 1
    newPath = os.path.join(path, str(extension) + os.path.basename(fileName))
    copyfile(fileName, newPath)
    return os.path.join(url, str(extension) + os.path.basename(fileName))

# Load the .json into a dictionary
fileName = sys.argv[1]

infile = open(fileName, "r")
cardData = json.load(infile)

# Upload data to the database

barcode = cardData["Barcode"]
uid = cardData["Unique_ID"]

if barcode == "": 
    try:
        qie = QieCard.objects.get(uid=getUID(uid))
    except:
        sys.exit('QIE card with uid "%s" is not in the database' % getUID(uid))
else:
    try:    
        qie = QieCard.objects.get(barcode=barcode)
    except:
        sys.exit('QIE card with barcode "%s" is not in the database' % barcode)

#load time of test
date = cardData["DateRun"] + "-06:00"

#find tester account
try:
    tester = Tester.objects.get(username=cardData["User"])
except:
    sys.exit("Tester %s not valid" % cardData["User"])

card = loadCard(cardData, qie)

path = moveJsonFile(qie, fileName)

test_list = ["Checksum", "SupplyI", "PrgmChk"]

for test in test_list:
    try:
        temp_test = Test.objects.get(abbreviation=test)
    except:
        temp_test = Test(name=test, abbreviation=test)
        print '"%s" test is not in the database' % temp_test
        print 'Creating "%s" test' % temp_test
        temp_test.save()
	
    prev_attempts = list(Attempt.objects.filter(card=qie, test_type=temp_test))
    attempt_num = len(prev_attempts) + 1
    card.save()
    if cardData[test] == "Passed":
        temp_attempt = Attempt(card=card,
	                       plane_loc="default",
	                       test_type=temp_test,
	                       attempt_number=attempt_num,
	                       tester=tester,
	                       date_tested=date,
	                       result=1,
	                       temperature=-999,
	                       humidity=-999,
	                       log_file=path,
	                       hidden_log_file=path,
	                       )

    elif cardData[test] == "N/Aed":
        temp_attempt = Attempt(card=card,
	                       plane_loc="default",
	                       test_type=temp_test,
	                       attempt_number=attempt_num,
	                       tester=tester,
	                       date_tested=date,
	                       result=None,
	                       temperature=-999,
	                       humidity=-999,
	                       log_file=path,
	                       hidden_log_file=path,
	                       ) 

    else:
        temp_attempt = Attempt(card=card,
	                       plane_loc="default",
	                       test_type=temp_test,
	                       attempt_number=attempt_num,
	                       tester=tester,
	                       date_tested=date,
	                       result=0,
	                       temperature=-999,
	                       humidity=-999,
	                       log_file=path,
	                       hidden_log_file=path,
	                       )

	
    for attempt in prev_attempts:
        attempt.revoked = True
        attempt.save()
	
    temp_attempt.save()

set_card_status(card)


