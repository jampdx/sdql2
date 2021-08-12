import sys
from PyQt4.QtCore import QUrl, SIGNAL, QTimer
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import QWebPage, QWebView



class WebPage(QWebPage):
    """
    QWebPage that prints Javascript errors to stderr.
    """
    def javaScriptConsoleMessage(self, message, lineNumber, sourceID):
        sys.stderr.write('Javascript error at line number %d\n' % lineNumber)
        sys.stderr.write('%s\n' % message)
        sys.stderr.write('Source ID: %s\n' % sourceID)
# this has a high failure/hang rate that is hard to figure out due, presumably to ajax: access by hand or via manage.py
class CoversScrapeBot(QApplication):
    def __init__(self, argv,url='', write_file_name='/tmp/dc.tmp',show_window=False,wait_for_ajax=20):
        super(CoversScrapeBot, self).__init__(argv)
        self.url = url
        self.write_file_name=write_file_name
        self.wait_for_ajax = wait_for_ajax
        self.web_view = QWebView()
        self.web_page = WebPage()
        self.web_view.setPage(self.web_page)
        if show_window is True:
            self.web_view.show()
        self.connect(self.web_view, SIGNAL("loadFinished(bool)"),
            self.load_finished)
        self.set_load_function(None)

    def evalJS(self, date):
        #js = js_for_date(date)
        #js = js_for_odds()
        js = "fn();"
        print "evalJS",js
        self.set_load_function(self.rest,date)
        #js = ''
        print "set load f"
        #current_frame = self.web_view.page().currentFrame()
        #current_frame.evaluateJavaScript(js) # doing twice used to magically  work, now an error.
        #time.sleep(2)
        #self.web_page.currentFrame().load(QUrl(url_for_date(date)))

        #current_frame.evaluateJavaScript(js)
        self.web_view.page().currentFrame().evaluateJavaScript(js)

    def load_finished(self, ok):
        self.load_function(*self.load_function_args, **self.load_function_kwargs)

    def save_page(self,date):
        print "save_page for",date
        current_frame = self.web_page.currentFrame()
        open(self.write_file_name,'w').write(current_frame.toHtml())
        self.exit()

    def search(self, date):
        self.set_load_function(self.evalJS, date)
        self.web_page.currentFrame().load(QUrl(self.url))

    def rest(self,date):
        print "rest"
        QTimer.singleShot(self.wait_for_ajax*1000,lambda s=self.save_page,d=date:s(d))

    def set_load_function(self, load_function, *args, **kwargs):
        self.load_function = load_function
        self.load_function_args = args
        self.load_function_kwargs = kwargs
