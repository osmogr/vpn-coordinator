# VPN Request & Coordination Portal

A Flask-based web application for coordinating site-to-site VPN requests between remote contacts and local network teams. This portal streamlines the VPN setup process by collecting requirements from both sides and ensuring mutual agreement before finalization.

## Features

- **Initial VPN Request Form**: Collect basic VPN requirements and contact information
- **Tokenized Access**: Secure unique links sent to remote contacts and local teams
- **Separate Forms**: Remote and local teams fill in their technical details independently
- **Review & Agreement Process**: Both parties must review and agree to the final configuration
- **Admin Panel**: Manage all VPN requests and resend email notifications
- **Email Integration**: Automated email notifications throughout the process

## Screenshots

### Main Submission Interface
The initial form where VPN requests are submitted:

![VPN Submission Form](https://github.com/user-attachments/assets/f1832214-5a9d-4fce-807e-636e04f86b94)

### Admin Panel
Administrative interface for managing VPN requests:

![Admin Panel](https://github.com/user-attachments/assets/c289c437-1b87-4b63-9420-b86c6d06e27f)

## Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/osmogr/vpn-coordinator.git
   cd vpn-coordinator
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy
   ```

4. **Set environment variables (optional)**
   ```bash
   export BASE_URL="http://localhost:5000"  # For correct email links
   ```

5. **Start the application**
   ```bash
   python main.py
   ```

6. **Open your browser**
   Navigate to http://127.0.0.1:5000

## Usage Workflow

### 1. Submit New VPN Request
- Fill out the initial form with:
  - VPN Name/Vendor
  - VPN Type (Policy or Routed)
  - Business justification
  - Contact information for remote and local teams
- Click "Submit Request"

### 2. Email Notifications
After submission, the system automatically:
- Generates unique tokens for remote and local teams
- Sends email notifications with secure links to both parties
- Each party receives a link to their specific form

### 3. Remote Team Form
The remote contact receives a link to provide:
- Gateway IP address
- IKE version and configuration
- Cryptographic settings
- Diffie-Hellman group
- Pre-shared key (PSK)
- Protected subnets
- Additional notes

### 4. Local Team Form  
The local network team receives a link to provide:
- Local gateway configuration
- IKE and encryption preferences
- Local protected networks
- Technical notes and requirements

### 5. Review & Agreement
When both sides submit their details:
- Review emails are sent to both parties
- Each side can review the complete configuration
- Both parties must explicitly agree to proceed
- Either side can edit their information if needed

### 6. Finalization
Once both parties agree:
- Final summary email sent to all stakeholders
- VPN request marked as completed
- Configuration details preserved for implementation

## Admin Panel

Access the admin panel at `/admin` to:
- View all VPN requests in a tabular format
- Check request status and details
- Resend email notifications:
  - **Resend Initial**: Re-send initial access links
  - **Resend Agreement**: Re-send review & agreement emails
  - **Resend Final**: Re-send final summary emails

## Configuration

### Environment Variables

- `BASE_URL`: Public base URL for the application (default: http://localhost:5000)
- `SMTP_HOST`: SMTP server hostname
- `SMTP_PORT`: SMTP server port  
- `SMTP_USER`: SMTP username
- `SMTP_PASS`: SMTP password
- `SMTP_FROM`: From email address

**Note**: If SMTP settings are not configured, email content will be printed to the console for testing.

### Email Configuration Example
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASS="your-app-password"
export SMTP_FROM="vpn-portal@yourcompany.com"
```

## Security Considerations

⚠️ **Important Security Notes**:

- **Tokens**: Links contain unguessable UUIDs but should be treated as sensitive
- **PSKs**: Pre-shared keys are stored in plaintext - **NOT suitable for production use**
- **HTTPS**: Use HTTPS in production environments
- **Authentication**: Add proper authentication and authorization for production
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Access Control**: Consider IP allowlists for admin panel access

## Database

The application uses SQLite by default with the following tables:
- `vpn_request`: Main request information
- `remote_details`: Remote team technical details  
- `local_details`: Local team technical details

Database file is created automatically as `vpn_portal.db` in the project directory.

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
python main.py
```

The application runs in debug mode by default, providing:
- Automatic reloading on code changes
- Detailed error messages
- Debug toolbar

## Troubleshooting

### Common Issues

1. **Module not found errors**
   ```bash
   pip install flask flask-sqlalchemy
   ```

2. **Email not sending**
   - Check SMTP configuration
   - Verify firewall settings
   - Check console output for email content

3. **Database errors**
   - Delete `vpn_portal.db` to reset the database
   - Check file permissions

4. **Port already in use**
   ```bash
   # Kill process using port 5000
   lsof -ti:5000 | xargs kill -9
   ```

## API Endpoints

- `GET /`: Main submission form
- `POST /request/new`: Process new VPN request
- `GET /remote/<token>`: Remote team form
- `POST /remote/<token>`: Submit remote details
- `GET /local/<token>`: Local team form  
- `POST /local/<token>`: Submit local details
- `GET /agree/<token>`: Review and agreement page
- `POST /agree/<token>`: Submit agreement
- `GET /admin`: Admin panel
- `GET /_status`: Application health check

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
