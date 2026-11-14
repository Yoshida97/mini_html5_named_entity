# mini_html5_named_entity

Decodes the complete set of HTML5 named character references, including the
legacy entities that are allowed without a trailing semicolon.

```python
from mini_html5_named_entity import decode, decode_bytes

decode("Tom &amp; Jerry &copy; 2024")
# 'Tom & Jerry \u00a9 2024'

decode("5 &lt 6")
# '5 < 6'  (legacy form without a semicolon)

decode("&amp=1")
# '&amp=1'  (HTML5 does not consume a legacy name before '=')

decode_bytes(b"&lt;p&gt;hi&lt;/p&gt;")
# b'<p>hi</p>'
```

## Why this exists

The standard library's `html.unescape` covers numeric references and most
named ones, but it is a general-purpose HTML parser helper and its behaviour
around the legacy no-semicolon forms is easy to get subtly wrong when you are
trying to match a browser exactly. This library is a single, small, explicit
table plus a matcher that follows the WHATWG rule for legacy names: a name
without a semicolon is only consumed when the next character is neither `=`
nor alphanumeric.

The trade-off is scope. Numeric references (`&#65;`, `&#x41;`) are left
alone on purpose. Mixing them in would mean reimplementing the numeric
parsing rules too, and the named set is what this library is about. If you
need numeric decoding as well, run the output through `html.unescape`
afterwards.

## The awkward edge

Legacy names are greedy until a non-name character. `&notin` is not `&not`
followed by `in`: because `i` is alphanumeric, the legacy `&not` is not
consumed at all and the whole string stays literal. `&notin;` with the
semicolon does decode, to `\u2209`. If you are porting from a parser that
treats `&notin` as `\u00ac` + `in`, this is the case that will surprise you.

## API

- `decode(text: str) -> str` — decode named references in a string.
- `decode_bytes(data: bytes, encoding: str = "utf-8", errors: str = "strict") -> bytes` — decode in a byte string and re-encode with the same codec.

Both raise `TypeError` on the wrong input type. Unknown or malformed `&`
sequences are passed through unchanged.
