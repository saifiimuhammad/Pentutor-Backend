# Pentutor Backend

This is the backend service for **Pentutor**, an advanced tutoring and mentorship platform tailored for programming, cybersecurity, and tech education.

It powers all core backend operations including authentication, user management, scheduling, messaging, and admin dashboard functionalities.

---

## 🌐 API Features

- 🔐 User Authentication (JWT + OAuth2 ready)
- 🧑‍🏫 Role-based Access (Admin, Mentor, Student)
- 📅 Session Booking & Scheduling APIs
- 💬 Real-time Messaging System (via Channels/WebSockets)
- 📚 Course, Subject, and Resource APIs
- 🛡️ Secure Input Validation & Exception Handling
- 📈 Admin Dashboard Stats and Logs

---

## 🛠️ Tech Stack

| Layer       | Tech Stack             |
|-------------|------------------------|
| Language    | Python                 |
| Framework   | Django + Django REST   |
| Frontend    | React (separate repo)  |
| Database    | PostgreSQL             |
| Auth        | JWT (via djangorestframework-simplejwt) |
| Caching     | Redis (for sessions/chat) |
| Deployment  | Docker, Heroku / DigitalOcean |

---

## 📁 Project Structure

```bash
pentutor-backend/
├── pentutor_backend/      # Main Django project (settings, URLs, etc.)
├── apps/                  # Custom apps (auth, courses, chat, scheduling, etc.)
│   ├── auth/              # JWT login/register, OAuth, roles
│   ├── users/             # Mentor/Student profiles
│   ├── courses/           # Course APIs, content, categories
│   ├── schedules/         # Booking and calendar logic
│   ├── chat/              # Messaging, WebSocket handlers
│   └── dashboard/         # Admin APIs, logs, analytics
├── config/                # Environment and global settings
├── requirements.txt       # Python package requirements
├── manage.py              # Django CLI entry point
└── Dockerfile             # For containerization
