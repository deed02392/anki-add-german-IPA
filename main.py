#!/usr/bin/env python3
import requests
import re
import json


def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    requestJson = json.dumps(request(action, **params))
    response = requests.get('http://localhost:8765', data=requestJson).json()
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def parse_german_word(german_text):
    article = ''
    word = ''
    try:
        german, sound = str(german_text).split('[', 1)
    except ValueError:
        print("%s has no sound" % german_text)
        german = german_text

    parts = german.replace(',', '').split(' ')

    for part in parts:
        if part.lower() in ['der', 'die', 'das']:
            article = part
            continue
        # ignore words
        if part.lower() in ['(pl)']:
            continue
        word = part
        break

    return [article, word]


note_ids = invoke('findNotes', query='"deck:German Top 4027 Words with Example Sentence Audio from Natives"')
notes = invoke('notesInfo', notes=note_ids)
for note in notes:
    ipa = note['fields']['IPA']['value']
    german_text = note['fields']['GermanEntry']['value']
    if ipa:
        continue
    article, word = parse_german_word(german_text)
    payload = {'action': 'parse', 'page': word, 'format': 'json', 'prop': 'wikitext'}
    r = requests.get('https://de.wiktionary.org/w/api.php', params=payload)
    try:
        wikitext = r.json()['parse']['wikitext']['*']
        p = re.compile("{{IPA}} {{Lautschrift\|([^}]+)")
        m = p.search(wikitext)
        ipa = m.group(1)
        print("%d: %s (%s)" % (note['noteId'], word, ipa))
        invoke('updateNoteFields', note={'id': note['noteId'], 'fields': {'IPA': ipa}})
    except (KeyError, AttributeError):
        print("%s not found (%s)" % (german_text, word))
