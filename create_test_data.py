#!/usr/bin/env python3
"""
Script to create test data for VPN portal admin panel testing
"""

import json
import uuid
from datetime import datetime
from main import app, db, VPNRequest

def create_test_data():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Clear existing data
        VPNRequest.query.delete()
        db.session.commit()
        
        # Test data for different scenarios
        test_requests = [
            {
                'vpn_name': 'Partner Site A VPN',
                'vpn_type': 'Policy',
                'status': 'awaiting_details',
                'reason': 'Establish secure connection to partner site for joint project',
                'requester_name': 'John Smith',
                'requester_email': 'john.smith@company.com',
                'remote_contact_name': 'Alice Johnson',
                'remote_contact_email': 'alice.johnson@partnera.com',
                'local_team_email': 'network-team@company.com',
                'remote_agreed': False,
                'local_agreed': False,
                'remote_data': None,
                'local_data': None
            },
            {
                'vpn_name': 'Remote Office VPN',
                'vpn_type': 'Routed',
                'status': 'awaiting_agreement',
                'reason': 'Connect remote office to main headquarters',
                'requester_name': 'Sarah Davis',
                'requester_email': 'sarah.davis@company.com',
                'remote_contact_name': 'Bob Wilson',
                'remote_contact_email': 'bob.wilson@remoteoffice.com',
                'local_team_email': 'network-ops@company.com,security@company.com',
                'remote_agreed': True,
                'local_agreed': False,
                'remote_data': json.dumps({
                    'contact_name': 'Bob Wilson',
                    'contact_email': 'bob.wilson@remoteoffice.com',
                    'gateway': '203.0.113.10',
                    'ike_version': 'IKEv2',
                    'phase1_encryption': 'AES256',
                    'phase1_authentication': 'SHA256',
                    'phase1_dh_group': '14',
                    'phase1_lifetime': '86400',
                    'phase2_esp_encryption': 'AES256',
                    'phase2_esp_hash': 'SHA256',
                    'phase2_lifetime': '28800',
                    'phase2_pfs': 'Disabled',
                    'subnets': '192.168.100.0/24, 192.168.101.0/24',
                    'notes': 'Remote office connection for daily operations'
                }),
                'local_data': json.dumps({
                    'contact_name': 'Network Team',
                    'contact_email': 'network-ops@company.com',
                    'gateway': '198.51.100.5',
                    'ike_version': 'IKEv2',
                    'phase1_encryption': 'AES256',
                    'phase1_authentication': 'SHA256',
                    'phase1_dh_group': '14',
                    'phase1_lifetime': '86400',
                    'phase2_esp_encryption': 'AES256',
                    'phase2_esp_hash': 'SHA256',
                    'phase2_lifetime': '28800',
                    'phase2_pfs': 'Disabled',
                    'subnets': '10.0.0.0/8, 172.16.0.0/12',
                    'notes': 'Main corporate network'
                })
            },
            {
                'vpn_name': 'Data Center Link',
                'vpn_type': 'Routed',
                'status': 'complete',
                'reason': 'Backup data center connectivity for DR purposes',
                'requester_name': 'Mike Johnson',
                'requester_email': 'mike.johnson@company.com',
                'remote_contact_name': 'Lisa Brown',
                'remote_contact_email': 'lisa.brown@datacenter.com',
                'local_team_email': 'infrastructure@company.com',
                'remote_agreed': True,
                'local_agreed': True,
                'remote_data': json.dumps({
                    'contact_name': 'Lisa Brown',
                    'contact_email': 'lisa.brown@datacenter.com',
                    'gateway': '198.51.100.20',
                    'ike_version': 'IKEv2',
                    'phase1_encryption': 'AES256',
                    'phase1_authentication': 'SHA256',
                    'phase1_dh_group': '14',
                    'phase1_lifetime': '86400',
                    'phase2_esp_encryption': 'AES256',
                    'phase2_esp_hash': 'SHA256',
                    'phase2_lifetime': '28800',
                    'phase2_pfs': 'Disabled',
                    'subnets': '10.100.0.0/16, 10.101.0.0/16',
                    'notes': 'Data center backup connection'
                }),
                'local_data': json.dumps({
                    'contact_name': 'Infrastructure Team',
                    'contact_email': 'infrastructure@company.com',
                    'gateway': '203.0.113.50',
                    'ike_version': 'IKEv2',
                    'phase1_encryption': 'AES256',
                    'phase1_authentication': 'SHA256',
                    'phase1_dh_group': '14',
                    'phase1_lifetime': '86400',
                    'phase2_esp_encryption': 'AES256',
                    'phase2_esp_hash': 'SHA256',
                    'phase2_lifetime': '28800',
                    'phase2_pfs': 'Disabled',
                    'subnets': '10.0.0.0/8',
                    'notes': 'Main corporate infrastructure'
                })
            },
            {
                'vpn_name': 'Vendor Access VPN',
                'vpn_type': 'Policy',
                'status': 'cancelled',
                'reason': 'Temporary vendor access for system maintenance',
                'requester_name': 'Tom Wilson',
                'requester_email': 'tom.wilson@company.com',
                'remote_contact_name': 'Chris Miller',
                'remote_contact_email': 'chris.miller@vendor.com',
                'local_team_email': 'security-team@company.com',
                'remote_agreed': False,
                'local_agreed': False,
                'remote_data': None,
                'local_data': None
            }
        ]
        
        # Create VPN requests with tokens
        for i, req_data in enumerate(test_requests, 1):
            vpn = VPNRequest(
                id=i,  # Set explicit ID for consistency
                created_at=datetime.utcnow().isoformat(),
                vpn_name=req_data['vpn_name'],
                vpn_type=req_data['vpn_type'],
                reason=req_data['reason'],
                requester_name=req_data['requester_name'],
                requester_email=req_data['requester_email'],
                remote_contact_name=req_data['remote_contact_name'],
                remote_contact_email=req_data['remote_contact_email'],
                local_team_email=req_data['local_team_email'],
                remote_token=uuid.uuid4().hex,
                local_token=uuid.uuid4().hex,
                status=req_data['status'],
                remote_agreed=req_data['remote_agreed'],
                local_agreed=req_data['local_agreed'],
                remote_data=req_data['remote_data'],
                local_data=req_data['local_data']
            )
            db.session.add(vpn)
        
        db.session.commit()
        
        print("Test data created successfully!")
        print("Created 4 VPN requests with different statuses:")
        print("1. Partner Site A VPN - awaiting_details")
        print("2. Remote Office VPN - awaiting_agreement")
        print("3. Data Center Link - complete")
        print("4. Vendor Access VPN - cancelled")

if __name__ == '__main__':
    create_test_data()