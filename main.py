import trello
import requests
import re
import json

def find_zendesk_url(card):
  try:
    attach_json = requests.request('GET', trello.url_cards + card['id'] + '/attachments' + trello.tokens).json()
    if len(attach_json):
      for a in attach_json:
        if a['url'].startswith('https://datadog.zendesk.com/agent/tickets/'):
          return a['url']
    regex = r'https:\/\/datadog\.zendesk\.com\/agent\/tickets\/[0-9]*'
    card_str = json.dumps(card)
    searchObj = re.search(regex, card_str, re.M|re.I)
    if searchObj:
      return searchObj.group()
    else:
      return 'No Zendesk Ticket Found'
  except:
    return 'An error occurred'

def main_script():
  for b in trello.trello_boards:
    for l in b['lists']:
      list_json = requests.request('GET', trello.url_lists + l['id'] + '/cards' + trello.tokens).json()
      for c in list_json:
        l['cards'].append({
          'name': c['name'],
          'id': c['id'],
          'lastUpdated': c['dateLastActivity'],
          'cardLink': c['shortUrl'],
          'zendeskLink': find_zendesk_url(c)
        })

  print(trello.trello_boards)

main_script()
