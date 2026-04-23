def test_admin_creates_event(client, admin_token):
    resp = client.post('/admin/event', json={
        'job_title': 'Test Workshop',
        'job_description': 'A workshop for testing.',
        'eligible_branch': 'All',
        'cgpa_required': 0.0,
        'event_type': 'workshop',
        'venue': 'Room 101',
        'max_team_size': 1,
        'organizer_name': 'Test Org'
    }, headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 201
    assert 'event_id' in resp.get_json()


def test_participant_registers_for_event(client, admin_token, participant_token):
    resp = client.post('/admin/event', json={
        'job_title': 'Open Registration Event',
        'job_description': 'Open to all.',
        'eligible_branch': 'All',
        'cgpa_required': 0.0,
        'eligible_year': 2025,
        'event_type': 'seminar',
        'venue': 'Hall A',
        'max_team_size': 1
    }, headers={'Authorization': f'Bearer {admin_token}'})
    event_id = resp.get_json()['event_id']

    resp = client.post(f'/events/{event_id}/register', json={},
                       headers={'Authorization': f'Bearer {participant_token}'})
    assert resp.status_code == 201
    assert 'ticket_id' in resp.get_json()


def test_duplicate_registration_blocked(client, admin_token, participant_token):
    from models.placement import PlacementDrive
    from flask import current_app
    with current_app.app_context():
        event = PlacementDrive.query.filter_by(job_title='Open Registration Event').first()
        if event:
            resp = client.post(f'/events/{event.drive_id}/register', json={},
                               headers={'Authorization': f'Bearer {participant_token}'})
            assert resp.status_code == 409


def test_qr_ticket_returns_base64(client, participant_token):
    from models.application import Application
    from flask import current_app
    with current_app.app_context():
        app_entry = Application.query.first()
        if app_entry and app_entry.ticket_id:
            resp = client.get(f'/ticket/{app_entry.ticket_id}/qr',
                              headers={'Authorization': f'Bearer {participant_token}'})
            assert resp.status_code == 200
            assert 'qr_base64' in resp.get_json()


def test_team_code_join_flow(client, admin_token, participant_token):
    resp = client.post('/admin/event', json={
        'job_title': 'Team Hackathon Test',
        'job_description': 'Team event for testing.',
        'eligible_branch': 'All',
        'cgpa_required': 0.0,
        'event_type': 'hackathon',
        'venue': 'Lab',
        'max_team_size': 4
    }, headers={'Authorization': f'Bearer {admin_token}'})
    event_id = resp.get_json()['event_id']

    resp = client.post(f'/events/{event_id}/register',
                       json={'team_code': 'TEAMTEST'},
                       headers={'Authorization': f'Bearer {participant_token}'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data.get('team_code') == 'TEAMTEST'
