from tkinter import *
from psgsql import *
from tkinter import messagebox
import random
import time
import config
import difftexts as diff
import datetime
from itertools import chain

# ================= Interface parameters =======================
title_string = "Anecdotes"
win_geometry = "900x600+10+10"
bg_of_view_area = "powder blue"
fg_of_view_area = "Steel Blue"
title_font = ("arial", 30, "bold")
info_font = ("arial", 10)
text_font = ("arial", 14)
bg_of_edit_area = "pink"
fg_of_edit_area = "Steel Blue"

# ================= Functions ==================================


def close(event=None):
    root.destroy()
    print("   Exiting...")
    exit()


def tick(lbl):
    """
    Display current time in lbl
    :param lbl:
    :return:
    """
    # get the current local time
    localtime = time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(time.time()))
    lbl.config(text=localtime)
    # calls itself every 200 milliseconds
    # to update the time display as needed
    # could use >200 ms, but display gets jerky
    lbl.after(200, tick, lbl)

# ==================== Classes ================================

class ListBoxChoice(object):
    def __init__(self, parent_window, data):
        self.master = parent_window
        self.data = data
        self.view_bg = "powder blue"
        self.edit_bg = "pink"
        self.fg = "Steel Blue"
        self.listfg = "black"
        self.text_font = ("arial", 14)
        self.list_font = ("arial", 15, "bold")
        self.qtywin = qtyInfo
        self.new = False
        self.key = 0
        self.after_check = False
        self.oldkey = 0
        self.listframe = Frame(self.master)
        self.listframe.pack(side=LEFT, fill=Y)
        self.listframe.tk_focusFollowsMouse()
        self.listscrollbar = Scrollbar(self.listframe)
        self.listscrollbar.pack(side=RIGHT, fill=Y)
        self.listbox = Listbox(self.listframe, font=self.list_font, fg=self.listfg, bg=self.view_bg, bd=5, width=5)
        self.listbox.pack(side=LEFT, fill=Y)
        self.listscrollbar.config(command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.listscrollbar.set)
        self.textframe = Frame(self.master)
        self.textframe.pack(side=RIGHT, fill=Y)
        self.textbox = Text(self.textframe, font=self.text_font, wrap='word', bg=self.edit_bg, bd=5, width=72)
        self.textbox.pack(side=LEFT, fill=Y, padx=0, pady=0)
        self.textscrollbar = Scrollbar(self.textframe)
        self.textscrollbar.pack(side=RIGHT, fill=Y)
        self.textscrollbar.config(command=self.textbox.yview)
        self.textbox.config(yscrollcommand=self.textscrollbar.set)
        self._qty(self.qtywin)
        self._build_listbox()
        self.master.bind("<Return>", self._view)
        self.master.bind("<Double-Button-1>", self._view)
        self.master.bind("<Button-1>", self._view)
        self.master.bind("<Up>", self._view)
        self.master.bind("<Down>", self._view)
        self.listbox.bind('<Delete>', self._delete)
        # viewBtn.config(command=self._view)
        newBtn.config(command=self._add)
        editBtn.config(command=self._edit)
        deleteBtn.config(command=self._delete)
        searchBtn.config(command=self._search)
        checkDbBtn.config(command=self._checkDB)
        AllBtn.config(command=self._all)


    def _qty(self, lbl):
        """
        How much items selected from the DataBase
        :param lbl:
        :return:
        """
        self.qty_string = f"There are {self.data.len()} items in the DataBase"
        lbl.config(text=self.qty_string)

    def _build_listbox(self):
        # print("Building listbox!...\n keys = ", self.key, self.oldkey)
        self.listbox.delete(0, END)         # Очистка списка анекдотов
        self.fltr = searchWin.get()
        if self.fltr:
            self.fltr = [('anecdote', self.fltr)]         # Считывание подстроки из окна searchWin
        if not self.after_check:
            self.lst = sorted(self.data.keys(self.fltr))     # Получение списка ключей для отображениея
        self.len = len(self.lst)
        #print(self.lst)
        if self.len > 0:
            # Словарь, где ключ - id отобранных анекдотов, а значение - порядковый номер
            self.dct = {self.lst[i]: i for i in range(self.len)}
            #
            for item in self.lst:
                self.listbox.insert(END, item)
            if self.new:
                self.dct = {self.lst[i]: i for i in range(self.len)}
                self.new = False
            else:
                self.key = random.choice(self.lst)
                print(self.key)
            self._sel()
            self._view()
        else:
            # Если список пуст, ничего не делаем
            self.key = 0
        self._qty(self.qtywin)

    def _add(self):
        print("_add: key=", self.key)
        self.new = True
        self.oldkey = self.key
        self.key = 0
        self._edit()

    def _edit(self):
        # print("_edit: key=", self.key)
        self.Edit = Toplevel(self.master)
        self.master.attributes('-disabled', 1)
        self.Edit.transient(self.master)
        self.Edit.title("Editing.....")
        self.tmp_panel = Frame(self.Edit, height=50, width=800, bg=self.view_bg)
        self.tmp_panel.pack(side='top', fill='x')
        self.tmp_textbox = Text(self.Edit, font=self.text_font, wrap='word', bg=self.edit_bg,
                                bd=5, width=72)
        self.tmp_textbox.pack(side=LEFT, fill=Y, padx=0, pady=0)
        self.saveBtn = Button(self.tmp_panel, text='Save', command=self._save)
        self.saveBtn.place(x=10, y=10, width=40, height=40)
        self.cancelBtn = Button(self.tmp_panel, text='Cancel', command=self._cancel)
        self.cancelBtn.place(x=50, y=10, width=40, height=40)
        self.tmp_textbox.configure(state="normal")
        self.tmp_textbox.delete('1.0', 'end')
        if self.key > 0:
            self.value = self.data.get(self.key)
            self.tmp_textbox.insert('1.0', self.value['anecdote'])


    def _cancel(self):
        # print("_cancel: key=", self.key)
        if messagebox.askyesno("Edit", "All changes will be lost Are you sure?", default="no"):
                self.new = False
                self.Edit.destroy()
                self.master.attributes('-disabled', 0)
                if self.key == 0 and self.oldkey != 0:
                    self.key = self.oldkey
                    self.oldkey = 0
                self._view()

    def _save(self):
        # print("_save: key=", self.key)
        if messagebox.askyesno("Edit", "All changes will be saved Are you sure?", default="no"):
                edited = self.tmp_textbox.get('1.0', 'end')
                if self.key == 0:
                    record = Record({config.anecdot_params['value_column']: edited})
                    self.key = self.data.add(record)

                else:
                    record = Record({config.anecdot_params['key_column']: self.key,
                                     config.anecdot_params['value_column']: edited})
                    self.key = self.data.update(record)
                # print("_save: key=", self.key)
                self.oldkey = 0
                if self.new:
                    self._build_listbox()
                # self.tmp_textbox.destroy()
                self.Edit.destroy()
                self.master.attributes('-disabled', 0)
                self.listbox.focus_force()
                self._view()
                return

    def _delete(self, event=None):
        # print("_delete: key=", self.key)
        if messagebox.askyesno("Delete", "Are you sure?", default="no"):
            self.idx = self.listbox.curselection()[0]
            self.key = self.lst[int(self.idx)]
            # print("Delete: ", self.key)
            self.data.delete(self.key)
            self.textbox.configure(state="normal")
            self.textbox.delete('1.0', 'end')
            self.textbox.configure(state="disabled")
            self._build_listbox()

    def _view(self, event=None):
        # print("_view: key= ", self.key, self.new)
        if not self.new:
            selection = self.listbox.curselection()
            if self.len > 0 and len(selection) > 0:
                self.idx = selection[0]
                self.key = self.lst[int(self.idx)]

        self.value = self.data.get(self.key)
        self.textbox.configure(state="normal")
        self.textbox.delete('1.0', 'end')
        if self.value is not None:
            creation_date = self.value['creationdate'] if self.value['creationdate'] is not None else None
            CreationTime.config(text=f"Creation Date: {creation_date}")
            Votes.config(text=f"Votes: {self.value['votes']}")
            Rating.config(text=f"Rating: {self.value['rating']}")
            self.textbox.insert('1.0', self.value['anecdote'])
        self.textbox.configure(state="disabled")
        self.new = False

    def _sel(self):
        """
        Установка курсора на элементе, соответствующем self.key при запуске программы
        :return:
        """
        self.ind = self.dct.get(self.key)
        print("_sel: ", self.key, self.ind)
        self.listbox.see(self.ind)
        self.listbox.activate(self.ind)
        # self.listbox.selection_anchor(self.ind)
        self.listbox.selection_set(self.ind)
        self.listbox.focus_set()

    def _search(self):
        self.textbox.configure(state="normal")
        self.textbox.delete('1.0', 'end')
        self.textbox.configure(state="disable")
        self._build_listbox()

    def _checkDB(self):
        #
        # Looking for dublicates
        #
        all = self.data.getall()
        dublicates = [(i['id'], k['id']) for i in all for k in all if i['id'] > k['id']
                      and diff.compareText(i['anecdote'], k['anecdote'])]
        if len(dublicates) > 0:
            self.after_check = True
            print(dublicates)
            self.lst = list(chain.from_iterable(dublicates))
            self._build_listbox()

    def _all(self):
        self.after_check = False
        searchWin.delete(0, 'end')
        self._build_listbox()


# ================================== Main ===============================================

if __name__ == '__main__':
    with OpenDB(config.db_params) as a:
        anecdotes = SqlDBTable(a, config.anecdot_params)
        root = Tk()
        root.protocol("WM_DELETE_WINDOW", close)
        root.geometry(win_geometry)
        root.title(title_string)
        root.resizable(False, False)

        # ===================================== Title ===============================================

        Tops = Frame(root, width=800, height=50, bg=bg_of_view_area,  borderwidth=5)
        Tops.pack(side=TOP)
        lblInfo = Label(Tops, font=title_font, text=title_string, fg=fg_of_view_area)
        lblInfo.grid(row=0, column=0, columnspan=2)

        # ===================================== Status =============================================

        Status = Frame(root, width=800, height=40, bg=bg_of_view_area,  borderwidth=5)
        Status.pack(side=BOTTOM)
        CreationTime = Label(Status, font=info_font, text="CreationTime:", fg=fg_of_view_area)
        CreationTime.grid(row=0, column=700, columnspan=100)
        Votes = Label(Status, font=info_font, text="Votes:", fg=fg_of_view_area)
        Votes.grid(row=0, column=400, columnspan=100)
        Rating = Label(Status, font=info_font, text="Rating:", fg=fg_of_view_area)
        Rating.grid(row=0, column=0, columnspan=100)

        # ====================== Clock in the title ===========================================

        clock = Label(Tops, font=info_font, fg=fg_of_view_area)
        clock.grid(row=1, column=1)
        tick(clock)

        # =================Number of anecdotes in the DB in the title ==============================

        qtyInfo = Label(Tops, font=info_font, fg=fg_of_view_area)
        qtyInfo.grid(row=1, column=0, pady=0, padx=1)

        # ===================== Menu ============================================================
        panelFrame = Frame(root, height=50, width=800, bg=bg_of_view_area)
        panelFrame.pack(side='top', fill='x')
        editBtn = Button(panelFrame, text='Edit')
        editBtn.place(x=10, y=10, width=40, height=40)
        deleteBtn = Button(panelFrame, text='Delete')
        deleteBtn.place(x=50, y=10, width=40, height=40)
        newBtn = Button(panelFrame, text='New')
        newBtn.place(x=90, y=10, width=40, height=40)
        quitBtn = Button(panelFrame, text='Quit', command=close)
        quitBtn.place(x=130, y=10, width=40, height=40)
        searchWin = Entry(panelFrame, justify=CENTER)
        searchWin.place(x=650, y=10, width=150, height=40)
        searchBtn = Button(panelFrame, text='Search')
        searchBtn.place(x=800, y=10, width=40, height=40)
        checkDbBtn = Button(panelFrame, text='CheckDB')
        checkDbBtn.place(x=550, y=10, width=70, height=40)
        AllBtn = Button(panelFrame, text='All')
        AllBtn.place(x=500, y=10, width=40, height=40)
        root.bind('<Control-z>', close)

        # ===================== View area =======================================================

        ListBoxChoice(root, anecdotes)

        root.mainloop()
