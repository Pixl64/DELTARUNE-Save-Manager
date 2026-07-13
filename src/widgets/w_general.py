from tkinter import Frame, Listbox, Scrollbar
from tkinter.constants import LEFT, RIGHT, VERTICAL


class ScrollableListbox(Frame):
    def __init__(
        self, parent, selectbackground, items=None, height=10, width=40, **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.listbox = Listbox(
            self, height=height, width=width, selectbackground=selectbackground
        )
        self.scrollbar = Scrollbar(self, orient=VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=LEFT, fill="both", expand=True)
        self.scrollbar.pack(side=RIGHT, fill="y")
        if items:
            for item in items:
                self.listbox.insert("end", item)

    def insert(self, index, item):
        self.listbox.insert(index, item)

    def delete(self, first, last=None):
        self.listbox.delete(first, last)

    def get(self, first, last=None):
        return self.listbox.get(first, last)

    def curselection(self):
        return self.listbox.curselection()

    def bind_listbox(self, sequence=None, func=None, add=None):
        self.listbox.bind(sequence, func, add)
