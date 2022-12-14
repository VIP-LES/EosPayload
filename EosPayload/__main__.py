import argparse

from EosPayload.lib.orcheostrator import OrchEOStrator

""" Payload software entry point.  Invoke as `python -m EosPayload` from repo root. """

if __name__ == '__main__':
    # read args
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-directory', required=False, default='.')
    args = parser.parse_args()

    # do the things
    eos = OrchEOStrator(args.output_directory)
    eos.run()
