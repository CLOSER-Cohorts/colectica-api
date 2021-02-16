## Overview

Colectica Portal can be accessed using the Rest API. 

Other examples are available on the Colectica Docs at https://docs.colectica.com/portal/api/examples/ 
and the API documentation is avaiable at https://discovery.closer.ac.uk/swagger/index.html

## File Description

- get_mode_collection.py - outputs study, instrument_urn and data collection mome
  - instrument_mode_data_collection.csv (questionnaire and mode list)
- get_questions.py - outputs the different item types
  - question.csv (question text and link to responses)
  - codelist.csv (code list response type_
  - response.csv (other response types)
- get_question_groups.py - outputs the concepts and a link to the question items
- RCNIC.py - creates question-concept dataset for input into a question-concept model
- xxx - creates questionnaire and associated items dataset for input into a question extraction model

## Dependencies

Non-standard libraries are required for these:

- Pandas
- Requests

To add these: (if using pip)

- pip install pandas
- pip install requests
