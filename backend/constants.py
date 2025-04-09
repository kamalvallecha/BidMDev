ROLES_AND_PERMISSIONS = {
    'admin': {
        'can_view_all': True,
        'can_view_bids': True,
        'can_view_infield': True,
        'can_view_closure': True,
        'can_view_invoice': True,
        'can_view_users': True,
        'can_edit_all': True
    },
    'PM': {
        'can_view_all': False,
        'can_view_bids': False,
        'can_view_infield': True,
        'can_view_closure': True,
        'can_view_invoice': False,
        'can_view_users': False,
        'can_edit_infield': True,
        'can_edit_closure': True
    },
    'VM': {
        'can_view_all': False,
        'can_view_bids': True,
        'can_view_infield': False,
        'can_view_closure': False,
        'can_view_invoice': False,
        'can_view_users': False,
        'can_edit_bids': True
    }
} 