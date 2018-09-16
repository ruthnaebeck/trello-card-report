import secrets
import trello
import json
import requests
import re

# Table to organize zendesk ticket assignees by id
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
    user_json = requests.get(url=get_ticket_url, auth=(secrets.zendesk_email, secrets.zendesk_password)).json()['user']
    return user_json['name']
  except:
    return 'get_zendesk_user error'

def get_zendesk_ticket(ticket_id):
  try:
    get_ticket_url = 'https://datadog.zendesk.com/api/v2/tickets/%s.json' % (ticket_id)
    ticket_json = requests.get(url=get_ticket_url, auth=(secrets.zendesk_email, secrets.zendesk_password)).json()['ticket']
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

def open_zendesk_tickets(ticket_list):
    # open_tickets_url = str(
    #     'https://datadog.zendesk.com/api/v2/tickets/update_many.json?ids=%s' %
    #     (','.join(ticket_list),)
    # )
    # parms = json.dumps({'ticket': {'status': 'open'}})
    # print('opening tickets: %s' % (','.join(ticket_list),))
    # resp = requests.put(
    #     url=open_tickets_url,
    #     auth=(secrets.zendesk_email, secrets.zendesk_password),
    #     data=parms,
    #     headers={'content-type': 'application/json'}
    # ).text
    # return resp
    print('open_zendesk_tickets')
