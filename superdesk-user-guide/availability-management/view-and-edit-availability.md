# View and edit Availability

#### Understanding Your Availability

Your availability information consists of two parts:

* **Default Weekly Schedule**\
  Your recurring template that defines when you typically work each week.
* **Daily Records**\
  Individual entries for specific dates that override or supplement your defaults.

#### View Your Availability

**In Your Profile**

1. Go to **User Profile** → **Availability**
2. View your default working schedule for each day of the week
3. See upcoming generated availability (up to 12 weeks ahead)
4. Check any manually added daily entries

**In the Dashboard**

1. Navigate to the **Availability Dashboard** (if your organization has one)
2. View your availability in calendar or list format
3. See published articles and events per day (if tracked)

<figure><img src="../../.gitbook/assets/grafik (12).png" alt=""><figcaption><p>The availability dashboard</p></figcaption></figure>

#### Edit Default Working Schedule

**General Settings: Select your Language and Tasks**

1. Specify your working language (e.g., English, French, Spanish) (currently this only works for one language per user). These are inherited by all daily records created from this schedule
2. Add organizational tasks that you may take over (e.g., a certain Region or type of Coverage). This narrows down the list of tasks to select from when setting your schedule

**Set or edit default working schedule**

Your default schedule sets the pattern for future automatic generation.

<figure><img src="../../.gitbook/assets/grafik (10).png" alt="Screenshot of the modal to set the users regular availability throughout a week."><figcaption><p>Edit your weekly Availability in this form.</p></figcaption></figure>

**Access Your Default Settings**

1. Open your **User Profile**
2. Go to **Availability** section
3. Select **Edit Default Schedule**

**Configure Each Day**

For each day of the week, specify the following. If you select partial availability, please also set the respective end and start time:

| Field      | Required | Description                                             |
| ---------- | -------- | ------------------------------------------------------- |
| **Status** | Yes      | Available / Partial / Unavailable                       |
| **Tags**   | Optional | Categorization (e.g., "regular", "morning", "training") |

**Example Default Schedule**

Code

```
Monday:     (Available)
Tuesday:    (Available)
Wednesday:  (Partial)        09:00 - 13:00  
Thursday:   (Available)
Friday:     (Available)
Saturday:   (Unavailable)
Sunday:     (Unavailable)
```



**The system automatically**

* Regenerates future availability records (up to 12 weeks)
* Only affects dates marked as `_generated: true`
* Does NOT change manually-set daily entries

#### Edit Specific Day Availability

For dates different from your default schedule.

<figure><img src="../../.gitbook/assets/grafik (11).png" alt=""><figcaption><p>To edit specific availability on a give date - click on the date and either edit or discard the availability of this day</p></figcaption></figure>

**Access Daily Records**

1. In your user profile. Go to the **Availability** tab
2. Select the date you want to modify and click on it
3. Find a layover to either discard individual Settings or **Edit** them

**Modify a Single Day**

Update any of these fields:

| Field                                     | Description                                              |
| ----------------------------------------- | -------------------------------------------------------- |
| **Date**                                  | The specific date (read-only if editing existing record) |
| **Status**                                | Available / Partial / Unavailable                        |
| **Start Time (for partial availability)** | Your available start time (HH:MM format)                 |
| **End Time (for partial availability)**   | Your available end time (HH:MM format)                   |
| **Tags**                                  | Custom notes or categorization                           |

**Save Your Changes**

1. Click **Save** when finished
2. The record is marked as manually-set (not auto-generated)
3. Your manual entry overrides any auto-generated default

#### Delete an Availability Record

1. Select the record you wish to remove
2. Click **Delete**

