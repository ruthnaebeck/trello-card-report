import authenticate
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

def get_zendesk_ticket(ticket_id):
  try:
    get_ticket_url = 'https://datadog.zendesk.com/api/v2/tickets/%s.json' % (ticket_id)
    ticket_json = requests.get(url=get_ticket_url, auth=(authenticate.zendesk_email, authenticate.zendesk_password)).json()['ticket']
    ticket_parts = {
      'zAssigneeId': ticket_json['assignee_id'],
      'zStatus': ticket_json['status'],
      'zLastUpdated': ticket_json['updated_at']
    }
    print(ticket_parts)
    return ticket_parts
  except:
    return 'An error occurred'

def get_trello_cards():
  for b in trello.trello_boards:
    for l in b['lists']:
      list_json = requests.request('GET', trello.url_lists + l['id'] + '/cards' + trello.tokens).json()
      for c in list_json:
        zendesk_url = find_zendesk_url(c)
        zendesk_id = zendesk_url.split('/').pop()
        if len(zendesk_id) <= 6:
          zendesk_ticket = get_zendesk_ticket(zendesk_id)
        l['cards'].append({
          'tName': c['name'],
          'id': c['id'],
          'tLastUpdated': c['dateLastActivity'],
          'tUrl': c['shortUrl'],
          'zUrl': zendesk_url
        })
  # print(trello.trello_boards)

def main_script():
  get_trello_cards()
  # get_zendesk_ticket('125226')

main_script()
