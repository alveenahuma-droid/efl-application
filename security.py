import config 

def current_user_id():
    """Until login exists (Thrusday) every request belongs to the demo user"""
    return config.DEMO_USER_ID