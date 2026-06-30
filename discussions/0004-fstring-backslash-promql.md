# Python f-string 'unexpected character after line continuation' building a PromQL selector

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/29

## Question

Building PromQL label selectors in Python f-strings, this blew up:

```python
tgt(f'mongodb_connections{f("state=\"current\"")}')
```

`SyntaxError: unexpected character after line continuation character`. What's going on and what's the clean fix?
## Answer

Before Python 3.12 (and still the safest habit), the **expression part of an f-string cannot contain a backslash**. Your `\"` escapes live inside the `{...}` replacement field, so the parser chokes on the backslash — that's the "line continuation character" error, not anything about Mongo or PromQL.

Cleanest fixes:

1. **Build the string with concatenation** so the quotes aren't inside an f-string expression:
   ```python
   def fm(extra=None):
       return '{instance' + sel + (',' + extra if extra else '') + '}'
   tgt('mongodb_connections' + fm('state="current"'))
   ```
   Now `state="current"` is an ordinary string literal — double quotes, no escaping.

2. Or pull the escape out into a variable referenced by the f-string.
3. Or, on Python 3.12+, the grammar change (PEP 701) actually permits backslashes in f-strings — but concatenation keeps it portable and readable.

Bonus: it also dodges the brace-doubling headache when your literal already contains `{` `}`.
