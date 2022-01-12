import genanki
import helpers
from bs4 import BeautifulSoup
import urllib

if __name__ == "__main__":
    for jlptLv in [5, 4, 3, 2, 1]:  # Use [5] to allow only N5

        my_model = genanki.Model(
            1380124060 + jlptLv,
            'JishoOrg2022ToJLPT' + str(jlptLv),
            fields=[
                {'name': 'word'},
                {'name': 'kana with precedence over kanjis'},
                # The field above is used only if there's a kanji form for word,
                # so it's used for 燐寸/マッチ (fire) but not for マッチ (contest).
                {'name': 'top 3 meanings in jisho.org without examples'},
                {'name': 'top 5 meanings in jisho.org with examples'},
                {'name': 'word with furigana'},
                {'name': 'other forms'},
                {'name': 'kanjis'},
                {'name': 'source'}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '<span class="kana">{{kana with precedence over kanjis}}</span><span class="word">{{kanji:word with furigana}}</span>',
                    'afmt': '<span class="word">{{furigana:word with furigana}}</span><br/>{{other forms}}' +
                            '<hr/>{{furigana:top 5 meanings in jisho.org with examples}}{{kanjis}}' +
                            '<hr/><span  class="tiny">source: <a href="{{source}}">{{kanji:word with furigana}}</a></span>'
                    ,
                },
            ],
            css="""
        .card {
          font-family: Arial;
          font-size:  16px;
          text-align: center;
          color: black;
          background-color: white;
        }
        .question {
          font-size: 20px;
        }
        .word {
          font-family: MS Mincho, Arial;
          font-size: 36px;
        }
        .kana {
          font-family: MS Mincho, Arial;
          font-size: 24px;
          color: red;
        }
        .japanese {
          font-family: MS Mincho, Arial;
        }
        .tiny {
          font-family: MS Mincho, Arial;
          font-size:12px;
        }
        """)

        my_deck = genanki.Deck(
            2059441190 + jlptLv,
            "JLPT-N" + str(jlptLv) + " words in jisho.org (2022)")

        pageId = 0
        words = []
        pageIsValid = True
        while pageIsValid:
            pageId = pageId + 1
            if pageId % 40 == 0:
                input('Congratulation on making it all the way to page ' + str(pageId) + '.\n' +
                      "It may be time to switch your IP with a VPN, or just cool down for a while.\n" +
                      "Press enter to resume.")
            pageUrlString = "https://jisho.org/search/%20%23jlpt-n" + str(jlptLv) + "%20%23words?page=" + str(pageId)
            helpers.wait()
            searchPage = BeautifulSoup(helpers.safeRequest(pageUrlString).text, 'html.parser')
            noMatches = searchPage.find("div", {"id": "no-matches"})
            if noMatches is not None:
                pageIsValid = False
            else:
                print(pageUrlString)

                linksToWordPage = searchPage.find_all("a", {"class": "light-details_link"})
                for linkToWordPage in linksToWordPage:
                    wordPageUrlString = urllib.parse.urljoin(pageUrlString, linkToWordPage.get('href'))
                    wordPage = BeautifulSoup(helpers.safeRequest(wordPageUrlString).text, 'html.parser')
                    word = wordPage.find("div", {"class": "concept_light-representation"}) \
                        .find("span", {"class": "text"}).text.strip()
                    tags = [tagSpan.text.strip() for tagSpan in
                            wordPage.find_all("span", {"class": "concept_light-tag label"})]
                    if not ("JLPT N" + str(jlptLv) in tags):
                        # For a given level, jisho.org lists all the words at this level and below
                        print("skip " + word + " which is " + str(tags) + " but not JLPT N" + str(jlptLv))
                    elif word in words:
                        # Surprisingly words can appear several times, for instance 作文 is listed twice at N5
                        print("skip " + word + " which was already listed")
                    else:
                        words.append(word)
                        print(word + " " + wordPageUrlString)
                        helpers.wait()

                        meanings = ""
                        question = ""
                        otherForms = ""
                        hasOtherForms = False
                        cancelNext = False
                        kanaOnly = False
                        kanaIfOnlyKana = ""
                        meaningWrapper = wordPage.find("div", {"class": "meanings-wrapper"})
                        for meaningLine in meaningWrapper.find_all("div", recursive=False):
                            tags = None
                            # build the meanings
                            if meaningLine.attrs.get('class')[0] == "meaning-tags":
                                if meaningLine.text == "Notes" or meaningLine.text == "Place" or meaningLine.text == "Wikipedia definition":
                                    cancelNext = True
                                elif meaningLine.text == "Other forms":
                                    hasOtherForms = True
                                else:
                                    tags = meaningLine.text.strip()
                            if meaningLine.attrs.get('class')[0] == "meaning-wrapper":
                                if cancelNext:
                                    cancelNext = False
                                elif hasOtherForms:
                                    hasOtherForms = False
                                    otherFormDivs = meaningLine.find_all("span", {"class": "break-unit"})
                                    for otherFormDiv in otherFormDivs:
                                        if not otherForms:
                                            otherForms = "<br/>Other form"
                                            if len(otherFormDivs) > 1:
                                                otherForms = otherForms + "s"
                                            otherForms = otherForms + ": "
                                        else:
                                            otherForms = otherForms + ", "
                                        otherForms = otherForms + otherFormDiv.text.strip()
                                else:
                                    if meanings:
                                        meanings = meanings + "<br/><br/>"
                                        question = question + "<br/>"

                                    # In "1. to raise; to elevate See also 手を挙げる" num is "1."
                                    num = meaningLine.find("span", {
                                        "class": "meaning-definition-section_divider"}).text.strip()
                                    meanings = meanings + num
                                    question = question + num

                                    # In "1. to raise; to elevate See also 手を挙げる" english is "to raise; to elevate"
                                    english = meaningLine.find("span", {"class": "meaning-meaning"}).text.strip()
                                    meanings = meanings + " " + english
                                    question = question + " " + english

                                    if tags:
                                        meanings = meanings + " (" + tags + ")"
                                        question = question + " (" + tags + ")"

                                    supplementalInfoDiv = meaningLine.find("span", {"class": "supplemental_info"})
                                    if supplementalInfoDiv:
                                        supplementalInfo = supplementalInfoDiv.text.strip()
                                        meanings = meanings + " " + supplementalInfo
                                        question = question + " " + supplementalInfo
                                        if supplementalInfoDiv.text.find("Usually written using kana alone") != -1:
                                            kanaOnly = True

                                    for sentenceDiv in meaningLine.find_all("div", {"class": "sentence"}):
                                        sentence = helpers.jishoSentence2Ruby(sentenceDiv)
                                        meanings = meanings + "<br/>" + sentence

                        meanings = meanings.split("6. ")[0].strip()
                        question = question.split("4. ")[0].strip()

                        wordWithFurigana = helpers.jishoWord2Ruby(
                            wordPage.find("div", {"class": "concept_light-representation"}))
                        if kanaOnly and wordWithFurigana != word:
                            kana = helpers.rubyToKana(wordWithFurigana)
                            if kana != word:
                                # Ｙシャツ is tagged as usually written using kana alone, マッチ is not,
                                # so ignore the behavior for kana alone if it's redundant.
                                kanaIfOnlyKana = helpers.rubyToKana(wordWithFurigana) + "<br/>"
                                print("    kana only: " + kanaIfOnlyKana[:-5])

                        details = ""
                        if True:  # Toggle whether to look up for kanjis or not
                            kanjisLightContent = wordPage.find_all("div", {"class": "entry kanji_light clearfix"})
                            for kanjiLightContent in kanjisLightContent:
                                kanjiChar = kanjiLightContent.find("div", {"class": "literal_block"}).text.strip()
                                kanjiDef = kanjiLightContent.find("div", {"class": "meanings"}).text

                                kunReadings = ""
                                for kunReadingDiv in kanjiLightContent.find_all("div", {"class": "kun"}):
                                    for kunReadingA in kunReadingDiv.find_all("a"):
                                        if kunReadings:
                                            kunReadings = kunReadings + ", "
                                        kunReadings = kunReadings + kunReadingA.text

                                onReadings = ""
                                for onReadingDiv in kanjiLightContent.find_all("div", {"class": "on"}):
                                    for onReadingA in onReadingDiv.find_all("a"):
                                        if onReadings:
                                            onReadings = onReadings + ", "
                                        onReadings = onReadings + onReadingA.text

                                radical = None
                                composition = []
                                if True:  # Toggle whether to include the composition or not
                                    kanjiUrl = "https:" + kanjiLightContent.find("a", {"class": "light-details_link"})[
                                        'href']
                                    kanjiPage = BeautifulSoup(helpers.safeRequest(kanjiUrl).text, 'html.parser')
                                    print("    " + kanjiChar + " " + kanjiUrl)
                                    entries = kanjiPage.find_all("dl", {"class": "dictionary_entry on_yomi"})

                                    radicalSpan = entries[0].find("span")
                                    radicalChar = ''.join(radicalSpan.find_all(text=True, recursive=False)).strip()
                                    radicalDef = radicalSpan.find("span", {"class": "radical_meaning"}).text.strip()
                                    radical = (radicalChar, radicalDef)
                                    print("        radical: " + radicalChar + " (" + radicalDef + ")")

                                    for part in entries[1].find_all("a"):
                                        partChar = part.text.strip()
                                        partUrl = "https:" + part['href']
                                        if partUrl == kanjiUrl:
                                            print("        skip " + kanjiChar + " as a part of itself")
                                        else:
                                            partPage = BeautifulSoup(helpers.safeRequest(partUrl).text, 'html.parser')
                                            if partPage.find("h1", {"class": "character"}):
                                                # For 事 a listed part is ヨ which doesn't have it's own page
                                                partDef = partPage.find("div", {
                                                    "class": "kanji-details__main-meanings"}).text.strip()
                                                print("        " + partChar + " " + partUrl)
                                                composition.append((partChar, partDef))
                                            else:
                                                print("        " + partChar)
                                                composition.append((partChar, None))

                                details = details + "<hr/>" + kanjiChar + "<br/>" + kanjiDef

                                if kunReadings:
                                    details = details + "<br/>kun reading"
                                    if len(kunReadings.split(", ")) > 1:
                                        details = details + "s"
                                    details = details + ": " + kunReadings
                                if onReadings:
                                    details = details + "<br/>on reading"
                                    if len(onReadings.split(", ")) > 1:
                                        details = details + "s"
                                    details = details + ": " + onReadings

                                if True:  # Toggle whether to include the radical or not
                                    # Needs to have looked into the composition else radical will be None anyway.
                                    # For 供, 人(亻) is known to be the radical but it is not listed as a part, but 化 is.
                                    # For 冬, 冫 (ice) is known to be the radical but it is not listed as a part.
                                    # For 花, 艸 (艹) is known to be the radical but it is not listed as a part.
                                    # Usually the radical is also a listed part, so it's rarely worth being mentioned,
                                    # yet for good measure I decided to leave it.
                                    radicalChar, radicalDef = radical
                                    if radicalChar != kanjiChar:
                                        details = details + "<br/>radical: " + radicalChar + " (" + radicalDef + ")"
                                        # Will print "radical: 人 (亻) (man, human)" which doesn't look too good
                                    else:
                                        details = details + "<br/>" + kanjiChar + " is its own radical"
                                    i = 0
                                    while i < len(composition):
                                        if composition[i][0] == radicalChar or composition[i][0] == kanjiChar:
                                            del composition[i]
                                        else:
                                            i += 1

                                if composition:
                                    details = details + "<br/>composition: " + composition[0][0]
                                    if composition[0][1]:
                                        details = details + " (" + composition[0][1] + ")"
                                    for partChar, partDef in composition[1:]:
                                        details = details + ", " + partChar
                                        if partDef:
                                            details = details + " (" + partDef + ")"

                        fields = [field if field else ' ' for field in [
                            word,  # 'word'
                            kanaIfOnlyKana,  # 'kana with precedence over kanjis'
                            question,  # 'top 3 meanings in jisho.org without examples'
                            meanings,  # 'top 5 meanings in jisho.org with examples'
                            wordWithFurigana,  # 'word with furigana'
                            otherForms,  # 'other forms'
                            details,  # 'kanjis'
                            wordPageUrlString  # 'source'
                        ]]
                        note = genanki.Note(
                            model=my_model, fields=fields
                        )
                        my_deck.add_note(note)

                        if False:  # Toggle whether to stop or not after the first word of a page
                            break  # Break here to allow only one word per page
                if False:  # Toggle whether to stop or not after the first visited page
                    break

        my_package = genanki.Package(my_deck)
        APKG_PATH = 'C:\\_\\tmp\\anki\\JishoOrg2022ToJLPT' + str(jlptLv) + '.apkg'
        my_package.write_to_file(APKG_PATH)
        print(APKG_PATH)
