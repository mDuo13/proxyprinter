#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
import argparse
import pyexcel_ods3 as pyexcel
from cgi import escape
from random import randint
from logging import warning
from collections import OrderedDict
from time import strftime

SPECIAL_FIELDS = [
    "Name", #Title of the card
    "Traits", #Comma-separated list of tags/classes
    "Text", #Shares a box with flavor text
    "Flavor Text", #Italicized, follows text
    "Version", #Appears in footer; can be used to print only updated cards
]

TEXT_SIZING_THRESHOLDS = {
    "*": (30, 50),
    "Text": (140, 220),
    "Name": (18, 24),
}

def escape_html(s):
    #like cgi.escape, but undo escaping &nbsp;
    return escape(s).replace("&amp;nbsp;", "&nbsp;")

def replace_all(s, replacements):
    for key in replacements:
        s = s.replace(key, replacements[key])
    return s

def twod_array_to_ordered_dict_array(array2d):
    if len(array2d) < 2 or type(array2d[0]) != list:
        warning("Not a 2d array?")
        return []

    keys = array2d[0]
    vals = array2d[1:]
    od_rows = []
    for row in vals:
        od = OrderedDict()
        if len(keys) != len(row):
            warning("Mismatched number of fields in row: %s" % row)

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
                size_thresholds=TEXT_SIZING_THRESHOLDS):
        self.cardtype = cardtype
        self.copyowner = copyowner
        self.fields = fields
        self.intify_fields()
        self.size_thresholds = size_thresholds

    def intify_fields(self):
        """Force integer floats to integer type"""
        #PyExcel provides all numbers as floats, but for board gaming
        # we usually want to deal with whole numbers, so this fixes that.
        for key,val in self.fields.items():
            if type(val) == float and val.is_integer():
                self.fields[key] = int(val)

    def process(self, text, context="*"):
        #save the text length before we html-ify it
        text = str(text)
        textlen = len(text)
        text = escape_html(text)

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

    # def title_html(self):
    #     s = "<div class='titlebox'>\n"
    #     #adapt font size to name length
    #     fontsize = "bigtext"
    #     if len(self.name) > 13:
    #         fontsize = "mediumtext"
    #     if len(self.name) > 22:
    #         fontsize = "smalltext"
    #     s += ("<div class='name %s'>" % fontsize)
    #     if self.name.lower() == "(unnamed)":
    #         s += "&nbsp;"
    #     else:
    #         s += self.name
    #     s += "</div>\n"#name
    #     if self.traits:
    #         s += "<div class='subtitle'>"
    #         for t in self.traits:
    #             if t:
    #                 s += "<span class='"+t.lower()+" trait'>"+t+"</span>\n"
    #         s += "<span class='cardtype'>%s</span>\n"%self.get_type().title()
    #         s += "</div>\n"#subtitle
    #     s += "</div>\n"#titlebox
    #     return s

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
        _, fontsize = self.process(text+flavor_text, "Text")
        text, _ = self.process(text, "Text")
        flavor_text, _ = self.process(flavor_text, "Flavor Text")

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
            traits = [t.strip() for t in self.fields["Traits"].split(",")]
            for trait in traits:
                trait_text, fontsize = self.process(trait, "Traits")
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

def all_cards(spreadsheet, copyowner, version=None, addcss=None, defaultcss=True):
    allcards = []
    spreadsheet_data = pyexcel.get_data(spreadsheet)
    for sheetname, sheetdata in spreadsheet_data.items():
        cardtype = sheetname
        cardrows = twod_array_to_ordered_dict_array(sheetdata)
        for row in cardrows:
            if cli_args.version:
                if "Version" not in row or str(row["Version"]) != version:
                    continue
            c = Card(cardtype=sheetname, fields=row, copyowner=copyowner)
            allcards.append(c)

    s = "<!DOCTYPE html>\n<html>\n<head>\n"
    if defaultcss:
        with open("proxyprinter.css","r") as f:
            s += "<style type='text/css'>%s</style>" % f.read()
    if addcss:
        s += "<link rel='stylesheet' href='%s' />" % cli_args.css
    s += "</head><body>"

    for c in allcards:
        s += c.html()

    s += "</body></html>"
    return s

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate card images in HTML from spreadsheet.")
    parser.add_argument("spreadsheet", type=str,
                        help=".ods spreadsheet to source card data")
    parser.add_argument("--copyright","-c", type=str, default="Rome Reginelli",
                        help="Copyright owner to show in footer")
    parser.add_argument("--css", type=str,
                        help="Name of additional css file")
    parser.add_argument("--no_default_css", action="store_true",
                        help="Don't include the default CSS")
    parser.add_argument("--version", "-v", type=str,
                        help="Print only cards whose Version matches this")

    cli_args = parser.parse_args()

    defaultcss = not cli_args.no_default_css
    print( all_cards(cli_args.spreadsheet, copyowner=cli_args.copyright,
            version=cli_args.version, defaultcss=defaultcss, addcss=cli_args.css) )
