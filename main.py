import authenticate
import trello
import requests
import re
import json
import time
import datetime as dt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(authenticate.google_json_file, scope)
gc = gspread.authorize(credentials)
service = build('sheets', 'v4', http=credentials.authorize(Http()))

# Get workbook and worksheet
wb = gc.open_by_key(authenticate.google_sheet_id)
wks = wb.worksheet('Report')

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

def numberToLetters(q):
  q = q - 1
  result = ''
  while q >= 0:
      remain = q % 26
      result = chr(remain+65) + result
      q = q//26 - 1
  return result

def colrow_to_A1(col, row):
    return numberToLetters(col)+str(row)

def update_sheet(ws, rows, left=1, top=2):
  print(rows)

  # number of rows and columns
  num_lines, num_columns = len(rows), len(rows[0])

  # selection of the range that will be updated
  cell_list = ws.range(
      colrow_to_A1(left,top)+':'+colrow_to_A1(left+num_columns-1, top+num_lines-1)
  )

  # modifying the values in the range
  for cell in cell_list:
    val = rows[cell.row-top][cell.col-left]
    print('val = ' + val)
    cell.value = val

  # update in batch
  ws.update_cells(cell_list)

# The trello_boards object could be built programmatically if boards and lists are named consistently. An example is below but is not used to pull this report.
def get_trello_boards():
  trello_boards = []
  boards_json = requests.request('GET', trello.url_members + trello.tokens).json()
  for b in boards_json:
    if b['name'].startswith('Support -'):
      lists_json = requests.request('GET', trello.url_boards + b['id'] + '/lists' + trello.tokens).json()
      for l in lists_json:
        if 'Waiting' in l['name']:
          trello_boards.append({
            'name': b['name'], 'id': b['id'], 'lists': [
              {'name': l['name'], 'id': l['id']}
            ]
          })
  return trello_boards

def main_script():
  # Duplicate the Report worksheet
  DATA = {'requests': [
    {
        'duplicateSheet': {
            'sourceSheetId': int(wks.id),
            'insertSheetIndex': 0,
            'newSheetName': 'Report ' + dt.datetime.today().strftime('%m-%d-%y')
        }
    }
  ]}
  service.spreadsheets().batchUpdate(
        spreadsheetId=authenticate.google_sheet_id, body=DATA).execute()

  # Collect Trello Card / Zendesk ticket info
  table = []
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
            new_row.extend((zendesk_ticket['zAssigneeName'], zendesk_ticket['zStatus'], str(dt.datetime.strptime(zendesk_ticket['zLastUpdated'], '%Y-%m-%dT%H:%M:%SZ'))))
          except KeyError:
            print(zendesk_id, 'No Zendesk Ticket Found')
            new_row.extend(('x', 'error', 'x'))
        else:
          new_row.extend(('x', 'missing', 'x'))

        # Append card / ticket to the table
        table.append(new_row)
      print('--------------------')

  # Add card / ticket info to Google Sheet
  update_sheet(wks, table)
  print('Complete!')

main_script()
