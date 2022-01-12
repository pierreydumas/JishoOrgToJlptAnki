import requests
import bs4
import time
import random


def wait():
    time.sleep(random.randint(4, 7))


def safeRequest(pageUrlString):
    while True:
        try:
            return requests.get(pageUrlString)
        except:
            wait()


def rubyToKana(ruby):
    kana = ''
    for part1 in ruby.split(' '):
        for part2 in part1.split("]"):
            part3 = part2.split("[")
            if len(part3) > 1:
                kana = kana + part3[1]
            else:
                kana = kana + part3[0]
    return kana


def jishoWord2Ruby(jishoWord):
    debug = False
    if debug:
        print("*****")
    furigana = jishoWord.find("span", {"class": "furigana"})
    rubySpan = furigana.find("ruby", {"class": "furigana-justify"})
    ruby = ""
    if rubySpan:
        for tag in rubySpan.contents:
            if tag.name == "rb":
                ruby = ruby + " " + tag.text
            elif tag.name == "rt":
                ruby = ruby + "[" + tag.text + "]"
    else:

        kanas = []
        i = -1
        for furiganaSpan in furigana.find_all("span"):
            kana = furiganaSpan.text.strip()
            kanas = kanas + [kana]
            i = i + 1
            if debug:
                print("kana[" + str(i) + "]: " + kana)

        parts = []
        i = -1
        for wordPart in jishoWord.find("span", {"class": "text"}).contents:
            part = ''
            hasKanjis = True
            if isinstance(wordPart, bs4.element.Tag):
                hasKanjis = False
                part = wordPart.text
            else:
                part = wordPart.string
            part = part.strip()
            while part.find("\n") != - 1:
                part.replace("\n", "")
            if part:
                parts = parts + [
                    [part, hasKanjis]]  # A list of a single element, itself a list of two elements
                i = i + 1
                if debug:
                    print("part[" + str(i) + "]: " + part + " hasKanjis: " + str(hasKanjis))

        i = -1
        storedKana = ''
        for part in parts:
            if not part[1]:
                i = i + 1
                ruby = ruby + part[0]
            else:
                i = i + 1
                kanjis = part[0]
                j = - 1
                for kanji in kanjis:
                    j = j + 1
                    if i > 0 and j == 0:
                        ruby = ruby + ' '
                    ruby = ruby + kanji
                    kana = ''
                    if i + j < len(kanas) and kanas[i + j]:
                        storedKana = kanas[i + j]
                    nextKanaNeeded = j + 1 < len(kanjis)
                    nextKana = ''
                    if i + j + 1 < len(kanas) and kanas[i + j + 1]:
                        nextKana = kanas[i + j + 1]

                    if storedKana and ((not nextKanaNeeded) or nextKana):
                        ruby = ruby + "[" + storedKana + "]"
    if debug:
        print("*****")
    return ruby


def jishoSentence2Ruby(jishoSentence):
    kanjiRangeFirst = int("0x4E00", 0)
    kanjiRangeLast = int("0x9FFF", 0)
    ul = jishoSentence.find("ul", {"class": "japanese"})
    sentence = ""
    for child in ul.contents:
        if isinstance(child, bs4.element.Tag):
            if child['class'][0] == "english":
                sentence = sentence + "<br/>" + child.text.strip()
            else:
                text = child.find("span", {"class": "unlinked"}).text.strip()
                lastKanjiAt = len(text) - 1
                for c in text[::-1]:
                    if ord(c) >= kanjiRangeFirst and ord(c) <= kanjiRangeLast or c == '々':
                        break
                    else:
                        lastKanjiAt = lastKanjiAt - 1
                furiganaDiv = child.find("span", {"class": "furigana"})
                sentence = sentence + " "
                if lastKanjiAt == -1:
                    sentence = sentence + text
                else:
                    sentence = sentence + text[:lastKanjiAt + 1]
                if furiganaDiv:
                    sentence = sentence + "[" + furiganaDiv.text.strip() + "]"
                if not lastKanjiAt == -1:
                    sentence = sentence + text[lastKanjiAt + 1:]
        else:
            sentence = sentence + child.string.strip()
    return sentence