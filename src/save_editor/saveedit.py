from copy import deepcopy
from tkinter import Entry, Frame, Label, LabelFrame, StringVar
from tkinter.constants import BOTH, LEFT, NW, TOP, N, X
from tkinter.messagebox import askyesno
from tkinter.simpledialog import Dialog

from src.save_editor.basic_containers.basiccontainers import (
    BasicContainer,
    LongItemContainer,
)
from src.save_editor.basic_containers.inventory import Inventory
from src.save_editor.basic_containers.partymember import PartyMember
from src.save_editor.basic_containers.storage import Storage
from src.save_editor.change_report import generateCategorizedChangeReport
from src.save_editor.drag.dragmanager import DragManager
from src.save_editor.file_managing.active_save_read import readActiveSaveFile
from src.save_editor.file_managing.active_save_write import writeActiveSaveFile


class SaveFileEdit(Dialog):
    def __init__(
        self,
        parent,
        chapter: int,
        slot: int,
        dw_invItems: dict,
        chapterData: dict,
        fullConfig: dict,
        title="",
    ):
        self.FileDialogueTitle = title
        self.chapter = chapter
        self.slot = slot
        self.dw_invItems = dw_invItems
        self.chapterData = chapterData
        self.fullConfig = fullConfig  # Full config with all chapter data
        self.entryWidth = 40

        self.dragManager = DragManager(parent, fullConfig)

        self.savePattern = "ch1" if self.chapter == 1 else "ch2+"

        self.saveData = readActiveSaveFile(chapter, slot, fullConfig)

        # Store original data for change tracking
        self.originalData = deepcopy(self.saveData)

        # Initialize the dialog
        super().__init__(parent, title=title)

    # Function to create the body of the dialog
    def body(self, master):
        self.winfo_toplevel().resizable(False, False)
        self.minsize(width=250, height=100)
        self.mainFrame = Frame(master)

        # Top: Party Frame (horizontal row of party members)
        self.partyFrame = Frame(self.mainFrame)
        self.krisItems = PartyMember(
            self.partyFrame,
            "Kris",
            self.fullConfig,
            self.chapter,
            self.saveData["party"]["kris"],
            self.dragManager,
        )
        self.susieItems = PartyMember(
            self.partyFrame,
            "Susie",
            self.fullConfig,
            self.chapter,
            self.saveData["party"]["susie"],
            self.dragManager,
        )
        self.ralseiItems = PartyMember(
            self.partyFrame,
            "Ralsei",
            self.fullConfig,
            self.chapter,
            self.saveData["party"]["ralsei"],
            self.dragManager,
        )

        self.krisItems.pack(side=LEFT, anchor=NW, padx=(5, 0), pady=(0, 5))
        self.susieItems.pack(side=LEFT, anchor=NW)
        self.ralseiItems.pack(side=LEFT, anchor=NW)

        if self.isToggleEnabled("showNoelle", default=False):
            self.noelleItems = PartyMember(
                self.partyFrame,
                "Noelle",
                self.fullConfig,
                self.chapter,
                self.saveData["party"]["noelle"],
                self.dragManager,
            )
            self.noelleItems.pack(side=LEFT, anchor=NW, padx=(0, 5))
        else:
            self.noelleItems = None

        self.partyFrame.pack(side=TOP, fill=X, padx=5, pady=(5, 0))

        # Row 2: Armor, Weapons, Key Items (side by side)
        self.row2Frame = Frame(self.mainFrame)
        self.armorItems = LongItemContainer(
            self.row2Frame,
            "Armor",
            self.fullConfig,
            self.chapter,
            self.saveData["armor"],
            "armor",
            self.dragManager,
        )
        self.armorItems.itemListbox.listbox.config(width=12, height=12)
        self.weaponItems = LongItemContainer(
            self.row2Frame,
            "Weapons",
            self.fullConfig,
            self.chapter,
            self.saveData["weapons"],
            "weapon",
            self.dragManager,
        )
        self.weaponItems.itemListbox.listbox.config(width=12, height=12)
        self.keyItemsContainer = BasicContainer(
            self.row2Frame,
            "Key Items",
            self.fullConfig,
            self.chapter,
            self.saveData["keyItems"],
            "keyItem",
            self.dragManager,
        )
        self.keyItemsContainer.itemListbox.config(width=14, height=12)

        self.armorItems.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0, 5))
        self.weaponItems.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0, 5))
        self.keyItemsContainer.pack(
            side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0, 5)
        )
        self.row2Frame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(0, 5))

        self.statsFrame = LabelFrame(self.mainFrame, text="Save Stats")
        self.darkDollarVar = StringVar(value=str(self.saveData.get("darkDollar")))
        self.pointsVar = StringVar(value=str(self.saveData.get("points")))
        self.floweryDollarsVar = StringVar(
            value=str(self.saveData.get("floweryDollars"))
        )
        self.pinkCoinsVar = StringVar(value=str(self.saveData.get("pinkCoins")))

        stats = [
            ("Dark Dollars", self.darkDollarVar, True),
            ("Points", self.pointsVar, "dw_pointsLine" in self.chapterData),
            (
                "Flowery Dollars",
                self.floweryDollarsVar,
                "dw_floweryDollarsLine" in self.chapterData,
            ),
            ("Pink Coins", self.pinkCoinsVar, "dw_pinkCoinsLine" in self.chapterData),
        ]

        column = 0
        row = 0

        for label, variable, enabled in stats:
            if not enabled:
                continue

            map = {
                "Points": "showPoints",
                "Flowery Dollars": "showFloweryDollars",
                "Pink Coins": "showPinkCoins",
            }

            if label in map and not self.isToggleEnabled(map[label], default=True):
                continue

            Label(self.statsFrame, text=f"{label}:").grid(
                row=row, column=column * 2, padx=(5, 2), pady=5, sticky="e"
            )

            Entry(self.statsFrame, textvariable=variable, width=12).grid(
                row=row, column=column * 2 + 1, padx=(0, 10), pady=5, sticky="w"
            )

            column += 1

            if column == 3:
                column = 0
                row += 1

        self.statsFrame.pack(side=TOP, fill=X, padx=10, pady=(0, 5))

        # Row 3: Items and Storage (side by side)
        self.row3Frame = Frame(self.mainFrame)
        # Format Items inventory like Storage (grid with pages) but without View All button
        self.itemsContainer = Inventory(
            self.row3Frame,
            "Inventory",
            self.fullConfig,
            self.chapter,
            self.saveData["items"],
            self.dragManager,
        )

        # Changes based on chapter
        if self.chapter == 1:
            # In chapter 1, only show items container and center it
            self.itemsContainer.pack(expand=True, padx=5, pady=(0, 5))
        else:
            # In other chapters, show both items and storage side by side

            self.storageItems = Storage(
                self.row3Frame,
                "Storage",
                self.fullConfig,
                self.chapter,
                self.saveData["storage"],
                self.dragManager,
            )

            self.itemsContainer.pack(
                side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0, 5), anchor=N
            )
            self.storageItems.pack(
                side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0, 5)
            )

        self.row3Frame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(5, 5))

        # Register listboxes with the drag manager
        self.dragManager.registerListbox(self.krisItems.getListbox())
        self.dragManager.registerListbox(self.susieItems.getListbox())
        self.dragManager.registerListbox(self.ralseiItems.getListbox())

        for lb in self.itemsContainer.getListboxes():
            self.dragManager.registerListbox(lb)

        if hasattr(self, "storageItems"):
            for lb in self.storageItems.getListboxes():
                self.dragManager.registerListbox(lb)

        self.dragManager.registerListbox(self.keyItemsContainer.getListbox())
        self.dragManager.registerListbox(self.armorItems.getListbox())
        self.dragManager.registerListbox(self.weaponItems.getListbox())

        self.mainFrame.pack(fill=BOTH, expand=True)

    def validate(self):
        """Validate and show changes before saving."""
        # Collect current data from UI
        currentData = {
            "party": {
                "kris": self.krisItems.getAllItems(),
                "susie": self.susieItems.getAllItems(),
                "ralsei": self.ralseiItems.getAllItems(),
                "noelle": (
                    self.noelleItems.getAllItems()
                    if self.noelleItems is not None
                    else self.originalData["party"]["noelle"]
                ),
            },
            "items": self.itemsContainer.getAllItems(),
            "keyItems": self.keyItemsContainer.getAllItems(),
            "weapons": self.weaponItems.getAllItems(),
            "armor": self.armorItems.getAllItems(),
            "storage": self.storageItems.getAllItems()
            if hasattr(self, "storageItems")
            else [],
        }

        if "dw_darkDollarLine" in self.chapterData:
            currentData["darkDollar"] = self._parse_int(
                self.darkDollarVar.get(), self.saveData.get("darkDollar", 0)
            )
        if "dw_pointsLine" in self.chapterData:
            currentData["points"] = self._parse_int(
                self.pointsVar.get(), self.saveData.get("points", 0)
            )
        if "dw_floweryDollarsLine" in self.chapterData:
            currentData["floweryDollars"] = self._parse_int(
                self.floweryDollarsVar.get(), self.saveData.get("floweryDollars", 0)
            )
        if "dw_pinkCoinsLine" in self.chapterData:
            currentData["pinkCoins"] = self._parse_int(
                self.pinkCoinsVar.get(), self.saveData.get("pinkCoins", 0)
            )

        # Generate change report with categories
        changesByCategory = generateCategorizedChangeReport(
            self.originalData, currentData, self.dw_invItems, self.chapterData
        )

        # Count total changes
        totalChanges = sum(len(changes) for changes in changesByCategory.values())

        # If no changes, confirm with user
        if totalChanges == 0:
            return askyesno(
                "No Changes", "No changes were made to the save file. Close the editor?"
            )

        # Build categorized message
        changeMessage = "The following changes will be made:\n\n"

        for category, changes in changesByCategory.items():
            if changes:
                changeMessage += f"{category}:\n"
                # Show up to 10 changes per category
                changeMessage += "\n".join(f"  • {change}" for change in changes[:10])
                if len(changes) > 10:
                    changeMessage += (
                        f"\n  ... and {len(changes) - 10} more {category.lower()}"
                    )
                changeMessage += "\n\n"

        changeMessage += "Do you want to save these changes?"

        return askyesno("Confirm Changes", changeMessage)

    def apply(self):
        """Apply changes and write the save file."""
        # Collect all data from the UI components
        newData = {
            "partyMembers": {
                "kris": self.krisItems.getAllItems(),
                "susie": self.susieItems.getAllItems(),
                "ralsei": self.ralseiItems.getAllItems(),
                "noelle": (
                    self.noelleItems.getAllItems()
                    if self.noelleItems is not None
                    else self.saveData["party"]["noelle"]
                ),
            },
            "items": self.itemsContainer.getAllItems(),
            "keyItems": self.keyItemsContainer.getAllItems(),
            "weapons": self.weaponItems.getAllItems(),
            "armor": self.armorItems.getAllItems(),
            "storage": self.storageItems.getAllItems()
            if hasattr(self, "storageItems")
            else [],
            "darkDollar": self._parse_int(
                self.darkDollarVar.get(), self.saveData.get("darkDollar", 0)
            ),
            "floweryDollars": self._parse_int(
                self.floweryDollarsVar.get(), self.saveData.get("floweryDollars", 0)
            ),
            "pinkCoins": self._parse_int(
                self.pinkCoinsVar.get(), self.saveData.get("pinkCoins", 0)
            ),
            "points": self._parse_int(
                self.pointsVar.get(), self.saveData.get("points", 0)
            ),
        }

        # Write the save file
        writeActiveSaveFile(self.chapter, self.slot, newData, self.fullConfig)
        return

    def isToggleEnabled(self, toggleName: str, default=True):
        return self.chapterData.get("chapterToggles", {}).get(toggleName, default)

    def _parse_int(self, value: str, default: int = 0) -> int:
        """Safely parse an integer value from a string."""
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            try:
                return int(float(value.strip()))
            except (ValueError, AttributeError):
                return default
