"""Storage helper (disabled).

This project currently does not accept or store file uploads. The original
storage helper has been replaced with a stub that returns an explanatory
message. Keep this file so existing imports won't break; it will return
`(False, message)` for any upload attempt.
"""

def upload_file(*args, **kwargs):
    return False, "uploads are disabled in this deployment"

