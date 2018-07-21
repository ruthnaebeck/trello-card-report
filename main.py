import trello
import requests

def find_zendesk_url(card_id):
  try:
    attach_json = requests.request('GET', trello.url_cards + card_id + '/attachments' + trello.tokens).json()
    if len(attach_json):
      for a in attach_json:
        if a['url'].startswith('https://datadog.zendesk.com/agent/tickets/'):
          return a['url']
  except:
    return 'An error occurred'
  return 'No attachments found'

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
          'zendeskLink': find_zendesk_url(c['id'])
        })

  print(trello.trello_boards)

main_script()
