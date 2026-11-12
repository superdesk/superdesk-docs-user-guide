# How to set it up

## Before you start

Availability Management is part of the standard Superdesk installation. If you do not see it, ask your administrator to check that it is enabled.

## Privileges for availability managers and users

Three privileges control access to Availability Management. Administrators give them to roles in **Settings** > **User Roles**:

1. **Availability - view** (`user_availability`)
   * Shows the **Availability Management** dashboard.
   * Give it to people who need to check the team's availability.
2. **Availability - manage** (`user_availability_manage`)
   * Lets availability managers change the availability of any user.
   * Give it to the people who plan coverage and need to make manual changes.
3. **Availability - manage own availability** (`user_availability_manage_own`)
   * Shows the **Availability** section in the user's own profile, where they set their availability.
   * Give it to everyone who should enter their availability.

## For administrators: enable the feature

### Step 1: Grant the privileges

{% stepper %}
{% step %}
### Open the role privileges

Open the Main menu, click **Settings** and then **User Roles**. Click the **Roles privileges** tab.
{% endstep %}

{% step %}
### Tick the privileges

Find the three **Availability** rows and tick them in the column of each role that needs them:

* **Availability - manage own availability** for everyone who sets their own availability.
* **Availability - view** for people who check the dashboard.
* **Availability - manage** only for availability managers.
{% endstep %}

{% step %}
### Save

Click **Save**.
{% endstep %}
{% endstepper %}

### Step 2: Set up the tasks and subtasks

Tasks and subtasks are the things a person can be assigned to, for example a type of coverage, or a province and its regions. They live in a controlled vocabulary.

1. Open the Main menu, click **Settings** and then **Metadata**.
2. Find the vocabulary with the ID `availability_manager_tags`. Its name is what people see in the dashboard and in their profile, so you can rename it to suit your newsroom.
3. Add the items. The vocabulary has two levels, such as Task and Subtask, or Province and Region.

Availability also uses the `languages` vocabulary for the language filter and the language field. Both vocabularies must exist, or Availability Management does not start. See [Manage Availability](manage-availability.md#manage-the-tasks-and-subtasks) for an example.

### Step 3: Check the server setup

The backend module (`apps.user_availability`) is on by default, so there is usually nothing to do here. Every night Superdesk fills in the coming 12 weeks for each active user from their default schedule. It also does this straight away when someone changes their default schedule or language. Entries that someone set by hand are never overwritten. Your system administrator can change the number of weeks with the `AVAILABILITY_GENERATE_WEEKS` setting. The dashboard link sits in the Main menu by default; it can be moved to the Workspace Panel with the extension's `dashboard.addLinkToSideMenu` option.

## For users: initial setup

Once your administrator has given you the **Availability - manage own availability** privilege:

1. Click your avatar in the top-right corner and click **Manage profile**.
2. Click the **Availability** tab at the top of your profile.
3. Tick **Enabled**. The language, task and calendar options appear.

You only show up on the Availability Management dashboard while **Enabled** is ticked. See [View and edit Availability](view-and-edit-availability.md) for the next steps.
