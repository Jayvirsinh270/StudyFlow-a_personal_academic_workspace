# StudyFlow - Your Personal Academic Workspace

A comprehensive desktop application for students to manage their academic life, including subjects, assignments, attendance, notes, CGPA tracking, and more.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## Features

- **Dashboard**: Overview of academic progress with study streak, upcoming assignments, and attendance summary
- **Subjects Management**: Add, edit, and organize subjects with faculty information and color coding
- **Subject Workspace**: Dedicated workspace for each subject with notes, files, and attendance tracking
- **Assignments**: Centralized assignment management with due dates, priorities, and status tracking
- **Attendance**: Track attendance across all subjects with bulk marking and percentage calculations
- **Planner**: Daily study planner integrating timetable, calendar events, and study tasks
- **Calendar**: Monthly calendar view with personal and academic events
- **CGPA Calculator**: Track semester GPAs and calculate overall CGPA with visual charts
- **Documents**: Centralized file management organized by subject
- **Focus Timer**: Pomodoro-style timer for productive study sessions
- **Global Search**: Search across subjects, notes, assignments, and files
- **Notifications**: Smart notifications for upcoming deadlines and low attendance alerts
- **Data Backup**: Export and import your data for safekeeping

## Screenshots

*Coming soon*

## Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package installer)

### Setup

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd student
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## Usage

### First Launch

On first launch, you'll see a welcome onboarding dialog to help you get started:
- Add your first subject
- Set up your profile and preferences
- Start with the dashboard

### Navigation

Use the sidebar to navigate between modules:
- **Dashboard**: Overview and quick actions
- **Subjects**: Manage your subjects
- **Assignments**: View and manage assignments
- **Attendance**: Track attendance across all subjects
- **Planner**: Daily schedule and tasks
- **Calendar**: Monthly events
- **Focus Timer**: Pomodoro timer
- **Documents**: File management
- **CGPA**: GPA tracking
- **Settings**: Profile and app preferences

### Keyboard Shortcuts

- `Alt+1-9`: Quick navigation to sidebar items
- `Alt+0`: Go to Settings
- `Ctrl+S`: Quick save (context-dependent)
- `Ctrl+F`: Focus search bar
- `Escape`: Close dialogs or return to dashboard

### Data Management

Your data is stored locally in the `UserData/` directory:
- Database: `UserData/studyflow.db`
- Files: `UserData/Files/`
- Logs: `logs/`

**Backup your data regularly** using Settings → Export Data (Backup)

## Project Structure

```
student/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── components/            # UI components
│   ├── header.py          # Top header with search and notifications
│   └── sidebar.py         # Navigation sidebar
├── modules/               # Feature modules
│   ├── dashboard/         # Dashboard overview
│   ├── subjects/          # Subject management
│   ├── assignments/       # Assignment tracking
│   ├── attendance/        # Attendance tracking
│   ├── planner/          # Study planner
│   ├── calendar/          # Calendar events
│   ├── cgpa/             # CGPA calculator
│   ├── documents/         # File management
│   ├── productivity/      # Pomodoro timer
│   └── settings/         # App settings
├── database/              # Database layer
│   ├── database.py        # Database connection
│   ├── db_setup.py       # Table creation
│   └── queries.py         # SQL queries
├── utils/                 # Utilities
│   ├── file_manager.py    # File operations
│   ├── theme.py          # Theme constants
│   └── logger.py         # Logging utility
└── UserData/              # User data (created on first run)
```

## Development

### Running Tests

```bash
python test_application.py
```

### Adding New Features

1. Create a new module in `modules/`
2. Add the module import to `main.py`
3. Add navigation entry to `components/sidebar.py`
4. Update page titles in `main.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Log important events using the logger utility

## Troubleshooting

### Application won't start

- Ensure Python 3.12+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify `UserData/` directory exists and is writable

### Database errors

- Check `logs/studyflow_*.log` for error details
- Ensure no other instance of StudyFlow is running
- Try deleting `UserData/studyflow.db` to reset (warning: this deletes all data)

### Theme not persisting

- Check database write permissions
- Verify `settings` table exists in database

## Dependencies

- `customtkinter>=5.2.0` - Modern UI framework
- `Pillow>=10.0.0` - Image processing
- `matplotlib>=3.8.0` - Charts and graphs
- `reportlab>=4.0.0` - PDF generation
- `tkcalendar>=1.6.0` - Calendar widget

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on the repository.

## Roadmap

- [ ] Mobile app version
- [ ] Cloud sync support
- [ ] Collaboration features
- [ ] Advanced analytics
- [ ] Integration with calendar apps
- [ ] Export to PDF reports

## Acknowledgments

Built with:
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [SQLite](https://www.sqlite.org/) - Database
- [Matplotlib](https://matplotlib.org/) - Data visualization

---

**StudyFlow** - Your Personal Academic Workspace © 2026
