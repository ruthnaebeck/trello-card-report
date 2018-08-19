import secrets
import trello
import leads
from zendesk import find_zendesk_url, get_zendesk_user, get_zendesk_ticket

import requests
import datetime as dt
import unicodedata
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(secrets.google_json_file, scope)
gc = gspread.authorize(credentials)
service = build('sheets', 'v4', http=credentials.authorize(Http()))

# Get workbook and worksheet
wb = gc.open_by_key(secrets.google_sheet_id)
wks = wb.worksheet('Report')

datadog_api = {}

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

def main_script():
  # Duplicate the Report worksheet
  # today = dt.datetime.today().strftime('%m-%d-%y')
  # DATA = {'requests': [
  #   {
  #       'duplicateSheet': {
  #           'sourceSheetId': int(wks.id),
  #           'insertSheetIndex': 0,
  #           'newSheetName': 'Report ' + today
  #       }
  #   }
  # ]}
  # service.spreadsheets().batchUpdate(
  #       spreadsheetId=secrets.google_sheet_id, body=DATA).execute()

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
            agent = zendesk_ticket['zAssigneeName']
            status = zendesk_ticket['zStatus']
            new_row.extend((agent, status, str(dt.datetime.strptime(zendesk_ticket['zLastUpdated'], '%Y-%m-%dT%H:%M:%SZ'))))
            add_to_datadog_api(b['tag'], l['tag'], 'zendesk_agent:' + remove_accents(agent.replace(' ', '_').lower()), 'zendesk_status:' + status)
          except KeyError:
            new_row.extend(('unknown', 'error', 'x'))
        else:
          new_row.extend(('no_ticket', 'missing', 'x'))

        # Append card / ticket to the table
        table.append(new_row)
      print('--------------------')

  # Add card / ticket info to the newly created worksheet
  # new_wks = wb.worksheet('Report ' + today)
  # update_sheet(new_wks, table)
  # print(table)
  print(datadog_api)
  print('Complete!')

main_script()
