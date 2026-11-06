# Defining Publishing in Superdesk

There are several steps to defining publishing in Superdesk. This chapter gives an overview of everything an administrator sets up so that published items reach the right places. For what journalists and editors do when they publish an item, see [Sending, scheduling and publishing items](../../content-management/sending-scheduling-and-publishing.md).

The first step lets you create automatic rules that group published news items together. This means that you can use one instance of Superdesk to publish specific content to multiple destinations. These rules are called Content Filters.

Products are then created based on those Content Filters. The simplest Product is a Product with no Content Filter. In that case, every item that is published is part of the Product.

The next step is to set up Subscribers. Subscribers might be news agency customers, but in the world of digital publishing you can think of them as publications. For each Subscriber you define which Products it receives, and through its Destinations how (the output format and delivery method) and where the items are sent. Subscribers can also read content through the Content API instead of, or as well as, receiving it at a Destination.

Once items are published, you can check what was sent and resend items from the Publish Queue. If your instance has the Legal Archive, every published item is also saved there.

All of these settings are in the Main menu under **Settings**, in the **Content flow** group: **Content Filters**, **Internal Destinations**, **Products** and **Subscribers**. **Publish Queue** and **Legal Archive** are entries of the Main menu itself. Each of them needs its own privilege, see [Privileges](#privileges).

{% stepper %}
{% step %}
### Make Content Filters

Create the Filter Conditions and Content Filters that select published items. See [Make Content Filters](content-filters-and-internal-destinations.md#make-content-filters).
{% endstep %}

{% step %}
### Internal Destinations (optional)

Copy published items to a desk, for example for translators. See [Internal Destinations](content-filters-and-internal-destinations.md#internal-destinations-optional).
{% endstep %}

{% step %}
### Creating Products

Build Products from your Content Filters. See [Creating Products](products-and-subscribers.md#creating-products).
{% endstep %}

{% step %}
### Define Subscribers

Set up the Subscribers, the Products they receive and their Destinations. See [Define Subscribers](products-and-subscribers.md#define-subscribers).
{% endstep %}

{% step %}
### Publish

When an editor publishes an item, Superdesk checks it against the Products and Content Filters of every active Subscriber, formats it for each matching Destination and adds the transmissions to the Publish Queue. For the publishing steps, see [Sending, scheduling and publishing items](../../content-management/sending-scheduling-and-publishing.md).
{% endstep %}

{% step %}
### Check Publish Queue

Check what was sent to each Subscriber and resend items that failed. See [Check Publish Queue](publish-queue-legal-archive-and-content-expiry.md#check-publish-queue).
{% endstep %}

{% step %}
### View Legal Archive (optional)

Search the record of every published item. See [View Legal Archive](publish-queue-legal-archive-and-content-expiry.md#view-legal-archive-optional).
{% endstep %}
{% endstepper %}

How long items are kept before they are deleted or archived is described in [Content expiry](publish-queue-legal-archive-and-content-expiry.md#content-expiry).

## Output formats

The **Format** list of a Destination shows the output formats installed on your server. A standard installation has:

* **NINJS** and **NINJSv2**: JSON formats based on the IPTC ninjs standard.
* **NINJS FTP**: NINJS for FTP delivery. Links to pictures and other media point to the media path on the same FTP server.
* **Newsroom NINJS**: NINJS with the extra data the Superdesk Newshub needs, such as the matching API Products.
* **NewsML G2** and **NewsML 1.2**: IPTC XML formats.
* **NITF**: the News Industry Text Format.
* **Email**: formats the item as an email.
* **Adobe InDesign (IDML)**: an InDesign document for print layout.

When the Planning component is installed, its formats are listed too, for example **JSON Event** and **JSON Planning**. Your server may have more formats added by its own configuration.

## Delivery types

The **Delivery type** list shows the transmitters installed on your server. A standard installation has:

* **FTP**: uploads files to an FTP server. Options include passive mode, FTPS, the target path, the file extension, and pushing associated and feature media.
* **Email**: sends the item to visible and hidden (Bcc) recipients. Options include adding the feature media to the email in a chosen rendition, with an optional watermark.
* **File**: writes files to a folder on the server.
* **HTTP Push**: posts the item and its media to a web service, with a resource URL, an assets URL and a secret token.
* **Amazon SQS FIFO**: sends the item to an Amazon SQS FIFO queue.
* **ODBC**: calls a stored procedure in a database. Only available when the server has the ODBC driver installed.

Other delivery types can be added by server configuration or optional modules.

## Privileges

Set these privileges in [User Management and User Roles](../user-management-and-user-roles.md).

| Privilege | Allows |
| --- | --- |
| **Content Filters** | Creating, changing and deleting Content Filters and Filter Conditions |
| **Internal Destinations** | Managing Internal Destinations |
| **Products Management** | Managing Products |
| **Subscribers** | Managing Subscribers, their Destinations and Content API tokens |
| **Publish Queue** | Opening the Publish Queue, resending and canceling transmissions |
| **Legal Archive** | Reading the Legal Archive |

The **Content Filters** entry in **Settings** is only shown to roles that also have the **Dictionaries List Management** privilege. Give both privileges to the roles that manage Content Filters.
