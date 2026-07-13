from tkinter import Entry, Frame, Label, LabelFrame, StringVar
from tkinter.constants import BOTH, END, LEFT, TOP, X

from src.save_editor.drag.draggabblelistbox import DraggableListbox, DragManager


class PartyMember(LabelFrame):
    def __init__(
        self,
        parent,
        memberName: str,
        appConfig: dict,
        currentChapter: int,
        equippedItemData: dict,
        dragManager: DragManager,
    ):
        super().__init__(parent, text=memberName)

        self.currentHPVar = StringVar(value=str(equippedItemData.get("currentHP", 0)))
        self.maxHPVar = StringVar(value=str(equippedItemData.get("maxHP", 0)))

        self.hpFrame = Frame(self)
        Label(self.hpFrame, text="HP:").pack(side=LEFT)
        Entry(self.hpFrame, textvariable=self.currentHPVar, width=3).pack(
            side=LEFT, padx=(4, 0)
        )
        Label(self.hpFrame, text="/").pack(side=LEFT, padx=(2, 2))
        Entry(self.hpFrame, textvariable=self.maxHPVar, width=3).pack(side=LEFT)
        self.hpFrame.pack(side=TOP, fill=X, padx=5, pady=(5, 0))

        self.partyMemberListbox = DraggableListbox(
            self,
            dragManager,
            appConfig,
            chapter=currentChapter,
            allowInternalSwap=True,
            height=3,
        )
        self.partyMemberListbox.owner = memberName.lower()
        self.partyMemberListbox.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)

        # Insert items using IDs and tags
        self.partyMemberListbox.insertWithId(
            END, equippedItemData.get("weapon", 0), "weapon"
        )
        self.partyMemberListbox.insertWithId(
            END, equippedItemData.get("armor1", 0), "armor"
        )
        self.partyMemberListbox.insertWithId(
            END, equippedItemData.get("armor2", 0), "armor"
        )

    def getListbox(self):
        return self.partyMemberListbox

    def getAllItems(self):
        """Get the selected items by their IDs"""
        try:
            currentHP = int(self.currentHPVar.get().strip())
        except (ValueError, AttributeError):
            currentHP = 0
        try:
            maxHP = int(self.maxHPVar.get().strip())
        except (ValueError, AttributeError):
            maxHP = 0
        return {
            "currentHP": currentHP,
            "maxHP": maxHP,
            "weapon": self.partyMemberListbox.getItemId(0),
            "armor1": self.partyMemberListbox.getItemId(1),
            "armor2": self.partyMemberListbox.getItemId(2),
        }
