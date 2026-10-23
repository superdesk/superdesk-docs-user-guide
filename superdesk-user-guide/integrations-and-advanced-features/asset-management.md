# Asset management (SAMS)

*Available since Superdesk 2.2.*

{% hint style="info" %}
This is an optional module. If you do not see it, ask your administrator.
{% endhint %}

The Superdesk Asset Management Service (SAMS) is a shared library of files for your newsroom. You upload a file once, for example a PDF report, a press release, a spreadsheet, an image or an audio clip, and then attach it to as many stories as you need. Without SAMS, an attachment belongs to one story and you have to upload it again for every story that uses it.

SAMS accepts any file type, not only the media types you can upload in Monitoring.

Two terms come up on this page:

* An **asset** is a file plus its details: name, description, state, set and tags.
* A **set** is a folder that holds assets. Every asset belongs to exactly one set.

## Opening the SAMS workspace

Click the **SAMS** icon in the Workspace Panel on the left of the screen, or press **Ctrl+Alt+S**. You only see the icon if your role has the SAMS privilege. See [Keyboard shortcuts](../reference/keyboard-shortcuts.md) for other shortcuts.

The SAMS workspace has two bars above the asset list:

* The top bar has the set filter (it shows **All Sets** by default), the **Search Assets** box, the **Manage SAMS** menu (three dots, only for set managers) and the **Upload New Asset(s)** button.
* The second bar has the **Toggle filters** button, the file type buttons, the total number of assets, the sort options and the button that switches between grid and list view.

## Sets

Sets keep assets organised, in the same way that desks keep stories organised. A set has a name, a description, a maximum file size, a storage destination (where SAMS keeps the files) and, optionally, a list of desks that can use it.

### Set states

A set is always in one of three states. The state decides whether you can upload to it and whether it can be deleted.

| State | Upload assets | Change storage destination | Delete the set |
| --- | --- | --- | --- |
| **Draft** | No | Yes | Yes |
| **Usable** | Yes | No | No |
| **Disabled** | No | No | Only when it holds no assets |

A new set always starts as a draft. When you enable it, it becomes usable, and it can never go back to draft. When you disable a usable set it becomes disabled, and you can enable it again later.

You cannot edit assets that sit in a disabled set. Public assets in a disabled set are no longer served to websites.

### Managing sets

You need the **Sams manage** privilege to create and change sets. If you have it, you see the **Manage SAMS** menu in the top bar.

{% stepper %}
{% step %}
### Open the Manage Sets window

Click the three dots in the top right of the SAMS workspace and choose **Manage Sets**. The window lists your sets in three groups: **Draft Sets**, **Usable Sets** and **Disabled Sets**. Usable and disabled sets show how many assets they hold.
{% endstep %}

{% step %}
### Add a set

Click **Add New**. Fill in **Name**, and optionally **Description** and **Maximum Asset Size** with its **Storage Unit**. A size of 0 means there is no limit. Pick a **Destination**, then click **Create**. The set is created as a draft.
{% endstep %}

{% step %}
### Enable the set

Click the set, then click the pencil icon. Turn on **Enabled** and click **Save**. The set moves to **Usable Sets** and people can now upload to it.
{% endstep %}
{% endstepper %}

Click a set to see its **Set Details**. To edit or delete a set, hover over it and click the pencil or trash icon, or use the same icons in Set Details. The trash icon only appears when the set can be deleted (see the table above).

### Restricting a set to desks

*Available since Superdesk 2.3.*

Use **Allowed Desks** in the set editor to limit a set to some desks. A restricted set only appears, in the set filter and when you attach assets to a story, while you work in one of its allowed desks. Sets with no allowed desks are available everywhere. In a custom workspace you see every set.

## Uploading assets

You can upload assets from the SAMS workspace, or straight from a story (see [Attaching assets to a story](#attaching-assets-to-a-story)). There must be at least one usable set. If there is none, Superdesk tells you "No usable Sets found. Enable one first".

{% stepper %}
{% step %}
### Open the upload window

Click the **Upload New Asset(s)** button (the round button in the top right). The **Upload New Asset(s)** window opens together with your computer's file picker.
{% endstep %}

{% step %}
### Choose files

Select one or more files. To add more, click **Add File**. To drop a file from the list, click the cross on its card.
{% endstep %}

{% step %}
### Fill in the details for each file

Click a file card to edit its details on the right: **Name**, **Description**, **State**, **Set** and **Tags**. Name, State and Set are required. The name starts as the file name and the state starts as **Draft**.
{% endstep %}

{% step %}
### Upload

Click **Upload**. A progress circle shows on each card. When all files are in, the window closes and Superdesk confirms the upload.
{% endstep %}
{% endstepper %}

Choose the set carefully: you cannot move an asset to another set after it is uploaded. If the set has a maximum asset size, larger files are refused.

## Asset states

The state of an asset decides whether it can be attached to a story and whether it goes out when the story is published.

| State | Can be attached to a story | Sent to subscribers when the story is published | Available to websites from SAMS |
| --- | --- | --- | --- |
| **Draft** | No | No | No |
| **Internal** | Yes | No | No |
| **Public** | Yes | Yes | Yes, while its set is usable |

Use **Internal** for source material your colleagues need to see, for example research notes or a document from a source, but readers must not get. Use **Public** for files you want to publish with the story, for example the full text of a report. Keep an asset in **Draft** until it is ready.

See [Sending, scheduling and publishing items](../content-management/sending-scheduling-and-publishing.md) for how publishing works.

## Finding assets

### Grid and list views

The grid view is the default. Each card shows a thumbnail for images (an icon for other files), the last change time, the name, the start of the description, the file type, the size and the state.

The list view shows one row per asset with the same information in less space. Click the grid or list button at the right end of the second bar to switch.

### Filtering by set and file type

Click the set filter on the left of the top bar and pick a set, or **All Sets**. Disabled sets are listed with a lock and "(disabled)".

Use the buttons in the second bar to show **All item types**, **Images only**, **Videos only**, **Audio only** or **Documents only**. "Documents" means every file that is not an image, video or audio file.

### Searching

Type in **Search Assets** and press Enter to search all asset details.

For more control, click **Toggle filters** (the filter icon on the left of the second bar). The **Advanced Search** panel opens on the left. You can search by **Name**, **Filename**, **Description**, **Tags** and **State**, by file size (**Size From:** and **Size To:**) and by upload date (**Uploaded From:** and **Uploaded To:**). Click **Submit** to apply the filters, or **Clear** to remove them.

### Sorting

The sort menu in the second bar sorts by **Name**, **Filename**, **Created**, **Updated** or **Size**. The arrow next to it switches between ascending and descending order. The badge next to **Total:** shows how many assets match.

## Previewing and downloading assets

Click an asset to open the **Asset Preview** panel on the right. It shows the file and all its details: name, description, filename, size, type, state, set and tags. Images are shown in the panel, and audio and video files can be played there. For images, choose **Full-screen preview** in the three-dot menu to see the picture at full size.

To download an asset, open its three-dot menu, on the card or in the preview panel, and choose **Download**.

### Selecting several assets

*Available since Superdesk 2.4.*

Tick the checkbox on an asset card to select it. Hold Shift while you tick a second checkbox to select every asset in between. A bar replaces the top bar and shows how many items you selected, with buttons to **Download** or **Delete** them all. Several files download together as one zip file. Click **cancel** to clear the selection.

## Editing assets

Double-click an asset, or choose **Edit** in its three-dot menu. The details open in an editor on the right. You can change **Name**, **Description**, **State** and **Tags**. You cannot change the set. Click **Save** to keep your changes, or **Cancel** to drop them.

While you edit an asset, SAMS locks it so that nobody else can change or delete it at the same time. The lock is released when you save, cancel or log out. If someone left an asset locked, a user with the **SAMS Manage Assets** privilege can choose **Force Unlock** in its three-dot menu.

### Tags

*Available since Superdesk 2.3.*

Tags make assets easier to find. In the **Tags** field, start typing to see the tags already used in SAMS. Pick one, or choose **Create new tag** to add a new one. To remove a tag, click it. You can filter by tags in Advanced Search.

## Attaching assets to a story

When SAMS is enabled, the Attachments widget in the story editor works with SAMS. Every file you attach is stored as a SAMS asset, so other stories can reuse it.

Open the story for editing and click the paperclip icon (**Attachments**) in the toolbar on the right. Some content profiles also show an **Attachments** field inside the story. Both work the same way. See [Creating and Editing Content Items](../content-management/creating-and-editing-content-items/README.md) for the editor itself.

### Uploading a new file

Drag files onto the widget, or click **browse**. The **Upload New Asset(s)** window opens, as described in [Uploading assets](#uploading-assets). Here you can only choose **Internal** or **Public**, and the state starts as **Public**, because a draft asset cannot be attached. When the upload finishes, the files are attached to the story.

### Attaching an existing asset

{% stepper %}
{% step %}
### Open the asset picker

In the Attachments widget, click **Or select an existing asset**. The **Select Asset(s)** window opens.
{% endstep %}

{% step %}
### Find and select assets

Use the set filter, search and filters as in the SAMS workspace. Click each asset you want to attach. You can pick several.
{% endstep %}

{% step %}
### Attach them

Click **Attach Asset(s)**. The assets now appear in the Attachments widget.
{% endstep %}
{% endstepper %}

The picker only lists assets you can attach: internal and public assets, in sets available to your current desk, within the attachment size limit, and not yet attached to this story.

### Working with attachments

Each attachment shows its name, file name, size and description. Internal assets have an orange **internal** label. If the asset's set has been disabled, you also see **Set Disabled**.

Hover over an attachment to see its actions:

* **Download** saves a copy of the file.
* **Edit** (pencil) opens **Edit Attachment**, where you can change the name, description and state. The changes are saved to the asset in SAMS too. Edit is not available when the asset's set is disabled.
* **Remove** (trash) takes the file off this story. It does not delete the asset from SAMS.

When you publish the story, only public attachments go to subscribers. Internal attachments stay inside Superdesk.

### Attachments without SAMS

If your Superdesk does not use SAMS, the Attachments widget still exists, but each file belongs to one story. When you upload, you give each file a **Title** and optional **Description**, and you turn on the **Internal** switch for files that must not be published. You cannot pick a file from another story.

## Deleting assets

Choose **Delete** in the asset's three-dot menu, or select several assets and click **Delete** in the selection bar. Superdesk asks you to confirm. Deleting an asset cannot be undone.

You cannot delete an asset while:

* someone is editing it (it is locked), or
* it is attached to a story. Remove it from every story that uses it, and save those stories, first. If you try anyway, Superdesk shows "Asset is attached to a news item, cannot delete".

<!-- VERIFY: publish a story with a SAMS attachment, remove the attachment in a correction, then try to delete the asset in SAMS; note whether it is refused. -->

## For administrators

### Enabling SAMS

SAMS has three parts, and all three must be in place.

1. **The SAMS service.** SAMS runs as its own service next to Superdesk. Its storage destinations (for example Amazon S3 or MongoDB GridFS) are configured in the SAMS service with `STORAGE_DESTINATION_<n>` environment variables, not in Superdesk. See the [SAMS technical documentation](https://superams.readthedocs.io/) for installing and running it.
2. **The server side.** Superdesk forwards SAMS requests from the browser to the SAMS service. In the server settings:
   * add the SAMS Python client to the server requirements (`sams_client`, from https://github.com/superdesk/sams, subdirectory `src/clients/python`),
   * add `superdesk.sams` to `INSTALLED_APPS`,
   * set `SAMS_HOST` and `SAMS_PORT` (environment variables of the same name, defaults `localhost` and `5700`),
   * set `MEDIA_STORAGE_PROVIDER = "superdesk.sams.media_storage.SAMSMediaStorage"` so that story attachments are stored in SAMS.
3. **The client side.** Load the SAMS extension in `client/index.ts` and, to use the SAMS version of the Attachments widget, pass it as a custom UI component:

```typescript
import {startApp} from 'superdesk-core/scripts/index';
import {SamsAttachmentsWidget} from 'superdesk-core/scripts/extensions/sams/src/apps/samsAttachmentsWidget';

startApp(
    [
        // ...other extensions
        {
            id: 'sams',
            load: () => import('superdesk-core/scripts/extensions/sams'),
        },
    ],
    {
        AuthoringAttachmentsWidget: SamsAttachmentsWidget,
    },
);
```

Without the second argument, the SAMS workspace still works, but the Attachments widget keeps the standard behaviour and does not offer existing assets.

### Attachment limits

These server settings apply to the Attachments widget, with or without SAMS:

* `ATTACHMENTS_MAX_FILES`: the most files a story can have attached (default 10).
* `ATTACHMENTS_MAX_SIZE`: the largest file you can attach, in bytes (default 8 MB). The asset picker hides larger assets.

The Attachments widget is on by default. To hide it, set `features.editorAttachments` to `false` in the client configuration. To show the **Attachments** field inside the story, add it to the content profile under **Settings** > **Content Profiles**. See [Content profiles](../administration/content-configuration/content-profiles.md).

### Privileges

Grant these in **Settings** > **User Roles** > **Roles privileges**. See [User Management and User Roles](../administration/user-management-and-user-roles.md).

| Privilege (as shown) | Name in code | What it allows |
| --- | --- | --- |
| **Sams** | `sams` | See the SAMS icon and open the SAMS workspace. |
| **Sams manage** | `sams_manage` | Open **Manage Sets** to create, edit, enable, disable and delete sets. |
| **SAMS Manage Assets** | `sams_manage_assets` | Force unlock assets that another user has locked. |

Attaching files to a story only needs normal write access to the story. Users may need to log out and log back in after a privilege change.
