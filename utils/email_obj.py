#!/usr/bin/python
import mimetypes
from email import encoders

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase


def attachment(filename):
    """
    build attachment object
    """
    fd = open(filename, 'rb')
    mime_type, mime_encoding = mimetypes.guess_type(filename)
    if mime_encoding or (mime_type is None):
        mime_type = 'application/octet-stream'

    maintype, subtype = mime_type.split('/')

    if maintype == 'text':
        ret_val = MIMEText(fd.read(), _subtype=subtype)
    else:
        ret_val = MIMEBase(maintype, subtype)
        ret_val.set_payload(fd.read())
        encoders.encode_base64(ret_val)

    ret_val.add_header('Content-Disposition', 'attachment',
                       filename=filename.split('/')[-1])
    fd.close()
    return ret_val


class EmailObj(object):
    def __init__(self, server, user, pwd):
        self.server = server
        self.user = user
        self.pwd = pwd

    def send_mail(self, subject, msg_body, from_addr, to_addr, cc_addr='', attachments=None):
        msg = MIMEMultipart()
        msg['To'] = to_addr
        msg['From'] = from_addr
        msg['Cc'] = cc_addr
        msg['Subject'] = subject

        body = MIMEText(msg_body, _subtype='html', _charset='utf-8')
        msg.attach(body)

        if attachments is not None:
            for filename in attachments:
                msg.attach(attachment(filename))

        s = smtplib.SMTP(self.server)
        # s.set_debuglevel(True)
        s.ehlo()
        s.starttls()
        s.login(self.user, self.pwd)
        return s.sendmail(from_addr, cc_addr.split(",") + [to_addr], msg.as_string())

