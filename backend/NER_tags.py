import spacy
import en_core_web_sm
nlp = spacy.load("en_core_web_sm")
def generate_tags_from_description(description):
    doc = nlp(description)
    tags = set()

    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LANGUAGE']:
            tags.add(ent.text.lower())
            
            
    return ', '.join(tags)