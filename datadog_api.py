import leads
import unicodedata

datadog_api = {}

def get_team_lead(a):
  try:
    return 'lead:' + leads.leads[a]
  except KeyError:
    return 'lead:unknown'

def add_to_datadog_api(b, l, a, s):
  key = b + l + a + s
  try:
    datadog_api[key]['points'] += 1
  except KeyError:
    lead = get_team_lead(a.split(':')[1])
    datadog_api[key] = {
      'metric': 'trello.card.count',
      'points': 1,
      'tags': [b, l, a, lead, s]
    }

def remove_accents(input_str):
  nfkd_form = unicodedata.normalize('NFKD', input_str)
  return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
