import boto3
import os
import json
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

def get_config():
    return {
        'aws_regions': os.environ.get('AWS_REGIONS', '').split(','),
        'retention_days': int(os.environ.get('RETENTION_DAYS', 30)),
        'dry_run': os.environ.get('DRY_RUN', 'false').lower() == 'true',
        'sender_email': os.environ['SENDER_EMAIL'],
        'recipient_email': os.environ['RECIPIENT_EMAIL'],
        'ses_region': os.environ.get('SES_REGION', 'us-east-1')
    }

def process_region(ec2, retention_days, dry_run):
    deleted_count = 0
    size_saved = 0

    active_volumes = get_active_volumes(ec2)
    print(f"Found {len(active_volumes)} active volumes")
    snapshots = get_all_snapshots(ec2)

    for snapshot in snapshots:
        if should_delete_snapshot(snapshot, active_volumes, retention_days):
            size_saved += snapshot['VolumeSize']
            if not dry_run:
                try:
                    ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
                    deleted_count += 1
                    print(f"Deleted snapshot {snapshot['SnapshotId']}")
                except ClientError as e:
                    print(f"Error deleting snapshot {snapshot['SnapshotId']}: {str(e)}")
            else:
                deleted_count += 1
                print(f"Would delete snapshot {snapshot['SnapshotId']} (dry run)")

    return deleted_count, size_saved

def get_active_volumes(ec2):
    volumes = set()
    paginator = ec2.get_paginator('describe_volumes')
    for page in paginator.paginate(Filters=[{'Name': 'status', 'Values': ['in-use']}]):
        volumes.update(v['VolumeId'] for v in page['Volumes'])
    return volumes

def get_all_snapshots(ec2):
    snapshots = []
    paginator = ec2.get_paginator('describe_snapshots')
    for page in paginator.paginate(OwnerIds=['self']):
        snapshots.extend(page['Snapshots'])
    print(f"Found {len(snapshots)} snapshots")
    return snapshots

def should_delete_snapshot(snapshot, active_volumes, retention_days):
    snapshot_id = snapshot['SnapshotId']
    
    if 'Tags' in snapshot:
        for tag in snapshot['Tags']:
            if tag['Key'] == 'KeepForever' and tag['Value'].lower() == 'true':
                print(f"Snapshot {snapshot_id} has KeepForever tag")
                return False

    if snapshot['VolumeId'] in active_volumes:
        print(f"Snapshot {snapshot_id} is associated with an active volume")
        return False

    snapshot_date = snapshot['StartTime'].replace(tzinfo=None)
    if datetime.utcnow() - snapshot_date < timedelta(days=retention_days):
        print(f"Snapshot {snapshot_id} is newer than retention period")
        return False

    print(f"Snapshot {snapshot_id} is eligible for deletion")
    return True

def send_email_report(ses, config, report):
    subject = "EBS Snapshot Cleanup Report"
    
    body_text = (
        f"EBS Snapshot Cleanup Report\n\n"
        f"Total snapshots deleted: {report['total_snapshots_deleted']}\n"
        f"Total size saved: {report['total_size_saved_gb']} GB\n"
        f"Dry run: {report['dry_run']}\n\n"
        "Region-wise breakdown:\n"
        f"{chr(10).join(report['region_reports'])}"
    )
    
    body_html = f"""
    <html>
    <head></head>
    <body>
        <h1>EBS Snapshot Cleanup Report</h1>
        <p>Total snapshots deleted: {report['total_snapshots_deleted']}</p>
        <p>Total size saved: {report['total_size_saved_gb']} GB</p>
        <p>Dry run: {report['dry_run']}</p>
        <h2>Region-wise breakdown:</h2>
        <ul>
            {''.join(f'<li>{line}</li>' for line in report['region_reports'])}
        </ul>
    </body>
    </html>
    """
    
    try:
        response = ses.send_email(
            Source=config['sender_email'],
            Destination={'ToAddresses': [config['recipient_email']]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text},
                    'Html': {'Data': body_html}
                }
            }
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")

def lambda_handler(event, context):
    config = get_config()
    
    if not config['aws_regions'] or config['aws_regions'][0] == '':
        config['aws_regions'] = [boto3.session.Session().region_name]
    
    total_deleted = 0
    total_size_saved = 0
    region_reports = []

    for region in config['aws_regions']:
        ec2 = boto3.client('ec2', region_name=region)
        deleted, size_saved = process_region(ec2, config['retention_days'], config['dry_run'])
        total_deleted += deleted
        total_size_saved += size_saved
        region_reports.append(f"Region {region}: {deleted} snapshots deleted, {round(size_saved / 1024, 2)} GB saved")

    report = {
        'total_snapshots_deleted': total_deleted,
        'total_size_saved_gb': round(total_size_saved / 1024, 2),
        'dry_run': config['dry_run'],
        'region_reports': region_reports
    }

    print(json.dumps(report, indent=2))
    
    # Send email report
    ses = boto3.client('ses', region_name=config['ses_region'])
    send_email_report(ses, config, report)

    return report

if __name__ == "__main__":
    # This block is for local testing only
    os.environ['AWS_REGIONS'] = 'us-east-1,eu-west-1'
    os.environ['RETENTION_DAYS'] = '7'
    os.environ['DRY_RUN'] = 'true'
    os.environ['SENDER_EMAIL'] = 'sender@example.com'
    os.environ['RECIPIENT_EMAIL'] = 'recipient@example.com'
    os.environ['SES_REGION'] = 'us-east-1'
    
    print(json.dumps(lambda_handler({}, None), indent=2))