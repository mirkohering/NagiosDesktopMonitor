from gi.repository import Gtk
import os


class NagiosDetailWindow():

    def __add_data_to_hosts_liststore(self):
        for host in self.app.current_fetch:
            for service in self.app.current_fetch[host]:
                color = ""
                plugin_output = self.app.current_fetch[host][service]["plugin_output"]
                service_state = self.app.current_fetch[host][service]["current_state"]
                if service_state == "0":
                    color = "#A9FFA3"
                elif service_state == "1":
                    color = "#FFFFA3"
                elif service_state == "2":
                    color = "#DE1B1B"
                else:
                    color = "#FFFFFF"

                self.hosts_liststore.append([host, service, plugin_output, color, service_state])

    def __init__(self, root):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.dirname(__file__) + "/GUI.glade")
        handlers = {"on_update_button_clicked": self.on_update_button_clicked,
                    "show_check_details": self.show_check_details,
                    "filter_button": self.on_selection_button_clicked}

        self.builder.connect_signals(handlers)

        self.window = self.builder.get_object("main_window")

        self.window.connect('destroy', self.quit)

        self.app = root

        #Creating the ListStore model
        self.hosts_liststore = Gtk.ListStore(str, str, str, str, str)
        #self.hosts_liststore.set_sort_func(0, self.sort_table, None)
        self.filter = self.hosts_liststore.filter_new()
        self.filter.set_visible_func(self.filter_func)
        self.filter_by = "status"
        self.current_filter = None        

        self.__add_data_to_hosts_liststore()

        #creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = self.builder.get_object("treeview_main")
        self.time_label = self.builder.get_object("menuitem_last_update")
        self.items_label = self.builder.get_object("menuitem_no_items")
        self.radio_filter_by_host = self.builder.get_object("menuitem_Host")
        self.radio_filter_by_service = self.builder.get_object("menuitem_Service")

        self.treemodelsort = Gtk.TreeModelSort(self.filter)

        self.treeview.set_model(self.treemodelsort)

        for i, column_title in enumerate(["Host", "Service", "Status"]):
            col = Gtk.TreeViewColumn( column_title)
            self.treeview.append_column( col)
            cell = Gtk.CellRendererText()
            col.pack_start(cell, expand=False)
            col.set_attributes(cell, text=i, cell_background=3)
            #cell.connect('edited', self._text_changed, 0)
            if column_title == "Status":
                col.set_sort_column_id(4)
            elif column_title == "Host":
                col.set_sort_column_id(0)
            elif column_title == "Service":
                col.set_sort_column_id(1)
            else:
                col.set_sort_column_id(0)

        
        self.treeview.connect("row-activated", self.show_filtered_by_host_or_service)       
        self.update_time_label()



    def filter_func(self, model, iter, data):
        """Tests if the language in the row is the one in the filter"""
        if self.current_filter is None or self.current_filter == "None":
            return True
        else:
            # print ("Filtering by %s: %s" % (self.filter_by, self.current_filter))
            if self.filter_by == "status":
                return self.current_filter in model[iter][2]
            elif self.filter_by == "service":
                return self.current_filter in model[iter][1]
            elif self.filter_by == "host":
                return self.current_filter in model[iter][0]
            elif self.filter_by == "state":
                return self.current_filter == model[iter][4]

    def on_selection_button_clicked(self, widget):
        """Called on any of the button clicks"""
        #we set the current language filter to the button's label
        l = widget.get_label()
        if l == "OK":
            self.current_filter = "0"
        elif l == "WARNING":
            self.current_filter = "1"
        elif l == "CRITICAL":
            self.current_filter = "2"
        else:
            self.current_filter = "None"

        self.filter_by = "state"

        #we update the filter, which updates in turn the view
        self.filter.refilter()
        self.update_time_label()

    def on_update_button_clicked(self, widget):
        self.update_content()

    def show_check_details(self, widget):
        treeselection = self.treeview.get_selection()
        model, treeiter = treeselection.get_selected()

        if treeiter != None:
            text = ""
            host = model[treeiter][0]
            service = model[treeiter][1]
            service_info = self.app.current_fetch[host][service]
            infos = ["service_description", "check_command", "check_period", "check_interval", "retry_interval", "has_been_checked", "should_be_scheduled", "check_execution_time", "check_latency", "current_state", "last_hard_state", "current_problem_id", "last_problem_id", "plugin_output", "last_time_ok", "last_hard_state_change", "current_attempt", "max_attempts", "next_check", "last_check", "is_flapping", "flap_detection_enabled"]
            for info in service_info:
                if info in infos:
                    text +="%s: %s\n" % (info, service_info[info])

            dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.CLOSE, host)
            dialog.format_secondary_text(text)
        else:
            dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
            dialog.format_secondary_text("Please select a result first!")

        dialog.run()
        dialog.destroy()

    def show_filtered_by_host_or_service(self, tv, treepath, tv_column):
        path_iter = self.filter.get_iter(treepath)
        host = self.filter.get(path_iter, 0)[0]
        service = self.filter.get(path_iter, 1)[0]
        if self.radio_filter_by_host.get_active() == True:
            self.filter_by = "host"
            self.current_filter = host
        else:
            self.filter_by = "service"
            self.current_filter = service
        
        self.filter.refilter()
        self.update_time_label()

    def update_content(self):
        if self.app.is_fetching == False:
            self.hosts_liststore.clear()
            self.__add_data_to_hosts_liststore()
            self.update_time_label()

    def update_time_label(self):
        self.time_label.set_label(self.app.fetch_date.strip())
        self.items_label.set_label("#%i" % len(self.filter))

    def quit(self, widget, callback_data=None):
        self.app.indicator.detail_win = False

    def sort_table(self, model, row1, row2, user_data):
        sort_column, _ = model.get_sort_column_id()
        value1 = model.get_value(row1, sort_column)
        value2 = model.get_value(row2, sort_column)

        if value1 < value2:
            return -1
        elif value1 == value2:
            return 0
        else:
            return 1


