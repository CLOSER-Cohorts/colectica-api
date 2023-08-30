## Overview

This repository provides some utility classes to use the Rest APIs on a Colectica Portal. 
Developed as an in-house resource for CLOSER, we are making it publicly avaliable for others using the Colectica Portal.
If you have any requests or find any bugs, please log it under *Issues*.

If you want further advice or support please contact us at: closer@ucl.ac.uk

Colectica provide examples at https://docs.colectica.com/portal/api/examples/ and the Colectica Documentation for the API is available at https://discovery.closer.ac.uk/swagger/index.html

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
Colectica Portal supports DDI LIfecycle, the graph below, represents the relationship between the various DDI Elements to enable retrieval of related elements, e.g. variables linked to a specific quesiton

```mermaid
graph LR
  VS[Variable Set] --> VG[Variable Group]
  QGr[Question Group] --> Concept
  QGr[Question Group] --> QGr[Question Group]
  VG[Variable Group] --> Variable
  VG[Variable Group] --> Concept
  CS[Concept Set] --> Concept
  MetP[Metadata Package] --> InS[Instrument Set]
  MetP[Metadata Package] --> QuS[Question Set]
  MetP[Metadata Package] --> IIS[Interviewer Instruction Set]
  MetP[Metadata Package] --> CCS[Control Construct Set]
  MetP[Metadata Package] --> CaS[Category Set]
  MetP[Metadata Package] --> CLS[Code List Set]
  QuS[Question Set] --> Question
  OrS[Organization Set] -->  Organization
  UnS[Universe Set] --> Universe
  UnG[Universe Group] --> Universe
  Project --> Series
  Series --> Organization
  Series --> Universe
  Series --> Study
  Study --> Organization
  Study --> Universe
  Study --> DaC[Data Collection]
  Study --> DaF[Data File]
  DaC[Data Collection] --> Organization
  UnG[Universe Group] --> Universe
  InS[Instrument Set] --> Instrument
  Instrument --> Sequence
  Sequence --> Sequence
  Sequence --> Statement
  Sequence --> QA[Question Activity]
  QA[Question Activity] --> Question
  QG[Question Grid] --> CoS[Code Set]
  QG[Question Grid] --> II[Interviewer Instruction]
  Question --> CoS[Code Set]
  Question --> II[Interviewer Instruction]
  CLS[Code List Set] --> CoS[Code Set]
  CoS --> Category
  CaS[Category Set] --> Category
  CCS[Control Construct Set] --> Sequence
  Conditional --> Sequence
  CCS[Control Construct Set] --> Conditional
  CCS[Control Construct Set] --> Statement
  CCS[Control Construct Set] --> QA[Question Activity]
  DaF[Data file] --> DL[Data Layout]
  DaF[Data file] --> VaS[Variable Statistic]
  VaS[Variable Statistic] --> Variable
  IIS[Interviewer Instruction Set] --> II[Interviewer Instruction]
  loop --> Sequence
```
