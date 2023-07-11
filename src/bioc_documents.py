from pathlib import Path

from src.bioc_passages import BioCPassage


class BiocDocument:

    def build_passages(self, dataStore):
        seen_headings = []
        dataStore.main_text['title'] = dataStore.main_text['title'].strip()
        passages = [BioCPassage.from_title(dataStore.main_text['title'], 0).as_dict()]
        if dataStore.main_text['title'] not in seen_headings:
            offset = len(dataStore.main_text['title'])
            seen_headings.append(dataStore.main_text['title'])
        for passage in dataStore.main_text['paragraphs']:
            passage["body"] = passage["body"].strip()
            passage["section_heading"] = passage["section_heading"].strip()
            passage["subsection_heading"] = passage["subsection_heading"].strip()
            passage_obj = BioCPassage(passage, offset)
            passages.append(passage_obj.as_dict())
            offset += len(passage['body'])
            if passage['subsection_heading'] not in seen_headings:
                offset += len(passage['subsection_heading'])
                seen_headings.append(passage['subsection_heading'])
            if passage['section_heading'] not in seen_headings:
                offset += len(passage['section_heading'])
                seen_headings.append(passage['section_heading'])
        return passages

    def build_template(self, dataStore):
        return {
            "id": Path(dataStore.file_path).name.split(".")[0],
            "inputfile": dataStore.file_path,
            "infons": {},
            "passages": self.build_passages(dataStore),
            "annotations": [],
            "relations": []
        }

    def __init__(self, input):
        self.document = self.build_template(input)
        pass

    def as_dict(self):
        return self.document
