import sys
import json
import random
import traceback

import flask
from pprintpp import pprint
import logging

__PYTHON_VERSION__ = 'Python/%d.%d.%d' % (
    sys.version_info[0],
    sys.version_info[1],
    sys.version_info[2]
)

print('client')
print(__PYTHON_VERSION__)

app = flask.Flask(__name__)

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
   imp_id, imp_type, conv_payout, conv_dest, demo_country, demo_segment_id = params

   # TODO: Estimate conversion rate and expected payout to determine the value
   # of this impression. Store model state and your bid for future optimizations.
   # Bid <= the impression's value, or more if you're sneaky, reckless, or are
   # willing to pay extra for the information (as in poker).

   bid = random.random()

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

   # TODO: Update models for conversion rate and expected payout for the
   # demographics related to this impression. This will only be called if you 
   # won the bid and the impression resulted in a conversion.

   return flask.Response(status=204)

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=80, debug=True)
