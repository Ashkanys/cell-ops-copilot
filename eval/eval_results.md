# V1:
* Chunker: chunks with headers name, references are also chunked.
* eval_v2: only have doc only, doc + sections
=== DOC-ONLY (answerable only) ===
hit@1: 6/10 = 0.600
hit@3: 10/10 = 1.000
hit@5: 10/10 = 1.000
hit@10: 10/10 = 1.000
first_hit_k@10 median: 1.0 | miss@10: 0/10
MRR@10 (doc): 0.783

=== DOC+SECTION (answerable only) ===
Answerable examples with section labels in gold: 10/10
hit@1: 3/10 = 0.300
hit@3: 4/10 = 0.400
hit@5: 6/10 = 0.600
hit@10: 8/10 = 0.800
first_hit_k@10 median: 3.5 | miss@10: 2/10
MRR@10 (doc+section): 0.414

Combined score (0.3*doc + 0.7*doc+section): 0.525

=== NO-ANSWER ===
abstain accuracy: 0/1 = 0.000
false positives (should abstain but didn't): 1/1 = 1.000
false abstains (should answer but abstained): 0/10 = 0.000

# V2: 
* chunker: removed headers in the chunking, removed chunks with low character
eval: only have doc only, doc + sections

=== DOC-ONLY (answerable only) ===
hit@1: 5/10 = 0.500
hit@3: 10/10 = 1.000
hit@5: 10/10 = 1.000
hit@10: 10/10 = 1.000
first_hit_k@10 median: 1.5 | miss@10: 0/10
MRR@10 (doc): 0.717

=== DOC+SECTION (answerable only) ===
Answerable examples with section labels in gold: 10/10
hit@1: 3/10 = 0.300
hit@3: 4/10 = 0.400
hit@5: 6/10 = 0.600
hit@10: 8/10 = 0.800
first_hit_k@10 median: 3.0 | miss@10: 2/10
MRR@10 (doc+section): 0.429

Combined score (0.3*doc + 0.7*doc+section): 0.515

=== NO-ANSWER ===
abstain accuracy: 0/1 = 0.000
false positives (should abstain but didn't): 1/1 = 1.000
false abstains (should answer but abstained): 0/10 = 0.000

# V3 - new eval with doc+sec+subsec
* chunker: no reference, minimum characters
* eval, new eval that calculate Doc only, dec+sec, doc+sec+subsec
Examples: 11
Answerable: 10 | No-answer: 1
NO_ANSWER_THRESHOLD: 0.4

=== DOC-ONLY (answerable only) ===
hit@1: 5/10 = 0.500
hit@3: 10/10 = 1.000
hit@5: 10/10 = 1.000
hit@10: 10/10 = 1.000
first_hit_k@10 median: 1.5 | miss@10: 0/10
MRR@10 (doc): 0.717

=== DOC+SECTION (answerable only) ===
Gold with section labels: 10/10
hit@1: 3/10 = 0.300
hit@3: 4/10 = 0.400
hit@5: 6/10 = 0.600
hit@10: 8/10 = 0.800
first_hit_k@10 median: 3.0 | miss@10: 2/10
MRR@10 (doc+section): 0.429

=== DOC+SECTION+SUBSECTION (answerable only) ===
Gold with subsection labels: 10/10
hit@1: 2/10 = 0.200
hit@3: 4/10 = 0.400
hit@5: 6/10 = 0.600
hit@10: 8/10 = 0.800
first_hit_k@10 median: 3.5 | miss@10: 2/10
MRR@10 (doc+sec+subsec): 0.357

Combined score (0.2*doc + 0.3*doc+sec + 0.5*doc+sec+subsec): 0.450

=== NO-ANSWER ===
abstain accuracy: 0/1 = 0.000
false positives (should abstain but didn't): 1/1 = 1.000
false abstains (should answer but abstained): 0/10 = 0.000