# Trello Card Report for Support Escalation Boards

## Google Sheets Python API
NOTE - You may need to use your personal gmail account for these steps

- Create a Project at https://console.developers.google.com/cloud-resource-manager
- Add the Google Sheets API
- Add the Google Drive API
- Create Credentials
- Put the JSON file in the project directory
- Add the JSON file name to .gitignore
- Create a Google Sheet
- Share the Google Sheet with the `client_email` listed in the JSON file
- `pip install --upgrade google-api-python-client oauth2client`
- `pip install gspread`
