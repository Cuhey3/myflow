from settings.antenna_settings import span_option


def create_util():

    span_key_text_dict = {dic['key']: dic['text'] for dic in span_option}

    def span_key_to_text(key):
        return span_key_text_dict.get(key, '')

    return {'span_key_to_text': span_key_to_text}
