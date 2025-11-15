# Weekly Update — AUIB VMS Project

---

## Week ending: November 15, 2025

### Weekly Accomplishments
- **Database Migration:** Successfully removed SQLite dependency, making the system PostgreSQL-only for production stability
- **Docker Deployment:** Fixed critical deployment issues including module imports and database seeding
- **Officer Approval Workflow:** Implemented event volunteer approval system where officers can approve/reject volunteer signups
- **Enhanced UI:** Added summary cards and action buttons to event volunteers page with visual status indicators
- **Template Improvements:** Updated event_volunteers.html with conditional approve/reject/remove actions based on volunteer status

### Features Implemented
- **Event Volunteer Management:**
  - Officers can now approve volunteer signups from the event_volunteers page
  - Added approve/reject buttons for pending volunteers
  - Added remove button for approved volunteers to revoke access if needed
  - Summary cards showing Total Signups, Pending Approval, and Approved counts
  
- **Database Architecture:**
  - Removed SQLite fallback to ensure consistent PostgreSQL usage
  - Added DATABASE_URL validation with clear error messages
  - Optimized connection pooling for multi-worker Docker environment
  
- **UI/UX Design:**
  - Created professional CSS design system for Support Tickets pages
  - Added tickets-enhanced.css for ticket list/index page
  - Added ticket-detail.css for ticket detail/view page
  - color-coded status badges, and modern card layouts

### Challenges Encountered
- Docker multi-worker race conditions during database seeding required idempotent initialization
- Template updates not immediately visible required Docker container restarts
- Coordinating approval workflow with existing TimeLog status field values

### Goals & Next Steps
- Apply new CSS files to ticket templates (index.html and view.html)
- Test approve/reject functionality thoroughly in production environment
- Complete UI/UX enhancements for remaining pages
- Prepare for IT HOD meeting with updated feature demonstrations

---

## Week ending: October 26, 2025

### Weekly Accomplishments
This week, our group made major improvements to the backend of the AUIB VMS project:
- Made club and volunteer management easier
- Streamlined event creation and approval
- Improved email notifications
- Strengthened user login and security
- Enhanced reporting and system reliability

### Challenges Encountered
- Integrating new features with existing database models required extra testing and debugging
- Ensuring email notifications were sent reliably for all user actions
- Maintaining compatibility with older templates during backend upgrades

### Goals & Next Steps
- Continue implementing features from the backlog
- Run a full linter and test suite to catch any remaining issues
- Update README and changelog with new backend structure and instructions
- Prepare summary and checklist for the upcoming AUIB IT HOD meeting

### Features Implemented

- **Club & Volunteer Management:**
  - Added features to track club members, officers, and volunteers, making it easier to see who is involved and their roles.
  - Improved the way volunteer hours are submitted and approved, so club leaders and officers can review and confirm hours quickly.

- **Event Creation & Approval:**
  - Built tools for creating new events, submitting them for approval, and tracking their status from "pending" to "approved" or "rejected".
  - Made it possible for club leaders to request events and for admins to see all requests in one place.

- **Email Notifications:**
  - Set up automatic email alerts for important actions, like when a volunteer submits hours or an event is approved.
  - Added a log so admins can see which emails were sent and when.

- **User Login & Security:**
  - Improved login and password reset features to make it easier for users to access their accounts securely.
  - Added role-based access so only authorized users can see or change certain information.

- **Reporting & Logs:**
  - Created simple reports for club leaders and admins to view volunteer activity, event participation, and system logs.
  - Made it easier to track changes and spot issues quickly.

- **System Reliability:**
  - Fixed bugs that could cause errors when loading pages or sending emails.
  - Improved database connections and error handling to keep the system running smoothly.

### Verification & Next Steps
- Implement features from the backlog
- Lint issues addressed; recommend full linter and test run next.
- Update README and changelog with new structure and instructions.
- Prepare summary and checklist for AUIB IT HOD meeting.

### Meeting Booked
- **Purpose:** Confirm project follows AUIB standards and finalize migration plan.
- **Attendees:** IT HOD, Student life office, Project Team.
- **Agenda:**
  1. Review changes and standards
  2. Confirm compliance requirements
  3. Plan next steps and timeline

---
*This file is updated weekly to track project progress and key decisions.*
