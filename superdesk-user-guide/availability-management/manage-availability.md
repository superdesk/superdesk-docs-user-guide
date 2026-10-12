# Manage Availability

#### Administrator Capabilities

If you have the "Availability Manage" privilege, you can:

* View and modify any user's availability on the Availability Dashboard
* Override user-set availability
* Create or delete availability records for other users
* Ensure organizational coverage and planning needs

#### Override a User's Availability

**Create an Entry for Another User**

1. Navigate to the **User Availability Management** Dashboard
2. Select the the date and click on the user name in the availability entry
3. Set the status and working hours
4. Click **Save**

The entry is marked with the current user as `last_updated_by`.

**Update Another User's Availability**

1. Select an existing record for the user
2. Modify the status, hours, or tags
3. Save changes
4. The user can see that an admin modified their record

<figure><img src="../../.gitbook/assets/grafik (13).png" alt=""><figcaption><p>User with Management privilege edits the availability of another user</p></figcaption></figure>

#### Monitor Coverage

1. View the **Team Availability Calendar**
2. Identify gaps in coverage for specific dates
3. See which desks or specializations have availability
4. Use tags to filter by department or skill area

#### Permissions & Restrictions

| Action                      | Allowed    | Requires                  |
| --------------------------- | ---------- | ------------------------- |
| View own availability       | ✓          | `Availability View`       |
| Modify own availability     | ✓          | `Availability Manage own` |
| View others' availability   | ✓          | `Availability View`       |
| Modify others' availability | Admin only | `Availability Manage`     |
| Delete availability records | Admin only | `Availability Manage`     |
| Override user settings      | Admin only | `Availability Manage`     |

#### Manage the used Tasks and Subtasks via CV

This requires Superdesk admin rights.

Under Settings/Metadata fine the Controlled Vocabulary with the ID: `availability_manager_tags`

<figure><img src="../../.gitbook/assets/grafik (14).png" alt=""><figcaption><p>Manage the Availability Manager Tags</p></figcaption></figure>

Edit the CV with its Tasks and Subtasks. For example organize the Coverage for certain Regions by setting up the CV accordingly:

Province A\
&#x20;    \- Region X\
&#x20;    \- Region Y\
Province B\
&#x20;    \- Region Z

***
