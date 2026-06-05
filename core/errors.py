from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

# Enumerated transient errors. Workers catch this tuple to degrade to a
# "partial" result with a recorded reason; everything else (KeyError,
# ValidationError, etc.) propagates so real bugs are not swallowed.
TRANSIENT_LLM_ERRORS = (
    APITimeoutError,
    RateLimitError,
    APIConnectionError,
    InternalServerError,
)
