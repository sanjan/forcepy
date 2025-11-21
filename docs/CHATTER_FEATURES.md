# Chatter Integration Features

## Overview

forcepy includes comprehensive Chatter integration with rich formatting, mentions, and entity tagging support using square bracket notation.

## Key Features

### 1. Entity Tagging with Square Brackets

```python
from forcepy import Chatter, Salesforce

sf = Salesforce(username='...', password='...')
chatter = Chatter(sf)

# @[userId] - Mention a user
chatter.post("Hey @[005xx0000012345], can you help?")

# $[recordId] - Link to a record
chatter.post("Check out this account: $[001xx0000012345]")

# Combine mentions and links
chatter.post("@[005xx0000012345] please review $[001xx0000012345]")
```

### 2. HTML Formatting Support

Supports full HTML formatting that's automatically converted to Chatter markup:

```python
# Bold, italic, underline
chatter.post("<b>Important:</b> <i>Please review</i> <u>ASAP</u>")

# Lists
chatter.post("""
<ul>
    <li>First item</li>
    <li>Second item</li>
</ul>
""")

# Code blocks
chatter.post("<code>SELECT Id FROM Account</code>")

# Hyperlinks
chatter.post('<a href="https://example.com">Click here</a>')
```

### 3. Post to Feeds, Groups, and Records

```python
# Post to your feed
chatter.post("Hello Chatter!")

# Post to a group
chatter.post_to_group("0F9xx000000abcd", "Team update!")

# Post to a record's feed
chatter.post_to_record("001xx0000012345", "New update on this account")
```

### 4. Comments and Likes

```python
# Comment on a post
chatter.comment("0D5xx000000xyz", "Great post!")

# Like a post
chatter.like("0D5xx000000xyz")

# Unlike a post
chatter.unlike("0D5xx000000xyz", "0T9xx000000abc")
```

### 5. Read Feeds and Comments

```python
# Get your news feed
feed = chatter.get_feed("news", "me", page_size=25)

# Get group feed
group_feed = chatter.get_feed("record", "0F9xx000000abcd")

# Get specific feed element
element = chatter.get_feed_element("0D5xx000000xyz")

# Get comments
comments = chatter.get_comments("0D5xx000000xyz")
```

### 6. Manage Groups

```python
# Get your groups
groups = chatter.get_groups()

# Get specific group details
group = chatter.get_group("0F9xx000000abcd")
```

## Supported HTML Tags

- **Text Formatting**: `<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<code>`, `<strike>`
- **Structure**: `<p>`, `<br>`, `<br />`
- **Lists**: `<ul>`, `<ol>`, `<li>`
- **Links**: `<a href="url">text</a>`

## Entity Tag Formats

### Mentions: @[userId]
- 15-character ID: `@[005xx0000012345]`
- 18-character ID: `@[005xx0000012345ABC]`

### Entity Links: $[recordId]
- Any Salesforce record: `$[001xx0000012345]`, `$[a0Axx000000abcd]`, etc.

## Advanced Example

```python
# Complex formatted post with mentions, links, and HTML
chatter.post("""
<b>Sprint Review - Week 45</b>

<p>Team updates:</p>
<ul>
    <li>@[005xx0000012345] completed feature X</li>
    <li>@[005xx0000054321] fixed bug in $[001xx0000012345]</li>
    <li>@[005xx0000067890] deployed to production</li>
</ul>

<p>See details: <a href="https://example.com/sprint">Sprint Dashboard</a></p>

<i>Next review: Monday 9 AM</i>
""")
```

## Benefits Over Other Libraries

- **Entity tagging**: Native support for @mentions and $record links with square brackets
- **HTML formatting**: Full HTML support that's automatically converted
- **Type hints**: Complete type hints for better IDE support
- **Comprehensive**: Covers all major Chatter operations
- **Clean API**: Simple, intuitive methods
- **Well-tested**: 35 tests with 96% coverage

## Testing

The Chatter module includes comprehensive tests covering:
- Entity ID extraction (15 and 18 char IDs)
- HTML to Chatter markup conversion
- All Chatter API operations
- Edge cases and error handling

Run tests with:
```bash
pytest tests/test_chatter.py -v
```

## Implementation Notes

- Entity tags (`@[...]`, `$[...]`) are only parsed when `format_message=True` (default)
- Tags inside `<code>` blocks are preserved as literal text
- Whitespace in HTML is normalized automatically
- Page sizes are automatically capped at 100 (Salesforce limit)

## See Also

- Example: `examples/chatter_integration.py`
- API Docs: `src/forcepy/chatter.py`
- Tests: `tests/test_chatter.py`

