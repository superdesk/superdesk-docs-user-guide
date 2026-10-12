# Defining Publishing in Superdesk

There are several steps to defining publishing in Superdesk. This chapter provides an overview of all the various modules to consider when publishing from Superdesk. This chapter is presented independently from the Superdesk Publisher component, which is an optional add-on to Superdesk.

The first step to publishing in Superdesk allows users to create automatic rules that are used to group published news items together. This means that you can use one instance of Superdesk to publish specific content to multiple destinations. These rules are called Content Filters.

Products are then created based on the application of those Content Filters. The simplest Product would be a Product with no Content Filters applied. In that case, every item that is published will be part of the Product. Products also define the delivery method of the content that is being published.

The next step is to set up Subscribers. Setting up Subscribers lets you link Products with Destinations. Subscribers might be news agency customers, but in the world of digital publishing you can think of them as publications. For each Subscriber, you can define the Products. Products are how the news items are sent to your Subscribers, including formats and delivery methods, and the Destination to where they should be published.

Once you’ve attempted to publish your items, you can check the details or resend the item from the Publish Queue. Once successfully published to your Subscribers, all of your news items will be saved in your Legal Archive.

{% stepper %}
{% step %}
### Make Content Filters

Content Filters allow you to create a series of criteria through which Superdesk can narrow down the news items and create news item groupings. These Content Filters allow you to build various Products for distribution. You can use any number of Filter Conditions, or Content Filters to automatically select the content for the Product.

To get started with Content Filters, click on the Hamburger menu > Settings > Content Filter. You will notice three tabs along the top of the Content Filters pane: Filters, Filter Conditions and Filter Search.

![](<../../.gitbook/assets/image341 b493d9cc9472a9b1178698804e406aeb.png>)

Before you can apply a Content Filter, you must first create at least one Filter Condition.

To create a new Filter Condition, click the Filter Conditions tab, then click the + ADD NEW button in the top right corner. A new window will open.

![](<../../.gitbook/assets/image379 ac93da9575de410f0889a736a14850fd.png>)

* NAME: Label for the filter condition; descriptive names help other users understand the filter.
*   FIELD: Select which metadata field of the item to look at when filtering. The complete list of your instance’s available metadata fields is shown below:

    ![](<../../.gitbook/assets/image380 9ae67ebfaf941301c7d1ed186e0bd924.png>)
* OPERATOR: Logical operators depend on the FIELD chosen. For controlled vocabularies: in / nin (not in). For text fields: like, notlike, startswith, endswith, etc.
*   VALUES: Varies by FIELD. You might input free text or choose from a dropdown. Selecting multiple values produces an OR (value1 OR value2).

    ![](<../../.gitbook/assets/image332 295aad83931a5b78625554b7aeee5179.png>)

Click the square Create icon in the values section to add multiple values. To remove a value, mouse-over and click the ‘x’. Once you’ve entered NAME, FIELD, OPERATOR and VALUES, save the Filter Condition.

#### Assemble and test Content Filters

To create a new Content Filter, click the FILTERS tab, then click the + ADD NEW button in the top right of the Filters tab.

Note that Content Filters can be made up of a single condition or multiple conditions. For clarity, the NAME of the Content Filter should reflect the conditions it uses.

![](<../../.gitbook/assets/image256 e521d66d4ecff794b4d3b8537c969d93.png>)

* Global Block — When a filter is configured as a Global Block the content it defines will be blocked by default to all Subscribers. It is unblocked for specific Subscribers by deactivating it on the Applied Global Block Filters tab of the Subscriber form.
* Archived Block — Allows definition of a filter or filters to control what content is actually sent to the Archive, and what is deleted on expiry.

A single Filter Statement can search for multiple overlapping conditions. Add multiple conditions to the same Filter Statement (these combine with AND). Click ADD FILTER STATEMENT to add another Filter Statement (separate statements combine with OR).

![](<../../.gitbook/assets/image11 5a841db764fe976389379dbc4604456b.png>) ![](<../../.gitbook/assets/image360 a0b057c743f11f280cc02708fc2faa5b.png>)

FILTER PREVIEW shows the constructed query. Conditions in the same Filter Statement join with AND; separate Filter Statements join with OR. You can also use other Content Filters within a query (Condition X AND Filter Y). You can have any number of Filter Statements in a single Content Filter, but you can only apply one Filter per Product.

#### Testing the Content Filter

You can test the filter by copying an article GUID (from the article information tab in the article editing window) and pasting it into the Filter Test field at the bottom of the window. You will see whether the test article matches the Filter Condition.

![](<../../.gitbook/assets/image316 a0701c25e3eb5c8daf09a25dde7efc7b.png>)

#### Filter Search

The Filter Search tab shows which existing Content Filters contain your query Conditions and whether they are in use (and where). This helps before editing or deleting a Filter Condition.

Select FIELD, OPERATOR and VALUE used to create the Condition, then click SEARCH. The results show which Conditions match, which Content Filters contain them, and which Subscribers use those Content Filters.

![](<../../.gitbook/assets/image309 6b0abcbaa7bbfa066c98aaa241178db2.png>)

#### Edit, test or delete an existing Content Filter

Once created, Content Filters appear in the Filters tab. Hover over a Filter to see options to test, edit or delete it.

![](<../../.gitbook/assets/image136 2bc39bbb5ca125fe0148467399ad7052.png>)

Testing (checkmark icon) opens a window listing all articles that match the Filter conditions. You can also view non-matching articles by selecting the Non-Matching parameter.
{% endstep %}

{% step %}
### Internal Destinations (optional)

Internal Destinations route a copy of a published article to Desk(s) so you can reuse content without recreating it. Common uses include providing content to translators or creating shortened versions for further distribution.

Configure Internal Destinations at Hamburger menu > Settings > Internal Destinations.

![](<../../.gitbook/assets/image210 545bea2685f2cd0e69c597985b642841.png>)

When publishing, if Internal Destinations are configured, the article will be published to Subscribers and copied to the designated Desk(s) as defined. The story being published is copied and sent to a selected Desk. The story is checked against Content Filters and publishing occurs only if the content matches filter criteria.

Users can select Desk, Stage, and an optional macro to run on the content (macros typically modify content metadata).

To create an Internal Destination, click the Create icon in the top-right corner of the Internal Destinations pane.

![](<../../.gitbook/assets/image19 67889ff4b525dda00f98cb72d0a43a71.png>)

Example: news items matching "Desk = Karel" Content Filter are copied and sent to "Ontario" Desk: "Working" Stage, with an "Extract Html Macro" applied. Internal Destinations can be enabled/disabled with the Active toggle in the Edit Destination window.
{% endstep %}

{% step %}
### Creating Products

Products can be thought of as another layer of Content Filters. A Product might apply a Content Filter and further define territorial restrictions. Products can also apply the inverse of a Content Filter as a blocking filter.

![](<../../.gitbook/assets/image315 c0298f32408879642a33e7adf729f8da.png>)

Access Products at Hamburger menu > Settings > Products.

The Product Management pane lists current Products; mouse-over and click the pencil icon to edit.

![](<../../.gitbook/assets/image316 a0701c25e3eb5c8daf09a25dde7efc7b.png>)

Click + ADD NEW to create a Product. The simplest Product uses no filters — give it a name and all published content becomes part of the Product.

Fields:

* Product Name — Superdesk-internal name (mandatory).
* Product Description — Superdesk-internal description (optional).
* Product Type — Choose between API, Direct or Both.
* Product Codes — Assign proprietary descriptors/designators for upstream use.
* Content Filter — One filter per Product. If none selected, every published item in the instance can be sent to subscribers. If a Content Filter is selected, choose Content Filter Type: Permitting or Blocking.
* Content Filter Type — Permitting: allow only articles matching conditions. Blocking: prevent articles matching conditions from being selected (all but Filter XY).
* Target Regions — If configured, narrow Product by region; only selected regions receive the Product.
{% endstep %}

{% step %}
### Define Subscribers

Admins define Subscribers at Hamburger menu > Settings > Subscribers.

In Content Flow > Settings you define:

* Subscribers (to whom)
* Products (what they should receive)
* Destinations (where to send it)
* Formats (how it should be sent)

Subscribers are customers; each Subscriber can receive multiple Products to any number of Destinations (e.g., website, mobile app).

To add a Subscriber, click + ADD NEW in the Subscribers pane.

Many values in these menus map to controlled vocabularies defined in .../server/data/vocabularies.json. Example:

{% code title="vocabularies.json" %}
```json
{
  "is_active": true,
  "name": "All",
  "qcode": "all",
  "formats": [
    {"name": "NTBNITF", "qcode": "ntbnitf"},
    {"name": "NINJS", "qcode": "ninjs"},
    {"name": "AAP NewsML 1.2", "qcode": "newsml12"},
    {"name": "NewsML G2", "qcode": "newsmlg2"}
  ]
}
```
{% endcode %}

Typical Subscriber fields and settings:

* Status: Active / inactive.
* Email to broadcast kill events: Email used to send notifications on "killed" articles. Required (fill a valid email even if not using kills).
* Target type: Configured options (digital, paper, both, etc.).
* Media type: Configured options (media, non-media).
* Subscriber Codes: Assign subscriber-specific tokens/keys for upstream platforms.
* Targetable by Users: If enabled, editors can select the Subscriber when creating a story and send it directly even if the story doesn't match Subscriber Products.
* Products: Select multiple Products; if none selected, all published news items can be sent to this Subscriber.

![](<../../.gitbook/assets/image397 bdb35624ab9b779edafd31e79b2925b1.png>)

Sequence number settings: Transmission Sequence Numbers are a range of IDs in the Publish Queue passed to end users as part of delivered document formats. Historically used to detect transmission breaks; commonly run 1-999 or 1-9999 with a rollover. Sequence numbers usually avoid repetition within a 24-hour news cycle.

![](<../../.gitbook/assets/image229 90573d4e22c520faca5955c97e92a603.png>)

Destination: Destinations are the "where" in publishing. You can add multiple Destinations per Subscriber.

Delivery Type: Select from configured formats and delivery types; additional fields may appear depending on selection. To add another Destination, click + ADD NEW DESTINATION. For Content-API-only Subscribers, adding a Destination is not required.
{% endstep %}

{% step %}
### Publish

When you click PUBLISH in Superdesk, it sends news items through Content Filters to determine which Subscribers receive the item. Check the Publish Queue for details (Headline, Destination, Subscriber, status).
{% endstep %}

{% step %}
### Check Publish Queue

The Publish Queue lists published items and destinations. Access it from the Hamburger menu.

![](<../../.gitbook/assets/image109 9558772a01aef5ece59a2a0f32a13387.png>)

If an article failed to publish, it’s recorded here and you can resend from the Publish Queue. Note: "published" means the PUBLISH button was pressed; if Content Filters, Products, Subscribers, or Destinations are not assigned the content may remain in Superdesk even if marked published.

The Publish Queue shows what was sent and what was received by Subscribers.

![](<../../.gitbook/assets/image348 411d7a655cfc6b3aceae20bd4a1edf7a.png>)

You can search by Subscriber, Destination, status, or headline. You can cancel or resend items.

![](<../../.gitbook/assets/image299 9ef94c97008fd01f5959f6044e537cea.png>)

Each Publish Queue entry has a unique identifier and a sequence number. Status indicates if an article failed to publish.

Resending an article keeps the Unique Name identifier the same but assigns a new sequence number.

Clicking an article opens a right-side tab with an article summary: content, metadata, duplicates and full item history. Items cannot be edited from the Publish Queue.

![](<../../.gitbook/assets/image140 a7f3115bbce53f6b8e0734d637b1f8b7.png>)

Navigate pages with arrows beside the search icon. Sort by Subscriber, Ingest Provider, Content type, Status, etc. Double-clicking an item opens a pane with Content, Metadata and Item History tabs.

![](<../../.gitbook/assets/image124 cab5cd8008bac9ffbf7b2db76a8f09db.png>)

* Content tab: preview of the news item.
* Metadata tab: unique name, GUID, state, etc.
* Item History: versions and updates.
{% endstep %}

{% step %}
### View Legal Archive (optional)

The Legal Archive is an optional, immutable forensic record of every published item, including every edit action: what changed, when and by whom. It serves as an evidential record for commercial or legal disputes. Your instance might not include the Legal Archive.

![](<../../.gitbook/assets/image49 9f3d835ea71fcbd02a1e099b5f417fa8.png>)

Admins access the Legal Archive from the Hamburger menu.

![](<../../.gitbook/assets/image349 2474c0a5586ec42de57de95e4e3587e3.png>)

Use the search icon (Advanced Search) to open the left tab and input search criteria.

![](<../../.gitbook/assets/image18 559ceb27a86396764f9891adce2c5ab4.png>)

Search by Story ID, Headline, Slugline, Story Text keywords, or publishing dates. Adjust entries per page using Page Size.

![](<../../.gitbook/assets/image398 65e06d89d0911705e9afe354e0268b2f.png>)

Left-click articles to preview a right-side overview. Use the Action menu > Open to view the full article. Articles in the Legal Archive cannot be edited or deleted.
{% endstep %}
{% endstepper %}
