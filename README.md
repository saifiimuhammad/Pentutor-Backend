# Pentutor Backend

This is the backend service for **Pentutor**, an advanced tutoring and mentorship platform tailored for programming, cybersecurity, and tech education.

It handles authentication, user management, course/session scheduling, messaging, admin controls, and all core business logic.

## 🌐 API Features

- 🔐 User Authentication (JWT/OAuth2)
- 🧑‍🏫 Role-based Access (Admin, Mentor, Student)
- 📅 Session Booking & Scheduling
- 💬 Real-time Chat APIs
- 📚 Course & Resource APIs
- 🛡️ Secure Input Validation & Error Handling
- 📈 Admin Dashboard Endpoints (Stats, Logs, etc.)

## 🛠️ Tech Stack

| Layer       | Tech Stack                   |
|-------------|------------------------------|
| Language    | Python / Node.js / PHP       |
| Framework   | Django / Express / Laravel   |
| Database    | PostgreSQL / MongoDB / MySQL |
| Auth        | JWT, OAuth2                  |
| Caching     | Redis (optional)             |
| Deployment  | Docker, Heroku/DigitalOcean  |

## 📁 Project Structure

```bash
pentutor-backend/
├── config/           # App settings and env configs
├── controllers/      # Request handlers and logic
├── models/           # DB models and schemas
├── routes/           # API endpoints
├── middleware/       # Auth, validation, etc.
├── utils/            # Helper functions
└── server.js / app.py / index.php
