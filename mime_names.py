TYPES = \
{
    'doc': 'application/vnd.google-apps.document',
    'folder': 'application/vnd.google-apps.folder',
    'spreadsheet': 'application/vnd.google-apps.spreadsheet', #excel
    'txt': 'text/plain'
}

CONVERTS = \
{
    'application/vnd.google-apps.document': [
        'application/vnd.oasis.opendocument.text',
        '.odt'
    ],
    'application/vnd.google-apps.drawing': ['image/jpeg', '.jpg'],
    'application/vnd.google-apps.spreadsheet': [
        'application/x-vnd.oasis.opendocument.spreadsheet',
        '.ods'
    ],
    'application/vnd.google-apps.presentation	': [
        'application/vnd.oasis.opendocument.presentation',
        '.odp'
    ]
}
