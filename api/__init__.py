from .auth_apis import LoginUser, SignUpUser, LogoutUser

from .participant_api import (
    ParticipantProfileAPI, ParticipantStatsAPI,
    MyRegistrationsAPI, ParticipantExportAPI
)

from .admin_api import (
    AdminStatsAPI, AdminCreateEventAPI, AdminEventsAPI, AdminEventAPI,
    AdminParticipantsAPI, AdminToggleUserStatusAPI, AdminExportAPI,
    AdminMonthlyReportAPI, AdminRegistrationsAPI, AdminBulkStatusAPI,
    AdminUpdateRegistrationAPI, AdminScanAttendanceAPI,
    AdminDispatchCertificatesAPI, AdminMassEmailAPI
)

from .event_api import (
    EventListAPI, EventDetailAPI, EventRegisterAPI,
    CancelRegistrationAPI, TeamViewAPI, TicketQRAPI
)


def init_api(api):
    # ── Auth ──
    api.add_resource(LoginUser, '/login')
    api.add_resource(SignUpUser, '/signup')
    api.add_resource(LogoutUser, '/logout')

    # ── Events (participant-facing) ──
    api.add_resource(EventListAPI, '/events')
    api.add_resource(EventDetailAPI, '/events/<int:event_id>')
    api.add_resource(EventRegisterAPI, '/events/<int:event_id>/register')
    api.add_resource(CancelRegistrationAPI, '/my/registrations/<int:reg_id>')
    api.add_resource(MyRegistrationsAPI, '/my/registrations')
    api.add_resource(TeamViewAPI, '/my/team/<string:team_code>')
    api.add_resource(TicketQRAPI, '/ticket/<string:ticket_id>/qr')

    # ── Participant Profile ──
    api.add_resource(ParticipantProfileAPI, '/participant/profile')
    api.add_resource(ParticipantStatsAPI, '/participant/stats')
    api.add_resource(ParticipantExportAPI, '/participant/export')

    # ── Admin ──
    api.add_resource(AdminStatsAPI, '/admin/stats')
    api.add_resource(AdminCreateEventAPI, '/admin/event')
    api.add_resource(AdminEventsAPI, '/admin/events')
    api.add_resource(AdminEventAPI, '/admin/event/<int:event_id>')
    api.add_resource(AdminParticipantsAPI, '/admin/participants')
    api.add_resource(AdminToggleUserStatusAPI, '/admin/users/<int:user_id>/toggle')
    api.add_resource(AdminRegistrationsAPI, '/admin/registrations')
    api.add_resource(AdminBulkStatusAPI, '/admin/registrations/bulk')
    api.add_resource(AdminUpdateRegistrationAPI, '/admin/registration/<int:registration_id>')
    api.add_resource(AdminScanAttendanceAPI, '/admin/scan/<string:ticket_id>')
    api.add_resource(AdminDispatchCertificatesAPI, '/admin/dispatch-certificates/<int:event_id>')
    api.add_resource(AdminMassEmailAPI, '/admin/mass-email')
    api.add_resource(AdminExportAPI, '/admin/export/<string:target>')
    api.add_resource(AdminMonthlyReportAPI, '/admin/monthly-report')

    return api
