## Overview

This repository provides some utility classes to use the Rest APIs on a Colectica Portal. 
Developed as an in-house resource for CLOSER, we are making it publicly avaliable for others using the Colectica Portal.
If you have any requests or find any bugs, please log it under *Issues*.

If you want further advice or support please contact us at: closer@ucl.ac.uk

Colectica provide examples at https://docs.colectica.com/repository/functionality/rest-api/examples/
and the Colectica Documentation for the API is available at https://discovery.closer.ac.uk/swagger/index.html

## Installation

```
pip install colectica-api
```

## Basic usage

```
from colectica_api import ColecticaObject
C = ColecticaObject("colectica.example.com", <username>, <password>)
C.search_item(...)
```

See `example.ipynb` for a more complete example.

## API relationship graph
Colectica Portal supports DDI LIfecycle, the graph below, represents the relationship between the various DDI Elements to enable retrieval of related elements, e.g. variables linked to a specific question

```mermaid
graph LR
  QGr[Question Group] --> Concept
  QGr[Question Group] --> Question
  QGr[Question Group] --> QG[Question Grid]
  VG[Variable Group] --> Variable
  VG[Variable Group] --> Concept
  UnG[Universe Group] --> Universe
  Variable --> Question
  Group --> Organization
  Group --> Universe
  Group --> Study
  Study --> Organization
  Study --> Universe
  Study --> DaC[Data Collection]
  Study --> DaS[Data Set]
  DaC[Data Collection] --> Organization
  DaC[Data Collection] ==> Instrument
  UnG[Universe Group] --> Universe
  Instrument --> Sequence
  Sequence --> Statement
  Sequence --> QA[Question Activity]
  QA[Question Activity] --> Question
  QG[Question Grid] --> CoS[Code Set]
  QG[Question Grid] --> II[Interviewer Instruction]
  Question --> CoS[Code Set]
  Question --> II[Interviewer Instruction]
  CoS --> Category
  CCS[Control Construct Set] --> Sequence
  Conditional --> Sequence
  CCS[Control Construct Set] --> Conditional
  CCS[Control Construct Set] --> Statement
  CCS[Control Construct Set] --> Loop
  CCS[Control Construct Set] --> QA[Question Activity]
  DaS[Data Set] --> VaS[Variable Statistic]
  DaS[Data Set] --> Variable
  VaS[Variable Statistic] --> Variable
  Variable --> VariableRepresentation
  VariableRepresentation ==> CoS[Code Set]
  VariableRepresentation ==> Numeric
  VariableRepresentation ==> Text
  VariableRepresentation ==> DateTime
  Loop --> Sequence
```
