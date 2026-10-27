# Updates

An update is a new story that follows on from a published one. Use it when news develops: new figures, a reaction, a later stage of an event. The original stays published as it is, and subscribers receive the update as the next version of the same story.

{% stepper %}
{% step %}
### Start the update

Open the published story and click **Update** in the top bar. Or, in a list, open the item actions menu and choose **Publishing actions** > **Update**.
{% endstep %}

{% step %}
### Edit the update

Superdesk shows "Update Created." and opens the new story for editing. It is placed in the working stage of the desk you are working on. If you are not on a desk, it goes to the working stage of the original story's desk.
{% endstep %}

{% step %}
### Publish the update

Rewrite the story as needed, then send or publish it like any other item.
{% endstep %}
{% endstepper %}

The update starts as a copy of the original. It gets the same content profile, all the fields of that profile (headline, slugline, body, byline and so on), the subjects and other metadata, and the pictures and media embedded in the story. Its **Take Key** is set to "update". The next update in the chain gets "2nd update", then "3rd update", and so on.

A few rules keep updates in order:

* Updates can only be created for text items. You can not update pictures, other media or packages.
* Each version can only be updated once. The original then shows an **Updated** label in its header. To add another update, open the latest version in the chain and update that one.
* By default, you can not update an update that has not been published yet. Your administrator can allow several unpublished updates at once (see [For administrators](README.md#for-administrators)).
* You can not publish an update before the story it updates is published.

If Superdesk refuses to create an update, a window titled "An update can not be created" lists the reasons, for example "An update for this version of the item already exists. To create another update, find the latest version of the item."

The **Publish & Continue** and **Close & Continue** buttons, when your administrator has turned them on, also create an update. See [Shortcut buttons in the top bar](../sending-scheduling-and-publishing.md#shortcut-buttons-in-the-top-bar).

## Linking an existing story as an update

Sometimes you have already written a story before you realise it should be an update of a published one. You can link it instead of starting again.

{% stepper %}
{% step %}
### Open your story

Open the story you wrote for editing. It must be a text item that is not published and is not already an update.
{% endstep %}

{% step %}
### Find the published story

Open the **Related Items** widget. It lists stories from today with the same slugline.
{% endstep %}

{% step %}
### Link it

Hover over the published story in the list and click **Associate as update**. Superdesk shows "Story is associated as update." and your story becomes the update of that story.
{% endstep %}
{% endstepper %}

If a story has the same slugline as other stories from today but is not linked to any of them, its header shows a **Missing Link** label. That is a reminder to check whether it should be an update.

## Removing the link to the original

To turn an update back into an independent story, open the item actions menu of the update and choose **Publishing actions** > **Unlink update**. Superdesk shows "Link has been removed". This only works while the update is not published.

If you spike an update, Superdesk also removes the link, so the original can be updated again.

## Updates of embargoed stories

*Available since Superdesk 3.4.*

By default, you can not create an update while the original story's embargo is still running. Superdesk shows "Failed to generate update: Rewrite of an Item having embargo isn't possible". Once the embargo has passed, you can update the story as usual, and the update has no embargo.

Your administrator can allow updates of embargoed stories (see [For administrators](README.md#for-administrators)). Then the update keeps the original's embargo and its time zone, as long as the embargo is still in the future. You can change it in the **Publish** tab before you publish the update.

An update never keeps the original's publish schedule. If the update must go out at a set time, set a new schedule on it.
