import argparse

from EosPayload.lib.orcheostrator import OrchEOStrator

""" Payload software entry point.  Invoke as `python -m EosPayload -c config.json` from repo root. """

if __name__ == '__main__':
    # read args
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-directory', required=False, default='.')
    parser.add_argument('-c', '--config-filepath', required=False, default='config.json')
    args = parser.parse_args()

    # do the things
    eos = OrchEOStrator(args.output_directory, args.config_filepath)
    eos.run()
