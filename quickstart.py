from __future__ import print_function
import os.path

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint

# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
SCOPES = scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

# The ID of a sample document.
# DOCUMENT_ID = '195j9eDD3ccgjQRttHhJPymLJUCOUjs-jmwTrekvdjFE' # Google
DOCUMENT_ID = '1TJN0i6htLCMdKi92TBLIObLdZJvW0vGE3ewMGFqEIjo' # ITC
# DOCUMENT_ID = 1C3n7j-xJ2mabn7qDSGZ5YJD9WFwVHJ11naQbODd2tVw # Me
BTCRISK = '0'
BTCPRICE = '0'
BTCCHANGE = ''
ETHRISK = '0'
ETHPRICE = '0'
ETHCHANGE = ''

def main():
    # for x in range(1):
    try:
        update()
    except:
        print('Failed to fetch from Google Sheets')
        return
    print('-------------')
    print('BTC: ' + BTCPRICE + '\t' + BTCRISK + '\t :\t1h: ' + BTCCHANGE[0] + ' \t24h: ' + BTCCHANGE[1] + ' \t1w: ' + BTCCHANGE[2])
    print('ETH: ' + ETHPRICE + '\t' + ETHRISK + '\t :\t1h: ' + ETHCHANGE[0] + ' \t24h: ' + ETHCHANGE[1] + ' \t1w: ' + ETHCHANGE[2])
    print('-------------')

        # insertRow = ["hello", 5, "red", "blue"]
        # sheet.add_rows(insertRow, 4)  # Insert the list as a row at index 4
        # sheet.update_cell(2,2, "CHANGED")  # Update one cell
        # numRows = sheet.row_count  # Get the number of rows in the sheet

def update():
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    # sheet = client.open("python").sheet1  # Open the spreadhseet
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1TJN0i6htLCMdKi92TBLIObLdZJvW0vGE3ewMGFqEIjo/htmlview?pru=AAABe9P3B5w*EswS1LYYAD73MTMk3ElEyw#gid=272823807').sheet1

    data = sheet.get_all_records()  # Get a list of all records
    global BTCPRICE
    BTCPRICE = sheet.cell(6,2).value  # Get the value of a specific cell
    global BTCRISK
    BTCRISK = sheet.cell(6,4).value
    global BTCCHANGE
    BTCCHANGE = sheet.cell(6,8).value, sheet.cell(6,9).value, sheet.cell(6,10).value

    global ETHPRICE
    ETHPRICE = sheet.cell(7,2).value
    global ETHRISK
    ETHRISK = sheet.cell(7,4).value
    global ETHCHANGE
    ETHCHANGE = sheet.cell(7,8).value, sheet.cell(7,9).value, sheet.cell(7,10).value


# def main():
#     """Shows basic usage of the Docs API.
#     Prints the title of a sample document.
#     """
#     creds = None
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())

#     service = build('docs', 'v1', credentials=creds)

#     # Retrieve the documents contents from the Docs service.
#     document = service.documents().get(documentId=DOCUMENT_ID).execute()

#     print('The title of the document is: {}'.format(document.get('title')))


if __name__ == '__main__':
    main()