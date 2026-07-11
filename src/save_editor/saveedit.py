import os
from copy import deepcopy
from typing import TextIO

from tkinter import Frame, LabelFrame, Label, Entry, StringVar
from tkinter.simpledialog import Dialog
from tkinter.constants import LEFT, TOP, X, BOTH, NW, N
from tkinter.messagebox import askyesno

from src.save_editor.drag.dragmanager import DragManager
from src.save_editor.drag.drag_utils import get_item_name
from src.save_editor.basic_containers.basiccontainers import BasicContainer, LongItemContainer
from src.save_editor.basic_containers.partymember import PartyMember

from src.save_editor.basic_containers.inventory import Inventory
from src.save_editor.basic_containers.storage import Storage

from src.save_editor.file_managing.active_save_read import readActiveSaveFile

class SaveFileEdit(Dialog):
    def __init__(self, parent, chapter:int, slot:int, dw_invItems:dict, chapterData:dict, fullConfig:dict, title=""):
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
        self.krisItems = PartyMember(self.partyFrame, "Kris", self.fullConfig, self.chapter, self.saveData["party"]["kris"], self.dragManager)
        self.susieItems = PartyMember(self.partyFrame, "Susie", self.fullConfig, self.chapter, self.saveData["party"]["susie"], self.dragManager)
        self.ralseiItems = PartyMember(self.partyFrame, "Ralsei", self.fullConfig, self.chapter, self.saveData["party"]["ralsei"], self.dragManager)
        self.noelleItems = PartyMember(self.partyFrame, "Noelle", self.fullConfig, self.chapter, self.saveData["party"]["noelle"], self.dragManager)

        self.krisItems.pack(side=LEFT, anchor=NW, padx=(5,0), pady=(0,5))
        self.susieItems.pack(side=LEFT, anchor=NW)
        self.ralseiItems.pack(side=LEFT, anchor=NW)
        self.noelleItems.pack(side=LEFT, anchor=NW, padx=(0,5))
        self.partyFrame.pack(side=TOP, fill=X, padx=5, pady=(5, 0))

        # Row 2: Armor, Weapons, Key Items (side by side)
        self.row2Frame = Frame(self.mainFrame)
        self.armorItems = LongItemContainer(self.row2Frame, "Armor", self.fullConfig, self.chapter, self.saveData["armor"], "armor", self.dragManager)
        self.armorItems.itemListbox.listbox.config(width=12)
        self.weaponItems = LongItemContainer(self.row2Frame, "Weapons", self.fullConfig, self.chapter, self.saveData["weapons"], "weapon", self.dragManager)
        self.weaponItems.itemListbox.listbox.config(width=12)
        self.keyItemsContainer = BasicContainer(
            self.row2Frame, "Key Items", self.fullConfig, self.chapter, self.saveData["keyItems"], "keyItem", self.dragManager
        )
        self.keyItemsContainer.itemListbox.config(width=14, height=12)

        self.armorItems.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5))
        self.weaponItems.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5))
        self.keyItemsContainer.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5))
        self.row2Frame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(0,5))

        self.statsFrame = LabelFrame(self.mainFrame, text="Save Stats")
        self.darkDollarVar = StringVar(value=str(self.saveData.get("darkDollar", 0)))
        self.pointsVar = StringVar(value=str(self.saveData.get("points", 0)))
        self.floweryDollarsVar = StringVar(value=str(self.saveData.get("floweryDollars", 0)))
        self.pinkCoinsVar = StringVar(value=str(self.saveData.get("pinkCoins", 0)))

        Label(self.statsFrame, text="Dark Dollars:").pack(side=LEFT, padx=(5,2), pady=5)
        Entry(self.statsFrame, textvariable=self.darkDollarVar, width=12).pack(side=LEFT, padx=(0,10), pady=5)

        if "dw_floweryDollarsLine" in self.chapterData:
            Label(self.statsFrame, text="Flowery Dollars:").pack(side=LEFT, padx=(5,2), pady=5)
            Entry(self.statsFrame, textvariable=self.floweryDollarsVar, width=12).pack(side=LEFT, padx=(0,10), pady=5)

        if "dw_pinkCoinsLine" in self.chapterData:
            Label(self.statsFrame, text="Pink Coins:").pack(side=LEFT, padx=(5,2), pady=5)
            Entry(self.statsFrame, textvariable=self.pinkCoinsVar, width=12).pack(side=LEFT, padx=(0,10), pady=5)

        if "dw_pointsLine" in self.chapterData:
            Label(self.statsFrame, text="Points:").pack(side=LEFT, padx=(5,2), pady=5)
            Entry(self.statsFrame, textvariable=self.pointsVar, width=12).pack(side=LEFT, padx=(0,10), pady=5)

        self.statsFrame.pack(side=TOP, fill=X, padx=5, pady=(0,5))

        # Row 3: Items and Storage (side by side)
        self.row3Frame = Frame(self.mainFrame)
        # Format Items inventory like Storage (grid with pages) but without View All button
        self.itemsContainer = Inventory(
            self.row3Frame,
            "Inventory",
            self.fullConfig,
            self.chapter,
            self.saveData["items"],
            self.dragManager
        )
        self.storageItems = Storage(
            self.row3Frame,
            "Storage",
            self.fullConfig,
            self.chapter,
            self.saveData["storage"],
            self.dragManager,
        )

        # Layout changes based on chapter
        if self.chapter == 1:
            # In chapter 1, only show items container and center it
            self.itemsContainer.pack(expand=True, padx=5, pady=(0,5))
        else:
            # In other chapters, show both items and storage side by side
            self.itemsContainer.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5), anchor=N)
            self.storageItems.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5))
        
        self.row3Frame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(5, 5))

        # Register listboxes with the drag manager
        self.dragManager.registerListbox(self.krisItems.getListbox())
        self.dragManager.registerListbox(self.susieItems.getListbox())
        self.dragManager.registerListbox(self.ralseiItems.getListbox())
        
        for lb in self.itemsContainer.getListboxes():
            self.dragManager.registerListbox(lb)
        self.dragManager.registerListbox(self.keyItemsContainer.getListbox())
        self.dragManager.registerListbox(self.armorItems.getListbox())
        self.dragManager.registerListbox(self.weaponItems.getListbox())
        

        self.mainFrame.pack(fill=BOTH, expand=True)

        # Remove items that don't exist in chapter 1
        if self.chapter == 1:
            self.noelleItems.pack_forget()
            # Storage container is already not packed in chapter 1
        else:
            # Enable Noelle frame as she is not in chapter 1
            self.dragManager.registerListbox(self.noelleItems.getListbox())
            # Enable Storage frame as it is not in chapter 1
            for lb in self.storageItems.getListboxes():
                self.dragManager.registerListbox(lb)
    
    def _generateCategorizedChangeReport(self, original, current):
        """Generate a categorized dictionary of changes between original and current data."""
        changes = {
            "Party Equipment Changes": [],
            "Weapon & Armor Inventory Changes": [],
            "Key Item Changes": [],
            "Item & Storage Changes": [],
            "Save Stat Changes": []
        }
        
        # Check party member equipment changes
        for character in ["kris", "susie", "ralsei", "noelle"]:
            for slot in ["weapon", "armor1", "armor2"]:
                oldId = original["party"][character][slot]
                newId = current["party"][character][slot]
                if oldId != newId:
                    slotName = "Weapon" if slot == "weapon" else ("Armor 1" if slot == "armor1" else "Armor 2")
                    itemType = "weapon" if slot == "weapon" else "armor"
                    oldName = get_item_name(self.dw_invItems, oldId, itemType)
                    newName = get_item_name(self.dw_invItems, newId, itemType)
                    changes["Party Equipment Changes"].append(f"{character.capitalize()} {slotName}: \"{oldName}\" → \"{newName}\"")
            # Check current and max HP changes
            if original["party"][character].get("currentHP") != current["party"][character].get("currentHP"):
                changes["Save Stat Changes"].append(
                    f"{character.capitalize()} Current HP: \"{original['party'][character].get('currentHP')}\" → \"{current['party'][character].get('currentHP')}\"")
            if original["party"][character].get("maxHP") != current["party"][character].get("maxHP"):
                changes["Save Stat Changes"].append(
                    f"{character.capitalize()} Max HP: \"{original['party'][character].get('maxHP')}\" → \"{current['party'][character].get('maxHP')}\"")
        
        # Check weapons inventory changes
        for i in range(min(len(original["weapons"]), len(current["weapons"]))):
            if original["weapons"][i] != current["weapons"][i]:
                oldName = get_item_name(self.dw_invItems, original["weapons"][i], "weapon")
                newName = get_item_name(self.dw_invItems, current["weapons"][i], "weapon")
                changes["Weapon & Armor Inventory Changes"].append(f"Weapon Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check armor inventory changes
        for i in range(min(len(original["armor"]), len(current["armor"]))):
            if original["armor"][i] != current["armor"][i]:
                oldName = get_item_name(self.dw_invItems, original["armor"][i], "armor")
                newName = get_item_name(self.dw_invItems, current["armor"][i], "armor")
                changes["Weapon & Armor Inventory Changes"].append(f"Armor Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check key items changes
        for i in range(min(len(original["keyItems"]), len(current["keyItems"]))):
            if original["keyItems"][i] != current["keyItems"][i]:
                oldName = get_item_name(self.dw_invItems, original["keyItems"][i], "keyItem")
                newName = get_item_name(self.dw_invItems, current["keyItems"][i], "keyItem")
                changes["Key Item Changes"].append(f"Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check items inventory changes
        for i in range(min(len(original["items"]), len(current["items"]))):
            if original["items"][i] != current["items"][i]:
                oldName = get_item_name(self.dw_invItems, original["items"][i], "item")
                newName = get_item_name(self.dw_invItems, current["items"][i], "item")
                changes["Item & Storage Changes"].append(f"Item Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check storage changes (if applicable)
        if "storage" in original and "storage" in current:
            for i in range(min(len(original["storage"]), len(current["storage"]))):
                if original["storage"][i] != current["storage"][i]:
                    oldName = get_item_name(self.dw_invItems, original["storage"][i], "item")
                    newName = get_item_name(self.dw_invItems, current["storage"][i], "item")
                    changes["Item & Storage Changes"].append(f"Storage Slot {i+1}: \"{oldName}\" → \"{newName}\"")

        if original.get("darkDollar") != current.get("darkDollar"):
            changes["Save Stat Changes"].append(f"Dark Dollars: \"{original.get('darkDollar')}\" → \"{current.get('darkDollar')}\"")

        if original.get("floweryDollars") != current.get("floweryDollars"):
            changes["Save Stat Changes"].append(
                f"Flowery Dollars: \"{original.get('floweryDollars')}\" → \"{current.get('floweryDollars')}\"")

        if original.get("pinkCoins") != current.get("pinkCoins"):
            changes["Save Stat Changes"].append(
                f"Pink Coins: \"{original.get('pinkCoins')}\" → \"{current.get('pinkCoins')}\"")

        if original.get("points") != current.get("points"):
            changes["Save Stat Changes"].append(f"Points: \"{original.get('points')}\" → \"{current.get('points')}\"")
        
        return changes
    
    def validate(self):
        """Validate and show changes before saving."""
        # Collect current data from UI
        currentData = {
            "party": {
                "kris": self.krisItems.getAllItems(),
                "susie": self.susieItems.getAllItems(),
                "ralsei": self.ralseiItems.getAllItems(),
                "noelle": self.noelleItems.getAllItems() if hasattr(self, 'noelleItems') else {"currentHP": 0, "maxHP": 0, "weapon": 0, "armor1": 0, "armor2": 0}
            },
            "items": self.itemsContainer.getAllItems(),
            "keyItems": self.keyItemsContainer.getAllItems(),
            "weapons": self.weaponItems.getAllItems(),
            "armor": self.armorItems.getAllItems(),
            "storage": self.storageItems.getAllItems() if hasattr(self, 'storageItems') else [],
            "darkDollar": self._parse_int(self.darkDollarVar.get(), self.saveData.get("darkDollar", 0)),
            "floweryDollars": self._parse_int(self.floweryDollarsVar.get(), self.saveData.get("floweryDollars", 0)),
            "pinkCoins": self._parse_int(self.pinkCoinsVar.get(), self.saveData.get("pinkCoins", 0)),
            "points": self._parse_int(self.pointsVar.get(), self.saveData.get("points", 0))
        }
        
        # Generate change report with categories
        changesByCategory = self._generateCategorizedChangeReport(self.originalData, currentData)
        
        # Count total changes
        totalChanges = sum(len(changes) for changes in changesByCategory.values())
        
        # If no changes, confirm with user
        if totalChanges == 0:
            return askyesno("No Changes", "No changes were made to the save file. Close the editor?")
        
        # Build categorized message
        changeMessage = "The following changes will be made:\n\n"
        
        for category, changes in changesByCategory.items():
            if changes:
                changeMessage += f"{category}:\n"
                # Show up to 10 changes per category
                changeMessage += "\n".join(f"  • {change}" for change in changes[:10])
                if len(changes) > 10:
                    changeMessage += f"\n  ... and {len(changes) - 10} more {category.lower()}"
                changeMessage += "\n\n"
        
        changeMessage += "Do you want to save these changes?"
        
        return askyesno("Confirm Changes", changeMessage)
    
    def apply(self):
        """Apply changes and write the save file."""
        # Collect all data from the UI components
        self.result = {
            "party": {
                "kris": self.krisItems.getAllItems(),
                "susie": self.susieItems.getAllItems(),
                "ralsei": self.ralseiItems.getAllItems(),
                "noelle": self.noelleItems.getAllItems() if hasattr(self, 'noelleItems') else {"currentHP": 0, "maxHP": 0, "weapon": 0, "armor1": 0, "armor2": 0}
            },
            "items": self.itemsContainer.getAllItems(),
            "keyItems": self.keyItemsContainer.getAllItems(),
            "weapons": self.weaponItems.getAllItems(),
            "armor": self.armorItems.getAllItems(),
            "storage": self.storageItems.getAllItems() if hasattr(self, 'storageItems') else [],
            "darkDollar": self._parse_int(self.darkDollarVar.get(), self.saveData.get("darkDollar", 0)),
            "floweryDollars": self._parse_int(self.floweryDollarsVar.get(), self.saveData.get("floweryDollars", 0)),
            "pinkCoins": self._parse_int(self.pinkCoinsVar.get(), self.saveData.get("pinkCoins", 0)),
            "points": self._parse_int(self.pointsVar.get(), self.saveData.get("points", 0))
        }
        
        # Write the save file
        self.writeSaveFile()
        return


    def _parse_int(self, value: str, default: int = 0) -> int:
        """Safely parse an integer value from a string."""
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            try:
                return int(float(value.strip()))
            except (ValueError, AttributeError):
                return default
    
    def _write_character_equipment(self, fileList: list, character: str, equipment: dict):
        """Helper method to write character equipment and health to save file."""
        locData = self.chapterData["dw_partyMemberLocation"][character]
        base_idx = locData[0]
        fileList[base_idx] = f"{equipment.get('currentHP', 0)}\n"
        fileList[base_idx + 1] = f"{equipment.get('maxHP', 0)}\n"
        fileList[base_idx + 6] = f"{equipment.get('weapon', 0)}\n"
        fileList[base_idx + 7] = f"{equipment.get('armor1', 0)}\n"
        fileList[base_idx + 8] = f"{equipment.get('armor2', 0)}\n"

    def writeSaveFile(self):
        """
        Write the modified data back to the save file using the same format as extraction.
        """
        # Read the original file to preserve structure
        save_file_path = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{self.chapter}_{self.slot}")
        
        with open(save_file_path, 'r') as f:
            fileList = f.readlines()
        
        # Ensure all lines end with newline
        for i in range(len(fileList)):
            if not fileList[i].endswith('\n'):
                fileList[i] += '\n'
        
        if self.savePattern == "ch1":
            # Write items, keyItems, weapons, and armor (12 of each)
            start = self.chapterData["dw_invStart"]
            
            for i in range(12):
                # Each group of 4 lines: item, keyItem, weapon, armor
                item_idx = start - 1 + i * 4
                key_item_idx = start - 1 + i * 4 + 1
                weapon_idx = start - 1 + i * 4 + 2
                armor_idx = start - 1 + i * 4 + 3
                
                fileList[item_idx] = f"{self.result['items'][i] if i < len(self.result['items']) else 0}\n"
                fileList[key_item_idx] = f"{self.result['keyItems'][i] if i < len(self.result['keyItems']) else 0}\n"
                fileList[weapon_idx] = f"{self.result['weapons'][i] if i < len(self.result['weapons']) else 0}\n"
                fileList[armor_idx] = f"{self.result['armor'][i] if i < len(self.result['armor']) else 0}\n"
            
            # Write party member equipment for Kris, Susie, Ralsei
            for character in ["kris", "susie", "ralsei"]:
                self._write_character_equipment(fileList, character, self.result['party'][character])
        
        elif self.savePattern == "ch2+":
            # Write items and keyItems (interleaved)
            invStart = self.chapterData["dw_invStart"]
            
            for i in range(self.chapterData["dw_invCount"]["item"]):
                item_idx = invStart - 1 + i * 2
                key_item_idx = invStart - 1 + i * 2 + 1
                
                fileList[item_idx] = f"{self.result['items'][i] if i < len(self.result['items']) else 0}\n"
                fileList[key_item_idx] = f"{self.result['keyItems'][i] if i < len(self.result['keyItems']) else 0}\n"
            
            # Write weapons and armor (interleaved, after items)
            weapons_start = invStart - 1 + self.chapterData["dw_invCount"]["item"] * 2 + 2
            
            for i in range(self.chapterData["dw_invCount"]["weapon"]):
                weapon_idx = weapons_start + i * 2
                armor_idx = weapons_start + i * 2 + 1
                
                fileList[weapon_idx] = f"{self.result['weapons'][i] if i < len(self.result['weapons']) else 0}\n"
                fileList[armor_idx] = f"{self.result['armor'][i] if i < len(self.result['armor']) else 0}\n"
            
            # Write party member equipment for Kris, Susie, Ralsei, Noelle
            for character in ["kris", "susie", "ralsei", "noelle"]:
                self._write_character_equipment(fileList, character, self.result['party'][character])
        
        # Write storage if present
        if "dw_storageStart" in self.chapterData and "dw_storageEnd" in self.chapterData:
            storageStart = self.chapterData["dw_storageStart"]
            
            for i, storage_item in enumerate(self.result["storage"]):
                if storageStart - 1 + i < len(fileList):
                    fileList[storageStart - 1 + i] = f"{storage_item}\n"

        if "dw_darkDollarLine" in self.chapterData:
            darkDollarIdx = self.chapterData["dw_darkDollarLine"] - 1
            if 0 <= darkDollarIdx < len(fileList):
                fileList[darkDollarIdx] = f"{self.result['darkDollar']}\n"

        if "dw_floweryDollarsLine" in self.chapterData:
            floweryDollarsIdx = self.chapterData["dw_floweryDollarsLine"] - 1
            if 0 <= floweryDollarsIdx < len(fileList):
                fileList[floweryDollarsIdx] = f"{self.result.get('floweryDollars', 0)}\n"

        if "dw_pinkCoinsLine" in self.chapterData:
            pinkCoinsIdx = self.chapterData["dw_pinkCoinsLine"] - 1
            if 0 <= pinkCoinsIdx < len(fileList):
                fileList[pinkCoinsIdx] = f"{self.result.get('pinkCoins', 0)}\n"

        if "dw_pointsLine" in self.chapterData:
            pointsIdx = self.chapterData["dw_pointsLine"] - 1
            if 0 <= pointsIdx < len(fileList):
                fileList[pointsIdx] = f"{self.result.get('points', 0)}\n"

        # Write the modified content back to the file
        with open(save_file_path, 'w') as f:
            f.writelines(fileList)
