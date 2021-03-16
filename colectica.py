"""
    Pull information using python ColecticaPortal api
"""

from io import StringIO
import xml.etree.ElementTree as ET
import pandas as pd
import json
import api


def remove_xml_ns(xml):
    """
    Read xml from string, remove namespaces, return root
    """
    it = ET.iterparse(StringIO(xml))
    for _, el in it:
        prefix, has_namespace, postfix = el.tag.partition('}')
        if has_namespace:
            el.tag = postfix  # strip all namespaces
    root = it.root
    return root


def root_to_dict_study(root):
    """
    Part of parse xml, item_type = Study
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    # Sweep Description
    sweep = {}
    sweep['title'] = root.find('.//Citation/Title/String').text
    sweep['principal_investigator'] = root.find('.//Citation/Creator/CreatorName/String').text
    if root.find('.//Citation/Publisher') is not None:
        sweep['publisher'] = root.find('.//Citation/Publisher/PublisherName/String').text
    else:
        sweep['publisher'] = None
    sweep['abstract'] = root.find('.//Abstract/Content').text
    pop = {}
    if root.find('.//UniverseReference') is not None:
        pop['Agency'] = root.find('.//UniverseReference/Agency').text
        pop['ID'] = root.find('.//UniverseReference/ID').text
        pop['Version'] = root.find('.//UniverseReference/Version').text
        pop['Type'] = root.find('.//UniverseReference/TypeOfObject').text
    sweep['population'] = pop
    # custom filed
    CustomFields = root.findall('.//UserAttributePair/AttributeValue')
    custom_list = []
    for x, cus in enumerate(CustomFields):
        # Convert a string representation of a dictionary to a dictionary
        custom_list.append(json.loads(cus.text))
    sweep['custom_field'] = custom_list
    info['sweep'] = sweep

    # Funding
    funding = {}
    organization = {}
    organization['Agency'] = root.find('.//FundingInformation/AgencyOrganizationReference/Agency').text
    organization['ID'] = root.find('.//FundingInformation/AgencyOrganizationReference/ID').text
    organization['Version'] = root.find('.//FundingInformation/AgencyOrganizationReference/Version').text
    organization['Type'] = root.find('.//FundingInformation/AgencyOrganizationReference/TypeOfObject').text
    funding['organization'] = organization
    info['funding'] = funding
    # TODO: Coverage
    coverages = root.findall('.//Coverage')
    # Data
    data = {}
    k = root.find('.//KindOfData')
    data['KindOfData'] = '-'.join(item.text for item in k)
    data['Analysis Unit'] = root.find('.//AnalysisUnit').text
    # data files
    datafile = {}
    if root.find('.//PhysicalInstanceReference') is not None:
        datafile['Agency'] = root.find('.//PhysicalInstanceReference/Agency').text
        datafile['ID'] = root.find('.//PhysicalInstanceReference/ID').text
        datafile['Version'] = root.find('.//PhysicalInstanceReference/Version').text
        datafile['Type'] = root.find('.//PhysicalInstanceReference/TypeOfObject').text
    data['Data File'] = datafile
    info['data'] = data
    # data collection
    datacol = {}
    datacol['Agency'] = root.find('.//DataCollectionReference/Agency').text
    datacol['ID'] = root.find('.//DataCollectionReference/ID').text
    datacol['Version'] = root.find('.//DataCollectionReference/Version').text
    datacol['Type'] = root.find('.//DataCollectionReference/TypeOfObject').text
    info['Data Collection'] = datacol
    # Extra
    metadata = {}
    if root.find('.//RequiredResourcePackages/ResourcePackageReference') is not None:
        metadata['Agency'] = root.find('.//RequiredResourcePackages/ResourcePackageReference/Agency').text
        metadata['ID'] = root.find('.//RequiredResourcePackages/ResourcePackageReference/ID').text
        metadata['Version'] = root.find('.//RequiredResourcePackages/ResourcePackageReference/Version').text
        metadata['Type'] = root.find('.//RequiredResourcePackages/ResourcePackageReference/TypeOfObject').text
    info['Metadata Packages'] = metadata
    return info


def root_to_dict_series(root):
    """
    Part of parse xml, item_type = Series
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    # Study Description
    study = {}
    study['title'] = root.find('.//Citation/Title/String').text
    study['principal_investigator'] = root.find('.//Citation/Creator/CreatorName/String').text
    study['publisher'] = root.find('.//Citation/Publisher/PublisherName/String').text
    study['rights'] = root.find('.//Citation/Copyright/String').text
    study['abstract'] = root.find('.//Abstract/Content').text
    pop = {}
    pop['Agency'] = root.find('.//UniverseReference/Agency').text
    pop['ID'] = root.find('.//UniverseReference/ID').text
    pop['Version'] = root.find('.//UniverseReference/Version').text
    pop['Type'] = root.find('.//UniverseReference/TypeOfObject').text
    study['population'] = pop
    info['study'] = study
    # Funding
    funding = {}
    if not root.find('.//FundingInformation/GrantNumber') is None:
        funding['GrantNumber'] = root.find('.//FundingInformation/GrantNumber').text
    organization = {}
    organization['Agency'] = root.find('.//FundingInformation/AgencyOrganizationReference/Agency').text
    organization['ID'] = root.find('.//FundingInformation/AgencyOrganizationReference/ID').text
    organization['Version'] = root.find('.//FundingInformation/AgencyOrganizationReference/Version').text
    organization['Type'] = root.find('.//FundingInformation/AgencyOrganizationReference/TypeOfObject').text
    funding['organization'] = organization
    info['funding'] = funding
    # Studies
    studies = root.findall('.//StudyUnitReference')
    study_list = []
    for x, study in enumerate(studies):
        study_dict={}
        study_dict['position'] = x + 1
        study_dict['Agency'] = study.find(".//Agency").text
        study_dict['ID'] = study.find(".//ID").text
        study_dict['Version'] = study.find(".//Version").text
        study_dict['Type'] = study.find(".//TypeOfObject").text
        study_list.append(study_dict)
    info['study'] = study_list
    return info


def root_to_dict_metadata_package(root):
    """
    Part of parse xml, item_type = Data Collection
    """
    info = dict([[i.attrib['typeOfUserID'].split(':')[-1], i.text] for i in root.findall('.//UserID')])
    info['URN'] = root.find('.//URN').text
    info['VersionResponsibility'] = root.find('.//VersionResponsibility').text
    if not root.find('.//VersionRationale') is None:
        info['VersionRationale'] = root.find('.//VersionRationale/RationaleDescription/String').text
    info['Citation'] = root.find('.//Citation/Title/String').text
    info['Purpose'] = root.find('.//Purpose/Content').text

    # InterviewerInstructionSchemeReference
    instruction_dict = {}
    instruction_ref = root.find('.//InterviewerInstructionSchemeReference')
    if not instruction_ref is None:
        instruction_dict['Agency'] = instruction_ref.find(".//Agency").text
        instruction_dict['ID'] = instruction_ref.find(".//ID").text
        instruction_dict['Version'] = instruction_ref.find(".//Version").text
        instruction_dict['Type'] = instruction_ref.find(".//TypeOfObject").text
    info['InterviewerInstructionSchemeReference'] = instruction_dict

    # ControlConstructSchemeReference
    cc_dict = {}
    cc_ref = root.find('.//ControlConstructSchemeReference')
    if not instruction_ref is None:
        cc_dict['Agency'] = cc_ref.find(".//Agency").text
        cc_dict['ID'] = cc_ref.find(".//ID").text
        cc_dict['Version'] = cc_ref.find(".//Version").text
        cc_dict['Type'] = cc_ref.find(".//TypeOfObject").text
    info['ControlConstructSchemeReference'] = cc_dict

    # QuestionSchemeReference
    question_all = root.findall('.//QuestionSchemeReference')
    question_list = []
    for question in question_all:
        question_dict = {}
        question_dict['Agency'] = question.find('.//Agency').text
        question_dict['ID'] = question.find('.//ID').text
        question_dict['Version'] = question.find('.//Version').text
        question_dict['Type'] = question.find('.//TypeOfObject').text
        question_list.append(question_dict)
    info['QuestionSchemeReference'] = question_list

    # CategorySchemeReference
    category_dict = {}
    category_ref = root.find('.//CategorySchemeReference')
    if not instruction_ref is None:
        category_dict['Agency'] = category_ref.find(".//Agency").text
        category_dict['ID'] = category_ref.find(".//ID").text
        category_dict['Version'] = category_ref.find(".//Version").text
        category_dict['Type'] = category_ref.find(".//TypeOfObject").text
    info['CategorySchemeReference'] = category_dict

    # CodeListSchemeReference
    code_dict = {}
    code_ref = root.find('.//CodeListSchemeReference')
    if not instruction_ref is None:
        code_dict['Agency'] = code_ref.find(".//Agency").text
        code_dict['ID'] = code_ref.find(".//ID").text
        code_dict['Version'] = code_ref.find(".//Version").text
        code_dict['Type'] = code_ref.find(".//TypeOfObject").text
    info['CodeListSchemeReference'] = code_dict

    # InstrumentSchemeReference
    instrument_dict = {}
    instrument_ref = root.find('.//InstrumentSchemeReference')
    if not instruction_ref is None:
        instrument_dict['Agency'] = instrument_ref.find(".//Agency").text
        instrument_dict['ID'] = instrument_ref.find(".//ID").text
        instrument_dict['Version'] = instrument_ref.find(".//Version").text
        instrument_dict['Type'] = instrument_ref.find(".//TypeOfObject").text
    info['InstrumentSchemeReference'] = instrument_dict

    return info


def root_to_dict_data_collection(root):
    """
    Part of parse xml, item_type = Data Collection
    """
    info = {}
    print(info)
    info['URN'] = root.find('.//URN').text
    info['Name'] = root.find('.//DataCollectionModuleName/String').text
    info['Label'] = root.find('.//Label/Content').text
    # InstrumentRef
    cus_dict = {}
    cus = root.findall('.//UserAttributePair')
    for item in cus:
        k = item.find('.//AttributeKey').text.split(':')[-1]
        v = item.find('.//AttributeValue').text.replace('[','').replace(']','').replace('"', '').replace("'","")
        cus_dict[k] = v
    info['Ref'] = cus_dict

    # CollectionEvent
    event = {}
    event['URN'] = root.find('.//CollectionEvent/URN').text
    event['Agency'] = root.find('.//CollectionEvent/Agency').text
    event['ID'] = root.find('.//CollectionEvent/ID').text
    event['Version'] = root.find('.//CollectionEvent/Version').text
    # Organization Reference
    organization_list = []
    organization_all = root.findall('.//CollectionEvent/DataCollectorOrganizationReference')
    for organization in organization_all:
        OrganizationRef = {}
        OrganizationRef['Agency'] = organization.find('.//Agency').text
        OrganizationRef['ID'] = organization.find('.//ID').text
        OrganizationRef['Version'] = organization.find('.//Version').text
        OrganizationRef['Type'] = organization.find('.//TypeOfObject').text
    event['OrganizationRef'] = organization_list

    # Data Collection Date
    DCDate = {}
    date = root.find('.//CollectionEvent/DataCollectionDate')
    if date.find('.//StartDate') is not None:
        DCDate['StartDate'] = date.find('.//StartDate').text
    elif date.find('.//EndDate') is not None:
        DCDate['EndDate'] = date.find('.//EndDate').text
    elif date.find('.//SimpleDate') is not None:
        DCDate['SimpleDate'] = date.find('.//SimpleDate').text
    event['Date'] = DCDate
    # Mode Of Collection
    mode_list = []
    mode_all = root.findall('.//CollectionEvent/ModeOfCollection')
    # list multiple types
    for type_mode in mode_all:
        mode_dict = {}
        mode_dict['URN'] = type_mode.find('./URN').text
        mode_dict['Agency'] = type_mode.find('./Agency').text
        mode_dict['ID'] = type_mode.find('./ID').text
        mode_dict['Version'] = type_mode.find('./Version').text
        mode_dict['TypeOfMode'] = type_mode.find('./TypeOfModeOfCollection').text
        mode_dict['Description'] = type_mode.find('./Description/Content').text
        mode_list.append(mode_dict)
    event['ModeOfCollection'] = mode_list
    info['CollectionEvent'] = event
    # Question Scheme Reference
    QSR = {}
    if root.find('.//QuestionSchemeReference') is not None:
        QSR['Agency'] = root.find('.//QuestionSchemeReference/Agency').text
        QSR['ID'] = root.find('.//QuestionSchemeReference/ID').text
        QSR['Version'] = root.find('.//QuestionSchemeReference/Version').text
        QSR['TypeOfObject'] = root.find('.//QuestionSchemeReference/TypeOfObject').text
    info['reference'] = QSR
    return info


def root_to_dict_sequence(root):
    """
    Part of parse xml, item_type = Sequence
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    info['SourceId'] = root.find('.//UserID').text
    if root.find('.//ConstructName/String') is not None:
        info['ConstructName'] = root.find('.//ConstructName/String').text
    else:
        info['ConstructName'] = None
    if root.find('.//Label/Content') is not None:
        info['Label'] = root.find('.//Label/Content').text
    else:
        info['Label'] = None
    references = root.findall(".//ControlConstructReference")
    ref_list = []
    for x, ref in enumerate(references):
        ref_dict={}
        ref_dict['position'] = x + 1
        ref_dict['Agency'] = ref.find(".//Agency").text
        ref_dict['ID'] = ref.find(".//ID").text
        ref_dict['Version'] = ref.find(".//Version").text
        ref_dict['Type'] = ref.find(".//TypeOfObject").text
        ref_list.append(ref_dict)
    info['references'] = ref_list
    return info


def root_to_dict_statement(root):
    """
    Part of parse xml, item_type = Statement
    """
    info = {}
    info['StatementURN'] = root.find('.//URN').text
    info['SourceId'] = root.find('.//UserID').text
    instruction = root.find(".//UserAttributePair/AttributeValue").text
    if instruction == '{}':
        info['Instruction'] = ''
    else:
        info['Instruction'] = instruction
    info['Label'] = root.find(".//ConstructName/String").text
    info['Literal'] = root.find(".//DisplayText/LiteralText/Text").text
    return info


def root_to_dict_organization(root):
    """
    Part of parse xml, item_type = Organization
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    # Nickname
    cus_dict = {}
    cus = root.findall('.//UserAttributePair')
    for item in cus:
        k = item.find('.//AttributeKey').text.split(':')[-1]
        v = item.find('.//AttributeValue').text
        cus_dict[k] = v
    info['cust'] = cus_dict
    info['Name'] = root.find('.//OrganizationIdentification/OrganizationName/String').text
    info['Image'] = root.find('.//OrganizationIdentification/OrganizationImage/ImageLocation').text
    info['Description'] = root.find('.//Description/Content').text
    return info


def root_to_dict_instrument(root):
    """
    Part of parse xml, item_type = Instrument
    """
    info = {}
    info['InstrumentURN'] = root.find('.//URN').text
    if root.findall(".//*[@typeOfUserID='colectica:sourceId']") != []:
        info['InstrumentSourceID'] = root.findall(".//*[@typeOfUserID='colectica:sourceId']")[0].text 
    if root.findall(".//*[@typeOfUserID='closer:sourceFileName']") != []:
        info['InstrumentLabel'] = root.findall(".//*[@typeOfUserID='closer:sourceFileName']")[0].text
    info['InstrumentName'] = root.find(".//InstrumentName/String").text
    if not root.find(".//ExternalInstrumentLocation") is None:
        info['ExternalInstrumentLocation'] = root.find(".//ExternalInstrumentLocation").text
    else:
        info['ExternalInstrumentLocation'] = None
    references = root.findall(".//ControlConstructReference")
    ref_list = []
    for x, ref in enumerate(references):
        ref_dict={}
        ref_dict['position'] = x + 1
        ref_dict['Agency'] = ref.find(".//Agency").text
        ref_dict['ID'] = ref.find(".//ID").text
        ref_dict['Version'] = ref.find(".//Version").text
        ref_dict['Type'] = ref.find(".//TypeOfObject").text
        ref_list.append(ref_dict)
    info['references'] = ref_list
    return info


def root_to_dict_question_group(root):
    """
    Part of parse xml, item_type = Question Group
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    if root.find('.//QuestionGroupName/String') is not None:
        info['Name'] = root.find('.//QuestionGroupName/String').text
    else:
        info['Name'] = None
    if root.find('.//Label/Content').text is not None:
        info['Label'] = root.find('.//Label/Content').text
    else:
        info['Label'] = None

    # Concept Reference
    ConceptRef = {}
    if root.find('.//ConceptReference') is not None:
        ConceptRef['Agency'] = root.find('.//ConceptReference/Agency').text
        ConceptRef['ID'] = root.find('.//ConceptReference/ID').text
        ConceptRef['Version'] = root.find('.//ConceptReference/Version').text
        ConceptRef['Type'] = root.find('.//ConceptReference/TypeOfObject').text
    info['ConceptRef'] = ConceptRef
    # Question Item Reference
    QuestionItemRef = root.findall(".//QuestionItemReference")
    QIref_list = []
    for x, ref in enumerate(QuestionItemRef):
        ref_dict={}
        ref_dict['position'] = x + 1
        ref_dict['Agency'] = ref.find(".//Agency").text
        ref_dict['ID'] = ref.find(".//ID").text
        ref_dict['Version'] = ref.find(".//Version").text
        ref_dict['Type'] = ref.find(".//TypeOfObject").text
        QIref_list.append(ref_dict)
    info['QuestionItemRef'] = QIref_list
    # Question Group Reference
    QuestionGroupRef = root.findall(".//QuestionGroupReference")
    QGref_list = []
    for x, ref in enumerate(QuestionGroupRef):
        ref_dict={}
        ref_dict['position'] = x + 1
        ref_dict['Agency'] = ref.find(".//Agency").text
        ref_dict['ID'] = ref.find(".//ID").text
        ref_dict['Version'] = ref.find(".//Version").text
        ref_dict['Type'] = ref.find(".//TypeOfObject").text
        QGref_list.append(ref_dict)
    info['QuestionGroupRef'] = QGref_list
    return info


def root_to_dict_concept(root):
    """
    Part of parse xml, item_type = Concept
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    info['VersionResponsibility'] = root.find('.//VersionResponsibility').text
    info['VersionRationale'] = root.find('.//VersionRationale/RationaleDescription/String').text
    info['Name'] = root.find('.//ConceptName/String').text
    info['Label'] = root.find('.//Label/Content').text
    return info


def root_to_dict_interviewer_instruction(root):
    """
    Part of parse xml, item_type = Interviewer Instruction
    """
    info = {}
    info['InstructionURN'] = root.find('.//URN').text
    info['UserID'] = root.find('.//UserID').text
    info['InstructionText'] = root.find('.//InstructionText/LiteralText/Text').text
    return info


def root_to_dict_question(root):
    """
    Part of parse xml, item_type = Question
    """
    info = {}
    info['QuestionURN'] = root.find('.//URN').text
    info['QuestionUserID'] = root.find('.//UserID').text
    QLabel = root.find('.//UserAttributePair/AttributeValue').text
    info['QuestionLabel'] = list(eval(QLabel).values())[0]
    info['QuestionItemName'] = root.find(".//QuestionItemName/String").text
    if root.find(".//QuestionText/LiteralText/Text") is not None:
        info['QuestionLiteral'] = root.find(".//QuestionText/LiteralText/Text").text
    else:
        info['QuestionLiteral'] = None
    # ResponseCardinality
    cardinality = root.find('.//ResponseCardinality')
    car_dict = {}
    car_dict['minimumResponses'] = cardinality.attrib['minimumResponses']
    car_dict['maximumResponses'] = cardinality.attrib['maximumResponses']
    info['ResponseCardinality'] = car_dict
    # response
    response = {}
    CodeDomain = root.find(".//CodeDomain")
    TextDomain = root.find(".//TextDomain")
    NumericDomain = root.find(".//NumericDomain")
    DateTimeDomain = root.find(".//DateTimeDomain")
    if CodeDomain is not None:
        response['response_type'] = 'CodeList'
        response['CodeList_Agency'] = root.find('.//CodeListReference/Agency').text
        response['CodeList_ID'] = CodeDomain.find(".//CodeListReference/ID").text
        response['CodeList_version'] = CodeDomain.find(".//CodeListReference/Version").text
        response['code_list_URN'] = (':').join(['urn:ddi', response['CodeList_Agency'], response['CodeList_ID'], response['CodeList_version']])
    elif TextDomain is not None:
        response['response_type'] = 'Text'
        response['response_label'] = TextDomain.find(".//Label/Content").text
    elif NumericDomain is not None:
        response['response_type'] = 'Numeric'
        response['response_label'] = root.find(".//Label").text
        response['response_NumericType'] = root.find(".//NumericTypeCode").text
        if root.find(".//NumberRange/Low") is not None:
            response['response_RangeLow'] = root.find(".//NumberRange/Low").text
        else:
            response['response_RangeLow'] = None
        if root.find(".//NumberRange/High") is not None:
            response['response_RangeHigh'] = root.find(".//NumberRange/High").text
        else:
            response['response_RangeHigh'] = None
    elif DateTimeDomain is not None:
        response['response_type'] = 'DateTime'
        response['DateTypeCode'] = DateTimeDomain.find(".//DateTypeCode").text
        response['response_label'] = DateTimeDomain.find(".//Label/Content").text

    info['Response'] = response

    # InterviewerInstructionReference
    inst_dict = {}
    InstructionRef = root.find(".//InterviewerInstructionReference")
    if InstructionRef is not None:
        inst_dict['Agency'] = InstructionRef.find(".//Agency").text
        inst_dict['ID'] = InstructionRef.find(".//ID").text
        inst_dict['Version'] = InstructionRef.find(".//Version").text
        inst_dict['Type'] = InstructionRef.find(".//TypeOfObject").text
    info['Instruction'] = inst_dict
    return info


def root_to_dict_question_grid(root):
    """
    Part of parse xml, item_type = Question Grid
    """
    info = {}
    info['QuestionGridURN'] = root.find('.//URN').text
    info['QuestionGridUserID'] = root.find('.//UserID').text
    info['QuestionGridLabel'] = root.find(".//UserAttributePair/AttributeValue").text
    info['QuestionGridName'] = root.find('.//QuestionGridName/String').text
    info['QuestionGridLiteral'] = root.find('.//QuestionText/LiteralText/Text').text

    # GridDimension
    GridDimension = root.findall('.//GridDimension')
    grid_dimension_list = []
    for x, dim in enumerate(GridDimension):
        dim_dict={}
        dim_dict['rank'] = dim.attrib['rank']
        ResponseCardinality = dim.find('.//CodeDomain/ResponseCardinality')
        dim_dict['minimumResponses'] = ResponseCardinality.attrib['minimumResponses']
        dim_dict['maximumResponses'] = ResponseCardinality.attrib['maximumResponses']

        code_ref_dict = {}
        code_ref = dim.find('.//CodeDomain/CodeListReference')
        if not code_ref is None:
            code_ref_dict['Agency'] = code_ref.find('.//Agency').text
            code_ref_dict['ID'] = code_ref.find('.//ID').text
            code_ref_dict['Version'] = code_ref.find('.//Version').text
            code_ref_dict['TypeOfObject'] = code_ref.find('.//TypeOfObject').text

        dim_dict['CodeListReference'] = code_ref_dict
        grid_dimension_list.append(dim_dict)

    info['GridDimension'] = grid_dimension_list

    num_domain_dict = {}
    NumericDomain = root.find('.//NumericDomain')
    if not NumericDomain is None:
        num_domain_dict['NumericTypeCode'] = root.find(".//NumericTypeCode").text
        num_domain_dict['Content'] = root.find(".//Label/Content").text

        if NumericDomain.find(".//NumberRange/Low") is not None:
            num_domain_dict['NumberRangeLow'] = NumericDomain.find(".//NumberRange/Low").text
        else:
            num_domain_dict['NumberRangeLow'] = None
        if NumericDomain.find(".//NumberRange/High") is not None:
            num_domain_dict['NumberRangeHigh'] = NumericDomain.find(".//NumberRange/High").text
        else:
            num_domain_dict['NumberRangeHigh'] = None

    info['NumericDomain'] = num_domain_dict

    return info


def root_to_dict_code_set(root):
    """
    Part of parse xml, item_type = Code Set
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    info['UserID'] = root.find('.//UserID').text
    info['Label'] = root.find('.//Label/Content').text

    # Codes
    codes = root.findall('.//Code')
    code_list = []
    for x, code in enumerate(codes):
        code_dict={}
        code_dict['URN'] = code.find('.//URN').text
        code_dict['Agency'] = code.find('.//Agency').text
        code_dict['ID'] = code.find('.//ID').text
        code_dict['Version'] = code.find('.//Version').text
        code_dict['Value'] = code.find('.//Value').text

        cat_ref_dict = {}
        cat = code.find('CategoryReference')
        if not cat is None:
            cat_ref_dict['Agency'] = cat.find('.//Agency').text
            cat_ref_dict['ID'] = cat.find('.//ID').text
            cat_ref_dict['Version'] = cat.find('.//Version').text
            cat_ref_dict['TypeOfObject'] = cat.find('.//TypeOfObject').text
        code_dict['CategoryReference'] = cat_ref_dict
        code_list.append(code_dict)
    info['Code'] = code_list

    return info


def root_to_dict_category(root):
    """
    Part of parse xml, item_type = Category
    """
    info = {}
    info['URN'] = root.find('.//URN').text
    info['UserID'] = root.find('.//UserID').text
    info['Name'] = root.find('.//CategoryName/String').text
    if not root.find('.//Label/Content') is None:
        info['Label'] = root.find('.//Label/Content').text
    else:
        info['Label'] = None
    return info


def root_to_dict_question_activity(root):
    """
    Part of parse xml, item_type = Question Activity
    """
    info = {}
    info['URN'] = root.find('.//QuestionConstruct/URN').text
    info['UserID'] = root.find('.//QuestionConstruct/UserID').text
    info['ConstructName'] = root.find('.//QuestionConstruct/ConstructName/String').text
    info['Label'] = root.find('.//QuestionConstruct/Label/Content').text
    info['ResponseUnit'] = root.find('.//QuestionConstruct/ResponseUnit').text

    # QuestionReference
    QuestionReference = root.find('.//QuestionConstruct/QuestionReference')
    question_ref_dict = {}
    if not QuestionReference is None:
        question_ref_dict['Agency'] = QuestionReference.find('.//Agency').text
        question_ref_dict['ID'] = QuestionReference.find('.//ID').text
        question_ref_dict['Version'] = QuestionReference.find('.//Version').text
        question_ref_dict['TypeOfObject'] = QuestionReference.find('.//TypeOfObject').text
        info['QuestionReference'] = question_ref_dict

    return info


def root_to_dict_variable(root):
    """
    Part of parse xml, item_type = Variable
    """
    info = {}
    info['URN'] = root.find('.//Variable/URN').text
    info['UserID'] = root.find('.//Variable/UserID').text
    info['VariableName'] = root.find('.//Variable/VariableName/String').text
    info['Label'] = root.find('.//Variable/Label/Content').text

    # QuestionReference
    QuestionReference = root.find('.//Variable/QuestionReference')
    question_ref_dict = {}
    if not QuestionReference is None:
        question_ref_dict['Agency'] = QuestionReference.find('.//Agency').text
        question_ref_dict['ID'] = QuestionReference.find('.//ID').text
        question_ref_dict['Version'] = QuestionReference.find('.//Version').text
        question_ref_dict['TypeOfObject'] = QuestionReference.find('.//TypeOfObject').text
        info['QuestionReference'] = question_ref_dict

    # VariableRepresentation/CodeRepresentation
    CodeRepresentation = root.find('.//Variable/VariableRepresentation/CodeRepresentation')
    code_rep_dict = {}
    if not CodeRepresentation is None:
        code_rep_dict['RecommendedDataType'] = CodeRepresentation.find('.//RecommendedDataType').text
        # CodeListReference
        code_ref = {}
        CodeListReference = CodeRepresentation.find('.//CodeListReference')
        if not CodeListReference is None:
            code_ref['ID'] = CodeListReference.find('.//ID').text
            code_ref['Version'] = CodeListReference.find('.//Version').text
            code_ref['TypeOfObject'] = CodeListReference.find('.//TypeOfObject').text
        code_rep_dict['CodeListReference'] = code_ref
    info['CodeRepresentation'] = code_rep_dict

    return info


def root_to_dict_conditional(root):
    """
    Part of parse xml, item_type = Conditional
    """
    info = {}
    info['URN'] = root.find('.//IfThenElse/URN').text
    info['UserID'] = root.find('.//IfThenElse/UserID').text
    info['ConstructName'] = root.find('.//IfThenElse/ConstructName/String').text

    IfCondition = root.find('.//IfThenElse/IfCondition')
    ifcondition_dict = {}
    if not IfCondition is None:
        ifcondition_dict['Description'] = IfCondition.find('.//Description/Content').text
        ifcondition_dict['ProgramLanguage'] = IfCondition.find('.//Command/ProgramLanguage').text
        ifcondition_dict['CommandContent'] = IfCondition.find('.//Command/CommandContent').text
    info['IfCondition'] = ifcondition_dict

    # ThenConstructReference
    IfThenElseReference = root.find('.//IfThenElse/ThenConstructReference')
    IfThenElse_ref_dict = {}
    if not IfThenElseReference is None:
        IfThenElse_ref_dict['Agency'] = IfThenElseReference.find('.//Agency').text
        IfThenElse_ref_dict['ID'] = IfThenElseReference.find('.//ID').text
        IfThenElse_ref_dict['Version'] = IfThenElseReference.find('.//Version').text
        IfThenElse_ref_dict['TypeOfObject'] = IfThenElseReference.find('.//TypeOfObject').text
    info['IfThenElseReference'] = IfThenElse_ref_dict

    return info


def root_to_dict_loop(root):
    """
    Part of parse xml, item_type = Loop
    """
    info = {}
    info['URN'] = root.find('.//Loop/URN').text
    info['UserID'] = root.find('.//Loop/UserID').text
    info['ConstructName'] = root.find('.//Loop/ConstructName/String').text

    InitialValue = root.find('.//Loop/InitialValue')
    InitialValue_dict = {}
    if not InitialValue is None:
        InitialValue_dict['ProgramLanguage'] = InitialValue.find('.//Command/ProgramLanguage').text
        InitialValue_dict['CommandContent'] = InitialValue.find('.//Command/CommandContent').text
    info['InitialValue'] = InitialValue_dict

    LoopWhile = root.find('.//Loop/LoopWhile')
    LoopWhile_dict = {}
    if not LoopWhile is None:
        LoopWhile_dict['ProgramLanguage'] = LoopWhile.find('.//Command/ProgramLanguage').text
        LoopWhile_dict['CommandContent'] = LoopWhile.find('.//Command/CommandContent').text
    info['LoopWhile'] = LoopWhile_dict

    #TODO StepValue
    StepValue = root.find('.//Loop/StepValue')
    StepValue_dict = {}
    if not StepValue is None:
        print('TODO StepValue')

    # ControlConstructReference
    CCReference = root.find('.//Loop/ControlConstructReference')
    cc_ref_dict = {}
    if not CCReference is None:
        cc_ref_dict['Agency'] = CCReference.find('.//Agency').text
        cc_ref_dict['ID'] = CCReference.find('.//ID').text
        cc_ref_dict['Version'] = CCReference.find('.//Version').text
        cc_ref_dict['TypeOfObject'] = CCReference.find('.//TypeOfObject').text
    info['ControlConstructReference'] = cc_ref_dict

    return info


def parse_xml(xml, item_type):
    """
    Used for parsing Item value
    item_type in:
        - Series
        - Study
        - Metadata Package
        - Data Collection
        - Sequence
        - Statement
        - Organization
        - Instrument
        - Question Group
        - Concept
        - Question
        - Question Grid
        - Code Set
        - Interviewer Instruction
        - Category
        - Question Activity
        - Variable
        - Conditional
        - Loop
    """
    root = remove_xml_ns(xml)

    if item_type == 'Series':
        info = root_to_dict_series(root)
    elif item_type == 'Study':
        info = root_to_dict_study(root)
    elif item_type == 'Metadata Package':
        info = root_to_dict_metadata_package(root)
    elif item_type == 'Data Collection':
        info = root_to_dict_data_collection(root)
    elif item_type == 'Sequence':
        info = root_to_dict_sequence(root)
    elif item_type == 'Statement':
        info = root_to_dict_statement(root)
    elif item_type == 'Organization':
        info = root_to_dict_organization(root)
    elif item_type == 'Instrument':
        info = root_to_dict_instrument(root)
    elif item_type == 'Question Group':
        info = root_to_dict_question_group(root)
    elif item_type == 'Concept':
        info = root_to_dict_concept(root)
    elif item_type == 'Question':
        info = root_to_dict_question(root)
    elif item_type == 'Question Grid':
        info = root_to_dict_question_grid(root)
    elif item_type == 'Code Set':
        info = root_to_dict_code_set(root)
    elif item_type == 'Interviewer Instruction':
        info = root_to_dict_interviewer_instruction(root)
    elif item_type == 'Category':
        info = root_to_dict_category(root)
    elif item_type == 'Question Activity':
        info = root_to_dict_question_activity(root)
    elif item_type == 'Variable':
        info = root_to_dict_variable(root)
    elif item_type == 'Conditional':
        info = root_to_dict_conditional(root)
    elif item_type == 'Loop':
        info = root_to_dict_loop(root)
    else:
        info = {}
    return info


class ColecticaObject(api.ColecticaLowLevelAPI):
    """Ask practical questions to Colectica."""

    def item_to_dict(self, AgencyId, Identifier):
        """
        From an agency ID and an identifier, get information using get_an_item
        Return a dictionary
        """
        result = self.get_an_item(AgencyId, Identifier)
        info = {}
        item_info = None
        if not result is None:
            for k, v in result.items():
                if k == 'ItemType':
                    info[k] = self.item_code_inv(v)
                elif k == 'Item':
                    item_info = parse_xml(v, self.item_code_inv(result['ItemType']))
                else:
                    info[k] = v
            d = {**info, **item_info}
        else:
            d = {}
        return d


    def get_a_set_to_df(self, AgencyId, Identifier, Version):
        """
        From a study, find all questions
        Example:
            'ItemType': 'f196cc07-9c99-4725-ad55-5b34f479cf7d', (Instrument)
            'AgencyId': 'uk.cls.nextsteps',
            'Version': 1,
            'Identifier': 'a6f96245-5c00-4ad3-89e9-79afaefa0c28'
        """

        l = self.get_a_set_typed(AgencyId, Identifier, Version)
        # print(l)
        df = pd.DataFrame(
             [self.item_code_inv(l[i]["Item2"]), l[i]["Item1"]["Item1"]] for i in range(len(l))
         )
        df.columns = ["ItemType", "Identifier"]

        return df


    def item_info_set(self, AgencyId, Identifier):
        """
        From an ID, find it's name and set
        """
        info = self.item_to_dict(AgencyId, Identifier)
        df = self.get_a_set_to_df(AgencyId, Identifier, str(info['Version']))
        return df, info


    def get_question_group_info(self, AgencyId, Identifier):
        """
        From a question identifier, get information about it
        """
        question_group = self.get_an_item(AgencyId, Identifier)
        root = remove_xml_ns(question_group["Item"])

        question = {}
        for k, v in question_result.items():
            if k == 'ItemType':
                question[k] = self.item_code_inv(v)
            elif k == 'Item':
                question['UserID'] = root.find(".//UserID").text
                question['QuestionLabel'] = root.find(".//UserAttributePair/AttributeValue").text
                question['QuestionItemName'] = root.find(".//QuestionItemName/String").text
                question['QuestionLiteral'] = root.find(".//QuestionText/LiteralText/Text").text
            else:
                question[k] = v
        return question


    def get_question_all(self, AgencyId, Identifier):
        """
        From a question ID, return question info and it's response
        """
        # print(AgencyId, Identifier)
        question_info = self.item_to_dict(AgencyId, Identifier)
        # print(question_info)

        if question_info['Response']== {}:
            QI_response_type = None
        else:
            QI_response_type = question_info['Response']['response_type']
        question_data = [ [ question_info['QuestionURN'],
                            question_info['QuestionUserID'],
                            question_info['QuestionLabel'],
                            question_info['QuestionItemName'],
                            question_info['QuestionLiteral'],
                            QI_response_type ] ]

        df_question = pd.DataFrame(question_data,
                                   columns=['QuestionURN', 'QuestionUserID', 'QuestionLabel', 'QuestionItemName', 
                                            'QuestionLiteral', 'response_type'])

        # instruction
        if question_info['Instruction'] != {}:
            instruction_dict = self.item_to_dict(question_info['Instruction']['Agency'], question_info['Instruction']['ID'])
            df_question['Instruction_URN'] = instruction_dict['InstructionURN']
            df_question['Instruction'] = instruction_dict['InstructionText']
        else:
            df_question['Instruction_URN'] = None
            df_question['Instruction'] = None

        if QI_response_type == 'CodeList':
            code_result = self.item_to_dict(AgencyId, question_info['Response']['CodeList_ID'])
            code_list_sourceId = code_result['UserID']
            code_list_label = code_result['Label']

            code_list = code_result['Code']
            df = pd.DataFrame(columns=['response_type', 'Value', 'Name', 'ID', 'Label'])
            for c in code_list:
                category_dict = self.item_to_dict(c['CategoryReference']['Agency'], c['CategoryReference']['ID'])
                df = df.append({'response_type': 'CodeList',
                                        'Value': c['Value'],
                                         'Name': category_dict['Name'],
                                           'ID': category_dict['UserID'],
                                        'Label': category_dict['Label']
                               }, ignore_index=True)

            df['code_list_URN'] = question_info['Response']['code_list_URN']
            df['code_list_sourceId'] = code_list_sourceId
            df['code_list_label'] = code_list_label
            df['Order'] = df.index + 1
            df['QuestionURN'] = question_info['QuestionURN']
            df['QuestionItemName'] = question_info['QuestionItemName']

            df_question['response'] = code_list_label
            df_question['response_domain'] = question_info['Response']['code_list_URN']

        elif QI_response_type == 'Text':
            data = [ [ question_info['QuestionURN'],
                       question_info['QuestionItemName'],
                       question_info['Response']['response_type'],
                       question_info['Response']['response_label'] ] ]
            df = pd.DataFrame(data, columns=['QuestionURN', 'QuestionItemName', 'response_type', 'Label'])

            df_question['response'] = question_info['Response']['response_label']

        elif QI_response_type == 'Numeric':
            data = [ [ question_info['QuestionURN'],
                       question_info['QuestionItemName'], 
                       question_info['Response']['response_type'], 
                       question_info['Response']['response_label'],
                       question_info['Response']['response_NumericType'],
                       question_info['Response']['response_RangeLow'],
                       question_info['Response']['response_RangeHigh'] ] ]
            df = pd.DataFrame(data, columns=['QuestionURN', 'QuestionItemName', 'response_type', 'Label', 'response_NumericType', 'response_RangeLow', 'response_RangeHigh'])

            df_question['response'] = question_info['Response']['response_label']

        elif QI_response_type == 'DateTime':
            data = [ [ question_info['QuestionURN'],
                       question_info['QuestionItemName'],
                       question_info['Response']['response_type'],
                       question_info['Response']['response_label'],
                       question_info['Response']['DateTypeCode'] ] ]
            df = pd.DataFrame(data, columns=['QuestionURN', 'QuestionItemName', 'response_type', 'Label', 'DateTypeCode'])

            df_question['response'] = question_info['Response']['response_label']

        else:
            print(QI_response_type)
            print(question_info['Response'])
            df = pd.DataFrame()

        return df_question, df


if __name__ == "__main__":
    raise RuntimeError("don't run this directly")

