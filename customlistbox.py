import re
from typing import Optional, Union

from tkinter import Widget, Toplevel, Frame, Label, Listbox, Scrollbar, Menu
from tkinter.constants import SINGLE, VERTICAL, LEFT, BOTH, RIGHT, Y, END, RAISED
import tkinter.messagebox as messagebox

class DraggableListbox(Listbox):
    """A Listbox with drag-and-drop functionality and context menu support."""
    
    def __init__(self, parent:Widget, dragManager:'DragManager', dw_invItems=None, chapterLimits=None, currentChapter=1, allowInternalSwap=True, appConfig=None, **kwargs):
        # Set default selectbackground if not provided
        if 'selectbackground' not in kwargs:
            if appConfig and 'colors' in appConfig:
                kwargs['selectbackground'] = appConfig['colors'].get('selectBackground', '#00c5ff')
            else:
                kwargs['selectbackground'] = '#00c5ff'
        super().__init__(parent, selectmode=SINGLE, **kwargs)
        
        # Configuration
        self.dragManager = dragManager
        self.dw_invItems = dw_invItems or {}
        self.chapterLimits = chapterLimits or {}
        self.currentChapter = currentChapter
        self.allowInternalSwap = allowInternalSwap
        self.appConfig = appConfig or {}
        self.colors = appConfig.get('colors', {}) if appConfig else {}
        
        # Item tracking
        self.itemTags = {}  # Maps index to item tag (type)
        self.itemIds = {}   # Maps index to item ID
        
        # Visual state
        self.originalBg = self.cget("bg")  # Store original background color
        
        self.setupBindings()
        
    def setupBindings(self) -> None:
        """Set up mouse event bindings for drag-and-drop and context menu."""
        self.bind("<Button-1>", self._onStartDrag)   # Left mouse button press (Listbox drag start)
        self.bind("<B1-Motion>", self._onDrag)       # Mouse movement with button held down (Dragging listbox item)
        self.bind("<ButtonRelease-1>", self._onDrop) # Left mouse button release (Dropping listbox item)
        self.bind("<Enter>", self._onEnterListbox)   # Mouse enters listbox
        self.bind("<Leave>", self._onLeaveListbox)   # Mouse leaves listbox
        self.bind("<Button-3>", self._onRightClick)  # Right mouse button press (Context menu)
        
    # Category mapping for item types
    CATEGORY_MAP = {
        "item": "items",
        "keyItem": "keyItems",
        "weapon": "weapons",
        "armor": "armor"
    }
    
    def _onRightClick(self, event) -> None:
        """Handle right-click to show Windows Explorer-style context menu"""
        index = self.nearest(event.y)
        
        if 0 <= index < self.size():
            # Highlight the right-clicked item
            self.selection_clear(0, END)
            self.selection_set(index)
            
            itemTag = self.getItemTag(index)
            if itemTag:
                # Get all items of this type
                category = self.CATEGORY_MAP.get(itemTag, "items")
                availableItems = self.dw_invItems.get(category, {})
                
                if not availableItems:
                    messagebox.showwarning("No Items", f"No {itemTag} items available")
                    return
                
                self._showContextMenu(event, index, itemTag, availableItems)
    
    def _getChapterForItem(self, itemId: int, itemType: str) -> int:
        """Determine which chapter an item was added in based on chapter limits from config"""
        item_id_int = int(itemId)
        typeKey = "item" if itemType == "items" else itemType
        
        # Get limits for this item type from all chapters
        chapter_limits = []
        for chapter_num in range(1, 8):  # Chapters 1-7
            chapter_key = f"chapter{chapter_num}"
            if chapter_key in self.chapterLimits:
                chapter_data = self.chapterLimits[chapter_key]
                if "dw_invItemIdLimit" in chapter_data and typeKey in chapter_data["dw_invItemIdLimit"]:
                    chapter_limits.append((chapter_num, chapter_data["dw_invItemIdLimit"][typeKey]))
        
        chapter_limits.sort()
        
        # Find which chapter this item belongs to
        for chapter_num, limit in chapter_limits:
            if item_id_int <= limit:
                return chapter_num
        
        # If item ID is higher than all limits, return the last chapter or default to 1
        return chapter_limits[-1][0] if chapter_limits else 1
    
    def _formatItemType(self, itemTag: str) -> str:
        """Convert camelCase item tag to Title Case (e.g., 'keyItem' -> 'Key Item')."""
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', itemTag).title()
    
    def _showContextMenu(self, event, index: int, itemTag: str, availableItems: dict) -> None:
        """Show a Windows Explorer-style context menu"""
        # Get custom highlight color from config
        selectColor = self.colors.get('selectBackground', '#00c5ff')
        
        # Create the context menu with custom highlight color
        context_menu = Menu(self, tearoff=0, activebackground=selectColor, activeborderwidth=0)
        
        # Add current item info at the top (disabled/grayed out)
        current_item_id = self.getItemId(index)
        current_name = self._getItemName(current_item_id, itemTag)
        context_menu.add_command(label=f"Current: {current_name} (ID: {current_item_id})", 
                                state="disabled", foreground="gray")
        context_menu.add_separator()
        
        # Add "Replace with..." submenu
        replace_menu = Menu(context_menu, tearoff=0, activebackground=selectColor, activeborderwidth=0)
        
        # Add "Clear Slot" option at the top (ID 0)
        replace_menu.add_command(
            label="Clear Slot",
            command=lambda: self._replaceItem(index, 0)
        )
        replace_menu.add_separator()
        
        # Filter items to only show current chapter and past chapters
        filtered_items = {}
        current_chapter = self._getCurrentChapter()
        
        for itemId, itemName in availableItems.items():
            item_id_int = int(itemId)
            # Skip ID 0 since we handle it separately above
            if item_id_int == 0:
                continue
                
            item_chapter = self._getChapterForItem(itemId, itemTag)
            # Only include items from current chapter or earlier
            if item_chapter <= current_chapter:
                filtered_items[itemId] = itemName
        
        # Group filtered items by chapter
        chapters = {}
        for itemId, itemName in filtered_items.items():
            chapter = self._getChapterForItem(itemId, itemTag)
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append((int(itemId), itemName))
        
        # Sort chapters and create submenus
        for chapter in sorted(chapters.keys()):
            chapter_items = sorted(chapters[chapter], key=lambda x: x[0])  # Sort by ID within chapter
            
            if len(chapters) > 1:  # Only create chapter submenus if there are multiple chapters
                chapter_menu = Menu(replace_menu, tearoff=0, activebackground=selectColor, activeborderwidth=0)
                
                for itemId, itemName in chapter_items:
                    chapter_menu.add_command(
                        label=f"ID {itemId}: {itemName}",
                        command=lambda id_val=itemId: self._replaceItem(index, id_val)
                    )
                
                replace_menu.add_cascade(label=f"Chapter {chapter}", menu=chapter_menu)
            else:
                # If only one chapter, add items directly
                for itemId, itemName in chapter_items:
                    replace_menu.add_command(
                        label=f"ID {itemId}: {itemName}",
                        command=lambda id_val=itemId: self._replaceItem(index, id_val)
                    )
        
        context_menu.add_cascade(label=f"Replace {self._formatItemType(itemTag)}...", menu=replace_menu)
        
        # Add separator and additional options
        context_menu.add_separator()
        context_menu.add_command(label="Cancel", command=lambda: context_menu.unpost())
        
        # Show the context menu at mouse position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _getCurrentChapter(self) -> int:
        """Get the current chapter number."""
        if hasattr(self, 'currentChapter'):
            return self.currentChapter
        
        if 'currentChapter' in self.chapterLimits:
            return self.chapterLimits['currentChapter']
        
        # Fallback: find the highest chapter with limits defined
        for chapter_num in range(7, 0, -1):
            if f"chapter{chapter_num}" in self.chapterLimits:
                return chapter_num
        
        return 1
    
    def _replaceItem(self, index: int, new_item_id: int) -> None:
        """Replace the item at the given index with a new item ID"""
        self.setItemId(index, new_item_id)
        
    def insertWithId(self, index: Union[int, str], itemId: int, tag: str) -> None:
        """Insert an item with an associated ID and tag, converting ID to display name"""
        # Get item name from app_config based on tag
        displayText = self._getItemName(itemId, tag)
        self.insert(index, displayText)
        
        # Get the actual index after insertion
        if index == END:
            actualIndex = self.size() - 1
        else:
            actualIndex = index
            
        self.itemIds[actualIndex] = itemId
        self.itemTags[actualIndex] = tag
        self._updateIndices()
    
    def _getItemName(self, itemId: Optional[int], tag: str) -> str:
        """Get item name from app_config based on ID and tag."""
        if itemId is None:
            return f"Unknown {tag} (None)"
        category = self.CATEGORY_MAP.get(tag, "items")
        itemDict = self.dw_invItems.get(category, {})
        return itemDict.get(str(itemId), f"Unknown {tag} ({itemId})")
    
    def deleteItem(self, index: int) -> None:
        """Delete an item and update internal tracking indices."""
        if index in self.itemTags:
            del self.itemTags[index]
        if index in self.itemIds:
            del self.itemIds[index]
        self.delete(index)
        self._updateIndices()
    
    def _updateIndices(self) -> None:
        """Update tag and ID indices after insertions/deletions."""
        newTags = {}
        newIds = {}
        for i in range(self.size()):
            # Find the tag and ID for this position
            for oldIndex, tag in self.itemTags.items():
                if oldIndex == i:
                    newTags[i] = tag
                    break
            for oldIndex, itemId in self.itemIds.items():
                if oldIndex == i:
                    newIds[i] = itemId
                    break
        self.itemTags = newTags
        self.itemIds = newIds
    
    def getItemTag(self, index: int) -> Optional[str]:
        """Get the tag for an item at the given index"""
        return self.itemTags.get(index, None)
    
    def getItemId(self, index: int) -> Optional[int]:
        """Get the ID for an item at the given index"""
        return self.itemIds.get(index, None)
    
    def setItemTag(self, index: int, tag: str) -> None:
        """Set the tag for an item at the given index"""
        self.itemTags[index] = tag
        
    def setItemId(self, index: int, itemId: int) -> None:
        """Set the ID for an item at the given index and update display"""
        self.itemIds[index] = itemId
        tag = self.getItemTag(index)
        if tag is None:
            tag = "item"  # Default fallback
        displayText = self._getItemName(itemId, tag)
        self.delete(index)
        self.insert(index, displayText)
        
    def setDropHighlight(self, enabled: bool = True) -> None:
        """Set the background color to indicate valid drop zone."""
        if enabled:
            color = self.colors.get('dropHighlight', 'lightgreen')
            self.config(bg=color)
        else:
            self.config(bg=self.originalBg)
    
    def setInvalidHighlight(self, enabled: bool = True) -> None:
        """Set the background color to indicate invalid drop zone."""
        if enabled:
            color = self.colors.get('invalidHighlight', 'lightcoral')
            self.config(bg=color)
        else:
            self.config(bg=self.originalBg)
    
    def clearHighlight(self) -> None:
        """Clear any highlighting and restore original background."""
        self.config(bg=self.originalBg)
        
    # Event handlers for drag and drop
    def _onStartDrag(self, event) -> None:
        self.dragManager.startDrag(self, event)
    
    def _onDrag(self, event) -> None:
        self.dragManager.onDrag(event)
    
    def _onDrop(self, event) -> None:
        self.dragManager.onDrop(event)
    
    def _onEnterListbox(self, event) -> None:
        self.dragManager.onEnterListbox(event)
    
    def _onLeaveListbox(self, event) -> None:
        self.dragManager.onLeaveListbox(event)

class DraggableScrollableListbox(Frame):
    """A scrollable wrapper for DraggableListbox with vertical scrollbar."""
    
    def __init__(self, parent, dragManager: 'DragManager', dw_invItems=None, chapterLimits=None, 
                 currentChapter=1, allowInternalSwap=True, appConfig=None, **kwargs):
        super().__init__(parent)
        
        # Create listbox and scrollbar
        self.listbox = DraggableListbox(self, dragManager, dw_invItems, chapterLimits, 
                                      currentChapter, allowInternalSwap, appConfig, **kwargs)
        self.scrollbar = Scrollbar(self, orient=VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        
        # Pack components
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)
    
    # Delegate methods to the inner listbox
    def insertWithId(self, index: Union[int, str], itemId: int, tag: str) -> None:
        """Insert an item with ID and tag."""
        self.listbox.insertWithId(index, itemId, tag)
        
    def deleteItem(self, index: int) -> None:
        """Delete an item."""
        self.listbox.deleteItem(index)
        
    def getItemTag(self, index: int) -> Optional[str]:
        """Get item tag at index."""
        return self.listbox.getItemTag(index)
    
    def getItemId(self, index: int) -> Optional[int]:
        """Get item ID at index."""
        return self.listbox.getItemId(index)
    
    def setItemTag(self, index: int, tag: str) -> None:
        """Set item tag at index."""
        self.listbox.setItemTag(index, tag)
        
    def setItemId(self, index: int, itemId: int) -> None:
        """Set item ID at index."""
        self.listbox.setItemId(index, itemId)

    def getListbox(self) -> DraggableListbox:
        """Get the inner listbox widget."""
        return self.listbox

class DragManager:
    """Manages drag and drop operations between DraggableListbox instances."""
    
    def __init__(self, root, appConfig=None):
        self.root = root
        self.appConfig = appConfig or {}
        self.colors = appConfig.get('colors', {}) if appConfig else {}
        self.listboxes = []
        self.page_navigation_buttons = []  # List of (button, callback) tuples
        
        # Variables to track dragging
        self.dragStartListbox: Optional[DraggableListbox] = None
        self.dragStartIndex: Optional[int] = None
        self.dragData = None
        self.dragTag = None
        self.dragId = None
        
        # Create drag visualization window (initially hidden)
        self.dragWindow = None
    
    def registerListbox(self, listbox: DraggableListbox) -> None:
        """Register a listbox with the drag manager."""
        self.listboxes.append(listbox)
    
    def registerPageButton(self, button, callback) -> None:
        """Register a page navigation button with the drag manager."""
        self.page_navigation_buttons.append((button, callback))
    
    def createDragWindow(self) -> None:
        """Create the drag visualization window"""
        self.dragWindow = Toplevel(self.root)
        self.dragWindow.wm_overrideredirect(True)
        self.dragWindow.wm_attributes("-topmost", True)
        defaultColor = self.colors.get('dragWindowDefault', 'lightblue')
        self.dragWindow.configure(bg=defaultColor)
        
        self.dragLabel = Label(self.dragWindow, text="", 
                                bg=defaultColor, fg="black", 
                                font=("Arial", 9), padx=8, pady=4,
                                relief=RAISED, borderwidth=2)
        self.dragLabel.pack()
        self.dragWindow.withdraw()
    
    def _updateDragWindowStyle(self, color: str) -> None:
        """Update drag window background color and relief style."""
        if self.dragWindow is not None:
            self.dragWindow.configure(bg=color)
            self.dragLabel.configure(bg=color, relief=RAISED)
    
    def _cancelDrag(self) -> None:
        """Cancel the current drag operation"""
        # Clear all highlights
        self._clearAllHighlights()
        
        # Hide the drag window
        if self.dragWindow is not None:
            self.dragWindow.withdraw()
        
        # Reset drag state and cursor
        if self.dragStartListbox:
            self.dragStartListbox.config(cursor="")
        self.dragStartListbox = None
        self.dragStartIndex = None
        self.dragData = None
        self.dragTag = None
        self.dragId = None
    
    def startDrag(self, sourceListbox: DraggableListbox, event) -> None:
        """Start a drag operation"""
        index = sourceListbox.nearest(event.y)
        
        if index >= 0 and index < sourceListbox.size():
            self.dragStartListbox = sourceListbox
            self.dragStartIndex = index
            self.dragData = sourceListbox.get(index)
            self.dragTag = sourceListbox.getItemTag(index)
            self.dragId = sourceListbox.getItemId(index)
            
            # Only allow dragging items with IDs
            if self.dragId is None:
                return
            
            # Visual feedback
            sourceListbox.selection_clear(0, END)
            sourceListbox.selection_set(index)
            sourceListbox.config(cursor="hand2")
            
            # Create drag window if it doesn't exist
            if self.dragWindow is None:
                self.createDragWindow()
            
            # Show and position the drag window with tag and ID info
            displayText = f"{self.dragData}"
            if self.dragTag:
                displayText += f" [ {self.dragTag} ]"
            if self.dragId is not None:
                displayText += f" (ID: {self.dragId})"
            
            self.dragLabel.config(text=displayText)
            defaultColor = self.colors.get('dragWindowDefault', 'lightblue')
            self._updateDragWindowStyle(defaultColor)
            
            x, y = self.root.winfo_pointerxy()
            if self.dragWindow is not None:
                self.dragWindow.geometry(f"+{x+10}+{y+10}")
                self.dragWindow.deiconify()  # Show the window
            
            # Highlight valid drop zones
            self._highlightValidDropZones()
    
    def _highlightValidDropZones(self) -> None:
        """Highlight all listboxes that can accept the dragged item"""
        if self.dragStartListbox is None or self.dragStartIndex is None:
            return
        
        for listbox in self.listboxes:
            # Check if same listbox and internal swapping not allowed
            isSameListbox = listbox == self.dragStartListbox
            if isSameListbox and not self.dragStartListbox.allowInternalSwap:
                listbox.setInvalidHighlight(True)
                continue
            
            # Check if any items in this listbox can be swapped
            canAccept = False
            for i in range(listbox.size()):
                # Skip the dragged item itself
                if isSameListbox and i == self.dragStartIndex:
                    continue
                
                targetId = listbox.getItemId(i)
                if targetId is not None and self.canSwapItems(self.dragStartListbox, self.dragStartIndex, listbox, i):
                    canAccept = True
                    break
            
            listbox.setDropHighlight(canAccept)
            if not canAccept:
                listbox.setInvalidHighlight(True)
    
    def _clearAllHighlights(self) -> None:
        """Clear highlighting from all listboxes"""
        for listbox in self.listboxes:
            listbox.setDropHighlight(False)
            listbox.setInvalidHighlight(False)
    
    def canSwapItems(self, sourceListbox: DraggableListbox, sourceIndex: int, targetListbox: DraggableListbox, targetIndex: int) -> bool:
        """Check if two items can be swapped based on their tags"""
        sourceTag = sourceListbox.getItemTag(sourceIndex)
        targetTag = targetListbox.getItemTag(targetIndex)
        
        # Items can be swapped if:
        # 1. Both have no tags (None)
        # 2. Both have the same tag
        return sourceTag == targetTag
    
    def _findActualListbox(self, widget) -> Optional[DraggableListbox]:
        """Find the actual listbox widget (handles scrollable containers)"""
        # If it's a DraggableListbox, return it
        if isinstance(widget, DraggableListbox):
            return widget
        
        # If it's a container (like DraggableScrollableListbox), check for listbox attribute
        if hasattr(widget, 'listbox') and isinstance(widget.listbox, DraggableListbox):
            return widget.listbox
            
        # Check if the widget is a child of a registered listbox
        for listbox in self.listboxes:
            if widget == listbox:
                return listbox
                
        return None
    
    def onDrag(self, event) -> None:
        """Handle drag motion"""
        # Handle drag motion if we have an active drag
        if self.dragStartListbox is not None and self.dragWindow is not None and self.dragStartIndex is not None:
            # Update drag window position
            x, y = self.root.winfo_pointerxy()
            self.dragWindow.geometry(f"+{x+10}+{y+10}")
            
            # Get the widget under the mouse cursor
            widget = self.root.winfo_containing(x, y)
            
            actualListbox = self._findActualListbox(widget)
            
            # Clear all selections first
            for listbox in self.listboxes:
                listbox.selection_clear(0, END)
            
            # Check if we're over a registered listbox
            if actualListbox is not None:
                # Convert screen coordinates to widget coordinates
                relativeY = y - actualListbox.winfo_rooty()
                
                # Get the index at this position
                index = actualListbox.nearest(relativeY)
                
                if 0 <= index < actualListbox.size():
                    # Check if target item has an ID
                    targetId = actualListbox.getItemId(index)
                    if targetId is None:
                        invalidColor = self.colors.get('invalidHighlight', 'lightcoral')
                        self._updateDragWindowStyle(invalidColor)
                        return
                    
                    # Check if drop is allowed
                    isSameListbox = actualListbox == self.dragStartListbox
                    allowDrop = not (isSameListbox and not self.dragStartListbox.allowInternalSwap)
                    allowDrop = allowDrop and self.canSwapItems(self.dragStartListbox, self.dragStartIndex, actualListbox, index)
                    
                    if allowDrop:
                        actualListbox.selection_set(index)
                        validColor = self.colors.get('dropHighlight', 'lightgreen')
                        self._updateDragWindowStyle(validColor)
                    else:
                        invalidColor = self.colors.get('invalidHighlight', 'lightcoral')
                        self._updateDragWindowStyle(invalidColor)
                else:
                    invalidColor = self.colors.get('invalidHighlight', 'lightcoral')
                    self._updateDragWindowStyle(invalidColor)
            else:
                invalidColor = self.colors.get('invalidHighlight', 'lightcoral')
                self._updateDragWindowStyle(invalidColor)
    
    def onDrop(self, event) -> None:
        """Handle drop operation"""
        if self.dragStartListbox is not None and self.dragStartIndex is not None:
            # Get the widget under the mouse cursor
            x, y = self.root.winfo_pointerxy()
            widget = self.root.winfo_containing(x, y)
            targetListbox = self._findActualListbox(widget)
            
            # Check if dropping on a registered listbox (must be registered with THIS drag manager)
            if targetListbox is not None and targetListbox in self.listboxes:
                relativeY = y - targetListbox.winfo_rooty()
                dropIndex = targetListbox.nearest(relativeY)
                
                # Validate drop conditions
                if (0 <= dropIndex < targetListbox.size() and
                    self.dragStartListbox.getItemId(self.dragStartIndex) is not None and
                    targetListbox.getItemId(dropIndex) is not None):
                    
                    isSameListbox = targetListbox == self.dragStartListbox
                    allowDrop = not (isSameListbox and not self.dragStartListbox.allowInternalSwap)
                    allowDrop = allowDrop and self.canSwapItems(self.dragStartListbox, self.dragStartIndex, targetListbox, dropIndex)
                    
                    if allowDrop:
                        # Perform the swap
                        startId = self.dragStartListbox.getItemId(self.dragStartIndex)
                        dropId = targetListbox.getItemId(dropIndex)
                        startTag = self.dragStartListbox.getItemTag(self.dragStartIndex)
                        dropTag = targetListbox.getItemTag(dropIndex)
                        
                        # Only proceed if all values are not None
                        if startId is not None and dropId is not None and startTag is not None and dropTag is not None:
                            self.dragStartListbox.setItemId(self.dragStartIndex, dropId)
                            self.dragStartListbox.setItemTag(self.dragStartIndex, dropTag)
                            
                            targetListbox.setItemId(dropIndex, startId)
                            targetListbox.setItemTag(dropIndex, startTag)
                        
                        # Update selection
                        for listbox in self.listboxes:
                            listbox.selection_clear(0, END)
                        targetListbox.selection_set(dropIndex)
        
        # Clear all highlights
        self._clearAllHighlights()
        
        # Hide the drag window
        if self.dragWindow is not None:
            self.dragWindow.withdraw()
        
        # Reset drag state and cursor
        if self.dragStartListbox:
            self.dragStartListbox.config(cursor="")
        self.dragStartListbox = None
        self.dragStartIndex = None
        self.dragData = None
        self.dragTag = None
        self.dragId = None
    
    def onEnterListbox(self, event) -> None:
        """Handle mouse entering a listbox during drag"""
        if self.dragStartListbox is not None:
            event.widget.config(cursor="hand2")
    
    def onLeaveListbox(self, event) -> None:
        """Handle mouse leaving a listbox during drag"""
        if self.dragStartListbox is not None:
            if event.widget != self.dragStartListbox:
                event.widget.config(cursor="")
