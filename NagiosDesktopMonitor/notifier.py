'''
Created on Apr 29, 2015

@author: b3p
'''
from window import NagiosDetailWindow
from gi.repository import Gtk
from gi.repository import Notify
from gi.repository import GLib

try:
    from gi.repository import AppIndicator3 as AppIndicator
except:
    from gi.repository import AppIndicator

import sys
import json
import urllib.request
import datetime
import threading
import collections


class NagiosIndicator:
    def __init__(self, root):
        self.app = root
        self.ind = AppIndicator.Indicator.new(
                    self.app.name,
                    "dialog-information",
                    AppIndicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status (AppIndicator.IndicatorStatus.ACTIVE)
        self.menu = Gtk.Menu()
        item = Gtk.MenuItem()
        item.set_label("Details")
        item.connect("activate", self.cb_details, '')
        self.menu.append(item)

        item = Gtk.MenuItem()
        item.set_label("---")
        self.menu.append(item)

        item = Gtk.MenuItem()
        item.set_label("Exit")
        item.connect("activate", self.cb_exit, '')
        self.menu.append(item)

        self.menu.show_all()
        self.ind.set_menu(self.menu)

        self.detail_win = False

    def cb_exit(self, w, data):
        self.app.exit = True
        Gtk.main_quit()

    def cb_details(self, w, data):
        self.show_detail_window()

    def show_detail_window(self):
        if self.detail_win == False:
            self.detail_win = NagiosDetailWindow(self.app)
            print ("Created new window")
            self.detail_win.window.show_all()
        else:
            print ("Presenting window")
            self.detail_win.window.present()
        self.detail_win.update_content()


class NagiosMonitor():
    def __init__(self):
        #super().__init__()
        self.name = "Nagios Monitor"
        self.indicator = NagiosIndicator(self)

        self.changes = dict()
        self.last_fetch = dict()
        self.current_fetch = dict()

        self.fetch_date = ""
        self.is_fetching = False
        self.exit = False

        Notify.init("Nagios")
        print (Notify.get_server_caps())


    def run(self):
        self.getData()
        Gtk.main()

    def getData(self):
        if self.exit == False and self.is_fetching == False:
            self.is_fetching = True
            self.last_fetch = self.current_fetch
            self.current_fetch = dict()

            data = self.__loadJSONData()  
            for k in data["services"]:
                self.current_fetch[k] = data["services"][k]

            self.__compareData()
            self.is_fetching = False
            self.__showNotifications()
            threading.Timer(3, self.getData).start()

    def __loadJSONData(self):
        print ("Loading json.")
        response = urllib.request.urlopen("http://kjc-sv007/ninfo.php")
        self.fetch_date = "%s" % datetime.datetime.now()
        print(self.fetch_date)
        str_response = response.readall().decode('utf-8')
        data = collections.OrderedDict(sorted(json.loads(str_response).items()))
        response.close()
        return data

    def __compareData(self):
        print ("Comparing changes")
        self.changes = dict()
        for host in self.current_fetch:
            host_in_previous_fetch = host in self.last_fetch

            for service in self.current_fetch[host]:
                if "CRITICAL" in self.current_fetch[host][service]["plugin_output"] or "WARNING" in self.current_fetch[host][service]["plugin_output"]:
                    if host_in_previous_fetch == False or ("CRITICAL" not in self.last_fetch[host][service]["plugin_output"] and "WARNING" not in self.last_fetch[host][service]["plugin_output"]):
                        if host not in self.changes:
                            self.changes[host] = dict()
                        self.changes[host][service] = self.current_fetch[host][service]["plugin_output"]

    def __showNotifications(self):
        messageText = ""
        if len(self.changes) > 0:
            for host in self.changes:
                messageText += host + ":\n"
                for service in self.changes[host]:
                    messageText += service + ": " + self.changes[host][service] + "\n"
                messageText += "\n\n"

            Notify.init("Nagios")
            msg = Notify.Notification.new("Nagios", messageText, "dialog-information")
            msg.set_timeout(10000)
            msg.show()
            if not self.indicator.detail_win == False:
                self.indicator.detail_win.update_content()
        else:
            print ("No news.")

if __name__ == "__main__":
    app = NagiosMonitor()
    app.run()