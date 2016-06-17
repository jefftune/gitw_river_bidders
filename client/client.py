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

__PYTHON_VERSION__ = 'Python/%d.%d.%d' % (
    sys.version_info[0],
    sys.version_info[1],
    sys.version_info[2]
)

lock = Lock()
auction_count = 0
auction_balance_start = 500.00
auction_balance_converted = 0.00
auction_balance_spent = 0.00
auction_offer_count = 0
auction_won_count = 0
auction_conversion_count = 0

bidding_limit_spent = 0.00

def get_auction_balance():
    return float(round(auction_balance_start + auction_balance_converted - auction_balance_spent, 2))

def get_average_payout():
    if auction_won_count > 0:
        return float(round(auction_balance_converted / auction_won_count, 2))
    else:
        return 0

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


bidding_mode = "sleep"
bidding_mode_prev = None
bidding_bid = 0.00
bidding_product = ""
bidding_type = ""
bidding_limit = 0.00
bidding_winning = 0.00

def get_auction_limit():
    return float(round(bidding_limit - bidding_limit_spent, 2))


print(__PYTHON_VERSION__)

app = flask.Flask(__name__)

auction_data = {}
stats_imp_types = {}
stats_products = {}
stats_countries = {}
stats_products_countries = {}
stats_products_countries_types = {}

bid_choices = {}

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

    global auction_group_types
    global auction_group_countries
    global auction_group_segments
    global auction_group_products

    global bidding_mode
    global bidding_bid
    global bidding_field
    global bidding_value
    global bidding_limit
    global bid_choices
    global bidding_winning
    global auction_offer_count

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

        if None in params:
            flask.abort(400)

        bid_choice = bidding_mode

        bid = 0
        if bidding_mode == "sleep":
            bid = 0

        elif bidding_mode == 'fixed':
            bid = bidding_bid

        elif bidding_mode == 'winning':
            bidding_winning += 0.01
            bid = bidding_winning

        elif bidding_mode == 'auto':
            bid = float(round(get_average_payout(), 2))

        elif bidding_mode == 'random':
            bid = random.random()
            bid = float(round(bid, 2))

        elif bidding_mode == 'smart':
            product_country_type = '{},{},{}'.format(product, country, imp_type)
            product_country = '{},{}'.format(product, country)
            found_bid = False
            found_conversion = False
            if product_country_type in stats_products_countries_types and \
                    'prob' in stats_products_countries_types[product_country_type] and \
                    'ave_payout' in stats_products_countries_types[product_country_type]:
                found_conversion = True
                total_converted = \
                    stats_products_countries_types[product_country_type]['totalConverted']
                if total_converted >= 10:
                    found_bid = True
                    prob = stats_products_countries_types[product_country_type]['prob']
                    ave_payout = stats_products_countries_types[product_country_type]['ave_payout']

                    bid_choice += ":product_country_type"
                    bid = ave_payout * prob

            elif product_country in stats_products_countries and \
                    'prob' in stats_products_countries[product_country] and \
                    'ave_payout' in stats_products_countries[product_country]:
                found_conversion = True
                total_converted = \
                    stats_products_countries[product_country]['totalConverted']
                if total_converted >= 10:
                    found_bid = True
                    prob = stats_products_countries[product_country]['prob']
                    ave_payout = stats_products_countries[product_country]['ave_payout']

                    bid_choice += ":product_country"
                    bid = ave_payout * prob

            elif product in stats_products and \
                    'prob' in stats_products[product] and \
                    stats_products[product]['prob'] > 0 and \
                    'ave_payout' in stats_products[product]:
                found_conversion = True
                total_converted = stats_products[product]['totalConverted']

                if total_converted >= 10:
                    found_bid = True
                    prob = stats_products[product]['prob']
                    ave_payout = stats_products[product]['ave_payout']

                    bid_choice += ":product"
                    bid = ave_payout * prob

            elif country in stats_countries and \
                    'prob' in stats_countries[country] and \
                    'ave_payout' in stats_countries[country]:
                found_conversion = True
                total_converted = stats_countries[country]['totalConverted']
                if total_converted >= 10:
                    found_bid = True
                    prob = stats_countries[country]['prob']
                    ave_payout = stats_countries[country]['ave_payout']

                    bid_choice += ":country"
                    bid = ave_payout * prob

            else:
                bid_choice += ":winning"
                bidding_winning += 0.01
                if get_average_payout() > 0 and bidding_winning > get_average_payout():
                    bid_choice += ":reset"
                    bidding_winning = 0.01

                bid = bidding_winning

            if found_conversion:
                bidding_winning = 0.01
                if not found_bid:
                    bid_choice += ":reset"
                    bid = bidding_winning

        if bid_choice not in bid_choices:
            bid_choices[bid_choice] = 1
        else:
            bid_choices[bid_choice] += 1


        # TODO: Estimate conversion rate and expected payout to determine the value
        # of this impression. Store model state and your bid for future optimizations.
        # Bid <= the impression's value, or more if you're sneaky, reckless, or are
        # willing to pay extra for the information (as in poker).

        auction_count += 1
        auction_offer_count += 1

        offer_bid = float(round(bid, 2))
        
        if bid_choice != "sleep" and \
                imp_id not in auction_data:
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
                'offer_bid': offer_bid,
                'bid_choice': bid_choice
            }

        return flask.Response(json.dumps({"bid": bid}), mimetype='application/json')

@app.route('/won')
def won():
    global auction_data
    global auction_balance_spent
    global auction_won_count
    global bidding_limit_spent

    global bidding_mode
    global bidding_mode_prev
    global bidding_bid
    global bidding_product
    global bidding_type

    params = get_args_from_list((('impression_id', unicode),
                                          ('type', unicode),
                                          ('payout', float),
                                          ('winning_bid', float)))

    with lock:
        if None in params:
            flask.abort(400)
        imp_id, imp_type, payout, winning_bid = params

        bidding_limit_spent += winning_bid
        if get_auction_limit() <= 0:
            bidding_mode = 'sleep'

        if imp_id in auction_data:
            auction_data[imp_id]['won'] = True
            auction_data[imp_id]['winning_bid'] = winning_bid
            
            product = auction_data[imp_id]['product']
            country = auction_data[imp_id]['country']
            imp_type = auction_data[imp_id]['imp_type']
            
            # Calc the product count and prob.
            if product in stats_products:
                stats_products[product]['totalWon'] += 1
            else:
                stats_products[product] = {
                    'totalWon': 1,
                    'totalConverted': 0
                }

            stats_products[product]['prob'] = \
                float(stats_products[product]['totalConverted'] / (
                    stats_products[product]['totalWon'] * 1.0)
                )
        
            # Calc the country count and prob.
            if country in stats_countries:
                stats_countries[country]['totalWon'] += 1                    
            else:
                stats_countries[country] = {
                    'totalWon': 1,
                    'totalConverted': 0
                }

            stats_countries[country]['prob'] = \
                float(stats_countries[country]['totalConverted'] / (
                    stats_countries[country]['totalWon'] * 1.0)
                )
            
            # Calc the product and country count and prob.            
            product_country = '{},{}'.format(product, country)
            if product_country in stats_products_countries:
                stats_products_countries[product_country]['totalWon'] += 1
            else:
                stats_products_countries[product_country] = {
                    'totalWon': 1,
                    'totalConverted': 0
                }

            stats_products_countries[product_country]['prob'] = \
                float(stats_products_countries[product_country]['totalConverted'] / (
                    stats_products_countries[product_country]['totalWon'] * 1.0)
                )

            # Calc the product and country and type count and prob.
            product_country_stat = '{},{},{}'.format(product, country, imp_type)
            if product_country_stat in stats_products_countries_types:
                stats_products_countries_types[product_country_stat]['totalWon'] += 1
            else:
                stats_products_countries_types[product_country_stat] = {
                    'totalWon': 1,
                    'totalConverted': 0
                }

                stats_products_countries_types[product_country_stat]['prob'] = \
                    float(stats_products_countries_types[product_country_stat]['totalConverted'] / (
                        stats_products_countries_types[product_country_stat]['totalWon'] * 1.0)
                    )

        auction_balance_spent += winning_bid
        auction_won_count += 1

        # TODO: Update model state with the amount actually paid for the impression.
        # This will only be called if you won, and the winning bid will be 0.01 more
        # than the second-place bid. Possibly use this to modify your bidding strategy.

        return flask.Response(status=204)


@app.route('/conversion')
def conv():
    global auction_data
    global auction_balance_converted

    global bidding_mode
    global bidding_mode_prev
    global bidding_bid
    global bidding_product
    global bidding_type
    global auction_conversion_count

    global bidding_limit_spent

    params = get_args_from_list((('impression_id', unicode),
                                 ('type', unicode),
                                 ('payout', float)))

    with lock:
        if None in params:
            flask.abort(400)

        imp_id, imp_type, payout = params

        bidding_limit_spent -= payout

        if bidding_mode_prev is not None:
            bidding_mode = bidding_mode_prev
            bidding_mode_prev = None

        if imp_id in auction_data:
            auction_data[imp_id]['converted'] = True

            product = auction_data[imp_id]['product']
            country = auction_data[imp_id]['country']
            imp_type = auction_data[imp_id]['imp_type']
            
            # Calc the product prob and ave payout.
            if product in stats_products:
                if 'ave_payout' not in stats_products[product]:
                    stats_products[product]['ave_payout'] = payout

                if stats_products[product]['totalConverted'] == 0:
                    stats_products[product]['totalConverted'] = 1
                else:
                    ave_payout = stats_products[product]['ave_payout']
                    converted = stats_products[product]['totalConverted']
                    stats_products[product]['ave_payout'] = \
                        (ave_payout*converted + payout)/((converted + 1) * 1.0)
                    stats_products[product]['totalConverted'] += 1

            stats_products[product]['prob'] = \
                stats_products[product]['totalConverted'] / \
                (stats_products[product]['totalWon'] * 1.0)
            
            # Calc the country prob and ave payout.
            if country in stats_countries:
                if 'ave_payout' not in stats_countries[country]:
                    stats_countries[country]['ave_payout'] = payout

                if stats_countries[country]['totalConverted'] == 0:
                    stats_countries[country]['totalConverted'] = 1
                else:
                    ave_payout = stats_countries[country]['ave_payout']
                    converted = stats_countries[country]['totalConverted']
                    stats_countries[country]['ave_payout'] = \
                        (ave_payout*converted + payout)/((converted + 1) * 1.0)
                    stats_countries[country]['totalConverted'] += 1

            stats_countries[country]['prob'] = \
                stats_countries[country]['totalConverted'] / \
                (stats_countries[country]['totalWon'] * 1.0)
                
            # Calc the prod and country prob and ave payout.
            product_country = '{},{}'.format(product, country)
            if product_country in stats_products_countries:
                if 'ave_payout' not in stats_products_countries[product_country]:
                    stats_products_countries[product_country]['ave_payout'] = payout

                if stats_products_countries[product_country]['totalConverted'] == 0:
                    stats_products_countries[product_country]['totalConverted'] = 1
                else:
                    ave_payout = stats_products_countries[product_country]['ave_payout']
                    converted = stats_products_countries[product_country]['totalConverted']
                    stats_products_countries[product_country]['ave_payout'] = \
                        (ave_payout*converted + payout)/((converted + 1) * 1.0)
                    stats_products_countries[product_country]['totalConverted'] += 1

            stats_products_countries[product_country]['prob'] = \
                stats_products_countries[product_country]['totalConverted'] / \
                (stats_products_countries[product_country]['totalWon'] * 1.0)

            # Calc the prod and country prob and ave payout.
            product_country_type = '{},{},{}'.format(product, country, imp_type)
            if product_country_type in stats_products_countries_types:
                if 'ave_payout' not in stats_products_countries_types[product_country_type]:
                    stats_products_countries_types[product_country_type]['ave_payout'] = payout

                if stats_products_countries_types[product_country_type]['totalConverted'] == 0:
                    stats_products_countries_types[product_country_type]['totalConverted'] = 1
                else:
                    ave_payout = stats_products_countries_types[product_country_type]['ave_payout']
                    converted = stats_products_countries_types[product_country_type]['totalConverted']
                    stats_products_countries_types[product_country_type]['ave_payout'] = \
                        (ave_payout * converted + payout) / ((converted + 1) * 1.0)
                    stats_products_countries_types[product_country_type]['totalConverted'] += 1

            stats_products_countries_types[product_country_type]['prob'] = \
                stats_products_countries_types[product_country_type]['totalConverted'] / (
                    stats_products_countries_types[product_country_type]['totalWon'] * 1.0)

        auction_balance_converted += payout
        auction_conversion_count += 1

        # TODO: Update models for conversion rate and expected payout for the
        # demographics related to this impression. This will only be called if you
        # won the bid and the impression resulted in a conversion.

        return flask.Response(status=204)

@app.route('/auction')
def auction():
    global auction_data
    with lock:
        auction_stats = []
        for imp_id, auction_item in auction_data.items():
            auction_stats.append(auction_item)

        auction_stats_sorted = sorted(auction_stats, key=lambda k: k['index'])

        return flask.Response(json.dumps(auction_stats_sorted), mimetype='application/json')

@app.route('/stats')
def stats():
    global stats_products_countries
    global stats_products
    global stats_countries
    global stats_products_countries_types

    with lock:
        val = get_arg_by_name('stat', unicode)

        if val == 'country':
            stats = json.dumps(stats_countries)
        elif val == 'product':
            stats = json.dumps(stats_products)
        elif val == 'product_country':
            stats = json.dumps(stats_products_countries)
        else:
            all_stats = {
                'country': stats_countries,
                'product': stats_products,
                'product_country': stats_products_countries,
                'product_country_type': stats_products_countries_types
            }

            stats = json.dumps(all_stats)

        return flask.Response(stats, mimetype='application/json')

@app.route('/clear')
def clear():
    global auction_data
    with lock:
        auction_data = {}
        return flask.Response(status=200)

@app.route('/status')
def status():
    global bidding_mode
    global bidding_bid
    global bidding_product
    global bidding_type
    global bidding_limit
    global bidding_winning

    global auction_offer_count
    global auction_won_count
    global auction_conversion_count

    with lock:
        bidding = {
            'bidding_mode': bidding_mode,
            'bidding_bid': bidding_bid,
            'bidding_product': bidding_product,
            'bidding_type': bidding_type,
            'bidding_limit': bidding_limit
        }

        counts = {
            "offers": auction_conversion_count,
            "won": auction_won_count,
            "conversion": auction_conversion_count
        }

        balances = {
            'current_limit':  get_auction_limit(),
            'current_balance': get_auction_balance(),
            'avg_payout': get_average_payout(),
            'current_cost': bidding_winning
        }

        status = {
            'counts': counts,
            'bidding': bidding,
            'balances': balances,
            'choices': bid_choices
        }

        return flask.Response(json.dumps(status), mimetype='application/json')

@app.route('/bidding')
def bidding():

    global bidding_mode
    global bidding_bid
    global bidding_product
    global bidding_type
    global bidding_limit

    global bidding_limit_spent

    with lock:
        params = get_args_from_list((("mode", unicode),
                                     ("bid", float),
                                     ("product", unicode),
                                     ("type", unicode),
                                     ("limit", float)))
        if None in params:
            flask.abort(400)

        mode, bid, product, type, limit = params

        bidding_mode = safe_str(mode)
        bidding_bid = safe_float(bid)
        bidding_product = safe_str(product)
        bidding_type = safe_str(type)
        bidding_limit = safe_float(limit)

        bidding_limit_spent = 0.0

        bidding = {
            'bidding_mode': bidding_mode,
            'bidding_bid': bidding_bid,
            'bidding_product': bidding_product,
            'bidding_type': bidding_type,
            'bidding_limit': bidding_limit
        }

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
