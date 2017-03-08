import re
import json

ABBREVS = {
    'MRKT': 'MARKET',
    'ORDR': 'ORDER',
    'LWS': 'LAWS',
    'BRCH': 'BREACH',
    'DT': 'DUTY'
}

with open('data/allegation_types.txt', 'r') as f:
    # convert types into regexes
    # since they are inconsistent in spacing around dashes
    types = [l for l in f.read().split('\n')]
    types_regs = [re.compile(t.replace('-', '- *')) for t in types]
descs = json.load(open('data/allegation_descs.json', 'r'))


def parse_allegations(a):
    labels = []
    for t, r in zip(types, types_regs):
        if r.match(a) is not None:
            labels.append(t)
    if labels:
        return labels

    for t, desc in descs.items():
        if any(d in a for d in desc):
            labels.append(t)
    if labels:
        return labels

    # on a deadline so here are some handcrafted rules
    if 'VIOLATION' in a or 'VIOLATED' in a or \
            'FAILED TO COMPLY' in a or 'FAILURE TO COMPLY' in a:
        labels.append('RULE VIOLATION')
    if 'NON PAYMENT' in a or 'FAILED TO PAY' in a or 'FAILURE TO PAY' in a or ('FEE' in a and 'FAILURE' in a):
        labels.append('FAILURE TO PAY')
    if 'TRANSMIT' in a or 'FAILED TO PROPERLY NOTIFY' in a or 'NOT REPORTED' in a or 'FAILING TO REPORT' in a or 'NOT NOTIFY' in a or 'FAILED TO REPORT' in a or 'FAILURE TO REPORT' in a \
        or 'FAILED TO FILE' in a or 'FAILURE TO FILE' in a \
        or 'DISCLOSED' in a or 'DISCLOSURE' in a \
        or 'OMISSION' in a \
        or ('SUPPLYING' in a and 'STATEMENT' in a):
        labels.append('FAILURE TO REPORT')
    if 'INACCURATE' in a or 'INCORRECTLY REPORTED' in a or 'REPORTED INCORRECTLY' in a or \
            'SHOULD HAVE REPORTED' in a or 'IMPROPER FORM' in a or \
            'FAILED TO ACCURATELY REPORT' in a:
        labels.append('INCORRECTLY REPORTED')
    if 'FAILURE TO REGISTER' in a or ('REGISTRATION' in a and 'PENDING' in a) or \
            ('LICENSE' in a and ('WITHOUT' in a or 'FAILED' in a)) or \
            'REGISTRATION' in a or 'LICENSURE' in a or \
            'UNREGISTERED' in a or 'REGISTERED' in a:
        labels.append('ACTIVITY WHILE REGISTRATION PENDING')
    if 'DILIGENCE' in a:
        labels.append('FAILURE OF DUE DILIGENCE')
    if 'FAILURE TO RESPOND' in a or 'FAILED TO RESPOND' in a:
        labels.append('FAILURE TO RESPOND TO FINRA')
    if 'INACCURATE' in a and 'DATA' in a:
        labels.append('INACCURATE DATA')
    if 'MARKED' in a:
        labels.append('INCORRECT MARK')
    if 'CHARGED' in a:
        labels.append('IMPROPERLY CHARGED')
    if 'FAILED TO RECORD' in a:
        labels.append('FAILURE TO RECORD')
    if 'MISREPRESENTED' in a:
        labels.append('MISREPRESENTATION')
    if 'UNLICENSED' in a or 'LICENSE' in a:
        labels.append('OPERATING WITHOUT LICENSE OR IMPROPER LICENSE')
    if not labels:
        labels.append('OTHER')
    return labels
