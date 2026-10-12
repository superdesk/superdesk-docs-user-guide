# How to set it up

#### Before you start

The Availability Manager module must be enabled in your Superdesk installation. It is included in the default modules list (`apps.user_availability`). In case of doubt, reach out to your Superdesk Admin to make sure its enabled.

#### Required Privileges for Availability Managers and users

Three privilege levels control access to the Availability Manager. You can set them as Superdesk admin by opening the burger menu Settings/User Roles and provide the respective user types with the access they require:

1. **Availability - view** (`user_availability`)
   * Allows viewing the availability dashboard
   * Required for monitoring, checking team availability
2. **Availability - manage** (`user_availability_manage`)
   * Allows Availability adminis to override or modify any user's availability settings
   * Used by Availability Managers for manual adjustments and management
3. **Availability - manage own availability** (`user_availability_manage_own`)
   * Allows users to configure their own availability settings
   * Recommended for all team members who need to set their availability

#### For Administrators: Enable the Feature

**Step 1: Grant User Privileges**

1. Navigate to **User Roles, Roles Priviliges** in the Admin panel
2. Select or edit a role
3. Under **Privileges**, assign:
   * Availability Manage own - enables personal availability management
   * Availability View - enables viewing team availability (optional, for dashboards)
   * Availability Manage - enables admin overrides (for admin users only)

**Step 2: Verify Module Loading**

The feature auto-loads if included in the SUPERDESK\_APPS configuration:

Python

```
SUPERDESK_APPS = [
    # ... other apps ...
    "apps.user_availability",
    # ... other apps ...
]
```

**Step 3: Automated Availability Generation**

The system automatically generates availability records:

* **Schedule**: Daily at 1:40 AM (configurable via Celery Beat)
* **Duration**: Generates 12 weeks of recurring schedules (configurable via `AVAILABILITY_GENERATE_WEEKS`)
* **Scope**: Only for active users with enabled availability settings
* **Trigger**: Automatically runs when a user updates their default working days or languages

No additional setup is required for automation once the module is enabled.

**Step 4: Controlled Vocabulary**

Navigate to Settings/Metadata and look for a Controlled Vocabulary to manage the features Tasks and Subtasks to be assigned to the Freelancers or Correspondents using the feature to track and share their Availability. It can also be used to manage Coverage of Provinces and its Regions for example.

* The CV needs to have the ID availability\_manager\_tags and its name shows up in the Frontend View
* The CV works with two levels like Task and Subtask or Province and Region.

#### For Users: Initial Setup

Once your administrator has granted `user_availability_manage_own` privilege:

1. Open your **User Profile** (usually via account menu)
2. Navigate to the **Availability** section
3. You should now see options to enable and configure your availability
4. Without the checkbox switched on in the user profile the user will not be displayed in the Availability views
