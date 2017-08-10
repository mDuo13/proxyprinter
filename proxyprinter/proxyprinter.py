#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
import argparse
import pyexcel_ods3 as pyexcel
import hashlib
import logging
from cgi import escape
from random import randint
from collections import OrderedDict
from time import strftime
from pkg_resources import resource_string

SPECIAL_FIELDS = [
    "Name", #Title of the card
    "Traits", #Comma-separated list of tags/classes
    "Text", #Shares a box with flavor text
    "Flavor Text", #Italicized, follows text
    "Version", #Appears in footer; can be used to print only updated cards
    "Copies", #Print the same card this many times
]

DEFAULT_STYLE = resource_string(__name__, "proxyprinter.css").decode('utf-8')

DEFAULT_TEXT_SIZING_THRESHOLDS = {
    "*": (30, 50),
    "Text": (140, 220),
    "Name": (18, 24),
}
DEFAULT_RICH_FIELDS = [
    "Text"
]

#Reserved names potentially used to define settings in the spreadsheet
SETTING_SHEET_LABEL = "ProxyPrinter Settings"
SETTING_LABEL_CSSFILE = "CSSFile"
SETTING_LABEL_COPYRIGHT = "Copyright"
SETTING_LABEL_TEXTSIZEFIELD = "TextSizeField"
SETTING_LABEL_TEXTSIZETHRESHOLD1 = "TextSizeMediumIfOver"
SETTING_LABEL_TEXTSIZETHRESHOLD2 = "TextSizeSmallIfOver"
SETTING_LABEL_RICHFIELDS = "RichFields"
SETTING_LABEL_PROCESSPATTERNS = "ProcessPatterns"
SETTING_LABEL_PROCESSREPLACEMENTS = "ProcessReplacements"


#Set up logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

def escape_html(s):
    #like cgi.escape, but undo escaping &nbsp;
    return escape(s).replace("&amp;nbsp;", "&nbsp;")

def replace_all(s, replacements):
    for key in replacements:
        s = s.replace(key, replacements[key])
    return s

def twod_array_to_ordered_dict_array(array2d):
    if len(array2d) < 2 or type(array2d[0]) != list:
        logger.warning("Not a 2d array?")
        return []

    keys = array2d[0]
    vals = array2d[1:]
    od_rows = []
    for row in vals:
        if not row: #skip empty rows
            continue
        od = OrderedDict()
        if len(keys) != len(row):
            logger.info("Mismatched number of fields in row: %s" % row)

        for i in range(0, len(keys)):
            if i >= len(row):
                continue
            od[keys[i]] = row[i]
        od_rows.append(od)
    return od_rows

def slug_text(s):
    return re.sub(r"\W","",re.sub(r"\s","_",s.lower()))



class Card:
    def __init__(self, cardtype="", fields=OrderedDict(), copyowner="",
                size_thresholds=DEFAULT_TEXT_SIZING_THRESHOLDS,
                text_subs = {}, rich_fields = ["Text"]):
        self.cardtype = cardtype
        self.copyowner = copyowner
        self.fields = fields
        self.text_subs = text_subs
        self.size_thresholds = size_thresholds
        self.rich_fields = rich_fields
        self.intify_fields()
        self.process_split_fields()

    def intify_fields(self):
        """Force integer floats to integer type"""
        #PyExcel provides all numbers as floats, but for board gaming
        # we usually want to deal with whole numbers, so this fixes that.
        for key,val in self.fields.items():
            if type(val) == float and val.is_integer():
                self.fields[key] = int(val)

    def process_split_fields(self):
        if "Traits" in self.fields.keys():
            self.traits = [t.strip() for t in self.fields["Traits"].split(",")]
        else:
            self.traits = []

    def process(self, text, context="*"):
        #save the text length before we html-ify it
        text = str(text)
        textlen = len(text)
        text = escape_html(text)

        if context in self.rich_fields:
            for pattern, replacement in self.text_subs.items():
                text = re.sub(pattern, replacement, text)

        text = text.replace("\\n","<br />\n")
        textsize = self.size_text(textlen, context)
        return text, textsize

    def size_text(self, textlen, context="*"):
        if context not in self.size_thresholds:
            context = "*"

        mediumcutoff, smallcutoff = self.size_thresholds[context]
        if textlen > smallcutoff:
            return "smalltext"
        elif textlen > mediumcutoff:
            return "mediumtext"
        else:
            return "bigtext"


    def art_spacer_html(self):
        return "<div class='artspacer'>&nbsp;</div>\n"

    def textbox_html(self):
        if "Text" in self.fields.keys():
            text = self.fields["Text"].strip()
        else:
            text = "-"
        if "Flavor Text" in self.fields.keys():
            flavor_text = self.fields["Flavor Text"].strip()
        else:
            flavor_text = "-"

        # Process, escape HTML, figure out combined text length for font sizing
        _, fontsize = self.process(text+flavor_text, context="Text")
        text, _ = self.process(text, "Text")
        flavor_text, _ = self.process(flavor_text, context="Flavor Text")

        if (text == "-" or not text) and (flavor_text == "-" or not flavor_text):
            s = "<div class='empty text_area'>\n"
        else:
            s = "<div class='text_area %s'>\n" % fontsize

        s += "<div class='text field %s'>\n" % fontsize
        if text == "-" or not text:
            s += "&nbsp;\n"
        else:
            s += text + "\n"
        s += "</div>\n"#/.text.field

        if flavor_text and flavor_text != "-":
            s += "<div class='flavor_text field %s'>\n" % fontsize
            s += flavor_text + "\n"
            s += "</div>\n"#/.flavor_text.field

        s += "</div>\n"#/.text_area
        return s

    def fields_html(self):
        s = "<div class='fields_area'>\n"
        textbox_printed = False
        for field, val in self.fields.items():
            if field in SPECIAL_FIELDS:
                #These fields are explicitly printed elsewhere, so skip them
                continue
            field_text, fontsize = self.process(val, context=field)
            s += "<div class='field %s %s'>\n" % (slug_text(field), fontsize)
            s += "<span class='fieldname'>%s:</span>\n" % field
            s += "%s\n" % field_text
            s += "</div>\n"#/.field
        s += "</div>"#/.fields_area
        return s

    def traits_html(self):
        s = ""
        if "Traits" in self.fields.keys():
            s += "<div class='traits_area field'>\n"
            for trait in self.traits:
                trait_text, fontsize = self.process(trait, context="Traits")
                s += "<span class='trait %s %s'>%s</span>\n" % (slug_text(trait), fontsize, trait_text)
            s += "</div>"#/.traits
        return s

    def title_area_html(self):
        s = ""
        if "Name" in self.fields.keys():
            name_text, fontsize = self.process(self.fields["Name"], "Name")
            s += "<div class='title_area'>\n"
            s += "<div class='name field %s'>%s</div>\n" % (fontsize, name_text)
            s += "</div>\n"#/.title_area
        return s

    def cardtype_area_html(self):
        if self.cardtype == "-":
            return ""
        s = "<div class='cardtype_area'>\n"
        s += "<div class='cardtype_label'>%s</div>\n" % self.cardtype
        s += "</div>"#/.cardtype_area
        return s

    def copyline_html(self):
        if "Version" in self.fields.keys():
            vstring = "(v%s) " % self.fields["Version"]
        else:
            vstring = ""
        s = "<div class='copyline'>%s©%s %s</div>\n" % (vstring, self.copyowner, strftime("%Y"))
        return s

    def html(self):
        s = "<div class='%s card'>\n" % (slug_text(self.cardtype))

        s += self.title_area_html()
        s += self.cardtype_area_html()

        s += "<div class='card_body_area'>\n"
        s += self.fields_html()
        s += self.textbox_html()
        s += self.traits_html()
        s += "</div>"#/.card_body_area

        s += self.copyline_html()
        s += "</div>\n"
        return s

class ProxyPrinter:
    def __init__(self, spreadsheet, copyowner=None, version=None, addcss=None,
                defaultcss=True, text_subs={}, colorize=True, rich_fields=[]):
        self.read_sheet(spreadsheet)
        self.copyowner = copyowner
        self.version = version
        self.addcss = addcss
        self.defaultcss = defaultcss
        self.text_subs = text_subs
        self.colorize = colorize
        self.rich_fields = rich_fields

        self.parse_settings()
        self.parse_sheet_cards()

    def read_sheet(self, ods_file):
        self.sheet = pyexcel.get_data(ods_file)

    def parse_settings(self):
        self.skip_sheets = [SETTING_SHEET_LABEL]
        self.size_thresholds = DEFAULT_TEXT_SIZING_THRESHOLDS
        if type(self.sheet) != OrderedDict:
            logger.info("Single page sheet (%s); no settings pulled"%type(self.sheet))
            # Single page sheet; no custom settings defined
            return
        elif SETTING_SHEET_LABEL not in self.sheet.keys():
            logger.info("No settings sheet found")
            # No settings sheet; no custom settings defined
            return

        settings_sheet = self.sheet[SETTING_SHEET_LABEL]
        if len(settings_sheet) < 2:
            logger.info("Less than 2 rows in settings sheet")
            return

        setting_keys = settings_sheet[0]
        setting_simple_values = settings_sheet[1]

        # Setting: Custom CSS filename
        if not self.addcss:
            try:
                self.addcss = setting_simple_values[
                            setting_keys.index(SETTING_LABEL_CSSFILE)]
            except ValueError:
                logger.info("Failed to get addcss value from settings")
        else:
            print("ADDCSS",self.addcss, type(self.addcss))

        # Setting: Copyright
        if not self.copyowner:
            try:
                self.copyowner = setting_simple_values[
                            setting_keys.index(SETTING_LABEL_COPYRIGHT)]
            except ValueError:
                logger.info("Failed to get copyright value from settings")

        # Setting: Text Size Thresholds
        try:
            pos_textsizefield = setting_keys.index(SETTING_LABEL_TEXTSIZEFIELD)
            pos_textsizemed = setting_keys.index(SETTING_LABEL_TEXTSIZETHRESHOLD1)
            pos_textsizesmall = setting_keys.index(SETTING_LABEL_TEXTSIZETHRESHOLD2)
            got_textsize_settings = True
        except ValueError:
            logger.info("Failed to get text size thresholds from settings")
            got_textsize_settings = False

        if got_textsize_settings:
            for row in settings_sheet[1:]:
                if len(row) > pos_textsizefield and row[pos_textsizefield]:
                    textfieldname = row[pos_textsizefield]
                    # Get existing or default thresholds for this field name
                    if textfieldname in self.size_thresholds.keys():
                        threshold_med, threshold_sm = self.size_thresholds[textfieldname]
                    else:
                        threshold_med, threshold_sm = self.size_thresholds["*"]
                else:
                    logger.debug("Text Thresholds: Skipping row %s"%row)
                    continue

                if len(row) > pos_textsizemed and row[pos_textsizemed]:
                    threshold_med = row[pos_textsizemed]

                if len(row) > pos_textsizesmall and row[pos_textsizesmall]:
                    threshold_sm = row[pos_textsizesmall]

                self.size_thresholds[textfieldname] = (threshold_med, threshold_sm)

        # Setting: Rich Fields (These fields have post-processing applied)
        try:
            pos_richfields = setting_keys.index(SETTING_LABEL_RICHFIELDS)
            got_richfield_settings = True
        except ValueError:
            logger.info("Failed to get rich text settings")
            got_richfield_settings = False

        if got_richfield_settings:
            rich_fields = []
            for row in settings_sheet[1:]:
                if len(row) > pos_richfields and row[pos_richfields]:
                    rich_fields.append(row[pos_richfields])
            self.rich_fields = rich_fields
        else:
            self.rich_fields = DEFAULT_RICH_FIELDS

        # Setting: Text Processing Patterns (regex subs applied to rich fields)
        try:
            pos_processpatterns = setting_keys.index(SETTING_LABEL_PROCESSPATTERNS)
            pos_processreplacements = setting_keys.index(SETTING_LABEL_PROCESSREPLACEMENTS)
            got_textprocessing_settings = True
        except ValueError:
            logger.info("Failed to get text processing settings")
            got_textprocessing_settings = False

        if got_textprocessing_settings:
            text_subs = OrderedDict()
            for row in settings_sheet[1:]:
                if (len(row) > pos_processpatterns
                        and row[pos_processpatterns]
                        and len(row) > pos_processreplacements
                        and row[pos_processreplacements]):
                    pattern = re.compile(row[pos_processpatterns])
                    repl = row[pos_processreplacements]
                    text_subs[pattern] = repl
            self.text_subs = text_subs

    def parse_sheet_cards(self):
        self.cards = []
        # A single-sheet file comes back as a 2d array;
        # a multi-sheet file comes back as an OrderedDict of sheet names to 2d arrays
        if type(self.sheet) == OrderedDict:
            pages = self.sheet.items()
        else:
            pages = {"-": self.sheet}.items()
        for sheetname, sheetdata in pages:
            if sheetname == SETTING_SHEET_LABEL:
                #This sheet is settings, not cards; skip
                continue
            cardtype = sheetname
            cardrows = twod_array_to_ordered_dict_array(sheetdata)
            for row in cardrows:
                if self.version:
                    #Ignore cards not from this version
                    if "Version" not in row or str(row["Version"]) != self.version:
                        continue
                c = Card(cardtype=sheetname, fields=row,
                         copyowner=self.copyowner,
                         size_thresholds=self.size_thresholds,
                         text_subs=self.text_subs,
                         rich_fields=self.rich_fields)
                self.cards.append(c)

    def trait_colors_css(self):
        trait_keys = set()
        for c in self.cards:
            trait_keys.update(c.traits)

        def int_from_string_hash(s, min_i, max_i, encoding="utf-8"):
            m = hashlib.md5(bytes(s, encoding))
            return (int(m.hexdigest(), 16) % (max_i-min_i)) + min_i
        s = ""
        for t in trait_keys:
            hue = int_from_string_hash(t,0,360)#randint(0,360)
            sat = int_from_string_hash(t,40,100)#randint(40,100)
            lit = 85
            s += ".trait.%s {background-color: hsl(%d, %d%%, %d%%);}\n" % (slug_text(t), hue, sat, lit)

        return s

    def render_all(self):
        s = "<!DOCTYPE html>\n<html>\n<head>\n"
        if self.defaultcss:
            s += "<style type='text/css'>%s</style>" % DEFAULT_STYLE
        #randomly colorize traits
        if self.colorize:
            s += "<style type='text/css'>%s</style>" % self.trait_colors_css()
        if self.addcss:
            s += "<link rel='stylesheet' href='%s' />" % self.addcss
        s += "</head><body>"

        for c in self.cards:
            s_copies = c.fields.get("Copies", 1)
            try:
                copies = int(s_copies)
            except ValueError:
                copies = 1
            if copies < 0:
                copies = 1
            s += c.html()*copies

        s += "</body></html>"
        return s


def main():
    parser = argparse.ArgumentParser(
        description="Generate card images in HTML from spreadsheet.")
    parser.add_argument("spreadsheet", type=str,
                        help=".ods spreadsheet to source card data")
    parser.add_argument("--copyright","-c", type=str, default="",
                        help="Copyright owner to show in footer")
    parser.add_argument("--css", type=str,
                        help="Name of additional css file")
    parser.add_argument("--no_default_css", action="store_true",
                        help="Don't include the default CSS")
    parser.add_argument("--no_trait_colors", action="store_true",
                        help="Don't procedurally color-code Traits")
    parser.add_argument("--version", "-v", type=str,
                        help="Print only cards whose Version matches this")

    cli_args = parser.parse_args()

    defaultcss = not cli_args.no_default_css
    colorize = not cli_args.no_trait_colors
    pp = ProxyPrinter(cli_args.spreadsheet, copyowner=cli_args.copyright,
            version=cli_args.version, defaultcss=defaultcss, addcss=cli_args.css,
            colorize=colorize)
    print( pp.render_all() )

if __name__ == "__main__":
    main()
