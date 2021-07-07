import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from datetime import datetime

URL = 'https://www.ozbargain.com.au/deals'
EMAIL_LOGIN = '' # ADD EMAIL HERE - used to send emails to people in ContactsList.txt
EMAIL_PW = '' # ADD EMAIL PW HERE
CONTACT_LIST_FILE = 'ContactsList.txt'
MESSAGE_TEMPLATE_FILE = 'EmailTemplate.txt'

def get_contacts(contacts_file):
    names = []
    emails = []
    keywords_emails = {}
    with open(contacts_file, 'r', encoding='utf-8') as contacts_file:
        for line in contacts_file:
            contact_info = line.split(' ')
            names.append(contact_info[0])
            emails.append(contact_info[1])
            for keyword in contact_info[2].split(','):
                if keyword in keywords_emails:
                    keywords_emails[keyword.lower()].append(contact_info[1])
                else:
                    keywords_emails[keyword.lower()] = [contact_info[1]]

    return names,emails,keywords_emails

def get_message_template(template_file):
    with open(template_file, 'r', encoding='utf-8') as template_file:
        template = template_file.read()
    return template

def send_email_noName(smtp_connection, keyword, email, template, post_title, deal_link):
        msg = MIMEMultipart()       # create a message

        # add in the actual person name to the message template
        message = Template(template).substitute(KEYWORD=keyword, POST_TITLE=post_title, DEAL_LINK=deal_link)

        # setup the parameters of the message
        msg['From']=EMAIL_LOGIN
        msg['To']=email
        msg['Subject']="A new ozbargain deal you've been looking for has been posted!"

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier.
        smtp_connection.send_message(msg)
        del msg

# returns a logged in smtp connection
def smtp_connect():
    s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    s.starttls()
    s.login(EMAIL_LOGIN, EMAIL_PW)
    return s

def smtp_send(smtp_connection, keyword, email, template, title, deal_link):
    try:
        send_email_noName(smtp_connection, keyword, email, template, title, deal_link)
        print("email sent")
        with open('log.txt', 'a') as f:
            f.write(str(datetime.now()) + " | sent email to: " + email + " | Deal title: " + title + "\n")
    except Exception as e:
        print('exception has occurred', e)
        s = smtp_connect()
        smtp_send(s, keyword, email, template, title, deal_link)


if __name__ == '__main__':
    print("Starting scraper")
    seen_deals = []
    s = smtp_connect()

    # get list of email contacts and message template to send them notifications
    names,emails,keywords_emails = get_contacts(CONTACT_LIST_FILE)
    template = get_message_template(MESSAGE_TEMPLATE_FILE)

    # populating the first iteration of seen_deals
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    dealsContainer = soup.find(id='is0')
    deal_posts = dealsContainer.find_all('div', class_="node node-ozbdeal node-teaser")
    for deal in deal_posts:
        title = deal.find('h2', class_="title")
        seen_deals.append(title.text)
    print("populated first iteration of seen_deals")

    while True:
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        dealsContainer = soup.find(id='is0') # class that contains all the deals on the page
        deal_posts = dealsContainer.find_all('div', class_="node node-ozbdeal node-teaser")
        new_deals = []
        for deal in deal_posts:
            title = deal.find('h2', class_="title")
            new_deals.append(title.text)
            if title.text not in seen_deals:
                for keyword in keywords_emails:
                    if keyword in title.text.lower():
                        link_id = str(deal.find('a', href=True)['href']).split('/')[-1]
                        deal_link = 'www.ozbargain.com.au/node/' + link_id
                        for email in keywords_emails[keyword]:
                            smtp_send(s, keyword, email, template, title.text, deal_link)

        seen_deals = new_deals
        time.sleep(10)