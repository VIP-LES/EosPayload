import argparse

from EosPayload.lib.orcheostrator import OrchEOStrator

""" Payload software entry point.  Invoke as `python -m EosPayload` from repo root. """

if __name__ == '__main__':
    # read args
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-directory', required=False, default='.')
    parser.add_argument('-c', '--config', required=False)
    args = parser.parse_args()

    # do the things
    eos = OrchEOStrator(args.output_directory, args.config)
    eos.run()
