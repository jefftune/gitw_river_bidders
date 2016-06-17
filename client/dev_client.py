import sys
import json
import random
import traceback
import csv
import flask
from flask import make_response
import StringIO
import time
from threading import Lock
from pprintpp import pprint

__PYTHON_VERSION__ = 'Python/%d.%d.%d' % (
    sys.version_info[0],
    sys.version_info[1],
    sys.version_info[2]
)

lock = Lock()
auction_count = 0
auction_balance =

def safe_cast(val, to_type, default=None):
    if val is None:
        return default

    try:
        return to_type(val)
    except ValueError:
        return default


def safe_int(val):
    return safe_cast(val, int, 0)

def safe_str(val):
    return safe_cast(val, str, "")

def safe_float(val):
    return safe_cast(val, float, 0.0)

def safe_dict(val):
    return safe_cast(val, dict, {})

def safe_bool(val):
    return safe_cast(val, bool, {})


def safe_smart_cast(val):
    to_type = type(val)
    if to_type == str:
        return safe_str(val)
    if to_type == dict:
        return safe_dict(val)
    if to_type == int:
        return safe_int(val)
    if to_type == float:
        return safe_float(val)
    if to_type == bool:
        return safe_bool(val)

    return safe_str(str(val))

bidding = {
    "mode": "stop",
    "bid": 0.00,
    "field": "",
    "value": "",
    "limit": 0.00
}


print(__PYTHON_VERSION__)

app = flask.Flask(__name__)

auction_data = {}

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
    global auction_data
    global auction_balance
    global auction_count
    global bidding

    params = get_args_from_list((('impression_id', unicode),
                                          ('type', validate_type),
                                          ('payout', float),
                                          ('destination', unicode),
                                          ('country', unicode),
                                          ('segment', unicode)))

    with lock:

        if None in params:
            flask.abort(400)

        imp_id, imp_type, payout, product, country, segment = params


        if bidding["mode"] == "stop":
            bid = safe_float(0)
            return flask.Response(json.dumps({"bid": bid}), mimetype='application/json')

        if bidding["mode"] != 'fixed':
            bid = safe_float(bidding["bid"])
            return flask.Response(json.dumps({"bid": bid}), mimetype='application/json')


        # TODO: Estimate conversion rate and expected payout to determine the value
        # of this impression. Store model state and your bid for future optimizations.
        # Bid <= the impression's value, or more if you're sneaky, reckless, or are
        # willing to pay extra for the information (as in poker).

        bid = random.random()
        bid = float(round(bid, 2))

        auction_count += 1

        if imp_id not in auction_data:
            auction_data[imp_id] = {
                'index': auction_count,
                'imp_id': imp_id,
                'imp_type': imp_type,
                'payout': payout,
                'product': product,
                'country': country,
                'segment': segment,
                'won': False,
                'converted': False,
                'offer_bid': bid,
                'balance': float(round(auction_balance, 2))
            }

        return flask.Response(json.dumps({"bid": bid}), mimetype='application/json')


@app.route('/won')
def won():
    global auction_data
    global auction_balance

    global bidding

    params = get_args_from_list((('impression_id', unicode),
                                          ('type', unicode),
                                          ('payout', float),
                                          ('winning_bid', float)))

    with lock:
        if None in params:
            flask.abort(400)
        imp_id, imp_type, payout, winning_bid = params

        cost = winning_bid + 0.01
        auction_balance -= cost

        if bidding['limit'] > 0:
            bidding['limit'] -= cost
            if bidding['limit'] <= 0:
                bidding['limit'] = 0
                bidding['mode'] = 'stop'

        if imp_id in auction_data:
            auction_data[imp_id]['won'] = True
            auction_data[imp_id]['winning_bid'] = winning_bid
            auction_data[imp_id]['balance'] = float(round(auction_balance, 2))

        # TODO: Update model state with the amount actually paid for the impression.
        # This will only be called if you won, and the winning bid will be 0.01 more
        # than the second-place bid. Possibly use this to modify your bidding strategy.

        return flask.Response(status=204)


@app.route('/conversion')
def conv():
    global auction_data
    global auction_balance

    params = get_args_from_list((('impression_id', unicode),
                                 ('type', unicode),
                                 ('payout', float)))

    with lock:
        if None in params:
            flask.abort(400)
        imp_id, imp_type, payout = params

        auction_balance += payout
        bidding['limit'] += payout

        if imp_id in auction_data:
            auction_data[imp_id]['converted'] = True
            auction_data[imp_id]['balance'] = float(round(auction_balance, 2))

        # TODO: Update models for conversion rate and expected payout for the
        # demographics related to this impression. This will only be called if you
        # won the bid and the impression resulted in a conversion.

        return flask.Response(status=204)

@app.route('/stats')
def stats():
    with lock:
        auction_stats = []
        for imp_id, auction_item in auction_data.items():
            auction_stats.append(auction_item)

        auction_stats_sorted = sorted(auction_stats, key=lambda k: k['index'])

        return flask.Response(json.dumps(auction_stats_sorted), mimetype='application/json')

@app.route('/refresh')
def refresh():
    global auction_data
    with lock:
        auction_data = {}
        return flask.Response(status=200)

@app.route('/bidding')
def bidding():

    global bidding

    with lock:
        params = get_args_from_list((("mode", unicode),
                                     ("bid", float),
                                     ("field", unicode),
                                     ("value", unicode),
                                     ("limit", float)))

        bidding_mode, bidding_bid, bidding_field, bidding_value, bidding_limit = params

        bidding["mode"] = safe_str(bidding_mode)
        bidding["bid"] = safe_float(bidding_bid)
        bidding["field"] = safe_str(bidding_field)
        bidding["value"] = safe_str(bidding_value)
        bidding["limit"] = safe_cast(bidding_limit, float, -1)

        return flask.Response(json.dumps(bidding), mimetype='application/json')

@app.route('/download')
def download():
    with lock:
        si = StringIO.StringIO()
        cw = csv.writer(si)
        count = 0
        ts = time.time()
        auction_stats_filename = "auction_stats_{}.csv".format(int(ts))

        auction_stats = []
        for imp_id, auction_item in auction_data.items():
            auction_stats.append(auction_item)

        auction_stats_sorted = sorted(auction_stats, key=lambda k: k['index'])

        for auction_stat in auction_stats_sorted:
            if count == 0:
                header = auction_stat.keys()
                cw.writerow(header)

                count += 1
            cw.writerow(auction_stat.values())
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename={}".format(auction_stats_filename)
        output.headers["Content-type"] = "text/csv"
        return output

if __name__ == '__main__':
    print('App Begins')
    auction_balance = 500
    app.run(threaded=True, host='0.0.0.0', port=80, debug=True)
