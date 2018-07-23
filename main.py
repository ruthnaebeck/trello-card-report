import authenticate
import trello
import requests
import re
import json
import time
import datetime as dt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

assignees = {}
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(authenticate.google_json_file, scope)
gc = gspread.authorize(credentials)
wb = gc.open_by_key(authenticate.google_sheet_id)
wks = wb.worksheet('Report')

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

def main_script():
  print('--------------------')
  for b in trello.trello_boards:
    for l in b['lists']:
      list_json = requests.request('GET', trello.url_lists + l['id'] + '/cards' + trello.tokens).json()
      print(b['name'])
      print('--------------------')
      x = 0
      for c in list_json:
        x += 1
        print(str(x) + ' - ' + c['name'])
        zendesk_url = find_zendesk_url(c)
        zendesk_id = zendesk_url.split('/').pop()
        print('    Ticket #' + zendesk_id)
        new_row = [
          b['name'],
          l['name'],
          c['name'],
          c['shortUrl'],
          str(dt.datetime.strptime(c['dateLastActivity'], '%Y-%m-%dT%H:%M:%S.%fZ')),
          zendesk_url
        ]
        if len(zendesk_id) <= 6:
          zendesk_ticket = get_zendesk_ticket(zendesk_id)
          try:
            new_row.append(zendesk_ticket['zAssigneeName'])
            new_row.append(zendesk_ticket['zStatus'])
            new_row.append(str(dt.datetime.strptime(zendesk_ticket['zLastUpdated'], '%Y-%m-%dT%H:%M:%SZ')))
          except KeyError:
            print(zendesk_id, 'No Zendesk Ticket Found')
        print(new_row)
        wks.insert_row(new_row, index=2, value_input_option='USER_ENTERED')
      print('--------------------')
  print('Complete!')

main_script()
