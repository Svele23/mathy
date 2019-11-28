Mathy includes what's called a Computer Algebra System. Its job is to turn text into math trees that can be examined and manipulated by way of a two-step process:

1. [Tokenize](/cas/tokenizer) the text into a list of `type`/`value` pairs
2. [Parse](/cas/parser) the token list into an Expression tree

This is the main function of Mathy's CAS system.

## Examples

### Arithmetic

To get a sense for how Mathy's CAS components work, let's add some numbers together and assert that the end result is what we think it should be.

```Python
{!./snippets/cas/overview/evaluate_expression.py!}
```

`mathy:4+2`

### Variables Evaluation

Mathy can also deal with expressions that have variables.

When an expression has variables in it, you can evaluate it by passing the "context" to use:

`mathy:4x+2y`

```Python
{!./snippets/cas/overview/evaluate_expression_variables.py!}
```

### Tree Transformations

Mathy can also transform the parsed Expression trees using a set of Rules that change the tree structure without altering the value it outputs when you call `evaluate()`.

`mathy:4x+2x`

```python

{!./snippets/cas/overview/rules_factor_out.py!}

```

`mathy:(4 + 2)*x`