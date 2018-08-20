import secrets
import trello
import leads
from zendesk import find_zendesk_url, get_zendesk_user, get_zendesk_ticket
from sheets import update_sheet
from datadog_api import add_to_datadog_api, remove_accents, datadog_api

import requests
import datetime as dt
import gspread

# Google Sheets imports / settings
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(secrets.google_json_file, scope)
gc = gspread.authorize(credentials)
service = build('sheets', 'v4', http=credentials.authorize(Http()))

wb = gc.open_by_key(secrets.google_sheet_id)
wks = wb.worksheet('Report')

# Datadog API imports / settings
from datadog import initialize, api

options = {
    'api_key': secrets.datadog_api_key,
    'app_key': secrets.datadog_app_key
}

initialize(**options)

def main_script():
  # Duplicate the Report worksheet
  today = dt.datetime.today().strftime('%m-%d-%y')
  DATA = {'requests': [
    {
        'duplicateSheet': {
            'sourceSheetId': int(wks.id),
            'insertSheetIndex': 0,
            'newSheetName': 'Report ' + today
        }
    }
  ]}
  service.spreadsheets().batchUpdate(
        spreadsheetId=secrets.google_sheet_id, body=DATA).execute()

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
            if(isinstance(agent, str)):
              agent = u'unknown'
            new_row.extend((agent, status, str(dt.datetime.strptime(zendesk_ticket['zLastUpdated'], '%Y-%m-%dT%H:%M:%SZ'))))
            add_to_datadog_api(b['tag'], l['tag'], 'zendesk_agent:' + remove_accents(agent.replace(' ', '_').lower()), 'zendesk_status:' + status)
          except KeyError:
            new_row.extend(('unknown', 'error', 'x'))
            add_to_datadog_api(b['tag'], l['tag'], 'zendesk_agent:unknown', 'zendesk_status:error')
        else:
          new_row.extend(('no_ticket', 'missing', 'x'))
          add_to_datadog_api(b['tag'], l['tag'], 'zendesk_agent:no_ticket', 'zendesk_status:missing')

        # Append card / ticket to the table
        table.append(new_row)
      print('--------------------')

  # Add card / ticket info to the newly created worksheet
  new_wks = wb.worksheet('Report ' + today)
  update_sheet(new_wks, table)

  # Add metrics through datadog api
  metrics = []

  for attr, val in datadog_api.items():
    metrics.append(val)

  print(metrics)
  api.Metric.send(metrics)

  print('Complete!')

main_script()
