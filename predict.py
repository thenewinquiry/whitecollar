"""
trains the white collar crime model
and generates predictions
"""

import re
import json
import random
import geohash
import pandas as pd
from copy import deepcopy
from collections import defaultdict
from parse import parse_allegations
from sklearn.multiclass import OneVsRestClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer, normalize
from sklearn.model_selection import cross_val_score

# geohash precision
PRECISION = 7

# for extracting fine amounts
FINE_RE = re.compile('[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?')

# bin fines
FINE_BUCKETS = [
    10000,
    100000,
    500000,
    1000000,
    5000000,
    10000000,
    100000000
]

# spotcrime types
CRIME_TYPES = [
    'Arrest',
    'Arson',
    'Assault',
    'Burglary',
    'Other',
    'Robbery',
    'Shooting',
    'Theft',
    'Vandalism'
]

# collapse some allegation types to the same type
ALLEGATION_MAP = {
    'ACTIVITY WHILE REGISTRATION PENDING': 'OPERATING WITHOUT LICENSE OR IMPROPER LICENSE',
    'ACCOUNT ACTIVITY-OTHER': 'OTHER',
    'ACCOUNT RELATED-OTHER': 'OTHER',
    'FAILURE TO SUPERVISE THE SALE OF AUCTION RATE SECURITIES': 'ACCOUNT RELATED-FAILURE TO SUPERVISE',
    'FAILURE TO REPORT': 'FAILURE TO REPORT OR INCORRECT REPORTING',
    'INCORRECTLY REPORTED': 'FAILURE TO REPORT OR INCORRECT REPORTING'
}


# prep dataset
defaults = {
    'finra': [],
    'fines': [],
    'liquor': 0,
    'bccrime': 0,
    'tax_exempt_orgs': 0,
    'investment_advisers': 0,
    'allegations': ['NONE']
}
defaults.update({k: 0 for k in CRIME_TYPES})
data = defaultdict(lambda: deepcopy(defaults))

print('preparing the data...')

# geohash finra locs
# and grab fine amounts
df = pd.read_csv('data/FINRA_mostly_geocoded_20170205.csv')
for i, r in df.iterrows():
    try:
        hash = geohash.encode(float(r['latitude']), float(r['longitude']), PRECISION)
        data[hash]['finra'].append(int(i))
        try:
            fines = FINE_RE.findall(r['sanctions_ordered'])
            fines = [int(f.replace(',', '').split('.')[0]) for f in fines]
            fine = max(fines) if fines else 0
        except TypeError:
            fine = 0
        data[hash]['fines'].append(fine)
        a = r['allegations']
        if not isinstance(a, str):
            allegations = ['NONE']
        else:
            allegations = parse_allegations(a)
        data[hash]['allegations'] = [ALLEGATION_MAP[a] if a in ALLEGATION_MAP else a for a in allegations]
    except ValueError:
        continue

# auxiliary predictors
gh_groups = json.load(open('data/geohash_groups.json', 'r'))
for hash, ids in gh_groups['INVESTMENT_ADVISERS'].items():
    data[hash]['investment_advisers'] = len(ids)
for hash, ids in gh_groups['LIQUOR_LICENSES'].items():
    data[hash]['liquor'] = len(ids)
for hash, ids in gh_groups['TAX_EXEMPT_ORGS'].items():
    data[hash]['tax_exempt_orgs'] = len(ids)

# spotcrime predictors
gh_crimes = json.load(open('data/crimes_per_geohash.json'))
for hash, crimes in gh_crimes.items():
    data[hash]['bccrime'] = sum(crimes.values())
    for k, v in crimes.items():
        data[hash][k] = v

# even out the datasets by incorporating negative samples
finra = [d for d in data.values() if d['finra']]
no_finra = [d for d in data.values() if not d['finra']]
no_finra = random.sample(no_finra, len(finra))

# process the dataset into a format for the model
features = ['investment_advisers', 'liquor', 'tax_exempt_orgs'] + CRIME_TYPES
def to_row(entry):
    has_finra = bool(entry['finra'])
    fines = entry['fines']
    fine = sum(fines)

    fine_bucket = len(FINE_BUCKETS)
    for i, val in enumerate(FINE_BUCKETS):
        if fine <= val:
            fine_bucket = i
            break
    return [entry[f] for f in features], has_finra, fine_bucket, entry['allegations']

# extract inputs and targets,
# w/ some final preprocessing
dataset = map(to_row, finra + no_finra)
X, y, y_fines, y_allegations = zip(*dataset)
X = normalize(X)

mlb = MultiLabelBinarizer()
y_allegations = mlb.fit_transform(y_allegations)
types = mlb.classes_

print('training the models and generating predictions...')

# generate predictions for geohashes we have data for
X_pred = []
predictions = defaultdict(dict)
hashes, feats = zip(*data.items())
for f in feats:
    r, _, _, _ = to_row(f)
    X_pred.append(r)
print('geohashes to predict:', len(X_pred))

# model to predict if crime does or doesn't happen
# we can get probabilities with
#   m.predict_prob(X)
print('Predict crime happens y/n')
m = RandomForestClassifier()
scores = cross_val_score(m, X, y, cv=5)
print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

m = RandomForestClassifier()
m.fit(X, y)
print('score:', m.score(X, y))
for f, im in zip(features, m.feature_importances_):
    print(f, '->', im)

print('>PREDICTING FINANCIAL CRIME...')
crime_probs = m.predict_proba(X_pred)
for i, prob in enumerate(crime_probs):
    predictions[hashes[i]]['crime'] = prob[1]
print('--------------')

# model to predict fine amount
# this is going to be awful
print('Predict fine amount')
m = RandomForestClassifier()

scores = cross_val_score(m, X, y_fines, cv=5)
print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

m.fit(X, y_fines)
print('score:', m.score(X, y_fines))

print('>PREDICTING CRIME FINES...')
fine_probs = m.predict_proba(X_pred)
for i, probs in enumerate(fine_probs):
    # the indices of these probs
    # match to the indices of `types`
    predictions[hashes[i]]['fine_bucket_p'] = probs.tolist()
print('--------------')

# model to predict allegation types
print('Predict crime types')
m = OneVsRestClassifier(RandomForestClassifier())

scores = cross_val_score(m, X, y_allegations, cv=5)
print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

m.fit(X, y_allegations)
print('score:', m.score(X, y_allegations))

print('>PREDICTING CRIME TYPES...')
type_probs = m.predict_proba(X_pred)
for i, probs in enumerate(type_probs):
    # the indices of these probs
    # match to the indices of `types`
    predictions[hashes[i]]['type_p'] = probs.tolist()
print('--------------')

print('saving predictions')
with open('PREDICTIONS.json', 'w') as f:
    json.dump({
        'predictions': predictions,
        'types': types.tolist()
    }, f)
print('crime predicted!')
