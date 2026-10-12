# Content Configuration

The Superdesk Hamburger menu is where most of the newsroom workflow is set up. In the Admin tools section, under the Settings heading you can create Desks and Stages, manage Content Profiles, create Highlight lists, set default user privilege profiles, edit Subscribers, create Templates and more.

There are three sections within the Settings area: Content Flow, Workflow, and Content Configuration.

* The Content Flow section contains settings pertaining to how news items move from Superdesk to your customers or other Superdesk-internal locations (Internal Destinations). See [Defining Publishing in Superdesk](defining-publishing-in-superdesk.md).
* The Workflow section contains settings pertaining to user roles, desk creation and desk stages. See [Desk Creation and Desk Management](desk-creation-and-desk-management.md) and [User Management and User Roles](user-management-and-user-roles.md).
* The Content Configuration section contains settings pertaining to metadata fields for new item creation, highlights, templates and vocabularies. The content configuration section of the Settings menu is described below:

![](<../../.gitbook/assets/image122 715b145019a9e5c0c363aff37872a807.png>)

### Content Profiles

Content Profiles define metadata for new item creation. They determine which fields are available, and which fields are required when a news item is created.

![](<../../.gitbook/assets/image307 2942dfe36e94e4eaf3b94ff8b18dd0bc.png>)

To manage Content Profiles: open the Hamburger menu, then select Settings > Content Profiles.

Admins can create new Content Profile templates by clicking +ADD NEW at the top right of the Content Profiles tab.

![](<../../.gitbook/assets/image362 75c72122635bb0b23be359190b5dba84.png>)

{% stepper %}
{% step %}
### Create a Content Profile

* Assign a name and description for the new Content Profile.
* Click SAVE & CONTINUE to move to the metadata/fields customization.
{% endstep %}

{% step %}
### Edit Content Profile: understand tabs

In the Edit Content Profile window you will see three tabs:

* Header Fields — fields not transmitted to readers, used for internal communication.
* Content Fields — fields that are transmitted to readers.
* Widgets — determines which items appear in the Editor Sidebar during article creation.

![](<../../.gitbook/assets/image250 e7c6a61a01a1401b1a1b68ccaed75b69.png>)
{% endstep %}

{% step %}
### Configure fields

* Mark a field as mandatory by checking the Required checkbox.
* For most text fields you can set a minimum and maximum character length.
* Use the Create icon above/below fields to add additional fields.
* Custom fields are configured via Hamburger menu > Settings > Metadata.
{% endstep %}
{% endstepper %}

***

### Dictionaries

The Dictionaries tab lets you select dictionaries for internal spell check. Superdesk supports multiple dictionaries and can also integrate with third-party tools like Tansa: https://www.tansa.com/

To configure: Hamburger menu > Settings > Dictionaries.

![](<../../.gitbook/assets/image103 a8178f076efc18c4c84390e343372a84.png>)

Click the Create icon in the top-right of Dictionary Management to add a global dictionary, a personal dictionary, or an abbreviations dictionary.

In the Add New Dictionary window you must specify a unique name and ISO language code (see a list of language codes if unsure: http://www.lingoes.net/en/translator/langcode.htm). Global and personal dictionaries require uploading a reference file. Dictionary files must be .txt, one entry per line.

![](<../../.gitbook/assets/image42 23c8774e3c05697fc85fc8bd4d01723f.png>)

Notes:

* Personal dictionaries are only available to the creating user; global dictionaries are available to all users.
* After creating a dictionary you may need to log out and back in to use it.
* Toggle the dictionary to active in its configuration window to enable it.
* You can have multiple dictionaries with the same language code (e.g., a medical and a general dictionary). All active dictionaries that match the news item’s language code are used concurrently.
* View the current language code using the information button in the Editor Sidebar while editing an article.

![](<../../.gitbook/assets/image241 f98f7e7a640204547230b65ea2d0a7e6.png>)

{% stepper %}
{% step %}
### Add additional entries to a Dictionary

* Go to Hamburger menu > Settings > Dictionaries.
* Mouse over the desired Dictionary and click the Edit (pencil) icon.

![](<../../.gitbook/assets/image201 25e456f6c7867e1c52e12f6615442218.png>)
{% endstep %}

{% step %}
### Edit Dictionary entries

* In the Edit Dictionary window, search the dictionary using the search textbox at the bottom.
* If the word is not present, click ADD WORD beside the search textbox to add it.
* Words can also be added from the article editing window; those will be added to the user’s personal dictionary.
* To delete an entry, click the trash icon beside the searched entry.

![](<../../.gitbook/assets/image21 9966d08e45d3b62b2a76665982f1a706.png>) ![](<../../.gitbook/assets/image243 36c5528b39c3dd15be115f7efb6180b2.png>)
{% endstep %}

{% step %}
### Using the Spell Check feature

* Once Dictionaries are configured, open an article for editing.
* Use the action menu in the top-right of the article editor to access Spell Check.
* If Run Automatically is enabled (blue), spelling is checked as you type; otherwise run it manually (Ctrl + Shift + Y).
* Spell Check scans Headline, Body and Abstract fields.

![](<../../.gitbook/assets/image294 1691a114f46fb361bbe17eac2730e81a.png>)
{% endstep %}
{% endstepper %}

#### Abbreviations Dictionary

The abbreviations dictionary provides personal automatic text expansion while writing.

![](<../../.gitbook/assets/image350 56b0e992caed714c564aaa08c1da4b22.png>)

{% stepper %}
{% step %}
### Create an Abbreviations Dictionary

* Go to Hamburger menu > Settings > Dictionaries.
* Click the Create icon in the top-right, then select Abbreviations Dictionary.
* In "Add New Abbreviations Dictionary" enter a language code (e.g., EN).
* Enter the abbreviation to be replaced (e.g., UN).
* Enter the phrase to replace with (e.g., United Nations).
* Click ADD ABBREVIATION; your entry appears below the button.
* Add more abbreviations or click Save to close.
{% endstep %}

{% step %}
### How abbreviations work

* While typing in the article body, typing UN\* and pressing space will replace it with United Nations.
* You only need to click Create once; afterwards edit dictionaries via the pencil icon beside them to add items.
{% endstep %}
{% endstepper %}

***

### Highlights

Highlights are desk-specific curated lists of news items, used for top-10 lists, features and manually or automatically generated lists. Highlights can be published or used internally.

![](<../../.gitbook/assets/image115 c0855a8a3d42155935a68094672a7cdb.png>)

New Highlight lists are created via Hamburger menu > Settings > Highlights.

{% stepper %}
{% step %}
### Create a Highlight configuration

* Click CREATE CONFIGURATION in the upper-right of Highlights Configurations.
* Enter a CONFIGURATION NAME to name the Highlight.
* Choose a TEMPLATE from the drop-down for formatting when a new article is added.
{% endstep %}

{% step %}
### Assign desks and automatic insertion

* ASSIGNED DESKS: select desks that will view the Highlight. These desks are the source for automatic insertion if chosen.
* AUTOMATICALLY INSERT ITEMS: choose the timeframe to auto-insert items from the selected desks (e.g., last 12 hours). If no desk is selected at creation, the Highlight is available to all desks and curation is manual.
{% endstep %}
{% endstepper %}

![](<../../.gitbook/assets/image392 44d671c4dc3cc9a71c17c14048e7e13c.png>)

***

### Metadata

Most Superdesk fields are configurable. The Metadata section lets you define fields used for news items, media contacts, events, planning, etc.

![](<../../.gitbook/assets/image400 cdb5f0f0bf5f067871cb525834243c93.png>)

Open Hamburger menu > Settings > Metadata. Tabs at the top of Metadata Management may include Vocabularies, Custom Text fields, etc. Previously defined entries appear in the pane with a grey number bubble indicating the number of defined options in each entry.

To define a new field, click +ADD NEW in the top-right.

![](<../../.gitbook/assets/image106 a43d5610609a9dcf390db621ffb2a539.png>)

Metadata field properties:

* ID
* NAME: Title as it appears in Superdesk.
* DESCRIPTION: Internal description visible only in the metadata pane.
* CATEGORY: Organize vocabulary lists into categories.
* WIDTH: Field size in pixels.
* HELPER TEXT: Explainer text shown in the Editor when the field is in the content fields of a content profile.
* SHOW TO USERS AS: single selection, multi-selection, or neither.
* ITEMS: If multiple values are supported, add values here using +ADD ITEM.

***

### Search Providers

The Search Providers tab enables setup of external content providers for external image searches or other external content.

Click +ADD NEW in the upper-right of the Search providers window.

![](<../../.gitbook/assets/image82 a716a5512ab84eba9e7b98d255d17db9.png>)

In the Add Search Provider window:

* Toggle the provider on/off.
* Select provider type and enter the source name.
* Enter username and password credentials to configure the provider.

***

### Templates

Templates are Content Profiles with metadata fields pre-filled. They save time for routine news item creation, auto-generate articles, serve as generic kill notifications to subscribers, or auto-format Highlight List items.

![](<../../.gitbook/assets/image141 f7581a4909f6d3100b4263967bc077f2.png>)

Click the Create icon in the Templates pane to add a new Template. Each Template appears in the Templates pane showing template type, assigned Desk and Stage (if any), and automated creation schedule (if any).

Existing Templates:

* Edit via Action Menu > Edit.
* Remove via Action Menu > Remove.

![](<../../.gitbook/assets/image320 df24a0e03f6f8ba7135ee87cc073b4a6.png>)

{% stepper %}
{% step %}
### Create or edit a Template — left side

* Enter a Template name.
* Toggle Make Public on (blue) to allow other users to use it; off = personal use only.
* Choose a Content Profile from the drop-down; the metadata fields shown depend on this selection.
* Choose Template Type (Create or Highlight).
* Fill the content fields on the left; any entered information will appear in every news item created with this Template.
{% endstep %}

{% step %}
### Create or edit a Template — right side

* If the Template is public, expand the Desks tab and select desks that will have access (blue = access).
* Expand the metadata tab to edit Language, Not for publication toggle, target regions, etc.
* Use the AUTOMATICALLY CREATE ITEM toggle to enable scheduled automatic item creation; scheduling options appear when toggled on. This is useful for recurrent weekly items.
* Click SAVE to create/update the Template.
{% endstep %}
{% endstepper %}

![](<../../.gitbook/assets/image282 199bc759ce6ee0e7207286cd32d95ac8.png>) ![](<../../.gitbook/assets/image293 36f866180aee8dbdee3c96908e0f2169.png>)
