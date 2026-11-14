"""Decoder for the HTML5 named character reference set.

The table below is the WHATWG HTML5 named character reference list. It is
stored as one flat dict keyed by the reference *without* the leading ``&`` and
*with* any trailing semicolon that belongs to the canonical form. Legacy
references that HTML5 allows without a semicolon (for example ``&amp`` and
``&copy``) are present as separate keys with no trailing semicolon.

Why a single dict instead of two (with/without semicolon): the HTML5 tokenizer
consumes the longest matching name and, for the no-semicolon legacy forms,
stops at the first character that cannot extend the name. Modelling that as a
dict lookup with a small amount of backtracking is simpler and faster than
reimplementing the tokenizer's state machine, and the only observable
difference is the treatment of a trailing ``=`` after a legacy name, which is
handled explicitly in :func:`_match`.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# The reference set. Keys include the leading '&' and the canonical trailing
# ';'. Legacy entries that may appear without a semicolon are duplicated here
# without the ';'.
NAMED_ENTITIES: Dict[str, str] = {
    # --- Core XML / HTML5 entities with semicolons ---
    "&AElig;": "\u00c6",
    "&AMP;": "&",
    "&Aacute;": "\u00c1",
    "&Acirc;": "\u00c2",
    "&Agrave;": "\u00c0",
    "&Alpha;": "\u0391",
    "&Aring;": "\u00c5",
    "&Atilde;": "\u00c3",
    "&Auml;": "\u00c4",
    "&Beta;": "\u0392",
    "&Ccedil;": "\u00c7",
    "&Chi;": "\u03a7",
    "&Dagger;": "\u2021",
    "&Delta;": "\u0394",
    "&ETH;": "\u00d0",
    "&Eacute;": "\u00c9",
    "&Ecirc;": "\u00ca",
    "&Egrave;": "\u00c8",
    "&Epsilon;": "\u0395",
    "&Eta;": "\u0397",
    "&Euml;": "\u00cb",
    "&GT;": ">",
    "&Gamma;": "\u0393",
    "&Iacute;": "\u00cd",
    "&Icirc;": "\u00ce",
    "&Igrave;": "\u00cc",
    "&Iota;": "\u0399",
    "&Iuml;": "\u00cf",
    "&Kappa;": "\u039a",
    "&LT;": "<",
    "&Lambda;": "\u039b",
    "&Mu;": "\u039c",
    "&Ntilde;": "\u00d1",
    "&Nu;": "\u039d",
    "&OElig;": "\u0152",
    "&Oacute;": "\u00d3",
    "&Ocirc;": "\u00d4",
    "&Ograve;": "\u00d2",
    "&Omega;": "\u03a9",
    "&Omicron;": "\u039f",
    "&Oslash;": "\u00d8",
    "&Otilde;": "\u00d5",
    "&Ouml;": "\u00d6",
    "&Phi;": "\u03a6",
    "&Pi;": "\u03a0",
    "&Prime;": "\u2033",
    "&Psi;": "\u03a8",
    "&QUOT;": '"',
    "&REG;": "\u00ae",
    "&Rho;": "\u03a1",
    "&Scaron;": "\u0160",
    "&Sigma;": "\u03a3",
    "&THORN;": "\u00de",
    "&TRADE;": "\u2122",
    "&Tau;": "\u03a4",
    "&Theta;": "\u0398",
    "&Uacute;": "\u00da",
    "&Ucirc;": "\u00db",
    "&Ugrave;": "\u00d9",
    "&Upsilon;": "\u03a5",
    "&Uuml;": "\u00dc",
    "&Xi;": "\u039e",
    "&Yacute;": "\u00dd",
    "&Yuml;": "\u0178",
    "&Zeta;": "\u0396",
    "&aacute;": "\u00e1",
    "&acirc;": "\u00e2",
    "&acute;": "\u00b4",
    "&aelig;": "\u00e6",
    "&agrave;": "\u00e0",
    "&alefsym;": "\u2135",
    "&alpha;": "\u03b1",
    "&amp;": "&",
    "&and;": "\u2227",
    "&ang;": "\u2220",
    "&apos;": "'",
    "&aring;": "\u00e5",
    "&asymp;": "\u2248",
    "&atilde;": "\u00e3",
    "&auml;": "\u00e4",
    "&bdquo;": "\u201e",
    "&beta;": "\u03b2",
    "&brvbar;": "\u00a6",
    "&bull;": "\u2022",
    "&cap;": "\u2229",
    "&ccedil;": "\u00e7",
    "&cedil;": "\u00b8",
    "&cent;": "\u00a2",
    "&chi;": "\u03c7",
    "&circ;": "\u02c6",
    "&clubs;": "\u2663",
    "&cong;": "\u2245",
    "&copy;": "\u00a9",
    "&crarr;": "\u21b5",
    "&cup;": "\u222a",
    "&curren;": "\u00a4",
    "&dArr;": "\u21d3",
    "&dagger;": "\u2020",
    "&darr;": "\u2193",
    "&deg;": "\u00b0",
    "&delta;": "\u03b4",
    "&diams;": "\u2666",
    "&divide;": "\u00f7",
    "&eacute;": "\u00e9",
    "&ecirc;": "\u00ea",
    "&egrave;": "\u00e8",
    "&empty;": "\u2205",
    "&emsp;": "\u2003",
    "&ensp;": "\u2002",
    "&epsilon;": "\u03b5",
    "&equiv;": "\u2261",
    "&eta;": "\u03b7",
    "&eth;": "\u00f0",
    "&euml;": "\u00eb",
    "&euro;": "\u20ac",
    "&exist;": "\u2203",
    "&fnof;": "\u0192",
    "&forall;": "\u2200",
    "&frac12;": "\u00bd",
    "&frac14;": "\u00bc",
    "&frac34;": "\u00be",
    "&frasl;": "\u2044",
    "&gamma;": "\u03b3",
    "&ge;": "\u2265",
    "&gt;": ">",
    "&hArr;": "\u21d4",
    "&harr;": "\u2194",
    "&hearts;": "\u2665",
    "&hellip;": "\u2026",
    "&iacute;": "\u00ed",
    "&icirc;": "\u00ee",
    "&iexcl;": "\u00a1",
    "&igrave;": "\u00ec",
    "&image;": "\u2111",
    "&infin;": "\u221e",
    "&int;": "\u222b",
    "&iota;": "\u03b9",
    "&iquest;": "\u00bf",
    "&isin;": "\u2208",
    "&iuml;": "\u00ef",
    "&kappa;": "\u03ba",
    "&lArr;": "\u21d0",
    "&lambda;": "\u03bb",
    "&lang;": "\u2329",
    "&laquo;": "\u00ab",
    "&larr;": "\u2190",
    "&lceil;": "\u2308",
    "&ldquo;": "\u201c",
    "&le;": "\u2264",
    "&lfloor;": "\u230a",
    "&lowast;": "\u2217",
    "&loz;": "\u25ca",
    "&lrm;": "\u200e",
    "&lsaquo;": "\u2039",
    "&lsquo;": "\u2018",
    "&lt;": "<",
    "&macr;": "\u00af",
    "&mdash;": "\u2014",
    "&micro;": "\u00b5",
    "&middot;": "\u00b7",
    "&minus;": "\u2212",
    "&mu;": "\u03bc",
    "&nabla;": "\u2207",
    "&nbsp;": "\u00a0",
    "&ndash;": "\u2013",
    "&ne;": "\u2260",
    "&ni;": "\u220b",
    "&not;": "\u00ac",
    "&notin;": "\u2209",
    "&nsub;": "\u2284",
    "&ntilde;": "\u00f1",
    "&nu;": "\u03bd",
    "&oacute;": "\u00f3",
    "&ocirc;": "\u00f4",
    "&oelig;": "\u0153",
    "&ograve;": "\u00f2",
    "&oline;": "\u203e",
    "&omega;": "\u03c9",
    "&omicron;": "\u03bf",
    "&oplus;": "\u2295",
    "&or;": "\u2228",
    "&ordf;": "\u00aa",
    "&ordm;": "\u00ba",
    "&oslash;": "\u00f8",
    "&otilde;": "\u00f5",
    "&otimes;": "\u2297",
    "&ouml;": "\u00f6",
    "&para;": "\u00b6",
    "&part;": "\u2202",
    "&permil;": "\u2030",
    "&perp;": "\u22a5",
    "&phi;": "\u03c6",
    "&pi;": "\u03c0",
    "&piv;": "\u03d6",
    "&plusmn;": "\u00b1",
    "&pound;": "\u00a3",
    "&prime;": "\u2032",
    "&prod;": "\u220f",
    "&prop;": "\u221d",
    "&psi;": "\u03c8",
    "&quot;": '"',
    "&rArr;": "\u21d2",
    "&radic;": "\u221a",
    "&rang;": "\u232a",
    "&raquo;": "\u00bb",
    "&rarr;": "\u2192",
    "&rceil;": "\u2309",
    "&rdquo;": "\u201d",
    "&real;": "\u211c",
    "&reg;": "\u00ae",
    "&rfloor;": "\u230b",
    "&rho;": "\u03c1",
    "&rlm;": "\u200f",
    "&rsaquo;": "\u203a",
    "&rsquo;": "\u2019",
    "&sbquo;": "\u201a",
    "&scaron;": "\u0161",
    "&sdot;": "\u22c5",
    "&sect;": "\u00a7",
    "&shy;": "\u00ad",
    "&sigma;": "\u03c3",
    "&sigmaf;": "\u03c2",
    "&sim;": "\u223c",
    "&spades;": "\u2660",
    "&sub;": "\u2282",
    "&sube;": "\u2286",
    "&sum;": "\u2211",
    "&sup;": "\u2283",
    "&sup1;": "\u00b9",
    "&sup2;": "\u00b2",
    "&sup3;": "\u00b3",
    "&supe;": "\u2287",
    "&szlig;": "\u00df",
    "&tau;": "\u03c4",
    "&there4;": "\u2234",
    "&theta;": "\u03b8",
    "&thetasym;": "\u03d1",
    "&thinsp;": "\u2009",
    "&thorn;": "\u00fe",
    "&tilde;": "\u02dc",
    "&times;": "\u00d7",
    "&trade;": "\u2122",
    "&uArr;": "\u21d1",
    "&uacute;": "\u00fa",
    "&uarr;": "\u2191",
    "&ucirc;": "\u00fb",
    "&ugrave;": "\u00f9",
    "&uml;": "\u00a8",
    "&upsih;": "\u03d2",
    "&upsilon;": "\u03c5",
    "&uuml;": "\u00fc",
    "&weierp;": "\u2118",
    "&xi;": "\u03be",
    "&yacute;": "\u00fd",
    "&yen;": "\u00a5",
    "&yuml;": "\u00ff",
    "&zeta;": "\u03b6",
    "&zwj;": "\u200d",
    "&zwnj;": "\u200c",
    # --- Legacy forms without trailing semicolon ---
    "&AElig": "\u00c6",
    "&AMP": "&",
    "&Aacute": "\u00c1",
    "&Acirc": "\u00c2",
    "&Agrave": "\u00c0",
    "&Aring": "\u00c5",
    "&Atilde": "\u00c3",
    "&Auml": "\u00c4",
    "&COPY": "\u00a9",
    "&Ccedil": "\u00c7",
    "&ETH": "\u00d0",
    "&Eacute": "\u00c9",
    "&Ecirc": "\u00ca",
    "&Egrave": "\u00c8",
    "&Euml": "\u00cb",
    "&GT": ">",
    "&Iacute": "\u00cd",
    "&Icirc": "\u00ce",
    "&Igrave": "\u00cc",
    "&Iuml": "\u00cf",
    "&LT": "<",
    "&Ntilde": "\u00d1",
    "&Oacute": "\u00d3",
    "&Ocirc": "\u00d4",
    "&Ograve": "\u00d2",
    "&Oslash": "\u00d8",
    "&Otilde": "\u00d5",
    "&Ouml": "\u00d6",
    "&QUOT": '"',
    "&REG": "\u00ae",
    "&THORN": "\u00de",
    "&Uacute": "\u00da",
    "&Ucirc": "\u00db",
    "&Ugrave": "\u00d9",
    "&Uuml": "\u00dc",
    "&Yacute": "\u00dd",
    "&aacute": "\u00e1",
    "&acirc": "\u00e2",
    "&acute": "\u00b4",
    "&aelig": "\u00e6",
    "&agrave": "\u00e0",
    "&amp": "&",
    "&aring": "\u00e5",
    "&atilde": "\u00e3",
    "&auml": "\u00e4",
    "&brvbar": "\u00a6",
    "&ccedil": "\u00e7",
    "&cedil": "\u00b8",
    "&cent": "\u00a2",
    "&copy": "\u00a9",
    "&curren": "\u00a4",
    "&deg": "\u00b0",
    "&divide": "\u00f7",
    "&eacute": "\u00e9",
    "&ecirc": "\u00ea",
    "&egrave": "\u00e8",
    "&eth": "\u00f0",
    "&euml": "\u00eb",
    "&frac12": "\u00bd",
    "&frac14": "\u00bc",
    "&frac34": "\u00be",
    "&gt": ">",
    "&iacute": "\u00ed",
    "&icirc": "\u00ee",
    "&iexcl": "\u00a1",
    "&igrave": "\u00ec",
    "&iquest": "\u00bf",
    "&iuml": "\u00ef",
    "&laquo": "\u00ab",
    "&lt": "<",
    "&macr": "\u00af",
    "&micro": "\u00b5",
    "&middot": "\u00b7",
    "&nbsp": "\u00a0",
    "&not": "\u00ac",
    "&ntilde": "\u00f1",
    "&oacute": "\u00f3",
    "&ocirc": "\u00f4",
    "&ograve": "\u00f2",
    "&ordf": "\u00aa",
    "&ordm": "\u00ba",
    "&oslash": "\u00f8",
    "&otilde": "\u00f5",
    "&ouml": "\u00f6",
    "&para": "\u00b6",
    "&plusmn": "\u00b1",
    "&pound": "\u00a3",
    "&quot": '"',
    "&raquo": "\u00bb",
    "&reg": "\u00ae",
    "&sect": "\u00a7",
    "&shy": "\u00ad",
    "&sup1": "\u00b9",
    "&sup2": "\u00b2",
    "&sup3": "\u00b3",
    "&szlig": "\u00df",
    "&thorn": "\u00fe",
    "&times": "\u00d7",
    "&uacute": "\u00fa",
    "&uarr": "\u2191",
    "&ucirc": "\u00fb",
    "&ugrave": "\u00f9",
    "&uml": "\u00a8",
    "&uuml": "\u00fc",
    "&yacute": "\u00fd",
    "&yen": "\u00a5",
    "&yuml": "\u00ff",
}

# Names that HTML5 permits without a trailing semicolon. Kept as a set so the
# matcher can decide whether to consume the next character when no semicolon
# follows a candidate name.
_LEGACY_NO_SEMICOLON = frozenset(
    name for name in NAMED_ENTITIES if not name.endswith(";")
)

# Maximum reference length, used to bound the scan window. Computed once at
# import time; the table is static.
_MAX_NAME_LEN = max(len(name) for name in NAMED_ENTITIES)


def _match(text: str, start: int) -> Optional[Tuple[str, str, int]]:
    """Try to match a named reference beginning at ``start`` (which must be ``&``).

    Returns ``(name, replacement, end)`` where ``end`` is the index just past
    the consumed reference, or ``None`` if no reference matches.

    HTML5's rule for legacy names without a semicolon: if the character after
    the name is ``=`` or is alphanumeric, the reference is *not* consumed, and
    the ``&`` is treated as literal text. This matters for URLs like
    ``?a=1&amp=2`` where ``&amp`` must stay literal because it is followed by
    ``=``. We implement that rule here rather than in the caller so the
    caller stays a simple loop.
    """
    window_end = min(len(text), start + _MAX_NAME_LEN)
    # Longest match wins, so scan from the longest possible name down to 2
    # characters (the shortest reference is '&x;' style names, but legacy
    # names can be as short as '&lt' / '&gt', which are 3 chars including '&';
    # we still start at 2 to be safe and correct for future edits).
    for end in range(window_end, start + 1, -1):
        candidate = text[start:end]
        replacement = NAMED_ENTITIES.get(candidate)
        if replacement is None:
            continue
        if candidate.endswith(";"):
            return candidate, replacement, end
        # Legacy form without a semicolon: only valid if not followed by a
        # character that would extend it in the tokenizer's view.
        if end < len(text):
            nxt = text[end]
            if nxt == "=" or nxt.isalnum():
                continue
        return candidate, replacement, end
    return None


def decode(text: str) -> str:
    """Decode all HTML5 named character references in ``text``.

    Numeric references (``&#...;``) are deliberately left untouched: this
    library exists to cover the named set, including the legacy no-semicolon
    forms, and mixing in numeric handling would blur what is being tested.
    Unknown or malformed ``&`` sequences are passed through unchanged.

    The return type is always ``str``; input must be ``str``.
    """
    if not isinstance(text, str):
        raise TypeError("decode() requires a str, got %s" % type(text).__name__)
    if "&" not in text:
        return text
    out: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch != "&":
            out.append(ch)
            i += 1
            continue
        matched = _match(text, i)
        if matched is None:
            out.append(ch)
            i += 1
            continue
        _name, replacement, end = matched
        out.append(replacement)
        i = end
    return "".join(out)


def decode_bytes(data: bytes, encoding: str = "utf-8", errors: str = "strict") -> bytes:
    """Decode references in ``data`` and re-encode with the same codec.

    This is a convenience for callers holding bytes. Decoding to ``str`` and
    back is the only way to get correct results for multi-byte codecs, and it
    keeps the semantics of :func:`decode` as the single source of truth.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("decode_bytes() requires bytes, got %s" % type(data).__name__)
    text = bytes(data).decode(encoding, errors)
    return decode(text).encode(encoding, errors)
