# Task Detail Page with Categories

## Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to tasks                                             │
├─────────────────────────────────────────────────────────────┤
│ ☐ [Task Title Input Field]                    [▶ start]    │
│    [HEALTH] [CAREER] [LEARNING]                            │
├─────────────────────────────────────────────────────────────┤
│ 📝 Description:                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Add description...                                     │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [🗑️ Delete]                    [Save ⌘↵]                   │
└─────────────────────────────────────────────────────────────┘
```

## Category Badge Styles

### Health Category
- **Background**: Light green (`#e8f5e8`)
- **Text**: Dark green (`#2d5a2d`)
- **Style**: `HEALTH` (uppercase, small font)

### Career Category  
- **Background**: Light blue (`#e3f2fd`)
- **Text**: Dark blue (`#1565c0`)
- **Style**: `CAREER` (uppercase, small font)

### Learning Category
- **Background**: Light orange (`#fff3e0`)
- **Text**: Dark orange (`#ef6c00`)
- **Style**: `LEARNING` (uppercase, small font)

## Implementation Details

### HTML Structure
```html
<div class="task-title-header">
    <div class="task-checkbox-large">...</div>
    <div class="task-title-section">
        <input type="text" class="task-title-h1" id="detail-title">
        <div class="task-categories-detail" id="task-categories-detail">
            <!-- Categories rendered here -->
        </div>
    </div>
    <div class="task-title-actions">...</div>
</div>
```

### JavaScript Rendering
```javascript
_renderCategoriesInDetail(container, categories) {
    container.innerHTML = '';
    categories.forEach(category => {
        const badge = document.createElement('span');
        badge.className = `category-badge-detail category-${category}`;
        badge.textContent = category;
        container.appendChild(badge);
    });
}
```

### CSS Classes
- `.task-title-section` - Flex container for title and categories
- `.task-categories-detail` - Container for category badges
- `.category-badge-detail` - Base badge styling
- `.category-badge-detail.category-{name}` - Category-specific colors

## Features

✅ **Subtitle Display**: Categories appear as subtitles below the task title
✅ **Visual Distinction**: Each category has distinct colors and styling
✅ **Responsive Layout**: Categories wrap to multiple lines if needed
✅ **Real-time Updates**: Categories update when task data changes
✅ **Consistent Styling**: Matches the overall app design language
