Proxy Printer
=============

Generates reasonably good-looking HTML proxies for a card game from an ODS spreadsheet. Useful for making card game prototypes. Comes with some basic CSS; you can add your own style rules to make the proxies prettier or better suited to your game. Does some heuristic text resizing so that text of different lengths is more likely to fit without being too small.


Installing with pip
------

(Python 3 required)

```
pip3 install proxyprinter
```

(You might need to use `sudo` or a VirtualEnv depending on your system setup.)


Usage
------

     proxyprinter example-cards.ods > output_file.html

Do `proxyprinter --help` for usage statement with all commandline options.


Input Format
-------------
OpenDocument Spreadsheet (ODF) file. Example: [example-cards.ods](example-cards.ods). Each "Sheet" in the document is one type of card in your game. The name of the sheet is the card type. The first row in the sheet lists the titles for each field. Each subsequent row is a card.

The following field names are special in some way:

- **Name**: The name of your card (goes in the title area of the card).
- **Traits**: A comma-separated list of tags/labels for the card. Each gets its own span with a class so you can style it. Procedurally generates style rules to color-code these.
- **Text**: Gets put in a single text_area alongside Flavor Text.
- **Flavor Text**: Gets put in a single text_area alongside Text.
- **Version**: Listed in the footer. Use this with the `-v` switch to only print recently-updated cards.
- **Copies:** If present and a non-negative integer, prints that many copies of the card as part of the overall print sheet. (Otherwise, the print sheet contains 1 copy of this card.)


In-Stylesheet Settings
----------------------

You can customize various settings for your project by adding a `ProxyPrinter Settings` tab to your spreadsheet. (The sheet must match that name exactly.) In that spreadsheet page, put a setting name in the **first row** of the sheet to define a custom value for that setting:

| Setting    | Description | How to Set |
|------------|-------------|------------|
| `CSSFile`  | The filename of an external CSS file to reference. | Put the value in the **2nd row**, same column |
| `Copyright` | The copyright owner to print at the bottom of the cards. | Put the value in the **2nd row**, same column |
| Text Size Thresholds | Downsize text when it exceeds length thresholds. | [Text Size Thresholds](#text-size-thresholds) |
| Rich Field Substitution | Substitution patterns to embed special styles or symbols in field text | [Rich Field Substitutions](#rich-field-substitutions) |

For any setting defined in the spreadsheet that can also be set by commandline parameter, the commandline parameter overrides it if specified.

### Text Size Thresholds ###

The Proxy Printer sizes down text for most fields based on the number of characters in it. Depending on how much space you have available for each field, you may need to adjust these thresholds, so that it goes down to medium or small text sizes with less (or more) text.

To customize the text sizing thresholds, put the following 3 setting names in the first row of your settings sheet tab:

* `TextSizeField`
* `TextSizeMediumIfOver`
* `TextSizeSmallIfOver`

In each row after it, you can define a threshold to use.  In each row, put the values in the columns as follows:

| TextSizeField column | TextSizeMediumIfOver | TextSizeSmallIfOver |
|----------------------|----------------------|---------------------|
| Name of the field these thresholds apply to. (Each "Field" is a column from one of the card pages in your spreadsheet, e.g. `Text`, `Flavor Text`, `Cost`, etc.) The default for all fields is represented by the field name `*`. | Decrease from big to medium size text if the number of characters is over this number. (Defaults: 30 for most fields, 140 for `Text`, 18 for `Name`) | Decrease from medium to small size if the number of characters is over this limit. (Defaults: 50 for most fields, 220 for `Text`, 24 for `Name`.) |

Any default values you don't redefine remain. Any fields that don't have thresholds defined use the thresholds for `*` (whether you defined it or left it default).


### Rich Field Substitutions ###

To include special styles and images inline in your text, you can define patterns from the spreadsheet values that will map to specific styles in the HTML. For example, you can make it so that `<5 G>` gets replaced with a "5 Gold" icon in the text. (Custom CSS may be necessary, of course.)

Put the value `RichFields` in the first row of your settings sheet tab to define which fields should get processed this way. In each other row, put the name of a field in the same column. The field name `*` means "all fields". By default, only the `Text` field is processed.

To do define which substitutions to make, put the following 2 setting names in the first row of your settings sheet tab:

* `ProcessPatterns`
* `ProcessReplacements`

In each later row, put the following values:

| ProcessPatterns column | ProcessReplacements column |
|------------------------|----------------------------|
| [Regular Expression](https://docs.python.org/3/library/re.html) to search for in the text. Example: `\<([0-9]+) G\>` | Text to replace it with. Regular-expression backreferences are allowed. Example: `<span class='gold_coin'>\1</span>` |

These substitutions apply after escaping any HTML that appears in the text, so if your pattern needs to match `<` or `>`, you must use the escaped versions `&lt;` and `&gt;` instead. Also, this means your substitutions can include raw HTML.
