proof-of-existence
==================


<h3>Translating into your language</h3>

We use PyBabel and GetText to translate most of the site text.

* If your language is already in /locale, find the .po file (for example, /locale/en_US/LC\_MESSAGES/messages.po

* If you are adding a new locale, run ```pybabel init -l YOUR_LOCALE -d ./locale -i ./locale/messages.pot``` and PyBabel will create a /locale/YOUR_LOCALE/LC\_MESSAGES directory with a messages.po file.

* Also make sure your locale is in ```known_locales``` in translation.py

<h3>Editing the .po file</h3>

When you don't know a phrase, leave it blank, and the English content will appear.

In messages.po, put translations inside quotes following **msgstr**. Do not edit **msgid**.

When you have made a translation, update the .mo file by running ```pybabel compile -f -d ./locale```

<h3>Including a new phrase in translations</h3>

Put {% trans %} and {% endtrans %} tags around content in a template.

If it is used in JavaScript, call translate("phrase") and add the phrase in translation.py

Then update the source .pot file with ```pybabel extract -F ./babel.cfg -o ./locale/messages.pot ./ ```

Then update each .po file with ```pybabel update -l en_US -d ./locale -i ./locale/messages.pot```

<h3>Technical details</h3>

Using the translation libraries described here:

http://mikeshilkov.wordpress.com/2012/07/26/enable-jinja2-and-i18n-translations-on-google-appengine/