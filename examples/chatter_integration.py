"""Chatter integration examples for forcepy."""

from forcepy import Chatter, Salesforce

# Initialize client (auto-authenticates)
sf = Salesforce(username="your-username@example.com", password="your-password-with-security-token")

# Create Chatter client
chatter = Chatter(sf)

print("=== Basic Chatter Posts ===")

# Simple post to your feed
response = chatter.post("Hello Chatter from forcepy!")
print(f"Posted to feed: {response['id']}")

# Post with HTML formatting
chatter.post(
    """
    <b>Important Update</b>
    <p>This is a formatted post with:</p>
    <ul>
        <li>Bold text</li>
        <li>Paragraphs</li>
        <li>Lists</li>
    </ul>
    """
)

# Post with inline formatting
chatter.post("This is <b>bold</b>, this is <i>italic</i>, and this is <u>underlined</u>.")

print("\n=== Mentions and Entity Tags ===")

# Mention a user (replace with actual user ID starting with 005)
user_id = "005xx0000012345"
chatter.post(f"Hey @[{user_id}], can you review this?")

# Link to a record (replace with actual record ID)
account_id = "001xx0000012345"
chatter.post(f"Check out this account: $[{account_id}]")

# Combine mentions and entity links
chatter.post(f"@[{user_id}] please review $[{account_id}] - looks important!")

print("\n=== Post to Groups and Records ===")

# Post to a Chatter group (replace with actual group ID starting with 0F9)
group_id = "0F9xx000000abcd"
chatter.post_to_group(group_id, "Hello team! This is a group update.")

# Post to a record's Chatter feed
chatter.post_to_record(account_id, "New update on this account")

print("\n=== Comments and Likes ===")

# Post something and then comment on it
post_response = chatter.post("This is a test post")
feed_element_id = post_response["id"]

# Add a comment
comment_response = chatter.comment(feed_element_id, "Great post!")
print(f"Added comment: {comment_response['id']}")

# Like the post
like_response = chatter.like(feed_element_id)
print(f"Liked post: {like_response['id']}")

print("\n=== Reading Feeds ===")

# Get your news feed
news_feed = chatter.get_feed("news", "me", page_size=10)
print(f"Found {len(news_feed['elements'])} items in news feed")

for element in news_feed["elements"][:3]:
    print(f"  - {element['body']['text'][:50]}...")

# Get group feed
group_feed = chatter.get_feed("record", group_id, page_size=10)
print(f"\nFound {len(group_feed['elements'])} items in group feed")

# Get specific feed element
element = chatter.get_feed_element(feed_element_id)
print(f"\nFeed element: {element['body']['text']}")

print("\n=== Complex Formatted Posts ===")

# Post with multiple formatting types
chatter.post(
    """
    <b>Sprint Review - Week 45</b>

    <p>Team updates:</p>
    <ul>
        <li>@[{user_id1}] completed feature X</li>
        <li>@[{user_id2}] fixed bug in $[{record_id}]</li>
        <li>@[{user_id3}] deployed to production</li>
    </ul>

    <p>Key metrics:</p>
    <ol>
        <li><b>Velocity:</b> 45 points</li>
        <li><b>Bugs:</b> 3 resolved</li>
        <li><b>Deployment:</b> Successful</li>
    </ol>

    <p>See details: <a href="https://example.com/sprint">Sprint Dashboard</a></p>

    <i>Next review: Monday 9 AM</i>
    """.replace(
        "{user_id1}", "005xx0000012345"
    )
    .replace("{user_id2}", "005xx0000054321")
    .replace("{user_id3}", "005xx0000067890")
    .replace("{record_id}", "001xx0000012345")
)

print("\n=== Working with Groups ===")

# Get all your groups
groups = chatter.get_groups(page_size=50)
print(f"\nYou are a member of {len(groups.get('groups', []))} groups:")

for group in groups.get("groups", [])[:5]:
    print(f"  - {group['name']} (ID: {group['id']})")

# Get specific group details
if groups.get("groups"):
    first_group = groups["groups"][0]
    group_details = chatter.get_group(first_group["id"])
    print(f"\nGroup: {group_details['name']}")
    print(f"  Members: {group_details.get('memberCount', 'N/A')}")
    print(f"  Description: {group_details.get('description', 'No description')[:100]}")

print("\n=== Advanced: Entity Tags Only (No Formatting) ===")

# Use format_message=False to send raw text without parsing
chatter.post("This <b>won't</b> be bold and @[123] won't be a mention", format_message=False)

print("\n=== Cleanup ===")

# Delete a feed element (uncomment to actually delete)
# chatter.delete_feed_element(feed_element_id)

# Delete a comment (uncomment to actually delete)
# chatter.delete_comment(feed_element_id, comment_id)

print("\nChatter examples complete!")

