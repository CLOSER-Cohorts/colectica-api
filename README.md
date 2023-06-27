## Overview

Colectica Portal can be accessed using the Rest API. 

Other examples are available on the Colectica Docs at https://docs.colectica.com/portal/api/examples/ 
and the API documentation is avaiable at https://discovery.closer.ac.uk/swagger/index.html

## Installation

```
pip install colectica_api
```

## Basic usage

```
from colectica_api import ColecticaObject
C = ColecticaObject(collectica.example.com, <username>, <password>)
C.general_search(...)
```

See `example.ipynb` for a more complete example.