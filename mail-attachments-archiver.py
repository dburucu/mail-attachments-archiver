#!/usr/bin/env python3

# 
# mail-attachments-archiver
# Author: Enrico Cambiaso
# Email: enrico.cambiaso[at]gmail.com
# GitHub project URL: https://github.com/auino/mail-attachments-archiver
# 
# Additional modifications by
# Author: Ben Blasdell
# Email: ben@fiter.org
# GitHub project URL: https://github.com/johnbenclark/mail-attachments-archiver
#
# Additional modifications by
# Author: David Rickett
# Email: david@va7eex.ca
# GitHub project URL: https://github.com/va7eex/mail-attachments-archiver
#


# libraries import
import email
import email.header
import imaplib
import os
import time
import re
import json
import argparse

class mail-attachments-archiver()

    def __init__(self, imap_file, config_file):
        
        # Check command line arguments
        if not os.path.isfile(imap_file):
            raise FileNotFoundError("IMAP connection file missing.")
        if not os.path.isfile(config_file):
            raise FileNotFoundError("Configuration file missing.")

        # IMAP server connection configuration
        with open(imap_file, "r") as f:
            imap_conn = json.load(f)
            if not 'server' in imap_conn:
                raise ValueError("IMAP connection file missing server.")
            if not 'user' in imap_conn:
                raise ValueError("IMAP connection file missing user.")
            if not 'password' in imap_conn:
                raise ValueError("IMAP connection file missing password.")

        self.USER = imap_conn['user']
        self.PWD = imap_conn['password']
        self.IMAPSERVER = imap_conn['server']

        # storage/archive capabilities configuration
        with open(config_file, "r") as f:
            cfg = json.load(f)
            if not 'mappings' in cfg:
                raise ValueError("Configuration file missing mappings.")

        self.MAIL_MAPPINGS = cfg['mappings']

        # use gmail-specific trash flag when deleting
        self.USE_GMAIL_TRASH_FLAG_WITH_DELETE = cfg['use_gmail_trash_flag_with_delete']

        # only consider unread emails?
        self.FILTER_UNREAD_EMAILS = cfg['filter_unread_emails']

        # mark emails as read after their attachments have been archived?
        self.MARK_AS_READ = cfg['mark_as_read']

        # delete emails after their attachments have been archived?
        self.DELETE_EMAIL = cfg['delete_email']

        # if no attachment is found, mark email as read?
        self.MARK_AS_READ_NOATTACHMENTS = cfg['mark_as_read_no_attachments']

        # if no attachment is found, delete email?
        self.DELETE_EMAIL_NOATTACHMENTS = cfg['delete_email_no_attachments']

        # if no match is found (on MAIL_MAPPINGS), mark email as read?
        self.MARK_AS_READ_NOMATCH = cfg['mark_as_read_no_match']

        # if no match is found (on MAIL_MAPPINGS), delete email?
        self.DELETE_EMAIL_NOMATCH = cfg['delete_email_no_match']

    # source: https://stackoverflow.com/questions/12903893/python-imap-utf-8q-in-subject-string
    def decode_mime_words(self, s):
        return u''.join(word.decode(encoding or 'utf8') if isinstance(word, bytes) else word for word, encoding in email.header.decode_header(s))

    # source: https://stackoverflow.com/questions/41395745/deleting-an-email-using-imaplib-gmail
    def flag_delete(self, m, emailid):
        if self.USE_GMAIL_TRASH_FLAG_WITH_DELETE:
            m.store(emailid,'X-GM-LABELS','\\Trash')
        m.store(emailid,'+FLAGS','\\Deleted')

    def flag_seen(self, m, emailid):
        m.store(emailid,'+FLAGS','\\Seen')

    def get_mail(self):
        # connecting to the IMAP serer
        m = imaplib.IMAP4_SSL(self.IMAPSERVER)
        m.login(self.USER, self.PWD)
        # use m.list() to get all the mailboxes
        m.select("INBOX") # here you a can choose a mail box like INBOX instead

        # you could filter using the IMAP rules here
        # check http://www.example-code.com/csharp/imap-search-critera.asp)
        searchstring = 'ALL'
        if self.FILTER_UNREAD_EMAILS: searchstring = 'UNSEEN'
        resp, items = m.search(None, searchstring)
        items = items[0].split() # getting the mails id
        for emailid in items:
            # fetching the mail, "(RFC822)" means "get the whole stuff", but you can ask 
            # for headers only, etc
            resp, data = m.fetch(emailid, "(RFC822)")
            # getting the mail content
            email_body = data[0][1]
            # parsing the mail content to get a mail object
            mail = email.message_from_bytes(email_body)
            # check if any attachments at all
            if mail.get_content_maintype() != 'multipart':
                # marking as read and delete, if necessary
                if self.MARK_AS_READ_NOATTACHMENTS: flag_seen(m, emailid)
                if self.DELETE_EMAIL_NOATTACHMENTS: flag_delete(m, emailid)
                continue
            # checking sender
            sender = mail['from'].split()[-1]
            senderaddress = re.sub(r'[<>]','', sender)
            # checking receiver
            receiver = mail['to'].split()[-1]
            receiveraddress = re.sub(r'[<>]', '', receiver)
            # print some stuff
            print("<"+str(mail['date'])+"> "+
                  " from: "+str(mail['from'])+
                  "; to: "+str(mail['to'])+
                  "; subject: "+str(mail['subject']))
            # check if subject is allowed
            subject = mail['subject']
            # find matching rule
            outputrule = None
            for el in self.MAIL_MAPPINGS:
                if el['filter_sender'] and (not (senderaddress.lower() in el['senders'])): continue
                if el['filter_receiver'] and (not (receiveraddress.lower() in el['receivers'])): continue
                for sj in el['subject']:
                    if str(sj).lower() in str(subject).lower(): outputrule = el
            if outputrule == None: # no match is found
                # marking as read and delete, if necessary
                if self.MARK_AS_READ_NOMATCH: flag_seen(m, emailid)
                if self.DELETE_EMAIL_NOMATCH: flag_delete(m, emailid)
                continue
            outputdir = outputrule['destination']
            # we use walk to create a generator so we can iterate on the parts and 
            # forget about the recursive headach
            for part in mail.walk():
                # multipart are just containers, so we skip them
                if part.get_content_maintype() == 'multipart':
                    # marking as read and delete, if necessary
                    if self.MARK_AS_READ: flag_seen(m, emailid)
                    if self.DELETE_EMAIL: flag_delete(m, emailid)
                    continue
                # is this part an attachment?
                if part.get('Content-Disposition') is None:
                    # marking as read and delete, if necessary
                    if self.MARK_AS_READ: flag_seen(m, emailid)
                    if self.DELETE_EMAIL: flag_delete(m, emailid)
                    continue
                filename = part.get_filename()
                counter = 1
                # if there is no filename, we create one with a counter to avoid 
                # duplicates
                if not filename:
                    filename = 'part-%03d%s' % (counter, 'bin')
                    counter += 1
                # getting mail date
                if outputrule['add_date']:
                    d = mail['Date']
                    ss = [ ' +', ' -' ]
                    for s in ss:
                        if s in d: d = d.split(s)[0]
                    maildate = time.strftime('%Y%m%d', time.strptime(d, '%a, %d %b %Y %H:%M:%S'))
                    filename = maildate+'_'+filename
                filename = decode_mime_words(u''+filename)
                att_path = os.path.join(outputdir, filename)
                # check if output directory exists
                if not os.path.isdir(outputdir): os.makedirs(outputdir)
                # check if its already there
                if not os.path.isfile(att_path):
                    try:
                        print('Saving to', str(att_path))
                        # finally write the stuff
                        fp = open(att_path, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                        # marking as read and delete, if necessary
                        if self.MARK_AS_READ: flag_seen(m, emailid)
                        if self.DELETE_EMAIL: flag_delete(m, emailid)
                    raise: pass
        # Expunge the items marked as deleted... (Otherwise it will never be actually 
        # deleted)
        if self.DELETE_EMAIL: m.expunge()
        # logout
        m.logout()

if __name__ == "__main__":
   # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Mail attachments archiver'
    )
    parser.add_argument(
        '--imap',
        dest='imap',
        required=True,
        help='path to JSON IMAP connection file'
    )
    parser.add_argument(
        '--config',
        dest='config',
        required=True,
        help='path to JSON configuraiton file'
    )
    args = parser.parse_args()

    maa = mail-attachments-archiver(args.imap,args.config)
    maa.get_mail()