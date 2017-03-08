data sources:

- <https://app.enigma.io/table/us.gov.sec.iapd.investment-advisers>
- <https://app.enigma.io/table/us.gov.irs.soi.eobmf>
- <https://app.enigma.io/table/enigma.licenses.liquor.us>

to geohash a dataset, edit `do_geohash.py` and change the `KEY` value to one of `['TAX_EXEMPT_ORGS', 'INVESTMENT_ADVISERS', 'LIQUOR_LICENSES']`.

To use an [AWS-hosted Tiger geocoder](https://github.com/bibanul/tiger-geocoder/wiki/Running-your-own-Geocoder-in-Amazon-EC2), set `USE_TIGER = True` and set `TIGER_SERVER` to the AWS instance address. It will not try to geocode a dataset of over 10,000 rows if you aren't using Tiger.

This will run across multiple processes to execute simultaneously requests; change `PROCESSES` to the number of cores you have available.

Once you have geocoded your datasets (or samples), run `group_by_geohash.py` to group the rows of each dataset by their geohash.