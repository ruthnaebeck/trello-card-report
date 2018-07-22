import authenticate
import trello
import requests
import re
import json

assignees = {}

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
    return 'find_zendesk_url error'

def get_zendesk_user(user_id):
  try:
    get_ticket_url = 'https://datadog.zendesk.com/api/v2/users/%s.json' % (user_id)
    user_json = requests.get(url=get_ticket_url, auth=(authenticate.zendesk_email, authenticate.zendesk_password)).json()['user']
    return user_json['name']
  except:
    return 'get_zendesk_user error'

def get_zendesk_ticket(ticket_id):
  print(ticket_id)
  try:
    get_ticket_url = 'https://datadog.zendesk.com/api/v2/tickets/%s.json' % (ticket_id)
    ticket_json = requests.get(url=get_ticket_url, auth=(authenticate.zendesk_email, authenticate.zendesk_password)).json()['ticket']
    assignee_id = ticket_json['assignee_id']
    try:
      assignee_name = assignees[assignee_id]
    except KeyError:
      assignee_name = get_zendesk_user(assignee_id)
      assignees[assignee_id] = assignee_name
    return {
      'zAssigneeId': assignee_id,
      'zAssigneeName': assignee_name,
      'zStatus': ticket_json['status'],
      'zLastUpdated': ticket_json['updated_at']
    }
  except:
    print('get_zendesk_ticket error')
    return {}

def get_trello_cards():
  for b in trello.trello_boards:
    for l in b['lists']:
      list_json = requests.request('GET', trello.url_lists + l['id'] + '/cards' + trello.tokens).json()
      for c in list_json:
        zendesk_url = find_zendesk_url(c)
        zendesk_id = zendesk_url.split('/').pop()
        new_card = {
          'tName': c['name'],
          'id': c['id'],
          'tLastUpdated': c['dateLastActivity'],
          'tUrl': c['shortUrl'],
          'zUrl': zendesk_url
        }
        if len(zendesk_id) <= 6:
          zendesk_ticket = get_zendesk_ticket(zendesk_id)
          try:
            new_card['zAssigneeId'] = zendesk_ticket['zAssigneeId']
            new_card['zAssigneeName'] = zendesk_ticket['zAssigneeName']
            new_card['zStatus'] = zendesk_ticket['zStatus']
            new_card['zLastUpdated'] = zendesk_ticket['zLastUpdated']
          except KeyError:
            print(zendesk_id, 'No Zendesk Ticket Found')
        l['cards'].append(new_card)

def main_script():
  get_trello_cards()
  print('Complete!')

main_script()
