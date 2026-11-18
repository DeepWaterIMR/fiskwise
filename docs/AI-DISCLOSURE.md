# Fiskwise AI-use disclosure policy

This policy applies to every maintained Fiskwise knowledge pack and R package. It follows
current R practice: the [CRAN Repository Policy](https://cran.r-project.org/web/packages/policies.html)
and *Writing R Extensions* define authorship roles for people and legal entities only, and
the [rOpenSci policy on generative AI](https://ropensci.org/blog/2026/02/26/ropensci-ai-policy/)
(February 2026) asks authors to *disclose* AI use and affirm that they reviewed it.

## Credit

- AI tools are never listed in `Authors@R`, `@author`, `CITATION`, or as `cph`. The human
  maintainer stays `aut`/`cre` and is accountable for all content.
- `Co-Authored-By` trailers in commit messages remain the per-commit record of AI help.

## Package and pack statement

Every maintained repository carries a short **Use of generative AI** statement:
R packages in a `README.Rmd` section and on the package help page (`?pkg`, via
`@section Use of generative AI:` in `R/<pkg>-package.R`); knowledge packs in a README section.

> **Use of generative AI.** [Much of / Parts of] the code, tests and documentation in this
> [package / repository] were written with an AI coding assistant ([MODEL, VENDOR]) from the
> maintainer's prototypes and instructions. The maintainer reviewed, tested and accepted all
> AI-generated material and is responsible for it. Commits made with AI assistance carry a
> `Co-Authored-By` line in the Git history. This follows the rOpenSci policy on generative AI
> in software review.

`[MODEL, VENDOR]` names the model that actually did the work, as model and vendor, for example
"Claude Opus 5.5, Anthropic", "GPT-6.2 Sol, OpenAI", a Google model, or a local model. An agent
knows its own model ID from its system prompt.

## Per-function record (R packages)

Each documented, AI-assisted exported function has a roxygen section before `@author`:

```r
#' @section AI assistance:
#' Written with Claude Opus 5.5 (Anthropic); reviewed in full by Claude Opus
#' 5.5 (Anthropic), 2026-11-17.
```

Unexported helpers fall under the function that calls them. Functions from before this
policy whose model is unknown say "AI-assisted (model not recorded); not yet reviewed in
full by the current model."

## Review before replacing a model

A newer model replaces an older one only after it has reviewed the work:

1. When an agent whose model differs from the one named in a record (newer, or from another
   vendor) changes that function, it first reviews the **whole** function with its helpers,
   tests and documentation: correctness, edge cases, statistics, and style.
2. It reports what it found to the maintainer as suggested changes and applies only the
   changes the maintainer approves.
3. It then sets the record to "reviewed in full by <its model>, <date>".
4. An agent that does not do the full review keeps the record and appends "edited by
   <its model>".

A full review can also be requested on its own ("review function X with the current model").
The package statement names the models in the function records; a newer model replaces an
older one there once no record names the older model as its last full reviewer. Models from
different reviews are listed together (e.g. "Claude Opus 5.5, Anthropic; GPT-6.2 Sol,
OpenAI") until then.

Update the statement's share ("Much of" / "Parts of") and the records in the same commit
as the work.
