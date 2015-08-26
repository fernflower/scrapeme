import logging

from six.moves import cStringIO as StringIO
import six

from email.utils import COMMASPACE, formatdate
from six.moves.email_mime_multipart import MIMEMultipart
from six.moves.email_mime_text import MIMEText
from six.moves.email_mime_base import MIMEBase
if six.PY2:
    from email.MIMENonMultipart import MIMENonMultipart
    from email import Encoders
else:
    from email.mime.nonmultipart import MIMENonMultipart
    from email import encoders as Encoders

from twisted.internet import defer, reactor, ssl
from twisted.mail.smtp import ESMTPSenderFactory

from scrapy import mail

logger = logging.getLogger(__name__)


class MailSender(mail.MailSender):
    """Introduced because of us-ascii only encoding in mime* at the moment.

    Not the best implementation, but will do as a temp fix
    """

    # copies the send method adding the encoding supplied via encoding param
    def send(self, to, subject, body, cc=None, attachs=(),
             mimetype='text/plain', _callback=None, charset="utf-8"):
        if attachs:
            msg = MIMEMultipart()
        else:
            msg = MIMENonMultipart(*mimetype.split('/', 1))
        msg['From'] = self.mailfrom
        msg['To'] = COMMASPACE.join(to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        rcpts = to[:]
        if cc:
            rcpts.extend(cc)
            msg['Cc'] = COMMASPACE.join(cc)

        if attachs:
            msg.attach(MIMEText(body))
            for attach_name, mimetype, f in attachs:
                part = MIMEBase(*mimetype.split('/'))
                part.set_payload(f.read())
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition',
                                'attachment; filename="%s"' % attach_name)
                msg.attach(part)
        else:
            msg.set_payload(body)

        if _callback:
            _callback(to=to, subject=subject, body=body, cc=cc,
                      attach=attachs, msg=msg)

        if self.debug:
            logger.debug('Debug mail sent OK: To=%(mailto)s Cc=%(mailcc)s '
                         'Subject="%(mailsubject)s" Attachs=%(mailattachs)d',
                         {'mailto': to, 'mailcc': cc, 'mailsubject': subject,
                          'mailattachs': len(attachs)})
            return

        # here a temporary encoding fix
        if charset:
            msg.set_charset(charset)
        dfd = self._sendmail(rcpts, msg.as_string())
        dfd.addCallbacks(self._sent_ok, self._sent_failed,
                         callbackArgs=[to, cc, subject, len(attachs)],
                         errbackArgs=[to, cc, subject, len(attachs)])
        reactor.addSystemEventTrigger('before', 'shutdown', lambda: dfd)
        return dfd
