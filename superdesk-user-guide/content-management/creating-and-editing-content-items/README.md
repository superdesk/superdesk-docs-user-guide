# Creating and Editing Content Items

This page explains how to create and edit content items in Superdesk: creating articles and packages, editor features (Suggestions Mode, Annotations, Inline Comments), adding media, packages, moving items between desks/stages, and the Editor Sidebar.

### Create icon

The Create icon (top-right of the Monitoring Pane or Personal Space, and in versions 1.33+ the bottom-right of the interface) opens a menu to create new items.

<div align="left"><img src="../../../.gitbook/assets/image17 63a3f09dd0bfa75333d121efc9c0b112.png" alt="Create menu"></div>

Menu options:

* CREATE NEW ITEM: Choose a Content Profile for the new item. (Profile names vary by setup.)
* RECENT TEMPLATES: Choose a template (pre-filled metadata) — frequently used templates appear here.
* CREATE PACKAGE: Make a new empty package (a grouping of related news items).
* UPLOAD MEDIA: Upload an item (photo, audio, video) from your computer.

Metadata shown when creating items is configurable by users with appropriate permissions under Settings > Content Profiles.

When you create a new item, a pane opens on the right side of the Superdesk interface showing the metadata fields for the chosen Content Profile and the BodyHTML field for article content.

### Body HTML editor and toolbar

The BodyHTML field is where you enter the main text of an article. When typing, a blue toolbar appears above the body textbox with formatting buttons. Examples of toolbar functionality:

* Headings (make selected text into headings)
* Blockquote (apply quote formatting to the current line)
* Bulleted list
* Numbered list
* Paste with formatting (preserve original formatting)
* Bold, Italic, Underline, Strikethrough
* Superscript, Subscript
* Add link / attach an attachment
* Embed (enter a URL or embed code)
* Insert media into the body
* Insert table (then add rows/columns/formatting in-place)
* Remove formatting (clear formatting from selected text)
* Comments (add inline comments and notify users with @username)
* Annotations (add contextual annotations to selected text)
* Suggestions Mode (collaborative suggested edits)
* Show invisible formatting (e.g., line breaks highlighting)

Note: In older editor versions without a dedicated remove-formatting button, remove formatting by toggling the formatting button that originally added the formatting (e.g., deselect quote).

Superdesk tracks word and character counts just above the body text box.

{% hint style="info" %}
If you are using a Superdesk version prior to 1.33, the Create icon may only be available in certain panes. From 1.33 onward, a Create option is available in the bottom right of the interface, allowing item creation from any pane.
{% endhint %}

#### Using Suggestions Mode

![Suggestions mode toolbar](<../../../.gitbook/assets/image196 cd3f4bf2f7acf7ea09fe5315ec63d9f2.png>)

* Toggle Suggestions Mode using the toolbar button.
* When active (blue), added text appears green, deleted text appears red with strikethrough; formatting changes are highlighted in green.
* Click an altered text segment to accept or reject the suggested change.
* Useful for collaborative editing where changes are proposed while preserving the original text.

![Suggestions example](<../../../.gitbook/assets/image402 e097eb5ae690f9369fd6a114e668a569.png>)

#### Using the Annotations feature

The Annotations button may appear in the toolbar. Annotations let writers add contextual information (footnotes, jargon busters, etc.) tied to selected text.

* Highlight text and click the Annotations button to open the annotation window.
* The pop-up has two tabs: New Annotation and Annotations Library.
* Add Annotation Type, Annotation Body (rich text is supported), then SUBMIT to create the annotation.
* Text that contains annotations is underlined in green; click it to view the annotation and use the action menu to edit or delete it.

<div align="left"><figure><img src="../../../.gitbook/assets/image144 8ee71d728820fbade1d5901f8f55448a.png" alt=""><figcaption></figcaption></figure></div>

**Annotations Library**

The Annotations Library is accessible from the Hamburger menu. Create annotations directly there:

* Click Create in the Annotations Library pane.
* Provide NAME, LANGUAGE (language code), and DEFINITION (annotation content). All fields are mandatory.
* As of version 1.33, the Library permits multiple annotations with the same name and pre-fills language by default (adjust if needed).
* Saved annotations appear in the Annotations Library tab of the annotation pop-up when highlighted text exactly matches the NAME field.

<figure><img src="../../../.gitbook/assets/image238 bf4a6213da43ed0940af59ed5b4c84f6.png" alt=""><figcaption></figcaption></figure>

<br>

<div align="left"><figure><img src="../../../.gitbook/assets/image247 f4001ab19cb55797dcbb0c0c9c66852f.png" alt=""><figcaption></figcaption></figure></div>

#### Using the Inline Comments feature

Inline Comments let users add comments tied to selected text in the Body HTML field.

* Highlight text and click the Comments button in the toolbar.
* Type a comment and use @username to notify people (notifications depend on user preferences).
* Submitted inline comments appear in the Inline Comments tab of the Editor Sidebar.
* Click highlighted text in the body to resolve a comment or reply. Resolved comments remain associated with the item but are not published with it.

![Inline comments toolbar](<../../../.gitbook/assets/image131 397a24fceba338d71f9cf15c94f87cf5.png>)\
![Editor sidebar comments](<../../../.gitbook/assets/image343 cacbdd1a7b79508ca00835062bc4f341.png>)

### Adding media to the body

Use the media icon in the toolbar to upload media into the Body field. You can select multiple files at once; upload supports photos, audio, and video (destination-dependent).

* After selecting files, you may be required to enter metadata (title, description, headline). Mandatory fields are marked with a red star.
* Use SELECT ALL to apply metadata to all selected media, or edit items individually.
* Click Upload then edit the inserted media (rotate, crop, brightness, contrast, saturation). Click DONE to insert the media into the body.

![Upload media pane](<../../../.gitbook/assets/image164 19b9adb81622f603e54868d16fc82f3b.png>)

When a photo is inserted, click the image in the article body to edit or remove it (an “x” appears on hover).

Image editor buttons (Details / Metadata, Edit Image, Edit Crops):

* Details / Metadata: change text associated with the image.
* Edit Image: crop, rotate left/right, flip vertically/horizontally, adjust brightness/contrast/saturation.
* Edit Crops: choose predetermined image sizes and adjust the area of interest.

![Image editor details](<../../../.gitbook/assets/image346 8ec797da2cbabdc33a598f8a5928d36a.png>)\
![Image editor crops](<../../../.gitbook/assets/image262 8d820887f1ca619b3a36933a13d685c7.png>)

### Creating Packages

Packages group multiple news items and have metadata separate from individual items.

* Create an empty package via the Create icon (Monitoring Pane or Custom Workspace).
* Add articles to a package from the Search or Monitoring tabs:
  * Hover left of an article to reveal checkboxes, select articles, then click Add to Current Package.
  * Or use Create Package to create a new package with selected content already attached; then fill package metadata.
* Note: Packages cannot be created in Personal Items (Personal Space).

![Create package](<../../../.gitbook/assets/image70 63a3f09dd0bfa75333d121efc9c0b112.png>)\
![Package metadata](<../../../.gitbook/assets/image274 72b3327d7eeb7936162f8bf38dfdea37.png>)\
![Add to package button](<../../../.gitbook/assets/image259 4e86b760e5b4b9b3ddf72ab7c56c80b4.png>)

For more on packages, see [Packages](../packages.md).

### Moving items between Desks and Stages

The Send To button lets you move items between Desks and Stages, or send for publishing (depending on permissions).

* If you created an article in your Personal Space and want others to review it, click Send To and choose the Desk.
* If the article is created on a Desk, it is already visible to others.
* You can also use Send To to publish if you have the required permissions.
* If not ready to send, click SAVE (blue) then CLOSE to revisit later.

<div align="left"><img src="../../../.gitbook/assets/image277 a5f43f705c02d504832cba73b2fdc404.png" alt="Send to button"></div>

### Editing and re-opening existing items

Item lists appear in Monitoring, Search, or Personal Space. Hover an item in a list to reveal its Action menu (right side).

* From the Action menu choose Edit to continue editing an item. Available actions depend on item status, your permissions, and whether the planning component is enabled.

<div align="left"><img src="../../../.gitbook/assets/image298 172c2ab6cb942dffa1dc6832978b4d93.png" alt="Action menu example"></div>

Top-of-window editing tools include:

* Minimise: minimises the article into the Workspace Bar as a shortcut.
* Action menu: save formatting as a template, open in Multiedit (side-by-side editing), spell check, etc. Multiedit can also be launched from the Monitoring tab by selecting multiple articles and clicking Multiedit.
* Send To: send to a Desk/Stage or publish (permission-dependent).

### Editor Sidebar

The Editor Sidebar provides additional options while editing items. Available tabs vary by Content Profile.

* Open tabs are blue; mouse over a blue icon to reveal an “x” to close the tab.

<div align="left"><img src="../../../.gitbook/assets/image32 4686ae09a53a5d09defe7dab3840e23e.png" alt="Editor sidebar"></div>

Main sidebar tabs and features:

#### Info (Metadata) tab

* Not for Publication: flag shown beside slugline. Does not prevent publishing by itself; marks the item for internal use.
* Legal: flag indicating legally sensitive content (does not block publishing).
* Usage terms: notes about publishing conditions (may be inherited from ingest).
* Language: language code (affects dictionaries used).
* PubStatus: usable or unusable (unusable items should be killed and deleted).
* State: shows current article status flags (legal, fetched, not for publication, takes, corrected, published, etc.).
* Expiry: if desk auto-expiry is set, shows when the article expires and will be deleted.
* GuID: unique global identifier (immutable).
* Unique Name: editable identifier for easier searching (searchable in Advanced Search).
* Info tab also shows version, source, urgency, genre, type, and last updated info.

Note: Not for Publication toggling marks the item but does not block publication.

#### Find and Replace

* Use FIND and REPLACE WITH boxes to locate and update text.
* REPLACE ALL replaces every instance; REPLACE replaces instances one at a time.

#### Comments (general)

* General discussion comments about the news item (different from Inline Comments).
* New comments count shown in the info bubble. Add a comment at the bottom of the Comments pane and click POST.

<div align="right"><img src="../../../.gitbook/assets/image281 d470ede72361d68e445da4a806e4833d.png" alt="General comments pane"></div>

#### Versioning

* Superdesk saves versions on user save and autosaves after 3 seconds of inactivity.
* Access previous versions from the Versions tab. Click REVERT to continue from a previous version while retaining other versions.
* Item History shows who created and updated the item and when.

<div align="left"><img src="../../../.gitbook/assets/image207 56b6f162fba64a45d2755e2f3e47e7d0.png" alt="Versions pane"></div>

#### Packages Info

* Shows packages the current item belongs to, with link and timestamp for when it was added.
* Click a package to view or edit it (permissions permitting).

<div align="left"><img src="../../../.gitbook/assets/image274 72b3327d7eeb7936162f8bf38dfdea37.png" alt="Packages info"></div>

#### Macros

* View and apply macros created in the backend.
* Toggle grouping to find macros more easily.

<div align="left"><img src="../../../.gitbook/assets/image297 2f33dce0714fd429bfa8e43321e98293.png" alt="Macros pane"></div>

#### Attachments

* Add/view files attached to the news item. Attachments may be internal or published with the item.
* Click ATTACH FILES to upload. Use the toggle in the attach pane to select whether attachments are internal or published. Titles/descriptions may be required; size restrictions may apply.

<div align="right"><img src="../../../.gitbook/assets/image372 40178820a9f7f25a7f086d136cd62ac5.png" alt="Attachments pane"></div>

#### Inline Comments (tab)

* View inline comments submitted for the item (these are not transmitted on publication).
* To add inline comments: highlight text in the Body HTML field, click the Comments icon and submit. Use @username to notify specific users.
* For information to be transmitted with the content beyond publication, use the Editor’s notes field in the metadata header.

![Inline comments list](<../../../.gitbook/assets/image263 6be35432c122f2cc4ab1a6269fe38832.png>)

#### Related Items

* View items that share the same slugline or keywords; relate items together.
* Type keywords into the Related Items search bar to generate matches (configured in backend).
* Note: Related Items displays only while editing text items (not packages or media).
* Use the action menu of a related item to open it, associate metadata, or mark as an update.
* The gear icon configures complete/partial slugline matches and recency limits.
* Locked related items are indicated as such.

<div align="right"><img src="../../../.gitbook/assets/image239 cc90cb07cd779f01f159070b64ecac13.png" alt="Related items pane"></div>

If you need more details on any specific feature — e.g., Annotations Library workflows, image editing controls, or package creation flows — tell me which section you want expanded and I’ll produce step-by-step guidance.

***

{% hint style="info" %}
* editor
* belga
* for users
{% endhint %}
