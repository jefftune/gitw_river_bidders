import sys
import json
import random
import traceback
import csv
import flask

__PYTHON_VERSION__ = 'Python/%d.%d.%d' % (
    sys.version_info[0],
    sys.version_info[1],
    sys.version_info[2]
)


print(__PYTHON_VERSION__)

app = flask.Flask(__name__)

data = {}

def validate_type(type_str):
    if type_str in ('CPC', 'CPA'):
        return type_str
    raise ValueError('type must be "CPC" or "CPA"')

def get_arg_by_name(name, cast_func):
    try:
        val = flask.request.args[name]
        return cast_func(val)
    except:
        traceback.print_exc(limit=2)
        return None

def get_args_from_list(name_casts):
    try:
        return [get_arg_by_name(name_cast[0], name_cast[1]) for name_cast in name_casts]
    except:
        traceback.print_exc(limit=2)
        return None


@app.route('/offer')
def offer():
    params = get_args_from_list((('impression_id', unicode),
                                          ('type', validate_type),
                                          ('payout', float),
                                          ('destination', unicode),
                                          ('country', unicode),
                                          ('segment', unicode)))
    if None in params:
        flask.abort(400)

    imp_id, imp_type, conv_payout, conv_dest, country, segment = params



    # TODO: Estimate conversion rate and expected payout to determine the value
    # of this impression. Store model state and your bid for future optimizations.
    # Bid <= the impression's value, or more if you're sneaky, reckless, or are
    # willing to pay extra for the information (as in poker).

    bid = random.random()

    if imp_id not in data:
        data[imp_id] = {
            'imp_type': imp_type,
            'conv_payout': conv_payout,
            'conv_dest': conv_dest,
            'country': country,
            'segment': segment,
            'won': False,
            'converted': False,
            'offer_bid': float(bid)
        }

    return flask.Response(json.dumps({"bid": bid}), mimetype='application/json')


@app.route('/won')
def won():
    params = get_args_from_list((('impression_id', unicode),
                                          ('type', unicode),
                                          ('payout', float),
                                          ('winning_bid', float)))
    if None in params:
        flask.abort(400)
    imp_id, imp_type, conv_payout, winning_bid = params

    if imp_id in data:
        data[imp_id]['won'] = True
        data[imp_id]['winning_bid'] = winning_bid

    # TODO: Update model state with the amount actually paid for the impression.
    # This will only be called if you won, and the winning bid will be 0.01 more
    # than the second-place bid. Possibly use this to modify your bidding strategy.

    return flask.Response(status=204)


@app.route('/conversion')
def conv():
    params = get_args_from_list((('impression_id', unicode),
                                          ('type', unicode),
                                          ('payout', float)))
    if None in params:
        flask.abort(400)
    imp_id, imp_type, conv_payout = params

    if imp_id in data:
        data[imp_id]['converted'] = True

    # TODO: Update models for conversion rate and expected payout for the
    # demographics related to this impression. This will only be called if you 
    # won the bid and the impression resulted in a conversion.

    return flask.Response(status=204)

@app.route('/stats')
def stats():
    return flask.Response(json.dumps(data), mimetype='application/json')

if __name__ == '__main__':
    print('App Begins')
    app.run(host='0.0.0.0', port=80, debug=True)
