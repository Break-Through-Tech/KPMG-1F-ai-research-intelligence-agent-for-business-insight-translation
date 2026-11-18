# Experimental typed rate calculator

The model chooses a signed percentage-point or relative percent change and cites the initial and final rates. The host computes the value with decimal arithmetic. It accepts bounded decimal JSON numbers or strings, rejects undefined relative changes from zero, and checks that operands occur in the cited evidence. A text match cannot prove that the model chose the appropriate evidence or ordered the operands correctly; review that separately. Host rejection is not evidence that the model recognized insufficiency.

Run the CPU-only tests from the repository root:

    python -m unittest discover -s experiments/qwen-extraction/rate_menu -p 'test_*.py'

Research-only; the helper is not wired into the application. This directory contains the portable calculator slice, not the local MLX training harness or its private artifacts. See the introducing pull request for the matched development results and limitations.
