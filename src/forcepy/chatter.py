"""Chatter integration for forcepy.

Supports posting to Chatter feeds with rich formatting, mentions, and entity tags.
"""

from typing import Any, Optional


def extract_id(tail: str) -> tuple[str, str]:
    """Extract Salesforce ID from square bracket notation.

    Supports both 15 and 18 character IDs:
    - @[005xx0000012345] or @[005xx0000012345ABC]
    - $[001xx0000012345] or $[001xx0000012345ABC]

    Args:
        tail: String starting with bracket notation

    Returns:
        Tuple of (extracted_id, remaining_string)
    """
    mention = ""
    if len(tail) >= 18 and tail[17] == "]":
        mention = tail[2:17]
        tail = tail[18:]
    elif len(tail) >= 21 and tail[20] == "]":
        mention = tail[2:20]
        tail = tail[21:]
    return mention, tail


def format_chatter_post(message: str, break_on_newline: bool = True) -> list[dict[str, Any]]:
    """Format a message with HTML and entity tags into Chatter message segments.

    Supports:
    - HTML tags: <p>, <b>, <strong>, <i>, <em>, <u>, <code>, <strike>, <ul>, <ol>, <li>, <br>
    - Mentions: @[userId] - Tag a user (e.g., @[005xx0000012345])
    - Entity links: $[recordId] - Link to a record (e.g., $[001xx0000012345])
    - Hyperlinks: <a href="url">text</a>

    Args:
        message: Message with HTML and entity tags
        break_on_newline: Wrap plain newlines in <p> tags

    Returns:
        List of Chatter message segments

    Example:
        >>> segments = format_chatter_post("Hello @[005xx0000012345]! Check out $[001xx0000012345]")
        >>> # Returns segments for: text + mention + text + entity link
    """
    tags = {
        "<p>": {"markupType": "Paragraph", "type": "MarkupBegin"},
        "<b>": {"markupType": "Bold", "type": "MarkupBegin"},
        "<strong>": {"markupType": "Bold", "type": "MarkupBegin"},
        "<ul>": {"markupType": "UnorderedList", "type": "MarkupBegin"},
        "<ol>": {"markupType": "OrderedList", "type": "MarkupBegin"},
        "<li>": {"markupType": "ListItem", "type": "MarkupBegin"},
        "<i>": {"markupType": "Italic", "type": "MarkupBegin"},
        "<em>": {"markupType": "Italic", "type": "MarkupBegin"},
        "<u>": {"markupType": "Underline", "type": "MarkupBegin"},
        "<code>": {"markupType": "Code", "type": "MarkupBegin"},
        "<strike>": {"markupType": "Strikethrough", "type": "MarkupBegin"},
        "<br>": [
            {"markupType": "Paragraph", "type": "MarkupBegin"},
            {"text": "\u00a0", "type": "Text"},  # Non-breaking space
            {"markupType": "Paragraph", "type": "MarkupEnd"},
        ],
    }

    # Add closing tags
    for tag, value in list(tags.items()):
        if isinstance(value, dict):
            value = dict(value)
            value["type"] = "MarkupEnd"
        tags["</" + tag[1:]] = value
    tags["<br />"] = tags["<br>"]
    tag_names = tuple(tags.keys())

    # Pre-format message to preserve text format if HTML is present
    if break_on_newline:
        for tag in tags:
            if tag in message:
                lines = []
                for line in message.splitlines():
                    if not line.strip():
                        line = "<br>"
                    elif "<" not in line:
                        line = f"<p>{line}</p>"
                    lines.append(line)
                message = "\n".join(lines)
                break

    # Process message into segments
    segments = []
    tail = message
    inside_code = False

    while tail:
        tag_found = False
        for tag in tags:
            if tail.startswith(tag):
                if tag == "<code>":
                    inside_code = True
                tail = tail[len(tag) :]
                if isinstance(tags[tag], list):
                    segments.extend(tags["<br>"])
                    continue
                segments.append(tags[tag])
                tag_found = True
                break

        if tag_found and not inside_code:
            continue

        text = ""
        while tail:
            # Handle mentions: @[userId]
            if not inside_code and tail.startswith("@["):
                mention, tail = extract_id(tail)
                if mention:
                    if text:
                        segments.append({"text": text, "type": "Text"})
                        text = ""
                    segments.append({"type": "Mention", "id": mention})
                    break

            # Handle entity links: $[recordId]
            if not inside_code and tail.startswith("$["):
                entity_id, tail = extract_id(tail)
                if entity_id:
                    if text:
                        segments.append({"text": text, "type": "Text"})
                        text = ""
                    segments.append({"type": "EntityLink", "entityId": entity_id})
                    break

            # Handle hyperlinks: <a href="url">text</a>
            if not inside_code and tail.startswith("<a href="):
                if text:
                    segments.append({"text": text, "type": "Text"})
                    text = ""
                link, tail = tail.split("</a>", 1)
                url, name = link.split(">", 1)
                url = url.split("=", 1)[1][1:-1]  # Extract URL from href="url"
                segments.extend(
                    [
                        {"markupType": "Hyperlink", "altText": name, "type": "MarkupBegin", "url": url},
                        {"text": name, "type": "Text"},
                        {"markupType": "Hyperlink", "type": "MarkupEnd"},
                    ]
                )
                break

            # Check for closing tags
            if (inside_code and tail.startswith("</code>")) or (not inside_code and tail.startswith(tag_names)):
                inside_code = False
                break

            text += tail[0]
            tail = tail[1:]

        if text:
            segments.append({"text": text, "type": "Text"})

    return segments


class Chatter:
    """Chatter API client for Salesforce.

    Provides methods for posting to feeds, commenting, and liking.

    Example:
        >>> from forcepy import Salesforce
        >>> sf = Salesforce(username='...', password='...')
        >>> chatter = Chatter(sf)
        >>>
        >>> # Post to your feed
        >>> chatter.post("Hello Chatter!")
        >>>
        >>> # Post with mentions and entity links
        >>> chatter.post("Hey @[005xx0000012345]! Check out $[001xx0000012345]")
        >>>
        >>> # Post to a group
        >>> chatter.post_to_group("0F9xx000000abcd", "Hello group!")
    """

    def __init__(self, client: Any):
        """Initialize Chatter client.

        Args:
            client: Authenticated Salesforce client instance
        """
        self.client = client
        self.base_url = f"/services/data/v{client.version}/chatter"

    def post(
        self,
        text: str,
        subject_id: Optional[str] = None,
        format_message: bool = True,
        visibility: str = "AllUsers",
    ) -> dict[str, Any]:
        """Post a message to Chatter.

        Args:
            text: Message text (supports HTML and entity tags if format_message=True)
            subject_id: ID of user/group to post to (defaults to current user's feed)
            format_message: Parse HTML and entity tags (default: True)
            visibility: Post visibility - "AllUsers" or "InternalUsers" (default: "AllUsers")

        Returns:
            Feed element response from Salesforce

        Example:
            >>> chatter.post("Hello <b>world</b>!")
            >>> chatter.post("Hey @[005xx0000012345]!")
            >>> chatter.post("Check $[001xx0000012345]", subject_id="005xx0000054321")
        """
        if format_message:
            segments = format_chatter_post(text)
        else:
            segments = [{"type": "Text", "text": text}]

        # If no subject_id, post to current user's feed
        if subject_id is None:
            subject_id = "me"

        payload = {
            "body": {"messageSegments": segments},
            "feedElementType": "FeedItem",
            "subjectId": subject_id,
            "visibility": visibility,
        }

        url = f"{self.base_url}/feed-elements"
        return self.client.http("POST", url, json=payload)

    def post_to_group(self, group_id: str, text: str, format_message: bool = True) -> dict[str, Any]:
        """Post a message to a Chatter group.

        Args:
            group_id: Chatter group ID (starts with 0F9)
            text: Message text
            format_message: Parse HTML and entity tags (default: True)

        Returns:
            Feed element response from Salesforce

        Example:
            >>> chatter.post_to_group("0F9xx000000abcd", "Hello team!")
        """
        return self.post(text, subject_id=group_id, format_message=format_message)

    def post_to_record(self, record_id: str, text: str, format_message: bool = True) -> dict[str, Any]:
        """Post a message to a record's Chatter feed.

        Args:
            record_id: Salesforce record ID
            text: Message text
            format_message: Parse HTML and entity tags (default: True)

        Returns:
            Feed element response from Salesforce

        Example:
            >>> chatter.post_to_record("001xx0000012345", "Update on this account")
        """
        return self.post(text, subject_id=record_id, format_message=format_message)

    def comment(
        self, feed_element_id: str, text: str, format_message: bool = True
    ) -> dict[str, Any]:
        """Comment on a feed element.

        Args:
            feed_element_id: Feed element ID to comment on
            text: Comment text
            format_message: Parse HTML and entity tags (default: True)

        Returns:
            Comment response from Salesforce

        Example:
            >>> chatter.comment("0D5xx000000abcd", "Great post!")
        """
        if format_message:
            segments = format_chatter_post(text)
        else:
            segments = [{"type": "Text", "text": text}]

        payload = {"body": {"messageSegments": segments}}

        url = f"{self.base_url}/feed-elements/{feed_element_id}/capabilities/comments/items"
        return self.client.http("POST", url, json=payload)

    def like(self, feed_element_id: str) -> dict[str, Any]:
        """Like a feed element.

        Args:
            feed_element_id: Feed element ID to like

        Returns:
            Like response from Salesforce

        Example:
            >>> chatter.like("0D5xx000000abcd")
        """
        url = f"{self.base_url}/feed-elements/{feed_element_id}/capabilities/chatter-likes/items"
        return self.client.http("POST", url, json={})

    def unlike(self, feed_element_id: str, like_id: str) -> None:
        """Unlike a feed element.

        Args:
            feed_element_id: Feed element ID
            like_id: Like ID to remove

        Example:
            >>> chatter.unlike("0D5xx000000abcd", "0T9xx000000xyz")
        """
        url = f"{self.base_url}/feed-elements/{feed_element_id}/capabilities/chatter-likes/items/{like_id}"
        self.client.http("DELETE", url)

    def get_feed(
        self,
        feed_type: str = "news",
        subject_id: str = "me",
        page_size: int = 25,
    ) -> dict[str, Any]:
        """Get feed elements from a feed.

        Args:
            feed_type: Type of feed - "news", "company", "groups", "people", "record", etc.
            subject_id: Subject ID for the feed (user ID, group ID, record ID, or "me")
            page_size: Number of items per page (default: 25, max: 100)

        Returns:
            Feed response with elements

        Example:
            >>> # Get my news feed
            >>> chatter.get_feed("news", "me")
            >>>
            >>> # Get group feed
            >>> chatter.get_feed("record", "0F9xx000000abcd")
        """
        url = f"{self.base_url}/feeds/{feed_type}/{subject_id}/feed-elements"
        params = {"pageSize": min(page_size, 100)}
        return self.client.http("GET", url, params=params)

    def get_feed_element(self, feed_element_id: str) -> dict[str, Any]:
        """Get a specific feed element.

        Args:
            feed_element_id: Feed element ID

        Returns:
            Feed element details

        Example:
            >>> element = chatter.get_feed_element("0D5xx000000abcd")
        """
        url = f"{self.base_url}/feed-elements/{feed_element_id}"
        return self.client.http("GET", url)

    def delete_feed_element(self, feed_element_id: str) -> None:
        """Delete a feed element.

        Args:
            feed_element_id: Feed element ID to delete

        Example:
            >>> chatter.delete_feed_element("0D5xx000000abcd")
        """
        url = f"{self.base_url}/feed-elements/{feed_element_id}"
        self.client.http("DELETE", url)

    def get_comments(self, feed_element_id: str, page_size: int = 25) -> dict[str, Any]:
        """Get comments on a feed element.

        Args:
            feed_element_id: Feed element ID
            page_size: Number of comments per page (default: 25, max: 100)

        Returns:
            Comments response

        Example:
            >>> comments = chatter.get_comments("0D5xx000000abcd")
        """
        url = f"{self.base_url}/feed-elements/{feed_element_id}/capabilities/comments/items"
        params = {"pageSize": min(page_size, 100)}
        return self.client.http("GET", url, params=params)

    def delete_comment(self, feed_element_id: str, comment_id: str) -> None:
        """Delete a comment.

        Args:
            feed_element_id: Feed element ID
            comment_id: Comment ID to delete

        Example:
            >>> chatter.delete_comment("0D5xx000000abcd", "0D7xx000000xyz")
        """
        url = f"{self.base_url}/feed-elements/{feed_element_id}/capabilities/comments/items/{comment_id}"
        self.client.http("DELETE", url)

    def get_groups(self, page_size: int = 25) -> dict[str, Any]:
        """Get Chatter groups the current user is a member of.

        Args:
            page_size: Number of groups per page (default: 25, max: 100)

        Returns:
            Groups response

        Example:
            >>> groups = chatter.get_groups()
            >>> for group in groups['groups']:
            ...     print(group['name'])
        """
        url = f"{self.base_url}/users/me/groups"
        params = {"pageSize": min(page_size, 100)}
        return self.client.http("GET", url, params=params)

    def get_group(self, group_id: str) -> dict[str, Any]:
        """Get details about a specific Chatter group.

        Args:
            group_id: Chatter group ID

        Returns:
            Group details

        Example:
            >>> group = chatter.get_group("0F9xx000000abcd")
            >>> print(group['name'])
        """
        url = f"{self.base_url}/groups/{group_id}"
        return self.client.http("GET", url)

