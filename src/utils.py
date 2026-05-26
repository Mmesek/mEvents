def build_query(**kwargs):
    return "&".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)


def get_next(responses: dict, key: str):
    if type(responses[key]) is list:
        return next(responses[key])
    return responses[key]
