"""This code shows how we deprecated all the items in the MCS study, except for items with the type 
Data Collection, Organization, Concept, Universe, Study, and Series.
"""

from colectica_api import ColecticaObject
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
HOSTNAME = "HOSTNAME"
C = ColecticaObject(HOSTNAME, USERNAME, PASSWORD, verify_ssl=False)

# Specify the Millenium Cohort Study (MCS) which we want to search for items to deprecate in...
search_sets = [{ "agencyId": "uk.cls.mcs", 
   "identifier": "0d8a7220-c61b-4542-967d-a40cb5aca430", 
   "version": "57" }]
   
allItemsInMcs=C.search_items([],SearchSets=search_sets)['Results']

itemTypesToRemoveFromList = [C.item_code('Data Collection'), 
   C.item_code('Organization'),
   C.item_code('Concept'),
   C.item_code('Universe'),
   C.item_code('Study'),
   C.item_code('Series')
]

mcsAndCloserItemsToDeprecate=[x for x in allItemsInMcs if x['ItemType'] not in itemTypesToRemoveFromList]

# A count indicator to track progress
count = 0

for item in mcsAndCloserItemsToDeprecate:
    count = count + 1
    print(f"Deprecating {count} of {len(mcsAndCloserItemsToDeprecate)}")
    identifiersForItemToDeprecate = [{
      "agencyId": item['AgencyId'],
      "identifier": item['Identifier'],
      "version": item['Version']
       }]
    # Use the update_state method to deprecate an item.
    # Note that although we could send a list of items to deprecate,
    # the Colectica repository may return a 502 gateway error if 
    # we try to deprecate a list of items that is too large, so
    # to avoid this we are deprecating the items one by one.
    C.update_state(identifiersForItemToDeprecate, State=True)       

# Verify the deprecation operations have worked. We have to read in the items again
# from the repository...
allItemsInMcs=C.search_items([],SearchSets=search_sets)['Results']

# ...and we verify that the number of deprecated MCS items in the repository
# is what we expect it to be.
deprecatedMcsItems = sorted([x['Identifier'] for x in allItemsInMcs if x['IsDeprecated']==True])

deprecationSuccessful = deprecatedMcsItems == sorted([x['Identifier'] for x in mcsAndCloserItemsToDeprecate])

print(f"""Have we successfully deprecated the selected MCS items? {deprecationSuccessful}""")