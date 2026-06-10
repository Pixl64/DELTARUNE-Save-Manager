import os
import json
import copy
from typing import TextIO

from tkinter import Tk, Toplevel, Frame, LabelFrame, Label, Button
from tkinter.simpledialog import Dialog
from tkinter.constants import END, LEFT, RIGHT, TOP, BOTTOM, X, BOTH, NW, N
from tkinter.messagebox import askyesno

from customlistbox import DragManager, DraggableListbox, DraggableScrollableListbox

class PartyMemberItems(LabelFrame):
    def __init__(self, parent, memberName:str, appConfig:dict, chapterLimits:dict, currentChapter:int, equippedItemData:dict, dragManager:DragManager):
        super().__init__(parent, text=memberName)
        
        self.partyMemberListbox = DraggableListbox(self, dragManager, appConfig, chapterLimits, currentChapter, allowInternalSwap=True, appConfig=appConfig, height=3)
        self.partyMemberListbox.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,5), pady=5)
        
        # Insert items using IDs and tags
        self.partyMemberListbox.insertWithId(END, equippedItemData["weapon"], "weapon")
        self.partyMemberListbox.insertWithId(END, equippedItemData["armor1"], "armor")
        self.partyMemberListbox.insertWithId(END, equippedItemData["armor2"], "armor")
    
    def getListbox(self):
        return self.partyMemberListbox
    
    def getSelected(self):
        """Get the selected items by their IDs"""
        return {
            "weapon": self.partyMemberListbox.getItemId(0),
            "armor1": self.partyMemberListbox.getItemId(1),
            "armor2": self.partyMemberListbox.getItemId(2)
        }

class StorageContainer(LabelFrame):
    def __init__(self, parent, title: str, dw_invItems: dict, chapterLimits: dict, currentChapter: int, storageData: list, dragManager: DragManager, itemsPerPage=12, showViewAll=True):
        super().__init__(parent, text=title)
        self.dw_invItems = dw_invItems  # Item data for context menus
        self.chapterLimits = chapterLimits
        self.currentChapter = currentChapter
        self.dragManager = dragManager
        self.storageData = storageData
        self.itemsPerPage = itemsPerPage
        self.currentPage = 0
        self.lastPageChange = 0  # Track last page change time to prevent rapid changes
        self.showViewAll = showViewAll  # Whether to show the View All button

        self.rows = 6
        self.cols = 2

        self.listboxes = []
        self.config(text=title)
        self._build_widgets()
        self._load_page()


    def _build_widgets(self):
        self.gridFrame = Frame(self)
        self.gridFrame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)

        for r in range(self.rows):
            row_listboxes = []
            for c in range(self.cols):
                lb = DraggableListbox(self.gridFrame, self.dragManager, self.dw_invItems, self.chapterLimits, self.currentChapter, allowInternalSwap=True, appConfig=self.chapterLimits, height=1, width=18)
                lb.grid(row=r, column=c, padx=2, pady=1, sticky="ew")
                row_listboxes.append(lb)
            self.listboxes.extend(row_listboxes)

        # Page controls
        self.pageFrame = Frame(self)
        self.pageFrame.pack(side=BOTTOM, fill=X, padx=5, pady=(0, 5))
        
        self.prevBtn = Label(self.pageFrame, text="⯇ Prev", fg="blue", cursor="hand2")
        self.nextBtn = Label(self.pageFrame, text="Next ⯈", fg="blue", cursor="hand2")
        self.pageLabel = Label(self.pageFrame, text="Page 1")

        self.prevBtn.pack(side=LEFT)
        self.pageLabel.pack(side=LEFT, padx=(10,5))
        self.nextBtn.pack(side=RIGHT)
        self._add_view_all_button()

        self.prevBtn.bind("<Button-1>", lambda e: self._change_page(-1))
        self.nextBtn.bind("<Button-1>", lambda e: self._change_page(1))
        
        # Register page navigation buttons with drag manager for hover functionality
        self.dragManager.registerPageButton(self.prevBtn, lambda: self._change_page_if_possible(-1))
        self.dragManager.registerPageButton(self.nextBtn, lambda: self._change_page_if_possible(1))

    def _add_view_all_button(self):
        """Add View All button next to page label on same line"""
        if self.showViewAll:
            # View All button on the same line, positioned after page label
            self.viewAllBtn = Label(self.pageFrame, text="⌕ View All", fg="darkgreen", cursor="hand2")
            self.viewAllBtn.pack(side=RIGHT, padx=(5, 10))
            self.viewAllBtn.bind("<Button-1>", lambda e: self._open_view_all_window())

    def _load_page(self):
        start = self.currentPage * self.itemsPerPage
        end = start + self.itemsPerPage
        page_items = self.storageData[start:end]
        # Fill or clear all listboxes
        for i, lb in enumerate(self.listboxes):
            lb.delete(0, END)
            lb.itemIds.clear()
            lb.itemTags.clear()
            # Clear any highlighting that might remain
            lb.clearHighlight()
            if i < len(page_items):
                itemId = page_items[i]
                lb.insertWithId(END, itemId, "item")
        self.pageLabel.config(text=f"Page {self.currentPage + 1} / {self.page_count()}")

        # Enable/disable buttons
        self.prevBtn.config(state="normal" if self.currentPage > 0 else "disabled")
        self.nextBtn.config(state="normal" if self.currentPage < self.page_count() - 1 else "disabled")
        
        # Re-highlight valid drop zones if we're currently dragging
        if hasattr(self.dragManager, 'dragStartListbox') and self.dragManager.dragStartListbox is not None:
            self.dragManager._highlightValidDropZones()

    def _change_page(self, delta):
        new_page = self.currentPage + delta
        if new_page < 0 or new_page >= self.page_count():
            return  # Block going past 0 or above max
        self._save_page()
        self.currentPage = new_page
        self._load_page()

    def _change_page_if_possible(self, delta):
        """Change page only if it's possible (used for drag hover functionality)"""
        import time
        current_time = time.time()
        
        # Prevent rapid page changes (cooldown of 0.5 seconds)
        if current_time - self.lastPageChange < 0.5:
            return
            
        new_page = self.currentPage + delta
        if new_page >= 0 and new_page < self.page_count():
            self._save_page()
            self.currentPage = new_page
            self._load_page()
            self.lastPageChange = current_time

    def _save_page(self):
        # Save current page's items back to storageData
        start = self.currentPage * self.itemsPerPage
        for i, lb in enumerate(self.listboxes):
            idx = start + i
            if idx < len(self.storageData):
                self.storageData[idx] = lb.getItemId(0) if lb.size() > 0 else 0

    def page_count(self):
        return max(1, (len(self.storageData) + self.itemsPerPage - 1) // self.itemsPerPage)

    def getListboxes(self):
        return self.listboxes

    def getSelected(self):
        # Return all storage item IDs (flattened)
        self._save_page()
        return self.storageData
    
    def _open_view_all_window(self):
        """Open a window showing all storage items for easy management"""
        # Save current page before opening view all
        self._save_page()
        
        # Create new window
        view_all_window = Toplevel(self)
        view_all_window.title("Storage - View All Items")
        view_all_window.transient(self) # pyright: ignore[reportArgumentType, reportCallIssue]
        view_all_window.grab_set()
        
        # Create a separate drag manager for this window
        view_all_drag_manager = DragManager(view_all_window)
        
        # Main container frame
        main_frame = Frame(view_all_window)
        main_frame.pack(padx=10, pady=10)
        
        # Calculate how many pages we need based on the main storage pagination
        total_main_pages = self.page_count()
        
        # Create frames and listboxes for each page
        all_listboxes = []
        
        # Calculate grid layout for page frames (2 columns)
        page_cols = 2
        
        for page_num in range(total_main_pages):
            # Calculate position in the grid
            frame_row = page_num // page_cols
            frame_col = page_num % page_cols
            
            # Create labeled frame for this page
            page_frame = LabelFrame(main_frame, text=f"Page {page_num + 1}")
            page_frame.grid(row=frame_row, column=frame_col, padx=10, pady=10, sticky="nsew")
            
            # Create 2x6 grid of listboxes within this page frame
            page_listboxes = []
            for r in range(self.rows):  # Use same rows as main storage (6)
                for c in range(self.cols):  # Use same cols as main storage (2)
                    lb = DraggableListbox(
                        page_frame, 
                        view_all_drag_manager, 
                        self.dw_invItems, 
                        self.chapterLimits, 
                        self.currentChapter, 
                        allowInternalSwap=True, 
                        height=1, 
                        width=18  # Same width as main storage
                    )
                    lb.grid(row=r, column=c, padx=2, pady=1, sticky="ew")
                    page_listboxes.append(lb)
            
            all_listboxes.extend(page_listboxes)
            
            # Configure grid weights for this page frame
            for col in range(self.cols):
                page_frame.columnconfigure(col, weight=1)
        
        # Configure grid weights for the main frame
        for col in range(page_cols):
            main_frame.columnconfigure(col, weight=1)
        
        # Register all listboxes with the drag manager for proper highlighting
        for lb in all_listboxes:
            view_all_drag_manager.registerListbox(lb)
        
        # Populate all listboxes with data
        for i, lb in enumerate(all_listboxes):
            if i < len(self.storageData):
                item_id = self.storageData[i]
                lb.insertWithId(0, item_id, "item")  # Use "item" tag for storage items
        
        # Button frame at bottom
        button_frame = Frame(view_all_window)
        button_frame.pack(side=BOTTOM, fill=X, padx=10, pady=(0, 10))
        
        def close():
            # Save all changes back to storage data
            for i, lb in enumerate(all_listboxes):
                if i < len(self.storageData):
                    if lb.size() > 0:
                        self.storageData[i] = lb.getItemId(0) or 0
                    else:
                        self.storageData[i] = 0
            
            # Reload the current page in the main storage view
            self._load_page()
            view_all_window.destroy()
        
        # Add button
        Button(button_frame, text="Close", command=close).pack(side=RIGHT)
        
        # Add instructions
        Label(button_frame, text="Drag and drop items to reorganize across all pages.", 
              fg="gray").pack(side=LEFT)
        
        # Focus the window and auto-size to content
        view_all_window.focus_set()
        
        # Let the window size itself to fit the content
        view_all_window.update_idletasks()  # Ensure all widgets are rendered
        view_all_window.resizable(False, False)  # Prevent manual resizing
        
        # Center the window on screen
        window_width = view_all_window.winfo_reqwidth()
        window_height = view_all_window.winfo_reqheight()
        screen_width = view_all_window.winfo_screenwidth()
        screen_height = view_all_window.winfo_screenheight()
        
        # Calculate center position
        center_x = (screen_width - window_width) // 2
        center_y = (screen_height - window_height) // 2
        
        # Set window position
        view_all_window.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

class BasicContainer(LabelFrame):
    def __init__(self, parent, title:str, appConfig:dict, chapterLimits:dict, currentChapter:int, itemData:list, itemType:str, dragManager:DragManager):
        super().__init__(parent, text=title)
        
        self.itemListbox = DraggableListbox(self, dragManager, appConfig, chapterLimits, currentChapter, allowInternalSwap=True, appConfig=chapterLimits, height=10)
        self.itemListbox.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        
        # Insert items using IDs and tags
        for itemId in itemData:
            self.itemListbox.insertWithId(END, itemId, itemType)
    
    def getListbox(self):
        return self.itemListbox  # Return the actual listbox, not the container
    
    def getSelected(self):
        """Get all items by their IDs"""
        items = []
        for i in range(self.itemListbox.size()):
            items.append(self.itemListbox.getItemId(i))
        return items

class LongItemContainer(LabelFrame):
    def __init__(self, parent, title:str, appConfig:dict, chapterLimits:dict, currentChapter:int, itemData:list, itemType:str, dragManager:DragManager):
        super().__init__(parent, text=title)
        
        self.itemListbox = DraggableScrollableListbox(self, dragManager, appConfig, chapterLimits, currentChapter, allowInternalSwap=True, appConfig=chapterLimits, height=10)
        self.itemListbox.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        
        # Insert items using IDs and tags
        for itemId in itemData:
            self.itemListbox.insertWithId(END, itemId, itemType)
    
    def getListbox(self):
        return self.itemListbox.getListbox()  # Return the actual listbox, not the container
    
    def getSelected(self):
        """Get all items by their IDs"""
        items = []
        for i in range(self.itemListbox.listbox.size()):
            items.append(self.itemListbox.listbox.getItemId(i))
        return items

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
        
        if self.chapter == 1:
            self.savePattern = "ch1"
        else:
            self.savePattern = "ch2+"
        
        with open(os.path.join(os.environ["DR_SAVE_PATH"], f"filech{self.chapter}_{self.slot}")) as f:
            self.saveData = self.getSaveFileItemData(f)
        
        # Store original data for change tracking
        self.originalData = self._deepCopyData(self.saveData)
        
        # Initialize the dialog
        super().__init__(parent, title=title)


    # Function to create the body of the dialog
    def body(self, master):
        self.winfo_toplevel().resizable(False, False)
        self.minsize(width=250, height=100)
        self.mainFrame = Frame(master)

        # Top: Party Frame (horizontal row of party members)
        self.partyFrame = Frame(self.mainFrame)
        self.krisItems = PartyMemberItems(self.partyFrame, "Kris", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["party"]["kris"], self.dragManager)
        self.susieItems = PartyMemberItems(self.partyFrame, "Susie", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["party"]["susie"], self.dragManager)
        self.ralseiItems = PartyMemberItems(self.partyFrame, "Ralsei", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["party"]["ralsei"], self.dragManager)
        self.noelleItems = PartyMemberItems(self.partyFrame, "Noelle", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["party"]["noelle"], self.dragManager)

        self.krisItems.pack(side=LEFT, anchor=NW, padx=(5,0), pady=(0,5))
        self.susieItems.pack(side=LEFT, anchor=NW)
        self.ralseiItems.pack(side=LEFT, anchor=NW)
        self.noelleItems.pack(side=LEFT, anchor=NW, padx=(0,5))
        self.partyFrame.pack(side=TOP, fill=X, padx=5, pady=(5, 0))

        # Row 2: Armor, Weapons, Key Items (side by side)
        self.row2Frame = Frame(self.mainFrame)
        self.armorItems = LongItemContainer(self.row2Frame, "Armor", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["armor"], "armor", self.dragManager)
        self.armorItems.itemListbox.listbox.config(width=12)
        self.weaponItems = LongItemContainer(self.row2Frame, "Weapons", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["weapons"], "weapon", self.dragManager)
        self.weaponItems.itemListbox.listbox.config(width=12)
        self.keyItemsContainer = BasicContainer(
            self.row2Frame, "Key Items", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["keyItems"], "keyItem", self.dragManager
        )
        self.keyItemsContainer.itemListbox.config(width=14, height=12)

        self.armorItems.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5))
        self.weaponItems.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5))
        self.keyItemsContainer.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=(0,5))
        self.row2Frame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=(0,5))

        # Row 3: Items and Storage (side by side)
        self.row3Frame = Frame(self.mainFrame)
        # Format Items inventory like Storage (grid with pages) but without View All button
        self.itemsContainer = StorageContainer(
            self.row3Frame, "Items", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["items"], self.dragManager, showViewAll=False
        )
        self.storageItems = StorageContainer(self.row3Frame, "Storage", self.dw_invItems, self.fullConfig, self.chapter, self.saveData["storage"], self.dragManager)

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

    def _deepCopyData(self, data):
        """Create a deep copy of save data for change tracking."""
        return copy.deepcopy(data)
    
    def _getItemName(self, itemId, itemType):
        """Get the display name for an item ID and type."""
        # Map itemType to category in dw_invItems
        categoryMap = {
            "weapon": "weapons",
            "armor": "armor",
            "item": "items",
            "keyItem": "keyItems"
        }
        category = categoryMap.get(itemType, "items")
        itemDict = self.dw_invItems.get(category, {})
        return itemDict.get(str(itemId), f"Unknown {itemType} ({itemId})")
    
    def _generateCategorizedChangeReport(self, original, current):
        """Generate a categorized dictionary of changes between original and current data."""
        changes = {
            "Party Equipment Changes": [],
            "Weapon & Armor Inventory Changes": [],
            "Key Item Changes": [],
            "Item & Storage Changes": []
        }
        
        # Check party member equipment changes
        for character in ["kris", "susie", "ralsei", "noelle"]:
            for slot in ["weapon", "armor1", "armor2"]:
                oldId = original["party"][character][slot]
                newId = current["party"][character][slot]
                if oldId != newId:
                    slotName = "Weapon" if slot == "weapon" else ("Armor 1" if slot == "armor1" else "Armor 2")
                    itemType = "weapon" if slot == "weapon" else "armor"
                    oldName = self._getItemName(oldId, itemType)
                    newName = self._getItemName(newId, itemType)
                    changes["Party Equipment Changes"].append(f"{character.capitalize()} {slotName}: \"{oldName}\" → \"{newName}\"")
        
        # Check weapons inventory changes
        for i in range(min(len(original["weapons"]), len(current["weapons"]))):
            if original["weapons"][i] != current["weapons"][i]:
                oldName = self._getItemName(original["weapons"][i], "weapon")
                newName = self._getItemName(current["weapons"][i], "weapon")
                changes["Weapon & Armor Inventory Changes"].append(f"Weapon Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check armor inventory changes
        for i in range(min(len(original["armor"]), len(current["armor"]))):
            if original["armor"][i] != current["armor"][i]:
                oldName = self._getItemName(original["armor"][i], "armor")
                newName = self._getItemName(current["armor"][i], "armor")
                changes["Weapon & Armor Inventory Changes"].append(f"Armor Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check key items changes
        for i in range(min(len(original["keyItems"]), len(current["keyItems"]))):
            if original["keyItems"][i] != current["keyItems"][i]:
                oldName = self._getItemName(original["keyItems"][i], "keyItem")
                newName = self._getItemName(current["keyItems"][i], "keyItem")
                changes["Key Item Changes"].append(f"Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check items inventory changes
        for i in range(min(len(original["items"]), len(current["items"]))):
            if original["items"][i] != current["items"][i]:
                oldName = self._getItemName(original["items"][i], "item")
                newName = self._getItemName(current["items"][i], "item")
                changes["Item & Storage Changes"].append(f"Item Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        # Check storage changes (if applicable)
        if "storage" in original and "storage" in current:
            for i in range(min(len(original["storage"]), len(current["storage"]))):
                if original["storage"][i] != current["storage"][i]:
                    oldName = self._getItemName(original["storage"][i], "item")
                    newName = self._getItemName(current["storage"][i], "item")
                    changes["Item & Storage Changes"].append(f"Storage Slot {i+1}: \"{oldName}\" → \"{newName}\"")
        
        return changes
    
    def validate(self):
        """Validate and show changes before saving."""
        # Collect current data from UI
        currentData = {
            "party": {
                "kris": self.krisItems.getSelected(),
                "susie": self.susieItems.getSelected(),
                "ralsei": self.ralseiItems.getSelected(),
                "noelle": self.noelleItems.getSelected() if hasattr(self, 'noelleItems') else {"weapon": 0, "armor1": 0, "armor2": 0}
            },
            "items": self.itemsContainer.getSelected(),
            "keyItems": self.keyItemsContainer.getSelected(),
            "weapons": self.weaponItems.getSelected(),
            "armor": self.armorItems.getSelected(),
            "storage": self.storageItems.getSelected() if hasattr(self, 'storageItems') else []
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
                "kris": self.krisItems.getSelected(),
                "susie": self.susieItems.getSelected(),
                "ralsei": self.ralseiItems.getSelected(),
                "noelle": self.noelleItems.getSelected() if hasattr(self, 'noelleItems') else {"weapon": 0, "armor1": 0, "armor2": 0}
            },
            "items": self.itemsContainer.getSelected(),
            "keyItems": self.keyItemsContainer.getSelected(),
            "weapons": self.weaponItems.getSelected(),
            "armor": self.armorItems.getSelected(),
            "storage": self.storageItems.getSelected() if hasattr(self, 'storageItems') else []
        }
        
        # Write the save file
        self.writeSaveFile()
        return

    def _read_character_equipment(self, fileList: list, character: str) -> dict:
        """Helper method to read character equipment from save file."""
        locData = self.chapterData["dw_partyMemberLocation"][character]
        base_idx = locData[0]
        return {
            "weapon": int(fileList[base_idx + 6].strip()),
            "armor1": int(fileList[base_idx + 7].strip()),
            "armor2": int(fileList[base_idx + 8].strip())
        }
    
    def _write_character_equipment(self, fileList: list, character: str, equipment: dict):
        """Helper method to write character equipment to save file."""
        locData = self.chapterData["dw_partyMemberLocation"][character]
        base_idx = locData[0]
        fileList[base_idx + 6] = f"{equipment['weapon']}\n"
        fileList[base_idx + 7] = f"{equipment['armor1']}\n"
        fileList[base_idx + 8] = f"{equipment['armor2']}\n"

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
        
        # Write the modified content back to the file
        with open(save_file_path, 'w') as f:
            f.writelines(fileList)

    def getSaveFileItemData(self, file:TextIO) -> dict:
        """
        Reads the items from a save file and returns a dictionary of items.
        
        :param file: The file to read from.
        :param limiters: The limiters for the items.
        :param savePattern: The pattern of the save file.

        Valid save patterns:
        - "ch1": For save files with 12 weapon and armor slots (chapter 1)
        - "ch2+": For save files with 48 weapon and armor slots (chapter 2 and onwards)
        
        :return dict: A dictionary with the items, key items, weapons, armor, and storage
        
        """
        
        if self.savePattern not in ["ch1", "ch2+"]:
            raise ValueError("Invalid save pattern. Must be 'ch1' or 'ch2+'.")
        
        resDict = {
            "party": {
                "kris": {
                    "weapon": 0,
                    "armor1":0,
                    "armor2":0
                },
                "susie": {
                    "weapon": 0,
                    "armor1":0,
                    "armor2":0  
                },
                "ralsei": {
                    "weapon": 0,
                    "armor1":0,
                    "armor2":0
                },
                "noelle": {
                    "weapon": 0,
                    "armor1":0,
                    "armor2":0
                }
            },
            "items": [],
            "keyItems": [],
            "weapons": [],
            "armor": [],
            "storage": []
        }
            
        # Read the file into a list of lines for subsequent parsing
        fileList = file.readlines()
        if self.savePattern == "ch1":
            start = self.chapterData["dw_invStart"]
            end = self.chapterData["dw_invEnd"]
            items = fileList[start-1:end]
            
            # Check if the item counts match the expected values for chapter 1
            if self.chapterData["dw_invCount"]["item"] != 12 or \
                    self.chapterData["dw_invCount"]["keyItem"] != 12 or \
                    self.chapterData["dw_invCount"]["weapon"] != 12 or \
                    self.chapterData["dw_invCount"]["armor"] != 12:
                raise ValueError("Invalid item count in save file. Expected 12 items, key items, weapons, and armor.")
            
            # Read items, key items, weapons, and armor from the file
            # As this is a chapter 1 save file, 12 items of each is expected.
            for i in range(12):
                resDict["items"].append(int(items[i*4].strip()))
                resDict["keyItems"].append(int(items[i*4 + 1].strip()))
                resDict["weapons"].append(int(items[i*4 + 2].strip()))
                resDict["armor"].append(int(items[i*4 + 3].strip()))

            # Get equipped item data
            for character in ["kris", "susie", "ralsei"]:
                resDict["party"][character] = self._read_character_equipment(fileList, character)
            
        if self.savePattern == "ch2+":
            invStart = self.chapterData["dw_invStart"]
            invEnd = self.chapterData["dw_invEnd"]
            items = fileList[invStart-1:invEnd]
            
            # Check if the item counts match the expected values for chapter 2 and onwards
            if self.chapterData["dw_invCount"]["item"] != self.chapterData["dw_invCount"]["keyItem"]:
                raise ValueError("Invalid item count in save file. Expected equal item and key item counts.")
            
            # Read held items and key items from the file
            itemsAndKeyItems = items[:self.chapterData["dw_invCount"]["item"] * 2]
            for i in range(self.chapterData["dw_invCount"]["item"]):
                resDict["items"].append(int(itemsAndKeyItems[i*2].strip()))
                resDict["keyItems"].append(int(itemsAndKeyItems[i*2 + 1].strip()))
            
            # Check if the weapon and armor counts match the expected values for chapter 2 and onwards
            if self.chapterData["dw_invCount"]["weapon"] != self.chapterData["dw_invCount"]["armor"]:
                raise ValueError("Invalid weapon and armor count in save file. Expected equal weapon and armor counts.")
            
            # Read weapons and armor from the file
            armorAndWeapons = items[self.chapterData["dw_invCount"]["item"] * 2+2:]
            for i in range(self.chapterData["dw_invCount"]["weapon"]):
                resDict["weapons"].append(int(armorAndWeapons[i*2].strip()))
                resDict["armor"].append(int(armorAndWeapons[i*2 + 1].strip()))
            
            # Get equipped item data
            for character in ["kris", "susie", "ralsei", "noelle"]:
                resDict["party"][character] = self._read_character_equipment(fileList, character)
                
            
        # If storage is present, read it
        if "dw_storageStart" in self.chapterData and "dw_storageEnd" in self.chapterData:
            storageStart = self.chapterData["dw_storageStart"]
            storageEnd = self.chapterData["dw_storageEnd"]
            storageLength = self.chapterData["dw_invCount"]["storage"]
            
            # Check if the storage count matches the expected value
            if storageLength != storageEnd - storageStart + 1:
                raise ValueError(f"Invalid storage count in save file. Expected {storageLength} storage items instead of {storageEnd - storageStart + 1}.")
        
            storageItems = fileList[storageStart-1:storageEnd]
            resDict["storage"] = [int(item.strip()) for item in storageItems]
        
        return resDict

if __name__ == "__main__":
    runningDir = os.path.dirname(os.path.realpath(__file__))
    localAppData = os.getenv("LOCALAPPDATA") or ""
    os.environ["DR_SAVE_PATH"] = os.path.join(localAppData, "DELTARUNE")
    with open(os.path.join(runningDir, "app_config.json"), "r", encoding="utf-8") as v:
        cfg = json.load(v)
    
    chapter_slot = (4, 1)
    temp = Tk()
    temp.withdraw()

    popup = SaveFileEdit(temp, chapter_slot[0], chapter_slot[1], cfg["dw_invItems"], cfg[f"chapter{chapter_slot[0]}"], cfg, title="TEST")