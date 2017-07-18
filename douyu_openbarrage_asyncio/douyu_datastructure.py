

def escape(value):
    value = str(value)
    value = value.replace("@", "@A")
    value = value.replace("/", "@S")
    return value


def unescape(value):
    value = str(value)
    value = value.replace("@S", "/")
    value = value.replace("@A", "@")
    return value


def serialize(data):

    if data is None:
        return ''

    kv_pairs = []
    for key, value in data.items():
        kv_pairs.append(escape(key) + "@=" + escape(value))
    kv_pairs.append('')

    result = "/".join(kv_pairs)
    return result


def deserialize(raw):

    result = {}

    if raw is None or len(raw) <= 0:
        return result
    kv_pairs = raw.split("/")
    for kv_pair in kv_pairs:

        if len(kv_pair) <= 0:
            continue

        kv = kv_pair.split("@=")
        if len(kv) != 2:
            continue

        k = unescape(kv[0])
        v = unescape(kv[1])
        if not k:
            continue
        if not v:
            v = ''

        # Nested deserialize
        try:
            if v.index('@A=') >= 0:
                v = deserialize(unescape(v))
        except ValueError as e:
            pass

        result[k] = v

    return result