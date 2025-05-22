# Mining Ledger Management System

A secure and modern web application for managing mining department ledgers with separate access for mining and finance departments.

## Features

- Secure login system
- Responsive design that works on all devices
- Modern UI with mining-themed elements
- Separate dashboards for different departments
- Easy-to-use interface

## Login Credentials

### Mining Department
- **Username:** mining_admin
- **Password:** mining@123

### Finance Department
- **Username:** finance_admin
- **Password:** finance@123

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cash_control
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Security Note

This is a development setup. For production use:
- Use environment variables for sensitive information
- Implement proper user authentication with a database
- Use HTTPS
- Set a strong secret key in the environment variables

## License

This project is proprietary and confidential.
