# Analytics

{% hint style="info" %}
This is an optional module. If you do not see it, ask your administrator.
{% endhint %}

Analytics turns the activity in your newsroom into charts and tables. You can see how much content was published and by whom, how busy a desk is at different times of day, how long stories take to produce, and what a single journalist worked on during a day. You can save the settings of a report, share them with colleagues, and have Superdesk email a report on a schedule.

Each report is controlled by its own privilege, so you may see only some of the reports described on this page.

## Opening Analytics

Open the Main menu (also called the hamburger menu) in the top-left corner and click **Analytics**. See [Navigation](../navigating-superdesk/navigation.md#the-main-menu) for more on the Main menu.

**Analytics** is only listed if your role can view at least one report.

## The Analytics page

The page opens with no report selected. The bar at the top holds:

* the **filter** icon on the left, which opens and closes the report panel,
* the report list, which reads **Select A Report** until you pick one,
* the **Report** and **Schedules** switch, if the report can be scheduled and you are allowed to schedule reports,
* the **Highcharts License** button (an info icon) on the right, which shows the license of the charting library.

When you pick a report, the report panel opens on the left and the chart area fills the rest of the page. Superdesk adds the report to the page address, so you can bookmark a report or send the link to a colleague.

## Available reports

The list shows the reports below, in this order. Some reports only appear when your administrator has turned on the statistics they need, or when the Planning component is installed.

| Report | What it shows | Needs |
| --- | --- | --- |
| **Content Publishing** | The number of published stories, grouped by a metadata field such as category or source, and optionally subgrouped by a second field. | |
| **Desk Activity** | Items coming into and going out of one desk, per hour or per day. | Archive statistics |
| **Featuremedia Updates** | Changes made to the feature image of a story after it was first published. | Archive statistics |
| **Planning Usage** | How many events, planning items, coverages and assignments each user created. | Planning component |
| **Production Time** | How long stories spend on each desk: the minimum, average and maximum time, and the total. | Archive statistics |
| **Publishing Performance** | Published content per desk, user or metadata field, split into published, killed, corrected, updated and taken down items. | |
| **Update Time** | How long it took to publish an update after the original story. | Archive statistics |
| **User Activity** | A timeline of the stories one user worked on during one day. | Archive statistics |

"Archive statistics" are figures that Superdesk works out from the history of every item. Your administrator decides whether they are collected. They are refreshed once an hour, so the last hour of activity may not show yet in these reports.

### Publishing reports

**Content Publishing** answers "how much did we publish, and of what?". Under **Group By** you pick the field for the main bars: **Category**, **Genre**, **Source**, **Urgency**, **Subject**, **Author** or **Language**. **Subgroup By** splits each bar by a second field. Leave it empty for a simple chart.

**Publishing Performance** shows the same published content from a different angle. Under **Group By** you pick **Desk**, **User**, **Category**, **Source**, **Urgency**, **Genre**, **Subject** or **Author**. Each bar is then split by what happened to the content: **Published**, **Killed**, **Corrected**, **Updated** or **Taken Down**. See [Updates, corrections, kills and takedowns](../content-management/updates-corrections-kills-and-takedowns/README.md) for what these actions mean.

### Grouping by your own metadata fields

*Available since Superdesk 2.8.*

In **Content Publishing**, **Group By** and **Subgroup By** also list the custom vocabularies your administrator has set up, so you can report on your own metadata fields.

### Desk and production reports

**Desk Activity** shows when a desk is busiest. Pick the **Desk** (required) and the **Interval**, **Hourly** or **Daily**. The chart compares **Incoming** and **Outgoing** items over time. A table below the chart counts each kind of action:

* incoming: **Create**, **Fetch**, **Duplicate**, **Sent To**, **Deschedule** and **Unspike**,
* outgoing: **Publish**, **Spike**, **Sent From**, **Publish Scheduled** and **Publish Embargo**.

**Production Time** measures the time between a story entering a desk and leaving it, for each desk. Under **Included Statistics** tick the figures you want: **Minimum**, **Average**, **Maximum** and **Sum**. On the **Filters** tab you can narrow down which actions count as entering and leaving a desk.

**Update Time** lists updated stories with the time it took to publish each update after the original. Click a story in the table to open the original or the update in a preview panel on the right.

**Featuremedia Updates** lists stories whose feature image was added, removed or changed after the story was first published. Click the slugline to preview the latest version of the story, or the original image to see it in detail.

### User Activity

**User Activity** shows what one person worked on during one day. Pick the **User** and the day under **Date Filter**. This report only works for a single day.

Each row of the chart is a story, labelled with its slugline. The bars show when the user had the story open for editing. Hover over a bar to see the slugline, headline, times and the actions taken. Click a bar to open a second chart below with the full timeline of that story, from creation to its last action, with one colour per user who touched it.

User Activity cannot be scheduled.

### Planning Usage

**Planning Usage** shows who uses the Planning component. For each user it counts the **Events**, **Planning** items, **Coverages** and **Assignments** they created in the chosen period. Only users whose role gives them access to Planning are included. See [Superdesk Planning Component](../superdesk-planning-component/README.md).

## Running a report

Every report is set up in the report panel. The panel has two tabs at the top: **Advanced**, where you set up the report, and **Saved**, where you find saved reports. The **Advanced** tab has three sections: **Parameters**, **Filters** and **Chart**. Planning Usage has no **Filters** section.

{% stepper %}
{% step %}
### Pick the report

Click the report list in the top bar and choose a report. The report panel opens on **Parameters**.
{% endstep %}

{% step %}
### Set the parameters

Fill in the report's own fields, such as **Group By** or **Desk**, and choose the period under **Date Filter**.
{% endstep %}

{% step %}
### Narrow down the content

Click **Filters** to limit the report to some desks, users, categories, sources and so on. See [Filtering the content](#filtering-the-content).
{% endstep %}

{% step %}
### Choose how to show it

Click **Chart** to pick the chart type and set a title. See [Charts and tables](#charts-and-tables).
{% endstep %}

{% step %}
### Run it

Click **Run Report**. The chart appears in the main area. If nothing matches, Superdesk shows "No data found".
{% endstep %}
{% endstepper %}

To start again from the report's default settings, click **Reset Filters**.

### Choosing the period

Under **Date Filter** pick one of these options:

| Group | Options |
| --- | --- |
| Absolute | **Range** (pick a **From** and **To** date), **Single Day** |
| Hours | **Relative Hours** (the last 1 to 72 hours) |
| Days | **Relative Days** (the last 1 to 31 days), **Yesterday**, **Today** |
| Weeks | **Relative Weeks** (the last 1 to 52 weeks), **Last Week**, **This Week** |
| Months | **Relative Months** (the last 1 to 12 months), **Last Month**, **This Month** |
| Year | **Last Year**, **This Year** |

Dates in the future are not allowed. Most reports start with a range covering the last 30 days. Update Time starts with **Yesterday**. Relative periods are worked out again every time the report runs, which makes them a good choice for saved and scheduled reports.

### Filtering the content

The **Filters** section shows one box per filter. The filters available depend on the report. They include **Desks**, **Users**, **Categories**, **Genre**, **Source**, **Urgency**, **Content State**, **Ingest Providers**, **Stages** and **Content Types**.

Type in a box to find values and pick one or more. Turn on **Exclude** in a box to leave the picked values out instead of keeping only them. The **Content State** box also has a **Rewrites** option: **Include Rewrites**, **Exclude Rewrites** or **Rewrites Only**.

## Charts and tables

The **Chart** section sets how the result looks:

* **Title** and **Subtitle**: leave them empty to use the title Superdesk suggests, or type your own.
* **Chart Type**: the types this report supports. Most reports offer **Bar**, **Column** and **Table**. Desk Activity offers **Bar**, **Column**, **Line**, **Area**, **Scatter** and **Spline**. Featuremedia Updates, Update Time and User Activity have only one layout, so no choice is shown.
* **Order Data In**: **Descending Order** or **Ascending Order**. Shown for Content Publishing, Featuremedia Updates, Planning Usage, Production Time and Publishing Performance.
* **Page Size**: the number of rows per page. Shown for Featuremedia Updates and Update Time.

You can change the chart type and run the report again at any time. Your choice is part of the report settings, so it is kept when you save the report.

## Exporting a report

To download a chart, click the menu button in the top-right corner of the chart and pick a format:

* **Print chart**
* **Download PNG image**
* **Download JPEG image**
* **Download SVG vector image**
* **Download PDF document**
* **Download CSV**, the data behind the chart as a spreadsheet file

<!-- VERIFY: open a chart's export menu, choose Download PDF document and check that a PDF downloads; if it does not, drop that bullet. -->

A report shown as a table has a smaller menu at the top right of the table, **Export Chart As...**, with one option: **CSV File**.

## Saving report settings

Save a report when you run the same report often. Superdesk saves the parameters, filters and chart settings, not the result, so a saved report always shows fresh data when you run it.

{% stepper %}
{% step %}
### Set up the report

Set the parameters, filters and chart options you want. **Save Report** only becomes active once you change something from the defaults.
{% endstep %}

{% step %}
### Open the save form

Click **Save Report** at the bottom of the report panel. The **Save Report** form opens.
{% endstep %}

{% step %}
### Name it

Enter a **Name** (required) and, if you like, a **Description**.
{% endstep %}

{% step %}
### Share it, if you can

Turn on **Make Global** to share the report with everyone who can view this report. You only see this switch if your role allows you to manage global saved reports.
{% endstep %}

{% step %}
### Save

Click **Save**. If you started from a saved report, **Save** updates it and **Save As** creates a new one.
{% endstep %}
{% endstepper %}

### Using saved reports

Click the **Saved** tab in the report panel. It lists **My Saved Reports** and **Global Saved Reports** for the current report, with a search box at the top. Global reports created by someone else show their owner.

* Click a saved report to load its settings, then click **Run Report**.
* Click the trash icon to delete it. You can delete your own reports, and other people's global reports if you manage global saved reports.

A saved report that has schedules cannot be deleted, and cannot be made private again, until its schedules are removed.

## Scheduling reports by email

Superdesk can email a report regularly, for example the Desk Activity of the past day every morning. A schedule always uses a global saved report, so save the report and turn on **Make Global** first. User Activity cannot be scheduled.

{% hint style="info" %}
You need the privilege to manage scheduled reports to see the **Schedules** switch, the **Schedule** button and the scheduling options in the three-dot menu.
{% endhint %}

{% stepper %}
{% step %}
### Open the schedule form

Open the **Saved** tab of the report panel. Click the three-dot menu next to the global saved report you want to send and choose **Create new schedule**. The schedule form opens with that saved report already picked.
{% endstep %}

{% step %}
### Turn it on and name it

Turn on **Active**. New schedules start inactive, and inactive schedules are never sent. Enter a **Name** and, if you like, a **Description**.
{% endstep %}

{% step %}
### Choose when

Under **When**, pick **Hourly**, **Daily**, **Weekly** or **Monthly**. For daily, weekly and monthly reports, pick the hour after **at**. For weekly reports, tick the days (**MO** to **SU**). For monthly reports, pick the day after **on the**: **first**, a day number, or **last**.
{% endstep %}

{% step %}
### Choose the report

Check the **Report Type** and the **Saved Report**. Only global saved reports are listed. Expand **Parameters** to check what the report contains.
{% endstep %}

{% step %}
### Set the email

Under **Email**, add the recipients in **To:**. You can pick Superdesk users or type any email address. Fill in **Subject:** and **Body**, then pick the **Format** (**JPEG Image**, **PNG Image** or **PDF File**) and the **Image Width**, from 400 to 1400 pixels.
{% endstep %}

{% step %}
### Create

Click **Create**. Superdesk shows "Report Schedule created!".
{% endstep %}
{% endstepper %}

Superdesk checks the schedules at the start of every hour. The hours are in the newsroom's time zone, set by your administrator, which may differ from your own.

### Managing schedules

Switch to **Schedules** in the top bar to see the schedules of the current report as cards. Click **Add New** there to create a schedule from scratch, picking the saved report in the form.

To see only the schedules of one saved report, load it from the **Saved** tab and click **Schedule** at the bottom of the report panel, or click its three-dot menu and choose **View schedules**. Each card shows when the report is sent, the format, the recipients, the saved report and, at the bottom, when it was last sent.

The icons at the top of each card let you:

* **Email this report**: send the report now, without waiting for the schedule,
* **Edit this Schedule**: change any setting, including turning **Active** off to pause it,
* **Delete this Schedule**: remove it after you confirm.

## Publishing Actions dashboard widget

Analytics also adds a **Publishing Actions** widget to the dashboard. It shows today's publishing actions for your current desk as a small chart: published, killed, corrected, updated and taken down items. In the widget settings you can change the colour of each action. Every user can add the widget, but it only loads data if your role has the **Analytics - Publishing Performance Reports** privilege. See [Dashboards and Widgets](../workspace-and-search/dashboards-and-widgets.md) for how to add a widget.

## For administrators

Analytics is a separate package, `superdesk-analytics`, with a client part and a server part. The standard Superdesk setup already includes it. If your installation does not:

* **Server**: install the `superdesk-analytics` Python package and add `"analytics"` to `INSTALLED_APPS` in `settings.py`.
* **Client**: add `superdesk-analytics` to the client `package.json`, then add `'superdesk.analytics'` to `apps` and `'superdesk-analytics'` to `importApps` in `superdesk.config.js`, and rebuild the client.

### Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `ANALYTICS_ENABLE_ARCHIVE_STATS` | `False` (`True` in the standard setup) | Collects the archive statistics that Desk Activity, Featuremedia Updates, Production Time, Update Time and User Activity need. The statistics are generated every hour. Without this setting those reports are not available. |
| `ANALYTICS_ENABLE_SCHEDULED_REPORTS` | `False` (`True` in the standard setup) | Sends scheduled reports by email, checking the schedules every hour. |
| `STATISTICS_MONGO_DBNAME`, `STATISTICS_MONGO_URI`, `STATISTICS_ELASTIC_URL`, `STATISTICS_ELASTIC_INDEX` | `statistics`, on the main MongoDB and Elasticsearch | Where the archive statistics are stored. |
| `HIGHCHARTS_LICENSE_TYPE`, `HIGHCHARTS_LICENSEE`, `HIGHCHARTS_LICENSEE_CONTACT`, `HIGHCHARTS_LICENSE_ID`, `HIGHCHARTS_LICENSE_CUSTOMER_ID`, `HIGHCHARTS_LICENSE_EXPIRY` | empty, type `OEM` | The license details shown by the **Highcharts License** button. |
| `DEFAULT_TIMEZONE` | | The time zone used for schedule hours and for the date filters. |
| `START_OF_WEEK` | | The first day of the week for weekly periods. |

Featuremedia Updates and Update Time are also not listed when `PUBLISH_ASSOCIATED_ITEMS` is on, because their privileges are not registered then.

Analytics draws its charts with Highcharts, a commercial charting library. You need a valid Highcharts license to use it.

Scheduled reports and the **Email this report** action need two things on the server:

* the Highcharts export server, which renders the charts as images. Install it with the `install-highcharts-server` command that comes with the package. If it is missing, Superdesk does not send scheduled reports.
* working email settings (`MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` and related settings). Reports are sent from the first address in `ADMINS`.

To fill the archive statistics for older content, run `python manage.py analytics:gen_archive_statistics --max-days 0`. By default the command only reads the last 3 days of item history (`--max-days`), and each run continues after the last history entry the previous run processed. So run it with `--max-days 0` right after you turn on `ANALYTICS_ENABLE_ARCHIVE_STATS`, before the first hourly run. Use `--item-id` to regenerate the statistics of a single item.

### Privileges

Grant these in **Settings** > **User Roles** > **Roles privileges**. See [User Management and User Roles](../administration/user-management-and-user-roles.md).

| Privilege | Allows |
| --- | --- |
| Analytics - Content Publishing Reports | Viewing the Content Publishing report |
| Analytics - Publishing Performance Reports | Viewing the Publishing Performance report |
| Analytics - Desk Activity Reports | Viewing the Desk Activity report |
| Analytics - Production Time Reports | Viewing the Production Time report |
| Analytics - User Activity Reports | Viewing the User Activity report |
| Analytics - Featuremdia Updates Report | Viewing the Featuremedia Updates report (the privilege label is spelled this way in Superdesk) |
| Analytics - Update Time Report | Viewing the Update Time report |
| Analytics - Planning Usage Reports | Viewing the Planning Usage report |
| Analytics - Manage Saved Reports | Saving reports and deleting your own saved reports |
| Analytics - Manage Global Saved Reports | Making saved reports global, and changing or deleting other users' global saved reports |
| Analytics - Manage Scheduling Reports | Creating, editing, deleting and emailing report schedules |

A user sees **Analytics** in the Main menu only if their role has at least one of the report privileges. Newsroom managers who should set up scheduled reports need the last three privileges as well, because a schedule can only use a global saved report.
