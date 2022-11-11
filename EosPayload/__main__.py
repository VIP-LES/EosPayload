from EosPayload.lib.orcheostrator import OrchEOStrator

""" Payload software entry point.  Invoke as `python -m EosPayload` from repo root. """

if __name__ == '__main__':
    eos = OrchEOStrator()
    eos.run()
