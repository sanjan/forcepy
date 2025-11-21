"""Tests for Chatter module."""

import pytest

from forcepy.chatter import Chatter, extract_id, format_chatter_post


class TestExtractId:
    """Test extract_id function."""

    def test_extract_15_char_id(self):
        """Test extracting 15 character ID."""
        tail = "@[005xx0000012345] some text"
        mention, remaining = extract_id(tail)
        assert mention == "005xx0000012345"
        assert remaining == " some text"

    def test_extract_18_char_id(self):
        """Test extracting 18 character ID."""
        tail = "@[005xx0000012345ABC] some text"
        mention, remaining = extract_id(tail)
        assert mention == "005xx0000012345ABC"
        assert remaining == " some text"

    def test_no_closing_bracket(self):
        """Test when closing bracket is missing."""
        tail = "@[005xx0000012345"
        mention, remaining = extract_id(tail)
        assert mention == ""
        assert remaining == "@[005xx0000012345"

    def test_entity_link(self):
        """Test extracting entity link ID."""
        tail = "$[001xx0000012345] some text"
        entity_id, remaining = extract_id(tail)
        assert entity_id == "001xx0000012345"
        assert remaining == " some text"


class TestFormatChatterPost:
    """Test format_chatter_post function."""

    def test_plain_text(self):
        """Test plain text message."""
        segments = format_chatter_post("Hello World", break_on_newline=False)
        assert len(segments) == 1
        assert segments[0] == {"type": "Text", "text": "Hello World"}

    def test_bold_text(self):
        """Test bold formatting."""
        segments = format_chatter_post("<b>Bold</b>", break_on_newline=False)
        assert len(segments) == 3
        assert segments[0] == {"markupType": "Bold", "type": "MarkupBegin"}
        assert segments[1] == {"type": "Text", "text": "Bold"}
        assert segments[2] == {"markupType": "Bold", "type": "MarkupEnd"}

    def test_italic_text(self):
        """Test italic formatting."""
        segments = format_chatter_post("<i>Italic</i>", break_on_newline=False)
        assert segments[0]["markupType"] == "Italic"
        assert segments[1]["text"] == "Italic"

    def test_underline_text(self):
        """Test underline formatting."""
        segments = format_chatter_post("<u>Underlined</u>", break_on_newline=False)
        assert segments[0]["markupType"] == "Underline"
        assert segments[1]["text"] == "Underlined"

    def test_code_text(self):
        """Test code formatting."""
        segments = format_chatter_post("<code>code</code>", break_on_newline=False)
        assert segments[0]["markupType"] == "Code"
        assert segments[1]["text"] == "code"

    def test_mention(self):
        """Test mention with @[userId]."""
        segments = format_chatter_post("Hey @[005xx0000012345]!", break_on_newline=False)
        assert len(segments) == 3
        assert segments[0] == {"type": "Text", "text": "Hey "}
        assert segments[1] == {"type": "Mention", "id": "005xx0000012345"}
        assert segments[2] == {"type": "Text", "text": "!"}

    def test_entity_link(self):
        """Test entity link with $[recordId]."""
        segments = format_chatter_post("Check $[001xx0000012345]", break_on_newline=False)
        assert len(segments) == 2
        assert segments[0] == {"type": "Text", "text": "Check "}
        assert segments[1] == {"type": "EntityLink", "entityId": "001xx0000012345"}

    def test_multiple_mentions(self):
        """Test multiple mentions."""
        segments = format_chatter_post("@[005xx0000012345] and @[005xx0000054321]", break_on_newline=False)
        assert segments[0] == {"type": "Mention", "id": "005xx0000012345"}
        assert segments[1] == {"type": "Text", "text": " and "}
        assert segments[2] == {"type": "Mention", "id": "005xx0000054321"}

    def test_mixed_formatting_and_mentions(self):
        """Test combining formatting and mentions."""
        segments = format_chatter_post("<b>@[005xx0000012345]</b>", break_on_newline=False)
        assert segments[0]["markupType"] == "Bold"
        assert segments[1]["type"] == "Mention"
        assert segments[2]["markupType"] == "Bold"

    def test_hyperlink(self):
        """Test hyperlink formatting."""
        segments = format_chatter_post('<a href="https://example.com">Link</a>', break_on_newline=False)
        assert len(segments) == 3
        assert segments[0]["type"] == "MarkupBegin"
        assert segments[0]["markupType"] == "Hyperlink"
        assert segments[0]["url"] == "https://example.com"
        assert segments[1] == {"type": "Text", "text": "Link"}
        assert segments[2]["type"] == "MarkupEnd"

    def test_paragraph(self):
        """Test paragraph formatting."""
        segments = format_chatter_post("<p>Paragraph</p>", break_on_newline=False)
        assert segments[0]["markupType"] == "Paragraph"
        assert segments[1]["text"] == "Paragraph"

    def test_list(self):
        """Test list formatting."""
        segments = format_chatter_post("<ul><li>Item 1</li></ul>", break_on_newline=False)
        # Check for UnorderedList and ListItem markup
        markup_types = [s.get("markupType") for s in segments if "markupType" in s]
        assert "UnorderedList" in markup_types
        assert "ListItem" in markup_types

    def test_code_preserves_special_chars(self):
        """Test that code blocks don't parse mentions."""
        segments = format_chatter_post("<code>@[005xx0000012345]</code>", break_on_newline=False)
        # Should not create a mention inside code
        text_segments = [s for s in segments if s.get("type") == "Text"]
        assert any("@[005xx0000012345]" in s.get("text", "") for s in text_segments)

    def test_break_on_newline(self):
        """Test break_on_newline wraps lines in paragraphs when HTML is present."""
        # break_on_newline only activates when HTML tags are present
        segments = format_chatter_post("<b>Bold</b>\nLine 2", break_on_newline=True)
        # Should wrap lines in <p> tags when HTML is detected
        paragraph_begins = [s for s in segments if s.get("markupType") == "Paragraph"]
        assert len(paragraph_begins) > 0


class TestChatterClass:
    """Test Chatter class methods."""

    @pytest.fixture
    def mock_client(self, mocker):
        """Create a mock Salesforce client."""
        client = mocker.Mock()
        client.version = "53.0"
        client.http = mocker.Mock(return_value={"id": "0D5xx000000abcd", "success": True})
        return client

    @pytest.fixture
    def chatter(self, mock_client):
        """Create Chatter instance with mock client."""
        return Chatter(mock_client)

    def test_init(self, mock_client):
        """Test Chatter initialization."""
        chatter = Chatter(mock_client)
        assert chatter.client == mock_client
        assert chatter.base_url == "/services/data/v53.0/chatter"

    def test_post_simple(self, chatter, mock_client):
        """Test simple post."""
        chatter.post("Hello World")

        # Verify HTTP call
        mock_client.http.assert_called_once()
        call_args = mock_client.http.call_args
        assert call_args[0][0] == "POST"
        assert "/chatter/feed-elements" in call_args[0][1]
        assert "messageSegments" in call_args[1]["json"]["body"]

    def test_post_with_subject_id(self, chatter, mock_client):
        """Test post with subject ID."""
        chatter.post("Hello", subject_id="005xx0000012345")

        call_args = mock_client.http.call_args
        assert call_args[1]["json"]["subjectId"] == "005xx0000012345"

    def test_post_without_formatting(self, chatter, mock_client):
        """Test post without formatting."""
        chatter.post("<b>Test</b>", format_message=False)

        call_args = mock_client.http.call_args
        segments = call_args[1]["json"]["body"]["messageSegments"]
        # Should have only one text segment
        assert len(segments) == 1
        assert segments[0]["text"] == "<b>Test</b>"

    def test_post_to_group(self, chatter, mock_client):
        """Test posting to a group."""
        chatter.post_to_group("0F9xx000000abcd", "Hello group")

        call_args = mock_client.http.call_args
        assert call_args[1]["json"]["subjectId"] == "0F9xx000000abcd"

    def test_post_to_record(self, chatter, mock_client):
        """Test posting to a record."""
        chatter.post_to_record("001xx0000012345", "Hello record")

        call_args = mock_client.http.call_args
        assert call_args[1]["json"]["subjectId"] == "001xx0000012345"

    def test_comment(self, chatter, mock_client):
        """Test commenting on a feed element."""
        chatter.comment("0D5xx000000abcd", "Great post!")

        call_args = mock_client.http.call_args
        assert "0D5xx000000abcd" in call_args[0][1]
        assert "comments/items" in call_args[0][1]

    def test_like(self, chatter, mock_client):
        """Test liking a feed element."""
        chatter.like("0D5xx000000abcd")

        call_args = mock_client.http.call_args
        assert call_args[0][0] == "POST"
        assert "chatter-likes" in call_args[0][1]

    def test_unlike(self, chatter, mock_client):
        """Test unliking a feed element."""
        chatter.unlike("0D5xx000000abcd", "0T9xx000000xyz")

        call_args = mock_client.http.call_args
        assert call_args[0][0] == "DELETE"
        assert "0T9xx000000xyz" in call_args[0][1]

    def test_get_feed(self, chatter, mock_client):
        """Test getting a feed."""
        mock_client.http.return_value = {"elements": []}
        chatter.get_feed("news", "me", page_size=25)

        call_args = mock_client.http.call_args
        assert call_args[0][0] == "GET"
        assert "feeds/news/me" in call_args[0][1]
        assert call_args[1]["params"]["pageSize"] == 25

    def test_get_feed_element(self, chatter, mock_client):
        """Test getting a specific feed element."""
        chatter.get_feed_element("0D5xx000000abcd")

        call_args = mock_client.http.call_args
        assert call_args[0][0] == "GET"
        assert "0D5xx000000abcd" in call_args[0][1]

    def test_delete_feed_element(self, chatter, mock_client):
        """Test deleting a feed element."""
        chatter.delete_feed_element("0D5xx000000abcd")

        call_args = mock_client.http.call_args
        assert call_args[0][0] == "DELETE"

    def test_get_comments(self, chatter, mock_client):
        """Test getting comments."""
        mock_client.http.return_value = {"comments": []}
        chatter.get_comments("0D5xx000000abcd", page_size=50)

        call_args = mock_client.http.call_args
        assert "comments/items" in call_args[0][1]
        assert call_args[1]["params"]["pageSize"] == 50

    def test_delete_comment(self, chatter, mock_client):
        """Test deleting a comment."""
        chatter.delete_comment("0D5xx000000abcd", "0D7xx000000xyz")

        call_args = mock_client.http.call_args
        assert call_args[0][0] == "DELETE"
        assert "0D7xx000000xyz" in call_args[0][1]

    def test_get_groups(self, chatter, mock_client):
        """Test getting groups."""
        mock_client.http.return_value = {"groups": []}
        chatter.get_groups(page_size=100)

        call_args = mock_client.http.call_args
        assert "users/me/groups" in call_args[0][1]
        assert call_args[1]["params"]["pageSize"] == 100

    def test_get_group(self, chatter, mock_client):
        """Test getting a specific group."""
        chatter.get_group("0F9xx000000abcd")

        call_args = mock_client.http.call_args
        assert "groups/0F9xx000000abcd" in call_args[0][1]

    def test_page_size_limit(self, chatter, mock_client):
        """Test that page_size is capped at 100."""
        mock_client.http.return_value = {"elements": []}
        chatter.get_feed("news", "me", page_size=500)

        call_args = mock_client.http.call_args
        # Should be capped at 100
        assert call_args[1]["params"]["pageSize"] == 100
