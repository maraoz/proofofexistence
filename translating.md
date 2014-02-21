proof-of-existence
==================

Translating

Using the translation libraries described here:

http://mikeshilkov.wordpress.com/2012/07/26/enable-jinja2-and-i18n-translations-on-google-appengine/



* Adding a locale

We use PyBabel and GetText to translate most of the site text.

If your language is already in /locale,
find the .po file (for example, /locale/en_US/LC\_MESSAGES/messages.po

If you are adding a locale, run ```pybabel init -l YOUR_LOCALE -d ./locale -i ./locale/messages.pot```
and PyBabel will create a /locale/YOUR_LOCALE/LC\_MESSAGES directory with a messages.po file.

* Editing the .po file

When you don't know a phrase, leave it blank, and the English content will appear.

In messages.po, put translations inside quotes following **msgstr**. Do not edit **msgid**.

When you have made a translation, update the .mo file by running ```pybabel compile -f -d ./locale```

* Including a new phrase in translations

Put {% trans %} and {% endtrans %} tags around content in a template

* Client-side

In /static/js/translate.js there are about 20 phrases to include for your locale, including
a disclaimer explaining that the hash, not the document, is stored in the blockchain.