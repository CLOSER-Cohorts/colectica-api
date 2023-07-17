## Overview

Colectica Portal can be accessed using the Rest API. 

Other examples are available on the Colectica Docs at https://docs.colectica.com/portal/api/examples/ 
and the API documentation is available at https://discovery.closer.ac.uk/swagger/index.html

## Installation

```
pip install colectica_api
```

## Basic usage

```
from colectica_api import ColecticaObject
C = ColecticaObject(colectica.example.com, <username>, <password>)
C.search_item(...)
```

See `example.ipynb` for a more complete example.


## Closer Discovery relationship graph

Work-in-progress!

```mermaid
graph LR
  QG[Question Group] --> Concept
  QG[Question Group] --> QG[Question Group]
  VG[Variable Group] --> Concept
  CS[Concept Set] --> Concept
  Project --> Series
  Series --> Organization
  Series --> Universe
  Series --> Study
  Study --> Organization
  Study --> Universe
  Study --> DaC[Data Collection]
  Study --> DaF[Data File]
  DaC[Data Collection] --> Organization
  Instrument --> Sequence
  Sequence --> Sequence
  Sequence --> Statement
  Sequence --> QA[Question Activity]
  QA[Question Activity] --> Question
  Question --> CoS[Code Set]
  CoS --> Category
  CCS[Control Construct Set] --> Sequence
  Conditional --> Sequence
  CCS[Control Construct Set] --> Conditional
  CCS[Control Construct Set] --> Statement
  CCS[Control Construct Set] --> QA[Question Activity]
  DaF[Data file] --> DL[Data Layout]
  DaF[Data file] --> VaS[Variable Statistic]
  VaS[Variable Statistic] --> Variable
```
