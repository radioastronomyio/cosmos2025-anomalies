"""Spec-z science surface builders for spec P2R-05.

Package layout (executor decomposition, documented in the interior README):

- ``policy``     frozen semantic configuration loading and validation
- ``config``     repository paths, analyst credential handoff, staging layout
- ``preflight``  gate 5.1 access and before-state verification
- ``snapshot``   read-only capture of the build's consumed input identity
- ``canonical``  canonical serialization, content digests, run identity
- ``build``      measurement audit and source summary construction
- ``splits``     P-06 frozen tile partitions
- ``install``    bounded bootstrap of the four analysis tables
- ``verify``     independent reductions used by gates 5.3 and 5.7
- ``coverage``   P-07 diagnostics and the three sensitivity variants
"""

POLICY_ID = "p2r05-specz-policy-v1"
