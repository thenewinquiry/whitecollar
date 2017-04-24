# White Collar Crime Early Warning System

This is a predictive policing app that targets high-level financial fraud, published for [_The New Inquiry_](https://thenewinquiry.com/) as part of [Issue #59: Abolish](https://thenewinquiry.com/magazine/abolish/).

Presented here is a script to train our model along with the processed data used to train it. Please refer to our [white paper](https://whitecollar.thenewinquiry.com/static/whitepaper.pdf) for more details.

View the app live at [whitecollar.thenewinquiry.com](https://whitecollar.thenewinquiry.com/).

## Usage

First install the requirements:

    pip install -r requirements.txt

Then, to generate a JSON file of predictions per geohash, run:

    python predict.py

This will train a series of models to generate the predictions (see the [white paper](https://whitecollar.thenewinquiry.com/static/whitepaper.pdf) for details)