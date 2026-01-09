# LLM Election Results PDF Extraction

#### Derek Willis, OpenElections
#### SPSA 2026

## The Big Idea

You don't need to learn to code. LLMs can either:

1. Extract directly from image PDFs (works 60-70% of the time, or more depending)
2. Write custom parsers for you (for electronic PDFs)

Both approaches: describe what you want + provide examples. LLM does the work.

This [blog post](https://thescoop.org/archives/2025/06/09/how-openelections-uses-llms/) started me down this path.

## When to Use Which Approach

**Image PDF Extraction:**
- Works well on clean, consistent formats
- 95-100% accuracy on ~60% of PDFs tested

**LLM-Written Custom Parser:**
- Electronic PDFs
- Processing multiple counties with same format

## Recommended Models

**Best accuracy:** Gemini 2.5 Pro (99.1% on tested samples, $0.15-0.30/county)

**Best value:** Gemini Flash 3 (93.8% accuracy, $0.02-0.05/county)

Start with Flash for testing. Switch to 2.5  or 3 Pro if needed.

## Image PDF Extraction: Critical Prompt Elements

1. Exact CSV column structure
2. "Include ALL candidates, even those with 0 votes"
3. "Process ENTIRE PDF - don't stop early"
4. 5-10 example rows showing proper format
5. "Include 'Over Votes' and 'Under Votes' rows"
6. "Return ONLY CSV, no explanation"

**Most common failure:** Not mentioning zero-vote candidates (models often skip them by default)

**You might need to set max tokens to a higher limit on some models**

## Custom Parser: How to Get LLM to Write One

**You provide:**
- Sample PDF
- CSV example showing exactly what output you want
- Description of special cases and how to handle them

**LLM provides:**
- Complete working Python script
- Error handling
- Comments explaining logic

**Process:**
1. LLM writes parser
2. Test on sample PDF
3. Tell LLM what's wrong
4. LLM fixes code
5. Repeat until output matches (usually 3-5 iterations)

## Validation

You cannot skip this part!

**Minimum:** Compare precinct sums to county totals  
**Better:** Multi-model extraction on samples (where they agree = high confidence)  
**Best:** Above + manual spot-check 2-3 races per county

Check that CSV handles:
- Candidates with 0 votes
- "Over Votes" and "Under Votes" rows
- All races (especially those at end of PDF)
- Unusual races like judicial retention or ballot initiatives

## Cost for 100 Counties

- Gemini 2.5 Pro direct extraction: $15-30
- Gemini 3 Flash direct extraction: $2-5

## When LLMs Don't Work Well

- Vertically-oriented precinct names
- Handwritten documents (although this is changing!)
- Documents containing multiple formats

## Getting Started

Sign up for the [education benefits from GitHub](https://github.com/education/) and enable Copilot. That will give you greater access to fronter models for free (with monthly limits). Your students can do the same!

If you have some funding, Claude Code is an excellent tool to build software with, and you can set the terms of how much it does with or without your direct control.

## You Don't Need to Learn to Code
### You Need to Learn to Evaluate the Results

Tired: "I need to learn Python to process these PDFs"

Wired: "I need to describe what I want and show examples. LLM handles the code."

Your expertise: Understanding election data formats and validation  
LLM's expertise: Writing and debugging code

## Example: Scurry County, Texas

* [Original Image PDF](https://github.com/openelections/openelections-sources-tx/blob/master/2024/general/2024%20Scurry%20County%2C%20TX%20precinct-level%20results.pdf)
* [Prompt for models](https://github.com/openelections/openelections-data-tx/blob/master/python-parsers/pdf_extractor.py) (using Claude Haiku 4.5)
* [CSV Result](https://github.com/openelections/openelections-data-tx/blob/master/test/20241105__tx__general__scurry__precinct.csv)