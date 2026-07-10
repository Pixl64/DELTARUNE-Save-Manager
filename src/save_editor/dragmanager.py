from tkinter import Toplevel, Label, RAISED
from tkinter.constants import END
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.save_editor.dragabblelistbox import DraggableListbox

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
        from src.save_editor.dragabblelistbox import DraggableListbox

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
