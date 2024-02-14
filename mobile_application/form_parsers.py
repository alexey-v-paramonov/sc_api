from rest_framework.parsers import MultiPartParser, JSONParser

class MultiPartJSONParser(MultiPartParser):
    def parse(self, stream, *args, **kwargs):

        data = super().parse(stream, *args, **kwargs)

        # Any 'File' found having application/json as type will be moved to data
        mutable_data = data.data.copy()
        unmarshaled_blob_names = []
        json_parser = JSONParser()
        for name, blob in data.files.items():
            if blob.content_type == 'application/json' and name not in data.data:
                parsed = json_parser.parse(blob)
                if isinstance(parsed, list):
                    # need to break it out into [0], [1] etc
                    for idx, item in enumerate(parsed):
                        mutable_data[name+f"[{str(idx)}]"] = item
                else:
                    mutable_data[name] = parsed
                unmarshaled_blob_names.append(name)
        for name in unmarshaled_blob_names:
            del data.files[name]
        data.data = mutable_data

        return data
