# Markdown Typography Guide

This guide demonstrates the various typography elements available in Markdown.

## Headings
Headings are created using the `#` symbol, with the number of `#` indicating the heading level.

```markdown
# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading
```
# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading

## Emphasis
Emphasis can be added using asterisks `*` or underscores `_`.

```markdown
*Italic* or _Italic_

**Bold** or __Bold__

***Bold and Italic*** or ___Bold and Italic___
```
*Italic* or _Italic_

**Bold** or __Bold__

***Bold and Italic*** or ___Bold and Italic___



## Blockquotes
Blockquotes are indicated using the `>` symbol.

```markdown
> This is a single-line blockquote.

> This is a blockquote with
> multiple lines.
```

> This is a single-line blockquote.

> This is a blockquote with
> multiple lines.



## Lists
Markdown supports ordered and unordered lists.

### Unordered List
Use `-`, `*`, or `+` for unordered lists.

```markdown
- Item 1
- Item 2
  - Subitem 1
  - Subitem 2
* Item 3
+ Item 4
```

- Item 1
- Item 2
  - Subitem 1
  - Subitem 2
* Item 3
+ Item 4





### Ordered List
Use numbers followed by a period.

```markdown
1. First item
2. Second item
3. Third item
   1. Subitem 1
   2. Subitem 2
```

1. First item
2. Second item
3. Third item
   1. Subitem 1
   2. Subitem 2



## Code
Inline and block code can be formatted for syntax highlighting.

### Inline Code
Use backticks for inline code.

```markdown
`inline code`
```
MARK `inline code` MARK

### Block Code
Use triple backticks for block code.

```markdown
\```python
def hello_world():
    print("Hello, world!")
\```
```

```python
def hello_world():
    print("Hello, world!")
```

## Tables
Tables are created using pipes `|` and dashes `-` to separate columns.

```markdown
| Syntax      | Description |
| ----------- | ----------- |
| Header      | Title       |
| Paragraph   | Text        |
```
| Syntax      | Description |
| ----------- | ----------- |
| Header      | Title       |
| Paragraph   | Text        |



## Links
Create links using the `[text](URL)` syntax.

```markdown
[OpenAI](https://openai.com)
```
Text and text [OpenAI](https://openai.com) text and text

## Images
Include images with `![alt text](URL)`.

```markdown
![Markdown Logo](https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg)
```
can we do images? ![Markdown Logo](https://upload.wikimedia.org/wikipedia/commons/4/48/Markdown-mark.svg)




## Horizontal Rule
Create horizontal rules with three or more asterisks `***`, dashes `---`, or underscores `___`.

```markdown
---
```

---
rule
___




## Strikethrough
Strikethrough text using `~~` on both sides.

```markdown
~~This text is strikethrough.~~
```
~~This text is strikethrough.~~

## Task Lists
Use task lists to show to-do items.

```markdown
- [x] Task 1
- [ ] Task 2
- [ ] Task 3
```
- [x] Task 1
- [ ] Task 2
- [ ] Task 3

## Footnotes
Footnotes can be added for additional information.

```markdown
Here's a footnote reference[^1].

[^1]: This is the footnote.
```
Here's a footnote reference[^1].

[^1]: This is the footnote.

## Emojis
Add emojis using shortcodes like `:smile:`.

```markdown
:smile: :heart: :+1:
```
:smile: :heart: :+1:

## Escaping Special Characters
Use backslashes `\` to escape Markdown characters.

```markdown
\*This text is not italicized\*
```
\*This text is not italicized\*

## HTML in Markdown
HTML can also be used within Markdown for additional formatting.

```html
<div style="color: red;">This text is red</div>
```
<div style="color: red;">This text is red</div>