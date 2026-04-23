def test_admin_stats(client, admin_token):
    resp = client.get('/admin/stats',
                      headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'participant_count' in data
    assert 'event_count' in data
    assert 'registration_count' in data


def test_admin_lists_events(client, admin_token):
    resp = client.get('/admin/events',
                      headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_admin_marks_attendance_via_scan(client, admin_token):
    from models.application import Application
    from flask import current_app
    with current_app.app_context():
        app_entry = Application.query.first()
        if app_entry and app_entry.ticket_id:
            resp = client.post(f'/admin/scan/{app_entry.ticket_id}',
                               headers={'Authorization': f'Bearer {admin_token}'})
            assert resp.status_code == 200


def test_admin_bulk_status_update(client, admin_token):
    from models.application import Application
    from flask import current_app
    with current_app.app_context():
        apps = Application.query.limit(3).all()
        ids = [a.application_id for a in apps]
        if ids:
            resp = client.patch('/admin/registrations/bulk',
                                json={'ids': ids, 'status': 'Selected'},
                                headers={'Authorization': f'Bearer {admin_token}'})
            assert resp.status_code == 200
            assert 'updated' in resp.get_json()['message']


def test_admin_triggers_certificate_dispatch(client, admin_token):
    from models.placement import PlacementDrive
    from flask import current_app
    with current_app.app_context():
        event = PlacementDrive.query.first()
        if event:
            resp = client.post(f'/admin/dispatch-certificates/{event.drive_id}',
                               headers={'Authorization': f'Bearer {admin_token}'})
            assert resp.status_code == 200
            assert 'task_id' in resp.get_json()


def test_admin_updates_event(client, admin_token):
    from models.placement import PlacementDrive
    from flask import current_app
    with current_app.app_context():
        event = PlacementDrive.query.first()
        if event:
            resp = client.patch(f'/admin/event/{event.drive_id}',
                                json={'venue': 'Updated Venue'},
                                headers={'Authorization': f'Bearer {admin_token}'})
            assert resp.status_code == 200


def test_participant_cannot_access_admin(client, participant_token):
    resp = client.get('/admin/stats',
                      headers={'Authorization': f'Bearer {participant_token}'})
    assert resp.status_code == 403
