#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
REQUIRED = {"html", "head", "body", "title"}


class Validator(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.tags = set()
        self.errors = []
        self.has_doctype = False

    def handle_decl(self, decl):
        if decl.lower().strip() == "doctype html":
            self.has_doctype = True

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self.tags.add(tag)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.tags.add(tag.lower())

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"unexpected closing tag </{tag}>")
            return
        expected = self.stack.pop()
        if expected != tag:
            self.errors.append(f"expected </{expected}>, found </{tag}>")


def validate(path):
    parser = Validator()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except Exception as exc:
        return [f"parser error: {exc}"]
    errors = list(parser.errors)
    if not parser.has_doctype:
        errors.append("missing <!doctype html>")
    missing = REQUIRED - parser.tags
    if missing:
        errors.append("missing required tags: " + ", ".join(sorted(missing)))
    if parser.stack:
        errors.append("unclosed tags: " + ", ".join(parser.stack))
    return errors


def main():
    files = [p for p in Path(".").rglob("*.html") if not {".git", "node_modules"} & set(p.parts)]
    if not files:
        print("No HTML files found", file=sys.stderr)
        return 1
    failed = False
    for path in files:
        errors = validate(path)
        if errors:
            failed = True
            for error in errors:
                print(f"{path}: {error}", file=sys.stderr)
        else:
            print(f"OK: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
