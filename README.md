# VPN Request & Coordination Portal

A Flask-based web application for coordinating site-to-site VPN requests between remote contacts and local network teams. This portal streamlines the VPN setup process by collecting requirements from both sides and ensuring mutual agreement before finalization.

## Features

- **Initial VPN Request Form**: Collect basic VPN requirements and contact information
- **Tokenized Access**: Secure unique links sent to remote contacts and local teams
- **Structured Detail Forms**: Remote and local teams fill in their technical details using dropdown menus with preferred values to prevent configuration errors and ensure consistency
- **Cryptographic Parameter Dropdowns**: Pre-defined options for encryption, authentication, DH groups with clearly marked preferred values (e.g., "AES256 (Preferred)")
- **Phase 1 & Phase 2 Configuration**: Organized forms with separate sections for IKE Phase 1 and Phase 2 parameters
- **Review & Agreement Process**: Both parties must review and agree to the final configuration with enhanced structured display
- **Admin Panel**: Manage all VPN requests and resend email notifications
- **Email Integration**: Automated email notifications throughout the process
- **Document Generation**: Professional PDF and TXT documents for completed VPN requests
- **Email Attachments**: Automatic attachment of PDF and TXT documents to final summary emails
- **Document Downloads**: Admin panel download links for easy access to generated documents

## Screenshots

### Main Submission Interface
The initial form where VPN requests are submitted:

![VPN Submission Form](https://github.com/user-attachments/assets/35895014-d17e-47c6-a454-519f613681d4)

### VPN Detail Form with Dropdown Menus
The enhanced remote/local forms with structured Phase 1 and Phase 2 sections featuring dropdown menus for cryptographic parameters. Preferred values are clearly marked and selected by default to guide users toward recommended security settings:

![Detail Form with Dropdowns](https://github.com/user-attachments/assets/61cfd885-699f-4915-9c8c-316610a9d00f)

### Enhanced Review Page
The structured review page displaying configuration details in organized Phase 1 and Phase 2 sections, making it easier to compare settings between local and remote parties:

![Enhanced Review Page](https://github.com/user-attachments/assets/776c002e-40bd-4f4f-b3fb-71d13036a7ab)

### Admin Panel
Administrative interface for managing VPN requests with document download capabilities:

![Admin Panel](https://github.com/user-attachments/assets/a84fecb5-c56d-40a8-bdb4-10ebed5ea2a5)

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
   pip install flask flask-sqlalchemy reportlab
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
The remote contact receives a link to provide technical details through structured dropdown menus:

**Phase 1 Configuration:**
- **Encryption**: Choose from AES256 (Preferred) or AES128
- **Authentication**: Select SHA256 (Preferred) or SHA1  
- **DH Group**: Pick from options 14 (Preferred), 18, 19, 20, or 22
- **Life Time**: Text entry with "86400 (Preferred)" placeholder guidance

**Phase 2 Configuration:**
- **ESP Encryption**: Choose from AES256 (Preferred) or AES128
- **ESP Hash**: Select SHA256 (Preferred) or SHA1
- **Life Time**: Text entry with "28800 (Preferred)" placeholder guidance
- **PFS**: Choose between Disabled (Preferred) or Enabled

**Additional Information:**
- Gateway IP address and IKE version (text fields)
- Protected subnets and additional notes

### 4. Local Team Form  
The local network team receives a link to provide their configuration using the same structured dropdown format:
- Identical Phase 1 and Phase 2 dropdown options as remote form
- Local gateway configuration and protected networks
- Technical notes and requirements
- Consistent user experience with preferred values clearly marked

### 5. Review & Agreement
When both sides submit their details:
- Review emails are sent to both parties with structured Phase 1/Phase 2 display
- Each side can review the complete configuration in an organized format
- Both parties must explicitly agree to proceed
- Either side can edit their information if needed (form state is preserved)

### 6. Finalization
Once both parties agree:
- Final summary email sent to all stakeholders
- VPN request marked as completed
- Configuration details preserved for implementation

### 7. Document Generation
For completed VPN requests:
- **PDF Documents**: Professional formatted documents with tables, sections, and proper styling
- **TXT Documents**: Plain text format for easy archival and system integration
- **Email Attachments**: PDF and TXT files automatically attached to final summary emails
- **Admin Downloads**: Documents available for download from the admin panel

## Admin Panel

Access the admin panel at `/admin` to:
- View all VPN requests in a tabular format
- Check request status and details
- Resend email notifications:
  - **Resend Initial**: Re-send initial access links
  - **Resend Agreement**: Re-send review & agreement emails
  - **Resend Final**: Re-send final summary emails (includes document attachments)
- Download generated documents:
  - **📄 PDF**: Download professional formatted documentation
  - **📝 TXT**: Download plain text documentation
  - *Note: Download links only appear for completed VPN requests*

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

## Document Generation

The application generates professional documentation for completed VPN requests:

### Document Types
- **PDF Documents**: Professional formatted files with:
  - Proper styling and layout using ReportLab
  - Tables for technical specifications
  - Complete VPN request details and metadata
  - Contact information for both parties
  - Agreement status tracking

- **TXT Documents**: Plain text files containing:
  - All VPN request information in readable format
  - Technical specifications in structured text
  - Easy archival and system integration format

### Document Storage
- Generated documents are stored in the `documents/` directory
- Filenames include VPN name and request ID for easy identification
- Documents are automatically created when VPN requests are completed
- Files are attached to final summary emails and available for admin download

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
   pip install flask flask-sqlalchemy reportlab
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
- `GET /admin/download/<request_id>/<file_type>`: Download generated documents (PDF or TXT)
- `GET /_status`: Application health check

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
